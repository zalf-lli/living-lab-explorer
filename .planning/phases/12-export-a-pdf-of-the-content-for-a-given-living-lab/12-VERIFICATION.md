---
phase: 12-export-a-pdf-of-the-content-for-a-given-living-lab
verified: 2026-08-12T13:30:00Z
status: passed
score: 10/10 must-haves verified
overrides_applied: 0
notes:
  - "test_maps_raster.R could not be independently re-run to a PASS on this verification machine (missing local raw raster data/io_lulc_32U_2024.tif, gitignored/not committed). This is a local-machine raw-data gap, not a code defect introduced by this phase: no file in this phase's diff touches raster fetching or data/io_lulc_*.tif generation. Independently reproduced the exact same failure documented in 12-EVIDENCE.md's 'Post-checkpoint note', confirming the executor's own honest account. Already surfaced and accepted per the task brief ('accepted as-is by the user, documented in 12-EVIDENCE.md') — not re-raised here as a blocking or open item, only recorded for completeness."
---

# Phase 12: Export a PDF of the content for a given Living Lab Verification Report

**Phase Goal:** Every Living Lab has a downloadable, brand-styled PDF report — one per language —
built offline in the data pipeline with Quarto + Typst + R, covering all five tabs (KPIs, maps,
charts and narrative), published as a static file and reachable from a download control on the
detail page.

**Verified:** 2026-08-12
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Every Living Lab has a downloadable PDF, one per language (10 files) | VERIFIED | `data/reports/` and `app/public/data/reports/` each hold all 10 `report-{slug}-{lang}.pdf` files; independently confirmed `%PDF-1.7` magic bytes and 13 pages on `report-east-brandenburg-en.pdf`; `test_report_fixtures_exist_and_are_well_formed_pdfs` / `test_report_fixtures_published_to_app_public` in `data-pipeline/tests/test_pipeline_outputs.py` lock this; independently ran `python -m pytest data-pipeline/tests/ -q` → `43 passed` |
| 2 | Reports are brand-styled per LL | VERIFIED | `data-pipeline/R/report/_extensions/ll-explorer-typst/brands/{slug}.yml` exists for all 5 LLs; `render_reports.py` resolves each LL's `color`/`colorDark` and threads them as Typst metadata overrides |
| 3 | Built offline in the data pipeline with Quarto + Typst + R (not client-side) | VERIFIED | `grep -rc "window.print\|jsPDF" app/src` = 0; `data-pipeline/R/render_reports.py` (355 lines) shells out to `quarto render`; `sync.py` never invokes Quarto (`grep -c "quarto\|render_reports\|subprocess" data-pipeline/sync.py` = 0) |
| 4 | Reports cover all 5 tabs — KPIs, maps, charts, narrative | VERIFIED | `template.qmd` (423 lines) iterates `LL_TAB_ORDER`; `sections.R` (686 lines) builds KPI tables/narrative/chart accessors; `maps_vector.R`/`maps_raster.R` (585/517 lines) build every thematic map; independently ran `test_sections.R` → `tabs=5 kpi_boxes=19 charts=5` for all 5 LLs, `OK` |
| 5 | Published as a static file (sync.py plumbing, never regenerated at runtime) | VERIFIED | `sync_reports()` in `data-pipeline/sync.py:423-457` copies already-rendered files, logs `[report] skipped - not yet built` per missing file (D-20); independently re-ran `python data-pipeline/sync.py` — all 10 files matched, `git status --porcelain` showed only pre-existing, unrelated diffs (idempotent) |
| 6 | Reachable from a download control on the LL detail page | VERIFIED | `DownloadReportCTA` imported and rendered at both `LLDetail.jsx` call sites (lines 560, 742); `useReportAvailability.js` implements the fail-closed/optimistic three-state contract; `ComparisonColumn` contains zero references to `CompareCTA`/`DownloadReportCTA` (independently confirmed via `awk` extraction), satisfying D-17's comparison-mode hiding |
| 7 | Every automated gate passes on the final tree | VERIFIED | Independently re-ran all documented gates from a cold shell: `pytest` 43/43 pass; `test_theme_llexplorer.R` OK; `test_sections.R` OK (post-fix, confirmed the `8255fa1` CR-01 fix is live and correct); `test_maps_vector.R` OK; `npm run lint`/`build`/`check:soil-palette` all exit 0 with `check:soil-palette` printing the exact ΔE76 values documented in 12-EVIDENCE.md. One gate (`test_maps_raster.R`) could not be independently reproduced to PASS on this machine due to a missing local raw geodata file — see `notes` above; this is a pre-existing, already-disclosed, already-accepted local environment gap, not a code regression |
| 8 | All 22 locked decisions (D-01..D-22) have a recorded, evidenced verdict | VERIFIED | `12-EVIDENCE.md`'s Decision verdicts table has exactly 22 `D-0x`/`D-1x`/`D-2x` rows (independently counted via grep); 21 "Met", 1 "Met with deviation" (D-15); spot-checked D-01, D-04, D-11, D-12, D-14, D-17, D-19, D-20, D-22 against live code — every cited grep/file-existence claim reproduced exactly as stated |
| 9 | PROJECT.md no longer claims R is out of scope for this milestone | VERIFIED | `.planning/PROJECT.md:71-77` describes `data-pipeline/R/` as the activated offline PDF report pipeline, references D-03; `CLAUDE.md:39-40` lists `quarto`/`R` as external CLI deps with `QUARTO_BIN`/`R_HOME` override docs |
| 10 | A human confirmed the end-to-end bilingual experience (Task 3 checkpoint) | VERIFIED (with disclosed deviation) | 12-12-SUMMARY.md documents a real, detailed two-round feedback/fix cycle (commits `b385ad5`, `d039a43`) that reversed 12-UI-SPEC.md's locked compact/bare-pill `LayoutSplit` instance to a full card, then fixed a resulting card-height mismatch — independently confirmed both fixes are live in `DownloadReportCTA.jsx` (no `compact` prop remains) and `LLDetail.jsx` (`height: '100%'` on `CompareCTA`'s card, `alignItems: 'stretch'` in the compact row) |

