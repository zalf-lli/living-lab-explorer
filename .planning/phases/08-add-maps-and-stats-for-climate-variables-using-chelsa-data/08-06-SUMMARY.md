---
phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data
plan: 06
subsystem: pipeline
tags: [chelsa, climate, colour-breaks, continuous-colormap, two-pass-build, pmtiles]

# Dependency graph
requires: ["08-04"]
provides:
  - "data-pipeline/python/compute_climate_color_breaks.py: Pass 0 -- pooled five-Living-Lab colour breakpoints and the empirical diverging/sequential ramp verdict per variable and mode (D-09, D-12)"
  - "data/climate_color_breaks.json: committed, human-inspectable shared breakpoints, auditable per-LL means, and colour stops -- one block per variable/mode, fixed before any pixel is baked"
  - "data-pipeline/python/build_pmtiles.py::build_continuous_colormap(): continuous sibling to build_colormap(), value->RGBA by numeric range instead of exact class match (D-10)"
  - "data-pipeline/python/build_climate_pmtiles.py: Pass 1 -- per-(variable, period, slug) clip/reproject/continuous-bake/mbtiles/pmtiles tiler, enumerable and dry-runnable across the full 60-file matrix, reading fixed breaks from outside the loop"
  - "data-pipeline/tests/check_color_breaks.py + test_climate_color_breaks_contract: standing contract enforcement for the shared-scale artifact"
