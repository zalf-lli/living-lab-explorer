---
phase: 04-destatis-statistics-integration-source-process-and-app-integ
verified: 2026-07-25T21:50:00Z
status: gaps_found
score: 8/9 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 7/9
  gaps_closed:
    - "StatPanel's source-attribution line and 'View source' link correctly identify the actual data source (GENESIS-Online vs Regionalstatistik.de) for every KPI field"
  gaps_remaining:
    - "4 of 17 curated KPI fields (n_surplus_kg_ha, p_surplus_kg_ha, agr_ch4_kt, agr_n2o_kt) remain null — no Destatis-family data source found after exhaustive search; not overridden, now tracked as backlog Phase 999.1"
  regressions: []
gaps:
  - truth: "fetch_destatis.py produces real (non-null) per-NUTS3/per-LL data for the 17 curated indicators (Truth #4 / ROADMAP Success Criterion 1)"
    status: partial
    reason: >
      4 of 17 curated KPI fields (n_surplus_kg_ha, p_surplus_kg_ha, agr_ch4_kt, agr_n2o_kt)
      remain null in data/destatis_curated_kpis.json (source_host: null, genesis_table: null)
      after an exhaustive, live-verified search across both GENESIS-Online and
      Regionalstatistik.de (documented in 04-02/04-06/04-07-SUMMARY.md). The human explicitly
      declined to accept this via a verification override, instead creating a tracked backlog
      item (ROADMAP.md Backlog: "Phase 999.1 — Find real data sources for 4 curated Destatis KPI
      fields with no Destatis-family source"). This remains an open, honestly-reported gap against
      ROADMAP.md's literal Success Criterion 1 ("real (non-null) per-NUTS3/per-LL data for the 17
      curated indicators") — it is not resolved, only tracked for future discovery work.
    artifacts:
      - path: "data/destatis_curated_kpis.json"
        issue: "source_host and genesis_table are null for n_surplus_kg_ha, p_surplus_kg_ha, agr_ch4_kt, agr_n2o_kt — no data source exists to wire"
    missing:
      - "A real Destatis-family (or other authoritative) data source for these 4 fields — tracked as Phase 999.1 in ROADMAP.md's Backlog section, 0 plans yet, goal not yet scoped ('[Captured for future planning]')"
deferred:
  - truth: "natura2000_ha and nature_reserves_ha curated KPI slots have real, non-null data"
    addressed_in: "Phase 05.1"
    evidence: "ROADMAP.md Phase 05.1 goal: 'Calculate coverage KPIs for landscape tab using protected areas maps' — inserted specifically to compute Landscape-tab coverage KPIs (Natura 2000 / Naturschutzgebiet) from the new protected-areas GeoJSON introduced in Phase 5. Phase 05.1 now has 3 plans drafted (05.1-01/02/03-PLAN.md), confirming this is an active, concretely-scoped follow-on, unlike the vaguer Phase 999.1 backlog entry for the other 4 fields."
---

# Phase 4: Destatis Statistics Integration Verification Report

**Phase Goal:** Source socioeconomic and agricultural statistics for the 5 Living Lab regions from the Destatis GENESIS-Online RESTful API, process/aggregate them per NUTS3 and per LL, and integrate the selected indicators into the app.
**Verified:** 2026-07-25 (re-verification)
**Status:** gaps_found
**Re-verification:** Yes — after gap closure (previous report: 7/9, this report: 8/9)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `fetch_destatis.py` authenticates against the live GENESIS-Online API using header-based auth, not body params | VERIFIED | Unchanged since prior verification; not touched by the Gap 1 fix. `data-pipeline/python/fetch_destatis.py`: `_headers()`/`check_auth()`/`GENESIS_BASE` present |
| 2 | Regional-key column/code format empirically confirmed (AGS crosswalk), not assumed | VERIFIED | Unchanged since prior verification. `NUTS3_TO_AGS` constant confirmed present in `fetch_destatis.py` |
| 3 | The 17 curated KPI fields are verified live per D-13/D-14/D-15 with an honest, non-fabricated fallback | VERIFIED | Unchanged since prior verification. `data/destatis_curated_kpis.json` re-read directly this pass: still exactly 17 entries, correct per-tab counts `{landuse:4, soil:3, climate:2, landscape:4, economic:4}`, every entry carries `source_host` |
| 4 | `data/destatis_nuts3.json`/`data/destatis_ll.json` contain real, non-placeholder values for the curated indicators | PARTIAL (unchanged) | Re-confirmed: 11 of 17 fields carry real numeric values; 6 remain honestly `null`. 2 of the 6 (`natura2000_ha`, `nature_reserves_ha`) now have a concretely-scoped Phase 05.1 (3 plans drafted) — see Deferred Items. The other 4 (`n_surplus_kg_ha`, `p_surplus_kg_ha`, `agr_ch4_kt`, `agr_n2o_kt`) were **not** accepted via override; instead a new backlog item, ROADMAP.md "Phase 999.1", was created to track them as future work. This is a genuine, still-open gap against ROADMAP Success Criterion 1 — see `gaps` in frontmatter |
| 5 | `app/public/data/ll_metadata.json` carries `kpiByTab` per LL grouped into Agriculture/Soil/Climate/Landscape/Socio-economic, with real values/units/table provenance | VERIFIED | Re-read `app/public/data/ll_metadata.json` directly this pass: all 5 tab keys present per LL; `east-brandenburg.kpiByTab.landuse` confirmed with real values (`land_area_cropland_ha: 252996`, etc.) plus new `sourceHost` field on every entry |
| 6 | No legacy `"-"` placeholder strings leak into the new computed values; `ll_content.json` restructure was a direct executor edit, not a pipeline write | VERIFIED | Unchanged since prior verification; not touched by the Gap 1 fix |
| 7 | Tabs renamed/added per D-01..D-04 (Agriculture, Socio-economic, new Landscape tab, all previously-gated tabs now available) | VERIFIED | Unchanged since prior verification; not touched by the Gap 1 fix |
| 8 | Every LL detail tab renders a `StatPanel` with that tab's real KPI values in place of the retired `KPIStrip`; missing fields render a muted em-dash; numbers use locale-aware formatting; `KPIStrip.jsx` is fully deleted | VERIFIED | Re-confirmed this pass: `test -f app/src/components/KPIStrip.jsx` still fails (absent); `grep -rn "KPIStrip" app/src/` still returns zero matches; em-dash fallback (`field.value != null ? ... : '–'`) and `toLocaleString(locale)` unchanged in `StatPanel.jsx` |
| 9 | Every StatPanel shows a source-attribution line naming the correct GENESIS/Regionalstatistik table and retrieval date, with a working "View source" link | **VERIFIED (was FAILED)** | Fix confirmed real and correctly wired, not just claimed. `generate_metadata.py`'s `_build_kpi_by_tab()` (line 46) now emits `"sourceHost": entry.get("source_host")` into every `kpiByTab` field dict. `StatPanel.jsx` (lines 123-128) now branches: `const isRegionalstatistik = sourceHost === 'regionalstatistik'`, selects `sourceKey` between `statPanel.source` / `statPanel.sourceRegionalstatistik`, and builds `href` from `https://www.regionalstatistik.de/genesis/online?operation=table&code=${tableId}` vs the GENESIS-Online URL. `app/src/i18n.js` carries the new `statPanel.sourceRegionalstatistik` key in both EN and DE. `app/public/data/ll_metadata.json` re-read directly: `sourceHost: "regionalstatistik"` present on all 4 Agriculture-tab fields for `east-brandenburg`. **Independently live-verified (not just trusting the SUMMARY claim):** fetched `https://www.regionalstatistik.de/genesis/online?operation=table&code=41141-01-01-4` directly — HTTP 200, page title "Regionaldatenbank Deutschland: Tabelle abrufen", body contains the exact table code `41141-01-01-4` and its label "Bodennutzungsarten" (matches `land_area_cropland_ha`'s catalogue entry) — this is a real, resolving, table-specific GENESIS-Online-software page, not a generic landing/error page. Also fetched the GENESIS-Online URL template for the one `genesis`-sourced field (`population_total`, table `12411KJ002`) — HTTP 200. Both host branches resolve correctly |

