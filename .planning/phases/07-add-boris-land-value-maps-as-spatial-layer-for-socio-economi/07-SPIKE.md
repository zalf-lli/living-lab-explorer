# Phase 7 Wave-0 Spike

Run date: 2026-07-28. Every number below was measured live against the BORIS-BB and BORIS-HE WFS services by `data-pipeline/python/probe_boris.py` (plan 07-03), except where explicitly marked as an extrapolation.

## W-01 Volume and geometry fidelity

### east-brandenburg (30095 zones)

| Variant | Bytes | MB | Features | Vertices | Empty | Mean abs rel area change vs N |
|---|---:|---:|---:|---:|---:|---:|
| N | 477,223,290 | 455.12 | 30095 | 11467910 | 0 | n/a |
| A | 173,700,819 | 165.65 | 30095 | 6758756 | 0 | 0.0613 |
| B | 159,323,627 | 151.94 | 30002 | 6721474 | 93 | 0.0726 |
| C | 62,242,012 | 59.36 | 29708 | 2269430 | 387 | 0.0748 |
| D | 57,210,309 | 54.56 | 29060 | 2258032 | 1035 | 0.0830 |
| E | 33,954,375 | 32.38 | 29049 | 1082951 | 1046 | 0.1217 |
| F | 25,741,559 | 24.55 | 28709 | 706491 | 1386 | 0.2069 |

### havelland (18961 zones)

| Variant | Bytes | MB | Features | Vertices | Empty | Mean abs rel area change vs N |
|---|---:|---:|---:|---:|---:|---:|
| N | 352,683,181 | 336.34 | 18961 | 8493653 | 0 | n/a |
| A | 111,438,406 | 106.28 | 18961 | 4338217 | 0 | 0.0762 |
| B | 102,187,687 | 97.45 | 18935 | 4312057 | 26 | 0.0819 |
| C | 38,279,279 | 36.51 | 18835 | 1379780 | 126 | 0.0850 |
| D | 35,126,332 | 33.50 | 18644 | 1364571 | 317 | 0.0880 |
| E | 21,824,138 | 20.81 | 18644 | 692335 | 317 | 0.1194 |
| F | 16,619,590 | 15.85 | 18422 | 454938 | 539 | 0.1687 |

### rheingau (1688 zones)

| Variant | Bytes | MB | Features | Vertices | Empty | Mean abs rel area change vs N |
|---|---:|---:|---:|---:|---:|---:|
| N | 16,696,164 | 15.92 | 1688 | 370685 | 0 | n/a |
| A | 8,051,075 | 7.68 | 1688 | 322604 | 0 | 0.0248 |
| B | 7,065,976 | 6.74 | 1688 | 306283 | 0 | 0.0266 |
| C | 2,019,047 | 1.93 | 1687 | 63411 | 1 | 0.0498 |
| D | 1,886,106 | 1.80 | 1681 | 63162 | 7 | 0.0598 |
| E | 1,193,697 | 1.14 | 1676 | 26445 | 12 | 0.1732 |
| F | 953,429 | 0.91 | 1542 | 17412 | 146 | 0.2486 |

### Projected repository impact (both `data/geojson/` and `app/public/` copies, measured LLs summed + the two un-measured HE LLs extrapolated from rheingau's per-feature average size)

| Variant | Projected total bytes | Projected total MB |
|---|---:|---:|
| N | 1,949,701,079 | 1859.4 |
| A | 710,065,717 | 677.2 |
| B | 645,706,055 | 615.8 |
| C | 236,098,405 | 225.2 |
| D | 217,420,909 | 207.3 |
| E | 132,282,661 | 126.2 |
| F | 101,276,265 | 96.6 |

Budget anchor: the largest per-LL vector GeoJSON committed today is `protected-areas-east-brandenburg.geojson` at 7,582,567 bytes (7.2 MiB); the whole `data/geojson/` tree is ~29 MB; every file in that tree is committed twice.

No measured variant meets a <=8,000,000 byte (<=8 MB) per-LL-per-copy budget for east-brandenburg; a structural change (per-LL PMTiles for the two Brandenburg LLs, or a larger accepted budget) would be required to fit within it.

## W-02 has_current_value recency threshold

