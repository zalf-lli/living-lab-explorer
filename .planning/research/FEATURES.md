# Features Research — Phase 4: Data Pipeline & Content System

**Domain:** Geodata content/data pipeline system for a regional environmental research explorer
**Researched:** 2026-04-29
**Confidence:** HIGH (grounded in the actual codebase and established domain patterns; WebSearch unavailable)

---

## Table Stakes — LL Content System

These are the fields users of regional geodata portals always expect to see per region. Missing any
of them makes the per-region page feel like an empty template rather than a real data product.

### Identity fields (display + navigation)

| Field | Why expected | Complexity | Status in codebase |
|-------|--------------|------------|--------------------|
| Short name (EN + DE) | Used in nav pills, cards, page titles | Low | Present in `ll_metadata.json` |
| Tagline / one-liner (EN + DE) | Gives instant orientation on the landing card | Low | Present (`tagline`) |
| Brand colour + outline colour | Visual identity on map outlines, badges, cards | Low | Present in `ll_display.js` |
| Per-LL icon / symbol | Differentiates regions in the nav and badges | Low | Present (`ll_icons.js`) |
| Display order | Consistent ordering across all views | Low | Present (`LL_ORDER`) |
| NUTS-3 code list | Machine-readable link to official EU geography | Low | Present (`nuts3` array) |
| Region label (federal state) (EN + DE) | Grounds the region in familiar administrative geography | Low | Hardcoded in `ll_display.js`; should come from metadata |
| `mock` / draft flag | Signals provisional vs. finalised content to reviewers | Low | Present in JSON, **not surfaced in UI** |

### Narrative / descriptive fields

| Field | Why expected | Complexity | Status |
|-------|--------------|------------|--------------------|
| Soil description (EN + DE) | This is a research Living Lab; soil is the first question | Low | Present in `description.soil` |
| Climate description (EN + DE) | Required context for agricultural research | Low | Present in `description.climate` |
| Geography / landscape description (EN + DE) | Orientation for non-specialists | Low | Present in `description.geography` |
| Key challenges (bulleted list, EN + DE) | Explains the research motivation | Low | Present in `description.challenges` |
| Delineation justification (EN + DE) | Explains why these NUTS-3 codes were chosen | Low | Present in `delineation` |

### Numeric / tabular fields (production system)

These are currently `"—"` placeholders in the JSON. Users who open a region card
expect at least the core ones to be filled.

| Field | Why expected | Complexity | Priority |
|-------|--------------|------------|----------|
| Total land area (km²) | First KPI on every regional profile | Low | HIGH — currently in `ll_display.js` hardcoded |
| Agricultural area (% of total) | Core metric for an agroecology network | Low | HIGH |
| Grassland area (% of total) | Core for mixed farming / climate LLs | Low | Medium |
| Forest area (% of total) | Context for land-use balance | Low | Medium |
| Main crop types | Characterises farming system immediately | Low | HIGH |
| Average farm size (ha) | Structural context for farm economics | Low | Medium |
| Organic agriculture (%) | Research interest of the LL network | Low | High |
| Main livestock | Characterises animal husbandry systems | Low | Medium |
| Protected area (%) | Environmental significance | Low | Low |
| Average rent rate (€/ha) | Socioeconomic context for farmer surveys | Low | Low |

### Numeric / tabular fields (socioeconomic)

| Field | Why expected | Complexity | Priority |
|-------|--------------|------------|----------|
| Population | Standard regional context | Low | Medium |
| Population density (pop/km²) | Rurality indicator | Low | Medium |
| Nearest major city | Geographic orientation | Low | Low |

### Soil-climate summary fields (already present and real in one LL)

| Field | Status |
|-------|--------|
| Main soil types | Present (text) |
| Topography class | Present (text) |
| Altitude range | Present (text) |
| Rainfall range (mm/yr) | Present (text) |
| Temperature range (°C) | Present (text) |

These five are already well-designed. They should be the primary soil-climate KPI sources
for the `KPIStrip` (replacing the hardcoded values in `ll_display.js`).

### Fields to keep out of the hand-authored JSON

These must come from the pipeline, not hand-authoring, because they are computed from geodata:

| Field | Source |
|-------|--------|
| Computed area (km² from dissolved NUTS-3) | `fetch_nuts.py` → `ll_metadata.json` |
| Soil class distribution (% per class) | BÜK pipeline → chart JSON per LL |
| Crop type distribution (% per class) | Crop types pipeline → chart JSON per LL |

---

## Table Stakes — Chart Summaries for Categorical Area Data

