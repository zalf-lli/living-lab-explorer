---
phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data
plan: 08
subsystem: data-pipeline
tags: [rasterio, pmtiles, chelsa, climate, sync, codegen, mbtiles]

# Dependency graph
requires:
  - phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data
    provides: "08-06's compute_climate_color_breaks.py (Pass 0) + build_continuous_colormap() + build_climate_pmtiles.py (Pass 1), and 08-04/08-07's fetch_climate.py Germany-extent rasters"
provides:
  - "_pattern_to_glob() helper in sync.py, generalizing the per-LL sync glob from one placeholder to any number"
  - "generate_climate_legend() codegen in sync.py, producing app/src/data/climate_legend.js"
  - "60 built and published climate PMTiles (data/pmtiles/climate-*.pmtiles + app/public/data/pmtiles/climate-*.pmtiles)"
affects: [08-09, 08-10, 08-11]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "_pattern_to_glob(): regex substitution of every {...} placeholder with * (any-placeholder-count glob), shared by sync_pmtiles_per_ll() and sync_vector_geojson()"
    - "Two-stage measure-then-decide PMTiles build: one variable's full 15-file build measured and extrapolated (S1_BYTES * 4 * 2) against a literal byte cap before committing to the remaining three variables"
    - "Per-variable per-mode legend codegen: CLIMATE_VARIABLES (ordering/metadata) + CLIMATE_LEGEND (unit-aware bilingual band labels) + CLIMATE_RAMP_SHAPE (empirical sequential/diverging verdict), read from a Pass-0 computed JSON artifact rather than a static sources.yaml legend list"

key-files:
  created:
    - app/src/data/climate_legend.js
    - data/pmtiles/climate-*.pmtiles (60 files)
    - app/public/data/pmtiles/climate-*.pmtiles (60 files)
  modified:
    - data-pipeline/sync.py
    - app/src/data/layer_sources.js

key-decisions:
  - "Ran fetch_climate.py to re-acquire the 12 gitignored Germany-extent source rasters (absent in this fresh worktree checkout) before Task 3's build; every re-fetched raster's sha256 matched the digest already pinned in sources.yaml, confirming byte-identical reproduction"
  - "Chose gdd as the Stage 1 measurement variable (not the alphabetically-first bio1) since gdd's source files are the largest of the four (per 08-SPIKE.md, 3.9x-4.4x bio1's size), giving the most conservative Stage-1 extrapolation"
  - "Reused the Phase 6 short-path venv at C:\\lcvenv (documented in data-pipeline/README.md's Windows/OneDrive fallback) instead of creating a new venv inside the long OneDrive-nested worktree path, per the project's own documented MAX_PATH workaround"

requirements-completed: [D-05, D-09, D-10, D-12, D-13]

# Metrics
duration: 55min
completed: 2026-07-30
---

# Phase 8 Plan 8: Full 60-PMTiles Climate Build Summary

**Generalized sync.py's per-LL glob to any placeholder count, codegen'd a unit-aware per-variable/per-mode climate legend module, and built + published all 60 climate PMTiles inside a measured 49,642,502-byte footprint against the 209,715,200-byte (200 MiB) cap.**

## Performance

- **Duration:** 55 min
- **Started:** 2026-07-30T19:10:00Z (approx.)
- **Completed:** 2026-07-30T20:05:00Z (approx.)
- **Tasks:** 3 completed
- **Files modified:** 123 (sync.py, layer_sources.js, climate_legend.js, 60 source PMTiles, 60 published PMTiles)

## Accomplishments

