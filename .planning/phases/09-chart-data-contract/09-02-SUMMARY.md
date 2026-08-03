---
phase: 09-chart-data-contract
plan: 02
subsystem: data-pipeline
tags: [sync, sources-yaml, chart-contract, plumbing]
dependency-graph:
  requires: []
  provides:
    - "sources.yaml: chart.script + output.chart_pattern on all 5 chart-bearing layers"
    - "sources.yaml: climate.variables.*.label {en,de} bilingual chart-legend names"
    - "sync.py: sync_charts() publisher"
    - "sync.py: tag-aware sync_file()/_sync_matched_pattern()"
  affects:
    - "09-03 (agriculture chart script) reads chart.script + output.chart_pattern"
    - "09-04 (soil/landscape/economic chart scripts) read chart.script + output.chart_pattern"
    - "09-05 (climate chart script) reads chart.script + output.chart_pattern + climate.variables.*.label"
tech-stack:
  added: []
  patterns:
    - "sibling-stanza config idiom (chart: parallel to build:, chart_pattern under output:)"
    - "tag-parameterized sync helper (sync_file/_sync_matched_pattern default tag='sync', chart path passes tag='chart')"
    - "per-(layer, LL) explicit existence check before delegating the actual copy to the existing glob helper"
key-files:
  created: []
  modified:
    - data-pipeline/sources/sources.yaml
    - data-pipeline/sync.py
decisions:
  - "D-05..D-11, D-16 all confirmed as specified in 09-CONTEXT.md/09-RESEARCH.md; no deviation from locked interface values"
metrics:
  duration: "~35 min"
  completed: 2026-08-03
---

# Phase 9 Plan 2: Chart Data Contract Plumbing Summary

Added the declarative `chart:` stanza (script path + per-Living-Lab output pattern) to
all five chart-bearing layers in `sources.yaml`, four bilingual `label:{en,de}` blocks
to `chelsa-climate`'s climate variables, and a new `sync_charts()` function in `sync.py`
that names all 25 missing (layer, Living Lab) chart files individually before any
chart script exists.

## What Was Built

**Task 1 — `sources.yaml` (commit `4994e0d`):**
- Added `chart.script` (a new sibling stanza to each layer's existing `build:` block)
  and `output.chart_pattern` (a new key inside each layer's existing `output:` block)
  to `landuse-croptypes`, `io-lulc-landcover`, `buek250`, `boris`, and `chelsa-climate`
  — the exact literal script paths and pattern strings locked in the plan's
  `<interfaces>` table (D-05..D-11).
- Deliberately excluded `bfn-schutzgebiete` (the protected-areas overlay, not one of
  the five chart-bearing map tabs) from both new keys.
- Added a `label: {en, de}` block to each of `chelsa-climate`'s four
  `climate.variables` entries (`gdd`, `bio1`, `bio12`, `bio18`) — the long
  chart-legend names required by D-16, deliberately distinct from
  `app/src/i18n.js`'s existing short picker labels (`GDD`, `Mean temp.`,
  `Precipitation`, `Summer precip.`), which remain unchanged. Every existing German
  string in the file uses ASCII transliteration for umlauts (`ae`/`oe`/`ue`), so
  bio18's label reads `Niederschlag im waermsten Quartal`.
- `git diff --stat` confirms insertions-only (38 insertions, 0 deletions) — no
  pre-existing key's value changed.

**Task 2 — `sync.py` (commit `9731ba1`):**
- Added a keyword-only `tag: str = "sync"` parameter to `sync_file()` and
  `_sync_matched_pattern()`, threaded into both functions' print lines. Every one of
  the four existing call sites omits the parameter and keeps its `[sync]`/`[skip]`
  output byte-identical.
- Added `sync_charts()`, placed immediately after `sync_vector_geojson()` and called
  from `sync_to_app()` in the same slot (after `sync_vector_geojson()`, before
  `generate_landuse_legend()`), preserving the file's existing grouping of all
  `sync_*` calls ahead of all `generate_*` calls.
  - Reads the five Living Lab slugs from `data/ll_boundaries.geojson` via `resolve()`
    and `json.loads`, collecting `feature["properties"]["ll_slug"]` into a sorted set
    (no hardcoded slug list, no `conftest` import). Raises `RuntimeError` if the
    collected set is empty.
  - Iterates `load_sources()["layers"]`, skipping any layer with no
    `output.chart_pattern` (the mechanism that excludes `bfn-schutzgebiete` — no
    explicit id allow-list).
  - For each remaining layer, loops the five slugs and prints
    `[chart] skipped - not yet built: {relative-pattern-path}` for every
    `pattern.format(slug=slug)` that does not yet exist on disk (D-15's per-file
    requirement), then delegates the actual copy to
    `_sync_matched_pattern(pattern, tag="chart")` so the copy path keeps inheriting
    `_pattern_to_glob()` and the repo-root-escape guard at `sync.py:337-341` (D-10).

## Verification

- Task 1's automated verify command (a `yaml.safe_load` + assertion script over every
  locked literal string, the overlay exclusion, and the pre-existing unit-string
  byte-identity) printed `OK`.
- Task 2's automated verify command (signature introspection + a real `sync.py` run +
  pytest) all passed:
  - `python sync.py` exits 0, prints exactly 25 lines matching
    `^\[chart\] skipped - not yet built: ` and 0 lines matching `^\[chart\] .* -> `
    (no chart files exist yet, matching the plan's "nothing built yet" precondition).
  - `generated app/src/data/climate_legend.js` still appears in the log.
  - `git status --porcelain app/src/data/` is empty after the sync run — no generated
    JS file's content changed.
  - `python -m pytest data-pipeline/tests/` passes 31/31 (see Deviations — the plan's
    acceptance criteria text cites "20/20", a stale figure; the actual current suite
    size is 31, all passing, zero new tests added by this plan as expected).

## Deviations from Plan

### Auto-fixed Issues

None — no bugs, missing functionality, or blocking issues were found in the code
itself. `sources.yaml` and `sync.py` were edited exactly as the plan's `<action>`
blocks specified.

### Environment note (not a code deviation)

The worktree's default `python` on `PATH` resolves to a Windows Store Python 3.13
install with no `rasterio` installed, so the first `pytest` run failed on
`ModuleNotFoundError: No module named 'rasterio'` inside `fetch_climate.py` (an
unrelated, pre-existing import in a file this plan does not touch). Re-ran both the
`sync.py` verification and the pytest suite via the project's dedicated pipeline venv
at `C:\lcvenv\Scripts\python.exe` (referenced in `.planning/STATE.md`'s Phase 8 notes
and matching CLAUDE.md's "Python 3.12 required on Windows" constraint) — both runs
passed cleanly (25/25 skipped-chart lines, 31/31 tests). No source file was changed to
work around this; it is purely a shell-environment interpreter-selection issue in this
worktree, out of this plan's `files_modified` scope.

## Self-Check

- `data-pipeline/sources/sources.yaml`: FOUND, modified as described
- `data-pipeline/sync.py`: FOUND, modified as described
- Commit `4994e0d`: FOUND in `git log`
- Commit `9731ba1`: FOUND in `git log`
