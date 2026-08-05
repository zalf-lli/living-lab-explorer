---
phase: 12-export-a-pdf-of-the-content-for-a-given-living-lab
plan: 02
subsystem: infra
tags: [r, quarto, renv, toolchain, cran]

# Dependency graph
requires:
  - phase: 12 (12-01)
    provides: Phase 12 UI-SPEC and locked D-decisions (D-01 Quarto, D-02 R, D-04 sync.py never renders, D-19 toolchain docs, D-14 locator map basemap)
provides:
  - "data-pipeline/R/_toolchain.py: find_quarto_bin(), find_r_home(), require_toolchain() executable discovery"
  - "data-pipeline/R/README.md: toolchain setup docs, Windows PATH friction point, sync.py-never-renders contract"
  - "CLAUDE.md External CLI deps line naming quarto/R with QUARTO_BIN/R_HOME overrides"
  - ".gitignore renv library/staging exclusions"
  - "data-pipeline/R/renv.lock: 89 CRAN packages pinned (13 direct + transitive deps), all Source=Repository/Repository=CRAN"
  - "data-pipeline/R/.Rprofile + renv/activate.R: self-contained renv project, restorable via renv::restore()"
affects: [12-03, 12-04, 12-05, 12-06, 12-07, 12-08, 12-09]

# Tech tracking
tech-stack:
  added: ["renv 1.2.4 (R dependency pinning)", "maptiles 0.12.0 (cover-page locator map basemap, D-14)"]
  patterns:
    - "External-binary discovery mirrors _sources.py::find_rio_bin(): explicit env-var override (only if it exists on disk) -> shutil.which -> known-good fallback path -> RuntimeError naming the override"
    - "R dependency pinning via renv, self-contained per-project (data-pipeline/R/), parallel to Python's requirements.txt convention"

key-files:
  created:
    - data-pipeline/R/_toolchain.py
    - data-pipeline/R/README.md
    - data-pipeline/R/.Rprofile
    - data-pipeline/R/renv.lock
    - data-pipeline/R/renv/activate.R
    - data-pipeline/R/renv/settings.json
    - data-pipeline/R/renv/.gitignore
  modified:
    - CLAUDE.md
    - .gitignore

key-decisions:
  - "gitignore renv exclusion patterns written WITHOUT a trailing slash (data-pipeline/R/renv/library, not .../library/) because the plan's acceptance criteria run git check-ignore against a path that did not yet exist on disk at Task 1 time (renv hadn't been initialised) -- a trailing-slash directory-only pattern does not match a nonexistent, type-unknown path. Verified correct both before and after Task 3 created the real directory."
  - "renv::init() called with bare=TRUE so the initial lockfile did not eagerly snapshot every already-installed package in the base R library; the target 13 packages were then explicitly installed into the project's private library and captured via renv::snapshot(type=\"all\"), giving an exact, intentional package set rather than an incidental one"
  - "Both renv (v1.2.4) and maptiles (v0.12.0) approved for install by a human at the Task 2 blocking checkpoint after independently verifying CRAN maintainer/license/source-repo facts against the live CRAN pages -- no ggspatial/rosm substitution; installed exactly as researched"

requirements-completed: [D-03, D-19, D-14]

# Metrics
duration: ~1h35m (checkpoint wait included)
completed: 2026-08-05
---

# Phase 12 Plan 02: R/Quarto Toolchain Bootstrap Summary

**`data-pipeline/R/` turned from an empty stub into a working, reproducible renv project: a `_toolchain.py` discovery module with actionable R/Quarto failure errors, and a committed `renv.lock` pinning all 89 CRAN packages (13 direct incl. `renv`/`maptiles`, 76 transitive) the report render needs.**

## Performance

- **Duration:** ~1h35m (2026-08-05T08:24 - 09:59 local, including the blocking human-verify checkpoint wait)
- **Started:** 2026-08-05T08:24:24+02:00 (worktree base checkout)
- **Completed:** 2026-08-05T09:59:19+02:00
- **Tasks:** 3 of 3 (Task 2 was a checkpoint, no code changes)
- **Files modified:** 9 (7 created, 2 modified)

## Accomplishments

