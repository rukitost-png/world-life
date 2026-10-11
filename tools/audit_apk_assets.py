#!/usr/bin/env python3
"""Read-only aggregate asset audit for a game APK. Never extracts or modifies files."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import re
import struct
import zipfile
import zlib
from pathlib import Path

PNG_SIG = b"\x89PNG\r\n\x1a\n"
WRAPPER_MAGIC = b"nbc 0100"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inspect_wrapper(data: bytes) -> dict:
    result = {"wrapper": "unknown", "decompression": "not-attempted",
              "declared_size": None, "decoded_size": None,
              "decoded_type": None, "size_matches": None}
    if data.startswith(PNG_SIG):
        result.update(wrapper="direct-png", decoded_type="png")
        if len(data) >= 24:
            result["png_dimensions"] = [struct.unpack(">I", data[16:20])[0],
                                        struct.unpack(">I", data[20:24])[0]]
        return result
    if data.startswith(b"OggS"):
        result.update(wrapper="direct-ogg", decoded_type="ogg")
        return result
    if len(data) >= 12 and data[:8] == WRAPPER_MAGIC:
        declared = struct.unpack("<I", data[8:12])[0]
        result.update(wrapper="nbc-0100-plus-zlib", declared_size=declared)
        try:
            decoded = zlib.decompress(data[12:])
            result.update(decompression="ok", decoded_size=len(decoded),
                          size_matches=(len(decoded) == declared))
            if decoded.startswith(PNG_SIG):
                result["decoded_type"] = "png"
                if len(decoded) >= 24:
                    result["png_dimensions"] = [struct.unpack(">I", decoded[16:20])[0],
                                                struct.unpack(">I", decoded[20:24])[0]]
            elif decoded.startswith(b"OggS"):
                result["decoded_type"] = "ogg"
            elif decoded.startswith(b"PK\x03\x04"):
                result["decoded_type"] = "zip"
            else:
                result["decoded_type"] = "opaque-binary"
        except zlib.error as exc:
            result.update(decompression="error", error=str(exc))
        return result
    result["wrapper"] = "other-signature"
    return result


def audit(apk_path: Path) -> dict:
    extension_counts = collections.Counter()
    size_by_extension = collections.Counter()
    signature_counts = collections.Counter()
    decoded_type_counts = collections.Counter()
    png_dimensions = collections.Counter()
    wrapper_errors = []
    mapdata_resources = []
    with zipfile.ZipFile(apk_path, "r") as archive:
        bad_member = archive.testzip()
        file_count = 0
        for info in archive.infolist():
            if info.is_dir():
                continue
            file_count += 1
            ext = Path(info.filename).suffix.lower() or "[no-extension]"
            extension_counts[ext] += 1
            size_by_extension[ext] += info.file_size
            if ext not in {".smf", ".nbc", ".png", ".ogg"}:
                continue
            data = archive.read(info.filename)
            result = inspect_wrapper(data)
            mapdata_match = re.fullmatch(r"res/raw/mapdata(\\d+)\\.smf", info.filename)
            if mapdata_match:
                mapdata_resources.append({
                    "index": int(mapdata_match.group(1)),
                    "size_bytes": info.file_size,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "decoded_type": result.get("decoded_type"),
                })
            signature_counts[f"{ext}:{result['wrapper']}"] += 1
            if result.get("decoded_type"):
                decoded_type_counts[f"{ext}:{result['decoded_type']}"] += 1
            if result.get("png_dimensions"):
                png_dimensions[tuple(result["png_dimensions"])] += 1
            if result.get("decompression") == "error" or result.get("size_matches") is False:
                wrapper_errors.append({"extension": ext, **result})
    mapdata_indices = sorted(item["index"] for item in mapdata_resources)
    mapdata_size_counts = collections.Counter(item["size_bytes"] for item in mapdata_resources)
    mapdata_type_counts = collections.Counter(item["decoded_type"] or "unknown" for item in mapdata_resources)
    mapdata_hash_groups = collections.Counter(
        (item["size_bytes"], item["sha256"]) for item in mapdata_resources)
    duplicate_mapdata_groups = [
        {"size_bytes": size, "sha256": digest, "count": count}
        for (size, digest), count in mapdata_hash_groups.most_common()
        if count > 1
    ]
    mapdata_probe = {
        "resource_count": len(mapdata_resources),
        "index_min": min(mapdata_indices) if mapdata_indices else None,
        "index_max": max(mapdata_indices) if mapdata_indices else None,
        "missing_indices_in_range": (
            sorted(set(range(mapdata_indices[0], mapdata_indices[-1] + 1)) - set(mapdata_indices))
            if mapdata_indices else []),
        "size_counts": dict(sorted(mapdata_size_counts.items())),
        "decoded_type_counts": dict(sorted(mapdata_type_counts.items())),
        "duplicate_container_groups": duplicate_mapdata_groups[:20],
        "per_file_paths_included": False,
    }
    return {
        "schema_version": "1.1",
        "audit_mode": "read-only-aggregate; no archive member extraction",
        "apk": {"filename": apk_path.name, "size_bytes": apk_path.stat().st_size,
                "sha256": sha256_file(apk_path),
                "zip_test": "pass" if bad_member is None else "fail",
                "bad_member": bad_member},
        "archive": {"file_count": file_count,
                    "zip_entry_count_including_directories": len(archive.infolist()),
                    "extension_counts": dict(sorted(extension_counts.items())),
                    "uncompressed_bytes_by_extension": dict(sorted(size_by_extension.items()))},
        "mapdata_resource_probe": mapdata_probe,
        "format_probe": {
            "signature_counts": dict(sorted(signature_counts.items())),
            "decoded_type_counts": dict(sorted(decoded_type_counts.items())),
            "png_dimensions_top_20": [
                {"width": w, "height": h, "count": n}
                for (w, h), n in png_dimensions.most_common(20)],
            "wrapper_errors_count": len(wrapper_errors),
            "wrapper_error_examples": wrapper_errors[:10],
            "smf_and_nbc_observations": {
                "smf_files": extension_counts[".smf"],
                "nbc_files": extension_counts[".nbc"],
                "interpretation": (
                    "A subset uses an nbc 0100 header, a little-endian declared decoded size, "
                    "and zlib payload. Decoded content is mixed. This is a format clue, not a "
                    "complete file-format specification or proof of runtime import compatibility.")}},
        "entry_details_included": False
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path, help="Path to APK; read-only")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON path")
    args = parser.parse_args()
    report = audit(args.apk)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"output": str(args.output), "zip_test": report["apk"]["zip_test"],
                      "file_count": report["archive"]["file_count"],
                      "wrapper_errors_count": report["format_probe"]["wrapper_errors_count"],
                      "sha256": report["apk"]["sha256"]}, indent=2))
    return 0 if report["apk"]["zip_test"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
