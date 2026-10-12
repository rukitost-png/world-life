# Native Loader Findings v0.7 — Verified mapdata checksums and airport PNG offsets

Date: 2026-10-13  
Reference: read-only master APK SHA-256 `36727d1a1ac1b5f1e997efe8c312f1de7945bd6d13c91651a2b195e588185ca1`

## Confirmed: all 235 mapdata checksum entries match

`res/raw/maptexinfo.smf` begins with a little-endian count of 235, followed by 235 consecutive 32-byte SHA-256 digests. The checksum table occupies bytes 0–7,523 (end offset 7,524); the resource continues beyond that point and the tail is parsed by the native object-data manager, so it must not be discarded as padding.

The audit decompresses each `res/raw/mapdataNNN.smf` NBC wrapper, hashes the full decoded byte stream, and compares that digest with the corresponding 32-byte entry in `maptexinfo.smf`.

| Check | Result |
|---|---:|
| Checksum entries | 235 |
| Mapdata resources checked | 235 |
| Decoded-stream SHA-256 matches | 235 |
| Mismatches | 0 |
| Missing resources | 0 |

This proves the expected checksum covers the **decoded NBC stream**, not the stored compressed APK member. It also provides a regression oracle for future export/import tooling: a candidate replacement can be checked against this format rule, though a new asset would need a legitimate corresponding metadata/checksum update and runtime test.

## Confirmed: airporttexinfo indexes 84 concatenated PNG images

`res/raw/airporttexinfo.smf` is 372 bytes:
- bytes 0–31: SHA-256 digest of the decoded `airportdata` stream;
- bytes 32–35: little-endian image count, 84;
- bytes 36 onward: 84 little-endian byte offsets.

The 84 offsets are strictly increasing, start at zero, and each points to a PNG signature in the decoded `airportdata` stream. Parsing each PNG through its IEND chunk shows that its end equals the next offset (or the end of the decoded stream for the final image). All 84 offsets and image boundaries validate. The decoded `airportdata` stream is 401,744 bytes; its stored NBC resource is 336,125 bytes.

This confirms that `airportdata` is a concatenation of PNG images, with the index/offset table stored separately in `airporttexinfo`. The initial 32-byte digest matches the SHA-256 of the complete decoded concatenated stream.

## Reproduction

Extract nothing permanently and keep the master APK unchanged; the script reads the ZIP directly:

```sh
python tools/audit_mapdata_checksums.py World-Life-0.1-BGM-Fun-In-Kyoto-V2.apk --json mapdata-checksum-audit.json
python -m unittest discover -s tests -v
```

The JSON report includes every expected/actual digest, stored and decoded sizes, the checksum-table boundary, and airport PNG offsets. It contains metadata only, not extracted asset payloads.

## What remains unresolved

- The full schema of the 655,091-byte tail after the mapdata checksum table in `maptexinfo.smf`; native initialization parses this tail into object-display structures, so it is not safe to overwrite or trim.
- The complete semantics of the per-object records and how their indexes relate to the nested texture records in each mapdata stream.
- Whether a replacement asset may be activated by the legacy patch flow, and whether the legacy backend protocol remains reachable and authenticated.
- Android rebuild/sign/install/runtime testing remains blocked by missing Android build tools and the original private signing key.

The master APK remains read-only. No APK build, signature, installation, or gameplay test is claimed.
