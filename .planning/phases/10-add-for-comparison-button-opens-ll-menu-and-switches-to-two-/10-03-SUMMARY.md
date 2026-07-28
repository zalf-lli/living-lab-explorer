---
phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-
plan: 03
subsystem: ui
tags: [react, react-router, url-state, dropdown, dismiss-pattern, comparison-view]

# Dependency graph
requires:
  - phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-
    plan: 01
    provides: "llDetail.comparePickerTitle/compareCompactAction i18n keys"
  - phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-
    plan: 02
    provides: "lifted useLayerState in LLDetail; compare-aware Header pills"
provides:
  - "?compare=<slug> URL state on LLDetail: parsed, identity-validated against bySlug (T-10-06 mitigation), silently stripped when invalid/self-referential (D-01, D-03, D-05)"
  - "setCompare(nextSlug) writer that pushes a history entry (no replace) so Back undoes comparison"
  - "compareOptions: the other four LLs, memoised and sorted by order, excluding the current slug (D-12)"
  - "useDismissOnOutside(open, onClose) reusable hook (Escape + outside-click dismiss)"
  - "ComparePicker anchored dropdown component (220px, 4 rows, icon+name+brand chip)"
  - "CompareCTA now opens/closes ComparePicker and calls onPick(slug) -> setCompare"
