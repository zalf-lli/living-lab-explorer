# Phase 4: Destatis Statistics Integration - Context

**Gathered:** 2026-07-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix the Destatis GENESIS-Online API auth bug in `fetch_destatis.py`, verify a curated set of GENESIS
tables against the live API, process results into per-NUTS3/per-LL records, and wire selected
indicators into the app. Discussion significantly reshaped the "wire into the app" part of this
boundary: instead of populating the existing flat `KPIStrip`, the app's tab structure itself changes
to host per-tab statistics (see Decisions below). This restructuring is scoped to Phase 4 because it
is the concrete mechanism the user chose for "integrate the selected indicators into the app" — it is
not a separate new capability.

</domain>

<decisions>
## Implementation Decisions

### Tab structure & KPIStrip retirement
- **D-01:** The tab currently labeled "Land Use" (`layers.landuse`, id `landuse`) is renamed to
  **"Agriculture"** — its map (DLR croptypes PMTiles) is unchanged; only the label/framing changes,
  since the map has only ever shown crop types, not general land use.
- **D-02:** The tab currently labeled "Economic" (`layers.economic`, id `economic`) is renamed to
  **"Socio-economic"** — no map change.
- **D-03:** A new tab, **"Landscape"**, is added. It is **KPI-only in this phase** — no map layer. It
  uses the same "available once it has real content" gating as the other tabs (see D-04), not the
  current `available: false` placeholder treatment.
- **D-04:** Climate and Socio-economic tabs (currently `available: false`, "coming soon") flip to
  `available: true` **as soon as their KPI panel has real Destatis data** — independent of whether
  they have a map layer. A map overlay for Climate/Socio-economic/Landscape remains future work.
- **D-05:** The existing `KPIStrip` component (fixed 4-value strip above the tabs: totalArea,
  activeFarms, avgTemp, dominantSoil) is **retired entirely**. Each tab shows its own KPI panel in
  that same visual slot, swapping content when the active tab changes — not an additional panel
  alongside the old strip.

### Catalogue group → tab mapping
- **D-06:** Destatis catalogue group **Agriculture** (40 variables) → **Agriculture** tab.
- **D-07:** Destatis catalogue group **Social** (20 variables) → **Socio-economic** tab.
- **D-08:** Destatis catalogue group **Environment** (10 variables) splits three ways:
  - `forest_area_ha`, `forest_public_pct`, `natura2000_ha`, `nature_reserves_ha`,
    `landscape_protection_ha`, `settlement_area_ha`, `sealed_surface_pct` → **Landscape** tab
  - `agr_ch4_kt`, `agr_n2o_kt` → **Climate** tab
  - `groundwater_nitrate_mg_l` → **Soil** tab

### Curated KPIs (fixed count, decided now — not driven by expert review)
- **D-09:** Per-tab KPI sets are a **fixed, hand-picked list**, not derived from filling in
  `include_yn` across the full 71-row catalogue. Locked picks (17 variables / 11 unique GENESIS
  tables):

  | Tab | Variable key | GENESIS table |
  |-----|--------------|----------------|
  | Agriculture | `land_area_cropland_ha` | 33111BJ002 |
  | Agriculture | `farms_count` | 41120BJ001 |
  | Agriculture | `farm_avg_size_ha` | 41120BJ001 |
  | Agriculture | `organic_pct` | 41120BJ002 |
  | Soil | `n_surplus_kg_ha` | 41411BJ001 |
  | Soil | `p_surplus_kg_ha` | 41411BJ002 |
  | Soil | `groundwater_nitrate_mg_l` | 32221BJ001 |
  | Climate | `agr_ch4_kt` | 32411BJ001 |
  | Climate | `agr_n2o_kt` | 32411BJ001 |
  | Landscape | `forest_area_ha` | 33111BJ003 |
  | Landscape | `natura2000_ha` | 32121BJ001 |
  | Landscape | `nature_reserves_ha` | 32141BJ001 |
  | Landscape | `sealed_surface_pct` | 33111BJ004 |
  | Socio-economic | `population_total` | 12411KJ002 |
  | Socio-economic | `gdp_per_capita_eur` | 82111KJ001 |
  | Socio-economic | `unemployment_rate_pct` | 13211KJ002 |
  | Socio-economic | `household_income_eur` | 82521KJ001 |

