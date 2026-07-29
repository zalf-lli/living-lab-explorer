---
phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data
plan: 02
subsystem: ui
tags: [react, theme-tokens, kpi-tile, layers-registry, i18n-pending]

# Dependency graph
requires:
  - phase: 08-01
    provides: research spike deciding the static CHELSA acquisition shape (not consumed directly by this plan's pure frontend additions)
provides:
  - CLIMATE_HEAT_RAMP, CLIMATE_WATER_RAMP, CLIMATE_DIVERGING_RAMP exports in app/src/data/layers.js, built only from theme.js C.* tokens
  - resolveLayerAsset(layerId, { slug, variable, period }) — three-placeholder raster URL resolver that returns null instead of an unresolved-brace URL
  - StatPanel.jsx two-line KPI tile shape with an optional, independently-empty-able delta row
affects: ["08-05 (i18n keys incl. statPanel.byHorizon)", "08-09 (kpiByTab delta field production)", "08-10 (flips the climate LAYERS entry to raster and consumes the ramps + resolver)"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ramp-array exports built exclusively from theme.js C.* tokens, following the BORIS_RAMP precedent (zero literal hex in ramp arrays)"
    - "resolveLayerAsset generalized to a placeholder-substitution regex over {slug|variable|period} rather than per-key .replace() calls, returning null on any unresolved token"
    - "StatPanel tile delta row gated on `'delta' in field` (presence check) rather than truthiness, so a field with delta: null still renders the em-dash line"

key-files:
  created: []
  modified:
    - app/src/data/layers.js
    - app/src/components/StatPanel.jsx

key-decisions:
  - "resolveLayerAsset returns null (not a partially-substituted URL, not a fallback to pmtilesUrl) whenever any placeholder present in a raster pattern lacks a supplied value — matches the plan's explicit 404-diagnosability requirement (T-08-06 mitigation)"
  - "Delta row renders on its own line only when the field object has a 'delta' key at all; existing KPI entries from generate_metadata.py never carry that key today, so all four non-climate tabs are provably unaffected"
  - "Did not touch app/src/i18n.js per the plan's explicit instruction — statPanel.byHorizon renders as the raw key name until 08-05 lands, which only affects climate tiles that do not exist until 08-10"

patterns-established:
  - "Pattern: theme-token-only ramp array exports colocated with BORIS_RAMP in layers.js, ready for LLMap and future legend builders to import"
  - "Pattern: optional secondary KPI tile line keyed on property presence (`'delta' in field`), giving pipeline plans (08-09) an additive, non-breaking contract to write into"

requirements-completed: [D-11, D-13, D-20, D-21]

# Metrics
duration: ~20min
completed: 2026-07-29
---

# Phase 8 Plan 02: Climate Ramps + resolveLayerAsset Extension + StatPanel Delta Row Summary

**Added CLIMATE_HEAT_RAMP/CLIMATE_WATER_RAMP/CLIMATE_DIVERGING_RAMP theme-token exports, a three-placeholder resolveLayerAsset, and StatPanel's optional two-line KPI delta row — all additive, zero existing behavior changed.**

## Performance

- **Duration:** ~20 min
- **Completed:** 2026-07-29T12:08:35Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- `app/src/data/layers.js` now exports three CHELSA ramp constants (4/4/5 stops), built entirely from `theme.js` `C.*` tokens with zero new hex values, per D-13/D-12
- `resolveLayerAsset` generalized from a single `{slug}` placeholder to `{slug, variable, period}`, using a single regex substitution pass that returns `null` rather than emitting a URL with a literal unresolved brace — all four existing call sites (`landscape`, `soil`, `economic`, `agriculture`) verified unaffected
- `StatPanel.jsx`'s KPI tile grew an optional third line (12px/400/`C.muted`, 4px `marginTop`) rendered only when a field object carries a `delta` key, with independent em-dash fallbacks for baseline value and delta, and a unit fallback chain (`deltaUnit` → `unit`) supporting percent-family deltas under absolute baselines (D-11)

## Task Commits

Each task was committed atomically:

1. **Task 1: Export the climate ramps and extend resolveLayerAsset to three placeholders** - `b834d88` (feat)
2. **Task 2: Add the two-line delta row to the StatPanel KPI tile** - `5bf852e` (feat)

**Plan metadata:** (this commit, made after SUMMARY.md is written)

## Files Created/Modified
- `app/src/data/layers.js` - Added `CLIMATE_HEAT_RAMP`, `CLIMATE_WATER_RAMP`, `CLIMATE_DIVERGING_RAMP` exports; extended `resolveLayerAsset` to a generic `{slug|variable|period}` placeholder resolver
- `app/src/components/StatPanel.jsx` - Added the optional delta row inside the KPI tile map, gated on `'delta' in field`

## Decisions Made
- Implemented placeholder substitution as a single `replace(/\{(slug|variable|period)\}/g, ...)` pass with an `unresolved` flag rather than three sequential `.replace()` calls, so any single unresolved placeholder short-circuits the whole result to `null` (satisfies "no returned string ever contains `{` or `}`")
- Kept the `layer.pmtilesUrl` fallback branch reachable only when `pmtilesUrlPattern` is entirely absent (e.g. `agriculture`), matching the plan's instruction to leave that fallback unchanged
- Did not add the `statPanel.byHorizon` i18n key, per explicit plan instruction — documented as pending 08-05

## Deviations from Plan

None - plan executed exactly as written. `npm install` was run in `app/` because `node_modules` did not exist in this freshly-spawned worktree (not a plan deviation — a prerequisite for running the plan's own `npm run lint` / `npm run build` verification commands); no `package.json` or `package-lock.json` changes resulted.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `08-10` can now import `CLIMATE_HEAT_RAMP`/`CLIMATE_WATER_RAMP`/`CLIMATE_DIVERGING_RAMP` and call `resolveLayerAsset('climate', { slug, variable, period })` once the `climate` `LAYERS` entry flips from `type: 'placeholder'` to a real raster with a `pmtilesUrlPattern`
- `08-09` can now emit `delta`/`deltaUnit`/`deltaHorizon` on any `kpiByTab` entry and `StatPanel.jsx` will render it without further frontend changes
- `08-05` still owes the `statPanel.byHorizon` i18n key — until it lands, any KPI entry that does carry a `delta` key will render the literal key name for the horizon label (currently no such entry exists, so this is invisible in production today)

---
*Phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data*
*Completed: 2026-07-29*
