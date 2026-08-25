# Phase 5: Add protected areas as toggleable layer on landscape map — Research

**Researched:** 2026-07-25
**Domain:** OGC WFS 2.0 geodata acquisition (BfN Schutzgebiete) → GeoPandas per-LL GeoJSON → Leaflet vector overlay
**Confidence:** HIGH (every endpoint claim below was executed live against the production service on 2026-07-25)

---

<user_constraints>
## User Constraints (from 05-CONTEXT.md)

### Locked Decisions

- **D-01:** Include Natura 2000 sites (both SCIs — Special Conservation Areas — and SPAs — Special Protection Areas)
- **D-02:** Include German Nature Reserves (Naturschutzgebiete) from federal/state registries
- **D-03:** Display full polygon boundaries for any protected area that intersects the Living Lab region boundary (not clipped to LL boundary)
- **D-04:** Acquire protected areas data via live WFS (Web Feature Service) queries at pipeline runtime, not manual download + commit (unlike BÜK vector approach)
- **D-05:** Protected areas is a separate independent toggle, not forced along with land-use
- **D-06:** Protected areas layer always renders on top of land-use layer (no user-configurable stacking)
- **D-07:** Lazy load protected areas GeoJSON on toggle (when user clicks protected areas toggle), not upfront with land-use
- **D-08:** Render all polygon features without simplification or downsampling, accepting potential interaction slowness on large datasets for data fidelity

### Claude's Discretion

- Visual styling (colors, fill vs outline, opacity)
- Legend grouping (group by area type or show flat list)
- Hover/click interaction detail level (name only vs full metadata display)
- Exact WFS service endpoint selection if multiple providers available

### Deferred Ideas (OUT OF SCOPE)

- User-configurable layer stacking order
- Filtering protected areas by type/designation (show only SPAs, hide SCIs, etc.)
- Detailed info panels with protection status, management authority, conservation objectives
- Polygon simplification/downsampling for performance optimization
</user_constraints>

---

## Project Constraints (from CLAUDE.md)

| Directive | Impact on this phase |
|-----------|---------------------|
| Static-only hosting, `base: './'`, must work at any sub-path | GeoJSON URLs stay **relative** (`data/geojson/…`), matching `layers.js` `geojsonPathPattern` |
| Python 3.12 required on Windows | New fetch script must run under `data-pipeline/.venv` (Python 3.12, GeoPandas 1.1.3, Shapely 2.1.2) — verified |
| No TypeScript, no CSS frameworks, no SSR | Frontend work is plain JSX + inline styles, per `05-UI-SPEC.md` |
| **Never write `data/ll_content.json` from any pipeline script** | New script writes only `data/geojson/protected-areas-*.geojson` |
| **Always call `make_valid()` after `gpd.read_file()`** | Mandatory — ~1 % of BfN features are invalid on read (measured, see Pitfall 8) |
| **Always align CRS before clipping**, assert `len(clipped) > 0` | Source is EPSG:25832; LL boundaries are EPSG:4326. Reproject before `intersects()` |
| **`json.dumps(..., sort_keys=True)` everywhere in `sync.py`** | Use `GeoDataFrame.to_json(drop_id=True, sort_keys=True)` — same call `build_vector.py` uses |
| Pipeline–app contract: files on disk only | No runtime WFS calls from the browser. WFS runs at pipeline time only (satisfies D-04) |

---

<phase_requirements>
## Phase Requirements

`.planning/REQUIREMENTS.md` currently contains **no requirement IDs for Phase 5** — traceability
table stops at `CHARTS-02` (Phase 3). The planner should either add `PROTECTED-0x` IDs to
REQUIREMENTS.md or proceed with the CONTEXT decision IDs (D-01…D-08) as the traceability anchor.

| ID | Description | Research Support |
|----|-------------|------------------|
| D-01 | Natura 2000 SCI + SPA | `Fauna_Flora_Habitat_Gebiete` + `Vogelschutzgebiete` typenames, verified §1 |
| D-02 | German Nature Reserves | `Naturschutzgebiete` typename on the *same* BfN service, verified §1 |
| D-03 | Full unclipped polygons intersecting the LL | Padded-bbox fetch + `geometry.intersects(ll_geom)` boolean filter (no `gpd.clip`), verified §3 |
| D-04 | Live WFS at pipeline runtime | GetFeature proven for all 3 layers × 5 LLs, 33 s total, §3 |
| D-05/D-06/D-07 | Independent toggle, top stacking, lazy load | **Corrected during planning:** `LayerTabs` is *exclusive*, so it cannot express D-05/D-06. Delivered by a new `OVERLAYS` registry + an in-map toggle + an imperative `ProtectedAreasLayer` (`useMap()` + `useEffect`) in a dedicated pane; `useGeoJSON` covers D-07 unchanged. See 05-02-PLAN.md Task 1 |
| D-08 | No simplification | Feasible but **312 k vertices max per LL** — requires Canvas renderer, §5 Pitfall 12 |
</phase_requirements>

---

## Summary

**A single WFS endpoint serves all three required designations.** `https://geodienste.bfn.de/ogc/wfs/schutzgebiet`
(BfN, WFS 2.0.0, ArcGIS Server backed) publishes `Fauna_Flora_Habitat_Gebiete` (Natura 2000 SCI),
`Vogelschutzgebiete` (Natura 2000 SPA) and `Naturschutzgebiete` (German nature reserves) as separate
feature types. There is **no need for a second provider** — BfN harmonises the 16 state NSG registries
annually into one federal dataset. The `05-UI-SPEC.md` reference to *LAWA* as the nature-reserve
authority is **incorrect** and should be dropped: LAWA (Bund/Länder-Arbeitsgemeinschaft Wasser) is
the water-management working group and publishes no protected-area registry.
[VERIFIED: GetCapabilities executed 2026-07-25] [CITED: gdk.gdi-de.org record bec888f9-ba0c-42dc-846e-177b8265dafa]

**The service works, but has four silent-failure traps that will produce wrong or empty output if
the executor writes the "obvious" query.** The BBOX parameter *must* be `lat,lon` order with an
explicit `urn:ogc:def:crs:EPSG::4326` suffix — every other spelling (plain `EPSG:4326`, `EPSG:25832`,
no suffix) returns HTTP 200 with **zero features and no error**. Passing `SRSNAME` at all flips the
GeoJSON output to lat/lon axis order (invalid per RFC 7946). And `OUTPUTFORMAT=GEOJSON` **silently
drops features near the bbox edge** (measured: 80 returned vs 82 matched for Rheingau NSG). The
default GML 3.2 output is complete, correctly typed, declares EPSG:25832, and is read cleanly by
GDAL/GeoPandas — use it.

**Volume is the one open risk against D-08.** Measured end-to-end: 1,248 features and **1.01 million
vertices** across the 5 Living Labs; the largest single LL (East Brandenburg) is 355 features /
311,616 vertices / **12.55 MB** of unrounded GeoJSON. Leaflet's default SVG renderer will not
handle that interactively. Switching the GeoJSON layer to `L.canvas()` preserves full geometric
fidelity (it is a rendering backend change, not simplification, so D-08 holds) and is the single
highest-value implementation decision in this phase.

**Primary recommendation:** Add one new script `data-pipeline/python/fetch_protected_areas.py` that
GETs the three BfN feature types per LL using a lat/lon-ordered `urn:` BBOX padded by 0.05°, reads the
**GML** response with GeoPandas, `make_valid()`s, reprojects 25832→4326, filters with
`intersects(ll_geom)` (no clipping, per D-03), normalises the three divergent schemas onto the
UI-SPEC property contract, and writes `data/geojson/protected-areas-{slug}.geojson`. Register the
layer in `sources.yaml` with `kind: vector` + `app_layer: protected-areas` so **`sync.py` needs zero
code changes**. On the app side, add one entry to a new `OVERLAYS` array in `app/src/data/layers.js` (**corrected
during planning:** NOT `LAYERS`, which would create an exclusive tab and make D-06 unimplementable),
and render it with an imperative `ProtectedAreasLayer` component using `useMap()` + `useEffect`,
in a dedicated pane at `zIndex 450` with an `L.canvas({ padding: 0.5, pane: 'protectedAreasPane' })`
renderer.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| WFS querying, CRS handling, geometry validation | Python pipeline (`fetch_protected_areas.py`) | — | CLAUDE.md: pipeline–app contract is files on disk; browser never calls WFS. Also avoids CORS + BfN WAF entirely |
| Schema normalisation (3 divergent BfN schemas → 1 UI contract) | Python pipeline | — | Keeps JSX free of German field-name branching; matches `soil_semantics.py` precedent |
| Spatial intersect filter (D-03) | Python pipeline | — | GEOS `intersects()` in GeoPandas; not feasible client-side at 1 M vertices |
| Asset copy to `app/public/` | `sync.py` (`sync_vector_geojson`) | — | Already globs `output.geojson_pattern` for every `kind: vector` layer — no change needed |
| Source/licence attribution metadata | `sync.py` (`generate_layer_sources`) → `layer_sources.js` | `MapInfoControl` | Codegen path already exists; keyed by `app_layer` |
| Lazy fetch + cache | Browser (`useGeoJSON` hook) | — | Module-level `cache`/`inflight` Maps already implement D-07 |
| Layer toggle UI | Browser (`ProtectedAreasToggle` in `LLMap`) | `layers.js` `OVERLAYS` | **Corrected during planning 2026-07-25:** research originally proposed appending to `LAYERS`, but `LayerTabs` is *exclusive* (`active === l.id`), so a protected-areas tab hides land-use and makes D-06 ("renders on top of land-use") unimplementable. The layer is registered in a separate `OVERLAYS` array and toggled by an independent in-map control; `LayerTabs.jsx` and `LLDetail.jsx` stay untouched. See 05-02-PLAN.md Task 1. |
| Polygon rendering + tooltips + legend | Browser (`LLMap`, `MapLegend`) | — | Leaflet Canvas renderer required at this vertex count |

---

## 1. WFS Endpoints Found & Validated

### 1.1 The single authoritative endpoint

