---
status: complete
phase: quick
plan: "260725-e1x"
subsystem: data-pipeline
tags: [destatis, regionalstatistik, investigation, repurpose, kpi-manifest, verdict]
requirements:
  - D-08
  - D-09
  - D-14
  - D-15
dependency-graph:
  requires:
    - "fetch_destatis.py: base-aware _headers()/check_auth()/fetch_regionalstatistik_table() (Plans 04-06/04-07)"
    - "04-07-SUMMARY.md: original catalogue-title-only rejection of the three 32221 tables"
  provides:
    - "260725-e1x-PROBE.json: machine-readable, live-verified probe record for 32221-01-03-4/32221-02-01-4/32221-03-01-4"
    - "260725-e1x-FINDINGS.md: human-readable comparison, live-verified (not inferred)"
    - "260725-e1x-DECISION.md: recorded REPURPOSE:groundwater_abstraction_1000m3 verdict with full 5-gate evaluation"
    - "fetch_destatis.py: REGIONALSTATISTIK_TABLES['groundwater_abstraction_1000m3'] live-verified table mapping"
    - "data/destatis_curated_kpis.json: soil-tab slot resolved with real Kreis-level values"
  affects:
    - ".planning/phases/04-destatis-statistics-integration-source-process-and-app-integ/04-07-SUMMARY.md (Known Stubs bullet updated)"
    - ".planning/STATE.md (Active Work paragraph updated)"
    - "data-pipeline/python/fetch_destatis.py"
    - "data/destatis_variables_catalogue.csv, destatis_curated_kpis.json, destatis_nuts3.json, destatis_ll.json, destatis_nuts3_export.csv, destatis_variables.csv"
key-files:
  created:
    - .planning/quick/260725-e1x-investigate-the-near-miss-regionalstatis/260725-e1x-PROBE.json
    - .planning/quick/260725-e1x-investigate-the-near-miss-regionalstatis/260725-e1x-FINDINGS.md
    - .planning/quick/260725-e1x-investigate-the-near-miss-regionalstatis/260725-e1x-DECISION.md
    - data/destatis_raw/32221-01-03-4__regionalstatistik.csv
    - data/destatis_raw/32221-02-01-4__regionalstatistik.csv
    - data/destatis_raw/32221-03-01-4__regionalstatistik.csv
  modified:
    - data-pipeline/python/fetch_destatis.py
    - data/destatis_variables_catalogue.csv
    - data/destatis_curated_kpis.json
    - data/destatis_nuts3.json
    - data/destatis_ll.json
    - data/destatis_nuts3_export.csv
    - data/destatis_variables.csv
    - .planning/phases/04-destatis-statistics-integration-source-process-and-app-integ/04-07-SUMMARY.md
    - .planning/STATE.md
decisions:
  - "Verdict: REPURPOSE:groundwater_abstraction_1000m3. Gate 1 (same-real-world-quantity) fails decisively and is now live-verified fact for the ORIGINAL groundwater_nitrate_mg_l slot -- all three 32221 tables report volumes (1000 cbm), never a nitrate concentration (mg NO3/l). But 32221-01-03-4's Wasserart classifying dimension carries a live-confirmed Grundwasser (WASSERGRUND) category -- a genuine, Kreis-complete, 5-year groundwater abstraction-volume dataset -- which passes Gates 2-5 as a D-14 same-catalogue-group (Environment) substitution."
  - "This worktree initially had no .env file at all (gitignored, absent from the worktree checkout), producing a fully credential-blocked first pass that forced a conservative REJECT-ALL-THREE placeholder verdict. A working .env was added mid-task by the orchestrator; Tasks 1 and 2 were both fully redone against real live API data. The corrected verdict supersedes the placeholder via follow-up commits (6eef113, ab920f8), not amends, to preserve the audit trail."
  - "The other two candidates (32221-02-01-4, 32221-03-01-4) are live-verified but rejected as repurpose candidates on Gate 3 substance -- neither has any water-source dimension, so neither could ever isolate a groundwater-specific figure even in principle."
metrics:
  duration: "~100 minutes total (Tasks 1-2, including a full credential-blocked pass and a full corrective live-verified re-run, plus the Task 3 human-verify checkpoint)"
  completed: 2026-07-25
---

# Quick Task 260725-e1x: Investigate the Near-Miss Regionalstatistik Water Tables Summary

