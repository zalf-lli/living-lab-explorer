# Roadmap - LL-Explorer Phase 4

## Phases

| # | Phase | Goal | Requirements | UI |
|---|-------|------|--------------|-----|
| 1 | LL Content System | Replace ad-hoc hardcoded LL config with a structured, hand-authored JSON merged into a single metadata file | CONTENT-01, CONTENT-02, CONTENT-03, CONTENT-04 | yes |
| 2 | BUEK Vector Pipeline | Process the BUEK soil source through a new vector pipeline path and verify all pipeline outputs with smoke tests | PIPELINE-01, PIPELINE-02, PIPELINE-03 | no |
| 2.1 | Soil Map Tab Integration (INSERTED) | Wire the new BUEK GeoJSON outputs into the app so each LL can render the soil layer inside the soil map tab | TBD | yes |
| 2.2 | Soil Semantics & Translation (INSERTED) | Replace the raw German-only BUEK lookup fields with a clean bilingual soil contract derived from the SQLite database structure | TBD | yes |
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
| CHARTS-01   | 9     | Chart Data Contract |
| CHARTS-02   | 9     | Chart Data Contract |

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
**Plans:** 5/5 plans complete

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

- [x] 06-01-PLAN.md - Register io-lulc-landcover in sources.yaml, gitignore the source COGs, declare
      mercantile, make build_pmtiles.py clip per slug, add build_land_cover.py with class-value guards (wave 1)

- [x] 06-02-PLAN.md - sync.py per-LL PMTiles publishing and legend codegen; run the build; pin source
      SHA-256; commit five per-LL rasters and the class histogram (wave 2)

- [x] 06-03-PLAN.md - Frontend: pmtilesUrlPattern resolution, slug threading into RasterPmtilesLayer,
      agriculture/landscape LAYERS entries, i18n renames, Landscape as the default tab (wave 3)

- [x] 06-04-PLAN.md - Pipeline-side landuse -> agriculture join-key rename, metadata regeneration,
      test-contract updates and new regression assertions (wave 3)

- [x] 06-05-PLAN.md - Full automated gate, cross-file join-key consistency checks, blocking bilingual
      human verification, D-01..D-24 evidence record (wave 4)

### Phase 7: Add BORIS land value maps as spatial layer for socio-economic tab (WFS from Brandenburg and Hessen geoportals)

**Goal:** Living Lab visitors open the Socio-economic tab and see a standard-land-value (Bodenrichtwert)
choropleth for their region - every zone type, coloured by EUR/m2 through six per-Living-Lab quantile
buckets, with a bilingual usage-type tooltip - built offline from the Brandenburg and Hessen BORIS WFS
services and shipped as static per-Living-Lab GeoJSON, with no runtime API dependency.
**Requirements**: D-01 .. D-13 (from 07-CONTEXT.md) plus W-01 .. W-03 (Wave-0 decisions taken at the
07-05 checkpoint). Phase 7 has no REQUIREMENTS.md IDs; the CONTEXT decisions are the spec, as in Phases 5 and 6.
**Depends on:** Phase 6
**Plans:** 8/9 plans executed

