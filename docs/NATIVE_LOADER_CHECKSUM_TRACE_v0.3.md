# Native Loader Findings v0.3 — Checksum Table Trace

Date: 2026-10-12  
Reference: read-only `lib/armeabi/libKyotoLife.so` from the master APK  
Method: static ARM Thumb disassembly with LLVM; no APK modification

## New result

The `CObjectDataManager::Initialize()` call sequence separates two inputs that had previously been easy to conflate:

| Input | Observed EFILE argument | Direct evidence in `Initialize()` | Result / confidence |
|---|---:|---|---|
| Object-display metadata | 434 (`0x1B2`) | The returned pointer is read at offset `+0x20` for the record count; each allocated object-display record has a `0x2C` (44-byte) stride. | High for the observed argument and stride; schema semantics remain partial. |
| Expected display checksums | 0 | The returned buffer's first 32-bit word is read as the checksum count; the code allocates a pointer array with 4 bytes per entry and a contiguous buffer with 32 bytes per entry, then copies 32 bytes per checksum. | High for the observed memory layout; the enum-to-path name for EFILE 0 is still unresolved. |

The checksum accessor `CObjectDataManager::GetObjDisplayHashChecksum(int)` at Thumb address `0x0021e308` bounds-checks the requested index against a manager-held count and returns the indexed pointer from the checksum pointer array. The separate map-data load path computes SHA-256 of the decoded map-data stream and compares all 32 bytes against this accessor's result before caching the stream.

### Relevant disassembly landmarks

- `CObjectDataManager::Initialize()`: `0x0021ea50`
- First `ReadFile` call, argument EFILE 0: `0x0021ea5e–0x0021ea68`
- Second `ReadFile` call, argument EFILE 434: `0x0021ea70–0x0021ea80`
- Display-record allocation with stride `0x2C`: `0x0021eaa8–0x0021eaba`
- Checksum count read and checksum buffers allocated: approximately `0x0021ebfc–0x0021ec24`
- Checksum entries copied in 32-byte blocks: loop around `0x0021ec2a–0x0021ec4e`
- `CObjectDataManager::GetObjDisplayHashChecksum(int)`: `0x0021e308`
- `CObjTexManager::LoadMapData(int)`: Thumb address `0x001fe894`

These offsets are static addresses in this specific library build, not stable addresses for other builds.

## What is now established

1. The checksum table is not merely inferred from a nearby string: initialization explicitly reads a count and copies fixed 32-byte checksum entries from the EFILE-0 buffer.
2. EFILE 434 supplies a distinct input used to size the object-display record allocation.
3. Map-data validation is index-based: the decoded resource's SHA-256 must match the checksum at the corresponding display index.

## What remains unresolved

- The complete EFILE enum and the resource-path string table are not yet decoded, so EFILE 0 and 434 must not be given guessed filenames.
- The mapping between each object-display record/index and a specific `mapdataNNN.smf` or logical `mapdata%02d.nbc` resource still needs direct evidence.
- The exact schema and source of the 44-byte object-display records remain incomplete.
- External/patch-resource behavior and the mechanism by which a legitimate update could supply new matching checksums remain unresolved.

## Next falsifiable steps

1. Decode the resource-path lookup table behind `CAppResourceManager::GetResourcePath(EFILE)` and identify the exact package paths for EFILE 0 and 434.
2. Trace the `CObjectDataManager::Initialize()` field reads following allocation to identify which object-display field associates a record with the checksum index.
3. Trace the callers of `CObjTexManager::LoadMapData(int)` and `GetObjDisplayHashChecksum(int)` to connect the index to a concrete resource index in at least three examples.
4. Keep the master APK read-only; do not write checksums or claim runtime compatibility until a controlled test is accepted by the original runtime.

## Reproduction

Extract `lib/armeabi/libKyotoLife.so` from the master APK and run:

```sh
readelf -Ws libKyotoLife.so | grep -E 'CObjectDataManager.*(Initialize|GetObjDisplayHashChecksum)|CAppResourceManager.*GetResourcePath'
llvm-objdump -d --triple=thumbv7-linux-gnueabi --start-address=0x21ea50 --stop-address=0x21ed90 libKyotoLife.so
llvm-objdump -d --triple=thumbv7-linux-gnueabi --start-address=0x21e308 --stop-address=0x21e338 libKyotoLife.so
llvm-objdump -d --triple=thumbv7-linux-gnueabi --start-address=0xbf0b8 --stop-address=0xbf0d8 libKyotoLife.so
```

No extracted proprietary payloads or modified APKs are included in this repository change.
