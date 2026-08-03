# Phase 9: Chart Data Contract - Context

**Gathered:** 2026-08-03
**Status:** Ready for planning

<domain>
## Phase Boundary

**Scope expanded during this discussion** (see Specific Ideas) beyond the original
"contract and plumbing only" framing: this phase now documents the chart output JSON
schema, wires `sources.yaml` + `sync.py` chart-copy plumbing, **and implements real
chart-computation scripts for all 5 map layers** (agriculture, soil, landscape,
economic, climate), so every LL detail tab ships a real, pipeline-computed summary
chart — not a dry-run validation on one layer. REQUIREMENTS.md and ROADMAP.md have been
updated in place to match (CHARTS-01..02 kept as the contract/plumbing pair,
CHARTS-03..07 added for the five per-layer implementations; "Generic chart logic" was
removed from REQUIREMENTS.md's Out of Scope).

Wiring the produced chart JSON into `BarChart.jsx` (or a new line-chart component for
climate) is **still out of scope** — that consumption step remains a v2 requirement.
This phase's boundary ends at: schema documented, `sources.yaml`/`sync.py` plumbing
working, and real chart JSON files committed and synced to
`app/public/data/charts/` for all 5 layers.

</domain>

<decisions>
## Implementation Decisions

### Schema shape — chart_type as a discriminator
- **D-01:** `chart_type` is the discriminator for the whole JSON payload's shape, not
  just a label. Two values are implemented in this phase:
  - **`"bar"`** → `{ ll_slug, layer_id, chart_type, unit:{en,de}, series:[{label:{en,de}, value, pct}], mock, source, generated_at }` — exactly CHARTS-01's original shape. Used by agriculture, soil, landscape, economic.
  - **`"line"`** → `{ ll_slug, layer_id, chart_type, unit:{en,de}, x_axis:[{key, label:{en,de}}], lines:[{label:{en,de}, points:[{x, value}]}], mock, source, generated_at }` — a genuinely different structure, not a `series` array stretched to fit x-axis points. Used only by climate.
  - Both variants share the same envelope fields (`ll_slug`, `layer_id`, `chart_type`,
    `unit`, `mock`, `source`, `generated_at`); only the data-carrying field(s) differ
    (`series` vs. `x_axis`+`lines`).
  - `chart_type` remains an **open string** overall (not a code-enforced enum) — "bar"
    and "line" are the two values with real consumers/producers after this phase, but
    nothing prevents documenting a third later.

### `mock` field semantics
- **D-02:** `mock: true` means this chart JSON's values are synthetic/placeholder data
  — not yet computed from real geodata. A **fresh, per-chart-file definition**,
  deliberately decoupled from the Phase 1 "preliminary data" LL badge concept, which was
  fully deleted from the app in commit `a37a9b4` (confirmed zero `mock` references
  remain anywhere in `app/src` or `data-pipeline`). Since this phase computes real
  values for all 5 layers, every committed chart file should have `mock: false` by the
  time the phase closes — the flag exists for future placeholder/dry-run cases, not
  because any output in this phase actually is a placeholder.

### Schema documentation location
- **D-03:** Documented as a **new section in `data-pipeline/README.md`** (not a
  standalone spec file), styled after the existing `## BUEK250 soil semantics contract`
  section: field list plus short prose, covering both the `bar` and `line` shapes as
  named variants under one `chart_type`-discriminated heading.

### `source` field shape
- **D-04:** `source` is a **plain string holding the `sources.yaml` layer `id`** (e.g.
  `"landuse-croptypes"`, `"chelsa-climate"`), not a human-readable attribution string
  and not a nested object. Full provenance already lives once in `sources.yaml` and is
  already surfaced to the frontend via `generate_layer_sources()` → `layer_sources.js`;
  the chart JSON references it by id rather than duplicating attribution text.

### Per-layer chart content

- **D-05 (Agriculture / `landuse-croptypes`):** `chart_type: "bar"`, series = % area per
  crop type per LL. **Requires new pipeline work**: `landuse-croptypes` is built as one
  national PMTiles file today (`output.pmtiles`, not `output.pmtiles_pattern`) — there is
  no existing per-LL clip+histogram for it, unlike land cover. The chart script must
  clip the source raster to each LL boundary and compute a per-class pixel histogram,
  modeled on `build_land_cover.py`'s histogram step (Phase 6), then convert to
  percentages.
- **D-06 (Soil / `buek250`):** `chart_type: "bar"`, series = % area per `soil_group_key`
  per LL. Computed via projected-CRS area (dissolve by `soil_group_key` → clip to LL →
  area in `EPSG:25832` or similar), following the Phase 05.1
  `compute_protected_area_coverage.py` dissolve→clip→area pattern. `soil_group_key`
  (not `feature_kind` or raw `SYM_NR`) is the grouping field, per the Phase 2.2 semantic
  contract.
- **D-07 (Landscape / `io-lulc-landcover`):** `chart_type: "bar"`, series = % area per
  land-cover class per LL. **Nearly free** — `data/land_cover_class_histogram.json`
  already exists, keyed per LL slug with per-class pixel counts (confirmed: 5 LL keys,
  each a `{class_value: pixel_count}` map, including a `"0"` nodata key that must be
  excluded from the percentage denominator). The chart script converts existing counts
  to percentages; no new geometry/raster computation needed.
- **D-08 (Economic / `boris`):** `chart_type: "bar"`, series = % of zones per
  usage-type category per LL, using the existing bilingual usage-type semantic contract
  (`boris_semantics.py`, Phase 7 D-11) already present in the committed per-LL GeoJSON.
  Counts zones (feature count), not area — consistent with how the usage-type field is
  categorical/non-spatially-weighted in its current form.
- **D-09 (Climate / `chelsa-climate`):** `chart_type: "line"`, one line per variable
  (gdd, bio1, bio12, bio18), each with 2 points: `% change` at `2041_2070` and at
  `2071_2100`, relative to the 1981-2010 baseline. Reshapes figures already computed by
  `compute_climate_kpis.py` / present in `data/climate_kpis.json` — no new statistical
  computation, only reformatting into the `x_axis`+`lines` shape. Percent change (not
  absolute delta) is used for all 4 variables here specifically so temperature-family
  and water-family variables share one comparable unit on one chart, unlike
  `StatPanel`'s per-variable-unit-aware delta tiles (Phase 8 D-11).

### Output file granularity & sync plumbing
- **D-10:** All 5 layers get a `chart:` stanza in `sources.yaml` (not just
  `landuse-croptypes` as a dry run). Chart output is **one JSON file per (layer, LL)**,
  following the existing `geojson_pattern`/`pmtiles_pattern` naming idiom (e.g.
  `data/charts/{layer}-{slug}.json`). `sync.py`'s new chart-sync function should use the
  existing glob-based `_sync_matched_pattern()` helper (the same one
  `sync_pmtiles_per_ll()` and `sync_vector_geojson()` already use for `{slug}`-patterned
  outputs), not the single-file `sync_pmtiles()` model — this was originally deferred to
  "Claude's Discretion" under the dry-run-only framing but is now a locked decision
  given 5 layers × 5 LLs = 25 real files.
- **D-11:** `sync.py` still does not invoke chart scripts — it only copies
  already-produced output files, exactly like every other `sync_*` function. Chart
  scripts are run manually by a developer, same as `build_pmtiles.py` / `build_vector.py`
  today. Logging follows the bracketed-tag convention: `[chart]` per file copied,
  `[chart] skipped - not yet built` if a declared output is missing (locked by CHARTS-02
  and ROADMAP success criterion 2).
- **D-12:** Given this phase now commits 25 real chart output files across every data
  domain in the project (raster, vector-by-area, vector-by-count, continuous-field
  time series), `pytest` smoke tests validating each chart output's existence and
  contract shape are **required, not discretionary** — following the established
  precedent that every phase producing committed pipeline outputs has smoke tests
  (Phase 2 PIPELINE-03 onward). Style should follow
  `test_pipeline_outputs.py`'s existing per-fixture assertion-dense function pattern.

### Claude's Discretion
- Exact key name(s) inside each layer's `chart:` sources.yaml stanza (e.g.
  `chart.script`, `chart.output_pattern`) — follow the established `build.script` /
  `output.*_pattern` naming idiom already used by every other layer kind.
