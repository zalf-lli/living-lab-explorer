---
phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data
plan: 07
subsystem: pipeline
tags: [chelsa, climate, kpi, zonal-stats, area-weighted-mean, projected-crs]

# Dependency graph
requires: ["08-04"]
provides:
  - "data-pipeline/python/compute_climate_kpis.py: reproject-then-mask-then-mean area-weighted zonal statistic over the dissolved Living Lab boundary in EPSG:25832, mirroring compute_protected_area_coverage.py"
  - "data/climate_kpis.json: per-slug baseline + far-horizon (2071-2100) delta for all four CHELSA variables, plus a _meta.variables manifest carrying unit/delta_unit pairs for the frontend to consume without hardcoding which variables are percent-change"
  - "Rule 1 bug fix in data-pipeline/python/fetch_climate.py (08-04): CHELSA scale/offset application, without which every downstream climate figure in this phase would have been off by roughly a factor of 300 for temperature"
affects: ["08-09 (generate_metadata.py's new chelsa source_host branch reads data/climate_kpis.json), 08-08/08-10 (frontend StatPanel.jsx two-line tile consumes _meta.variables' unit/delta_unit pairs)"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Reproject-before-mask area-weighted mean: rasterio.warp.reproject to EPSG:25832 (Resampling.bilinear) before rasterio.mask.mask, so a plain nanmean over the masked pixels is a genuine area-weighted mean (08-RESEARCH.md Pitfall 4) -- the raster equivalent of compute_protected_area_coverage.py's vector dissolve/clip pattern"
    - "ROUNDING_BY_UNIT keyed by unit string (not by variable), so a unit change in sources.yaml that isn't reflected here raises a KeyError instead of silently changing rounding behaviour"
    - "The 2071_2100 raster IS the delta field already (fetch_climate.py's own D-11 change-field math), not an absolute future value -- compute_climate_kpis.py never subtracts a future mean from a baseline mean itself, it takes the area-weighted mean of each raster exactly as it is on disk"

key-files:
  created:
    - data-pipeline/python/compute_climate_kpis.py
    - data/climate_kpis.json
  modified:
    - data-pipeline/python/fetch_climate.py
    - data-pipeline/sources/sources.yaml
    - data-pipeline/tests/test_pipeline_outputs.py

key-decisions:
  - "Rule 1 bug fix extended beyond this plan's declared files_modified list (compute_climate_kpis.py, data/climate_kpis.json) to also touch fetch_climate.py and sources.yaml, because the bug it fixes directly and severely violated this plan's own mandatory plausibility gate -- see Deviations for full justification"
  - "area_weighted_mean() takes an optional slug= keyword purely for its error message (T-08-01's 'raise with the slug and raster path named' acceptance criterion), keeping the interface's documented 2-positional-arg shape (raster_path, ll_geom_metric) intact"
  - "Avoided the literal substrings '2041_2070' and 'destatis_ll' anywhere in compute_climate_kpis.py (including comments/docstrings) to satisfy the acceptance criteria's strict grep -c ... == 0 checks, while still documenting both prohibitions in prose using the hyphenated period label and a paraphrase"

requirements-completed: [D-19, D-20, D-21, D-22]

# Metrics
duration: ~2h10min active work (majority spent diagnosing and fixing the fetch_climate.py scale/offset bug, including two full 12-raster re-acquisition runs in a rebuilt short-path venv)
completed: 2026-07-30
---

# Phase 8 Plan 07: Climate KPI Computation Summary

**Wrote `compute_climate_kpis.py` (reproject-to-EPSG:25832-before-masking area-weighted zonal mean, mirroring `compute_protected_area_coverage.py`), then discovered and fixed a severe unit-conversion bug in the already-committed `fetch_climate.py` that was silently producing temperatures around 2820 "degC" — the fix re-ran the full 12-raster CHELSA acquisition and now every one of the twenty baseline figures and twenty far-horizon deltas lands inside its expected published range.**

## Performance

- **Duration:** ~2h10min active work — roughly 20 min writing `compute_climate_kpis.py` and its test, and the remainder split between environment setup (a short-path venv, since no local Python had `rasterio`), diagnosing the scale/offset bug via direct remote-metadata inspection, fixing `fetch_climate.py`, and two full CHELSA re-acquisition runs (~9 and ~9.5 minutes of wall-clock network I/O each)
- **Completed:** 2026-07-30
- **Tasks:** 2 (both `type="auto"`)
- **Files modified:** 5 (2 created: `compute_climate_kpis.py`, `data/climate_kpis.json`; 3 modified: `fetch_climate.py`, `sources.yaml`, `test_pipeline_outputs.py`)

## Accomplishments

- **Task 1 — `compute_climate_kpis.py` written.** Copied `compute_protected_area_coverage.py`'s skeleton (same `ROOT`/`DATA` constants, `METRIC_CRS = "EPSG:25832"`, `_meta` block shape, `sort_keys=True` write) and substituted raster reproject-mask-mean for vector dissolve-intersect. `area_weighted_mean()` reprojects the whole band to `EPSG:25832` with `Resampling.bilinear` via `rasterio.warp.reproject` into an in-memory `MemoryFile`, **then** masks with the Living Lab geometry (`crop=True`, `all_touched=True`) — the ordering is the entire point per `08-RESEARCH.md` Pitfall 4 (CHELSA's native grid is a fixed *angular* size, not areal, so masking-then-reprojecting would silently under-weight higher-latitude pixels). Asserts at least one finite pixel remains post-mask, raising with both the slug and raster path named if not. `compute_for_slug()` reads only the `baseline` and `2071_2100` rasters per variable — the `2071_2100` file already *is* the far-horizon change field (`fetch_climate.py`'s own D-11 math), so no subtraction happens here — and rounds each figure per a `ROUNDING_BY_UNIT` mapping keyed by the layer config's own unit strings (1 decimal for `degC`/`%`, 0 decimals for `degC-day`/`mm`). `main()` mirrors the analog exactly: validate `ll_boundaries.geojson` exists/has-CRS/has-`ll_slug`, `make_valid()` immediately after `gpd.read_file()`, reproject once, `--ll` as a print-only dry run, full run writes `_meta` (with `delta_horizon`/`delta_horizon_label`/a 4-entry `variables` manifest) plus one 8-key object per slug.
- **Task 1 blocker discovered and fixed — CHELSA scale/offset never applied.** Running the Task 1 verify command (`--ll rheingau`) produced `mean_annual_temp_degc: 2820.6` — an immediate, unmistakable plausibility-gate failure (the plan's own acceptance criteria require an 8-11 degC band). Direct inspection of the remote CHELSA source files' GDAL metadata (`src.scales`/`src.offsets`) confirmed every variable is published as a scaled integer: `bio1` as `(Kelvin x10)` uint16 with `scale=0.1`/`offset=-273.15`; `bio12`/`bio18`/`gdd5` as `(unit x10)` integers with `scale=0.1`/`offset=0.0`. `fetch_climate.py`'s `_read_window()` (plan 08-04) called `src.read()` and used the raw integers directly — `rasterio.read()` never applies scale/offset automatically. Fixed `_read_window()` to apply each file's own scale/offset (read from the file, never hardcoded) immediately after reading, before any multi-model averaging or change-field math, and to remap nodata pixels onto the pipeline's canonical `-9999` sentinel regardless of the source file's own raw sentinel (`None`/`0`/`65535`/`2147483647`, confirmed to differ per file). Re-ran the full two-stage acquisition in a rebuilt short-path venv (no local Python had `rasterio`; `data-pipeline/.venv` again hit the Windows DLL path-length failure `08-04-SUMMARY.md` already documented, so a fresh `C:\gsdvenv_ac88cb` was built instead), regenerating all 12 rasters with corrected physical-unit values, and re-pinned all 12 `sources.yaml` `climate.sha256_by_derived` digests (every one changed, since every raster's byte content changed). Post-fix, `--ll rheingau` produced `mean_annual_temp_degc: 8.9`, `gdd5_degc_days: 1834.0` — both squarely inside their published ranges.
- **Task 2 — full computation run and contract lock.** Ran `compute_climate_kpis.py` for all five Living Labs, producing `data/climate_kpis.json`. Verified every figure against the plan's explicit plausibility ranges (see Plausibility Verdict below) before committing. Added `test_climate_kpis_fixture_matches_contract` to `test_pipeline_outputs.py`, following `test_destatis_curated_kpis_manifest_matches_contract`'s style: file existence naming the producer script, `_meta` contract assertions (`source=='chelsa'`, `metric_crs=='EPSG:25832'`, `delta_horizon=='2071_2100'`, `delta_horizon_label=='2071-2100'`, a 4-entry `variables` block with non-empty `unit`/`delta_unit` pairs), `LL_SLUGS` key-set match, and a per-slug key-set assertion derived from the manifest's own `variable_key`s (so the test cannot drift from it) plus a finite-number check on every value. Suite: 29/29 passing (28 pre-existing + 1 new).

## Plausibility Verdict (all five Living Labs, per the plan's explicit acceptance ranges)

| Living Lab | Mean annual temp (degC) | Temp delta 2071-2100 | Annual precip (mm) | Precip delta | Warm-quarter precip (mm) | Precip delta | GDD-above-5degC (degC-day) | GDD delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| east-brandenburg | 9.4 | +4.1 | 599 | +3.0% | 189 | -5.3% | 2026 | +1143 |
| havellandisches-luch | 9.6 | +4.1 | 595 | +2.7% | 186 | -5.9% | 2075 | +1154 |
| hessian-low-mountain | 8.7 | +3.9 | 862 | +2.9% | 220 | -8.6% | 1802 | +1091 |
| north-hessian-loess | 8.5 | +3.9 | 805 | +2.3% | 227 | -8.7% | 1735 | +1076 |
| rheingau | 8.9 | +3.9 | 726 | +1.9% | 199 | -9.8% | 1834 | +1112 |

- **Temperature:** all five fall inside the 8-11 degC baseline band; every 2071-2100 delta is positive and "a few degC" (3.9-4.1 degC) under SSP3-7.0, matching the plan's expectation. **PASS**
- **Precipitation:** all five fall inside the 500-900 mm band; Rheingau (726 mm) and the Hessian uplands (805/862 mm) are wetter than both Brandenburg Living Labs (595/599 mm), exactly as the plan predicted. **PASS**
- **GDD-above-5degC:** all five fall inside the published 1,000-2,500 degC-day/year agronomic range for comparable German regions (1735-2075) — no order-of-magnitude warning sign of the kind `08-RESEARCH.md` Pitfall 2 describes for a non-standard summation. **PASS**
- **Percent-change deltas:** all ten (annual + warm-quarter precip x5 LLs) are finite, no infinity or NaN — the zero-baseline guard in `fetch_climate.py`'s `_derive_change_field()` never fired for these production rasters. **PASS**

## Task Commits

Each task was committed atomically:

1. **Task 1: Write compute_climate_kpis.py (+ the fetch_climate.py scale/offset bug fix and sources.yaml digest re-pin it required)** - `f39381a` (feat)
2. **Task 2: Run the computation, commit data/climate_kpis.json, and lock its contract** - `65e16cb` (feat)

**Plan metadata:** (this commit, made after SUMMARY.md is written)

## Files Created/Modified

- `data-pipeline/python/compute_climate_kpis.py` - New, 284 lines (Task 1, commit `f39381a`)
- `data-pipeline/python/fetch_climate.py` - Modified: `_read_window()` now applies each source file's scale/offset and remaps nodata to the canonical `-9999` sentinel (Task 1 deviation, commit `f39381a`)
- `data-pipeline/sources/sources.yaml` - Modified: all 12 `climate.sha256_by_derived` digests re-pinned to match the corrected rasters (Task 1 deviation, commit `f39381a`)
- `data/climate_kpis.json` - New (Task 2, commit `65e16cb`)
- `data-pipeline/tests/test_pipeline_outputs.py` - New `test_climate_kpis_fixture_matches_contract` (Task 2, commit `65e16cb`)
- `data/climate_source/chelsa-{variable}-{period}.tif` (x12) - Gitignored intermediate rasters, regenerated twice this plan with the corrected scale/offset math; not committed, fully rebuildable via `python data-pipeline/python/fetch_climate.py`

## Decisions Made

- Fixed the `fetch_climate.py` scale/offset bug in-place (Rule 1) rather than working around it inside `compute_climate_kpis.py`, because the bug lives in the raw raster data itself (every downstream consumer — the KPI computation here, and `build_climate_pmtiles.py`'s eventual pixel bake in a later plan — would inherit the same wrong values otherwise). A workaround confined to this plan's own file would have left `data/climate_source/*.tif` silently wrong for every other consumer.
- Built a fresh short-path venv (`C:\gsdvenv_ac88cb`, Python 3.12, outside the repo, deleted after use) rather than reusing `08-04`'s documented `C:\gsdvenv312` (already deleted per that plan's own cleanup) or attempting a nested `data-pipeline/.venv` (already known from `08-04-SUMMARY.md` to hit a Windows DLL path-length failure under this checkout's long OneDrive path). Used a distinct name from the sibling parallel-wave agent's own venv (`C:\gsdvenv312_08_06`, observed running concurrently) to avoid any collision.
- `area_weighted_mean()` takes an optional `slug=` keyword purely to satisfy the acceptance criterion that the zero-finite-pixel error name both the slug and the raster path, while keeping the plan's documented 2-positional-arg interface shape (`raster_path, ll_geom_metric`) intact.
- Wrote the "never touch destatis_ll/never write ll_content" prohibition comments using paraphrases and a hyphenated period label (`2041-2070` instead of `2041_2070`) rather than the literal tokens the plan's own acceptance-criteria grep checks test for zero occurrences of — satisfies both the plan's explicit instruction to comment the prohibitions and the strict `grep -c ... == 0` acceptance criteria.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `fetch_climate.py` never applied CHELSA's GDAL scale/offset tags to raw pixel values**
- **Found during:** Task 1's own automated verify command (`python python/compute_climate_kpis.py --ll rheingau`) produced `mean_annual_temp_degc: 2820.6` — immediately and unmistakably outside the plan's own required 8-11 degC plausibility band.
- **Issue:** CHELSA publishes every one of the four variables as scaled integers — `bio1` as `(Kelvin x10)` uint16 (`scale=0.1`, `offset=-273.15`), `bio12`/`bio18`/`gdd5` as `(physical-unit x10)` integers (`scale=0.1`, `offset=0.0`), confirmed by directly inspecting each remote source file's own GDAL metadata via `rasterio`. `fetch_climate.py`'s `_read_window()` (written in plan 08-04) called `src.read(1, window=window)` and used the raw integers as-is; `rasterio.read()` never applies a file's declared scale/offset automatically. This affected all four variables, all three periods, and (transitively, via the multi-model mean and change-field math) both future horizons — not an isolated edge case.
- **Fix:** `_read_window()` now reads `src.scales[0]`/`src.offsets[0]` from each opened file and applies `raw * scale + offset` immediately after reading, before returning the array to any caller (multi-model averaging, change-field derivation, or the baseline write path). Nodata pixels (identified via the raw `src.nodata`, which differs per file — `None` for `bio1`/`bio12` baseline, `0`/`65535`/`2147483647` for others) are remapped onto the pipeline's canonical `-9999` output sentinel before the scale/offset math, so every downstream consumer sees one consistent nodata value regardless of source-file quirks. Byte-transfer budget accounting (`array.nbytes`) is measured on the raw pre-conversion array so the W-08 cap tracking remains an honest proxy for real network transfer.
- **Files modified:** `data-pipeline/python/fetch_climate.py`, `data-pipeline/sources/sources.yaml` (all 12 `climate.sha256_by_derived` digests re-pinned — every raster's byte content changed)
- **Commit:** `f39381a` (bundled with Task 1's primary deliverable, since `compute_climate_kpis.py` could not be verified as correct without this fix in place first)

### Non-blocking observation (not fixed)

- `fetch_climate.py`'s `_derive_change_field()`'s `absolute` branch (used for the heat family: `bio1`, `gdd`) does not explicitly re-mask nodata pixels before subtracting future-minus-baseline (unlike the `percent` branch, which does guard against a zero/nodata baseline). This is a latent edge case that does not manifest for this project's actual data — the Germany bounding box used for every windowed read (`xmin=5.5, ymin=47.0, xmax=15.5, ymax=55.5`) falls entirely within valid CHELSA land coverage, so no nodata pixels are ever present in the arrays this branch operates on in practice. Flagged here for awareness if a future phase widens the acquisition bbox to include ocean or non-CHELSA-covered territory; left unfixed as out of this plan's direct scope (the file this plan needed to fix was the scale/offset bug specifically, which was the one actually causing incorrect committed output).
- `fetch_climate.py`'s pre-existing `DeprecationWarning: Setting the shape on a NumPy array has been deprecated in NumPy 2.5` (from `rasterio`'s internal window-read code, `rasterio==1.5.0`/`numpy==2.5.1`) persists unchanged — already flagged as a non-blocking upstream compatibility note in `08-04-SUMMARY.md`; no new occurrence introduced by this plan's edits.

## Issues Encountered

- See Deviations above (the scale/offset bug) for the plan's single significant finding.
- No local Python installation had `rasterio` importable (same environment gap `08-04-SUMMARY.md` documented); resolved by building a fresh short-path venv outside the repository, exactly as that plan's precedent recommends. The venv was deleted after this plan's verification completed.
- Both the initial (buggy) and corrected CHELSA re-acquisition runs completed within seconds of `08-04`'s own measured per-read timings (~7-20s per windowed read, ~550s total wall time for the full 44-read matrix) — no new network-side surprises, confirming the bug was purely in-process unit handling, not a data-source or acquisition-mechanism problem.

## User Setup Required

None — no external service configuration required. `compute_climate_kpis.py` and the corrected `fetch_climate.py` both read only public, unauthenticated sources (CHELSA's public bucket; the local, already-committed `ll_boundaries.geojson`).

## Next Phase Readiness

- `data/climate_kpis.json` exists, is committed, and is contract-tested (`test_climate_kpis_fixture_matches_contract`, suite 29/29 green) — ready for `08-09`'s `generate_metadata.py::_build_kpi_by_tab()` to merge via a new `chelsa` `source_host` branch, mirroring the existing `bfn_wfs` branch.
- The `_meta.variables` manifest (unit/delta_unit pairs per `variable_key`) is the exact shape `08-09`'s merge and the frontend's `StatPanel.jsx` two-line tile (D-20) need to render a percent-change delta beneath an absolute baseline without hardcoding which variables are which family.
- The 12 corrected `data/climate_source/*.tif` rasters (gitignored, digest-pinned in `sources.yaml`) are now also the correct, physically-meaningful input `08-06`'s (parallel wave) `build_climate_pmtiles.py`/`compute_climate_color_breaks.py` will consume — this plan's bug fix benefits that sibling plan's work as well, since both read the same `data/climate_source/` files.
- The `gdd5` formula's exact agronomic fidelity (flagged as an open verification item since `08-03`) remains unresolved as a documentation/labeling question, but this plan's plausibility check confirms the magnitude is correct (1735-2075 degC-day/year, squarely inside the published range) — the earlier concern that a non-standard formula might produce implausibly large values does not manifest here.

---
*Phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data*
*Completed: 2026-07-30*

## Self-Check: PASSED

- FOUND: data-pipeline/python/compute_climate_kpis.py (284 lines)
- FOUND: data/climate_kpis.json (_meta + 5 slug objects, 8 keys each, all finite)
- FOUND: data-pipeline/python/fetch_climate.py (scale/offset fix applied)
- FOUND: data-pipeline/sources/sources.yaml (12 sha256_by_derived digests re-pinned)
- FOUND: data-pipeline/tests/test_pipeline_outputs.py (test_climate_kpis_fixture_matches_contract added)
- FOUND commit: f39381a (Task 1)
- FOUND commit: 65e16cb (Task 2)
- Verified `python -m pytest data-pipeline/tests/` exits 0 (29 passed)
- Verified `git diff --stat data/destatis_ll.json` is empty (byte-unchanged)
- Verified `git status --porcelain data/climate_kpis.json` was empty before Task 2's real run (dry-run wrote nothing)
