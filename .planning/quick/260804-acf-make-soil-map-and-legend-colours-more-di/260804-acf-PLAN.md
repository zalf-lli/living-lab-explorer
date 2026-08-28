---
phase: quick-260804-acf
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - app/src/data/soil_legend.js
  - app/scripts/check_soil_palette.mjs
  - app/package.json
  - app/src/components/LLMap/index.jsx
  - app/src/data/layers.js
autonomous: false
requirements: [TODO-01]

must_haves:
  truths:
    - "Every soil class painted on the map in a given Living Lab has a colour no other class in that Living Lab uses"
    - "No two swatches in the soil legend look alike — the closest pair is >= 20 CIELAB units apart in all five Living Labs"
    - "The map fill and the legend swatch for the same soil class are still the identical hex value"
    - "Soil classes are separated by lightness as well as hue, so the map stays readable in greyscale and under red/green colour-vision deficiency"
    - "npm run lint and npm run build stay clean; no new dependency is added"
  artifacts:
    - path: "app/src/data/soil_legend.js"
      provides: "Single source of truth for soil class colours: SOIL_GROUP_COLORS, SOIL_FALLBACK_PALETTE, water/special fills and strokes, getSoilColor()"
      exports: ["SOIL_GROUP_COLORS", "SOIL_FALLBACK_PALETTE", "SOIL_WATER_FILL", "SOIL_WATER_STROKE", "SOIL_SPECIAL_FILL", "SOIL_SPECIAL_STROKE", "SOIL_UNIT_STROKE", "getSoilColor"]
    - path: "app/scripts/check_soil_palette.mjs"
      provides: "Automated distinctness gate over the palette and all five committed buek250 GeoJSON fixtures"
    - path: "app/src/components/LLMap/index.jsx"
      provides: "Map fill + dynamic legend, now reading colours from soil_legend.js instead of a local 8-brown array"
      contains: "from '../../data/soil_legend.js'"
    - path: "app/src/data/layers.js"
      provides: "Static pre-load SOIL_LEGEND fallback, colours derived from soil_legend.js"
  key_links:
    - from: "app/src/components/LLMap/index.jsx"
      to: "app/src/data/soil_legend.js"
      via: "import of getSoilColor + style constants"
      pattern: "getSoilColor|SOIL_WATER_FILL|SOIL_SPECIAL_FILL"
    - from: "app/src/data/layers.js"
      to: "app/src/data/soil_legend.js"
      via: "SOIL_GROUP_COLORS lookup inside SOIL_LEGEND"
      pattern: "SOIL_GROUP_COLORS"
    - from: "app/scripts/check_soil_palette.mjs"
      to: "app/public/data/geojson/buek250-*.geojson"
      via: "fs read of committed fixtures"
      pattern: "buek250"
---

<objective>
The soil map paints every soil class from an 8-entry palette of near-identical browns
(`#b88752`, `#c29b68`, `#a87445`, `#d0b385`, `#8f6136`, `#c98b5e`, `#aa7c57`, `#bfa07a`),
assigned by hashing the class key. Against the 16 distinct soil group keys in the committed
BÜK250 fixtures this produces **exact duplicates**, not merely similar colours:

- `hessian-low-mountain`: `brown-soils`, `stagnic-soils` and `alluvial-soils` all render `#b88752` — 3 of the 5 legend swatches are the same colour.
- `east-brandenburg` and `havelland`: `fens` and `ah-c-soils` both render `#d0b385`.
- `podzols` and `pelosols` both render `#a87445` everywhere.
- Three of the eight palette entries (`#c29b68`, `#8f6136`, `#c98b5e`) are never assigned at all.

Replace the hash-into-8-browns scheme with an explicit, stable class→colour map spanning a wide
lightness range and a full hue circle, plus a small distinct fallback tier for unnamed
anthropogenic units. Closes backlog item TODO-01 (`.planning/STATE.md`), the "improve colour
divergence in soil layer legend" half.

Purpose: a reader must be able to tell two soil classes apart at map zoom and match a polygon to
its legend swatch without guessing.
Output: one new palette module, one new automated distinctness gate, and two rewired consumers.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/STATE.md
@CLAUDE.md

