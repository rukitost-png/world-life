#!/usr/bin/env python3
"""Recover EFILE -> R.raw resource-ID -> APK entry mappings from a read-only APK."""
from __future__ import annotations
import argparse, csv, json, struct, zipfile
from pathlib import Path
import audit_efile_resources as elf_audit

DEFAULT_TABLE_VADDR = 0x002E1108
DEFAULT_EFILE_COUNT = 442
RESOURCES_CLASS = "Lcom/nubee/japanlife/Resources;"
RAW_CLASS = "Lcom/nubee/japanlife/R$raw;"

def u16(data, off): return struct.unpack_from("<H", data, off)[0]
def u32(data, off): return struct.unpack_from("<I", data, off)[0]
def i32(data, off): return struct.unpack_from("<i", data, off)[0]
def uleb(data, off):
    value = shift = 0
    while True:
        if off >= len(data): raise ValueError("truncated_uleb128")
        byte = data[off]; off += 1; value |= (byte & 0x7f) << shift
        if byte < 0x80: return value, off
        shift += 7
        if shift > 35: raise ValueError("invalid_uleb128")

def instruction_sizes():
    sizes = [1] * 256
    for op in [0x02,0x05,0x08,0x13,0x15,0x16,0x19,0x1a,0x1c,0x1f,0x20,0x22,0x23,0x29,*range(0x2d,0x3e),*range(0x44,0x6e)]: sizes[op] = 2
    for op in [0x03,0x06,0x09,0x14,0x17,0x1b,0x24,0x25,0x26,0x2a,0x2b,0x2c,*range(0x6e,0x73),*range(0x74,0x79),0xfc,0xfd,0xff]: sizes[op] = 3
    sizes[0x18] = 5; sizes[0xfa] = 4; sizes[0xfb] = 4
    return sizes
SIZES = instruction_sizes()

def skip_payload(insns, pc):
    ident = u16(insns, pc * 2)
    if ident == 0x0100: return 4 + 2 * u16(insns, (pc + 1) * 2)
    if ident == 0x0200: return 2 + 4 * u16(insns, (pc + 1) * 2)
    if ident == 0x0300:
        width = u16(insns, (pc + 1) * 2); count = u32(insns, (pc + 2) * 2)
        return 4 + (width * count + 1) // 2
    return 1

