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

### havellandisches-luch (18961 zones)

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

| Rule | havellandisches-luch | east-brandenburg | hessen (all HE LLs) |
|---|---:|---:|---:|
| R1 | 91.9% | 92.8% | 0.0% |
| R2 | 59.4% | 62.9% | 0.0% |
| R3 | 75.7% | 78.1% | 0.0% |

Hessen is 0% by construction: the year-versioned `/2024/wfs` endpoint only ever returns the 2024 vintage, so every HE zone is current under every rule.

### havellandisches-luch max(stichtag).year histogram (matched zones only)

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

