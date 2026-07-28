---
phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-
verified: 2026-07-28T10:15:00Z
status: passed
score: 29/29 decisions verified (D-01..D-29)
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 28/29
  gaps_closed:
    - "?layout survives comparison end-to-end, including via the header-pill route (D-02, in combination with D-04)"
  gaps_remaining: []
  regressions: []
deferred: []
human_verification: []
---

# Phase 10: Wire up "Add for comparison" button to a real two-column LL comparison layout Verification Report

**Phase Goal:** Turn the placeholder "Add for comparison" button into a working side-by-side
comparison of two Living Labs: clicking it opens a menu of LL names, and selecting one switches
`/ll/:slug` into a two-column `?compare=` view where each column stacks that LL's KPIs, map,
chart and text under one shared layer-tab row.

**Verified:** 2026-07-28T10:15:00Z
**Status:** passed
**Re-verification:** Yes — after gap closure (commit `0270de0`, "fix(10): close D-02 gap and three
review warnings")

**Traceability note:** ROADMAP Phase 10 declares `Requirements: TBD` — no REQ-IDs exist for this
phase. Per the phase's own design, the 29 locked decisions D-01..D-29 in `10-CONTEXT.md` are the
verifiable contract. This report verifies against those decisions. Missing REQ-ID traceability is
not reported as a gap.

## What changed since the previous pass

The previous pass (2026-07-28T07:29:32Z) returned `gaps_found` at 28/29, with one blocking gap:
D-02 broken specifically on the header-pill navigation path while comparing (`Header.jsx:75`
rebuilt the target URL from a template string, dropping `?layout`). Commit `0270de0` closes that
gap and additionally folds in three advisory-review Warning findings (WR-03, WR-04, WR-05) the
project owner chose to accept and fix in the same pass. This report re-verifies the fix against
the live source (not the commit message, not the SUMMARY) and re-checks all other 28 decisions for
regressions.

## Goal Achievement

### Core Observable Truths (phase goal, ROADMAP-level)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Clicking "Add for comparison" opens an anchored dropdown menu of the other 4 LL names | VERIFIED | Unchanged since prior pass; `CompareCTA`/`ComparePicker` (`LLDetail.jsx`) — no regression per file-diff against 4165d91 for the unaffected files |
| 2 | Selecting an LL switches `/ll/:slug` into a two-column `?compare=<slug>` view, no new route | VERIFIED | Unchanged; `App.jsx` untouched by the fix commit (confirmed empty diff) |
| 3 | Each column stacks that LL's KPIs, map, chart and text under one shared layer-tab row | VERIFIED | Unchanged; structural counts re-run and match prior pass exactly (`LayerTabs`=3, `CompareCTA`=2, `Suspense`=3, `height={300}`=2) |
| 4 | An unknown/self-referential `?compare=` is silently ignored, no error UI | VERIFIED | Unchanged mechanism, plus strengthened by the WR-03 fix (see below) — an empty `?compare=` is now also stripped |
| 5 | `?layout` survives entering/leaving comparison via the comparison bar's own controls | VERIFIED | Unchanged; `handleSwap`/`handleExit` untouched by the fix commit |
| 6 | `?layout` survives comparison end-to-end via **every** entry/exit path, including changing the primary LL from the site header while comparing | **VERIFIED (was FAILED)** | Gap closed — see D-02 re-verification below |
| 7 | `npm run lint` and `npm run build` both exit 0 on the current tree | VERIFIED | Ran independently, this pass: `npm run lint` exit 0, no output; `npm run build` exit 0, 120 modules, no errors |
| 8 | No npm dependency was added or changed | VERIFIED | `git diff --stat 5bc5516 -- app/package.json app/package-lock.json` — empty, ran independently this pass |
| 9 | `npm run format:check` — pre-existing, repo-wide, not a phase-10 regression | VERIFIED (with caveat) | Ran independently this pass: exit 1, same 16 files flagged as the prior pass, byte-identical file list; not a regression from the fix commit |

**Score:** 9/9 core truths verified.

### D-02 Re-verification (the closed gap)

**Prior finding:** `Header.jsx:75` (pre-fix) built the compare-aware pill navigation target as
`` `/ll/${ll.slug}?compare=${nextPartner}` ``, discarding every other search param, including
`?layout`.

**Fix, read directly from the current tree (`app/src/components/Header.jsx:70-84`):**

```jsx
onClick={() => {
  if (compareSlug && activeSlug) {
    // D-04: clicked LL becomes primary and keeps comparing; if it was
    // already the partner, the two swap sides.
    // D-02: clone the live params rather than rebuilding the query string,
    // so ?layout (and anything added later) rides along untouched and
    // exiting comparison restores the layout the user actually had.
    const next = new URLSearchParams(searchParams)
    next.set('compare', ll.slug === compareSlug ? activeSlug : compareSlug)
    navigate({ pathname: `/ll/${ll.slug}`, search: `?${next.toString()}` })
  } else {
    // Unchanged from before this phase: a plain LL switch resets the query
    // string. Not in D-02's scope, which governs comparison only.
    navigate(`/ll/${ll.slug}`)
  }
}}
```

**Verification performed (not trusting the SUMMARY or commit message):**

1. **Comparing branch now clones `searchParams`.** `useSearchParams()` is imported and destructured
   (`Header.jsx:1, 13`); `next = new URLSearchParams(searchParams)` copies every existing param,
   then only `compare` is mutated. `?layout` (and any future param) rides along untouched. This
   matches the pattern `LLDetail.jsx`'s `handleSwap`/`handleExit` already used correctly — the
   inconsistency that caused the gap is gone.
2. **Swap-direction logic is correct.** `ll.slug === compareSlug ? activeSlug : compareSlug` — if
   the clicked LL is already the partner, the compare value becomes the former primary (swap
   sides, D-04); otherwise the clicked LL becomes primary and the existing partner is kept. Matches
   D-04's contract exactly, unchanged from the pre-fix version (this part was never broken).
3. **Repro from the original gap report, re-traced against the fixed code:** set layout B → enter
   comparison → click a header LL pill → the new URL is
   `/ll/<clicked>?compare=<partner>&layout=B` (params cloned, order from `URLSearchParams`
   iteration, `layout` present) → click Exit → `LLDetail`'s `handleExit` deletes only `compare`,
   `layout=B` remains → `layoutParam` reads `B`. The failure mode described in the original gap
   (falling back to default `A`) no longer reproduces.
4. **Non-comparing branch is confirmed genuinely unchanged, not just claimed unchanged.** Ran
   `git diff 5bc5516 -- app/src/components/Header.jsx` (the pre-phase-10 commit) against the
   current tree: the `else` branch is `navigate(\`/ll/${ll.slug}\`)`, byte-identical to the
   pre-phase-10 line. This is deliberately outside D-02's scope (D-02 governs comparison state
   only) and was not touched by either the original phase-10 work or the fix commit. Confirmed by
   direct diff, not by trusting the inline comment.

