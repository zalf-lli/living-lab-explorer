---
phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-
plan: 04
subsystem: ui
tags: [react, comparison-view, two-column-layout, grid, suspense]

# Dependency graph
requires:
  - phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-
    plan: 01
    provides: "StatPanel maxColumns/showEmptyState props, BarChart minHeightWhenEmpty prop, empty-state i18n keys"
  - phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-
    plan: 03
    provides: "?compare= URL state (compareSlug/partner/compareOptions/setCompare) already parsed and identity-validated in LLDetail"
provides:
  - "ComparisonColumn({ ll, layer }) — a compact, self-contained single-LL column: accent bar, plain header (no ContactManagerButton), 2-column-capped StatPanel, its own Suspense-wrapped LLMap at height 300, compact BarChart, two stacked TextBlocks"
  - "LayoutCompare({ llA, llB, layer, setLayer }) — one shared LayerTabs row above one shared scroll container holding a 1fr/1fr grid of two ComparisonColumns"
  - "isComparing = Boolean(partner), now a real top-level binding in LLDetail, driving a three-way render branch (LayoutCompare / LayoutSplit / LayoutStacked)"
  - "/ll/<a>?compare=<b> now renders a working two-column comparison instead of the single-LL layout"
affects: ["10-05", "10-06"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Compose-don't-duplicate: ComparisonColumn is literally LayoutStacked's body minus LayerTabs/CompareCTA, with LayoutSplit's header chrome substituted for LayoutStacked's gradient hero — no new visual primitives introduced, only new arrangements of existing components (StatPanel, BarChart, LLMap, TextBlock, LLBadge)"
    - "One shared control drives N independent renderers: a single <LayerTabs active={layer} onChange={setLayer}> above the grid, with each ComparisonColumn receiving layer as a prop and mounting its own independent <Suspense>/<LLMap> — no shared Suspense boundary, no staggering, matching D-24's 'independent per column' requirement"
    - "Temporary eslint-disable-next-line no-unused-vars on a function declaration, removed in the very next task once its call site lands — used twice (ComparisonColumn in task 1, wired in task 2; LayoutCompare in task 2, wired in task 3) instead of restructuring task boundaries, since each task's own acceptance criteria required the named function to exist as a standalone artifact"

key-files:
  created: []
  modified:
    - app/src/pages/LLDetail.jsx

key-decisions:
  - "isComparing = Boolean(partner) is now extracted as a real top-level binding (10-03 deliberately deferred this exact re-derivation to this plan, per its own SUMMARY's 'Next Phase Readiness' note)"
  - "LayoutSwitcher is left untouched in its DOM slot per the plan's explicit instruction — plan 05 replaces it with the comparison bar; this means the layout A/B toggle remains visible (but ineffective) while isComparing is true, which is the plan's documented intended intermediate state, not a bug"
  - "Kept LayoutStacked's literal 32px/18px/16px margin/gap values inside each half-width ComparisonColumn rather than scaling them down — PATTERNS.md explicitly flagged this as 'planner discretion, not a blocker' and UI-SPEC.md's Spacing Scale explicitly reserves the 32px xl token for exactly this reuse"

patterns-established:
  - "Per-task temporary eslint-disable for build-order artifacts: when a plan's task boundaries require a function to exist as a standalone, source-grep-verifiable artifact before its only consumer exists in a later task, add a scoped eslint-disable-next-line no-unused-vars with a comment naming the task that removes it, rather than restructuring the plan's task split. Established precedent for any future plan.jsx-in-one-file multi-task sequences in this codebase."

requirements-completed: []

# Metrics
duration: ~50min
completed: 2026-07-28
---

# Phase 10 Plan 04: Two-Column Comparison Render Summary

**`LayoutCompare` renders two `ComparisonColumn`s side by side under one shared `LayerTabs` row and one shared scroll container; `LLDetail` now branches into it whenever `isComparing` is true**

## Performance

- **Duration:** ~50 min
- **Started:** 2026-07-28T06:05:00Z (approx)
- **Completed:** 2026-07-28T06:55:00Z (approx)
- **Tasks:** 3
- **Files modified:** 1

## Accomplishments

- `ComparisonColumn({ ll, layer })` composes a compact single-LL column: a 4px `ll.outlineColor` accent bar (the same hex `LLMap` draws as that LL's boundary line), `LayoutSplit`'s plain white header chrome with `ContactManagerButton` omitted and the typography collapsed to the phase's closed 12px/22px, 400/700 system (D-19), a `StatPanel` capped at `maxColumns={2}` with `showEmptyState` (D-29/D-10), its own `Suspense`-wrapped `<LLMap height={300}>` (D-22..D-27 — no shared Suspense boundary, no staggering), a `compact` `BarChart` with a 150px empty-state floor (D-28/D-10), and two vertically stacked `TextBlock`s (D-16, not the single-LL page's side-by-side grid)
- `LayoutCompare({ llA, llB, layer, setLayer })` renders exactly one `LayerTabs` row (ported `LayoutStacked` tab-strip chrome) above exactly one `overflowY: 'auto'` scroll container, inside which a `gridTemplateColumns: '1fr 1fr'` / `gap: 24` grid holds the two columns, left one bordered to match `LayoutSplit`'s divider convention (D-20/D-21/D-07)
- `LLDetail` now derives `isComparing = Boolean(partner)` as a real binding (10-03 had deliberately deferred this to avoid an unused-variable error) and branches its render: `isComparing` renders `<LayoutCompare key="C" llA={ll} llB={partner} .../>`; otherwise the existing `layout === 'A' ? LayoutSplit : LayoutStacked` ternary is byte-identical to before, including the `compareOptions`/`onPickCompare` props plan 03 added
- Confirmed via source grep that `CompareCTA` appears exactly twice in the file (inside `LayoutSplit` and `LayoutStacked` only) — structurally unreachable while comparing, satisfying D-15 without any conditional-hide logic
- Verified `LLMap` already renders its own `MapLegend` in all three of its render branches (loading/error/normal, confirmed at `LLMap/index.jsx:744,755,807,817`) and that `ll.outlineColor` is set as a React style-object property (not raw HTML/CSS string), satisfying threat mitigations T-10-12 and T-10-11 with zero new code

## Task Commits

Each task was committed atomically:

1. **Task 1: Build the ComparisonColumn component** - `fce0ec9` (feat)
2. **Task 2: Build the LayoutCompare two-column grid with one shared LayerTabs row** - `a4612e8` (feat)
3. **Task 3: Branch LLDetail into comparison mode** - `d598d30` (feat)

**Plan metadata:** (this commit, docs)

## Files Created/Modified

- `app/src/pages/LLDetail.jsx` - added `ComparisonColumn` (after `LayoutStacked`) and `LayoutCompare` (after `ComparisonColumn`) as new local functions; replaced the two-way `layout === 'A' ? ... : ...` render ternary with a three-way `isComparing ? <LayoutCompare .../> : layout === 'A' ? ... : ...` branch; extracted `isComparing = Boolean(partner)` as a top-level binding, replacing the code comment that previously explained its deferral

## Decisions Made

- Followed D-06, D-07, D-09 (unaffected — `useLayerState` was already lifted in plan 02), D-10, D-15, D-16, D-17, D-19 through D-29 exactly as specified in `10-CONTEXT.md`, `10-UI-SPEC.md`, and `10-PATTERNS.md`. Every UI-SPEC-declared literal (padding, border, border-radius, font-size/weight/line-height, spacing-scale token) was copied verbatim rather than approximated.
- `isComparing` now lives in `LLDetail` exactly as plan 03's SUMMARY anticipated ("Plan 04 should re-derive `isComparing = Boolean(partner)` at its own branch point").

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Temporary `eslint-disable-next-line no-unused-vars` on `ComparisonColumn` (Task 1) and `LayoutCompare` (Task 2), each removed in the very next task**
- **Found during:** Task 1 and Task 2 verification (`npm run lint`)
- **Issue:** The plan splits one cohesive feature across three tasks, each with its own `<verify>cd app && npm run lint && npm run build</verify>` and acceptance criteria requiring the named function to exist as a standalone, source-grep-verifiable artifact (`function ComparisonColumn({ ll, layer })` for Task 1; `function LayoutCompare({ llA, llB, layer, setLayer })` for Task 2). Neither function has a consumer until a later task wires it in, so `npm run lint` genuinely fails with `no-unused-vars` after Task 1's and Task 2's edits alone — this blocks each task's own required verification step from passing.
- **Fix:** Added a scoped `// eslint-disable-next-line no-unused-vars -- wired into <consumer> in the next task of this plan` comment directly above each function declaration, and removed it in the task that adds the consuming call site (Task 2 removes `ComparisonColumn`'s disable; Task 3 removes `LayoutCompare`'s disable). This mirrors 10-03's precedent of treating this exact class of issue as a real, immediate blocker (see `10-03-SUMMARY.md`'s Deviation 1), but resolves it via a scoped, self-documenting, self-removing disable comment instead of deferring the binding's introduction — appropriate here because, unlike 10-03's `isComparing`, this plan's acceptance criteria explicitly require each function to exist as a named, grep-matchable artifact after its own task.
- **Files modified:** `app/src/pages/LLDetail.jsx`
- **Verification:** `npm run lint` exits 0 after every one of the three tasks' commits, individually confirmed by running lint immediately after each edit and before each commit. Zero `eslint-disable` comments remain in the plan's final state (confirmed by grep after Task 3).
- **Committed in:** `fce0ec9` (Task 1, added), `a4612e8` (Task 2, removed for `ComparisonColumn` / added for `LayoutCompare`), `d598d30` (Task 3, removed for `LayoutCompare`)

