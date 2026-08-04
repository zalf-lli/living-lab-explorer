---
phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data
plan: 10
subsystem: app-frontend
tags: [react, leaflet, pmtiles, climate, state-lifting, legend]

# Dependency graph
requires:
  - phase: 08-05
    provides: "VariablePicker/PeriodSwitcher fully-controlled components and the complete bilingual climate copy surface in i18n.js"
  - phase: 08-08
    provides: "app/src/data/climate_legend.js (CLIMATE_VARIABLES, CLIMATE_LEGEND, CLIMATE_RAMP_SHAPE) and the 60 built/published climate PMTiles"
  - phase: 08-09
    provides: "kpiByTab.climate real values via the chelsa source_host branch, exercising StatPanel's delta row for the first time"
provides:
  - "Real per-Living-Lab raster on the Climate tab (climate layer entry flipped from placeholder to raster in layers.js)"
  - "useClimateControlState() lifted into LLDetail.jsx beside useLayerState(), driving VariablePicker/PeriodSwitcher across all three layouts and both Phase-10 comparison columns from one instance"
  - "RasterPmtilesLayer extended to variable/period-aware resolution with a cancelled-flag-guarded async status callback, reused by SoilStatusBadge for climate loading/error"
  - "Climate legend entries/note computed at the LLMap call site from CLIMATE_LEGEND, passed through MapLegend's existing entries/note props (MapLegend.jsx itself unmodified)"