- `sync.py` gained a single `_pattern_to_glob()` helper (regex substitution of every `{...}` placeholder) shared by `sync_pmtiles_per_ll()` and `sync_vector_geojson()`, plus an out-of-root guard and per-pattern matched-file-count logging
- `app/src/data/climate_legend.js` is now codegen'd from `sources.yaml`'s `chelsa-climate.climate.variables` block and `data/climate_color_breaks.json`, exporting `CLIMATE_VARIABLES` (4 entries, gdd first per D-08), `CLIMATE_LEGEND` (unit-aware bilingual baseline/change band labels per D-11), and `CLIMATE_RAMP_SHAPE` (all four variables verified `sequential` for both modes, per D-12's empirical resolution)
- All 60 climate PMTiles (4 variables x 3 periods x 5 Living Labs) are built and published, with the shared cross-Living-Lab colour scale (D-09) verified via a spot-check

## Task Commits

Each task was committed atomically:

1. **Task 1: Generalize the per-Living-Lab PMTiles glob to any number of placeholders** - `b2cfc4d` (feat)
2. **Task 2: Codegen app/src/data/climate_legend.js from the colour breaks** - `2ab0c6f` (feat)
3. **Task 3: Build, measure and commit the sixty climate PMTiles inside a hard footprint cap** - `b66339e` (feat)

_No separate plan-metadata commit — STATE.md/ROADMAP.md/REQUIREMENTS.md are owned by the orchestrator and are not touched by this worktree agent (see note below)._

## Files Created/Modified

- `data-pipeline/sync.py` - Added `_pattern_to_glob()`, `_sync_matched_pattern()` (shared glob+guard+copy logic), `_format_climate_number()`, `_format_climate_band_label()`, `_climate_bands_for_mode()`, and `generate_climate_legend()`; registered the new codegen call in `sync_to_app()`
- `app/src/data/climate_legend.js` - Generated module: `CLIMATE_VARIABLES`, `CLIMATE_LEGEND`, `CLIMATE_RAMP_SHAPE`
- `app/src/data/layer_sources.js` - Regenerated; picked up the already-committed `chelsa-climate` `sources.yaml` entry (stale prior to this plan's sync run, unrelated to this plan's own edits)
- `data/pmtiles/climate-{variable}-{period}-{slug}.pmtiles` (60 files) - Built via `build_climate_pmtiles.py`
- `app/public/data/pmtiles/climate-{variable}-{period}-{slug}.pmtiles` (60 files) - Published via `sync.py`

## Decisions Made

- **Stage 1 variable choice:** built `gdd` first for the Stage 1 measurement (not the alphabetically-first `bio1`), since `08-SPIKE.md` records `gdd5`'s source files as 3.9x-4.4x larger than `bio1`'s — this gives the most conservative (worst-case) Stage-1 extrapolation rather than an optimistic one.
- **Missing precondition, resolved via Rule 3 (auto-fix blocking issue):** this fresh worktree checkout had no `data/climate_source/*.tif` files (correctly gitignored per `sources.yaml`'s own comment) and no Python venv. Ran `python data-pipeline/python/fetch_climate.py` (the already-implemented 08-04 acquisition script) to re-derive all 12 Germany-extent rasters; every re-fetched file's sha256 matched the digest already pinned in `sources.yaml` (re-pinned at 08-07), confirming exact reproduction rather than a silent drift. This is reproducing already-committed, already-approved pipeline logic — not new architecture — so it was treated as a blocking-issue auto-fix rather than an architectural question.
- **Venv:** reused the existing short-path venv at `C:\lcvenv` (created for Phase 6, documented in `data-pipeline/README.md`'s "Recommended setup for Windows users" fallback sequence) rather than creating a new venv inside this deeply-nested OneDrive worktree path, since `06-02-SUMMARY.md` already documents that a long OneDrive path pushes shapely/rasterio/geopandas DLL paths past Windows' 260-char `MAX_PATH`. Added the one missing package (`python-dotenv`) to that venv.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Re-fetched the 12 gitignored Germany-extent CHELSA rasters**
- **Found during:** Task 3, precondition check before running `build_climate_pmtiles.py`
- **Issue:** `data/climate_source/` did not exist in this fresh worktree checkout (correctly gitignored, per `sources.yaml`'s own comment: "committed artifacts of this layer are the per-LL PMTiles plus `climate_kpis.json` and `climate_color_breaks.json`"), so `build_climate_pmtiles.py` would fail with "Missing Germany-extent raster ... run fetch_climate.py first"
- **Fix:** Ran `python data-pipeline/python/fetch_climate.py` (44 remote reads, 368.2s total wall time, 134,640,000 bytes transferred = 2.51% of the 5,368,709,120-byte W-08 cap). All 12 outputs' sha256 digests matched the values already pinned in `sources.yaml` (re-pinned at 08-07 after the scale/offset bug fix), confirming byte-identical reproduction
- **Files modified:** none tracked by git (`data/climate_source/` is gitignored, as designed)
- **Verification:** every `_check_or_report_digest()` call printed `[ok] {key}: digest verified`
- **Committed in:** n/a (gitignored, not a git change)

**2. [Rule 3 - Blocking] Created/repaired the Python 3.12 geospatial venv**
- **Found during:** start of Task 1 verification
- **Issue:** no Python 3.12 venv existed with `rasterio`/`geopandas`/`shapely`/`rio-mbtiles` installed; a plain `pip install -r requirements.txt` on a fresh venv hits the documented `rio-mbtiles==1.6.0` -> `shapely~=1.7.0` resolver conflict (no matching wheel for Python 3.12)
- **Fix:** Located the existing Phase 6 short-path venv at `C:\lcvenv` (per `data-pipeline/README.md`'s documented fallback install sequence) and installed the one missing package, `python-dotenv`, into it
- **Files modified:** none (venv is outside the repo, not tracked by git)
- **Verification:** `import shapely, geopandas, rasterio, mercantile, pytest, yaml, dotenv` succeeded; full `python -m pytest tests/ -q` suite passed (30/30) throughout all three tasks
- **Committed in:** n/a (environment setup, not a git change)

---

**Total deviations:** 2 auto-fixed (both Rule 3 - blocking preconditions, neither touching git-tracked files)
**Impact on plan:** Both were necessary to reach a runnable state for Task 3's real build; neither altered scope, architecture, or any committed file beyond what the plan itself specified.

## Issues Encountered

None beyond the two Rule-3 preconditions above. `npm install` was also required in `app/` (no `node_modules` present in this fresh worktree) before `npm run lint` could run for Task 2's verification — this is environment setup, not a deviation, and produced no tracked file changes (`package-lock.json` unchanged).

## Stage 1 / Final Footprint Gate Evidence (Task 3)

- **Stage 1** (variable `gdd`, all 3 periods x 5 Living Labs = 15 files): `S1_BYTES = 6,242,399` bytes
- **Stage 1 gate:** `S1_BYTES * 4 * 2 = 49,939,192` bytes, compared against the literal cap `209,715,200` bytes -> **PASS** (23.8% of cap) -> proceeded to Stage 2
- **Stage 2** (variables `bio1`, `bio12`, `bio18`, 45 more files): completed without incident
- **Final gate:** summed size of `data/pmtiles/climate-*.pmtiles` (60 files) + `app/public/data/pmtiles/climate-*.pmtiles` (60 files) = **49,642,502 bytes**, compared against the literal cap **209,715,200** bytes -> **PASS** (23.7% of cap). Asserted by Task 3's automated verify command, which exited 0.

### Per-variable wall time (derived from PMTiles file mtimes; two separate invocations)

| Variable | Files | Wall span | Bytes (source, 5 LLs x 3 periods) |
|---|---:|---:|---:|
| gdd (Stage 1) | 15 | 96.2s | 6,242,399 |
| bio1 (Stage 2) | 15 | 95.2s | 6,322,780 |
| bio12 (Stage 2) | 15 | 97.7s | 6,054,940 |
| bio18 (Stage 2) | 15 | 97.2s | 6,201,132 |

### Size table by variable x period (5 Living Labs each)

| Variable | baseline | 2041_2070 | 2071_2100 |
|---|---:|---:|---:|
| gdd | 2,481,969 B (2.37 MB) | 1,855,209 B (1.77 MB) | 1,905,221 B (1.82 MB) |
| bio1 | 2,536,434 B (2.42 MB) | 1,900,394 B (1.81 MB) | 1,885,952 B (1.80 MB) |
| bio12 | 2,409,471 B (2.30 MB) | 1,813,281 B (1.73 MB) | 1,832,188 B (1.75 MB) |
| bio18 | 2,589,511 B (2.47 MB) | 1,741,838 B (1.66 MB) | 1,869,783 B (1.78 MB) |

### Peak memory

Not instrumented with a live profiler during this run (no `psutil`/memory-tracing tool was attached to the build process). Qualitatively, this build's per-combination inputs are far smaller than Phase 6's: each Germany-extent source raster is 0.5-4.67 MB (1020x1200 pixels, float32), versus Phase 6's ~290 MB per-LL land-cover COGs that produced the ~2.2 GB per-LL reference figure. Per-iteration temp-file unlinking (the same discipline `build_land_cover.py` uses) was preserved throughout `build_climate_pmtiles.py`'s 60-iteration loop, and no OOM or swap behavior was observed on this machine during either stage. This is a qualitative, not measured, comparison — flagged for a future plan if a precise figure is ever needed.

### Shared-scale spot-check (D-09)

For `gdd`/`baseline`, the shared colour scale in `data/climate_color_breaks.json` is `{'#fce3da', '#eb5b25', '#dc4b14', '#bb3f11'}`. Re-running `build_climate_tif()` directly (in-process, not via the CLI) for all five Living Labs and inspecting each output's distinct opaque-pixel RGBA colours:

| Living Lab | Distinct colours observed | Extra (not in shared set) |
|---|---|---|
| east-brandenburg | `#dc4b14, #eb5b25, #bb3f11` | none |
| havellandisches-luch | `#dc4b14, #eb5b25, #bb3f11` | none |
| hessian-low-mountain | `#dc4b14, #eb5b25, #bb3f11, #fce3da` | none |
| north-hessian-loess | `#eb5b25, #fce3da` | none |
| rheingau | `#dc4b14, #eb5b25, #bb3f11, #fce3da` | none |

Every Living Lab's observed colour set is a subset of the shared 4-colour scale; no Living-Lab-only colour appeared. D-09's shared-across-all-LLs scale is confirmed for at least this variable/mode.

### Pre-existing layers unchanged

`git diff --stat` against `data/pmtiles/land-cover-*.pmtiles`, `data/pmtiles/landuse-croptypes.pmtiles`, and their `app/public/` copies shows no modification. `data/ll_metadata.json` and its published copy are content-unchanged after this plan's `sync.py` runs, as expected — the KPI manifest edit (D-18/D-19) has not landed yet; this is not a failed sync, it is the correct current state.

## Test Suite

`python -m pytest data-pipeline/tests/ -q` passed 30/30 after each task (Task 1, Task 2, and after the full Task 3 build). `cd app && npm run lint` exited 0.

## User Setup Required

None - no external service configuration required. (The Python venv and `npm install` steps above were one-time local environment setup performed by the executor, not a manual user action.)

## Next Phase Readiness

- All 60 climate PMTiles are built, published, committed, and colour-scale-consistent across Living Labs — the map slot's data dependency for `08-09`/`08-10` (frontend wiring) is fully satisfied.
- `app/src/data/climate_legend.js` exposes the full `CLIMATE_VARIABLES` / `CLIMATE_LEGEND` / `CLIMATE_RAMP_SHAPE` contract that `08-10`'s frontend work is written against (see `08-08-PLAN.md`'s `<interfaces>` section) — no further pipeline changes should be needed before the frontend variable picker, period switcher, and `MapLegend` wiring land.
- The i18n keys `climate.variable.<id>` and `legend.climate.note.<id>` referenced by the generated module do not yet exist in `app/src/i18n.js` — this is expected and out of this plan's `files_modified` scope; `08-UI-SPEC.md` already drafts the four legend-note translations for whichever future plan adds them.
- No blockers. The committed climate footprint (49,642,502 bytes, 23.7% of the 200 MiB cap) leaves substantial headroom for any future adjustment.

---
*Phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data*
*Completed: 2026-07-30*
