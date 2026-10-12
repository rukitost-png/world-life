#!/usr/bin/env python3
"""Read-only audit of nested text1000 RGBA4444 records in a World Life APK."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
import zipfile
import zlib
from collections import Counter
from pathlib import Path

NBC = b"nbc 0100"
TEXT_MAGIC = b"text1000"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
HEADER_BYTES = 28


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_nbc(data: bytes) -> bytes:
    if not data.startswith(NBC):
        return data
    if len(data) < 12:
        raise ValueError("truncated_nbc_header")
    expected = struct.unpack_from("<I", data, 8)[0]
    decoded = zlib.decompress(data[12:])
    if len(decoded) != expected:
        raise ValueError("nbc_declared_size_mismatch")
    return decoded


def inspect_texture(payload: bytes) -> dict:
    row = {"validation": "not_text1000", "payload_bytes": len(payload),
           "payload_sha256": sha256(payload)}
    if not payload.startswith(TEXT_MAGIC):
        return row
    if len(payload) < HEADER_BYTES:
        row["validation"] = "short_header"
        return row
    w, h, cw, ch, field16, field18 = struct.unpack_from("<HHHHHH", payload, 8)
    offset = struct.unpack_from("<I", payload, 20)[0]
    pixels = payload[offset:] if offset <= len(payload) else b""
    valid = (offset == HEADER_BYTES and len(pixels) == w * h * 2
             and payload[24:28] == bytes(4))
    row.update({"texture_width_px": w, "texture_height_px": h,
                "content_width_field": cw, "content_height_field": ch,
                "field_16": field16, "field_18": field18,
                "pixel_data_offset": offset, "pixel_bytes": len(pixels),
                "expected_pixel_bytes": w * h * 2,
                "validation": "texture_header_and_length_match" if valid
                              else "texture_header_length_mismatch"})
    return row


def parse_stream(data: bytes) -> dict:
    records, offset, error = [], 0, ""
    while offset < len(data):
        if offset + 8 > len(data):
            error = "truncated_record_header"
            break
        kind, size = struct.unpack_from("<II", data, offset)
        if kind != 2:
            break
        end = offset + 8 + size
        if size < 12 or end > len(data):
            error = "invalid_record_size"
            break
        wrapped = data[offset + 8:end]
        if not wrapped.startswith(NBC) or len(wrapped) < 12:
            error = "missing_inner_nbc_header"
            break
        try:
            payload = decode_nbc(wrapped)
        except (ValueError, zlib.error) as exc:
            error = str(exc) if isinstance(exc, ValueError) else "inner_decompression_error"
            break
        row = inspect_texture(payload)
        row.update({"record_ordinal": len(records) + 1, "record_offset": offset,
                    "record_size_bytes": size, "inner_decoded_bytes": len(payload),
                    "inner_declared_size_matches": True})
        records.append(row)
        if len(payload) != struct.unpack_from("<I", wrapped, 8)[0]:
            records[-1]["inner_declared_size_matches"] = False
            error = "inner_declared_size_mismatch"
            break
        if row["validation"] != "texture_header_and_length_match":
            error = row["validation"]
            break
        offset = end
    tail = data[offset:]
    return {"records": records, "record_error": error or None,
            "trailing_data_bytes": len(tail),
            "trailing_data_type": "png_signature" if tail.startswith(PNG_MAGIC)
                                  else ("none" if not tail else "unknown")}


def audit_apk(apk: Path, out: Path) -> dict:
    streams, records = [], []
    with zipfile.ZipFile(apk) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"zip_integrity_failure:{bad}")
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = Path(info.filename).name
            if not (name.startswith("mapdata") and name.endswith(".smf")):
                continue
            raw = archive.read(info.filename)
            stream = {"resource_path": info.filename, "resource_bytes": len(raw),
                      "resource_sha256": sha256(raw)}
            try:
                decoded = decode_nbc(raw)
                stream["decoded_bytes"] = len(decoded)
                if decoded.startswith(PNG_MAGIC):
                    stream.update({"payload_type": "png", "record_count": 0,
                                   "record_error": None, "trailing_data_type": "none"})
                else:
                    parsed = parse_stream(decoded)
                    stream.update({"payload_type": "texture_records" if parsed["records"] else "other",
                                   "record_count": len(parsed["records"]),
                                   "record_error": parsed["record_error"],
                                   "trailing_data_bytes": parsed["trailing_data_bytes"],
                                   "trailing_data_type": parsed["trailing_data_type"]})
                    for rec in parsed["records"]:
                        records.append({"resource_path": info.filename,
                                        "resource_sha256": stream["resource_sha256"], **rec})
            except (ValueError, zlib.error, struct.error) as exc:
                stream.update({"payload_type": "error", "record_count": 0,
                               "record_error": str(exc)})
            streams.append(stream)
    out.mkdir(parents=True, exist_ok=True)
    for name, rows in (("texture_stream_inventory.csv", streams),
                       ("texture_record_inventory.csv", records)):
        keys = list(dict.fromkeys(k for row in rows for k in row))
        with (out / name).open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(rows)
    summary = {"source_apk": apk.name, "source_apk_sha256": sha256(apk.read_bytes()),
               "mapdata_resources_scanned": len(streams), "texture_records_scanned": len(records),
               "stream_payload_types": dict(Counter(x.get("payload_type", "unknown") for x in streams)),
               "record_validation_counts": dict(Counter(x["validation"] for x in records)),
               "stream_errors": {x["resource_path"]: x["record_error"] for x in streams if x.get("record_error")},
               "limitations": ["Header fields beyond width, height, and pixel offset are not fully understood.",
                               "Row orientation and color-space behavior require runtime validation.",
                               "Index/checksum update semantics and runtime import acceptance are unresolved.",
                               "This is a read-only format audit, not an asset exporter or APK patcher."]}
    (out / "texture_payload_probe_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path, help="Master APK; opened read-only")
    parser.add_argument("--out", type=Path, default=Path("reports/texture_payload_probe"))
    args = parser.parse_args()
    summary = audit_apk(args.apk, args.out)
    print(json.dumps(summary, indent=2))
    if not summary["texture_records_scanned"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
