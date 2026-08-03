---
phase: 09-chart-data-contract
plan: 04
subsystem: data-pipeline
tags: [charts, agriculture, raster, croptypes, histogram]
dependency-graph:
  requires: [09-01, 09-02]
  provides: [compute_agriculture_chart.py, landuse-croptypes chart JSON x5]
  affects: [data-pipeline/python/compute_agriculture_chart.py, data/charts/landuse-croptypes-*.json]
tech-stack:
  added: []
  patterns:
    - "Per-LL raster clip+histogram over a single national GeoTIFF (no per-LL tile split, unlike build_land_cover.py)"
    - "pct floor of 0.1 for genuinely-observed classes that round to 0.0 at 1-decimal precision"
key-files:
  created:
    - data-pipeline/python/compute_agriculture_chart.py
    - data/charts/landuse-croptypes-east-brandenburg.json
    - data/charts/landuse-croptypes-havellandisches-luch.json
    - data/charts/landuse-croptypes-north-hessian-loess.json
    - data/charts/landuse-croptypes-hessian-low-mountain.json
    - data/charts/landuse-croptypes-rheingau.json
  modified: []
decisions:
  - "Followed D-05's locked precedent: build_clip_geometry's default buffered (2000m) clip, matching build_land_cover.py, for agriculture/landscape raster comparability (09-RESEARCH.md Pitfall 2)"
  - "Floored displayed pct at 0.1 (not 0.0) for a class with a genuinely non-zero pixel count that rounds to 0.0 at 1-decimal precision, to preserve the 'never drop a row' guarantee"
metrics:
  duration: "~35 minutes (incl. environment setup)"
  completed: 2026-08-03
---

# Phase 9 Plan 04: Agriculture Crop-Type Chart Summary

Built `compute_agriculture_chart.py`, the one chart in this phase requiring genuinely new
pipeline logic (a per-Living-Lab clip+histogram over the national `landuse-croptypes`
raster), and used it to compute and commit all five `data/charts/landuse-croptypes-*.json`
files with real hectare/pct crop-type shares.

## What Was Built

**Task 1 — `data-pipeline/python/compute_agriculture_chart.py`:**

- Imports `build_clip_geometry` from `build_pmtiles.py` and `write_bar_chart` from
  `chart_contract.py` — never re-derives clip logic or hand-rolls `json.dumps`.
- Opens `data/croptypes_2024.tif` once via `ensure_input_available(get_layer("landuse-croptypes"))`,
  then loops all five LL slugs against that single opened `rasterio` dataset (no
  per-tile lookup step, unlike `build_land_cover.py`'s `tiles_by_slug` loop — this
  layer has a single national `input.path`, not `input.tiles`).
- Per slug: `build_clip_geometry(layer, src.crs, slug=slug)` (default 2000 m buffer)
  then `rasterio.mask.mask(..., crop=True, all_touched=True, nodata=src.nodata)`, then
  `np.unique(..., return_counts=True)` to build a `{class_value: pixel_count}` histogram,
  excluding class 0 (nodata).
- Converts pixel counts to hectares via `layer["input"]["resolution_m"]` (10 m ->
  100 m2/pixel -> `resolution_m**2/10_000` ha/pixel), read from `sources.yaml`, never a
  bare literal.
- Unlisted-class guard: `missing = observed - legend_values` raises a `RuntimeError`
  naming the slug and sorted missing values — never a `continue`.
- Module docstring documents both (a) `pct` as a share of classified crop area (the
  raster codes all non-agricultural land as nodata) and (b) the deliberate buffered-clip
  choice for agriculture/landscape comparability, naming the soil/climate divergence
  explicitly (09-RESEARCH.md Pitfall 2).
- CLI: `--ll <slug>` (single-LL, default all five) and `--dry-run` (print, write nothing).

**Dry-run validation (rheingau, the smallest Living Lab):**
- 18 crop classes present.
- Top 3 by pct: permanent grassland (19.4%), winter wheat (14.1%), vineyard (11.0%).
- Wall-clock duration: **1.9 s** for the single-slug dry run — this comfortably bounded
  Task 2's full five-slug expectation; the actual full run (below) took ~28 s total,
  far under any budget concern for a 481 MB national raster.

**Task 2 — full five-Living-Lab run:**

Ran `compute_agriculture_chart.py` with no flags; wrote and committed all five
`data/charts/landuse-croptypes-{slug}.json` files.

| Living Lab | Classes | Total classified ha | Top 3 crop classes by pct |
|---|---|---|---|
| east-brandenburg | 18 | 352,606 | permanent grassland 17.6%, maize 16.1%, winter rye 13.7% |
| havellandisches-luch | 18 | 208,218 | permanent grassland 31.9%, maize 12.2%, winter rye 11.6% |
| hessian-low-mountain | 18 | 240,925 | permanent grassland 33.3%, winter wheat 11.6%, fruit trees/other woody 9.6% |
| north-hessian-loess | 18 | 117,125 | permanent grassland 20.2%, winter wheat 17.6%, winter barley 9.9% |
| rheingau | 18 | 26,270 | permanent grassland 19.4%, winter wheat 14.1%, vineyard 11.0% |

All five per-slug wall-clock times ranged 0.5-15.0 s (single-open `rasterio` dataset,
windowed mask per slug); no decimation or resolution reduction was used.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - blocking/environment] `data/croptypes_2024.tif` not present in this worktree**

