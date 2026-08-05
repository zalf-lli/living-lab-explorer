---
phase: 12-export-a-pdf-of-the-content-for-a-given-living-lab
plan: 02
subsystem: infra
tags: [r, quarto, renv, toolchain, cran]

# Dependency graph
requires:
  - phase: 12 (12-01)
    provides: Phase 12 UI-SPEC and locked D-decisions (D-01 Quarto, D-02 R, D-04 sync.py never renders, D-19 toolchain docs)
provides:
  - "data-pipeline/R/_toolchain.py: find_quarto_bin(), find_r_home(), require_toolchain() executable discovery"
  - "data-pipeline/R/README.md: toolchain setup docs, Windows PATH friction point, sync.py-never-renders contract"
  - "CLAUDE.md External CLI deps line naming quarto/R with QUARTO_BIN/R_HOME overrides"
  - ".gitignore renv library/staging exclusions"
affects: [12-03, 12-04, 12-05, 12-06, 12-07, 12-08, 12-09]

# Tech tracking
tech-stack:
  added: []  # Task 3 (renv init + CRAN package pins) is blocked on the Task 2 human checkpoint below
  patterns:
    - "External-binary discovery mirrors _sources.py::find_rio_bin(): explicit env-var override (only if it exists on disk) -> shutil.which -> known-good fallback path -> RuntimeError naming the override"

key-files:
  created:
    - data-pipeline/R/_toolchain.py
    - data-pipeline/R/README.md
  modified:
    - CLAUDE.md
    - .gitignore

key-decisions:
  - "gitignore renv exclusion patterns written WITHOUT a trailing slash (data-pipeline/R/renv/library, not .../library/) because the plan's acceptance criteria run git check-ignore against a path that does not yet exist on disk (renv hasn't been initialised) -- a trailing-slash directory-only pattern does not match a nonexistent path with unknown type"

requirements-completed: []  # D-03/D-19/D-14 partially addressed by Task 1 only; not marking complete until Task 3 (the renv.lock artifact) lands post-checkpoint

# Metrics
duration: partial (checkpoint reached)
completed: in-progress
---

# Phase 12 Plan 02: R/Quarto Toolchain Bootstrap Summary (PARTIAL — blocked at Task 2 checkpoint)

**R/Quarto executable-discovery module and D-19 toolchain docs shipped; CRAN package install for `renv`/`maptiles` blocked on a mandatory human legitimacy check (Task 2) before Task 3 can run.**

## Status: IN PROGRESS — awaiting human checkpoint response

This plan is `autonomous: false` and Task 2 is a `type="checkpoint:human-verify" gate="blocking-human"`
task (CRAN package legitimacy verification for `renv` and `maptiles`, per the threat model's T-12-SC
mitigation). Per the checkpoint protocol, execution stopped at Task 2 and this SUMMARY is being
committed now (worktree execution requires persisting progress before the orchestrator removes the
worktree) so a fresh continuation agent can resume from here after the human responds.

**Task 3 (renv init, CRAN package pinning) has NOT run.** `data-pipeline/R/.Rprofile` and
`data-pipeline/R/renv.lock` do not exist yet.

## Performance

- **Tasks completed:** 1 of 3
- **Files modified:** 4 (2 created, 2 modified)

## Accomplishments

- `data-pipeline/R/_toolchain.py` created: `find_quarto_bin()`, `find_r_home()`,
  `require_toolchain()`, structured identically to `data-pipeline/python/_sources.py`'s
  `find_rio_bin()` precedent (explicit candidate path -> `shutil.which` -> `RuntimeError` with an
  actionable message).
- `data-pipeline/R/README.md` created documenting the toolchain, the Windows PATH friction point
  (R installed but not on PATH; two fixes: `R_HOME` or PATH edit), and the D-04 contract that
  `sync.py` never invokes Quarto — reports render manually via `render_reports.py`.
- `CLAUDE.md`'s External CLI deps bullet extended to name `quarto`/`R` alongside `pmtiles`/`rio`,
  with `QUARTO_BIN`/`R_HOME` override documentation; Quick Start's Pipeline block gained a
  `python R/render_reports.py` line.
- `.gitignore` extended to ignore renv's local library/staging directories while keeping
  `renv.lock`, `.Rprofile`, and `renv/activate.R` trackable once Task 3 creates them.

## Task Commits

1. **Task 1: R/Quarto discovery module plus D-19 documentation** - `f0a70bc` (feat)

**Task 2: Human legitimacy check for the two new CRAN packages** - BLOCKED, awaiting response (checkpoint, no commit)