- `data-pipeline/R/_toolchain.py` created: `find_quarto_bin()`, `find_r_home()`, `require_toolchain()`,
  structured identically to `data-pipeline/python/_sources.py`'s `find_rio_bin()` precedent (explicit
  candidate path -> `shutil.which` -> `RuntimeError` with an actionable message). Both success and
  both documented failure modes verified live on this machine.
- `data-pipeline/R/README.md` created documenting the toolchain, the Windows PATH friction point (R
  installed at `C:\Program Files\R\R-4.5.0` but not on PATH; two fixes: `R_HOME` or PATH edit), and
  the D-04 contract that `sync.py` never invokes Quarto — reports render manually via
  `render_reports.py`.
- `CLAUDE.md`'s External CLI deps bullet extended to name `quarto`/`R` alongside `pmtiles`/`rio`, with
  `QUARTO_BIN`/`R_HOME` override documentation; Quick Start's Pipeline block gained a
  `python R/render_reports.py` line.
- `.gitignore` extended to ignore renv's local library/staging directories while keeping `renv.lock`,
  `.Rprofile`, and `renv/activate.R` trackable.
- Human checkpoint (Task 2) cleared: both `renv` (v1.2.4) and `maptiles` (v0.12.0) independently
  verified on their live CRAN pages and approved for install exactly as researched, no substitution.
- `data-pipeline/R/` initialised as a self-contained `renv` project (`renv::init(bare = TRUE)`);
  all 13 required packages (`renv`, `maptiles`, `ggplot2`, `sf`, `terra`, `tidyterra`, `jsonlite`,
  `yaml`, `patchwork`, `scales`, `ggtext`, `knitr`, `rmarkdown`) installed into the project's private
  library and captured by `renv::snapshot(type = "all")` — 89 packages total in the committed
  `renv.lock`, every one `Source: Repository` / `Repository: CRAN`.

## Task Commits

Each task was committed atomically:

1. **Task 1: R/Quarto discovery module plus D-19 documentation** - `f0a70bc` (feat)
2. **Task 2: Human legitimacy check for the two new CRAN packages** - checkpoint, no commit (approved "as specified")
3. **Task 3: Initialise renv and pin the report toolchain's package versions** - `f94d64e` (feat)

**Interim state commit (superseded by this SUMMARY):** `ac896b9` (docs — persisted progress across the checkpoint wait in worktree mode; this file replaces it)

**Plan metadata:** this commit (docs: complete plan)

## Files Created/Modified

- `data-pipeline/R/_toolchain.py` - R/Quarto executable discovery with env-var overrides and actionable `RuntimeError`s
- `data-pipeline/R/README.md` - Toolchain setup, Windows PATH friction point, sync.py-never-renders contract
- `data-pipeline/R/.Rprofile` - Sources `renv/activate.R`, activating the project's private library on R startup
- `data-pipeline/R/renv.lock` - Committed lockfile pinning all 89 packages (13 required + transitive deps), all from CRAN
- `data-pipeline/R/renv/activate.R` - renv's project-activation bootstrap script (tracked, not ignored)
- `data-pipeline/R/renv/settings.json` - renv project settings
- `data-pipeline/R/renv/.gitignore` - renv's own nested ignore rules for `library/`, `local/`, `staging/`, etc.
- `CLAUDE.md` - External CLI deps bullet + Quick Start Pipeline block updated
- `.gitignore` - renv library/staging exclusions added, `renv.lock`/`.Rprofile`/`renv/activate.R` deliberately left trackable

## Decisions Made

- Wrote the `.gitignore` patterns for renv's library/staging directories without a trailing slash
  (`data-pipeline/R/renv/library`, not `.../library/`). The plan's acceptance criteria assert
  `git check-ignore -q data-pipeline/R/renv/library` exits 0 — at Task 1 time that path did not yet
  exist on disk (Task 3 hadn't run `renv::init()` yet). A trailing-slash pattern is directory-only
  and Git will not match it against a nonexistent, type-unknown path, so the check would have falsely
  reported "not ignored." The no-trailing-slash form matches regardless of eventual file/directory
  type and was re-verified correct after Task 3 created the real `renv/library/` directory.
- Used `renv::init(bare = TRUE)` rather than the default dependency-scanning init, since
  `data-pipeline/R/` contained no R source files yet (they arrive in plans 12-06 through 12-09) — a
  non-bare init would have produced a near-empty, meaningless initial lockfile. The 13 required
  packages were then installed explicitly and captured via `renv::snapshot(type = "all")` per the
  plan's instruction, so the lockfile is deliberate rather than incidental.
- Both CRAN packages were approved and installed exactly as researched (no `ggspatial`/`rosm`
  substitution) after the human checkpoint verification.

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
  Phase 8): `"/c/lcvenv/Scripts/python.exe" -m pytest data-pipeline/tests/ -q` -> `36 passed` (both
  before and after Task 3).
