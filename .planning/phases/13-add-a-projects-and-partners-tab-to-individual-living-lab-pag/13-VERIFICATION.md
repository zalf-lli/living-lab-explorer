---
phase: 13-add-a-projects-and-partners-tab-to-individual-living-lab-pag
verified: 2026-08-14T00:00:00Z
status: human_needed
score: 18/18 must-haves verified (D-01..D-18)
overrides_applied: 0
human_verification:
  - test: "Switch the active Living Lab from the header LL switcher while the Partners & Projects tab is already open and active (not a fresh page load), for at least one LL pair. Watch the Partners panel and map during the transition."
    expected: "No frame shows the previous Living Lab's partner name/card/marker after the header/boundary have already updated to the new Living Lab. Loading state (or an immediate correct card) appears, never a stale-LL flash."
    why_human: "This is the exact runtime race CR-01's fix (commit 66383e2) targets. The fix's logic was traced algebraically against the codebase's own working precedent (useGeoJSON.js's state.key guard) and confirmed structurally sound by static reading, but it introduces new observable runtime behavior across an LL-switch-while-on-Partners-tab interaction that no human or automated check has ever exercised live — Task 3's original checklist did not include this path, and the project has no JS test runner to exercise it mechanically. Low risk, quick check (under a minute), not a request for a full Task 3 re-run."
---

# Phase 13: Add a Projects and Partners Tab to Individual Living Lab Pages — Verification Report

**Phase Goal:** Every Living Lab detail page carries a sixth, visually separated Partners & Projects
tab showing a boundary-only Leaflet map with partner point markers plus a two-section
partners/projects overview panel, driven by a hand-authored static JSON published by the pipeline
and fetched lazily only when the tab is active.

**Verified:** 2026-08-14
**Status:** human_needed (one low-risk, low-cost confirmatory check recommended — see below; not a
phase-blocking gap)
**Re-verification:** No — initial verification of this phase

## Goal Achievement

### Observable Truths (D-01..D-18, this phase's locked requirement set per ROADMAP.md/13-CONTEXT.md)

