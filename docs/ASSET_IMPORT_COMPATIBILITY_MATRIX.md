# Asset Import Compatibility Matrix

Status labels: **Observed** = directly verified from bytes/archive; **Hypothesis** = working interpretation; **Blocked** = missing proof/tooling; **Pass** = verified import/runtime result.

| Asset/data family | Observed | Current conclusion | Required next test | Status |
|---|---|---|---|---|
| PNG files | 129 direct PNG entries; dimensions are read from PNG headers | PNG signature confirmed; atlas conventions and world/UI roles are not established | Map files to resource references; record alpha, dimensions, and usage | Observed / Blocked |
| `.smf` wrapper subset | 344 files use `nbc 0100`, little-endian decoded length, and zlib; lengths match | Wrapper pattern confirmed for this subset only | Trace loader call sites; decode representative payload schemas | Observed / Blocked |
| `.smf` direct PNG subset | 26 files have PNG signature | Extension does not identify payload format | Trace resource references and expected loader behavior | Observed / Blocked |
| `.smf` unknown subset | 42 files did not match known signatures | Not classified | Compare headers, sizes, and references; do not rewrite blindly | Blocked |
| `.nbc` | 25 files use wrapper pattern; decoded bytes opaque to signature probe | Container identified, semantics unknown | Identify schema and locale/message table decoder | Observed / Blocked |
| `.ogg` | 21 files have OggS signature | Ogg container confirmed; codec/duration not audited | Use a trusted media probe; identify sound role from code references | Observed / Blocked |
| `mapdata*.smf` | 235 indexed entries 000–234; 122 outer-decode to PNG and 113 to a second NBC wrapper containing `text1000`; all 113 texture-like payloads have 28-byte headers and `width × height × 2` pixel-byte lengths; native code maps header format code `2` to 2 bytes/pixel | Nested texture parser and byte width are observed; channel packing and alpha semantics remain unproven | Trace the native `text1000` decoder and confirm channel packing/alpha; map EFILE indices to package paths and metadata | Observed / Blocked |
| Native `.so` libraries | 2 ARM 32-bit native libraries; focused ARM Thumb disassembly completed for map-data/resource-loader functions | `LoadMapData` reads a resource, decompresses the outer NBC wrapper, checks a 32-byte SHA-256 against index-specific object-display metadata, then caches accepted bytes; the cached data can contain a second NBC-wrapped `text1000` texture | Resolve EFILE/path table, checksum table population/update, and native `text1000` pixel format semantics | Observed / Blocked |
| NBC loader acceptance gate | Native header check validates `nbc 0100`; decoded-size field at offset 8; payload starts at offset 12; SHA-256 comparison follows decompression | Wrapper validity alone is not import compatibility; checksum and resource-index metadata must match | Build a controlled fixture and prove the original runtime accepts it without modifying the master APK | Observed / Blocked |
| Runtime import round-trip | No compatible writer or device runtime test performed | No asset can be called game-ready yet | Import a small fixture into the actual target runtime and capture evidence | Blocked |

## Release rule

Do not label an asset `validated` or `integrated` based only on its extension, successful decompression, or visual preview. Require a known schema, reproducible export settings, provenance/license, import evidence, and runtime validation.