| Property | Value |
|----------|-------|
| **Base URL** | `https://geodienste.bfn.de/ogc/wfs/schutzgebiet` |
| **Service title** | "Bundesamt für Naturschutz: Schutzgebiete" |
| **WFS version** | 2.0.0 (`ImplementsResultPaging=TRUE`, `ImplementsStandardJoins=FALSE`) |
| **Backend** | ArcGIS Server (namespace leaks internal host `https://gis-shost:6443/arcgis/services/bfn_sch/Schutzgebiet/MapServer/WFSServer`) |
| **DefaultCRS (declared)** | `urn:ogc:def:crs:EPSG::25832` (ETRS89 / UTM zone 32N) — no `OtherCRS` advertised |
| **CountDefault** | 1000 (must pass `COUNT` explicitly for larger result sets) |
| **outputFormat** | `GML32` (default), `GML3`, `GML2`, `GEOJSON`, `ESRIGEOJSON`, `CSV`, `KML`, `KMZ`, + `+ZIP` variants |
| **Auth** | **None.** "Es gelten keine Zugriffsbeschränkungen" |
| **Licence** | Nutzungsbestimmungen für die Bereitstellung von Geodaten des Bundes (GeoNutzV) — same licence family as the already-integrated BUEK250 layer |
| **Attribution required** | "Bundesamt für Naturschutz (BfN)" |
| **Access constraint note** | *"Nicht für Planungszwecke geeignet"* (not suitable for planning purposes) — should be surfaced in the legend note or info control |
| **Metadata record** | `https://gdk.gdi-de.org/geonetwork/srv/api/records/bec888f9-ba0c-42dc-846e-177b8265dafa` |
| **Human viewer** | `https://geodienste.bfn.de/schutzgebiete` |

[VERIFIED: GetCapabilities HTTP 200, 18,405 bytes, 2026-07-25]
[VERIFIED: `data/variables_catalogue.xlsx` → `source_catalogue` row `bfn_protected_areas` independently lists this exact URL, `decision` column blank]

### 1.2 Feature types required by D-01 / D-02

| UI designation | WFS `TYPENAMES` | Data vintage | Verified |
|---|---|---|---|
| `Natura 2000 SCI` | `bfn_sch_Schutzgebiet:Fauna_Flora_Habitat_Gebiete` | **2019** | ✅ |
| `Natura 2000 SPA` | `bfn_sch_Schutzgebiet:Vogelschutzgebiete` | **2019** | ✅ |
| `Naturschutzgebiet` | `bfn_sch_Schutzgebiet:Naturschutzgebiete` | **2023** | ✅ |

Six further feature types exist on the same service and are **out of scope** for D-01/D-02
(`Nationalparke` 2025, `Naturparke` 2025, `Biosphaerenreservate` 2025, `Biosphaerenreservate_Zonierung`,
`Nationale_Naturmonumente` 2025, `Landschaftsschutzgebiete` 2023). Adding any of them later is a
one-line change to the layer dict — worth structuring the code for that.
[VERIFIED: GetCapabilities FeatureType list]

**Data-currency caveat (flag for user):** Natura 2000 geometries are the 2019 harmonised release.
BfN's abstract states the harmonisation runs "einmal jährlich" but the FFH/VSG layers have not been
refreshed since 2019. For a *contextual* overlay this is acceptable — Natura 2000 boundaries change
slowly — but it should be stated in the legend/info control ("Stand: 2019 / 2023"). No newer
*live WFS* alternative for all-Germany Natura 2000 was found; state portals (e.g. Hessen NATUREG,
Brandenburg GeoBroker) publish more current per-state services but would require 5+ endpoints with
5 different schemas — a much worse trade for this phase. [CITED: bfn.de/daten-und-fakten/natura-2000-gebietsmeldestatistik-und-karten]

### 1.3 LAWA is not a nature-reserve source — correction to 05-UI-SPEC.md

`05-UI-SPEC.md` §4.1 lists the provider as *"BfN … / LAWA (German water authority)"*. LAWA is the
Bund/Länder-Arbeitsgemeinschaft Wasser; it publishes no Naturschutzgebiete registry. **BfN is the
sole provider for all three designations.** The planner must correct:
- `map.info.protectedAreasProvider` EN → `Federal Agency for Nature Conservation (BfN)`
- `map.info.protectedAreasProvider` DE → `Bundesamt für Naturschutz (BfN)`
[VERIFIED: no LAWA protected-area WFS exists; BfN abstract explicitly states it aggregates "aus den Datensätzen der Bundesländer und des Bundes"]

### 1.4 CRS / EPSG codes

| Context | Code | Notes |
|---|---|---|
| Source geometry | `EPSG:25832` | ETRS89 / UTM 32N, metres. GDAL reports this correctly from the GML |
| BBOX parameter | **`urn:ogc:def:crs:EPSG::4326` only** | Must be the URN form, and coordinates in **lat,lon** order |
| Pipeline output | `EPSG:4326` | RFC 7946 lon,lat — reproject in GeoPandas, never via `SRSNAME` |
| LL boundaries (`data/ll_boundaries.geojson`) | `EPSG:4326` | File has no `crs` member; GeoPandas infers 4326 correctly |

### 1.5 Rate limiting / access policy

- **No documented rate limit.** 15 sequential GetFeature calls (≈70 MB on the wire) completed in
  33 s with zero throttling. [VERIFIED: timed run 2026-07-25]
- **A WAF sits in front of the service and intermittently returns HTTP 403** with a German
  `403 - Zugriff verweigert | BFN` HTML page. Observed once on `GetCapabilities` with curl's default
  UA; the identical request succeeded seconds later with *any* UA including `python-urllib/3.12`.
  This is **transient, not UA-based** — a retry loop is required, not a fake browser UA.
  [VERIFIED: 403 then 200 on identical URL; later 3/3 UA variants all returned 200]
- Set a descriptive `User-Agent` anyway as good citizenship (e.g. `ll-explorer-pipeline/1.0 (+https://zalf.de)`) — verified accepted.

---

## 2. Feature Schema & Data Availability

### 2.1 The three schemas are inconsistent — normalisation is mandatory

BfN did not harmonise the *attribute* schemas. FFH uses long German field names; SPA and NSG use
legacy ArcGIS SHORTCAPS. The pipeline must map all three onto one contract.

**`Fauna_Flora_Habitat_Gebiete` (SCI)** — 14 attributes + `SHAPE`
| Field | Type | Example |
|---|---|---|
| `OBJECTID` | int | `2454` |
| `Gebietsname` | string(250) | `Mittelrhein` |
| `BfN-ID` | int | `83128` (**note the hyphen** in the field name) |
| `Bundesland` | string(20) | `RP` |
| `Gebietsnummer` | string(20) | `DE5510301` (EU site code) |
| `Gebietsnummer_mit_Landeskuerzel` | string(50) | `RP_DE5510301` |
| `Datum_der_gueltigen_Verordnung` | dateTime | `2005-10-01T00:00:00` |
| `Bezeichnung_der_gueltigen_Verordnung` | string(250) | `Landesnaturschutzgesetz §25 (2) Rheinland-Pfalz …` |
| `URL_der_gueltigen_Verordnung` | string(250) | **`null` in 51/51 sampled features** |
| `Marine_Flaeche_in_Prozent` | int | `0` |
| `Biogeographische_Region` | string(50) | `kontinental` |
| `FLAECHE` | double | `1194.0` (**hectares**, verified) |
| `Wasserrahmenrichtlinie` | string(5) | `ja` |
| `Wasserrahmenrichtlinie_` | string(106) | `https://www.bfn.de/natura-2000-gebiet/mittelrhein` — **upstream naming bug**: the field is named after the WFD column but actually holds the BfN site detail URL |

**`Vogelschutzgebiete` (SPA)** — 14 attributes + `SHAPE`
`OBJECTID`, `NAME`, `BFN_ID`, `BL`, `ID` (`RP_DE6013401`), `SITECODE` (`DE6013401`), `LEG_DATE`
(dateTime, **null in 6/6 sampled**), `LEG_LINK` (null in 6/6), `LEG_TITEL` (null in 6/6),
`MARIN_AREA`, `BIOGEO`, `FLAECHE` (ha), `WRRL`, `LINK` (BfN site URL — correctly named here).

**`Naturschutzgebiete` (NSG)** — 15 attributes + `SHAPE`
`OBJECTID`, `NAME`, `BFN_ID` (double), `BL`, `ID` (`he_1436017`), `LEG_DATE` (dateTime, populated),
`LEG_LINK` (state ordinance PDF, populated), `LEG_TITEL` (often a single space `" "`),
`CDDA_CODE` (double, EEA Common Database on Designated Areas key), `IUCN_KAT` (`IV`),
`JAHR` (double, e.g. `1994.0` — **year of designation**), `MAJ_ECO_T` (`T` = terrestrial),
`MARIN_AREA`, `FLAECHE` (ha), `STATUS` (double, `1.0`).

[VERIFIED: `DescribeFeatureType` for all three + live GetFeature value inspection]

### 2.2 Mapping to the `05-UI-SPEC.md` property contract

| UI-SPEC key | SCI source | SPA source | NSG source | Note |
|---|---|---|---|---|
| `name` / `name_de` | `Gebietsname` | `NAME` | `NAME` | German only |
| `name_en` | — | — | — | **No English names exist.** Set `name_en = name_de`; `getLocalizedValue()` already falls back |
| `designation` | literal `"Natura 2000 SCI"` | `"Natura 2000 SPA"` | `"Naturschutzgebiet"` | Emitted by the pipeline, matches the UI-SPEC `styleMap` keys exactly |
| `designation_de` / `designation_en` | constants | constants | constants | e.g. `FFH-Gebiet` / `Special Conservation Area` |
| `area_ha` | `FLAECHE` | `FLAECHE` | `FLAECHE` | **Confirmed hectares** — median ratio of GEOS-computed area to `FLAECHE` = 0.999 / 1.000 / 1.000 across the three layers |
| `established_year` | year of `Datum_der_gueltigen_Verordnung` | year of `LEG_DATE` (**usually null**) | `int(JAHR)`, else year of `LEG_DATE` | Must be nullable; UI-SPEC tooltip already guards with `if (props.established_year)` |
| `authority` | derive from `Bundesland` | derive from `BL` | derive from `BL` | **No authority field exists.** Recommend a 16-entry Bundesland-code → bilingual state-name map. Codes seen in LL bboxes: `BB`, `HE`, `RP`, `SN`, `ST`, `NI`, `NW`, `TH`, `MV` |
| `ll_slug` | injected | injected | injected | Pipeline-assigned |
| *(suggested extra)* `site_code` | `Gebietsnummer` | `SITECODE` | `ID` | Stable join key; useful for dedup + debugging |
| *(suggested extra)* `source_url` | `Wasserrahmenrichtlinie_` | `LINK` | `LEG_LINK` | Could power a click-through; deferred per CONTEXT |

