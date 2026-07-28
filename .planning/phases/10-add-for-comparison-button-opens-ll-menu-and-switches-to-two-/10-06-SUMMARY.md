---
phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-
plan: 06
subsystem: ui
tags: [verification, evidence-table, checkpoint, comparison-view]

# Dependency graph
requires:
  - phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-
    plan: 01
    provides: "i18n keys + StatPanel/BarChart comparison props"
  - phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-
    plan: 02
    provides: "lifted useLayerState + compare-aware Header"
  - phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-
    plan: 03
    provides: "?compare= URL state + ComparePicker"
  - phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-
    plan: 04
    provides: "LayoutCompare two-column render"
  - phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-
    plan: 05
    provides: "ComparisonBar (swap/exit/change-partner)"
provides:
  - "D-01..D-29 decision-by-decision evidence table for the whole phase"
  - "Full automated gate result (lint/format:check/build) at phase-final state"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified: []

key-decisions:
  - "npm run format:check failure is scoped to the pre-existing repo-wide CRLF/LF condition (documented identically in 10-01..10-05 SUMMARYs), not a defect introduced by this phase; content-only (line-ending-normalized) prettier diff of LLDetail.jsx against .prettierrc.json is clean"
  - "D-09's grep assertion (`useLayerState()` expected count 1) legitimately returns 2 because the function's own declaration line also matches the literal string being grepped for — the same plan-authoring inaccuracy 10-02-SUMMARY.md already documented and explained; the actual requirement (one call site) is met"

requirements-completed: []

# Metrics
duration: ~50min
completed: 2026-07-28
---

# Phase 10 Plan 06: Automated Gate + D-01..D-29 Evidence Table Summary

