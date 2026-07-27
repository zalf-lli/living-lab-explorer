# Phase 7: Add BORIS land value maps as spatial layer for socio-economic tab - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-27
**Phase:** 07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi
**Areas discussed:** Value visualization style, Land-use scope (which zones to show), Cross-LL comparability, Two-state data harmonization & tooltip detail

---

## Value visualization style

| Option | Description | Selected |
|--------|-------------|----------|
| Choropleth by €/m² value | Sequential color scale driven by standard land value | ✓ |
| Categorical by usage type | Fixed color per land-use code, like soil/protected-areas | |
| Choropleth with usage-type as secondary filter/toggle | Value color + optional usage-type filter UI | |

**User's choice:** Choropleth by €/m² value

| Option | Description | Selected |
|--------|-------------|----------|
| Quantile bins (5-6 classes) | Equal number of zones per bucket | ✓ |
| Equal-interval bins | Fixed € ranges per bucket | |
| Continuous gradient (no discrete bins) | Smooth interpolation, no legend buckets | |

**User's choice:** Quantile bins (5-6 classes)

| Option | Description | Selected |
|--------|-------------|----------|
| New sequential ramp from theme.js | Derived from existing brand colors | ✓ |
| Standard sequential palette (ColorBrewer etc.) | External cartographic palette | |

**User's choice:** New sequential ramp (e.g. teal/orange from theme.js)

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — show € ranges per swatch | e.g. "€2–4/m²" per legend entry | ✓ |
| No — gradient bar with min/max labels only | Simpler, less precise | |

**User's choice:** Yes — show € ranges per swatch

**Notes:** None additional; user moved to next area after 4 questions.

---

## Land-use scope (which zones to show)

| Option | Description | Selected |
|--------|-------------|----------|
| Agricultural zones only | Filter to farmland | |
| Agricultural + forest (rural land only) | Excludes residential/commercial | |
| All zones (agricultural, residential, commercial, forest, etc.) | Complete BORIS coverage | ✓ |

**User's choice:** All zones (agricultural, residential, commercial, forest, etc.)

| Option | Description | Selected |
|--------|-------------|----------|
| No — value color only, usage type in tooltip | Single visual channel | ✓ |
| Yes — secondary cue (hatching/border) per usage type | Two visual channels | |

**User's choice:** No — value color only, usage type in tooltip

| Option | Description | Selected |
|--------|-------------|----------|
| Across all zones together (single scale) | One shared quantile scale | ✓ |
| Per usage-type scale | Independent scale per land-use category | |

**User's choice:** Across all zones together (single scale)

| Option | Description | Selected |
|--------|-------------|----------|
| Include development-expectation land (Bauerwartungsland) as its own zone | Full fidelity to WFS data | ✓ |
| Exclude development-expectation land specifically | Remove speculative outlier category | |

**User's choice:** Include it as its own zone (with all other zones)

| Option | Description | Selected |
|--------|-------------|----------|
| Skip zones with no current value | Only render active-value zones | |
| Show them in a distinct "no data" style | Neutral/hatched fill, preserves geographic completeness | ✓ |

**User's choice:** Show them in a distinct "no data" style

**Notes:** User explicitly asked to continue discussing this area twice (5 total questions) before moving on.

---

## Cross-LL comparability

| Option | Description | Selected |
|--------|-------------|----------|
| Shared scale across all 5 LLs | One combined quantile scale, cross-region comparable | |
| Independent scale per LL | Each LL gets its own quantile buckets | ✓ |

**User's choice:** Independent scale per LL

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — add a small note under the legend | Bilingual note that scale is relative to this LL only | ✓ |
| No — rely on € range labels to make it self-evident | No extra note | |

**User's choice:** Yes — add a small note under the legend

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed 5-6 buckets for every LL | Consistent legend shape across all LL pages | ✓ |
| Adapt bucket count to zone count | Fewer buckets for LLs with fewer zones | |

**User's choice:** Fixed 5-6 buckets for every LL

**Notes:** User continued discussion twice before moving to the next area.

---

## Two-state data harmonization & tooltip detail

| Option | Description | Selected |
|--------|-------------|----------|
| Full bilingual semantic contract (like Phase 2.2 soil) | Map both states' raw codes into one shared EN/DE vocabulary | ✓ |
| Minimal harmonization for MVP (raw codes + lookup) | Keep native codes, translate labels only, no full unification | |

**User's choice:** Full bilingual semantic contract (like Phase 2.2 soil)

| Option | Description | Selected |
|--------|-------------|----------|
| Value + usage type + valuation date | 3-row tooltip | ✓ |
| Value + usage type + valuation date + zone reference code | 4-row tooltip with technical ID | |

**User's choice:** Value + usage type + valuation date

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — show a vintage/mock-style badge on the tab | Page-level "as of [date]" badge | |
| No — date only in the per-zone tooltip | Tooltip-only | ✓ |

**User's choice:** No — date only in the per-zone tooltip

**Notes:** User confirmed ready for context after this area.

---

## Claude's Discretion

- Exact hex values for the sequential color ramp
- Client-side vs. pipeline-precomputed quantile-bin computation
- "No data" style specifics
- Tooltip layout/row order beyond the three required fields
- WFS query parameters, pagination, and per-LL clip/filter mechanics
- Whether BORIS reuses the exact hardcoded `layer === 'economic'` rendering path or generalizes the existing vector-rendering branch in `LLMap/index.jsx`

## Deferred Ideas

- Per-usage-type quantile scaling (separate scale per land-use category)
- Page-level vintage/"as of" badge for the Bodenrichtwert reference date
- Secondary visual channel (hatching/border) for usage type
- Adaptive bucket count per LL's zone density
