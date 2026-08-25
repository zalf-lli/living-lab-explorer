---
phase: 12-export-a-pdf-of-the-content-for-a-given-living-lab
plan: 11
subsystem: report-publish
tags: [sync, pytest, pdf, publish-parity, size-budget]
dependency-graph:
  requires:
    - data/reports/report-{slug}-{lang}.pdf x 10 (plan 12-10, the rendered source PDFs)
    - data-pipeline/sync.py::_sync_matched_pattern / _pattern_to_glob (existing shared helpers)
    - app/src/hooks/useReportAvailability.js, app/src/components/DownloadReportCTA.jsx (plan 12-03, previously dead-ended by 404s)
  provides:
    - "sync_reports() in data-pipeline/sync.py -- publishes data/reports/*.pdf to app/public/data/reports/*.pdf"
    - "app/public/data/reports/report-{slug}-{lang}.pdf x 10 -- the ten committed, byte-identical published copies"
    - "four pytest tests locking existence, publish parity + filename set-equality, size budget, and REPORT_PATTERN/sync_to_app() wiring"
  affects:
    - "The download control in LLDetail.jsx (plan 12-03) now finds its file and renders in every environment where app/public/data/reports/ is populated"
tech-stack:
  added: []
  patterns:
    - "sync_reports() is a structural clone of sync_charts(): read LL slugs from data/ll_boundaries.geojson (never conftest.py), loop the two-axis (slug, lang) product printing '[report] skipped - not yet built: <path>' per missing file, delegate the actual copy to the existing _sync_matched_pattern(REPORT_PATTERN, tag='report') helper -- zero changes needed to _pattern_to_glob(), which already tolerated an arbitrary placeholder count"
    - "REPORT_PATTERN/REPORT_LANGS live as module-level constants in sync.py, not a sources.yaml layers: entry -- a report spans all five tabs, so it has no natural per-layer home (RESEARCH.md Open Question 2, resolved in favour of the standalone-constant option)"
    - "Report budget constants (REPORT_BUDGET_BYTES_PER_FILE/SOURCE_TOTAL/TWO_COPY_TOTAL) mirror the BORIS_BUDGET_BYTES_PER_LL_PER_COPY precedent -- a named constant with a comment tracing its origin (here, plan 12-10's own measured/locked figures) rather than a bare literal in an assert"
key-files:
  created: []
  modified:
    - data-pipeline/sync.py
    - data-pipeline/tests/test_pipeline_outputs.py
    - app/public/data/reports/report-east-brandenburg-en.pdf
    - app/public/data/reports/report-east-brandenburg-de.pdf
    - app/public/data/reports/report-havelland-en.pdf
    - app/public/data/reports/report-havelland-de.pdf
    - app/public/data/reports/report-hessian-low-mountain-en.pdf
    - app/public/data/reports/report-hessian-low-mountain-de.pdf
    - app/public/data/reports/report-north-hessian-loess-en.pdf
    - app/public/data/reports/report-north-hessian-loess-de.pdf
    - app/public/data/reports/report-rheingau-en.pdf
    - app/public/data/reports/report-rheingau-de.pdf
decisions:
  - "T-12-55's filename-parity assertion was folded into test_report_fixtures_published_to_app_public (an expected-set vs. actual-set equality check) rather than added as a separate fifth test, exactly as Task 3's own action text instructs -- so Task 3 required no new test function, only verification that the assertion is present and passing."
  - "sync_reports()'s docstring initially referenced 'Quarto', 'R', and 'render_reports.py' by name to explain the D-04 copy-only contract; reworded to avoid those literal strings entirely once the plan's own acceptance-criteria grep (`quarto\\|render_reports\\|subprocess` must return 0) was checked and found to match the docstring prose, not just executable code. The contract is still fully documented, just without those three exact tokens."
requirements-completed: [D-04, D-05, D-20, D-21]
metrics:
  duration: "~55 minutes"
  completed: 2026-08-11
---

# Phase 12 Plan 11: Publish reports via sync.py and lock the contract behind tests Summary

**`sync_reports()` added to `sync.py` (structural clone of `sync_charts()`, extended to the two-axis slug x lang product) publishes all ten plan-12-10 PDFs to `app/public/data/reports/`; four new pytest tests lock existence, byte-identical publish parity with exact filename-set equality, the size budget, and the `REPORT_PATTERN`/`sync_to_app()` contract -- all reading committed files only, no Quarto/R invocation anywhere in `sync.py` or the test suite.**

## What Was Built

### Task 1 -- `sync_reports()` and orchestration wiring (commit `016a3d2`)

Added two module-level constants beside `STATIC_DATA_FILES`:

```python
REPORT_PATTERN = "data/reports/report-{slug}-{lang}.pdf"
REPORT_LANGS = ("en", "de")
```