affects: ["08-08 (build_climate_pmtiles.py's real 60-file run, sync.py's multi-placeholder glob, and the codegen'd climate_legend.js all read data/climate_color_breaks.json this plan wrote)"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Two-pass build for a shared, pre-baked continuous colour scale: Pass 0 (compute_climate_color_breaks.py) pools pixels across all five Living Labs and persists breakpoints before Pass 1 (build_climate_pmtiles.py) bakes any pixel -- no Phase 6/7 precedent existed for this ordering constraint"
    - "Empirical ramp-shape determination: the change-mode diverging-vs-sequential verdict is derived from the five real per-LL means' sign spread at build time, never hardcoded or assumed per-variable"
    - "build_continuous_colormap()'s classify(values, nodata_mask) callable: numpy.digitize against interior breaks, vectorised boolean-mask RGBA assignment mirroring build_paletted_geotiff's existing bake loop"

key-files:
  created:
    - data-pipeline/python/compute_climate_color_breaks.py
    - data-pipeline/python/build_climate_pmtiles.py
    - data-pipeline/tests/check_color_breaks.py
    - data/climate_color_breaks.json
  modified:
    - data-pipeline/python/build_pmtiles.py
    - data-pipeline/tests/test_pipeline_outputs.py

key-decisions:
  - "All four variables (gdd, bio1, bio12, bio18) empirically resolved to 'sequential' for both baseline and change against the real built data -- no variable's five per-LL means span both signs (bio12 change: all positive 1.44 to 2.2 pooled over both horizons; bio18 change: all negative -4.85 to -8.33). D-12 explicitly forbids hardcoding the expectation that precipitation diverges; the empirical check ran as designed and none of the four variables triggered the diverging branch"
  - "Pass 0's per_ll_means pool BOTH horizon rasters together for the change mode (per this plan's own pooling rule, so 2041-2070 and 2071-2100 share one scale) -- these values are therefore a two-horizon-pooled mean, not the far-horizon-only figure 08-07's climate_kpis.json reports. The two files answer different questions by design: climate_color_breaks.json's per_ll_means exist to justify a ramp-shape verdict across the whole change period, climate_kpis.json's deltas exist to report the D-21 far-horizon-only KPI tile value"
  - "Adopted the prior halted attempt's WIP branch (worktree-agent-aceaf6c51f1dfbc20) draft implementations of all three new files as a strong starting reference per the redispatch brief, but independently re-verified every acceptance criterion against 08-06-PLAN.md and re-ran every script for real rather than trusting the draft's own unfinished verification -- see Deviations for what was and was not carried over"
  - "Did not touch fetch_climate.py or sources.yaml's sha256_by_derived pins -- re-ran fetch_climate.py only to regenerate the gitignored data/climate_source/ rasters missing from this fresh worktree; all 12 computed digests matched the already-pinned values exactly (zero mismatch), confirming 08-07's merged scale/offset fix needed no rework here"

requirements-completed: [D-09, D-10, D-12, D-13]

# Metrics
duration: ~50min active work (majority spent on the ~7.2min live CHELSA re-acquisition of the 12 gitignored source rasters, absent from this fresh worktree; remainder on file authoring, independent verification, and test runs)
completed: 2026-07-30
---

# Phase 8 Plan 6: Shared Climate Colour Breaks + Pass-1 Tiler Summary

**Built the two-pass machinery D-09 requires: `compute_climate_color_breaks.py` pools all five Living Labs' pixels into one shared, committed breakpoint set per variable/mode before any pixel is baked, `build_continuous_colormap()` bakes a continuous value to a colour band by numeric range, and `build_climate_pmtiles.py` can enumerate and dry-run the full 60-file (variable, period, slug) matrix reading those fixed breaks -- no PMTiles are actually produced yet, that is `08-08`'s job.**

## Performance

- **Duration:** ~50 min active work -- roughly 7-8 min was the live CHELSA re-acquisition of the twelve gitignored `data/climate_source/*.tif` rasters (absent from this fresh worktree; 44 windowed reads, 433.8s wall time, 134,640,000 bytes, all 12 computed digests verified against the already-pinned `sources.yaml` values with zero mismatch), the remainder on writing and independently re-verifying the three new files plus the additive `build_pmtiles.py`/`test_pipeline_outputs.py` changes
- **Completed:** 2026-07-30
- **Tasks:** 3 (all `type="auto"`)
- **Files modified:** 6 (4 created: `compute_climate_color_breaks.py`, `build_climate_pmtiles.py`, `check_color_breaks.py`, `data/climate_color_breaks.json`; 2 modified: `build_pmtiles.py`, `test_pipeline_outputs.py`)

## Redispatch Context

This is a redispatch of the same plan. A prior executor attempt ran ~2.5 hours, drafted working
implementations of all three new files on branch `worktree-agent-aceaf6c51f1dfbc20`, but was lost to a
session boundary before finishing, verifying, or writing a SUMMARY. Meanwhile the sibling plan `08-07`
ran to completion independently, found and fixed a severe `fetch_climate.py` scale/offset bug, and
merged into this plan's base. Per the redispatch brief: the prior attempt's draft files were read via
`git show` as a strong starting reference (never merged or cherry-picked, since the draft also carried
its own now-redundant copy of the fetch_climate.py fix), adopted after independent line-by-line
verification against `08-06-PLAN.md`'s actual contract, then every script was re-run for real in this
worktree to re-derive every numeric output rather than trust the draft's own unfinished checks. No
change was needed to the draft's logic -- every acceptance criterion in the plan was independently
re-confirmed to hold against the code as adopted (see Deviations for what was deliberately NOT carried
over: the draft's now-superseded `fetch_climate.py`/`sources.yaml` copy, and its deletion of
`test_climate_kpis_fixture_matches_contract`).

## Accomplishments

- **Task 1 -- `compute_climate_color_breaks.py` written and run for real.** Pools pixels for each
  (variable, mode) across all five Living Labs using the exact same `build_clip_geometry()` Pass 1
  consumes, so both passes pool identical pixels. `baseline` pools only the baseline raster; `change`
  pools both horizon rasters together so the trajectory over time reads as a deepening colour on one
  fixed scale. Asserts per-slug non-empty contribution before pooling. Decides `sequential` vs
  `diverging` from the five real per-LL means' sign spread (D-12) rather than assuming precipitation
  diverges -- against the real built CHELSA data, **all four variables landed sequential for both
  modes**: `bio12`'s change means were all positive (1.44 to 2.2, pooled across both horizons) and
  `bio18`'s were all negative (-4.85 to -8.33), so neither crossed zero. Rounds breakpoints to a
  legible per-unit step (0.1 degC, 1 degC-day, 1 mm, 0.5 %), widening any collapsed pair to stay
  strictly increasing. Writes `data/climate_color_breaks.json` (`sort_keys=True`); ran the script twice
  and confirmed byte-identical output apart from `_meta.computed_at`; confirmed `--dry-run` leaves
  `git status --porcelain` unchanged.
- **Task 2 -- contract locked.** `tests/check_color_breaks.py` is a standalone runnable checker
  declaring the nine permitted hex stops (four heat, four water, plus `#f9fef9`) as a module-level
  frozenset and enforcing the full shape/monotonicity/band-count/sign-consistency contract, printing an
  `[ok]` line naming each variable's baseline/change ramp verdicts. Manually corrupted a scratch copy's
  `colors` list length by one and confirmed the checker exits non-zero naming the offending variable and
  mode (`bio1/baseline: len(colors)=3 must equal len(breaks)-1=4`). Added
  `test_climate_color_breaks_contract` to `test_pipeline_outputs.py` additively -- the existing
  `test_climate_kpis_fixture_matches_contract` (08-07) is untouched; `git diff --stat` on that file shows
  additions only (19 insertions, 0 deletions). Suite: 30/30 (29 pre-existing + 1 new).
- **Task 3 -- `build_continuous_colormap()` + Pass-1 tiler.** Added `build_continuous_colormap(breaks,
  colors)` to `build_pmtiles.py` directly beneath `build_colormap()`: validates strictly-increasing
  breaks and `len(colors)==len(breaks)-1`, raising `ValueError` naming the offending input on either
  violation (independently verified both raise paths plus the returned `classify()` callable's
  clamp-below/clamp-above/NaN-transparent behaviour by direct unit test). Zero lines removed from
  `build_pmtiles.py` across all three of this plan's commits (`git diff HEAD~3 HEAD -- ... | grep '^-'`
  is empty) -- the categorical path (`build_colormap`, `build_paletted_geotiff`, `build_mbtiles`,
  `convert_pmtiles`, `build_clip_geometry`, `cleanup_temp_dir`, `build_layer`) is byte-for-byte
  unchanged. `build_climate_pmtiles.py` loads `data/climate_color_breaks.json` exactly once in setup
  scope and builds one `classify()` callable per (variable, mode) pair before the per-slug loop starts.
  `--list` printed exactly 60 rows (4 variables x 3 periods x 5 slugs) matching
  `data/pmtiles/climate-{variable}-{period}-{slug}.pmtiles`; `--dry-run` exited 0, wrote nothing, and
  reported `{'baseline': 'baseline', '2041_2070': 'change', '2071_2100': 'change'}` -- confirming both
  horizons resolve to the shared `change` block while `baseline` resolves to `baseline`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Pass 0 -- compute shared cross-Living-Lab colour breaks and the empirical ramp verdict** - `b18ceca` (feat)
