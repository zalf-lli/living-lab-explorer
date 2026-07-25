# Decision: the three near-miss 32221 water tables vs. `groundwater_nitrate_mg_l`

## CORRECTION -- this is the live-verified re-run

An earlier version of this document recorded a "reject all three tables" placeholder verdict
while this worktree's Regionalstatistik.de probe was fully credential-blocked (no working
`.env`). A working `.env` was subsequently added, the live probe was re-run for real (see the
corrected `260725-e1x-PROBE.json` / `260725-e1x-FINDINGS.md`), and this document has been
rewritten against that real evidence. **The verdict recorded under `## Verdict` below supersedes
that earlier placeholder and is the only verdict this document endorses.**

## Gate evaluation (against live-verified PROBE.json evidence)

**Gate 1 -- Same-quantity gate:** FAIL for all three tables, now live-verified rather than
inferred.

Every value in all three tables is reported in `1000 cbm` (confirmed directly from the live
`value_unit` column of the ffcsv response). `groundwater_nitrate_mg_l` declares a concentration,
`mg NO3/l`. A volume can never satisfy a concentration requirement, per 04-07's
same-real-world-quantity rule -- this holds even for `32221-01-03-4`'s live-confirmed
groundwater-specific breakdown (`WASSERGRUND`), which is a groundwater *abstraction volume*
(how much groundwater is pumped), not a groundwater *nitrate concentration* (how contaminated the
groundwater is). **`groundwater_nitrate_mg_l`, as originally defined, can never be filled by any
of these three tables.** This conclusion is now a live-verified fact, not an inference -- it does
not change the plan's earlier inference-based conclusion, but it does upgrade its evidentiary
status.