| Rule | havelland | east-brandenburg | hessen (all HE LLs) |
|---|---:|---:|---:|
| R1 | 91.9% | 92.8% | 0.0% |
| R2 | 59.4% | 62.9% | 0.0% |
| R3 | 75.7% | 78.1% | 0.0% |

Hessen is 0% by construction: the year-versioned `/2024/wfs` endpoint only ever returns the 2024 vintage, so every HE zone is current under every rule.

### havelland max(stichtag).year histogram (matched zones only)

| Year | Zones |
|---:|---:|
| 2010 | 738 |
| 2011 | 882 |
| 2012 | 1716 |
| 2013 | 860 |
| 2014 | 865 |
| 2015 | 903 |
| 2016 | 936 |
| 2017 | 1002 |
| 2018 | 1065 |
| 2019 | 1114 |
| 2020 | 1179 |
| 2022 | 1538 |
| 2023 | 1549 |
| 2024 | 1547 |
| 2025 | 1536 |
| 2026 | 1531 |

### east-brandenburg max(stichtag).year histogram (matched zones only)

| Year | Zones |
|---:|---:|
| 2010 | 1636 |
| 2011 | 1443 |
| 2012 | 3040 |
| 2013 | 1623 |
| 2014 | 1623 |
| 2015 | 1620 |
| 2016 | 1640 |
| 2017 | 1554 |
| 2018 | 1562 |
| 2019 | 1600 |
| 2020 | 1590 |
| 2022 | 2291 |
| 2023 | 2270 |
| 2024 | 2293 |
| 2025 | 2138 |
| 2026 | 2172 |

## W-03 Hessen usage-code vocabulary

| HE code | Occurrences (3 Hessen LLs) | Proposed canonical target |
|---|---:|---|
| W | 2693 | 1100 (Wohnbauflaeche) |
| M | 2160 | 1200 (gemischte Baufl.) |
| F | 1395 | 2800 (forstwirtschaftliche Fl.) |
| A | 1177 | 2100 (Acker) |
| GR | 1147 | 2200 (Gruenland) |
| WA | 1020 | 1130 (allgemeines Wohngebiet) |
| G | 715 | 1300 (gewerbliche Baufl.) |
| KGA | 582 | 3020 (Kleingartenfl.) |
| MI | 478 | 1230 (Mischgebiet) |
| FGA | 447 | 3030 (Freizeitgartenfl.) |
| GB | 424 | 1500 (Baufl. fuer Gemeinbedarf) |
| LW | 384 | UNMAPPABLE |
| GE | 381 | 1310 (Gewerbegebiet) |
| PG | 281 | 3010 (private Gruenfl.) |
| SO | 225 | 1420 (sonstige Sondergebiete) |
| MD | 222 | 1210 (Dorfgebiet) |
| FH | 207 | 3070 (Friedhof) |
| SPO | 135 | 3050 (Sportfl.) |
| S | 131 | 1400 (Sonderbaufl.) |
| SE | 118 | 1410 (Sondergebiet fuer Erholung) |
| WR | 80 | 1120 (reines Wohngebiet) |
| GF | 71 | 3130 (Gemeinbedarfsfl., kein Bauland) |
| GI | 61 | 1320 (Industriegebiet) |
| SN | 48 | 3140 (Sondernutzungsfl.) |
| SG | 37 | 3060 (sonstige private Fl.) |
| WG | 34 | 2500 (Weingarten) |
| WB | 28 | 1140 (besonderes Wohngebiet) |
| MK | 28 | 1240 (Kerngebiet) |
| WS | 10 | 1110 (Kleinsiedlungsgebiet) |
| CA | 10 | 3040 (Campingplatz) |
| FP | 4 | 3090 (Flughafen, Flugplaetze) |
| EGA | 2 | 2300 (Erwerbsgartenbaufl.) |
| LG | 1 | 3110 (Lagerfl.) |

### entwicklungszustand union (3 Hessen LLs)

| Code | Occurrences | In expected {B,R,E,LF,SF}? |
|---|---:|---|
| B | 8642 | yes |
| LF | 4139 | yes |
| SF | 1823 | yes |
| R | 84 | yes |
| E | 48 | yes |

## Open items for the checkpoint

