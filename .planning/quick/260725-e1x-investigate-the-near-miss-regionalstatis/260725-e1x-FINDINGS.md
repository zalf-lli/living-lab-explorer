# Findings: Live-probe of the three near-miss 32221 Regionalstatistik.de water tables

## CORRECTION -- this is the live-verified re-run

An earlier version of this document (and the accompanying PROBE.json) was produced while this
worktree had no `.env` file at all, so every live-probe attempt failed at the Regionalstatistik.de
auth gate before any table content could be inspected. A working `.env` (matching the repo-root
copy) was subsequently added to this worktree. This document has been fully rewritten against the
**real, live API responses** obtained after that fix -- every claim below is a live observation,
not inference, unless explicitly marked otherwise.

## Summary of the live probe

All three tables **live-verify at Kreis level for all 14 of this project's AGS codes**, across
five survey years (2010, 2013, 2016, 2019, 2022 -- confirming the plan's expectation of a
triennial-ish survey with gaps). All three tables' `metadata/table` response carries **`Valid:
false`** -- catalogue/tables confirms there is no successor code at the `3222*` prefix that
supersedes them, so this flag most likely reflects "this survey wave (through 2022) is the latest
published, no newer wave yet" rather than the pre-2007 kind of definitive staleness the plan's
context flagged for the `41120-*` series (that series' `Time.To` was 2007, over 15 years out of
date; here `Time.To` is 2022, the most recent year the search returned for anything under this
statistic). All three tables belong to statistic **32221, "Erhebung der nichtöffentlichen
Wasserversorgung und Abwasserentsorgung"** (survey of NON-PUBLIC water supply/wastewater disposal
-- i.e. self-supplying industrial, agricultural, and private users, NOT municipal drinking-water
systems). Every reported value across all three tables is a **volume in `1000 cbm`** (thousand
cubic metres) -- confirmed directly from the `value_unit` column of the live ffcsv response, not
inferred from a title.

The critical new finding: **`32221-01-03-4` has an explicit Grundwasser (groundwater) category.**
Its `Wasserart` (water-type) classifying dimension carries 8 categories, one of which is
`WASSERGRUND = "Grundwasser"` -- a genuine, live-confirmed groundwater-specific abstraction volume,
covering all 14 Kreise across all 5 survey years, with only 2 of 70 Kreis-year cells suppressed
(both in the earliest 2010 wave; every Kreis still resolves to a real, recent value via
"latest year wins"). This is the scenario the plan explicitly flagged as "the strongest possible
repurpose candidate" if confirmed -- and it is now confirmed.

## Comparison table

| Table | Title (live-verified) | Status | Years | Kreis coverage | What it measures (live-verified) | Unit | Groundwater-specific breakdown? |
|---|---|---|---|---|---|---|---|
| `32221-01-03-4` | "Wassergewinnung und -bezug - 31.12. / Jahressumme" (water abstraction/procurement) | `kreis-verified` | 2010, 2013, 2016, 2019, 2022 | 14/14 | Volume of water abstracted/procured, by water source | 1000 cbm | **YES** -- `WASSERGRUND` = Grundwasser category, live-confirmed |
| `32221-02-01-4` | "Wassereinsatz und ungenutztes Wasser - Jahressumme" (water use / unused water) | `kreis-verified` | 2010, 2013, 2016, 2019, 2022 | 14/14 | Volume of water used within operations, by purpose (cooling, production, staff) | 1000 cbm | No -- no water-source dimension exists in this table at all |
| `32221-03-01-4` | "Abwasserverbleib - Jahressumme" (wastewater disposal destination) | `kreis-verified` | 2010, 2013, 2016, 2019, 2022 | 14/14 | Volume of wastewater, by disposal destination (sewer, own treatment plant, direct discharge) | 1000 cbm | No -- measures discharge destination, not water source or quality |

## Per-table notes

### `32221-01-03-4` -- "Wassergewinnung und -bezug"

Live-fetched via `fetch_regionalstatistik_table("32221-01-03-4", force=True)`: 700 rows, all 14
project AGS codes present across all 5 survey years. `metadata/table`'s `Structure.Columns` shows
the `WAS001` ("Wasseraufkommen") value column cross-classified by TWO dimensions: `WASBZ1`
("Wasserentnahme und -bezug", withdrawal vs. external supply -- only `WASBZ102` "Fremdbezug von
Wasser" appears in the actual Kreis-level data) and `WASAT2` ("Wasserart", water type, 8
categories). The `WASAT2` inventory, read directly off the live response:

- `WASAT1001` -- Uferfiltrat (bank filtrate)
- `WASAT1002` -- angereichertes Grundwasser (enriched/artificially recharged groundwater)
- `WASAT1003` -- See- und Talsperrenwasser (lake/reservoir water)
- `WASAT1004` -- Flusswasser (river water)
- `WASAT1005` -- Meer- und Brackwasser (sea/brackish water)
- `WASAT1006` -- andere Wasserarten (other water types)
- **`WASSERGRUND` -- Grundwasser (groundwater)**
- `WASSERQUELL` -- Quellwasser (spring water)

For AGS `12064` (Märkisch-Oderland, the project's standard sanity-check Kreis), the `WASSERGRUND`
category's latest (2022) value is **12,927 (1000 cbm)**, with prior years 2010/2013/2016/2019
reading 12,885 / 13,044 / 13,647 / 13,722 -- a stable, plausible time series for a rural
Brandenburg Kreis. Across all 14 project Kreise, latest-year Grundwasser abstraction values range
from 74 (1000 cbm, Rheingau-Taunus-Kreis) to 12,927 (1000 cbm, Märkisch-Oderland), a spread
consistent with differing Kreis size/industrial-agricultural activity. Only 2 of the 70
Kreis-year cells for this category are privacy-suppressed (`.`), both in the 2010 wave for
Dahme-Spreewald and Oberhavel -- every one of the 14 Kreise still resolves to a real "latest
non-null" value.

The statistic's own head label (`metadata/table`'s `Structure.Head.Content`) is "Erhebung der
nichtöffentlichen Wasserversorgung und Abwasserentsorgung" -- this is specifically about
**non-public** (self-supplying) water abstraction: industrial plants, farms, and private
self-suppliers who draw their own water rather than buying from a municipal utility. For a rural,
agriculturally-oriented Living Lab audience, this is arguably a MORE relevant slice of groundwater
pressure than municipal supply figures would be, since it captures exactly the sector (agriculture
and industry) whose water draw is of greatest environmental-pressure interest.

### `32221-02-01-4` -- "Wassereinsatz und ungenutztes Wasser"

Live-fetched: 280 rows, 14/14 AGS codes, same 5 years. Two classifying dimensions in the live data:
`WASVB2` ("Art der Wasserverwendung", 1 category: "im Betrieb eingesetztes Frischwasser" -- fresh
water used within the operation) and `WASVB3` ("Nutzungsarten", 3 categories: cooling of
production/power-generation plants, production/commercial/other purposes, workforce/staff
purposes). There is NO water-source dimension anywhere in this table -- it cannot be broken down by
groundwater vs. any other source at all. For AGS 12064, the 2022 "im Betrieb eingesetztes
Frischwasser" value is 1,457 (1000 cbm). This table answers "how is water used once it's obtained",
not "where does the water come from" -- irrelevant to a groundwater-specific indicator regardless
of the concentration-vs-volume question.

### `32221-03-01-4` -- "Abwasserverbleib"

Live-fetched: 350 rows, 14/14 AGS codes, same 5 years. One classifying dimension, `WASVB4` ("Art
der Einleitung von Abwasser", disposal route): public sewer/treatment plant, own treatment plant,
other establishments, direct discharge to surface water/underground, plus an "Insgesamt" (total)
row. For AGS 12064, the 2022 total (`WASNW3`, blank attr code) is 685 (1000 cbm). This measures
where wastewater GOES, not what is dissolved in groundwater or where the water originally came
from -- the weakest of the three candidates on every dimension.

## Requirements of the `groundwater_nitrate_mg_l` slot

The `groundwater_nitrate_mg_l` curated KPI slot (Soil tab, D-08/D-09) declares its unit as **mg
NO3/l** -- a concentration. Live-confirmed: every value in all three tables is reported in `1000
cbm` -- a volume. This is now a live-verified fact, not an inference: none of the three tables can
ever fill the `groundwater_nitrate_mg_l` slot AS DEFINED (same variable_key, same mg NO3/l unit),
because a volume can never satisfy a concentration requirement, per 04-07's same-real-world-quantity
rule. This holds even for `32221-01-03-4`'s Grundwasser-specific breakdown -- it is a groundwater
*abstraction volume* (how much groundwater is pumped), not a groundwater *nitrate concentration*
(how contaminated the groundwater is). These are different, non-substitutable real-world
quantities.

However, `32221-01-03-4`'s Grundwasser category is a live-verified, Kreis-complete, 5-year,
plausible-magnitude dataset measuring a genuinely different but thematically-adjacent
environmental quantity: groundwater abstraction pressure. Per the plan's own D-14 substitution
mechanism (swap in the next-best variable from the SAME catalogue group -- Environment -- rather
than leaving the slot empty), this is evaluated as a REPURPOSE candidate in
`260725-e1x-DECISION.md`, not folded into this document's per-table verdict. See DECISION.md for
the full 5-gate rubric evaluation and the recorded verdict.

## Evidence trail

- Live probe script (session scratchpad, not committed, not part of the pipeline) imports
  `fetch_destatis` via `sys.path.insert(0, "python")` and calls `fd.check_auth()`,
  `fd._post("catalogue/tables", ...)`, `fd._post("metadata/table", ...)`, and
  `fd.fetch_regionalstatistik_table(..., force=True)` for all three tables.
- `fd.check_auth(base=fd.REGIONALSTATISTIK_BASE)` succeeded: `[ok] Regionalstatistik.de auth
  verified (Sie wurden erfolgreich an- und abgemeldet! ...)`.
- `catalogue/tables` (`selection=32221*`) returned all three table codes with live titles and a
  `2007 - 2022` time range for each.
- `metadata/table` for each of the three tables returned `Valid: false`, `Time: {From: 2007, To:
  2022}`, statistic head "Erhebung der nichtöffentlichen Wasserversorgung und
  Abwasserentsorgung", and (for `32221-01-03-4` only) a `WASAT2` "Wasserart" column with 8
  declared category values.
- A broader `catalogue/tables selection=3222*` search confirmed no successor/newer table code
  exists for statistic 32221 at Kreis depth -- these three ARE the current dash-coded offering.
- `fetch_regionalstatistik_table()` for all three tables returned real Kreis-level rows (700, 280,
  350 rows respectively), all matching one of this project's 14 AGS codes.
- Raw ffcsv caches committed: `data/destatis_raw/32221-01-03-4__regionalstatistik.csv`,
  `32221-02-01-4__regionalstatistik.csv`, `32221-03-01-4__regionalstatistik.csv`. Each grepped for
  the literal `DESTATIS_API_TOKEN` and `REGIONALSTATISTIK_PASSWORD` values loaded from `.env` --
  zero matches in all three files.
- See `260725-e1x-PROBE.json` for the full machine-readable record backing every claim above.
