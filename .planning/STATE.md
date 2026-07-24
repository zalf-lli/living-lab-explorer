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
| 4 | Destatis Statistics Integration | Waves 1-2+6 complete; Waves 3-5 awaiting user decision (2026-07-24) — see Active Work |

## Active Work

**Phase 4: Waves 1, 2, and 6 are complete and merged to `data-pipeline-development`** (04-01,
04-02, 04-06 all have SUMMARY.md + passing tests). Waves 3-5 (kpiByTab wiring into
ll_metadata.json, tab/i18n restructure, StatPanel UI component) remain deferred pending a decision
below.

**The core data-availability finding stands even after obtaining Regionalstatistik.de credentials.**
Wave 2 (`04-02`) discovered via exhaustive live GENESIS-Online API probing that 16 of the 17 D-09
curated KPI fields cannot be sourced from GENESIS-Online at Kreis level; only `population_total`
resolves there. The user then obtained Regionalstatistik.de credentials and gap-closure plan
`04-06` activated the D-15 fallback (fixed a wrongly-assumed token-auth scheme, a case-sensitive
URL bug, and an intermittent stale-login-response bug — all real, now-fixed bugs) and genuinely
retried all 15 null slots against Regionalstatistik.de with working credentials. **Empirical
result: 0 of 15 additional slots resolve there either** — these statistics are published only at
Bund/Länder granularity on both platforms' public APIs, not a code or credentials problem. Full
detail: `.planning/phases/04-destatis-statistics-integration-source-process-and-app-integ/04-06-SUMMARY.md`.

**Decision needed before continuing to Waves 3-5:**
1. **Accept population-only real data** and proceed with `/gsd:execute-phase 4` — Waves 3-5 build kpiByTab/StatPanel UI now; 16 of 17 KPI slots render null/pending in the UI.
2. **Search for alternate Regionalstatistik.de table codes** for the 15 unresolved indicators (Regionalstatistik.de sometimes publishes the same statistic under different table codes than GENESIS-Online; 04-06 only retried the same codes, per its scope) — would need a new plan, not yet created.
3. **Re-scope the curated KPI list** (D-09) to only genuinely-available indicators rather than shipping mostly-null fields — would require revisiting CONTEXT.md decisions.

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
