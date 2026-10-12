#!/usr/bin/env python3
"""Read-only SHA-256 audit of legacy mapdata and airport texture-offset tables."""
from __future__ import annotations
import argparse, hashlib, json, struct, zipfile, zlib
from pathlib import Path
NBC=b"nbc 0100"
PNG=b"\x89PNG\r\n\x1a\n"
def sha256(data: bytes) -> bytes: return hashlib.sha256(data).digest()
def decode_nbc(data: bytes) -> bytes:
    if not data.startswith(NBC): return data
    if len(data)<12: raise ValueError("truncated_nbc_header")
    declared=struct.unpack_from("<I",data,8)[0]
    try: decoded=zlib.decompress(data[12:])
    except zlib.error as exc: raise ValueError("invalid_nbc_zlib_stream") from exc
    if len(decoded)!=declared: raise ValueError("nbc_declared_size_mismatch")
    return decoded
def parse_checksum_table(data: bytes) -> tuple[list[bytes],int]:
    if len(data)<4: raise ValueError("checksum_table_header_truncated")
    count=struct.unpack_from("<I",data,0)[0]; end=4+count*32
    if count<1 or end>len(data): raise ValueError("checksum_table_truncated")
    return [data[4+i*32:4+(i+1)*32] for i in range(count)],end
def png_end(data: bytes,start: int=0) -> int:
    if not data.startswith(PNG,start): raise ValueError("png_signature_missing")
    pos=start+8
    while pos+12<=len(data):
        size=struct.unpack_from(">I",data,pos)[0]; kind=data[pos+4:pos+8]; end=pos+12+size
        if end>len(data): raise ValueError("png_chunk_out_of_bounds")
        pos=end
        if kind==b"IEND": return pos
    raise ValueError("png_iend_missing")
def parse_airport_offsets(info: bytes,decoded_data: bytes) -> dict:
    if len(info)<36: raise ValueError("airport_info_header_truncated")
    if sha256(decoded_data)!=info[:32]: raise ValueError("airport_data_sha256_mismatch")
    count=struct.unpack_from("<I",info,32)[0]; end=36+count*4
    if count<1 or end>len(info): raise ValueError("airport_offset_table_truncated")
    offsets=list(struct.unpack_from("<"+"I"*count,info,36))
    if offsets[0]!=0: raise ValueError("airport_offsets_do_not_start_at_zero")
    if any(a>=b for a,b in zip(offsets,offsets[1:])): raise ValueError("airport_offsets_not_strictly_increasing")
    if any(o>=len(decoded_data) for o in offsets): raise ValueError("airport_offset_out_of_bounds")
    if any(not decoded_data.startswith(PNG,o) for o in offsets): raise ValueError("airport_offset_not_png_signature")
    actual=[]; pos=0
    while True:
        pos=decoded_data.find(PNG,pos)
        if pos<0: break
        actual.append(pos); pos+=len(PNG)
    if actual!=offsets: raise ValueError("airport_offsets_do_not_match_all_png_starts")
    lengths=[]
    for i,start in enumerate(offsets):
        end_png=png_end(decoded_data,start); expected_end=offsets[i+1] if i+1<len(offsets) else len(decoded_data)
        if end_png!=expected_end: raise ValueError("airport_png_boundaries_do_not_match_offset_table")
        lengths.append(end_png-start)
    return {"count":count,"offsets":offsets,"png_lengths":lengths,"decoded_bytes":len(decoded_data),"sha256_match":True}
def audit_apk(apk_path: str|Path) -> dict:
    with zipfile.ZipFile(apk_path) as archive:
        names=set(archive.namelist()); info=archive.read("res/raw/maptexinfo.smf")
        hashes,table_end=parse_checksum_table(info); maps=[]
        for i,expected in enumerate(hashes):
            name=f"res/raw/mapdata{i:03d}.smf"
            if name not in names: maps.append({"index":i,"archive_entry":name,"status":"missing"}); continue
            stored=archive.read(name); decoded=decode_nbc(stored); actual=sha256(decoded)
            maps.append({"index":i,"archive_entry":name,"stored_bytes":len(stored),"decoded_bytes":len(decoded),
                "expected_sha256":expected.hex(),"actual_sha256":actual.hex(),"status":"match" if actual==expected else "mismatch"})
        airport_info=archive.read("res/raw/airporttexinfo.smf"); airport_stored=archive.read("res/raw/airportdata.smf")
        airport_decoded=decode_nbc(airport_stored); airport=parse_airport_offsets(airport_info,airport_decoded); previews=[]
        for row in maps:
            if row.get("status")!="match": continue
            decoded=decode_nbc(archive.read(row["archive_entry"]))
            if decoded.startswith(PNG):
                end=png_end(decoded); previews.append({"index":row["index"],"preview_png_bytes":end,"trailing_bytes":len(decoded)-end})
    return {"format":"world-life-mapdata-checksum-audit-v1","archive":str(apk_path),"maptexinfo_bytes":len(info),
        "mapdata_checksum_count":len(hashes),"checksum_table_end_offset":table_end,
        "mapdata_matches":sum(r.get("status")=="match" for r in maps),"mapdata_mismatches":sum(r.get("status")=="mismatch" for r in maps),
        "mapdata_missing":sum(r.get("status")=="missing" for r in maps),"mapdata":maps,"airporttexinfo_bytes":len(airport_info),
        "airportdata_stored_bytes":len(airport_stored),"airportdata_decoded_sha256":sha256(airport_decoded).hex(),
        "airport_texture_offsets":airport,"mapdata_png_previews":previews}
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("apk",type=Path);parser.add_argument("--json",dest="json_path",type=Path);args=parser.parse_args()
    report=audit_apk(args.apk)
    summary={k:report[k] for k in ["maptexinfo_bytes","mapdata_checksum_count","checksum_table_end_offset","mapdata_matches","mapdata_mismatches","mapdata_missing","airporttexinfo_bytes","airportdata_stored_bytes","airportdata_decoded_sha256"]}
    summary["airport_texture_count"]=report["airport_texture_offsets"]["count"]
    summary["airport_offsets_match_pngs"]=len(report["airport_texture_offsets"]["offsets"])==len(report["airport_texture_offsets"]["png_lengths"])
    print(json.dumps(summary,indent=2))
    if args.json_path: args.json_path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return 0 if report["mapdata_mismatches"]==0 and report["mapdata_missing"]==0 else 1
if __name__=="__main__": raise SystemExit(main())