**2. [Rule 3 - Blocking issue] Reverted 34 files unintentionally reformatted by `npm run format`**
- **Found during:** Post-Task-3 verification, `git status --short`
- **Issue:** This plan's per-task verification loop ran `npm run format` (to keep `LLDetail.jsx` Prettier-compliant before each commit) from the `app/` directory. `npm run format` invokes `prettier --write .`, which reformats every tracked file under `app/`, not just the one this plan is scoped to modify. `git status` after Task 2 showed 34 unrelated files (`App.jsx`, `LLMap/index.jsx`, `theme.js`, `i18n.js`, config files, etc.) modified in the working tree, none of which this plan's `files_modified: [app/src/pages/LLDetail.jsx]` frontmatter authorizes touching.
- **Fix:** Ran `git checkout -- <path>` individually against each of the 34 out-of-scope files (never a blanket `git checkout .` or `git clean`) to restore them to their last-committed state, leaving only `app/src/pages/LLDetail.jsx` modified. Re-ran `npm run lint`, `npm run build`, and `npm run format:check` on the reverted tree to confirm the revert did not break anything; `LLDetail.jsx` alone was independently re-verified with `npx prettier --check src/pages/LLDetail.jsx` and passes.
- **Files modified:** none beyond the plan's own scope (34 files reverted, 0 files newly touched)
- **Verification:** `git status --short` after the revert shows only the pre-existing, out-of-scope `.planning/HANDOFF.json` (present before this session started, untouched by this plan) plus the plan's own commits' effect on `app/src/pages/LLDetail.jsx`.
- **Committed in:** not committed (working-tree-only revert; nothing to commit since the 34 files were never staged)

