# Camera and Scale Study Plan

## Objective
Match the broad camera readability and object scale of the reference experience while creating original assets. The exact projection, tilt, zoom range, world units, and screen-space scale are not yet certified.

## Evidence available
The native library exposes map coordinate conversion, map index, map render, zoom-factor, and map-size symbols. These suggest a dedicated native map/rendering path, but do not by themselves establish the exact camera projection or world coordinate units.

## Measurement protocol
1. Capture the reference app at fixed device resolution and orientation, using an authorized test environment.
2. Record viewport dimensions, visible grid width/height, and the pixel footprint of several stable objects.
3. Repeat at minimum, default, and maximum zoom if those states are available.
4. Measure object footprints in grid cells and screen pixels; keep a sample table with screenshot hash and capture date.
5. Distinguish screen-space UI sprites from world-space textures and object geometry.
6. Record projection class only after observing multiple surfaces/edges and confirming perspective behavior.
7. Validate new blockout assets against these measurements without copying original meshes, textures, or branding.

## Scale reference sheet
For each reference sample, record: sample ID, object class, estimated grid footprint, screen-pixel bounds, zoom state, occlusion, camera angle evidence, and confidence level.

## Gate
Do not freeze world units, camera parameters, model scale, or export-axis conventions until at least three object classes and two zoom states have been measured. Do not mark camera parity as complete based on a single screenshot.
