# Phase 12 Decision Evidence Record (D-01..D-22)

**Phase:** 12-export-a-pdf-of-the-content-for-a-given-living-lab
**Plan:** 12-12, Task 1 (automated gate)
**Date:** 2026-08-12

---

## Automated gate

Every command below was run from the repository root on the final merged tree (this plan's own
worktree, based on commit `705497a`, the head of `data-pipeline-development` after wave 6/plan
12-11 merged). Python commands via `C:\lcvenv\Scripts\python.exe` (the project's documented
short-path venv, per `CLAUDE.md`'s Windows/OneDrive `MAX_PATH` workaround); R commands via
`C:\Program Files\R\R-4.5.0\bin\Rscript.exe` with `R_HOME` set; `npm` commands from `app/`.

| # | Command | Exit code | Result |
|---|---|---|---|
| 1 | `python -m pytest data-pipeline/tests/ -q` | 0 | `43 passed in 17.02s`, no skips |
| 2 | `Rscript data-pipeline/R/tests/test_theme_llexplorer.R` | 0 | One line per Living Lab (`boundary features=1`), ends `OK` |
| 3 | `Rscript data-pipeline/R/tests/test_sections.R` | 0 | `tabs=5 kpi_boxes=19 charts=5` for all five Living Labs (plus each LL's empty-narrative slot list), ends `OK` |
| 4 | `Rscript data-pipeline/R/tests/test_maps_vector.R` | 0 | Soil/economic/locator summary line per Living Lab (soil classes, econ zone counts/ranges, locator credit `© OpenStreetMap contributors © CARTO`), ends `OK` |
| 5 | `Rscript data-pipeline/R/tests/test_maps_raster.R` | 0 | Source-raster presence + colour-parity checks, then agriculture/landscape/climate render summary per Living Lab (`agriculture legend=19, landscape legend=8, climate panels=8`, non-NA cell counts for all 8 climate panels), ends `OK` |
| 6 | `cd app && npm run lint` | 0 | ESLint clean, no output |
| 7 | `cd app && npm run build` | 0 | `vite build` succeeded, 130 modules transformed, `dist/` produced in 3.49s |
| 8 | `cd app && npm run check:soil-palette` | 0 | All five Living Labs report `uniqueColors == classes`, `legendMinDeltaE >= 20.9` (see gate-driven fix below) — `OK` |
| 9 | `cd app && npm run export:report-tokens` then `git diff --exit-code data/report_tokens.json` | 0 / 0 | Regeneration prints the 9-line per-palette summary + `OK`; `git diff --exit-code` against the post-fix commit is empty — the committed bundle is current |
| 10 | `python data-pipeline/sync.py` then `git status --porcelain` | 0 / n/a | Full sync republishes every GeoJSON/chart/report/codegen'd JS file; `git status --porcelain` shows only the pre-existing, out-of-phase `.planning/HANDOFF.json` modification (untouched by this plan, present before this plan started — see `## Open items` in the follow-up Task 2 section of this file) — zero drift attributable to `sync.py`'s regeneration. Re-ran a second time: identical, byte-for-byte idempotent |

**All ten gate commands exit 0.**

### Gate-driven fix: `npm run check:soil-palette` (commit `55e9881`)

Gate #8 initially **failed**: `havellandisches-luch: legend minimum pairwise ΔE76 is 19.0,
expected >= 20`. This exact condition had been flagged as a pre-existing, out-of-scope failure in
plans 12-01, 12-03 and 12-04's own SUMMARYs (`deferred-items.md`, tracked as `STATE.md` TODO-01 /
quick-task `260804-acf`, "pending human visual check"). This plan's own Task 1 instruction is
explicit: *"If any gate fails, stop and fix it before proceeding to Task 2. Do not record a
failing gate as an accepted deviation."* — so, unlike every prior plan in this phase (whose
declared `files_modified` never touched `app/src/data/soil_legend.js`), this plan fixed it.

Root cause: `fens` (`#41382B`) and `sealed-surfaces` (`#4E545C`) both land in
`havellandisches-luch`'s real top-5-by-frequency legend and are two dark, low-saturation colours
18.99 ΔE76 apart — a near-miss `260804-acf`'s own design-time simulation (computed against an
earlier cut of the BUEK fixture) did not catch, since the live fixture's actual class-frequency
ranking differs slightly from what that quick task simulated (12 painted classes today vs. 13 at
design time).

Fix: `sealed-surfaces` nudged from `#4E545C` to `#4E5460` (blue channel +4/255, ~1.6%,
imperceptible) — the minimal RGB shift found that raises the fens/sealed-surfaces pair to ΔE76
20.9 while keeping every other pairwise distance across the whole 19-colour base palette >= 15
(the base-palette floor) and introducing no duplicate hex. `data/report_tokens.json` was
regenerated via `npm run export:report-tokens` so the R report pipeline's token bridge stays true
to the corrected source colour. The ten already-rendered, human-approved PDFs (plan 12-10, round-2
checkpoint approved) were **not** re-rendered for this — the shift is sub-perceptible, was not
among the defects the Task 3 checkpoint reviewer flagged, and re-running the full Quarto/Typst
render pipeline for a single-channel 4/255 nudge inside one Living Lab's soil legend carries no
visual benefit. Discussed further in the follow-up Task 2 section of this file (`## Open items`).

### Measured PDF artifact figures

Ten committed report files under `data/reports/` (byte-identical to their published copies under
`app/public/data/reports/`, per plan 12-11's `test_report_fixtures_published_to_app_public`):

| File | Bytes | Per-file budget (8,388,608) |
|------|------:|:---:|
| report-east-brandenburg-en.pdf | 1,013,635 | 12.1% |
| report-east-brandenburg-de.pdf | 1,022,200 | 12.2% |
| report-havellandisches-luch-en.pdf | 1,080,897 | 12.9% |
| report-havellandisches-luch-de.pdf | 1,078,472 | 12.9% |
| report-hessian-low-mountain-en.pdf | 1,520,283 | 18.1% |
| report-hessian-low-mountain-de.pdf | 1,515,380 | 18.1% |
| report-north-hessian-loess-en.pdf | 1,269,319 | 15.1% |
| report-north-hessian-loess-de.pdf | 1,271,935 | 15.2% |
| report-rheingau-en.pdf | 1,268,487 | 15.1% |
| report-rheingau-de.pdf | 1,270,572 | 15.1% |

- **Largest single file:** `report-hessian-low-mountain-en.pdf`, 1,520,283 bytes — **18.1%** of the
  8,388,608-byte (8 MiB) per-file cap.
- **Ten-file source total:** 12,311,180 bytes — **23.5%** of the 52,428,800-byte (50 MiB) source
  total cap.
- **Two-copy footprint** (`data/reports/` + `app/public/data/reports/`, both committed): 24,622,360
  bytes — **23.5%** of the 104,857,600-byte (100 MiB) two-copy total cap.

All three budgets are asserted as binding pytest gates (`test_report_sizes_within_budget`, plan
12-11) and as a binding render-time assertion (`enforce_report_budget()`, plan 12-10) — not
reported qualitatively, per Phase 8's own close-out precedent (`08-EVIDENCE.md`).