2. **Task 2: Add a contract test for the colour-breaks artifact** - `618f480` (test)
3. **Task 3: Add build_continuous_colormap() and the Pass-1 per-Living-Lab climate tiler** - `6d44348` (feat)

**Plan metadata:** (this commit, made after SUMMARY.md is written)

## Files Created/Modified

- `data-pipeline/python/compute_climate_color_breaks.py` - New, 283 lines (Task 1, commit `b18ceca`)
- `data/climate_color_breaks.json` - New, committed Pass-0 artifact (Task 1, commit `b18ceca`)
- `data-pipeline/tests/check_color_breaks.py` - New, 132 lines (Task 2, commit `618f480`)
- `data-pipeline/tests/test_pipeline_outputs.py` - Additive: `test_climate_color_breaks_contract` (Task 2, commit `618f480`)
- `data-pipeline/python/build_pmtiles.py` - Additive: `build_continuous_colormap()` (Task 3, commit `6d44348`)
- `data-pipeline/python/build_climate_pmtiles.py` - New, 339 lines (Task 3, commit `6d44348`)
- `data/climate_source/chelsa-{variable}-{period}.tif` (x12) - Gitignored, re-fetched into this fresh worktree via `fetch_climate.py` (no change to that script); all 12 digests matched `sources.yaml`'s already-pinned values exactly

## Decisions Made

- Adopted the prior halted attempt's draft (`worktree-agent-aceaf6c51f1dfbc20`) as the starting text for
  all three new files and the `build_pmtiles.py` addition, after reading each via `git show` (never
  merged/cherry-picked) and verifying line-by-line against `08-06-PLAN.md`'s actual `<action>` and
  `<acceptance_criteria>` text -- not against the draft's own unfinished self-verification. Every
  acceptance criterion was independently re-run and confirmed to hold in this worktree.
