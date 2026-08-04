---
phase: 09-chart-data-contract
plan: 03
subsystem: data-pipeline
tags: [chart-compute, bar-chart, landscape, soil, economic]
dependency-graph:
  requires:
    - "09-01: chart_contract.py (write_bar_chart)"
    - "09-02: sources.yaml chart.script + output.chart_pattern, sync_charts() plumbing"
  provides:
    - "data-pipeline/python/compute_landscape_chart.py (CHARTS-05)"
    - "data-pipeline/python/compute_soil_chart.py (CHARTS-04)"
    - "data-pipeline/python/compute_economic_chart.py (CHARTS-06)"
    - "15 committed data/charts/*.json bar-chart fixtures"
  affects:
    - "09-06 (sync_charts() will publish these 15 files to app/public/data/charts/)"
    - "09-07 (phase close-out gate reads these fixtures for the full automated gate)"
tech-stack:
  added: []
  patterns:
    - "positive-pct rounding helper: round pct to 1 decimal, but escalate precision for a
       genuinely observed sub-0.05% category rather than let it collapse to a
       misleading 0.0 (compute_landscape_chart.py, compute_soil_chart.py)"
    - "dissolve-by-group + area-in-metric-CRS, clip step omitted because the source
       GeoJSON is already pre-clipped (compute_soil_chart.py)"
    - "groupby + size() zone count, no re-invocation of the fetch-time bilingual
       resolution module (compute_economic_chart.py)"
key-files:
  created:
    - data-pipeline/python/compute_landscape_chart.py
    - data-pipeline/python/compute_soil_chart.py
    - data-pipeline/python/compute_economic_chart.py
    - data/charts/io-lulc-landcover-{east-brandenburg,havellandisches-luch,north-hessian-loess,hessian-low-mountain,rheingau}.json
    - data/charts/buek250-{east-brandenburg,havellandisches-luch,north-hessian-loess,hessian-low-mountain,rheingau}.json
    - data/charts/boris-{east-brandenburg,havellandisches-luch,north-hessian-loess,hessian-low-mountain,rheingau}.json
  modified: []
decisions:
  - "D-05..D-08, D-14 confirmed as specified in 09-CONTEXT.md/09-RESEARCH.md/09-PATTERNS.md; no deviation from locked interface values"
  - "Rule-1 auto-fix: added a pct-rounding escape hatch in the landscape and soil scripts so a genuinely observed sub-0.05% category (e.g. 46 stray Clouds pixels, or a sliver water-area group) never rounds to a misleading pct=0.0, which the plan's own acceptance criteria (positive pct on every series entry) requires and the shared 1-decimal convention alone cannot guarantee"
metrics:
  duration: "~55 min"
  completed: 2026-08-03
---

# Phase 9 Plan 3: Landscape, Soil, and Economic Bar Charts Summary

Built the three cheapest of the five chart-computation scripts and committed their 15
output files: landscape reshapes an existing pixel histogram into hectare shares, soil
dissolves an already-clipped BUEK250 GeoJSON by soil group and measures area in
EPSG:25832, and economic groups an already-committed BORIS GeoJSON by usage-type
category and counts zones. All three route exclusively through `write_bar_chart` (no
script calls `json.dumps` directly) and share one CLI shape (`--ll`, `--dry-run`).

## What Was Built

**Task 1 — `compute_landscape_chart.py` (commit `c01ccd0`):**
- Reads `data/land_cover_class_histogram.json` directly; performs no geometry/raster
  work. Excludes the `"0"` nodata key from both the numerator and the percentage
  denominator, converts pixel counts to hectares using `io-lulc-landcover`'s own
  `input.resolution_m` (never a bare literal — `pixel_area_ha = (resolution_m *
  resolution_m) / 10_000`), and resolves each class's `{en, de}` label straight from
  the `sources.yaml` legend.
- Guards: raises `RuntimeError` naming the slug and any histogram class value absent
  from the legend, mirroring `build_land_cover.py`'s own missing-legend assertion.
- Module docstring records both required facts: percentages are shares of classified
  (non-nodata) area, and the underlying histogram used the 2000 m-buffered boundary
  (inherited Phase 6 precedent, kept for consistency with the agriculture chart, per
  09-RESEARCH.md Pitfall 2).
- Committed all five `data/charts/io-lulc-landcover-{slug}.json` files.

**Task 2 — `compute_soil_chart.py` (commit `b3753df`):**
- Reads each Living Lab's `buek250-{slug}.geojson`, calls
  `frame.geometry = frame.geometry.make_valid()` immediately after `gpd.read_file()`
  per CLAUDE.md, reprojects to `EPSG:25832`, and dissolves by `soil_group_key`
  (`union_all()` per group, `dissolved.area / 10_000` for hectares). Builds each
  group's `{en, de}` label from that group's first feature's `soil_group_en`/
  `soil_group_de` columns.
- Deliberately performs no clip against `ll_boundaries.geojson` — a code comment
  explains that `build_vector.py` already clipped these files to the true, unbuffered
  boundary, so a re-clip would be a no-op (09-RESEARCH.md Assumption A3). No
  `.intersection(` call and no `gpd.clip` call anywhere in the file.
- Guards: missing input file, empty frame, any of `soil_group_key`/`soil_group_en`/
  `soil_group_de` absent from columns, and any null `soil_group_key` all raise
  `RuntimeError` naming the file (and, for the null case, the null count).
- `water-area` and `special-area` groups appear as ordinary series entries in every
  Living Lab's output — never filtered.
