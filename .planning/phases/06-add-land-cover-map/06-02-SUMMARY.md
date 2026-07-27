---
phase: 06-add-land-cover-map
plan: 02
subsystem: infra
tags: [pipeline, rasterio, sync, pmtiles, sources-yaml, land-cover, legend-codegen, esri, impact-observatory]

# Dependency graph
requires:
  - phase: 06-add-land-cover-map
    plan: 01
    provides: io-lulc-landcover layer registration in sources.yaml, slug-aware build_pmtiles.py helpers, build_land_cover.py orchestrator
provides:
  - Five committed land-cover-{slug}.pmtiles pairs (data/pmtiles/ and app/public/data/pmtiles/), one per Living Lab
  - app/src/data/land_cover_legend.js (LAND_COVER_LEGEND), codegen'd and histogram-filtered
  - data/land_cover_class_histogram.json, the build evidence artefact
  - Pinned SHA-256 digests for both io-lulc-landcover source tiles (32U, 33U)
  - sync.py::sync_pmtiles_per_ll() and generate_land_cover_legend(), reusable for any future per-LL raster layer
affects: [06-03-app-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "pattern-based PMTiles sync: sync_pmtiles_per_ll() globs output.pmtiles_pattern with {slug} replaced by *, mirroring sync_vector_geojson() exactly"
    - "histogram-filtered legend codegen: generate_land_cover_legend() drops value:0 always, and drops any class with zero pixels across every LL when data/land_cover_class_histogram.json exists"
    - "short-path venv workaround: this OneDrive-nested worktree path plus Windows' 260-char MAX_PATH breaks DLL loading for shapely/rasterio/geopandas wheels even with ASCII-safe scratch paths; the working fix is creating the venv at a very short root path (C:\\lcvenv) rather than trying to fix encoding"

key-files:
  created:
    - app/src/data/land_cover_legend.js
    - data/land_cover_class_histogram.json
    - data/pmtiles/land-cover-east-brandenburg.pmtiles
    - data/pmtiles/land-cover-havellandisches-luch.pmtiles
    - data/pmtiles/land-cover-north-hessian-loess.pmtiles
    - data/pmtiles/land-cover-hessian-low-mountain.pmtiles
    - data/pmtiles/land-cover-rheingau.pmtiles
    - app/public/data/pmtiles/land-cover-east-brandenburg.pmtiles
    - app/public/data/pmtiles/land-cover-havellandisches-luch.pmtiles
    - app/public/data/pmtiles/land-cover-north-hessian-loess.pmtiles
    - app/public/data/pmtiles/land-cover-hessian-low-mountain.pmtiles
    - app/public/data/pmtiles/land-cover-rheingau.pmtiles
  modified:
    - data-pipeline/sync.py
    - data-pipeline/sources/sources.yaml
    - data-pipeline/python/build_pmtiles.py
    - data-pipeline/README.md
    - app/src/data/landuse_legend.js
    - app/src/data/layer_sources.js
    - data/destatis_curated_kpis.json
    - data/ll_metadata.json
    - app/public/data/ll_metadata.json

key-decisions:
  - "generate_land_cover_legend() follows sync.py's existing convention of json.dumps(indent=2, ensure_ascii=False) without sort_keys for generated JS array bodies -- CLAUDE.md's sort_keys=True directive targets dict-shaped output; the legend is a list whose per-object key order is already deterministic from sources.yaml. Not applied to crop-types output as a side effect."
  - "Rule 1 fix in build_pmtiles.py::build_mbtiles(): sqlite3.Connection's context manager only commits/rolls back, never closes -- fixed by managing the connection lifecycle explicitly with try/finally so the file is unlocked before build_land_cover.py's per-LL unlink() runs. This pre-existing bug also affects crop-types' build_layer(), which never surfaced it because it only removes the whole temp dir via a retry-and-warn cleanup path."
  - "Rule 1 fix in data/destatis_curated_kpis.json: restored source_host: bfn_wfs for natura2000_ha/nature_reserves_ha, reverting a bad merge-conflict resolution (commit a7aace7) that had silently undone Phase 05.1 commit aeafc72's fix. Discovered only because this plan's Task 3 mandates running sync.py, which regenerates ll_metadata.json from the (regressed) manifest instead of relying on stale committed output."
  - "Environment workaround: created the data-pipeline geospatial venv at C:\\lcvenv (a very short absolute path) rather than inside the worktree or the scratchpad directory, because both of those paths are long enough to push shapely/rasterio/geopandas DLL paths past Windows' 260-char MAX_PATH, which fails as 'ImportError: DLL load failed... filename or extension too long' rather than a clearer error."

requirements-completed: [D-09, D-12, D-13, D-14, D-16, D-18]

# Metrics
duration: 2h13min
completed: 2026-07-26
---

# Phase 06 Plan 02: Land Cover Build Execution & Sync Summary

**Extended sync.py with pattern-based per-LL PMTiles publishing and histogram-filtered legend codegen, then actually ran the ESRI/Impact Observatory land cover build for all five Living Labs (~290 MB of source tiles), pinned both SHA-256 digests, and published the runtime assets — fixing two pre-existing blocking bugs (a Windows sqlite file-lock bug in build_pmtiles.py and a regressed merge-conflict resolution in destatis_curated_kpis.json) along the way.**

## Performance

- **Duration:** ~2h13min (includes provisioning a working rasterio/geopandas/pmtiles toolchain from scratch in this worktree, plus two ~290 MB tile downloads)
- **Started:** 2026-07-26T20:05:16+02:00 (first commit)
- **Completed:** 2026-07-26T22:17:48+02:00 (last commit)
- **Tasks:** 3/3 completed
- **Files modified:** 21 (12 created, 9 modified)

## Environment Setup (not a plan task, but required to execute one)

This worktree had no Python geospatial toolchain at all (matching 06-01-SUMMARY.md's note that "no `rasterio` installed anywhere" in this environment). To actually run Task 2's build, I:

1. Created a Python 3.12 venv and installed the exact fallback dependency sequence from `data-pipeline/README.md` (`shapely==2.1.2`, `geopandas==1.1.3`, `rasterio==1.5.0`, `rio-mbtiles==1.6.0 --no-deps`, `mercantile`, `supermercado`, `tqdm`, `pytest`)
2. Hit a new, previously undocumented environment failure: `ImportError: DLL load failed while importing lib: The filename or extension is too long` when importing `shapely` (and later `rasterio`) from a venv living under this worktree's deeply nested OneDrive path. Root-caused this as Windows' 260-character `MAX_PATH` limit on the wheel's bundled DLL search path (228-263 chars measured, not an encoding issue like Pitfall 5 in 06-RESEARCH.md — confirmed by reproducing the identical failure from an ASCII-safe scratchpad path that was merely *shorter but still too long*, then succeeding once the venv moved to `C:\lcvenv`, a 9-character root path)
3. Located `pmtiles.exe` already installed at `C:\Users\black\Tools\pmtiles\pmtiles.exe` (set via `PMTILES_BIN` env var) and confirmed `rio.exe` (installed by `rasterio`/`rio-mbtiles`) worked once the venv itself was at a short path

This is not tracked as a plan deviation because it's pure local-environment provisioning, not a change to any committed file. It is documented here (and as a `tech-stack.patterns` entry) so a future executor in this same worktree doesn't waste time assuming the venv location doesn't matter.

## Accomplishments

- `sync.py` gained `sync_pmtiles_per_ll()` (glob-based per-LL PMTiles publisher, structurally identical to `sync_vector_geojson()`) and `generate_land_cover_legend()` (codegen `LAND_COVER_LEGEND` from `sources.yaml`'s `io-lulc-landcover` legend, dropping the `value: 0` nodata row always and any class with zero pixels across every LL once the class histogram exists); both wired into `sync_to_app()` immediately after the corresponding crop-types calls, leaving `sync_pmtiles()` and `generate_landuse_legend()` completely untouched
- Ran `build_land_cover.py` for all five Living Labs. Rheingau (smallest, ~63 tiles) validated the full chain first; the remaining four followed. Every LL's class histogram contains value 11 (Rangeland/grassland), confirming the correct ESRI v3 source product was used, and no unexpected class values (3, 6) appeared anywhere
- Pinned both source tile SHA-256 digests (`32U`, `33U`) into `sources.yaml`'s `input.sha256_by_tile`, replacing the two `null`s, then re-ran a build to confirm `ensure_input_available()` accepts them without a mismatch
- Ran `python data-pipeline/sync.py`, which copied all five land cover PMTiles into `app/public/data/pmtiles/`, regenerated `land_cover_legend.js` (8 of 9 legend classes survive the histogram filter — only Snow/Ice is dropped, since it never occurs in any of the five LLs; Clouds survives because it genuinely has non-zero pixels in 3/5 LLs), regenerated `landuse_legend.js` (drops the `value: 0` row removed in 06-01) and `layer_sources.js` (adds the `io-lulc-landcover` CC BY 4.0 attribution entry)
- Extended `data-pipeline/README.md` with a new "Build the land cover PMTiles layer (per Living Lab)" section documenting `build_land_cover.py`'s `--list`/`--slug` flags, the per-LL memory rationale, and the fact that `land_cover_legend.js` is generated and the source COGs are gitignored

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend sync.py with per-LL PMTiles publishing and land cover legend codegen** - `d14ff22` (feat)
2. **Task 2: Run the land cover build for all five Living Labs and pin the source digests** - `a035829` (feat)
3. **Task 3: Publish the runtime assets and document the layer** - `ab50fe9` (feat)

_No TDD tasks in this plan; all three were straight `auto` implementation tasks._

## Files Created/Modified

- `data-pipeline/sync.py` - Added `sync_pmtiles_per_ll()` and `generate_land_cover_legend()`, wired into `sync_to_app()`
- `data-pipeline/sources/sources.yaml` - Pinned `input.sha256_by_tile.32U`/`.33U` (both were `null`)
- `data-pipeline/python/build_pmtiles.py` - Fixed a Windows-only sqlite connection-not-closed bug in `build_mbtiles()` (Rule 1, see Deviations)
- `data-pipeline/README.md` - Documented `io-lulc-landcover`, `build_land_cover.py`, and the generated legend contract
- `data/pmtiles/land-cover-{5 slugs}.pmtiles` (new) - Committed per-LL land cover rasters, 0.6-5.1 MB each
- `app/public/data/pmtiles/land-cover-{5 slugs}.pmtiles` (new) - Runtime copies for the browser
- `data/land_cover_class_histogram.json` (new) - Per-LL class pixel histogram, build evidence
- `app/src/data/land_cover_legend.js` (new) - Generated `LAND_COVER_LEGEND`, 8 entries (Snow/Ice filtered out)
- `app/src/data/landuse_legend.js` - Regenerated (drops the `value: 0` row, matching 06-01's fix)
- `app/src/data/layer_sources.js` - Regenerated with the new land cover attribution entry
- `data/destatis_curated_kpis.json`, `data/ll_metadata.json`, `app/public/data/ll_metadata.json` - Fixed a regressed merge-conflict resolution (Rule 1, see Deviations) and regenerated from the corrected manifest

## Decisions Made

- Followed the plan's exact `sync_pmtiles_per_ll()`/`generate_land_cover_legend()` implementations verbatim from `06-RESEARCH.md`'s code examples (Pattern 3 and the legend codegen example), adding the histogram-filter behavior the plan's `<action>` additionally specified
- Kept the local convention of `json.dumps(indent=2, ensure_ascii=False)` without `sort_keys` for the generated legend JS array, per the plan's explicit note that CLAUDE.md's `sort_keys=True` rule targets dict-shaped output and the legend's key order is already deterministic
- Built `rheingau` first per the plan's build-order suggestion, confirming the full chain (download, validation guards, clip, warp, colourise, tile, PMTiles convert) before committing to the full five-LL run

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug, blocking] `build_mbtiles()` never closed its sqlite connection, locking the temp mbtiles file on Windows**
- **Found during:** Task 2, first `build_land_cover.py --slug rheingau` run
- **Issue:** `with rasterio.open(paletted_tif) as src, sqlite3.connect(output_mbtiles) as conn:` relies on `sqlite3.Connection.__exit__`, which only commits/rolls back the active transaction -- it does not call `close()`. This is standard, documented sqlite3 behavior, not new to this plan. It went unnoticed for crop-types because `build_layer()` never explicitly `unlink()`s the temp mbtiles; it only calls `cleanup_temp_dir()`, whose `shutil.rmtree()` retries and eventually just warns on `PermissionError` (the six orphaned `landuse-croptypes-*` temp dirs `06-RESEARCH.md` Pitfall 9 already documents are the visible symptom). `build_land_cover.py`'s per-LL loop explicitly calls `paletted_tif.unlink(missing_ok=True)` / `temp_mbtiles.unlink(missing_ok=True)` between slugs (to avoid accumulating 5x the temp files across a five-LL loop), and that explicit unlink crashed with `PermissionError` on the very first slug because the sqlite handle was still open.
- **Fix:** Restructured `build_mbtiles()` to manage the connection lifecycle explicitly with `try/finally`, calling `conn.close()` after the `with rasterio.open(...)` block completes, instead of relying on `with sqlite3.connect(...) as conn:`.
- **Files modified:** `data-pipeline/python/build_pmtiles.py`
- **Commit:** `a035829`

**2. [Rule 1 - Bug, blocking, pre-existing but plan-triggered] `data/destatis_curated_kpis.json` had a regressed `source_host` for two protected-area KPI slots**
- **Found during:** Task 3, after running `python data-pipeline/sync.py` and then `pytest`
- **Issue:** `test_protected_area_kpis_reach_ll_metadata` failed with `east-brandenburg.natura2000_ha: value is null`. Investigation traced this to merge commit `a7aace7` (2026-07-26, well before this plan started), which resolved a conflict on `data/destatis_curated_kpis.json` by silently reverting Phase 05.1 commit `aeafc72`'s fix (`source_host: "bfn_wfs"` -> back to `null` for `natura2000_ha` and `nature_reserves_ha`). This regression was invisible until now because the previously-committed `app/public/data/ll_metadata.json` still carried the correct pre-regression values on disk, and nothing had re-run `sync.py` (which regenerates `ll_metadata.json` from the current manifest) since the bad merge. This plan's Task 3 explicitly requires running `sync.py`, which surfaced the drift as a test failure. Out of this plan's declared file scope (it's a Phase 05.1 KPI manifest, unrelated to land cover), but it directly blocked the plan's own `<verification>` gate (`pytest tests/ -q` must exit 0), so it qualifies as a Rule 1/3 blocking-issue fix rather than an out-of-scope item to defer.
- **Fix:** Restored `source_host: "bfn_wfs"` for both `natura2000_ha` and `nature_reserves_ha` entries in `data/destatis_curated_kpis.json` (matching commit `aeafc72`'s original fix exactly), then re-ran `sync.py` to regenerate `data/ll_metadata.json` and `app/public/data/ll_metadata.json`.
- **Also benign, same regeneration:** the corrected regeneration also drops legacy `kpi`/`production`/`socio` placeholder blocks (all `"-"` sentinel values) from both `ll_metadata.json` copies. These fields no longer exist in the human-owned `data/ll_content.json` since Phase 4's `kpiByTab` restructure; the committed metadata files were simply stale relative to the current authored source. Verified via `grep` that no frontend code (`app/src/**`) reads `.kpi`, `.production`, or `.socio` off `ll_metadata.json` records.
- **Files modified:** `data/destatis_curated_kpis.json`, `data/ll_metadata.json`, `app/public/data/ll_metadata.json`
- **Commit:** `ab50fe9`

## Issues Encountered

- Non-fatal, environment-only: the venv provisioning hit an undocumented DLL-loading failure (`ImportError: ... The filename or extension is too long`) tied to Windows' 260-char path limit interacting with this worktree's deeply nested absolute path, distinct from `06-RESEARCH.md` Pitfall 5's non-ASCII/`UnicodeDecodeError` issue. Root-caused and worked around by creating the venv at a short path (`C:\lcvenv`) instead. See "Environment Setup" above.

## User Setup Required

None. All required tools (`pmtiles.exe`, a working Python 3.12 geospatial venv) were provisioned during this plan's execution; no external service configuration is needed.

## Next Phase Readiness

- Five per-Living-Lab `land-cover-{slug}.pmtiles` files are committed in both `data/pmtiles/` and `app/public/data/pmtiles/`, ready for the frontend to consume via `RasterPmtilesLayer` with slug-aware `resolveLayerAsset()`
- `app/src/data/land_cover_legend.js` exports `LAND_COVER_LEGEND` (8 `{value, en, de, color}` entries), ready to be imported by `layers.js` and rendered by `MapLegend.jsx`
- Both source tile SHA-256 digests are pinned; a future rebuild will fail loudly if the upstream S3 objects change
- No blockers. All 12 tests in `data-pipeline/tests/` pass; `git status --porcelain` shows no `.tif` staged and no `[skip]` line for the land cover pattern when `sync.py` runs
- Ready for the next plan in this phase (frontend integration: `layers.js` LAYERS array update, tab rename/restructure per D-01..D-24)

---
*Phase: 06-add-land-cover-map*
*Completed: 2026-07-26*

## Self-Check: PASSED

- FOUND: data-pipeline/sync.py
- FOUND: data-pipeline/python/build_pmtiles.py
- FOUND: data-pipeline/sources/sources.yaml
- FOUND: data-pipeline/README.md
- FOUND: data/pmtiles/land-cover-east-brandenburg.pmtiles
- FOUND: data/pmtiles/land-cover-havellandisches-luch.pmtiles
- FOUND: data/pmtiles/land-cover-north-hessian-loess.pmtiles
- FOUND: data/pmtiles/land-cover-hessian-low-mountain.pmtiles
- FOUND: data/pmtiles/land-cover-rheingau.pmtiles
- FOUND: data/land_cover_class_histogram.json
- FOUND: app/public/data/pmtiles/land-cover-east-brandenburg.pmtiles
- FOUND: app/src/data/land_cover_legend.js
- FOUND: app/src/data/landuse_legend.js
- FOUND commit: d14ff22 (Task 1)
- FOUND commit: a035829 (Task 2)
- FOUND commit: ab50fe9 (Task 3)
- FOUND commit: 9a8a5b5 (SUMMARY)
