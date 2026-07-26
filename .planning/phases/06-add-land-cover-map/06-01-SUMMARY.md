---
phase: 06-add-land-cover-map
plan: 01
subsystem: infra
tags: [pipeline, rasterio, geopandas, pmtiles, sources-yaml, land-cover, esri, impact-observatory]

# Dependency graph
requires:
  - phase: 03-chart-data-contract
    provides: declarative sources.yaml layer registry pattern, build_pmtiles.py raster machinery
provides:
  - io-lulc-landcover layer registered in sources.yaml with verified 9-class legend and per-LL tile assignment
  - slug-aware build_clip_geometry/build_paletted_geotiff in build_pmtiles.py (backward compatible)
  - build_land_cover.py per-Living-Lab orchestrator CLI (--list, --slug)
  - .gitignore protection for io_lulc_*.tif source COGs before any build runs
affects: [06-02-build-execution, 06-03-app-integration, 06-04-legend-codegen]

# Tech tracking
tech-stack:
  added: [mercantile>=1.2 (declared in requirements.txt; already installed/imported, was undeclared)]
  patterns:
    - "slug-aware clip geometry: optional slug kwarg filters clip_to features by ll_slug before union/buffer, defaulting to None for byte-identical prior behaviour"
    - "per-tile ensure_input_available() shim: assemble a minimal {input: {path, download_url, sha256}} dict rather than writing a new downloader"
    - "class histogram as build evidence: per-slug numpy.unique() counts merged into a single JSON file across partial reruns"
    - "single reused temp dir across a multi-slug loop, with a sweep of stale dirs from earlier interrupted runs"

key-files:
  created:
    - data-pipeline/python/build_land_cover.py
  modified:
    - data-pipeline/sources/sources.yaml
    - data-pipeline/python/build_pmtiles.py
    - .gitignore
    - data-pipeline/requirements.txt

key-decisions:
  - "Legend uses raw ESRI v3 class values 1,2,4,5,7,8,9,10,11 (never 3, 6, or a value:0 row) verified from Planetary Computer STAC file:values"
  - "Palette reuses nine hex codes already present in app/src/theme.js, app/src/data/layers.js, or LLMap/index.jsx -- zero new colours introduced"
  - "Corrected two pre-existing landuse-croptypes bugs in the same commit: removed phantom value:0 legend row, fixed input.crs from EPSG:4326 to the file's actual EPSG:32632 (Rule 1/Rule 2 auto-fixes, not new scope)"
  - "Per-Living-Lab processing (not a combined mosaic) is required to keep peak build memory near 2.2 GB against a 16.6 GB machine, per 06-RESEARCH.md measurements"
  - "input.crs deliberately omitted from the new layer -- the build always reads src.crs, never the YAML field"

requirements-completed: [D-05, D-06, D-07, D-08, D-09, D-10, D-11, D-13, D-14, D-15, D-16, D-17]

# Metrics
duration: 47min
completed: 2026-07-26
---

# Phase 06 Plan 01: Land Cover Pipeline Registration Summary

**Registered the io-lulc-landcover layer with a verified 9-class ESRI legend and zero-new-colour palette, made build_pmtiles.py's clip geometry slug-aware without touching crop-types' output, and shipped a new build_land_cover.py orchestrator that builds one Living Lab's PMTiles at a time with build-time class-value validation.**

## Performance

- **Duration:** 47 min
- **Started:** 2026-07-26T16:28:21+02:00 (first commit)
- **Completed:** 2026-07-26T17:14:58+02:00 (last commit)
- **Tasks:** 3/3 completed
- **Files modified:** 5 (1 created, 4 modified)

## Accomplishments
- `sources.yaml` now declares `io-lulc-landcover` (`app_layer: landscape`, `per_ll: true`) with the exact non-contiguous class values `[1,2,4,5,7,8,9,10,11]`, per-LL tile assignment (`32U`/`33U`), and full attribution/citation/license metadata including the CC-BY-4.0 provenance note
- `build_pmtiles.py::build_clip_geometry()` and `build_paletted_geotiff()` accept an optional `slug` kwarg; `slug=None` reproduces prior behaviour exactly (verified via full pytest run and a smaller-geometry assertion), and a new `RuntimeError` guard fires if a clip produces an all-nodata array
- New `data-pipeline/python/build_land_cover.py` CLI builds `data/pmtiles/land-cover-{slug}.pmtiles` per Living Lab, validates source rasters (`count==1`, `dtype==uint8`, `nodata==0`) before any tiling work, and asserts observed class values are a legend-covered subset of the valid ESRI v3 taxonomy -- converting the "Rangeland disappears" silent-transparency failure mode into a build failure
- `.gitignore` and `requirements.txt` updated in the same wave as the layer registration, so the ~290 MB source COGs can never be accidentally staged and a fresh clone won't fail on the undeclared `mercantile` import

