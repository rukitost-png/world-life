# Native Loader Disassembly Findings v0.2

Date: 2026-10-11  
Reference binary: `libKyotoLife.so` from the read-only master APK  
Analysis mode: static ARM Thumb disassembly using LLVM 17; no code or APK changes

## Executive result

The loader path is now clearer than symbol/string triage alone. The native object-texture manager reads an indexed resource, passes its bytes through the native NBC header/decompression implementation, computes SHA-256 over the decoded content, and compares the result against an object-display checksum for that index before accepting the decoded bytes into its cache. This means that matching the wrapper alone is not sufficient to make a replacement map resource valid.

## Evidence and call path

### 1. `CObjTexManager::LoadMapData(int)`

- ELF symbol: `_ZN14CObjTexManager11LoadMapDataEi`
- Thumb entry address: `0x001fe894` (symbol table value includes the Thumb bit; disassembly address is even)
- Observed control flow:
  1. Bounds-checks the integer resource index against a manager-held count.
  2. Releases the prior cached entry for that index.
  3. Calls `CAppResourceManager::ReadFile(EFILE, char**, int*)`.
  4. Calls `CNBCompressFile::UncompressAllocate(...)` on the returned bytes.
  5. Computes SHA-256 using `CSha256::GetHash`.
  6. Obtains an expected value through `CObjectDataManager::GetObjDisplayHashChecksum(index)` and compares 32 bytes.
  7. On a matching checksum, replaces the cached decoded data for the indexed resource; on mismatch, emits the observed log message `[ObjTexManager] Invalid checksum for mapdata%02d.nbc` and does not accept the new content.
- Relevant call addresses in the disassembly: `ReadFile` at `0x000bf448`, `UncompressAllocate` at `0x00133100`, `CSha256::GetHash` at `0x000c3278`, `GetObjDisplayHashChecksum` at `0x0021e308`.

**Implication:** a syntactically valid wrapper is only one validation layer. The index-to-resource mapping and expected checksum source must also be understood before a custom resource can be accepted.

### 2. Native NBC wrapper validation

- `CNBCompressFile::CheckHeader(void*, unsigned int)`: `0x00132cf0`
- `CNBCompressFile::UncompressAllocate(...)`: `0x00133100`
- `CNblTexture::LoadTextureFromCompressedRaw(...)`: `0x00136910`
- `CNblTexture::LoadTexture(...)`: `0x00136748`
- `CNblTexture::Initialize(...)`: `0x00136780`
- `CNblTexture::GetBytesPerPixel()`: `0x00136690`
- `CheckHeader` rejects inputs of 12 bytes or fewer and checks the first two 32-bit words against the `nbc 0100` magic/version bytes.
- `UncompressAllocate` reads the 32-bit decoded-size field at byte offset 8, allocates that many bytes, and passes the payload beginning at byte offset 12 to the native inflate helper.
- This independently confirms the observed 12-byte wrapper layout: 8-byte magic/version text, a 4-byte size field, then compressed data.

The static implementation supports the existing Python audit's wrapper interpretation. It does **not** establish that every opaque decoded payload has the same internal schema.

### 3. Expected checksum table

- Accessor: `CObjectDataManager::GetObjDisplayHashChecksum(int)` at `0x0021e308`.
- The accessor bounds-checks the requested index against a manager-held count, returns the corresponding pointer from an indexed checksum array, and has a special case for an airport checksum when the index equals the count.
- `CObjectDataManager::Initialize()` at `0x0021ea50` invokes `CBin2CSV::Initialize(EFILE)` repeatedly and consumes typed fields (`GetUINT`, `GetUSHORT`, `GetINT`, `SkipString`) while constructing object-display metadata. The binary contains the log string `[InitializeDisplayData] Invalid number of hash checksums(%d)` and the resource-name string `maptexinfo.dat`.
- This strongly indicates that checksum expectations are part of initialized object-display metadata, but the exact `EFILE` value/source table that supplies the relevant checksum records is not yet mapped. Do not assume `maptexinfo.dat` is the sole or confirmed source without resolving the enum/path mapping.

### 4. Second-level mapdata texture payload

A second, in-memory probe of all 235 `res/raw/mapdataNNN.smf` resources found two broad outer-decoded groups:

- 122 decode directly to PNG data. A group of 105 entries share identical 721-byte containers and identical decoded PNG bytes; this byte identity alone does not establish that the entries are unused.
- 113 decode to an 8-byte prefix followed by a second `nbc 0100` wrapper. All 113 inner wrappers decompress to a payload beginning with ASCII `text1000`.

The 113 `text1000` payloads share the following observed layout:

| Offset | Observed field | Finding |
|---:|---|---|
| 0–7 | Magic | ASCII `text1000` |
| 8–9 | First dimension | 16-bit little-endian value |
| 10–11 | Second dimension | 16-bit little-endian value |
| 12–13 | Secondary dimension A | 16-bit little-endian value; meaning not confirmed |
| 14–15 | Secondary dimension B | 16-bit little-endian value; meaning not confirmed |
| 16–17 | Field A | `2` in all 113 samples; meaning not confirmed |
| 18–19 | Field B | `1` in all 113 samples; meaning not confirmed |
| 20–23 | Payload offset | `28` in all 113 samples |
| 24–27 | Reserved-looking bytes | Four zero bytes in all 113 samples |
| 28 onward | Pixel-like payload | Exactly `first dimension × second dimension × 2` bytes in all 113 samples |

