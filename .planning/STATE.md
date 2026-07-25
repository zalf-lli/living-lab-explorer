---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: unknown
last_updated: "2026-07-24T09:41:23.854Z"
progress:
  total_phases: 7
  completed_phases: 4
  total_plans: 16
  completed_plans: 10
  percent: 57
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-04-29)

**Core value:** A researcher or stakeholder can open the app and immediately see accurate, up-to-date geodata and statistics for any of the five Living Labs without any server infrastructure.

**Current focus:** Phase 04 — destatis-statistics-integration-source-process-and-app-integ

## Status

| Phase | Name | Status |
|-------|------|--------|
| 1 | LL Content System | Complete (2026-04-29) |
| 2 | BUEK Vector Pipeline | Complete (2026-04-30) |
| 2.1 | Soil Map Tab Integration | Complete (2026-04-30) |
| 2.2 | Soil Semantics & Translation | Complete (2026-04-30) |
| 3 | Chart Data Contract | Ready to plan |
| 3.1 | Data Source Research & User Validation | Inserted - ready to plan |
| 4 | Destatis Statistics Integration | Waves 1-2+6-7 complete; 10/17 KPIs real; Waves 3-5 ready (2026-07-24) — see Active Work |

## Active Work

**Phase 4: Waves 1, 2, 6, and 7 are complete and merged to `data-pipeline-development`** (04-01,
04-02, 04-06, 04-07 all have SUMMARY.md + passing tests, 7/7). Waves 3-5 (kpiByTab wiring into
ll_metadata.json, tab/i18n restructure, StatPanel UI component) are now ready to execute.

**Data availability final state (2026-07-24, after 04-07's Regionalstatistik.de table discovery):**
The 04-06 "0/15" result was a code-format mismatch, not a data gap — Regionalstatistik.de
publishes Kreis-level statistics as dash-coded tables (`data/tablefile`, format=ffcsv), not
GENESIS-Online-style cube codes. Searching with the correct format resolved 9 more slots.
**10 of 17 curated KPIs now carry real, live-fetched Kreis-level values** (all committed):
- landuse 4/4: land_area_cropland_ha, farms_count, farm_avg_size_ha, organic_pct
- landscape 2/4: forest_area_ha, sealed_surface_pct
- economic 4/4: population_total, unemployment_rate_pct, household_income_eur, gdp_per_capita_eur
  (gdp restored to its original D-09 slot, replacing the 04-02 population-density substitute)

**7 slots remain genuinely null** — confirmed unavailable at Kreis level on BOTH Destatis
platforms after exhaustive prefix + keyword search: n_surplus_kg_ha, p_surplus_kg_ha,
groundwater_nitrate_mg_l (nutrient/nitrate data are non-Destatis products), agr_ch4_kt,
agr_n2o_kt (GHG emissions are Länder-level only), natura2000_ha, nature_reserves_ha
(nature-conservation area stats are non-Destatis products). Nearest-miss candidates are
documented in 04-07-SUMMARY.md for human review. Filling these would require non-Destatis
sources (e.g. UBA, BfN, LAWA) — out of Phase 4's Destatis scope; candidates for a future phase
or the Phase 3.1 source-catalogue process. **Quick-task 260725-e1x (2026-07-25) attempted a
live-verification follow-up on the three near-miss `groundwater_nitrate_mg_l` water tables
(`32221-01-03-4`/`32221-02-01-4`/`32221-03-01-4`) but was fully credential-blocked in that
execution environment; verdict REJECT-ALL-THREE recorded in
`.planning/quick/260725-e1x-investigate-the-near-miss-regionalstatis/260725-e1x-DECISION.md`,
still resting on 04-07's catalogue-title inference (volumes, not nitrate concentration), now
explicitly flagged as unconfirmed-by-live-data. Still 7 null slots — no change to the count.**

**Next step:** run `/gsd:execute-phase 4` to execute Waves 3-5 (04-03 kpiByTab wiring, 04-04
tab/i18n restructure, 04-05 StatPanel UI — 04-05 has a human-verify checkpoint). The UI will show
real values for 10/17 KPIs; the 7 null slots need a UI decision (hide vs. "data not available"
state) which the UI-SPEC/plans already contemplate.

Phase 03.1 Wave 2 completed on 2026-06-02. The source review catalogue is now populated with citation-backed fact columns, advisory `(AI)` assessment columns, and an updated `source_catalogue` xlsx tab ready for human review.

Phase 03.1 Wave 3 is paused at its human-verify checkpoint: reviewers must fill `decision`, `priority`, and `rationale` for each candidate row in `data/variables_catalogue.xlsx`.

Phase 2.2 completed on 2026-04-30 and replaced the shallow German-only soil lookup with a richer bilingual semantic contract.

- Pipeline outcome: `data-pipeline/python/soil_semantics.py` now centralizes normalization, translation, special-area handling, and compact profile summaries sourced from the BUEK250 SQLite schema
- Fixture outcome: all five committed `data/geojson/buek250-*.geojson` files and the matching runtime copies in `app/public/data/geojson/` now expose semantic fields such as `feature_kind`, `soil_label_*`, `soil_group_*`, and provenance-aware summaries
- Frontend outcome: the soil map now styles and labels features from the semantic contract first, with Living-Lab-specific legend entries and semantic tooltips
- Next suggested step: run `$gsd-plan-phase 3.1` to define the iterative AI-plus-end-user research loop for selecting geodata and statistical sources before subsequent integrations

## Open Questions (from research)

- Chart data embedded in `ll_metadata.json` OR separate per-LL files in `app/public/data/charts/`? (decide before Phase 3)
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
