---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: in_progress
stopped_at: Phase 8 Wave 4 (08-06, 08-07) complete — colour-break machinery + climate KPIs merged; Wave 5 (08-08, full PMTiles build) next
last_updated: "2026-07-30T12:30:00.000Z"
progress:
  total_phases: 15
  completed_phases: 9
  total_plans: 56
  completed_plans: 48
  percent: 61
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-04-29)

**Core value:** A researcher or stakeholder can open the app and immediately see accurate, up-to-date geodata and statistics for any of the five Living Labs without any server infrastructure.

**Current focus:** Phase 08 — add-maps-and-stats-for-climate-variables-using-chelsa-data

## Status

| Phase | Name | Status |
|-------|------|--------|
| 1 | LL Content System | Complete (2026-04-29) |
| 2 | BUEK Vector Pipeline | Complete (2026-04-30) |
| 2.1 | Soil Map Tab Integration | Complete (2026-04-30) |
| 2.2 | Soil Semantics & Translation | Complete (2026-04-30) |
| 3.1 | Data Source Research & User Validation | Inserted - ready to plan |
| 4 | Destatis Statistics Integration | Waves 1-2+6-7 complete; 11/17 KPIs real; Waves 3-5 ready (2026-07-25) — see Active Work |
| 5 | Protected areas as toggleable layer | Planned (2026-07-25) — 4 plans, 3 waves, 2 checkpoints, verified ✓ |
| 6 | Add land cover map | Complete (2026-07-26) — 5/5 plans, 4 waves, D-01..D-24 evidence recorded, bilingual checkpoint approved |
| 7 | Add BORIS land value maps as spatial layer for socio-economic tab | In progress — 8/9 plans complete (07-08 executed 2026-07-28: all five Living Labs fetched, committed, published, and locked behind a fixture regression test) |
| 8 | Add maps and stats for climate variables using CHELSA data | In progress (2026-07-30) — 7/11 plans complete: Waves 1-4 merged (08-01..08-07). Wave 4 (08-06 colour breaks + Pass-1 tiler, 08-07 climate KPIs) done; 30/30 tests passing. Wave 5 (08-08, full 60-PMTiles build) next |
| 9 | Chart Data Contract | Not planned yet (2026-07-27) |
| 10 | Two-column LL comparison view | Planned (2026-07-27) — 6 plans, 5 waves, 1 checkpoint, verified ✓ (0 blockers, 4 warnings) |

## Active Work