@app/src/components/LLMap/index.jsx
@app/src/data/layers.js
@app/src/components/MapLegend.jsx
</context>

<investigation_findings>
Verified against the working tree on branch `data-pipeline-development` (2026-08-04):

1. **Colours are hand-authored app-side, NOT codegen'd.** `data-pipeline/sync.py` generates only
   `app/src/data/land_cover_legend.js` (`generate_land_cover_legend`, line 66) and
   `app/src/data/climate_legend.js` (`generate_climate_legend`, line 178). Neither
   `app/src/components/LLMap/index.jsx` nor `app/src/data/layers.js` is ever written by the
   pipeline, and no Python file contains any soil hex. **`python sync.py` will not revert this
   change.** Do not edit `land_cover_legend.js` or `climate_legend.js` — they are generated and
   belong to a different layer, even though they happen to reuse the hexes `#88bfd9`, `#4f89a3`,
   `#d0b385` and `#c6d2d5`.

2. **Map and legend already read the same colour source** — both go through `getSoilColor()` in
   `app/src/components/LLMap/index.jsx` (line 216 via `getSoilStyle`, line 262 via
   `buildSoilLegendEntries`). Keeping them in sync is a matter of not breaking that; this plan
   strengthens it by moving the palette into one importable module.

3. **A second, static colour source exists**: `SOIL_LEGEND` in `app/src/data/layers.js:10-20`
   (4 entries). `MapLegend.jsx:9` falls back to it (`cfg?.legend`) whenever `soilLegendEntries` is
   null — i.e. while the GeoJSON is still loading or after a fetch error. Its hexes must be kept in
   sync with the new palette or the legend will flip colours mid-load.

4. **Class count.** 16 distinct group keys exist across the five committed
   `app/public/data/geojson/buek250-*.geojson` fixtures; per Living Lab there are 7–12 soil classes
   plus `water_area` and `special_area`. Twelve keys are stable, semantically named groups; four are
   long free-text-derived anthropogenic slugs. Feature counts across all five fixtures:

   | key | EN label | DE label | features | current colour |
   |-----|----------|----------|----------|----------------|
   | `brown-soils` | Brown soils | Braunerden | 165 | `#b88752` |
   | `gley-soils` | Gley soils | Gleye | 78 | `#bfa07a` |
   | `luvisols` | Luvisols | Lessivés | 66 | `#aa7c57` |
   | `ah-c-soils` | Ah/C soils | Ah/C-Böden | 53 | `#d0b385` |
   | `stagnic-soils` | Stagnic soils | Stauwasserböden | 36 | `#b88752` (dup) |
   | `fens` | Fens | Niedermoore | 35 | `#d0b385` (dup) |
   | `alluvial-soils` | Alluvial soils | Auenböden | 16 | `#b88752` (dup) |
   | `initial-soils` | Initial soils | Rohböden | 10 | `#b88752` (dup) |
   | `sealed-surfaces` | Sealed surfaces | versiegelte Flächen | 10 | `#b88752` (dup) |
   | `podzols` | Podzols | Podsole | 6 | `#a87445` |
   | `pelosols` | Pelosols | Pelosole | 3 | `#a87445` (dup) |
   | `raised-bogs` | Raised bogs | Hochmoore | 2 | `#b88752` (dup) |
   | 4 long anthropogenic slugs | (Kippsubstrate / Stadtkernbereiche / Abgrabungsflächen / Bergbau-Tagebau) | | 7 total | 3 of 4 collide |

5. **The legend shows at most 7 swatches**: the 5 most frequent soil groups of that Living Lab
   (`buildSoilLegendEntries`, `.slice(0, 5)`) plus `water-area` and `special-area` when present.
   All five fixtures currently hit that 7-swatch maximum.

6. **Nothing else consumes these hexes.** `grep` over `app/src`, `data`, `data-pipeline` (excluding
   the build output in `app/dist/`) finds the soil hexes only at `LLMap/index.jsx:53,55,57,61,63,232`
   and `layers.js:11,12,13,18`. No Python test asserts any soil colour. The soil BarChart deliberately
   uses `CHART_RANK_COLORS`, not this palette (Phase 11, `legendMatchesChartCategories` is false for
   soil because the on-map legend is per-Living-Lab dynamic) — **leave the chart alone**;
   it is out of scope.