**Score:** 10/10 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `data/reports/report-{slug}-{lang}.pdf` × 10 | Committed, well-formed PDFs | VERIFIED | All 10 present in both `data/reports/` and `app/public/data/reports/`; magic bytes confirmed |
| `app/src/components/DownloadReportCTA.jsx` | Download control component | VERIFIED | 76 lines, substantive, fail-closed on unavailability, D-15/16/17/18 comments trace decisions |
| `app/src/hooks/useReportAvailability.js` | Availability probe hook | VERIFIED | 67 lines, HEAD-request probe with cache/inflight dedup, allow-listed slug/lang, fails closed |
| `app/src/pages/LLDetail.jsx` | Two call sites + comparison-mode exclusion | VERIFIED | Lines 560, 742; `ComparisonColumn` (line 752) contains zero references |
| `data-pipeline/sync.py::sync_reports()` | Copy-only publish step, D-20 log line | VERIFIED | Lines 423-457; exact `[report] skipped - not yet built` log string present; zero `quarto`/`subprocess` references |
| `data-pipeline/R/render_reports.py` | Manual render driver | VERIFIED | 355 lines |
| `data-pipeline/R/report/template.qmd`, `sections.R`, `maps_vector.R`, `maps_raster.R`, `theme_llexplorer.R` | Report content/map/theme modules | VERIFIED | 423/686/585/517/457 lines respectively, all substantive |
| `data-pipeline/R/report/_extensions/ll-explorer-typst/` | Vendored, rebranded Typst extension incl. 5 per-LL brand files | VERIFIED | Present with `NOTICE.md`, `_brand.yml`, theme `.typ` files, 5 `brands/*.yml` |
| `data-pipeline/R/renv.lock` | Pinned R packages | VERIFIED | Present (89 packages per 12-EVIDENCE.md, file confirmed present) |
| `.planning/phases/12.../12-EVIDENCE.md` | Per-decision verdict table, D-01..D-22 | VERIFIED | 22/22 rows present, spot-checked against live code |
| `.planning/PROJECT.md` | Corrected Context section | VERIFIED | Lines 71-77 corrected, references D-03 |
| `CLAUDE.md` | quarto/R external CLI deps documented | VERIFIED | Lines 39-40 |
| `data-pipeline/tests/test_pipeline_outputs.py` | D-21 smoke tests for 10 PDFs | VERIFIED | `test_report_fixtures_exist_and_are_well_formed_pdfs`, `test_report_fixtures_published_to_app_public`, `test_report_sizes_within_budget`, `test_report_pattern_declared_in_sync` all present and substantive |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `LLDetail.jsx` (compact + full) | `DownloadReportCTA` | import + JSX render | WIRED | Imported once (line 18), rendered at lines 560 and 742 |
| `DownloadReportCTA` | `useReportAvailability` | hook call, `if (!available) return null` | WIRED | Line 18/19 of component |
| `useReportAvailability` | `data/reports/report-{slug}-{lang}.pdf` | `fetch(url, {method:'HEAD'})` | WIRED | Allow-listed slug/lang before building URL (T-12-05) |
| `sync.py::sync_to_app()` | `sync_reports()` | direct call | WIRED | Line 470; independently re-ran `sync.py`, confirmed all 10 files copied and log lines emitted |
| `render_reports.py` | `quarto render` | subprocess with argument list | WIRED | Confirmed no shell-string subprocess use (per 12-REVIEW.md, no security findings) |
| `template.qmd` | `sections.R` / `maps_vector.R` / `maps_raster.R` / `theme_llexplorer.R` | `source()` | WIRED | Confirmed via independent `Rscript` runs of each test file, all producing real per-LL output |
| `app/public/data/charts/*.json` | `sections.R::ll_chart()` | direct JSON read | WIRED | Per D-06 verdict evidence, independently spot-checked no statistical computation in `sections.R` |