- Whether each layer gets its own standalone chart-computation script (mirroring the
  strong existing one-script-per-data-type precedent: `build_land_cover.py`,
  `compute_climate_kpis.py`, `compute_protected_area_coverage.py`, `fetch_boris.py`) or
  a shared driver script — the former is the established pattern and is expected, but
  not a user-facing decision.
- Exact projected CRS used for soil's area computation (D-06) — follow whatever
  `compute_protected_area_coverage.py` already uses for consistency.
- New chart-output JSON writer code must call `json.dumps(..., sort_keys=True)` per
  CLAUDE.md's rule — note that `sync.py`'s four *existing* `json.dumps()` calls do
  **not** currently pass `sort_keys=True` (a pre-existing gap between CLAUDE.md and the
  code), but fixing that pre-existing gap in unrelated existing code is out of this
  phase's scope — only new code must comply.

</decisions>

<specifics>
## Specific Ideas

- **This phase's scope changed mid-discussion.** The initial CONTEXT.md draft (contract
  + one-layer dry-run only, matching ROADMAP.md/REQUIREMENTS.md's original text
  verbatim) was rejected by the human, who clarified the actual intent: real
  chart-producing scripts for every tab, now. REQUIREMENTS.md and ROADMAP.md have been
  edited in place to reflect this (see canonical_refs) — a downstream agent reading
  either document directly will see the expanded scope already, not a contradiction to
  reconcile.
