---
status: complete
phase: 04-destatis-statistics-integration-source-process-and-app-integ
plan: "04-04"
wave: 4
completed: 2026-07-25
subsystem: app-frontend
tags: [i18n, tabs, layers, destatis, statPanel]
requirements:
  - P4-SCOPE-3
  - D-01
  - D-02
  - D-03
  - D-04
  - D-06
  - D-07
  - D-08
dependency-graph:
  requires:
    - "app/src/data/layers.js: existing 4-entry LAYERS array (landuse/climate/soil/economic)"
    - "app/src/i18n.js: existing layers.*/kpi.* namespaces"
    - "data/destatis_curated_kpis.json: 17-entry tab/variable_key/label manifest (Plan 04-02, D-14-updated)"
  provides:
    - "app/src/data/layers.js: LAYERS with 5 entries; climate/economic/landscape all available: true"
    - "app/src/i18n.js: renamed layers.landuse/economic labels, new layers.landscape key"
    - "app/src/i18n.js: 17 new kpi.* keys (EN+DE) matching generate_metadata.py's kpiByTab field keys 1:1"
    - "app/src/i18n.js: new statPanel.* namespace (EN+DE) for Plan 04-05's StatPanel component"
  affects:
    - "app/src/data/layers.js"
    - "app/src/i18n.js"
tech-stack:
  added: []
  patterns:
    - "kpi.* i18n keys use literal snake_case variable_key strings (e.g. land_area_cropland_ha) as object keys, not camelCase, to match generate_metadata.py's kpiByTab[...].key values 1:1 per the existing t(`kpi.${key}`) convention"
    - "statPanel.* is a new top-level i18n namespace (not nested under kpi.* or layers.*) reserved for Plan 04-05's StatPanel component copy (pending-review banner, source attribution, error state)"
decisions:
  - "Used data/destatis_curated_kpis.json's actual variable_key/label_en/label_de for the Soil tab's third KPI slot (groundwater_abstraction_1000m3) instead of the plan's literal groundwater_nitrate_mg_l text, per the plan's own interfaces-block override instruction for D-14 fallback substitutions"
metrics:
  duration_minutes: 35
  tasks_completed: 2
  files_changed: 2
---

# Phase 4 Plan 04: Tab Registry & i18n Restructure Summary

One-liner: Renamed the Land Use/Economic tabs to Agriculture/Socio-economic, added a KPI-only
Landscape tab, flipped Climate/Socio-economic/Landscape to `available: true`, and added the 17
curated `kpi.*` i18n keys plus a new `statPanel.*` copy namespace that Plan 04-05's `StatPanel`
component will consume.

## Completed

### Task 1: Add the Landscape tab and flip availability per D-01 through D-04

