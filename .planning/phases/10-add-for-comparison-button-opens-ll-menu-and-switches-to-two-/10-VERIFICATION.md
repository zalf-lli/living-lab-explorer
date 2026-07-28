---
phase: 10-add-for-comparison-button-opens-ll-menu-and-switches-to-two-
verified: 2026-07-28T07:29:32Z
status: gaps_found
score: 28/29 decisions verified (D-01..D-29), 1 confirmed defect (D-02 x D-04 interaction)
overrides_applied: 0
gaps:
  - truth: "?layout survives comparison end-to-end, including via the header-pill route (D-02, in combination with D-04)"
    status: failed
    reason: >
      LLDetail's own handleSwap/handleExit correctly clone searchParams and leave ?layout
      untouched, so D-02 holds for the ComparisonBar's own controls. But Header.jsx's
      compare-preserving pill click (D-04's implementation) rebuilds the target URL from
      scratch as `/ll/${ll.slug}?compare=${nextPartner}` (Header.jsx:75), dropping every
      other search param including ?layout. Repro, confirmed by direct code read: set layout
      B -> enter comparison -> click any header LL pill (to change primary or swap sides) ->
      click Exit -> LLDetail's layoutParam falls back to its 'A' default because ?layout is
      gone from the URL. This is a real, reproducible violation of D-02's explicit contract
      ("?layout stays in the URL untouched"), first surfaced in the committed advisory review
      (10-REVIEW.md WR-01) and independently confirmed here by reading Header.jsx:70-79 and
      LLDetail.jsx:22-23, 81-93.
    artifacts:
      - path: "app/src/components/Header.jsx"
        issue: "Line 75 constructs the navigate() target as a template string instead of cloning the existing useSearchParams() and only touching the compare key, so ?layout (and any other future param) is silently discarded on every compare-aware pill click."
    missing:
      - "Header.jsx must clone the current searchParams (via useSearchParams(), not the raw location.pathname) and set/delete only `compare`, leaving `layout` and any other existing param untouched — the same pattern LLDetail.jsx's handleSwap/handleExit already use. 10-REVIEW.md WR-01 contains a ready-to-use fix."
deferred: []
human_verification: []
---

# Phase 10: Wire up "Add for comparison" button to a real two-column LL comparison layout Verification Report

**Phase Goal:** Turn the placeholder "Add for comparison" button into a working side-by-side
comparison of two Living Labs: clicking it opens a menu of LL names, and selecting one switches
`/ll/:slug` into a two-column `?compare=` view where each column stacks that LL's KPIs, map,
chart and text under one shared layer-tab row.

**Verified:** 2026-07-28T07:29:32Z
**Status:** gaps_found
**Re-verification:** No — initial verification

**Traceability note:** ROADMAP Phase 10 declares `Requirements: TBD` — no REQ-IDs exist for this
phase. Per the phase's own design, the 29 locked decisions D-01..D-29 in `10-CONTEXT.md` are the
verifiable contract. This report verifies against those decisions and the `must_haves` blocks in
`10-01-PLAN.md` through `10-06-PLAN.md`. Missing REQ-ID traceability is not reported as a gap.

## Goal Achievement

### Core Observable Truths (phase goal, ROADMAP-level)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Clicking "Add for comparison" opens an anchored dropdown menu of the other 4 LL names | VERIFIED | `CompareCTA` (`LLDetail.jsx:834-892`) toggles `pickerOpen`; `ComparePicker` (`LLDetail.jsx:748-832`) renders `compareOptions` (built at `LLDetail.jsx:43-49` via `Object.values(bySlug).filter(x => x.slug !== slug)`) — always 4 rows, icon + name + colour chip, confirmed by direct read |
| 2 | Selecting an LL switches `/ll/:slug` into a two-column `?compare=<slug>` view, no new route | VERIFIED | `setCompare` (`LLDetail.jsx:51-55`) sets `?compare` via cloned `searchParams`; `isComparing` (`LLDetail.jsx:42`) branches to `<LayoutCompare>` (`LLDetail.jsx:110-111`); `git diff --stat` on `App.jsx` against the pre-phase commit `5bc5516` is empty — no route added |
| 3 | Each column stacks that LL's KPIs, map, chart and text under one shared layer-tab row | VERIFIED | `LayoutCompare` (`LLDetail.jsx:677-717`) renders one `<LayerTabs>` (line 697) above a grid of two `<ComparisonColumn>` (`LLDetail.jsx:567-671`), each rendering header -> `StatPanel` -> `LLMap` -> `BarChart` -> two `TextBlock`s in that order, confirmed by direct read |
| 4 | An unknown/self-referential `?compare=` is silently ignored, no error UI | VERIFIED | `partner` guard (`LLDetail.jsx:38-41`) checks `partnerCandidate.slug === compareSlug && compareSlug !== slug`; strip effect (`LLDetail.jsx:60-67`) deletes `compare` with `replace: true` when invalid — confirmed by direct read; exercised by human verification step 20 (`?compare=bogus`, self-slug, `__proto__`, all pass) |
| 5 | `?layout` survives entering/leaving comparison via the comparison bar's own controls | VERIFIED | `handleSwap`/`handleExit` (`LLDetail.jsx:81-93`) clone `searchParams` and only `set`/`delete` `compare`; `?layout` is read independently at `LLDetail.jsx:22-23` and never touched by either handler — confirmed by direct read and by human verification step 19 |
| 6 | `?layout` survives comparison end-to-end via **every** entry/exit path, including changing the primary LL from the site header while comparing | **FAILED** | See Gap below. `Header.jsx:70-79` rebuilds the target URL from scratch, dropping `?layout`. Confirmed by direct code read of `Header.jsx:75` and `LLDetail.jsx:22-23` |
| 7 | `npm run lint` and `npm run build` both exit 0 on the phase-final tree | VERIFIED | Ran independently: `npm run lint` exit 0 (no output); `npm run build` exit 0, 120 modules, no errors |
| 8 | No npm dependency was added or changed during the phase | VERIFIED | `git diff --stat 5bc5516 -- package.json package-lock.json` (app/) prints nothing |
| 9 | `npm run format:check` — pre-existing, repo-wide, not a phase-10 regression | VERIFIED (with caveat) | Ran independently: exit 1, 16 files flagged, matching the SUMMARY's claimed count exactly. Flagged set includes files this phase never touched (`LandingMap.jsx`, `MapLegend.jsx`, `chart_data.js`, `layers.js`, `useGeoJSON.js`, `projection.js`, etc.), corroborating the repo-wide-CRLF/pre-existing-printWidth explanation. Per the task's pre-established finding, not reported as a phase-10 regression |

**Score:** 8/9 core truths verified (one FAILED — see Gap below)

### D-01..D-29 Decision Verification (full contract)

Independently re-derived and spot-checked against `10-06-SUMMARY.md`'s evidence table rather than
trusting it. Every row below reflects a direct code read performed during this verification, not a
copy of the SUMMARY's claims.

| Decision | Status | Independent evidence |
|---|---|---|
| D-01 | VERIFIED | `compareSlug = searchParams.get('compare')` (`LLDetail.jsx:33`); `App.jsx` diff clean vs. `5bc5516` — no new route |
| D-02 | **PARTIAL** | Holds for `LLDetail`'s own `handleSwap`/`handleExit` (`LLDetail.jsx:81-93`); **fails** via `Header.jsx:70-79`'s pill click while comparing (see Gap) |
| D-03 | VERIFIED | `partner` guard + strip effect, `LLDetail.jsx:38-41, 60-67`; exercised by human step 20 |
| D-04 | VERIFIED | `Header.jsx:70-79` branches on `compareSlug`, swaps partner correctly when clicked LL is the current partner; exercised by human steps 16-17 |
| D-05 | VERIFIED | No `.split(` on `compare` anywhere in `LLDetail.jsx` (confirmed by grep) |
| D-06 | VERIFIED | `handleSwap` (`LLDetail.jsx:81-85`) always routes `/ll/<partner.slug>` with `compare=<former slug>`; no `?side=` param anywhere |
| D-07 | VERIFIED | Exactly one `<LayerTabs>` per rendered layout; `LayoutCompare` renders it once above both columns (`LLDetail.jsx:697`) |
| D-08 | VERIFIED | `grep -rc "get('layer')" app/src` returns 0 everywhere (confirmed independently) |
| D-09 | VERIFIED | `useLayerState()` called once (`LLDetail.jsx:31`), above the loading/unknown-slug early returns (`LLDetail.jsx:69-76`); remount keys no longer interpolate `ll.slug` (`key="A"`/`"B"`/`"C"`, lines 111/114/122-123) |
| D-10 | VERIFIED (currently dead-path in production data) | `StatPanel.jsx:31-53` and `BarChart.jsx:8-29` both correctly branch to a same-footprint placeholder instead of `null`; confirmed by direct read. Note (non-blocking, IN-01 in 10-REVIEW.md): all 5 LLs' `kpiByTab`/`CHART_DATA` are currently fully populated, so this code path cannot be exercised by clicking through the live app today — it is implemented correctly but untested by the human-verification pass |
| D-11 | VERIFIED | `useDismissOnOutside` (`LLDetail.jsx:722-743`) mirrors `StatPanel.jsx:14-29`'s Escape/outside-click pattern; no backdrop/focus-trap/scroll-lock in either dropdown's markup |
| D-12 | VERIFIED | `compareOptions` filters `x.slug !== slug` (`LLDetail.jsx:46`) — 4 rows, no disabled-state branch anywhere in `ComparePicker` |
| D-13 | VERIFIED | Each picker row ends with an `ll.outlineColor` chip (`LLDetail.jsx:816-826`) |
| D-14 | VERIFIED | `ComparisonBar` (`LLDetail.jsx:199-327`) owns hint label, both name buttons (shared `pickerOpen`), swap, exit — all in one row; neither `ComparisonColumn` nor `LayoutCompare` renders any comparison-control markup (confirmed by reading `LLDetail.jsx:567-717`) |
| D-15 | VERIFIED | `<CompareCTA` appears only inside `LayoutSplit` (line 439) and `LayoutStacked` (line 558); both are unreachable while `isComparing` (mutually exclusive render branch, lines 110-130) |
| D-16 | VERIFIED | `ComparisonColumn` order: accent bar -> header -> `StatPanel` -> `LLMap` -> `BarChart` -> two stacked `TextBlock`s (`LLDetail.jsx:567-671`), confirmed sequential (not grid) unlike `LayoutStacked`'s side-by-side text grid |
| D-17 | VERIFIED | 4px accent bar sourced from `ll.outlineColor` (`LLDetail.jsx:571`), the same field `LLMap` draws as the boundary line (`LLMap/index.jsx:733`) |
| D-18 | VERIFIED | Same `ll.outlineColor` chip pattern reused in `ComparisonBar` (`LLDetail.jsx:249-257, 274-282`) and `ComparePicker` rows (`816-826`) |
| D-19 | VERIFIED | `ComparisonColumn`'s header (`LLDetail.jsx:573-610`) matches `LayoutSplit`'s plain white header chrome, `ContactManagerButton` absent (present in `LayoutSplit`/`LayoutStacked`) |
| D-20 | VERIFIED | Single `overflowY: 'auto'` on `LayoutCompare`'s outer wrapper (`LLDetail.jsx:703`); the grid and columns set no `overflow` of their own |
| D-21 | VERIFIED | `grep -rn "@media\|matchMedia" app/src` returns nothing (confirmed independently, repo-wide) |
| D-22 | VERIFIED | `LLMap/index.jsx` byte-identical to pre-phase state (diff clean vs `5bc5516`); each `ComparisonColumn` passes its own `ll` to its own `<LLMap>` (`LLDetail.jsx:626`) |
| D-23 | VERIFIED | Both `ComparisonColumn`s render unconditionally in the same pass (`LLDetail.jsx:707-712`); `LLMap` remains `lazy()` (line 13), unchanged |
| D-24 | VERIFIED | One `<Suspense fallback={<MapFallback/>}>` per `ComparisonColumn` instance (`LLDetail.jsx:625-627`), independently mounted per column |
| D-25 | VERIFIED | `LLMap/index.jsx` renders its own `<MapLegend>` in every branch (lines 744, 755, 807, 817), confirmed unchanged; `grep -c "MapLegend" LLDetail.jsx` returns 0 — no page-level legend |
| D-26 | VERIFIED | `LLMap/index.jsx` unchanged (diff clean); it already owns its own inline per-layer error badges, no page-level banner exists in `LLDetail.jsx` |
| D-27 | VERIFIED | `height={300}` used in both `LayoutStacked` (line 509) and `ComparisonColumn` (line 626) |
| D-28 | VERIFIED | `ComparisonColumn`'s `<BarChart>` passes `compact` (`LLDetail.jsx:640`); `BarChart.jsx` itself confirmed unchanged in shape (compact prop pre-existing) |
| D-29 | VERIFIED | `StatPanel` accepts `maxColumns = 4` default (`StatPanel.jsx:8`), caps grid at `Math.min(fields.length, maxColumns)` (`StatPanel.jsx:97`); `ComparisonColumn` is the sole `maxColumns={2}` call site (`LLDetail.jsx:613`); single-LL calls (`398, 484`) pass no `maxColumns`, unchanged 4-across grid |

**Score:** 28/29 decisions fully verified; D-02 verified for its own primary mechanism
(ComparisonBar swap/exit) but fails for the Header-pill interaction path (D-04's implementation).

### Assessment of the WR-01 / D-02 defect (independent judgment)

This is a real, reproducible, code-confirmed violation of a locked decision, not a
documentation-only nit. It was surfaced by the committed advisory review (`10-REVIEW.md` WR-01,
severity Warning) and is independently confirmed here by reading `Header.jsx:70-79` and
`LLDetail.jsx:22-23, 81-93`. It was **not** caught by the phase's own 23-step human verification
script: step 19 checks "exit restores your prior layout" only via the direct
enter-comparison-then-exit path, and steps 16-17 check the header-pill primary/swap behavior in
isolation, but no step combines the two (switch primary via header pill, *then* exit).

Judgment: this rises to a **phase-level gap**, not a mere polish item, because it is a direct,
provable break of one of the 29 decisions this phase's own traceability model treats as its
contract — and because it defeats exactly the "sweep through LLs against a fixed reference" workflow
D-04 was designed to support (10-CONTEXT.md's `<specifics>` section states this explicitly). It does
**not**, however, block the phase's headline deliverable: the picker opens, selecting an LL renders
the two-column view, both columns render KPIs/map/chart/text under one shared layer-tab row, and the
comparison bar's own swap/exit controls correctly preserve `?layout`. The defect is narrowly scoped
to one specific compound interaction (header-pill navigation while comparing, followed by exit), has
a one-file, already-fully-specified fix (`10-REVIEW.md` WR-01), and does not corrupt data, crash the
app, or leave the user in a broken state (layout silently resets to a still-valid default, A, rather
than erroring). Classification: **BLOCKER for full phase closure** (must be fixed before the phase is
considered fully done, since it fails one of the phase's own locked decisions), but it is a small,
scoped, one-file fix — not evidence that the phase's core mechanism is unsound.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `app/src/pages/LLDetail.jsx` | `?compare=` parsing, `ComparisonBar`, `ComparePicker`, `LayoutCompare`, `ComparisonColumn`, lifted `useLayerState` | VERIFIED | All present, substantive, wired — confirmed by direct read of the full 927-line file |
| `app/src/components/Header.jsx` | `?compare=`-aware pill navigation | VERIFIED (exists/wired) but see D-02 gap for a correctness defect in its implementation | `Header.jsx:70-79` |
| `app/src/components/StatPanel.jsx` | `maxColumns` + `showEmptyState` props | VERIFIED | `StatPanel.jsx:8, 31-53, 97` |
| `app/src/components/BarChart.jsx` | `minHeightWhenEmpty` prop | VERIFIED | `BarChart.jsx:5, 8-29` |
| `app/src/i18n.js` | EN+DE comparison-bar/picker/empty-state keys | VERIFIED | All 10 keys present in both EN (lines 230-240) and DE (457-467) blocks; parity confirmed by independent grep |
| `.planning/phases/10.../10-06-SUMMARY.md` | Decision-evidence table + human sign-off | VERIFIED | Present, 29-row table, human approval recorded verbatim |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `CompareCTA` button | `ComparePicker` | `pickerOpen` state + `useDismissOnOutside` ref | WIRED | `LLDetail.jsx:836-889` |
| `ComparePicker` row `onClick` | `setCompare` / `onPickCompare` | `onPick(ll.slug)` prop chain | WIRED | `LLDetail.jsx:786, 884-887` -> `LLDetail.jsx:51-55` |
| `LLDetail` compare state | URL search params | `useSearchParams` + `setSearchParams` | WIRED | `LLDetail.jsx:21, 33, 51-55, 60-67` |
| `ComparisonBar` name buttons | `ComparePicker` | shared `pickerOpen` + `useDismissOnOutside` | WIRED | `LLDetail.jsx:201-296` |
| `ComparisonBar` swap | `react-router navigate` | `handleSwap` -> `navigate({pathname, search})` | WIRED | `LLDetail.jsx:81-85, 302` |
| `ComparisonBar` exit | `setSearchParams` | `handleExit` deletes `compare`, keeps `layout` | WIRED | `LLDetail.jsx:89-93, 315` |
| `LayoutCompare` render branch | `ComparisonColumn` x2 | `isComparing` ternary, `llA`/`llB` props | WIRED | `LLDetail.jsx:110-111, 707-712` |
| `LayoutCompare` | shared `LayerTabs` | single `active`/`onChange` pair above the grid | WIRED | `LLDetail.jsx:697` |
| Header LL pill | `?compare=`-aware navigation | `navigate()` template string | **PARTIALLY WIRED** | Sets `compare` correctly but drops `layout` and any other existing param — see Gap |

### Data-Flow Trace (Level 4)

Not applicable in the traditional API/DB sense — this is a client-only SPA reading pre-built static
JSON via `useLLMetadata`. Traced the one data dependency relevant to this phase instead:
`bySlug` (from `useLLMetadata`, passed into `LLDetail` from `App.jsx:34`) is the same object used
for both the primary `ll` lookup and the partner lookup (`LLDetail.jsx:34`) — confirmed no separate
fetch was introduced for the comparison partner, consistent with the plan's stated reuse of the
existing metadata hook.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Lint passes | `cd app && npm run lint` | exit 0, no output | PASS |
| Build passes | `cd app && npm run build` | exit 0, 120 modules, no errors | PASS |
| No new/changed dependency | `git diff --stat 5bc5516 -- app/package.json app/package-lock.json` | empty | PASS |
| Untouched files byte-identical | `git diff --stat 5bc5516 -- app/src/App.jsx app/src/components/LayerTabs.jsx app/src/components/LLMap/index.jsx app/src/components/LLBadge.jsx app/src/components/TextBlock.jsx` | empty | PASS |
| No `?layer=` param anywhere | `grep -rn "get('layer')" app/src` | no matches | PASS |
| No responsive infra introduced | `grep -rn "@media\|matchMedia" app/src` | no matches | PASS |
| `format:check` scope (pre-existing) | `cd app && npm run format:check` | exit 1, 16 files, including files this phase never touched | PASS (as pre-existing, per task's pre-established finding) |
| i18n EN/DE key parity for compare* strings | manual grep of `compare*` keys | all 10 keys present in both language blocks | PASS |

Not applicable: this phase has no server/API to curl and no CLI entry point beyond the Vite dev
server; a full click-through was performed by the human reviewer instead (see below).

### Probe Execution

No `scripts/*/tests/probe-*.sh` convention exists in this repo, and neither the plans nor the
SUMMARYs reference probe-based verification for this phase. Step 7c: SKIPPED (no runnable probes
declared or discoverable for this phase).

### Requirements Coverage

ROADMAP Phase 10 declares `Requirements: TBD` and no plan in this phase lists any REQ-ID in its
`requirements:` frontmatter field (all six plans have `requirements: []`). No REQUIREMENTS.md rows
map to Phase 10. This is intentional per the phase's own design (traceability runs through
D-01..D-29 instead) and is not reported as a gap, per the task's explicit instruction.

### Anti-Patterns Found

No debt markers (`TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER`) exist anywhere in the five files
this phase modified (`LLDetail.jsx`, `Header.jsx`, `StatPanel.jsx`, `BarChart.jsx`, `i18n.js`) —
confirmed by direct grep, zero matches. The advisory review (`10-REVIEW.md`, committed) documents
7 Warning-level and 8 Info-level findings beyond WR-01/D-02, none of which are debt markers and
none of which were re-derived as blocking here; they are non-blocking quality/robustness/a11y
issues (dropdown a11y gaps, an empty-value `?compare=` edge case, a z-index tie with Leaflet's
control corners, dead code, hardcoded colour literals, an inert `gridColumn` rule, an unguarded
`activeSlug` decode). Not re-listed row-by-row here since `10-REVIEW.md` is the canonical source
and is already committed to the repo; none of them contradict a locked D-01..D-29 decision the way
WR-01 does, so none of them independently change this report's overall status.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `app/src/components/Header.jsx` | 75 | URL rebuilt from scratch on compare-aware pill click, dropping `?layout` | 🛑 Blocker (fails locked decision D-02) | See Gap above |
| `app/src/pages/LLDetail.jsx` | 60-67 | `?compare=` with an empty string (`?compare=`) is not stripped (`WR-03` in `10-REVIEW.md`) | ⚠️ Warning | Edge case, not part of the 29 locked decisions' literal wording; documented in the advisory review, not independently re-derived as blocking |
| `app/src/pages/LLDetail.jsx` | 763 | Picker `zIndex: 1000` ties with Leaflet's `.leaflet-top/.leaflet-bottom` (`WR-04`) | ⚠️ Warning | Thin but real overlap risk; not a locked-decision violation |
| `app/src/pages/LLDetail.jsx` | 241-296, 722-767, 862-878 | Dropdown lacks `aria-haspopup`/`role="menu"`, Escape drops focus to `<body>` (`WR-05`) | ⚠️ Warning | A11y gap; D-11's "no focus trap" allowance does not require this, but it is a UX regression for keyboard users |

### Human Verification Required

None outstanding. A human reviewer (Benjamin Samuel Black, project owner) already completed the
full 23-step bilingual verification script (`10-06-PLAN.md`) on 2026-07-28 and returned `approved`
with no issues reported, recorded verbatim in `10-06-SUMMARY.md` under "Human verification
findings." That approval is accepted at face value for everything the script actually exercised.
It does not cover the WR-01/D-02 compound interaction (header-pill switch, then exit) — no step
combines steps 16/17 with step 19 — so its absence from the sign-off is expected, not a
contradiction.

### Gaps Summary

Of the phase's 29 locked decisions, 28 are fully and directly verified against the shipped code —
independently re-derived here, not copied from `10-06-SUMMARY.md`'s table. The one exception is
D-02, which holds for the comparison bar's own swap/exit controls but is broken by `Header.jsx`'s
compare-aware pill-click navigation, which rebuilds the target URL from scratch and silently drops
`?layout` (and would drop any other future search param the same way). This was already caught and
fully specified by the committed advisory review (`10-REVIEW.md` WR-01) and is confirmed here by
direct code read, not by trusting the review or the SUMMARY. The fix is a single, already-specified
change to `Header.jsx`'s pill `onClick` handler (clone `useSearchParams()` instead of rebuilding the
URL from `location.pathname`), matching the pattern `LLDetail.jsx`'s own `handleSwap`/`handleExit`
already use correctly. The phase's headline deliverable — a working picker-driven two-column
comparison view with shared layer tabs, per-column KPIs/map/chart/text, and a working
comparison-bar swap/exit — is otherwise fully achieved and verified.

---

_Verified: 2026-07-28T07:29:32Z_
_Verifier: Claude (gsd-verifier)_
