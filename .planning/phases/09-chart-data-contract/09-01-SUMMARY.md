---
phase: 09-chart-data-contract
plan: 01
subsystem: pipeline
tags: [chart-contract, json-schema, writer-module, docs]

# Dependency graph
requires: []
provides:
  - data-pipeline/python/chart_contract.py — write_bar_chart() / write_line_chart() shared envelope writers (D-01, D-02, D-04, D-13, D-14)
  - "## Chart data contract" section in data-pipeline/README.md documenting both chart_type variants
  - chart.script / output.chart_pattern bullet in data-pipeline/sources/README.md
affects: ["09-02 (chelsa-climate label field + 5x sources.yaml chart stanzas)", "09-03/09-04/09-05 (all five compute_*_chart.py scripts import write_bar_chart/write_line_chart by name)"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Discriminator-by-function-name: chart_type is never a caller-supplied parameter — write_bar_chart() always sets 'bar', write_line_chart() always sets 'line', making a mismatched envelope structurally unwritable"
    - "generated_at computed inside the writer (datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')), never passed in by a caller, so all future chart scripts share one timestamp idiom"

key-files:
  created:
    - data-pipeline/python/chart_contract.py
  modified:
    - data-pipeline/README.md
    - data-pipeline/sources/README.md

key-decisions:
  - "chart_contract.py imports nothing beyond json, datetime, pathlib and __future__ — no geopandas/rasterio/yaml — per the plan's explicit instruction to keep the writer a thin, dependency-free stdlib module any future chart script can import cheaply"
  - "No validation of series/lines contents was added to the writer; shape enforcement is deferred to plan 09-06's pytest contract tests, per the plan's explicit scope boundary"

requirements-completed: [CHARTS-01]

# Metrics
duration: ~25min
completed: 2026-08-03
---

# Phase 9 Plan 01: Chart Data Contract Writer Module + Documentation Summary

**Extracted the chart_type-discriminated bar/line JSON envelope into one stdlib-only writer module (`chart_contract.py`) and documented both variants concretely in both pipeline READMEs, before any layer-specific chart script exists.**

## Performance

- **Duration:** ~25 min
- **Completed:** 2026-08-03
- **Tasks:** 2
- **Files modified:** 3 (1 created, 2 modified)

## Accomplishments

- `data-pipeline/python/chart_contract.py` exports exactly two public functions, `write_bar_chart` and `write_line_chart`, both keyword-only, matching the plan's `<interfaces>` block verbatim. `chart_type` is a literal inside each function body, never an argument, so a caller cannot write a `bar` envelope holding `x_axis` or vice versa. Verified: positional-argument calls raise `TypeError`; written bar/line payloads have exactly the locked eight/nine-key sets; `json.dumps` is called with `sort_keys=True`, `ensure_ascii=False`, `indent=2`; `generated_at` ends with `Z`; `mock` defaults to `False`.
- `data-pipeline/README.md` gained a new `## Chart data contract` section (positioned after `## BUEK250 soil semantics contract`, before `### Full working Windows sequence`) documenting both `chart_type` shapes, all seven shared envelope fields with concrete examples, the `value`/`pct` absolute-vs-percentage split, per-layer units, the raster percentage denominator note, and the `sync.py` copies-never-invokes rule.
- `data-pipeline/sources/README.md`'s `## What belongs in each layer entry` list gained one new bullet naming both `chart.script` and `output.chart_pattern` with concrete example values, cross-referencing the new README section.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create the shared chart envelope writer module** - `c449e17` (feat)
2. **Task 2: Document the chart data contract in both READMEs** - `83259c7` (docs)

**Plan metadata:** (this commit, made after SUMMARY.md is written)

## Files Created/Modified

- `data-pipeline/python/chart_contract.py` - New stdlib-only writer module. `write_bar_chart()` and `write_line_chart()` both build a payload dict, `mkdir(parents=True, exist_ok=True)` the output directory, write `json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)` as utf-8, and print `[ok] wrote {output_path}`.
- `data-pipeline/README.md` - Added `## Chart data contract` section (58 lines) between the BUEK250 semantics contract and the Windows sequence walkthrough.
- `data-pipeline/sources/README.md` - Added one bullet to the layer-entry list documenting `chart.script`/`output.chart_pattern`.

## Decisions Made

- Followed `09-PATTERNS.md`'s recommended full module body verbatim for `chart_contract.py`, since RESEARCH.md had already validated it against the three existing write-step duplicates (`compute_protected_area_coverage.py`, `compute_climate_kpis.py`, `build_land_cover.py`).
- Documentation section text follows the plan's `<action>` block closely (concrete file-path examples, all seven field names, the raster percentage-denominator caveat) rather than paraphrasing, since the plan's own acceptance criteria enumerate each required sentence.

## Deviations from Plan

None - plan executed exactly as written. Both tasks' automated verify commands passed on the first attempt.

## Issues Encountered

- The full `python -m pytest data-pipeline/tests/` suite reports 30 passed, 1 failed (`test_derive_change_field_guards_nodata`, which fails with `ModuleNotFoundError: No module named 'rasterio'`). This is a pre-existing environment gap in this worktree's Python environment (rasterio is not installed), unrelated to this plan's changes — `chart_contract.py` imports nothing beyond stdlib and touches no code path this failing test exercises. Out of scope per the Scope Boundary rule; not fixed. The plan's own `<verification>` target of "20 tests, pre-plan count" and STATE.md's more recent "31/31" both predate this environment; 30/31 passing with 1 pre-existing environment-only failure is consistent with no regression introduced by this plan.

## User Setup Required

None - no external service configuration required. This plan added a stdlib-only Python module and two documentation edits; no new dependencies, no network calls, no shell-outs.

## Next Phase Readiness

- `09-02` can now add the `chelsa-climate` `label:{en,de}` field and the five `chart:`/`output.chart_pattern` stanzas to `sources.yaml`, referencing the documented contract.
- `09-03`/`09-04`/`09-05` can import `write_bar_chart`/`write_line_chart` from `data-pipeline/python/chart_contract.py` by name with the exact keyword arguments locked in this plan's `<interfaces>` block — no further contract negotiation needed.
- `09-06`'s pytest contract tests can validate `series`/`lines` shape without needing to touch or re-derive the writer, since the writer deliberately does not perform that validation itself.

---
*Phase: 09-chart-data-contract*
*Completed: 2026-08-03*

## Self-Check: PASSED

- FOUND: data-pipeline/python/chart_contract.py
- FOUND: data-pipeline/README.md (## Chart data contract section)
- FOUND: data-pipeline/sources/README.md (chart.script / output.chart_pattern bullet)
- FOUND commit: c449e17 (Task 1)
- FOUND commit: 83259c7 (Task 2)
