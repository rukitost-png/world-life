# World Life — Dukku Project Status Report

**Report date:** 2026-10-13  
**Goal:** restore and extend the original Android game using the master APK as a read-only reference; do not restart the cancelled Godot prototype.

## Executive status

The legacy asset investigation has reached a repeatable static-format baseline. The original APK's Java/Dex resource index, native EFILE filename table, and APK archive entries are now cross-referenced. All 235 mapdata SHA-256 entries validate against their decoded streams, and the airport texture-offset table validates 84 concatenated PNG images.

**The game is not yet ready for an APK test build.** No modified APK has been rebuilt, signed, installed, or run. The current workspace has no Android build toolchain or original private signing key. Server Alpha v1.3 is a backend prototype, not a working drop-in backend for the original client.

## Confirmed evidence

| Area | Verified result | Source |
|---|---|---|
| Master APK integrity | ZIP structure checked; SHA-256 `36727d1a1ac1b5f1e997efe8c312f1de7945bd6d13c91651a2b195e588185ca1` | Master APK, read-only |
| Native library | `lib/armeabi/libKyotoLife.so`, 32-bit ARM | APK archive |
| EFILE/resource map | 442/442 EFILE indices mapped through DEX `R.raw` values to unique APK raw-resource entries | [v0.6 map](../docs/NATIVE_LOADER_EFILE_RESOURCE_MAP_v0.6.md) |
| Package resource offsets | Java obtains `AssetFileDescriptor.getStartOffset()` and `getLength()` and passes them through `SetResourceOffset` to native code | v0.6 static trace |
| Mapdata checksums | 235/235 SHA-256 entries match full decoded NBC streams; zero mismatches/missing files | [v0.7 audit](../docs/NATIVE_LOADER_MAPDATA_CHECKSUM_AUDIT_v0.7.md) |
| Airport images | 84 offsets point to concatenated PNGs; all image boundaries validate | v0.7 audit |
| Nested texture payloads | 1,605 texture records structurally validated across 113 resources; RGBA4444 interpretation is supported by prior native texture-upload analysis | [Texture findings v0.3](../docs/MAPDATA_TEXTURE_FINDINGS_v0.3.md) |
| Server Alpha | v1.3 prototype has owner console, application review, shop CRUD, server-side purchase checks, and 16 local integration tests | [Server status](SERVER_ALPHA_V1.3_IMPLEMENTATION_STATUS.md) |

## Main-branch research changes

The following pull requests were merged into `main` after their CI checks succeeded:

- PR #7 — [EFILE offset audit and patch-validation trace](https://github.com/rukitost-png/world-life/pull/7)
- PR #8 — [Exact DEX resource-ID mapping for all 442 EFILE indices](https://github.com/rukitost-png/world-life/pull/8)
- PR #9 — [Mapdata checksum and airport PNG-offset validation](https://github.com/rukitost-png/world-life/pull/9)

The tools are read-only and do not alter the master APK:
- `tools/audit_efile_resources.py`
- `tools/audit_efile_dex_mapping.py`
- `tools/audit_mapdata_checksums.py`

Run repository tests with `python -m unittest discover -s tests -v`.

## Remaining technical work, in order

1. **Finish the maptexinfo tail schema.** The bytes after the 7,524-byte checksum table are consumed by native initialization to populate 44-byte object-display records and variable arrays. They are not padding and must not be truncated. Record field semantics and their relation to nested texture streams are not yet fully decoded.
2. **Close the texture-index cross-check.** Validate the object-display index, the `CObjTexManager::LoadMapData(int)` argument, EFILE resource index, and checksum-array index against the same observed records before attempting any resource replacement.
3. **Establish a reproducible Android build environment.** Available analysis environment lacks `gradle`, `adb`, `apktool`, `aapt`, `apksigner`, `d8`, `jadx`, and `baksmali`. The user has only a phone, so this needs a controlled private CI workflow or a trusted remote build environment.
4. **Make the master APK available to that private workflow.** Keep the APK and any signing material private. Do not commit a production signing key, access token, or credentials.
5. **Resolve the client/backend protocol.** Server Alpha is not yet proven compatible with the original client. Identify the actual login, inventory, shop, purchase, and save endpoints/protocol from the APK before enabling any client-facing service.
6. **Build and test a candidate APK.** Only after the prior gates: rebuild, align, sign, install on a compatible ARM Android device, smoke-test launch/login/map rendering/shop/save, and verify that the untouched master APK remains recoverable.

## Release gates and honesty policy

- No custom asset import is considered compatible solely because its file extension or pixel format looks correct.
- No server compatibility is claimed until the original client protocol is proven.
- No APK build, signing, installation, login, rendering, purchase, or save success is claimed until observed on a device.
- The master APK remains read-only. No game assets or executable payloads were committed to this repository.