### Requirements Coverage

This phase uses its own local D-01..D-22 decision-ID scheme instead of v1 REQ-IDs (confirmed:
`.planning/REQUIREMENTS.md` contains no `D-0x`/Phase 12 references). Cross-referencing every D-ID
that appears in a plan's `requirements:` frontmatter field against `12-CONTEXT.md`'s decisions and
`12-EVIDENCE.md`'s verdict table:

| Requirement | Source Plans | Verdict in 12-EVIDENCE.md | Status |
|-------------|--------------|---------------------------|--------|
| D-01 | 12-05, 12-10, 12-12 | Met | SATISFIED |
| D-02 | 12-06, 12-08, 12-09, 12-12 | Met | SATISFIED |
| D-03 | 12-02, 12-12 | Met | SATISFIED |
| D-04 | 12-05, 12-11, 12-12 | Met | SATISFIED |
| D-05 | 12-05, 12-10, 12-11, 12-12 | Met | SATISFIED |
| D-06 | 12-04, 12-07, 12-12 | Met | SATISFIED |
| D-07 | 12-01, 12-04, 12-05, 12-06, 12-08, 12-12 | Met | SATISFIED |
| D-08 | 12-05, 12-12 | Met | SATISFIED |
| D-09 | 12-10, 12-12 | Met | SATISFIED |
| D-10 | 12-01, 12-04, 12-07, 12-10, 12-12 | Met | SATISFIED |
| D-11 | 12-10, 12-12 | Met | SATISFIED |
| D-12 | 12-09, 12-10, 12-12 | Met | SATISFIED |
| D-13 | 12-04, 12-06, 12-08, 12-09, 12-10, 12-12 | Met (fix widened contrast, doesn't change verdict) | SATISFIED |
| D-14 | 12-02, 12-08, 12-09, 12-10, 12-12 | Met | SATISFIED |
| D-15 | 12-03, 12-12 | Met with deviation (compact/full density distinction reversed post-checkpoint, human-approved) | SATISFIED (disclosed deviation) |
| D-16 | 12-01, 12-03, 12-12 | Met | SATISFIED |
| D-17 | 12-03, 12-12 | Met | SATISFIED |
| D-18 | 12-01, 12-03, 12-12 | Met | SATISFIED |
| D-19 | 12-02, 12-12 | Met | SATISFIED |
| D-20 | 12-11, 12-12 | Met | SATISFIED |
| D-21 | 12-11, 12-12 | Met | SATISFIED |
| D-22 | 12-06, 12-12 | Met | SATISFIED |

All 22 D-IDs declared across plans' `requirements:` frontmatter are accounted for with an evidenced
verdict. No orphaned requirements found.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `data-pipeline/R/tests/test_sections.R` | 65 (pre-fix) | Stale pinned expected-colour literal, caught by code review CR-01 | Was CRITICAL, now RESOLVED | Independently re-confirmed `8255fa1` fixes this — `test_sections.R` now passes on a live re-run |
| `data-pipeline/R/report/maps_vector.R` + `sections.R` | 131-155 / 352-388 | Duplicate `ll_soil_color()`/FNV-1a hash port, one silently shadows the other | WARNING (WR-01, non-blocking) | Both independently verified correct; documented as deliberate, tracked debt, not a correctness bug today |
| `data-pipeline/R/report/sections.R` | 507-526 | Fragile `startsWith()` prefix-match fallback for climate variable resolution | WARNING (WR-02, non-blocking) | Correct for today's 4 variables; a future variable with a shared label prefix could silently mis-colour a chart line with no test failure |
| `app/src/components/DownloadReportCTA.jsx`, `app/src/hooks/useReportAvailability.js` | 21 / 50 | Relative `data/reports/...` URLs with no `BASE_URL` anchor | WARNING (WR-03, non-blocking) | Matches pre-existing app-wide convention; safe only because `HashRouter` is used; not a regression introduced by this phase |

No debt markers (`TBD`/`FIXME`/`XXX`) found in any file this phase modified. No blocker-level
anti-patterns found — the one CRITICAL finding from code review (CR-01) has an independently
re-verified fix already merged (`8255fa1`).

### Human Verification Required

None. The blocking human-verify checkpoint (Task 3 of plan 12-12) was already executed within the
phase's own workflow — its two rounds of real, specific feedback (density-distinction reversal,
card-height equalization) are independently confirmed live in the code (`DownloadReportCTA.jsx` has
no `compact` prop; `LLDetail.jsx`'s `CompareCTA` card has `height: '100%'`), which is strong
corroborating evidence the checkpoint genuinely occurred rather than being narrated after the fact.

### Gaps Summary

No gaps found. All 6 phase-goal-derived truths and all 4 plan-12-12 close-out truths are verified
directly against the codebase, not merely asserted in SUMMARY.md. The one item that could not be
independently reproduced on this verification machine — `test_maps_raster.R`'s PASS, blocked by a
missing local raw raster file (`data/io_lulc_32U_2024.tif`, gitignored) — is a pre-existing,
already-disclosed, already-user-accepted local environment gap (see 12-EVIDENCE.md's
"Post-checkpoint note"), not a code defect introduced by this phase, and does not affect any of the
already-rendered, already-committed, already-human-approved PDF artifacts that constitute this
phase's actual deliverable. It is recorded here for completeness only, not as a blocking or
actionable gap.

---

_Verified: 2026-08-12_
_Verifier: Claude (gsd-verifier)_