affects: ["Phase 10 (D-17 shared period-switcher/variable-picker instance across both comparison columns is already the pattern LayoutCompare/ComparisonColumn use)", "08-11 (closing human-verification checkpoint)"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Climate control state lifted to the same level as useLayerState (climateVariable/periodMode/horizon), with a single derived `period` token computed once in the parent rather than per layout"
    - "RasterPmtilesLayer's mount key extends to cover all three axes (layer, variable, period) for the climate layer only, so exactly one raster is ever in flight and a variable/period change fully remounts rather than mutates the Leaflet overlay"
    - "Async load-status reporting via an optional onStatus callback plus a cancelled flag captured in the effect closure, guarding against a stale PMTiles header-read resolving after a variable/period change has already torn the effect down"

key-files:
  created: []
  modified:
    - app/src/data/layers.js
    - app/src/i18n.js
    - app/src/pages/LLDetail.jsx
    - app/src/components/LLMap/index.jsx

key-decisions:
  - "climate layer's legend field stays null with an explanatory comment (not LAND_COVER_LEGEND-style inline data), since climate's bands are per-variable and per-mode and must be computed at the LLMap call site from CLIMATE_LEGEND, exactly as soil and economic already do"
  - "LAYER_COLORS.climate deleted outright rather than left to rot, since MapLegend's LAYER_COLORS fallback branch is now permanently unreachable for a real raster layer with its own entries-prop legend"
  - "RasterPmtilesLayer now awaits the PMTiles instance's getHeader() promise before calling overlay.addTo(map), rather than adding the overlay synchronously and reporting status separately -- this makes the loading/error badge state and the actual overlay-mount state a single source of truth per the plan's explicit before/on-resolution/on-rejection sequencing"
  - "PeriodSwitcher is positioned at { top: 56, right: 12 } to sit below ProtectedAreasToggle's own top-right slot (top: 12) rather than beside it, since both controls can be visible simultaneously on the Climate tab and D-15 requires they never overlap"

requirements-completed: [D-08, D-10, D-11, D-12, D-14, D-15, D-16, D-17]

# Metrics
duration: ~50min
completed: 2026-07-31
---

# Phase 8 Plan 10: Climate Tab Wiring Summary

**Flipped the Climate tab from a coming-soon placeholder into a working raster map: the layer entry is now a real three-placeholder-URL raster, climate control state (variable + baseline/change period + horizon) is lifted once into LLDetail.jsx beside the existing layer state, and LLMap resolves the raster, legend, note and status badges from that shared state end to end.**

## Performance

- **Duration:** ~50 min
- **Completed:** 2026-07-31T07:15:00Z (approx.)
- **Tasks:** 3 completed
- **Files modified:** 4 (layers.js, i18n.js, LLDetail.jsx, LLMap/index.jsx)

## Accomplishments

- `app/src/data/layers.js`: the `climate` entry is now `{ id: 'climate', type: 'raster', pmtilesUrlPattern: 'data/pmtiles/climate-{variable}-{period}-{slug}.pmtiles', legend: null, available: true }`, matching `sources.yaml`'s `output.pmtiles_pattern` byte for byte; `CLIMATE_VARIABLES`/`CLIMATE_LEGEND` are imported from `climate_legend.js` and re-exported so `layers.js` stays the single module the map layer configuration is read from; `LAYER_COLORS.climate` is deleted (the fallback branch it fed is now permanently unreachable for this layer)
- `app/src/i18n.js`: the five dead `legend.climate.{arable,forest,grassland,settlement,water}` placeholder keys are gone from both EN and DE trees; `legend.climate.note.*` and `layers.climate` are untouched; EN/DE key sets remain symmetric (170/170, verified by an automated flatten-and-diff script)
- `app/src/pages/LLDetail.jsx`: a new `useClimateControlState()` hook (same minimal `startTransition`-wrapped style as `useLayerState`) is called once beside it, initialising `climateVariable` to `CLIMATE_VARIABLES[0].id` (D-08), `periodMode` to `'baseline'`, and `horizon` to `'2071_2100'` (D-21); a single `period` token is derived once in the parent. `LayoutSplit`, `LayoutStacked` and `LayoutCompare` each render `<VariablePicker>` directly under `<LayerTabs>` only when `layer === 'climate'` (D-15); `LayoutCompare` instantiates it exactly once and forwards identical values into both `ComparisonColumn` instances (D-17)
- `app/src/components/LLMap/index.jsx`: `RasterPmtilesLayer` now accepts `variable`/`period`/`onStatus`, resolves the three-placeholder URL, and awaits the PMTiles header read (guarded by a `cancelled` flag against a stale resolution) before adding the overlay and reporting success/failure; the raster mount `key` extends to `${layer}-${slug}-${variable}-${period}` for the climate layer so exactly one raster is ever in flight; the climate loading/error badges reuse `SoilStatusBadge` with the existing `map.climateLoading`/`map.climateError` keys (no new badge component); `<PeriodSwitcher>` mounts on the map, offset below `ProtectedAreasToggle`, only when `layer === 'climate'`, fully driven by props; a `useMemo` selects the active `CLIMATE_LEGEND[variable][mode]` band array for `MapLegend`'s `entries` prop, and the `note` prop resolves the active variable's `legendNoteKey` -- `MapLegend.jsx` itself is unmodified

## Task Commits

Each task was committed atomically:

1. **Task 1: Flip the climate layer entry and delete the dead placeholder legend** - `29fa159` (feat)
2. **Task 2: Lift climate control state into LLDetail and thread it through all three layouts** - `f29a544` (feat)
3. **Task 3: Wire the climate raster, period switcher, legend and status badges into LLMap** - `3d9da40` (feat)

_No separate plan-metadata commit -- STATE.md/ROADMAP.md/REQUIREMENTS.md are owned by the orchestrator and are not touched by this worktree agent._

## Files Created/Modified

- `app/src/data/layers.js` - `climate` entry flipped to a real raster (`pmtilesUrlPattern`, `legend: null` with explanatory comment); imports and re-exports `CLIMATE_VARIABLES`/`CLIMATE_LEGEND` from `climate_legend.js`; `LAYER_COLORS.climate` deleted
- `app/src/i18n.js` - Deleted the five `legend.climate.{arable,forest,grassland,settlement,water}` placeholder keys (EN+DE); `legend.climate.note.*`, `layers.climate` and `charts.climate` untouched
- `app/src/pages/LLDetail.jsx` - Added `useClimateControlState()`; threaded `climateVariable`/`setClimateVariable`/`periodMode`/`setPeriodMode`/`horizon`/`setHorizon`/derived `period` through `LayoutSplit`, `LayoutStacked`, `LayoutCompare`, `ComparisonColumn` and every `<LLMap>` call site; rendered `<VariablePicker>` conditionally under `<LayerTabs>` in all three layouts
- `app/src/components/LLMap/index.jsx` - Extended `RasterPmtilesLayer`'s signature and effect; extended the raster mount key; added climate status badges via `SoilStatusBadge`; mounted `<PeriodSwitcher>` on the map; added a `climateLegendEntries` `useMemo` and a climate arm to the legend `note` expression; extended `LLMap`'s own props with safe defaults

## Decisions Made

- Kept `climate`'s `legend` field `null` with an explanatory comment (not inline legend data) since the bands are per-variable/per-mode and must be resolved at the `LLMap` call site from `CLIMATE_LEGEND`, matching the existing soil/economic pattern rather than the land-cover pattern
- Deleted `LAYER_COLORS.climate` rather than leaving it to rot, since `MapLegend`'s `LAYER_COLORS` fallback branch is now permanently unreachable for this layer (`entries?.length ? entries : cfg?.legend` always takes the generated-legend branch once the layer carries real `entries` from the call site)
- `RasterPmtilesLayer` awaits `getHeader()` before adding the overlay (rather than adding it synchronously and reporting status as a side effect), so the loading/error badge state and the actual Leaflet-overlay-mounted state are the same source of truth, matching the plan's explicit before/on-resolution/on-rejection sequencing
- `PeriodSwitcher` is positioned at `{ top: 56, right: 12 }` (below `ProtectedAreasToggle`'s `{ top: 12, right: 12 }`) so the two absolutely-positioned map controls never overlap when both are visible on the Climate tab

## Deviations from Plan

None -- the plan's three tasks were executed as written. `npm install` in `app/` was required as one-time environment setup (fresh worktree checkout, no `node_modules`), matching the pattern already documented as non-deviation in `08-05-SUMMARY.md`/`08-08-SUMMARY.md`/`08-09-SUMMARY.md`.

## Known Stubs

None. All four CHELSA variables resolve to real, already-built PMTiles for all five Living Labs (spot-checked `climate-bio12-baseline-east-brandenburg.pmtiles` and `climate-gdd-2071_2100-rheingau.pmtiles`, both present under `app/public/data/pmtiles/`), and `kpiByTab.climate` already carries real values from `08-09`. No hardcoded empty array/object/null flows to the Climate tab's rendering path introduced by this plan.

## Issues Encountered

None. `npm run lint` and `npm run build` both exited 0 after every task; `python -m pytest data-pipeline/tests/ -q` (via the existing `C:\lcvenv` short-path venv) passed 31/31 with zero pipeline files touched by this plan, as expected.

## User Setup Required

None -- no external service configuration required. The `npm install` step was one-time local environment setup performed by the executor, not a manual user action.

## Threat Flags

None. This plan's threat register (T-08-06, T-08-11, T-08-21, T-08-10, T-08-17, T-08-04, T-08-SC) covers every trust boundary the four modified files touch (raster URL construction from `variable`/`period`, overlapping-tile-request DoS, malformed PMTiles response, legend/note strings rendered as text, hand-edited generated legend module, public climate data disclosure, npm installs); no new surface outside that register was introduced.

## Next Phase Readiness

- The Climate tab is now fully wired end to end: real raster (this plan, on top of `08-08`'s 60 built PMTiles), real per-variable/per-mode legend and note (this plan, reading `08-08`'s `climate_legend.js`), real KPI tiles (`08-09`), and the shared control-state pattern Phase 10's two-column comparison view already exercises (`LayoutCompare` instantiates one `VariablePicker` and forwards one `period`/`periodMode`/`horizon` set into both `ComparisonColumn`/`LLMap` instances, matching D-17 exactly).
- `08-11` (closing human-verification checkpoint) can proceed -- no blockers, no known stubs, no deferred items.

---
*Phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data*
*Completed: 2026-07-31*

## Self-Check: PASSED

- FOUND: `app/src/data/layers.js`
- FOUND: `app/src/i18n.js`
- FOUND: `app/src/pages/LLDetail.jsx`
- FOUND: `app/src/components/LLMap/index.jsx`
- FOUND: `.planning/phases/08-add-maps-and-stats-for-climate-variables-using-chelsa-data/08-10-SUMMARY.md`
- FOUND commit `29fa159` (Task 1)
- FOUND commit `f29a544` (Task 2)
- FOUND commit `3d9da40` (Task 3)
