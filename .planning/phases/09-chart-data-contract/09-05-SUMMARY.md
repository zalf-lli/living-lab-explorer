---
phase: 09-chart-data-contract
plan: 05
subsystem: data-pipeline
tags: [climate, chelsa, line-chart, chart-contract]
dependency-graph:
  requires:
    - "09-01: chart_contract.py write_line_chart()"
    - "09-02: sources.yaml chart.script + output.chart_pattern + climate.variables.*.label"
  provides:
    - "data-pipeline/python/compute_climate_chart.py"
    - "data/charts/chelsa-climate-{slug}.json (5 files)"
  affects:
    - "09-06 (sync.py publishes these 5 files to app/public/data/charts/)"
    - "09-07 (phase close-out checkpoint reads this chart's sign/magnitude table)"
tech-stack:
  added: []
  patterns:
    - "import area_weighted_mean from compute_climate_kpis.py rather than re-deriving it"
    - "line-variant chart_type (x_axis + lines, no series) as the one CHARTS-07 discriminator proof"
    - "percent-change normalization across heat-family (absolute change_mode) and water-family (percent change_mode) variables to share one axis"
key-files:
  created:
    - data-pipeline/python/compute_climate_chart.py
    - data/charts/chelsa-climate-east-brandenburg.json
    - data/charts/chelsa-climate-havellandisches-luch.json
    - data/charts/chelsa-climate-north-hessian-loess.json
    - data/charts/chelsa-climate-hessian-low-mountain.json
    - data/charts/chelsa-climate-rheingau.json
  modified: []
decisions:
  - "D-08/D-09/D-16/D-21 all confirmed as specified in 09-CONTEXT.md/09-RESEARCH.md/09-PATTERNS.md; no deviation from locked interface values"
metrics:
  duration: "~40 min"
  completed: 2026-08-03
---

# Phase 9 Plan 5: CHELSA Climate Line Chart Summary

Built `compute_climate_chart.py`, the only `line`-variant chart producer in Phase 9, and
committed all five per-Living-Lab `data/charts/chelsa-climate-{slug}.json` files. Each file
carries four lines (gdd, bio1, bio12, bio18) x two horizon points (2041-2070, 2071-2100),
all expressed as percent change against the 1981-2010 baseline — the near horizon computed
fresh from the raster since `compute_climate_kpis.py` (Phase 8 D-21) never opens it.

## What Was Built

**Task 1 — `data-pipeline/python/compute_climate_chart.py` (commit `d5f2bbe`):**
- Imports `area_weighted_mean` from `compute_climate_kpis` (never re-derived) and
  `write_line_chart` from `chart_contract` (script contains zero `json.dumps` calls).
- Boundary setup mirrors `compute_climate_kpis.py::main()` exactly: `gpd.read_file()` →
  `make_valid()` → CRS/column guards → `to_crs("EPSG:25832")` once.
- `pct_change_for_horizon()`: for `change_mode: percent` variables (bio12, bio18) the
  horizon raster's area-weighted mean is used directly (already a percent-change field
  per `fetch_climate.py::_derive_change_field`); for `change_mode: absolute` variables
  (gdd, bio1) the horizon mean is converted to `horizon_value / baseline_mean * 100.0`.
  An unknown `change_mode` raises `ValueError`.
- `lines_for_slug()` builds `x_axis` from `climate.horizons` (sorted keys: `2041_2070`
  then `2071_2100`, labels read verbatim from the config's display strings, no
  `.replace()` string-munging) and `lines` in the Phase 8 D-08 locked variable order
  (gdd, bio1, bio12, bio18), each line's label read from
  `climate.variables.{id}.label` — no Python string literal for any variable display
  name, `app/src/i18n.js` never read.
- Twelve-file raster-existence guard (`_guard_rasters_exist`) checks all
  4-variables x 3-periods paths before any compute call and names
  `fetch_climate.py` in its `RuntimeError` message if any are missing.
