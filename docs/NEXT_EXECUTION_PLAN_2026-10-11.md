# Next Execution Plan — Legacy Map/Texture Compatibility

Date: 2026-10-11
Status: investigation plan; no runtime compatibility claim

## Purpose

Convert the current static-analysis findings into a controlled, falsifiable investigation. Keep the master APK read-only and do not produce replacement resources until the object-display index, resource lookup, and checksum metadata are understood.

## Verified baseline carried forward

- Master APK SHA-256: `36727d1a1ac1b5f1e997efe8c312f1de7945bd6d13c91651a2b195e588185ca1`.
- 235 indexed `mapdataNNN.smf` entries were observed.
- 122 outer-decompressed resources contain PNG payloads; 105 have byte-identical 721-byte wrappers. Identity is not proof that these are unused.
- 113 resources contain 1,605 type-2 records with nested NBC wrappers and `text1000` payloads.
- Each parsed texture has a 28-byte header and a pixel length consistent with width × height × 2.
- Native texture upload uses RGBA + UNSIGNED_SHORT_4_4_4_4.
- `CObjTexManager::LoadMapData(int)` decompresses a resource and compares SHA-256 of the decoded buffer against index-specific object-display metadata before caching it.
- Unknowns remain: resource path mapping, checksum-table population/update, record-to-object mapping, secondary header fields, row orientation, color-space assumptions, and trailing PNG-signature data.

## Progress note — 2026-10-11 follow-up

- Hardened the read-only parser so malformed first type-2 records remain structured diagnostic results.
- Added synthetic regression cases for invalid record size, missing inner NBC header, and a valid record followed by a malformed record.
- Found and fixed a classification gap: a stream with at least one valid texture followed by a malformed record could previously be labeled verified if the valid records satisfied the size invariants. Classification now also requires `record_error` to be absent.
- The latest code/test edits are committed, but no passing CI result has been independently observed for these commits in this session. Local GitHub access is unavailable, so treat these tests as **added but pending execution/CI confirmation**.
- WP4 remains partial: synthetic malformed-record diagnostics are improved, but a complete synthetic round-trip fixture and validation against the original runtime are not done.

## Work packages

### WP1 — Map resource index to display metadata

1. Trace `CObjectDataManager::Initialize()` from its calls to `CBin2CSV::Initialize(EFILE)` through typed field reads and checksum-array allocation.
2. Identify the enum values and path table that map each `EFILE` to package, external, save-data, or patch resources.
3. Record the exact input file/table and field order that populates each mapdata checksum.
4. Produce a compact evidence table: function/address, observed read, inferred field, confidence, and unresolved alternatives.
5. Do not edit the APK or generate a replacement checksum table during this work package.

**Acceptance:** the resource filename/index and checksum source are linked by direct code-path evidence, not merely matching strings.

### WP2 — Resolve type-2 record indexing

1. Trace callers that consume the parsed texture record stream and identify whether records are addressed sequentially or via a separate offset/index table.
2. Correlate one representative object-display entry with a mapdata resource index and one record boundary.
3. Expand to at least three independent examples, including a stream with multiple records.
4. Keep aggregate-only reporting; avoid committing extracted copyrighted payloads or per-resource content dumps.

**Acceptance:** at least three examples map display metadata to record offsets deterministically, with no unexplained off-by-one or bounds errors.

### WP3 — Characterize texture semantics safely

1. Decode only synthetic RGBA4444 test patterns first (distinct corner colors, alpha ramps, row markers) to test candidate channel ordering and row orientation.
2. Treat header fields at offsets 12–19 as unknown until evidence supports semantics; do not rename them as confirmed fields.
3. Compare declared dimensions, content dimensions, and pixel payload lengths across the aggregate audit.
4. Investigate the 55 trailing regions beginning with a PNG signature by documenting their boundaries and byte-level structure; do not assume they are standalone PNG files because bytes follow IEND.
5. Document gamma/color-space assumptions as unknown unless native code or controlled rendering confirms them.

**Acceptance:** each interpretation is backed by either native code evidence or a reproducible synthetic fixture. Unknowns stay explicitly unknown.

### WP4 — Build a non-production parser fixture

1. Add synthetic test fixtures created from scratch; do not include original APK payloads.
2. Test nested wrapper bounds, record-size boundaries, declared decompressed sizes, header minimum length, truncation, and trailing data.
3. Round-trip only synthetic data through any candidate writer/reader.
4. Do not attempt original-runtime injection until WP1–WP3 identify the full validation requirements.

**Acceptance:** automated tests pass for valid and malformed fixtures; no claim of original-runtime compatibility is made.

### WP5 — Camera and scale reference

1. Capture the reference app at a fixed resolution/orientation using an authorized test environment.
2. Measure at least three object classes across at least two zoom states.
3. Record screenshot hash, viewport size, visible grid count, object pixel bounds, estimated footprint, and confidence.
4. Use these measurements for original blockout assets only; do not copy source meshes, textures, logos, or audio.

**Acceptance:** camera/scale parameters are supported by multiple samples. Until then, world units, projection, axes, and final export settings remain TBD.

## Stop conditions

Stop and document a blocker if the needed binary, authorized reference capture, toolchain, or runtime cannot be accessed. Do not infer success from symbol names, decompression, matching dimensions, or CI passing.

## Release gates unchanged

No catalog item may be marked `validated` or `integrated` without a real original asset, provenance/license, reproducible export settings, import evidence, and runtime QA. No modified APK may be described as built, signed, installed, or tested unless those operations actually succeeded.
