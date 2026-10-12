# Server Alpha v1.3 — implementation and release status

Updated: 2026-10-12

## Scope delivered in the source package

The companion source package `World_Life_Dukku_Server_Alpha_v1.3.zip` extends the Dukku backend prototype with:

- Owner browser console at `/admin-panel`, including applicant approval/rejection, shop catalog maintenance, and audit-log viewing.
- Persistent server-owned shop catalog with owner-only create/update/disable/delete operations.
- Public enabled-only catalog endpoint: `GET /v1/game/catalog`.
- Authenticated purchase endpoint: `POST /v1/game/shop/purchase`, with server-side balance validation, inventory updates, audit records, bounded quantities, and per-user request-ID replay protection.
- Owner-only purchase history endpoint: `GET /v1/admin/shop-purchases`.
- Startup refusal when `JWT_SECRET` is missing or shorter than 32 characters.
- SQLite integration coverage for account verification/approval, gameplay save/load, owner-only shop management, catalog visibility, purchase balance deduction, idempotent retries, and the admin panel.

## Local verification performed

- `python -m compileall -q auth tests tools`: PASS.
- `python tests/smoke_check.py`: PASS.
- `python tests/test_api_integration_local.py`: PASS (isolated SQLite; test-only auth/OIDC fallbacks when optional libraries are unavailable).
- `python -m pytest -q`: 16 passed.
- Master APK reverified read-only: 56,840,959 bytes, SHA-256 `36727d1a1ac1b5f1e997efe8c312f1de7945bd6d13c91651a2b195e588185ca1`; ZIP integrity PASS.

## Important boundaries

This is not a completed game release. The legacy APK is kept unchanged. The new API is not yet wire-compatible with the original Japan Life client; no modified APK has been built, signed, installed, or tested. Android SDK/build tools and the original signing private key were not available in the build environment. No production server/domain, SMTP account, Google OAuth client, or production secrets are configured.

Before a public launch: deploy behind HTTPS, configure real secrets and email/OIDC, run PostgreSQL and multi-worker concurrency tests, add operational monitoring/backups/rate limiting and formal DB migrations, then implement and verify the legacy-client adapter or a rebuilt Android client. Do not point the legacy APK at these endpoints until compatibility is proven.
