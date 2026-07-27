# Phase 7: Add BORIS land value maps as spatial layer for socio-economic tab - Research

**Researched:** 2026-07-27
**Domain:** OGC WFS 2.0 geodata acquisition (BORIS-BB + BORIS-HE Bodenrichtwert) -> GeoPandas per-LL GeoJSON -> Leaflet choropleth
**Confidence:** HIGH for endpoints/schemas/volume (executed live against both production services 2026-07-27); MEDIUM for the full HE usage-code vocabulary (partially observed, not exhaustively documented)

---

<user_constraints>
## User Constraints (from 07-CONTEXT.md)

### Locked Decisions

**Value Visualization Style**
- **D-01:** Zones are colored by a choropleth of the standard land value (EUR/m2), not by usage-type category. First continuous-value choropleth in the app (soil and protected-areas use flat categorical legends).
- **D-02:** Binning is quantile-based (5-6 classes), computed across all zones together (not split by usage type). Fixed at 5-6 buckets for every Living Lab regardless of zone count.
- **D-03:** Color ramp is a new sequential ramp derived from existing `theme.js` tokens (e.g. teal family `C.tealBg` -> `C.tealLight`, or teal->orange), not an external cartographic palette. Follows Phase 6's D-10/D-11 "minimize new colors" precedent.
- **D-04:** The legend shows the exact EUR/m2 range per bucket (e.g. "EUR2-4/m2"), extending the existing `value/en/de/color` legend entry shape with a formatted range as the label.

**Land-Use Scope**
- **D-05:** Show ALL BORIS zones (agricultural, residential, commercial, forest, etc.) - not filtered to agricultural-only.
- **D-06:** Usage type is NOT a second visual channel on the map (no hatching/border-per-type) - fill color encodes value only. Usage type is tooltip-only information.
- **D-07:** Speculative development-expectation land (Bauerwartungsland) is included as its own zone alongside everything else - no special exclusion.
- **D-08:** Zones with no current/live Bodenrichtwert (only historical or null values) ARE still shown, in a distinct "no data" style (neutral/hatched fill), not dropped.

**Cross-LL Comparability**
- **D-09:** Color scale is computed independently per Living Lab (each LL's own quantile buckets) - NOT a shared scale across all 5 LLs.
- **D-10:** A small bilingual note under the legend (reusing `legendNoteKey`) states the scale is relative to that Living Lab only.

**Two-State Data Harmonization & Tooltip**
- **D-11:** Build a full bilingual semantic contract for BORIS usage-type codes - map both Brandenburg's and Hessen's raw WFS usage codes into one shared canonical EN/DE vocabulary before writing per-LL GeoJSON, mirroring the Phase 2.2 BUEK soil semantic-contract precedent. Do not ship two different raw code vocabularies to the frontend.
- **D-12:** Tooltip shows: value (EUR/m2), usage type (bilingual), and valuation date (Stichtag). No separate zone-reference-code row.
- **D-13:** No page-level "as of [date]" vintage badge near the map - the valuation date lives only in the per-zone tooltip.

### Claude's Discretion
- Exact hex values for the sequential color ramp (derive from `theme.js`, D-03 sets the family)
- Whether quantile-bin computation happens client-side (from the per-LL fetched GeoJSON, like `buildSoilLegendEntries`) or is precomputed in the pipeline and embedded in GeoJSON properties
- "No data" style specifics (exact gray/hatch treatment)
- Tooltip layout/row order beyond the three required fields (D-12)
- **WFS query parameters, pagination, and per-LL clip/filter mechanics** <- this research materially informs this item; see "The Volume Problem" below
- Whether BORIS is wired as a `type: 'vector'` layer following soil's exact hardcoded `layer === 'economic'` rendering path in `LLMap/index.jsx`, or as a small generalization of the existing vector-rendering branch

### Deferred Ideas (OUT OF SCOPE)
- Per-usage-type quantile scaling (separate scale per land-use category)
- Page-level vintage/"as of" badge for the Bodenrichtwert reference date
- Secondary visual channel for usage type (hatching/border patterns)
- Adaptive bucket count per LL's zone density
</user_constraints>

---

## Project Constraints (from CLAUDE.md)

| Directive | Impact on this phase |
|-----------|----------------------|
| Static-only hosting, `base: './'`, must work at any sub-path | Per-LL GeoJSON URLs stay relative (`data/geojson/...`), matching `layers.js` `geojsonPathPattern` |
| Python 3.12 required on Windows | New fetch script runs under `data-pipeline/.venv` (Python 3.12, GeoPandas 1.1.3, Shapely 2.1.2, verified installed) |
| No TypeScript, no CSS frameworks, no SSR | Frontend work is plain JSX + inline styles |
| **Never write `data/ll_content.json` from any pipeline script** | New script writes only `data/geojson/boris-*.geojson` |
| **Always call `make_valid()` after `gpd.read_file()`** | Mandatory for both BB and HE GML reads; BB's AdV BRM zone polygons include complex multi-ring geometries (interior rings observed, see Code Examples) that are plausible sources of self-intersection |
| **Always align CRS before clipping**, assert `len(clipped) > 0` | BB default CRS is **EPSG:25833** (UTM 33N); HE default CRS is **EPSG:25832** (UTM 32N) - the two states use *different* native CRSs. Reproject both to EPSG:4326 before any spatial op |
| **`json.dumps(..., sort_keys=True)` everywhere in `sync.py`** | Use `GeoDataFrame.to_json(drop_id=True, sort_keys=True)`, matching `build_vector.py`/`fetch_protected_areas.py` |
| Pipeline-app contract: files on disk only | No runtime WFS calls from the browser; WFS runs at pipeline time only |

---

<phase_requirements>
## Phase Requirements

`.planning/REQUIREMENTS.md` has no requirement IDs for Phase 7 (traceability table stops at `CHARTS-02`, Phase 3). As with Phase 5, proceed with the CONTEXT decision IDs (D-01..D-13) as the traceability anchor; the planner may optionally add `BORIS-0x` IDs to REQUIREMENTS.md.

| ID | Description | Research Support |
|----|-------------|-------------------|
| D-01/D-02/D-04 | Continuous choropleth, quantile bins, ranged legend labels | `bodenrichtwert` (double, EUR/m2) confirmed as a plain numeric field on both states' polygon-bearing feature types, verified live, section 2 |
| D-05/D-07 | Show all zones incl. Bauerwartungsland | `entwicklungszustand` field (BB numeric 1000-5000, HE letters B/R/E/LF/SF) is the field that carries Bauerwartungsland; verified 5-category ImmoWertV taxonomy, section 3 |
| D-08 | No-data zones still shown | BB's WFS explicitly mixes **all historical Stichtage since 2010** into one endpoint with no per-year split (unlike HE); a BB zone whose only linked value record is a stale historical Stichtag is exactly the D-08 scenario. Verified live example: a Potsdam zone whose only ever value dates to 2010-01-01, section 4 |
| D-09/D-10 | Per-LL independent scale + note | No WFS dependency; a Claude's-Discretion frontend concern, addressed in Architecture Patterns |
| D-11 | Bilingual usage-code harmonization | BB `nutzung.art` = GDI-DE national codelist reference (44 entries, fully enumerated, section 3.1); HE `nutzung.art` = free-text legacy abbreviation (partially observed, section 3.2) - genuinely two different vocabularies requiring a harmonization table, confirming D-11's premise |
| D-12 | Tooltip: value, usage type, Stichtag | All three fields (`bodenrichtwert`, `nutzung.art`, `stichtag`) confirmed present on both states' feature schemas, section 2 |
| WFS mechanics (discretion) | Query params, pagination, clip | **The dominant finding of this research**: verified feature-per-LL counts (1,668-30,018) are 5-80x higher than any prior vector layer in this project; see "The Volume Problem", section 5 |
</phase_requirements>

---

## Summary

**Both WFS endpoints exist, are live, unauthenticated, and were fully queried on 2026-07-27.** Brandenburg publishes `https://isk.geobasis-bb.de/ows/boris_wfs` (WFS 2.0.0, AdV BRM 3.0.1 object model, native CRS **EPSG:25833**); Hessen publishes a year-versioned endpoint family at `https://www.gds.hessen.de/wfs2/boris/cgi-bin/brw/{year}/wfs` (WFS 2.0.0/1.1.0, older BRM 2.1 object model, native CRS **EPSG:25832**; use the `2024` vintage). Both accept the same lat/lon + `urn:ogc:def:crs:EPSG::4326` BBOX convention discovered in Phase 5's BfN research, and both only offer GML 3.2.1 output (no GeoJSON option) - read with `gpd.read_file()` exactly as Phase 5 and `build_vector.py` already do. No API key, no rate limiting observed, no cost (Hessen's `AccessConstraints` explicitly states free automated use under the Gutachterausschusskostengesetz).