One-liner: Live-verified the three 04-07 near-miss 32221 water tables against
`groundwater_nitrate_mg_l`, confirmed all three report volumes (never a nitrate concentration),
but found `32221-01-03-4` carries a live-verified groundwater-specific abstraction-volume
breakdown covering all 14 project Kreise -- applied a D-14 repurpose that moves the Soil-tab slot
from the perpetually-unfillable `groundwater_nitrate_mg_l` to `groundwater_abstraction_1000m3`,
now resolving with real values (11/17 curated KPIs real, up from 10/17).

## Completed

### Task 1: Live-probe the three 32221 Kreis-level tables and record what they actually contain

**First pass (credential-blocked):** This worktree initially had no `.env` file at all (gitignored,
not carried into the worktree checkout). `check_auth(base=REGIONALSTATISTIK_BASE)` and every
catalogue/metadata/data endpoint failed identically at the live API's auth gate. Recorded
PROBE.json with `status: "fetch-failed: ..."` for all three tables and a prominent credential-block
notice in FINDINGS.md, per the plan's own fallback instruction. Committed as `56bcf4c`.

**Correction (after a working `.env` was added):** The orchestrator added a working `.env` to this
worktree mid-task. Re-ran the full live probe for real:

- `check_auth(base=REGIONALSTATISTIK_BASE)` succeeded.
- `catalogue/tables` (`selection=32221*`) and `metadata/table` for each of the three tables
  returned live titles, `Valid: false`, `Time: {From: 2007, To: 2022}`, and (for `32221-01-03-4`
  only) a `WASAT2` "Wasserart" column with 8 declared category values. A broader
  `catalogue/tables selection=3222*` search confirmed no successor/newer table code exists at
  this prefix.
- `fetch_regionalstatistik_table()` returned real Kreis-level rows for all three tables (700, 280,
  350 rows respectively), all 14 project AGS codes present across 5 survey years (2010, 2013,
  2016, 2019, 2022). Every value is reported in `1000 cbm` (a volume), confirmed from the live
  `value_unit` column, not inferred from a title.
- **Critical finding:** `32221-01-03-4`'s `WASAT2` "Wasserart" dimension includes an explicit
  `WASSERGRUND = "Grundwasser"` category -- a genuine groundwater-specific abstraction volume,
  live-confirmed for all 14 Kreise (only 2 of 70 Kreis-year cells suppressed, both in the 2010
  wave; every Kreis still resolves via "latest year wins"). For AGS 12064 (Märkisch-Oderland),
  latest (2022) value is 12,927 (1000 cbm); across all 14 Kreise, values range 74-12,927 (1000
  cbm), a plausible spread.
- Overwrote `260725-e1x-PROBE.json` and `260725-e1x-FINDINGS.md` with the real, live-verified
  content. Committed 3 raw ffcsv caches
  (`data/destatis_raw/32221-{01-03,02-01,03-01}-4__regionalstatistik.csv`), each grepped for
  `DESTATIS_API_TOKEN`/`REGIONALSTATISTIK_PASSWORD` -- zero matches. Committed as `6eef113`
  (follow-up commit, not an amend, to preserve the audit trail of the credential-blocked-then-
  corrected sequence).

### Task 2: Reach the verdict, record it, and apply it

**First pass (credential-blocked):** Recorded verdict `REJECT-ALL-THREE` -- forced by the plan's
own credential-blocked fallback, since Gate 1 alone (inference-only) was also dispositive. No
pipeline code changes. Committed as `1d6e1d0`.

**Correction (after the real Task 1 evidence):** Re-evaluated all 5 gates against the live
`PROBE.json`:

- **Gate 1 (same-quantity):** FAIL for all three, now live-confirmed rather than inferred. A
  volume can never satisfy `groundwater_nitrate_mg_l`'s `mg NO3/l` concentration requirement --
  this holds even for the Grundwasser-specific breakdown (abstraction volume, not nitrate
  concentration).
- **Gate 2 (Kreis-depth):** PASS for all three tables (14/14 Kreise, 5 years, live-verified).
- **Gate 3 (indicator-defensibility):** STRONG PASS for `32221-01-03-4`'s Grundwasser category
  (a genuine groundwater-pressure indicator from exactly the non-public/agricultural-industrial
  sector most relevant to a Living Lab audience); FAIL for the other two tables (no water-source
  dimension exists in either).
- **Gate 4 (integration-correctness):** PASS -- straightforward `_SUM` field, no new derivation
  logic (one caveat noted: `Valid: false`, likely "latest wave, no newer wave yet" rather than
  genuinely superseded, since no successor table code exists).
- **Gate 5 (tab/contract):** PASS -- stays on the Soil tab, same `Environment` catalogue group,
  no change to the 17-entry/locked-per-tab-count contract.

