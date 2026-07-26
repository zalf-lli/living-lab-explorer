# Roadmap - LL-Explorer Phase 4

## Phases

| # | Phase | Goal | Requirements | UI |
|---|-------|------|--------------|-----|
| 1 | LL Content System | Replace ad-hoc hardcoded LL config with a structured, hand-authored JSON merged into a single metadata file | CONTENT-01, CONTENT-02, CONTENT-03, CONTENT-04 | yes |
| 2 | BUEK Vector Pipeline | Process the BUEK soil source through a new vector pipeline path and verify all pipeline outputs with smoke tests | PIPELINE-01, PIPELINE-02, PIPELINE-03 | no |
| 2.1 | Soil Map Tab Integration (INSERTED) | Wire the new BUEK GeoJSON outputs into the app so each LL can render the soil layer inside the soil map tab | TBD | yes |
| 2.2 | Soil Semantics & Translation (INSERTED) | Replace the raw German-only BUEK lookup fields with a clean bilingual soil contract derived from the SQLite database structure | TBD | yes |
| 3 | Chart Data Contract | Define and plumb the per-source chart summary interface so future chart implementations have a clear, stable target | CHARTS-01, CHARTS-02 | no |
| 3.1 | Data Source Research & User Validation (INSERTED) | Research candidate geodata and statistical portals with AI-assisted summaries, review them with end-users, and turn the selected data opportunities into an integration-ready backlog | TBD | no |
| 4 | Destatis Statistics Integration | 7/7 | Complete   | 2026-07-25 |

---

## Phase Details

### Phase 1: LL Content System

**Status:** Complete (2026-04-29)

**Goal:** Replace scattered, hardcoded LL display config (`ll_display.js` + values in `fetch_nuts.py`) with a single hand-authored `ll_content.json` merged by `sync.py` into the app's `ll_metadata.json`.
**Requirements:** CONTENT-01, CONTENT-02, CONTENT-03, CONTENT-04
**UI hint**: yes

**Implementation plan:**

**Wave 1**
- `01-01` - Establish `data/ll_content.json` as the single hand-authored LL source and move metadata merge logic into the pipeline

**Wave 2** *(blocked on Wave 1 completion)*
- `01-02` - Remove `app/src/data/ll_display.js`, migrate UI consumers to metadata-only reads, and render preliminary-data badges

**Cross-cutting constraints:**
- `data/ll_content.json` is the only human-authored LL content source; pipeline code may read it but must never overwrite it
- Human-authored metadata fields win on merge conflicts when producing `data/ll_metadata.json`
- `mock: true` must render a bilingual preliminary-data badge on both the landing card and LL detail header

**Success criteria:**
1. Developer edits a tagline in `data/ll_content.json`, runs `python data-pipeline/sync.py`, and the updated text appears in `app/public/data/ll_metadata.json` without touching any other file
2. `app/src/data/ll_display.js` no longer exists; `npm run build` still produces a working app with correct LL colours, icons, and names
3. An LL with `"mock": true` in `ll_content.json` shows a bilingual "Preliminary data / Vorlaeufige Daten" badge in both the landing card and the detail page header

---

### Phase 2: BUEK Vector Pipeline

**Status:** Complete (2026-04-30)

**Goal:** Process the BUEK250 GeoPackage through a new `build_vector.py` script, producing per-LL GeoJSON outputs, and add `pytest` smoke tests covering both raster and vector pipeline outputs.
**Requirements:** PIPELINE-01, PIPELINE-02, PIPELINE-03
**UI hint**: no

**Success criteria:**
1. Running `python data-pipeline/python/build_vector.py --layer buek250` produces one GeoJSON file per LL in `data/geojson/` with correct CRS (EPSG:4326), non-empty features, and a build log line reporting output file size
2. Running `python -m pytest data-pipeline/tests/` passes all smoke tests, verifying PMTiles output (existing layer) and GeoJSON outputs (new BUEK layer) without re-running the full build
3. The script aborts with a clear error message (not a silent empty file) if CRS misalignment or invalid geometries are detected

---

### Phase 2.1: Soil Map Tab Integration (INSERTED)

**Status:** Complete (2026-04-30)

**Goal:** Wire the committed per-LL BUEK250 GeoJSON outputs into the frontend so the soil map tab can render the new vector layer for each Living Lab without changing the Phase 2 pipeline contract.
**Requirements:** TBD
**UI hint**: yes

**Implementation plan:**

