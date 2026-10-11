# Native Runtime Symbol Triage

## Method
The reference APK was treated as read-only. The two ARM shared libraries were copied to a temporary analysis directory, then inspected with ELF metadata and exported symbol/string listings. No native library was modified or committed.

## Direct observations
- The main native library is an ELF32, little-endian ARM EABI5 shared object and is stripped in the sense that source-level debug information is not available.
- It exports recognizable C++ symbols for CMapDataManager, CPackedTextureManager, CObjTexManager, CMapData, CGameServer, and CQueryManager.
- Observed map-related symbols include initialization, render/update, map coordinate conversion, map index calculation, map size, zoom-factor control, object placement/movement, road access/direction updates, and map loading callbacks.
- Observed texture-related symbols include texture manager initialization, load/cache/unload operations, and object texture map-data loading.
- The binary includes PNG-related symbols and zlib inflate functions.
- Native string data includes filenames following a mapdataNNN.nbc pattern and names such as sh.dat and maptexinfo.dat.
- A symbol named TryLoadMap and callbacks related to loading map data are present.

## Engineering interpretation
This is evidence that map layout, object placement, map-coordinate conversion, and texture loading are managed by native code. It supports prioritizing native loader analysis before attempting to author replacement map files or object resources.

The filename strings do not prove that the packaged mapdataNNN.smf files and runtime mapdataNNN.nbc resources are interchangeable. Nor do exported symbols alone prove which exact functions are called on a particular runtime path.

## Next actions
1. Disassemble focused functions around native map initialization and map/texture loading.
2. Identify resource lookup rules and how the app chooses between packaged resources and server/downloaded resources.
3. Trace a single known map object from resource identifier to map record, texture identifier, and render path.
4. Use this evidence to define coordinate units, object footprint, rotation encoding, texture atlas mapping, and collision/road metadata.
5. Keep the master APK hash unchanged and record all offsets, symbol names, and evidence in a follow-up report.

## Limitations
No complete decompilation, call graph, live runtime trace, or device test has been performed. No claim is made that a custom asset has been accepted by the original game.