**Verdict: `REPURPOSE:groundwater_abstraction_1000m3`.** Applied:

1. Added a catalogue row (`data/destatis_variables_catalogue.csv`, group `Environment`).
2. Added `REGIONALSTATISTIK_TABLES["groundwater_abstraction_1000m3"]` (table `32221-01-03-4`,
   `value_variable_code: WAS001`, `attr_code: WASSERGRUND`, `unit_factor: 1.0`).
3. Added the field to `apply_regionalstatistik_indicators()`'s `direct_output_fields` set.
4. Changed the `soil` slot's `variable_key` in `CURATED_KPIS` from `groundwater_nitrate_mg_l` to
   `groundwater_abstraction_1000m3` (other 16 entries untouched).
5. Registered in `_SUM` (volume field); left `groundwater_nitrate_mg_l` in `_MEAN` untouched per
   the plan's own "leave it alone if in doubt" guidance (harmless stale entry).
6. Added to `FIELD_LABELS` and `FIELD_THEME` (`"Nature & environment"`).
7. Ran `python python/fetch_destatis.py --force`: resolution log confirmed `[ok]
   groundwater_abstraction_1000m3 resolved via Regionalstatistik.de (32221-01-03-4)`. All 14
   Kreise resolve to non-null values; LL-level `_SUM` aggregates verified correct by hand (e.g.
   `east-brandenburg` = 20,656 = 12,927+1,204+3,496+3,029, exactly matching its 4 constituent
   Kreise).
8. Updated `04-07-SUMMARY.md`'s Known Stubs bullet in place (Soil-tab entry count 7->6 null
   slots overall) and `STATE.md`'s Active Work paragraph (10/17 -> 11/17 real KPIs).
