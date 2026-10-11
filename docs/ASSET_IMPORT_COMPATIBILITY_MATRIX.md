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
| `mapdata*.smf` | 235 named mapdata entries; file sizes vary | Likely map-related based on names only; binary semantics unproven | Trace map loader; compare payloads and decode schema | Hypothesis / Blocked |
| Native `.so` libraries | 2 ARM 32-bit native libraries | Native code may contain loaders/protocol logic | Use ELF/static analysis tooling and map file-access call sites | Blocked |
| Runtime import round-trip | No compatible writer or device runtime test performed | No asset can be called game-ready yet | Import a small fixture into the actual target runtime and capture evidence | Blocked |

## Release rule

Do not label an asset `validated` or `integrated` based only on its extension, successful decompression, or visual preview. Require a known schema, reproducible export settings, provenance/license, import evidence, and runtime validation.
