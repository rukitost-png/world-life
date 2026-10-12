# World Life — Dukku

Repository baseline for original game assets, read-only APK format research, and repeatable project guardrails.

## Start here
- [Project Charter](docs/PROJECT_CHARTER.md)
- [Asset Production Pipeline v0.1](docs/ASSET_PRODUCTION_PIPELINE_v0.1.md)
- [Asset Catalog v0.1](assets/catalog/asset-catalog-v0.1.json)
- [APK Asset Format Findings](docs/APK_ASSET_FORMAT_FINDINGS.md)
- [Nested Texture Findings v0.3](docs/MAPDATA_TEXTURE_FINDINGS_v0.3.md)
- [Asset Import Compatibility Matrix](docs/ASSET_IMPORT_COMPATIBILITY_MATRIX.md)
- [QA and Release Checklist](docs/QA_RELEASE_CHECKLIST.md)
- [Build Toolchain and Blockers](docs/BUILD_TOOLCHAIN_AND_BLOCKERS.md)
- [Native Runtime Symbol Triage](docs/NATIVE_RUNTIME_SYMBOL_TRIAGE.md)
- [Native Loader EFILE Filename Map v0.4](docs/NATIVE_LOADER_EFILE_FILENAME_MAP_v0.4.md)
- [Native Loader EFILE Resource Audit v0.5](docs/NATIVE_LOADER_EFILE_RESOURCE_AUDIT_v0.5.md) — basename-only preliminary audit, superseded by v0.6\n- [Native Loader EFILE Resource Map v0.6](docs/NATIVE_LOADER_EFILE_RESOURCE_MAP_v0.6.md)\n- [Native Loader Mapdata Checksum Audit v0.7](docs/NATIVE_LOADER_MAPDATA_CHECKSUM_AUDIT_v0.7.md)
- [Native Loader Checksum Trace v0.3](docs/NATIVE_LOADER_CHECKSUM_TRACE_v0.3.md) — earlier record with a superseding mapping note
- [Camera and Scale Study](docs/CAMERA_AND_SCALE_STUDY.md)
- [Asset Brief Template](docs/ASSET_BRIEF_TEMPLATE.md)
- [Catalog JSON Schema](assets/catalog/asset-catalog.schema.json)
- [Repository Layout](docs/REPOSITORY_LAYOUT.md)
- [Consolidated Project Status Report](reports/PROJECT_STATUS_2026-10-11.md)\n- [Consolidated Project Status Report — 2026-10-13](reports/PROJECT_STATUS_2026-10-13.md)
- [Next Execution Plan — Legacy Map/Texture Compatibility](docs/NEXT_EXECUTION_PLAN_2026-10-11.md)
- [Server Alpha v1.3 Implementation Status](reports/SERVER_ALPHA_V1.3_IMPLEMENTATION_STATUS.md)

## Current status
The asset catalog remains a planning catalog, not a finished asset pack. The master APK has been re-verified read-only and nested text1000 payloads are confirmed as RGBA4444 textures, not established tile grids. Server Alpha v1.3 adds an owner console, applicant review, shop catalog CRUD, server-side purchase checks, and local integration tests; see the implementation status report. The legacy game client is not yet compatible with the new server, and no modified APK has been built or tested.

## Project boundaries
- Keep the master APK unchanged and treat it as a read-only reference.
- Do not reuse unrelated projects or the cancelled Godot prototype.
- Do not commit secrets or private signing material.
- Record asset provenance and license before import.
- Never claim build, signing, installation, or runtime tests that have not actually succeeded.

## Tools
- `tools/audit_apk_assets.py` generates aggregate APK metadata and probes known signatures without extracting archive members.
- `tools/audit_efile_resources.py` cross-references native EFILE logical names with conservative APK resource-name candidates.\n- `tools/audit_efile_dex_mapping.py` joins native EFILE indices to the DEX `R.raw` IDs and exact APK resource entries for the master build.\n- `tools/audit_mapdata_checksums.py` verifies the decoded mapdata SHA-256 table and the airport concatenated-PNG offset table.
- Run automated checks with: `python -m unittest discover -s tests -v`.

## Automated checks
GitHub Actions runs the test suite on pushes, pull requests, and manual dispatch.

## Corrected texture probe (2026-10-12)

- Recovered and reverified the exact master APK from ChatGPT Library; SHA-256 and ZIP integrity match the immutable baseline.
- Native texture-upload evidence plus visual previews corrects the previous grid/cell hypothesis: 1,605 nested text1000 records are RGBA4444 textures across 113 resources.
- See [Nested Texture Findings v0.3](docs/MAPDATA_TEXTURE_FINDINGS_v0.3.md) for dimensions, header observations, statistics, and unresolved import gates.
- Server Alpha v1.3 extends the backend prototype with an owner console and server-side shop prototype. Its local SQLite integration and 16-test suite pass, but PostgreSQL concurrency, production deployment, legacy protocol compatibility, and APK rebuild/runtime testing remain open release gates.