---

**Total deviations:** 2 auto-fixed (1 build-order lint gate resolved via a scoped, self-removing disable comment per task; 1 formatter-tool side-effect reverted before it could pollute the commit history). No architectural changes, no scope creep. All threat-register items for this plan (T-10-10 accept, T-10-11 mitigate, T-10-12 mitigate, T-10-SC mitigate) hold with zero new code beyond what the plan specifies — confirmed by source grep and by `git diff --stat app/package.json app/package-lock.json` printing nothing.

## Issues Encountered

**Pre-existing, repo-wide `npm run format:check` issue, unrelated to this plan** (same condition documented in `10-01-SUMMARY.md`, `10-02-SUMMARY.md`, `10-03-SUMMARY.md`, and this phase's `deferred-items.md`): the Windows checkout has CRLF line endings while Prettier's default `endOfLine: 'lf'` expects LF, so `npm run format:check` reports drift across ~35 tracked files this plan never touched. `LLDetail.jsx` was independently verified with `npx prettier --check src/pages/LLDetail.jsx` and passes cleanly on its own. `npm run lint` and `npm run build` both exit 0.

**No browser automation tool was available in this environment**, so the plan's Task 3 "Behavior (dev server)" acceptance criteria (visual two-column rendering, per-column legends/accent colors matching, single shared scrollbar, both maps loading independently, reload persistence) could not be exercised by clicking through a real browser. Verified instead via: (a) source-grep acceptance criteria for every literal string/attribute/prop the plan specifies (all passed, documented above), (b) `npm run lint` / `npm run build` / `npm run format:check` (for the plan's own file) all passing cleanly, (c) confirming `LLMap` already renders its own `MapLegend` in every branch by reading `LLMap/index.jsx:744,755,807,817` directly rather than assuming it, and (d) full manual code review of the final diff against `10-UI-SPEC.md`'s "Column structure" and "Two-column grid" sections line by line. A human should spot-check the interactive comparison view (two real LL pairs, all three tabs, both languages) before this phase's final bilingual checkpoint (plan `10-06`).