- The `line` chart_type was not part of any prior written requirement — it emerged
  specifically because climate's continuous, multi-unit, multi-horizon data doesn't fit
  a "% composition" bar chart the way the other 4 tabs' categorical data does. The human
  explicitly wanted `chart_type` to work as a real discriminator with its own documented
  shape per type, not one `series` shape awkwardly reused for both.
- The codebase has two competing bilingual-field conventions today: nested `{en, de}`
  objects (`sources.yaml` legends, `climate_kpis.json`) versus flat `_en`/`_de`-suffixed
  keys (`destatis_curated_kpis.json`). CHARTS-01's own requirement wording locks the
  **nested-object** form for both the `bar` and `line` chart schemas — not itself an
  open question in this discussion.
- Landscape (D-07) and climate (D-09) are the two "cheap" charts — both reshape data a
  prior phase already computed (`land_cover_class_histogram.json`,
  `climate_kpis.json`). Agriculture (D-05) is the one layer requiring genuinely new
  raster-clipping pipeline logic, since `landuse-croptypes` was built nationally rather
  than per-LL (there was no prior need for a per-LL split before this phase).

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & requirements (updated during this discussion — read these, not memory of the old text)
- `.planning/ROADMAP.md` — Phase 9 entry, updated 2026-08-03 to describe the expanded
  goal, CHARTS-01..07 requirement list, and 4 success criteria (was 3; #4 added for the
  per-layer content).
- `.planning/REQUIREMENTS.md` — CHARTS-01..07 now all live under Phase 9's "Chart Data
  Contract & Implementation" heading in v1 Requirements (moved out of v2, moved out of
  Out of Scope). CHARTS-01's schema text is now chart_type-discriminated
  (bar/line), matching D-01 above.
- `CLAUDE.md` — `json.dumps(..., sort_keys=True)` everywhere in `sync.py`; pipeline-app
  contract is files on disk only.

### Prior phase precedents
- `.planning/phases/08-add-maps-and-stats-for-climate-variables-using-chelsa-data/08-CONTEXT.md`
  — `climate_kpis.json`'s existing baseline+change figures are what D-09's line chart
  reshapes; D-11 there (unit-aware delta, absolute for temperature-family / percent for
  water-family) is explicitly **not** followed for the chart — D-09 uses percent
  uniformly across all 4 variables so they share one line-chart axis.
- `.planning/phases/06-add-land-cover-map/06-CONTEXT.md` — `build_land_cover.py`'s
  per-LL clip+histogram step is the direct model for D-05's new agriculture pipeline
  work, and `land_cover_class_histogram.json`'s existing shape is what D-07 reads as-is.
- `.planning/phases/05-add-protected-areas-as-toggleable-layer-on-landscape-map/05-CONTEXT.md`
  and the Phase 05.1 "Locked decisions" block in `.planning/ROADMAP.md` —
  `compute_protected_area_coverage.py`'s dissolve→clip→area-in-projected-CRS pattern is
  the direct model for D-06's soil area computation.
- `.planning/phases/07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi/07-CONTEXT.md`
  — D-11 there (bilingual usage-type semantic contract, `boris_semantics.py`) is what
  D-08's economic chart groups zones by.
- Phase 2.2 (Soil Semantics & Translation, `.planning/phases/` — search for its
  CONTEXT.md) — established `soil_group_key` as the stable grouping field D-06 uses.

### Files this phase modifies
- `data-pipeline/sources/sources.yaml` — add a `chart:` stanza to **all 5** layer
  entries (`landuse-croptypes` lines 13-68, `io-lulc-landcover` 70-129, `buek250`
  130-175, `boris` 213-301, `chelsa-climate` 303-467), each as a sibling top-level key to
  `build:`/`output:`, following the `climate:`/`vector:`/`wfs:` sibling-stanza
  precedent.
- `data-pipeline/sync.py` — add a chart-sync function using `_sync_matched_pattern()`
  (line 320) as its model, called from `sync_to_app()`'s orchestration list (line 378
  area, alongside the other `sync_*` calls).
- `data-pipeline/README.md` — new chart-type-discriminated schema section (D-03).
- `data-pipeline/sources/README.md` — add the new `chart:` stanza's fields to the
  existing "what belongs in each layer entry" documentation.
