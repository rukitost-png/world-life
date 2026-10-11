# QA and Release Checklist

## Project integrity
- [ ] Master APK filename, byte size, and SHA-256 match the recorded baseline.
- [ ] Master APK remains read-only; no rebuilt artifact replaces it.
- [ ] No unrelated project files, cancelled Godot prototype artifacts, credentials, keystores, or tokens were added.
- [ ] Review public exposure before publishing research metadata.

## Asset provenance
- [ ] Every asset has a stable catalog ID and category.
- [ ] Source/provenance and license are recorded and compatible with distribution.
- [ ] Editable source and exported runtime file are tracked where appropriate.
- [ ] Scale, axes, pivot, texture/color space, compression, dimensions, and dependencies are recorded.
- [ ] Planned/not-created entries have no fake file path and are not presented as deliverables.

## Technical validation
- [ ] Catalog JSON parses; IDs are unique; required fields exist.
- [ ] Automated unit tests pass.
- [ ] Export/import format is supported by evidence, not guessed from an extension.
- [ ] A known-good sample round-trips through format tooling.
- [ ] Runtime/device import test passes with logs and screenshots attached.
- [ ] Memory, loading time, texture size, draw calls, and lower-end device constraints are reviewed.

## Android package release
- [ ] Build toolchain and target SDK are explicitly recorded.
- [ ] APK is built from known source and build steps are reproducible.
- [ ] Signing certificate is documented; do not claim a new key matches the original private key.
- [ ] APK signature verification passes.
- [ ] Install/upgrade behavior is tested; package ID/signature compatibility is understood.
- [ ] Login, network, purchase, and legacy-server dependencies are documented and tested independently.
- [ ] Final APK SHA-256, version, test matrix, known limitations, and rollback plan are recorded.

## Current release gate

**NOT READY:** original import-format semantics, native loader call paths, compatible build toolchain, signing continuity, and runtime/device tests remain unverified.