9. `test_pipeline_outputs.py`: not extended -- the two existing manifest tests already cover the
   change (documented explicitly in DECISION.md per the plan's own instruction). `pytest
   tests/test_pipeline_outputs.py -q`: 7 passed, no regressions, both before and after applying
   the verdict.

Committed as `ab920f8` (follow-up commit, not an amend, superseding `1d6e1d0`'s credential-blocked
placeholder verdict). Incidentally, running `--force` refreshed several other GENESIS/
Regionalstatistik.de raw caches (audit-footer timestamp / row-order changes only, underlying
values unchanged) and added the GENESIS-side dead-cache `data/destatis_raw/32221-01-03-4.csv`
(Code 104 "no objects", confirming the dash-coded table ID correctly fails on GENESIS `cubefile`
and triggers the Regionalstatistik.de fallback path as designed) -- all grepped for secrets, zero
matches.

### Task 3: Human verification checkpoint -- APPROVED

The human reviewed `260725-e1x-FINDINGS.md` and `260725-e1x-DECISION.md` and responded
"approved" to the `REPURPOSE:groundwater_abstraction_1000m3` verdict as recorded. The full task
content, verbatim from the plan, is reproduced below for the record:

---

**what-built:**

Live-probed all three near-miss 32221 water tables (the ones 04-07 rejected on title alone),
produced PROBE.json + FINDINGS.md as evidence, reached and applied a single recorded verdict in
DECISION.md, and updated 04-07-SUMMARY.md / STATE.md accordingly.

**how-to-verify:**

1. Read `.planning/quick/260725-e1x-investigate-the-near-miss-regionalstatis/260725-e1x-FINDINGS.md`
   -- the comparison table should tell you, per table, exactly what quantity it measures, in
   what unit, and for how many of the 14 Kreise.
2. Read `260725-e1x-DECISION.md` and check the `## Verdict` line. Confirm you agree with it.
   Pay particular attention if the verdict is `REPURPOSE:` -- that consumes the Soil-tab slot
   D-09/D-08 assigned to `groundwater_nitrate_mg_l`, so the KPI a user sees on the Soil tab
   changes. The Soil tab currently has 0/3 real values; a repurpose makes it 1/3 but with a
   water-volume indicator instead of a nitrate concentration.
3. If a repurpose was applied, spot-check the values: run
   `python -c "import json; d=json.load(open('data/destatis_curated_kpis.json',encoding='utf-8')); print([e for e in d if e['tab']=='soil'])"`
   and confirm the new slot's label/unit read sensibly in both EN and DE, then check a couple of
   Kreis values in `data/destatis_nuts3.json` for plausible magnitude.
4. Confirm `cd data-pipeline && python -m pytest tests/test_pipeline_outputs.py -q` passes.

**resume-signal:**

Type "approved" to accept the verdict, or say which gate you disagree with and what the verdict
should be instead.

---

**Executor note for the human/orchestrator:** the recorded verdict IS `REPURPOSE:
groundwater_abstraction_1000m3` -- step 3 above applies. Running the suggested spot-check:

```
[{'genesis_table': None, 'source_host': None, 'tab': 'soil', 'variable_key': 'n_surplus_kg_ha', ...},
 {'genesis_table': None, 'source_host': None, 'tab': 'soil', 'variable_key': 'p_surplus_kg_ha', ...},
 {'genesis_table': '32221-01-03-4', 'source_host': 'regionalstatistik', 'tab': 'soil',
  'variable_key': 'groundwater_abstraction_1000m3',
  'label_en': 'Groundwater abstraction (non-public supply)',
  'label_de': 'Grundwasserentnahme (nichtoeffentliche Versorgung)',
  'unit_en': '1000 m3', 'unit_de': '1000 cbm'}]
```

`data/destatis_nuts3.json` values checked and plausible for a Kreis-level water-abstraction figure
(74 to 12,927, in units of 1000 m3, i.e. roughly 74,000 to 12.9 million m3/year -- consistent with
a mix of small rural Kreise and larger industrial/agricultural ones). Step 4 (`pytest
tests/test_pipeline_outputs.py -q`) has already been run by the executor and passes (7/7); the
human may re-run it independently. The human should specifically weigh whether a groundwater
*abstraction volume* indicator is an acceptable substitute for the originally-intended groundwater
*nitrate concentration* indicator on the Soil tab -- these answer genuinely different
environmental questions (water quantity/pressure vs. water quality/contamination), even though
both are live-verified, Kreis-complete, and thematically water/groundwater-related.

**Human response:** "approved". The verdict `REPURPOSE:groundwater_abstraction_1000m3` is
accepted as final. No further gate disagreements or alternative-verdict requests were raised.

## Final Verification (plan's `<verification>` block, re-run after approval)

All items from the plan's `<verification>` block were re-confirmed after the checkpoint approval,
against the final committed state (`ab920f8`):

- `cd data-pipeline && python -m pytest tests/test_pipeline_outputs.py -q` -- **7 passed**, no
  regressions.
- `python -m py_compile python/fetch_destatis.py` -- **compiles clean**.
- `260725-e1x-PROBE.json` -- parses as **three complete records**, each with a definitive
  `status` (`kreis-verified` for all three tables).
- `260725-e1x-DECISION.md` -- contains exactly **one `## Verdict` heading**, value
  `REPURPOSE:groundwater_abstraction_1000m3`, from the allowed set.
- `data/destatis_curated_kpis.json` -- **still 17 entries**; per-tab counts unchanged
  (`{landuse:4, soil:3, climate:2, landscape:4, economic:4}`).
- `04-07-SUMMARY.md`'s `## Known Stubs` groundwater bullet -- **cites live-probe evidence and
  links `260725-e1x-DECISION.md`** (both `260725-e1x-DECISION.md` and
  `groundwater_abstraction_1000m3` confirmed present in the bullet text).
- `git status` -- **no unexpected deletions** across the plan's full commit range
  (`3f30f18..HEAD`, verified via `git diff --diff-filter=D`); `data/ll_content.json`
  **untouched** (last modified by an unrelated, pre-existing commit).

All checks pass. The plan is complete.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] `260725-e1x-PROBE.json` initially omitted the required
`classifying_categories` key on all three records (first, credential-blocked pass)**

- **Found during:** Task 1's own automated verification step, first pass.
- **Fix:** Added `"classifying_categories": []` to all three records before the first commit.
- **Commit:** `56bcf4c` (fixed before commit).

**2. [Rule 3 - Blocking issue] Full credential block prevented any live data retrieval on the
first pass**

- **Found during:** Task 1, first `check_auth(base=REGIONALSTATISTIK_BASE)` attempt.
- **Issue:** This worktree had no `.env` file at all initially.
- **Fix:** Followed the plan's credential-blocked fallback verbatim on the first pass (commits
  `56bcf4c`/`1d6e1d0`). After the orchestrator added a working `.env` mid-task, both Task 1 and
  Task 2 were fully redone against real live API data (commits `6eef113`/`ab920f8`), superseding
  the placeholder findings and verdict via follow-up commits rather than amends, to preserve a
  clear audit trail of what happened and why.
- **Files modified:** all four output docs (PROBE.json, FINDINGS.md, DECISION.md,
  04-07-SUMMARY.md) plus the full set of pipeline/data files listed under `key-files.modified`
  above.
- **Commits:** `56bcf4c`, `1d6e1d0` (credential-blocked pass), `6eef113`, `ab920f8` (corrective
  live-verified pass).