## Task Commits

Each task was committed atomically:

1. **Task 1: Register the io-lulc-landcover layer and protect the build inputs** - `fc4c102` (feat)
2. **Task 2: Make clip geometry slug-aware without changing crop-types behaviour** - `60f1891` (feat)
3. **Task 3: Create the per-Living-Lab land cover build orchestrator** - `5830880` (feat)

_No TDD tasks in this plan; all three were straight `auto` implementation tasks._

## Files Created/Modified
- `data-pipeline/sources/sources.yaml` - Added `io-lulc-landcover` layer (legend, per-LL tile map, build/output config); fixed `landuse-croptypes` legend value:0 row and `input.crs`
- `data-pipeline/python/build_pmtiles.py` - `build_clip_geometry`/`build_paletted_geotiff` gained an optional `slug` kwarg; added all-nodata guard after `mask()`
- `data-pipeline/python/build_land_cover.py` (new) - Per-LL CLI orchestrator: tile fetch/validation, class histogram + legend-coverage assertions, single reused temp dir, merged histogram JSON output
- `.gitignore` - Added `data/io_lulc_*.tif`
- `data-pipeline/requirements.txt` - Added `mercantile>=1.2`

## Decisions Made
- Followed the plan's exact legend values, hex codes, and YAML field names verbatim (all pre-verified in `06-RESEARCH.md` against Planetary Computer STAC `file:values` and the project's existing theme colours)
- Kept `build_layer()` in `build_pmtiles.py` completely untouched, per the plan -- it continues to serve only the single-output crop-types path; `build_land_cover.py` owns its own per-slug loop
- Chose to write the class-histogram JSON incrementally (once per completed slug inside the loop, not only at the end) so a mid-run failure on a later slug still preserves the completed slugs' histogram records on disk

## Deviations from Plan

None - plan executed exactly as written. Both pre-existing crop-types corrections (value:0 legend removal, `input.crs` fix) and the `mercantile` dependency addition were explicitly specified in the plan's Task 1 `<action>`, not discovered separately, so they are not tracked as deviations.

One environment note handled without deviation: this worktree's available Python interpreters (3.13 user install and a separate 3.12 install) have `geopandas`/`shapely`/`mercantile`/`pyyaml`/`pytest` available but **no `rasterio` installed anywhere**. The existing test suite and `build_pmtiles.py` already avoid importing `rasterio` at module scope for exactly this reason (all rasterio imports are deferred inside function bodies). `build_land_cover.py` was written to follow the same lazy-import convention so `--list` and the plan's automated verification commands run without requiring rasterio to be installed in this environment; the actual raster build path (which does need rasterio) is exercised in plan 06-02.

## Issues Encountered

- First draft of `build_land_cover.py` imported `numpy`/`rasterio`/`rasterio.mask` at module top level, which broke `python python/build_land_cover.py --list` and the structural-wiring verification command in this environment (no rasterio installed). Moved those imports into the two functions that actually need them (`_validate_source_raster`, `_class_histogram_for_slug`), matching the existing lazy-import pattern already used throughout `build_pmtiles.py`. Re-ran all three Task 3 verification commands after the fix; all passed.

## User Setup Required

None - no external service configuration required. (Plan 06-02 will need network access to download the two ~145 MB source tiles from the anonymous AWS bucket, but that is out of scope for this plan.)

## Next Phase Readiness
- `io-lulc-landcover` is fully declared and ready for plan 06-02 to execute the actual per-LL build (download tiles, pin `sha256_by_tile` digests, produce the five `land-cover-{slug}.pmtiles` files and the class histogram)
- `build_pmtiles.py`'s slug-aware clip geometry is available for any other future per-LL raster layer, not just this one
- No blockers. The full existing pipeline test suite (12 tests) and all plan-specified automated verifications pass; `git status --porcelain` shows no `.tif` staged

---
*Phase: 06-add-land-cover-map*
*Completed: 2026-07-26*