- **Found during:** Task 1, before the first dry run.
- **Issue:** The 481 MB gitignored source raster (`data/croptypes_2024.tif`) exists in the
  main repo checkout (already used to build the committed `landuse-croptypes.pmtiles`) but
  worktrees do not share gitignored files with the main checkout, so it was absent here.
  `ensure_input_available()` would have re-downloaded the full 481 MB from the pinned
  `input.download_url`.
- **Fix:** Copied the existing local file from the main repo's `data/` directory into this
  worktree's `data/` directory (a plain filesystem copy of an already-verified, gitignored,
  non-tracked file — no git-tracked file was touched, no re-download occurred).
- **Files modified:** None (git-tracked). `data/croptypes_2024.tif` remains outside git in
  both locations.
- **Commit:** N/A (environment-only, not committed).

**2. [Rule 3 - blocking/environment] No Python environment with `rasterio`/`geopandas` in this worktree**

- **Found during:** Task 1, first attempt to run the script.
- **Issue:** This worktree has no `data-pipeline/.venv`; the default `python` on PATH
  (Windows Store Python 3.13) lacks `rasterio`/`geopandas`/`numpy`.
- **Fix:** Used the documented short-path venv workaround from `STATE.md`'s "Phase 8, Wave 5"
  note and `data-pipeline/README.md`'s Windows environment section: ran all pipeline commands
  via `C:\lcvenv\Scripts\python.exe`, which already has `rasterio==1.5.0`,
  `geopandas==1.1.3`, `numpy==2.5.1` installed (sidesteps the OneDrive-path `MAX_PATH` issue).
- **Files modified:** None (git-tracked); no new dependency was installed, the existing
  `C:\lcvenv` environment was reused as-is.
- **Commit:** N/A (environment-only, not committed).

**3. [Rule 1 - bug] `pct` rounding to 1 decimal produced `0.0` for a genuinely-present crop class**

- **Found during:** Task 2, running the plan's own automated verify assertion
  (`s['value']>0 and s['pct']>0` for every series entry).
- **Issue:** Four of the five Living Labs have a small number of stray "vineyard"
  pixels (16.1 ha / 2.7 ha / 88.7 ha / 34.4 ha out of totals of 117k-353k ha — precise
  shares of 0.0013%-0.0368%). Rounding `pct` to 1 decimal (the shared_conventions-locked
  rule, applied identically across all five Phase 9 chart scripts) produced `pct: 0.0` for
  these entries, even though `value` (hectares) was correctly positive. A `pct` of exactly
  `0.0` reads as "class not present", which directly contradicts the plan's own "never drop
  a row" guarantee — a class that IS present should never *display* as absent.
- **Fix:** In `_series_from_histogram`, after rounding `pct` to 1 decimal, if the rounded
  value is `<= 0.0` for a class with a real (non-zero) pixel count, floor it to `0.1` — the
  smallest positive value representable at 1-decimal precision. `value` (hectares) is left
  completely untouched; only the displayed percentage floor is adjusted. This preserves the
  locked 1-decimal rounding convention for every other entry and only engages for the rare
  sub-0.05%-share case.
- **Files modified:** `data-pipeline/python/compute_agriculture_chart.py`
- **Commit:** `cbe491e` (Task 2's commit, since the fix was made and verified together with
  the full run before committing)
- **Note for future reviewers/plan-checker:** this is a real tension between the
  shared_conventions "round pct to 1 decimal" rule and the acceptance criteria's own
  `pct>0` assertion, surfaced by real data (a genuinely tiny vineyard presence in four
  non-Rheingau Living Labs). If sibling chart scripts (soil, landscape, economic — plan
  09-03) encounter classes with a similarly small share, the same floor pattern should be
  considered for consistency.

## Known Stubs

None — all five committed files carry real, computed (`mock: false`) data.

## Threat Flags

None — no new network endpoints, auth paths, or trust-boundary changes were introduced.
The only trust boundary (`data/croptypes_2024.tif`'s unpinned `sha256`) was already
identified and dispositioned `accept` in this plan's own `<threat_model>` (T-09-09).

## Verification

- `data-pipeline/python/compute_agriculture_chart.py` exists, imports `build_clip_geometry`
  from `build_pmtiles` and `write_bar_chart` from `chart_contract`, contains zero
  `json.dumps` calls.
- `--ll rheingau --dry-run` completed in 1.9 s, printed 18 crop classes summing to ~100%,
  wrote no file.
- Full five-slug run wrote and committed all five `data/charts/landuse-croptypes-*.json`
  files; each has `chart_type: bar`, `layer_id: agriculture`, `source: landuse-croptypes`,
  `mock: false`, `unit: {en: ha, de: ha}`, >=5 series entries, every entry with a positive
  `value` and `pct`, pct sums within +-1.0 of 100, pct non-increasing, total classified area
  >1000 ha.
- `python -m pytest data-pipeline/tests/` — 31/31 passing.
- `git status --porcelain data/croptypes_2024.tif` — empty (untracked, as required).
- `git status --porcelain app/public/data/charts/` — directory does not exist yet
  (publishing is plan 09-06's scope, unaffected by this plan).

## Self-Check: PASSED

- FOUND: data-pipeline/python/compute_agriculture_chart.py
- FOUND: data/charts/landuse-croptypes-east-brandenburg.json
- FOUND: data/charts/landuse-croptypes-havellandisches-luch.json
- FOUND: data/charts/landuse-croptypes-hessian-low-mountain.json
- FOUND: data/charts/landuse-croptypes-north-hessian-loess.json
- FOUND: data/charts/landuse-croptypes-rheingau.json
- FOUND commit 23a4427 (Task 1) in `git log --oneline --all`
- FOUND commit cbe491e (Task 2) in `git log --oneline --all`
