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

---

*Created: 2026-04-29*
