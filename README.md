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
- [Camera and Scale Study](docs/CAMERA_AND_SCALE_STUDY.md)
- [Asset Brief Template](docs/ASSET_BRIEF_TEMPLATE.md)
- [Catalog JSON Schema](assets/catalog/asset-catalog.schema.json)
- [Repository Layout](docs/REPOSITORY_LAYOUT.md)
- [Consolidated Project Status Report](reports/PROJECT_STATUS_2026-10-11.md)
- [Next Execution Plan — Legacy Map/Texture Compatibility](docs/NEXT_EXECUTION_PLAN_2026-10-11.md)

## Current status
The catalog contains 17 planning entries. They are not finished or importable game assets. The master APK has now been re-verified from the Library and the nested text1000 payloads are confirmed as RGBA4444 textures, not established tile grids. Import compatibility and Android runtime readiness remain unproven.

## Project boundaries
- Keep the master APK unchanged and treat it as a read-only reference.
- Do not reuse unrelated projects or the cancelled Godot prototype.
- Do not commit secrets or private signing material.
- Record asset provenance and license before import.
- Never claim build, signing, installation, or runtime tests that have not actually succeeded.

## Tools
- tools/audit_apk_assets.py generates aggregate APK metadata and probes known signatures without extracting archive members.
- Run automated checks with: python -m unittest discover -s tests -v.

## Automated checks
GitHub Actions runs the test suite on pushes, pull requests, and manual dispatch.


## Corrected texture probe (2026-10-12)

- Recovered and reverified the exact master APK from ChatGPT Library; SHA-256 and ZIP integrity match the immutable baseline.
- Native texture-upload evidence plus visual previews corrects the previous grid/cell hypothesis: 1,605 nested text1000 records are RGBA4444 textures across 113 resources.
- See [Nested Texture Findings v0.3](docs/MAPDATA_TEXTURE_FINDINGS_v0.3.md) for dimensions, header observations, statistics, and unresolved import gates.
- Server Alpha v1.2 has a corrected probe, per-record CSV, preview sheet, and passing local unit/smoke checks. No new Dukku asset has been runtime-integrated; no modified APK has been built.
