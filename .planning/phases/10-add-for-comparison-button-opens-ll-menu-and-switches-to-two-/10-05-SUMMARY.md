---
phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-
plan: 05
subsystem: ui
tags: [react, comparison-view, navigation, i18n]

# Dependency graph
requires:
  - phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-
    plan: 03
    provides: "ComparePicker, useDismissOnOutside, compareOptions/setCompare, and the compareSwap/compareExit/compareChangePartnerAria i18n keys"
  - phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-
    plan: 04
    provides: "isComparing/ll/partner as top-level LLDetail bindings, and the three-way render branch LayoutCompare needed to sit inside"
provides:
  - "ComparisonBar({ llA, llB, options, onPick, onSwap, onExit }) — the comparison mode's control bar: hint label, two identical name buttons sharing one ComparePicker, a swap button, an exit button"
  - "handleSwap/handleExit navigation handlers in LLDetail, rewriting the route and query string via cloned URLSearchParams"
  - "LayoutSwitcher's DOM slot now branches: ComparisonBar while isComparing, LayoutSwitcher otherwise — full entry/re-target/swap/exit loop through the UI with no hand-edited URLs"
affects: ["10-06"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Container-chrome reuse without semantic reuse: ComparisonBar copies LayoutSwitcher's outer div shape (background/borderBottom/flex/gap) but deliberately drops role=group/aria-pressed since it is a row of distinct actions, not a toggle group — plain buttons with individual aria-labels instead"
    - "Both name buttons in ComparisonBar are functionally identical (same onClick, same aria-label) because there is only ever one thing to re-target (the partner) regardless of which name is clicked — the route slug is always the left column and ?compare= holds exactly one slug"
    - "Swap/exit built by cloning searchParams into a new URLSearchParams and mutating that clone (set/delete), never string-concatenating the query — percent-encoding and untrusted-value safety come for free"

key-files:
  created: []
  modified:
    - app/src/pages/LLDetail.jsx

key-decisions:
  - "handleSwap/handleExit are plain functions (not hooks), defined after the two early returns, since they only need ll/partner which are guaranteed non-null past that point — matches the plan's explicit instruction"
  - "handleExit calls setSearchParams(next) without { replace: true } so Back re-enters comparison symmetrically with how setCompare (entry) already pushes a history entry, per the plan"
  - "LayoutSwitcher itself is untouched; only its call site in LLDetail's render became a ternary — the single-LL page's A/B toggle behavior is provably unchanged (byte-identical function body)"

requirements-completed: []

# Metrics
duration: ~35min
completed: 2026-07-28
---

# Phase 10 Plan 05: Comparison Bar (Change Partner, Swap, Exit) Summary

**`ComparisonBar` gives comparison mode its own control row — change partner, swap sides, or exit — replacing the A/B `LayoutSwitcher` in the exact same DOM slot only while comparing**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-07-28T07:05:00Z (approx)
- **Completed:** 2026-07-28T07:40:00Z (approx)
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- `ComparisonBar({ llA, llB, options, onPick, onSwap, onExit })` renders, left to right: a 12px/400 hint label (`llDetail.comparePrefix`), a relatively-positioned name-button group (color chip + `llA.name`, an `aria-hidden` `↔` separator, color chip + `llB.name`) that shares one local `pickerOpen` state and one `useDismissOnOutside` ref, a swap button styled with the orange accent border, and an exit button styled with the structural teal — matching UI-SPEC's copywriting and spacing-scale contract (`padding: '8px 24px'`) exactly
- Both name buttons carry the identical `aria-label={t('llDetail.compareChangePartnerAria')}` and the identical `onClick`, opening the same `ComparePicker` regardless of which one is clicked — the locked reading of D-14 ("clicking either LL name reopens the same picker")
- `LLDetail` now defines `handleSwap` (clones `searchParams`, sets `compare` to `ll.slug`, navigates to `/ll/${partner.slug}` with the cloned search string) and `handleExit` (clones `searchParams`, deletes `compare`, calls `setSearchParams` without `replace`) below its early returns, and imports `useNavigate` alongside the existing `useParams`/`useSearchParams`
- The render's `LayoutSwitcher` call site became a ternary: `isComparing ? <ComparisonBar .../> : <LayoutSwitcher .../>`, with `LayoutSwitcher`'s own function body left byte-identical — the single-LL page's layout toggle is unaffected
- Confirmed by source grep: `<LayoutSwitcher` and `<ComparisonBar` each appear exactly once; `compareChangePartnerAria` appears exactly twice (both name buttons); no `role="group"`/`aria-pressed` inside `ComparisonBar`; zero `dangerouslySetInnerHTML` inside `ComparisonBar` (T-10-15); `git diff --stat` on `package.json`/`package-lock.json` prints nothing (T-10-SC)

## Task Commits

Each task was committed atomically:

1. **Task 1: Build the ComparisonBar component** - `d2f9420` (feat)
2. **Task 2: Swap the bar into LayoutSwitcher's slot and wire swap/exit navigation** - `8efb152` (feat)
3. **Prettier auto-fix on Task 1's picker wrapper div** - `071aa47` (style, Rule 3 auto-fix, see Deviations)

**Plan metadata:** (this commit, docs)

## Files Created/Modified

- `app/src/pages/LLDetail.jsx` - added `function ComparisonBar({ llA, llB, options, onPick, onSwap, onExit })` immediately after `LayoutSwitcher`; added `useNavigate` to the `react-router-dom` import and the `navigate` binding in `LLDetail`; added `handleSwap`/`handleExit` handlers below the early returns; replaced the unconditional `<LayoutSwitcher layout={layout} onChange={setLayout} />` render with an `isComparing` ternary rendering `ComparisonBar` or `LayoutSwitcher`

## Decisions Made

- Followed D-02, D-06, D-14, D-15, D-18 exactly as specified in `10-CONTEXT.md`/`10-UI-SPEC.md`/`10-PATTERNS.md`: the bar occupies `LayoutSwitcher`'s exact DOM slot, columns carry no comparison chrome of their own (untouched from plan 04), swap rewrites the route so the URL always reads left-to-right, exit strips only `?compare=`, and both LL chips reuse `outlineColor` (the same field `LLMap` uses for its boundary line and the picker rows already use)
- Every UI-SPEC literal (padding `8px 24px`, font sizes/weights/line-heights, `C.orange`/`C.teal`/`C.mutedLight` colors) was copied verbatim rather than approximated

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Prettier line-width wrap on the picker-anchor `div`**
- **Found during:** Post-commit full verification pass (`npm run format:check` scoped to `LLDetail.jsx` via `npx prettier --check`)
- **Issue:** The picker wrapper `<div ref={pickerRef} style={{ position: 'relative', display: 'flex', alignItems: 'center', gap: 8 }}>` written in Task 1 exceeded Prettier's configured line width as a single line, so `npx prettier --check src/pages/LLDetail.jsx` failed even though `npm run lint`/`npm run build` both passed.
- **Fix:** Ran `npx prettier --write src/pages/LLDetail.jsx` (scoped to this one file, not the whole `app/` tree, to avoid the repo-wide CRLF reformat trap plan 10-04 already documented and reverted). The write reflowed only that one attribute list onto multiple lines; no logic changed.
- **Files modified:** `app/src/pages/LLDetail.jsx`
- **Verification:** `npx prettier --check src/pages/LLDetail.jsx` now reports "All matched files use Prettier code style!"; `npm run lint` and `npm run build` re-run clean afterward.
- **Committed in:** `071aa47`

---

**Total deviations:** 1 auto-fixed (a Prettier line-width wrap on new code, isolated to this plan's own file). No architectural changes, no scope creep. All threat-register items for this plan (T-10-13 mitigate, T-10-14 mitigate, T-10-15 mitigate, T-10-SC mitigate) hold — confirmed by source grep and by `git diff --stat app/package.json app/package-lock.json` printing nothing.

## Issues Encountered

**Pre-existing, repo-wide `npm run format:check` issue, unrelated to this plan** (same condition documented in `10-01`, `10-02`, `10-03`, `10-04` SUMMARYs and this phase's `deferred-items.md`): the Windows checkout has CRLF line endings while Prettier's default `endOfLine: 'lf'` expects LF, so the repo-wide `npm run format:check` reports drift across ~35 tracked files this plan never touched (confirmed identical on the unmodified base commit via a scoped read-only comparison, no destructive git operations used to verify it). `LLDetail.jsx` was independently verified with `npx prettier --check src/pages/LLDetail.jsx` and now passes cleanly on its own. `npm run lint` and `npm run build` both exit 0.

**Worktree base correction at startup**: this agent's worktree branch (`worktree-agent-a03c5bd321593f5eb`) was found pointing at an unrelated, diverged commit (`9ec9ba1`, containing an unrelated merged PR) rather than the expected wave-4 base (`8e4be06`). Per the mandatory `<worktree_branch_check>` protocol, `git reset --hard 8e4be065d9c8f90f7de3334f3e630af1f0779797` was run before any task work began, correcting the base. No commits were lost since none of this agent's work existed yet at that point.

**No browser automation tool was available in this environment**, so the plan's Task 2 "Behavior (dev server)" acceptance criteria (visual bar rendering, swap/exit URL transitions, picker dismiss behavior, bilingual copy) could not be exercised by clicking through a real browser. Verified instead via: (a) source-grep acceptance criteria for every literal string/attribute/prop the plan specifies (all passed, documented above), (b) `npm run lint` / `npm run build` / scoped `npx prettier --check` all passing cleanly, (c) confirming `handleSwap`'s target construction (`/ll/${partner.slug}` + `compare` set to `ll.slug`) and `handleExit`'s `next.delete('compare')` without `replace` by direct code read, and (d) full manual review of the final diff against `10-UI-SPEC.md`'s "Comparison bar" and Copywriting Contract sections line by line, plus confirming both EN and DE i18n keys already exist in `app/src/i18n.js` (added by plan 01). A human should spot-check the interactive comparison bar (change partner, swap, exit, both languages, both starting `?layout` values) before this phase's final bilingual checkpoint (plan `10-06`).

## Known Stubs

None introduced by this plan.

## Threat Flags

None — all four threat-register items for this plan (T-10-13, T-10-14, T-10-15, T-10-SC) were mitigated exactly as specified, with no new surface beyond what `10-CONTEXT.md`'s threat model already anticipated.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The full comparison-mode UI loop is now complete: enter via `CompareCTA` (plan 03), view two columns (plan 04), change partner/swap/exit via the comparison bar (this plan). No hand-edited URLs are needed anywhere in the flow.
- `LayoutSwitcher` is fully restored to view the instant `isComparing` becomes false (exit), with `?layout` surviving entry, swap, and exit untouched.
- Plan `10-06` can now run its full bilingual human-verification checkpoint and D-01..D-29 evidence table across the complete feature.
- No blockers for plan 10-06.

---
*Phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-*
*Completed: 2026-07-28*

## Self-Check: PASSED

- FOUND: app/src/pages/LLDetail.jsx
- FOUND: .planning/phases/10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-/10-05-SUMMARY.md
- FOUND commit: d2f9420 (Task 1)
- FOUND commit: 8efb152 (Task 2)
- FOUND commit: 071aa47 (Rule 3 auto-fix)
- Verified: `cd app && npm run lint` exits 0
- Verified: `cd app && npm run build` exits 0
- Verified: `npx prettier --check src/pages/LLDetail.jsx` (from `app/`) passes
- Verified: `grep -c "<LayoutSwitcher" app/src/pages/LLDetail.jsx` returns 1
- Verified: `grep -c "<ComparisonBar" app/src/pages/LLDetail.jsx` returns 1
- Verified: `grep -c "compareChangePartnerAria" app/src/pages/LLDetail.jsx` returns 2 (occurrences inside `ComparisonBar`, confirmed by scoped grep)
- Verified: zero `dangerouslySetInnerHTML` inside `ComparisonBar`'s function body
- Verified: `git diff --stat app/package.json app/package-lock.json` prints nothing
