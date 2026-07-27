# Phase 7: Add BORIS land value maps as spatial layer for socio-economic tab - Context

**Gathered:** 2026-07-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Fill the currently-empty `economic` tab placeholder (`type: 'placeholder'` in `app/src/data/layers.js`)
with a BORIS (Bodenrichtwertinformationssystem / standard land value) vector map. Data is acquired via
live WFS queries against the Brandenburg (BORIS-BB) and Hessen (BORIS-HE) state geoportals at pipeline
build time — all 5 Living Labs sit entirely within these two states, so no third source is needed. The
`economic` tab keeps its existing `StatPanel` (Destatis KPIs) rendered alongside the new map, unchanged.
No new tab is added — this fills an existing slot, following the same "placeholder → real layer" pattern
Phase 6 used for `landscape`.

</domain>

<decisions>
## Implementation Decisions

### Value Visualization Style
- **D-01:** Zones are colored by a choropleth of the standard land value (€/m²), not by usage-type category. This is a new visual pattern for the app — soil and protected-areas use flat categorical legends; this is the first continuous-value choropleth.
- **D-02:** Binning is quantile-based (5-6 classes), computed across all zones together (not split by usage type). Fixed at 5-6 buckets for every Living Lab regardless of how many zones that LL has, for a consistent legend shape across all 5 LL pages.
- **D-03:** Color ramp is a new sequential ramp derived from existing `theme.js` tokens (e.g. the teal family `C.tealBg` → `C.tealLight`, or teal→orange), not an external cartographic palette like ColorBrewer. Follows Phase 6's D-10/D-11 "minimize new colors" precedent.
- **D-04:** The legend shows the exact €/m² range per bucket (e.g. "€2–4/m²"), not just gradient endpoints — extends the existing `value/en/de/color` legend entry shape with a formatted range as the label.

### Land-Use Scope
- **D-05:** Show ALL BORIS zones (agricultural, residential, commercial, forest, etc.) — not filtered to agricultural-only. Quantile binning (D-02) is relied on to keep the map visually varied despite the wide value range this introduces.
- **D-06:** Usage type is NOT shown as a second visual channel on the map (no hatching/border-per-type) — fill color encodes value only. Usage type is tooltip-only information.
- **D-07:** Speculative development-expectation land (Bauerwartungsland) is included as its own zone alongside everything else — no special exclusion.
- **D-08:** Zones with no current/live Bodenrichtwert (only historical or null values) ARE still shown, rendered in a distinct "no data" style (neutral/hatched fill) rather than being dropped from the collection — preserves geographic completeness, avoids visible gaps being misread as zero value.

