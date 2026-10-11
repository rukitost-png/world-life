# World Life — Dukku Project Status Report

**Report date:** 2026-10-11  
**Repository:** rukitost-png/world-life  
**Branch:** main  
**Scope:** Asset Catalog v0.1, APK asset-format audit, native symbol triage, asset pipeline and release gates.

## Executive summary

The repository and engineering baseline are now in place, and automated checks are passing. The original APK was audited read-only; its ZIP integrity and SHA-256 were verified. The audit identifies a subset of compressed asset wrappers and confirms that the file extensions do not reliably describe payload types.

This is a **technical baseline and planning milestone, not a completed game build**. No new asset has yet passed import/runtime validation, and no modified APK has been built, signed, installed, or tested. Those steps remain blocked by incomplete legacy format semantics and missing Android build/device tooling.

## Completed and verified

1. **Repository write access** — successfully created and updated files in the GitHub repository.
2. **Project guardrails** — master APK is designated read-only; unrelated projects and the cancelled Godot prototype are out of scope; secrets and signing material must not be committed.
3. **Asset Catalog v0.1** — 17 stable planning entries cover environment, buildings, shops, decoration, vegetation, roadside, vehicle, character, UI, audio, VFX, and map data. Every entry is marked not-created until a real asset exists and passes the acceptance gates.
4. **Catalog schema** — JSON Schema file added to document catalog structure.
5. **Asset pipeline** — production, export, provenance, validation, import round-trip, visual QA, runtime QA, and release stages documented.
6. **Read-only APK audit tool** — aggregate report generator added. It reads the archive, checks ZIP integrity, checks selected signatures, probes wrapper decompression, and does not extract archive members to disk.
7. **Format findings** — the tested APK has 641 file entries (670 ZIP entries including directory records), including 412 SMF, 129 PNG, 25 NBC, and 21 OGG files.
8. **Wrapper probe** — 344 SMF files matched the NBC-0100 + little-endian size + zlib pattern with matching decoded sizes; 26 SMF files were direct PNG data; 42 SMF files remain unclassified. All 25 NBC files matched the wrapper pattern. No wrapper decompression failures or decoded-size mismatches were observed.
9. **Native symbol triage** — the ARM library exports map, object-placement, coordinate conversion, zoom, render, texture loading, and map-load-related symbols. This is symbol evidence, not a full decompilation or runtime call trace.
10. **Automation** — catalog and wrapper tests are present; the latest GitHub Actions run passed.
11. **Native loader disassembly v0.2** — focused ARM Thumb disassembly traced map-data loading through package/external resource lookup, NBC decompression, SHA-256 checksum validation, and indexed cache acceptance. It also confirmed native map coordinate conversion functions; exact grid constants and the EFILE path table remain unresolved.
12. **Mapdata resource coverage** — 235 indexed `res/raw/mapdataNNN.smf` entries (000–234); 105 share one identical 721-byte wrapper/decoded PNG, and 130 are larger/non-placeholder by file size. No payload was committed.

## Source APK baseline

- Filename: World-Life-0.1-BGM-Fun-In-Kyoto-V2.apk
- Size: 56,840,959 bytes
- SHA-256: 36727d1a1ac1b5f1e997efe8c312f1de7945bd6d13c91651a2b195e588185ca1
- ZIP integrity: PASS
- Package: com.nubee.japanlife
- Version: 0.1, versionCode 63

The master APK has not been modified or committed to this repository.

## Repository deliverables

- README.md — entry point and project links
- docs/PROJECT_CHARTER.md — scope and non-negotiable guardrails
- docs/ASSET_PRODUCTION_PIPELINE_v0.1.md — asset pipeline stages
- docs/ASSET_BRIEF_TEMPLATE.md — reusable production brief
- docs/CAMERA_AND_SCALE_STUDY.md — protocol for measuring the reference camera and object scale
- docs/APK_ASSET_FORMAT_FINDINGS.md — archive and wrapper probe results
- docs/ASSET_IMPORT_COMPATIBILITY_MATRIX.md — observed, hypothesized, and blocked formats
- docs/NATIVE_RUNTIME_SYMBOL_TRIAGE.md — native symbol/string evidence
- docs/NATIVE_LOADER_DISASSEMBLY_FINDINGS_v0.2.md — focused native loader disassembly and checksum gate
- docs/BUILD_TOOLCHAIN_AND_BLOCKERS.md — environment and signing blockers
- docs/QA_RELEASE_CHECKLIST.md — release acceptance checklist
- docs/REPOSITORY_LAYOUT.md — folder plan
- assets/catalog/asset-catalog-v0.1.json — 17 planning entries
- assets/catalog/asset-catalog.schema.json — catalog schema
- tools/audit_apk_assets.py — read-only APK audit utility
- reports/apk_asset_inventory_metadata.json — aggregate metadata report without per-file paths
- tests/test_asset_catalog.py — catalog guardrail tests
- tests/test_apk_asset_audit.py — wrapper-signature unit tests
- .github/workflows/guardrails.yml — automated test workflow
- .gitignore — ignores APKs, signing material, secrets, and build artifacts

## Test status

- Local read-only APK audit: PASS; ZIP integrity passed and no wrapper decompression/declared-size errors were found.
- Focused static disassembly: PASS for the targeted symbol functions; this is static analysis only, not a runtime trace or device test.
- Wrapper unit tests: PASS in local run.
- Latest GitHub Actions workflow: PASS. The run completed successfully on the current repository head.

## Explicit blockers — do not treat these as complete

1. **Legacy data formats:** the 42 unclassified SMF files and the opaque decoded binary payloads still need schema analysis.
2. **Runtime loader path:** focused disassembly now confirms the decompression and SHA-256 checksum gate, but the full `EFILE` enum/path table and checksum-table population/update path remain unresolved.
3. **Camera/scale measurements:** exact projection, zoom range, world units, and object footprint need measurements from reference screenshots/device captures.
4. **Real assets:** catalog records are planning placeholders. No 3D model, texture, UI pack, or audio asset is marked validated or integrated.
5. **Import compatibility:** no custom asset has completed a round-trip through the original runtime.
6. **Android build environment:** apktool, aapt, d8, apksigner, adb, jadx, baksmali, Android SDK, and emulator/device tooling were not available during the audit.
7. **Signing continuity:** the original private signing keystore was not found. A new signing key cannot be assumed to match the original app.
8. **Runtime regression:** login, server, purchase, install/upgrade, and in-game behavior have not been tested with a modified APK.

## Next execution sequence

1. Use ARM-aware disassembly or a suitable Android reverse-engineering toolchain to trace map and texture loading.
2. Identify the schema for one representative map record and one texture/object record without rewriting the master APK.
3. Build a tiny non-production parser/round-trip fixture and test it against a known sample.
4. Measure camera and grid scale from controlled reference captures; then fill the actual unit/axis/pivot fields in the catalog.
5. Produce one original low-risk asset first, with editable source, license/provenance, export settings, and import/runtime evidence.
6. Expand the asset family only after the first asset passes the compatibility gate.
7. Set up a reproducible Android build environment, establish a signing strategy, and run install/regression tests before any APK release.

## Repository visibility note

The GitHub API reported this repository as public during the audit. No master APK, private keystore, or credentials were uploaded. Review visibility before adding any sensitive research data.

## Definition of done

A catalog item is not done until an actual original asset exists, rights/provenance are documented, export settings are reproducible, automated checks pass, import succeeds, and runtime QA evidence is attached. An APK is not done until a reproducible build, signature verification, install test, and regression test are recorded.