**Phase 8, Wave 4 complete (2026-07-30).** 08-06 built the shared cross-Living-Lab colour-break
machinery (`compute_climate_color_breaks.py` Pass 0 + `build_continuous_colormap()` +
`build_climate_pmtiles.py` Pass 1) and empirically resolved D-12's diverging-vs-sequential question:
against real built data, **all four variables (gdd, bio1, bio12, bio18) came back `sequential`** for
both baseline and change — no variable's five per-LL means crossed zero. This is a legitimate
empirical result, not a bug, but it differs from earlier docs' assumption that precipitation would
likely diverge — flag for `08-08`'s legend codegen. 08-07 built `compute_climate_kpis.py` (area-weighted
zonal mean per Living Lab) and caught a real bug while validating its own plausibility gate: `08-04`'s
`fetch_climate.py` never applied CHELSA's GDAL scale/offset tags, so every raster held raw scaled
integers instead of physical units (mean annual temperature was reading ~2820 instead of ~8.9 degC).
Fixed `_read_window()` to apply each file's own scale/offset, re-ran the full 12-raster acquisition,
and re-pinned all `sha256_by_derived` digests in `sources.yaml`. Both plans landed on the fix
independently (08-06's own draft found the same bug) — 08-07's already-merged, already-tested version
was kept as the single source of truth; 08-06's redispatch reused it rather than re-fixing it. Full
suite: 30/30 passing. **Next:** `/gsd:execute-phase 8 --wave 5` (08-08 — the real 60-PMTiles build).

**Session note:** the first 08-06 executor attempt stalled mid-run (paused on a background CHELSA
fetch) and its process was lost across a session boundary before it could finish or write a SUMMARY.
Its in-progress draft was checkpointed as a WIP commit before being superseded by a clean redispatch;
that WIP branch has since been deleted after the redispatch completed and merged. No work was lost.

**Phase 8, Wave 2 complete (2026-07-30).** 11 plans across 8 waves fill both halves of
the Climate tab from CHELSA: the `climate` placeholder in `app/src/data/layers.js:41` becomes a real
per-LL raster (60 PMTiles = 4 variables x 3 periods x 5 LLs), and the tab's two permanently-null KPI
slots (`agr_ch4_kt`, `agr_n2o_kt`) are dropped for four CHELSA-derived tiles mirroring the map
variables.

Research reversed one of the phase's own premises. `08-CONTEXT.md` called `chelsa_cmip6` an unvetted
GitLab dependency; it is in fact published on PyPI as `chelsa-cmip6==1.4` (the GitLab repo is the dev
version — user-corrected during planning). It *does* expose `.gdd()` at a 5 degC default matching
D-06, so GDD is not underivable — but only via a live cloud-compute path adding ~10 heavy
dependencies (xarray, dask, zarr, gcsfs, netcdf4, esgf-pyclient, google-cloud-storage), and its
formula sums raw temperatures on days above threshold rather than the textbook `sum(max(T - 5, 0))`.
A lighter static path research surfaced — pre-built CHELSA CMIP6 GeoTIFFs on WSL's public envicloud,
fetchable with the already-pinned `rasterio`/`requests`, zero new dependencies — covers bio1/bio12/bio18
but carries no GDD. Waves 1-2 are therefore a measure-then-decide spike (`08-01`) feeding a blocking
`checkpoint:decision` (`08-03`), copying Phase 7's `07-03`/`07-05` precedent verbatim.

**The GDD fork resolved to a fourth option nobody had planned for.** `08-01`'s live probe surfaced
`gdd5` — CHELSA's own directly-published static GDD-above-5degC file — which neither `08-CONTEXT.md`
nor `08-RESEARCH.md` knew about. At the `08-03` checkpoint (2026-07-30) the human chose `gdd5` over
`bio10`, `gdd-light`, and `gdd-heavy`. Because `gdd5` uses the same static per-variable acquisition
shape `08-04` already implements for `bio10`, this does **not** trigger the re-planning halt — no
`/gsd:plan-phase 8 --gaps` detour is needed, and `08-SPIKE.md` carries `## Phase status` (proceed),
not `## Phase halt`. W-06 (URL templates), W-07 (provenance text, with an explicit caveat that the
underlying CMIP6 GCM outputs' own WCRP Terms of Use were not independently re-verified) and W-08
(300s/read cap, ~5GB total transfer cap, 5degC GDD base) are all locked in `08-SPIKE.md`'s
`## Locked decisions` section regardless of the W-05 outcome.

**One required fix before Wave 3 runs:** `08-04-PLAN.md`'s Task 1 precondition text only recognizes
`bio10`/`gdd-light`/`gdd-heavy` as valid W-05 verdicts — it needs a one-line wording update to also
accept `gdd5`, the actual locked outcome. This was left unfixed by design (out of `08-03`'s declared
`files_modified` scope) and is flagged in both `08-SPIKE.md`'s `### W-05` subsection and
`08-03-SUMMARY.md`'s Deviations. `gdd5`'s per-file sizes (452-532MB) are notably larger than
`bio1`/`bio10`'s (~103MB for the whole 4-variable matrix) and no windowed-read cost has been measured
for it yet, so `08-04`'s W-08 budget-cap enforcement should be watched closely on first real run.

Two design surfaces have no analog anywhere in the codebase and are planned as real design work:
D-09's shared-across-all-LLs colour scale (a Pass-0 `compute_climate_color_breaks.py` pooling all five
LLs' pixels into committed breakpoints before any per-LL bake, plus a `build_continuous_colormap()`
sibling to `build_colormap()` — no Phase 6/7 precedent, since palette hex is baked into PNG pixels),
and `StatPanel.jsx`'s D-20 two-line delta tile. D-12's diverging-vs-sequential ramp split is settled
empirically from the five observed per-LL means, not hardcoded. Two volume gates are binding fail
assertions, not warnings: `08-04` halts on the W-08 transfer cap, `08-08` on a literal 209,715,200-byte
committed-footprint cap asserted inside its verify command. Plan-checker passed after one revision
(the open-fork blocker); decision coverage D-01..D-23 is 23/23. Next: apply the one-line `gdd5`
precondition fix to `08-04-PLAN.md`, then `/gsd:execute-phase 8 --wave 3` (or `/gsd:execute-phase 8`
to run all remaining waves).

**Phase 10 is planned and ready to execute (2026-07-27).** 6 plans across 5 waves turn the
placeholder "Add for comparison" button into a real two-column comparison. The view is a
`?compare=<slug>` param on the existing `/ll/:slug` route (no new route), with one shared layer-tab
row driving two columns, a comparison bar replacing the A/B switcher, and each column a compact
`LayoutStacked` reusing every existing component. `app/src/pages/LLDetail.jsx` is the hot file, so
plans `10-02` → `10-03` → `10-04` → `10-05` are strictly serialized across waves 2-5; only wave 1
(`10-01` i18n/StatPanel/BarChart props, `10-02` state lift + header) parallelizes. Wave 5 (`10-06`)
closes with a blocking bilingual human-verification checkpoint plus a D-01..D-29 evidence table.
The one structural refactor is lifting `useLayerState` out of the remount-keyed layout components so
the active tab survives LL swaps (D-09). Per-column map legends are a correctness requirement, not
styling — Phase 7 D-09 locks BORIS to per-LL quantile scales.

Planning surfaced two real defects: `Header` is rendered outside `<Routes>` (`App.jsx:27`) so its
`useParams()` returns `{}` and the active-pill highlight is dead code (fixed in `10-02` via
`useLocation()`); and `bySlug` is built with `Object.fromEntries`, so `?compare=__proto__` resolves
truthy — mitigated in `10-03` by an own-property `partnerCandidate.slug === compareSlug` identity
check. Plan-checker found 0 blockers and 4 informational warnings; the notable one is that
`ROADMAP.md` declares Phase 10 `Depends on: Phase 9`, but Phase 9 is not planned and Phases 7-8 are
not merged into this branch — the D-10 empty-state design degrades gracefully under exactly that
partial-completeness condition, so the plans still reach the Phase 10 goal. Reconcile the
ROADMAP/STATE sequencing when Phase 9 lands. Next: `/gsd:execute-phase 10`.

**Phase 7: 8/9 plans complete (2026-07-28).** 9 plans across 7 waves cover the BORIS
(Bodenrichtwert) land-value choropleth for the Socio-economic tab, built from live Brandenburg
(BORIS-BB) and Hessen (BORIS-HE) WFS services. Research flagged a blocking volume risk (verified
per-Living-Lab zone counts run 1,668-30,018 — 5x-80x denser than any prior vector layer), so waves
2-3 were a measure-then-decide spike (`07-03`) feeding a blocking `checkpoint:decision` (`07-05`) that
locked the geometry/size budget, the `has_current_value` recency rule, and the Hessen usage-code map
before any production fetch code was written. Plan `07-08` (2026-07-28) ran the full unfiltered fetch
across all five Living Labs, committed all ten GeoJSON copies (`data/geojson/` + published
`app/public/data/geojson/`), and locked the ten-key contract behind a new pytest regression test
(`test_boris_geojson_fixtures_exist_and_match_contract`, suite now 27/27 green). All five zone counts
landed within 5% of `07-RESEARCH.md`'s figures and both Brandenburg no-data shares reproduced the
locked W-02 figures within rounding. One flagged-but-not-blocking discrepancy: east-brandenburg's
committed size (33,948,983 bytes) exceeds `fetch_boris.py`'s rounded diagnostic constant
(33,000,000 bytes) but is 5,392 bytes under `07-SPIKE.md`'s own specific locked measurement for that
Living Lab (33,954,375 bytes) — see `07-08-SUMMARY.md` Deviations for full reasoning; flagged for
`07-09`'s evidence record and human sign-off. Wave 7 (`07-09`) closes with a blocking bilingual
human-verification checkpoint across all five Living Labs, now backed by real data end-to-end. Next:
`/gsd:execute-phase 7` to run `07-09`.

**Phase 6 is complete (2026-07-26).** Land cover from the Impact Observatory / Esri / Microsoft 10m
2024 dataset now fills the Landscape tab as five per-Living-Lab PMTiles files; crop types moved to a
renamed Agriculture tab; Landscape is the LL detail page's default tab. All 5 plans executed across 4
waves (06-01 dataset registration + build machinery, 06-02 sync.py wiring + actual PMTiles build, 06-03
frontend tab restructure, 06-04 pipeline `landuse`→`agriculture` rename, 06-05 full automated gate +
bilingual human-verify checkpoint). The reviewer approved the palette with no changes needed. All 24
locked decisions (D-01..D-24), the three deliberate deviations from literal CONTEXT wording, and the
phase's deferred scope (full-Germany backdrop, annual time series, live ESRI integration,
vector-to-raster fusion) are recorded in `06-EVIDENCE.md`. Remaining: `/gsd:execute-phase 6`'s
post-phase gates (code review, regression check, goal verification) still need to run.

