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
- Among wrapped .smf payloads, 123 decoded as PNG and 221 were opaque binary under current signature checks.
- All 129 direct PNG files and all 21 Ogg files had their expected file signatures.
- No wrapper decompression failures or declared-size mismatches were observed.

## Interpretation limits
This is a useful lead, not a complete format specification. It does not decode map/object semantics, identify every payload schema, or prove newly authored assets can be imported by the original runtime. File extensions alone are not reliable format identifiers. No extracted proprietary payload was committed as a game asset.

## Required follow-up
1. Trace native and Java loader call paths to learn how the runtime consumes these containers.
2. Analyze representative examples from each signature group.
3. Establish coordinate units, pivots, texture/material references, map encoding, and required metadata.
4. Require a reproducible round-trip and runtime acceptance test before marking an asset compatible.
