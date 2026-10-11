# World Life — Dukku Project Status Report

**Report date:** 2026-10-11  
**Repository:** rukitost-png/world-life  
**Branch:** main  
**Scope:** Asset Catalog v0.1, APK asset-format audit, native symbol triage, asset pipeline and release gates.

## Executive summary

The repository and engineering baseline are now in place, and automated checks are passing. The original APK was audited read-only; its ZIP integrity and SHA-256 were verified. Focused native disassembly plus a second-level payload probe now identifies 1,605 nested `text1000` texture records across 113 mapdata streams. The native upload path confirms RGBA4444 (GL_RGBA + GL_UNSIGNED_SHORT_4_4_4_4), with a consistent 28-byte header and a `width × height × 2` byte-size invariant.

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
12. **Nested texture structure** — 235 indexed mapdata resources: 122 decode to PNG and 113 contain concatenated type-2 records, totaling 1,605 nested NBC + `text1000` textures. Native code confirms RGBA4444 uploads; all 1,605 records satisfy the 28-byte-header plus `width × height × 2` invariant. Secondary dimensions, row orientation, and color-space/gamma assumptions remain unresolved. 55 streams also contain trailing bytes beginning with a 2×2 PNG signature; their purpose is unknown. 105 PNG entries share identical 721-byte containers; no per-file payloads were committed.
13. **Repeatable mapdata audit** — the read-only audit tool now parses all 1,605 type-2 texture records across 113 streams and reports aggregate dimensions, RGBA4444 size invariants, index gaps, duplicate container fingerprints, and 55 trailing PNG-signature regions without listing individual resource paths. Regression tests cover multi-record streams, trailing data, index gaps, and duplicate grouping.

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

## Follow-up hardening — 2026-10-11

The parser now preserves malformed first type-2 mapdata records as structured diagnostic output, including invalid record-size and missing-inner-wrapper cases. Regression cases now cover invalid record size, missing inner NBC header, a truncated type-2 record header, and a valid record followed by a malformed record. During review, a classification gap was found and fixed: partially parsed streams can no longer be labeled verified merely because the records parsed before the error satisfy the size invariants. Short type-2 payloads are retained for diagnostics rather than ignored by the initial length guard. The previously recorded passing CI run predates these newest edits; this session could not independently confirm a new workflow run, so the new tests are pending CI confirmation.

## Test status

- Local read-only APK audit: PASS; ZIP integrity passed and no wrapper decompression/declared-size errors were found.
- Second-level mapdata probe: PASS for 113/113 nested wrappers; inner decoded sizes matched, and all 113 `text1000` payloads matched the 28-byte-header plus `width × height × 2` length invariant.
- Focused static disassembly: PASS for the targeted symbol functions; this is static analysis only, not a runtime trace or device test.
- Wrapper unit tests: PASS in local run.
- Latest completed code regression workflow: PASS, run [38147726908](https://github.com/rukitost-png/world-life/actions/runs/38147726908), on commit `9a4f6e96e1fd72939a61102ba29e3393d8809511`. It covers nested texture stream parsing, multiple records, trailing PNG-signature data, and aggregate mapdata audit; subsequent changes were documentation-only.

## Explicit blockers — do not treat these as complete

1. **Legacy data formats:** 42 SMF files remain unclassified, and 108 non-mapdata SMF payloads still fall into the opaque-binary bucket. The 113 mapdata streams are now parsed into 1,605 RGBA4444 texture records, but their offset/index metadata is not yet fully mapped.
2. **Runtime loader path:** focused disassembly confirms the decompression and SHA-256 checksum gate, but the full `EFILE` enum/path table and checksum-table population/update path remain unresolved.
3. **Texture decoder semantics:** RGBA4444 is confirmed, but row orientation, color-space/gamma assumptions, secondary header fields, and the 55 trailing PNG-signature regions remain unresolved.
4. **Camera/scale measurements:** exact projection, zoom range, world units, and object footprint need measurements from reference screenshots/device captures.
5. **Real assets:** catalog records are planning placeholders. No 3D model, texture, UI pack, or audio asset is marked validated or integrated.
6. **Import compatibility:** no custom asset has completed a round-trip through the original runtime.
7. **Android build environment:** apktool, aapt, d8, apksigner, adb, jadx, baksmali, Android SDK, and emulator/device tooling were not available during the audit.
8. **Signing continuity:** the original private signing keystore was not found. A new signing key cannot be assumed to match the original app.
9. **Runtime regression:** login, server, purchase, install/upgrade, and in-game behavior have not been tested with a modified APK.

## Next execution sequence

1. Resolve object-display offsets into the 1,605-record mapdata streams and determine what the 55 trailing PNG-signature regions represent.
2. Trace the expected-checksum table update/patch path before designing any replacement-resource writer.
3. Build a tiny non-production parser/round-trip fixture and test it against a known sample.
4. Measure camera and grid scale from controlled reference captures; then fill the actual unit/axis/pivot fields in the catalog.
5. Produce one original low-risk asset first, with editable source, license/provenance, export settings, and import/runtime evidence.
6. Expand the asset family only after the first asset passes the compatibility gate.
7. Set up a reproducible Android build environment, establish a signing strategy, and run install/regression tests before any APK release.

## Repository visibility note

The GitHub API reported this repository as public during the audit. No master APK, private keystore, or credentials were uploaded. Review visibility before adding any sensitive research data.

## Definition of done

A catalog item is not done until an actual original asset exists, rights/provenance are documented, export settings are reproducible, automated checks pass, import succeeds, and runtime QA evidence is attached. An APK is not done until a reproducible build, signature verification, install test, and regression test are recorded.
