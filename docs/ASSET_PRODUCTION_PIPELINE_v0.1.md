# Asset Production Pipeline v0.1

This pipeline remains engine-agnostic until the target runtime and original asset formats are verified.

## Stages

1. **Reference and specification**
   - Record the asset's in-game role, camera visibility, approximate footprint, visual style, and performance budget.
   - Use the APK as a read-only reference. Do not republish extracted copyrighted assets as newly created work.
2. **Asset brief**
   - Assign a stable catalog ID and create a short brief.
   - Specify silhouette, dimensions, pivot/origin, collision intent, texture resolution, LOD needs, and dependencies.
3. **Original production**
   - Create new geometry, textures, audio, UI, or effects.
   - Store editable source separately from exported game files.
4. **Export**
   - Use an interchange format only when useful (for example PNG, WAV, or glTF); do not call it runtime-compatible until import is verified.
   - Record tool/version, scale, axis orientation, texture color space, compression, and export settings.
5. **Format-specific export gate (legacy map textures, experimental only)**
   - Static analysis has identified an outer NBC wrapper, an inner NBC wrapper, and a `text1000` texture payload with a 28-byte header. Native code maps header format code `2` to 2 bytes per pixel.
   - Do not produce release assets from this partial specification: channel packing, alpha behavior, color space, row orientation, secondary header fields, and the resource-index/checksum update path remain unresolved.
   - The native loader checks SHA-256 over the first decompressed resource buffer against index-specific object-display metadata. A wrapper that decompresses successfully is not enough.
6. **Automated validation**
   - Check file existence, naming and ID uniqueness, dimensions, size limits, and required metadata.
   - Verify provenance and license fields.
7. **Import round-trip**
   - Import into the actual target runtime/toolchain.
   - Confirm materials, texture orientation, scale, pivots, animation, and collision.
8. **Visual and runtime QA**
   - Review at the intended gameplay camera and device aspect ratio.
   - Check draw calls, memory, loading time, and lower-end device behavior where possible.
9. **Integration and release**
   - Mark an asset `integrated` only after runtime verification.
   - Attach evidence: screenshots/video, test log, version/hash, reviewer, and date.

## Naming convention
`<CATEGORY>-<4-digit ID>_<short_snake_case_name>.<ext>`

Examples:
- `BLD-0001_small_residential_facade.blend`
- `BLD-0001_small_residential_facade.glb`
- `SHP-0001_convenience_storefront.png`

## Catalog status meanings
- `planned`: brief/spec exists; production has not started.
- `in-production`: source work is underway.
- `review`: export is awaiting review.
- `validated`: file and import checks passed.
- `integrated`: runtime test confirms it is in the game.
- `blocked`: a dependency or toolchain prevents progress.
- `rejected`: failed review or incompatible license/quality.
- `not-created`: explicit placeholder only; no asset file exists.

## Acceptance gate
An asset cannot be marked `validated` or `integrated` without a real file, provenance/license evidence, reproducible export settings, and corresponding validation evidence.