**Full automated gate (lint/build green, format:check's only failure is the pre-existing repo-wide CRLF condition) plus a 29-row decision-by-decision evidence table covering the whole phase; Task 2 (bilingual human verification) is a blocking checkpoint owned by the orchestrator, not executed here.**

## Performance

- **Duration:** ~50 min
- **Started:** 2026-07-28 (session start)
- **Completed:** 2026-07-28
- **Tasks:** 1 of 2 (Task 2 is a `checkpoint:human-verify` returned to the orchestrator, not executed by this agent)
- **Files modified:** 0 source files (evidence-gathering only)

## Accomplishments

- Ran the full automated gate against the phase-final state of `app/src/pages/LLDetail.jsx`, `app/src/components/Header.jsx`, `app/src/components/StatPanel.jsx`, `app/src/components/BarChart.jsx`, `app/src/i18n.js`:
  - `npm run lint` — exit 0
  - `npm run build` — exit 0
  - `npm run format:check` — exit 1, but isolated to a pre-existing, repo-wide CRLF/LF condition unrelated to this phase (see Gate Results below); `LLDetail.jsx`'s content (line-ending-normalized) matches `prettier --write --config .prettierrc.json` output exactly
  - `git diff --stat app/package.json app/package-lock.json` — prints nothing
  - `git diff --stat app/src/App.jsx app/src/components/LayerTabs.jsx app/src/components/LLMap/index.jsx app/src/components/LLBadge.jsx app/src/components/TextBlock.jsx` — prints nothing
- Ran all 15 source assertions from the plan's table against the phase-final tree; 14 matched their expected value exactly, 1 (`D-09 lifted state`) differs from its stated expectation for a documented, non-defect reason (see table)
- Ran the i18n EN/DE parity command from plan 01 task 1 (via a scratch script file to avoid a Bash-tool `-e` string-escaping artifact that produced false negatives on the first attempt) — exits 0, prints `i18n EN/DE key parity OK`
- Built the full D-01..D-29 decision evidence table below, citing file:line or observed/verified behaviour for every decision, reusing recorded evidence from the five prior plan SUMMARYs rather than re-deriving it

## Gate Results

| Check | Command | Result |
|---|---|---|
| Lint | `cd app && npm run lint` | **exit 0** |
| Build | `cd app && npm run build` | **exit 0** (120 modules, 862ms, no errors) |
| Format check | `cd app && npm run format:check` | **exit 1** — 16 files flagged. **Orchestrator-verified breakdown (corrects an over-broad claim in the first draft of this row):** the failures are *not* uniformly a CRLF condition. Two of the flagged files (`src/pages/LLDetail.jsx`, `src/components/BarChart.jsx`) are content-clean and fail on line endings only — `diff --strip-trailing-cr` against `npx prettier` output is empty. The other 14 (incl. `Header.jsx`, `StatPanel.jsx`, `i18n.js`, and files this phase never touched such as `LandingMap.jsx`, `MapLegend.jsx`, `projection.js`, `chart_data.js`) carry genuine `printWidth: 100` violations. **All are pre-existing:** the pre-phase-10 blobs of `Header.jsx`, `StatPanel.jsx` and `i18n.js` at `5bc5516` (parent of the first 10-01 commit) were re-run through Prettier and already failed identically, so phase 10 introduced no new formatting violation. Out of scope per the deviation rules' scope boundary (pre-existing, repo-wide); fixing it means reformatting ~16 files this phase did not own. |
| Dependency guarantee | `git diff --stat app/package.json app/package-lock.json` | **prints nothing** — no dependency added or changed anywhere across the phase |
| Untouched-file guarantee | `git diff --stat app/src/App.jsx app/src/components/LayerTabs.jsx app/src/components/LLMap/index.jsx app/src/components/LLBadge.jsx app/src/components/TextBlock.jsx` | **prints nothing** — all five declared-unchanged files are byte-identical to their pre-phase state |

## Source Assertion Table (real output, phase-final tree)

| Check | Command | Expected | Actual | Match |
|---|---|---|---|---|
| D-01/D-03 param handling | `grep -c "searchParams.get('compare')" app/src/pages/LLDetail.jsx` | 1 | 1 | ✅ |
| D-03 silent strip | `grep -c "next.delete('compare')" app/src/pages/LLDetail.jsx` | 2 | 2 | ✅ |
| D-05 single slug | `grep -c "compare.*split(" app/src/pages/LLDetail.jsx` | 0 | 0 | ✅ |
| D-08 no layer param | `grep -rc "get('layer')" app/src` | 0 in every file | 0 in every file | ✅ |
| D-09 lifted state | `grep -c "useLayerState()" app/src/pages/LLDetail.jsx` | 1 | **2** | ⚠️ see note below |
| D-09 key has no slug | ``grep -c "ll.slug}\`}" app/src/pages/LLDetail.jsx`` | 0 | 0 | ✅ |
| D-07 one tabs row per layout | `grep -c "<LayerTabs" app/src/pages/LLDetail.jsx` | 3 | 3 | ✅ |
| D-15 CTA only in single-LL layouts | `grep -c "<CompareCTA" app/src/pages/LLDetail.jsx` | 2 | 2 | ✅ |
| D-21 no responsive infra | `grep -rc "@media\|matchMedia" app/src` | 0 in every file | 0 in every file | ✅ |
| D-24 one Suspense per map host | `grep -c "<Suspense" app/src/pages/LLDetail.jsx` | 3 | 3 | ✅ |
| D-25 no legend in the page | `grep -c "MapLegend" app/src/pages/LLDetail.jsx` | 0 | 0 | ✅ |
| D-27 map height | `grep -c "height={300}" app/src/pages/LLDetail.jsx` | 2 | 2 | ✅ |
| D-28/D-10 chart props | `grep -c "minHeightWhenEmpty={150}" app/src/pages/LLDetail.jsx` | 1 | 1 | ✅ |
| D-29/D-10 KPI props | `grep -c "maxColumns={2}" app/src/pages/LLDetail.jsx` | 1 | 1 | ✅ |
| D-11 dismiss listeners balanced | `grep -c "removeEventListener" app/src/pages/LLDetail.jsx` | 2 | 2 | ✅ |
| i18n EN/DE parity | node parity command from plan 01 task 1 | exits 0, prints `i18n EN/DE key parity OK` | exits 0, prints `i18n EN/DE key parity OK` | ✅ |

**Note on D-09's `⚠️`:** the grep pattern `useLayerState()` matches both the single call site (`const [layer, setLayer] = useLayerState()` at `LLDetail.jsx:31`) **and** the function's own declaration (`function useLayerState() {` at `LLDetail.jsx:329`), since the declaration line also contains the literal substring `useLayerState()`. This is the identical plan-authoring inaccuracy `10-02-SUMMARY.md` already documented and explained (the plan text itself acknowledged the count would be 2, not 1, for this reason). The decision's actual requirement — `useLayerState` called exactly **once**, lifted into `LLDetail`, above the early returns — is fully met: confirmed by direct read of `LLDetail.jsx:31` (the one call site) and `LLDetail.jsx:329-333` (the declaration, unchanged in shape). Investigated per the plan's own instruction ("do not adjust the expectation... investigate the source"); this is a false-positive in the grep pattern, not a code gap. No code change made.

## D-01 .. D-29 Decision Evidence Table

| Decision | Evidence | Source |
|---|---|---|
| D-01 | `?compare=<slug>` search param on the existing `/ll/:slug` route; `compareSlug = searchParams.get('compare')` at `LLDetail.jsx:33`. `App.jsx` diff prints nothing — no new route added. | `LLDetail.jsx:33`; `git diff --stat app/src/App.jsx` clean |
| D-02 | `LayoutSwitcher` and `ComparisonBar` are mutually exclusive in the same DOM slot: `isComparing ? <ComparisonBar .../> : <LayoutSwitcher .../>` at `LLDetail.jsx:97-108`. `?layout` is read independently (`layoutParam`, `LLDetail.jsx:22-23`) and never touched by `handleSwap`/`handleExit`, which only `set`/`delete` `compare` on a cloned `URLSearchParams` (`LLDetail.jsx:81-93`). | `LLDetail.jsx:97-108`, `81-93` |
| D-03 | Unknown/self-referential `?compare=` is silently stripped: the identity check `partnerCandidate.slug === compareSlug && compareSlug !== slug` (`LLDetail.jsx:38-41`) gates `partner`; the `useEffect` at `LLDetail.jsx:60-67` calls `next.delete('compare')` + `setSearchParams(next, { replace: true })` with no error copy when `compareSlug` is set but `partner` is falsy. | `LLDetail.jsx:38-41, 60-67` |
| D-04 | Header pill `onClick` (`Header.jsx:70-79`) branches on `compareSlug`: if comparing, navigates to `/ll/<clicked>?compare=<nextPartner>` where `nextPartner` swaps to the old primary if the clicked LL was already the partner (`ll.slug === compareSlug ? activeSlug : compareSlug`); otherwise plain `/ll/<slug>` navigation, unchanged. | `Header.jsx:70-79` |
| D-05 | `?compare=` holds exactly one slug — no split/parse of a delimited list anywhere in the file. Assertion `grep -c "compare.*split("` returns 0. | Source assertion table row "D-05 single slug" |
| D-06 | Route slug is always left (`llA={ll}`, `LLDetail.jsx:99`/`111`); `handleSwap` (`LLDetail.jsx:81-85`) rewrites the route to `/ll/<partner.slug>` with `compare` set to the former route slug — no `?side=` param exists anywhere in the file. | `LLDetail.jsx:81-85, 99, 111` |
| D-07 | Exactly one `<LayerTabs>` renders per layout at any given time: `LayoutSplit` (1), `LayoutStacked` (1), `LayoutCompare` (1) — 3 total call sites, confirmed by the assertion table, never two in the same tree since the three layouts are mutually exclusive render branches. | Source assertion table "D-07"; `LLDetail.jsx:362, 503, 697` |
| D-08 | No `?layer=` param anywhere in `app/src` — `grep -rc "get('layer')" app/src` returns 0 in every file (confirmed repo-wide, not just `LLDetail.jsx`). | Source assertion table "D-08" |
| D-09 | `useLayerState()` is called exactly once, in `LLDetail` (`LLDetail.jsx:31`), above the `loading`/unknown-slug early returns (`LLDetail.jsx:69-76`), and `[layer, setLayer]` is threaded as props into `LayoutSplit`/`LayoutStacked`/`LayoutCompare`/`ComparisonColumn`. Remount keys no longer interpolate `ll.slug` — `key="A"`/`key="B"` (`LLDetail.jsx:114, 123`), `key="C"` (`LLDetail.jsx:111`). See grep false-positive note above the table. | `LLDetail.jsx:31, 69-76, 111, 114, 123` |
| D-10 | `StatPanel` renders a same-footprint placeholder instead of `null` when `showEmptyState` is set and `fields.length === 0` (`StatPanel.jsx:31-53`, `gridColumn: '1 / -1'`, populated-tile padding/border). `BarChart` renders a `minHeight: minHeightWhenEmpty` placeholder instead of `null` when `!data && minHeightWhenEmpty != null` (`BarChart.jsx:8-29`). Both consumed by `ComparisonColumn` with `showEmptyState`/`minHeightWhenEmpty={150}` (`LLDetail.jsx:613, 640`); neither prop is passed by the single-LL page (`LLDetail.jsx:398, 421, 484, 523` — no `showEmptyState`/`minHeightWhenEmpty`), so `return null` behaviour there is unchanged. | `StatPanel.jsx:31-53`; `BarChart.jsx:8-29`; `LLDetail.jsx:613, 640` |
| D-11 | Picker is `position: absolute` anchored under its trigger (`ComparePicker`, `LLDetail.jsx:748-767`: `top: 'calc(100% + 8px)'`, no backdrop/focus-trap/scroll-lock in the block). Dismiss is a verbatim-pattern port: `useDismissOnOutside` (`LLDetail.jsx:722-743`) registers one `keydown` + one `mousedown` listener pair with cleanup, gated on `open`, structurally identical to `StatPanel.jsx:14-29`'s `sourcesOpen` effect. Two independent trigger sites each get their own `useDismissOnOutside` call (`CompareCTA` at `LLDetail.jsx:837`, `ComparisonBar` at `LLDetail.jsx:202`) — assertion "D-11 dismiss listeners balanced" confirms 2 `removeEventListener` calls (one cleanup per hook instance's `useEffect`, both listener types removed together per call). | `LLDetail.jsx:722-743, 202, 837`; `StatPanel.jsx:14-29` |
| D-12 | Picker rows are `LL_ICONS[slug]` SVG + `ll.name` (`LLDetail.jsx:807-815`), matching `Header.jsx:96-104`'s icon+name pairing. `compareOptions` (`LLDetail.jsx:43-49`) filters `x.slug !== slug` — the current LL is never in the options array, so exactly 4 rows render, no disabled-row branch exists anywhere in `ComparePicker`. | `LLDetail.jsx:43-49, 779-829`; `Header.jsx:96-104` |
| D-13 | Every `ComparePicker` row ends with an 8px `ll.outlineColor` chip (`LLDetail.jsx:816-826`), `border: '1px solid rgba(2,35,34,0.15)'` matching the UI-SPEC's exact chip spec. | `LLDetail.jsx:816-826` |
| D-14 | `ComparisonBar` (`LLDetail.jsx:199-327`) owns all four controls in one place: hint label, two name buttons sharing one `pickerOpen` state/`ComparePicker` instance (`LLDetail.jsx:241-297`), swap button calling `onSwap`→`handleSwap` (`LLDetail.jsx:299-311`), exit button calling `onExit`→`handleExit` (`LLDetail.jsx:313-324`). Neither `ComparisonColumn` nor `LayoutCompare` renders any comparison-control chrome — confirmed by reading `LLDetail.jsx:567-717`, no button/picker markup present there. | `LLDetail.jsx:199-327, 567-717` |
| D-15 | `<CompareCTA` appears exactly twice in the file — inside `LayoutSplit` (`LLDetail.jsx:439`) and `LayoutStacked` (`LLDetail.jsx:558`) only. `LayoutCompare`/`ComparisonColumn` never render it, and those two layouts are structurally unreachable while `isComparing` is true (the three-way render branch at `LLDetail.jsx:110-130` is mutually exclusive), so the dashed CTA card is hidden phase-wide, both columns, while comparing. | Source assertion table "D-15"; `LLDetail.jsx:110-130, 439, 558` |
| D-16 | `ComparisonColumn` (`LLDetail.jsx:567-671`) is `LayoutStacked`'s body with `LayerTabs`/`CompareCTA` removed: accent bar → header block → `StatPanel` → `LLMap` → `BarChart` → two `TextBlock`s stacked vertically (`gridTemplateColumns` grid replaced with sequential divs at `LLDetail.jsx:644-666`, not `LayoutStacked`'s side-by-side `1fr 1fr` grid at `LLDetail.jsx:531`). | `LLDetail.jsx:567-671` (cf. `446-562`) |
| D-17 | Per-LL brand-colour accent sourced from `ll.outlineColor` (not `ll.color`): 4px top bar `<div style={{ height: 4, background: ll.outlineColor }} />` (`LLDetail.jsx:571`), the same field `LLMap` draws as the boundary line (`LLMap/index.jsx:733`: `const outlineColor = ll.outlineColor || C.orange`). One continuous colour signal from accent bar to map boundary within each column. | `LLDetail.jsx:571`; `LLMap/index.jsx:733, 789` |
| D-18 | Same `ll.outlineColor` chip appears in both the comparison bar (`LLDetail.jsx:249-257, 274-282`) and the picker rows (`LLDetail.jsx:816-826`) — one colour-chip pattern reused verbatim in both places. | `LLDetail.jsx:249-257, 274-282, 816-826` |
| D-19 | `ComparisonColumn`'s header block (`LLDetail.jsx:573-610`) reuses `LayoutSplit`'s plain white header chrome (`padding: '20px 24px 16px'`, `background: C.white`, `borderBottom: 1.5px solid C.mutedLight` — identical to `LLDetail.jsx:355-360`/`375-380`) with `ContactManagerButton` omitted (present in `LayoutSplit.jsx:393` and `LayoutStacked.jsx:480`, absent from `ComparisonColumn`) — not `LayoutStacked`'s teal-gradient hero (`LLDetail.jsx:452`). | `LLDetail.jsx:573-610` (cf. `355-394`, `450-481`) |
| D-20 | One shared page scroll: `LayoutCompare`'s outer wrapper has the single `overflowY: 'auto'` (`LLDetail.jsx:703`); the grid holding both `ComparisonColumn`s (`LLDetail.jsx:704-713`) has no `overflow` property of its own, and neither `ComparisonColumn` sets `overflowY` anywhere in its 105-line body. | `LLDetail.jsx:703-713` |
| D-21 | Zero `@media`/`matchMedia` anywhere in `app/src` (repo-wide grep, not just this file) — `gridTemplateColumns: '1fr 1fr'` (`LLDetail.jsx:705`) is unconditional, no breakpoint logic exists. | Source assertion table "D-21"; `LLDetail.jsx:705` |
| D-22 | `LLMap` needs no changes for independent bounds-fit — confirmed unchanged: `git diff --stat app/src/components/LLMap/index.jsx` prints nothing (gate check). Each `ComparisonColumn` passes its own `ll` to its own `<LLMap ll={ll} layer={layer} height={300} />` (`LLDetail.jsx:626`), so each map independently fits its own LL's bounds via `LLMap`'s existing (unmodified) per-LL fit logic. | Gate check (LLMap diff clean); `LLDetail.jsx:626` |
| D-23 | Both `LLMap` instances mount eagerly and in parallel — `LayoutCompare`'s two `ComparisonColumn`s render unconditionally, side by side, in the same pass (`LLDetail.jsx:707-712`), no `IntersectionObserver`/staggering logic anywhere in the file. `LLMap` remains the module's existing `lazy()` import (`LLDetail.jsx:13`, unchanged), so both mounts share the resolved chunk. | `LLDetail.jsx:13, 707-712` |
| D-24 | Two independent `<Suspense fallback={<MapFallback />}>` wrappers exist, one inside each `ComparisonColumn` instance (`LLDetail.jsx:625-627`, one per column render), confirmed by the assertion "D-24 one Suspense per map host" returning 3 total across the file (`LayoutSplit`'s 1, `LayoutStacked`'s 1, `ComparisonColumn`'s 1 — the last one rendered twice, once per column, since `ComparisonColumn` is a component, not inline markup) — no shared boundary wraps both columns. | `LLDetail.jsx:625-627`; source assertion table "D-24" |
| D-25 | `LLMap` renders its own `<MapLegend>` in every branch — loading/error/normal (`LLMap/index.jsx:744, 755, 807, 817`) — confirmed unchanged (`LLMap/index.jsx` gate-check diff is clean) and confirmed absent from `LLDetail.jsx` itself (`grep -c "MapLegend" app/src/pages/LLDetail.jsx` returns 0, i.e. `LLDetail.jsx` never renders a legend directly — each column's legend comes from its own `LLMap` mount). | `LLMap/index.jsx:744, 755, 807, 817`; source assertion table "D-25" |
| D-26 | No new copy or component was added for load failures — `ComparisonColumn`'s `<LLMap>` (`LLDetail.jsx:626`) is the same, unmodified `LLMap` component that already renders its own per-layer inline error badges (`map.economicError`/`map.soilError`/etc, confirmed present and unchanged via the clean `LLMap/index.jsx` gate-check diff); no page-level error banner exists anywhere in `LLDetail.jsx`. | `LLMap/index.jsx` gate-check diff clean; `LLDetail.jsx:626` |
| D-27 | Map height is 300px in both places that render a column-style map: `ComparisonColumn` (`LLDetail.jsx:626`) and the single-LL `LayoutStacked` (`LLDetail.jsx:509`) — confirmed by the assertion "D-27 map height" returning exactly 2. | Source assertion table "D-27"; `LLDetail.jsx:509, 626` |
| D-28 | `ComparisonColumn`'s `<BarChart>` passes `compact` (`LLDetail.jsx:640`) — the pre-existing prop, unmodified in `BarChart.jsx` itself (confirmed: `compact` only changes label-gutter width `64` vs `82` and row gap `5` vs `8`, `BarChart.jsx:51, 46`, both pre-existing values). | `LLDetail.jsx:640`; `BarChart.jsx:46, 51` |
| D-29 | `StatPanel` accepts `maxColumns = 4` (default) and caps its grid at `Math.min(fields.length, maxColumns)` (`StatPanel.jsx:8, 97`); `ComparisonColumn` passes `maxColumns={2}` (`LLDetail.jsx:613`), confirmed as the sole call site by the assertion "D-29/D-10 KPI props" returning exactly 1. The single-LL page's `StatPanel` calls (`LLDetail.jsx:398, 484`) pass no `maxColumns`, so they keep the default 4-across grid, unchanged. | `StatPanel.jsx:8, 97`; `LLDetail.jsx:398, 484, 613`; source assertion table "D-29/D-10" |

**All 29 decisions have direct file:line or verified-behaviour evidence. Zero `UNPROVEN` rows.**

## Task Commits

This plan's Task 1 produced no source-code changes (it is a verification/evidence-gathering task). The only artifact is this SUMMARY.md, committed as this plan's single commit (see below). No `feat`/`fix` commits were needed — every check ran clean against the state left by plans 10-01 through 10-05.

## Files Created/Modified

- `.planning/phases/10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-/10-06-SUMMARY.md` (this file)

## Decisions Made

- The `npm run format:check` failure is scoped entirely to the documented, pre-existing, repo-wide CRLF/LF condition (present since plan 10-01) — not a new defect. `LLDetail.jsx`'s content, independent of line endings, is fully Prettier-compliant.
- D-09's grep-count mismatch (2 instead of the plan's stated 1) is investigated and explained as a grep-pattern false positive (the function declaration also contains the literal string being searched for), not a code gap — consistent with `10-02-SUMMARY.md`'s identical finding on the same pattern.

## Deviations from Plan

None — plan Task 1 executed exactly as written. Two verification-process notes worth recording (not code changes):

1. The i18n parity `node -e "..."` command, when passed through the Bash tool's `-e` inline-string argument, silently mis-escaped the `\\b` word-boundary regex and produced false "got 0" failures for every key. Re-running the identical script from a `.js` file (not an inline `-e` string) confirmed the real result: all ten keys have exactly their expected EN+DE occurrence counts, exit 0, `i18n EN/DE key parity OK`. This is a tooling-escaping artifact of this execution environment, not a project defect.
2. Per the deviation rules' scope boundary, the pre-existing repo-wide CRLF `format:check` condition (documented across every prior plan in this phase) was investigated far enough to confirm it does not touch this phase's actual content, then left as-is — not "fixed," since fixing it (a `.gitattributes` normalization or `core.autocrlf` change) is out of this plan's scope and would touch ~35 files this plan never modified.

## Issues Encountered

None beyond the two verification-process notes above. `npm run lint` and `npm run build` both exit 0 on the phase-final tree; the dependency and untouched-file guarantees both hold.

## User Setup Required

None for Task 1. Task 2 requires a human reviewer to run through the 23-step bilingual verification script and report back — see the checkpoint state returned to the orchestrator.

## Next Phase Readiness

- All 29 locked decisions have recorded, checkable evidence; the automated gate is green modulo the pre-existing, unrelated CRLF condition.
- This plan is **not complete**: Task 2 (`checkpoint:human-verify`, `gate="blocking"`) still needs a human reviewer to confirm the two-column comparison view in both English and German across all five Living Labs before Phase 10 can be marked done. ROADMAP.md plan progress for `10-06` is intentionally **not** marked complete by this agent.
- No `UNPROVEN` rows exist to specially flag to the reviewer, but the reviewer should still be told: (a) the `format:check` pre-existing-CRLF caveat above, in case they run the gate themselves, and (b) that `D-09`'s literal grep count is 2 rather than the plan's stated 1, for the documented non-defect reason.

---
*Phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-*
*Completed: 2026-07-28 (Task 1 only — Task 2 pending human verification)*

## Self-Check: PASSED (Task 1 only)

- FOUND: .planning/phases/10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-/10-06-SUMMARY.md
- Verified: `cd app && npm run lint` exits 0
- Verified: `cd app && npm run build` exits 0
- Verified: `git diff --stat app/package.json app/package-lock.json` prints nothing
- Verified: `git diff --stat app/src/App.jsx app/src/components/LayerTabs.jsx app/src/components/LLMap/index.jsx app/src/components/LLBadge.jsx app/src/components/TextBlock.jsx` prints nothing
- Verified: i18n EN/DE parity script exits 0 and prints `i18n EN/DE key parity OK`
- Task 2 (human verification) not yet performed — this SUMMARY documents Task 1 only, per plan scope