- Deliberately did NOT carry over the draft's `test_pipeline_outputs.py` change, which deleted
  `test_climate_kpis_fixture_matches_contract` (08-07's already-merged, already-passing test) and
  replaced it with `test_climate_color_breaks_contract` in the same slot. Instead added the new test as
  a separate, additive function, preserving 08-07's test unmodified.
- Did not touch `fetch_climate.py` or `sources.yaml`'s `sha256_by_derived` pins. Re-ran
  `fetch_climate.py` only to regenerate the twelve gitignored `data/climate_source/*.tif` rasters
  missing from this fresh worktree (expected, per the redispatch brief); all twelve freshly-computed
  digests matched the already-pinned values with zero mismatch, confirming 08-07's merged scale/offset
  fix is correct and needs no rework here.
- Used the pre-existing short-path venv `C:\gsdvenv312_08_06` (left over from the prior halted attempt,
  still present and working -- Python 3.12.10, rasterio 1.5.0) rather than building a fresh one, since
  this repo's OneDrive-synced checkout path is too long for a nested `data-pipeline/.venv`'s rasterio
  DLLs to load (the same Windows path-length failure `08-04-SUMMARY.md` and `08-07-SUMMARY.md` both
  documented).

## Deviations from Plan

### Auto-fixed Issues

None -- plan executed exactly as written; the pre-adopted draft required no logic corrections after
independent verification.

### Non-blocking observations (not fixed, not this plan's scope)

- All four variables' change-mode ramp verdicts came out `sequential`, not the "expected: precipitation
  diverges" framing in `08-CONTEXT.md`/`08-RESEARCH.md`/`08-UI-SPEC.md`. This is not a bug: D-12 states
  the expectation is "something to test, not to assume," and the empirical check ran exactly as
  designed -- `bio12`'s five per-LL change means (pooled across both horizons) are all positive
  (1.44-2.2) and `bio18`'s are all negative (-4.85 to -8.33), so neither variable's sign spans both
  positive and negative across the five Living Labs. `08-08`'s legend codegen and any downstream
  UI copy referencing a "diverging precipitation ramp" should read this file's actual `ramp` fields
  rather than assume the diverging branch fires -- it does not, for this real dataset.
- `fetch_climate.py`'s pre-existing `DeprecationWarning: Setting the shape on a NumPy array has been
  deprecated in NumPy 2.5` (from `rasterio`'s internal window-read code) reappeared during this plan's
  re-fetch, unchanged from `08-04-SUMMARY.md`'s and `08-07-SUMMARY.md`'s prior notes. Out of this plan's
  scope (no file this plan modifies controls that code path).

## Issues Encountered

- This fresh worktree had none of the twelve gitignored `data/climate_source/*.tif` rasters
  `compute_climate_color_breaks.py` and `build_climate_pmtiles.py` need to read. Re-ran
  `fetch_climate.py` (unmodified, already correct from 08-07) for real; all twelve digests matched the
  pinned values in `sources.yaml` exactly, confirming this was a worktree-freshness gap, not a code
  issue.
- No local Python installation in this worktree session had `rasterio` importable, matching the
  environment gap `08-04-SUMMARY.md`/`08-07-SUMMARY.md` both documented. Reused the pre-existing
  short-path venv `C:\gsdvenv312_08_06` (left over from the prior halted attempt at this same plan,
  confirmed still functional) rather than building a new one.

## User Setup Required

None -- no external service configuration required. All scripts in this plan read only already-fetched
local files (`data/climate_source/*.tif`, `data/nuts3_ll.geojson`) or already-pinned `sources.yaml`
config.

## Next Phase Readiness

- `data/climate_color_breaks.json` exists, is committed, contract-tested (`test_climate_color_breaks_contract`,
  suite 30/30 green), and holds real, empirically-derived breakpoints and ramp verdicts for all four
  variables and both modes -- ready for `08-08`'s real 60-file `build_climate_pmtiles.py` run to consume.
- `build_continuous_colormap()` is available from `build_pmtiles.py` and independently verified
  (ValueError paths, clamp behaviour, NaN-transparency) -- `08-08` can call `build_climate_pmtiles.py`
  without this plan's `--dry-run`/`--list` scaffolding needing further changes.
- `08-08` must widen `sync.py::sync_pmtiles_per_ll()`'s single-`{slug}`-placeholder glob to handle the
  three-placeholder `pmtiles_pattern` this plan's tiler writes to -- flagged in `08-08-PLAN.md` itself,
  not newly discovered here, but confirmed still outstanding.
- The empirical all-sequential ramp-verdict finding (see Deviations) should inform `08-08`'s legend
  codegen and any Phase 8 UI copy that assumed a diverging precipitation ramp would appear for this
  real dataset.

---
*Phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data*
*Completed: 2026-07-30*

## Self-Check: PASSED

- FOUND: data-pipeline/python/compute_climate_color_breaks.py (283 lines)
- FOUND: data-pipeline/python/build_climate_pmtiles.py (339 lines)
- FOUND: data-pipeline/tests/check_color_breaks.py (132 lines)
- FOUND: data/climate_color_breaks.json (_meta + 4 variable entries, each baseline+change)
- FOUND: data-pipeline/python/build_pmtiles.py (build_continuous_colormap present, build_colormap count still 1)
- FOUND: data-pipeline/tests/test_pipeline_outputs.py (test_climate_color_breaks_contract added, test_climate_kpis_fixture_matches_contract still present)
- FOUND commit: b18ceca (Task 1)
- FOUND commit: 618f480 (Task 2)
- FOUND commit: 6d44348 (Task 3)
- Verified `python -m pytest data-pipeline/tests/` exits 0 (30 passed)
- Verified `git diff HEAD~3 HEAD -- data-pipeline/python/build_pmtiles.py | grep '^-'` is empty (additions only across all three commits)
- Verified `git diff --stat data-pipeline/tests/test_pipeline_outputs.py` shows additions only (19 insertions, 0 deletions)