1. Which W-01 volume/fidelity variant (or a structural alternative such as per-LL PMTiles for the two Brandenburg Living Labs) to lock for the committed BORIS GeoJSON output, given the measured per-LL-per-copy byte budget above.
2. Which W-02 recency rule (R1 relative, R2 >=2022-01-01, or R3 >=2024-01-01) sets `has_current_value`, given the measured false-percentage per rule per Brandenburg Living Lab above.
3. Which proposed W-03 HE-to-canonical usage-code mappings to confirm or adjust, and how to handle any UNMAPPABLE HE code (for example `LW`, which does not exactly match any BB abbreviation).

## Locked Wave-0 Decisions

### W-01 Geometry fidelity and size budget

**Chosen option:** `w01-raise-budget` (W-01 B — accept a larger per-Living-Lab budget in exchange for
higher geometric fidelity), variant **E**.

- `coordinate_precision`: **0.0001** decimal degrees (~11 m)
- `simplify_tolerance`: **0.0005** decimal degrees (~55 m)
- Accepted per-Living-Lab-per-copy byte budget: **~33 MB (33,000,000 bytes)**
- Measured east-brandenburg size at variant E: **33,954,375 bytes (32.38 MB)**, 29,049 of 30,095
  features surviving, 1,046 geometries collapsing to empty, mean abs rel area change 0.1217
- Measured havelland at E: 21,824,138 bytes (20.81 MB)
- Measured rheingau at E: 1,193,697 bytes (1.14 MB)
- Projected total repository impact (all 5 Living Labs x both committed copies, `data/geojson/` +
  `app/public/data/geojson/`): **132,282,661 bytes (126.2 MB)**
- Output format: **GeoJSON for all five Living Labs.** No re-plan of 07-06..07-09 is required.

**Rationale:**
- There is no backend server; the app is served statically from GitHub Pages, so GitHub file/repo size
  limits are the binding constraint, not a server-side storage budget.
- `w01-fit-budget` (fit an 8 MB/LL/copy budget) is **not achievable** — no measured variant meets it for
  east-brandenburg; the smallest, variant F, is 24.55 MB.
- `w01-structural` (per-LL PMTiles for the two Brandenburg Living Labs) was **rejected**: its premise is
  false for this vector data. `data-pipeline/python/build_pmtiles.py` builds *raster* PMTiles via
  rasterio/`rio`; `app/src/components/LLMap/index.jsx` imports `leafletRasterLayer` and the app has no
  vector-tile renderer (no maplibre-gl, no protomaps-leaflet in `app/package.json`); `tippecanoe` is not
  installed and has no official Windows build. Raster tiles also carry no per-feature attributes, which
  would break the D-12 tooltip, the client-side quantile bucketing, and the data-driven legend that plan
  07-04 already implemented.
- Measured gzip ratio on this repo's own largest committed GeoJSON
  (`data/geojson/protected-areas-east-brandenburg.geojson`, 7,582,567 bytes -> 2,047,526 bytes at gzip
  -6, 3.7x) implies variant E costs roughly 8.7 MB over the wire for east-brandenburg, assuming GitHub
  Pages gzips `.geojson`. Verify this on first deploy; pre-compress if it does not.
- Variant E's largest single file (32.38 MB) sits below GitHub's 50 MB warning threshold and well below
  the 100 MB hard block. `.git` is currently 541 MB against a 1 GB recommended ceiling.
- **Deliberately out of scope for Phase 7** (tracked separately, do not implement here): `app/public/data/`
  is a committed duplicate of `data/`, and `.github/workflows/deploy-pages.yml` never runs Python. Adding
  a plain copy step to that workflow and gitignoring `app/public/data/` would halve every projected figure
  above.

### W-02 has_current_value recency rule

**Chosen rule:** rolling 10-year window (a self-maintaining generalisation of R2/R3).

- Predicate to implement: **`max(stichtag) >= (run_year - 10)-01-01`**
- Evaluated at the 2026 run date: **`max(stichtag) >= "2016-01-01"`**
- Stated criterion: aligning the recency bar to Hessen's vintage is not important; **maximal coverage**
  of the map is the goal.
- Recomputed impact (derived independently from the `max(stichtag).year` histograms above; agrees with
  the values reported at checkpoint time, no discrepancy found):
  - **havelland:** 12,997 of 18,961 matched zones have `max(stichtag).year >= 2016` ->
    **68.54% coloured / 31.46% no-current-value**.
  - **east-brandenburg:** 19,110 of 30,095 matched zones have `max(stichtag).year >= 2016` ->
    **63.50% coloured / 36.50% no-current-value**.
  - **hessen (all 3 HE Living Labs):** 0% no-current-value (unchanged from the table above).