- New Python scripts (naming/count at planner's discretion) computing real chart data
  for each of the 5 layers.
- `data-pipeline/tests/test_pipeline_outputs.py` — new smoke tests per D-12.

### Files this phase reads but should not need to change
- `app/src/components/BarChart.jsx`, `app/src/data/chart_data.js` — the current
  placeholder chart-rendering path (confirmed: `agriculture`/`soil`/`economic`/
  `landscape`/`climate` all have hand-authored placeholder bars today, with `climate`'s
  placeholder shaped as *monthly* values — unrelated to and superseded by D-09's line
  chart). Wiring is explicitly out of scope (v2).
- `data/land_cover_class_histogram.json` — read as-is by D-07's chart script, not
  modified.
- `data/climate_kpis.json` — read as-is by D-09's chart script, not modified.
- `data-pipeline/python/generate_metadata.py` — no chart-JSON merge into
  `ll_metadata.json` is implied; chart files are copied standalone into
  `app/public/data/charts/`, not merged into metadata.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`data/land_cover_class_histogram.json`** — already per-LL keyed
  (`{ll_slug: {class_value: pixel_count}}`, confirmed via direct read: 5 LL keys, each
  with an excludable `"0"` nodata key) — D-07's chart script reads this directly, no new
  computation.
- **`data/climate_kpis.json`** — already has area-weighted baseline + change figures
  per variable per LL (Phase 8 D-22/D-23) — D-09's line chart reshapes these numbers,
  computing percent change if not already stored as percent.
- **`sync.py::_sync_matched_pattern()`** (line 320) — the glob-based per-LL sync helper
  already used by `sync_pmtiles_per_ll()` and `sync_vector_geojson()`; the direct model
  for the new chart-sync function per D-10.
- **`build_land_cover.py`**'s per-LL clip + class-histogram step — the direct model for
  D-05's new agriculture per-LL histogram logic.
- **`compute_protected_area_coverage.py`**'s dissolve→clip→area pattern — the direct
  model for D-06's soil area-per-group computation.
- **`boris_semantics.py`**'s bilingual usage-type lookup — feeds D-08's economic
  zone-count-by-category chart directly from the already-committed per-LL GeoJSON.
- **`data-pipeline/tests/conftest.py`** — shared `repo_root()` and `LL_SLUGS` fixtures
  already used by every pipeline smoke test; new chart contract tests reuse these
  directly.
- **`test_pipeline_outputs.py::test_buek250_layer_contract_declared`** — style precedent
  for a "declared config in sources.yaml matches an expected contract" test.

### Established Patterns
- Every `sources.yaml` layer-entry field carries inline `#` comments citing the
  Decision ID and phase/plan that produced it — the new `chart:` stanzas should cite
  D-01..D-12 the same way.
- `sync.py`'s logging is bracketed single-word tags: `[sync]`, `[skip]`, `[warn]` (no
  `[ok]` tag exists). `[chart]` is a new tag, matching this style.
- Bilingual fields are always `{ en, de }` nested objects in every `sources.yaml`-adjacent
  generated JSON except `destatis_curated_kpis.json`'s flat `_en`/`_de` suffix outlier.
- `landuse-croptypes` is currently the **only** raster layer built nationally rather
  than per-LL (`output.pmtiles`, not `output.pmtiles_pattern`) — D-05's per-LL histogram
  work does not require rebuilding the PMTiles itself per-LL, only computing per-LL
  statistics from the same source raster clipped in-memory per LL boundary.

### Integration Points
- `sources.yaml` — 5 layer entries, each gaining a `chart:` stanza.
- `sync.py`'s `sync_to_app()` orchestrator — one new `sync_*` call site.
- `app/public/data/charts/` — new output directory; does not exist yet, created on
  first successful sync; will hold 25 files (5 layers × 5 LLs) after this phase.

</code_context>

<deferred>
## Deferred Ideas

- **`useChartData(layerId, slug)` frontend hook** and wiring `BarChart.jsx`/a new
  line-chart component to the new contract — v2 requirement, this phase produces the
  files but does not consume them in the UI.
- **`--build-all` flag**, replacing placeholder KPI values, adding layers beyond the
  current 5 — unchanged v2 items, untouched by this discussion.
- **De-duplicating `app/public/data/` from `data/` in git** (pending todo
  `single-copy-public-data.md`) — reviewed during this discussion and explicitly left in
  the backlog; it's a repo-size/CI concern unrelated to the chart data contract.
- **Reconciling the two competing bilingual-field conventions** (`{en,de}` nested vs.
  `_en`/`_de` flat suffix) project-wide — not raised as an in-scope cleanup; this phase
  simply follows the already-locked nested form for its own new fields.

</deferred>

---

*Phase: 09-chart-data-contract*
*Context gathered: 2026-08-03*