Because Gate 1 fails for the ORIGINAL variable_key, the question becomes whether a **D-14
same-catalogue-group substitution** (a different Environment-group variable entirely, occupying
the same Soil-tab slot) is defensible. Gates 2-5 below evaluate exactly that, per the plan's own
explicit framing of this exact scenario ("if `32221-01-03-4` breaks abstraction down by water
source, a groundwater-specific abstraction volume exists and is the strongest possible repurpose
candidate").

**Gate 2 -- Kreis-depth gate:** PASS for all three tables, live-verified.

`fetch_regionalstatistik_table()` returned real Kreis-level rows for all three tables, with all
14 project AGS codes present across 5 survey years (2010, 2013, 2016, 2019, 2022) in every case.
For `32221-01-03-4`'s specific Grundwasser (`WASSERGRUND`) category: 70 of 70 possible
Kreis-year cells exist, with only 2 privacy-suppressed (both in the 2010 wave, for
Dahme-Spreewald and Oberhavel) -- every one of the 14 Kreise still resolves to a real, recent
non-null value via "latest year wins". This is a strong pass, not a marginal one.

**Gate 3 -- Indicator-defensibility gate:** STRONG PASS for `32221-01-03-4`'s Grundwasser
category; FAIL for the other two candidates.

`32221-01-03-4`'s Grundwasser-specific abstraction volume answers a real, Living-Lab-relevant
question: how much groundwater is being pumped by non-public (self-supplying industrial,
agricultural, and private) users in each Kreis. This statistic (32221, "Erhebung der
nichtöffentlichen Wasserversorgung und Abwasserentsorgung") explicitly excludes municipal supply,
meaning it isolates exactly the sector -- agriculture and industry -- whose groundwater draw is of
greatest environmental-pressure interest to a rural Living Lab audience. It speaks directly to
groundwater pressure, thematically adjacent to the Soil tab's water/nutrient concerns (even though
it does not answer the water-QUALITY question the original nitrate slot was meant to answer).
`32221-02-01-4` (water use by purpose, no source dimension) and `32221-03-01-4` (wastewater
disposal destination) are municipal/industrial-infrastructure figures that tell a Living Lab
researcher little about the landscape -- neither has any water-source dimension at all, so neither
could ever isolate a groundwater-specific figure even in principle. Judged on substance: only the
`32221-01-03-4` Grundwasser candidate passes this gate.

**Gate 4 -- Integration-correctness gate:** PASS, no new derivation logic required.

Groundwater abstraction volume is a straightforward `_SUM` field (summed across Kreise for the
LL-level aggregate), exactly like every other absolute-volume/absolute-area curated field
(`forest_area_ha`, `land_area_cropland_ha`, etc.) -- no per-capita or per-area normalisation was
judged necessary (raw absolute volume is itself a meaningful "how much groundwater pressure in
this Kreis" figure, and the plan's existing pattern for other absolute-magnitude fields does not
normalise them either). Mapped via a single new `REGIONALSTATISTIK_TABLES` entry (`table:
"32221-01-03-4"`, `value_variable_code: "WAS001"`, `attr_code: "WASSERGRUND"`, `unit_factor:
1.0`) and a `direct_output_fields` addition -- no new formula, no new derived-field logic, no
duplicated percentage-calc code.

One caveat worth recording under Gate 4: `metadata/table` reports `Valid: false` for this table.
A `catalogue/tables selection=3222*` search confirmed no successor/newer table code exists at this
prefix, so this is very likely "latest survey wave, no newer wave published yet" rather than
"superseded, do not use" (contrast with the `41120-*` series, whose `Time.To` was 2007 -- over 15
years stale -- while this table's `Time.To` is 2022, the most recent year available). This is
flagged as a maintainability risk (future `--force` re-fetches will keep returning 2022 as the
latest year until Destatis publishes triennial wave 2025+), not a data-quality blocker.

**Gate 5 -- Tab/contract gate:** PASS.

The repurpose stays on the Soil tab (D-08/D-09's locked assignment), does not change the
per-tab counts (`{landuse:4, soil:3, climate:2, landscape:4, economic:4}` unchanged, still 17
entries total), and the new catalogue row is added to the `Environment` group -- the same group
`groundwater_nitrate_mg_l` belonged to -- satisfying D-14's "same catalogue group" substitution
requirement exactly.

## Verdict

**REPURPOSE:groundwater_abstraction_1000m3**

## Reasoning

Gate 1 fails decisively and is now a live-verified fact: no table reports a nitrate concentration,
so `groundwater_nitrate_mg_l` as originally defined can never be filled by any of the three
candidates, regardless of credentials or further investigation. That said, D-14 does not require
leaving the slot null when the ORIGINAL indicator is unfillable -- it explicitly sanctions
substituting the next-best variable from the SAME catalogue group (Environment) rather than
leaving an empty panel. `32221-01-03-4`'s live-confirmed Grundwasser abstraction volume passes
every one of Gates 2-5 cleanly: full Kreis coverage (14/14, only 2/70 cells suppressed, both
recoverable via latest-year-wins), a substantively defensible environmental question (groundwater
abstraction pressure from exactly the non-public/agricultural-industrial sector a Living Lab
audience cares about), trivial integration via existing `_SUM` machinery with no new derivation
code, and full compliance with the locked Soil-tab slot and 17-entry/per-tab-count contract. The
other two candidate tables (`32221-02-01-4`, `32221-03-01-4`) fail Gate 3 outright -- neither has
any water-source dimension, so neither could ever isolate a groundwater-specific figure even in
principle -- and are therefore rejected as repurpose candidates (they remain live-verified-but-
unused evidence, same as before).

This verdict was reached by evaluating substance, not by a desire to fill an empty panel: the
Soil tab's other two slots (`n_surplus_kg_ha`, `p_surplus_kg_ha`) remain genuinely null after
exhaustive search (unaffected by this task), so the Soil tab goes from 0/3 to 1/3 real values --
a real but partial improvement, not a full fix, and one this decision earns through Gate 3's
substantive defensibility test rather than through unit-rescaling or a weakened same-quantity
rule.

## What was applied

1. Added one row to `data/destatis_variables_catalogue.csv`: `group=Environment`,
   `variable_key=groundwater_abstraction_1000m3`, `genesis_table=32221-01-03-4`,
   `label_en=Groundwater abstraction (non-public supply)`,
   `label_de=Grundwasserentnahme (nichtoeffentliche Versorgung)`, `unit_en=1000 m3`,
   `unit_de=1000 cbm`.
2. Added a `REGIONALSTATISTIK_TABLES["groundwater_abstraction_1000m3"]` spec (`table:
   "32221-01-03-4"`, `value_variable_code: "WAS001"`, `attr_code: "WASSERGRUND"`,
   `unit_factor: 1.0`) to `fetch_destatis.py`.
3. Added `"groundwater_abstraction_1000m3"` to `apply_regionalstatistik_indicators()`'s
   `direct_output_fields` set.
4. Changed the `soil` slot's `variable_key` in `CURATED_KPIS` from `groundwater_nitrate_mg_l` to
   `groundwater_abstraction_1000m3` (`genesis_table` updated to `32221-01-03-4` for documentation
   -- this GENESIS-format lookup is expected to fail on `genesis.destatis.de`, which is exactly
   what triggers the Regionalstatistik.de fallback path). The other 16 entries are untouched.
5. Registered `groundwater_abstraction_1000m3` in `_SUM` (volume field, summed across Kreise at
   LL level). Left `groundwater_nitrate_mg_l` in `_MEAN` untouched per the plan's own guidance
   (a stale, no-longer-produced entry there is harmless -- it yields `None` -- while removing it
   risked no benefit).
6. Added `groundwater_abstraction_1000m3` to `FIELD_LABELS` ("Groundwater abstraction, non-public
   supply (1000 m3)") and `FIELD_THEME` (theme `"Nature & environment"`, alongside the other
   Environment fields) so the expert-review CSVs (`destatis_nuts3_export.csv`,
   `destatis_variables.csv`) carry the new column.
7. Ran `python python/fetch_destatis.py --force` from `data-pipeline/`. Resolution log confirmed:
   `[ok] groundwater_abstraction_1000m3 resolved via Regionalstatistik.de (32221-01-03-4)`.
   Sanity-checked magnitudes for AGS 12064 (DE409, Märkisch-Oderland): 12,927 (1000 cbm) for
   2022, consistent with the Task 1 probe. All 14 Kreise resolve to non-null values, range 74
   (Rheingau-Taunus-Kreis) to 12,927 (Märkisch-Oderland) (1000 cbm). LL-level aggregates
   (`data/destatis_ll.json`) are correct sums of their constituent Kreise (e.g.
   `east-brandenburg`: 20,656 = 12,927 + 1,204 + 3,496 + 3,029, matching DE409+DE40A+DE40B+DE40C
   exactly).
8. Updated `04-07-SUMMARY.md`'s `groundwater_nitrate_mg_l` Known Stubs bullet to record that this
   slot moved OUT of the null set via a D-14 repurpose, linking this document. 04-07's original
   history (catalogue-title-only rejection at the time) is preserved unedited elsewhere in that
   document -- only the one bullet is updated in place, per the plan's own instruction.
9. `test_pipeline_outputs.py`: NOT extended. The two existing manifest tests
   (`test_destatis_curated_kpis_manifest_matches_contract`, which asserts 17 entries, the 8-key
   set, `source_host` values, and locked per-tab counts; `test_destatis_resolved_slots_have_real_
   values`, which asserts every non-null-`source_host` slot has real Kreis values) already fully
   cover this change -- the repurposed slot's `source_host="regionalstatistik"` and non-null
   values across all 14 Kreise are covered by these existing assertions with no gaps. Re-ran
   `pytest tests/test_pipeline_outputs.py -q`: 7 passed, no regressions.

`.planning/STATE.md`'s Active Work paragraph is updated separately (not a pipeline file) to
record 6 null slots (down from 7) and cite this repurpose.

## Not now, but revisitable

- If Regionalstatistik.de ever publishes a successor to statistic 32221 with a `Valid: true`
  flag and a newer survey wave (2025+), `fetch_destatis.py --force` would need to be re-pointed
  at the new table code once it is discovered -- the current `32221-01-03-4` code has no known
  successor as of this task's `catalogue/tables selection=3222*` search, so this is a future
  maintenance item, not an immediate action.
- `groundwater_nitrate_mg_l` itself remains permanently unfillable from Destatis-family sources
  (both GENESIS-Online and Regionalstatistik.de only publish water abstraction/usage/disposal
  volumes under statistic 32221, never a nitrate concentration). The genuinely defensible path to
  a real nitrate-concentration indicator remains a non-Destatis source (UBA, LAWA, or similar
  water-quality monitoring body), unaffected by this task's findings -- if such a source is ever
  integrated in a future phase, it would need its OWN new curated slot (or a further D-14
  substitution back onto the Soil tab), since `groundwater_abstraction_1000m3` now occupies the
  slot `groundwater_nitrate_mg_l` used to hold.
- `32221-02-01-4` and `32221-03-01-4` remain live-verified-but-unused: genuinely different
  quantities (water-use-by-purpose, wastewater-disposal-destination) with no water-source
  dimension, correctly rejected as repurpose candidates on Gate 3 substance, not merely because
  a stronger candidate was found first.