All 18 were spot-checked directly against the current source tree (not merely re-stated from
`13-EVIDENCE.md`'s own table). Evidence column cites files/line content actually read in this
verification pass.

| #    | Truth (from 13-CONTEXT.md decisions)                                                                 | Status     | Evidence (read directly, this pass)                                                                                                                                                                                                                                                                                     |
| ---- | ------------------------------------------------------------------------------------------------------ | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D-01 | EN tab label "Partners & Projects", Partners first                                                     | ✓ VERIFIED | `app/src/i18n_resources.js:72` — `partners: 'Partners & Projects'`; rendered via `LayerTabs.jsx:80` `{t('layers.partners')}`                                                                                                                                                                                             |
| D-02 | DE tab label "Partner & Projekte"                                                                      | ✓ VERIFIED | `app/src/i18n_resources.js:314` — `partners: 'Partner & Projekte'`                                                                                                                                                                                                                                                        |
| D-03 | Two visually separate sections (Partners, Projects), not one mixed list                                | ✓ VERIFIED | `PartnersOverviewPanel.jsx:180-189` renders `<PartnersSection>` then `<ProjectsSection>` as two independent `<section>` blocks in a `flexDirection: 'column'` wrapper — no shared/interleaved list                                                                                                                      |
| D-04 | Tab visually separated on the right side of the tab container                                          | ✓ VERIFIED | `LayerTabs.jsx:14` outer div `justifyContent: 'space-between'`; partners button (line 53-81) sits outside the `LAYERS.map()` group with `borderLeft`, `marginLeft: 8`, `paddingLeft: 16` as a divider — a genuinely separate right-hand group, not appended inline                                                     |
| D-05 | One combined tab; no new route; not a map-only drilldown                                               | ✓ VERIFIED | `App.jsx:33-35` — only two routes (`/`, `/ll/:slug`) exist, unchanged since before this phase; one `layer === 'partners'` value drives both `PartnersMapSlot` and `PartnersPanelSlot` from the same `LLDetail.jsx` branch points                                                                                       |
| D-06 | Separate static JSON, not `ll_content.json`/`ll_metadata.json`                                         | ✓ VERIFIED | `data/partners_projects.json` exists as its own file; `git diff --exit-code <BASE>..HEAD -- data/ll_content.json` (re-run this pass) is empty — confirmed byte-unchanged                                                                                                                                                |
| D-07 | Grouped by LL slug, each entry `{partners[], projects[]}`                                              | ✓ VERIFIED | Read `data/partners_projects.json` directly — 5 top-level keys (`east-brandenburg`, `havellandisches-luch`, `north-hessian-loess`, `hessian-low-mountain`, `rheingau`), each `{partners:[...], projects:[]}`; `test_partners_projects_contract_and_publish_parity` re-run live this pass, passed                        |
| D-08 | Hand-authored under `data/`, published by `sync.py`                                                    | ✓ VERIFIED | `data-pipeline/sync.py:35` — `"data/partners_projects.json"` in `STATIC_DATA_FILES`; `diff data/partners_projects.json app/public/data/partners_projects.json` run this pass — byte-identical                                                                                                                          |
| D-09 | Lazy-fetched only when tab active, never eager, never merged into `ll_metadata.json`                   | ✓ VERIFIED | `usePartnersProjects` is called only from `PartnersMapSlot`/`PartnersPanelSlot` (`PartnersProjectsTab.jsx:68,90`), both mounted only inside `layer === 'partners'` branches in `LLDetail.jsx` (5 call sites, all guarded); module-scoped `cache`/`inflight` in `usePartnersProjects.js:6-24` dedupes concurrent callers |
| D-10 | Map shows partners only; projects are panel-only content                                               | ✓ VERIFIED | `grep -c projects app/src/components/PartnersMap.jsx` → 0 (re-run this pass); `PartnersMap.jsx` has no `projects` prop or reference anywhere                                                                                                                                                                             |
| D-11 | JSON presence is the permission boundary; no permission/visibility field or filter                     | ✓ VERIFIED | `grep -n "permission|visible|approved|published" app/src/components/PartnersMap.jsx` → no matches (re-run this pass); schema test asserts exact key set `{partners, projects}` per slug and `{name,type,location,website,lat,lng,id}`-shaped partner objects only                                                     |
| D-12 | Marker tooltip on hover/focus; click opens partner website when available                              | ✓ VERIFIED | `PartnersMap.jsx:42-54` — `eventHandlers: {focus: openTooltip, blur: closeTooltip, click: safeExternalUrl-guarded window.open}`, `keyboard` prop set on `<Marker>`; keyboard-only human pass (Task 3, all 4 sub-checks) confirmed live per `13-EVIDENCE.md` "Step 7" table                                            |
| D-13 | Map background is base map + LL boundary/mask only, no thematic layer/legend                           | ✓ VERIFIED | `PartnersMap.jsx` imports no `layers.js`/`MapLegend`; renders only `TileLayer` + optional mask `GeoJSON` + boundary outline `GeoJSON` + `PartnerMarker`s (lines 115-142); `grep -c "layers.js\|LAYER_INDEX\|MapLegend"` → 0                                                                                              |
| D-14 | Partners without coordinates appear in the panel but not on the map                                    | ✓ VERIFIED | `partnersProjects.js:30-42` `partitionPartnersByCoordinates` splits on `Number.isFinite(lat/lng)`; `PartnersProjectsTab.jsx:76` passes only `.mapped` to `PartnersMap`, `PartnersPanelSlot` (line 95) passes the full unpartitioned `data.partners`; live data exercises this — 4 of 5 slugs ship a partner with no `lat`/`lng`                                                        |
| D-15 | Partner cards show `name`, `type`, `location`, `website`                                               | ✓ VERIFIED | `PartnersOverviewPanel.jsx:25-72` `PartnerCard` renders all four, three conditional (`type`, `location`, `website`), `name` unconditional                                                                                                                                                                                |
| D-16 | Project cards show `title`, `summary`, `partner`, `website`                                            | ✓ VERIFIED (code path only — no live project data exists) | `PartnersOverviewPanel.jsx:109-145` `ProjectCard` renders all four fields correctly; all five LL slugs ship `projects: []` today (human-accepted "ship as-is" content decision, `13-EVIDENCE.md` "Content decision") — verified by code inspection, not exercised end-to-end with real content                        |
| D-17 | Only `project.summary` is bilingual `{en, de}`; names/titles/URLs are shared strings                   | ✓ VERIFIED | `ProjectCard`'s only `[lang]`-keyed read is `project.summary?.[lang]` (line 117); pytest schema test asserts `summary` is the only `{en,de}`-shaped field                                                                                                                                                                |
| D-18 | Empty Partners/Projects sections stay visible with a quiet bilingual empty state                       | ✓ VERIFIED | `PartnersSection`/`ProjectsSection` (`PartnersOverviewPanel.jsx:74-107, 147-174`) render heading unconditionally + a `1px dashed` placeholder block when the array is empty; this is the live default state today (all 5 slugs ship `projects:[]`)                                                                     |

**Score:** 18/18 truths verified against the current codebase (not against `13-EVIDENCE.md`'s
narrative alone).

### Required Artifacts

| Artifact                                        | Expected                                    | Status     | Details                                                                                             |
| ------------------------------------------------ | -------------------------------------------- | ---------- | ----------------------------------------------------------------------------------------------------- |
| `data/partners_projects.json`                    | Hand-authored, grouped-by-slug source        | ✓ VERIFIED | 5 slugs, 5 partners, 0 projects, schema matches D-07/D-15/D-16                                        |
| `app/public/data/partners_projects.json`         | Published runtime copy                      | ✓ VERIFIED | Byte-identical to source (`diff` run this pass, no output)                                            |
| `app/src/lib/llBoundary.js`                      | Shared boundary/bounds logic                | ✓ VERIFIED | `selectBoundary`/`getBounds`, imported by both `LLMap/index.jsx:29` and `PartnersMap.jsx:7`           |
| `app/src/lib/partnersProjects.js`                | Pure selection/partition/URL-safety helpers  | ✓ VERIFIED | `selectLLPartnersProjects`, `partitionPartnersByCoordinates`, `safeExternalUrl` all present and used  |
| `app/src/hooks/usePartnersProjects.js`           | Lazy, cached, per-slug fetch hook            | ✓ VERIFIED | Module cache/inflight dedup + (post-fix) `state.slug !== slug` stale-guard, mirroring `useGeoJSON.js` |
| `app/src/components/PartnersMap.jsx`             | Boundary-only Leaflet map with markers       | ✓ VERIFIED | Renders `TileLayer`+mask+outline+markers only; XSS-safe divIcon; aria-label fix present               |
| `app/src/components/PartnersOverviewPanel.jsx`   | Two-section overview panel                   | ✓ VERIFIED | `PartnersSection`/`ProjectsSection`, all D-15/D-16 fields, D-18 empty states                          |
| `app/src/components/PartnersProjectsTab.jsx`     | Composition root, two mountable slot exports | ✓ VERIFIED | `PartnersMapSlot`/`PartnersPanelSlot`, correctly split per the Task 3 layout-bug fix                  |
| `app/src/components/LayerTabs.jsx`               | Right-side, visually separated tab button    | ✓ VERIFIED | Separate group with divider styling, D-04                                                             |
| `app/src/pages/LLDetail.jsx`                     | Three layout branch points wired             | ✓ VERIFIED | `LayoutSplit`, `LayoutStacked`, `ComparisonColumn` all branch `layer === 'partners'` correctly         |
| `data-pipeline/sync.py`                          | Publish step                                 | ✓ VERIFIED | One-line `STATIC_DATA_FILES` addition                                                                 |
| `data-pipeline/tests/test_pipeline_outputs.py`   | Contract + publish-parity pytest             | ✓ VERIFIED | `test_partners_projects_contract_and_publish_parity`, re-run live this pass, passed                   |
| `app/src/i18n_resources.js`                      | EN/DE strings, key parity                    | ✓ VERIFIED | `layers.partners`, `partnersTab.*` blocks present and parallel in both `en`/`de` sections              |

### Key Link Verification

| From                              | To                                     | Via                                                     | Status  | Details                                                                                                                    |
| ---------------------------------- | ---------------------------------------- | ---------------------------------------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------- |
| `LayerTabs.jsx` partners button    | `LLDetail.jsx` `setLayer`                | `onClick={() => onChange('partners')}`                     | WIRED   | Sets shared `layer` state, propagates to all three layout functions                                                       |
| `LLDetail.jsx` `layer==='partners'`| `PartnersMapSlot`/`PartnersPanelSlot`    | Conditional branch in `LayoutSplit`/`LayoutStacked`/`ComparisonColumn` | WIRED   | Confirmed by direct read of all 3 call sites — map always renders in `LLMap`'s own slot, panel in the normal content slot |
| `PartnersMapSlot`/`PartnersPanelSlot` | `usePartnersProjects(ll.slug)`        | Direct hook call                                            | WIRED   | Both call sites confirmed; module cache/inflight guarantees exactly one network request                                   |
| `usePartnersProjects`              | `data/partners_projects.json`            | `fetch('data/partners_projects.json')`                     | WIRED   | Runtime fetch resolves against the published file; pytest confirms publish parity                                         |
| `sync.py` `STATIC_DATA_FILES`      | `app/public/data/partners_projects.json` | `sync_file()` copy                                          | WIRED   | Byte-identical copy confirmed live this pass                                                                              |
| `PartnersMap.jsx`                  | `data/ll_boundaries.geojson`             | `useGeoJSON('data/ll_boundaries.geojson')` + `llBoundary.js`| WIRED   | Shared with `LLMap`, confirmed both import the same `selectBoundary`/`getBounds`                                          |
| `PartnerMarker` click              | Partner website                          | `safeExternalUrl` + `window.open`                           | WIRED   | Scheme-allowlisted (`https:`/`http:` only); confirmed by direct read                                                       |

### Data-Flow Trace (Level 4)

| Artifact                  | Data Variable                | Source                                | Produces Real Data | Status                                                                                                     |
| --------------------------- | ------------------------------- | ---------------------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------- |
| `PartnersMapSlot`           | `data.partners` (mapped subset) | `usePartnersProjects` → fetch → JSON     | Yes (1 partner/LL)   | ✓ FLOWING — `east-brandenburg` renders a real marker (lat/lng present); other 4 LLs correctly show none      |
| `PartnersPanelSlot`         | `data.partners`/`data.projects` | Same hook                                | Partners: yes. Projects: no (empty array by design, human-accepted) | ✓ FLOWING for partners; ⚠️ deliberately empty for projects (not a defect — human "ship as-is" decision, `13-EVIDENCE.md`) |

### Anti-Patterns Found

None. Grepped all phase-13-authored/modified files (`PartnersMap.jsx`, `PartnersOverviewPanel.jsx`,
`PartnersProjectsTab.jsx`, `LayerTabs.jsx`, `usePartnersProjects.js`, `partnersProjects.js`,
`llBoundary.js`, `LLDetail.jsx`, `sync.py`) for `TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER` — the only
hits are an unrelated pre-existing `_PLACEHOLDER_RE` regex variable name in `sync.py`, not a debt
marker. No `dangerouslySetInnerHTML`/`innerHTML`/`insertAdjacentHTML` sinks touch any
partner/project-authored content (re-confirmed via the negative grep from `13-EVIDENCE.md`, and by
direct read of `PartnersMap.jsx`/`PartnersOverviewPanel.jsx` — all authored content reaches the DOM
through React's auto-escaping interpolation only).

### Behavioral Spot-Checks (re-run live this verification pass, not merely re-cited from EVIDENCE)

| Behavior                                                              | Command                                                                    | Result                                          | Status  |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------- | ------------------------------------------------ | ------- |
| Pipeline contract + publish-parity test                                  | `pytest data-pipeline/tests/test_pipeline_outputs.py -k partners_projects` | `1 passed`                                        | ✓ PASS  |
| Full pipeline pytest suite                                               | `pytest data-pipeline/tests/`                                             | `43 passed, 1 failed` — failure is `test_report_fixtures_published_to_app_public` on `report-rheingau-de.pdf`, a **pre-existing local, out-of-phase content diff** (matches the `M data/reports/report-rheingau-de.pdf` line present in `git status` at session start, unrelated to any phase-13 file) | ✓ PASS (phase-13 scope) |
| Frontend lint                                                            | `npm run lint`                                                             | Clean, no output                                  | ✓ PASS  |
| Frontend build                                                           | `npm run build`                                                            | Succeeded, 136 modules, `dist/assets/PartnersMap-*.js` chunk present | ✓ PASS  |
| Source/published-copy byte parity                                        | `diff data/partners_projects.json app/public/data/partners_projects.json` | Identical                                         | ✓ PASS  |

### Requirements Coverage

Phase 13 has no `REQUIREMENTS.md` IDs; `13-CONTEXT.md`'s D-01..D-18 decisions are the declared
requirement set (per `.planning/ROADMAP.md`'s Phase 13 entry). All 18 are SATISFIED — see Observable
Truths table above. No orphaned requirements found (`13-CONTEXT.md` and `13-EVIDENCE.md` both
enumerate exactly D-01..D-18; every plan's `requirements` field carries a D-ID subset of this set,
per `13-EVIDENCE.md`'s own commit-by-commit table, spot-confirmed for D-01/D-04/D-07/D-09/D-13 above).

---

## Post-Approval Code-Review Fixes: Safety Assessment (commit `66383e2`)

**Context:** The human approved Task 3's checklist (D-01..D-18, bilingual pass, 3 layouts, D-12
keyboard pass) in commit `c5f8c41`. The orchestrator's own code review then ran (`13-REVIEW.md`,
`d6b8bcd`) and found 1 critical + 2 warning + 1 info-level issue, all fixed in one commit
(`66383e2`) **after** human sign-off, without a third human checkpoint round. This section
independently re-derives whether that was safe, by reading the actual diff (not the SUMMARY's prose)
and tracing each change against what Task 3's checklist actually exercised.

### CR-01 — `usePartnersProjects` stale-slug guard

**Diff read directly** (`git show 66383e2 -- app/src/hooks/usePartnersProjects.js`): adds a `slug`
field to the hook's state object and a `if (state.slug !== slug) return {data:null, loading:true,
error:null}` guard before the final `return state`, mirroring `useGeoJSON.js`'s established
`state.key !== key` pattern.

**Traced against Task 3's checklist:** Task 3's 12 steps never include "switch LL from the header
while already on the Partners tab" — every step operates on one LL at a time (steps 1-9), comparison
mode (step 10) mounts two independent, already-correct `PartnersProjectsTab`/slot instances rather
than switching an existing one's slug. On initial mount (every scenario Task 3 *did* exercise), the
hook's `useState` initializer sets `state.slug` to the current `slug` argument, so
`state.slug === slug` is true immediately and the guard is a no-op — behavior is unchanged from
before the fix for every tested path. The guard only ever activates on a slug **change without
unmount**, which is exactly the untested path CR-01 identified. **Conclusion: this fix cannot have
altered any Task 3-observed behavior — it only changes behavior on a path Task 3 never visited.**
It does, however, introduce genuinely new runtime behavior on that untested path, which is why this
report recommends (not requires) one quick live confirmatory check — see `human_verification` above.

### WR-01 — Marker `aria-label` fix

**Diff read directly**: removes the (silently inert, per WR-01's own diagnosis) `alt` prop from
`<Marker>` and adds an `eventHandlers.add` callback that sets `aria-label` on the marker's DOM node.
The pre-existing `focus`/`blur`/`click` handlers are untouched — `add` is a distinct event key in
the same object, fired once when Leaflet mounts the marker, with no interaction with focus/blur
timing.

**Traced against Task 3's checklist:** Step 7 (D-12 keyboard pass) tests focus ring visibility,
tooltip-on-focus, tooltip-close-on-blur, and Enter-opens-website — none of which read or depend on
`alt`/`aria-label`. The `alt` prop being removed had **zero effect before the fix** (confirmed by
Leaflet's own `DivIcon.createIcon()` always returning a bare `<div>`, on which `.alt` is an inert JS
expando, not a reflected HTML attribute) — so removing a no-op prop cannot regress anything a sighted
keyboard pass could observe. **Conclusion: WR-01's fix is additive-only for assistive technology and
provably could not have affected any behavior Task 3's sighted+keyboard pass could detect** — this
matches `13-EVIDENCE.md`'s own reasoning, independently re-derived here from the diff rather than
trusted from its prose.

### WR-02 — Dead outer `<Suspense>` removal

**Diff read directly**: removes `<Suspense fallback={<MapFallback />}>` wrapping `<PartnersMapSlot>`
at all three `LLDetail.jsx` call sites. `PartnersMapSlot` is a plain, eagerly-imported function
component (confirmed: `import { PartnersMapSlot, PartnersPanelSlot } from
'../components/PartnersProjectsTab.jsx'` at the top of `LLDetail.jsx`, no `lazy()` wrapper) — it can
never itself throw a promise, so the outer boundary was inert. The only actual `lazy()` import in
this tree (`PartnersMap`, inside `PartnersProjectsTab.jsx`) retains its own, correctly-scoped inner
`<Suspense>` (confirmed present at `PartnersProjectsTab.jsx:78-82` in the current tree).

**Traced against Task 3's checklist:** Removing a boundary with no suspending descendant is a
behavioral no-op by React's own semantics — there is nothing for Task 3's map-loading/layout checks
(steps 4, 9) to have observed differently, and the inner boundary that actually matters is
unchanged. **Conclusion: no behavioral change possible.**

### IN-01 — Documentation comment on `unmapped`

Comment-only change (verified via diff — zero lines of executable code touched in
`partnersProjects.js`). **Conclusion: cannot affect any behavior.**

### Overall verdict on shipping without a third human checkpoint

**Safe.** Independently re-deriving from the diff (not the SUMMARY's narrative), none of the four
fixes in `66383e2` change any behavior Task 3's original 12-step checklist exercised — three of the
four (WR-01, WR-02, IN-01) are provably behavior-preserving by construction (dead code removal, a
previously-inert prop replaced with a working equivalent that no test path reads, and a comment).
The fourth (CR-01) only activates on an LL-switch-while-on-Partners-tab path that Task 3 never
tested, so it cannot have regressed anything already approved — but it is also the one piece of
genuinely new, previously-unexercised runtime behavior in this commit, on a path with no automated
test coverage (the project has no JS test runner). That gap is real but narrow, and does not
warrant reopening the full Task 3 checklist — a single, low-cost manual confirmation of the
LL-switch-while-on-Partners-tab path (see `human_verification` above) closes it without the overhead
of a third full round.

---

## Human Verification Required

### 1. LL-switch-while-on-Partners-tab stale-data check (CR-01 fix confirmation)

**Test:** With the Partners & Projects tab already active for one Living Lab, use the header's LL
switcher to change to a different Living Lab (do not navigate away from the Partners tab first).
Repeat once more for a second LL pair to be confident.

**Expected:** The Partners panel and map update to the new Living Lab's data without ever showing a
frame where the header/name/boundary already reflect the new LL but the partner card/marker still
show the previous LL's data. A brief loading state (or an already-correct card, since the JSON is
already cached from the first tab visit) is acceptable; a stale-LL flash is not.

**Why human:** This is a React state-timing race across a slug prop change without component
unmount — the exact class of bug `useGeoJSON.js`'s established `state.key` guard pattern exists to
prevent, and the fix (commit `66383e2`) mirrors that pattern correctly by static reading, but the
project has no JS test runner to exercise it mechanically, and no human has watched it live yet
(Task 3's checklist did not include this interaction). Low risk given the pattern is proven
elsewhere in the app; recommended as a quick confirmatory check, not a blocker to phase closure.

---

## Gaps Summary

No gaps found. All 18 locked decisions (D-01..D-18) verified directly against the current source
tree, not merely re-stated from `13-EVIDENCE.md`. Lint, build, and the phase's own pytest contract
test all pass live as re-run during this verification. The one failing pytest test in the full suite
(`test_report_fixtures_published_to_app_public` on `report-rheingau-de.pdf`) is a pre-existing,
out-of-phase local content diff unrelated to any phase-13 file (matches the `M
data/reports/report-rheingau-de.pdf` line already present in `git status` before this verification
began) and does not count against this phase's score.

The single item raised is a recommended, low-cost confirmatory check on the post-approval CR-01 fix
(see Human Verification above) — not a gap in what was built, but a request to close the one sliver
of genuinely new runtime behavior shipped after the human's last live look at the feature. Everything
else the post-approval code-review commit (`66383e2`) touched is independently confirmed, by direct
diff reading in this pass, to be either behavior-preserving by construction or additive-only for
assistive technology.

---

_Verified: 2026-08-14_
_Verifier: Claude (gsd-verifier)_
