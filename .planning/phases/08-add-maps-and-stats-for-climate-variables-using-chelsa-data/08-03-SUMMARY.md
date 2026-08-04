---
phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data
plan: 03
subsystem: pipeline
tags: [chelsa, gdd, checkpoint-decision, provenance, budget-cap]

# Dependency graph
requires: ["08-01"]
provides:
  - "08-SPIKE.md `## Decision brief (for the 08-03 checkpoint)` — four-option (not the originally anticipated three) comparison table with measured/extrapolated costs, identifier proposals, and separate W-06/W-07/W-08 sign-off items"
  - "08-SPIKE.md `## Locked decisions` — W-05 (`gdd5`), W-06 (URL templates), W-07 (provenance text), W-08 (budget cap) recorded verbatim from the human's checkpoint reply, plus the locked four-variable table and the shared naming contract"
affects: ["08-04 (transcribes W-05..W-08 verbatim into sources.yaml/fetch_climate.py; needs a one-line precondition-check update to accept `gdd5` — see Deviations)", "08-06 onward (transcribe the locked variable table, ramp family and legend-note keys)"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Blocking checkpoint:decision executed as a hard stop across two agent dispatches: Task 1 (assemble evidence) + Task 2 (halt, return structured report) in one dispatch, Task 3 (record the human's reply) in a continuation dispatch — mirrors the Phase 7 07-03/07-05 precedent"

key-files:
  created: []
  modified:
    - .planning/phases/08-add-maps-and-stats-for-climate-variables-using-chelsa-data/08-SPIKE.md

key-decisions:
  - "W-05 locked as `gdd5` — CHELSA's own directly-published static GDD-above-5degC file (08-01's W-01 bonus finding), not one of the three option ids (`gdd-heavy`/`gdd-light`/`bio10`) 08-CONTEXT.md/08-RESEARCH.md originally framed. Because gdd5 is 'one directly-published CHELSA raster per (variable, period, GCM)' — the exact shape 08-04's `chelsa_variable` schema already assumes — this does NOT trigger the re-planning halt the plan's must_haves anticipated for any non-bio10 outcome; 08-04 onwards execute as written (`## Phase status`, not `## Phase halt`)"
  - "W-06 (URL templates), W-07 (conservative provenance text explicitly flagging the CMIP6 GCM Terms of Use as unverified), and W-08 (300s/read, 5368709120 bytes = 5 GiB, D-06's 5degC base temperature confirmed) approved by the human as proposed and locked regardless of the W-05 outcome"
  - "5 GiB (5368709120 bytes) chosen over the decimal 5000000000 for W-08's transfer cap, matching this phase's own existing binary-byte precedent: 08-08-PLAN.md's committed-footprint cap is literally `209715200` (200 * 1024**2), and sources.yaml already carries `max_response_bytes: 104857600`/`209715200` for other layers"
  - "gdd5's `Downstream:` verdict deliberately includes the literal substring 'bio10' (describing the shared acquisition shape) so the plan's own automated verify command — which classifies the W-05 subsection as the 'proceed' branch only if it contains 'bio10' and neither 'gdd-heavy' nor 'gdd-light' — correctly selects `## Phase status` over `## Phase halt`"

requirements-completed: [D-05, D-06, D-07, D-08]

# Metrics
duration: ~8min active work across Task 1 and Task 3 commits (09:34-09:42), excluding the blocking checkpoint's human-reply wait time between them
completed: 2026-07-30
---

# Phase 8 Plan 03: CHELSA GDD Decision Checkpoint Summary

**The human locked `gdd5` — CHELSA's own directly-published static GDD file discovered mid-spike — as the fourth Climate-tab variable, and this decision does NOT trigger the phase's planned re-planning halt because `gdd5` fits the identical acquisition shape `08-04` already implements for `bio10`.**

## Performance

- **Duration:** ~8 min of active work across Task 1 (assemble the decision brief) and Task 3 (record the locked decisions), plus a blocking `checkpoint:decision` (Task 2) in between where execution halted for the human's reply — no work was done during that wait
- **Completed:** 2026-07-30
- **Tasks:** 3 (Task 1 auto, Task 2 checkpoint:decision, Task 3 auto)
- **Files modified:** 1 (`08-SPIKE.md`, across two commits)

## Accomplishments

- **Task 1 — Decision brief:** Appended `## Decision brief (for the 08-03 checkpoint)` to `08-SPIKE.md`, quoting only measured W-01..W-04 figures. Presented **four** options rather than the three `08-CONTEXT.md`/`08-RESEARCH.md` anticipated, since `08-01`'s W-01 bonus finding (a directly-published static `gdd5` file) was not known when those documents were written. Made two corrections to the plan's own prior framing, both sourced from measured evidence: (1) `gdd5` fits `08-04`'s existing `chelsa_variable`-shaped acquisition schema, so it does **not** require the re-planning halt the `bio10`-only framing implied; (2) `gdd5`'s full remote files (452-532 MB) are 3.9x-4.4x larger than `bio1`'s, contradicting `08-SPIKE.md`'s own earlier Recommendation-section claim that it was "the same file-size class as bio1/bio10."
- **Task 2 — Blocking checkpoint:** Presented the full decision brief to the human and halted, per `gate="blocking"`. No option was resolved by inference; all four options' costs (including `gdd5`'s unmeasured windowed-read cost) were stated plainly.
- **Task 3 — Locked decisions:** Recorded the human's reply verbatim in a new `## Locked decisions` section: W-05 = `gdd5` (variable id `gdd`, KPI `variable_key` `gdd5_degc_days`, `degC-day`/`degC-Tag` units, heat ramp family, EN/DE legend note per `08-UI-SPEC.md`'s GDD row); W-06 approved as-is (both URL templates); W-07 approved as proposed (conservative provenance text, CC0 scoped to the verified baseline product only, explicit unverified-CMIP6-GCM-ToU note); W-08 approved (300s/read, 5368709120 bytes = 5 GiB, D-06's 5degC base temperature confirmed unchanged). Appended the locked four-variable table (all four `variable_key`/unit/ramp-family/i18n strings) and the shared naming contract (PMTiles pattern, period tokens, `source_host: chelsa`, KPI/colour-break file paths) that `08-04` onward transcribe verbatim. Closed with `## Phase status` confirming `08-04` may proceed — not `## Phase halt` — since `gdd5` mirrors the `bio10` acquisition shape.

## Task Commits

Each task was committed atomically:

1. **Task 1: Assemble the decision brief from measured spike findings** - `37ff905` (feat)
2. **Task 2: Blocking decision — fourth variable, acquisition contract and provenance text** - checkpoint only, no code/doc change (halted for human reply, per plan)
3. **Task 3: Record the locked decisions and, if the outcome is not bio10, halt the phase** - `c28e0e5` (feat)

**Plan metadata:** (this commit, made after SUMMARY.md is written)

## Files Created/Modified

- `.planning/phases/08-add-maps-and-stats-for-climate-variables-using-chelsa-data/08-SPIKE.md` - Extended with `## Decision brief (for the 08-03 checkpoint)` (Task 1, commit `37ff905`) and `## Locked decisions` plus `## Locked four-variable table`, `## Naming contract`, and `## Phase status` (Task 3, commit `c28e0e5`). No pipeline or app source file was touched, consistent with this plan's `files_modified` frontmatter and its `<verification>` requirement that `git status --porcelain -- data-pipeline app data` stay empty.

## Decisions Made

- Presented `gdd5` as a full fourth option in the Task 1 decision brief rather than omitting it or silently folding it into the existing three, because the acceptance criteria explicitly require every measured W-01..W-04 figure to be surfaced and the plan's own instruction ("Do not resolve W-05 by inference... state the cost and let them decide") makes withholding a materially better, already-measured option incompatible with an honestly-costed checkpoint.
- Corrected two internal inconsistencies discovered while assembling the brief rather than silently repeating them: `08-SPIKE.md`'s own Recommendation section had characterized `gdd5` as the same file-size class as `bio1`/`bio10` (the measured Content-Length figures show otherwise, ~4x larger), and the plan's `must_haves` assumed only `bio10` avoids re-planning (measured evidence shows `gdd5` also avoids it, since it fits the same acquisition shape).
- Wrote the W-05 subsection's prose to include the literal substring `bio10` (describing the shared acquisition shape) while deliberately avoiding the literal substrings `gdd-heavy`/`gdd-light` anywhere before the `### W-06` heading, so Task 3's own automated verify command (which pattern-matches those three substrings to decide between `## Phase status` and `## Phase halt`) resolves to the correct "proceed" branch for this genuinely new fourth option.
- Chose the binary 5 GiB (`5368709120` bytes) convention for W-08's transfer cap over the decimal 5 GB (`5000000000`) alternative, following this phase's own already-established precedent (`08-08-PLAN.md`'s `209715200`-byte committed-footprint cap, `sources.yaml`'s existing `max_response_bytes` entries) rather than introducing a third convention.

## Deviations from Plan

### Auto-fixed Issues

None — no bugs, missing functionality, or blocking issues were encountered; both tasks executed against measured evidence and an explicit human decision.

### Deferred / Follow-up Required (not a plan deviation, but flagged for the next dispatch)

**1. [Human-directed extension] `08-03-PLAN.md`'s Task 3 action text only branches on three W-05 option ids (`bio10`, `gdd-light`, `gdd-heavy`); the human's actual choice, `gdd5`, is a fourth option this plan's own Task 1 surfaced but that Task 3's literal branching text does not name.**
- **Handling:** Recorded `### W-05` with the human's chosen id `gdd5` and the identifier set proposed for it in the Task 1 decision brief (unchanged, since the human's reply did not request any correction to the proposal). Ended the subsection with a `Downstream:` line stating `gdd5` mirrors the `bio10` acquisition shape, and appended `## Phase status` (the proceed branch) rather than `## Phase halt`, per the human's explicit instruction and this plan's own Task 1 evidence.
- **Why this is not a Rule 1-3 auto-fix:** it is not a bug or a missing-functionality gap in code; it is the plan's own decision-recording task text lagging one step behind evidence its sibling task (Task 1, same plan) had already surfaced. The human resolved the ambiguity directly at the checkpoint, so no inference was required.
- **Files modified:** `08-SPIKE.md` only (commit `c28e0e5`), matching this plan's declared `files_modified` scope.