### Cross-LL Comparability
- **D-09:** Color scale is computed independently per Living Lab (each LL's own quantile buckets from its own zones) — NOT a shared scale across all 5 LLs. Same color can mean different €/m² in different LLs.
- **D-10:** Because the scale isn't cross-LL comparable, add a small bilingual note under the legend (reusing the existing `legendNoteKey` pattern from soil/protected-areas) stating the scale is relative to that Living Lab only.

### Two-State Data Harmonization & Tooltip
- **D-11:** Build a full bilingual semantic contract for BORIS usage-type codes — map both Brandenburg's and Hessen's raw WFS usage codes into one shared canonical EN/DE vocabulary before writing per-LL GeoJSON, mirroring the Phase 2.2 BÜK soil semantic-contract precedent. Do not ship two different raw code vocabularies to the frontend.
- **D-12:** Tooltip shows: value (€/m²), usage type (bilingual), and valuation date (Stichtag). No separate zone-reference-code row.
- **D-13:** No page-level "as of [date]" vintage badge near the map — the valuation date lives only in the per-zone tooltip, not surfaced elsewhere on the tab.

### Claude's Discretion
- Exact hex values for the sequential color ramp (derive from `theme.js`, D-03 sets the family)
- Whether quantile-bin computation happens client-side (from the per-LL fetched GeoJSON, like `buildSoilLegendEntries`) or is precomputed in the pipeline and embedded in GeoJSON properties
- "No data" style specifics (exact gray/hatch treatment)
- Tooltip layout/row order beyond the three required fields (D-12)
- WFS query parameters, pagination, and per-LL clip/filter mechanics
- Whether BORIS is wired as a `type: 'vector'` layer following soil's exact hardcoded `layer === 'economic'` rendering path in `LLMap/index.jsx`, or as a small generalization of the existing vector-rendering branch — implementation detail, not a user-facing decision

</decisions>

<specifics>
## Specific Ideas

- The point of this layer is showing "where is land expensive/cheap" as a socio-economic signal, not primarily a farmland-value tool — hence showing all zone types rather than agricultural-only (D-05).
- Per-LL independent scaling (D-09) was chosen deliberately over a shared scale: the priority is visual contrast and legibility within each Living Lab's own page, not cross-region ranking.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & Project Constraints
- `.planning/ROADMAP.md` Phase 7 entry — "Add BORIS land value maps as spatial layer for socio-economic tab (WFS from Brandenburg and Hessen geoportals)"
- `CLAUDE.md` — Static file pipeline contract: pipeline fetches WFS at build time and commits output files; no runtime API coupling. `make_valid()` must be called after `gpd.read_file()`; CRS must be aligned before clipping; assert `len(clipped) > 0`.

### Prior Phase Precedents (closest analogs)
- `.planning/phases/05-add-protected-areas-as-toggleable-layer-on-landscape-map/05-CONTEXT.md` — D-04 established the "live WFS query at pipeline runtime, not manual download" pattern this phase reuses for BORIS-BB/BORIS-HE.
- `.planning/phases/06-add-land-cover-map/06-CONTEXT.md` — D-02 established the "fill an existing placeholder tab" pattern (`landscape`) that this phase repeats for `economic`. D-10/D-11 established "minimize new colors, derive from theme.js" that D-03 here follows.
- Phase 2.2 (Soil Semantics & Translation) — bilingual semantic-contract precedent referenced by D-11. Locate its CONTEXT.md/plans under `.planning/phases/` (soil semantics phase) for the exact mapping-table pattern to replicate for BORIS usage codes.

### Frontend Architecture
- `app/src/data/layers.js` — `LAYERS` array; `economic` entry is currently `{ id: 'economic', type: 'placeholder', pmtilesUrl: null, legend: null, available: true }` (line 39) and must become a `type: 'vector'` entry with `geojsonPathPattern` and `legend`, following the `soil` entry's shape (lines 30-38).
- `app/src/components/LLMap/index.jsx` — Vector-layer rendering is currently hardcoded per layer id (`layer === 'soil'` branches at lines 698-702, 779-786, 793-794, 806). A BORIS choropleth needs an analogous `layer === 'economic'` (or generalized) data-fetch, style function, and legend-building path. `getSoilStyle`/`buildSoilLegendEntries` (lines 179-250) are the closest structural analogs for value-driven style/legend functions, though BORIS needs continuous quantile logic instead of categorical hashing.
- `app/src/components/StatPanel.jsx` / `app/src/pages/LLDetail.jsx` (lines 163, 196, 287, 306) — `StatPanel` renders per-tab KPIs independently of the map component; the existing `economic` StatPanel is unaffected by this phase and continues to render alongside the new map.
- `app/src/theme.js` — Color tokens available for the D-03 sequential ramp: `teal` family (`tealBg` `#00413f` → `teal` `#005754` → `tealMid` `#008581` → `tealLight` `#00b3ad`) and `orange` family (`orangeDeep` → `orangeDark` → `orange` → `orangeGhost`).

### Pipeline
- `data-pipeline/sources/sources.yaml` — `kind: vector` entry pattern (see BÜK/protected-areas entries) to replicate for a new BORIS layer with two state-specific WFS sources.
- `data-pipeline/python/build_vector.py` — Existing vector pipeline script (CRS alignment, `make_valid()`, per-LL clip) — reference for a new BORIS fetch/harmonization script; will need per-state WFS query logic (Brandenburg BORIS-BB, Hessen BORIS-HE) feeding into one shared harmonization step (D-11).
- `data/variables_catalogue.xlsx` — Referenced in Phase 5 context as the guide for WFS endpoint selection; check whether it already has entries for BORIS-BB/BORIS-HE endpoints or licensing notes.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `LLMap.jsx`'s soil-layer branch (data fetch via `useGeoJSON`, `GeoJSON` component with a `style` function and `onEachFeature` tooltip binder) is the direct structural template for the BORIS choropleth — swap categorical hash-coloring for quantile-bucket coloring.
- `MapLegend.jsx` already renders `{value, en, de, color}` entries generically — the choropleth legend can reuse it as long as each bucket is represented as one such entry with a formatted €-range label (D-04).
- Per-LL split GeoJSON file pattern (`data/geojson/{layer}-{slug}.geojson`) means each fetched collection already contains only that LL's zones — supports computing per-LL quantiles client-side directly from the fetched collection (like `buildSoilLegendEntries` does), without needing a separate cross-LL data pass.

### Established Patterns
- Tabs (not overlays) lazy-load their data only when active: `soilUrl` in `LLMap.jsx` is `null` unless `layer === 'soil'`. The same lazy pattern applies naturally once `economic` gets a real `useMemo`-gated URL.
- `sync.py` copies pipeline output into `app/public/data/...` — a new BORIS GeoJSON output needs a corresponding copy step, following soil/protected-areas' existing copy wiring.

### Integration Points
- `layers.js`: `economic` entry converted from placeholder to `type: 'vector'`.
- `LLMap/index.jsx`: new data-fetch memo, style function (quantile-based), legend-builder function, and tooltip binder for `economic`/BORIS, following the soil branch's shape.
- `sources.yaml` + new pipeline script: register BORIS as a two-source (BB + HE) vector layer with a harmonization step producing one canonical bilingual schema.
- `sync.py`: add copy step for the new per-LL BORIS GeoJSON outputs.
- i18n: new `legend.economic.*` (or `legend.boris.*`) keys for usage-type labels and the cross-LL-scale note (D-10), plus tooltip labels (D-12).

</code_context>

<deferred>
## Deferred Ideas

- Per-usage-type quantile scaling (separate scale per land-use category) — rejected in favor of a single combined scale (D-02); could revisit if agricultural zones end up visually flattened into one bucket in practice.
- Page-level vintage/"as of" badge for the Bodenrichtwert reference date — rejected in favor of tooltip-only date (D-13); could add later if users find the currency of the data unclear.
- Secondary visual channel for usage type (hatching/border patterns) — rejected for MVP simplicity (D-06); revisit if user feedback suggests value-only coloring is confusing when zones of very different uses look similar in color.
- Adaptive bucket count per LL's zone density — rejected in favor of fixed 5-6 buckets everywhere (locked under Cross-LL comparability) for legend consistency.

</deferred>

---

*Phase: 07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi*
*Context gathered: 2026-07-27*