**Wave 1**
- `02.1-01` - Publish the committed BUEK250 GeoJSON files into `app/public/data/geojson/` during sync and add a vector-capable frontend layer contract for the soil tab

**Wave 2** *(blocked on Wave 1 completion)*
- `02.1-02` - Render the soil tab through a lazy per-LL GeoJSON overlay in `LLMap`, with deterministic styling and resilient loading/error states

**Cross-cutting constraints:**
- Phase 2 remains the source contract: execution must consume `data/geojson/buek250-{slug}.geojson` rather than inventing a second soil output format
- Soil data must load lazily for the active LL only; switching away from the soil tab must not trigger or require a soil fetch
- Soil overlay failures must not blank the LL detail shell or regress the existing landuse PMTiles behavior

**Success criteria:**
1. The app can load the matching `buek250-{ll-slug}.geojson` file for the active Living Lab from `app/public/data/` when the soil map tab is opened
2. The LL detail experience renders the BUEK polygons inside the soil map tab with stable styling and without regressing the existing map behavior
3. The vector layer load is lazy and surfaces a clear loading or error state instead of blocking the rest of the LL detail page

---

### Phase 2.2: Soil Semantics & Translation (INSERTED)

**Status:** Complete (2026-04-30)

**Goal:** Replace the current raw `soil_name` / `soil_type_*` enrichment with a normalized, bilingual soil metadata contract that respects the structure of the BUEK250 SQLite database and avoids leaking low-quality German-only strings straight into the app.
**Requirements:** TBD
**UI hint**: yes

**Implementation plan:**

**Wave 1**
- `02.2-01` - Analyze the SQLite schema (`LEGENDENEINHEIT`, `PROFIL`, `HORIZONT`, `GL_EINHEIT`, `GL_BAG_FLAECHENTYP`) and define a canonical per-polygon soil metadata contract with null-handling and field provenance

**Wave 2** *(blocked on Wave 1 completion)*
- `02.2-02` - Build the bilingual and cleaned export path in the pipeline, including normalization of malformed strings and a deterministic strategy for mapping German source terms into English

**Wave 3** *(blocked on Wave 2 completion)*
- `02.2-03` - Update the frontend soil legend/info usage to consume the improved contract instead of the current two-bucket fallback and raw German text

**Cross-cutting constraints:**
- The SQLite database is authoritative for soil semantics, but its text content is German-first and partially sparse; the app contract must make provenance and fallback behavior explicit instead of pretending all fields are complete
- The BUEK250 database metadata states that `LEGENDENEINHEIT` contains the textual legend descriptions, while `PROFIL` and `HORIZONT` drive thematic evaluations and `GL_EINHEIT` plus `GL_BAG_FLAECHENTYP` provide higher-level grouping of general legend units and parent-material surface types
- English names should be generated through a reproducible mapping or translation layer committed to the repo, not via ad-hoc manual edits inside emitted GeoJSON files
- Nulls such as the very sparse `soil_type_3` field must be normalized intentionally, either by omission, fallback, or a derived alternative field, rather than surfacing confusing half-empty columns to the UI
- Broken or truncated strings from the raw database export must be cleaned in the preparation step before they reach runtime assets

**Success criteria:**
1. Running the BUEK vector preparation emits a documented soil metadata contract with readable fields whose provenance is clear and whose empty values are handled intentionally
2. The app-facing soil metadata includes stable English labels or names for user-facing fields, without losing the original German source values where traceability is needed
3. Raw malformed text snippets and sparsely populated fields no longer leak directly into the runtime UI contract
4. The resulting contract is rich enough for a future soil legend/info experience to use more than the current generic "soil polygons vs water" split

---

### Phase 3: Chart Data Contract

**Goal:** Document the chart output JSON schema and add optional `chart:` stanza support to `sources.yaml` + `sync.py` so any layer can declare a chart script and have its output copied to `app/public/data/charts/`.
**Requirements:** CHARTS-01, CHARTS-02
**UI hint**: no

**Success criteria:**
1. The chart JSON schema is documented (shape, field names, types, bilingual label convention) in a location a future implementer can find without reading source code
2. A `sources.yaml` entry with a `chart:` stanza passes `sync.py` without errors; `sync.py` logs a `[chart]` line and copies the output file if it exists, or logs `[chart] skipped - not yet built` if it doesn't
3. The crop-types layer (existing) can be given a `chart:` stanza as a dry-run validation without writing any chart computation code

---

### Phase 3.1: Data Source Research & User Validation (INSERTED)