- `app/src/data/layers.js`: flipped `climate` and `economic` entries' `available` from `false`
  to `true` (D-04 — both now have real Destatis KPI data via Plan 04-03's `kpiByTab`).
- Added a new `landscape` entry to the `LAYERS` array (after `economic`):
  `{ id: 'landscape', type: 'placeholder', pmtilesUrl: null, legend: null, available: true }`
  (D-03 — KPI-only tab, no map layer, same shape as `climate`/`economic`).
- No `landscape` key was added to `LAYER_COLORS` — intentional, since KPI-only tabs render no
  map-legend color swatches.
- Internal `id` values for `landuse`/`economic` were left unchanged (only display labels change
  in Task 2), per CONTEXT.md's discretion note to minimize churn in `geojsonPathPattern`,
  `LAYER_COLORS`, and `pmtilesUrl` keys.
- Commit: `70e8182`

### Task 2: Rename tab labels, add landscape label, add 17 kpi.* keys and statPanel.* namespace

- EN `layers`: `landuse: 'Land Use'` -> `landuse: 'Agriculture'` (D-01), `economic: 'Economic'`
  -> `economic: 'Socio-economic'` (D-02), added `landscape: 'Landscape'` (D-03). `climate`/`soil`
  unchanged.
- DE `layers`: mirrored — `landuse: 'Landwirtschaft'`, `economic: 'Sozioökonomie'`, added
  `landscape: 'Landschaft'`.
- Added 17 new keys to both the EN and DE `kpi` objects (additive — the 4 legacy
  `totalArea`/`activeFarms`/`avgTemp`/`dominantSoil` keys are untouched, per plan scope; they are
  removed in Plan 04-05 alongside `KPIStrip`'s deletion), keyed by each curated `variable_key`
  exactly (e.g. `land_area_cropland_ha`, `farms_count`, ... `household_income_eur`) to match
  `generate_metadata.py`'s `kpiByTab[...].key` values 1:1.
- Added a new top-level `statPanel` namespace to both EN and DE `translation` objects (placed
  directly after `kpi`, before `layers`), with `pendingReviewTitle`, `pendingReviewBody`,
  `source`, `viewSource`, `errorTitle`, `errorBody` keys per the plan's exact copy text.
- Commit: `b837398`

## Verification

- `cd app && npm run build` succeeded after both Task 1 and Task 2 (no import/reference errors).
- `cd app && npm run lint` — passed clean, no new warnings.
- `grep -n "id: 'landscape'" app/src/data/layers.js` — 1 match.
- `grep -n "id: 'climate'" -A3 app/src/data/layers.js` — shows `available: true`.
- `grep -n "id: 'economic'" -A3 app/src/data/layers.js` — shows `available: true`.
- `grep -n "landuse: 'Agriculture'"`, `economic: 'Socio-economic'"`, `landscape: 'Landscape'"`,
  `landscape: 'Landschaft'"` in `app/src/i18n.js` — all match once as expected.
- `grep -n "statPanel:" app/src/i18n.js | wc -l` — reports 2 (EN + DE).
- 17-key grep count (using the actual manifest key `groundwater_abstraction_1000m3` in place of
  the plan's literal `groundwater_nitrate_mg_l` text — see Deviations) — reports 34 (17 keys x 2
  languages), matching the plan's "at least 34" acceptance target.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Plan-text/manifest reconciliation] Used `groundwater_abstraction_1000m3` instead
of the plan's literal `groundwater_nitrate_mg_l` for the Soil tab's third KPI slot**

- **Found during:** Task 2, before writing the `kpi.*` keys.
- **Issue:** The plan's `<interfaces>` block lists `groundwater_nitrate_mg_l` ("Nitrate in
  groundwater"/"Nitrat im Grundwasser") as one of the 17 curated keys, but also explicitly notes:
  "If Plan 04-02's D-14 fallback substituted a different variable for any tab slot, use
  `data/destatis_curated_kpis.json`'s actual `label_en`/`label_de` values for that slot instead of
  the list above (the manifest is the final source of truth after any substitution)." Quick-task
  260725-e1x (recorded in STATE.md and `.planning/quick/260725-e1x-.../260725-e1x-DECISION.md`,
  commit `ab920f8`) already repurposed this exact slot from `groundwater_nitrate_mg_l` to
  `groundwater_abstraction_1000m3` in `data/destatis_curated_kpis.json` and
  `data/destatis_variables_catalogue.csv`, prior to this plan's execution.
  - Verified via `data/destatis_curated_kpis.json` (row 7): `variable_key:
    "groundwater_abstraction_1000m3"`, `label_en: "Groundwater abstraction (non-public supply)"`,
    `label_de: "Grundwasserentnahme (nichtoeffentliche Versorgung)"`.
- **Fix:** Added `groundwater_abstraction_1000m3` (not `groundwater_nitrate_mg_l`) to both the EN
  and DE `kpi` objects, using the manifest's actual label text, per the plan's own override
  instruction.
- **Side effect:** The plan's Task 2 acceptance-criteria grep pattern hardcodes the literal string
  `groundwater_nitrate_mg_l:`, which does not match the substituted key — using that exact pattern
  yields a count of 32, not the target 34. Re-running the same grep with
  `groundwater_abstraction_1000m3:` substituted for `groundwater_nitrate_mg_l:` (i.e. the actual
  manifest key) yields 34, satisfying the plan's "at least 34" acceptance target and the "17
  new `kpi.*` i18n keys exist... keyed to match `generate_metadata.py`'s field names exactly"
  success criterion. No code defect — this is a stale literal string in the plan's own
  acceptance-criteria regex, predating the D-14 substitution's arrival at the manifest.
- **Files modified:** `app/src/i18n.js`.
- **Commit:** `b837398`

## Known Stubs

None introduced by this plan. `app/src/data/layers.js` and `app/src/i18n.js` are static,
build-time, developer-controlled config files with no runtime data flow — there is no UI
component in this plan's scope that could render an empty/placeholder value. Plan 04-05 is
responsible for wiring the new `kpi.*`/`statPanel.*` copy into an actual rendered `StatPanel`
component.

## Threat Flags

None. Both modified files (`app/src/data/layers.js`, `app/src/i18n.js`) are static, build-time,
developer-controlled config with no injection surface, consistent with this plan's
`<threat_model>` T-04-10 disposition (accept — no dynamic/user-supplied content interpolated).

## Self-Check: PASSED

- FOUND: `app/src/data/layers.js`
- FOUND: `app/src/i18n.js`
- FOUND commit: `70e8182` (feat(04-04): add Landscape tab and flip climate/economic to available)
- FOUND commit: `b837398` (feat(04-04): rename tab labels and add kpi.*/statPanel.* i18n keys)