### 2.3 Coverage per Living Lab — measured, not estimated

**Correction to the task brief:** the 5 Living Labs are in **Brandenburg (2) and Hesse (3)** — not
Lower Saxony / Rhineland-Palatinate / North Rhine-Westphalia. Confirmed from
`data/ll_boundaries.geojson` and `data/ll_metadata.json`. (Protected areas *from* RP, SN, NI, NW, TH
do appear in the results because bboxes overlap neighbouring states; the `intersects()` filter keeps
only genuinely overlapping sites.)

Feature counts after the exact `intersects(ll_geometry)` filter (D-03 semantics):

| Living Lab | NUTS3 | SCI | SPA | NSG | **Total** | Vertices | GeoJSON (raw) | @1e-6 | gzip @1e-6 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `east-brandenburg` | DE409, DE40C | 186 | 18 | 151 | **355** | 311,616 | 12.55 MB | 7.42 MB | 2.00 MB |
| `havelland` | DE408 | 130 | 11 | 116 | **257** | 190,204 | 7.70 MB | 4.57 MB | 1.22 MB |
| `hessian-low-mountain` | — | 153 | 20 | 189 | **362** | 275,573 | 10.87 MB | 6.29 MB | 1.65 MB |
| `north-hessian-loess` | — | 92 | 8 | 96 | **196** | 165,610 | 6.54 MB | 3.71 MB | 0.89 MB |
| `rheingau` | — | 33 | 4 | 41 | **78** | 69,737 | 2.75 MB | 1.59 MB | 0.42 MB |
| **Total** | | **594** | **61** | **593** | **1,248** | **1,012,740** | **40.41 MB** | **23.58 MB** | **6.18 MB** |

"raw" = `GeoDataFrame.to_json()` at full float precision. "@1e-6" = after
`shapely.set_precision(grid_size=1e-6)` (≈0.11 m) — **zero features lost, no visible geometry
change**. `@1e-5` (≈1.1 m) yields 20.84 MB total, also zero feature loss.

[VERIFIED: full end-to-end run against the live service, 2026-07-25]

### 2.4 Geometry quality

- **All features are `MultiPolygon`** across all three layers and all 5 LLs. No mixed geometry types,
  no points, no nulls. [VERIFIED]
- **~1 % of features are invalid on read** and require `make_valid()`:
  measured SCI 540/545 valid → 545/545 after; SPA 44/46 → 46/46; NSG 460/460 (already valid).
  After `make_valid()` + reprojection, `geometry.is_valid.all()` was `True` for all 5 merged outputs.
  [VERIFIED — this is exactly the CLAUDE.md `make_valid()` rule paying off]
- **Encoding is clean UTF-8.** Zero `U+FFFD` replacement characters in 1,065 sampled attribute cells;
  umlauts (`Lahnhänge`, `Schmittröder Wiesen`, `§25`) round-trip correctly. Console mojibake on
  Windows cp1252 terminals is a display artefact only. [VERIFIED]