class DexFile:
    def __init__(self, data):
        if len(data) < 112 or not data.startswith(b"dex\n") or data[7] != 0: raise ValueError("not_standard_dex")
        if u32(data, 40) != 0x12345678: raise ValueError("unsupported_dex_endianness")
        self.data=data; self.strings=self._strings()
        self.types=[u32(data,u32(data,68)+i*4) for i in range(u32(data,64))]
        self.fields=self._fields(); self.methods=self._methods(); self.class_defs=self._class_defs()
    def _strings(self):
        data=self.data; count=u32(data,56); off=u32(data,60); out=[]
        for i in range(count):
            pos=u32(data,off+i*4); _n,pos=uleb(data,pos); end=data.find(b"\0",pos)
            if end<0: raise ValueError("unterminated_dex_string")
            out.append(data[pos:end].decode("utf-8","replace"))
        return out
    def _fields(self):
        data=self.data; count=u32(data,80); off=u32(data,84); out=[]
        for i in range(count):
            p=off+i*8; out.append((u16(data,p),u16(data,p+2),self.strings[u32(data,p+4)]))
        return out
    def _methods(self):
        data=self.data; count=u32(data,88); off=u32(data,92); out=[]
        for i in range(count):
            p=off+i*8; out.append((u16(data,p),u16(data,p+2),self.strings[u32(data,p+4)]))
        return out
    def _class_defs(self):
        data=self.data; count=u32(data,96); off=u32(data,100); out=[]
        for i in range(count):
            p=off+i*32; out.append({"class_idx":u32(data,p),"class_data_off":u32(data,p+24),"static_values_off":u32(data,p+28)})
        return out
    def _class_data(self, offset):
        if not offset: return {"static_fields":[],"direct_methods":[],"virtual_methods":[]}
        data=self.data; sf,off=uleb(data,offset); inf,off=uleb(data,off); dm,off=uleb(data,off); vm,off=uleb(data,off)
        static=[]; idx=0
        for _ in range(sf):
            diff,off=uleb(data,off); access,off=uleb(data,off); idx+=diff; static.append((idx,access))
        for _ in range(inf): _,off=uleb(data,off); _,off=uleb(data,off)
        groups=[]
        for count in (dm,vm):
            idx=0; group=[]
            for _ in range(count):
                diff,off=uleb(data,off); access,off=uleb(data,off); code,off=uleb(data,off); idx+=diff; group.append((idx,access,code))
            groups.append(group)
        return {"static_fields":static,"direct_methods":groups[0],"virtual_methods":groups[1]}
    def raw_resource_ids(self):
        target=next((c for c in self.class_defs if self.strings[self.types[c["class_idx"]]]==RAW_CLASS),None)
        if not target: raise ValueError("R_raw_class_not_found")
        fields=self._class_data(target["class_data_off"])["static_fields"]; off=target["static_values_off"]
        if not off: raise ValueError("R_raw_static_values_missing")
        count,off=uleb(self.data,off)
        if count!=len(fields): raise ValueError("R_raw_static_value_count_mismatch")
        out={}
        for field_id,_access in fields:
            if off>=len(self.data): raise ValueError("truncated_encoded_value")
            header=self.data[off]; off+=1; typ=header&0x1f; size=(header>>5)+1
            if off+size>len(self.data): raise ValueError("truncated_encoded_value_data")
            value=int.from_bytes(self.data[off:off+size],"little",signed=typ in (0,2,4,6)); off+=size
            if typ==4: out[value]=self.fields[field_id][2]
        if not out: raise ValueError("R_raw_integer_ids_missing")
        return out
    def resource_groups(self):
        target=next((c for c in self.class_defs if self.strings[self.types[c["class_idx"]]]==RESOURCES_CLASS),None)
        if not target: raise ValueError("Resources_class_not_found")
        methods=self._class_data(target["class_data_off"])
        code=next((code for mid,_acc,code in methods["direct_methods"] if self.methods[mid][2]=="<init>" and code),None)
        if not code: raise ValueError("Resources_constructor_not_found")
        count=u32(self.data,code+12); insns=self.data[code+16:code+16+count*2]; pc=0; groups=[]
        while pc<count:
            word=u16(insns,pc*2); op=word&0xff
            if op==0 and word in (0x0100,0x0200,0x0300): pc+=skip_payload(insns,pc); continue
            if op==0x26:
                target_pc=pc+i32(insns,(pc+1)*2)
                if target_pc<0 or target_pc+4>count: raise ValueError("fill_array_target_out_of_bounds")
                if u16(insns,target_pc*2)!=0x0300: raise ValueError("unexpected_array_payload")
                width=u16(insns,(target_pc+1)*2); n=u32(insns,(target_pc+2)*2)
                if width!=4: raise ValueError("resource_array_element_width_not_int")
                pos=(target_pc+4)*2
                if pos+n*4>len(insns): raise ValueError("resource_array_payload_truncated")
                ids=list(struct.unpack_from("<"+"I"*n,insns,pos))
                q=pc+3; name=None
                while q<min(count,pc+12):
                    qw=u16(insns,q*2); qo=qw&0xff
                    if qo==0 and qw in (0x0100,0x0200,0x0300): break
                    if qo==0x5b: name=self.fields[u16(insns,(q+1)*2)][2]; break
                    q+=SIZES[qo]
                if not name: raise ValueError(f"resource_array_field_not_found_at_code_unit_{pc}")
                groups.append({"group":name,"resource_ids":ids})
            pc+=SIZES[op]
        if not groups: raise ValueError("resource_groups_not_found")
        return groups

