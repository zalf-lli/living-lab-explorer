---
phase: 13-add-a-projects-and-partners-tab-to-individual-living-lab-pag
plan: 06
subsystem: quality-gate
tags:
  [
    close-out,
    evidence,
    xss-audit,
    dependency-audit,
    human-checkpoint,
    layout-fix,
  ]

dependency-graph:
  requires:
    - phase: 13-01
      provides: data/partners_projects.json, sync.py publish, i18n strings, pytest contract test
    - phase: 13-02
      provides: app/src/lib/llBoundary.js, app/src/lib/partnersProjects.js, usePartnersProjects.js
    - phase: 13-03
      provides: app/src/components/PartnersMap.jsx
    - phase: 13-04
      provides: app/src/components/PartnersOverviewPanel.jsx
    - phase: 13-05
      provides: original PartnersProjectsTab.jsx composition root, LayerTabs.jsx right-side group, three LLDetail.jsx layer==='partners' branch points
  provides:
    - .planning/phases/13-add-a-projects-and-partners-tab-to-individual-living-lab-pag/13-EVIDENCE.md (full phase close-out record, D-01..D-18 verdicts, human sign-off)
    - app/src/components/PartnersProjectsTab.jsx (revised: PartnersMapSlot + PartnersPanelSlot, replacing the single combined export)
  affects: []

tech-stack:
  added: []
  patterns:
    - "Phase close-out pattern: automated-gate task + decision-evidence task + blocking bilingual human-verify checkpoint (Phases 5-12 precedent)"
    - "Independent map-slot/content-slot components mirroring LLMap/StatPanel's own per-layout placement, replacing a single stacked composition root"

key-files:
  created:
    - .planning/phases/13-add-a-projects-and-partners-tab-to-individual-living-lab-pag/13-EVIDENCE.md
  modified:
    - app/src/components/PartnersProjectsTab.jsx
    - app/src/hooks/usePartnersProjects.js
    - app/src/pages/LLDetail.jsx
    - .planning/phases/13-add-a-projects-and-partners-tab-to-individual-living-lab-pag/13-UI-SPEC.md

decisions:
  - "Zero npm/pip dependencies added across the whole phase (T-13-SC discharged) -- BASE established mechanically as the parent of the first commit touching data/partners_projects.json"
  - "T-13-03 (no raw-HTML sink for authored content) discharged for all phase-13-authored content; one pre-existing, unrelated Phase-10 dangerouslySetInnerHTML match in LLDetail.jsx documented and excluded (static icon glyph, not partner/project data)"
  - "format:check gate recorded as failing on this machine for pre-existing, environment-specific Windows CRLF-checkout drift plus 17 files of pre-existing non-phase-13 Prettier debt -- mechanically proven zero phase-13-attributable defect rather than fabricated as passing"
  - "Map/panel layout bug found during the human's first live Task 3 pass: PartnersMap rendered in the wide content column instead of LLMap's own map-column slot. Fixed by splitting PartnersProjectsTab.jsx into PartnersMapSlot/PartnersPanelSlot and updating all three LLDetail.jsx call sites to mirror LLMap/StatPanel's per-layout slot placement exactly"
  - "Content sign-off: ship as-is -- the seeded one-ZALF-partner-per-slug, zero-projects content ships unchanged; nothing was authored at the checkpoint"

requirements-completed:
  [
    D-01,
    D-02,
    D-03,
    D-04,
    D-05,
    D-06,
    D-07,
    D-08,
    D-09,
    D-10,
    D-11,
    D-12,
    D-13,
    D-14,
    D-15,
    D-16,
    D-17,
    D-18,
  ]

metrics:
  duration: "~3.5 hours across two sessions (Tasks 1-2 + checkpoint dispatch; deviation fix; sign-off + this summary)"
  completed: 2026-08-13
---

# Phase 13 Plan 06: Phase Close-Out — Automated Gate, Decision Evidence, and Human Sign-Off Summary

**Ran every repository-wide automated gate on the final merged tree, proved zero new dependencies and no raw-HTML sinks for phase-13-authored content, recorded a backed verdict for all eighteen locked decisions, fixed a real map-placement layout bug the human found during live verification, and closed the phase on a plain human "approved" with the seeded ZALF-only content shipping as-is.**

## Performance