**D-02 status: VERIFIED.** Holds for both the comparison bar's own controls (unchanged, previously
verified) and the header-pill path (fixed and re-verified here).

### Fixed advisory-review warnings (folded into this closure pass)

These were Warning-severity findings in `10-REVIEW.md`, not part of the original 29-decision gap,
but the user chose to fix them in the same commit. Verified directly against the live source, not
assumed from the description:

**WR-03 — `?compare=` with an empty value not stripped.** `LLDetail.jsx:68-78`. The strip effect's
guard changed from `if (!compareSlug) return` to `if (compareSlug === null) return`, with an
inline comment explaining the distinction. `searchParams.get('compare')` returns `''` for a URL
ending in bare `?compare=` and `null` when the param is absent entirely; JS falsiness treats both
the same, but only `null` should skip the strip. Confirmed the new guard uses strict `=== null`,
not falsiness — the fix is correct and matches `10-REVIEW.md`'s suggested patch.

**WR-04 — picker `zIndex` tied Leaflet's control corners.** `LLDetail.jsx:~809` (inside
`ComparePicker`). Changed from `zIndex: 1000` to `zIndex: 1200`, with a comment explaining
Leaflet's `.leaflet-top`/`.leaflet-bottom` sit at `z-index: 1000` with no intervening stacking
context, so the map (later in DOM order) would win a tie. 1200 unambiguously clears it. Confirmed
by direct read.

