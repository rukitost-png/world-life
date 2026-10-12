# Native Loader Findings v0.4 — EFILE Filename Table

Date: 2026-10-12  
Reference: `lib/armeabi/libKyotoLife.so` from the read-only master APK  
Method: static ARM Thumb disassembly and direct inspection of the library's read-only pointer table; no APK modification

## Key new result: EFILE indices now map to logical filenames

The native `CAppResourceManager::GetFilename(EFILE)` implementation bounds-checks an enum value against `0x1B9` (441) and returns the corresponding pointer from a filename-pointer table. Resolving the table's PC-relative address against the library's read-only data yields the following direct mappings:

| EFILE index | Logical filename returned by native table | Confidence |
|---:|---|---|
| 0 | `maptexinfo.dat` | Direct table entry |
| 1 | `mapdata000.nbc` | Direct table entry |
| 2 | `mapdata001.nbc` | Direct table entry |
| 3 | `mapdata002.nbc` | Direct table entry |
| 235 | `mapdata234.nbc` | Direct table entry |
| 433 | `eff_rain.png` | Direct table entry |
| 434 | `airporttexinfo.dat` | Direct table entry |
| 435 | `airportdata.nbc` | Direct table entry |
| 441 | `MapSelection_Theme.bin` | Direct table entry |

This resolves the most important ambiguity from v0.3: **EFILE 0 is the logical `maptexinfo.dat` resource; EFILE 434 is `airporttexinfo.dat`, not another `mapdataNNN.nbc` entry.** The second input read by `CObjectDataManager::Initialize()` is therefore an airport texture-info resource. The precise relationship between its 44-byte-stride records and the manager's object-display structures still requires field-level tracing; do not relabel the whole table as generic map object metadata.

## Relevant native functions and evidence

- `CAppResourceManager::GetFilename(EFILE)`: Thumb address `0x000bf114`, 28 bytes.
  - Compares EFILE against the maximum value `0x1B9` (441).
  - For an in-range value, loads the pointer at `filename_table + 4 * EFILE`.
- Filename pointer table: PC-relative base resolved to virtual address `0x002e1108` for this exact library build.
- `CAppResourceManager::GetEnumFromFilename(char const*)`: Thumb address `0x000bf1c0`; iterates 442 filename pointers and compares case-insensitively.
- `CAppResourceManager::GetResourcePath(EFILE)`: Thumb address `0x000bf0b8`; separately checks an EFILE-indexed table and returns a shared path prefix for entries with a positive value. It does not itself provide the filename string.
- `CObjectDataManager::Initialize()`: Thumb address `0x0021ea50`.
  - First `ReadFile` call uses EFILE 0, which now maps to `maptexinfo.dat`.
  - Second `ReadFile` call uses EFILE 434, which now maps to `airporttexinfo.dat`.
- `CObjTexManager::LoadMapData(int)`: Thumb address `0x001fe894`; separately reads an indexed mapdata resource, decompresses it, hashes the decoded stream with SHA-256, and compares it against the checksum accessor.

Addresses are build-specific. The direct filename mappings were recovered from the original library's pointer table; they are not guessed from strings alone.

## Updated interpretation

The filename table makes it possible to distinguish three concepts that must not be conflated:

1. **Logical EFILE name** — the name returned by `GetFilename(EFILE)`, such as `mapdata000.nbc`.
2. **Android APK resource name** — the archive contains entries such as `res/raw/mapdata000.smf`; this is a package-level name and differs from the logical native filename.
3. **Decoded payload and checksum** — the native map-data loader validates the decompressed byte stream against a checksum indexed through object-display metadata.

The observed native table establishes logical names but does not, by itself, prove how the Android resource manager maps `.nbc` names to `.smf` archive entries in every package/external/patch branch. That mapping should be traced in `ReadFileFromPackage`, `OpenFileFromPackage`, and the resource-offset/hash-check setup before attempting any replacement.

## Next falsifiable steps

1. Trace how `maptexinfo.dat` is parsed: confirm its header/count and each 32-byte checksum entry against the code path in `CObjectDataManager::Initialize()`.
2. Trace how `airporttexinfo.dat` is parsed and identify the field at offset `+0x20` used as the record count; distinguish airport records from map object-display records.
3. Trace `GetFilename` through `OpenFileFromPackage` and `GetResourceOffset` to establish the package resource-ID/index mapping between logical `.nbc` names and APK `.smf` entries.
4. Follow the `IsPackedTextureUpdated` and patch-manager path to determine whether checksum metadata can legitimately be updated from server-provided patch data.
5. Keep the master APK read-only and do not claim runtime import compatibility until a controlled, authorized runtime test passes.

## Reproduction

```sh
readelf -Ws libKyotoLife.so | c++filt | grep -E 'CAppResourceManager::(GetFilename|GetEnumFromFilename|GetResourcePath|GetResourceOffset|GetResourceSize)|CObjectDataManager::Initialize'
llvm-objdump -d --triple=thumbv7-linux-gnueabi --start-address=0xbf114 --stop-address=0xbf130 libKyotoLife.so
llvm-objdump -d --triple=thumbv7-linux-gnueabi --start-address=0xbf1c0 --stop-address=0xbf270 libKyotoLife.so
```

No extracted game payloads, modified APKs, or signing material are included in this change.
