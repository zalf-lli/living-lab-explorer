---
phase: 12-export-a-pdf-of-the-content-for-a-given-living-lab
plan: 06
subsystem: report-generation (R/ggplot2 shared foundation)
tags: [r, ggplot2, quarto-report, theming, data-accessors]
requires:
  - data/report_tokens.json (plan 12-04)
  - app/public/data/ll_metadata.json (existing pipeline output)
  - data/ll_boundaries.geojson (existing pipeline output)
  - data-pipeline/R/renv.lock (plan 12-02)
provides:
  - data-pipeline/R/theme_llexplorer.R (ll_repo_root, ll_tokens, ll_meta, ll_lab, ll_str,
    ll_brand, ll_boundary, theme_ll_base, theme_ll_map, ll_legend_df,
    ll_discrete_map_scale, LL_TAB_ORDER, LL_TAB_CHART_LAYER, LL_FIG)
  - data-pipeline/R/tests/test_theme_llexplorer.R (runnable Rscript gate)
  - data-pipeline/R/README.md ## Verification section (4-gate index for the phase)
affects:
  - plans 12-07, 12-08, 12-09 (build directly against these function signatures)
tech-stack:
  added: []
  patterns:
    - "Lift-and-copy R module: plain ll_-prefixed functions, one project-specific
      input (data/report_tokens.json), no side effects at source time"
    - "Module-local cache (new.env()) for expensive JSON/GeoJSON parses"
    - "Own-source-file resolution captured eagerly at source() time (sys.frames()
      only exposes ofile while source() is still on the call stack), not lazily"
    - "stop()-on-missing-data discipline for every accessor (T-12-28)"
key-files:
  created:
    - data-pipeline/R/theme_llexplorer.R
    - data-pipeline/R/tests/test_theme_llexplorer.R
  modified:
    - data-pipeline/R/README.md
decisions:
  - "ll_repo_root()'s own-file-path detection must be captured once at source
    time and cached, not re-derived lazily inside a later function call --
    sys.frames() loses the source() frame's ofile the moment source() returns."
  - "Font resolution tries systemfonts::match_fonts() first (current API),
    falls back to the deprecated match_font() only if match_fonts is absent,
    and always degrades to 'sans' rather than raising -- systemfonts itself is
    not pinned in renv.lock, so this path must tolerate its complete absence too."
  - "palettes$landscape has 8 entries in the real committed data/report_tokens.json,
    not the 9 the plan's Task 3 text described -- verified by direct read and used
    as the authoritative figure in the test gate, per Task 1's own read_first
    instruction to trust the real emitted file over the plan's interface block."
metrics:
  duration: ~45m
  completed: 2026-08-05
---

# Phase 12 Plan 06: R theming/accessor foundation Summary

One `data-pipeline/R/theme_llexplorer.R` module giving every later report plan branded
ggplot2 themes, palette/string/brand accessors and a boundary loader — all fourteen
interface-block exports, each `stop()`-ing loudly on missing data instead of ever silently
returning an empty string or blank geometry into a printed PDF.

## What Was Built

**Task 1 — Data accessors, brand lookup and the string resolver** (`88588a4`)

`ll_repo_root()` resolves from `LL_REPO_ROOT` (set by `render_reports.py` in plan 12-05, not
yet merged into this wave) or by walking up from this file's own on-disk location until a
directory containing both `data/` and `app/` is found — never from the working directory,
since Quarto changes it during render. `ll_tokens()`/`ll_meta()` parse and cache
`data/report_tokens.json` and `app/public/data/ll_metadata.json` in a module-local
environment. `ll_lab()`/`ll_brand()`/`ll_str()`/`ll_boundary()` all `stop()` on bad input
(unknown slug, unknown string key, unsupported language, empty boundary result) rather than
returning `NULL` or an empty string. `LL_TAB_ORDER`, `LL_TAB_CHART_LAYER` and `LL_FIG` are
defined per the interface block, cross-checked live against `app/src/data/layers.js`'s
`LAYERS` array order and `data-pipeline/sources/sources.yaml`'s `chart_pattern` keys.