**Status:** Planned (2026-06-01)

**Plans:** 3 plans (one per wave)

**Goal:** Create an iterative discovery loop between AI support and end-users to identify relevant geodata and statistical services, summarize what each source can contribute, and convert the selected opportunities into concrete follow-on integration work.
**Requirements:** TBD
**UI hint**: no

**Implementation plan:**

**Wave 1**
- [ ] `03.1-01-PLAN.md` - Define the 21-column review-catalogue format; scaffold export_source_catalogue.py + source_catalogue.csv + the source_catalogue xlsx review tab with seed rows

**Wave 2** *(blocked on Wave 1 completion)*
- [ ] `03.1-02-PLAN.md` - AI-assisted, citation-backed source research filling the catalogue; targeted IACS/InVeKoS discovery for Brandenburg, Hesse, Lower Saxony; verified facts kept separate from advisory (AI) columns

**Wave 3** *(blocked on Wave 2 completion)*
- [ ] `03.1-03-PLAN.md` - Human review (include/defer/reject + priority + rationale); regenerate the committed CSV mirror; convert approved sources into 999.x backlog items with integration sketches; restructure docs/data-sources.md

**Cross-cutting constraints:**
- The research loop must stay human-in-the-loop: AI can accelerate discovery and summarization, but end-users decide what is relevant enough to include
- Each candidate source summary must make scope, spatial or temporal coverage, access method, licensing or reuse constraints, update cadence, and likely integration complexity explicit
- Research outputs must separate verified source facts from AI interpretation so later implementation work can trust the evidence chain
- The outcome of this phase is not data ingestion itself; it is a curated and decision-backed shortlist that de-risks subsequent integration phases

**Success criteria:**
1. There is a documented inventory of candidate geodata and statistical services or portals, each summarized in a consistent, end-user-readable format
2. End-users can review those summaries and clearly indicate which sources should be included, deferred, or rejected
3. The approved sources are converted into concrete follow-on integration inputs, such as prioritized requirements, backlog items, or future roadmap phases with enough detail to implement

---

## Requirement Traceability

| Requirement | Phase | Phase Name |
|-------------|-------|------------|
| CONTENT-01  | 1     | LL Content System |
| CONTENT-02  | 1     | LL Content System |
| CONTENT-03  | 1     | LL Content System |
| CONTENT-04  | 1     | LL Content System |
| PIPELINE-01 | 2     | BUEK Vector Pipeline |
| PIPELINE-02 | 2     | BUEK Vector Pipeline |
| PIPELINE-03 | 2     | BUEK Vector Pipeline |
| CHARTS-01   | 3     | Chart Data Contract |
| CHARTS-02   | 3     | Chart Data Contract |

### Phase 4: Destatis Statistics Integration

**Goal:** Source socioeconomic and agricultural statistics for the 5 Living Lab regions from the Destatis GENESIS-Online RESTful API, process/aggregate them per NUTS3 and per LL, and integrate the selected indicators into the app.
**Requirements**: TBD (no ROADMAP REQ-IDs assigned; plans reference CONTEXT.md decisions D-01..D-15 and ROADMAP scope items P4-SCOPE-1..3 instead)
**Depends on:** Phase 3 (Phase 3.1 still open, but Destatis inclusion is confirmed regardless of its outcome)
**Plans:** 7/7 plans complete

**Context (resumes paused work):**
- Prior work exists and was paused: `data-pipeline/python/fetch_destatis.py` (fetch + aggregation + expert-review CSV export), `data/destatis_variables.csv` (per-indicator values for expert selection), `data/destatis_variables_catalogue.csv` (candidate variable catalogue with EN/DE labels and GENESIS table IDs)
- Previous API calls failed. Destatis support (email, 2026-07) diagnosed the request structure. Required fixes:
  - POST requests with `Content-Type: application/x-www-form-urlencoded` set in the HTTP header
  - Access credentials (username/token) passed in the HTTP header — **not** in the request body as `fetch_destatis.py` currently does
  - All other parameters in the request body
- Reference docs: https://www-genesis.destatis.de/datenbank/online#modal=web-service-api , introduction PDF: https://www-genesis.destatis.de/datenbank/online/docs/GENESIS-Webservices_Introduction.pdf , official code snippets: https://github.com/StatistischesBundesamt/GENESIS-Online
- Note: base URL changes to `https://genesis.destatis.de/genesisWS/rest/2020/` from 28 May 2026 (already past — verify which host is live)