**WFS sources (validated live 2026-07-27 during research, superseding the user's original candidate links):**

- Brandenburg (BORIS-BB): `https://isk.geobasis-bb.de/ows/boris_wfs` - WFS 2.0.0, AdV BRM 3.0.1, EPSG:25833.
  Geometry and value live on **separate** feature types joined by `gehoertZu`; one endpoint mixes every
  Stichtag since 2010.

- Hessen (BORIS-HE): `https://www.gds.hessen.de/wfs2/boris/cgi-bin/brw/2024/wfs` - WFS 2.0.0, AdV BRM 2.1,
  EPSG:25832. Self-contained polygons, year-versioned endpoint.

- Original user-supplied links resolved to portal/metadata pages rather than WFS endpoints; the two URLs
  above were discovered and verified during Phase 7 research.

**Planning decisions (resolved during breakdown):**

- **Volume is the gating risk, not an implementation detail.** Verified per-Living-Lab zone counts run
  1,668 (rheingau) to 30,018 (east-brandenburg) - 5x to 80x denser than any prior vector layer (protected
  areas topped out at 362/LL). An unmitigated fetch would add roughly 1.2 GB across the two committed
  copies. Waves 2-3 are therefore a measure-then-decide spike (`07-03`, `07-05`) that fixes the geometry
  fidelity and size budget against real numbers before any production fetch code is written.

- **Brandenburg and Hessen get separate fetch code paths**, not one config-driven function. Their object
  models differ (BRM 3.0.1 vs 2.1) and Brandenburg requires a mandatory point/polygon join against a cached
  full-state fetch of 113,293 value records. The `build_vector.py`/`fetch_protected_areas.py` "one fetch
  function, config-driven field names" pattern is insufficient here.

- **Canvas rendering is mandatory, not preferred.** The declarative `<GeoJSON>` component the soil tab uses
  would emit one SVG path per polygon; the imperative `L.canvas()` pattern from `ProtectedAreasLayer` is the
  required precedent.

- **Frontend work runs in parallel with the pipeline spike** (waves 1-2), implementing against the locked
  07-UI-SPEC.md property contract; visual verification is deferred to wave 7 once real data exists.

- **Per-Living-Lab source attribution** required extending `sources.yaml` and `sync.py::generate_layer_sources()`
  rather than hand-copying provider strings into `i18n.js` - every Living Lab sits entirely within one state,
  so a single fixed attribution row would misattribute three of the five.

- Zero new packages. Every dependency (geopandas, shapely, requests, pyyaml) is already installed.

Plans:

- [x] 07-01-PLAN.md - `boris_wfs.py` WFS 2.0 transport: fes:Intersects/gehoertZu request builders, capped
      retrying HTTP, byte-sliced count extraction, per-state CRS-asserting GML reader, no-network unit tests (wave 1)

- [x] 07-02-PLAN.md - Frontend static config: `economic` placeholder to vector layer, BORIS ramp/no-data/hover
      style exports from theme tokens, ten bilingual i18n keys (wave 1)

- [x] 07-03-PLAN.md - `probe_boris.py` spike: Hessen usage-code census, Brandenburg statewide point cache +
      gehoertZu join + Stichtag histograms, seven-variant size/fidelity grid, `07-SPIKE.md` (wave 2)

- [x] 07-04-PLAN.md - LLMap economic path: quantile bucketing, value/no-data style, ranged legend builder,
      three-row tooltip, Canvas `EconomicLayer`, per-state `MapInfoControl` attribution (wave 2)

- [x] 07-05-PLAN.md - **Blocking checkpoint:decision** W-01 volume budget + geometry fidelity, W-02
      `has_current_value` recency rule, W-03 Hessen code map sign-off (wave 3)

- [x] 07-06-PLAN.md - `boris_semantics.py` state-discriminated bilingual contract (44-entry GDI-DE codelist),
      `sources.yaml` two-state boris entry, `providersByState`/`llStates` codegen, contract tests (wave 4)

- [x] 07-07-PLAN.md - `fetch_boris.py`: Hessen self-contained path, Brandenburg cached-join path,
      harmonize/trim/clip/simplify/round, validated sorted-key write (wave 5)

- [x] 07-08-PLAN.md - Full five-Living-Lab fetch, size-budget gate, `sync.py` publish, fixture contract
      regression test (wave 6)

- [ ] 07-09-PLAN.md - Full automated gate, four cross-file join-key checks, blocking bilingual human
      verification across all five Living Labs, D-01..D-13 + W-01..W-03 evidence record (wave 7)

### Phase 8: Add maps and stats for climate variables using CHELSA data

**Goal:** Living Lab visitors open the Climate tab and see a CHELSA-derived ~1 km climate raster for
their region - one of four variables, shown either as the 1981-2010 baseline or as projected change
under SSP3-7.0 across two future horizons - on a colour scale shared by all five Living Labs, with
four KPI tiles beneath it reporting each variable's baseline value plus its 2071-2100 change. Built
offline from static CHELSA/CMIP6 files and shipped as 60 per-Living-Lab PMTiles, with no runtime API
dependency.
**Requirements**: D-01 .. D-23 (from 08-CONTEXT.md) plus W-05 .. W-08 (Wave-2 decisions taken at the
08-03 checkpoint). Phase 8 has no REQUIREMENTS.md IDs; the CONTEXT decisions are the spec, as in
Phases 5, 05.1, 6 and 7.
**Depends on:** Phase 7 (BORIS land value layer - last of the existing map-layer phases; the
pipeline/layer conventions it establishes are reused here)
**Plans:** 11/11 plans executed

**Planning decisions (resolved during breakdown):**

- **D-07 (GDD) is a live two-path decision, not a yes/no.** Research reversed 08-CONTEXT.md's premise:
  `chelsa-cmip6==1.4` is on PyPI and does expose a `.gdd()` method with a 5 degC default matching D-06,
  but only through a live cloud-compute path adding ~10 heavy dependencies, and its formula sums raw
  temperatures on days above threshold rather than the textbook `sum(max(T - 5, 0))`. A lighter static
  path (pre-built CHELSA CMIP6 GeoTIFFs on WSL's envicloud, zero new dependencies) covers bio1/bio12/bio18
  but carries no GDD. Waves 1-2 are therefore a measure-then-decide spike (`08-01`) feeding a blocking
  `checkpoint:decision` (`08-03`), copying the Phase 7 `07-03`/`07-05` precedent verbatim.

- **D-09's shared colour scale needs a two-pass build with no Phase 6/7 precedent.** `build_colormap()`
  takes an a-priori categorical dict; climate's mapping is computed. `compute_climate_color_breaks.py`
  pools all five Living Labs' pixels into one committed breakpoint set before any per-LL bake, and
  `build_continuous_colormap()` becomes a sibling to `build_colormap()`.

- **D-12 is settled empirically, not assumed.** The Pass-0 script derives the diverging-vs-sequential
  verdict from the five observed per-Living-Lab means and records them alongside it for audit.

- **`sync.py::sync_pmtiles_per_ll()` needs a real code change.** Its `.replace("{slug}", "*")` handles
  one placeholder; the climate pattern carries three.

- **Two surfaces have no analog:** `StatPanel.jsx`'s D-20 delta row and `sources.yaml`'s
  variable x period x GCM-crossed input block. Both are planned as design work, not copy-paste.

- **D-18 is a same-commit requirement.** The manifest edit, both locked `tab_counts` dicts, the
  `source_host` allow-list and the two dead i18n labels land together (Phase 05.1 D-05 discipline).

- Zero new packages under the recommended static path.

Plans:

**Wave 1**

- [x] 08-01-PLAN.md - `probe_chelsa.py` spike: future-period URL structure, static monthly `tas`,
      CMIP6 product licence, five-GCM grid alignment, windowed-read cost, `08-SPIKE.md`
- [x] 08-02-PLAN.md - Frontend contracts: climate ramp exports, three-placeholder `resolveLayerAsset`,
      `StatPanel.jsx` two-line delta tile

**Wave 2** *(blocked on Wave 1)*

- [x] 08-03-PLAN.md - **Blocking checkpoint:decision** — W-05 locked as `gdd5` (CHELSA's own static
      GDD-above-5degC file, discovered mid-spike; not one of the plan's original three options), W-06
      URL templates, W-07 provenance text, W-08 acquisition budget cap all locked. `08-SPIKE.md`
      carries `## Phase status` (proceed) — no re-planning halt.

**Wave 3** *(blocked on Wave 2)*

- [x] 08-04-PLAN.md - `sources.yaml` `chelsa-climate` entry, `fetch_climate.py` windowed acquisition +
      five-GCM mean + family-aware change fields, twelve gitignored rasters. **Required pre-check:**
      Task 1's precondition text only recognizes `bio10`/`gdd-light`/`gdd-heavy` as valid W-05
      verdicts and needs a one-line wording update to also accept the actual locked outcome, `gdd5`,
      before this plan executes (flagged in `08-03-SUMMARY.md` Deviations).
- [x] 08-05-PLAN.md - Full bilingual climate i18n block, `VariablePicker.jsx`, `PeriodSwitcher.jsx`

**Wave 4** *(blocked on Wave 3)*

- [x] 08-06-PLAN.md - Pass-0 `compute_climate_color_breaks.py`, `build_continuous_colormap()`,
      Pass-1 `build_climate_pmtiles.py`, breaks contract test
- [x] 08-07-PLAN.md - `compute_climate_kpis.py` area-weighted zonal mean, `data/climate_kpis.json`

**Wave 5** *(blocked on Wave 4)*

- [x] 08-08-PLAN.md - Multi-placeholder sync glob, `generate_climate_legend()` codegen, the 60-file
      build run and publish

**Wave 6** *(blocked on Wave 5)*

- [x] 08-09-PLAN.md - D-18 manifest swap + both `tab_counts` dicts + allow-list + dead i18n labels,
      `chelsa` `source_host` branch with delta threading, regenerated metadata (one commit)

**Wave 7** *(blocked on Wave 6)*

- [x] 08-10-PLAN.md - `layers.js` climate raster entry, `useClimateControlState` lift and threading,
      `LLMap` raster/legend/note/badge wiring, dead placeholder legend removal

**Wave 8** *(blocked on Wave 7)*

- [x] 08-11-PLAN.md - Full automated gate, seven cross-file join-key checks, D-01..D-23 evidence
      record, blocking bilingual human verification

### Phase 9: Chart Data Contract

**Goal:** Document the chart-type-discriminated output JSON schema (bar and line variants), add optional `chart:` stanza support to `sources.yaml` + `sync.py` so any layer can declare a chart script and have its per-LL output copied to `app/public/data/charts/`, and implement real chart-computation scripts for all 5 map layers so every tab has a real, pipeline-computed summary chart.
**Requirements**: CHARTS-01, CHARTS-02, CHARTS-03, CHARTS-04, CHARTS-05, CHARTS-06, CHARTS-07
**Depends on:** Phase 8 (all map layers - protected areas, land cover, BORIS land value, CHELSA climate - must be built first so charts can be produced from the finished maps)
**Plans:** 7/7 plans complete

**Note:** Formerly numbered Phase 3. Moved to the end of the roadmap (2026-07-27) because chart implementations are meant to summarize the map layers, so the contract should be defined once every map layer exists rather than speculatively up front. **Scope expanded 2026-08-03** (09-CONTEXT.md discussion): originally contract-and-plumbing-only with crop-types as a dry-run validation target; the human decided during discussion to implement real chart computation for all 5 tabs in this phase rather than deferring it to v2. REQUIREMENTS.md updated to match (CHARTS-03..07 added, "Generic chart logic" removed from Out of Scope).

**Success criteria:**

1. The chart JSON schema is documented (shape, field names, types, bilingual label convention) in `data-pipeline/README.md`, covering both the `bar` shape (`series:[{label,value,pct}]`) and the `line` shape (`x_axis` + `lines:[{label,points:[{x,value}]}]`)
2. A `sources.yaml` entry with a `chart:` stanza passes `sync.py` without errors; `sync.py` logs a `[chart]` line and copies each per-LL output file if it exists, or logs `[chart] skipped - not yet built` if it doesn't
3. All 5 layers (`landuse-croptypes`, `buek250`, `io-lulc-landcover`, `boris`, `chelsa-climate`) have a `chart:` stanza and a real chart-computation script producing valid per-LL chart JSON matching the documented schema
4. Agriculture, soil, and economic charts show a % composition breakdown (crop type / soil group / usage type) per LL; landscape reuses the existing `land_cover_class_histogram.json`; climate is a `chart_type: "line"` showing % change per variable across the two future horizons

**Planning decisions (resolved during breakdown):**

- **One `compute_*_chart.py` script per layer**, not a shared driver — matching the strong
  existing one-script-per-data-type precedent (`build_land_cover.py`,
  `compute_climate_kpis.py`, `compute_protected_area_coverage.py`). A sixth new module,
  `chart_contract.py`, holds the two envelope writers so the CHARTS-01 schema and CLAUDE.md's
  `sort_keys=True` rule are satisfied in exactly one place and cannot drift across five layers.

- **D-10 and D-15 conflict and both are honoured.** D-10 locks `_sync_matched_pattern()` as
  the sync mechanism; D-15 requires naming each missing (layer, Living Lab) file, which a pure
  glob cannot do. `sync_charts()` therefore runs an explicit per-slug existence pre-check for
  the naming and still delegates the copy to `_sync_matched_pattern(..., tag="chart")`, so the
  repo-root-escape guard (`sync.py:337-341`) is inherited rather than re-implemented.

- **D-09's "no new statistical computation" framing was wrong** and is planned as real work:
  `compute_climate_kpis.py` hardcodes `DELTA_HORIZON = "2071_2100"` and Phase 8's D-21
  deliberately never opened the near horizon, so the 2041-2070 point exists nowhere on disk.
  `compute_climate_chart.py` imports `area_weighted_mean()` and computes both horizons itself.

- **Two boundary conventions coexist and the split is deliberate.** Agriculture and landscape
  use `build_clip_geometry()`'s 2000 m-buffered extent (inherited from Phase 6, so the two
  raster charts stay comparable); soil and climate use the true unbuffered
  `data/ll_boundaries.geojson`. Both scripts document the tension inline rather than inheriting
  it by omission.

- **Agriculture is the only genuinely new pipeline logic** — `landuse-croptypes` is the sole
  nationally-built raster (`output.pmtiles`, no `pmtiles_pattern`), so it gets its own plan with
  a dry-run gate on the smallest Living Lab before the full 481 MB five-Living-Lab run.

- Zero new packages. Every dependency (geopandas, rasterio, numpy, pyyaml, pytest) is already
  pinned in `data-pipeline/requirements.txt`.

Plans:

**Wave 1**

- [ ] `09-01-PLAN.md` — `chart_contract.py` bar/line envelope writers; `## Chart data contract`
      section in `data-pipeline/README.md`; `chart:` stanza bullet in `sources/README.md` (CHARTS-01)
- [ ] `09-02-PLAN.md` — 5 `chart.script` + 5 `output.chart_pattern` stanzas and 4 climate
      `label:{en,de}` blocks in `sources.yaml`; `tag` param on `sync_file`/`_sync_matched_pattern`;
      `sync_charts()` with per-(layer, LL) skip naming (CHARTS-02)

**Wave 2** *(blocked on Wave 1)*

- [ ] `09-03-PLAN.md` — `compute_landscape_chart.py`, `compute_soil_chart.py`,
      `compute_economic_chart.py` and their 15 chart files (CHARTS-04, CHARTS-05, CHARTS-06)
- [ ] `09-04-PLAN.md` — `compute_agriculture_chart.py`: per-LL clip + class histogram over the
      national crop-types raster, dry-run gate then full run, 5 chart files (CHARTS-03)
- [ ] `09-05-PLAN.md` — `compute_climate_chart.py`: two-horizon percent change per variable,
      the only `line` variant, 5 chart files (CHARTS-07)

**Wave 3** *(blocked on Wave 2)*

- [ ] `09-06-PLAN.md` — `sync.py` publish of all 25 files to `app/public/data/charts/`, Vite
      build confirmation, 5 new pytest contract tests (suite 20 -> 25) (CHARTS-01, CHARTS-02)

**Wave 4** *(blocked on Wave 3)*

- [ ] `09-07-PLAN.md` — full automated gate, 7 cross-file join-key checks, chart-script
      determinism check, D-01..D-16 + CHARTS-01..07 evidence record, blocking bilingual
      human verification of the computed values (all CHARTS ids)

### Phase 10: Wire up "Add for comparison" button to a real two-column LL comparison layout

**Goal:** Turn the placeholder "Add for comparison" button into a working side-by-side comparison of two Living Labs: clicking it opens a menu of LL names, and selecting one switches /ll/:slug into a two-column ?compare= view where each column stacks that LL's KPIs, map, chart and text under one shared layer-tab row.
**Requirements**: TBD
**Depends on:** Phase 9 (the comparison columns stack KPIs, maps and charts, so every map layer and the chart data contract must exist first)
**Plans:** 6/6 plans complete

**Context (captured 2026-07-27, promoted from backlog 999.2 on 2026-07-27):**

- The "Add for comparison" button in the bottom right is currently a placeholder with no behaviour
- On click it should open a small menu listing the LL names
- Selecting an LL switches the layout to two columns (one per LL)
- Each column shows a stacked view of KPIs, maps, charts, and text

Plans:
**Wave 1**

- [x] 10-01-PLAN.md — i18n comparison strings (EN+DE) plus StatPanel maxColumns/showEmptyState and BarChart minHeightWhenEmpty props
- [x] 10-02-PLAN.md — lift useLayerState into LLDetail (drop slug from remount keys) and make header LL pills carry/swap the ?compare= partner

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 10-03-PLAN.md — parse, validate and silently strip ?compare=; add the dismiss hook, the ComparePicker dropdown and the wired CompareCTA

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 10-04-PLAN.md — ComparisonColumn + LayoutCompare two-column grid with one shared LayerTabs row and one shared scroll container

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 10-05-PLAN.md — ComparisonBar replacing the A/B switcher, with change-partner, swap-sides and exit navigation

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 10-06-PLAN.md — full automated gate, D-01..D-29 evidence table, and blocking bilingual human verification

### Phase 11: Wire chart JSON data to chart UI components

**Goal:** Wire the chart content produced as JSON files in Phase 9 to the chart UI components in the app, so the charts render real data instead of placeholder/legacy sources.
**Requirements**: TBD (no ROADMAP or REQUIREMENTS.md REQ-IDs; REQUIREMENTS.md maps CHARTS-01..07 to Phase 9. The spec is `11-UI-SPEC.md`'s eight locked decisions, referenced as UI-1..UI-8 in every plan's `ui_decisions` field)
**Depends on:** Phase 9 (produces the chart data contract and JSON outputs), Phase 10 (comparison layout renders the same chart components in two columns)
**Plans:** 4/5 plans executed

**Context (captured 2026-08-03):**

- Phase 9 delivered the chart data contract and emits chart content as JSON files; this phase is the consumption side
- Scope is app-side integration only — no new pipeline work
- Expected to need minimal to no research and a small number of plans

**Planning decisions (resolved during breakdown):**

- **Climate needs a second component, not a patched `BarChart`.** Climate is the only `chart_type: "line"`
  layer (4 variables x 2 future horizons of percent change, values of both signs); the existing bar code
  path renders 6 fake months and cannot express that shape at all. `LineChart.jsx` is hand-rolled SVG plus
  absolutely-positioned divs — no charting library is added, per the UI-SPEC.

- **Every real bar file exceeds 6 categories** (landscape 7-8, soil 9-14, agriculture 18, economic 17-31),
  so the top-6-plus-Other truncation is the production path, not an edge case. It lives in a pure
  `app/src/lib/chartSeries.js` module rather than inside the component, so a node command can assert the
  row cap, the preserved pct total and the never-re-sort rule against all 20 real files — the project has
  no JS test runner, so a node-importable pure module is the only way to get a real automated gate here.

- **Two UI-SPEC statements were wrong against the code and are corrected in the plans.** (a) It assumes
  every chart call site's card already renders a title; only `LayoutSplit` does, so `11-04` adds title rows
  to `LayoutStacked` and `ComparisonColumn`. (b) Its defensive climate-colour fallback (compare the
  translated `CLIMATE_VARIABLES[i].labelKey` against `lines[i].label[lang]`) can never match — the i18n
  labels are abbreviations ("GDD", "Mean temp.") while the JSON carries full names ("Growing degree days")
  — so a length-guarded index mapping is the locked behaviour instead.

- **`app/src/i18n.js` is the hot file** and is deliberately split across two waves: additions in `11-01`
  (wave 1), deletions of the dead `charts.*` / `barChart.*` blocks in `11-04` (wave 3), once nothing
  references them. Only wave 2 parallelizes (`11-02` BarChart and `11-03` LineChart touch disjoint files).

- Zero new npm packages; zero pipeline files touched (both asserted as gates in `11-05`).

Plans:

**Wave 1**

- [ ] `11-01-PLAN.md` — `useChartData` hook (404 = empty), pure `chartSeries.js` truncation + rank palette,
      shared `ChartStates.jsx` blocks, and the `chart.*` / `llDetail.projectionTitle` i18n additions

**Wave 2** *(blocked on Wave 1)*

- [ ] `11-02-PLAN.md` — `BarChart.jsx` rewrite: real per-Living-Lab data, three async states, top-6 + Other
      rows with rank colours, value+unit captions, real source footer
- [ ] `11-03-PLAN.md` — new `LineChart.jsx`: 4 fixed-colour polylines over 2 horizons, zero-inclusive shared
      scale, dashed zero line, signed percentage labels

**Wave 3** *(blocked on Wave 2)*

- [ ] `11-04-PLAN.md` — three `LLDetail.jsx` call sites branch on `layer === 'climate'` and thread `ll`;
      titled cards everywhere; `chart_data.js` and the dead `charts.*` / `barChart.*` i18n blocks deleted

**Wave 4** *(blocked on Wave 3)*

- [ ] `11-05-PLAN.md` — full automated gate (lint/format/build, 25-file join-key + contract check,
      dead-token and scope gates), `11-EVIDENCE.md` for UI-1..UI-8, blocking bilingual human verification

## Backlog

### Phase 999.1: Find real data sources for 4 curated Destatis KPI fields with no Destatis-family source (BACKLOG)

**Goal:** [Captured for future planning]
**Requirements:** TBD
**Plans:** 0 plans

Plans:

- [ ] TBD (promote with /gsd:review-backlog when ready)

---

*Created: 2026-04-29*