affects: ["10-04", "10-05", "10-06"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "URL state as view mode, extended to a second param: ?compare= follows the exact clone-searchParams-then-set idiom already used by ?layout, but omits `replace: true` on the picker's setCompare because entering comparison is a navigation, not a preference (unlike ?layout)"
    - "Own-property identity check against Object.fromEntries-built lookup objects (bySlug) to close an inherited-property (prototype pollution-adjacent) hole: `partnerCandidate.slug === compareSlug` rather than a bare truthy check"
    - "Reusable dismiss-on-Escape/outside-click hook extracted from StatPanel's inline pattern (StatPanel.jsx:14-29) into a parametrised `useDismissOnOutside(open, onClose)` for reuse across multiple dropdown triggers"

key-files:
  created: []
  modified:
    - app/src/pages/LLDetail.jsx

key-decisions:
  - "isComparing (Boolean(partner)) was deliberately NOT extracted as a standalone top-level binding in this plan, despite the plan's action text listing it as a derived value. Task 3 as scoped by the plan never branches rendering on it (that arrives in plan 04's LayoutCompare), so declaring it would be an eslint no-unused-vars error with zero runtime purpose in this plan. Documented as a deviation below."
  - "ComparePicker's row hover/focus state is local (hoveredSlug), not CSS :hover, per CLAUDE.md's no-CSS-framework/inline-style-only constraint and the project having zero .css files"
  - "Panel positioning uses `calc(100% + 8px)` (the sm spacing token) and default `align='right'`, both deliberate, UI-SPEC-documented deviations from the CONTEXT's literal 6px/left-0 discretion answers, to keep the panel on-screen and 4px-grid-compliant"

patterns-established:
  - "Anchored-dropdown-panel-separate-from-trigger: ComparePicker takes only {options, onPick, align} and renders nothing about the trigger button, so the same panel component can be re-anchored to a different trigger (the comparison bar's name buttons) in plan 05 without duplicating the panel markup"

requirements-completed: []

# Metrics
duration: ~45min
completed: 2026-07-27
---

# Phase 10 Plan 03: Compare Param + Picker Dropdown Summary

**`?compare=<slug>` URL state (parsed, identity-validated, silently stripped) plus a reusable dismiss hook and an anchored `ComparePicker` dropdown wired to the formerly-dead `CompareCTA` button**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-07-27T16:10:00Z (approx, continuing from wave 1 completion)
- **Completed:** 2026-07-27T16:55:00Z (approx)
- **Tasks:** 3
- **Files modified:** 1

## Accomplishments

- `LLDetail` now derives `compareSlug`/`partnerCandidate`/`partner` from `?compare=`, mirroring the existing `?layout` clone-searchParams-then-set idiom, and hardens the lookup with an own-property identity check (`partnerCandidate.slug === compareSlug`) so `bySlug`'s `Object.fromEntries` construction cannot be exploited via `?compare=__proto__`/`constructor`/`toString` (T-10-06, verified by the acceptance-criterion URL case)
- The one legitimate `useEffect` in the file strips an unknown or self-referential `?compare=` value with `replace: true` and zero error copy (D-03), gated in order on `loading`/`bySlug` readiness so a valid partner is never stripped mid-fetch
- `compareOptions` (the four other LLs, memoised, sorted by `order`) and `setCompare` (pushes a real history entry, no `replace`, so Back undoes comparison) are threaded from `LLDetail` through `LayoutSplit`/`LayoutStacked` into every `CompareCTA` instance
- `useDismissOnOutside(open, onClose)` is a reusable generalisation of `StatPanel`'s inline Escape/outside-click dismiss effect — same `keydown`/`mousedown` listener pair with cleanup, now parametrised so it can anchor to any trigger
- `ComparePicker` renders the 220px, 4-row anchored dropdown: `LL_ICONS[slug]` SVG + name + `ll.outlineColor` brand-colour chip per row, heading from `llDetail.comparePickerTitle`, hover/focus driven by local state (no stylesheet, no `:hover`)
- `CompareCTA` now owns `pickerOpen` state, wraps its existing button in a `position: relative` div carrying the dismiss ref, toggles the dropdown via `aria-expanded`/`onClick`, and calls `onPick(slug)` on row selection — which `LLDetail` wires to `setCompare`
- Verified the four URL edge cases at the source-grep level (`?compare=bogus`, `?compare=<self>`, `?compare=__proto__`, `?compare=rheingau&layout=B` leaves both params intact) and confirmed via Vite dev-server module transform that the file compiles with no runtime import/syntax errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Parse, validate and strip the ?compare= search param in LLDetail** - `2514e20` (feat)
2. **Task 2: Add useDismissOnOutside hook and the ComparePicker dropdown** - `4b7cc85` (feat)
3. **Task 3: Wire the CompareCTA button to the picker** - `931976e` (feat)

**Plan metadata:** (this commit, docs)

## Files Created/Modified

- `app/src/pages/LLDetail.jsx` - `?compare=` derivation/validation/strip effect above the `loading` early return; `useDismissOnOutside` and `ComparePicker` new local functions; `CompareCTA` signature and body extended with picker state; `LayoutSplit`/`LayoutStacked` signatures and their `CompareCTA` call sites extended with `compareOptions`/`onPickCompare`; `LLDetail`'s render branch passes both props to whichever layout renders

## Decisions Made

- Followed D-01, D-03, D-05, D-11, D-12, D-13, D-18 exactly as specified in the plan, `10-CONTEXT.md`, `10-UI-SPEC.md` and `10-PATTERNS.md`. Panel chrome, spacing, colours and copy match `10-UI-SPEC.md`'s "Picker dropdown" section verbatim (220px width, `zIndex: 1000`, `calc(100% + 8px)` top offset, `align="right"` default, 8px brand-colour chip, `C.surface`/`C.orange` hover state).
- `isComparing` (`Boolean(partner)`) was not extracted as a standalone binding — see Deviations below.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed the plan-specified `isComparing` binding to prevent a real, immediate `no-unused-vars` lint error**
- **Found during:** Task 1 verification (`npm run lint`)
- **Issue:** The plan's action text for Task 1 instructs adding `const isComparing = Boolean(partner)` as a derived value, and states in the interfaces/tasks sections that `isComparing` is "consumed by tasks 2-3 of this plan and by plans 04-05." In practice, neither Task 2 (the picker/dismiss hook) nor Task 3 (wiring `CompareCTA`) as scoped in this plan ever reads `isComparing` — the two-column render branch that would consume it is plan 04's `LayoutCompare`, not anything in this plan. Declaring the binding therefore produces a genuine `'isComparing' is assigned a value but never used  no-unused-vars` ESLint error (confirmed) with zero code in this plan reading it, contradicting the plan's own "no unused-variable lint error is introduced" acceptance bar.
- **Fix:** Did not extract `isComparing` as a top-level binding in `LLDetail`. `partner` (which IS consumed, by the strip effect) remains exactly as specified. A code comment at the omission site explains the rationale and points to plan 04 for the future re-derivation (`Boolean(partner)`, an 8-character re-derivation, so no functionality is lost or made harder to add later).
- **Files modified:** `app/src/pages/LLDetail.jsx`
- **Verification:** `npm run lint` exits 0 in the plan's final state; the `partner`-consuming strip effect and `partnerCandidate.slug === compareSlug` identity check (the actual security-relevant logic, T-10-06) are unchanged and fully present per the acceptance criteria.
- **Committed in:** `2514e20` (Task 1)

**2. [Rule 1 - Bug] Corrected a self-introduced Prettier violation (trailing comma in a function-call argument list)**
- **Found during:** Task 1, line-by-line Prettier-compliance verification of `compareOptions`'s `useMemo(...)` call
- **Issue:** The multi-line `useMemo(fn, [bySlug, slug],)` I wrote included a trailing comma after the deps array. The project's Prettier config is `trailingComma: 'es5'`, which does not add trailing commas after the last argument of a function call (only in array/object literals), so this violated the project's formatting convention.
- **Fix:** Removed the trailing comma so the call matches `es5` trailing-comma style.
- **Files modified:** `app/src/pages/LLDetail.jsx`
- **Verification:** Line-ending-normalized diff against `prettier --write --config .prettierrc.json` output (run against a scratch copy) shows zero remaining differences for any line this plan added or modified, other than two pre-existing lines (see Issues Encountered).
- **Committed in:** `2514e20` (Task 1)

---

**Total deviations:** 2 auto-fixed (1 unused-variable/plan-authoring inaccuracy, 1 self-introduced formatting bug). No architectural changes, no scope creep. All three of this plan's threat-register mitigations (T-10-06 identity check, T-10-07 icon rendering only ever receiving `LL_ICONS[ll.slug]` from validated metadata objects — never the raw `compareSlug` string, T-10-09 dismiss-listener cleanup) are implemented exactly as specified, verified by source grep and by `npm run lint`/`build` passing.

## Issues Encountered

**Per-task intermediate lint state is expected and self-resolving within this plan, by the plan's own design.** Tasks 1 and 2 each introduce derived values/components (`compareOptions`, `setCompare`, `useDismissOnOutside`, `ComparePicker`) that have no consumer until Task 3 wires `CompareCTA`. Running `npm run lint` in isolation after Task 1's commit or Task 2's commit therefore reports 2-4 `no-unused-vars` errors for bindings that Task 3 goes on to consume — this matches the plan's own text ("consumed by tasks 2-3 of this plan... leave them wired to real consumers by the end of this plan"). Verified: `npm run lint` and `npm run build` both exit 0 in the plan's final state (after Task 3's commit, `931976e`), which is the state that matters for the plan's own `<verification>` section and this SUMMARY's Self-Check.