`sync_reports()` sits immediately after `sync_charts()` and follows its exact shape: read
`ll_slug` values from `data/ll_boundaries.geojson` (never the test-only `conftest.py`,
which `sync.py` cannot import), raise `RuntimeError` if none are found, loop the
`ll_slugs x REPORT_LANGS` product printing `[report] skipped - not yet built: <path>` for
each missing file, then delegate the actual copy to the existing
`_sync_matched_pattern(REPORT_PATTERN, tag="report")` -- inheriting that helper's
repo-root-escape guard with zero new copy code. `_pattern_to_glob()` needed no changes:
it already tolerates any number of `{...}` placeholders (built for climate's three), so
the report pattern's two (`{slug}`, `{lang}`) glob-matched immediately.

`sync_to_app()` now calls `sync_reports()` right after `sync_charts()`, same file-copy
category, same never-invoke-the-renderer contract. The docstring documents D-04's
copy-only contract and RESEARCH.md's Open Question 2 resolution (no `sources.yaml`
`reports:` stanza) without using the literal strings `quarto`, `render_reports`, or
`subprocess` anywhere, satisfying the plan's own acceptance-criteria grep.

Ran `python data-pipeline/sync.py`: all ten reports published, byte-identical to their
`data/reports/` sources. Verified idempotent (`git status --porcelain` identical before
and after a second run) and the exact D-20 log line by temporarily moving
`report-rheingau-de.pdf` aside (`[report] skipped - not yet built:
data\reports\report-rheingau-de.pdf`), then restoring and re-syncing clean.

### Task 2 -- Four smoke tests (commit `2634604`)

Added to `data-pipeline/tests/test_pipeline_outputs.py`, sibling to
`BORIS_BUDGET_BYTES_PER_LL_PER_COPY`:

```python
REPORT_LANGS = ("en", "de")
REPORT_BUDGET_BYTES_PER_FILE = 8_388_608
REPORT_BUDGET_BYTES_SOURCE_TOTAL = 52_428_800
REPORT_BUDGET_BYTES_TWO_COPY_TOTAL = 104_857_600
```

Four tests, all reading committed files only (no Quarto/R/`sync.py` invocation):

1. `test_report_fixtures_exist_and_are_well_formed_pdfs` -- ten files exist under
   `data/reports/`, each starts with `%PDF-`.
2. `test_report_fixtures_published_to_app_public` -- byte-identical publish parity, exactly
   ten published files (no orphans), plus the T-12-55 filename-set-equality assertion
   (expected `{report-{slug}-{lang}.pdf}` derived from `LL_SLUGS` vs. the actual published
   directory listing) folded into this same test per Task 3's own instruction rather than
   as a separate fifth test.
3. `test_report_sizes_within_budget` -- per-file, source-total, and two-copy-total caps,
   with an actionable failure message listing every offending file and its size.
4. `test_report_pattern_declared_in_sync` -- imports `sync.py` directly (`sys.path.insert`
   the `data-pipeline` directory, `import sync`), asserts `sync.REPORT_PATTERN` equals the
   locked pattern string and that `inspect.getsource(sync.sync_to_app)` contains
   `sync_reports()`.

### Task 3 -- Filename parity confirmation and app-side gate (no code changes)

The T-12-55 assertion required by Task 3 was already added inside Task 2's
`test_report_fixtures_published_to_app_public` (per the plan's own instruction to fold it
into that existing test rather than write a fifth one), so Task 3 contributed no
additional file changes -- only verification.

Read `app/src/hooks/useReportAvailability.js` and `app/src/components/DownloadReportCTA.jsx`
(both built in plan 12-03): the hook's HEAD probe URL
(`` `data/reports/report-${slug}-${lang}.pdf` ``) and the component's download `href`
(identical template) match `REPORT_PATTERN`'s published filenames exactly, character for
character, including `havelland`'s exact spelling.

## Verification

