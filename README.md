# World Life — Dukku

Repository baseline for original game assets, a repeatable asset-production pipeline, and project guardrails.

## Start here
- [Project Charter](docs/PROJECT_CHARTER.md)
- [Asset Production Pipeline v0.1](docs/ASSET_PRODUCTION_PIPELINE_v0.1.md)
- [Repository Layout](docs/REPOSITORY_LAYOUT.md)
- [Asset Catalog v0.1](assets/catalog/asset-catalog-v0.1.json)

## Current status
The catalog contains planning placeholders only. They are not finished or importable game assets. The target runtime and import format must be verified before compatibility can be claimed.

## Project boundaries
- Keep the master APK unchanged and treat it as a read-only reference.
- Do not reuse unrelated projects or the cancelled Godot prototype.
- Do not commit secrets or private signing material.
- Record asset provenance and license before import.
- Never claim build, signing, installation, or runtime tests that have not actually succeeded.

## Automated checks
GitHub Actions runs the asset catalog guardrail tests on pushes, pull requests, and manual dispatch.
