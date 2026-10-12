#!/usr/bin/env python3
"""Read-only cross-reference audit for the native EFILE filename table."""
from __future__ import annotations
import argparse, csv, json, struct, zipfile
from pathlib import Path, PurePosixPath

DEFAULT_TABLE_VADDR = 0x002E1108
DEFAULT_EFILE_COUNT = 442

def vaddr_to_offset(blob: bytes, vaddr: int) -> int:
    """Translate a virtual address through ELF32 PT_LOAD headers."""
    if len(blob) < 52 or blob[:4] != b"\x7fELF":
        raise ValueError("not_elf")
    if blob[4] != 1 or blob[5] != 1:
        raise ValueError("expected_elf32_little_endian")
    phoff = struct.unpack_from("<I", blob, 28)[0]
    entsize = struct.unpack_from("<H", blob, 42)[0]
    count = struct.unpack_from("<H", blob, 44)[0]
    for i in range(count):
        off = phoff + i * entsize
        typ, p_off, p_va, _pa, file_size, _mem_size, _flags, _align = struct.unpack_from("<IIIIIIII", blob, off)
        if typ == 1 and p_va <= vaddr < p_va + file_size:
            result = p_off + vaddr - p_va
            if result < len(blob):
                return result
    raise ValueError(f"vaddr_not_in_file_backed_load_segment:0x{vaddr:x}")

def read_c_string(blob: bytes, offset: int) -> str:
    if not 0 <= offset < len(blob):
        raise ValueError(f"string_pointer_out_of_bounds:0x{offset:x}")
    end = blob.find(b"\0", offset, min(len(blob), offset + 4096))
    if end < 0:
        raise ValueError(f"unterminated_string_at:0x{offset:x}")
    try:
        return blob[offset:end].decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError(f"non_ascii_filename_at:0x{offset:x}") from exc

def extract_filename_table(elf: bytes, table_vaddr: int = DEFAULT_TABLE_VADDR,
                           count: int = DEFAULT_EFILE_COUNT) -> list[dict]:
    if count < 1 or count > 4096:
        raise ValueError("invalid_efile_count")
    table_off = vaddr_to_offset(elf, table_vaddr)
    if table_off + count * 4 > len(elf):
        raise ValueError("filename_pointer_table_truncated")
    rows = []
    for index in range(count):
        ptr = struct.unpack_from("<I", elf, table_off + index * 4)[0]
        rows.append({"efile": index, "logical_filename": read_c_string(elf, vaddr_to_offset(elf, ptr)),
                     "pointer_vaddr": ptr})
    return rows

def candidate_archive_names(logical_name: str) -> list[str]:
    """Generate basename candidates; a match is not proof of resource-ID mapping."""
    name = PurePosixPath(logical_name).name
    candidates = [name]
    suffix = PurePosixPath(name).suffix.lower()
    if suffix in {".dat", ".nbc", ".png", ".bin"}:
        candidates.append(name[:-len(suffix)] + ".smf")
    return list(dict.fromkeys(candidates))

def audit(elf: bytes, apk_path: str | Path, table_vaddr: int = DEFAULT_TABLE_VADDR,
          count: int = DEFAULT_EFILE_COUNT) -> dict:
    rows = extract_filename_table(elf, table_vaddr, count)
    with zipfile.ZipFile(apk_path) as archive:
        raw = {name.lower(): name for name in archive.namelist()
               if name.lower().startswith("res/raw/")}
        for row in rows:
            matches = []
            for candidate in candidate_archive_names(row["logical_filename"]):
                found = raw.get(("res/raw/" + candidate).lower())
                if found and found not in matches:
                    matches.append(found)
            row["candidate_archive_entries"] = matches
            row["candidate_archive_sizes"] = [archive.getinfo(m).file_size for m in matches]
            row["archive_match_status"] = "basename_candidate_found" if matches else "no_basename_candidate"
            row["mapping_proven"] = False
    return {"format": "world-life-efile-resource-audit-v1", "table_vaddr": f"0x{table_vaddr:08x}",
            "efile_count": count, "archive_path": str(apk_path),
            "interpretation": "Basename candidates do not prove Android resource-ID or runtime offset mapping.",
            "entries": rows}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path, help="Read-only master APK")
    parser.add_argument("elf", type=Path, help="Extracted libKyotoLife.so")
    parser.add_argument("--table-vaddr", type=lambda s: int(s, 0), default=DEFAULT_TABLE_VADDR)
    parser.add_argument("--count", type=int, default=DEFAULT_EFILE_COUNT)
    parser.add_argument("--json", dest="json_path", type=Path)
    parser.add_argument("--csv", dest="csv_path", type=Path)
    args = parser.parse_args()
    report = audit(args.elf.read_bytes(), args.apk, args.table_vaddr, args.count)
    print(json.dumps({"efile_count": report["efile_count"],
        "candidate_matches": sum(bool(r["candidate_archive_entries"]) for r in report["entries"]),
        "no_candidate": sum(not r["candidate_archive_entries"] for r in report["entries"]),
        "mapping_proven": 0}, indent=2))
    if args.json_path:
        args.json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.csv_path:
        with args.csv_path.open("w", newline="", encoding="utf-8") as stream:
            fields = ["efile", "logical_filename", "archive_match_status", "candidate_archive_entries",
                      "candidate_archive_sizes", "mapping_proven"]
            writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
            for row in report["entries"]:
                writer.writerow({"efile": row["efile"], "logical_filename": row["logical_filename"],
                    "archive_match_status": row["archive_match_status"],
                    "candidate_archive_entries": ";".join(row["candidate_archive_entries"]),
                    "candidate_archive_sizes": ";".join(map(str, row["candidate_archive_sizes"])),
                    "mapping_proven": row["mapping_proven"]})
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