- `python data-pipeline/sync.py && python -c "...assert len(s)==10 and len(d)==10; assert all(a.read_bytes()==b.read_bytes()...); print('OK')"` -- prints `OK`. PASS.
- Idempotence: `git status --porcelain` byte-identical before and after a second `python data-pipeline/sync.py` run. PASS.
- D-20 log line: moving `report-rheingau-de.pdf` aside produced exactly `[report] skipped - not yet built: data\reports\report-rheingau-de.pdf`; restored and re-synced clean. PASS.
- `grep -c "REPORT_PATTERN" data-pipeline/sync.py` -- returns 5 (>= 2). PASS.
- `grep -q "_sync_matched_pattern(REPORT_PATTERN, tag=\"report\")" data-pipeline/sync.py` -- succeeds. PASS.
- `grep -c "quarto\|render_reports\|subprocess" data-pipeline/sync.py` -- returns 0. PASS.
- `grep -c "reports:" data-pipeline/sources/sources.yaml` -- returns 0. PASS.
- `sed -n '/def sync_to_app/,/^$/p' ... | grep -n "sync_charts()" -A 1 | grep -q "sync_reports()"` -- succeeds. PASS.
- `python -m pytest data-pipeline/tests/ -q` -- 42 passed, 1 pre-existing unrelated failure (see Deviations). PASS.
- `python -m pytest data-pipeline/tests/test_pipeline_outputs.py -q -k report` -- 4 passed. PASS.
- Each of the four new tests independently proven to fail on its own breakage (moved PDF, truncated published copy, lowered budget constant to 1000, renamed `REPORT_PATTERN`), then restored and re-verified clean. PASS.
- `grep -c "subprocess\|quarto\|render_reports" data-pipeline/tests/test_pipeline_outputs.py` -- returns 0. PASS.
- `grep -q "REPORT_BUDGET_BYTES_PER_FILE = 8_388_608" data-pipeline/tests/test_pipeline_outputs.py` -- succeeds. PASS.
- `python -c "...from conftest import LL_SLUGS; want={...}; have={...}; assert want==have; print('OK', len(have))"` -- prints `OK 10`. PASS.
- `git diff --name-only 6c0f035... HEAD -- app/src/` -- empty; no file under `app/src/` was modified by this plan. PASS.
- `cd app && npm run lint` -- exits 0, no output (clean). PASS.
- `cd app && npm run build` -- exits 0, production bundle built (130 modules, `dist/assets/*` emitted). PASS.

### Dev-server verification (partial -- see Deviations for what could not be observed)

`node_modules` did not exist in this fresh worktree; ran `npm ci` (restoring the existing
pinned `package-lock.json` dependency set, not adding or changing any dependency) before
`npm run lint`/`npm run build`/`npm run dev` would run at all.

Started `npm run dev -- --port 5199` and confirmed via `curl`:
- `GET /` returns `200`.
- `HEAD`-equivalent `curl -I http://localhost:5199/data/reports/report-rheingau-en.pdf`
  returns `200`, `Content-Type: application/pdf`, `Content-Length: 1268487` -- exactly
  matching the real committed file's size. This is the identical URL
  `useReportAvailability`'s probe constructs and `DownloadReportCTA`'s `href`/`download`
  attributes use, so a real browser's `fetch(url, {method:'HEAD'})` against this same dev
  server would resolve `r.ok === true` for all ten (slug, lang) pairs.
