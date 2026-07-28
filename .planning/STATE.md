---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: ready_to_plan
last_updated: "2026-07-28T06:54:15.389Z"
progress:
  total_phases: 15
  completed_phases: 9
  total_plans: 45
  completed_plans: 36
  percent: 60
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-04-29)

**Core value:** A researcher or stakeholder can open the app and immediately see accurate, up-to-date geodata and statistics for any of the five Living Labs without any server infrastructure.

**Current focus:** Phase 10 — add-for-comparison-button-opens-ll-menu-and-switches-to-two-

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
| 7 | Add BORIS land value maps as spatial layer for socio-economic tab | Planned (2026-07-27) — 9 plans, 7 waves, 2 checkpoints, verified ✓ (0 blockers, warnings fixed) |
| 9 | Chart Data Contract | Not planned yet (2026-07-27) |
| 10 | Two-column LL comparison view | Planned (2026-07-27) — 6 plans, 5 waves, 1 checkpoint, verified ✓ (0 blockers, 4 warnings) |

## Active Work

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

**Phase 7 is planned and ready to execute (2026-07-27).** 9 plans across 7 waves cover the BORIS
(Bodenrichtwert) land-value choropleth for the Socio-economic tab, built from live Brandenburg
(BORIS-BB) and Hessen (BORIS-HE) WFS services. Research flagged a blocking volume risk (verified
per-Living-Lab zone counts run 1,668-30,018 — 5x-80x denser than any prior vector layer), so waves
2-3 are a measure-then-decide spike (`07-03`) feeding a blocking `checkpoint:decision` (`07-05`) that
locks the geometry/size budget, the `has_current_value` recency rule, and the Hessen usage-code map
before any production fetch code is written. Wave 7 (`07-09`) closes with a blocking bilingual
human-verification checkpoint across all five Living Labs. The plan-checker found 0 blockers and 3
warnings (pane z-index collision with the protected-areas overlay, an untraceable requirement ID, and
a pending UI-SPEC sign-off note); the first two were fixed directly in the plan files, the third is
informational only. Next: `/gsd:execute-phase 7`.

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
