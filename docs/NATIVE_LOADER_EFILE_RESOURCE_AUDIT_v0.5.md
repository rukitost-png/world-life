# Native Loader Findings v0.5 — EFILE resource offsets and patch validation

Date: 2026-10-13  
Reference: read-only `lib/armeabi/libKyotoLife.so` extracted from the master APK  
Master APK SHA-256: `36727d1a1ac1b5f1e997efe8c312f1de7945bd6d13c91651a2b195e588185ca1`  
Method: static ARM Thumb disassembly and read-only APK ZIP inventory

## New result: offset and size are supplied by the Android layer

The native bridge `Java_com_nubee_japanlife_GameActivity_SetResourceOffset` at Thumb address `0x0025b980` forwards three integer arguments to `CAppResourceManager::SetResourceOffsets` at `0x000bf0d8`:

- EFILE enum index;
- package-file byte offset;
- resource byte size.

`SetResourceOffsets` writes the offset and size into separate EFILE-indexed arrays. `GetResourceOffset` and `GetResourceSize` read those arrays. `OpenFileFromPackage` / `ReadFileFromPackage` use the EFILE's resource-path prefix, offset, and size to seek/read from the package file. Thus the native library does not derive the APK byte offset from the logical filename at read time: the Android/Java side supplies the offset-size pair to native code.

This narrows the remaining gap: the Java caller that enumerates Android raw resources and calls `SetResourceOffset` must be inspected to prove the exact resource-ID-to-EFILE mapping. A matching basename alone is not sufficient proof.

## Read-only cross-reference audit

`tools/audit_efile_resources.py` reads the ELF32 little-endian filename pointer table (default virtual address `0x002e1108`, 442 entries for this exact library build), then compares logical names with candidate basenames in `res/raw/`. It does not extract or modify archive members. It reports candidate archive names and uncompressed sizes, and deliberately marks every candidate mapping as unproven.

Running it against the master APK and its `libKyotoLife.so` found candidate basenames for 375 of 442 logical EFILE names; 67 had no candidate under the conservative basename/suffix rules. This is a search result, not proof of missing game assets: some entries may be non-raw resources, external/patch resources, differently named resources, or non-package paths.

| EFILE | Native logical name | Candidate APK entry | Uncompressed bytes |
|---:|---|---|---:|
| 0 | `maptexinfo.dat` | `res/raw/maptexinfo.smf` | 662,615 |
| 1 | `mapdata000.nbc` | `res/raw/mapdata000.smf` | 28,686 |
| 2 | `mapdata001.nbc` | `res/raw/mapdata001.smf` | 106,341 |
| 434 | `airporttexinfo.dat` | `res/raw/airporttexinfo.smf` | 372 |
| 435 | `airportdata.nbc` | `res/raw/airportdata.smf` | 336,125 |

The extension conversion (`.dat`/`.nbc` to `.smf`) is only a candidate-generation heuristic; do not use it to rewrite resources without the Java resource-ID mapping and a successful runtime test.

## Patch validation path — what static analysis supports

- `CPatchManager::CheckNeedUpdate` at `0x00239710` calls `CPatchData::ReadPatchFile`.
- `CPatchData::ReadPatchFile` validates the patch container, allocates patch entries, reads each entry's filename and resolves it through `CAppResourceManager::GetEnumFromFilename`.
- `CPatchData::ValidatePatchFileData` computes SHA-256 over the patch data and compares the 32-byte digest with the digest stored in the patch entry before the patch object is accepted.
- `CPatchManager::SetFileDownloaded` at `0x00238eb8` finds an EFILE entry in its parsed patch table and compares a supplied 32-byte value with the stored digest before taking the matching branch.

This shows that the legacy runtime has a filename-indexed patch manifest and digest checks. It does **not** establish that arbitrary server-delivered replacement assets can be safely installed, that checksum metadata can be changed remotely, or that the existing service protocol is still reachable. The exact persistence/activation path and authorization/signature guarantees remain unresolved.

## Reproduction

Extract `lib/armeabi/libKyotoLife.so` from the master APK, then run:

```sh
python tools/audit_efile_resources.py World-Life-0.1-BGM-Fun-In-Kyoto-V2.apk libKyotoLife.so --json efile-resource-audit.json --csv efile-resource-audit.csv
python -m unittest discover -s tests -v
```

The default table address is build-specific. For another library build, resolve the `GetFilename(EFILE)` pointer table first and pass `--table-vaddr` and `--count` explicitly.

## Next proof gates

1. Inspect the Android Java/Dex caller of `GameActivity.SetResourceOffset` and prove how each `R.raw.*` ID, package offset, and size is assigned to an EFILE index.
2. Decode the `maptexinfo.dat` checksum table against the exact `mapdataNNN.smf` payloads and determine whether the checksums cover stored or decoded bytes.
3. Trace where patch data is persisted, promoted to active resources, and authenticated; do not infer server compatibility from the native patch parser alone.
4. Keep the master APK read-only. Do not claim import compatibility, APK rebuild, signing, installation, or device runtime success until those tests actually pass.