**Scope:**
1. Fix `fetch_destatis.py` auth/request structure per the support email; verify each GENESIS table ID in the catalogue actually exists and resolves at Kreis (NUTS3) level
2. Process raw responses into per-NUTS3 records and per-LL aggregates (`data/destatis_nuts3.json`, `data/destatis_ll.json`) plus expert-review CSVs
3. Wire selected indicators through `sync.py` into the app (respecting the file-on-disk pipeline–app contract) and render them in the LL views

**Implementation plan:**

**Wave 1**
- [ ] `04-01-PLAN.md` — Fix GENESIS-Online auth (headers not body, corrected host), add pre-flight check_auth(), empirically confirm the regional-key column/code format

**Wave 2** *(blocked on Wave 1 completion)*
- [ ] `04-02-PLAN.md` — Align curated field names with the variable catalogue, verify the 17 curated picks' GENESIS tables live with D-14 fallback, run the live fetch, add pytest coverage

**Wave 3** *(blocked on Wave 2 completion)*
- [ ] `04-03-PLAN.md` — Extend generate_metadata.py with a kpiByTab computed field; one-time direct strip of ll_content.json's legacy placeholder blocks (D-11); regenerate and verify ll_metadata.json

**Wave 4** *(blocked on Wave 3 completion)*
- [ ] `04-04-PLAN.md` — Rename/add tabs and flip availability (D-01..D-04, D-06..D-08) in layers.js; add 17 kpi.* labels + statPanel.* i18n copy

**Wave 5** *(blocked on Wave 4 completion)*
- [ ] `04-05-PLAN.md` — Build StatPanel component; wire into LLDetail (both layouts); retire KPIStrip (D-05); human-verify checkpoint across all tabs and both languages

**Cross-cutting constraints:**
- `data/ll_content.json` is edited directly by the executor once (D-11), never written by a pipeline script
- Destatis credentials stay in HTTP headers only, never in the POST body or in printed logs
- `_deep_merge`'s authored-wins policy is unchanged (D-12); Pitfall 3 is resolved by removing the conflicting authored fields instead

**Success criteria:**
1. `fetch_destatis.py` successfully authenticates against the live GENESIS-Online API and produces real (non-null) per-NUTS3/per-LL data for the 17 curated indicators
2. `app/public/data/ll_metadata.json` carries a `kpiByTab` field per LL with real values, units, and GENESIS table provenance, grouped into Agriculture/Soil/Climate/Landscape/Socio-economic
3. The LL detail page renders a StatPanel per tab (replacing the retired KPIStrip) with locale-aware formatting, an empty-state em-dash, and a working source-attribution link, verified across all 5 tabs and both languages

### Phase 5: Add protected areas as toggleable layer on landscape map

**Goal:** Living Lab visitors can switch on an independent protected-areas overlay that draws every Natura 2000 SCI/SPA site and German Naturschutzgebiet intersecting the region, at full geometric fidelity, on top of whichever thematic layer is active.
**Requirements**: D-01, D-02, D-03, D-04, D-05, D-06, D-07, D-08 (Phase 5 has no REQUIREMENTS.md IDs; the 05-CONTEXT.md decisions are the spec)
**Depends on:** Phase 4
**Plans:** 4 plans

Plans:
- [ ] 05-01-PLAN.md - BfN WFS fetch script, sources.yaml registration, five per-LL GeoJSON outputs (wave 1, blocking decision: coordinate precision)
- [ ] 05-02-PLAN.md - Overlay registration in layers.js, bilingual i18n keys, UI-SPEC corrections (wave 1, blocking decision: overlay vs tab)
- [ ] 05-03-PLAN.md - LLMap overlay toggle, lazy fetch, Canvas rendering, tooltips, legend, attribution (wave 2)
- [ ] 05-04-PLAN.md - D-01..D-08 evidence record and bilingual human verification (wave 3)

### Phase 05.1: Calculate coverage KPIs for landscape tab using protected areas maps (INSERTED)

**Goal:** Fill the two pre-declared but permanently-null landscape KPI slots (`natura2000_ha`, `nature_reserves_ha`) with real per-Living-Lab coverage figures computed from Phase 5's protected-areas geometry, clipped to each LL boundary and dissolved per designation.
**Requirements**: D-01, D-02, D-03, D-04, D-05 (Phase 05.1 has no REQUIREMENTS.md IDs; the locked planning decisions are the spec)
**Depends on:** Phase 5 (HARD blocker - consumes `data/geojson/protected-areas-{slug}.geojson`, which does not exist until Phase 5 executes)
**Plans:** 3 plans