- **Overlaps are expected and correct.** A single site is frequently both an FFH area and an NSG
  (e.g. `NSG Hinter der Mortkaute` appears inside the SPA layer's name field). D-03 keeps full
  polygons, so overlapping fills are by design — the UI-SPEC legend note already covers this.

---

## 3. Query Approach (proven)

### 3.1 The one query form that works

```
GET https://geodienste.bfn.de/ogc/wfs/schutzgebiet
  ?SERVICE=WFS
  &VERSION=2.0.0
  &REQUEST=GetFeature
  &TYPENAMES=bfn_sch_Schutzgebiet:Naturschutzgebiete
  &BBOX=<lat_min>,<lon_min>,<lat_max>,<lon_max>,urn:ogc:def:crs:EPSG::4326
  &COUNT=5000
```

Note what is **absent**: no `SRSNAME`, no `OUTPUTFORMAT` (default GML 3.2), no CQL filter.

**Worked example — Rheingau (`data/ll_boundaries.geojson` bbox 7.7726, 49.9720 → 8.4108, 50.2960,
padded by 0.05°):**

```
BBOX=49.9220,7.7226,50.3460,8.4608,urn:ogc:def:crs:EPSG::4326
→ HTTP 200, numberMatched="117" numberReturned="117", 1.16 MB GML
→ GeoPandas reads 117 rows, crs=EPSG:25832, all MultiPolygon
→ after intersects(rheingau_geom): 41 NSG features
```
[VERIFIED: executed 2026-07-25]

### 3.2 The BBOX axis-order trap — four spellings tested

| BBOX spelling | Result |
|---|---|
| `49.972,7.7726,50.296,8.4108,urn:ogc:def:crs:EPSG::4326` (lat,lon + URN) | ✅ 82 features |
| `7.7726,49.972,8.4108,50.296` (lon,lat, no CRS suffix) | ❌ **HTTP 200, 0 features** |
| `414000,5535000,459000,5572000,EPSG:25832` (native, plain code) | ❌ **HTTP 200, 0 features** |
| `414000,5535000,459000,5572000,urn:ogc:def:crs:EPSG::25832` | ❌ **HTTP 200, 0 features** |

There is **no error response** for the failing forms. A naive implementation ships five empty
GeoJSON files and every test that only checks "file exists / valid JSON" passes. The pipeline must
assert `numberMatched > 0`.

### 3.3 Why GML, not `OUTPUTFORMAT=GEOJSON`

| Aspect | `GML32` (default) | `OUTPUTFORMAT=GEOJSON` |
|---|---|---|
| Completeness | `numberMatched == numberReturned == rows read by GDAL` for **all 15** LL×layer queries | **Drops edge features silently** — 80 of 82 for Rheingau NSG |
| CRS | Declares `urn:ogc:def:crs:EPSG::25832` per geometry; GDAL sets `crs=EPSG:25832` | Reports `EPSG:4326`; axis order flips if `SRSNAME` is sent |
| Axis order | Unambiguous, handled by GDAL | Correct **only if `SRSNAME` is omitted**; any `SRSNAME=…4326` yields lat,lon |
| Nulls | Absent elements → proper `None` | Literal string `"null"` |
| Dates | ISO `2005-10-01T00:00:00` | German `01.10.2005` |
| Wire size | ~2× larger (70 MB total vs ~35 MB) | smaller |
| GeoPandas | `gpd.read_file(path)` works directly | needs manual `json` + `shape()` |

The dropped-feature behaviour was isolated precisely: the two missing Rheingau NSGs
(`OBJECTID` 1520 `Walterstein bei Lorsbach`, 1874 `Oberes Emsbachtal`) both sit at easting ≈458,050
— the eastern bbox edge. Re-running with a 0.05° padded bbox recovered both (117 matched /
114 GeoJSON, both IDs present). The GeoJSON writer evidently re-applies the spatial filter after
reprojection with slightly different edge arithmetic. Padding masks it; GML avoids it entirely.
[VERIFIED: OBJECTID-level diff between GML and GeoJSON responses]

### 3.4 Paging

`CountDefault=1000` and `ImplementsResultPaging=TRUE`. Highest `numberMatched` observed on a padded
LL bbox was **630** (SCI, East Brandenburg) — comfortably under the default. Passing `COUNT=5000`
was honoured (returned 630/630). Recommendation: pass `COUNT` explicitly **and** assert
`numberMatched == numberReturned`, raising if the server ever truncates. Do not build a paging loop
speculatively; `STARTINDEX` paging works (`COUNT=50&STARTINDEX=50` verified) if it is ever needed.

### 3.5 Timing

| Living Lab | 3 WFS calls + parse + intersect |
|---|---|
| east-brandenburg | 11 s |
| havelland | 8 s |
| hessian-low-mountain | 6 s |
| north-hessian-loess | 5 s |
| rheingau | 3 s |
| **Total** | **33 s** |

Set `timeout=300` per request; the largest single response was 14.57 MB.

---

## 4. Pipeline Implementation Pattern

### 4.1 How this differs from Phase 2's `build_vector.py`

| Aspect | `build_vector.py` (BUEK250) | `fetch_protected_areas.py` (this phase) |
|---|---|---|
| Input | Local GeoPackage via `ensure_input_available()` (download + SHA-256) | Live WFS GetFeature per LL × 3 typenames (D-04) |
| Spatial op | **`gpd.clip(source, mask)`** — geometry cut at the LL boundary | **`source[source.intersects(ll_geom)]`** — boolean filter, geometry untouched (D-03) |
| Simplification | `simplify(0.0005, preserve_topology=True)` | **None** (D-08) |
| Precision | `set_precision(grid_size=0.0001)` (≈11 m) | Decision needed — see §5 Pitfall 13 |
| Semantics | SQLite lookup join (`soil_semantics.py`) | Inline constant maps (3 schemas → 1 contract) |
| Layers per output file | 1 | **3 concatenated**, distinguished by `designation` |
| Empty-result policy | Raises on 0 features | Must **allow** 0 features (UI-SPEC §3.3 defines an empty state) but **must** raise on WFS `numberMatched == 0` for a whole LL, which indicates a query bug |

**Reusable verbatim from `build_vector.py`:**
- `_write_geojson()` — `to_json(drop_id=True, sort_keys=True)` + trailing newline (CLAUDE.md rule)
- The write-then-reread validation block (`gpd.read_file(output_path)`, assert non-empty, assert `crs == EPSG:4326`)
- The `[input]` / `[ok]` / `[error]` print-prefix convention
- `argparse` with `--layer` / `--list`
- `_sources.py` helpers: `get_layer()`, `resolve()`, `repo_root()`

**Not reusable:** `ensure_input_available()` (no local file), `vector.gpkg_layer` / `keep_fields`
config (WFS has its own field sets), `_load_semantic_frame()`.

### 4.2 Script sketch

```python
# data-pipeline/python/fetch_protected_areas.py
"""Fetch BfN Schutzgebiete (Natura 2000 SCI/SPA + NSG) per Living Lab via WFS.

Writes data/geojson/protected-areas-{slug}.geojson (EPSG:4326).
Full polygons for every site intersecting the LL boundary (not clipped).
"""
from __future__ import annotations
import argparse, tempfile, time
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from _sources import get_layer, repo_root, resolve

BBOX_PAD_DEG = 0.05          # ~5 km; compensates for WFS edge behaviour
REQUEST_TIMEOUT = 300
RETRIES = 4                  # BfN WAF returns transient 403

BUNDESLAND = {              # BL / Bundesland code -> bilingual authority label
    "BB": ("Brandenburg", "Brandenburg"),
    "HE": ("Hesse", "Hessen"),
    "RP": ("Rhineland-Palatinate", "Rheinland-Pfalz"),
    # ... 13 more
}

# designation key -> (TYPENAMES, name field, area field, year source, bl field,
#                     site-code field, en label, de label)
DESIGNATIONS = { ... }

def _get(params: dict) -> bytes:
    url = LAYER["wfs"]["url"]
    for attempt in range(RETRIES):
        try:
            r = requests.get(url, params=params,
                             headers={"User-Agent": "ll-explorer-pipeline/1.0 (+https://zalf.de)"},
                             timeout=REQUEST_TIMEOUT)
            if r.status_code == 403 and attempt < RETRIES - 1:
                wait = 2 ** attempt
                print(f"  [retry {attempt+1}/{RETRIES-1} in {wait}s] BfN WAF returned 403")
                time.sleep(wait); continue
            r.raise_for_status()
            return r.content
        except requests.RequestException as exc:
            if attempt == RETRIES - 1: raise
            time.sleep(2 ** attempt)
            print(f"  [retry {attempt+1}/{RETRIES-1}] {exc}")

def _bbox_param(geom) -> str:
    minx, miny, maxx, maxy = geom.bounds          # lon/lat, EPSG:4326
    p = BBOX_PAD_DEG
    # lat,lon order is MANDATORY with the urn: CRS form. Any other spelling
    # returns HTTP 200 with zero features and no error.
    return f"{miny-p},{minx-p},{maxy+p},{maxx+p},urn:ogc:def:crs:EPSG::4326"

def _fetch_designation(key, cfg, ll_geom) -> gpd.GeoDataFrame:
    raw = _get({"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature",
                "TYPENAMES": cfg["typename"], "BBOX": _bbox_param(ll_geom),
                "COUNT": 5000})                    # NOTE: no SRSNAME, no OUTPUTFORMAT
    matched  = int(raw.split(b'numberMatched="')[1].split(b'"')[0])
    returned = int(raw.split(b'numberReturned="')[1].split(b'"')[0])
    if matched != returned:
        raise RuntimeError(f"[error] {key}: server truncated {returned}/{matched}; add paging")
    if matched == 0:
        raise RuntimeError(f"[error] {key}: 0 features for bbox — check BBOX axis order/CRS suffix")

    # GDAL writes a .gfs sidecar next to the .gml and caches type inference in it.
    # Use a throwaway temp dir so runs stay deterministic and data/ stays clean.
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"{key}.gml"
        path.write_bytes(raw)
        frame = gpd.read_file(path)

    if str(frame.crs) != "EPSG:25832":
        raise RuntimeError(f"[error] {key}: expected EPSG:25832, got {frame.crs}")
    frame.geometry = frame.geometry.make_valid()   # ~1% invalid on read (CLAUDE.md rule)
    frame = frame.to_crs("EPSG:4326")              # align CRS BEFORE the spatial op
    selected = frame[frame.geometry.intersects(ll_geom)].copy()   # D-03: no clipping
    return _normalise(selected, key, cfg)
```

**`_normalise()` must:**
1. Emit `name`, `name_de`, `name_en`, `designation`, `designation_de`, `designation_en`,
   `area_ha`, `established_year`, `authority`, `site_code`, `ll_slug`.
2. **Coerce every datetime column to `str` (or drop it).** `GeoDataFrame.to_json()` raises
   `TypeError: Object of type Timestamp is not JSON serializable` otherwise — and whether GDAL
   returns `str` or `datetime64` depends on the `.gfs` sidecar state, so this bites
   non-deterministically. [VERIFIED: reproduced live]
3. Cast `numpy.int32` / `numpy.float64` to native Python `int` / `float`, and `NaN` → `None`.
4. Drop `gml_id`, `OBJECTID` and the raw German field names — keep the output contract stable so
   the JSX never branches on source schema.

**Main loop:**
```python
for row in boundaries.itertuples(index=False):
    parts = [_fetch_designation(k, cfg, row.geometry) for k, cfg in DESIGNATIONS.items()]
    merged = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), crs="EPSG:4326")
    merged["ll_slug"] = row.ll_slug
    if not merged.geometry.is_valid.all():
        raise RuntimeError(f"[error] invalid geometries remain for ll_slug='{row.ll_slug}'")
    _write_geojson(merged, output_dir / f"protected-areas-{row.ll_slug}.geojson")
    # then re-read and assert non-empty + crs == EPSG:4326 (copy from build_vector.py)
```

### 4.3 Dependencies

**No new packages required.** `data-pipeline/requirements.txt` already has `geopandas>=0.14`,
`shapely>=2.0`, `requests>=2.31`, `pyyaml>=6.0`, `pytest>=7.0`. Installed and verified working:
GeoPandas 1.1.3, Shapely 2.1.2, Python 3.12, with a working GDAL GML driver.
No `ogr2ogr`, no `owslib`, no new CLI tools. See §Package Legitimacy Audit.

### 4.4 Error handling strategy

| Failure | Detection | Response |
|---|---|---|
| BfN WAF 403 | `status_code == 403` | Exponential-backoff retry ×4, then raise |
| Network timeout | `requests.RequestException` | Same retry loop |
| BBOX spelling bug | `numberMatched == 0` | **Raise** with an explicit "check axis order / urn CRS" message |
| Server truncation | `numberMatched != numberReturned` | Raise, instructing to add `STARTINDEX` paging |
| Wrong CRS from server | `frame.crs != EPSG:25832` | Raise |
| Invalid geometries | `is_valid.all()` after processing | Raise (post-`make_valid()` it should never trigger) |
| Zero features **after** intersect | `len(merged) == 0` | **Warn, do not raise** — UI-SPEC §3.3 defines a legitimate empty state. (In practice all 5 LLs have ≥78 features.) |
| `Timestamp` serialisation | — | Prevented by the `_normalise()` datetime coercion |

**Idempotency / diff noise:** `to_json(sort_keys=True)` plus the pad-and-intersect approach makes
output deterministic *given a stable upstream*. Because the WFS is live, re-running after a BfN
refresh will produce large diffs — that is expected and is the D-04 trade-off. Consider caching raw
GML under `data/_cache/` (already gitignored) so re-runs during development do not re-hit BfN.

---

## 5. Integration with `sync.py` and `sources.yaml`

### 5.1 `sources.yaml` entry — `sync.py` needs zero code changes

`sync_vector_geojson()` iterates layers where `kind == "vector"`, globs
`output.geojson_pattern` with `{slug}` → `*`, and copies each match to
`app/public/<same relative path>`. Declaring the layer as `kind: vector` therefore wires up the
copy automatically. `generate_layer_sources()` picks up any layer with an `app_layer` key and
emits it into `app/src/data/layer_sources.js`, keyed by `appLayer` — which is exactly what
`MapInfoControl` looks up via `LAYER_SOURCE_INDEX.get(layer)`.

```yaml
  - id: bfn-schutzgebiete
    app_layer: protected-areas
    kind: vector
    title:
      en: "Protected areas (BfN, 2019/2023)"
      de: "Schutzgebiete (BfN, 2019/2023)"
    description:
      en: "Natura 2000 sites (SCI and SPA) and German nature reserves intersecting each living lab."
      de: "Natura-2000-Gebiete (FFH und Vogelschutz) und Naturschutzgebiete je Reallabor."
    source:
      provider: "Bundesamt fuer Naturschutz (BfN)"
      dataset: "Schutzgebiete in Deutschland (FFH 2019, Vogelschutz 2019, Naturschutzgebiete 2023)"
      url: "https://geodienste.bfn.de/schutzgebiete"
      metadata: "https://gdk.gdi-de.org/geonetwork/srv/api/records/bec888f9-ba0c-42dc-846e-177b8265dafa"
      license: "Nutzungsbestimmungen fuer die Bereitstellung von Geodaten des Bundes (GeoNutzV)"
      attribution: "Datenquelle: Bundesamt fuer Naturschutz (BfN)"
      citation: "BfN: Schutzgebiete in Deutschland. https://geodienste.bfn.de/schutzgebiete"
      note: "Nicht fuer Planungszwecke geeignet."
    build:
      script: python/fetch_protected_areas.py
    wfs:
      url: "https://geodienste.bfn.de/ogc/wfs/schutzgebiet"
      version: "2.0.0"
      source_crs: "EPSG:25832"
      bbox_crs: "urn:ogc:def:crs:EPSG::4326"   # lat,lon order — see 05-RESEARCH.md 3.2
      bbox_pad_deg: 0.05
      output_format: gml32                      # NOT geojson — drops edge features
      count: 5000
      typenames:
        natura2000-sci: "bfn_sch_Schutzgebiet:Fauna_Flora_Habitat_Gebiete"
        natura2000-spa: "bfn_sch_Schutzgebiet:Vogelschutzgebiete"
        naturschutzgebiet: "bfn_sch_Schutzgebiet:Naturschutzgebiete"
      output_dir: data/geojson
    output:
      geojson_pattern: "data/geojson/protected-areas-{slug}.geojson"
```

**One caveat:** `build_vector.py --list` filters on `kind == "vector"` and would now list
`bfn-schutzgebiete` as if it were buildable by that script. `build_vector.py` already raises a clear
error (`missing vector.gpkg_layer`) if invoked on it. Optional polish: have `list_layers()` print
the `build.script` alongside the id.

### 5.2 App-side changes

**`app/src/data/layers.js`** — add one entry. **Corrected during planning:** the entry goes into a new
`OVERLAYS` array, *not* `LAYERS`, so it never becomes an exclusive tab (see the Architectural
Responsibility Map above and 05-02-PLAN.md Task 1). `LAYER_INDEX` becomes the union of both arrays so
`resolveLayerAsset`, `MapLegend` and `MapInfoControl` keep resolving it:
```js
{
  id: 'protected-areas',
  type: 'vector',
  pmtilesUrl: null,
  geojsonPathPattern: 'data/geojson/protected-areas-{slug}.geojson',
  legend: PROTECTED_AREAS_LEGEND,      // static 3-entry list; see UI-SPEC 2.6
  legendNoteKey: 'legend.protectedAreas.note',
  available: true,
},
```
`resolveLayerAsset()` already handles `type === 'vector' && geojsonPathPattern && slug`.

**`app/src/components/LLMap/index.jsx`** — three corrections the planner must apply to the
UI-SPEC snippets:

1. **`useGeoJSON` returns an array.** `05-UI-SPEC.md` §6.1 uses `protectedAreasState.data`
   directly as the `<GeoJSON data=…>` prop. That is wrong — the hook returns
   `{ data: [collection], loading, error }`. Follow the existing soil pattern:
   ```js
   const protectedAreasFeatureCollection = useMemo(
     () => (Array.isArray(protectedAreasState.data) ? protectedAreasState.data[0] ?? null : null),
     [protectedAreasState.data],
   )
   ```

2. **The existing soil render/badge/legend blocks are gated on `layerConfig?.type === 'vector'`**
   (lines 558, 569, 570) — a *type* check, not an *id* check. Adding a second vector layer makes
   the soil branch fire for protected-areas and vice versa. All five sites must be narrowed to
   `layer === 'soil'` / `layer === 'protected-areas'`. Line 575 likewise passes
   `note={t('legend.soil.note')}` unconditionally.

3. **Use the Canvas renderer** (see Pitfall 12). **Corrected during planning:** do *not* use
   react-leaflet's `<GeoJSON>` for this layer. React-leaflet may reorder sibling children when
   layers mount and unmount, which would let the white LL mask bury the overlay. Build it
   imperatively instead, mirroring the existing `RasterPmtilesLayer`: inside a `useMap()` +
   `useEffect`, call `map.createPane('protectedAreasPane')` and set its `zIndex` to 450, create
   `L.canvas({ padding: 0.5, pane: 'protectedAreasPane' })`, then `L.geoJSON(collection, { pane,
   renderer, style: getProtectedAreasStyle, onEachFeature })` and `addTo(map)`, returning
   `map.removeLayer(layer)` as cleanup. See 05-03-PLAN.md Task 2.

**`app/src/components/MapLegend.jsx`** — no change needed. It already accepts an `entries` array of
`{ value, en, de, color }` and renders `entry[lang] || entry.en`, plus a `note`.

**`app/src/i18n.js`** — add the keys from UI-SPEC §5, with the LAWA correction from §1.3 above.

**`app/src/components/LayerTabs.jsx`** — no change, and **no new tab**. It maps over `LAYERS`,
which stays tab-only. **Corrected during planning:** the overlay toggle renders as an in-map control
at the top-right of the map (`ProtectedAreasToggle` in `LLMap`), independent of whichever tab is
active, so there is no tab-order question to answer.

### 5.3 Repository size impact

`data/geojson/*` and `app/public/data/geojson/*` are **both tracked in git** (the pipeline commits
each file twice). Current geodata footprint: BUEK250 5.7 MB ×2 + a 37.6 MB PMTiles archive; `.git`
is already 725 MB.

| Precision | Per-LL max | Total | Committed (×2) |
|---|---|---|---|
| Raw (`to_json()` default) | 12.55 MB | 40.41 MB | **80.8 MB** |
| `set_precision(1e-6)` (≈0.11 m) | 7.42 MB | 23.58 MB | 47.2 MB |
| `set_precision(1e-5)` (≈1.1 m) | 6.80 MB | 20.84 MB | 41.7 MB |

Both precision levels lose **zero** features. See Pitfall 13 for the D-08 interaction.
Gzip over HTTP reduces the browser fetch to 0.42–2.00 MB per LL regardless — but static hosts do
not always gzip `.geojson`; verify the deployment target's MIME/compression config.

---

## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---|---|---|---|
| Parsing the WFS GML response | A regex/ElementTree GML reader | `gpd.read_file(path_to_gml)` | GDAL's GML driver handles `MultiSurface`→`MultiPolygon`, `srsName` per geometry, EPSG:25832 detection, and the bogus `gis-shost:6443` namespace. **Verified: 82/82 rows, correct CRS, correct dtypes** |
| Reprojecting 25832 → 4326 | Manual UTM math, or `SRSNAME` on the WFS | `frame.to_crs("EPSG:4326")` | `SRSNAME` on this server either returns 0 features (25832) or emits lat,lon GeoJSON (4326). PyPROJ is correct and free |
| "Does this site touch the LL?" | Bbox-overlap arithmetic, point-in-polygon loops | `frame[frame.geometry.intersects(ll_geom)]` | GEOS predicate; bbox overlap over-selects by ~2× (measured: 545 bbox hits → 186 true intersections for east-brandenburg SCI) |
| Repairing self-intersecting rings | Buffer(0) tricks, ring rewinding | `geometry.make_valid()` | CLAUDE.md mandates it; ~1 % of BfN features need it |
| Coordinate rounding | `round()` on nested coordinate lists | `shapely.set_precision(geom, grid_size=…)` | Topology-aware; `build_vector.py` already uses it |
| Copying outputs into `app/public/` | A bespoke copy step | `sync.py::sync_vector_geojson()` | Already globs `output.geojson_pattern` for every `kind: vector` layer |
| Source/licence metadata for the info control | Hand-written JS constants | `sync.py::generate_layer_sources()` + `app_layer` key | Codegen keeps `sources.yaml` the single source of truth |
| Lazy-load + de-dup fetch | New fetch logic in `LLMap` | `useGeoJSON` hook | Module-level `cache` + `inflight` Maps already implement D-07 exactly |
| Rendering 300 k vertices fast | Custom tiling, feature culling, web workers | `L.canvas()` renderer | One prop. Not simplification, so D-08 is preserved |
| Retry/backoff for the BfN WAF | A bare `try/except: pass` | The `_post()` backoff pattern from `fetch_destatis.py` | Existing in-repo precedent (lines 119-130) |

**Key insight:** every hard part of this phase — GML parsing, CRS transforms, geometry repair,
spatial predicates, asset sync, lazy loading — is already solved by a dependency or by existing
project code. The genuinely novel work is *exactly three things*: the WFS query parameter spelling,
the 3-schema→1-contract normalisation, and the Canvas renderer swap.

---

## Common Pitfalls

### Pitfall 1: BBOX axis order — silent empty output
**What goes wrong:** Five valid-looking GeoJSON files containing `{"type":"FeatureCollection","features":[]}`.
**Why:** The service accepts *only* `lat,lon` order with an explicit `urn:ogc:def:crs:EPSG::4326`
suffix. Lon,lat order, plain `EPSG:4326`, native `EPSG:25832`, and no-suffix all return **HTTP 200
with zero features and no error message.**
**Avoid:** Format the bbox as `f"{miny},{minx},{maxy},{maxx},urn:ogc:def:crs:EPSG::4326"` and assert
`numberMatched > 0` before writing anything.
**Warning sign:** Any per-LL feature count of 0. Expected minimum is 78 (Rheingau).

### Pitfall 2: `OUTPUTFORMAT=GEOJSON` silently drops features
**What goes wrong:** 80 of 82 matched features written; no warning.
**Why:** The ArcGIS GeoJSON writer re-applies the spatial filter after reprojection with different
edge arithmetic, discarding features near the bbox boundary.
**Avoid:** Use the default GML 3.2 output and read it with `gpd.read_file()`.
**Warning sign:** `numberMatched != len(frame)`. Assert this every request.

### Pitfall 3: `SRSNAME` flips GeoJSON axis order
**What goes wrong:** `[50.065, 7.851]` instead of `[7.851, 50.065]` — every polygon lands in
Kazakhstan; `intersects()` returns 0 everywhere.
**Why:** With `SRSNAME=EPSG:4326` **or** `SRSNAME=urn:ogc:def:crs:EPSG::4326`, the writer honours the
EPSG authority axis order (lat,lon), violating RFC 7946. Omitting `SRSNAME` produces correct lon,lat.
`SRSNAME=EPSG:25832` returns 0 features.
**Avoid:** Never send `SRSNAME`. Reproject in GeoPandas.
**Warning sign:** `frame.total_bounds` with `minx > 45`.

### Pitfall 4: `Timestamp is not JSON serializable`
**What goes wrong:** `TypeError: Object of type Timestamp is not JSON serializable` from
`GeoDataFrame.to_json()` — sometimes. On other runs the same file reads back as `str` and works.
**Why:** GDAL's GML driver caches type inference in a `.gfs` sidecar written next to the `.gml`.
Whether `LEG_DATE` / `Datum_der_gueltigen_Verordnung` comes back as `object` or `datetime64[ns]`
depends on whether that sidecar exists and what it says.
**Avoid:** Write the GML into a `tempfile.TemporaryDirectory()` (also keeps `.gfs` files out of
`data/`) **and** unconditionally coerce datetime columns to strings in `_normalise()`.
**Warning sign:** Stray `*.gfs` files appearing in the repo; the bug reproducing only on second runs.

### Pitfall 5: Transient HTTP 403 from the BfN WAF
**What goes wrong:** `GetCapabilities` returns a German `403 - Zugriff verweigert | BFN` HTML page.
**Why:** A WAF in front of `geodienste.bfn.de` intermittently blocks. It is **not** User-Agent
based — the identical request succeeded seconds later with curl's default UA, `python-urllib/3.12`,
and a browser UA.
**Avoid:** Exponential-backoff retry (mirror `fetch_destatis.py::_post`). Do not spoof a browser UA —
send an honest identifying UA.
**Warning sign:** A 7,410-byte HTML body where XML was expected.

### Pitfall 6: Clipping instead of filtering (violates D-03)
**What goes wrong:** Protected areas appear cut off at the LL boundary.
**Why:** `build_vector.py` uses `gpd.clip()` and is the natural copy-paste source.
**Avoid:** `frame[frame.geometry.intersects(ll_geom)]` — boolean mask, geometry untouched.
**Warning sign:** Polygon edges tracing the LL outline exactly.

### Pitfall 7: `build_vector.py`'s `raise on empty clip` copied verbatim
**What goes wrong:** The pipeline aborts on a legitimately empty LL.
**Why:** BUEK250 covers all of Germany so 0 features always means a bug; protected areas may
legitimately be absent, and UI-SPEC §3.3 defines an empty state.
**Avoid:** Raise on `numberMatched == 0` (query bug); warn on `len(after_intersect) == 0`.

### Pitfall 8: Skipping `make_valid()`
**What goes wrong:** `intersects()` throws `TopologyException`, or silently mis-selects.
**Why:** ~1 % of BfN polygons are invalid on read (measured: SCI 540/545, SPA 44/46).
**Avoid:** `frame.geometry = frame.geometry.make_valid()` immediately after `read_file()`, and
assert `is_valid.all()` before writing. CLAUDE.md already mandates this.

### Pitfall 9: Assuming a bilingual schema
**What goes wrong:** `name_en` ends up `null` and English tooltips show blanks.
**Why:** BfN publishes **German names only** across all three layers.
**Avoid:** Set `name_en = name_de`. `getLocalizedValue()` (LLMap line 97) already falls back
cross-language, so blanks only occur if the field is omitted entirely.

### Pitfall 10: The three BfN schemas are not interchangeable
**What goes wrong:** `KeyError: 'NAME'` on the FFH layer.
**Why:** FFH uses long German names (`Gebietsname`, `BfN-ID`, `Bundesland`); SPA/NSG use
SHORTCAPS (`NAME`, `BFN_ID`, `BL`). FFH's site-URL column is misnamed `Wasserrahmenrichtlinie_`.
NSG has `JAHR`/`IUCN_KAT`/`CDDA_CODE` that the others lack; SPA/FFH have `BIOGEO`/
`Biogeographische_Region` that NSG lacks.
**Avoid:** A per-designation field-mapping dict; never index a shared column name.

### Pitfall 11: `layerConfig?.type === 'vector'` gates in `LLMap`
**What goes wrong:** Selecting the protected-areas tab renders the *soil* GeoJSON, shows
`map.soilLoading`, and prints the soil legend note — because five call sites branch on layer
**type**, not layer **id**.
**Avoid:** Narrow lines 558, 569, 570, 575 (and the `soilUrl` memo, line 495) to `layer === 'soil'`.

### Pitfall 12: SVG renderer at 300 k vertices
**What goes wrong:** Selecting the tab for East Brandenburg freezes the tab for seconds; pan/zoom
becomes unusable.
**Why:** Leaflet's default renderer creates one SVG `<path>` element per feature; the browser
layout/paint cost scales with total vertex count. Measured worst case: **311,616 vertices in 355
features** in one LL.
**Avoid:** render with an `L.canvas({ padding: 0.5 })` renderer instead of the default SVG one.
This changes only the rasterisation backend — geometry is unmodified, so **D-08 is fully
preserved.** Tooltips and `onEachFeature` continue to work with Canvas.
**Corrected during planning 2026-07-25:** the original wording here recommended passing
`renderer={...}` to react-leaflet's `<GeoJSON>`, or setting `preferCanvas` on `<MapContainer>`.
Both are superseded. Use the imperative `ProtectedAreasLayer` form in the Code Examples section:
a `useMap()` + `useEffect` that creates a dedicated `protectedAreasPane` at `zIndex 450`, binds
`L.canvas({ padding: 0.5, pane: 'protectedAreasPane' })` to it, and adds an `L.geoJSON` layer.
React-leaflet may reorder sibling children on mount/unmount, which would let the white LL mask
bury the overlay; a dedicated pane makes D-06 structural. See 05-03-PLAN.md Task 2.
Trade-off: Canvas paths have no CSS `:hover`, so the UI-SPEC §2.3 hover emphasis must be implemented
via `layer.on('mouseover', () => layer.setStyle(...))` rather than CSS.
[CITED: leafletjs.com/reference.html#path-renderer — `preferCanvas` default `false`, "whether Paths should be rendered on a Canvas renderer"]

### Pitfall 13: D-08 vs. file size — decision required
**What goes wrong:** 80.8 MB of new binary-ish content committed to a repo whose `.git` is already 725 MB.
**Why:** D-08 forbids simplification/downsampling, and full-precision `to_json()` writes ~15
significant digits per ordinate.
**Nuance:** `set_precision(grid_size=1e-6)` is **coordinate rounding to ~11 cm**, not simplification —
no vertices are removed, no features lost (verified: 1,248/1,248 kept at both 1e-6 and 1e-5). It cuts
the total from 40.4 MB to 23.6 MB. Project precedent exists: `build_vector.py` applies
`set_precision(0.0001)` (~11 m) to BUEK250.
**Recommendation:** Apply `set_precision(1e-6)` and record it in `sources.yaml` as
`coordinate_precision: 0.000001`. **Resolved during planning 2026-07-25:** rounding is coordinate
adjustment rather than vertex removal, so every option is D-08-compliant, but the committed size
varies by 39 MB across them — so the choice is escalated to a blocking `checkpoint:decision` at
05-01-PLAN.md Task 0, before any fetch runs. The selected literal is written to
`sources.yaml` as `wfs.coordinate_precision` (`null` = raw, the strict reading of D-08).

### Pitfall 14: Data vintage is stale and legally caveated
**What goes wrong:** Users treat 2019 Natura 2000 boundaries as current, or use the map for planning.
**Why:** FFH/VSG = 2019, NSG = 2023; BfN explicitly states *"Nicht für Planungszwecke geeignet."*
**Avoid:** Put the vintage in `sources.yaml` `title` (already drafted as "BfN, 2019/2023") so it
surfaces in `MapInfoControl`, and consider appending the planning caveat to the legend note.

---

## Code Examples

### Fetching one designation for one Living Lab (verified working)

```python
# Source: executed live against https://geodienste.bfn.de/ogc/wfs/schutzgebiet on 2026-07-25
import tempfile
from pathlib import Path
import geopandas as gpd
import requests

BASE = "https://geodienste.bfn.de/ogc/wfs/schutzgebiet"
PAD = 0.05

boundaries = gpd.read_file("data/ll_boundaries.geojson")          # EPSG:4326
row = boundaries[boundaries.ll_slug == "rheingau"].iloc[0]
minx, miny, maxx, maxy = row.geometry.bounds                       # lon/lat

# lat,lon order + urn: CRS is MANDATORY. Any other form -> HTTP 200, zero features.
bbox = f"{miny-PAD},{minx-PAD},{maxy+PAD},{maxx+PAD},urn:ogc:def:crs:EPSG::4326"

resp = requests.get(BASE, params={
    "SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature",
    "TYPENAMES": "bfn_sch_Schutzgebiet:Naturschutzgebiete",
    "BBOX": bbox, "COUNT": 5000,
    # deliberately NO SRSNAME (flips axis order) and NO OUTPUTFORMAT (drops edge features)
}, headers={"User-Agent": "ll-explorer-pipeline/1.0 (+https://zalf.de)"}, timeout=300)
resp.raise_for_status()
raw = resp.content

matched  = int(raw.split(b'numberMatched="')[1].split(b'"')[0])    # 117
returned = int(raw.split(b'numberReturned="')[1].split(b'"')[0])   # 117
assert matched == returned and matched > 0

with tempfile.TemporaryDirectory() as tmp:                          # keeps .gfs out of data/
    p = Path(tmp) / "nsg.gml"
    p.write_bytes(raw)
    frame = gpd.read_file(p)

assert str(frame.crs) == "EPSG:25832"
frame.geometry = frame.geometry.make_valid()                        # ~1% invalid on read
frame = frame.to_crs("EPSG:4326")                                   # align CRS before predicate
selected = frame[frame.geometry.intersects(row.geometry)]           # D-03: filter, don't clip
# -> 41 features, full polygons, all valid
```

### Checking the count / hits before a full fetch

```python
# RESULTTYPE=hits returns a ~900-byte header-only response — cheap pre-flight
params = {"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature",
          "TYPENAMES": typename, "BBOX": bbox, "RESULTTYPE": "hits"}
# -> <wfs:FeatureCollection ... numberMatched="117" numberReturned="0" ...>
```

### Normalising the three schemas (pattern)

```python
DESIGNATIONS = {
    "natura2000-sci": {
        "typename": "bfn_sch_Schutzgebiet:Fauna_Flora_Habitat_Gebiete",
        "name": "Gebietsname", "state": "Bundesland", "site_code": "Gebietsnummer",
        "date": "Datum_der_gueltigen_Verordnung", "year": None,
        "label": ("Natura 2000 SCI", "Special Conservation Area", "FFH-Gebiet"),
    },
    "natura2000-spa": {
        "typename": "bfn_sch_Schutzgebiet:Vogelschutzgebiete",
        "name": "NAME", "state": "BL", "site_code": "SITECODE",
        "date": "LEG_DATE", "year": None,
        "label": ("Natura 2000 SPA", "Special Protection Area", "Vogelschutzgebiet"),
    },
    "naturschutzgebiet": {
        "typename": "bfn_sch_Schutzgebiet:Naturschutzgebiete",
        "name": "NAME", "state": "BL", "site_code": "ID",
        "date": "LEG_DATE", "year": "JAHR",
        "label": ("Naturschutzgebiet", "Nature Reserve", "Naturschutzgebiet"),
    },
}
```

### Canvas renderer in a dedicated pane (imperative — supersedes the react-leaflet form)

**Corrected during planning 2026-07-25.** The original draft of this section used react-leaflet's
`<GeoJSON>` with a shared module-level renderer. Two defects: a module-level renderer instance is
shared across every mounted map (`LLDetail` renders `LLMap` from two layout branches), and child
order in JSX does not reliably determine Leaflet stacking. The shipped form is imperative and
pane-based:

```jsx
function ProtectedAreasLayer({ collection, slugKey, t, lang }) {
  const map = useMap()
  useEffect(() => {
    if (!map.getPane('protectedAreasPane')) {
      map.createPane('protectedAreasPane').style.zIndex = 450   // > overlayPane (400) > tilePane (200)
    }
    const renderer = L.canvas({ padding: 0.5, pane: 'protectedAreasPane' })
    const layer = L.geoJSON(collection, {
      pane: 'protectedAreasPane',
      renderer,
      style: getProtectedAreasStyle,
      onEachFeature: (feature, featureLayer) => {
        bindProtectedAreasTooltip(feature, featureLayer, t, lang)
        // Canvas has no CSS :hover — wire emphasis explicitly (UI-SPEC 2.3)
        featureLayer.on('mouseover', () => featureLayer.setStyle(PROTECTED_AREAS_HOVER_STYLE))
        featureLayer.on('mouseout', () => featureLayer.setStyle(getProtectedAreasStyle(feature)))
      },
    }).addTo(map)
    return () => { map.removeLayer(layer) }
  }, [collection, slugKey, map, t, lang])
  return null
}
// caller passes protectedAreasState.data[0] — the hook returns an array
```

---

## Runtime State Inventory

*(Included because this phase adds committed data artefacts and a live external dependency, even
though it is not a rename/refactor.)*

| Category | Items found | Action required |
|---|---|---|
| Stored data | None — no database in this project. New committed artefacts: `data/geojson/protected-areas-{slug}.geojson` ×5 and their `app/public/` copies ×5 | New files only; nothing to migrate |
| Live service config | **BfN WFS `geodienste.bfn.de/ogc/wfs/schutzgebiet`** — external, unversioned, no SLA. Endpoint/typenames change independently of this repo. Recorded in `sources.yaml` | Pin typenames in `sources.yaml`; add a contract test asserting the layer entry (mirrors `test_buek250_layer_contract_declared`) |
| OS-registered state | None — verified: no scheduled tasks, no services; pipeline is run manually per CLAUDE.md quick start | None |
| Secrets / env vars | **None** — BfN WFS requires no auth (`Es gelten keine Zugriffsbeschränkungen`). Contrast with `fetch_destatis.py`, which needs `.env` credentials | None. Do not add `.env` entries |
| Build artefacts | GDAL writes `*.gfs` sidecars next to any `.gml` it reads; `.gitignore` has no `*.gfs` rule | Use `tempfile.TemporaryDirectory()` (preferred) **or** add `*.gfs` to `.gitignore` |

---

## Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|---|---|---|---|---|
| Python | pipeline | ✓ | 3.12 (`data-pipeline/.venv`) | — |
| `geopandas` | GML read, reproject, intersect | ✓ | 1.1.3 | — |
| `shapely` | `make_valid`, `set_precision` | ✓ | 2.1.2 | — |
| GDAL GML driver | reading WFS GML 3.2 | ✓ | bundled with GeoPandas/pyogrio; **read 82/82 rows with correct CRS** | `OUTPUTFORMAT=GEOJSON` + manual parse (worse — drops features) |
| `requests` | WFS HTTP | ✓ | ≥2.31 in requirements.txt | `urllib.request` (also verified working) |
| `pyyaml` | `sources.yaml` | ✓ | ≥6.0 | — |
| `pytest` | pipeline contract tests | ✓ | ≥7.0, `data-pipeline/tests/` exists | — |
| Network → `geodienste.bfn.de` | live WFS (D-04) | ✓ | HTTPS 200, ~70 MB/33 s | none — phase cannot complete offline |
| `leaflet` | Canvas renderer | ✓ | ^1.9.4 (`L.canvas` present since 1.0) | — |
| `react-leaflet` | `renderer` prop pass-through | ✓ | ^5.0.0 | direct `L.geoJSON` in a `useMap()` effect |
| `pmtiles` CLI / `rio` | **not needed** — vector phase | n/a | — | — |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none.

---

## Package Legitimacy Audit

**No new packages are introduced by this phase.** Every library required
(`geopandas`, `shapely`, `requests`, `pyyaml`, `pytest`) is already declared in
`data-pipeline/requirements.txt` and installed in the project virtualenv; every frontend library
(`leaflet`, `react-leaflet`, `react`, `i18next`) is already in `app/package.json`.

| Package | Registry | Status in repo | Disposition |
|---|---|---|---|
| `geopandas` | PyPI | already in `requirements.txt`, installed 1.1.3 | Approved (no change) |
| `shapely` | PyPI | already in `requirements.txt`, installed 2.1.2 | Approved (no change) |
| `requests` | PyPI | already in `requirements.txt` | Approved (no change) |
| `pyyaml` | PyPI | already in `requirements.txt` | Approved (no change) |
| `leaflet` | npm | already in `app/package.json` `^1.9.4` | Approved (no change) |
| `react-leaflet` | npm | already in `app/package.json` `^5.0.0` | Approved (no change) |

**Packages removed due to slopcheck `[SLOP]` verdict:** none — no new packages proposed.
**Packages flagged `[SUS]`:** none.

`slopcheck` was **not run** because the phase adds zero new dependencies; the audit surface is empty.
If the planner introduces a new package (e.g. `owslib` for WFS — **not recommended**, see
*Don't Hand-Roll*), the Package Legitimacy Gate must be run before that install.

---

## State of the Art

| Old approach | Current approach | When changed | Impact |
|---|---|---|---|
| Manual download + commit of a national geodata archive (BUEK250, Phase 2) | Live WFS GetFeature at pipeline runtime | This phase (D-04) | No 100 MB source archive in `.gitignore`; but adds an external runtime dependency and non-reproducible output |
| `gpd.clip()` to the LL boundary | `intersects()` boolean filter | This phase (D-03) | Full site polygons extend past the LL outline — deliberate context cue |
| Leaflet SVG renderer (soil layer, ≤ 35 features/LL) | Leaflet Canvas renderer | This phase | Required at 78–362 features / 70 k–312 k vertices |
| Per-state NSG registries (16 different schemas) | BfN federal harmonisation | ongoing, annual | One endpoint, three typenames, boundaries snapped to BKG VG25 state borders |

**Deprecated / not applicable:**
- **LAWA as a nature-reserve source** — never was one; remove from `05-UI-SPEC.md` §4.1 and the
  `map.info.protectedAreasProvider` i18n strings.
- **WFS 1.1.0 `maxFeatures` / `typeName` (singular)** — this service is WFS 2.0.0; use `COUNT`
  and `TYPENAMES`.
- **`gpd.read_file(wfs_url)` via the OGR WFS driver** — not tested here and would re-introduce the
  bbox/SRSNAME ambiguity. Fetch with `requests`, read from a temp file.

---

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|---|---|---|
| A1 | `set_precision(1e-6)` counts as "rounding", not "simplification/downsampling", and is therefore compatible with D-08 | Pitfall 13, §5.3 | If the user reads D-08 strictly, committed size doubles to 80.8 MB. **Confirm with user.** |
| A2 | `L.canvas()` satisfies D-08 (rendering backend change, geometry untouched) | Pitfall 12 | If rejected, the East Brandenburg tab will be effectively unusable at 311 k vertices |
| A3 | The `authority` field should be derived from the `BL`/`Bundesland` code rather than hard-coded to "BfN" | §2.2 | Tooltip shows a state name where the user expected the federal agency; trivial to flip |
| A4 | The Natura 2000 2019 vintage is acceptable for a contextual overlay | §1.2 | If current boundaries are required, the phase would need 5+ per-state WFS endpoints — a much larger scope |
| A5 | Feature counts and file sizes are stable — measured on 2026-07-25 against a live service | §2.3 | BfN could publish a refresh; counts would shift but the method holds |
| A6 | The intermittent 403 is a transient WAF, not a rate limit | §1.5 | If it is actually rate limiting, the retry loop still handles it, just more slowly |
| A7 | Static hosting will gzip `.geojson` responses | §5.3 | Without gzip, browser fetch is 1.6–7.4 MB instead of 0.4–2.0 MB per LL |
| A8 | Phase 5 has no `REQ-` IDs and D-01…D-08 serve as traceability anchors | phase_requirements | Planner may need to author `PROTECTED-0x` IDs in REQUIREMENTS.md first |

---

## Open Questions (RESOLVED)

*All five questions were answered during Phase 5 planning on 2026-07-25. Nothing in this section
remains open; each answer is carried into a specific plan task.*

1. **Does D-08 forbid coordinate rounding, or only vertex removal?** **(RESOLVED: rounding is
   coordinate adjustment, not vertex removal, and is compatible with D-08 per the user.)**
   - What we know: `set_precision(1e-6)` keeps all 1,248 features and every vertex; it only truncates
     ordinates to ~11 cm. It cuts committed size from 80.8 MB to 47.2 MB. `build_vector.py` already
     applies a 100x coarser `set_precision(0.0001)` to BUEK250.
   - Resolution: rounding does not violate D-08, because D-08 forbids *simplification and
     downsampling* (removing geometry), and rounding removes neither vertices nor features.
   - Because the committed size varies by 39 MB across the admissible options, the *choice of
     precision* is nevertheless a developer decision rather than a planner one. It is presented as a
     blocking `checkpoint:decision` at the START of 05-01-PLAN.md (Task 0), before any fetch runs, so
     the outcome is never baked into git history unreviewed. The chosen value is recorded in
     `sources.yaml` as `wfs.coordinate_precision` (`null` = raw).

2. **Should the six other BfN designations be structured for, even if not shipped?**
   **(RESOLVED: yes — structured for, not shipped.)**
   - `Nationalparke`, `Naturparke`, `Biosphaerenreservate`, `Nationale_Naturmonumente` and
     `Landschaftsschutzgebiete` live on the same endpoint with the same query form.
   - Resolution: only the three designations named by D-01/D-02 ship. `DESIGNATIONS` is keyed off
     `sources.yaml` `wfs.typenames`, so adding a fourth later is a YAML edit plus one dict entry.
     Implemented in 05-01-PLAN.md Task 2.

3. **Where does the protected-areas tab go in the tab order?** **(RESOLVED: there is no tab.)**
   - Resolution: superseded. `LayerTabs` is exclusive, so a protected-areas tab would hide land-use
     and make D-06 unimplementable. The layer ships as an independent overlay registered in a new
     `OVERLAYS` array with an in-map toggle; `LayerTabs.jsx` is untouched. Confirmed with the
     developer via the `checkpoint:decision` in 05-02-PLAN.md Task 1. See the Architectural
     Responsibility Map above.

4. **Is the pipeline expected to be re-runnable in CI, or developer-machine only?**
   **(RESOLVED: developer machine only; outputs stay committed.)**
   - Resolution: `fetch_protected_areas.py` is a manual refresh tool matching the `fetch_nuts.py`
     "run once after editing" model. Outputs are committed (as BUEK250 is) so the app builds offline
     and CI never depends on BfN availability. No CI job invokes it.

5. **Should `data/_cache/` hold the raw GML between runs?** **(RESOLVED: yes, with a `--refresh`
   bypass flag.)**
   - Resolution: raw GML is cached under `data/_cache/protected-areas/` (already gitignored) and
     re-used unless `--refresh` is passed. Implemented in 05-01-PLAN.md Task 2. The flag is named
     `--refresh` rather than the originally suggested `--no-cache` so the default path is the cheap
     one and refreshing is the explicit act.

**Related assumption-log entries also resolved:** A1 (see question 1), A2 (`L.canvas()` accepted as
a rasterisation-backend change that leaves geometry untouched, so D-08 holds), A4 (the 2019 Natura
2000 vintage is acceptable for a contextual overlay, and the vintage plus the BfN "not suitable for
planning purposes" constraint are surfaced in the legend note), A8 (no `PROTECTED-0x` IDs are
authored; D-01..D-08 are the traceability anchor, recorded in the ROADMAP Phase 5 entry).

---

## Security Domain

No `security_enforcement` key is present in `.planning/config.json`; treating as enabled.
This phase has a small but non-empty security surface: it introduces the project's first
**unauthenticated outbound HTTP fetch whose response is parsed by a native library (GDAL)**.

### Applicable ASVS categories

| ASVS category | Applies | Standard control |
|---|---|---|
| V2 Authentication | no | BfN WFS is public; no credentials introduced. Explicitly *do not* add `.env` entries |
| V3 Session Management | no | No sessions; static SPA |
| V4 Access Control | no | All data is public, licence-permitted (GeoNutzV) |
| V5 Input Validation | **yes** | WFS response is untrusted input. Validate `numberMatched == numberReturned`, `crs == EPSG:25832`, geometry types ∈ {Polygon, MultiPolygon}, `is_valid.all()` before writing. Cap response size |
| V6 Cryptography | no | No crypto. **HTTPS is mandatory** — never downgrade the endpoint to `http://` |
| V12 Files & Resources | **yes** | GML is written to disk before GDAL parses it. Use `tempfile.TemporaryDirectory()`, never a predictable path in `/tmp` or `data/` |
| V14 Configuration | **yes** | Endpoint URL and typenames belong in `sources.yaml` (reviewable, diffable), not hard-coded strings scattered in Python |

### Known threat patterns for this stack

| Pattern | STRIDE | Standard mitigation |
|---|---|---|
| XXE / entity expansion in the GML response | Tampering, DoS | GDAL's GML driver does not resolve external entities by default. Do **not** add a hand-rolled `xml.etree`/`lxml` parser with `resolve_entities=True`. The `numberMatched` extraction in the sketch uses byte-slicing, not XML parsing — keep it that way |
| Endpoint hijack / MITM | Spoofing, Tampering | HTTPS only; `requests` verifies certificates by default — never pass `verify=False` |
| Uncontrolled response size → memory exhaustion | DoS | Largest observed response is 14.57 MB. Assert `len(raw) < 100 * 1024 * 1024` before writing |
| Untrusted attribute values rendered into tooltips | XSS (browser tier) | `createTooltipRow()` (LLMap line 177) uses `textContent`, **not** `innerHTML` — safe. Any refactor to template strings + `innerHTML` would introduce stored XSS from BfN's `LEG_TITEL` / `Bezeichnung_der_gueltigen_Verordnung` free-text fields |
| Untrusted URL in attributes used as an `href` | Open redirect / `javascript:` URI | If `source_url` (`LEG_LINK`, `LINK`) is ever surfaced as a link (deferred per CONTEXT), validate the scheme is `https:` before rendering |
| Path traversal via `ll_slug` in the output filename | Tampering | `ll_slug` comes from the repo-owned `data/ll_boundaries.geojson`, not user input. Still, build paths with `output_dir / f"protected-areas-{slug}.geojson"` and never `os.path.join` on a raw pattern |
| Dependency confusion / slopsquatting | Tampering | Zero new packages — surface is empty. See Package Legitimacy Audit |

---

## Sources

### Primary (HIGH confidence — executed live 2026-07-25)
- `https://geodienste.bfn.de/ogc/wfs/schutzgebiet?SERVICE=WFS&REQUEST=GetCapabilities&VERSION=2.0.0` — feature types, CRS, output formats, `CountDefault`, licence, access constraints
- `…&REQUEST=DescribeFeatureType&TYPENAMES=…` ×3 — full attribute schemas for FFH / VSG / NSG
- `…&REQUEST=GetFeature&BBOX=…&RESULTTYPE=hits` ×15 — `numberMatched` per LL × designation
- `…&REQUEST=GetFeature&BBOX=…` (GML32) ×15 — full end-to-end fetch, parse, `make_valid`, reproject, intersect, write; 1,248 features, 33 s
- Controlled A/B experiments: BBOX CRS-suffix ×4, `SRSNAME` ×4, `OUTPUTFORMAT` GML vs GEOJSON, `COUNT`/`STARTINDEX` paging, padded vs unpadded bbox, User-Agent ×3
- Repo files read: `data-pipeline/python/build_vector.py`, `_sources.py`, `sync.py`, `fetch_nuts.py`, `fetch_destatis.py`, `sources/sources.yaml`, `tests/test_pipeline_outputs.py`, `tests/conftest.py`, `app/src/data/layers.js`, `layer_sources.js`, `app/src/components/LLMap/index.jsx`, `LayerTabs.jsx`, `MapLegend.jsx`, `app/src/hooks/useGeoJSON.js`, `app/package.json`, `data/ll_boundaries.geojson`, `data/ll_metadata.json`, `data/variables_catalogue.xlsx` (`source_catalogue` sheet), `.planning/config.json`, `.gitignore`
- Environment probes: GeoPandas 1.1.3 / Shapely 2.1.2 / Python 3.12; GDAL GML round-trip; UTF-8 integrity; `FLAECHE` unit verification against GEOS-computed area

### Secondary (MEDIUM confidence)
- `https://gdk.gdi-de.org/geonetwork/srv/api/records/bec888f9-ba0c-42dc-846e-177b8265dafa` — GDI-DE metadata: licence, attribution requirement, update frequency, per-layer vintage (corroborates the GetCapabilities abstract)
- `https://leafletjs.com/reference.html#path-renderer` — `renderer` option, `L.Canvas`, `preferCanvas` semantics
- `https://www.bfn.de/daten-und-fakten/natura-2000-gebietsmeldestatistik-und-karten` — Natura 2000 reporting statistics and update cadence

### Tertiary (LOW confidence — flagged, not relied upon)
- WebSearch results on Natura 2000 currency in Germany. Used only to corroborate the 2019 vintage
  already stated authoritatively in the GetCapabilities abstract; no unique claim rests on these.

---

## Metadata

**Confidence breakdown:**
- **WFS endpoint + typenames:** HIGH — GetCapabilities executed; corroborated by `variables_catalogue.xlsx` and the GDI-DE record
- **Feature schemas:** HIGH — `DescribeFeatureType` for all three layers plus live value inspection
- **Query methodology:** HIGH — every parameter variant tested empirically; all four silent-failure modes reproduced and isolated
- **Coverage / volume figures:** HIGH — measured end-to-end, not estimated
- **Pipeline pattern:** HIGH — derived from `build_vector.py` and validated by executing the proposed flow
- **`sync.py` integration:** HIGH — read the code; `sync_vector_geojson()` + `generate_layer_sources()` require no changes
- **App integration corrections:** HIGH — read `LLMap`, `useGeoJSON`, `LayerTabs`, `MapLegend`, `layers.js` directly
- **Canvas-renderer necessity:** MEDIUM — vertex counts measured precisely; the rendering-slowness threshold is a documented Leaflet characteristic, not benchmarked in this browser/app
- **D-08 vs. precision interpretation:** LOW — requires a user decision (A1)
- **Data vintage acceptability:** LOW — requires a user decision (A4)

**Validation Architecture:** omitted — `.planning/config.json` sets `workflow.nyquist_validation: false`.

**Research date:** 2026-07-25
**Valid until:** ~2026-08-24 (30 days). The BfN service is stable but externally controlled;
re-verify `numberMatched` counts and the GetCapabilities feature-type list before any future
re-plan of this phase.