**3. [Rule 3 - Blocking issue] DECISION.md's correction note initially used the literal string
"REJECT-ALL-THREE" in prose, which the plan's own automated verdict-detection regex
(`re.search(r'REJECT-ALL-THREE|REPURPOSE:\S+|OTHER:', ...)`) matched BEFORE the real `## Verdict`
line**

- **Found during:** Task 2's own automated verification step, after rewriting DECISION.md with
  the corrected verdict.
- **Issue:** The regex is a first-match search across the whole document; mentioning the old
  placeholder verdict string in a "CORRECTION" note earlier in the file caused the check to
  report the superseded verdict instead of the real one, even though `## Verdict` and the correct
  string were both present.
- **Fix:** Reworded the correction note to describe the old verdict in prose ("reject all three
  tables" placeholder) without using the exact matchable token, so the regex's first (and only)
  match is the real, current verdict under `## Verdict`.
- **Files modified:** `260725-e1x-DECISION.md`.
- **Commit:** `ab920f8` (fixed before commit).

## Known Stubs

None introduced by this task. `n_surplus_kg_ha` and `p_surplus_kg_ha` remain genuinely null on
the Soil tab (unaffected by this task, unchanged from before). `groundwater_nitrate_mg_l` itself
no longer exists as a curated slot (repurposed to `groundwater_abstraction_1000m3`) -- this is the
correct, intentional outcome of the recorded verdict, not a stub.

## Threat Flags

None beyond what 04-07 already assessed. This task exercised the same already-assessed
Regionalstatistik.de endpoints (`catalogue/tables`, `metadata/table`, `data/tablefile`) via the
existing `fetch_destatis.py` transport helpers. Credential-leak grep (T-04-13 precedent) confirmed
zero matches for `DESTATIS_API_TOKEN`/`REGIONALSTATISTIK_PASSWORD` across all new and
incidentally-refreshed raw cache files.

## Self-Check: PASSED

- FOUND: `.planning/quick/260725-e1x-investigate-the-near-miss-regionalstatis/260725-e1x-PROBE.json` (live-verified content)
- FOUND: `.planning/quick/260725-e1x-investigate-the-near-miss-regionalstatis/260725-e1x-FINDINGS.md` (live-verified content)
- FOUND: `.planning/quick/260725-e1x-investigate-the-near-miss-regionalstatis/260725-e1x-DECISION.md` (verdict: REPURPOSE:groundwater_abstraction_1000m3)
- FOUND: `data/destatis_raw/32221-01-03-4__regionalstatistik.csv`, `32221-02-01-4__regionalstatistik.csv`, `32221-03-01-4__regionalstatistik.csv`
- FOUND: `.planning/phases/04-destatis-statistics-integration-source-process-and-app-integ/04-07-SUMMARY.md` (Known Stubs bullet updated, cites `260725-e1x`)
- FOUND: `.planning/STATE.md` (Active Work paragraph updated, 11/17 real, 6 null)
- FOUND commit: `56bcf4c` (feat(260725-e1x): live-probe -- credential-blocked pass)
- FOUND commit: `1d6e1d0` (docs(260725-e1x): REJECT-ALL-THREE -- credential-blocked pass)
- FOUND commit: `6eef113` (fix(260725-e1x): supersede credential-blocked probe with real live findings)
- FOUND commit: `ab920f8` (fix(260725-e1x): apply live-verified REPURPOSE:groundwater_abstraction_1000m3 verdict)
- CONFIRMED: `pytest tests/test_pipeline_outputs.py -q` -- 7 passed, no regressions (re-confirmed after checkpoint approval)
- CONFIRMED: `data/destatis_curated_kpis.json` -- still 17 entries, per-tab counts unchanged, soil-tab now shows `groundwater_abstraction_1000m3` resolved via `regionalstatistik`
- CONFIRMED: `data/destatis_nuts3.json` -- all 14 Kreise non-null for `groundwater_abstraction_1000m3`; `data/destatis_ll.json` LL-level sums verified correct by hand
- CONFIRMED: no unexpected file deletions across the plan's full commit range (`git diff --diff-filter=D 3f30f18 HEAD` empty)
- CONFIRMED: `data/ll_content.json` untouched by this plan (last modified by an unrelated, pre-existing commit)
- CONFIRMED: Task 3 checkpoint approved by human ("approved") -- verdict `REPURPOSE:groundwater_abstraction_1000m3` accepted as final
- CONFIRMED: plan status -- **COMPLETE** (all 3 tasks done, checkpoint resolved)
