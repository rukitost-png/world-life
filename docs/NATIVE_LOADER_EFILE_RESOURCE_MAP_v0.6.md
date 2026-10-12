# Native Loader Findings v0.6 — Exact DEX resource-ID mapping

Date: 2026-10-13  
Reference: read-only master APK `World-Life-0.1-BGM-Fun-In-Kyoto-V2.apk` and its `classes.dex` / `lib/armeabi/libKyotoLife.so`  
Master APK SHA-256: `36727d1a1ac1b5f1e997efe8c312f1de7945bd6d13c91651a2b195e588185ca1`

## Major result: all 442 native EFILE indices map to one APK raw resource

The previous v0.5 audit only guessed archive candidates from the native filename suffix and found 375 matches. That was intentionally conservative but incomplete: many native logical filenames do not share the exact stem of the Android `R.raw` resource (for example, localized message files, effects, and UI themes).

The DEX now resolves the mapping directly:

1. `com.nubee.japanlife.R$raw` contains static resource-ID values and their names.
2. `com.nubee.japanlife.Resources.<init>` constructs nine integer arrays of those `R.raw` IDs, then stores them in `m_anResources` in a defined order.
3. `Resources.Count()` and `Resources.GetResource(int)` expose those groups to `GameActivity.onCreate`.
4. `GameActivity.onCreate` opens each resource with `Resources.openRawResourceFd(resourceId)`, reads `AssetFileDescriptor.getStartOffset()` and `getLength()`, and calls native `GameActivity.SetResourceOffset`.
5. Native `SetResourceOffset` forwards the EFILE index, package offset, and size to `CAppResourceManager::SetResourceOffsets`. Native package reads then use the per-index offset and size.

The nine resource groups are flattened in the same order used by the Java loader and total exactly 442 entries, matching the native filename pointer table length. For this master APK, every flattened index resolves to one `R.raw` field and exactly one `res/raw/` archive entry.

| Group order | DEX field | Entries | EFILE index range |
|---:|---|---:|---:|
| 1 | `m_anMapdata` | 236 | 0–235 |
| 2 | `m_anPackedData` | 87 | 236–322 |
| 3 | `m_anMovie` | 4 | 323–326 |
| 4 | `m_anData` | 17 | 327–343 |
| 5 | `m_anMessage` | 25 | 344–368 |
| 6 | `m_anFont` | 4 | 369–372 |
| 7 | `m_anEffect` | 61 | 373–433 |
| 8 | `m_anAirport` | 2 | 434–435 |
| 9 | `m_anUITheme` | 6 | 436–441 |
| | **Total** | **442** | **0–441** |

## Cross-check examples

| EFILE | Native logical filename | DEX `R.raw` name | Exact APK entry |
|---:|---|---|---|
| 0 | `maptexinfo.dat` | `maptexinfo` | `res/raw/maptexinfo.smf` |
| 1 | `mapdata000.nbc` | `mapdata000` | `res/raw/mapdata000.smf` |
| 235 | `mapdata234.nbc` | `mapdata234` | `res/raw/mapdata234.smf` |
| 236 | `packed0.png` | `packed0` | `res/raw/packed0.smf` |
| 344 | `message_common.msg.nbc` | `message_common` | `res/raw/message_common.msg.nbc` |
| 419 | `eff_Valentine.png` | `eff_valentine_t` | `res/raw/eff_valentine_t.smf` |
| 433 | `eff_rain.png` | `eff_rain_t` | `res/raw/eff_rain_t.smf` |
| 434 | `airporttexinfo.dat` | `airporttexinfo` | `res/raw/airporttexinfo.smf` |
| 435 | `airportdata.nbc` | `airportdata` | `res/raw/airportdata.smf` |
| 441 | `MapSelection_Theme.bin` | `uitheme_mapselection_theme` | `res/raw/uitheme_mapselection_theme.smf` |

The native logical filename, Android `R.raw` name, and archive filename are distinct naming layers. The DEX resource ID values plus the loader's array ordering resolve the association; basename similarity alone does not.

## Reproduction

Extract `lib/armeabi/libKyotoLife.so` from the master APK and run:

```sh
python tools/audit_efile_dex_mapping.py \
  World-Life-0.1-BGM-Fun-In-Kyoto-V2.apk libKyotoLife.so \
  --json efile-dex-map.json --csv efile-dex-map.csv
python -m unittest discover -s tests -v
```

The tool reads `classes.dex`, parses the `R.raw` static ID values and the resource-group arrays in the `Resources` constructor, extracts the native EFILE filename table, and joins those indices to archive entries. Default native table address `0x002e1108` is specific to this library build. The report intentionally includes names, resource IDs, archive paths, and sizes only; it does not include extracted game payloads.

## What this proves — and what it does not

**Proved for this APK build:** the 442 EFILE indices have a deterministic Java/Dex resource-ID association, the loader passes package start offsets and lengths into native code, and all 442 IDs resolve to unique `res/raw` archive entries.

**Not proved:** the full semantic schema of `maptexinfo.dat`, whether its SHA-256 entries cover stored or decoded data, whether custom assets can be imported without changing other metadata, whether the legacy patch endpoint remains reachable/authenticated, or whether a modified APK builds, signs, installs, logs in, renders the map, or saves successfully.

Keep the master APK read-only. The next task is to decode the checksum table and record-to-resource relationship, then test a minimal controlled asset round-trip only after a buildable and testable Android toolchain is available.
