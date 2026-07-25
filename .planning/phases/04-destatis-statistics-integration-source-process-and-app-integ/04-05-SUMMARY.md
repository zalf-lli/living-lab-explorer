---
phase: 04-destatis-statistics-integration-source-process-and-app-integ
plan: 05
subsystem: ui
tags: [react, i18next, statistics-display, destatis, disclosure-pattern]

# Dependency graph
requires:
  - phase: 04-destatis-statistics-integration-source-process-and-app-integ (04-03)
    provides: kpiByTab/destatisRetrievedAt computed fields in ll_metadata.json
  - phase: 04-destatis-statistics-integration-source-process-and-app-integ (04-04)
    provides: renamed/available tabs (Agriculture/Climate/Soil/Landscape/Socio-economic) and statPanel.* i18n namespace
provides:
  - "StatPanel component rendering per-tab Destatis KPI tiles with locale-aware formatting"
  - "KPIStrip fully retired (deleted, no imports, legacy kpi.* i18n keys removed)"
  - "useLLMetadata.js exposes kpiByTab/destatisRetrievedAt instead of flat kpi fields"
  - "Collapsible source-attribution disclosure toggle on StatPanel"
affects: [phase-05-protected-areas, future-statpanel-consumers]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Disclosure toggle with aria-expanded + click-outside/Escape-to-close, mirrored from LLMap's MapInfoControl"
    - "Locale-aware number formatting via Number(value).toLocaleString(i18n.language === 'de' ? 'de-DE' : 'en-US')"

key-files:
  created: [app/src/components/StatPanel.jsx]
  modified: [app/src/pages/LLDetail.jsx, app/src/hooks/useLLMetadata.js, app/src/i18n.js]

key-decisions:
  - "Source-attribution lines (per unique GENESIS table + View source link) collapsed behind a 'Sources' disclosure button per reviewer feedback, to avoid multi-line crowding on tabs spanning several tables (e.g. Socio-economic)"
  - "Pending-review footnote stays always-visible (not gated behind the new toggle) since it is panel-level state, not per-source attribution"
  - "kpi_icons.js left in place though now unreferenced (KPIStrip was its only consumer) — out of this plan's file scope, StatPanel does not use per-field icons per UI-SPEC's 'optional scope' note"

patterns-established:
  - "StatPanel: composite of KPIStrip's tile visual language + LLMap InfoRow's external-link pattern + a new disclosure-toggle pattern for secondary/collapsible content"

requirements-completed: [P4-SCOPE-3, D-05, D-09]

# Metrics
duration: 80min
completed: 2026-07-25
---

# Phase 4 Plan 05: StatPanel UI Component Summary

**New `StatPanel` component renders real per-tab Destatis KPI tiles (locale-aware formatting, muted em-dash for unverified fields, collapsible GENESIS source-attribution) in place of the retired fixed-4-value `KPIStrip`, across all 5 LL detail tabs and both languages.**

## Performance

- **Duration:** ~80 min
- **Started:** 2026-07-25T18:2x (approx, first file read before Task 1 commit)
- **Completed:** 2026-07-25T19:56:08+02:00
- **Tasks:** 3 (2 auto + 1 human-verify checkpoint)
- **Files modified:** 5 (1 created, 3 modified, 1 deleted) + 1 deferred-items note

## Accomplishments
- Built `StatPanel({ tab, ll })`: renders `ll.kpiByTab[tab]` as a responsive tile grid (up to 4 columns), each tile showing the localized, unit-suffixed value or a muted em-dash for `null` values, with a single pending-review footnote when any field in the tab lacks a verified value.
- Wired `StatPanel` into both `LLDetail.jsx` layouts (`LayoutSplit` and `LayoutStacked`), swapping content by active tab (`layer` state, unchanged hook wiring).
- Retired `KPIStrip.jsx` entirely (deleted file, removed import, removed the 4 legacy `kpi.*` i18n keys it alone consumed).
- Updated `useLLMetadata.js`'s `buildLL()` to expose `kpiByTab`/`destatisRetrievedAt` instead of the old flat `area`/`farms`/`tempRange`/`precip`/`soil` fields that no longer exist in `ll_metadata.json`.
- Human-verify checkpoint (Task 3): reviewer confirmed all 5 tabs render distinct, correct StatPanel content in both EN/DE, no crashes, em-dashes render correctly, and source links work — **approved**, with one follow-up UX fix requested and delivered (see Deviations).

## Task Commits

Each task was committed atomically:

1. **Task 1: Build the StatPanel component per UI-SPEC** - `788eeb4` (feat)
2. **Task 2: Wire StatPanel into LLDetail, retire KPIStrip, update useLLMetadata** - `a92f18e` (feat)
3. **Task 3: Human verification checkpoint** - approved by reviewer; no separate feature commit (checkpoint itself makes no code changes) — see the post-approval fix commit below, made in response to checkpoint feedback.

**Post-checkpoint fix (reviewer-requested):** `b8e15b1` (fix) — collapse source-attribution lines behind a disclosure toggle.

**Plan metadata:** _(this commit)_ - docs: complete plan

_Note: Task 3 is a human-verify checkpoint, not a code-producing task; its outcome (approval + one requested revision) is documented under Deviations below._

