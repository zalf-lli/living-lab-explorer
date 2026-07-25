# Decision: the three near-miss 32221 water tables vs. `groundwater_nitrate_mg_l`

## Credential-blocked context (read this first)

This investigation's live probe (Task 1, `260725-e1x-PROBE.json` / `260725-e1x-FINDINGS.md`)
could not reach the Regionalstatistik.de API at all. No `.env` file exists anywhere in this
worktree; `REGIONALSTATISTIK_USERNAME`/`REGIONALSTATISTIK_PASSWORD` (and even
`DESTATIS_USERNAME`/`DESTATIS_API_TOKEN`) are unset. Every attempted call --
`check_auth(base=REGIONALSTATISTIK_BASE)`, `catalogue/tables`, `metadata/table`,
`fetch_regionalstatistik_table()` -- failed identically at the live API's auth gate (HTTP 404,
`{"Code":2,"Type":"ERROR"}`, "Bitte geben Sie Ihren Nutzernamen ein."). Per the plan's own
credential-blocked fallback, this forces the conservative verdict below regardless of how the
gate evaluation reads -- a repurpose on unverified data is explicitly disallowed.

## Gate evaluation

**Gate 1 -- Same-quantity gate:** FAIL for all three tables.

The `groundwater_nitrate_mg_l` slot declares `mg NO3/l`, a concentration. None of the three
tables can be live-confirmed to report a concentration; the best available evidence (04-07's
catalogue-title inference, explicitly labelled as inference throughout `FINDINGS.md`, NOT a new
live observation from this task) is that all three measure water/wastewater *volumes*
("Wassergewinnung und -bezug" = water abstraction, "Wassereinsatz und ungenutztes Wasser" =
water use/unused water, "Abwasserverbleib" = wastewater disposal destination). A volume in m3
can never satisfy a concentration requirement in mg NO3/l, per 04-07's same-real-world-quantity
rule, no matter what unit-rescaling is attempted. Even under the single best-case hypothesis
considered plausible for `32221-01-03-4` (a Grundwasser-specific *abstraction volume* breakdown),
that would still be a volume, not a concentration -- so this gate would fail even with full
credentials and a maximally favourable live result.

Gate 1 is dispositive: since it fails for all three tables independently of the credential block,
the remaining gates are evaluated for completeness but do not change the outcome.

**Gate 2 -- Kreis-depth gate:** UNREACHABLE (credential-blocked).

`kreis_codes_covered` is `0/14` for all three tables in `PROBE.json`, but this reflects total
inability to query the API, not a live finding of zero regional coverage. This gate cannot be
scored on its merits from this task's evidence.

**Gate 3 -- Indicator-defensibility gate:** Would be reachable only if Gate 2 passed; it did not
(unreachable). Not scored.

**Gate 4 -- Integration-correctness gate:** Not reached; moot given Gate 1's failure.

**Gate 5 -- Tab/contract gate:** Not reached; moot given Gate 1's failure.

## Verdict

**REJECT-ALL-THREE**

## Reasoning

Gate 1 fails decisively and independently of the credential block: even the most favourable
inference-based reading of any of the three tables describes a water/wastewater *volume*, never
a nitrate *concentration*. 04-07's same-real-world-quantity rule is non-negotiable, so no
plausible live result from these three tables could ever fill the `groundwater_nitrate_mg_l`
slot. Separately and independently, this task's live probe was fully credential-blocked, which
by the plan's own instruction forces the conservative verdict regardless of gate outcomes. Both
lines of reasoning converge on the same answer: reject all three tables.

This upgrades 04-07's original title-based rejection in one specific way -- it is now an
explicitly documented fact that a live-verification attempt was made and blocked by missing
credentials in this execution environment, rather than simply never having been attempted at all.
The underlying substantive conclusion (these are volume statistics, not concentration statistics)
remains inference, carried forward unchanged from 04-07, and is flagged as such everywhere it
appears in `FINDINGS.md`.

## What was applied

- No pipeline code changes (`fetch_destatis.py` untouched).
- `data/destatis_curated_kpis.json`: `groundwater_nitrate_mg_l` unchanged --
  `genesis_table: null`, `source_host: null`, still 17 total entries, per-tab counts unchanged
  (`{landuse:4, soil:3, climate:2, landscape:4, economic:4}`).
- `fetch_destatis.py`'s `CURATED_KPIS` entry for `groundwater_nitrate_mg_l` (pointing at the dead
  `32221BJ001` cube, the documented provenance of the slot's origin) is left exactly as-is --
  not "cleaned up".
- `.planning/phases/04-destatis-statistics-integration-source-process-and-app-integ/04-07-SUMMARY.md`:
  the `groundwater_nitrate_mg_l` bullet under `## Known Stubs` is updated in place to record that
  a live-verification attempt was made under quick-task `260725-e1x`, that it was fully
  credential-blocked in this worktree, and that the rejection therefore still rests on 04-07's
  original catalogue-title inference -- now explicitly cross-linked to
  `260725-e1x-DECISION.md` / `260725-e1x-PROBE.json` / `260725-e1x-FINDINGS.md` for the full
  evidence trail and the reason a live upgrade could not be completed this round.
- `.planning/STATE.md`: Active Work paragraph updated -- still 7 null slots; the
  `groundwater_nitrate_mg_l` line now notes the credential-blocked live-verification attempt
  instead of resting solely on catalogue-title inference.
- Test suite: no changes needed (`test_destatis_curated_kpis_manifest_matches_contract` and
  `test_destatis_resolved_slots_have_real_values` already cover the unchanged 17-entry manifest
  and null-`source_host` slot; re-ran `pytest tests/test_pipeline_outputs.py -q` -- 7 passed, no
  regressions).

## Not now, but revisitable

- If Regionalstatistik.de credentials become available in a future execution environment, this
  investigation's Task 1 probe script (design captured in `260725-e1x-FINDINGS.md`'s Evidence
  Trail section) can be re-run to obtain a genuinely live-verified confirmation of Gate 1 rather
  than relying on 04-07's catalogue-title inference. Given the categorical mismatch (volume vs.
  concentration) is unlikely to change under live data, this would most likely convert an
  inference-based REJECT into a live-verified REJECT rather than change the outcome -- but it
  would close the evidentiary gap this task was unable to close.
- `32221-01-03-4` ("Wassergewinnung und -bezug") remains the single most plausible candidate
  among the three IF the app ever grows a water-infrastructure or municipal-infrastructure tab
  unrelated to the Soil tab's nitrate-concentration concern -- a groundwater-specific abstraction
  *volume* (if the table indeed breaks down by water source, still unconfirmed) would speak to
  groundwater *pressure*, a different but adjacent question to groundwater *quality*. This is
  out of scope for the Soil tab's `groundwater_nitrate_mg_l` slot regardless.
- The genuinely defensible path to filling `groundwater_nitrate_mg_l` remains a non-Destatis
  source (UBA, LAWA, or similar water-quality monitoring body), as 04-07 already noted --
  unaffected by this task's findings.
