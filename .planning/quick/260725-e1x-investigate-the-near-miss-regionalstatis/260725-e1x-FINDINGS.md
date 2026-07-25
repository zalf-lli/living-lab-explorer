# Findings: Live-probe of the three near-miss 32221 Regionalstatistik.de water tables

## CREDENTIAL-BLOCKED -- read this first

**This investigation could not reach the live Regionalstatistik.de API at all.** No `.env` file
exists anywhere in this worktree (repo root or `data-pipeline/`) -- `.env` is gitignored and was
not carried into this git worktree checkout. Neither `REGIONALSTATISTIK_USERNAME`/
`REGIONALSTATISTIK_PASSWORD` nor even `DESTATIS_USERNAME`/`DESTATIS_API_TOKEN` are set in the
process environment.

Concretely:

- `fetch_destatis.py` refuses to import at all without `DESTATIS_USERNAME`/`DESTATIS_API_TOKEN`
  (`raise SystemExit("[error] DESTATIS_USERNAME or DESTATIS_API_TOKEN not set in .env")` at
  module load time). Dummy values were supplied for those two GENESIS-host variables purely to
  get past the import guard so the Regionalstatistik.de code path itself could be exercised and
  its failure observed.
- With `REGIONALSTATISTIK_USERNAME`/`REGIONALSTATISTIK_PASSWORD` genuinely absent,
  `fd.check_auth(base=fd.REGIONALSTATISTIK_BASE)` fails live against the real API with:
  `Ein Fehler ist aufgetreten. (Bitte geben Sie Ihren Nutzernamen ein.)` ("An error occurred.
  Please enter your username.") -- an HTTP 404 response carrying `{"Code":2,"Type":"ERROR"}`.
- The SAME error, at the SAME auth-gate, was reproduced directly against `catalogue/tables` and
  `metadata/table` (Step 1 of the plan's probe sequence) with a raw unauthenticated `_post()`
  call -- i.e. Regionalstatistik.de's catalogue/metadata endpoints are NOT open to anonymous
  callers on this host. There is no unauthenticated fallback path to exploit here, unlike some
  other GENESIS-family deployments.
- Consequently **zero live data was retrieved for any of the three candidate tables.** Every
  claim below about what these three tables measure is **inference carried over from
  04-07-SUMMARY.md's catalogue-title reading**, not a new live observation. It is labelled as
  such everywhere it appears.
- Per the plan's credential-blocked fallback, Task 2's verdict is therefore forced to the
  conservative outcome (reject / leave null) -- a repurpose on unverified data is explicitly
  disallowed by the plan regardless of how plausible the titles look.

## Comparison table

| Table | Title (04-07 inference, NOT live-verified) | Status | Years | Kreis coverage | What it measures (inference only) | Unit (inference only) | Groundwater-specific breakdown? |
|---|---|---|---|---|---|---|---|
| `32221-01-03-4` | "Wassergewinnung und -bezug" (water abstraction / supply) | `fetch-failed: Regionalstatistik.de auth blocked` | unknown | 0/14 (unreachable) | inferred: volume of water abstracted | inferred: 1000 m3 | unknown -- could not inspect the classifying-category dimensions live |
| `32221-02-01-4` | "Wassereinsatz und ungenutztes Wasser" (water use / unused water) | `fetch-failed: Regionalstatistik.de auth blocked` | unknown | 0/14 (unreachable) | inferred: volume of water used/unused | inferred: 1000 m3 | unknown |
| `32221-03-01-4` | "Abwasserverbleib" (wastewater disposal destination) | `fetch-failed: Regionalstatistik.de auth blocked` | unknown | 0/14 (unreachable) | inferred: volume of wastewater by disposal route | inferred: 1000 m3 | unknown |

## Per-table notes

### `32221-01-03-4` -- "Wassergewinnung und -bezug"

Live probe attempted via `metadata/table` (auth-blocked, HTTP 404 auth-gate error) and
`fetch_regionalstatistik_table("32221-01-03-4", force=True)` (same auth-gate failure --
`check_auth` fails before any table-specific request can even be attempted meaningfully). No raw
ffcsv cache was produced for this table; none exists at
`data/destatis_raw/32221-01-03-4__regionalstatistik.csv`. Everything about what this table
contains -- title, regional depth, value-variable inventory, whether it has a Grundwasser-specific
breakdown -- remains exactly what it was after 04-07: a catalogue-listing inference, not an
empirical finding. This is the ONE candidate where a groundwater-specific abstraction volume was
considered plausible (public water-supply statistics do sometimes break abstraction down by
source: groundwater vs. surface water vs. spring water), but that hypothesis is unconfirmed and
cannot be confirmed without working credentials.

### `32221-02-01-4` -- "Wassereinsatz und ungenutztes Wasser"

Same credential-blocked outcome as above. No raw cache produced. Per the established facts already
recorded in the plan's context (04-07's Bund-level cube fetch for statistic 32221, "Oeffentliche
Wasserversorgung und Abwasserbeseitigung"), the WAS-prefixed `value_variable_code`s associated with
this statistic are volume figures reported in "1000 cbm" -- i.e. a volume, not a concentration.
Nothing in this probe contradicts or confirms that for this specific dash-coded table; it is
carried forward as the best available (still inference-labelled) evidence.

### `32221-03-01-4` -- "Abwasserverbleib"

Same credential-blocked outcome. "Abwasserverbleib" (wastewater destination / disposal route) is,
by its own title, a wastewater-infrastructure statistic -- a municipal-infrastructure figure, not
an environmental-quality measurement of any kind. Even under the most generous live-verification
outcome this table could not plausibly report a nitrate concentration; it measures where
wastewater goes (treatment plant, direct discharge, etc.), not what is dissolved in groundwater.

## Requirements of the `groundwater_nitrate_mg_l` slot

The `groundwater_nitrate_mg_l` curated KPI slot (Soil tab, D-08/D-09) declares its unit as
**mg NO3/l** -- milligrams of nitrate per litre, a **concentration**, i.e. a mass-per-volume ratio
describing water quality. This is fundamentally different in kind from a volume figure (m3 or
1000 m3 of water moved, abstracted, or disposed of), which describes a quantity of water, not what
is dissolved in it. 04-07's same-real-world-quantity rule states a table may only fill a slot if it
measures the same real-world quantity the slot declares; a volume can never satisfy a concentration
requirement no matter how the numbers are rescaled.

For each candidate table, whether it measures nitrate concentration in mg NO3/l:

- **`32221-01-03-4`** -- Cannot confirm or deny live; catalogue-title inference (carried over from
  04-07, NOT live-verified by this probe) says this table measures water abstraction *volume*, not
  concentration. Even in the best case (a Grundwasser-specific abstraction volume breakdown
  existing), that would still be a volume in m3, never a concentration in mg NO3/l. **Does not
  measure nitrate concentration in mg NO3/l**, by inference.
- **`32221-02-01-4`** -- Catalogue-title inference says this measures water use/unused-water
  *volume*. **Does not measure nitrate concentration in mg NO3/l**, by inference.
- **`32221-03-01-4`** -- Catalogue-title inference says this measures wastewater disposal-route
  *volume*. **Does not measure nitrate concentration in mg NO3/l**, by inference.

None of the three tables can be live-confirmed to report a concentration in mg NO3/l, and even
under the most favourable inference-based reading, all three describe water/wastewater *volumes*,
which is categorically different from what the slot needs. Combined with the plan's instruction
that a credential-blocked run forces the conservative verdict, this points decisively toward
rejection -- see `260725-e1x-DECISION.md` for the formally recorded verdict and full gate-by-gate
reasoning.

## Evidence trail

- Throwaway probe script: written to the session scratchpad (not committed, not part of the
  pipeline), imports `fetch_destatis` via `sys.path.insert(0, "python")` and calls
  `fd.check_auth(base=fd.REGIONALSTATISTIK_BASE)`, `fd._post("metadata/table", ...)`, and
  `fd.fetch_regionalstatistik_table(..., force=True)` -- all three failed identically at the
  Regionalstatistik.de auth gate.
- Raw HTTP evidence captured directly: `POST https://www.regionalstatistik.de/genesisws/rest/2020/catalogue/tables`
  with empty `username`/`password` headers returns HTTP 404 with body
  `{"Code":2,"Content":"Ein Fehler ist aufgetreten. (Bitte geben Sie Ihren Nutzernamen ein.)","Type":"ERROR"}`.
- No `data/destatis_raw/32221-01-03-4__regionalstatistik.csv`,
  `32221-02-01-4__regionalstatistik.csv`, or `32221-03-01-4__regionalstatistik.csv` cache files
  were produced by this task -- there is no data to grep for secrets, and none is claimed.
- See `260725-e1x-PROBE.json` for the machine-readable record backing every claim above.
