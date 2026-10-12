# Nested Texture Findings v0.3 — World Life / Dukku

**Date:** 2026-10-12  
**Source:** Read-only master APK World-Life-0.1-BGM-Fun-In-Kyoto-V2.apk from the user's ChatGPT Library  
**SHA-256:** 36727d1a1ac1b5f1e997efe8c312f1de7945bd6d13c91651a2b195e588185ca1

## Executive correction

The earlier hypothesis that nested text1000 payloads were tile-grid/cell data was incorrect. Native texture upload evidence identifies them as **RGBA4444 image textures**. The mapdataNNN.smf filename is not sufficient evidence of map-cell semantics.

## Reproduced archive facts

- APK size: 56,840,959 bytes; ZIP integrity test passes.
- 670 ZIP entries including directories; 641 files.
- 412 .smf, 129 .png, 25 .nbc, 21 .ogg, 28 XML, 2 native .so, and 1 DEX.
- 235 res/raw/mapdataNNN.smf resources.
- 122 resources outer-decode directly to PNG; 105 of these share identical 721-byte wrappers and the same decoded 2×2 PNG payload. Do not infer they are unused without tracing references.
- 113 resources contain concatenated type-2 records, totaling 1,605 nested NBC-wrapped text1000 textures.
- All 1,605 records pass the declared inner-size check and the 28-byte header + width × height × 2 pixel-length invariant.
- Across the records, 112,677,888 RGBA4444 pixels are present. The low alpha-nibble count is 79,928,219 (70.935%); this is descriptive only, not a quality or usage verdict.

## Header observed in the nested texture payload

| Offset | Observed value/meaning | Confidence |
|---:|---|---|
| 0–7 | ASCII text1000 | Confirmed |
| 8–9 | Texture width, unsigned 16-bit little-endian | Confirmed by payload-size invariant |
| 10–11 | Texture height, unsigned 16-bit little-endian | Confirmed by payload-size invariant |
| 12–13 | Secondary dimension field | Value recorded; exact semantics unconfirmed |
| 14–15 | Secondary dimension field | Value recorded; exact semantics unconfirmed |
| 16–17 | 2 in all 1,605 records | Observed; native bytes-per-pixel lookup maps this code to 2 bytes |
| 18–19 | 1 in all 1,605 records | Observed; meaning unconfirmed |
| 20–23 | Pixel-data offset 28 in all 1,605 records | Confirmed by payload layout |
| 24–27 | Four zero bytes in all 1,605 records | Observed |
| 28 onward | width × height × 2 bytes | Confirmed |

The native upload path uses glTexImage2D with GL_RGBA and GL_UNSIGNED_SHORT_4_4_4_4, confirming four 4-bit channels (RGBA4444). Rendering previews expands each channel nibble to 8-bit by multiplying by 17. The preview transform is an analysis aid; row orientation and color-space assumptions still require runtime comparison.

## Loader and compatibility gate

CObjTexManager::LoadMapData(int) reads the indexed resource, decompresses the outer NBC wrapper, calculates SHA-256 over the decoded resource buffer, and compares it with the index-specific checksum supplied by object-display metadata. A valid texture payload and valid wrapper are therefore **not sufficient** for original-runtime import.

Still unresolved:
- Exact EFILE to packaged/external resource-path mapping.
- Source and update procedure for the index-specific object-display checksum table.
- Exact semantics of secondary header fields.
- Row orientation and color-space/gamma behavior.
- Purpose of trailing bytes beginning with a PNG signature in 55 texture streams.
- Whether the 105 identical 2×2 PNG resources are placeholders, shared resources, or still referenced.
- A controlled asset import round-trip and device/runtime validation.

## Repeatable tooling and test results

The Server Alpha v1.2 bundle includes tools/texture_payload_probe.py, which scans all 235 resources and parses every type-2 record, tests/test_texture_payload_probe.py, per-record/per-stream CSVs, a JSON summary, 113 first-record PNG previews, and a contact sheet. Raw decoded .texbin payloads are optional output and are not included in the source bundle by default.

Local verification on the recovered APK:
- Master APK hash and ZIP integrity: PASS.
- Asset inventory: PASS.
- Native binary inventory: PASS (2 libraries, 83 URL-like strings, 6 hosts).
- DEX method/string trace: PASS (26,963 strings, 3,417 types, 21,092 methods, 2,547 class definitions, 17,821 methods with code, 718 methods with target-string references).
- Server Alpha syntax and smoke checks: PASS.
- Server Alpha unit suite: 16 passed after replacing four obsolete grid-hypothesis tests with the corrected texture-probe tests.

## Project status remains bounded

This is static analysis and visual preview only. It does not establish the original gameplay camera projection from screenshots, create a playable map, produce original Dukku art, prove import compatibility, replace the legacy server protocol, or build/sign/install an APK. Keep the master APK read-only and do not revive the cancelled Godot prototype.