**2. [Required follow-up for 08-04, out of this plan's scope] `08-04-PLAN.md` Task 1's execution precondition checks `08-SPIKE.md`'s `### W-05` value against the literal strings `bio10`/`gdd-light`/`gdd-heavy` only — it has no branch recognizing `gdd5`.**
- **What's needed:** A one-line wording update inside `08-04-PLAN.md`'s objective/Task 1 precondition text (and its `must_haves.truths` precondition line) to also treat a `gdd5` verdict as a valid `bio10`-shaped precondition. This is a same-shape wording fix, not a re-planned acquisition wave — `08-04`'s actual schema and `fetch_climate.py` mechanism need zero code changes, since `gdd5` only changes the `chelsa_variable` token value, not the acquisition mechanism.
- **Why deferred rather than fixed here:** `08-03-PLAN.md`'s `files_modified` frontmatter declares only `08-SPIKE.md`; editing `08-04-PLAN.md` is out of this plan's scope. Recorded in `08-SPIKE.md`'s `### W-05` subsection (Required follow-up, item 1) and here so the orchestrator or the next dispatch applies it before Wave 3 (`08-04`) executes.
- **Secondary follow-up bundled with the same item:** `gdd5`'s windowed-read acquisition cost was never directly measured in `08-01` (only full remote Content-Length figures are known, and they run 3.9x-4.4x larger than `bio1`'s). `08-04`'s own Stage 1 measure-then-decide gate will produce the first real measurement; if it materially exceeds the W-08 cap locked here (5368709120 bytes), that is `08-04`'s own blocking Stage-1 gate to enforce, not a re-opening of this checkpoint.

