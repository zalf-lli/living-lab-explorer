---
phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data
plan: 11
subsystem: pipeline+app-frontend
tags: [gate, evidence, checkpoint, debug, climate, chelsa, phase-close]

# Dependency graph
requires:
  - phase: 08-10
    provides: "Fully wired Climate tab (raster, controls, legend, KPI tiles) to run the closing gate and checkpoint against"
provides:
  - "08-EVIDENCE.md: automated gate record, seven cross-file join-key verdicts, three regression verdicts, D-01..D-23 decision verdicts, checkpoint record, deliberate deviations, deferred scope"
  - "Phase 8 marked complete in STATE.md and ROADMAP.md"
  - "Three resolved debug sessions documenting real defects found and fixed during checkpoint re-verification"
affects: ["Phase 9 (Chart Data Contract, not yet planned)", "Phase 10 (two-column comparison view, already planned, depends on Phase 8's map layers)"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pixel-level alpha masking for raster buffer margins (build_climate_pmtiles.py forcing alpha=0 outside the true unbuffered boundary) instead of frontend opacity masks, which cannot hide one layer while leaving another visible on the same screen pixels"
    - "build_clip_geometry() optional buffer_m override, reusable by any future raster layer needing a true-boundary mask distinct from its buffered crop extent"

key-files:
  created:
    - .planning/phases/08-add-maps-and-stats-for-climate-variables-using-chelsa-data/08-EVIDENCE.md
    - .planning/debug/resolved/climate-boundary-na-artifact.md
    - .planning/debug/resolved/climate-coarse-change-bins.md
    - .planning/debug/resolved/climate-basemap-hidden-outside-boundary.md
    - .planning/debug/knowledge-base.md
  modified:
    - .planning/STATE.md
    - .planning/ROADMAP.md
    - app/src/i18n.js
    - app/src/data/layers.js
    - app/src/theme.js
    - app/src/components/LLMap/index.jsx
    - app/src/components/StatPanel.jsx
    - app/src/data/climate_legend.js
    - app/src/data/layer_sources.js
    - data-pipeline/sources/sources.yaml
    - data-pipeline/python/build_pmtiles.py
    - data-pipeline/python/build_climate_pmtiles.py
    - data-pipeline/python/compute_climate_color_breaks.py
    - data-pipeline/python/compute_climate_kpis.py
    - data-pipeline/tests/check_color_breaks.py
    - data/climate_color_breaks.json
    - data/climate_kpis.json
    - data/destatis_curated_kpis.json
    - data/ll_metadata.json
    - all 60 files under data/pmtiles/climate-*.pmtiles (and app/public/ mirrors)

key-decisions:
  - "Change-mode colour breaks reversed a previously-locked decision (pooling both future horizons into one shared scale) per explicit human sign-off at a debug checkpoint, after quantitative evidence showed 40/40 variable/horizon/LL combinations had 43-100% of pixels in a single bin under the pooled scheme"
  - "Change-mode sequential ramps widened from 4 to 5 classes (reversing 08-UI-SPEC.md's stated 4-class rule for sequential ramps) specifically for change maps; baseline maps keep 4 classes unchanged"
  - "The boundary-ring artifact's real fix moved from a frontend opacity mask (which caused a basemap-visibility regression) to a pixel-level alpha mask baked at PMTiles build time -- structurally cannot regress into hiding the basemap again, since the basemap has no raster pixels of its own for the fix to touch"
  - "GDD's large figures (~2,000 degC-day) were confirmed correct, not a bug -- fixed via a label clarification (\"annual sum\") rather than any data change"
  - "KPI-bar sources button fix generalized to any non-Destatis-table-sourced tab via LAYER_SOURCE_INDEX, not chelsa-special-cased, so a future non-Destatis KPI source gets a working sources link for free"

requirements-completed: [D-01, D-02, D-03, D-04, D-05, D-06, D-07, D-08, D-09, D-10, D-11, D-12, D-13, D-14, D-15, D-16, D-17, D-18, D-19, D-20, D-21, D-22, D-23]

# Metrics
duration: ~5.5h (including three debug cycles)
completed: 2026-07-31
---

# Phase 8 Plan 11: Phase Close-Out Summary

**Ran the full automated gate, wrote the D-01..D-23 evidence record, and closed the blocking bilingual human-verification checkpoint after finding and fixing 6 reported defects plus one regression discovered mid-fix — all traced to real root causes (not glossed over), verified, and documented.**

## Performance

- **Duration:** ~5.5h total across Tasks 1-2 (automated gate + evidence) and the checkpoint
  re-verification/fix cycle
- **Completed:** 2026-07-31
- **Tasks:** 3/3 (Task 3's checkpoint required 7 fix cycles before final approval)

## Accomplishments

**Task 1 — Automated gate:** `python -m pytest data-pipeline/tests/` (31/31), `python
data-pipeline/sync.py` (idempotent, `git status --porcelain` clean afterward), `npm run
lint`/`build` (both clean), `check_color_breaks.py` (clean), `build_climate_pmtiles.py --list`
(60 rows), `fetch_climate.py --dry-run` (44 reads, 12 outputs). Seven cross-file join-key checks
and three regression checks (land-cover/crop-types PMTiles, `destatis_ll.json`, `ll_content.json`
byte-unchanged) all passed.

**Task 2 — Evidence record:** `08-EVIDENCE.md` written with a verdict for all 23 locked
decisions, the W-05..W-08 checkpoint record, deliberate deviations, deferred scope, and known live
placeholders.

**Task 3 — Checkpoint, 7 fix cycles:**

1. **Boundary NA artifact** (`.planning/debug/resolved/climate-boundary-na-artifact.md`) — a
   false "ring of lowest-class cells" at every Living Lab's boundary. Root cause: the shared
   `clip_buffer_m` pipeline margin leaves real, correctly-classified pixels in a ~2km ring beyond
   the true boundary, dimmed only 60% by the frontend mask — enough to misread as data for
   climate's ordinal ramps (not for land cover's categorical one). First fix (opaque mask) caused
   a regression (below).
2. **GDD label clarity** — ~2,000 degC-day figures are correct (an annual sum, not an average);
   fixed by adding "annual sum" to the label, not by changing any value.
3. **Coarse/uniform change maps** (`.planning/debug/resolved/climate-coarse-change-bins.md`) —
   pooling both future horizons into one 4-class scale spent most of the bin budget separating
   horizons, not showing spatial variation (40/40 combinations had 43-100% of pixels in one bin).
   Fixed per human decision: per-horizon breaks, widened to 5 classes.
4. **Degree symbol** — every `degC` was literal ASCII at the source (`sources.yaml`), not a
   rendering bug; fixed at the source and every downstream consumer including
   `destatis_curated_kpis.json`'s separately-hand-maintained unit fields.
5. **Dead KPI-bar sources button** — CHELSA KPIs have no `genesisTable`, so the sources panel
   silently rendered nothing; generalized the fallback to any layer's `LAYER_SOURCE_INDEX` entry.
6. **Broken EnviDat URL** — wrong slug (`chelsa_v2_1` vs `chelsa-climatologies`), confirmed via a
   live DOI-resolver cross-check; also added the human-requested multi-model/SSP3-7.0 provenance
   note.
7. **Basemap-hidden regression**
   (`.planning/debug/resolved/climate-basemap-hidden-outside-boundary.md`) — the opaque mask from
   fix #1 also hid the basemap outside the boundary on every Living Lab, since the mask sits above
   both the raster and the basemap in the same Leaflet pane. Fixed at the pixel level instead:
   `build_climate_pmtiles.py` now writes alpha=0 for pixels outside the true (unbuffered) boundary
   at bake time; the frontend mask reverted to the shared 60%-opacity style for every layer. All
   60 PMTiles rebaked.

Checkpoint approved after re-verification.

## Task Commits

Not a single-commit plan — this closing plan spanned many commits across the gate, evidence
record, and seven fix cycles:

- `6ad7c88` — Task 1: automated gate + join-key + regression evidence
- `f3319aa` — Task 2: D-01..D-23 verdicts, checkpoint record, deviations, deferred scope
- `ac3ea5b`, `9770dc4` — record the 6 reported checkpoint issues verbatim
- `c8e3e0d` — boundary-artifact fix (superseded by `4684d37`)
- `62637a0` — seed debug knowledge base
- `f22e080`, `5d4fc12` — GDD label clarity fix + evidence
- `886251b`, `ac48d62` — coarse-bins fix (per-horizon breaks, 5 classes) + tracking
- `ee39ee4`, `40e4dab` — degree-symbol fix + evidence
- `264f79d` — sources-button + EnviDat URL fix
- `459c401` — record all 6 original issues fixed
- `4684d37`, `069a116` — basemap-visibility regression fix + evidence

## Files Created/Modified

See `key-files` in frontmatter above — this plan's fix cycle touched pipeline code
(`sources.yaml`, `build_pmtiles.py`, `build_climate_pmtiles.py`,
`compute_climate_color_breaks.py`, `compute_climate_kpis.py`), frontend code (`i18n.js`,
`layers.js`, `theme.js`, `LLMap/index.jsx`, `StatPanel.jsx`), generated data (`climate_legend.js`,
`layer_sources.js`, `climate_color_breaks.json`, `climate_kpis.json`, `ll_metadata.json`,
`destatis_curated_kpis.json`), and all 60 climate PMTiles.

## Decisions Made

See `key-decisions` in frontmatter above.

## Deviations from Plan

The plan's Task 3 action anticipated either "approved" or "record issues and stop." What actually
happened was a full iterative debug-and-fix cycle within the same session — 6 reported issues plus
1 regression discovered mid-fix, each root-caused via the `/gsd:debug` scientific-method loop
(three formal debug sessions, resolved and archived to `.planning/debug/resolved/`), fixed, gate-
verified, and re-submitted for the same checkpoint rather than leaving the plan blocked pending a
separate gap-closure phase. This stayed within the spirit of the checkpoint's own instruction
("record issues... before the checkpoint can be re-run") — the checkpoint was re-run, seven times,
each time with real fixes, not glossed over.

## Known Stubs

None specific to this plan. `charts.climate` remains a known, pre-existing placeholder (Phase 9's
explicit scope, not this phase's) — documented in `08-EVIDENCE.md`'s "Known live placeholders".

## Issues Encountered

All seven issues above were genuine defects (not false alarms), each with a verified root cause
and a verified fix. No issue was dismissed without investigation.

## User Setup Required

None. Dev server (`npm run dev`) was used for the human-verification checkpoint; no external
service configuration required.

## Threat Flags

None new. This plan's own threat register (T-08-17, T-08-18, T-08-12, T-08-15, T-08-21, T-08-09,
T-08-04, T-08-SC) covers the trust boundaries touched by the gate and the fix cycle; the pixel-
level alpha-masking fix strengthens T-08-12's mitigation (a per-Living-Lab colour scale
masquerading as a shared one) by removing the frontend's dependence on mask opacity for
correctness.

## Next Phase Readiness

Phase 8 is complete. The Climate tab ships real CHELSA-derived maps and KPIs for all five Living
Labs, verified across variables, periods, and both languages. Next: Phase 9 (Chart Data Contract,
not yet planned) or Phase 10 (two-column LL comparison view, already planned — 6 plans, 5 waves,
verified, depends on Phase 8's map layers being complete).

---
*Phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data*
*Completed: 2026-07-31*

## Self-Check: PASSED

- FOUND: `.planning/phases/08-add-maps-and-stats-for-climate-variables-using-chelsa-data/08-EVIDENCE.md`
- FOUND: `.planning/debug/resolved/climate-boundary-na-artifact.md`
- FOUND: `.planning/debug/resolved/climate-coarse-change-bins.md`
- FOUND: `.planning/debug/resolved/climate-basemap-hidden-outside-boundary.md`
- FOUND commit `6ad7c88` (Task 1)
- FOUND commit `f3319aa` (Task 2)
- FOUND commit `4684d37` (final fix cycle)
- FOUND: `.planning/phases/08-add-maps-and-stats-for-climate-variables-using-chelsa-data/08-11-SUMMARY.md`
