---
phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data
plan: 05
subsystem: ui
tags: [react, i18n, presentational-component, accessibility]

# Dependency graph
requires:
  - phase: 08-02
    provides: statPanel.byHorizon call site, resolveLayerAsset three-placeholder resolver, climate ramp exports (not consumed directly by this plan's standalone components)
  - phase: 08-03
    provides: W-05 locked fourth-variable decision (gdd5 -> variable id `gdd`, variable_key `gdd5_degc_days`) from 08-SPIKE.md
provides:
  - Complete bilingual climate copy surface in app/src/i18n.js (climate.*, legend.climate.note.*, map.climate*, statPanel.byHorizon, four new kpi.* labels)
  - VariablePicker({ variables, active, onChange, disabled }) - controlled four-button second-level tab row
  - PeriodSwitcher({ mode, horizon, onModeChange, onHorizonChange, horizons, style }) - controlled two-level segmented Baseline/Change control
affects: ["08-10 (wires both components + the i18n surface into LLDetail.jsx and LLMap/index.jsx)", "Phase 10 (lifts one instance of each control to drive two comparison columns, D-17)"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Second-level tab row copies LayerTabs.jsx's button treatment verbatim except the locked inactive-weight exception (400, not LayerTabs' legacy 500)"
    - "Two-level segmented control built fresh from ProtectedAreasToggle's pill/border/shadow visual tokens (no two-level control precedent existed anywhere in the codebase)"
    - "Both new components are fully controlled (zero useState) so a single instance of each can later be lifted and shared across Phase 10's two comparison columns"

key-files:
  created:
    - app/src/components/VariablePicker.jsx
    - app/src/components/PeriodSwitcher.jsx
  modified:
    - app/src/i18n.js

key-decisions:
  - "Legend notes and map loading/error copy transliterated to the file's existing ASCII-umlaut convention (ue/ae/ss, 'degC' for °C) and its single-hyphen-with-spaces em-dash style (' - '), matching neighbouring keys rather than either 08-UI-SPEC.md's raw Unicode draft or 08-SPIKE.md's own '--' convention"
  - "Added climate.period.rowLabel (EN 'Time period' / DE 'Zeitraum'), a key not enumerated in Task 1's instructions, because Task 3's own accessibility contract explicitly forbids reusing climate.period.baseline as level 1's group aria-label and no dedicated label key existed yet (Rule 2 - auto-add missing accessibility labeling)"
  - "Period tokens use literal ASCII hyphens ('2041-2070', '2071-2100') per Task 1's explicit instruction, not 08-UI-SPEC.md's en-dash draft ('2041-2070')"

requirements-completed: [D-08, D-14, D-15, D-16]

# Metrics
duration: ~55min
completed: 2026-07-30
---

# Phase 8 Plan 05: Climate Tab i18n Surface + VariablePicker + PeriodSwitcher Summary

**Delivered the Climate tab's full bilingual copy surface and two standalone, fully-controlled presentational components (four-button variable picker, two-level Baseline/Change period switcher) — built detached from LLDetail.jsx/LLMap so 08-10 gets finished parts to wire up.**

## Performance

- **Duration:** ~55 min
- **Completed:** 2026-07-30T08:29:15Z
- **Tasks:** 3
- **Files modified:** 3 (1 modified, 2 created)

## Accomplishments
- `app/src/i18n.js` gained a new top-level `climate` block (variable labels, period labels/hints, row labels), a new `legend.climate.note.*` sub-block with the D-14 per-variable explanatory notes (the GDD note defines the index in plain language, per D-14's explicit requirement), `map.climateLoading`/`map.climateError`, `statPanel.byHorizon` (already called by 08-02's delta row), and four new `kpi.*` labels for the W-05-locked `variable_key`s — verified symmetric across EN/DE (177 keys, zero asymmetric) by an automated flatten-and-diff script
- `VariablePicker.jsx` renders exactly one button per entry in the caller-supplied `variables` array (ordering authority for D-08's "first variable pre-selected"), copying `LayerTabs.jsx`'s button treatment with the locked inactive-weight-400 exception, `role="tablist"`/`role="tab"`/`aria-selected`/`aria-label` wired for accessibility
- `PeriodSwitcher.jsx` renders `[Baseline | Change]` always and the `[2041-2070 | 2071-2100]` horizon sub-toggle only when `mode === 'change'` — structurally absent (no DOM node at all), not disabled or CSS-hidden, satisfying D-16's absolute-vs-change distinction — reusing `ProtectedAreasToggle`'s pill/border/shadow recipe verbatim
- Both new components hold zero `useState` and accept all state via props, so a single instance of each can later be lifted into `LLDetail.jsx` (08-10) and shared across Phase 10's two comparison columns (D-17)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add the complete bilingual climate copy block to i18n.js** - `863bc0e` (feat)
2. **Task 2: Build the VariablePicker second-level tab row** - `9d86dfd` (feat)
3. **Task 3: Build the two-level PeriodSwitcher** - `362b0c2` (feat)

**Plan metadata:** (this commit, made after SUMMARY.md is written)

## Files Created/Modified
- `app/src/i18n.js` - New `climate` block (both languages); new `legend.climate.note.*` sub-block; new `map.climateLoading`/`map.climateError`; new `statPanel.byHorizon`; four new `kpi.*` labels; existing placeholder `legend.climate.{arable,forest,grassland,settlement,water}` and `kpi.agr_ch4_kt`/`kpi.agr_n2o_kt` left untouched per plan instruction
- `app/src/components/VariablePicker.jsx` (new) - Controlled four-button second-level tab row
- `app/src/components/PeriodSwitcher.jsx` (new) - Controlled two-level segmented Baseline/Change control with conditional horizon sub-toggle

## Decisions Made
- Carried the W-05-locked `gdd` variable id (not `bio10`) into every new i18n key, per `08-SPIKE.md`'s `### W-05` locked-decisions section - `climate.variable.gdd`, `legend.climate.note.gdd`, and `kpi.gdd5_degc_days` all use the CHELSA-static-file outcome's copy, not the `bio10` fallback copy
- Transliterated all new German copy (and the GDD/bio1/bio18 notes drafted with Unicode in `08-UI-SPEC.md`) into the file's existing ASCII-umlaut convention (`ue`, `ae`, `ss`, `degC`) so the new block matches its neighbours rather than introducing mixed encoding within one file
- Used the file's existing single-hyphen-with-spaces em-dash substitute (`' - '`) for all new copy, rather than `08-SPIKE.md`'s own `'--'` convention, since the plan's read_first explicitly asks to match the file's own neighbouring-key convention
- Added `climate.period.rowLabel` (not in Task 1's key list) to satisfy Task 3's own accessibility contract, which explicitly forbids reusing `climate.period.baseline`'s text as level 1's group `aria-label`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - missing accessibility label] Added `climate.period.rowLabel` i18n key**
- **Found during:** Task 3
- **Issue:** Task 3's action text requires level 1 of `PeriodSwitcher` to carry a `role="group"` `aria-label` that is "`t('climate.period.baseline')`-agnostic — use a dedicated label," but no such key existed in Task 1's enumerated key list and Task 1 had already been committed.
- **Fix:** Added `climate.period.rowLabel` (EN "Time period" / DE "Zeitraum") to both language trees in `i18n.js` and used it for level 1's `aria-label` in `PeriodSwitcher.jsx`. Re-verified EN/DE symmetry after the addition (177 keys, still zero asymmetric).
- **Files modified:** `app/src/i18n.js`, `app/src/components/PeriodSwitcher.jsx`
- **Commit:** `362b0c2` (bundled into Task 3's commit, since the key exists solely to satisfy that task's own accessibility contract)

### Environment notes (not plan deviations)

- `npm install` was run in `app/` because `node_modules` did not exist in this freshly-spawned worktree — a prerequisite for running the plan's own `npm run lint`/`npm run build` verification, not a change to `package.json`/`package-lock.json`.
- The plan's Task 1 verify command imports `app/src/i18n.js` directly under plain Node, but `i18n.js`'s `getInitialLanguage()` reads `window.navigator.language` unconditionally at module-load time (pre-existing code, not introduced by this plan) — plain Node has no `window` global. Ran the identical verification logic with a two-line `globalThis.window` stub (`{ navigator: { language: 'en' }, localStorage: { getItem: () => null } }`) prepended, which exercises the exact same `getResourceBundle` calls and flatten-and-diff logic the plan's verify command specifies. No source file was changed to work around this; it only affects how the verification script itself must be invoked outside a browser context.

## Issues Encountered
None blocking. See Environment notes above for the two non-blocking verification-harness adjustments.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `08-10` can now import `{ VariablePicker }` from `app/src/components/VariablePicker.jsx` and `{ PeriodSwitcher }` from `app/src/components/PeriodSwitcher.jsx`, lift `variable`/`mode`/`horizon` state into `LLDetail.jsx`, and resolve every string the Climate tab needs from `i18n.js` — no further copy or control work remains before wiring
- Neither component is yet rendered anywhere in the app (deliberately out of scope, per this plan's objective) - `08-10` is responsible for mounting both inside `LLDetail.jsx`/`LLMap/index.jsx` and threading `CLIMATE_VARIABLES`-sourced ids into `VariablePicker`'s `variables` prop
- `legend.climate.{arable,forest,grassland,settlement,water}` (the dead placeholder fallback keys) and `charts.climate` remain untouched, exactly as instructed - both are flagged for removal in `08-10`'s same commit that flips the layer to a real raster, not here

---
*Phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data*
*Completed: 2026-07-30*