7. `LAYER_COLORS.soil` in `layers.js:203-209` is dead for the soil layer (`MapLegend` only reaches
   it when `cfg.legend` is null, and soil's is not). Out of scope — do not touch.
</investigation_findings>

<palette_spec>
## New palette — exact values

Design rationale: every class is separated on **both** hue and lightness. Sorted by CIE L*, the
twelve named soil groups plus water and special areas step 24 → 36 → 37 → 39 → 45 → 46 → 58 → 60 →
60 → 68 → 71 → 76 → 81 → 89, so classes that share a lightness band (e.g. `alluvial-soils` L*58,
`stagnic-soils` L*60, `podzols` L*60) sit far apart in hue instead. Hues are drawn from an
Okabe-Ito-style colour-vision-deficiency-safe set (orange / blue / bluish-green / violet / vermillion)
rather than a red-green axis, tinted toward earth tones so the map still reads as a soil map.
Water-influenced soils (`gley-soils`, `stagnic-soils`) are deliberately dark and saturated so they do
not collide with the pale blue reserved for actual water polygons.

### Tier 1 — `SOIL_GROUP_COLORS` (12 stable named groups)

| key | old (effective) | **new** | L* | description |
|-----|-----------------|---------|-----|-------------|
| `brown-soils` | `#b88752` | `#8C4A16` | 38.8 | dark umber brown |
| `luvisols` | `#aa7c57` | `#E69F00` | 70.6 | amber |
| `ah-c-soils` | `#d0b385` | `#EFE0A2` | 89.1 | pale straw |
| `gley-soils` | `#bfa07a` | `#0072B2` | 46.0 | deep azure blue |
| `stagnic-soils` | `#b88752` | `#A97FCB` | 59.8 | violet |
| `fens` | `#d0b385` | `#41382B` | 24.1 | near-black peat brown |
| `alluvial-soils` | `#b88752` | `#009E73` | 57.7 | bluish green |
| `initial-soils` | `#b88752` | `#C9A063` | 68.4 | ochre |
| `podzols` | `#a87445` | `#8C8FA8` | 59.9 | ash slate-lilac |
| `pelosols` | `#a87445` | `#B5453C` | 44.8 | brick red |
| `raised-bogs` | `#b88752` | `#6B4B7A` | 37.0 | dark plum |
| `sealed-surfaces` | `#b88752` | `#4E545C` | 35.5 | dark slate grey |

### Tier 2 — `SOIL_FALLBACK_PALETTE` (unnamed / future keys, order is significant)

Index order matters: it is what the hash indexes into. Keep exactly this order.

| index | **hex** | L* | description |
|-------|---------|-----|-------------|
| 0 | `#6E4B4B` | 37.2 | dark brick brown |
| 1 | `#7F9E5C` | 60.4 | moss green |
| 2 | `#8E6E4E` | 48.8 | mid taupe |
| 3 | `#D4A6C8` | 72.6 | dusty pink |
| 4 | `#4F6B4A` | 42.3 | dark sage |

### Tier 3 — non-soil feature kinds and strokes

| constant | old | **new** | note |
|----------|-----|---------|------|
| `SOIL_WATER_FILL` | `#88bfd9` | `#88BFD9` | unchanged value, uppercased for consistency |
| `SOIL_WATER_STROKE` | `#4f89a3` | `#4F89A3` | unchanged value, uppercased |
| `SOIL_SPECIAL_FILL` | `#c6d2d5` | `#C9C9C9` | **changed** — the old pale blue-grey read as water; a neutral grey separates it |
| `SOIL_SPECIAL_STROKE` | `#768a8f` | `#8A8A8A` | **changed** — follows the fill to neutral |
| `SOIL_UNIT_STROKE` | `#6e4d31` | `#3F3F3F` | **changed** — a brown hairline looked wrong around the new blue/violet/green fills |

### Measured result (computed against the five committed fixtures)

| Living Lab | painted classes | unique colours | min ΔE76 (whole map) | legend swatches | min ΔE76 (legend) |
|------------|-----------------|----------------|----------------------|-----------------|-------------------|
| east-brandenburg | 14 | **14** | 18.0 | 7 | **22.8** |
| havelland | 13 | **13** | 19.0 | 7 | **22.8** |
| hessian-low-mountain | 12 | **12** | 22.0 | 7 | **22.8** |
| north-hessian-loess | 12 | **12** | 22.8 | 7 | **22.8** |
| rheingau | 9 | **9** | 22.0 | 7 | **22.8** |

Today the same table reads 3–4 unique colours per 5-swatch legend with a min ΔE of 0.
</palette_spec>

<tasks>

<task type="auto">
  <name>Task 1: Create the soil palette module and its automated distinctness gate</name>
  <files>app/src/data/soil_legend.js, app/scripts/check_soil_palette.mjs, app/package.json</files>
  <action>
Create `app/src/data/soil_legend.js` as a pure, dependency-free ES module (no React, no Leaflet
imports — it must be importable by plain `node`, following the `app/src/lib/chartSeries.js`
precedent from Phase 11). It exports, using the exact hex values from the `<palette_spec>` tables
above:

- `SOIL_GROUP_COLORS` — a frozen plain object mapping the 12 Tier-1 keys to their new hex strings.
- `SOIL_FALLBACK_PALETTE` — a frozen 5-element array in exactly the Tier-2 index order shown.
- `SOIL_WATER_FILL`, `SOIL_WATER_STROKE`, `SOIL_SPECIAL_FILL`, `SOIL_SPECIAL_STROKE`,
  `SOIL_UNIT_STROKE` — the Tier-3 constants.
- `getSoilColor(groupKey)` — returns `SOIL_GROUP_COLORS[groupKey]` when the key is a known named
  group, otherwise indexes `SOIL_FALLBACK_PALETTE` by an FNV-1a hash of the key. Implement FNV-1a
  with offset basis `0x811c9dc5`, prime multiply via `Math.imul(h, 0x01000193)`, `>>> 0` after each
  step and on the final result, XOR-ing `charCodeAt(i)` per character. This replaces the current
  `hashSoilKey` (a `acc * 31 + charCode` reduce seeded at 7), which distributes so poorly across
  these long slug keys that three of the four unnamed keys land on the same bucket. Use an own-property
  lookup (`Object.prototype.hasOwnProperty.call` or a `Map`) so a key like `constructor` cannot
  resolve to a prototype member.

Add a file-top comment stating that this module is the single source of truth for soil colours, that
both the map fill and the legend swatches must resolve through it, and that it is hand-authored —
`data-pipeline/sync.py` does not generate it (unlike its siblings `land_cover_legend.js` and
`climate_legend.js`). Do not write any of the retired hex codes into comments — a grep gate in
Task 2 asserts they are gone from `app/src`.

Create `app/scripts/check_soil_palette.mjs`, a node script (no dependencies) that imports
`../src/data/soil_legend.js` and fails with a non-zero exit and a descriptive message if any of:

1. `SOIL_GROUP_COLORS` does not have exactly 12 entries, or `SOIL_FALLBACK_PALETTE` is not 5 long.
2. Any hex appears twice across `SOIL_GROUP_COLORS` + `SOIL_FALLBACK_PALETTE` + `SOIL_WATER_FILL` + `SOIL_SPECIAL_FILL`.
3. The minimum CIELAB ΔE76 across every pair of those same colours is below `15`. Implement sRGB →
   linear → XYZ (D65) → L*a*b* inline; do not add a colour library.
4. For any of the five `app/public/data/geojson/buek250-*.geojson` fixtures, two distinct classes
   painted in that Living Lab resolve to the same colour. Derive each feature's class the same way
   `LLMap` does: `water_area` and `special_area` feature kinds map to the water/special fills,
   everything else to `getSoilColor(props.soil_group_key || props.parent_material_code ||
   props.SYM_NR || props.GEN_ID || 'soil-unit')`.
5. For any fixture, the simulated legend set — the 5 most frequent soil classes plus water and
   special when present, mirroring `buildSoilLegendEntries` — has a minimum pairwise ΔE76 below `20`.

On success it prints one line per Living Lab with class count, unique-colour count and both minimum
ΔE figures, then `OK`. Locate it under `app/scripts/` (a new directory) so it sits beside the app it
checks, mirroring `data-pipeline/tests/check_color_breaks.py`.

Register it in `app/package.json` under `scripts` as `"check:soil-palette": "node scripts/check_soil_palette.mjs"`,
placed after `"lint"`. Add no dependencies.
  </action>
  <verify>
    <automated>cd app && npm run check:soil-palette</automated>
  </verify>
  <done>`npm run check:soil-palette` exits 0 and reports, for each of the five Living Labs, unique-colour count equal to class count, whole-map min ΔE ≥ 15 and legend min ΔE ≥ 20. `app/src/data/soil_legend.js` imports nothing.</done>
</task>

<task type="auto">
  <name>Task 2: Rewire the map and both legend sources onto the new palette</name>
  <files>app/src/components/LLMap/index.jsx, app/src/data/layers.js</files>
  <action>
In `app/src/components/LLMap/index.jsx`:

- Delete the `SOIL_PALETTE` array (line 53), the `hashSoilKey` function (lines 203-207) and the local
  `getSoilColor` (lines 215-217). Import `getSoilColor`, `SOIL_WATER_FILL`, `SOIL_WATER_STROKE`,
  `SOIL_SPECIAL_FILL`, `SOIL_SPECIAL_STROKE` and `SOIL_UNIT_STROKE` from `../../data/soil_legend.js`
  instead. Every existing call site (`getSoilStyle` line 230, `buildSoilLegendEntries` line 262)
  keeps working unchanged because the imported name matches.
- Rewrite `SOIL_SPECIAL_STYLE` (lines 54-59) and `SOIL_STRUCTURAL_STYLE` (lines 60-65) so their
  `color` and `fillColor` reference the imported constants rather than inline hexes. Keep `weight`
  and `fillOpacity` exactly as they are (0.8/0.7 and 0.7/0.65) — this change is colour-only.
- In `getSoilStyle` (line 232), replace the hardcoded `'#6e4d31'` stroke with `SOIL_UNIT_STROKE`.
  Keep `weight: 0.6` and `fillOpacity: 0.7` unchanged.
- Leave `getSemanticSoilKey` and `buildSoilLegendEntries` logic untouched — the class-key derivation
  and the top-5 selection are correct as they stand.

In `app/src/data/layers.js`:

- Import `SOIL_GROUP_COLORS` and `SOIL_WATER_FILL` from `./soil_legend.js`.
- Rewrite the four `SOIL_LEGEND` entries (lines 10-20) so their `color` fields read
  `SOIL_GROUP_COLORS['brown-soils']`, `SOIL_GROUP_COLORS['luvisols']`,
  `SOIL_GROUP_COLORS['gley-soils']` and `SOIL_WATER_FILL` respectively. No literal hex may remain in
  this array — it is the pre-load fallback legend and drifting from the dynamic legend is exactly the
  bug this task removes.
- While editing those lines, repair two mojibaked German labels that are wrong against the data:
  `'Lessives'` → `'Lessivés'` and `'Gewaesser / Sonderflaechen'` → `'Gewässer / Sonderflächen'`.
  The GeoJSON fixtures carry `Lessivés`. Leave the English labels as they are.
- Do not touch `LAYER_COLORS.soil` (lines 203-209) or the `legendMatchesChartCategories` handling —
  both are out of scope per the investigation findings.

Then run the gates. The retired-hex grep must find nothing in the two rewired files.
  </action>
  <verify>
    <automated>cd app && test "$(grep -io 'b88752\|c29b68\|a87445\|d0b385\|8f6136\|c98b5e\|aa7c57\|bfa07a\|6e4d31\|c6d2d5\|768a8f' src/components/LLMap/index.jsx src/data/layers.js | wc -l)" = "0" && grep -q "soil_legend.js" src/components/LLMap/index.jsx && grep -q "soil_legend.js" src/data/layers.js && npm run check:soil-palette && npm run lint && npm run build</automated>
  </verify>
  <done>Zero retired soil hexes remain in `LLMap/index.jsx` and `layers.js`; both files import from `soil_legend.js`; `npm run check:soil-palette`, `npm run lint` and `npm run build` all exit 0.</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>
The soil layer's 8 near-identical browns were replaced by an explicit 12-class palette plus a
5-colour fallback tier, held in the new `app/src/data/soil_legend.js` and consumed by both the map
fill and the legend. Duplicate colours are gone: every soil class painted in a Living Lab now has its
own colour, and the closest pair of legend swatches is at least 20 CIELAB units apart in all five
Living Labs (previously 0 — several swatches were byte-identical). Special areas moved from a pale
blue-grey to a neutral grey so they no longer read as water, and the polygon hairline moved from
brown to neutral dark grey.
  </what-built>
  <how-to-verify>
1. `cd app && npm run dev`, then open the printed localhost URL.
2. For each of the five Living Labs, open its detail page and select the **Soil** tab:
   east-brandenburg, havelland, hessian-low-mountain, north-hessian-loess, rheingau.
3. For each: confirm no two swatches in the legend strip under the map look like the same colour,
   and that you can pick any coloured polygon on the map and match it to exactly one legend swatch.
   Pay particular attention to hessian-low-mountain and north-hessian-loess, where Brown soils,
   Luvisols and Stagnic soils were previously indistinguishable.
4. Confirm water polygons still read as water (pale blue) and that "Special areas" is now a plain
   neutral grey, clearly not blue.
5. Toggle the language to Deutsch (header switcher) and re-check one Living Lab: the legend labels
   must still be German (Braunerden, Gleye, Lessivés, Stauwasserböden, Niedermoore, Gewässer,
   Sonderflächen) and the swatch colours must be unchanged.
6. Confirm the colours still read acceptably against the basemap at both the default zoom and one
   step zoomed in — no class should disappear into the background.
7. Optional: hard-reload with the network throttled and confirm the brief pre-load legend (Brown
   soils / Luvisols / Gley soils / Water) uses the same colours as the loaded legend.
  </how-to-verify>
  <resume-signal>Type "approved", or name the specific Living Lab and the two classes that are still hard to tell apart</resume-signal>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| committed GeoJSON → `getSoilColor` | `soil_group_key` is pipeline-derived free text used as an object lookup key in the browser |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-acf-01 | Tampering | `getSoilColor` in `app/src/data/soil_legend.js` | mitigate | Resolve `SOIL_GROUP_COLORS` via an own-property check (`Object.prototype.hasOwnProperty.call` or a `Map`) so a crafted key such as `constructor` or `__proto__` cannot return a prototype member as a colour — the same class of defect fixed for `bySlug` in Phase 10 plan `10-03` |
| T-acf-02 | Information disclosure | rendered palette | accept | Colours carry no data beyond what the already-public BÜK250 fixtures expose |
| T-acf-SC | Tampering | npm installs | accept | No package is added or upgraded by this plan; `app/package.json` gains only a `scripts` entry, so the Package Legitimacy Gate does not apply |
</threat_model>

<verification>
- `cd app && npm run check:soil-palette` — palette uniqueness, ΔE floors, and per-Living-Lab class/legend distinctness against all five committed fixtures
- `cd app && npm run lint` — clean
- `cd app && npm run build` — clean
- `grep -c` over `app/src/components/LLMap/index.jsx` and `app/src/data/layers.js` for the eleven retired hex codes returns 0
- No change under `data-pipeline/`; `python -m pytest data-pipeline/tests/` is unaffected and need not be re-run
</verification>

<success_criteria>
- In every one of the five Living Labs, the number of unique colours painted on the soil map equals the number of soil classes present (14/14, 13/13, 12/12, 12/12, 9/9)
- The minimum pairwise CIELAB ΔE76 among the 7 legend swatches is ≥ 20 in every Living Lab (currently 0)
- The map fill and the legend swatch for any given class resolve to the same hex, via a single shared module
- `npm run lint` and `npm run build` pass; `package.json` `dependencies` and `devDependencies` are byte-identical to before
- The human reviewer approves the visual result in both EN and DE
</success_criteria>

<output>
Create `.planning/quick/260804-acf-make-soil-map-and-legend-colours-more-di/260804-acf-SUMMARY.md` when done.
On completion, mark TODO-01 in `.planning/STATE.md` as partially closed (the colour-divergence half;
the tooltip verbosity and mixed-language half remains open).
</output>