The native consumer is now traced one level deeper: `CNblTexture::LoadTextureFromCompressedRaw` calls `UncompressAllocate` on the nested wrapper and then dispatches to `CNblTexture::LoadTexture`; its initializer reads the `text1000` header and copies pixel bytes from offset 28. `CNblTexture::GetBytesPerPixel` indexes a native lookup table `[1, 1, 2, 2, 4]` using the 16-bit field at header offset 16. That field is `2` in all 113 mapdata samples, so the native code confirms 2 bytes per pixel and explains the exact `width × height × 2` invariant. This confirms the byte width, **not** the channel packing, alpha mode, color space, row orientation, or the semantic meaning of the secondary dimensions. Those still require more decoder analysis.

### 5. Package resources and external/patch resources

- `CAppResourceManager::ReadFile(EFILE, char**, int*)`: `0x000bf448`
- `CAppResourceManager::ReadFileFromPackage(...)`: `0x000bf324`
- `CAppResourceManager::ReadFileFromExternal(...)`: `0x000bf404`
- The package path calls `GetResourcePath(EFILE)`, opens the returned path, reads the file bytes, and returns the allocated buffer and byte count.
- The general read path has branches into both package-resource loading and an external/save-data read path, with patch-manager state involved. The exact `EFILE` enum-to-path table and every branch condition have not yet been fully reconstructed.

The APK contains Android raw resources named `res/raw/mapdataNNN.smf` (235 indexed entries for indices 000–234). A follow-up archive probe found 105 entries with a 721-byte container; all 105 have the same container SHA-256 and decode to the same 19,020-byte PNG. The remaining 130 entries are larger by file size. The native library also contains logical filename strings such as `mapdata%02d.nbc` and checksum/texture error messages. These observations are consistent with a resource abstraction that can use different package and logical names; they do not prove the names are interchangeable in every code path.

### 6. Map coordinate conversion

- `CMapDataManager::GetMapPos(S2DPointF&, float, float)`: `0x00217434`
- `CMapDataManager::GetMapIndex(S2DPoint&, int, int)`: `0x002176e0`
- The functions perform floating-point arithmetic involving map offsets, manager-held scale/size values, and separate horizontal/vertical terms. The map-index function writes two 16-bit coordinates.
- This is evidence of a native coordinate transform and grid-index conversion. The global data structures and literal-pool values still need to be resolved to calculate authoritative tile dimensions, origin, axis direction, and exact projection coefficients. No camera or tile scale should be marked confirmed from this disassembly alone.

## Reproducible analysis commands

Run from an environment with LLVM 17 and the extracted library:

```sh
readelf -Ws libKyotoLife.so | grep -E 'CObjTexManager.*LoadMapData|CAppResourceManager.*ReadFile|CNBCompressFile.*(CheckHeader|UncompressAllocate)|CMapDataManager.*(GetMapPos|GetMapIndex)'
llvm-objdump -d --triple=thumbv7-linux-gnueabi --disassemble-symbols=_ZN14CObjTexManager11LoadMapDataEi,_ZN19CAppResourceManager8ReadFileENS_5EFILEEPPcPi,_ZN15CNBCompressFile11CheckHeaderEPvj,_ZN15CNBCompressFile18UncompressAllocateEPvjPS0_Pj libKyotoLife.so
```

The symbol spellings above are the Itanium C++ ABI names reported by this binary. The master APK remains read-only; extracted libraries and disassembly outputs were kept in a temporary analysis directory and are not committed.

## What this does and does not prove

**Supported by disassembly**
- The native loader uses the 12-byte NBC header and a decompression step.
- Map-data acceptance includes a SHA-256 comparison against an index-specific expected checksum held by `CObjectDataManager`.
- Package and external resource-read paths both exist.
- Map-to-screen and map-to-index conversions are native functions.

**Still unproven**
- Full internal schema for opaque map-data payloads.
- Complete `EFILE` enum and resource path mapping.
- Where expected object-display checksums are authored, downloaded, or updated.
- Exact map tile units, object pivots/footprints, rotation encoding, collision rules, and camera coefficients.
- Whether a newly authored resource can pass the original runtime's checksum, texture parsing, and map rendering paths.

## Next investigation

1. Recover the `EFILE` enum/path table from `GetResourcePath` and relevant read-only ELF data.
2. Trace the checksum table population and patch/update logic, including `IsPackedTextureUpdated` and object display metadata.
3. Compare one non-empty map resource's decoded bytes with its corresponding object-display/texture metadata without publishing proprietary payloads.
4. Resolve the global constants and data structures used by `GetMapPos` and `GetMapIndex`; then create a coordinate calibration test using several known points.
5. Keep all new assets marked experimental until the original runtime accepts a controlled test resource.
