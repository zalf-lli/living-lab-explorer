# Phase 14: Add soil yield potential (SQR) as a switchable Type/Yield potential map on the soil tab, plus an SQR-derived KPI in the KPI bar and reports - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-24
**Phase:** 14-add-soil-yield-potential-sqr-as-a-switchable-type-yield-pote
**Areas discussed:** Switcher & default mode, SQR map rendering, The SQR statistic, Report & chart reach
**Mode:** discuss (default, interactive)

---

## Todo Cross-Reference

| Option | Description | Selected |
|--------|-------------|----------|
| Leave it out | `single-copy-public-data` is repo hygiene unrelated to SQR; its own phase | ✓ |
| Fold it in | Do the `.gitignore` + CI copy-step change as part of Phase 14 | |

**User's choice:** Leave it out — recorded in CONTEXT.md `<deferred>` as reviewed-not-folded.

---

## Switcher & default mode

### Q1 — Landing mode

| Option | Description | Selected |
|--------|-------------|----------|
| Type (BÜK) — unchanged | Soil tab keeps opening on BÜK250; Yield is what you switch *to* | ✓ |
| Yield potential (SQR) | Lead with the new layer, as Phase 8 D-08 led with GDD | |

**User's choice:** Type (BÜK) — unchanged. → D-01

### Q2 — Control placement and component

| Option | Description | Selected |
|--------|-------------|----------|
| On-map, generalise PeriodSwitcher | Float over the map like the climate control; extract shared segmented control | ✓ (later retracted) |
| On-map, new soil-only component | Same placement, separate `SoilModeSwitcher.jsx` | |
| Second tab row under LayerTabs | Like `VariablePicker` — sub-tab level beneath the layer tabs | ✓ (final) |

**User's choice:** Initially selected the on-map/generalise-PeriodSwitcher option, then **reversed it
during Q3** with the free-text answer: *"Actually scratch the decision to use the switcher, to
actually be aligned with the climate tab the two soil map [options] should be in a row below the soil
tab label the same as the different climate variables are."*

**Notes:** This is the phase's one reversal and the most likely thing to be mis-restored downstream,
because the ROADMAP entry's own wording ("mirroring the climate tab's Baseline/Change control")
points at the retracted option. Flagged explicitly in CONTEXT.md `<specifics>`. → D-02

### Q3 — Shared across comparison columns

Asked as a standalone question; **answered implicitly by the Q2 reversal.** `VariablePicker` renders
inside `LayerBar`, which is rendered once above both Phase 10 comparison columns — so Phase 8 D-17's
shared-instance requirement is satisfied by placement rather than by new state plumbing. No separate
choice was needed. → D-04

### Q4 — Component reuse

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse `VariablePicker.jsx` directly | Already fully controlled; pass a two-entry array | ✓ |
| Rename it to something layer-neutral | Same reuse, renamed `SubTabRow`; touches climate imports | |
| New soil-specific component | Copy the styling into `SoilModePicker.jsx` | |

**User's choice:** Reuse directly. → D-03

### Q5 — Two dataset provenances on one tab

| Option | Description | Selected |
|--------|-------------|----------|
| Own `sources.yaml` entry, mode-aware attribution | `id: sqr1000` with its own source block, also `app_layer: soil` | ✓ |
| Nested under the `buek250` entry | Like `chelsa-climate`'s `climate.variables` sub-map | |
| One combined credit line | Extend the BÜK source block to name both BGR products | |

**User's choice:** Own entry with mode-aware attribution. → D-06, D-07

**Notes:** This is what breaks the 1:1 `app_layer` key assumption — recorded as the phase's
highest-risk hazard in CONTEXT.md `<code_context>`.

### Q6 — Does the KPI bar react to the sub-tab?

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed — same soil KPIs in both modes | Matches how the climate tab already behaves | ✓ |
| Mode-aware — swap tiles with the map | Tighter map–number coupling; new `StatPanel` behaviour | |

**User's choice:** Fixed. → D-05

---

## SQR map rendering

### Q1 — Shared or per-LL colour scale

| Option | Description | Selected |
|--------|-------------|----------|
| Shared fixed scale | One scale for all 5 LLs (Phase 8 D-09 reasoning) | ✓ |
| Per-LL quantile scale | Phase 7 D-09's BORIS approach | |
| Shared scale on observed range | Shared, but endpoints from the observed ~15–99 | |

**User's choice:** Shared fixed scale. → D-08 (endpoint choice left to Claude's discretion)

### Q2 — Ramp family

| Option | Description | Selected |
|--------|-------------|----------|
| Lime → green | `limePale → lime → limeDark → greenMid → green`; only unclaimed family | ✓ |
| Reuse BORIS teal → orange | Consistent low→high encoding, but prime cropland becomes warning-orange | |
| Orange family | Brand primary, but collides with the climate heat family | |

**User's choice:** Lime → green. → D-09

### Q3 — Unrated (non-arable) cells

| Option | Description | Selected |
|--------|-------------|----------|
| Muted grey + explicit legend entry | Reuse `BORIS_NO_DATA_STYLE` `#d8d8d2` plus a bilingual row | ✓ |
| Fully transparent | Basemap shows through; indistinguishable from a tiling failure | |
| Transparent + a legend note only | No grey fill, explanation in prose | |

**User's choice:** Muted grey + legend entry. → D-10

### Q4 — Legend bands

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed equal bands with numeric ranges | e.g. "60–75"; Phase 7 D-04's explicit-ranges rule | ✓ |
| Named quality classes | "low / moderate / high"; boundaries would be ours, not the BGR's | |
| Ranges plus names | Both; doubles legend row width, still invents boundaries | |

**User's choice:** Numeric ranges. → D-11

