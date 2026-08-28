---
phase: 12-export-a-pdf-of-the-content-for-a-given-living-lab
reviewed: 2026-08-12T00:00:00Z
depth: standard
files_reviewed: 45
files_reviewed_list:
  - .gitignore
  - CLAUDE.md
  - app/package.json
  - app/scripts/check_report_map_parity.mjs
  - app/scripts/export_report_tokens.mjs
  - app/src/components/DownloadReportCTA.jsx
  - app/src/data/soil_legend.js
  - app/src/hooks/useReportAvailability.js
  - app/src/i18n.js
  - app/src/i18n_resources.js
  - app/src/pages/LLDetail.jsx
  - data-pipeline/R/.Rprofile
  - data-pipeline/R/README.md
  - data-pipeline/R/_toolchain.py
  - data-pipeline/R/render_reports.py
  - data-pipeline/R/renv.lock
  - data-pipeline/R/renv/.gitignore
  - data-pipeline/R/renv/activate.R
  - data-pipeline/R/renv/settings.json
  - data-pipeline/R/report/_extensions/ll-explorer-typst/NOTICE.md
  - data-pipeline/R/report/_extensions/ll-explorer-typst/_brand.yml
  - data-pipeline/R/report/_extensions/ll-explorer-typst/_extension.yml
  - data-pipeline/R/report/_extensions/ll-explorer-typst/assets/zukunft-land-logo.svg
  - data-pipeline/R/report/_extensions/ll-explorer-typst/brands/east-brandenburg.yml
  - data-pipeline/R/report/_extensions/ll-explorer-typst/brands/havelland.yml
  - data-pipeline/R/report/_extensions/ll-explorer-typst/brands/hessian-low-mountain.yml
  - data-pipeline/R/report/_extensions/ll-explorer-typst/brands/north-hessian-loess.yml
  - data-pipeline/R/report/_extensions/ll-explorer-typst/brands/rheingau.yml
  - data-pipeline/R/report/_extensions/ll-explorer-typst/ll-explorer-theme.typ
  - data-pipeline/R/report/_extensions/ll-explorer-typst/typst-show.typ
  - data-pipeline/R/report/_extensions/ll-explorer-typst/typst-template.typ
  - data-pipeline/R/report/generate_brands.py
  - data-pipeline/R/report/maps_raster.R
  - data-pipeline/R/report/maps_vector.R
  - data-pipeline/R/report/sections.R
  - data-pipeline/R/report/template.qmd
  - data-pipeline/R/tests/test_maps_raster.R
  - data-pipeline/R/tests/test_maps_vector.R
  - data-pipeline/R/tests/test_sections.R
  - data-pipeline/R/tests/test_theme_llexplorer.R
  - data-pipeline/R/theme_llexplorer.R
  - data-pipeline/sync.py
  - data-pipeline/tests/test_pipeline_outputs.py
  - data-pipeline/tests/test_report_tokens.py
  - data/report_tokens.json
findings:
  critical: 1
  warning: 3
  info: 2
  total: 6
status: issues_found
---

# Phase 12: Code Review Report

**Reviewed:** 2026-08-12
**Depth:** standard
**Files Reviewed:** 45
**Scope note:** SUMMARY.md frontmatter extraction (Tier 2) failed silently because this
project's SUMMARY.md files use CRLF line endings, which the workflow's frontmatter regex
does not match. The workflow's `--grep="12"` fallback (Tier 3) also failed, matching
hundreds of unrelated commits. The reviewing agent instead computed an explicit
`git diff 39be2819d4665cd147cbb75d2e4e1031321ba5f8^..HEAD`, filtered to exclude planning
docs, lockfiles, and generated binary pipeline artifacts (PDFs, pmtiles, geojson, chart
JSON, xlsx). This is noted here so the workflow author can fix the CRLF-sensitive regex
and the overly broad commit-message grep for future runs.
**Status:** issues_found

## Summary