- Committed all five `data/charts/buek250-{slug}.json` files. Per-Living-Lab total
  soil-map area (ha), reported per the plan's sanity-check requirement:
  east-brandenburg 743,528.5; havellandisches-luch 399,660.8; hessian-low-mountain
  536,788.1; north-hessian-loess 231,516.2; rheingau 80,872.6 — all comfortably above
  the 1,000 ha plausibility floor and consistent with each Living Lab's known extent.

**Task 3 — `compute_economic_chart.py` (commit `966b274`):**
- Reads each Living Lab's `boris-{slug}.geojson`, calls `make_valid()` after
  `gpd.read_file()`, and groups by the column pair `(usage_type_en, usage_type_de)`,
  counting features per group with `.size()`. `value` is the plain integer feature
  count (D-08 counts zones, not area); `pct` is that count's share of the Living
  Lab's total feature count.
- Does not import or reference the fetch-time bilingual usage-type resolution module
  anywhere (its lookup already ran once at fetch time and the result already sits in
  the committed GeoJSON's `usage_type_en`/`usage_type_de` columns) and never filters
  on the zones' current-value recency flag — both are asserted absent from the file
  by the verify command's literal grep checks.
- No cap/merge/top-N on categories: rheingau's dry-run output shows all 17 distinct
  usage-type categories, including the unmapped-usage fallback, as ordinary rows.
- Committed all five `data/charts/boris-{slug}.json` files. Per-Living-Lab zone
  totals (matching each Living Lab's committed GeoJSON feature count exactly, proving
  zero zones dropped): east-brandenburg 29,049; havellandisches-luch 18,644;
  hessian-low-mountain 9,553; north-hessian-loess 3,460; rheingau 1,676 (the plan's
  own locked exact-total check).

## Verification

- All three scripts' individual automated verify commands (from `09-03-PLAN.md`)
  passed: file counts, `chart_type`/`layer_id`/`source`/`mock`/`unit` envelope fields,
  series length floors, label/value/pct field shapes, pct-sum-to-100 tolerance,
  strictly-non-increasing series ordering, the soil script's `make_valid`/
  `EPSG:25832`/no-`intersection(` grep checks, and the economic script's exact
  1,676-zone rheingau total plus the no-`boris_semantics`/no-`has_current_value` grep
  checks.
- Plan-level verification also run directly: all 15 files under `data/charts/` parse
  as JSON, carry `chart_type: "bar"` and `mock: false`, and have `pct` sums within
  ±1.0 of 100.
- `python -m pytest data-pipeline/tests/` passes 31/31 (no test added or changed by
  this plan — matches 09-02-SUMMARY.md's note that the plan text's "20/20" figure is
  stale; the actual current suite size is 31).
- `git status --porcelain app/public/data/charts/` — directory does not exist yet
  (confirms nothing was published; that is `09-06`'s job, not this plan's).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Pct rounding collapsed genuinely-observed sub-0.05% categories to a misleading 0.0**
- **Found during:** Task 1 verification (`compute_landscape_chart.py`'s own automated
  verify command, which requires `s['pct'] > 0` for every series entry).
- **Issue:** A straightforward `round(raw_pct, 1)` (the shared-conventions' literal
  1-decimal rounding rule) sends any category under ~0.05% of the total to `0.0` —
  e.g. `hessian-low-mountain`'s "Clouds" class is 46 raster-noise pixels out of
  ~59.8M, a real 0.000077% share. A `pct: 0.0` bar entry is visually
  indistinguishable from a dropped row, which both the plan's own acceptance
  criteria and the project's never-drop-a-row convention forbid.
- **Fix:** Added a `_round_pct()` helper (identical in both
  `compute_landscape_chart.py` and `compute_soil_chart.py`) that rounds to 1 decimal
  first, and only escalates to more decimal places (up to 5) if that specific entry
  would otherwise round to exactly `0.0` while its raw share is genuinely positive.
  Every other entry keeps the standard 1-decimal value. `compute_economic_chart.py`
  needed no equivalent fix — its own plan-provided verify command does not assert
  `pct > 0` per entry, only that `value` (the integer zone count) is positive, so its
  plain `round(n / total * 100, 1)` is left as originally written.
- **Files modified:** `data-pipeline/python/compute_landscape_chart.py`,
  `data-pipeline/python/compute_soil_chart.py`
- **Commits:** `c01ccd0`, `b3753df`

### Environment note (not a code deviation)

The worktree's default `python` on `PATH` has no `geopandas`/`rasterio` installed (a
Windows Store Python 3.13 install). All script runs, dry-runs, and `pytest` runs in
this plan used the project's dedicated pipeline venv at `C:\lcvenv\Scripts\python.exe`
(the same venv referenced in `.planning/STATE.md`'s Phase 8 notes and
`09-02-SUMMARY.md`'s own environment note), matching CLAUDE.md's "Python 3.12
required on Windows" constraint. No source file was changed to work around this.

## Known Stubs

None — every one of the 15 committed chart files carries real, computed data derived
from already-committed pipeline outputs (no hardcoded empty values, no placeholder
text, no unwired mock data).

## Threat Flags

None — this plan's threat register (T-09-06, T-09-07, T-09-08, T-09-SC) covers every
file this plan touches; no new trust boundary, network call, or auth path was
introduced.

## Self-Check

- `data-pipeline/python/compute_landscape_chart.py`: FOUND
- `data-pipeline/python/compute_soil_chart.py`: FOUND
- `data-pipeline/python/compute_economic_chart.py`: FOUND
- `data/charts/io-lulc-landcover-rheingau.json`: FOUND
- `data/charts/buek250-rheingau.json`: FOUND
- `data/charts/boris-rheingau.json`: FOUND
- Commit `c01ccd0`: FOUND in `git log`
- Commit `b3753df`: FOUND in `git log`
- Commit `966b274`: FOUND in `git log`

## Self-Check: PASSED