**Task 3: Initialise renv and pin the report toolchain's package versions** - NOT STARTED (depends on Task 2)

## Files Created/Modified

- `data-pipeline/R/_toolchain.py` - R/Quarto executable discovery with env-var overrides and actionable `RuntimeError`s
- `data-pipeline/R/README.md` - Toolchain setup, Windows PATH friction point, sync.py-never-renders contract
- `CLAUDE.md` - External CLI deps bullet + Quick Start Pipeline block updated
- `.gitignore` - renv library/staging exclusions added, `renv.lock`/`.Rprofile`/`renv/activate.R` deliberately left trackable

## Decisions Made

- Wrote the new `.gitignore` patterns for renv's library/staging directories without a trailing
  slash. The plan's own acceptance criteria assert `git check-ignore -q data-pipeline/R/renv/library`
  exits 0 — but at Task 1 time that path does not exist on disk yet (Task 3 hasn't run `renv::init()`).
  A trailing-slash (`.../library/`) pattern is directory-only and Git will not match it against a
  nonexistent, type-unknown path, so the check would falsely report "not ignored." Removing the
  trailing slash makes the pattern match regardless of eventual file/directory type, satisfying the
  acceptance criterion both now and once the real `renv/library/` directory exists post-Task-3.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Ran pipeline test suite with the correct interpreter**

- **Found during:** Task 1 verification (the plan's overall `<verification>` block requires
  `python -m pytest data-pipeline/tests/ -q` to still pass at its pre-plan count)
- **Issue:** The `python` resolved on this worktree's shell `PATH` is the Windows Store Python 3.13
  (`AppData/Local/Microsoft/WindowsApps/...`), which has none of `data-pipeline/requirements.txt`
  installed (`ModuleNotFoundError: No module named 'rasterio'` in an unrelated file,
  `fetch_climate.py`). This is a pre-existing environment/interpreter-selection condition, not
  caused by anything in this plan's files (only `data-pipeline/R/`, `CLAUDE.md`, `.gitignore`
  touched — no Python pipeline files modified).
- **Fix:** Re-ran the suite with the project's actual pinned-dependency venv at `C:\lcvenv`
  (documented in `STATE.md` as the short-path venv used for the same OneDrive-`MAX_PATH` reason in
  Phase 8): `"/c/lcvenv/Scripts/python.exe" -m pytest data-pipeline/tests/ -q` -> `36 passed`.
- **Files modified:** none (test-runner selection only, no code changed)
- **Verification:** 36/36 passing, matching the pre-plan count; the `_toolchain.py` module import
  and `require_toolchain()` verify command were also re-confirmed against the same venv.
- **Committed in:** N/A (no file change; documented here per Rule 3 scope)

---

**Total deviations:** 1 auto-fixed (1 blocking, environment-only, no tracked files changed)
**Impact on plan:** None — Task 1's actual deliverables are unaffected; this only affected which
interpreter ran the verification command.

## Issues Encountered

None beyond the interpreter-selection issue documented above.

## Checkpoint: Task 2 — Human legitimacy check for `renv` and `maptiles`

**Status:** Awaiting human response. Nothing has been installed. See `12-02-PLAN.md` Task 2 for the
full verification steps (CRAN package pages for `renv` v1.2.4+ and `maptiles` v0.12.0+, maintainer,
license, and GitHub-repo cross-checks) and the `resume-signal` options: `"approved"`,
`"approved with ggspatial"`, or a description of what did not match.

Task 3 is fully blocked on this checkpoint's outcome and has not been started.

## Next Phase Readiness

- Task 1's discovery module and documentation are complete, committed, and independently verified
  (both success and both failure-mode acceptance criteria pass; `36/36` pytest; gitignore/CLAUDE.md
  grep checks all pass).
- Task 3 cannot proceed until a human responds to the Task 2 checkpoint. If approved as-is,
  Task 3 runs `renv::init()` + installs/pins `renv`, `maptiles`, `ggplot2`, `sf`, `terra`,
  `tidyterra`, `jsonlite`, `yaml`, `patchwork`, `scales`, `ggtext`, `knitr`, `rmarkdown` via
  `renv::snapshot(type = "all")`. If "approved with ggspatial", substitute `ggspatial`+`rosm` for
  `maptiles` throughout Task 3 and record the substitution here for plan 12-08 to pick up.
- This SUMMARY will be updated (or superseded) once Task 3 completes and the plan reaches its
  `<success_criteria>` in full.

---
*Phase: 12-export-a-pdf-of-the-content-for-a-given-living-lab*
*Status: PARTIAL — 1/3 tasks complete, blocked at Task 2 checkpoint*
