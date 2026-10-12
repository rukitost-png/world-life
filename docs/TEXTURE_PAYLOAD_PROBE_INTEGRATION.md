# Texture Payload Probe Integration

Date: 2026-10-12

## Why this is in the main repository

The validated texture probe existed in the Server Alpha v1.2 package but was not present at the same path in the main `world-life` repository. This change brings a minimal, repeatable, read-only version into the project source tree so future investigations and CI tests can use the same parser rather than relying on a zip-only tool snapshot.

## What it does

- Opens the master APK as a ZIP archive and checks ZIP integrity.
- Reads only `mapdata*.smf` entries; never rewrites the APK.
- Validates the observed NBC wrapper's declared decoded size.
- Parses concatenated type-2 records and checks nested `text1000` dimensions, pixel offset, reserved bytes, and RGBA4444 payload length.
- Writes stream and record CSV inventories plus a JSON summary.
- Keeps malformed records and trailing PNG-signature bytes visible as diagnostics.

## Reproduction

```bash
python tools/texture_payload_probe.py World-Life-0.1-BGM-Fun-In-Kyoto-V2.apk --out reports/texture_payload_probe
python -m unittest discover -s tests -v
```

Expected baseline from the audited master APK: 235 mapdata resources and 1,605 parsed nested texture records. A successful structural audit does not prove that custom textures can be imported by the original runtime.

## Explicit non-goals / unresolved gates

This is not an exporter, checksum-table writer, APK patcher, or proof of runtime compatibility. EFILE mapping, object-display index mapping, expected-checksum update semantics, header field semantics, row orientation, color-space behavior, and Android runtime import tests remain unresolved. Do not put extracted legacy asset payloads into Git.