## Files Created/Modified
- `app/src/components/StatPanel.jsx` - New component: per-tab KPI tile grid, locale-aware formatting, empty-state em-dash, pending-review footnote, and a collapsible source-attribution disclosure (button + per-table lines + "View source" link)
- `app/src/pages/LLDetail.jsx` - Import swapped from `KPIStrip` to `StatPanel`; both `LayoutSplit` and `LayoutStacked` mount `<StatPanel tab={layer} ll={ll} />` in place of `<KPIStrip ll={ll} />`
- `app/src/hooks/useLLMetadata.js` - `buildLL()` now returns `kpiByTab`/`destatisRetrievedAt` instead of the retired flat `area`/`farms`/`tempRange`/`precip`/`soil` fields
- `app/src/components/KPIStrip.jsx` - Deleted (fully superseded by `StatPanel`)
- `app/src/i18n.js` - Removed legacy `kpi.totalArea`/`activeFarms`/`avgTemp`/`dominantSoil` keys (EN+DE); added `statPanel.sourcesToggle` key (EN "Sources" / DE "Quellen") for the new disclosure button
- `.planning/phases/04-destatis-statistics-integration-source-process-and-app-integ/deferred-items.md` - New file logging one deferred, out-of-scope cleanup item (see Deviations)

## Decisions Made
- Source-attribution content (per-unique-table lines + "View source" link) moved behind a collapsed-by-default disclosure toggle, driven directly by human-verify checkpoint feedback — tabs spanning multiple GENESIS tables (e.g. Socio-economic, ~4 tables) were visually crowded with the original always-visible design.
- The disclosure toggle reuses the existing click-outside/Escape-to-close pattern from `LLMap`'s `MapInfoControl` for consistency, rather than inventing a new interaction pattern.
- `kpi_icons.js` (now unreferenced after `KPIStrip.jsx`'s deletion) is left in place rather than deleted — it's out of this plan's declared file scope and `StatPanel` intentionally omits per-field icons per UI-SPEC's explicit "optional scope" note.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed app dependencies from lockfile**
- **Found during:** Task 1 verification (`cd app && npm run build`)
- **Issue:** Fresh worktree had no `node_modules`; build/lint could not run
- **Fix:** Ran `npm ci` (from existing `package-lock.json`, not a new/unverified package install)
- **Files modified:** none tracked (node_modules is gitignored)
- **Verification:** `npm run build` and `npm run lint` succeed afterward
- **Committed in:** n/a (no file changes to commit; environment setup only)

**2. [Post-checkpoint, reviewer-requested] Collapse source-attribution lines behind a disclosure toggle**
- **Found during:** Task 3 human-verify checkpoint (initial round)
- **Issue:** On tabs with multiple distinct GENESIS tables (e.g. Socio-economic, ~4 tables), the always-visible source-attribution lines stacked up and crowded the panel
- **Fix:** Added an accessible `<button aria-expanded>` "Sources"/"Quellen" toggle, collapsed by default; per-table source lines + "View source" link now render only when expanded. Pending-review footnote unaffected (stays always-visible).
- **Files modified:** `app/src/components/StatPanel.jsx`, `app/src/i18n.js`
- **Verification:** `npm run build` and `npm run lint` pass clean; reviewer re-verified and approved in a follow-up checkpoint round
- **Committed in:** `b8e15b1`

### Out-of-scope items logged (not fixed)

**`app/src/data/kpi_icons.js` is now unreferenced** — its only consumer, `KPIStrip.jsx`, was deleted in Task 2. Not deleted here since it isn't in this plan's `files_modified` list and `StatPanel` intentionally has no per-field icon requirement (UI-SPEC marks icons "optional scope"). Logged in `.planning/phases/04-destatis-statistics-integration-source-process-and-app-integ/deferred-items.md` for a future cleanup pass.

---

**Total deviations:** 1 auto-fixed (blocking, environment setup) + 1 reviewer-requested UX revision (post-checkpoint fix)
**Impact on plan:** No scope creep — the dependency install was a mechanical environment-setup step, and the disclosure-toggle change is a direct, scoped response to human-verify checkpoint feedback within Task 3's own acceptance criteria (visual/functional correctness of the same component under review).

## Issues Encountered
None beyond the deviations documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness

- Phase 4's D-05 (KPIStrip retirement) and D-09 (17 curated KPI fields surfaced in the UI) are now both satisfied end-to-end: real Destatis-sourced statistics are visible on every LL detail tab, in both languages, with proper empty-state and source-attribution handling.
- This was the final plan in Phase 4 (`04-destatis-statistics-integration-source-process-and-app-integ`) — Waves 1-2 and 6-7 were already complete; Waves 3-5 (04-03, 04-04, 04-05) are now all complete, closing out the phase.
- No blockers for downstream work. The 6 KPI slots that remain genuinely null (per STATE.md's data-availability notes) render correctly as muted em-dashes with the pending-review footnote — no UI change needed if/when those slots are ever filled from a non-Destatis source in a future phase.

---
*Phase: 04-destatis-statistics-integration-source-process-and-app-integ*
*Completed: 2026-07-25*

## Self-Check: PASSED

- FOUND: `app/src/components/StatPanel.jsx`
- CONFIRMED DELETED: `app/src/components/KPIStrip.jsx`
- FOUND: `.planning/phases/04-destatis-statistics-integration-source-process-and-app-integ/deferred-items.md`
- FOUND commit: `788eeb4`
- FOUND commit: `a92f18e`
- FOUND commit: `b8e15b1`
