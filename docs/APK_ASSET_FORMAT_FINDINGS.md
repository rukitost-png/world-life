# APK Asset Format Findings

This document summarizes a read-only archive and signature probe. It does not publish extracted game assets.

## Reference file
- File: World-Life-0.1-BGM-Fun-In-Kyoto-V2.apk
- Size: 56,840,959 bytes
- SHA-256: 36727d1a1ac1b5f1e997efe8c312f1de7945bd6d13c91651a2b195e588185ca1
- ZIP integrity: PASS
- Archive entries: 670 total, including directories; 641 files.

## Counts observed
- 412 files with the .smf extension
- 129 .png
- 25 .nbc
- 21 .ogg
- 28 .xml
- 2 native .so libraries
- 1 DEX file

## Wrapper signature observations
- 344 of 412 .smf files use an nbc 0100 header, a 4-byte little-endian decoded-size field, and a zlib payload. All tested decoded sizes matched the header.
- 26 .smf files are PNG data directly, despite the extension.
- 42 .smf files did not match those signatures and remain unclassified.
- All 25 .nbc files matched the wrapper pattern and decoded to opaque binary under the current signature checks.
- In the original first-level signature probe, 123 wrapped `.smf` payloads decoded as PNG and 221 fell into the opaque-binary bucket. The second-level mapdata probe has since identified 113 of those mapdata payloads as nested `text1000` texture records; the remaining opaque payloads still require analysis.
- All 129 direct PNG files and all 21 Ogg files had their expected file signatures.
- No wrapper decompression failures or declared-size mismatches were observed.

## Native loader follow-up (static disassembly, 2026-10-11)

- Focused ARM Thumb disassembly confirms `CNBCompressFile::CheckHeader` checks the `nbc 0100` magic/version words and `UncompressAllocate` reads the declared decoded size at byte offset 8, then inflates bytes beginning at offset 12.
- `CObjTexManager::LoadMapData(int)` calls the resource manager, decompresses the bytes, calculates SHA-256 over the decoded payload, and compares it with an index-specific checksum returned by `CObjectDataManager::GetObjDisplayHashChecksum(int)`. A wrapper-only match is therefore insufficient for compatibility.
- `CAppResourceManager::ReadFile` has both package and external/save-data resource paths, with patch-manager state involved. The complete `EFILE` to Android resource-path table remains unresolved.
- The APK has 235 `res/raw/mapdataNNN.smf` entries for indices 000–234. Of these, 105 entries are 721-byte wrappers with identical container SHA-256 and identical decoded SHA-256; their decoded payload is a 19,020-byte PNG. The other 130 entries are non-placeholder by size. This is a byte-pattern observation, not proof that the identical PNG entries are unused or interchangeable.
- See [Native Loader Disassembly Findings v0.2](NATIVE_LOADER_DISASSEMBLY_FINDINGS_v0.2.md) for symbols, addresses, call path, and remaining unknowns.

## Second-level mapdata record and texture probe

A deeper, in-memory probe of all 235 indexed mapdata resources found:

- 122 resources decode after the outer NBC wrapper to PNG data. Of these, 105 share an identical 721-byte wrapper and identical decoded PNG bytes.
- 113 resources decode to concatenated type-2 records, totaling 1,605 records. Each record contains a 32-bit type value (2), a 32-bit byte length, and a nested NBC wrapper of exactly that length.
- All 1,605 nested payloads begin with text1000 and have a 28-byte header. The texture width/height are followed by two secondary dimensions, format code 2, field value 1, a data offset of 28, and four zero bytes. The pixel payload length equals width × height × 2 for every record.
- Native disassembly confirms RGBA4444: the reader uses GL_RGBA (0x1908) with GL_UNSIGNED_SHORT_4_4_4_4 (0x8033), and the bytes-per-pixel lookup maps format code 2 to two bytes per pixel.
- 55 record streams contain additional trailing bytes that begin with a PNG signature (2×2 dimensions); substantial bytes follow the PNG IEND chunk, so this region is not yet understood as a standalone PNG.

The audit tool now parses all type-2 records, aggregates texture dimensions and length checks, and avoids recording individual resource paths. This still does not prove that a newly authored resource can be loaded by the original runtime: record offsets, secondary header semantics, trailing data, and the checksum/metadata update path remain unresolved.

## Interpretation limits
This is a useful lead, not a complete format specification. It does not decode map/object semantics, identify every payload schema, or prove newly authored assets can be imported by the original runtime. File extensions alone are not reliable format identifiers. No extracted proprietary payload was committed as a game asset.

## Required follow-up
1. Trace native and Java loader call paths to learn how the runtime consumes these containers.
2. Analyze representative examples from each signature group.
3. Establish coordinate units, pivots, texture/material references, map encoding, and required metadata.
4. Require a reproducible round-trip and runtime acceptance test before marking an asset compatible.