**The two states' schemas are structurally different, not just field-renamed.** Hessen's polygon feature type (`boris:BR_BodenrichtwertZonal`) is **self-contained**: value, Stichtag, usage type, and development status are all properties directly on the polygon. Brandenburg's polygon feature type (`br:BR_BodenrichtwertFlaeche`) carries **geometry only** - value, Stichtag, and usage type live on a *separate point feature type* (`br:BR_Bodenrichtwert`) linked by a `gehoertZu`/`inversZu_gehoertZu` reference pair, and that point feature type **cannot be filtered by BBOX at all** (the server returns an explicit "has no geometry property... in the configuration" error). A join step is mandatory for Brandenburg and was not anticipated by either the CONTEXT document or the Phase 5 precedent it cites. This is fully solved below (section 4) with a verified, working approach.

**The single most important finding, and the one that should gate planning, is volume.** Exact server-side spatial-intersect counts (verified via WFS 2.0 `fes:Intersects` POST filters against each LL's real boundary geometry, not bbox estimates) are:

| Living Lab | State | Zones (exact, `fes:Intersects`) |
|---|---|---:|
| rheingau | HE | 1,668 |
| north-hessian-loess | HE | 3,435 |
| hessian-low-mountain | HE | 9,531 |
| havellandisches-luch | BB | 19,083 |
| east-brandenburg | BB | 30,018 |
| **Total** | | **63,735** |

This is **5x to 80x** the feature density of every vector layer previously integrated into this project (protected areas topped out at 362 features for the single densest LL; BUEK250 soil is lower still). A naive full-fidelity fetch of the smallest LL (rheingau, 1,668 zones) already produced a **12.96 MB** GML response and a **16.7 MB** unrounded/untrimmed GeoJSON. Scaling by feature count alone (ignoring that larger LLs may also have more geometrically complex zones) implies the two Brandenburg LLs would each land in the **150-300 MB** range before any mitigation - multiplied by two because both `data/geojson/` and `app/public/data/geojson/` are committed. **This must be treated as a blocking architectural question, not an implementation detail**, and is escalated as Open Question 1 below with a concrete recommendation (property trimming + coordinate rounding + simplification, sized and validated in a Wave 0 spike before committing anything).

**Primary recommendation:** Add one new script `data-pipeline/python/fetch_boris.py`, registered in `sources.yaml` as `kind: vector` with two state-specific WFS sub-configs. For each Living Lab: (1) fetch the LL's boundary geometry, (2) query the relevant state's polygon feature type using a server-side `fes:Intersects` spatial filter (not a padded BBOX - it is both more accurate and, as measured, returns up to 3x fewer candidate features than a bbox+client-filter approach), (3) for Brandenburg only, join value attributes from a **once-per-run, cached, full-state fetch** of `br:BR_Bodenrichtwert` points (113,293 statewide, fetched once via COUNT/STARTINDEX paging into `data/_cache/boris/`, never committed) rather than one WFS round-trip per zone, (4) normalise both states' usage-type and development-status codes onto one bilingual contract (D-11) using the verified 44-entry BB codelist as the canonical vocabulary target, (5) aggressively trim properties, round coordinates, and simplify geometry before writing (D-08's "no current value" zones are a first-class output, not an error case), (6) write `data/geojson/boris-{slug}.geojson`.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|-----------------|-----------|
| WFS querying, CRS handling (25832/25833 -> 4326), geometry validation | Python pipeline (`fetch_boris.py`) | - | CLAUDE.md: pipeline-app contract is files on disk; avoids CORS entirely |
| Brandenburg point/polygon join (`gehoertZu`) | Python pipeline | - | Requires a full-state cached fetch + in-memory join; infeasible client-side or per-request |
| Usage-code + development-status harmonization (D-11) | Python pipeline | - | Mirrors `soil_semantics.py` precedent; keeps JSX free of raw-code branching |
| Quantile bucket computation (D-02) | Browser (`useMemo`, mirrors `buildSoilLegendEntries`) OR Python pipeline (precomputed) | - | Claude's Discretion per CONTEXT; recommend **client-side** (see Architecture Patterns) so the choropleth bucket boundaries can be recomputed if the app ever needs a different bucket count without a pipeline re-run |
| Geometry simplification / coordinate rounding / property trimming | Python pipeline | - | Mandatory given the Volume Problem; no equivalent exists client-side |
| Asset copy to `app/public/` | `sync.py` (`sync_vector_geojson`) | - | Already globs `output.geojson_pattern` for every `kind: vector` layer - no change needed if `sources.yaml` declares it correctly |
| Source/licence attribution | `sync.py` (`generate_layer_sources`) -> `layer_sources.js` | `MapInfoControl` | Existing codegen path, keyed by `app_layer` |
| Choropleth rendering + tooltip + legend | Browser (`LLMap`, `MapLegend`) | - | Likely requires `L.canvas()` renderer given feature counts far exceeding the protected-areas precedent that already needed Canvas at 362 features/LL |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|---------------|
| geopandas | 1.1.3 (already installed) | GML read, reprojection, spatial filtering, simplification | Already the project's vector pipeline library (`build_vector.py`, `fetch_protected_areas.py`) |
| shapely | 2.1.2 (already installed) | `make_valid()`, `set_precision()`, GML polygon construction for POST filters | Same |
| requests | >=2.31 (already installed) | WFS HTTP GET/POST | Same; WFS 2.0 POST is required here (see Architecture Patterns) whereas Phase 5 only needed GET |
| pyyaml | >=6.0 (already installed) | `sources.yaml` parsing | Same |