**Locked decisions:**
- D-01: Fill only the two existing `_ha` slots. No percentage KPI, no new curated-KPI entry.
- D-02: Add `bfn_wfs` as a new `source_host` enum value in the curated KPI manifest.
- D-03: Computed values live in a new `data/protected_area_kpis.json`, merged into `kpiByTab` at `generate_metadata.py` build time - never patched into `destatis_ll.json`, which `aggregate_ll()` destructively regenerates.
- D-04: Phase 5 must execute first and produce all five per-LL protected-areas GeoJSON files.
- D-05: Two existing test contracts must be deliberately updated in the same commit as the manifest change.

Plans:
- [ ] 05.1-01-PLAN.md - Coverage computation script (dissolve -> clip -> EPSG:25832 area) and `data/protected_area_kpis.json` (wave 1)
- [ ] 05.1-02-PLAN.md - `bfn_wfs` source_host, test-contract repairs, `generate_metadata.py` merge, regenerated metadata, 2 new regression tests (wave 2)
- [ ] 05.1-03-PLAN.md - D-01..D-05 evidence record and blocking bilingual Landscape-tab verification (wave 3)

### Phase 6: Add land cover map. I want to add a new map to the landscape tab (currently named land use but will be re-named in phase 4). It should use the ESRI sentinel 2 land cover data via the API service. The existing crop type map should be moved to the new 'agriculture' tab

**Goal:** Living Lab visitors land on a Landscape tab showing 10 m Sentinel-2-derived land cover for
their region, while crop types move to a distinct Agriculture tab - five exclusive tabs, five per-LL
land cover rasters built offline from CC BY 4.0 source data, no API key at runtime.
**Requirements**: D-01 .. D-24 (Phase 6 has no REQUIREMENTS.md IDs; the 06-CONTEXT.md decisions are the spec)
**Depends on:** Phase 5
**Plans:** 5 plans, 4 waves, 1 blocking checkpoint

**Planning decisions (resolved during breakdown):**
- The internal `landuse` -> `agriculture` rename is **in scope**, not deferred. `LAYERS[].id`,
  `kpiByTab` keys and `sources.yaml`'s `app_layer` are string-matched, so renaming only the app side
  would silently empty the Agriculture tab's four Destatis KPIs. The dataset id `landuse-croptypes`
  and the committed `.pmtiles` filenames deliberately keep their names.
- `LAND_COVER_LEGEND` is **codegen'd** from `sources.yaml` into `app/src/data/land_cover_legend.js`
  and imported by `layers.js`, rather than hand-written there. D-12's structure is delivered exactly;
  hand-authoring was rejected because `build_colormap()` bakes the same hex codes into the PNG pixels.
- No `legend.landCover.*` i18n keys are added. `MapLegend.jsx` reads `entry[lang]` off the generated
  legend array; such keys would be dead code. Class labels live in the `sources.yaml` legend.
- Per-LL processing (D-14) is treated as **mandatory**, not preferred: the combined build peaks near
  11.6 GB on a 16.6 GB machine, per-LL near 2.2 GB.

Plans:
- [ ] 06-01-PLAN.md - Register io-lulc-landcover in sources.yaml, gitignore the source COGs, declare
      mercantile, make build_pmtiles.py clip per slug, add build_land_cover.py with class-value guards (wave 1)
- [ ] 06-02-PLAN.md - sync.py per-LL PMTiles publishing and legend codegen; run the build; pin source
      SHA-256; commit five per-LL rasters and the class histogram (wave 2)
- [ ] 06-03-PLAN.md - Frontend: pmtilesUrlPattern resolution, slug threading into RasterPmtilesLayer,
      agriculture/landscape LAYERS entries, i18n renames, Landscape as the default tab (wave 3)
- [ ] 06-04-PLAN.md - Pipeline-side landuse -> agriculture join-key rename, metadata regeneration,
      test-contract updates and new regression assertions (wave 3)
- [ ] 06-05-PLAN.md - Full automated gate, cross-file join-key consistency checks, blocking bilingual
      human verification, D-01..D-24 evidence record (wave 4)

## Backlog

### Phase 999.1: Find real data sources for 4 curated Destatis KPI fields with no Destatis-family source (BACKLOG)

**Goal:** [Captured for future planning]
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

---

*Created: 2026-04-29*
