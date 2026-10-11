# Repository Layout

- `assets/catalog/` — machine-readable asset catalog.
- `assets/source/` — editable original asset source files, organized by category.
- `assets/exports/` — generated/exported files awaiting or passing validation.
- `docs/` — project charter, pipeline, technical findings, and decisions.
- `tools/` — repeatable analysis and validation scripts.
- `tests/` — automated guardrail tests.
- `reports/` — audit output with provenance and hashes.
- `.github/workflows/` — automated checks.

Do not commit the master APK, private signing material, credentials, or unrelated project files.