### Placeholder data & file ownership
- **D-10:** Every existing value in `data/ll_content.json`'s `kpi`/`production`/`socio` blocks is
  placeholder-only (confirmed by user) — safe to overwrite entirely, no value needs preserving.
- **D-11:** The restructure of `ll_content.json` (new per-tab KPI shape, placeholders stripped) is
  done as a **one-time direct edit by the executor during this phase** — not by any pipeline
  script. This satisfies CLAUDE.md's rule that pipeline scripts must never write
  `data/ll_content.json`; the edit is a deliberate one-off content pass, not recurring pipeline output.
- **D-12:** No change to `generate_metadata.py`'s `_deep_merge` (authored-wins) policy is needed —
  since `ll_content.json` itself is being directly rewritten to the new shape, there's no stale
  placeholder left for the merge to fight with.

### Table verification scope & fallback
- **D-13:** Verification is scoped to the **11 unique GENESIS table IDs** backing the 17 curated
  picks above — **not** a full expert review of all 71 catalogue rows (diverges from Phase 3.1's
  full-catalogue review pattern; the other ~54 rows stay untouched).
- **D-14:** If a picked table fails verification (doesn't exist, doesn't resolve at Kreis level, or
  returns GENESIS code 104), **swap in the next-best variable from the same catalogue group** for
  that tab slot rather than leaving it empty — keeps each tab's KPI count intact.
- **D-15:** If a table turns out to live on **Regionalstatistik.de** instead of
  `genesis.destatis.de`, **pursue registration/credentials for that second host** rather than
  treating it as out of scope — a new base URL and credential set for that host is in-scope work for
  this phase if needed.

### Claude's Discretion
- Whether `LAYERS` array internal `id` values change (e.g. `landuse` → `agriculture`) or only
  display labels/i18n strings change — pick whichever minimizes unrelated file/path churn
  (`geojsonPathPattern`, PMTiles keys, `LAYER_COLORS` map, etc.).
- Exact `StatPanel`/`DataRow` layout differences needed for a KPI-only tab (Landscape, Climate,
  Socio-economic) vs. a tab that also has a map (Agriculture, Soil).
- Whether the ~54 unpicked catalogue variables' `include_yn`/`priority_1_3` columns get touched at
  all this phase (default: leave empty — no action).
- Exact copy/UX for a tab that has real KPIs but still no map layer (Climate, Socio-economic,
  Landscape) — UI-SPEC.md's existing "coming soon" wireframe note must not contradict a tab that now
  shows real numbers.

</decisions>

<specifics>
## Specific Ideas

- "The map in the currently named land use tab actually reflects only crop types" — the direct
  rationale for the Agriculture rename; the map itself does not change.
- "KPIs can be adjusted based on destatis variables if necessary" — the curated list in D-09 is a
  strong starting point, not untouchable; if a table fails verification, swap per D-14 rather than
  re-opening the whole picklist.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase definition & prior research
- `.planning/ROADMAP.md` §"Phase 4: Destatis Statistics Integration" — goal, scope, Destatis support
  email fixes, reference docs/PDF links
- `.planning/phases/04-destatis-statistics-integration-source-process-and-app-integ/04-RESEARCH.md`
  — auth/request-structure fix (headers not body, new host), GENESIS code 104 meaning, AGS vs NUTS3
  regional-key risk, table verification approach, Pitfall 3 (placeholder resolution) that this
  discussion resolved via D-10/D-11/D-12

### UI design contract — NEEDS REVISION
- `.planning/phases/04-destatis-statistics-integration-source-process-and-app-integ/04-UI-SPEC.md`
  — **already approved, but written before this discussion's tab restructuring.** It assumed a single
  new `StatPanel` appended below the existing `KPIStrip`, not a full tab-structure change (rename +
  new Landscape tab + KPIStrip retirement). Its typography/spacing/color tokens and copywriting
  contract (empty-state em-dash, source-attribution line, "View source" link) still apply — but its
  "Implementation Notes" section describing where `StatPanel` sits needs to be reconciled with D-01
  through D-05 before/during planning. **Re-run `/gsd:ui-phase 4` or explicitly re-verify this
  section before the planner locks task-level UI work.**

