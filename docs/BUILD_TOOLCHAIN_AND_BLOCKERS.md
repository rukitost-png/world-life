# Build Toolchain and Remaining Blockers

## Confirmed environment limitations
The analysis environment does not currently have the Android build/decompile toolchain needed to produce a verified modified APK. The following tools were not available during the audit: apktool, aapt, d8, apksigner, adb, jadx, and baksmali. No Android SDK or emulator/device test environment was found.

## Signing continuity
The master APK signing certificate is not the private signing key. The original private keystore was not found. A new keystore can sign a test build, but it cannot be assumed to match the original app's signing identity. Upgrade behavior must be tested before choosing a release package ID and install strategy.

## Engine/runtime decision
Do not create or revive a Godot prototype. Keep the project engine-agnostic while investigating the original native runtime and its asset loaders. A new engine should only be selected after an explicit compatibility and scope decision; it is not a shortcut to making the original APK import custom assets.

## What is completed
- Master APK baseline hash and archive integrity recorded.
- Aggregate read-only asset audit script and report added.
- A subset of SMF and NBC wrapper signatures identified and tested.
- Asset catalog expanded to 17 planning entries across environment, buildings, shops, decoration, vegetation, roads, vehicles, characters, UI, audio, VFX, and map data.
- Automated tests and a GitHub Actions workflow configured.

## What remains blocked
- Full format specification for unknown SMF files and decoded binary payloads.
- Exact EFILE/resource path and checksum-table update semantics; focused loader analysis and texture upload format are now documented.
- Proven export/import round-trip for new assets.
- Original production asset files, camera measurements from controlled gameplay screenshots, and visual review at the verified gameplay camera.
- Android rebuild, signing, installation, and device/runtime testing.

## Exit criteria
An asset is ready only after it has original editable source, documented provenance/license, reproducible export settings, successful format validation, import evidence, and runtime QA. An APK is ready only after a reproducible build, signature verification, installation test, and feature regression tests.


## Corrected nested texture finding (2026-10-12)

The exact master APK was retrieved from the user's Library, hash-verified, and ZIP-tested. Native upload uses GL_RGBA + GL_UNSIGNED_SHORT_4_4_4_4; the 1,605 nested text1000 records are RGBA4444 textures, not established tile grids. A repeatable texture probe and preview report are included in Server Alpha v1.2. This is static-format progress only: checksum-table updates, EFILE mapping, secondary header fields, row orientation, trailing PNG-signature data, camera calibration, import round-trip, Android build/signing, and device testing remain open.
