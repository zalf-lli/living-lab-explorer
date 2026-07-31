---
status: fixed_pending_human_verify
trigger: "for all of the change maps the number of categories is too coarse and all cells are falling into the same categories leading to uniformly coloured maps."
created: 2026-07-31
updated: 2026-07-31
phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data
related_plan: 08-11
---

## Symptoms

- **Expected behavior:** In Change mode (either horizon), the map should show visible per-pixel
  variation in the change colour ramp, discriminating meaningful differences in projected change
  across a Living Lab's area — matching the apparent design intent of a multi-class sequential/
  diverging ramp (`CLIMATE_RAMP_SHAPE`, `data/climate_color_breaks.json`).
- **Actual behavior:** For all four variables' Change maps, the number of effectively-used colour
  categories is too coarse — most or all cells fall into the same 1-2 bins, producing a uniformly
  (or near-uniformly) coloured map with little to no visible spatial variation.
- **Scope (user-clarified):** Mixed severity — some Living-Lab/period/variable combinations render as
  effectively single-colour (one uniform shade across nearly the whole map), others show a few cells
  in different classes but the vast majority still cluster into 1-2 bins. Severity depends on which
  Living Lab and which future period (2041-2070 vs 2071-2100) is being viewed.
- **Error messages:** None reported — purely a visual/classification artifact, not a crash or console
  error.
- **Timeline:** First observed during the Phase 8 (`08-11`) blocking human-verification checkpoint
  (2026-07-31) — this is new CHELSA change-mode raster data, no prior working state to compare
  against.
- **Reproduction:** Open any Living Lab's Climate tab, click "Change", select either horizon
  (2041-2070 or 2071-2100), and view any of the four variables. The map shows little to no colour
  variation across the Living Lab's extent.

## Related context