**Task 2 — Branded ggplot themes and shared map legend helper** (`1abca9f`)

`theme_ll_base()`/`theme_ll_map()` build on `theme_minimal()`, reading colours from
`ll_tokens()$theme` and font family from `ll_tokens()$font` (resolved via
`.ll_resolve_font_family()`, which degrades to `"sans"` whenever the requested family cannot
be confirmed on the render machine — never aborts). `theme_ll_map()` strips all axis
chrome, gridlines and panel border, and sets a small right-side legend. `ll_legend_df()`
normalizes either a `data.frame(label, color)` or a named colour vector into one
order-preserving shape. `ll_discrete_map_scale()` builds a `scale_fill_manual()` with
explicit `limits`/`breaks` so every legend row stays visible even when a class is absent
from one Living Lab's extent (D-13's correctness requirement) — verified live that the
returned scale's `$palette(3)` preserves input colour order.

**Task 3 — A runnable Rscript gate over every export** (`c462eb4`)

`data-pipeline/R/tests/test_theme_llexplorer.R` exercises every accessor against the real
committed data for all five Living Labs (both languages), all three negative failure modes,
and the palette entry-count bridge to `report_tokens.json`. No unit-test framework
dependency (matches `app/scripts/check_soil_palette.mjs`'s standalone-gate shape: descriptive
per-case messages, one summary line per subject, `OK` on success, non-zero exit on failure).
Live-verified the gate actually catches breakage: temporarily renamed
`report.documentTitle` in `data/report_tokens.json`, confirmed the gate failed with 10
messages each naming the exact key, then restored the file and re-confirmed a clean pass.
`data-pipeline/R/README.md` gained a `## Verification` section indexing all four phase gates
(this plan's real one, plus the three arriving in 12-07/12-08/12-09), so those three
parallel sibling plans do not each have to edit the same README section.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - blocking] `data-pipeline/R/renv.lock` packages were not installed in this
worktree's project-local R library**
- **Found during:** pre-flight, before Task 1
- **Issue:** `Rscript` was reachable once `R_HOME`/PATH were set (per `CLAUDE.md`'s documented
  Windows PATH friction point), but `renv::status()` reported ~80 lockfile-recorded packages
  as not installed in this worktree's own `renv/library/` (each git worktree gets its own
  filesystem, so a sibling worktree's already-restored library does not carry over).
- **Fix:** ran `renv::restore(prompt = FALSE)`; all 73 needed packages linked instantly from
  the shared global renv package cache (no network fetch, no version drift from the pinned
  lockfile).
- **Files modified:** none (environment-only; `renv.lock` itself untouched)
- **Commit:** N/A (no git-tracked change)