**WR-05 — dropdown a11y (no popup semantics; Escape drops focus to `<body>`).**
Three sub-fixes, all confirmed by direct read of the current `LLDetail.jsx`:

- **Popup semantics:** `ComparePicker`'s root `div` now carries `id`, `role="menu"`,
  `aria-labelledby={titleId}`; the heading `div` carries the matching `id`; each row `button`
  carries `role="menuitem"`. All three trigger buttons (`ComparisonBar`'s two name buttons,
  `CompareCTA`'s button) now carry `aria-haspopup="menu"` and `aria-controls={pickerOpen ? pickerId : undefined}`,
  with `pickerId` generated via `useId()` per component instance so the two `ComparisonBar` name
  buttons that share one `pickerOpen` state each get a stable, unique id passed to the shared
  panel.
- **Focus restoration on Escape:** `useDismissOnOutside` (`LLDetail.jsx:740-778`) now holds a
  `triggerRef`. On the `onKey` Escape handler: `onClose()` is called, then focus is restored to
  `triggerRef.current` if it still exists in the document. Confirmed by direct read.
- **Guard-logic correctness (specifically checked per the task's instruction):** The capture
  happens inside `useEffect(() => { if (!open) { triggerRef.current = null; return undefined } if (triggerRef.current === null) { triggerRef.current = document.activeElement } ... }, [open, onClose])`.
  Traced the re-render behavior: both call sites pass an inline arrow as `onClose`
  (`() => setPickerOpen(false)`), which gets a new identity every parent render, so this effect's
  cleanup+re-run fires on *every* render while the panel is open, not just the open/close
  transition (this is the same instability WR-07 in `10-REVIEW.md` describes and was not fixed
  here — see Anti-Patterns below). However, the capture itself is correctly guarded: on each
  re-run, the `if (triggerRef.current === null)` check only lets `document.activeElement` be
  captured when `triggerRef.current` is currently `null`, which is only true immediately after the
  `open: false → true` transition (the `!open` branch unconditionally resets it to `null`). On
  every subsequent re-run while `open` stays `true`, `triggerRef.current` is already non-null, so
  the guard is false and the capture is skipped — a user tabbing onto a row while the panel stays
  open does **not** overwrite the remembered trigger. This is a correct implementation of "capture
  once, on the closed→open edge only," verified by tracing the guard condition against React's
  effect re-run semantics, not by trusting the inline comment.

**Note (non-blocking, informational):** WR-05's fix does not also fix WR-07 (the unrelated
listener-resubscription issue on every render) — that finding remains open in `10-REVIEW.md` and
was not claimed as fixed by the task description; not reporting it as a new gap since it predates
this closure pass and is Warning-severity, not a locked-decision violation.

### D-01..D-29 Decision Verification (full contract, re-checked for regressions)

Full re-derivation was not repeated for the 27 decisions untouched by the fix commit — confirmed
via `git diff` that their supporting files (`StatPanel.jsx`, `BarChart.jsx`, `i18n.js`, `App.jsx`,
`LayerTabs.jsx`, `LLMap/index.jsx`) are byte-identical between the prior verification's commit
(`4165d91`) and the current tree (`0270de0`), and the structural assertion counts the user
independently re-ran (`LayerTabs`=3, `CompareCTA`=2, `Suspense`=3, `height={300}`=2,
`removeEventListener`=2, `compare-get`=1, `compare-delete`=2, `MapLegend`=0, `@media`/`matchMedia`=0)
were independently re-run here and match exactly. D-02 and D-04 were re-derived in full (above,
and D-04 confirmed unchanged in swap-direction logic). D-09, D-11, D-14 touch the two files the fix
commit did modify (`Header.jsx`, `LLDetail.jsx`) beyond the D-02 fix itself (the WR-05 a11y changes
live inside `useDismissOnOutside`/`ComparisonBar`/`CompareCTA`/`ComparePicker`), so those were
re-checked directly rather than assumed unchanged.

| Decision | Status | Independent evidence |
|---|---|---|
| D-01 | VERIFIED | Unchanged; `App.jsx` diff clean vs. `4165d91` |
| D-02 | **VERIFIED** (was PARTIAL) | See full re-verification above |
| D-03 | VERIFIED | Strengthened by WR-03 fix; strip effect still deletes `compare` with `replace: true` for any invalid value, now including the empty-string case |
| D-04 | VERIFIED | Swap-direction ternary in `Header.jsx:78` unchanged in logic, only the URL-construction mechanism changed (see D-02) |
| D-05 | VERIFIED | No `.split(` on `compare` anywhere in `LLDetail.jsx` (confirmed by grep, this pass) |
| D-06 | VERIFIED | `handleSwap` unchanged; no `?side=` param anywhere |
| D-07 | VERIFIED | `LayerTabs` count still exactly 3 in `LLDetail.jsx` (single/split/stacked call sites + compare), no duplicate added by the fix |
| D-08 | VERIFIED | `grep -rc "get('layer')" app/src` returns 0, re-run this pass |
| D-09 | VERIFIED | `useLayerState()` call site and remount keys (`key="A"`/`"B"`/`"C"`) untouched by the fix diff |
| D-10 | VERIFIED (dead-path, unchanged) | `StatPanel.jsx`/`BarChart.jsx` byte-identical to prior pass (confirmed empty diff) |
| D-11 | VERIFIED, strengthened | `useDismissOnOutside` still mirrors Escape/outside-click dismiss with no backdrop/focus-trap/scroll-lock; now additionally restores focus on Escape (WR-05), which is an accessibility improvement, not a contract change |
| D-12 | VERIFIED | `compareOptions` filtering unchanged (`LLDetail.jsx` diff shows no change to this logic) |
| D-13 | VERIFIED | Brand-colour chip on picker rows unchanged |
| D-14 | VERIFIED | `ComparisonBar` still owns hint label, both name buttons, swap, exit in one row; only additions are `aria-haspopup`/`aria-controls`/`pickerId` — no structural change |
| D-15 | VERIFIED | `CompareCTA` still gated to `LayoutSplit`/`LayoutStacked` only, unchanged |
| D-16 | VERIFIED | `ComparisonColumn` internal order unchanged (fix commit did not touch this function) |
| D-17 | VERIFIED | Accent bar sourcing unchanged |
| D-18 | VERIFIED | Colour-chip pattern unchanged |
| D-19 | VERIFIED | Column header chrome unchanged |
| D-20 | VERIFIED | Shared scroll container unchanged |
| D-21 | VERIFIED | `grep -rn "@media\|matchMedia" app/src` returns 0 matches, re-run this pass |
| D-22 | VERIFIED | `LLMap/index.jsx` still byte-identical to pre-phase state (confirmed empty diff, this pass) |
| D-23 | VERIFIED | Both columns still mount eagerly in parallel, unchanged |
| D-24 | VERIFIED | Independent `Suspense` count still 3, re-run this pass |
| D-25 | VERIFIED | `MapLegend` count in `LLDetail.jsx` still 0, re-run this pass |
| D-26 | VERIFIED | `LLMap/index.jsx` unchanged; no page-level error banner introduced |
| D-27 | VERIFIED | `height={300}` count still 2, re-run this pass |
| D-28 | VERIFIED | `BarChart.jsx` byte-identical, `compact` prop usage unchanged |
| D-29 | VERIFIED | `StatPanel.jsx` byte-identical; `maxColumns={2}` call site unchanged |

**Score:** 29/29 decisions fully verified. No regressions detected in any of the 27 decisions not
directly touched by the fix commit — confirmed via file-level diffs against the prior verification
pass's commit, not assumed.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `app/src/pages/LLDetail.jsx` | `?compare=` parsing, `ComparisonBar`, `ComparePicker`, `LayoutCompare`, `ComparisonColumn`, lifted `useLayerState` | VERIFIED | Present, substantive, wired; WR-03/WR-05 fixes confirmed by direct read this pass |
| `app/src/components/Header.jsx` | `?compare=`-aware pill navigation, preserving all other params | VERIFIED (was: exists/wired but with a correctness defect) | `Header.jsx:70-84` — D-02 gap closed, confirmed by direct read |
| `app/src/components/StatPanel.jsx` | `maxColumns` + `showEmptyState` props | VERIFIED | Unchanged, byte-identical to prior pass |
| `app/src/components/BarChart.jsx` | `minHeightWhenEmpty` prop | VERIFIED | Unchanged, byte-identical to prior pass |
| `app/src/i18n.js` | EN+DE comparison-bar/picker/empty-state keys | VERIFIED | Unchanged, byte-identical to prior pass (the fix commit needed no new i18n keys) |
| `.planning/phases/10.../10-06-SUMMARY.md` | Decision-evidence table + human sign-off | VERIFIED | Present from prior pass; unaffected by fix commit |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `CompareCTA` button | `ComparePicker` | `pickerOpen` state + `useDismissOnOutside` ref | WIRED | Unchanged |
| `ComparePicker` row `onClick` | `setCompare` / `onPickCompare` | `onPick(ll.slug)` prop chain | WIRED | Unchanged |
| `LLDetail` compare state | URL search params | `useSearchParams` + `setSearchParams` | WIRED | Strengthened by WR-03 (empty-value case now also stripped) |
| `ComparisonBar` name buttons | `ComparePicker` | shared `pickerOpen` + `useDismissOnOutside` | WIRED | Unchanged, plus `aria-controls` now points to the correct shared panel id |
| `ComparisonBar` swap | `react-router navigate` | `handleSwap` -> `navigate({pathname, search})` | WIRED | Unchanged |
| `ComparisonBar` exit | `setSearchParams` | `handleExit` deletes `compare`, keeps `layout` | WIRED | Unchanged |
| `LayoutCompare` render branch | `ComparisonColumn` x2 | `isComparing` ternary, `llA`/`llB` props | WIRED | Unchanged |
| `LayoutCompare` | shared `LayerTabs` | single `active`/`onChange` pair above the grid | WIRED | Unchanged |
| Header LL pill | `?compare=`-aware navigation | `navigate({pathname, search})`, cloned `searchParams` | **WIRED (was PARTIALLY WIRED)** | Fixed — now preserves `layout` and any other param, confirmed by direct read |

### Data-Flow Trace (Level 4)

Not applicable in the traditional API/DB sense — unchanged from prior pass. `bySlug` (from
`useLLMetadata`) remains the single source for both primary and partner LL lookups; no separate
fetch introduced by the fix commit.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Lint passes | `cd app && npm run lint` | exit 0, no output | PASS |
| Build passes | `cd app && npm run build` | exit 0, 120 modules, no errors | PASS |
| No new/changed dependency | `git diff --stat 5bc5516 -- app/package.json app/package-lock.json` | empty | PASS |
| `StatPanel.jsx`/`BarChart.jsx`/`i18n.js`/`App.jsx`/`LayerTabs.jsx`/`LLMap/index.jsx` unchanged since prior pass | `git diff --stat 4165d91 0270de0 -- <files>` | empty | PASS |
| `?compare=` handling strip-guard uses `=== null` not falsiness | grep + direct read of `LLDetail.jsx:68-78` | confirmed | PASS |
| Header pill compare-aware branch clones `searchParams` | direct read of `Header.jsx:70-84` | confirmed | PASS |
| Header pill non-comparing branch unchanged from pre-phase-10 | `git diff 5bc5516 -- app/src/components/Header.jsx` (else branch) | byte-identical | PASS |
| Structural counts unchanged (`LayerTabs`=3, `CompareCTA`=2, `Suspense`=3, `height={300}`=2, `removeEventListener`=2, `compare-get`=1, `compare-delete`=2, `MapLegend`=0, `@media`/`matchMedia`=0) | grep, re-run this pass | all match | PASS |
| `format:check` scope unchanged (pre-existing, not a regression) | `cd app && npm run format:check` | exit 1, same 16 files as prior pass | PASS (as pre-existing) |

Not applicable: no server/API to curl, no CLI entry point beyond the Vite dev server.

### Probe Execution

No `scripts/*/tests/probe-*.sh` convention exists in this repo, and neither the plans, SUMMARYs,
nor this closure task reference probe-based verification. Step 7c: SKIPPED (no runnable probes
declared or discoverable for this phase).

### Requirements Coverage

ROADMAP Phase 10 declares `Requirements: TBD`; traceability runs through D-01..D-29 instead, per
the phase's own design. Not reported as a gap.

### Anti-Patterns Found

No debt markers (`TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER`) in `Header.jsx` or `LLDetail.jsx`
— confirmed by direct grep, zero matches, this pass.

The fix commit closes WR-01 (now D-02, resolved), WR-03, WR-04 and the focus-restoration portion of
WR-05. `10-REVIEW.md`'s remaining findings (WR-02, WR-06, WR-07, and IN-01 through IN-08) were not
in scope for this closure task and remain open as non-blocking advisory items — none of them
contradict a locked D-01..D-29 decision, so none change this report's status. Specifically WR-07
(the `useDismissOnOutside` listener re-subscription on every render) is adjacent to the WR-05 fix
but was not itself addressed — verified by reading the effect's dependency array
(`[open, onClose]`, still present in the current code) and confirming the resubscription behavior
described in `10-REVIEW.md` still applies. Not a new finding; not reported as a gap since it
predates this closure pass and was not claimed as fixed.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `app/src/pages/LLDetail.jsx` | 775 | `useDismissOnOutside`'s effect still depends on `[open, onClose]` where callers pass a fresh inline arrow (WR-07, unaddressed by this fix) | ⚠️ Warning (pre-existing, not new) | Listeners re-subscribe on every render while the panel is open; does not affect correctness of the WR-05 focus-capture guard, which is independently gated (verified above) |

### Human Verification Required

None. The prior pass's outstanding item (the compound header-pill-then-exit interaction that the
23-step human script did not cover) is now closed by direct code verification of the fix — no new
UI behavior was introduced that requires visual/interactive human confirmation beyond what the
prior human sign-off already covered (picker open/close, swap, exit, all exercised in the original
23-step script). The aria/focus changes (WR-05) are verifiable by code trace (confirmed above); a
screen-reader spot-check would be good practice but is not required to consider the phase's locked
decisions satisfied, since D-11's contract ("no backdrop, focus trap, or scroll lock") does not
mandate the popup semantics WR-05 added — those are an accepted improvement beyond the phase's own
contract.

### Gaps Summary

None. The one gap from the prior pass — D-02 broken specifically on the header-pill navigation
path while comparing — is closed and re-verified directly against the live source in commit
`0270de0`. All 29 locked decisions (D-01..D-29) are now verified. The three additional advisory
warnings folded into the same commit (WR-03, WR-04, and the focus-restoration/popup-semantics
portion of WR-05) were also independently re-verified as correctly fixed. `npm run lint` and
`npm run build` both exit 0. No regressions were found in any of the 27 decisions not directly
touched by the fix — confirmed via file-level diffs, not assumed. The phase's headline deliverable
— a working picker-driven two-column comparison view with shared layer tabs, per-column
KPIs/map/chart/text, and working comparison-bar swap/exit/header-pill controls that all correctly
preserve `?layout` — is fully achieved.

---

_Verified: 2026-07-28T10:15:00Z_
_Verifier: Claude (gsd-verifier)_