For soil classification (BÜK-type) and land-use/crop-type data, these are the chart types and
statistics that users of environmental dashboards reliably expect.

### Chart type: horizontal proportional bar chart (ranked)

This is the dominant pattern for categorical area data in regional geodata portals. It answers
"how much of this region is each category?" at a glance.

**Required elements:**
- One bar per category, sorted descending by area share
- Bar length proportional to percentage of total area (0–100%)
- Category label left of bar (translated EN/DE)
- Numeric value right of bar (percentage to 1 decimal place, e.g. `38.4%`)
- Bar colour matching the map legend colour for that category
- Source citation below the chart (dataset name + year)

The existing `BarChart.jsx` already implements this correctly. The missing piece is that
the bars are not per-LL and not computed from real data.

**What the BarChart component needs from the pipeline:**
```json
{
  "layer": "soil",
  "ll_slug": "east-brandenburg",
  "unit": "%",
  "bars": [
    { "key": "SS", "label": { "en": "Sandy soil (SS)", "de": "Sandiger Boden (SS)" }, "v": 42.3, "c": "#d4b483" },
    { "key": "SL", "label": { "en": "Sandy loam (SL)", "de": "Sandiger Lehm (SL)" }, "v": 28.1, "c": "#c4a870" }
  ],
  "source": "BKG BÜK 1000 v2.0",
  "generated_at": "2026-04-29"
}
```

The current `chart_data.js` shape (`{ key, v, c }`) is correct but misses `label` (uses i18n
key instead) and has no `source` or `generated_at` field. The contract should add these.

### Statistics users expect to see for BÜK soil classification

The BÜK (Bodenübersichtskarte) classifies soils by `BOART` (soil type abbreviation) plus `BGL`
(soil parent material group). For a regional soil summary, the minimum expected output is:

| Statistic | Description | Chart form |
|-----------|-------------|------------|
| % area per soil type abbreviation (BOART) | How much of the LL is each broad soil type | Horizontal bar |
| Dominant soil type | Single-value KPI (the top-ranked BOART) | KPI tile |
| Number of distinct soil types present | Structural richness indicator | KPI tile or subtitle |

**Not expected at this stage (defer):**
- Soil capability index (Ackerzahl) distribution — requires a different attribute; complex
- Depth-to-groundwater statistics — requires an additional joined attribute
- Cross-tabulation of soil type × land use — requires spatial join; Phase 5+ complexity

### Statistics users expect for categorical land-use / crop-type data (DLR layer)

| Statistic | Description | Chart form |
|-----------|-------------|------------|
| % area per crop class (top N, e.g. top 8) | Dominant crops in the LL | Horizontal bar |
| Dominant crop type | Single-value KPI | KPI tile |
| Arable vs. grassland share | Summary of land-use character | KPI or sub-bar |

**Important: "top N" truncation for crop types.** The DLR layer has 20 classes. Showing all 20
bars makes the chart unreadable. Standard practice in environmental dashboards is to show the
top 8–10 categories by area share and merge the rest into "other". The pipeline should emit
bars already ranked and truncated; the frontend should not need to do this.

### What the mock `chart_data.js` already gets right

The existing data shape `{ key, v, c }` and the `BarChart` rendering logic (relative bar widths,
colour coding, source caption) are correct patterns. Phase 4 should preserve this shape and add:
1. Per-LL data (currently the same values are shown for all five LLs)
2. A `source` field (dataset name + year)
3. A `mock: true/false` flag so the UI can show a "placeholder data" badge (the bug documented
   in CONCERNS.md)
