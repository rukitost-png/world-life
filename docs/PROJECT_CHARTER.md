# World Life — Dukku: Project Charter

## Goal
Create an organized, verifiable pipeline for original game assets and future integration work, using the supplied Japan Life APK only as a read-only research reference.

## Non-negotiable boundaries
- Preserve the master APK unchanged; never overwrite it.
- Do not reuse unrelated repositories, projects, assets, credentials, or personal data.
- The cancelled Godot prototype is out of scope and must not be reused.
- Never commit secrets, private keys, signing keystores, access tokens, or production credentials.
- Static strings and URLs are evidence for investigation only; they do not prove a live server or reachable runtime call path.
- Every imported asset must have documented provenance and a compatible license.
- A catalog entry marked `not-created` is planning data, not a finished asset.
- Do not claim an APK was built, signed, installed, or tested unless each operation actually succeeded.

## Master APK baseline
- Filename: `World-Life-0.1-BGM-Fun-In-Kyoto-V2.apk`
- Package: `com.nubee.japanlife`
- Version name/code: `0.1` / `63`
- Size: `56,840,959` bytes
- SHA-256: `36727d1a1ac1b5f1e997efe8c312f1de7945bd6d13c91651a2b195e588185ca1`

## Pipeline decision
The original asset import/build format is not yet confirmed. Do not lock the project to Godot or another engine. First establish asset types, dimensions, coordinate conventions, compression, metadata, and a verified import round-trip from the actual target runtime/toolchain.