## Known Stubs

None introduced by this plan. `TextBlock`'s placeholder-narrative rendering (striped gradient + "coming soon" italic caption) is a pre-existing component behavior, reused identically to how `LayoutSplit` and `LayoutStacked` already use it elsewhere in this same file — not a new stub.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `/ll/<a>?compare=<b>` now renders a real, functionally complete two-column comparison: shared tabs, shared scroll, per-column accent/header/KPIs/map/legend/chart/text, no `CompareCTA` anywhere in the tree.
- `LayoutSwitcher` still occupies its original DOM slot while comparing (deliberately left as-is per this plan's Task 3 instructions) — plan 05 replaces it with the comparison bar (swap/exit/name-buttons), which is the next piece needed for a complete UX (currently there is no in-page way to exit comparison mode other than manually editing the URL).
- `isComparing`, `ll` (route slug, always left/`llA`), and `partner` (always right/`llB`) are now available as the exact bindings plan 05's `ComparisonBar` needs to read.
- No blockers for plan 10-05 or 10-06.

---
*Phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-*
*Completed: 2026-07-28*

## Self-Check: PASSED

- FOUND: app/src/pages/LLDetail.jsx
- FOUND: .planning/phases/10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-/10-04-SUMMARY.md
- FOUND commit: fce0ec9 (Task 1)
- FOUND commit: a4612e8 (Task 2)
- FOUND commit: d598d30 (Task 3)
- Verified: `cd app && npm run lint` exits 0
- Verified: `cd app && npm run build` exits 0
- Verified: `npx prettier --check src/pages/LLDetail.jsx` (from `app/`) passes
- Verified: `grep -c "<CompareCTA" app/src/pages/LLDetail.jsx` returns 2
- Verified: `grep -c "<LayerTabs" app/src/pages/LLDetail.jsx` returns 3
- Verified: `grep -c "@media\|matchMedia\|minWidth" app/src/pages/LLDetail.jsx` returns 0
- Verified: `git diff --stat app/src/App.jsx app/src/components/LLMap/index.jsx app/src/components/LayerTabs.jsx` prints nothing (working tree matches base commit for these files)
- Verified: `git diff --stat app/package.json app/package-lock.json` prints nothing