4. `label` objects for EN/DE (currently delegated entirely to i18n keys, which breaks when keys
   don't exist for pipeline-generated category codes like BÜK `BOART` abbreviations)

---

## Differentiators

What separates good regional geodata explorers from basic ones. These are features the target
audience (agricultural researchers, stakeholders, policy reviewers) notice and value, but they
are not the first things to build.

### 1. Draft / mock data badge (HIGH VALUE, LOW COST)

Good portals signal clearly which content is provisional. The `mock` flag already exists in
`ll_metadata.json` but is never shown to the user. A small "Preliminary data / Vorläufige Daten"
banner on the LL detail page, driven by `ll.mock`, immediately separates the one real LL
(Hessian Low Mountain Range) from the four placeholder LLs. Cost: one conditional render.

### 2. Source citation on every data element

Good portals cite their data at the point of use. The `BarChart` already has a source caption
slot (`t('barChart.source', { unit })`), and `MapInfoControl` shows layer provenance. What's
missing is the citation in the chart data itself (see `generated_at` + `source` fields above).
For BÜK data this matters because the BKG license requires attribution.

### 3. Per-LL variation in charts

The single biggest differentiator between a real explorer and a demo: East Brandenburg shows
sandy soils, Havelländisches Luch shows peat/gley, Rheingau shows slate/shallow loam. When
charts reflect actual pipeline-computed values per LL, the product becomes genuinely useful to
researchers comparing regions. This is exactly what Phase 4.3 is designing for.

### 4. Consistent colour mapping between legend and chart

Strong explorers maintain legend-to-chart colour identity: the colour for "sandy soil" in the
bar chart is the same as the polygon colour on the map. The existing `landuse_legend.js`
generation pattern already achieves this for crop types. The chart data contract should require
that `c` (colour) in each bar matches the legend colour from `sources.yaml` for that category.

### 5. Delineation justification visible to users

The `delineation` field is authored in the JSON but not rendered anywhere in the UI. For
researchers and policy reviewers, understanding why a region's boundaries were drawn is as
important as the statistics themselves. Showing this as a collapsible "Why these boundaries?"
section is a high-value differentiator at low cost.

---

## Anti-Features

Things these apps often include that add complexity without value. Avoid in Phase 4.

### 1. Generic chart logic in the pipeline

**What gets built:** A universal "compute-chart-for-any-layer" function that tries to handle
raster layers, vector layers, and tabular CSVs with one code path.
**Why it fails:** The statistic you want from BÜK polygons (% area per BOART, weighted by
polygon area) is entirely different from what you want from the crop-type raster (pixel count
per class). The correct abstraction does not exist until you have implemented at least two real
chart sources. Phase 4.3 calls this out explicitly: design the interface only, not the
implementation. Do not invent a generic function prematurely.

### 2. Interactive chart filtering / drill-down

**What gets built:** Click a bar to filter the map to that category, or a time-series selector
for multi-year data.
**Why it adds no value now:** There is no time-series data, and the map interaction story is
already complex. Adding chart-to-map linking before both the chart data and the vector layer
rendering are solid creates a fragile two-way dependency. Defer until both subsystems are stable.

### 3. A separate chart JSON file per LL per layer

**What gets built:** `chart_east-brandenburg_soil.json`, `chart_havelland_soil.json`,
etc. — one file per LL per layer.
**Why it adds complexity:** Five LLs × four layers = 20 files that must all be in sync,
all fetched separately, and all cached in the client. The better contract is to embed chart
data inside the existing `ll_metadata.json` output under a `charts` key per layer, or to
produce one `ll_charts.json` with all LLs. Either way, one file, one fetch.

### 4. Embedding raw geodata attributes in the chart JSON

**What gets built:** The full attribute table of the BÜK polygons (BOART, BGL, BZG, etc.)
serialised into the chart output.
**Why it fails:** BÜK has ~30 attributes per polygon; including raw attributes bloats the
output and forces the frontend to implement aggregation logic. The pipeline must do the
aggregation (weighted area sum) and emit only the display-ready bars.

### 5. A CMS or admin UI for hand-authored content

**What gets built:** A web form for researchers to edit taglines and descriptions in a browser.
**Why it adds no value now:** The team is comfortable with git and JSON. A CMS adds a runtime
backend, authentication, and a deployment dependency. The hand-authored JSON in-repo approach
(Phase 4.1 plan) is exactly right for the scale and team.

### 6. Automatic "coming soon" content for missing fields

**What gets built:** If a field is `"—"`, the UI automatically shows an estimated value
derived from adjacent data or a default.
**Why it is harmful:** Fabricated data in a research tool damages credibility. The correct
handling of `"—"` placeholders is to render them as `—` or to hide the row. Do not infer.

### 7. Multiple chart types per layer (pie + bar + map)

**What gets built:** A pie chart showing the same soil distribution as the bar chart, plus a
choropleth mini-map, plus a table.
**Why it adds no value:** For categorical area data, the horizontal ranked bar chart is the
clear winner for readability. Pie charts become unreadable at more than five categories (BÜK
and crop types both exceed five). A choropleth mini-map duplicates the main map. Add types only
when a specific dataset justifiably needs a different representation (e.g. a line chart for
monthly temperature data).

---

## Implications for Phase 4

Findings that directly affect implementation decisions in Phase 4.1–4.3.

### 4.1 Hand-authored LL content JSON + sync.py

**Field set is already well-designed.** The existing `ll_metadata.json` schema (identity,
narrative descriptions, production, socioeconomic) covers the table-stakes fields. The gaps to
fill before Phase 4.1 is complete:

1. The `kpi` block in `ll_display.js` must migrate to `ll_metadata.json`. Specifically:
   - `area` → derive from `production.land_area` or compute from dissolved NUTS geometry
   - `farms` → `production.active_farms` (new field, not yet in schema)
   - `tempRange` → derive from `soil_climate.temperature`
   - `soil` → derive from `soil_climate.main_soil_types`
   - Precipitation is in `soil_climate.rainfall` but not in the KPI strip — add it or drop it

2. The `region` label (federal state) currently hardcoded in `ll_display.js` should be added
   to the hand-authored JSON and emitted into `ll_metadata.json` by `sync.py`.

3. The `mock` flag is present but the CONCERNS.md documents that no component reads it.
   Phase 4.1 should add a visible "Preliminary data / Vorläufige Daten" badge driven by
   `ll.mock`. This is table-stakes for a research audience.

4. `sync.py` merge logic: the hand-authored JSON provides identity + narrative + production
   skeleton; the pipeline computes computed KPIs (area from geometry) and chart data. The
   merged `ll_metadata.json` must carry a clear schema comment so future contributors know
   which fields are hand-authored vs. pipeline-computed.

### 4.2 BKG BÜK soil vector layer

**The BÜK shapefile is already in the repo** at `data/boart1000_ob_v20/`. It contains
`boart1000_ob_v20.shp` with a `BOART` attribute (soil type abbreviation). The pipeline task is:

1. Clip to each LL's NUTS-3 boundary
2. Compute area-weighted percentage per `BOART` value
3. Emit a ranked bar list (top 8–10 categories + "other")
4. Assign colours from a BÜK-specific palette (brown/ochre tones; see `chart_data.js` soil
   placeholders for the existing colour choices)

**Note on the existing colour placeholders.** The current `chart_data.js` soil bars use keys
`sandyLoam`, `loam`, `clayLoam`, `peat`, `other` — these are English-language descriptions,
not BÜK `BOART` codes. The pipeline should use the official BOART abbreviations (e.g. `SS`,
`SL`, `Sl`, `T`, `Mo`) as keys, with `label.en` / `label.de` carrying the human-readable
translations. This allows the frontend to use the key for CSS/legend lookups and the label
for display.

### 4.3 Chart data contract

**Recommended contract shape** (minimal, sufficient, bilingual):

```json
{
  "layer_id": "soil",
  "ll_slug": "east-brandenburg",
  "chart_type": "bar_horizontal",
  "unit": "%",
  "mock": false,
  "source": { "provider": "BKG", "dataset": "BÜK 1000 v2.0", "year": 2020 },
  "generated_at": "2026-04-29",
  "bars": [
    {
      "key": "SS",
      "label": { "en": "Sandy soil (SS)", "de": "Sandiger Boden (SS)" },
      "v": 42.3,
      "c": "#d4b483"
    }
  ]
}
```

**Why this shape:**
- `key` is the authoritative code (BOART or DLR class integer) used for colour lookups
- `label` carries bilingual display text, decoupling it from i18n key indirection
- `v` is already-computed percentage (pipeline does the aggregation, not the frontend)
- `c` is the colour that matches the map legend (enforced by reading from `sources.yaml` palette)
- `mock: true/false` gates the "placeholder data" badge in `BarChart.jsx`
- `source` provides the citation required by data licences (BÜK: BKG attribution required)
- `generated_at` enables "last updated" display and cache-busting reasoning

**Where to store it:** Embed under a `charts` key inside `ll_metadata.json`, not as separate
files. One fetch, one file, atomic update.

```json
{
  "east-brandenburg": {
    "slug": "east-brandenburg",
    "charts": {
      "soil": { ...contract above... },
      "landuse": { ...same shape... }
    }
  }
}
```

**What the frontend needs to change:**
- `BarChart.jsx` reads `b.key` for the bar identifier; add a fallback to `b.label[lang]` for
  display (removes the i18n key dependency for pipeline-generated categories)
- `BarChart.jsx` adds a conditional "Preliminary data" badge when `data.mock === true`
- `app/src/data/chart_data.js` becomes deprecated; its role is replaced by `ll_metadata.json`
  (the file can stay as a fallback for the two non-soil/non-landuse stub layers)

---

*Research grounded in: codebase analysis (`ll_metadata.json`, `ll_display.js`, `chart_data.js`,
`sources.yaml`, `CONCERNS.md`, `ARCHITECTURE.md`), the BKG BÜK shapefile present in the repo,
and established conventions for environmental data portals and regional geodata dashboards.*