**No new packages are required.** [VERIFIED: `data-pipeline/.venv` already has geopandas 1.1.3 installed and working, confirmed live 2026-07-27]

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Hand-built GML POST filter strings (this research's approach) | `owslib` (Python WFS client library) | Not currently a dependency; adds a package for a capability (`fes:Filter` construction) achievable with an f-string template, mirroring the project's existing preference (Phase 5 explicitly rejected `owslib`). **Not recommended** - see Don't Hand-Roll |
| Per-zone individual WFS point lookups for Brandenburg | One cached full-state point fetch + local join | Individual lookups do not scale to 19k-30k zones/LL; a single ~113k-record fetch (cached, gitignored) is one round trip |

**Installation:** none - all dependencies already present in `data-pipeline/requirements.txt` and the active venv.

---

## Package Legitimacy Audit

**No new packages are introduced by this phase.** Every library required (`geopandas`, `shapely`, `requests`, `pyyaml`) is already declared in `data-pipeline/requirements.txt` and confirmed installed and working in the project virtualenv (verified live: `geopandas.__version__` == `1.1.3`, 2026-07-27).

| Package | Registry | Status in repo | Disposition |
|---------|----------|-----------------|-------------|
| geopandas | PyPI | already in `requirements.txt`, installed 1.1.3, verified live | Approved (no change) |
| shapely | PyPI | already in `requirements.txt` | Approved (no change) |
| requests | PyPI | already in `requirements.txt` | Approved (no change) |
| pyyaml | PyPI | already in `requirements.txt` | Approved (no change) |

**Packages removed due to slopcheck `[SLOP]` verdict:** none - no new packages proposed.
**Packages flagged `[SUS]`:** none.

`slopcheck` was not run because the phase adds zero new dependencies; the audit surface is empty. If the planner or executor later decides `owslib` is needed after all, the Package Legitimacy Gate must run before that install - but this research explicitly recommends against it (see Don't Hand-Roll).

---

## 1. WFS Endpoints Found & Validated

### 1.1 Brandenburg (BORIS-BB)

| Property | Value |
|----------|-------|
| **Base URL** | `https://isk.geobasis-bb.de/ows/boris_wfs` |
| **Service title** | "WFS BB BRW" |
| **WFS version** | 2.0.0 |
| **Object model** | AdV BORIS-Objektartenkatalog **BRM 3.0.1** (Beschluss 2024-02-13) |
| **Default CRS** | `urn:ogc:def:crs:EPSG::25833` (ETRS89 / UTM zone 33N) |
| **BBOX CRS** | `urn:ogc:def:crs:EPSG::4326`, **lat,lon order** (same convention as Phase 5's BfN service) |
| **Output formats** | `text/xml; subtype=gml/3.2.1`, `application/gml+xml; version=3.2` only - **no GeoJSON option exists on this server at all** (not merely "don't use it" as with BfN - it is not offered) |
| **Auth** | None |
| **Vintage scope** | The service abstract states it aggregates **"aktuelle sowie historische Bodenrichtwerte ab dem Jahr 2010"** - i.e. one endpoint carries every Stichtag since 2010, not just the current one. This is structurally different from Hessen (below) and is the mechanism behind D-08 (see section 4.3) |
| **Attribution** | Landesvermessung und Geobasisinformation Brandenburg (LGB) |
| **Metadata/contact** | `geobasis-bb.de/lgb/de/geodaten/grundstuecksmarkt/bodenrichtwert-portal/`; kundenservice@geobasis-bb.de |

[VERIFIED: `GetCapabilities` HTTP 200, 30,310 bytes, executed 2026-07-27]
[VERIFIED: `data/variables_catalogue.xlsx` `source_catalogue` sheet has **no** BORIS-BB or BORIS-HE row - this phase's endpoints were discovered fresh this session, not pre-catalogued. The catalogue's only Brandenburg WFS entry is an unrelated layer (`invekos_brandenburg_dfbk`, field-block cadastre)]

### 1.2 Hessen (BORIS-HE)

| Property | Value |
|----------|-------|
| **Base URL (2024 vintage)** | `https://www.gds.hessen.de/wfs2/boris/cgi-bin/brw/2024/wfs` |
| **Other vintages** | `.../brw/2022/wfs`, `.../brw/2020/wfs` exist as **separate endpoints per Stichtag year** - unlike Brandenburg, Hessen does not mix years on one service |
| **Service title** | "WFS HE BORIS 2024" |
| **WFS version** | 1.1.0 and 2.0.0 both offered; use 2.0.0 for parity with Brandenburg |
| **Object model** | Older AdV **BRM 2.1** (not 3.0) |
| **Default CRS** | `urn:ogc:def:crs:EPSG::25832` (ETRS89 / UTM zone 32N) - **different from Brandenburg's 25833** |
| **BBOX CRS** | `urn:ogc:def:crs:EPSG::4326`, lat,lon order (same convention, verified working) |
| **Output formats** | `text/xml; subtype=gml/3.2.1` only |
| **Auth** | None |
| **Fees/licence** | "Der automatisierte Abruf... sind kostenfrei" (free per Gutachterausschusskostengesetz SS1(2)); `AccessConstraints` explicitly permits commercial and non-commercial reuse, modification, and redistribution without restriction |
| **Attribution** | Hessisches Landesamt fuer Bodenmanagement und Geoinformation (HLBG) / Hessen Geodatenmanagement (HVBG) |

[VERIFIED: `GetCapabilities` HTTP 200, 21,523 bytes, executed 2026-07-27]

### 1.3 Feature types (both services expose several; only these two are needed)

| State | UI purpose | WFS `TYPENAMES` | Geometry-bearing? | Contains value directly? |
|---|---|---|---|---|
| BB | Zone polygons | `br:BR_BodenrichtwertFlaeche` | Yes (Polygon) | **No** - geometry + lifecycle metadata only |
| BB | Value records | `br:BR_Bodenrichtwert` | **Not BBOX-filterable** (server error, section 4.1) | Yes - `bodenrichtwert`, `stichtag`, `nutzung`, `entwicklungszustand` |
| HE | Zone polygons + value | `boris:BR_BodenrichtwertZonal` | Yes (Polygon) | **Yes** - self-contained |
| HE | Parcel-level "typical" points | `boris:BR_BodenrichtwertLagetypisch` | Yes (Point) | Not needed for this phase (zone-level choropleth only) |

Both services also expose ALKIS reference layers (`adv:AX_*`), `BR_Verfahren`, and `BR_Umrechnungstabelle*` (conversion-table feature types for adjusting values by parcel characteristics) - none needed for a flat zone-value choropleth.

[VERIFIED: `DescribeFeatureType` for `br:BR_BodenrichtwertFlaeche`, `br:BR_Bodenrichtwert`, and `boris:BR_BodenrichtwertZonal`, executed live 2026-07-27]

---

## 2. Feature Schema

### 2.1 Hessen (`boris:BR_BodenrichtwertZonal`) - self-contained

Confirmed live fields (from an actual GetFeature response, Rheingau, 2 sampled features):

| Field | Type | Example | Notes |
|---|---|---|---|
| `bodenrichtwert` | double | `220.0`, `2.6` | **EUR/m2** |
| `stichtag` | date | `2024-01-01` | Single vintage per this endpoint |
| `bodenrichtwertNummer` | string, pattern `[0-9]{8}` | `00260104` | Zone reference code |
| `bodenrichtwertzoneName` | string, optional | (often absent) | Human-readable zone name, sparse |
| `entwicklungszustand` | enum: `B`,`R`,`E`,`LF`,`SF` | `B`, `LF` | Development status - see section 3 |
| `nutzung.art` | **plain unrestricted string** | `G`, `LW` | Usage type - see section 3.2 |
| `gemeinde.name`, `gemarkung.name` | string | `Nauheim` | Administrative context, not required by D-12 |
| `bemerkungen` | string, optional | free text | Optional remark, sparse |
| geometry | `gml:Polygon` (can include `gml:interior` rings - donut/hole geometries observed) | - | Property name `adv:position` |

[VERIFIED: live GetFeature, 2 zones fetched and fully inspected, 2026-07-27]

### 2.2 Brandenburg - split across two feature types

**`br:BR_BodenrichtwertFlaeche`** (polygon) - confirmed to contain **only**: `gml:identifier`, `adv:lebenszeitintervall` (lifecycle dates, unrelated to Stichtag), `adv:modellart`, and `adv:position` (the `gml:Polygon`). The schema-declared `inversZu_gehoertZu` reference field (which would list the linked value record IDs) is **not populated in the live response**, even when requested with `RESOLVE=local`. [VERIFIED: two live GetFeature responses inspected end-to-end for this feature type; `inversZu_gehoertZu` absent in both]

**`br:BR_Bodenrichtwert`** (point, carries the actual value):

| Field | Type | Example | Notes |
|---|---|---|---|
| `bodenrichtwert` | double | `65.0`, `310.0` | EUR/m2 |
| `stichtag` | date | `2010-01-01` | **Can be any year since 2010** - see 4.3 |
| `bodenrichtwertNummer` | string | `00100001` | Zone reference code |
| `bodenrichtwertzoneName` | string | `Am Goerdensee` | |
| `entwicklungszustand` | enum: `1000`,`2000`,`3000`,`4000`,`5000` | `1000` | Plain numeric string, not a codelist reference |
| `nutzung.art` | **`gml:ReferenceType`** -> `xlink:href` to `https://registry.gdi-de.org/codelist/de.adv-online.gid/BR_Art_Nutzung/{code}` | `.../1100` | Usage type - GDI-DE national codelist reference, see 3.1 |
| `gehoertZu` | `gml:ReferenceType` -> `xlink:href="urn:adv:oid:{FlaecheGmlId}"` | `urn:adv:oid:DEBBBR001WQ0011f` | **The join key back to the polygon** |
| geometry | none exposed for spatial filtering | - | Attempting `BBOX` on this typename returns a server error, section 4.1 |

[VERIFIED: live GetFeature, multiple points fetched and fully inspected, 2026-07-27]

---

## 3. Usage-Type & Development-Status Harmonization (D-11)

### 3.1 Brandenburg's `nutzung.art` - full national codelist (VERIFIED, 44 entries)

BB references the **GDI-DE national codelist `de.adv-online.gid/BR_Art_Nutzung`**, fetched and enumerated in full:

| Code | German label (abbreviation) | Suggested EN canonical |
|---|---|---|
| 1100 | Wohnbauflaeche (W) | Residential building land |
| 1110 | Kleinsiedlungsgebiet (WS) | Small-holdings settlement area |
| 1120 | reines Wohngebiet (WR) | Pure residential area |
| 1130 | allgemeines Wohngebiet (WA) | General residential area |
| 1140 | besonderes Wohngebiet (WB) | Special residential area |
| 1200 | gemischte Baufl. (M) | Mixed building land |
| 1210 | Dorfgebiet (MD) | Village area |
| 1220 | Doerfliches Wohngebiet (MDW) | Village residential area |
| 1230 | Mischgebiet (MI) | Mixed-use area |
| 1240 | Kerngebiet (MK) | Core/urban-centre area |
| 1250 | Urbanes Gebiet (MU) | Urban area |
| 1300 | gewerbliche Baufl. (G) | Commercial building land |
| 1310 | Gewerbegebiet (GE) | Commercial area |
| 1320 | Industriegebiet (GI) | Industrial area |
| 1400 | Sonderbaufl. (S) | Special-purpose building land |
| 1410 | Sondergebiet fuer Erholung (SE) | Special recreation area |
| 1420 | sonstige Sondergebiete (SO) | Other special-purpose area |
| 1500 | Baufl. fuer Gemeinbedarf (GB) | Public-facility building land |
| 2000 | landwirtschaftliche Fl. (L) | Agricultural land |
| 2100 | Acker (A) | Arable land |
| 2200 | Gruenland (GR) | Grassland |
| 2300 | Erwerbsgartenbaufl. (EGA) | Commercial horticulture |
| 2400 | Anbaufl. f. Sonderkulturen (SK) | Special-crop cultivation |
| 2500 | Weingarten (WG) | Vineyard |
| 2600 | Kurzumtriebsplantagen, Agroforst (KUP) | Short-rotation coppice / agroforestry |
| 2700 | Unland, Geringstland, Bergweide, Moor (UN) | Wasteland / poor land / mountain pasture / moor |
| 2800 | forstwirtschaftliche Fl. (F) | Forestry land |
| 3010 | private Gruenfl. (PG) | Private green space |
| 3020 | Kleingartenfl. (KGA) | Allotment garden |
| 3030 | Freizeitgartenfl. (FGA) | Recreational garden |
| 3040 | Campingplatz (CA) | Campsite |
| 3050 | Sportfl. (SPO) | Sports facility |
| 3060 | sonstige private Fl. (SG) | Other private land |
| 3070 | Friedhof (FH) | Cemetery |
| 3080 | Wasserfl. (WF) | Water area |
| 3090 | Flughafen, Flugplaetze (FP) | Airport / airfield |
| 3100 | private Parkplaetze (PP) | Private parking |
| 3110 | Lagerfl. (LG) | Storage area |
| 3120 | Abbauland (AB) | Extraction land (quarrying/mining) |
| 3130 | Gemeinbedarfsfl., kein Bauland (GF) | Public-facility land (non-buildable) |
| 3140 | Sondernutzungsfl. (SN) | Special-use area |
| 9998 | Nach Quellenlage nicht zu spezifizieren | Not specifiable from source data |

[VERIFIED: `https://registry.gdi-de.org/codelist/de.adv-online.gid/BR_Art_Nutzung` listing page fetched live 2026-07-27, all 44 rows enumerated; single-code lookup (`.../1100`) independently confirmed as "Wohnbauflaeche (W)"]

**Recommendation:** use this 44-entry table as the **canonical vocabulary target** for D-11 (it is the more granular, nationally standardized list). Both states' raw codes map *onto* this vocabulary; the frontend only ever sees the canonical EN/DE pair plus the raw code retained as a provenance field, exactly mirroring `soil_semantics.py`'s pattern of `soil_group_en`/`soil_group_de` derived fields plus raw `GEN_ID`/`SYM_NR` kept for provenance only.

### 3.2 Hessen's `nutzung.art` - free text, NOT the same vocabulary [ASSUMED - partial]

Hessen's schema types `nutzung.art` as a **plain, unrestricted `xsd:string`** (no enumeration in `DescribeFeatureType`), and the live values observed (`G`, `LW`) do **not** match the BB codelist's own abbreviations exactly (BB's "commercial" abbreviation is `G` for code 1300 - that one matches; but BB's "agricultural" abbreviation is `L` for code 2000 or `A` for 2100, whereas Hessen returned the literal string `LW`, which appears in neither). This indicates **Hessen is running its own, older, independently-abbreviated code scheme** (consistent with Hessen's WFS advertising the older BRM 2.1 object model vs. Brandenburg's BRM 3.0.1), not a subset of the same national list.

**What is confirmed:** `G` = Gewerbe/commercial (maps to BB 1300 "gewerbliche Flaeche"), `LW` = Landwirtschaft/agricultural (maps to BB 2000 "landwirtschaftliche Flaeche").
**What is not confirmed:** the full Hessen code set. A documentation search (BORIS Hessen Handbuch PDF, Brandenburg Gutachterausschuss legend PDF) did not yield a machine-readable code table in this session - the PDFs found are compressed/image-based and did not extract cleanly via automated tooling.

**Recommendation (concrete, actionable):** do not hand-author a guessed Hessen code table. Instead, have the pipeline **empirically discover the actual code set** by requesting `GetPropertyValue` (WFS 2.0 operation, listed in both services' `GetCapabilities`) for `boris:nutzung/boris:BR_Nutzung/boris:art` and `boris:entwicklungszustand` scoped to the 3 Hessen LLs during the Wave 0 build - this returns only the *distinct values actually present*, which for 3 predominantly rural/small-town Kreise is very likely a small set (a dozen or fewer), not the full statewide vocabulary. Build the BB<->HE<->canonical mapping table from that live-sampled set, with an explicit fallback ("Unmapped usage type" bilingual label + raw code preserved) for anything encountered later that isn't in the table - mirroring the `fallback_policy` pattern already used for BUEK250 soil semantics in `sources.yaml`.

### 3.3 `entwicklungszustand` (development status) - same 5 categories, different alphabets [CITED, MEDIUM-HIGH confidence]

Both states restrict this field to exactly 5 values, and the codes align 1:1 with the nationally standardized ImmoWertV development-status taxonomy:

| Concept | HE code | BB code | EN |
|---|---|---|---|
| Bauland (development-ready) | `B` | `1000` | Building-ready land |
| Rohbauland | `R` | `2000` | Raw building land |
| **Bauerwartungsland** (D-07) | `E` | `3000` | Building-expectation land |
| Land-/forstwirtschaftliche Flaeche | `LF` | `4000` | Agricultural or forestry land |
| Sonderflaeche | `SF` | `5000` | Other/special land |

[VERIFIED: `DescribeFeatureType` confirms exactly 5 enum values for both states' `entwicklungszustand` fields] [CITED: WebSearch corroboration from `code-knacker.de/bodenrichtwerte.htm` and Brandenburg Gutachterausschuss public documentation for the B/R/E/LF/SF -> German-label mapping; this is a well-known ImmoWertV SS3 concept, not unique to either state's WFS] This is a much smaller, cleaner mapping problem than `nutzung.art` and directly implements D-07 (Bauerwartungsland = `E`/`3000` is simply one more value shown identically to the others, not specially excluded).

---

## 4. The Brandenburg Point/Polygon Join (verified, working)

### 4.1 Why it's needed

`br:BR_BodenrichtwertFlaeche` (fetched via BBOX or spatial filter) returns geometry only. Attempting to BBOX-filter `br:BR_Bodenrichtwert` (the value-bearing point type) directly fails:

```
Error in filter expression: FeatureType "br:BR_Bodenrichtwert" has no geometry
property or it is missing in the configuration.
```//
[VERIFIED: reproduced live 2026-07-27]

### 4.2 The join key

A point's `gehoertZu` references its polygon by `xlink:href="urn:adv:oid:{FlaecheGmlId}"`. Observed IDs follow a `...f` (Flaeche) / `...z` (presumably "Zuordnung"/point) suffix convention (e.g. polygon `DEBBBR004WQ0GD1f` <-> point `DEBBBR004WQ0GD1z`), and a **direct `RESOURCEID` lookup using the suffix-substituted ID works**:

```
GET .../boris_wfs?...&TYPENAMES=br:BR_Bodenrichtwert&RESOURCEID=DEBBBR004WQ0GD1z
-> returns exactly the point whose gehoertZu references DEBBBR004WQ0GD1f
```
[VERIFIED live 2026-07-27]

**However, this is a fast-path heuristic, not a guaranteed rule.** The Flaeche schema declares `inversZu_gehoertZu` as `maxOccurs="unbounded"` - a single zone polygon *can* be referenced by multiple point records (e.g. one per historical Stichtag, section 4.3). A verified, robust alternative is a `PropertyIsEqualTo` filter on the reference itself:

```xml
<fes:Filter>
  <fes:PropertyIsEqualTo>
    <fes:ValueReference>br:gehoertZu/@xlink:href</fes:ValueReference>
    <fes:Literal>urn:adv:oid:DEBBBR004WQ0GD1f</fes:Literal>
  </fes:PropertyIsEqualTo>
</fes:Filter>
```
[VERIFIED: returns the correct, single matching point; requires declaring `xmlns:xlink="http://www.w3.org/1999/xlink"` on the request root]

### 4.3 Recommended join strategy: cache the whole state once, join locally

Per-zone individual WFS round trips do not scale (19,083-30,018 zones per BB Living Lab). The statewide total for `br:BR_Bodenrichtwert` is **113,293 records** [VERIFIED: `RESULTTYPE=hits`, no bbox, 2026-07-27] - far more than the ~40,101 combined polygon zones across both BB Living Labs, **because Brandenburg's single endpoint mixes every historical Stichtag since 2010** (section 1.1) - one physical zone can have several point records across different years.

**Recommended approach:**
1. Fetch all 113,293 `br:BR_Bodenrichtwert` points **once per pipeline run**, paginated (`COUNT=5000` + `STARTINDEX`, ~23 pages), into `data/_cache/boris/bb_points.gml` (gitignored, matching the `fetch_protected_areas.py` `--refresh` cache pattern).
2. Build an in-memory dict keyed by the polygon ID extracted from `gehoertZu` (strip `urn:adv:oid:` prefix), with **list** values (a zone may have multiple Stichtage).
3. For each fetched `br:BR_BodenrichtwertFlaeche` zone, look up its list of point records, pick the one with the **maximum `stichtag`** as the "current" value, and set a `has_current_value` flag based on whether that Stichtag is recent enough to be considered live (a concrete recency threshold - e.g. within the last two Hauptfeststellungszeitraum cycles - is a planner/user decision; flagged in Open Questions). Zones with **no** matching point record at all, or whose only record's Stichtag is old, are exactly the D-08 "no data" case.

This turns an intractable "one WFS call per zone" problem into "one large cached fetch + a Python dict lookup," which is the same caching philosophy `fetch_protected_areas.py` already established for a smaller dataset.

---

## 5. The Volume Problem (READ THIS BEFORE PLANNING TASKS)

### 5.1 Exact per-LL zone counts (server-side spatial filter, not estimated)

Verified by sending each Living Lab's real boundary geometry (from `data/ll_boundaries.geojson`, simplified to keep the request body manageable) as a WFS 2.0 `fes:Intersects` POST filter directly to each state's WFS - this is the exact server-computed intersection count, not a bounding-box overestimate:

| Living Lab | State | BBOX-hits (padded rectangle, overestimate) | `fes:Intersects` (exact) |
|---|---|---:|---:|
| rheingau | HE | - | **1,668** |
| north-hessian-loess | HE | - | **3,435** |
| hessian-low-mountain | HE | - | **9,531** |
| havellandisches-luch | BB | 68,540 | **19,083** |
| east-brandenburg | BB | 89,263 | **30,018** |

For comparison, Phase 5's protected areas (the closest prior "live WFS, per-LL vector" precedent) topped out at **362 features** for its single densest Living Lab. **BORIS zone density is 5x-80x higher.**

[VERIFIED: server-side `fes:Intersects` executed against both live WFS endpoints using each LL's actual (simplified) boundary polygon as the filter geometry, 2026-07-27]

### 5.2 Measured file size (smallest LL, worst case not yet measured)

A full fetch of `rheingau` (1,668 zones, self-contained HE schema, no join needed) produced:
- **12.96 MB** raw GML response
- **16.7 MB** unrounded, all-29-columns GeoJSON (`GeoDataFrame.to_json()` with default settings)

Scaling naively by feature count alone (larger LLs are not necessarily geometrically simpler, so this is a floor, not a ceiling):

| Living Lab | Zones | Naive GeoJSON estimate |
|---|---:|---:|
| rheingau | 1,668 | ~16.7 MB (measured) |
| north-hessian-loess | 3,435 | ~34 MB |
| hessian-low-mountain | 9,531 | ~95 MB |
| havellandisches-luch | 19,083 | ~190 MB |
| east-brandenburg | 30,018 | ~300 MB |

Because the project commits every layer's output **twice** (`data/geojson/` and `app/public/data/geojson/`, per the existing `build_vector.py`/`fetch_protected_areas.py` pattern), an unmitigated implementation could add roughly **1.2 GB** to a repository whose `.git` was already ~725 MB as of Phase 5. This is not viable.

### 5.3 What actually drives the size, and what to do about it

Inspecting the fetched Rheingau features directly: the bulk of payload size is **polygon vertex coordinates**, not properties (one observed Zonal feature's `posList` alone ran to several thousand coordinate pairs, including interior/donut rings for zones with excluded sub-areas). The raw GML also carries ~29 columns per feature including verbose repeated nested objects (`gutachterausschuss.bezeichnung` full committee names repeated on every feature, `basiskarte.bezeichnung`, etc.) that D-12's tooltip contract does not need.

**Two independent, additive mitigations, both with direct precedent in this codebase:**
1. **Property trimming**: keep only the ~8 fields the contract needs (`bodenrichtwertNummer`, `bodenrichtwert`, `stichtag`, harmonized usage-type EN/DE + raw code, harmonized development-status EN/DE + raw code, `has_current_value`, `ll_slug`) instead of ~29 raw GML columns. This has a bounded, moderate impact (properties are a minority of the byte count).
2. **Geometry simplification + coordinate rounding**, exactly as `build_vector.py` already does for BUEK250 (`simplify_tolerance`, `coordinate_precision` in `vector:` config) and as `fetch_protected_areas.py` does for BfN (`set_precision`). This is the **dominant lever** since geometry dominates payload size, but note that simplification reduces *per-feature* size, not *feature count* - with 30,018 zones in east-brandenburg, even an aggressively simplified per-feature footprint may still sum to tens of MB.

**Neither mitigation alone is guaranteed sufficient for the two Brandenburg LLs at this feature count.** This is why Open Question 1 (below) recommends a Wave 0 spike that actually measures the trimmed+simplified output size for the two Brandenburg LLs *before* any task commits to a specific approach, with the fallback options (courser simplification, or reconsidering whether every historical-duplicate BB zone geometry needs to ship, or a raster/PMTiles rendering path instead of per-LL GeoJSON) evaluated against real numbers rather than assumptions.

---

## Architecture Patterns

### System Architecture Diagram

```
                    PIPELINE (build time, Python)
  ll_boundaries.geojson (EPSG:4326, per-LL geometry)
            |
            v
   +-------------------+        +--------------------------+
   | HE: fes:Intersects|        | BB: fes:Intersects        |
   | POST -> Zonal      |        | POST -> Flaeche (geom-only)|
   | (self-contained)   |        +--------------------------+
   +-------------------+                    |
            |                                v
            |                    +-----------------------------+
            |                    | BB: cached full-state fetch  |
            |                    | (113,293 pts, data/_cache/)  |
            |                    | -> join by gehoertZu, pick   |
            |                    |    max(stichtag) per zone    |
            |                    +-----------------------------+
            |                                |
            v                                v
   +---------------------------------------------------+
   | Harmonization (D-11): raw code -> canonical EN/DE  |
   | Property trim + set_precision + simplify           |
   | has_current_value flag (D-08)                      |
   +---------------------------------------------------+
            |
            v
   data/geojson/boris-{slug}.geojson  (EPSG:4326)
            |
            v (sync.py, existing sync_vector_geojson(), no code change)
   app/public/data/geojson/boris-{slug}.geojson
            |
            v
                       BROWSER (runtime)
   useGeoJSON('data/geojson/boris-{slug}.geojson')  [lazy on economic tab select]
            |
            v
   client-side quantile bucketing (D-02, per-LL, D-09)
   -> style fn (choropleth fill by bucket) + legend entries (D-04) + tooltip (D-12)
            |
            v
   L.canvas() rendered GeoJSON layer inside LLMap (mirrors ProtectedAreasLayer pattern)
```

### Recommended Project Structure

```
data-pipeline/
  python/
    fetch_boris.py          # new: WFS fetch + join + harmonize + write
    boris_semantics.py       # new (optional split): usage-type + entwicklungszustand mapping tables, mirrors soil_semantics.py
  sources/
    sources.yaml             # add `boris` entry, kind: vector, two wfs sub-configs (bb/he)
app/src/
  data/
    layers.js                # economic: placeholder -> vector, add BORIS_LEGEND (quantile-bucket shape) + legendNoteKey
  components/LLMap/index.jsx # add economic data-fetch memo, quantile style fn, legend builder, tooltip binder (mirrors soil branch)
  i18n.js                    # add legend.economic.note/tooltip keys (careful: legend.economic.{arable,forest,...} already exists as the LAYER_COLORS fallback - becomes dead code once cfg.legend is populated)
```

### Pattern: Client-side quantile bucketing (recommended for D-02/D-09 discretion item)

**What:** Compute 5-6 quantile breakpoints from the fetched per-LL GeoJSON's `bodenrichtwert` values, entirely in the browser, the same way `buildSoilLegendEntries` already derives its legend from `soilFeatureCollection`.
**When to use:** Always for this phase - it requires zero pipeline changes if the bucket count (D-02) ever needs adjusting, and per-LL independence (D-09) falls out naturally since each LL's GeoJSON is fetched and processed independently already.
**Example (sketch, to be refined by the planner):**
```javascript
// Mirrors buildSoilLegendEntries's shape (LLMap/index.jsx lines 192-250)
function computeQuantileBuckets(collection, bucketCount = 6) {
  const values = collection.features
    .map((f) => f.properties?.bodenrichtwert)
    .filter((v) => typeof v === 'number')
    .sort((a, b) => a - b)
  if (!values.length) return null
  const breaks = Array.from({ length: bucketCount + 1 }, (_, i) =>
    values[Math.min(values.length - 1, Math.floor((i / bucketCount) * values.length))]
  )
  return breaks // [min, q1, q2, q3, q4, q5, max] -> 6 ranges
}
```
Values with no current Bodenrichtwert (`has_current_value === false`, D-08) are excluded from the quantile computation itself but still rendered, in the distinct "no data" style.

### Anti-Patterns to Avoid
- **Assuming HE and BB share a usage-code vocabulary:** they do not (section 3.2) - a shared lookup table keyed by raw code without a state discriminator will silently mis-map values.
- **Fetching `br:BR_Bodenrichtwert` per zone:** does not scale past a few hundred zones; use the cached full-state fetch (section 4.3).
- **Reusing `gpd.clip()` uncritically:** given the feature counts here, clipping (vs. an intersects-only filter) materially reduces committed geometry size for zones straddling the LL boundary edge - recommended, unlike Phase 5's protected areas which deliberately kept full unclipped polygons (D-03 there). This phase has no equivalent "show full polygon" decision, so `gpd.clip()` (the `build_vector.py`/soil pattern) is the safer default, not the `intersects()`-only pattern from protected areas.

---

## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---------|-------------|--------------|-----|
| Parsing the WFS GML response | A regex/ElementTree GML reader | `gpd.read_file(path_to_gml)` | GDAL's GML driver handles both AdV object models correctly; verified 100% row/column fidelity on both HE and BB samples |
| Building `fes:Filter` XML | `owslib` (adds a new dependency) | Plain f-string XML templates (verified working in this research for both `Intersects` and `PropertyIsEqualTo`) | Matches Phase 5's explicit precedent of avoiding WFS client libraries; the filter XML needed here is small and stable |
| Reprojecting 25832/25833 -> 4326 | Manual UTM math | `frame.to_crs("EPSG:4326")` | Both states' native CRS differ from each other and from the app's storage CRS; GeoPandas handles both transforms correctly |
| Brandenburg point/polygon join at scale | Per-zone WFS round trips | One cached full-state fetch + in-memory dict join (section 4.3) | 113,293 records fetched once vs. up to 30,018 round trips per LL |
| Usage-code translation | Hand-guessed Hessen abbreviation table | Empirical `GetPropertyValue` sampling scoped to the 3 Hessen LLs (section 3.2) | Avoids shipping a wrong/incomplete guessed vocabulary as if it were verified |
| Coordinate rounding | `round()` on nested coordinate lists | `shapely.set_precision(geom, grid_size=...)` | Topology-aware; `build_vector.py` precedent |
| Copying outputs into `app/public/` | A bespoke copy step | `sync.py::sync_vector_geojson()` | Already globs `output.geojson_pattern` for every `kind: vector` layer |
| Quantile computation | A stats library dependency | Plain JS sort + index math (Architecture Patterns, above) | Trivial at these array sizes; matches `buildSoilLegendEntries`'s existing hand-rolled-but-simple style |

**Key insight:** every genuinely hard part of this phase - the two-state schema divergence, the Brandenburg join, the usage-code vocabulary mismatch, and the volume problem - is a *data modeling* problem, not a *missing library* problem. No new pipeline dependency is needed; the risk is entirely in getting the join and the size budget right.

---

## Common Pitfalls

### Pitfall 1: Treating Brandenburg like Hessen (assuming self-contained polygons)
**What goes wrong:** `br:BR_BodenrichtwertFlaeche` reads back with geometry but every value field is `None`/missing.
**Why:** Brandenburg splits geometry (Flaeche) and value (Bodenrichtwert point) across two feature types; Hessen does not.
**Avoid:** Branch the fetch logic per state explicitly; never assume a shared schema shape.
**Warning sign:** `bodenrichtwert` column entirely null after a BB fetch.

### Pitfall 2: BBOX-filtering `br:BR_Bodenrichtwert` directly
**What goes wrong:** HTTP 400, `"has no geometry property or it is missing in the configuration"`.
**Avoid:** Never spatially filter the point feature type. Filter `Flaeche` spatially, then join to points by ID (section 4).

### Pitfall 3: Assuming Brandenburg's Stichtag is always current
**What goes wrong:** A zone renders with a 2010 value as if it were live/current.
**Why:** Brandenburg's single WFS mixes every historical Stichtag since 2010; a `bodenrichtwert` value existing does not mean it's current.
**Avoid:** After the join, pick `max(stichtag)` per zone and compare against a recency threshold to set `has_current_value` (D-08). Hessen's year-specific endpoint (`/2024/wfs`) does not have this problem - every HE record it returns is already the 2024 vintage.
**Warning sign:** Tooltip shows a Stichtag more than one or two Hauptfeststellungszeitraum cycles old, presented identically to a fresh one.

### Pitfall 4: Mixing up the two native CRSs
**What goes wrong:** Geometry silently lands hundreds of km off (or `to_crs` raises) if Brandenburg output is assumed to be EPSG:25832 like Hessen.
**Why:** BB's `DefaultCRS` is **EPSG:25833**; HE's is **EPSG:25832**. Adjacent UTM zones, easy to conflate.
**Avoid:** Read the CRS from each state's config explicitly (`wfs.source_crs` in `sources.yaml`, one value per state sub-config) and assert it after `gpd.read_file()`, exactly as `build_vector.py`'s `_validate_declared_crs()` already does.

### Pitfall 5: Assuming BBOX-hit counts are the real per-LL feature count
**What goes wrong:** Sizing/performance estimates come out 2-3x too high (or a planning decision is made on padded-rectangle numbers instead of true intersection numbers).
**Why:** A padded bounding-box query over-selects; verified up to 3.6x overselection for `havellandisches-luch` (68,540 bbox-hits vs. 19,083 true `fes:Intersects` matches).
**Avoid:** Use a server-side `fes:Intersects` spatial filter with the actual LL geometry (verified working via WFS 2.0 POST for both states, section 5.1) rather than BBOX + client-side filtering.

### Pitfall 6: Assuming this phase's scale matches Phase 5's protected-areas precedent
**What goes wrong:** Reusing Phase 5's "no clip, no simplify, full fidelity, Canvas renderer handles it" approach verbatim leads to an unreviewable multi-hundred-MB commit.
**Why:** Protected areas topped out at 362 features/LL; BORIS zones run 1,668-30,018/LL. The same architecture does not scale by 2 orders of magnitude for free.
**Avoid:** Treat volume as the primary open question for this phase (Open Question 1) rather than assuming the prior phase's defaults transfer.

### Pitfall 7: Skipping `make_valid()` on Brandenburg's multi-ring zone polygons
**What goes wrong:** `intersects()`/`clip()` raises `TopologyException` or silently mis-selects.
**Why:** AdV BRM zone geometries can include interior (donut) rings for excluded enclaves (observed directly in a fetched Hessen sample; the same object model underlies Brandenburg's geometry too) - a plausible source of the same ~1% invalid-geometry rate Phase 5 measured for BfN's simpler polygons.
**Avoid:** `frame.geometry = frame.geometry.make_valid()` immediately after every `gpd.read_file()`, exactly per CLAUDE.md.

---

## Code Examples

### Verified: correct BBOX form for both states (fallback path, if spatial-filter POST is not used)
```python
# Source: executed live against both isk.geobasis-bb.de and www.gds.hessen.de, 2026-07-27
# lat,lon order + urn: CRS suffix is mandatory (same convention as Phase 5's BfN service)
bbox = f"{miny},{minx},{maxy},{maxx},urn:ogc:def:crs:EPSG::4326"
params = {"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature",
          "TYPENAMES": typename, "BBOX": bbox, "COUNT": 5000}
# No SRSNAME, no OUTPUTFORMAT (matches BfN precedent; both services default to GML 3.2.1 anyway)
```

### Verified: server-side spatial Intersects filter (recommended primary approach)
```python
# Source: executed live 2026-07-27; returns the EXACT per-LL zone count, not a bbox overestimate
def poly_to_gml(poly, idx, crs_urn):
    poslist = " ".join(f"{x} {y}" for x, y in poly.exterior.coords)
    return (f'<gml:Polygon gml:id="p{idx}" srsName="{crs_urn}"><gml:exterior>'
            f'<gml:LinearRing><gml:posList>{poslist}</gml:posList></gml:LinearRing>'
            f'</gml:exterior></gml:Polygon>')

# geom_p = LL boundary reprojected to the state's native CRS (25833 for BB, 25832 for HE)
crs_urn = f"urn:ogc:def:crs:EPSG::{epsg_code}"       # NOTE: double colon before the number
parts = geom_p.geoms if hasattr(geom_p, "geoms") else [geom_p]
members = "".join(f'<gml:surfaceMember>{poly_to_gml(p, i, crs_urn)}</gml:surfaceMember>'
                   for i, p in enumerate(parts))
multisurface = f'<gml:MultiSurface gml:id="ms1" srsName="{crs_urn}">{members}</gml:MultiSurface>'
body = f'''<?xml version="1.0" encoding="UTF-8"?>
<wfs:GetFeature service="WFS" version="2.0.0" count="5000"
  xmlns:wfs="http://www.opengis.net/wfs/2.0" xmlns:fes="http://www.opengis.net/fes/2.0"
  xmlns:gml="http://www.opengis.net/gml/3.2"
  xmlns:adv="http://www.adv-online.de/namespaces/adv/gid/7.1"
  xmlns:br="http://www.adv-online.de/namespaces/adv/br/3.0">
  <wfs:Query typeNames="br:BR_BodenrichtwertFlaeche">
    <fes:Filter><fes:Intersects>
      <fes:ValueReference>adv:position</fes:ValueReference>
      {multisurface}
    </fes:Intersects></fes:Filter>
  </wfs:Query>
</wfs:GetFeature>'''
r = requests.post(wfs_url, data=body.encode("utf-8"),
                   headers={"Content-Type": "application/xml"}, timeout=120)
# For Hessen, swap typeNames to "boris:BR_BodenrichtwertZonal" and declare
# xmlns:boris="http://www.adv-online.de/namespaces/adv/brm/2.1" instead of xmlns:br=...
```

### Verified: Brandenburg point/polygon join by exact reference match
```python
# Source: executed live 2026-07-27; robust alternative to the f/z suffix heuristic
body = '''<?xml version="1.0" encoding="UTF-8"?>
<wfs:GetFeature service="WFS" version="2.0.0"
  xmlns:wfs="http://www.opengis.net/wfs/2.0" xmlns:fes="http://www.opengis.net/fes/2.0"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:br="http://www.adv-online.de/namespaces/adv/br/3.0">
  <wfs:Query typeNames="br:BR_Bodenrichtwert">
    <fes:Filter><fes:PropertyIsEqualTo>
      <fes:ValueReference>br:gehoertZu/@xlink:href</fes:ValueReference>
      <fes:Literal>urn:adv:oid:DEBBBR004WQ0GD1f</fes:Literal>
    </fes:PropertyIsEqualTo></fes:Filter>
  </wfs:Query>
</wfs:GetFeature>'''
# Returns exactly the point record(s) whose gehoertZu references this Flaeche.
# For scale (thousands of zones), prefer: one full-state paginated fetch of
# br:BR_Bodenrichtwert (113,293 records, COUNT=5000 + STARTINDEX), cached to
# data/_cache/boris/, then an in-memory dict join keyed on the stripped OID.
```

---

## State of the Art

| Old approach | Current approach | When changed | Impact |
|---|---|---|---|
| Phase 5's "BBOX + client-side `intersects()`" WFS pattern | Server-side `fes:Intersects` spatial filter (this phase) | This phase | Reduces overselection by up to 3.6x at this feature density; also avoids padding-related edge-feature loss entirely since the exact LL polygon (not a rectangle) is the filter |
| Assuming one WFS schema per "layer type" (Phase 5's 3-designation-but-1-schema-family BfN precedent) | Two genuinely different object models (BRM 2.1 vs 3.0.1) requiring different fetch code paths, not just different field names | This phase | The `build_vector.py`/`fetch_protected_areas.py` "one fetch function, config-driven field names" pattern is insufficient here; BB needs an entirely separate join step HE does not |
| `gpd.clip()` for national-coverage sources (BUEK250) vs. `intersects()`-only for BfN (deliberate, per D-03 there) | This phase has no equivalent "must show full unclipped polygon" decision, so `gpd.clip()` is the recommended default given the volume pressure | This phase | Reduces committed geometry for boundary-straddling zones, unlike protected areas which explicitly kept them full-size |

---

## Runtime State Inventory

*(Included per the "new committed artefacts + live external dependency" convention Phase 5 established, though this is not a rename/refactor phase.)*

| Category | Items found | Action required |
|---|---|---|
| Stored data | None - no database. New committed artefacts: `data/geojson/boris-{slug}.geojson` x5 and `app/public/` copies x5 | New files only; size budget must be resolved first (Open Question 1) |
| Live service config | **BB:** `isk.geobasis-bb.de/ows/boris_wfs` (external, unversioned typenames `br:BR_BodenrichtwertFlaeche`/`br:BR_Bodenrichtwert`). **HE:** `www.gds.hessen.de/wfs2/boris/cgi-bin/brw/2024/wfs` (year-versioned - a future `/2026/wfs` variant will eventually supersede this URL) | Pin both URLs + typenames in `sources.yaml`; add a contract test asserting the layer entry, mirroring `test_buek250_layer_contract_declared` |
| OS-registered state | None | None |
| Secrets/env vars | None - both WFS require no auth | None; do not add `.env` entries |
| Build artefacts | GDAL writes `*.gfs` sidecars next to any `.gml` it reads; a new `data/_cache/boris/` cache directory (for the BB full-state point fetch) needs to exist and be gitignored | `data/_cache/` is already gitignored (verified in `.gitignore` line 12) - reuse that prefix; write GML to `tempfile.TemporaryDirectory()` for the per-request DescribeFeatureType-driven reads, same as `fetch_protected_areas.py` |

---

## Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|---|---|---|---|---|
| Python | pipeline | Yes | 3.12 (`data-pipeline/.venv`) | - |
| geopandas | GML read, reproject, spatial ops | Yes | 1.1.3, verified live | - |
| shapely | `make_valid`, `set_precision`, GML polygon construction | Yes | 2.1.2 | - |
| requests | WFS HTTP GET/POST | Yes | >=2.31 | - |
| pyyaml | `sources.yaml` | Yes | >=6.0 | - |
| Network -> `isk.geobasis-bb.de` | BORIS-BB WFS | Yes | HTTPS 200, verified 2026-07-27 | None - phase cannot complete offline |
| Network -> `www.gds.hessen.de` | BORIS-HE WFS | Yes | HTTPS 200, verified 2026-07-27 | None |
| Network -> `registry.gdi-de.org` | BB codelist lookup (one-time, at authoring time, not needed at pipeline runtime since the table is hardcoded from this research) | Yes | HTTPS 200 | Table is already captured in section 3.1; no runtime dependency |
| leaflet / react-leaflet | Canvas renderer for high feature counts | Yes | ^1.9.4 / ^5.0.0 (per Phase 5 findings) | - |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none.

---

## Security Domain

No `security_enforcement` key in `.planning/config.json`; treated as enabled. This phase introduces the project's **second and third** unauthenticated outbound WFS fetches (after Phase 5's BfN), plus a novel **WFS 2.0 POST request with a hand-built XML body** (Phase 5 only used GET).

### Applicable ASVS categories

| ASVS category | Applies | Standard control |
|---|---|---|
| V2 Authentication | No | Both WFS are public, no credentials |
| V3 Session Management | No | Static SPA, no sessions |
| V4 Access Control | No | Both licences explicitly permit unrestricted reuse |
| V5 Input Validation | **Yes** | WFS responses are untrusted input. Validate `numberMatched`, CRS (`25833` for BB, `25832` for HE - do not conflate), geometry types, `is_valid.all()` before writing. Cap response size given the volume risk in section 5 |
| V6 Cryptography | No | HTTPS mandatory for both endpoints; never downgrade |
| V12 Files & Resources | **Yes** | GML written to disk before GDAL parses it - use `tempfile.TemporaryDirectory()` for per-request reads; the new `data/_cache/boris/` full-state point cache is a deliberate, gitignored, longer-lived exception to that rule (same precedent as `data/_cache/protected-areas/`) |
| V14 Configuration | **Yes** | Both endpoint URLs, typenames, and native CRSs belong in `sources.yaml`, not hard-coded in Python |

### Known threat patterns for this stack

| Pattern | STRIDE | Standard mitigation |
|---|---|---|
| XXE/entity expansion in GML | Tampering, DoS | GDAL's GML driver does not resolve external entities by default; extract `numberMatched`/`numberReturned` via byte-slicing (not XML parsing) as `fetch_protected_areas.py` already does |
| Hand-built XML injection via LL geometry coordinates | Tampering | Coordinates come from the repo-owned `ll_boundaries.geojson`, not user input - low risk, but still format via a dedicated helper (not raw string concatenation of untrusted input) |
| Uncontrolled response size -> memory exhaustion | DoS | The full-state BB point cache alone is expected in the ~100+ MB range (113,293 records); stream to disk rather than holding the full response in memory where practical, and assert a `max_response_bytes` ceiling per request as `fetch_protected_areas.py` does |
| Untrusted attribute values rendered into tooltips | XSS (browser tier) | Follow the existing `createTooltipRow()` pattern (`textContent`, never `innerHTML`) for `bodenrichtwertzoneName`/`bemerkungen` free-text fields |
| Dependency confusion / slopsquatting | Tampering | Zero new packages - surface is empty |

---

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|-------|---------|-----------------|
| A1 | Hessen's `nutzung.art` full code vocabulary is not exhaustively enumerated in this research (only `G` and `LW` directly observed) | 3.2 | The D-11 mapping table could ship with an incomplete Hessen vocabulary at launch; mitigated by the recommended fallback ("Unmapped usage type" + raw code preserved) so it degrades gracefully rather than crashing |
| A2 | `entwicklungszustand` B/R/E/LF/SF <-> 1000/2000/3000/4000/5000 meanings are the standard ImmoWertV taxonomy | 3.3 | Corroborated by WebSearch (code-knacker.de, Brandenburg Gutachterausschuss docs) but not confirmed via an official codelist API call the way the BB `nutzung.art` codelist was; if wrong, Bauerwartungsland (D-07) could be mislabeled in the tooltip |
| A3 | Naive per-LL GeoJSON size scales roughly linearly with feature count (section 5.2) | 5.2 | Larger LLs' zones could be geometrically simpler *or* more complex than Rheingau's average, making the size projections directionally right but not precisely accurate; a Wave 0 measurement on the actual data supersedes this estimate |
| A4 | A "recency threshold" for `has_current_value` (D-08) needs a concrete definition (e.g., most recent Hauptfeststellungszeitraum) | 4.3 | Left as an open, user-facing decision - flagged explicitly in Open Questions rather than guessed |
| A5 | `br:BR_BodenrichtwertFlaeche`'s `inversZu_gehoertZu` field is genuinely never populated by this server (not just missing from the 2 samples inspected) | 4.2 | If it is sometimes populated, the "cached full-state fetch + local join" approach in section 4.3 still works and is strictly safer regardless |

**If this table is empty:** N/A - see above.

---

## Open Questions

1. **What geometry/property size budget is acceptable for the two Brandenburg Living Labs, and what specific `simplify_tolerance`/`coordinate_precision`/column set achieves it?**
   - What we know: rheingau (1,668 zones, HE) measured at 16.7 MB naive. East-brandenburg (30,018 zones, BB) will be substantially larger even after trimming; exact post-mitigation size was not measured in this research session because it requires implementing the harmonization + trimming logic first.
   - What's unclear: whether property trimming + `set_precision`/`simplify` alone bring east-brandenburg under a reasonable per-LL budget (a few MB, matching the soil/protected-areas precedent), or whether a more structural change (courser simplification tolerance than BUEK250's, dropping to a lower coordinate precision, or reconsidering the "ship every individual zone polygon" approach in favor of a raster/PMTiles-rendered choropleth for just the two Brandenburg LLs) is required.
   - Recommendation: insert a **blocking `checkpoint:decision`** as the very first task of this phase's plan (mirroring Phase 5's Pitfall 13/`checkpoint:decision` for coordinate precision), where the executor fetches, harmonizes, trims, and measures the actual output size for `east-brandenburg` specifically (the worst case) *before* any other task proceeds, and the plan branches based on the measured number.

2. **What is the exact Hessen `nutzung.art` code set for the 3 Hessen Living Labs, and what does each code mean?**
   - What we know: `G` (commercial) and `LW` (agricultural) confirmed live; the full set is not confirmed.
   - What's unclear: the complete vocabulary and whether it maps cleanly 1:1 onto BB's 44-entry codelist or needs its own canonical categories for concepts BB's codelist doesn't have an exact Hessen equivalent for.
   - Recommendation: a Wave 0 task should run `GetPropertyValue` (or a full fetch + `.unique()`) scoped to the 3 Hessen LLs to enumerate the actual codes before building the harmonization table, per section 3.2.

3. **What recency threshold defines `has_current_value` for Brandenburg zones (D-08)?**
   - What we know: BB's WFS mixes Stichtage back to 2010 on one endpoint; some zones' only value is old (e.g. one observed Potsdam zone's only record dates to 2010-01-01).
   - What's unclear: is "current" defined as "the single most recent Stichtag among all zones fetched" (relative), "within the last N years" (absolute), or "matches Hessen's reference year, 2024" (cross-state consistency)?
   - Recommendation: surface this as a `checkpoint:decision` or discuss-phase-style question to the user before implementation, since it directly determines how many zones render in the D-08 "no data" style for the two Brandenburg LLs.

---

## Sources

### Primary (HIGH confidence - executed live 2026-07-25/27)
- `https://isk.geobasis-bb.de/ows/boris_wfs?SERVICE=WFS&REQUEST=GetCapabilities&VERSION=2.0.0` - BB service identification, feature types, CRS, output formats, licence
- `https://www.gds.hessen.de/wfs2/boris/cgi-bin/brw/2024/wfs?SERVICE=WFS&REQUEST=GetCapabilities&VERSION=2.0.0` - HE service identification, feature types, CRS, output formats, licence
- `...&REQUEST=DescribeFeatureType&TYPENAMES=br:BR_BodenrichtwertFlaeche` / `br:BR_Bodenrichtwert` / `boris:BR_BodenrichtwertZonal` - full attribute schemas
- `...&REQUEST=GetFeature` (GML) x multiple, both services - live feature inspection, join verification, BBOX axis-order confirmation
- `...&REQUEST=GetFeature&RESULTTYPE=hits` and WFS 2.0 POST `fes:Intersects`/`fes:PropertyIsEqualTo` filters - exact per-LL zone counts (section 5.1) and join verification (section 4.2)
- `https://registry.gdi-de.org/codelist/de.adv-online.gid/BR_Art_Nutzung` - full 44-entry national usage-type codelist, fetched and enumerated in full
- Repo files read: `data-pipeline/python/build_vector.py`, `fetch_protected_areas.py`, `_sources.py`, `sources/sources.yaml`, `app/src/data/layers.js`, `app/src/components/LLMap/index.jsx`, `app/src/components/MapLegend.jsx`, `app/src/i18n.js`, `app/src/theme.js`, `data/ll_boundaries.geojson`, `data/source_catalogue.csv`, `.gitignore`, `.planning/config.json`
- Environment probe: `data-pipeline/.venv` geopandas 1.1.3 confirmed installed and used for live server-side spatial-filter testing

### Secondary (MEDIUM confidence)
- `https://gdk.gdi-de.org/geonetwork/srv/api/records/c1afe4df-1290-42b3-9399-6bfd00652c13` - BORIS Hessen GDI-DE metadata record (WebSearch, not independently re-fetched)
- WebSearch corroboration of the B/R/E/LF/SF ImmoWertV development-status taxonomy (`code-knacker.de/bodenrichtwerte.htm`, Brandenburg Gutachterausschuss public legend references) - the concept is well-documented but the specific PDFs found could not be extracted as machine-readable text in this session

### Tertiary (LOW confidence - flagged, not relied upon)
- `handbuch-boris-hessen-0.pdf` and Brandenburg's `Legende_BRW_ab_2023.pdf` - fetched but could not be extracted as readable text (compressed/encoded PDF streams); no claim in this document rests on their content. If the planner needs the full Hessen usage-code vocabulary, prefer the empirical `GetPropertyValue` sampling approach (section 3.2, Open Question 2) over re-attempting extraction of these PDFs.

---

## Metadata

**Confidence breakdown:**
- WFS endpoints, versions, CRS, output formats: **HIGH** - `GetCapabilities` executed live for both states
- Feature schemas (BB split model, HE self-contained model): **HIGH** - `DescribeFeatureType` + live `GetFeature` value inspection for all three relevant feature types
- Brandenburg point/polygon join mechanics: **HIGH** - both the ID-suffix heuristic and the robust `PropertyIsEqualTo` filter were executed and verified live
- Per-LL exact zone counts: **HIGH** - server-side `fes:Intersects` executed against each LL's real boundary geometry, not estimated
- Usage-type harmonization, Brandenburg side: **HIGH** - full 44-entry codelist fetched and enumerated
- Usage-type harmonization, Hessen side: **MEDIUM-LOW** - only 2 of an unknown-size code set directly observed; explicitly flagged as needing empirical sampling (Open Question 2), not guessed
- Development-status (Bauerwartungsland etc.) mapping: **MEDIUM-HIGH** - schema-confirmed 5-value enums on both sides, semantic meaning corroborated by WebSearch but not by an official codelist API call
- Volume/file-size projections: **HIGH** for the measured LL (rheingau); **MEDIUM** for the extrapolated LLs (linear-scaling assumption, flagged as A3)

**Validation Architecture:** omitted - `.planning/config.json` sets `workflow.nyquist_validation: false`.

**Research date:** 2026-07-27
**Valid until:** ~2026-08-26 (30 days) for endpoint/schema facts. The volume/size numbers are tied to the live datasets' current state and should be re-verified if re-planning is deferred more than a few weeks, since both states' Gutachterausschuesse republish Bodenrichtwerte periodically (Hessen: biennial Stichtage; Brandenburg: continuously mixed into one endpoint).