**Pre-existing, repo-wide `npm run format:check` issue, unrelated to this plan** (same condition documented in 10-01-SUMMARY.md and 10-02-SUMMARY.md): the Windows checkout has CRLF line endings while Prettier's default `endOfLine: 'lf'` expects LF, and two pre-existing lines this plan did not touch (`LLDetail.jsx`'s `LayoutSplit`/`LayoutStacked` layer-tabs-hint header divs, both present before wave 1) exceed the 100-char printWidth. Every line this plan itself added or modified was individually verified against `prettier --write --config .prettierrc.json` output (line-ending-normalized) and found fully compliant. `npm run lint` and `npm run build` both exit 0.

**No browser automation tool was available in this environment**, so the plan's "Manual (dev server)" behavioral verification steps (picker open/select/Escape/outside-click flow visually, bilingual copy switching) could not be executed by clicking through a real browser. Verified instead via: (a) source-grep acceptance criteria for every literal string/attribute the plan specifies, (b) `npm run lint`/`npm run build` passing cleanly, (c) confirming via `curl` that the Vite dev server serves and transforms `LLDetail.jsx` with no runtime import/syntax errors, and (d) `useDismissOnOutside`'s listener-pair/cleanup shape being a structural (not just textual) match to `StatPanel.jsx`'s already-shipped, already-verified dismiss pattern. A human should still spot-check the interactive picker flow (open/select/Escape/outside-click, both layouts, both languages) before this phase's final bilingual checkpoint (plan `10-06`).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `LLDetail.jsx` now exposes `partner`, `compareOptions`, `setCompare`, `useDismissOnOutside` and `ComparePicker` as building blocks plan 04 (`LayoutCompare`, the two-column branch) and plan 05 (`ComparisonBar`, which reopens the same `ComparePicker` from its name buttons) can consume directly — `ComparePicker` was deliberately built with no dependency on `CompareCTA`'s trigger markup so it re-anchors cleanly.
- Plan 04 should re-derive `isComparing = Boolean(partner)` at its own branch point (see Deviations) rather than assume it already exists in `LLDetail`.
- Selecting a partner is fully functional at the URL level: `?compare=<slug>` is written, survives reload, and Back undoes it. The page still renders the normal single-LL layout after selection — this is the plan's documented intended intermediate state, resolved by plan 04.
- No blockers for plans 10-04/10-05/10-06.

---
*Phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-*
*Completed: 2026-07-27*

## Self-Check: PASSED

- FOUND: app/src/pages/LLDetail.jsx
- FOUND: .planning/phases/10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-/10-03-SUMMARY.md
- FOUND commit: 2514e20 (Task 1)
- FOUND commit: 4b7cc85 (Task 2)
- FOUND commit: 931976e (Task 3)
- FOUND commit: 520b8b3 (SUMMARY.md metadata commit)
- Verified: `cd app && npm run lint` exits 0
- Verified: `cd app && npm run build` exits 0
- Verified: `git diff --stat -- app/src/App.jsx app/package.json app/package-lock.json` prints nothing
- Verified: `grep -c "removeEventListener" app/src/pages/LLDetail.jsx` returns 2