- Module docstring records the three required facts: (a) the near horizon is computed
  here because Phase 8 D-21 never opens it, so this is not a pure `climate_kpis.json`
  reshape; (b) all four variables share one percent-change axis, deliberately
  overriding `StatPanel`'s unit-aware delta tiles (Phase 8 D-11) per Phase 9's D-09;
  (c) percent change of a Celsius quantity is scale-dependent (the Celsius zero is
  arbitrary) — gdd's and bio1's percentages are a comparability device for this chart
  only, not a physical rate for reuse elsewhere.
- CLI matches every other chart script: `--ll <slug>` restricts to one Living Lab,
  `--dry-run` prints and writes nothing, an unknown `--ll` raises listing available
  slugs.

**Task 1 four-way rheingau cross-check** (far-horizon chart point vs. `climate_kpis.json`
stored delta, reconciled as `stored_delta / stored_baseline * 100` for absolute-family
variables and directly for percent-family variables):

| Variable | Chart 2071-2100 | KPI-derived expected | Diff |
|---|---|---|---|
| Growing degree days (gdd, absolute) | 60.6 | 60.6 | 0.0 |
| Mean annual temperature (bio1, absolute) | 44.1 | 43.8 | 0.3 |
| Annual precipitation (bio12, percent) | 1.9 | 1.9 | 0.0 |
| Precipitation of warmest quarter (bio18, percent) | -9.8 | -9.8 | 0.0 |

All four agree within rounding; the 0.3pp bio1 difference is expected — the KPI-derived
"expected" value is computed from `climate_kpis.json`'s already-rounded (1-decimal)
baseline and delta figures, while the chart computes the ratio from full-precision
internal means before its own final rounding.

**Task 2 — five committed chart files (commit `9b91731`):**
- Ran `python python/compute_climate_chart.py` with no flags, writing all five
  `data/charts/chelsa-climate-{slug}.json` files.
- Full 20-cell far-horizon reconciliation (5 Living Labs x 4 variables) against
  `data/climate_kpis.json`, same methodology as the Task 1 four-way check:

| Living Lab | gdd diff | bio1 diff | bio12 diff | bio18 diff |
|---|---|---|---|---|
| east-brandenburg | 0.0 | 0.4 | 0.0 | 0.0 |
| havellandisches-luch | 0.0 | 0.2 | 0.0 | 0.0 |
| hessian-low-mountain | 0.0 | 0.2 | 0.0 | 0.0 |
| north-hessian-loess | 0.0 | 0.3 | 0.0 | 0.0 |
| rheingau | 0.0 | 0.3 | 0.0 | 0.0 |

  All 20 cells pass within rounding. Largest observed absolute discrepancy: **0.4
  percentage points** (east-brandenburg, mean annual temperature) — same rounded-input
  artifact as the Task 1 rheingau check, not a defect.
- `data/climate_kpis.json`, `compute_climate_kpis.py`, `fetch_climate.py`, and
  `data/climate_source/` are all unmodified (`git status --porcelain` empty for all
  four).
- `python -m pytest data-pipeline/tests/` 31/31 passing (no new tests added by this
  plan; suite size matches the current baseline, not the plan text's stale "20/20"
  figure — same documented discrepancy 09-02-SUMMARY.md already recorded).
- `git status --porcelain app/public/data/charts/` reports nothing — the directory
  does not exist yet; publishing is plan 09-06's job.