**Phase 4: Waves 1, 2, 6, and 7 are complete and merged to `data-pipeline-development`** (04-01,
04-02, 04-06, 04-07 all have SUMMARY.md + passing tests, 7/7). Waves 3-5 (kpiByTab wiring into
ll_metadata.json, tab/i18n restructure, StatPanel UI component) are now ready to execute.

**Data availability final state (2026-07-24, after 04-07's Regionalstatistik.de table discovery):**
The 04-06 "0/15" result was a code-format mismatch, not a data gap — Regionalstatistik.de
publishes Kreis-level statistics as dash-coded tables (`data/tablefile`, format=ffcsv), not
GENESIS-Online-style cube codes. Searching with the correct format resolved 9 more slots.
**11 of 17 curated KPIs now carry real, live-fetched Kreis-level values** (all committed):

- landuse 4/4: land_area_cropland_ha, farms_count, farm_avg_size_ha, organic_pct
- soil 1/3: groundwater_abstraction_1000m3 (D-14 repurpose of the null groundwater_nitrate_mg_l
  slot, quick-task 260725-e1x, 2026-07-25 — see below)

- landscape 2/4: forest_area_ha, sealed_surface_pct
- economic 4/4: population_total, unemployment_rate_pct, household_income_eur, gdp_per_capita_eur
  (gdp restored to its original D-09 slot, replacing the 04-02 population-density substitute)

**6 slots remain genuinely null** — confirmed unavailable at Kreis level on BOTH Destatis
platforms after exhaustive prefix + keyword search: n_surplus_kg_ha, p_surplus_kg_ha, agr_ch4_kt,
agr_n2o_kt (GHG emissions are Länder-level only), natura2000_ha, nature_reserves_ha
(nature-conservation area stats are non-Destatis products). Nearest-miss candidates are
documented in 04-07-SUMMARY.md for human review. Filling these would require non-Destatis
sources (e.g. UBA, BfN, LAWA) — out of Phase 4's Destatis scope; candidates for a future phase
or the Phase 3.1 source-catalogue process. **Quick-task 260725-e1x (2026-07-25) live-verified the
three near-miss water tables (`32221-01-03-4`/`32221-02-01-4`/`32221-03-01-4`) that 04-07 had
only identified by catalogue title. All three confirmed as pure volume statistics (`1000 cbm`) --
`groundwater_nitrate_mg_l` (a concentration, `mg NO3/l`) can never be filled from any of them,
now a live-verified fact. However, `32221-01-03-4` carries an explicit live-verified
groundwater-specific abstraction-volume breakdown for all 14 project Kreise, so the Soil-tab slot
was repurposed (D-14 same-catalogue-group substitution) from `groundwater_nitrate_mg_l` to
`groundwater_abstraction_1000m3`, which now resolves via Regionalstatistik.de. Verdict
`REPURPOSE:groundwater_abstraction_1000m3` recorded in
`.planning/quick/260725-e1x-investigate-the-near-miss-regionalstatis/260725-e1x-DECISION.md`.
Null-slot count decreased from 7 to 6; the 17-entry manifest and locked per-tab counts
(`{landuse:4, soil:3, climate:2, landscape:4, economic:4}`) are unchanged.**

**Next step:** run `/gsd:execute-phase 4` to execute Waves 3-5 (04-03 kpiByTab wiring, 04-04
tab/i18n restructure, 04-05 StatPanel UI — 04-05 has a human-verify checkpoint). The UI will show
real values for 11/17 KPIs; the 6 null slots need a UI decision (hide vs. "data not available"
state) which the UI-SPEC/plans already contemplate.

Phase 03.1 Wave 2 completed on 2026-06-02. The source review catalogue is now populated with citation-backed fact columns, advisory `(AI)` assessment columns, and an updated `source_catalogue` xlsx tab ready for human review.

Phase 03.1 Wave 3 is paused at its human-verify checkpoint: reviewers must fill `decision`, `priority`, and `rationale` for each candidate row in `data/variables_catalogue.xlsx`.

Phase 2.2 completed on 2026-04-30 and replaced the shallow German-only soil lookup with a richer bilingual semantic contract.

- Pipeline outcome: `data-pipeline/python/soil_semantics.py` now centralizes normalization, translation, special-area handling, and compact profile summaries sourced from the BUEK250 SQLite schema
- Fixture outcome: all five committed `data/geojson/buek250-*.geojson` files and the matching runtime copies in `app/public/data/geojson/` now expose semantic fields such as `feature_kind`, `soil_label_*`, `soil_group_*`, and provenance-aware summaries
- Frontend outcome: the soil map now styles and labels features from the semantic contract first, with Living-Lab-specific legend entries and semantic tooltips
- Next suggested step: run `$gsd-plan-phase 3.1` to define the iterative AI-plus-end-user research loop for selecting geodata and statistical sources before subsequent integrations

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260725-e1x | Investigate near-miss Regionalstatistik.de water tables (32221-01-03-4/02-01-4/03-01-4) as replacements for the null groundwater_nitrate_mg_l KPI slot | 2026-07-25 | ab920f8 | [260725-e1x-investigate-the-near-miss-regionalstatis](./quick/260725-e1x-investigate-the-near-miss-regionalstatis/) |
| 260727-fast | Remove all preliminary-data flags from app UI and pipeline; recast the design-option bar as a subtle "Change layout" switcher | 2026-07-27 | a37a9b4 | (inline) |
| 260727-fast2 | Remove mock placeholder factsheet fields (soil_climate/description/delineation, EN+DE) from ll_content.json, ll_metadata.json, and fetch_nuts.py | 2026-07-27 | 4069627 | (inline) |
| 260729-bsg | Wire per-theme narrative text (about + focus) for each layer tab from ll_content.json through generate_metadata.py into TextBlock, across split, stacked and comparison layouts — plumbing shipped, awaiting human authoring of the first real prose (Task 3 checkpoint) | 2026-07-29 | 13d2d20 | [260729-bsg-wire-per-theme-narrative-text-about-focu](./quick/260729-bsg-wire-per-theme-narrative-text-about-focu/) |

## Open Questions (from research)

- Chart data embedded in `ll_metadata.json` OR separate per-LL files in `app/public/data/charts/`? (decide before Phase 9)
- Which candidate geodata portals and statistical services should be reviewed first, and what evidence format will make end-user approval easiest during Phase 3.1?
- Should Phase 4 pursue Regionalstatistik.de credentials to fill the 15 GENESIS-Online data gaps before building Waves 3-5's app-layer UI, or accept population-only real data for an initial ship and backfill later?

## Backlog / Follow-up Todos

| ID | Phase | Item | Status |
|----|-------|------|--------|
| TODO-01 | 2.2 | Improve tooltips: fix mixed German/English text, reduce verbosity, improve colour divergence in soil layer legend | open |

## Roadmap Evolution

- 2026-04-30: Inserted Phase 2.1 "Soil Map Tab Integration" after Phase 2 to wire the new BUEK GeoJSON outputs into the app before Phase 3
- 2026-04-30: Completed Phase 2.1 after syncing BUEK250 GeoJSON runtime assets and enabling the frontend soil overlay
- 2026-04-30: Inserted Phase 2.2 "Soil Semantics & Translation" between Phase 2.1 and Phase 3 to normalize and translate SQLite-derived soil metadata before broader UI use
- 2026-04-30: Completed Phase 2.2 after introducing the semantic soil contract, rebuilding the BUEK fixtures, and migrating the frontend soil experience onto semantic fields
- 2026-05-20: Inserted Phase 3.1 "Data Source Research & User Validation" after Phase 3 to research candidate geodata and statistical portals, summarize their available data with AI assistance, and let end-users decide what should move forward into integration
- 2026-06-02: Completed Phase 03.1 Wave 1 after creating the source catalogue generator, CSV mirror, and workbook review tab
- 2026-06-02: Completed Phase 03.1 Wave 2 after populating the source catalogue with evidence-chained facts and advisory assessments
- 2026-07-24: Phase 4 added: "Destatis Statistics Integration" — source LL statistics via the GENESIS-Online API (resuming paused fetch_destatis.py work), process per NUTS3/LL, and integrate into the app; added while Phase 3.1 is still open because Destatis inclusion is confirmed regardless of the 3.1 review outcome. API auth must move to HTTP headers per Destatis support email (2026-07)

## Accumulated Context

### Roadmap Evolution

- Phase 05.1 inserted after Phase 5: Calculate coverage KPIs for landscape tab using protected areas maps (URGENT)
- 2026-07-27: Phase 7 added: "Add BORIS land value maps as spatial layer for socio-economic tab (WFS from Brandenburg and Hessen geoportals)" — incorporates BORIS land-value map data via WFS services from Brandenburg and Hessen (the two Bundesländer covering the 5 Living Labs) for the socio-economic tab
- 2026-07-27: Phase 3 "Chart Data Contract" removed from its original slot (never started, no directory existed) and re-added as Phase 9 at the end of the roadmap, so chart implementations are defined after all map layers (Phases 5, 5.1, 6, 7) exist for charts to summarize. CHARTS-01/CHARTS-02 traceability in ROADMAP.md and REQUIREMENTS.md updated to point at Phase 9. Phases 4-7 were left unrenumbered since they are already complete/underway with directories and commit history referencing their current numbers.
- 2026-07-27: Phase 8 added: "Add maps and stats for climate variables using CHELSA data" — climate variable maps plus summary statistics, sourced from CHELSA via the `chelsa_cmip6` Python library (https://gitlabext.wsl.ch/karger/chelsa_cmip6/). Placed in the free slot 8 (vacated when the old Phase 3 moved to 9) rather than appended as Phase 10, so it sits with the other map-layer phases and before the Phase 9 chart contract that summarizes them. Phase 9's "Depends on" updated from Phase 7 to Phase 8 accordingly.

### Plan Decisions

- [Phase 07, plan 06]: `boris_semantics.BR_ART_NUTZUNG` has 42 entries, not the 44 that `07-RESEARCH.md`'s prose claims — its own section 3.1 table only enumerates 42 rows; transcribed the verified 42 rather than inventing 2 more. Hessen code `LW` is deliberately excluded from `HE_ART_NUTZUNG` (falls to `UNMAPPED_USAGE` with the raw code preserved) per the `07-SPIKE.md` W-03 locked checkpoint decision, overriding `07-06-PLAN.md`'s own acceptance-criteria text which (echoing a superseded `07-RESEARCH.md` guess) said `LW` should map to the agricultural canonical pair. `semantics.recency_cutoff` in `sources.yaml` is `null` (with a new `recency_window_years: 10` key) rather than a baked-in `"2016-01-01"` literal, per the locked instruction to implement W-02 as a rolling window, not a hardcoded date. See `07-06-SUMMARY.md` Deviations for full detail.
- [Phase 07, plan 07]: `fetch_boris.py` written and live-verified against both states — rheingau (Hessen, 1676 features written and re-validated) and havellandisches-luch (Brandenburg, 18644 features dry-run only, matched=18961/unmatched=0/failing_recency=5964, all figures matching `07-SPIKE.md`'s locked W-01/W-02 measurements within rounding). Fixed a live bug: a trailing 0-feature GML paging page crashes pyogrio (no layer schema to detect), so only pages with `numberReturned > 0` are parsed. All three tasks' code was authored together in one file and landed in a single commit (`406514e`) rather than three, since splitting the write into separate passes would have produced an unrunnable intermediate script; each task's verification still ran independently against the live services in plan order. See `07-07-SUMMARY.md` Deviations for full detail.
- [Phase 07, plan 08]: Ran the unfiltered five-Living-Lab fetch, committed all ten GeoJSON copies, and added `test_boris_geojson_fixtures_exist_and_match_contract` (suite 27/27 green). All zone counts within 5% of `07-RESEARCH.md`; both Brandenburg no-data shares within rounding of the locked W-02 figures; all three Hessen fixtures 0% no-data. east-brandenburg's committed size (33,948,983 bytes) exceeds `fetch_boris.py`'s rounded diagnostic constant (33,000,000 bytes) but is 5,392 bytes under `07-SPIKE.md`'s own specific locked measurement for that Living Lab (33,954,375 bytes) — the new regression test asserts against the precise locked figure, not the rounded constant. Flagged (not blocking) for `07-09`'s evidence record and human sign-off. See `07-08-SUMMARY.md` Deviations for full detail.

## Session

**Last session:** 2026-07-30T09:58:00.000Z
**Stopped at:** Phase 8 Wave 2 (08-03) complete — W-05 locked as gdd5; needs 08-04-PLAN.md precondition fix before Wave 3
**Resume file:** .planning/phases/08-add-maps-and-stats-for-climate-variables-using-chelsa-data/08-SPIKE.md