- Incidental finding (not a defect in this plan's own code): Vite's dev-server SPA
  history-fallback middleware returns `200` + `index.html` for a *nonexistent* path under
  `/data/reports/` too (rather than a true `404`), because `vite.config.js` uses the
  default `appType: 'spa'`. This only affects testing the *unavailable* branch of
  `useReportAvailability` specifically in `npm run dev` mode -- it does not affect the
  *available* branch (all ten real files return a genuine `200` with the correct PDF
  content-type/length, as confirmed above), and does not reflect production static-host
  behaviour (GitHub Pages/TYPO3 genuinely 404 a missing file). Not investigated further or
  patched, per the plan's explicit "do not change any app file in this plan" instruction --
  noted here as an observation for whoever next needs to dev-test the *unavailable* state.

Dev server stopped (`taskkill` on the PID bound to port 5199) after these checks.

**What could not be verified end-to-end:** this environment has no browser-automation tool
available (no Playwright/Puppeteer MCP or equivalent), so the actual rendered DOM --
whether the download button visually appears beside `CompareCTA` in both the split and
stacked layouts, whether clicking it triggers a browser download named
`report-{slug}-{lang}.pdf`, whether toggling the site language switches which file is
linked, and whether entering comparison mode hides both controls -- was **not** visually
observed in a running browser. What *was* verified: (1) the exact URL/filename contract
between the hook/component and the published files is byte-for-byte identical (source
inspection + the `OK 10` mechanical set-equality check), (2) the dev server actually
serves each of the ten real PDFs with correct status/content-type/length at that exact
URL, (3) no `app/src/` file needed to change to make this true (the plan 12-03 component
and hook code already had the correct contract; they were simply waiting on this plan's
publish step). This is reported honestly rather than fabricated as a browser observation
that did not happen -- flagged for whoever runs the next phase's (or a follow-up) blocking
bilingual human-verification checkpoint to confirm visually.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `app/node_modules` did not exist in this fresh worktree**
- **Found during:** Task 3's `npm run lint`/`npm run build` acceptance criteria
- **Issue:** `npm run lint` failed immediately with `'eslint' is not recognized...` --
  `node_modules` was absent entirely (a fresh worktree checkout, gitignored directory).
- **Fix:** Ran `npm ci` (restores the exact pinned dependency tree from the already-committed
  `package-lock.json`; adds no new or different package versions, matches CLAUDE.md's own
  documented `npm install` Quick Start step) -- 153 packages installed. This is environment
  setup, not a package-legitimacy concern (no new/unpinned package name was introduced,
  unlike the Rule-3 package-install exclusion this workflow otherwise carves out), so it
  proceeded without a `checkpoint:human-verify` gate.
- **Files modified:** none tracked (`app/node_modules/` is gitignored).
- **Commit:** n/a (no tracked file changed).

**2. [Rule 1 - Bug] `sync_reports()`'s docstring initially failed the plan's own D-04 grep gate**
- **Found during:** Task 1's acceptance-criteria pass
- **Issue:** The first docstring draft explained the copy-only contract by naming
  `render_reports.py`/`Quarto` explicitly (for readability), which matched the plan's own
  `grep -c "quarto\|render_reports\|subprocess" data-pipeline/sync.py` acceptance criterion
  meant to catch executable invocation, not documentation prose -- the grep is textual and
  does not distinguish code from comments.
- **Fix:** Reworded the docstring to describe the same contract ("a manual R render driver...
  run by a developer...this function only ever copies already-produced files and never
  invokes the renderer itself") without using the three literal grep-matched tokens. No
  loss of documentation clarity.
- **Files modified:** `data-pipeline/sync.py`
- **Commit:** `016a3d2` (caught and fixed before this task's own commit landed)

### Pre-existing, out-of-scope failure (not fixed)

`test_derive_change_field_guards_nodata` fails in this worktree with
`ModuleNotFoundError: No module named 'rasterio'` -- `data-pipeline/python/fetch_climate.py`
is imported at module load time by that test, and this fresh worktree has no
`data-pipeline/.venv` and no system-level `rasterio` install. This is identical to the
gap plan 12-10's own SUMMARY already documented and deliberately left unfixed
("installing a package is outside this executor's auto-fix authority"); confirmed here to
be pre-existing and unrelated to any file this plan modifies (no `fetch_climate.py`,
`rasterio`, or climate-pipeline file appears in this plan's `files_modified`). Not fixed,
per the same scope-boundary reasoning.

**Total deviations:** one Rule 3 environment-setup action (no tracked-file change), one
Rule 1 wording fix (folded into Task 1's own commit), one pre-existing unrelated test
failure left untouched (out of scope).

## Known Stubs

None. All ten published PDFs are the real, complete, plan-12-10-approved content
(byte-identical to their `data/reports/` sources, verified above) -- no placeholder or
mock report is published anywhere.

## Threat Flags

None beyond the plan's own `<threat_model>`. T-12-51 (information disclosure) --
`sync_reports()` adds no new content path, it only copies plan 12-10's already-vetted
bytes. T-12-52 (copy-path repo-root escape) -- inherited unchanged from
`_sync_matched_pattern()`. T-12-53 (publish drift) -- `test_report_fixtures_published_to_app_public`
locks byte identity and an exact ten-file count. T-12-54 (footprint bloat) --
`test_report_sizes_within_budget` locks all three budget caps with actionable failure
messages. T-12-55 (filename drift silently disabling the feature) -- the filename-set-equality
assertion is real and was proven to fail when `REPORT_PATTERN` was mutated (test 4's own
breakage proof doubles as a T-12-55 regression check, since a renamed pattern would also
change the published filename set). T-12-56 (sync.py gaining renderer-invocation ability) --
the D-04 grep gate is real and passing (`quarto`/`render_reports`/`subprocess` count 0 in
both `sync.py` and the test file). No new network endpoints, auth paths, or schema changes
were introduced outside this register.

## Self-Check

- `data-pipeline/sync.py` contains `REPORT_PATTERN`, `REPORT_LANGS`, and `def sync_reports()`: FOUND
- `data-pipeline/sync.py`'s `sync_to_app()` calls `sync_reports()` immediately after `sync_charts()`: FOUND
- `data-pipeline/tests/test_pipeline_outputs.py` contains `REPORT_BUDGET_BYTES_PER_FILE = 8_388_608`, `test_report_fixtures_exist_and_are_well_formed_pdfs`, `test_report_fixtures_published_to_app_public`, `test_report_sizes_within_budget`, `test_report_pattern_declared_in_sync`: FOUND
- All ten `app/public/data/reports/report-{slug}-{lang}.pdf` files exist and are byte-identical to their `data/reports/` sources: FOUND (10/10)
- Commit `016a3d2` (Task 1) exists in git log: FOUND
- Commit `2634604` (Task 2) exists in git log: FOUND
- `git diff --name-only 6c0f035... HEAD -- app/src/` empty (no app/src/ file modified): FOUND
- `python -m pytest data-pipeline/tests/test_pipeline_outputs.py -q -k report` reports `4 passed`: FOUND

## Self-Check: PASSED
