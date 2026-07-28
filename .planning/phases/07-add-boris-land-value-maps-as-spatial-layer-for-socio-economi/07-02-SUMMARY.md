---
phase: 07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi
plan: 02
subsystem: ui
tags: [react, i18n, map-layers, boris, choropleth]

requires:
  - phase: 07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi
    provides: 07-UI-SPEC BORIS ramp, no-data style, and bilingual copy contract
provides:
  - Economic tab registered as a BORIS vector GeoJSON layer
  - BORIS choropleth style exports for ramp, no-data, base, and hover state
  - English and German BORIS legend, loading, error, and tooltip copy
affects: [phase-07, LLMap, MapLegend, i18n]

tech-stack:
  added: []
  patterns:
    - Static layer configuration imports theme tokens for map styling
    - Dynamic legend copy uses existing i18n legend and map namespaces

key-files:
  created:
    - .planning/phases/07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi/07-02-SUMMARY.md
  modified:
    - app/src/data/layers.js
    - app/src/i18n.js

key-decisions:
  - "Kept LAYER_COLORS.economic as the fallback palette while the economic tab now resolves BORIS dynamically."
  - "Used the UI-SPEC's single neutral no-data color pair because theme.js has no grey token."

patterns-established:
  - "BORIS style constants live in app/src/data/layers.js and should be imported by LLMap instead of redeclared."
  - "BORIS usage labels remain data properties, not i18n keys."

requirements-completed: [D-01, D-03, D-04, D-08, D-10, D-12]

coverage:
  - id: D1
    description: "Economic layer is a vector layer resolving data/geojson/boris-{slug}.geojson with the economic legend note key."
    requirement: D-01
    verification:
      - kind: other
        ref: "PowerShell/rg acceptance counts for boris-{slug}.geojson, legend.economic.note, and placeholder removal"
        status: pass
      - kind: other
        ref: "cd app && npm run lint"
        status: pass
      - kind: other
        ref: "cd app && npm run build"
        status: pass
    human_judgment: false
  - id: D2
    description: "BORIS_RAMP, BORIS_NO_DATA_STYLE, BORIS_VALUE_STYLE_BASE, and BORIS_HOVER_STYLE are exported for renderer reuse."
    requirement: D-03
    verification:
      - kind: other
        ref: "PowerShell acceptance count: 4 BORIS exports, 0 hex literals in BORIS_RAMP"
        status: pass
      - kind: other
        ref: "cd app && npm run lint"
        status: pass
      - kind: other
        ref: "cd app && npm run build"
        status: pass
    human_judgment: false
  - id: D3
    description: "English and German BORIS legend, loading, error, and tooltip keys exist with placeholder economic legend labels removed."
    requirement: D-10
    verification:
      - kind: other
        ref: "PowerShell acceptance counts for economicTooltip, economicLoading, economicError, noCurrentValue, valuationDate, Nutzungsart, Usage type, and fuer/umlaut checks"
        status: pass
      - kind: other
        ref: "cd app && npm run lint"
        status: pass
      - kind: other
        ref: "cd app && npm run build"
        status: pass
    human_judgment: false

# Metrics
duration: 49 min
completed: 2026-07-28
status: complete
---

# Phase 07 Plan 02: BORIS Static Layer and Copy Summary

**Economic tab static configuration now points at BORIS GeoJSON assets and exposes the locked BORIS styling and bilingual copy contract.**

## Performance

- **Duration:** 49 min
- **Started:** 2026-07-28T06:38:00Z
- **Completed:** 2026-07-28T07:26:13Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Converted the `economic` layer from a placeholder into a vector layer using `data/geojson/boris-{slug}.geojson` and `legend.economic.note`.
- Added the BORIS ramp, no-data, base, and hover style exports in `app/src/data/layers.js` so later renderer work can import them directly.
- Replaced placeholder economic legend labels with EN/DE BORIS legend, loading, error, and tooltip keys from the UI-SPEC.

## Task Commits

Each task was committed atomically:

1. **Task 1: Convert the economic layer entry and export the BORIS ramp** - `55f5919` (feat)
2. **Task 2: Add the bilingual BORIS i18n keys** - `a1e8aa9` (feat)

**Plan metadata:** this summary commit.

## Files Created/Modified

- `app/src/data/layers.js` - Registers BORIS as the economic vector layer and exports BORIS style constants.
- `app/src/i18n.js` - Adds BORIS EN/DE copy and removes unreachable placeholder economic legend labels.
- `.planning/phases/07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi/07-02-SUMMARY.md` - Records plan completion.

## Decisions Made

- Kept `LAYER_COLORS.economic` in place as the fallback palette for any remaining placeholder code paths.
- Used the UI-SPEC's grey no-data style as the sole new color pair because `theme.js` does not define a neutral grey.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The direct `node -e "import('./src/i18n.js')..."` check reached the existing browser-only `window.navigator.language` access and failed under Node. The plan's fallback path was followed: `npm run lint` passed.
- `npm run build` initially failed inside the sandbox with Vite/Rolldown `spawn EPERM`; rerunning the same build with elevated permission passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for `07-03`: the frontend now has the static economic layer registration and copy/style constants that BORIS measurement and rendering plans depend on.

---
*Phase: 07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi*
*Completed: 2026-07-28*