- **Files modified:** none (test-runner selection only, no code changed)
- **Verification:** 36/36 passing at both check points, matching the pre-plan count.
- **Committed in:** N/A (no file change; documented here per Rule 3 scope)

**2. [Rule 3 - Blocking] Installed R packages via direct `Rscript.exe`/`renv` R-side calls rather than a Python wrapper**

- **Found during:** Task 3
- **Issue:** The plan's action text describes the intended `renv::init()`/`renv::install()`/
  `renv::snapshot()` sequence in prose but doesn't hand over a ready-made script; `renv::install()`
  called with an explicit `project=` argument (but without first `renv::load()`-ing/activating that
  project) installs into the *global* user library, not the project's private renv library — the
  first attempt did exactly this and had to be corrected.
- **Fix:** Re-ran with `renv::load(project_dir)` first (activating the project's private library via
  `.libPaths()`), then `renv::install()`/`renv::snapshot()` against the now-active project. Verified
  by listing the project's `renv/library/windows/R-4.5/x86_64-w64-mingw32/` directory before and
  after — the corrected run installed all 13 requested packages plus transitive deps (89 total)
  into the project-private library, not the global one.
- **Files modified:** `data-pipeline/R/renv.lock` (final, correct snapshot only — the mis-targeted
  first install left no lockfile since snapshot was never run against it)
- **Verification:** the plan's exact verify command (`renv.lock` contains all 13 required packages
  with versions, `R` version `4.5.0`) passes; `maptiles`'s `Source`/`Repository` fields confirmed
  `Repository`/`CRAN`; all 89 packages in the lockfile are `Source: Repository` (spot-checked via a
  full scan, not just `maptiles`).
- **Committed in:** `f94d64e` (Task 3 commit — only the corrected, final state was ever committed)

---

**Total deviations:** 2 auto-fixed (both Rule 3, both environment/tooling correctness issues; no
scope creep, no unplanned files)
**Impact on plan:** None on the plan's deliverables — both fixes were needed to make the plan's own
acceptance criteria actually pass, not additions beyond plan scope.

## Issues Encountered

- The `renv::install()` background R process for the 13-package + transitive-dependency set took
  ~14 minutes wall-clock (`stringi` built from source, ~14m of that), all in a background shell
  task; no failures, just slow (source compile, not a network or install error).

## User Setup Required

None — no external service configuration required. A fresh machine setup is: install R >= 4.5 and
Quarto >= 1.4 (see `data-pipeline/R/README.md`), set `R_HOME`/`QUARTO_BIN` if either isn't on PATH,
then run `renv::restore()` inside `data-pipeline/R/` to reproduce the exact pinned package set from
`renv.lock`.

## Next Phase Readiness

- Both interfaces the plan promised (`data-pipeline/R/_toolchain.py`'s `find_quarto_bin()`,
  `find_r_home()`, `require_toolchain()`) exist, are independently verified against both success and
  both documented failure modes, and match the exact function signatures plan 12-05's
  `render_reports.py` will import.
- `data-pipeline/R/renv.lock` is committed with all 89 packages pinned; `renv::restore()` on a fresh
  machine reproduces the exact library with no manual `install.packages()` follow-up.
- Nothing was rendered — per the plan's explicit scope, plan 12-05 owns the first real render. No R
  source files (`.qmd`, `.R`) exist in `data-pipeline/R/` yet; they arrive in plans 12-06 through
  12-09.
- All of this plan's `<success_criteria>` are met: discovery module + actionable errors, `CLAUDE.md`
  D-19 line, README setup docs, human-verified CRAN packages, committed 13-package-minimum lockfile,
  and `.gitignore` correctly split between the tracked renv artifacts and the ignored local library.

---
*Phase: 12-export-a-pdf-of-the-content-for-a-given-living-lab*
*Completed: 2026-08-05*