**Score:** 8/9 truths fully verified (1 partial data-availability gap remains open — genuine external constraint, now tracked via backlog Phase 999.1 for 4/6 fields, concretely scoped for the other 2/6 via Phase 05.1)

### Deferred Items

Items not yet met but explicitly addressed in later/tracked phases. The two groups below have materially different confidence: Phase 05.1 is concretely scoped (3 plans drafted); Phase 999.1 is a bare backlog placeholder (0 plans, goal still `[Captured for future planning]`) — its existence documents intent to revisit but does **not** close the gap, which is why the corresponding truth still appears in `gaps` above rather than being fully deferred.

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | `natura2000_ha` / `nature_reserves_ha` curated KPI slots remain null | Phase 05.1 | ROADMAP.md Phase 05.1 goal: "Calculate coverage KPIs for landscape tab using protected areas maps" — directly targets computing these two Landscape-tab coverage KPIs from the Phase 5 protected-areas layer. Phase 05.1 now has 3 drafted plans (`05.1-01/02/03-PLAN.md`), confirming active planning, not just an aspiration |
| 2 | `n_surplus_kg_ha` / `p_surplus_kg_ha` / `agr_ch4_kt` / `agr_n2o_kt` curated KPI slots remain null | Phase 999.1 (Backlog, not yet scheduled) | ROADMAP.md `## Backlog` section: "Phase 999.1: Find real data sources for 4 curated Destatis KPI fields with no Destatis-family source (BACKLOG)" — captured for future planning, 0 plans, no committed goal text yet. **This is a tracked follow-up, not a closure** — the underlying truth (#4) remains an open gap in this report (see `gaps` frontmatter) because the human did not override it and no concrete plan yet exists to resolve it |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `data-pipeline/python/fetch_destatis.py` | Header-based auth, cube+table fetch, curated-KPI verification/fallback, dual-host (GENESIS+Regionalstatistik) support | VERIFIED | Unchanged since prior verification |
| `data/destatis_curated_kpis.json` | 17-entry manifest, tab/variable_key/genesis_table/labels/units/source_host | VERIFIED | Unchanged; 17 entries, correct per-tab counts, re-confirmed via direct read this pass |
| `data/destatis_meta.json` | `fetched_at` ISO date | VERIFIED | Unchanged |
| `data/destatis_nuts3.json`, `data/destatis_ll.json` | Real per-NUTS3/per-LL values | PARTIAL | Unchanged: 11/17 fields real; 6/17 honestly null (2 concretely deferred to Phase 05.1, 4 tracked-but-open via Phase 999.1 backlog) |
| `data-pipeline/python/generate_metadata.py` | `kpiByTab` computed field, `sort_keys=True`, `source_host` passthrough | **VERIFIED (gap closed)** | `_build_kpi_by_tab()` now includes `"sourceHost": entry.get("source_host")` (line 46) in every field dict; `sort_keys=True` still present in `write_metadata()` |
| `data/ll_content.json` | Legacy placeholder blocks removed | VERIFIED | Unchanged |
| `app/src/data/layers.js` | 5-entry LAYERS, climate/economic/landscape available | VERIFIED | Unchanged |
| `app/src/i18n.js` | Renamed tab labels, 17 `kpi.*` keys (EN+DE), `statPanel.*` namespace incl. `sourceRegionalstatistik` | **VERIFIED (gap closed)** | 17/17 `kpi.*` keys confirmed present in both languages; new `statPanel.sourceRegionalstatistik` key confirmed present in both EN ("Source: Regionalstatistik.de, table {{tableId}}, retrieved {{date}}") and DE ("Quelle: Regionalstatistik.de, Tabelle {{tableId}}, abgerufen am {{date}}") |
| `app/src/components/StatPanel.jsx` | Per-tab KPI tiles, empty-state em-dash, pending-review footnote, collapsible source-attribution disclosure, correct per-host source line/link | **VERIFIED (gap closed)** | Component renders correctly; disclosure-toggle unchanged; source-attribution now branches on `field.sourceHost` per unique `{sourceHost}::{genesisTable}` pair, producing correct copy key and URL for both GENESIS-Online and Regionalstatistik.de sources — confirmed via direct code read and live URL fetch (see Truth #9 evidence) |
| `app/src/pages/LLDetail.jsx` | StatPanel mounted in both layouts | VERIFIED | Unchanged |
| `app/src/hooks/useLLMetadata.js` | `kpiByTab`/`destatisRetrievedAt` passthrough, old flat kpi fields removed | VERIFIED | Unchanged |
| `app/src/components/KPIStrip.jsx` | Deleted | VERIFIED | Re-confirmed absent this pass; zero references |
| `data-pipeline/tests/test_pipeline_outputs.py` | Destatis output-contract smoke tests | VERIFIED | Re-ran this pass: 8/8 tests pass, no regressions |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `fetch_destatis.py:_post` | GENESIS-Online / Regionalstatistik.de | `requests.post` with base-aware `_headers(base)` | WIRED | Unchanged |
| `fetch_destatis.py` | `data/destatis_curated_kpis.json` | `json.dumps(..., sort_keys=True)` write in `main()` | WIRED | Unchanged |
| `generate_metadata.py:_build_computed_record` | `data/destatis_ll.json` | `_build_kpi_by_tab()` lookup by `variable_key` | WIRED | Unchanged; now also carries `source_host` through |
| `data/ll_metadata.json` | `app/public/data/ll_metadata.json` | `sync.py`'s `write_metadata()` | WIRED | Re-confirmed byte-identical this pass (`node` diff check: `identical: true`) |
| `app/src/pages/LLDetail.jsx` | `app/src/components/StatPanel.jsx` | `<StatPanel tab={layer} ll={ll} />` | WIRED | Unchanged |
| `app/src/components/StatPanel.jsx` | `app/src/hooks/useLLMetadata.js` | `ll.kpiByTab[tab]` field list | WIRED | Unchanged |
| `app/src/components/StatPanel.jsx` | External GENESIS/Regionalstatistik table page | "View source" `<a href>` branched on `sourceHost` | **WIRED (was PARTIAL)** | Live-fetched both host URL templates this pass: Regionalstatistik URL for `41141-01-01-4` returns HTTP 200 with the correct table-specific "Tabelle abrufen" page containing the exact table code and label; GENESIS-Online URL for `12411KJ002` returns HTTP 200. Both branches resolve to real, correct destinations |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `StatPanel.jsx` | `ll.kpiByTab[tab]` | `app/public/data/ll_metadata.json` fetched once via `useLLMetadata` | Yes for 11/17 fields, `null` (honest) for 6/17; `sourceHost` now present on all entries with a table | FLOWING (unchanged data-availability contract; provenance field now flows correctly) |
| `generate_metadata.py` `kpiByTab` | `destatis_ll.json` | Live GENESIS/Regionalstatistik.de fetch, committed to disk | Yes | FLOWING — unchanged |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| `data-pipeline` pytest suite (Destatis + BUEK + pmtiles contracts) | `cd data-pipeline && python -m pytest tests/test_pipeline_outputs.py -v` | 8 passed, re-run this session | PASS |
| App production build | `cd app && npm run build` | Built successfully, 119 modules transformed, re-run this session | PASS |
| `data/ll_metadata.json` == `app/public/data/ll_metadata.json` | Node byte-comparison | `identical: true` | PASS |
| Regionalstatistik.de "View source" link resolves to the correct table | `curl` fetch of `https://www.regionalstatistik.de/genesis/online?operation=table&code=41141-01-01-4` | HTTP 200; body contains exact table code and label "Bodennutzungsarten" | PASS |
| GENESIS-Online "View source" link resolves | `curl` fetch of `https://www-genesis.destatis.de/genesis//online?operation=table&code=12411KJ002` | HTTP 200 | PASS |
| `KPIStrip.jsx` still fully removed (regression check) | `grep -rn "KPIStrip" app/src/` | zero matches | PASS |

### Requirements Coverage

Phase 4 has no ROADMAP.md REQ-IDs; traceability is via CONTEXT.md decisions D-01..D-15 and ROADMAP scope items P4-SCOPE-1..3, declared per-plan in each PLAN.md's `requirements:` frontmatter. Unchanged from prior verification except P4-SCOPE-3, whose remaining caveat (source-attribution gap) is now closed for the fix; the data-availability caveat for Success Criterion 1 remains open per Truth #4.

| Decision/Scope | Source Plan(s) | Description | Status | Evidence |
|-----------------|-----------------|--------------|--------|----------|
| P4-SCOPE-1 | 04-01, 04-02 | Fix auth/request structure; verify GENESIS table IDs | SATISFIED | Unchanged |
| P4-SCOPE-2 | 04-02, 04-03 | Process raw responses into per-NUTS3/per-LL records | SATISFIED | Unchanged |
| P4-SCOPE-3 | 04-03, 04-04, 04-05 | Wire indicators through `sync.py` into the app and render them | **SATISFIED** | Source-attribution accuracy gap closed via `e194bc6`; rendering fully correct across both source hosts |
| D-01..D-08 | 04-04 | Tab rename/availability | SATISFIED | Unchanged |
| D-05 | 04-05 | Retire KPIStrip | SATISFIED | Unchanged |
| D-09 | 04-02, 04-03, 04-05 | 17 curated KPI fixed list | SATISFIED | Unchanged |
| D-10/D-11/D-12 | 04-03 | Placeholder data handling, one-time direct edit, merge policy unchanged | SATISFIED | Unchanged |
| D-13/D-14/D-15 | 04-02, 04-06, 04-07 | Table verification scope, fallback substitution, Regionalstatistik.de pursuit | SATISFIED | Unchanged; still an honest null-handling contract for the 4 fields with no source, now tracked as Phase 999.1 |

No orphaned requirements found.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `app/src/data/kpi_icons.js` | n/a | Unreferenced file left in place after `KPIStrip.jsx` deletion | Info | Unchanged; documented as intentional, out-of-scope cleanup; no runtime cost |

The previously-flagged Warning (`StatPanel.jsx` ~116-119, hardcoded source host/URL ignoring `source_host`) is **resolved** — the branch logic now correctly reads `field.sourceHost`. No `TODO`/`FIXME`/`XXX`/`HACK` markers found in any file touched by the fix commit (`e194bc6`).

### Human Verification Required

None. The prior human-verification item ("Click 'View source' on a Regionalstatistik-sourced field... confirm the corrected link resolves") has been satisfied by this verifier's own live `curl` fetch of both URL templates (see Behavioral Spot-Checks and Truth #9 evidence), which is a stronger, reproducible substitute for a manual browser click-through: it confirms the link is well-formed, resolves with HTTP 200, and lands on the specific cited table page (not a generic landing page). No remaining item requires subjective/visual human judgment.

### Gaps Summary

Phase 4's core data pipeline, tab restructuring, StatPanel UI, and now the source-attribution accuracy defect are all solidly built, wired, and independently verified (including live external-link resolution, not just static grep). One genuine, honestly-reported gap remains open:

**4 of 17 curated KPI slots remain null** (`n_surplus_kg_ha`, `p_surplus_kg_ha`, `agr_ch4_kt`, `agr_n2o_kt`) — this is short of ROADMAP.md's literal Success Criterion 1. It is not a code defect; it is a live-verified, exhaustively documented external data-availability gap (both GENESIS-Online and Regionalstatistik.de searched, per D-13/D-14/D-15's explicit never-fabricate contract). The human explicitly chose **not** to accept this via a verification override, and instead created a tracked backlog item (`ROADMAP.md` "Phase 999.1"). Because Phase 999.1 has zero plans and its goal is still `[Captured for future planning]`, it does not yet constitute resolution or a concrete commitment — it is process visibility, not closure. This report therefore continues to carry the gap forward rather than silently accepting or deferring it. The other 2 of the original 6 null fields (`natura2000_ha`, `nature_reserves_ha`) are addressed by the concretely-scoped Phase 05.1 (3 plans now drafted) and are correctly treated as deferred, not an open gap.

**Recommendation:** This phase can reasonably proceed to the next phase given the tracked backlog item, but the developer should be aware that ROADMAP Success Criterion 1 is not fully met and remains formally open pending Phase 999.1's eventual promotion and execution (or a future override decision).

---

*Verified: 2026-07-25T21:50:00Z*
*Verifier: Claude (gsd-verifier)*