def native_names(elf, table_vaddr=DEFAULT_TABLE_VADDR, count=DEFAULT_EFILE_COUNT):
    table=elf_audit.vaddr_to_offset(elf,table_vaddr)
    if table+count*4>len(elf): raise ValueError("native_filename_table_truncated")
    result=[]
    for i in range(count):
        ptr=u32(elf,table+i*4); result.append(elf_audit.read_c_string(elf,elf_audit.vaddr_to_offset(elf,ptr)))
    return result

def build_mapping(apk_path, elf, table_vaddr=DEFAULT_TABLE_VADDR, count=DEFAULT_EFILE_COUNT):
    with zipfile.ZipFile(apk_path) as archive:
        dex=DexFile(archive.read("classes.dex")); raw_ids=dex.raw_resource_ids(); groups=dex.resource_groups()
        entries={n.lower():n for n in archive.namelist() if n.lower().startswith("res/raw/")}
        native=native_names(elf,table_vaddr,count); flat=[]
        for group in groups:
            for local,rid in enumerate(group["resource_ids"]):
                name=raw_ids.get(rid)
                if name is None: raise ValueError(f"resource_id_not_in_R_raw:0x{rid:08x}")
                paths=sorted({p for key,p in entries.items() if key.startswith(("res/raw/"+name+".").lower())})
                flat.append((group["group"],local,rid,name,paths))
        if len(flat)!=count: raise ValueError(f"native_dex_resource_count_mismatch:{count}!={len(flat)}")
        rows=[]
        for i,(group,local,rid,name,paths) in enumerate(flat):
            status="unique_archive_entry" if len(paths)==1 else "no_archive_entry" if not paths else "ambiguous_archive_entry"
            rows.append({"efile":i,"native_filename":native[i],"resource_group":group,"group_index":local,
                "resource_id":f"0x{rid:08x}","r_raw_name":name,"archive_entries":paths,
                "archive_sizes":[archive.getinfo(p).file_size for p in paths],"archive_match_status":status,
                "mapping_basis":"DEX resource array order + R.raw ID value + native EFILE filename table"})
    return {"format":"world-life-efile-dex-resource-map-v1","efile_count":count,
        "resource_groups":[{"group":g["group"],"count":len(g["resource_ids"])} for g in groups],
        "mapping_note":"Static mapping for this APK build; replacement/runtime compatibility is not tested.","entries":rows}

def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("apk",type=Path); parser.add_argument("elf",type=Path)
    parser.add_argument("--table-vaddr",type=lambda x:int(x,0),default=DEFAULT_TABLE_VADDR); parser.add_argument("--count",type=int,default=DEFAULT_EFILE_COUNT)
    parser.add_argument("--json",dest="json_path",type=Path); parser.add_argument("--csv",dest="csv_path",type=Path); args=parser.parse_args()
    report=build_mapping(args.apk,args.elf.read_bytes(),args.table_vaddr,args.count); counts={}
    for row in report["entries"]: counts[row["archive_match_status"]]=counts.get(row["archive_match_status"],0)+1
    print(json.dumps({"efile_count":report["efile_count"],"groups":report["resource_groups"],"archive_status_counts":counts},indent=2))
    if args.json_path: args.json_path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    if args.csv_path:
        fields=["efile","native_filename","resource_group","group_index","resource_id","r_raw_name","archive_entries","archive_sizes","archive_match_status","mapping_basis"]
        with args.csv_path.open("w",newline="",encoding="utf-8") as stream:
            writer=csv.DictWriter(stream,fieldnames=fields); writer.writeheader()
            for row in report["entries"]:
                writer.writerow({**row,"archive_entries":";".join(row["archive_entries"]),"archive_sizes":";".join(map(str,row["archive_sizes"]))})
    return 0
if __name__=="__main__": raise SystemExit(main())