This phase adds a per-Living-Lab PDF report pipeline (Quarto + Typst + R, driven by a
new `report_tokens.json` bridge exported from the app's own JS colour/string modules) and
a small web-app surface (`DownloadReportCTA` + `useReportAvailability`) that links to the
committed PDFs. The engineering is unusually well-documented and the R ports of the app's
JS colour-resolution logic (FNV-1a hash, soil legend, economic quantile buckets) are
carefully cross-checked against the real app code via a dedicated Node parity script and
several Rscript test gates.

One genuine defect was found: a pinned expected-colour literal in
`data-pipeline/R/tests/test_sections.R` does not match the real, correct value in
`data/report_tokens.json` / `app/src/data/soil_legend.js`, which makes that test gate's
palette-drift check permanently fail (a false negative that will either be ignored by
developers or "fixed" by someone incorrectly changing the real palette to match the typo).
The remaining findings are quality/robustness issues: intentional but risky code
duplication (two independent ports of the same hash function, one silently shadowing the
other by source order) and some string-matching fragility in one report code path.

No security vulnerabilities, injection risks, or hardcoded secrets were found. Subprocess
calls in the Python/R render driver use argument lists (never shell strings), and the
report-download URL construction in the web app is properly slug/lang allow-listed before
use.

## Critical Issues

### CR-01: Pinned soil colour in test_sections.R does not match the real palette value, permanently failing the drift-detection gate

**File:** `data-pipeline/R/tests/test_sections.R:65`
**Issue:**
`EXPECTED_SOIL_GROUP_COLORS` pins `"sealed-surfaces" = "#4E545C"`, but the actual,
correct value — in both `app/src/data/soil_legend.js:31` (`'sealed-surfaces': '#4E5460'`)
and the generated `data/report_tokens.json:651` (`"sealed-surfaces": "#4E5460"`) — is
`#4E5460`, not `#4E545C`. These are different hex values (`...60` vs `...5C`), confirmed
programmatically (`'#4E5460' === '#4E545C'` is `false`).

`check_token_bundle_pinned()` (test_sections.R:77-114) compares the *entire*
`palettes$soil$groups` vector against `EXPECTED_SOIL_GROUP_COLORS` with `identical()`.
Because one pinned entry is wrong, this comparison will fail every single time the test
is run against the correct, unmodified `report_tokens.json` — the gate can never pass in
its current state. This defeats the stated purpose of the check (comment at
test_sections.R:74-76: "this is what makes 'temporarily change one colour in
report_tokens.json' a real, catchable mutation" — instead it makes *no* colour change,
correct or not, distinguishable, since the test is always red).

A test that is permanently red is worse than no test: it trains developers to ignore the
gate's output, and risks someone "fixing" it by changing the real, correct colour in
`soil_legend.js`/`report_tokens.json` to match the typo instead of fixing the typo.

**Fix:**
```r
EXPECTED_SOIL_GROUP_COLORS <- c(
  "ah-c-soils" = "#EFE0A2", "alluvial-soils" = "#009E73", "brown-soils" = "#8C4A16",
  "fens" = "#41382B", "gley-soils" = "#0072B2", "initial-soils" = "#C9A063",
  "luvisols" = "#E69F00", "pelosols" = "#B5453C", "podzols" = "#8C8FA8",
  "raised-bogs" = "#6B4B7A", "sealed-surfaces" = "#4E5460", "stagnic-soils" = "#A97FCB"
)
```

## Warnings

### WR-01: Duplicate, independently-maintained `ll_soil_color()` / FNV-1a hash implementations across two R modules

**File:** `data-pipeline/R/report/maps_vector.R:131-155` and
`data-pipeline/R/report/sections.R:352-388`
**Issue:**
Both `maps_vector.R` and `sections.R` independently define a function named
`ll_soil_color()` (and a private `*_fnv1a_hash()` helper) that ports
`app/src/data/soil_legend.js::getSoilColor()`/`fnv1aHash()` to R. They use two different
double-precision decomposition strategies for the 32-bit multiply
(`maps_vector.R`'s 16-bit-halves `.mv_mul_mod_2_32` vs. `sections.R`'s
`hash*2^24 + hash*403` decomposition of the FNV prime). Because both files are `source()`d
into the same session by `template.qmd` (lines 65-67), the one sourced last
(`maps_vector.R`) silently overwrites `sections.R`'s definition — a fact `template.qmd`
itself documents at lines 69-76 as deliberate, pre-existing, out-of-scope duplication.

This is currently safe only because both implementations happen to be correct and
produce identical output (verified by `test_sections.R`'s and `test_maps_vector.R`'s own
gates). But it is a real maintenance hazard: a future edit to the soil palette's hashing
behaviour in one file (e.g. fixing an edge case) will not automatically propagate to the
other, and nothing prevents the *next* accidental divergence (unlike CR-01 above, which
a test gate does catch when correctly pinned) from shipping unnoticed if it happens to
agree with both files' own self-tests but not with the real JS source.

**Fix:** Consolidate into a single shared function (e.g. move both to
`theme_llexplorer.R`, which every module already sources first) and delete the duplicate
from whichever of `maps_vector.R` / `sections.R` doesn't need it standalone.

### WR-02: `.ll_resolve_climate_line_variable()`'s `startsWith()` fallback is a fragile prefix match

**File:** `data-pipeline/R/report/sections.R:507-526`
**Issue:**
When matching a chart line's English label to a canonical climate variable id, the
function accepts either an exact match or `startsWith(kpi_label_en, line_label_en)`
(i.e. the KPI's full label starts with the chart line's shorter label). This is fine for
the four variables that exist today (verified distinct, non-prefixing labels), but the
function's own docstring explicitly frames this as avoiding "LineChart.jsx's WR-01
positional coupling" — i.e. this is meant to be the more robust path going forward. A
future climate variable whose English KPI label happens to share a common prefix with
another variable's chart-line label (e.g. two precipitation-related variables) would
silently resolve to the wrong `var_id`, and therefore the wrong theme colour — with no
test failure, since `check_soil_palette_parity()`/`check_bar_palette_parity()` don't cover
this code path and `test_sections.R`'s per-(slug,tab,lang) loop only asserts the chart
"produced a non-empty plot", not which colour each line received.

**Fix:** Either match on the chart's own stable `x_key`/variable identifier if the chart
JSON contract can be extended to carry one, or add an explicit equality-only mode and
fail loudly (as the function already does for "no match found") rather than accepting a
prefix match that could be coincidentally satisfied by an unrelated variable.

### WR-03: `DownloadReportCTA`/`useReportAvailability` build download URLs as page-relative paths with no `import.meta.env.BASE_URL` anchor

**File:** `app/src/components/DownloadReportCTA.jsx:21` and
`app/src/hooks/useReportAvailability.js:50`
**Issue:**
Both files build `data/reports/report-${slug}-${lang}.pdf` as a bare relative path (no
leading `./` or `import.meta.env.BASE_URL` prefix). This matches the pre-existing
convention already used by `useChartData`/`layers.js` elsewhere in the codebase, and is
currently safe only because `App.jsx` uses `HashRouter` (so the document's own URL path
never changes on client-side navigation, and every relative fetch always resolves
against the same base). This is not a new bug in this phase's diff, but it is a latent
correctness landmine: switching routers (e.g. to `BrowserRouter`, which several React SPA
migrations do to drop the `#` from URLs) would silently break every relative
`fetch`/`href` in the app, including this phase's own download link and availability
probe, with no compiler or lint warning.

**Fix:** Not blocking for this phase (consistent with existing convention), but worth a
one-line CLAUDE.md note ("all `data/...` fetch URLs are relative and depend on
`HashRouter`; do not switch routers without prefixing every one of them with
`import.meta.env.BASE_URL`") so a future router change doesn't silently break downloads.

## Info

### IN-01: `render_reports.py::enforce_report_budget()` writes oversized files to disk before failing

**File:** `data-pipeline/R/render_reports.py:246-284`
**Issue:** The per-file/total byte-budget check runs only after every requested render in
the invocation has already completed and been written to `data/reports/`. If a render
regresses (e.g. a much larger raster grid or a bloated font embed) and exceeds
`MAX_REPORT_BYTES`, the oversized PDF is already sitting in the working tree when the
`RuntimeError` is raised. A developer who doesn't notice the non-zero exit code (e.g. a
partially-read CI log) could `git add -A` and commit the oversized file anyway before the
budget failure is investigated.
**Fix:** Low priority — the failure message is actionable and this mirrors the documented
Phase 7/Phase 8 precedent. Consider deleting or truncating oversized outputs (or moving
them to a temp path first, renaming into `data/reports/` only after the budget check
passes) if this becomes a recurring real-world footgun.

### IN-02: `.ll_group_thousands()`/`.ll_format_number()` re-implement locale number formatting instead of using R's own `format()`/`prettyNum()`

**File:** `data-pipeline/R/report/sections.R:38-91`
**Issue:** This is a faithful, well-commented, deliberately hand-rolled port of
`Number(x).toLocaleString(locale)`'s exact behaviour (matching StatPanel.jsx byte-for-byte,
including trailing-zero trimming with no `toLocaleString`-style minimum-fraction-digits
floor). It works correctly for the current test matrix but is more code surface than
using `format(x, big.mark=..., decimal.mark=..., scientific=FALSE)` plus a
trailing-zero-trim regex would be. Not a defect — flagged only because a future
maintainer unfamiliar with the JS-parity requirement might "simplify" this into R's
built-in formatter and inadvertently break the trailing-zero-trimming/`sign: exceptZero`
parity with `StatPanel.jsx` that the tests currently lock.
**Fix:** No action needed; the extensive doc comment already explains why this exists.
Consider linking directly to `StatPanel.jsx`'s `toLocaleString` call site in the comment
for easier future cross-referencing.

---

_Reviewed: 2026-08-12_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