**Per-Living-Lab sign/magnitude table** (near-horizon, far-horizon percent change; for
09-07's human checkpoint sanity check):

| Living Lab | gdd (near, far) | bio1 (near, far) | bio12 (near, far) | bio18 (near, far) |
|---|---|---|---|---|
| east-brandenburg | +32.7, +56.4 | +28.6, +44.0 | +1.4, +3.0 | -4.4, -5.3 |
| havellandisches-luch | +32.1, +55.6 | +27.5, +42.5 | +1.2, +2.7 | -4.3, -5.9 |
| hessian-low-mountain | +34.6, +60.5 | +28.2, +45.0 | +1.4, +2.9 | -5.7, -8.6 |
| north-hessian-loess | +35.6, +62.0 | +29.2, +46.2 | +0.7, +2.3 | -5.6, -8.7 |
| rheingau | +34.8, +60.6 | +27.7, +44.1 | +1.0, +1.9 | -6.9, -9.8 |

All gdd and bio1 (heat family) points are positive at both horizons across all five
Living Labs — consistent with warming under SSP3-7.0. bio12 (annual precipitation) is
positive and bio18 (warmest-quarter precipitation) is negative across all five Living
Labs and both horizons — a legitimate empirical result the plan explicitly flags as not
automatically wrong (precipitation signs may differ by Living Lab and horizon).

## Verification

- Task 1's automated verify command (dry-run + import/pattern grep assertions)
  printed `DRY-RUN-OK` after one edit (see Deviations).
- Task 2's automated verify command (full run + schema/contract assertion script +
  pytest + protected-file `git status` checks) all passed, printing `OK` with the
  full five-Living-Lab payload dump.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - blocking] Missing gitignored CHELSA source rasters in this worktree**
- **Found during:** Task 1, before first dry-run
- **Issue:** `data/climate_source/*.tif` (12 files, gitignored intermediates written
  by `fetch_climate.py`) did not exist in this git worktree — they are per-machine
  local files, not shared via git across worktrees.
- **Fix:** Copied all 12 `.tif` files from the main repository checkout's
  `data/climate_source/` directory into this worktree's `data/climate_source/`
  (a local file copy, not a re-download; no network fetch, no digest re-pinning).
- **Files modified:** none tracked by git (gitignored directory)
- **Commit:** n/a (not a git-tracked change)

**2. [Rule 1/self-correction] `DELTA_HORIZON` literal appeared in explanatory comments**
- **Found during:** Task 1, running the plan's automated verify command
- **Issue:** The plan's verify command asserts
  `grep -c 'DELTA_HORIZON' python/compute_climate_chart.py` equals 0 (the script must
  never reference that Phase 8 constant), but the module docstring and a code comment
  used the literal string `DELTA_HORIZON` while explaining why it is deliberately not
  imported.
- **Fix:** Reworded both passages to describe the constant's behavior ("the
  far-horizon-only constant") without spelling out its identifier.
- **Files modified:** `data-pipeline/python/compute_climate_chart.py`
- **Commit:** folded into `d5f2bbe` (fixed before the first commit; no separate commit)

### Environment note (not a code deviation)

Same dedicated pipeline venv used throughout Phase 8/9 (`C:\lcvenv\Scripts\python.exe`,
matching CLAUDE.md's "Python 3.12 required on Windows" constraint and
09-02-SUMMARY.md's precedent) was used for every script run and pytest invocation in
this plan — the worktree's default `python` on `PATH` was not tested but is expected to
have the same missing-`rasterio` issue documented in 09-02-SUMMARY.md.

## Known Stubs

None. All five committed chart files carry real computed values (no mock/placeholder
data); `mock: false` in every file.

## Threat Flags

None. No new network endpoints, auth paths, or trust-boundary changes — this plan only
reads already-fetched local rasters and already-committed config, and writes five new
JSON files under the same `data/charts/` directory pattern already accepted (T-09-15)
by plan 09-01/09-02's threat model.

## Self-Check

- `data-pipeline/python/compute_climate_chart.py`: FOUND
- `data/charts/chelsa-climate-east-brandenburg.json`: FOUND
- `data/charts/chelsa-climate-havellandisches-luch.json`: FOUND
- `data/charts/chelsa-climate-north-hessian-loess.json`: FOUND
- `data/charts/chelsa-climate-hessian-low-mountain.json`: FOUND
- `data/charts/chelsa-climate-rheingau.json`: FOUND
- Commit `d5f2bbe`: FOUND in `git log`
- Commit `9b91731`: FOUND in `git log`