Reported alongside 5 other Phase 8 checkpoint defects (see
`.planning/phases/08-add-maps-and-stats-for-climate-variables-using-chelsa-data/08-EVIDENCE.md`
`## Reported issues` section). The user flagged this issue and the boundary-NA-artifact issue as
*possibly* sharing a root cause; the boundary artifact investigation
(`.planning/debug/resolved/climate-boundary-na-artifact.md`) found its cause was purely a frontend
masking-opacity issue (`app/src/components/LLMap/index.jsx`'s `MASK_STYLE` at 60% opacity), NOT a
pipeline classification/nodata bug — so that shared-cause hypothesis is now much less likely for
this issue, though not entirely ruled out (worth a quick sanity check: does an already-hidden buffer
ring change the *visible* colour distribution enough to explain "uniform" impressions? Probably not,
since the true LL polygon interior is what's being judged, but note this in evidence gathering).

Likely relevant pipeline files (not yet confirmed):
- `data-pipeline/python/compute_climate_color_breaks.py` — Pass 0, computes the `change`-mode
  colour breakpoints per variable, pooling across all 5 Living Labs and (per `08-EVIDENCE.md`
  Deliberate deviation #2) pooling BOTH horizons (2041-2070 and 2071-2100) together into one shared
  change scale per variable
- `data/climate_color_breaks.json` — the committed breakpoints and `per_ll_means` this task should
  inspect directly for bin-edge spacing vs. actual per-pixel change distribution
- `data-pipeline/python/build_climate_pmtiles.py` — Pass 1, classifies pixels into bins using the
  Pass-0 breakpoints and bakes the PNG palette

## Current Focus

- **hypothesis:** CONFIRMED (see Evidence). `compute_climate_color_breaks.py`'s change-mode
  breaks pool BOTH horizons (2041_2070 + 2071_2100) into one 4-bin sequential percentile scale
  (deliberate deviation #2, 08-EVIDENCE.md). The two horizons form two well-separated clusters
  (delta magnitude ~1.0-1.5 units apart), while a single LL+horizon's own spatial pixel range is
  only ~10-25% as wide as that between-horizon gap. The 4-bin budget is therefore consumed mostly
  by separating the two horizons from each other, leaving each individual map (one LL, one
  horizon) only 1-2 of the 4 bins to work with — and many LLs' local range falls entirely inside
  one bin, producing pure single-colour maps. This directly explains both the overall "too
  coarse" symptom and the "mixed severity by LL and period" pattern.
- **decision needed:** whether to reverse deliberate deviation #2 (compute breaks per-horizon
  instead of pooled) — see CHECKPOINT below. This conflicts with a previously human-locked design
  decision recorded in `08-EVIDENCE.md`, so escalating rather than unilaterally reversing it.
- **test:** Simulated per-horizon-only breaks (pooling only across the 5 LLs, not across
  horizons) against the same real committed rasters, to check whether reversing the pooling
  decision would actually fix the symptom.
- **expecting:** If per-horizon breaks show visibly better within-map class spread than the
  current pooled breaks, this confirms pooling-across-horizons (not some other pipeline bug) is
  the root cause, and reversing it is a viable fix direction.
- **decision received:** User chose Option A plus widening to 5 classes ("I would like Option A
  but also expand to five bins"). Implemented and gate-verified — see Resolution below.
- **next_action:** Human visual re-verification of the rendered Change maps, deferred to the
  08-11 Task 3 checkpoint re-run alongside the other pending Phase 8 fixes.

## Evidence

- timestamp: 2026-07-31T00:00:00Z
  checked: `data/climate_color_breaks.json` change-mode `breaks`/`per_ll_means` for all 4
  variables, cross-referenced against `compute_climate_color_breaks.py`'s `_sequential_breaks()`
  (plain 0/25/50/75/100 percentiles of the pooled-across-both-horizons-and-5-LLs array).
  found: Breaks are wide (e.g. bio1 change: `[2.4, 2.6, 3.3, 4.0, 4.3]`, total span 1.9 degC)
  because they must cover both the 2041-2070 cluster (~2.4-2.8 degC) and the 2071-2100 cluster
  (~3.8-4.3 degC) — a ~1-degree gap between clusters with almost no data in it.
  implication: The pooled range is dominated by between-horizon separation, not within-map
  spatial variation, suggesting the 4-bin budget will mostly get "spent" separating horizons
  rather than discriminating pixels within one map.

- timestamp: 2026-07-31T00:05:00Z
  checked: Loaded real committed `data/climate_source/chelsa-{variable}-{period}.tif` rasters,
  clipped each of the 5 LLs x 2 horizons x 4 variables using the exact same
  `build_clip_geometry()` Pass-0/Pass-1 use, and histogrammed each LL+horizon's real pixel values
  against the actual committed `climate_color_breaks.json` breaks.
  found: Every single one of the 40 (variable x horizon x LL) combinations has one dominant bin
  containing 43-100% of pixels; most are 60-100%. E.g. bio1 2041_2070/hessian-low-mountain:
  100% in one bin (min=2.36, max=2.52, entirely inside a single bin's [2.4,2.6)-adjacent range).
  bio18 2071_2100 for 3 of 5 LLs (hessian-low-mountain, north-hessian-loess, rheingau): 100% in
  one bin. Severity varies by LL because some LLs' narrow local range happens to straddle a break
  boundary (partial split) while others fall entirely inside one bin (pure uniform colour) —
  matches the user-reported "mixed severity by LL and period" scope exactly.
  implication: Confirms the reported symptom precisely and quantitatively — this is not a
  reporting exaggeration, every combination is measurably coarse, with roughly half being
  literally 100% single-colour.

- timestamp: 2026-07-31T00:10:00Z
  checked: Simulated an alternative breaks computation — same `_sequential_breaks()` percentile
  logic, but pooling ONLY across the 5 LLs for a single horizon (not across both horizons), then
  histogrammed the same real per-LL pixel data against these per-horizon breaks.
  found: Dominant-bin percentage drops substantially for the large majority of combinations (e.g.
  bio1 2041_2070 dominant bins fall to 51-59% across all 5 LLs, vs. 78-100% under the current
  pooled scheme; bio12 2041_2070 east-brandenburg spreads across all 4 bins 16/17/23/45% instead
  of a 2-bin 53/47% split). A handful of combinations remain single-bin even under per-horizon
  breaks (e.g. bio18 rheingau both horizons, bio12 2071_2100 north-hessian-loess) — those appear
  to be cases where that specific LL's true intra-map spatial variability is itself very small
  (an intrinsic property of the smoothed CHELSA data for that small/flat region), not a
  classification artifact.
  implication: Confirms pooling-across-horizons is the dominant, fixable cause of the coarse-bins
  symptom (not e.g. a pipeline nodata/classification bug) — reversing deliberate deviation #2
  (compute change-mode breaks per-horizon, not pooled) would substantially improve, though not
  perfectly eliminate, the coarse-bin symptom. The remaining few near-uniform cases reflect real
  data characteristics, not a bug.

- timestamp: 2026-07-31T00:12:00Z
  checked: Whether the already-resolved `climate-boundary-na-artifact` masking-opacity issue
  (60% dimming of the 2km clip buffer ring) could explain or contribute to this issue, per the
  "Related context" note in this file.
  found: The dominant-bin percentages above were computed directly from clipped raster pixel
  values inside the true LL boundary (via `build_clip_geometry()`), not from rendered map pixels
  — the frontend mask/opacity layer plays no role in this measurement at all.
  implication: Ruled out — the two issues are unrelated; this is purely a Pass-0
  classification/breaks statistics issue, confirming the note in "Related context" that a shared
  root cause was unlikely.

## Eliminated

- hypothesis: Shared root cause with `climate-boundary-na-artifact` (frontend masking opacity
  affecting perceived colour distribution).
  evidence: Dominant-bin percentages were computed from raw clipped pixel values (independent of
  any frontend rendering/masking), and are extreme (many at 100%) even measured this way — the
  coarseness exists in the underlying classification, not in how it's displayed.
  timestamp: 2026-07-31T00:12:00Z

- hypothesis: Pipeline classification/nodata bug in `build_climate_pmtiles.py` (Pass 1)
  misapplying the Pass-0 breakpoints, or nodata contamination skewing the pooled statistics.
  evidence: Breaks in `climate_color_breaks.json` are internally consistent with
  `_sequential_breaks()`'s stated percentile logic when checked by hand against the raw pooled
  array; the coarseness is fully explained by the pooled array's own bimodal (two-horizon-cluster)
  shape, with no unexplained residual once that's accounted for.
  timestamp: 2026-07-31T00:10:00Z

## Resolution

root_cause: "compute_climate_color_breaks.py's change-mode breaks pool BOTH future horizons
(2041_2070 and 2071_2100) together (deliberate deviation #2, 08-EVIDENCE.md) into one 4-bin
0/25/50/75/100-percentile sequential scale per variable. Because the two horizons form two
well-separated value clusters (the between-horizon gap is roughly 3-5x wider than any single
LL+horizon's own true spatial pixel range), the 4-bin budget is consumed mostly by separating the
two horizons from each other rather than by discriminating real per-pixel spatial variation
within any single map view. Confirmed by direct histogram of real committed CHELSA rasters: every
one of 40 (variable x horizon x LL) combinations has 43-100% of pixels in one dominant bin, and a
simulated per-horizon (non-pooled) breaks scheme substantially improves within-map class spread
for the large majority of cases."
fix: |
  Human decision at checkpoint: Option A (per-horizon breaks) plus widen to 5 classes.
  Implemented across:
  - `data-pipeline/python/compute_climate_color_breaks.py`: `_sequential_breaks()` now takes
    `n_classes` (4 for baseline, unchanged; 5 for change); `_compute_block()` computes one block
    per horizon token instead of pooling both; added `HEAT_RAMP_CHANGE`/`WATER_RAMP_CHANGE`
    5-stop ramps (existing 4-stop family + one new darkest stop each).
  - `app/src/theme.js`: added `C.orangeDeepest` (`#9f350e`) and `C.tealDeepest` (`#00312f`),
    each a documented one-step continuation of its family's existing darkening progression, used
    only by change-mode ramps.
  - `app/src/data/layers.js`: added `CLIMATE_HEAT_RAMP_CHANGE`/`CLIMATE_WATER_RAMP_CHANGE`
    mirroring the Python side.
  - `data-pipeline/python/build_climate_pmtiles.py`: classifiers now keyed by
    `(variable_id, period_token)` instead of `(variable_id, mode)`, resolving each horizon's own
    breaks block via `_block_for_period()`.
  - `data-pipeline/sync.py::generate_climate_legend()`: `CLIMATE_LEGEND[variable].change` and
    `CLIMATE_RAMP_SHAPE[variable].change` are now keyed by horizon token instead of being one
    flat block.
  - `app/src/components/LLMap/index.jsx`: legend band selection now reads
    `CLIMATE_LEGEND[variable].change[horizon]` instead of `.change`.
  - `data-pipeline/tests/check_color_breaks.py`: updated to check both horizons' ramp verdicts
    per variable.
  - All 40 change-mode PMTiles (4 variables x 2 horizons x 5 Living Labs) rebaked via
    `build_climate_pmtiles.py`; baseline's 20 PMTiles and 4-class ramp are untouched.
  - `08-EVIDENCE.md` updated: deviation #2 marked superseded (with a pointer to this session and
    the new deviation #5), deviation #5 added recording the fix and the human's checkpoint
    decision, and "Reported issues" #4 marked fixed.
verification: |
  `python -m pytest data-pipeline/tests/ -q` — 31/31 passing.
  `python data-pipeline/tests/check_color_breaks.py` — all 4 variables report
  `change=(2041_2070=sequential, 2071_2100=sequential)`.
  `python data-pipeline/sync.py` — regenerated `climate_legend.js`/`layer_sources.js`; confirmed
  `CLIMATE_LEGEND.gdd.change` now has 2 horizon keys each with 5 bands, `.baseline` still 4 bands.
  `npm run lint` and `npm run build` (in `app/`) — both clean.
  Quantitative before/after: `bio1` 2041-2070 dominant-bin share dropped from 78-100% to 51-59%
  across all 5 Living Labs (matches the pre-fix simulation in Evidence above).
  Not yet done: human visual re-verification in a running dev server (deferred to the 08-11 Task 3
  checkpoint re-run, alongside the other pending Phase 8 fixes) — this session's automated/gate
  verification is complete, but nobody has looked at the actual rendered map since the fix landed.
files_changed:
  - data-pipeline/python/compute_climate_color_breaks.py
  - data-pipeline/python/build_climate_pmtiles.py
  - data-pipeline/sync.py
  - data-pipeline/tests/check_color_breaks.py
  - app/src/theme.js
  - app/src/data/layers.js
  - app/src/components/LLMap/index.jsx
  - data/climate_color_breaks.json
  - 40 files under data/pmtiles/climate-{bio1,bio12,bio18,gdd}-{2041_2070,2071_2100}-*.pmtiles
    (and their app/public/data/pmtiles/ mirrors)
  - app/src/data/climate_legend.js (codegen'd)
  - app/src/data/layer_sources.js (codegen'd)
  - .planning/phases/08-add-maps-and-stats-for-climate-variables-using-chelsa-data/08-EVIDENCE.md
