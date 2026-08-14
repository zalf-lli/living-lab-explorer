---
phase: 13-add-a-projects-and-partners-tab-to-individual-living-lab-pag
plan: 05
subsystem: ui
tags: [react, lazy-loading, i18n, layer-tabs, composition]

requires:
  - phase: 13-01
    provides: partnersTab.* / layers.partners i18n keys, common.loading/common.loadingMap reuse
  - phase: 13-02
    provides: app/src/hooks/usePartnersProjects.js, app/src/lib/partnersProjects.js
  - phase: 13-03
    provides: app/src/components/PartnersMap.jsx (default export, `{ ll, partners, height = 300 }`)
  - phase: 13-04
    provides: app/src/components/PartnersOverviewPanel.jsx (named export `{ partners, projects, lang }`)
provides:
  - app/src/components/PartnersProjectsTab.jsx (named export PartnersProjectsTab({ ll, mapHeight = 300 }))
  - Right-side "Partners and Projects" tab control in LayerTabs.jsx
  - Three layer === 'partners' branch points in LLDetail.jsx (LayoutSplit, LayoutStacked, ComparisonColumn)
affects: [13-06]

tech-stack:
  added: []
  patterns:
    - "Composition root owning a single hook call plus a shared loading/error status slot, mirroring the App.jsx ErrorBanner / LLDetail.jsx LoadingCard padding:40 treatment"
    - "lazy(() => import(...)) + Suspense for the Leaflet-bearing child, mirroring LLDetail.jsx's own LLMap treatment one level up the tree"

key-files:
  created:
    - app/src/components/PartnersProjectsTab.jsx
  modified:
    - app/src/components/LayerTabs.jsx
    - app/src/pages/LLDetail.jsx

key-decisions:
  - "LayoutSplit's map slot in the narrow left column is fully suppressed when layer === 'partners' -- PartnersProjectsTab's own map renders once, in the wide right column -- per the UI-SPEC's explicit prose-lock resolution overriding its own conflicting ASCII-diagram parenthetical (documented in the plan's UI-SPEC resolution note)"
  - "LayoutStacked and ComparisonColumn each combine their chart-card + text-block replacement into a single ternary (PartnersProjectsTab in the true branch, a React fragment holding the original blocks in the false branch), while the StatPanel wrapper and the Suspense/LLMap block get their own separate layer !== 'partners' guards, matching the plan's two distinct instruction shapes for those two site classes"

requirements-completed: [D-04, D-05, D-09, D-10, D-14, D-17, D-18]

duration: "~35min"
completed: 2026-08-13
---

# Phase 13 Plan 05: Wire the Partners & Projects Tab Together Summary

**One new composition-root component, a right-side tab control, and three layer==='partners' branch points across LayoutSplit/LayoutStacked/ComparisonColumn -- the Partners & Projects tab is now reachable end-to-end in every layout, including two-column comparison mode.**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-08-13 (worktree base corrected to `e58e20d` before Task 1)
- **Completed:** 2026-08-13
- **Tasks:** 3/3
- **Files modified:** 3 (1 created, 2 modified)

## Accomplishments

- `PartnersProjectsTab.jsx` calls `usePartnersProjects(ll.slug)` exactly once, resolves language
  once via `normalizeLanguage(i18n.resolvedLanguage)`, and lazy-loads `PartnersMap` the same way
  `LLDetail.jsx` lazy-loads `LLMap` -- confirmed by the production build splitting a dedicated
  `PartnersMap-*.js` chunk (3.09 kB gzip 1.52 kB) out of the main bundle
- The D-14 coordinate split is centralized in one place: `PartnersMap` receives
  `partitionPartnersByCoordinates(data.partners).mapped`; `PartnersOverviewPanel` receives the
  full, unpartitioned `data.partners` array (verified by a zero-occurrence grep for `.unmapped` in
  the component's non-comment source)
- Loading and error states share one centred `padding: 40` slot (the named UI-SPEC spacing
  exception, inherited verbatim from `LoadingCard`/`ErrorBanner`); neither ever renders alongside
  the map or the panel
- `LayerTabs.jsx` now renders a second, visually distinct button group at the right end of the tab
  row (`justifyContent: 'space-between'`, `alignItems: 'flex-end'`, `borderLeft` separator,
  `marginLeft: 8`, `paddingLeft: 16`) without adding a sixth entry to `LAYERS` -- `layers.js` is
  byte-for-byte unchanged, confirmed by an empty `git diff --stat`
- All three of `LLDetail.jsx`'s independent content-composition sites (`LayoutSplit`,
  `LayoutStacked`, `ComparisonColumn`) branch on `layer === 'partners'`, and all three
  `llDetail.layerTabsHint` occurrences (including `LayoutCompare`'s third, phase-research-flagged
  site) are suppressed while the tab is active
- `LLMap` never mounts while `layer === 'partners'` at any of its three call sites; a negative grep
  for the literal `'partners'` in `LLMap/index.jsx`'s non-comment source returns 0, confirming the
  T-13-12 mitigation holds without any new branch inside `LLMap` itself

