---
phase: 06-add-land-cover-map
plan: 03
subsystem: frontend
tags: [react, i18n, layers-registry, raster, pmtiles, land-cover, tab-restructure]

# Dependency graph
requires:
  - phase: 06-add-land-cover-map
    plan: 02
    provides: app/src/data/land_cover_legend.js (LAND_COVER_LEGEND) and five committed land-cover-{slug}.pmtiles pairs
provides:
  - Five exclusive tabs in order agriculture, climate, soil, economic, landscape
  - Slug-aware resolveLayerAsset() for pattern-based rasters, backward compatible with scalar crop-types
  - RasterPmtilesLayer receiving and forwarding the active Living Lab slug
  - Landscape as the LL detail page landing tab (both layouts)
affects: [06-04, 06-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "pattern-based raster resolution: resolveLayerAsset's raster branch now mirrors its vector branch exactly -- checks for a {slug} pattern field first (pmtilesUrlPattern), falls back to a scalar field (pmtilesUrl) for callers/layers that never pass a slug"
    - "explicit remount key on multi-instance overlays: RasterPmtilesLayer's call site now keys on `${layer}-${ll.slug}` so a stale Leaflet overlay can never survive an LL or tab switch, even though the existing layerUrl-keyed useEffect already handled it"

key-files:
  created: []
  modified:
    - app/src/data/layers.js
    - app/src/components/LLMap/index.jsx
    - app/src/i18n.js
    - app/src/pages/LLDetail.jsx
    - app/src/data/chart_data.js

key-decisions:
  - "Kept the landuse-croptypes.pmtiles filename and LANDUSE_LEGEND export name unchanged when renaming the tab id landuse -> agriculture -- the dataset id and the tab id are different things, and renaming the committed ~38 MB asset would churn git history for no benefit (plan's explicit instruction)"
  - "No legend.landCover.* i18n keys added -- MapLegend.jsx renders generated legends straight from LAND_COVER_LEGEND's entry[lang]/entry.en fields, so such keys would be dead code; this intentionally supersedes an earlier CONTEXT.md suggestion, per the plan's explicit note that no locked decision (D-04/D-19 concern layers.* labels only) is affected"

requirements-completed: [D-01, D-02, D-03, D-04, D-19, D-20, D-21, D-22, D-23, D-24]

# Metrics
duration: ~25min (excluding one-time `npm install`, which had not yet been run in this worktree)
completed: 2026-07-26
---

# Phase 06 Plan 03: App Integration - Landscape Tab & Slug-Aware Rasters Summary

**Restructured the app's exclusive layer tabs so crop types moved from `landuse` to `agriculture` and land cover now fills `landscape`, fixed the blocking bug where `resolveLayerAsset()` ignored `slug` entirely for raster layers, and made `landscape` the LL detail page's landing tab in both layouts.**

## Performance

- **Duration:** ~25 minutes of active edit/verify/commit work (plus a one-time `npm install` in this worktree, since `app/node_modules` did not exist yet)
- **Started:** first edit ~2026-07-26T22:35 (local)
- **Completed:** 2026-07-26T22:41:16+02:00 (last task commit)
- **Tasks:** 3/3 completed
- **Files modified:** 5

## Accomplishments

- `app/src/data/layers.js`: imported `LAND_COVER_LEGEND`, renamed the first `LAYERS` entry's id from `landuse` to `agriculture` (asset path and `LANDUSE_LEGEND` untouched), replaced the `landscape` placeholder entry with a real raster entry (`pmtilesUrlPattern: 'data/pmtiles/land-cover-{slug}.pmtiles'`, `legend: LAND_COVER_LEGEND`), extended `resolveLayerAsset`'s raster branch to substitute `{slug}` when `pmtilesUrlPattern` is present and a slug is supplied (falling back to the scalar `pmtilesUrl` otherwise -- backward compatible with crop-types), and renamed the `LAYER_COLORS` key `landuse` to `agriculture`
- `app/src/components/LLMap/index.jsx`: `RasterPmtilesLayer` now accepts `{ layerId, slug }` and calls `resolveLayerAsset(layerId, { slug })`; the call site inside `LLMap` passes `slug={ll.slug}` and an explicit `key={`${layer}-${ll.slug}`}` so the overlay remounts cleanly on LL or tab change
- `app/src/i18n.js`: renamed `layers.landuse` / `legend.landuse` / `charts.landuse` to `...agriculture` in both the English and German resource blocks, with every translated string left byte-for-byte identical; `layers.landscape` ('Landscape' / 'Landschaft') was already correct and untouched; no `legend.landCover.*` keys were added since `MapLegend.jsx` reads generated legend entries directly
- `app/src/pages/LLDetail.jsx`: `useLayerState()`'s default changed from `useState('landuse')` to `useState('landscape')`, which both `LayoutSplit` and the second layout share via the one hook
- `app/src/data/chart_data.js`: renamed the `CHART_DATA` key `landuse` to `agriculture`; no `landscape` key was added since `BarChart` already returns `null` for a layer with no chart data, which is the current (non-regressive) behavior for the landscape tab

## Task Commits

Each task was committed atomically:

1. **Task 1: Add pattern-based raster resolution and restructure the LAYERS registry** - `e100a9e` (feat)
2. **Task 2: Thread the active Living Lab slug into the raster overlay** - `3c4ddd2` (feat)
3. **Task 3: Rename the tab's i18n and chart keys and make landscape the landing view** - `5450046` (feat)

_No TDD tasks in this plan; all three were straight `auto` implementation tasks._

## Files Created/Modified

- `app/src/data/layers.js` - `agriculture`/`landscape` raster entries, slug-aware `resolveLayerAsset`, renamed `LAYER_COLORS` key
- `app/src/components/LLMap/index.jsx` - `RasterPmtilesLayer` accepts and forwards `slug`; call site passes `ll.slug` and a layer+slug key
- `app/src/i18n.js` - `layers`/`legend`/`charts` `landuse` -> `agriculture` renames in both languages
- `app/src/pages/LLDetail.jsx` - `useLayerState` default is now `'landscape'`
- `app/src/data/chart_data.js` - `CHART_DATA` key `landuse` -> `agriculture`

## Decisions Made

- Left `landuse-croptypes.pmtiles` and `LANDUSE_LEGEND` names untouched per the plan's explicit rationale (dataset id vs. tab id are different concerns; renaming the ~38 MB committed asset has no benefit)
- Did not add `legend.landCover.*` i18n keys, per the plan's explicit supersession of an earlier CONTEXT.md suggestion -- `MapLegend.jsx` already renders `LAND_COVER_LEGEND` entries directly via `entry[lang] || entry.en`

## Deviations from Plan

None - plan executed exactly as written. One environment note (not a deviation, no committed-file change): `app/node_modules` did not exist in this worktree, so `npm install` was run once before `npm run lint`/`npm run build` could execute; this matches the pattern documented in 06-02's summary that fresh worktrees need environment provisioning that isn't itself a plan task.

## Issues Encountered

None.

## User Setup Required

None. No new packages were installed (`package.json` untouched); the only local action was running `npm install` to populate this worktree's missing `node_modules` (a required action to run this plan's own lint/build verification gates, not a plan deviation).

## Next Phase Readiness

- Five exclusive tabs render in the declared order (`agriculture, climate, soil, economic, landscape`); `LayerTabs.jsx` required no change since it derives order from `LAYERS`
- `resolveLayerAsset('landscape', { slug })` resolves each Living Lab's own `land-cover-{slug}.pmtiles`; a missing slug resolves to `null` rather than falling back to any other region's data (per the threat model's T-06-12 mitigation)
- `RasterPmtilesLayer` receives and uses the active Living Lab's slug end-to-end
- The LL detail page defaults to the Landscape tab in both layouts; the Agriculture tab still renders the crop-types raster exactly as before
- No app-side `landuse` tab-id key remains anywhere under `app/src/` (confirmed via `grep -rn "'landuse'" app/src/`)
- `cd app && npm run lint` and `cd app && npm run build` both exit 0
- Ready for the next plan in this phase (06-04, running in parallel in a sibling worktree, and 06-05's bilingual/attribution checkpoint)

---
*Phase: 06-add-land-cover-map*
*Completed: 2026-07-26*
