---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: unknown
last_updated: "2026-06-01T14:26:25.589Z"
progress:
  total_phases: 6
  completed_phases: 4
  total_plans: 11
  completed_plans: 8
  percent: 67
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-04-29)

**Core value:** A researcher or stakeholder can open the app and immediately see accurate, up-to-date geodata and statistics for any of the five Living Labs without any server infrastructure.

**Current focus:** Phase 3.1 - Data Source Research & User Validation (next to plan)

## Status

| Phase | Name | Status |
|-------|------|--------|
| 1 | LL Content System | Complete (2026-04-29) |
| 2 | BUEK Vector Pipeline | Complete (2026-04-30) |
| 2.1 | Soil Map Tab Integration | Complete (2026-04-30) |
| 2.2 | Soil Semantics & Translation | Complete (2026-04-30) |
| 3 | Chart Data Contract | Ready to plan |
| 3.1 | Data Source Research & User Validation | Inserted - ready to plan |

## Active Work

Phase 2.2 completed on 2026-04-30 and replaced the shallow German-only soil lookup with a richer bilingual semantic contract.

- Pipeline outcome: `data-pipeline/python/soil_semantics.py` now centralizes normalization, translation, special-area handling, and compact profile summaries sourced from the BUEK250 SQLite schema
- Fixture outcome: all five committed `data/geojson/buek250-*.geojson` files and the matching runtime copies in `app/public/data/geojson/` now expose semantic fields such as `feature_kind`, `soil_label_*`, `soil_group_*`, and provenance-aware summaries
- Frontend outcome: the soil map now styles and labels features from the semantic contract first, with Living-Lab-specific legend entries and semantic tooltips
- Next suggested step: run `$gsd-plan-phase 3.1` to define the iterative AI-plus-end-user research loop for selecting geodata and statistical sources before subsequent integrations

## Open Questions (from research)

- Chart data embedded in `ll_metadata.json` OR separate per-LL files in `app/public/data/charts/`? (decide before Phase 3)
- Which candidate geodata portals and statistical services should be reviewed first, and what evidence format will make end-user approval easiest during Phase 3.1?

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