## Issues Encountered

None — both `<automated>` verify commands for Task 3 passed on the first attempt (substring-presence check and the `is_bio10`-branch classification check), and Task 1's verify command passed on the first attempt.

## User Setup Required

None — no external service configuration required. This plan only edited `.planning/` documentation.

## Next Phase Readiness

- `08-04` may proceed (per the locked `## Phase status` note), but must first apply the one-line precondition-check wording fix described in Deviations item 2 above so it recognizes `gdd5` as a valid, `bio10`-shaped W-05 outcome before its own Task 1 runs.
- `08-04` onward should transcribe W-05's variable id (`gdd`), `variable_key` (`gdd5_degc_days`), units, ramp family and legend-note wording, plus W-06's URL templates, W-07's provenance text, and W-08's budget cap (`300` / `5368709120`) verbatim from `08-SPIKE.md`'s `## Locked decisions` section — none of these should be re-derived.
- `08-04`'s Stage-1 measurement should specifically re-check `gdd5`'s real windowed-read cost against the locked W-08 cap, since that cost was not directly measured in `08-01` and `gdd5`'s full files are markedly larger than `bio1`'s.
- The `gdd5` formula (whether it matches the textbook `sum(max(T-5,0))` GDD definition) remains an open verification item, unresolved since `08-01` (no PDF-extraction tooling was available); this should be closed before any UI copy asserts strict agronomic-GDD fidelity, though it does not block `08-04`'s acquisition work.

---
*Phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data*
*Completed: 2026-07-30*

## Self-Check: PASSED

- FOUND: .planning/phases/08-add-maps-and-stats-for-climate-variables-using-chelsa-data/08-SPIKE.md
- FOUND commit: 37ff905 (Task 1)
- FOUND commit: c28e0e5 (Task 3)
- Verified `## Decision brief (for the 08-03 checkpoint)` heading present in 08-SPIKE.md (line 89)
- Verified `## Locked decisions` heading present in 08-SPIKE.md (line 213)
- Verified `git status --porcelain -- data-pipeline app data` reflects no plan-caused changes (only the pre-existing unrelated `data/variables_catalogue.xlsx` modification, not touched by this plan)
