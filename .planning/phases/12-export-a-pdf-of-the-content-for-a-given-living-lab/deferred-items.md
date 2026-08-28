# Deferred Items — Phase 12

## 12-01: `npm run check:soil-palette` failure (pre-existing, out of scope)

**Found during:** 12-01 Task 3 verification (the plan's overall `<verification>` block lists
`check:soil-palette` as a gate).

**Failure:**
```
FAILED:
  - havelland: legend minimum pairwise ΔE76 is 19.0, expected >= 20
```

**Why deferred, not fixed:** This check exercises `app/src/data/soil_legend.js`, a file no task
in 12-01 reads, modifies, or is scoped to touch (its `files_modified` list is
`app/src/i18n_resources.js`, `app/src/i18n.js`, `app/src/hooks/useReportAvailability.js` only).
`git log` confirms the soil-palette files were last changed by an unrelated prior commit
(`fbe9914`, "colour soil bar chart from the map palette"), pre-dating this plan's work. `STATE.md`
already tracks this exact palette work as TODO-01 / quick-task `260804-acf`, "pending human visual
check" — this is a known, already-flagged, pre-existing condition, not a regression introduced by
12-01.

**Scope boundary rule applied:** "Only auto-fix issues DIRECTLY caused by the current task's
changes. Pre-existing warnings, linting errors, or failures in unrelated files are out of scope."

**Recommended next step:** Resolve as part of the existing TODO-01 / `260804-acf` follow-up, not
as part of Phase 12.

## 12-03: same `check:soil-palette` failure recurs (still pre-existing, still out of scope)

**Found during:** 12-03 Task 2 verification (`npm run check:soil-palette` is one of Task 2's
listed acceptance criteria).

**Failure:** identical to the 12-01 entry above — `havelland` legend ΔE76 19.0 < 20.

**Why deferred, not fixed:** 12-03's `files_modified` list is
`app/src/components/DownloadReportCTA.jsx`, `app/src/pages/LLDetail.jsx` — neither touches
`app/src/data/soil_legend.js` or any `app/public/data/geojson/*` fixture; `git diff --stat` between
this plan's base commit and its final commit confirms zero changes to either. Same pre-existing,
already-tracked condition (TODO-01 / `260804-acf`), not a regression introduced by 12-03.

## 12-04: `npm run check:soil-palette` failure recurs (same pre-existing condition)

**Found during:** 12-04's overall `<verification>` block, which also lists `check:soil-palette`
as a gate (`cd app && npm run lint`, `npm run build` and `npm run check:soil-palette` all exit 0).

**Failure:** identical to the 12-01 entry above --
`havelland: legend minimum pairwise ΔE76 is 19.0, expected >= 20`.

**Why deferred, not fixed:** 12-04's `files_modified` list (`app/scripts/export_report_tokens.mjs`,
`app/package.json`, `data/report_tokens.json`, `data-pipeline/tests/test_report_tokens.py`) never
touches `app/src/data/soil_legend.js` or any `buek250-*.geojson` fixture. `npm run lint` and
`npm run build` both pass clean; only this pre-existing, already-tracked soil-palette condition
fails. Confirmed to be the exact same failure already logged under 12-01 above -- not a new
regression, and not caused by this plan's report-tokens work (the report tokens bundle imports
`soil_legend.js`'s raw exports unmodified for R to reimplement the same colour resolution, so it
carries the same colours through faithfully, whatever they are).

**Recommended next step:** unchanged from the 12-01 entry -- resolve via TODO-01 / `260804-acf`.

## 12-10 checkpoint review round 2: `test_derive_change_field_guards_nodata` failure (pre-existing environment gap, out of scope)

**Found during:** round 2's own `python -m pytest data-pipeline/tests/ -q` re-verification, after
all four checkpoint-review defects were fixed and the full ten-file re-render completed.

**Failure:**
```
data-pipeline/python/fetch_climate.py:35: in <module>
    import rasterio
E   ModuleNotFoundError: No module named 'rasterio'
FAILED data-pipeline/tests/test_pipeline_outputs.py::test_derive_change_field_guards_nodata
```

**Why deferred, not fixed:** this executor's worktree has no `data-pipeline/.venv` (per CLAUDE.md,
pipeline Python dependencies live in a per-machine venv created via `python -m venv .venv && pip
install -r requirements.txt`, never committed) and the system Python resolved by `python` on PATH
(`...PythonSoftwareFoundation.Python.3.13.../python.exe`) has no `rasterio` installed either
(`pip show rasterio` confirms "Package(s) not found"). None of this round's four fixes touch
`data-pipeline/python/fetch_climate.py` or anything it imports -- the failure is a raw
`ModuleNotFoundError` at import time, in a file this round's `files_modified` never lists. Package
installs are explicitly excluded from this executor's auto-fix authority (a missing/uninstalled
dependency requires human verification before an install, not a unilateral `pip install
rasterio`), and this is an environment-setup gap specific to this fresh worktree checkout, not a
regression introduced by this round's KPI-box/pagebreak/locator-layout/caption work. All 38 other
collected tests pass (confirmed both before and after this round's fixes were applied).

**Recommended next step:** run `pip install -r data-pipeline/requirements.txt` (or set up
`data-pipeline/.venv` per CLAUDE.md's own Development Quick Start) in whatever environment next
executes this suite; not part of this plan's own scope.