## Task Commits

Each task was committed atomically:

1. **Task 1: PartnersProjectsTab composition root** - `5685799` (feat)
2. **Task 2: Right-side Partners and Projects group in LayerTabs** - `22ca5f3` (feat)
3. **Task 3: Branch all three LLDetail content sites and suppress the thematic hint** - `4618756` (feat)

## Files Created/Modified

- `app/src/components/PartnersProjectsTab.jsx` - new composition root; single fetch, D-14 split,
  shared loading/error slot, lazy-loaded map + overview panel stack
- `app/src/components/LayerTabs.jsx` - added the right-side Partners and Projects button group;
  `app/src/data/layers.js` left untouched
- `app/src/pages/LLDetail.jsx` - added the `PartnersProjectsTab` import and four edits keyed on
  `layer === 'partners'`/`layer !== 'partners'` across `LayoutSplit`, `LayoutStacked`,
  `ComparisonColumn` and the three `layerTabsHint` sites

## Decisions Made

- Resolved the plan's own flagged UI-SPEC ambiguity for `LayoutSplit` per its explicit
  instruction: the prose lock ("map on top, panel below ... in every layout") wins over the ASCII
  diagram's conflicting parenthetical, so the narrow left column's map slot is suppressed and the
  partner map renders once, inside `PartnersProjectsTab`, in the wide right column. No second map
  is ever mounted.
- Kept `LayoutStacked` and `ComparisonColumn`'s `StatPanel`/`Suspense`+`LLMap` guards as two
  separate `layer !== 'partners' ? (...) : null` blocks (rather than merging them into the same
  ternary as the chart/text-block replacement), matching the plan's own separate phrasing for
  those two site classes and keeping the tabs-plus-map card's wrapper/tab-strip genuinely
  unconditional as instructed.

## Deviations from Plan

None — plan executed exactly as written. The `git diff` for `LLDetail.jsx` (532 changed lines
across a 285-insertion/247-deletion commit) looks large for four conceptual edits; verified line
by line that every changed hunk is either a literal new conditional/fragment I introduced or the
consequent re-indentation of the JSX I nested one level deeper -- targeted greps for
`CompareCTA`/`DownloadReportCTA`/`ComparisonBar`/`LayoutSwitcher`/`accent`/`useLayerState` inside
the diff confirm those blocks are untouched except for the one new import line.

## Issues Encountered

- Same pre-existing Windows `core.autocrlf=true` CRLF drift documented in `13-01-SUMMARY.md`,
  `13-03-SUMMARY.md` and `13-04-SUMMARY.md`: `npm run format:check` across the whole `app/` tree
  flags 52 files, none of which are this plan's three files. Investigated one instance
  (`LayerTabs.jsx`) in depth: after `npx prettier --write`, `git add` reported zero staged changes
  against the already-committed blob, proving the object database's stored content was already
  prettier-clean at the LF level -- the local `prettier --check` failure was produced entirely by
  git's checkout-time CRLF smudge filter rewriting the working-tree copy, not by any real
  formatting defect in the commit. No fix commit was needed or made for `LayerTabs.jsx`; this
  plan's own three files (`PartnersProjectsTab.jsx`, `LayerTabs.jsx`, `LLDetail.jsx`) all pass
  `npx prettier --check` individually in the current working tree, and none of the three appear in
  the whole-tree `format:check` failure list. The remaining 52 pre-existing files are unrelated to
  this plan and out of scope, matching prior plans' documented precedent.
- `npm run install` was required once at the start of this worktree session (`app/node_modules`
  absent, same one-time environment condition documented in every prior Phase 13 plan). No
  `package.json`/`package-lock.json` changes resulted.

## Next Phase Readiness

The Partners & Projects tab is now reachable and functional end-to-end in `LayoutSplit`,
`LayoutStacked` and the two-column `ComparisonColumn` layout, satisfying this plan's three
`<success_criteria>`. No blockers for `13-06` (the phase's closing wave: full automated gate plus
the blocking bilingual human-verification checkpoint). One item worth flagging for that
checkpoint's manual pass: the tab's keyboard-focus tooltip wiring (`13-03-SUMMARY.md`) and the
comparison-mode dual-column simultaneous fetch (T-13-11's mitigation, module-scoped cache in
`usePartnersProjects`) have not yet been manually exercised end-to-end in a running browser.

## Self-Check: PASSED

- FOUND: app/src/components/PartnersProjectsTab.jsx
- FOUND: app/src/components/LayerTabs.jsx (modified)
- FOUND: app/src/pages/LLDetail.jsx (modified)
- FOUND commit 5685799 (Task 1)
- FOUND commit 22ca5f3 (Task 2)
- FOUND commit 4618756 (Task 3)

---
*Phase: 13-add-a-projects-and-partners-tab-to-individual-living-lab-pag*
*Completed: 2026-08-13*
