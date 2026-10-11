# World Life — Dukku Project Status Report

**Report date:** 2026-10-11  
**Repository:** rukitost-png/world-life  
**Branch:** main  
**Scope:** Asset Catalog v0.1, APK asset-format audit, native symbol triage, asset pipeline and release gates.

## Executive summary

The repository and engineering baseline are now in place, and automated checks are passing. The original APK was audited read-only; its ZIP integrity and SHA-256 were verified. Focused native disassembly plus a second-level payload probe now identifies a nested `text1000` texture structure in 113 mapdata resources, including a consistent 28-byte header and a `width × height × 2` byte-size invariant.

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
11. **Native loader disassembly v0.2** — focused ARM Thumb disassembly traced map-data loading through package/external resource lookup, NBC decompression, SHA-256 checksum validation, and indexed cache acceptance. The checksum comes from indexed object-display metadata; the EFILE path table and checksum update source remain unresolved.
12. **Nested texture structure** — 235 indexed mapdata resources: 122 decode to PNG and 113 contain a second NBC wrapper that decompresses to `text1000`. All 113 have a 28-byte header and exactly `width × height × 2` bytes after the header. This supports a raw 16-bpp texture hypothesis, but channel packing, alpha behavior, and other header semantics are not yet confirmed. 105 PNG entries share identical 721-byte containers; no per-file payloads were committed.
13. **Repeatable mapdata audit** — the read-only audit tool now detects nested NBC + `text1000` texture payloads and reports aggregate dimensions, size invariants, index gaps, decoded-type counts, and duplicate container fingerprints without listing individual resource paths. Regression tests cover nested texture recognition, index gaps, and duplicate grouping.

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
- docs/NATIVE_LOADER_DISASSEMBLY_FINDINGS_v0.2.md — focused native loader disassembly, checksum gate, and nested texture structure
- docs/BUILD_TOOLCHAIN_AND_BLOCKERS.md — environment and signing blockers
- docs/QA_RELEASE_CHECKLIST.md — release acceptance checklist
- docs/REPOSITORY_LAYOUT.md — folder plan
- assets/catalog/asset-catalog-v0.1.json — 17 planning entries
- assets/catalog/asset-catalog.schema.json — catalog schema
- tools/audit_apk_assets.py — read-only APK audit utility
- reports/apk_asset_inventory_metadata.json — aggregate metadata report without per-file paths
- tests/test_asset_catalog.py — catalog guardrail tests
- reports/apk_mapdata_resource_probe.json — aggregate indexed mapdata coverage and duplicate fingerprint summary
- tests/test_apk_asset_audit.py — wrapper-signature and aggregate mapdata-audit unit tests
- .github/workflows/guardrails.yml — automated test workflow
- .gitignore — ignores APKs, signing material, secrets, and build artifacts

## Test status

- Local read-only APK audit: PASS; ZIP integrity passed and no wrapper decompression/declared-size errors were found.
- Second-level mapdata probe: PASS for 113/113 nested wrappers; inner decoded sizes matched, and all 113 `text1000` payloads matched the 28-byte-header plus `width × height × 2` length invariant.
- Focused static disassembly: PASS for the targeted symbol functions; this is static analysis only, not a runtime trace or device test.
- Wrapper unit tests: PASS in local run.
- Latest completed regression workflow: PASS, run [38147221058](https://github.com/rukitost-png/world-life/actions/runs/38147221058), on commit `4fe8aad6863a2d261b7095e4e38395afbc83d090`. It covers the nested texture parser and aggregate mapdata audit; later documentation/report updates also trigger the same guardrail workflow.

## Explicit blockers — do not treat these as complete

1. **Legacy data formats:** the 42 unclassified SMF files and the opaque decoded binary payloads still need schema analysis.
2. **Runtime loader path:** focused disassembly confirms the decompression and SHA-256 checksum gate, but the full `EFILE` enum/path table and checksum-table population/update path remain unresolved.
3. **Texture decoder semantics:** the `text1000` payload size invariant strongly suggests 16-bpp pixels, but channel packing, alpha behavior, color space, row orientation, and the meaning of secondary header fields still require native decoder analysis.
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
