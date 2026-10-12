# APK Recovery Execution Status — 2026-10-12

## Goal

Produce a separately signed Android test APK that installs and can be tested on a real Android device, while keeping the supplied master APK immutable. The server alpha ZIP is not an APK and must not be represented as one.

## Verified baseline

- Master: `World-Life-0.1-BGM-Fun-In-Kyoto-V2.apk`
- SHA-256: `36727d1a1ac1b5f1e997efe8c312f1de7945bd6d13c91651a2b195e588185ca1`
- ZIP integrity: passed in the prior audit.
- Package/version: `com.nubee.japanlife`, version `0.1` (code 63).
- Launcher: `.GameActivity`.
- Native payload: `lib/armeabi/libKyotoLife.so`, `lib/armeabi/libcurljni.so` (32-bit ARM).
- DEX trace: 26,963 strings, 21,092 methods, 17,821 methods with code, 718 methods with targeted strings. This is static tracing, not a decompiled call graph.
- Existing Dukku server Alpha v1.3 tests passed locally (16 tests), but its `/v1/*` API is not wire-compatible with the legacy game.

## Findings that prevent a safe APK patch today

1. **No Android build chain in the current execution environment.** Java exists, but Android SDK/platform, `aapt`, `apktool`, `d8`, Gradle Android plugin, `zipalign`, and `apksigner` were not found. An attempt to reach the public package host failed because this environment cannot resolve external hosts, so tools cannot be installed here.
2. **No original project source or signing private key.** The APK contains a public signing certificate only. A new build would need a separately documented test signing key and may require uninstalling the original package before installation.
3. **Legacy protocol not reconstructed.** Static DEX strings show `com/nubee/japanlife/HTTPManager`, legacy account-verification flows, old social identity SDKs, payment/receipt-verification code, and multiple historical hosts. String presence alone does not reveal mandatory startup calls or request/response schemas.
4. **No real-device runtime access.** No Android device/emulator is available in this execution environment, so installation, login, map loading, persistence, resume, and crash checks cannot be claimed.

## Safest implementation route

### Gate A — Prepare a controlled Android build environment
- Use a trusted machine/CI runner with Android SDK platform/build-tools, apktool/baksmali (or equivalent), and a 32-bit ARM-capable test device/emulator.
- Keep the master APK read-only and record its checksum before/after every operation.
- Decode the APK into a separate working directory; never overwrite the master.

### Gate B — Trace the real client contract
- Decompile `GameActivity`, `HTTPManager`, login/auth verification callbacks, JNI declarations, and native request dispatch.
- Build a call-site inventory for bootstrap/login, profile, world/map data, save/load, inventory/shop, friends, analytics, and payments.
- Separate mandatory gameplay calls from obsolete social and payment SDK flows. Do not redirect payment/receipt verification or disable login based on string matching alone.
- Capture request and response schemas from bytecode and, where feasible, controlled runtime logs. Do not probe historical hosts with user credentials.

### Gate C — Choose a compatibility strategy
- Preferred: implement a legacy-wire adapter on the Dukku server only after exact schemas and authentication semantics are established; or
- Rebuild the client networking/auth layer against a documented Dukku API if source/bytecode patching is feasible.
- The existing Alpha v1.3 API is not a drop-in replacement and must not be advertised as such.

### Gate D — Produce a test candidate
- Apply a minimal patch set to a copy of the APK.
- Rebuild, align, and sign with a clearly labelled test key. Document that the signer differs from the master.
- Verify archive integrity, manifest, native library ABI, certificate, and SHA-256.
- Install on a real test device and verify: cold launch, sign-up/email verification/owner approval, login rejection states, world/map load, save/reload, shop balance and inventory, app resume, network loss/recovery, and crash logs.
- Release the APK only after these gates pass; include installation steps and known limitations.

## Current status

**APK candidate: NOT BUILT.** This is an environment/toolchain and protocol-evidence blocker, not a passing build. The original master remains unchanged. No fake or placeholder APK should be generated merely to satisfy the file-format expectation.

## What would unblock the next build step

At least one of:
- Access to an Android SDK/build runner with APK decoding/rebuild/signing tools and the master APK mounted privately; or
- The original Android project/source plus its supported build instructions.

A matching original signing keystore is needed only if in-place upgrade identity is required; otherwise use a separate test signing identity and document the uninstall/data-continuity implications. Real-device testing is still required before calling the result playable.