- **Duration:** ~3.5 hours of active work across two dispatch sessions (Tasks 1-2 plus the initial checkpoint return; a deviation fix requested mid-checkpoint; final sign-off and this summary after human approval)
- **Completed:** 2026-08-13
- **Tasks:** 3/3, plus one mid-checkpoint deviation fix
- **Files modified:** 5 (1 created — `13-EVIDENCE.md`; 4 modified — `PartnersProjectsTab.jsx`, `usePartnersProjects.js`, `LLDetail.jsx`, `13-UI-SPEC.md`)

## Accomplishments

- Ran every repository gate (`lint`, `build`, `check:soil-palette`, full `pytest` suite — 44 passed, `export:report-tokens` parity, `sync.py` idempotency) on the final merged tree; all pass
- Established the phase's `BASE` commit mechanically and proved, with `--exit-code` diffs, zero npm/pip dependency changes (`app/package.json`, `app/package-lock.json`, `data-pipeline/requirements.txt`) across the whole phase — discharges T-13-SC
- Proved `app/src/data/layers.js` and `data/ll_content.json` are byte-for-byte unchanged across the whole phase
- Ran the whole-phase XSS negative grep across every phase-touched `app/src/` file; found and fully investigated one pre-existing, unrelated match (Phase 10's `LLDetail.jsx` `ComparePicker` icon rendering) — confirmed zero phase-13-authored content ever reaches a raw-HTML sink, discharging T-13-03
- Recorded the whole-phase file-list diff: fifteen files match the plan's `<interfaces>` table exactly; seventeen additional files (five plan SUMMARYs, orchestrator tracking commits, and two unrelated human-authored Phase-12 report commits) are all accounted for and explained
- Recorded a backed verdict (met / met with deviation) for all eighteen locked decisions D-01..D-18, each citing a file path, command output, or SUMMARY reference
- Proved all three deferred ideas (project/example location mapping, full CMS, permission workflow) were not built, via mechanical greps/checks
- Recorded the eight discretionary planner decisions, explicitly resolving 13-RESEARCH.md Open Questions 1 (comparison-mode inclusion) and 2 (lat/lng key naming) by name
- **Fixed a real layout bug the human found during live Task 3 verification:** the Partners & Projects map was rendering in the wide content column instead of `LLMap`'s own narrow map-column slot. Split `PartnersProjectsTab.jsx` into two independently-mountable exports (`PartnersMapSlot`, `PartnersPanelSlot`) and updated all three `LLDetail.jsx` layout call sites so the map always renders in `LLMap`'s own slot and the panel always renders in the layout's normal content slot, in `LayoutSplit`, `LayoutStacked`, and `ComparisonColumn`
- Human approved the corrected result on a second live pass (after the orchestrator merged this worktree's commits), confirming all twelve Task 3 verification steps, including the D-12 keyboard-only pass (focus ring, focus-triggered tooltip, blur-close, Enter-to-website) — retiring 13-RESEARCH.md Assumption A1 by name
- Content decision: **ship as-is** — the seeded one-ZALF-partner-per-slug, zero-projects content ships unchanged

## Task Commits

Each task/deviation/sign-off was committed atomically:

1. **Task 1: Full automated gate, whole-phase dependency diff and XSS negative grep** — `59b1298` (test)
2. **Task 2: D-01..D-18 decision evidence table, deferred-scope proof and planner decisions** — `0d6b011` (docs)
3. **Deviation: Render PartnersMap in the same layout slot as LLMap** — `676ba24` (fix)
4. **Task 3: Content sign-off, human verification record** — this plan's final commit (docs)

## Files Created/Modified

- `.planning/phases/13-add-a-projects-and-partners-tab-to-individual-living-lab-pag/13-EVIDENCE.md` — full phase close-out record: `## Automated gate`, `## Decision verdicts`, `## Deferred scope`, `## Planner decisions`, `## Open items`, `## Content sign-off`
- `app/src/components/PartnersProjectsTab.jsx` — revised from one combined composition root to two independently-mountable exports, `PartnersMapSlot({ll, height})` and `PartnersPanelSlot({ll})`
- `app/src/hooks/usePartnersProjects.js` — updated a stale doc comment to describe the hook's two new callers (still module-cached, still exactly one network request)
- `app/src/pages/LLDetail.jsx` — all three layout call sites (`LayoutSplit`, `LayoutStacked`, `ComparisonColumn`) restructured so `PartnersMapSlot` renders in `LLMap`'s own slot and `PartnersPanelSlot` renders in the layout's normal content slot
- `.planning/phases/13-add-a-projects-and-partners-tab-to-individual-living-lab-pag/13-UI-SPEC.md` — "Three `LLDetail.jsx` branch points" and "`PartnersProjectsTab` internal layout" sections revised in place to document the map/panel slot resolution, retaining the superseded stacked-block rationale for historical context

No content/data files were modified by this plan — `data/partners_projects.json` and `app/public/data/partners_projects.json` ship byte-identical to what plan 13-01 authored.

## Decisions Made

- **BASE commit established mechanically** as the parent of the first commit introducing `data/partners_projects.json` (`5a8cfab0...`), making the whole-phase dependency and forbidden-file diffs reproducible by anyone re-running the same one-line command.
- **`format:check` gate limitation accepted, not fabricated as passing.** Windows `core.autocrlf=true` on this machine rewrites every checked-out file to CRLF while committed blobs stay LF; Prettier then flags the CRLF working-tree bytes. Proved conclusively (individual `prettier --write` on every phase-13-owned file produces zero real diff; the one phase-13-touched file with a real diff, `LLMap/index.jsx`, is proven pre-existing debt by diffing against the commit immediately before phase 13 touched it) that zero phase-13-created or phase-13-content-modified file carries a real formatting defect. No repo-wide `.gitattributes`/reformat change was made — out of this plan's declared scope.
- **The one XSS-grep match outside the phase's own components (`LLDetail.jsx`'s pre-existing Phase-10 `dangerouslySetInnerHTML` for a static SVG icon glyph) was investigated to its root commit** (`4b7cc85`, Phase 10) rather than dismissed, confirming it predates the phase and carries zero partner/project-authored content.
- **Map/panel slot fix scoped narrowly to layout structure only** — no content, data, or i18n change; `PartnersMap.jsx`/`PartnersOverviewPanel.jsx` themselves are untouched, only which layout slot each is mounted into changed.
- **13-UI-SPEC.md revised in place, not silently overwritten** — the superseded stacked-block rationale is retained inline as historical context so a future reader can see what changed and why, rather than erasing the record of plan 13-05's original (locked-at-the-time) decision.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug, found via live human verification] Partners & Projects map rendered in the wrong layout slot**

- **Found during:** The human's first live Task 3 verification pass (before any approval)
- **Issue:** Plan 13-05's original `PartnersProjectsTab` composition root stacked `PartnersMap` + `PartnersOverviewPanel` as one block inside the layout's _content_ slot (the same slot `StatPanel`/chart/text occupy). For `LayoutSplit`, that content slot is the wide right/58% column — not the narrow left/42% column `LLMap` normally occupies. The map visually jumped to the right side of the screen for this one tab, inconsistent with every other tab's map placement.
- **Fix:** Split `PartnersProjectsTab.jsx` into `PartnersMapSlot({ll, height})` and `PartnersPanelSlot({ll})`. Updated all three `LLDetail.jsx` layout call sites (`LayoutSplit`, `LayoutStacked`, `ComparisonColumn`) so the map slot and content slot are branched independently, exactly mirroring where `LLMap` and `StatPanel`/chart/text render for every other tab. Both new components call `usePartnersProjects` independently; D-09's "exactly one request" guarantee still holds via the hook's existing module-scoped `cache`/`inflight` dedup.
- **Files modified:** `app/src/components/PartnersProjectsTab.jsx`, `app/src/hooks/usePartnersProjects.js`, `app/src/pages/LLDetail.jsx`, `13-UI-SPEC.md`, `13-EVIDENCE.md`
- **Verification:** `npm run lint`, `npm run build`, and `npx prettier --check` on all three touched JS/JSX files all re-confirmed clean after the fix. Human confirmed the corrected placement on a second live pass across all three layouts, approving without qualification.
- **Commit:** `676ba24`

No other deviations. The `format:check` gate's whole-tree failure (pre-existing, environment-specific CRLF drift affecting 55 files, none of which carry a real phase-13-attributable defect) and the one pre-existing, unrelated `dangerouslySetInnerHTML` match in `LLDetail.jsx`'s `ComparePicker` (Phase 10, static icon glyph, not partner/project content) are documented in full in `13-EVIDENCE.md` but are not phase-13 deviations — both predate this phase and are outside its declared scope.

---

**Total deviations:** 1 auto-fixed (Rule 1, a real layout bug caught by live human verification, not by any automated gate — automated gates cannot detect visual/layout placement).
**Impact on plan:** Scoped narrowly to layout structure; no content, data, schema, or i18n change. Re-verified green after the fix; approved by the human on the corrected result.

## Human Checkpoint (Task 3)

**Round 1 (not approved):** The human found the map/panel layout bug described above during live verification in the primary checkout, before this worktree's Task 1/2 commits had been merged. Reported as a real bug with a clarifying question about the Leaflet dependency (answered by the orchestrator — `leaflet`/`react-leaflet`/`pmtiles` are pre-existing deps `LLMap` already uses, no new stack introduced). No approval given; the deviation fix above was applied in response.

**Round 2 (approved):** After the orchestrator merged this worktree's commits (Task 1, Task 2, and the deviation fix) into `data-pipeline-development`, the human re-verified against the corrected build and responded with a plain "approved" — no issues, no content supplied to author. This is recorded as full approval of all twelve of Task 3's verification steps, including:

- The corrected map placement in all three layouts (split, stacked, comparison)
- The D-12 keyboard-only pass: focus ring visible, tooltip opens on focus (no hover), closes on blur, Enter opens `https://www.zalf.de` in a new tab with the app page unchanged behind it — all four sub-checks passed, retiring 13-RESEARCH.md Assumption A1 by name
- Bilingual verification (English and German tab label, section headings, empty-state copy, marker tooltip/link text)
- Comparison-mode inclusion (13-RESEARCH.md Open Question 1), accepted without qualification
- `13-EVIDENCE.md`'s `## Planner decisions` and `## Open items` sections, accepted without qualification
- Content sign-off: **ship as-is** — no content authored, the seeded ZALF-only data ships unchanged

Full per-step verdicts and the four keyboard sub-checks are recorded in `13-EVIDENCE.md`'s `## Content sign-off` section.

## Verification

- `cd app && npm run lint` — clean, exits 0
- `cd app && npm run build` — succeeds, `PartnersMap-*.js` remains a dedicated lazy chunk (Leaflet stays out of the main bundle)
- `cd app && npx prettier --check` on every file this plan touched (`PartnersProjectsTab.jsx`, `usePartnersProjects.js`, `LLDetail.jsx`, `13-EVIDENCE.md`) — all pass
- `python -m pytest data-pipeline/tests/ -q` — 44 passed, no skips
- Task 3's full `<verify>` chain: `SCHEMA-OK`, `PARITY-OK`, `SIGNOFF-OK` all printed; `data/partners_projects.json` and `app/public/data/partners_projects.json` confirmed byte-identical and unchanged from Task 1's recorded state
- `git status --porcelain -- data/partners_projects.json app/public/data/partners_projects.json` — empty, confirming no content edit was made
- Task 2's evidence-file structural verify (`python -c "..."` checking all D-01..D-18 present, all six required sections present, T-13-SC/T-13-03/Open Question 1/Open Question 2/A1 all named) — prints `OK`

## Known Stubs

None. All five Living Labs ship with an empty `projects` array — this is the human-approved final content state ("ship as-is"), not a stub blocking the plan's goal. `13-EVIDENCE.md`'s `## Content sign-off` and `## Open items` both record this explicitly as a known, accepted state, not a silent omission.

## Threat Flags

None. All STRIDE threats this plan's threat model registered (T-13-SC, T-13-03, T-13-01, T-13-14, T-13-15, T-13-16, T-13-17, T-13-18) are discharged and recorded in `13-EVIDENCE.md`'s `## Automated gate` and `## Content sign-off` sections. No new network endpoint, auth path, file-access pattern, or schema change was introduced beyond what plans 13-01 through 13-05 already registered.

## Self-Check: PASSED

- FOUND: `.planning/phases/13-add-a-projects-and-partners-tab-to-individual-living-lab-pag/13-EVIDENCE.md`
- FOUND: `app/src/components/PartnersProjectsTab.jsx` (exports `PartnersMapSlot`, `PartnersPanelSlot`)
- FOUND: `app/src/pages/LLDetail.jsx` (three call sites updated)
- FOUND commit `59b1298` (Task 1)
- FOUND commit `0d6b011` (Task 2)
- FOUND commit `676ba24` (deviation fix)

---

## Phase 13 Close-Out

This is the final plan in Phase 13 (add a Projects and Partners tab to individual Living Lab pages).
All eighteen locked decisions (D-01..D-18) are met, every automated repository gate passes on the
final merged tree (with the one documented, pre-existing, out-of-scope `format:check` limitation),
and a human has verified the tab end-to-end in both languages, all three layouts, and with the
keyboard alone, approving the content that ships. Phase 13 is complete.

---

_Phase: 13-add-a-projects-and-partners-tab-to-individual-living-lab-pag_
_Completed: 2026-08-13_