### Q5 — Explanation shipped with the map

| Option | Description | Selected |
|--------|-------------|----------|
| One-sentence bilingual `legendNoteKey` | Existing `MapLegend` note path, no new component | ✓ |
| Note plus a fuller info popover | Rejected by Phase 8 D-14's competing-surfaces reasoning | |

**User's choice:** One-sentence note. → D-12

### Q6 — Resampling and zoom fidelity

| Option | Description | Selected |
|--------|-------------|----------|
| Nearest resampling, cap the zoom | Preserves plateau structure of the 1:1M source; no invented edge values | ✓ |
| Bilinear, match the climate layer | Prettier, but manufactures detail the source doesn't have | |
| Nearest, no zoom cap | Exact values, blocky at high zoom | |

**User's choice:** Nearest + capped zoom. → D-13 (exact cap left to Claude's discretion)

---

## The SQR statistic

### Q1 — What the number is

| Option | Description | Selected |
|--------|-------------|----------|
| Mean over rated cells only | Area-weighted, boundary-clipped in a projected CRS | ✓ |
| Mean over the whole LL area | Unrated as zero; conflates soil quality with land use | |
| Share of area above a threshold | Legible, but the threshold would be ours | |

**User's choice:** Mean over rated cells only. → D-14

### Q2 — Tile set for the soil KPI bar

| Option | Description | Selected |
|--------|-------------|----------|
| Drop both null tiles — soil becomes 2 real tiles | Phase 8 D-18 applied verbatim | |
| Add SQR as a 4th tile, keep the dashes | Minimal blast radius; two real numbers next to two em-dashes | |
| Drop the nulls **and** add a second SQR-derived tile | Back to 3 filled tiles, all real | ✓ |

**User's choice:** Drop the nulls and add a second SQR tile. → D-15, D-16

**Notes:** The ROADMAP asks for one SQR KPI; the user chose two. Both come from the same raster, so
this stays inside the phase's data boundary rather than being scope creep.

### Q3 — What the second tile is

| Option | Description | Selected |
|--------|-------------|----------|
| Share of LL area rated as cropland | Explains the map's grey areas; honest denominator for Q1's mean | ✓ |
| Share of rated land above a threshold | Invented-boundary problem again | |
| Range within the LL (min–max) | Two numbers in one tile; outlier-sensitive | |

**User's choice:** Share of LL area rated as cropland. → D-16

### Q4 — KPI plumbing

| Option | Description | Selected |
|--------|-------------|----------|
| Own JSON file, merged in `generate_metadata.py` | Phase 05.1 D-03 / Phase 8 D-23 pattern, third application | ✓ |
| Fold into an existing computed-KPI file | Fewer files; mixes unrelated sources under one `source_host` | |

**User's choice:** Own JSON file. → D-17

---

## Report & chart reach

### Q1 — Does the report's soil section gain the yield map?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — both maps in the soil section | The PDF is the offline substitute; the climate section precedents it | ✓ |
| No — KPI only, as the roadmap states | Smallest change; reader never sees the yield map on paper | |
| Yes, but as a small inset | Likely unreadable at 250 m | |

**User's choice:** Both maps. → D-18

### Q2 — Does the chart change with the map mode?

| Option | Description | Selected |
|--------|-------------|----------|
| No — chart stays the BÜK chart | Chart belongs to the tab; zero pipeline work | |
| Yes — Yield mode gets an SQR distribution chart | New compute script, new chart JSON, mode-aware loading | |

**User's choice (free text):** *"the reports now add charts as legends to most maps, in this sense
the BUK chart stays as the map legend and the SQR map gets it's own chart as legend."*

**Notes:** This reframes the question. In the report the chart **is** the map legend
(`legend_bars.R`, Phase 12), and that module's stated rule — "no statistic is recomputed in R"
(D-06/T-12-25) — means the SQR bar legend can only be drawn from a committed chart JSON. So the SQR
chart script became mandatory rather than optional. Reflected back to the user before continuing.
→ D-19

### Q3 — App-side chart behaviour (follow-up to the reframing)

| Option | Description | Selected |
|--------|-------------|----------|
| Swap it — Yield mode shows the SQR band chart | Chart follows the map, consistent with the report | ✓ |
| Keep the BÜK chart in both modes | SQR chart JSON built only to feed the report | |
| Show both charts in both modes | No mode-aware wiring, but mismatched chart/map pairings | |

**User's choice:** Swap it. → D-20

### Q4 — Does "Not rated" get a bar?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — include it as a grey bar | Legend must explain every colour on the map; shares sum to the whole LL | ✓ |
| No — score bands only, shares of rated land | Cleaner distribution, but the grey has no printed legend row | |

**User's choice:** Yes, grey bar. → D-21

**Notes:** This creates two different denominators (chart over whole LL, mean over rated cells).
Recorded as an intentional difference and a named hazard in CONTEXT.md.

---

## Claude's Discretion

Recorded in CONTEXT.md `<decisions>` → "Claude's Discretion". Summary: legend band count; exact max
zoom cap; whether the shared scale uses nominal 0–102 or the observed range; KPI rounding and tile
shape; how the soil `LAYERS` entry expresses two asset kinds; PMTiles file naming; whether the SQR
build reuses existing raster machinery; whether the source GeoTIFF stays committed; report soil
section layout.

## Deferred Ideas

- `single-copy-public-data` todo — reviewed, not folded
- Named SQR quality classes in the legend
- "Share of cropland above threshold X" as a KPI
- Within-LL min–max range on the mean-SQR tile
- Nutrient surplus from a non-Destatis source (UBA / LAWA)
- Mode-aware KPI bar
- A fuller SQR methodology popover