**Rationale:**
- Hessen publishes biennial WFS vintages and 2026 is NOT yet available. Live probe on 2026-07-28 of
  `https://www.gds.hessen.de/wfs2/boris/cgi-bin/brw/{year}/wfs?service=WFS&request=GetCapabilities`
  returned HTTP 404 for 2026 and 2025, HTTP 200 "WFS HE BORIS 2024" for 2024, and HTTP 200 "WFS HE BORIS
  2022" for 2022. The 2026 Stichtag data visible in the Hessen geoportal is a WMS/portal view carrying no
  per-zone attributes, so it cannot feed this choropleth.
- Rule R1 (relative to the newest year present in each Living Lab) was rejected: Brandenburg revalues on
  a rolling staggered cycle, so R1 would mark ~92% of Brandenburg zones as current against 0% no-data in
  Hessen — an artifact of publication cadence, not of land values.

### W-03 Hessen usage-code map

All 32 cleanly-proposed HE-code rows below are approved unchanged. `LW` is deliberately UNMAPPABLE and is
NOT given an invented canonical target; it falls to the bilingual fallback below with the raw code `LW`
preserved in `usage_type_code`. The same fallback applies to any Hessen code not present in this table.

| HE raw code | Canonical BB codelist code | EN | DE |
|---|---|---|---|
| W | 1100 | Residential building area | Wohnbaufläche |
| M | 1200 | Mixed building area | Gemischte Baufläche |
| F | 2800 | Forestry area | Forstwirtschaftliche Fläche |
| A | 2100 | Arable land | Acker |
| GR | 2200 | Grassland | Grünland |
| WA | 1130 | General residential area | Allgemeines Wohngebiet |
| G | 1300 | Commercial building area | Gewerbliche Baufläche |
| KGA | 3020 | Allotment garden area | Kleingartenfläche |
| MI | 1230 | Mixed-use area | Mischgebiet |
| FGA | 3030 | Recreational garden area | Freizeitgartenfläche |
| GB | 1500 | Public-facility building area | Baufläche für Gemeinbedarf |
| LW | UNMAPPABLE | Unmapped usage type | Nicht zugeordneter Nutzungstyp |
| GE | 1310 | Commercial zone | Gewerbegebiet |
| PG | 3010 | Private green area | Private Grünfläche |
| SO | 1420 | Other special-purpose area | Sonstige Sondergebiete |
| MD | 1210 | Village area | Dorfgebiet |
| FH | 3070 | Cemetery | Friedhof |
| SPO | 3050 | Sports area | Sportfläche |
| S | 1400 | Special building area | Sonderbaufläche |
| SE | 1410 | Special recreational area | Sondergebiet für Erholung |
| WR | 1120 | Pure residential area | Reines Wohngebiet |
| GF | 3130 | Public-facility area, non-building land | Gemeinbedarfsfläche, kein Bauland |
| GI | 1320 | Industrial zone | Industriegebiet |
| SN | 3140 | Special-use area | Sondernutzungsfläche |
| SG | 3060 | Other private area | Sonstige private Fläche |
| WG | 2500 | Vineyard | Weingarten |
| WB | 1140 | Special residential area | Besonderes Wohngebiet |
| MK | 1240 | Core area | Kerngebiet |
| WS | 1110 | Small settlement area | Kleinsiedlungsgebiet |
| CA | 3040 | Campsite | Campingplatz |
| FP | 3090 | Airport, airfields | Flughafen, Flugplätze |
| EGA | 2300 | Commercial horticulture area | Erwerbsgartenbaufläche |
| LG | 3110 | Storage area | Lagerfläche |

Fallback statement: any Hessen code absent from this table (or explicitly `LW`) maps to
`("Unmapped usage type", "Nicht zugeordneter Nutzungstyp")` with the raw code preserved in
`usage_type_code`.

`entwicklungszustand` needs no decision: all five observed codes (B 8642, LF 4139, SF 1823, R 84, E 48)
fall inside the expected {B, R, E, LF, SF} set.

---

Checkpoint answered 2026-07-28. Plans 07-06 and 07-07 must transcribe these values rather than
re-deriving them.