**2. [Rule 1 - bug] Own-source-file detection was resolving to `NULL` when called after
`source()` had already returned**
- **Found during:** Task 1, first live verify run
- **Issue:** The initial `.ll_this_file()` implementation queried `sys.frames()` lazily,
  inside `ll_repo_root()`, which is only ever called *after* the top-level `source()` call
  that loaded the module has already returned — by then `sys.frames()` no longer carries the
  source call's `ofile`, so `ll_repo_root()` failed with "could not determine this file's own
  source location" on every accessor call in the exact invocation shape (`Rscript -e
  "source('...'); ll_brand(...)"`) the plan's own verify commands use.
- **Fix:** capture `.ll_source_file <- .ll_this_file()` once, as a top-level statement that
  runs *during* the `source()` call itself (while `sys.frames()` still exposes it), and have
  `ll_repo_root()` read that cached value instead of re-deriving it lazily.
- **Files modified:** `data-pipeline/R/theme_llexplorer.R`
- **Commit:** `88588a4` (fixed before the task's own commit; not a separate follow-up)

**3. [Rule 1 - bug] `systemfonts::match_font()` deprecation warning surfaced from
`theme_ll_map()`**
- **Found during:** Task 2, first live verify run
- **Issue:** `systemfonts` 1.3.2 (present on this machine as a transitive dependency, though
  not itself pinned in `renv.lock`) emits a deprecation warning for `match_font()` in favour
  of `match_fonts()`. This polluted an otherwise-clean render/test run with a spurious
  warning.
- **Fix:** `.ll_resolve_font_family()` now prefers `match_fonts()` (current API) when present
  on the `systemfonts` namespace, falling back to the deprecated `match_font()` only if
  `match_fonts` is absent (older `systemfonts`), wrapped in `suppressWarnings()` either way.
- **Files modified:** `data-pipeline/R/theme_llexplorer.R`
- **Commit:** `1abca9f`

**4. [Rule 1 - bug] Plan's stated `palettes$landscape` entry count (9) did not match the
real committed `data/report_tokens.json` (8)**
- **Found during:** Task 3, writing the palette-bridge assertions
- **Issue:** Plan 12-06's Task 3 action text says `$landscape has 9`. Live inspection of the
  actual committed file (both from R via `ll_tokens()$palettes$landscape` and independently
  cross-checked with a direct Python JSON read) shows exactly 8 entries (`value` codes 1, 2,
  4, 5, 7, 8, 10, 11).
- **Fix:** wrote the test assertion against the real, verified figure (8), per Task 1's own
  `read_first` instruction to trust the real emitted file over the plan's interface-block
  prose. Documented inline in the test file and here rather than silently diverging from the
  plan text without a record.
- **Files modified:** `data-pipeline/R/tests/test_theme_llexplorer.R`
- **Commit:** `c462eb4`

**5. [Rule 1 - bug] `testthat` literal string in a comment tripped the acceptance-criteria
grep gate**
- **Found during:** Task 3, acceptance-criteria pass
- **Issue:** The file's header comment explained the absence of a unit-test framework by
  naming `testthat`, which made `grep -c "testthat" <file>` return 1 instead of the required
  0.
- **Fix:** reworded the comment to describe the same fact ("no unit-test framework
  dependency") without using the literal string.
- **Files modified:** `data-pipeline/R/tests/test_theme_llexplorer.R`
- **Commit:** `c462eb4`

## Verification

- `Rscript -e "source('data-pipeline/R/theme_llexplorer.R'); cat('OK\n')"` — exits 0, no
  warnings. PASS.
- `Rscript data-pipeline/R/tests/test_theme_llexplorer.R` — exits 0, prints one line per
  Living Lab, ends with `OK`. PASS. Confirmed the gate actually fails on breakage (see
  Deviation 4's sibling test in Task 3, or rather the documentTitle-rename live test recorded
  in Task 3's own acceptance pass) and recovers cleanly once restored.
- `python -m pytest data-pipeline/tests/ -q` — 38/39 passing. The one failure
  (`test_derive_change_field_guards_nodata`) is a pre-existing environment gap: the ambient
  global Python interpreter used to run this check has no `rasterio` installed (the
  pipeline's own dedicated venv, which does have it, was not active in this worktree). No
  Python file was touched by this plan, so this is unrelated to the R work above and is
  flagged as a known environment limitation, not a regression.
- `python data-pipeline/R/render_reports.py --slug rheingau --lang en` — **not run**.
  `render_reports.py` is plan 12-05's deliverable, which is not a dependency of this plan
  (`depends_on: ["12-02", "12-04"]`) and has not been merged into this wave's base. This
  check belongs to the phase's overall goal verification once 12-05 lands, not to this plan.

## Self-Check

- `data-pipeline/R/theme_llexplorer.R` exists: FOUND
- `data-pipeline/R/tests/test_theme_llexplorer.R` exists: FOUND
- `data-pipeline/R/README.md` contains `## Verification`: FOUND
- Commit `88588a4` exists in git log: FOUND
- Commit `1abca9f` exists in git log: FOUND
- Commit `c462eb4` exists in git log: FOUND

## Self-Check: PASSED