### Project rules
- `CLAUDE.md` — critical rules: never write `data/ll_content.json` from a pipeline script (D-11
  satisfies this), always `json.dumps(..., sort_keys=True)` in pipeline output, files-on-disk
  pipeline–app contract (no runtime coupling)

### Data sources
- `data/destatis_variables_catalogue.csv` — 71-row candidate catalogue; source of the group→tab
  mapping (D-06/D-07/D-08) and the 11 GENESIS table IDs in D-09
- `data-pipeline/python/fetch_destatis.py` — existing fetch/cache/aggregate script; auth bug fix
  target per RESEARCH.md
- `data-pipeline/python/generate_metadata.py` — `_deep_merge`/`_build_computed_record`; unchanged
  per D-12 but the extension point for wiring computed Destatis fields into `ll_metadata.json`
- `data/ll_content.json` — human-authored content file; target of the D-11 one-time restructure edit

### Frontend code to change
- `app/src/data/layers.js` — `LAYERS` array; add `landscape` entry, adjust `available` flags per D-04
- `app/src/components/LayerTabs.jsx` — tab rendering; no structural change expected, driven by
  `LAYERS` + i18n
- `app/src/components/KPIStrip.jsx` — retired per D-05; replaced by new per-tab component(s)
- `app/src/i18n.js` — `layers.*` keys (rename `landuse`→"Agriculture", `economic`→"Socio-economic",
  add `landscape`) and new per-tab KPI label keys (EN + DE, lines ~48 and ~211)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `data-pipeline/python/fetch_destatis.py`: fetch/cache/retry/aggregate architecture
  (`LL_NUTS3` mapping, `_post()` exponential backoff, `build_nuts3_records`/`aggregate_ll`) is sound
  per RESEARCH.md — only the auth header bug needs fixing, not a rewrite.
- `app/src/components/KPIStrip.jsx`: existing tile visual language (white card, `C.mutedLight`
  border, uppercase `C.greenMid` label, bold `C.teal` value) — the pattern UI-SPEC.md's new
  `StatPanel`/`DataRow` should follow, per-tab, once KPIStrip itself is retired.
- `data/destatis_variables_catalogue.csv`: already has EN/DE labels, units, and GENESIS table IDs
  for every variable — no new lookup/labeling work needed for the 17 curated picks.

### Established Patterns
- `sources.yaml` `kind:` vocabulary is `raster`/`vector`; Phase 3.1's CONTEXT.md flagged `tabular` as
  the natural new value for statistical sources like Destatis (not yet added to the YAML).
- i18n keys are namespaced per domain (`kpi.*`, `layers.*`, `legend.*`) in `app/src/i18n.js` — new
  per-tab KPI labels should follow this convention, not introduce a new top-level namespace.
- `generate_metadata.py`'s `_deep_merge(computed, authored)` — authored wins on conflict; unaffected
  by this phase per D-12.

### Integration Points
- `app/src/hooks/useLLMetadata.js` fetches the single merged `ll_metadata.json` — no hook changes
  anticipated if the new per-tab KPI shape flows through the same file.
- `data-pipeline/sync.py` is the file-on-disk bridge; whatever `generate_metadata.py` emits into
  `ll_metadata.json` reaches the app through the existing sync step, no new sync logic anticipated.

</code_context>

<deferred>
## Deferred Ideas

- **Full 71-variable expert review** (filling `include_yn`/`priority_1_3`/`expert_comments` for every
  catalogue row, mirroring Phase 3.1's Wave 3 human-in-the-loop pattern) — deferred; only the 11
  tables behind the curated picks get verified this phase.
- **Map layers for Climate, Landscape, and Socio-economic tabs** — explicitly future work; these tabs
  get real KPIs this phase but stay map-less.
- **The ~54 unpicked catalogue variables** — remain available in `data/destatis_variables_catalogue.csv`
  for a future phase if more indicators are wanted; no action taken on them this phase.

</deferred>

---

*Phase: 04-destatis-statistics-integration-source-process-and-app-integ*
*Context gathered: 2026-07-24*
