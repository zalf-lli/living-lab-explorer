# Phase 8 Wave-0 Spike (plan 08-01)

Every number below was measured live against os.zhdk.cloud.switch.ch / envicloud.wsl.ch / www.envidat.ch by `data-pipeline/python/probe_chelsa.py`, except where explicitly marked as an extrapolation.

## W-01 -- Confirmed download URL templates

**Future-period template** (source: S3 ListObjectsV2 listing (derived from real key GLOBAL/climatologies/2071-2100/GFDL-ESM4/ssp370/bio/CHELSA_bio1_2071-2100_gfdl-esm4_ssp370_V.2.1.tif)):

    https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/{period}/{GCM_UPPER}/{ssp}/bio/CHELSA_{variable}_{period}_{gcm}_{ssp}_V.2.1.tif

**Baseline template** (re-confirmed live): `https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/1981-2010/bio/CHELSA_{variable}_1981-2010_V.2.1.tif`

40-URL matrix (4 variables x 2 periods x 5 GCMs): 40/40 resolved HTTP 200.
All 40 combinations resolved 200 -- no gaps in the matrix.

Baseline re-confirmation (all 4 variables):

| Variable | Status | Content-Length (bytes) |
|---|---:|---:|
| bio1 | 200 | 115,490,323 |
| bio10 | 200 | 123,145,240 |
| bio12 | 200 | 655,151,886 |
| bio18 | 200 | 438,957,395 |

The plain-text `envidatS3paths.txt` index named by the plan as the "authoritative shortcut" 404s on both `os.zhdk.cloud.switch.ch` and `envicloud.wsl.ch`. The bucket instead exposes a standard, public S3 `ListObjectsV2`-style listing query (`?list-type=2&prefix=...&delimiter=/`), used here as an equivalent authoritative source (it lists real keys, not a guess) before falling back to candidate probing -- the fallback was not needed; the listing resolved the template on the first attempt.

### Bonus finding, live-verified this run: a directly-published static `gdd5` file

The same `--urls` bio/ folder listing surfaced `CHELSA_gdd5_*` alongside `bio1`..`bio19` -- CHELSA's own growing-degree-days-above-5C variable, matching D-06's index exactly, published as a first-class static bioclim-family file **entirely independent of the `chelsa_cmip6` Python package**. This is the lead a prior halted attempt at this same plan noticed but never live-verified; it is re-verified live here, not trusted secondhand:

- Baseline (1981-2010): status 200, 452,334,119 bytes
- Future period 2071-2100/ssp370, all 5 D-04 GCMs:

| GCM | Status | Content-Length (bytes) |
|---|---:|---:|
| gfdl-esm4 | 200 | 499,682,878 |
| ipsl-cm6a-lr | 200 | 511,643,035 |
| mpi-esm1-2-hr | 200 | 501,930,974 |
| mri-esm2-0 | 200 | 504,564,193 |
| ukesm1-0-ll | 200 | 531,940,694 |

**Verdict: CONFIRMED** -- `gdd5` is fetchable with the exact same zero-new-dependency `requests`/`rasterio` mechanism as bio1/bio12/bio18, for both the baseline and all 5 future-period GCMs. See the Recommendation section below: this is a third, previously-unconsidered option for the D-07 GDD slot, lighter than both alternatives research compared.

## W-02 -- Static monthly `tas` availability for future periods

**PUBLISHED**

Evidence: URL: https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/2071-2100/GFDL-ESM4/ssp370/tas/CHELSA_gfdl-esm4_r1i1p1f1_w5e5_ssp370_tas_01_2071_2100_norm.tif -> 200 (120685951 bytes)

Consequence for D-07: since monthly `tas` is statically published for future periods too, true GDD *could* in principle be hand-derived from it via the standard `sum(max(T - 5, 0))` formula without the `chelsa_cmip6` heavy dependency -- but this is now superseded by the gdd5 bonus finding above, which is a directly-published GDD-equivalent file needing no derivation at all.

## W-03 -- License, attribution and citation for the CMIP6-derived product

- `license`: CC0-1.0 (Creative Commons Zero - No Rights Reserved (CC0 1.0))
- `attribution`: CHELSA V2.1 (WSL), (c) Dirk Nikolaus Karger, Olaf Conrad, Jürgen Böhner et al., DOI 10.16904/envidat.228
- `citation`: Karger DN. et al. Climatologies at high resolution for the earth’s land surface areas, Scientific Data, 4, 170122 (2017)  [doi: 10.1038/sdata.2017.122](https://doi.org/10.1038/sdata.2017.122).
- `note`: This EnviDat entry (DOI 10.16904/envidat.228, license CC0-1.0) is the umbrella 'Climatologies at high resolution' dataset page; its 'CHELSA V2.1 (current)' resource (https://envicloud.wsl.ch/#/?bucket=https%3A%2F%2Fos.unil.cloud.switch.ch%2Fchelsa02%2F&prefix=chelsa%2Fglobal%2Fclimatologies%2F) links to a bucket-family prefix that differs by hostname from the os.zhdk.cloud.switch.ch host this script's --urls path confirmed live for the CMIP6-future product, though both share the same V.2.1 file-naming suffix. The underlying CMIP6 GCM model outputs additionally carry their own WCRP CMIP6 Terms of Use (conventionally CC-BY-4.0-style, naming the modelling centre per GCM) which this session could not independently re-verify against a live WSL-hosted page -- confirm this at the 08-03 checkpoint before sources.yaml is finalized.

This MATCHES the CHELSA V2.1 baseline climatology's CC0 license (confirms research Assumption A2).

## W-04 -- Grid alignment and windowed-read cost

**Grid alignment: CONFIRMED** -- all 5 D-04 GCM rasters (bio1, 2071-2100, ssp370) share an identical transform/shape/crs/dtype/nodata:

    transform=(0.0083333333, 0.0, -180.00013888885002, 0.0, -0.0083333333, 83.99986041515001)  shape=(20880, 43200)  crs=EPSG:4326  dtype=uint16  nodata=0.0

Full remote file size (bio1, 2071-2100, ssp370, gfdl-esm4): 119,627,391 bytes (114.1 MB).
Germany-window `/vsicurl/` read: 7.48 seconds wall time, array shape (1020, 1200), dtype uint16, in-memory size 2,448,000 bytes (2.33 MB).
GDAL byte-level transfer was not directly observable (per the plan's explicit fallback); wall time + in-memory array size are reported as the proxy measurement.

Projected full acquisition matrix (4 variables x (1 baseline + 2 horizons x 5 GCMs) = 44 reads): ~102.7 MB extrapolated transfer, ~329.3 seconds extrapolated wall time.

Both caps (300s per read, 5GB projected total) are observed -- recommended acquisition budget cap for `sources.yaml`: use this measured projection as the baseline budget, revisited once `bio12`/`bio18` (larger files) are individually measured in a later plan.

## Recommendation for the 08-03 checkpoint

Three options now exist for the D-07 GDD slot (a third beyond the two `08-RESEARCH.md` compared), presented here as measured costs -- **08-03 decides, not this document:**

| | `chelsa-cmip6==1.4` (heavy) | `bio10` fallback (light, no true GDD) | `gdd5` static file (light, true GDD-equivalent) |
|---|---|---|---|
| New dependencies | ~10 transitive (xarray, dask, zarr, gcsfs, netcdf4, h5netcdf, esgf-pyclient, siphon, google-cloud-storage family, aiohttp) | zero | zero |
| Network calls at build time | live GCS/ESGF pulls on every run | static `requests`/`rasterio` fetch (same mechanism as bio1/bio12/bio18) | static `requests`/`rasterio` fetch (same mechanism as bio1/bio12/bio18) |
| Formula | non-standard: sums raw temperature on days >=threshold, not `sum(max(T-5,0))` (Pitfall 2) | N/A -- not a GDD variable at all (bio10 = mean temp of warmest quarter) | CHELSA's own bioclim-family `gdd5` (definition not independently re-derived this session; recommend confirming the exact formula against CHELSA's technical documentation PDF before 08-03, since this session had no PDF-text-extraction tooling available) |
| Measured cost this spike | not measured (out of scope for the light-path spike) | covered by this spike's bio1 measurements above (same acquisition shape) | CONFIRMED fetchable across baseline + all 5 GCMs for 2071-2100/ssp370; same file-size class as bio1/bio10 (not bio12/bio18's much larger precipitation files) |
| On-brand match to D-08 ("GDD is the default variable") | yes, if the heavy path is accepted | no -- would require rewriting D-06/D-08's copy around `bio10` instead of GDD | **yes** -- delivers the literal GDD index D-06 named, with zero dependency cost |

This spike's measurements suggest the `gdd5` static file is the strongest candidate of the three -- it is the only option matching D-06's literal GDD requirement at zero new dependency cost -- but the exact `gdd5` formula has not been independently verified against CHELSA's own technical specification in this session (no PDF-reading tool was available), and D-07 explicitly reserves this decision for a human. **08-03 must decide among `chelsa-cmip6`, `bio10`, and `gdd5`,** not this spike.

## Decision brief (for the 08-03 checkpoint)

### The W-02 fact that almost settles this on its own

W-02 above recorded **PUBLISHED**: monthly `tas` is statically published for the future CMIP6 periods,
not just the 1981-2010 baseline. That means true GDD is *not* unreachable outside the heavy
`chelsa-cmip6` cloud-compute path -- the textbook `sum(max(T - 5, 0))` formula can in principle be
hand-rolled from statically published monthly `tas` files with zero new heavy dependencies. That is
the `gdd-light` option below, and it is presentable here precisely because W-02 = PUBLISHED. Had W-02
recorded NOT PUBLISHED, `gdd-light` would not exist as an option and the only route to true GDD would
be the heavy `chelsa-cmip6` path.

**But W-01 found something better before this brief was even drafted.** The same S3 listing that
resolved W-01's URL template also surfaced `CHELSA_gdd5_*` files sitting directly alongside
`bio1`..`bio19` in the same bio/ folder -- CHELSA's own growing-degree-days-above-5C variable,
published as a first-class static bioclim-family file, live-verified this session at both the
baseline and all 5 D-04 GCMs for 2071-2100/ssp370 (see W-01's "Bonus finding" subsection above). This
is **not** the `gdd-light` option research anticipated (interpolate-then-sum from twelve monthly
grids) -- it needs no derivation step, no monthly-`tas` fetch, and no interpolation at all. It is
fetched with the exact same `requests`/`rasterio` mechanism as `bio1`/`bio12`/`bio18`/`bio10`. This
brief therefore presents **four** options, not the three `08-CONTEXT.md`/`08-RESEARCH.md` anticipated:
`gdd-heavy`, `gdd-light`, the new `gdd5` static-file option, and the `bio10` fallback.

### The downstream re-planning fact this brief must keep visible

Waves 3-7 (`08-04` onward) implement exactly one acquisition shape: static per-variable GeoTIFF
windows fetched from a URL template that interpolates a `chelsa_variable` token. `08-04` Task 1's
`climate.variables` schema carries that token and nothing else -- no field for a library-computed
variable, no branch for a variable assembled from twelve monthly grids -- and `08-04` Task 2's
`fetch_climate.py` implements a single acquisition mechanism whose dry-run assertion of 44 planned
remote reads (4 variables x 1 baseline + 4 variables x 2 horizons x 5 GCMs) is arithmetic that holds
only under that one shape. Choosing `gdd-light` or `gdd-heavy` therefore halts the phase after this
plan and returns to `/gsd:plan-phase 8 --gaps` to re-plan the acquisition wave, exactly as `08-04`'s
own execution precondition already states.

**Correction to that framing, made necessary by the `gdd5` bonus finding:** `gdd5` is also "one
directly-published CHELSA raster per (variable, period, GCM)" -- the exact shape `08-04`'s schema
already assumes for `bio10`. Choosing `gdd5` does **not** require re-planning the acquisition wave.
`08-04`'s `sources.yaml` `climate.variables` entry for the fourth slot would simply carry
`chelsa_variable: gdd5` instead of `chelsa_variable: bio10`, and `fetch_climate.py` needs no code
change. The one loose end: `08-04` Task 1's own precondition-check text currently tests
`08-SPIKE.md`'s `### W-05` value against the literal strings `bio10` / `gdd-light` / `gdd-heavy`
only -- it has no branch recognizing the literal string `gdd5`. Task 3 of this plan (or a one-line
edit inside `08-04` itself when it runs) must teach that check to treat a `gdd5` verdict as a
`bio10`-shaped outcome; this is a same-plan wording fix, not a re-planned acquisition wave, and this
brief flags it here so it is not silently forgotten between `08-03` and `08-04`.

### Comparison table

| Option | New `requirements.txt` lines | Transitive dependencies | Live network at build time | Measured/projected acquisition cost | GDD formula fidelity | Python 3.12 compatibility confidence | Downstream re-planning cost |
|---|---|---|---|---|---|---|---|
| **`gdd-heavy`** -- `chelsa-cmip6==1.4` | 1 direct (`chelsa-cmip6==1.4`) | ~10 (`xarray`, `dask`, `zarr`, `gcsfs`, `netcdf4`, `h5netcdf`, `esgf-pyclient`, `siphon`, the `google-cloud-storage` family, `aiohttp`) | Yes -- live GCS/ESGF pulls on every run | Not measured this spike (out of scope for the light-path spike) | Non-standard: sums raw temperature on days >= threshold, not `sum(max(T-5,0))` (Pitfall 2) | MEDIUM -- metadata floor is `>=3.6`; package prose only names 3.8/3.10 as "tested" | Halts the phase, return to `/gsd:plan-phase 8 --gaps`. `08-04` Task 1's `chelsa_variable` schema has no field for a library-computed variable; Task 2's 44-read dry-run assertion is `bio10`-shape arithmetic |
| **`gdd-light`** -- hand-rolled `sum(max(T-5,0))` from monthly `tas` | 1 new (`scipy`, for the monthly-to-daily interpolation step in `08-RESEARCH.md`'s own hand-rolled example -- not currently pinned in `data-pipeline/requirements.txt`; this spike's "zero new dependencies" framing for the static paths covers fetch-only variables, not this derivation step) | `scipy`'s own (small) transitive footprint; nothing near `gdd-heavy`'s stack | No -- static `requests`/`rasterio` fetch, same mechanism as `bio1`/`bio12`/`bio18` | Not directly measured. Using W-04's single measured windowed read (7.48s wall, 2.33 MB in-memory) as a flat per-read proxy: this plan's literal instruction is 12 months x 5 GCMs x 2 horizons = 120 future reads => ~897.6s wall (~15.0 min) / ~279.6 MB, for this one variable alone. A complete accounting also needs 12 baseline monthly reads (model-independent, no GCM factor) => ~89.8s / ~28.0 MB more. Total ~132 reads / ~987.4s (~16.5 min) / ~307.6 MB for the GDD slot alone, versus ~11 reads / ~82.3s / ~25.6 MB for any single `bio10`-shape variable under the same proxy. This proxy was measured on `bio1`'s uint16 grid, not on a `tas` file, so the true figure is unverified in either direction | Textbook `sum(max(T-5,0))`, zero fidelity caveat -- the only path yielding textbook agronomic GDD with no caveat | HIGH -- `scipy` has mature, mainstream Python 3.12 wheels; no exotic transitive risk | Halts the phase, return to `/gsd:plan-phase 8 --gaps`. No plan in the current set fetches monthly `tas` or interpolates twelve monthly grids into a daily series; `08-04`'s `climate.variables` schema has no field/branch for a multi-source-grid variable, and `fetch_climate.py` reads exactly one window per (variable, period, GCM) |
| **`gdd5`** -- CHELSA's own static GDD-above-5C file (bonus finding, W-01) | 0 -- same `requests`/`rasterio` mechanism as `bio1`/`bio12`/`bio18`/`bio10` | 0 new | No -- static fetch, identical mechanism to the other three fixed variables | Full remote file sizes are confirmed live (not a windowed-read cost): baseline 452,334,119 bytes; future 2071-2100/ssp370 across the 5 GCMs ranges 499,682,878-531,940,694 bytes. **Correction to this spike's own Recommendation-section wording above:** those figures are 3.9x-4.4x larger than `bio1`'s equivalent full files (115,490,323 baseline / 119,627,391 future) and closer in scale to `bio18`'s 438,957,395-byte baseline -- not "the same file-size class as bio1/bio10" as this document's Recommendation section states. No windowed `/vsicurl/` Germany-extent read was measured for `gdd5` in this spike, so its true acquisition cost (unlike `gdd-light`'s, which this brief extrapolates above) is an open measurement gap, not a number to sign off on yet -- W-08's budget cap should be revisited once `gdd5` is measured directly, the same way W-04 already flags for `bio12`/`bio18` | Not independently re-derived against CHELSA's own technical documentation this session (no PDF-extraction tooling available) -- flagged as an open verification item, not confirmed textbook-equivalent | N/A -- no new library; same file-format/mechanism compatibility already proven for `bio1`/`bio10` | **None**, subject to the one-line `08-04` precondition-check update described above. `gdd5` is a `bio10`-shaped static single-file variable, so Waves 3-7 execute as planned with `chelsa_variable: gdd5` substituted for `chelsa_variable: bio10` |
| **`bio10`** -- D-07's pre-agreed fallback (mean temp of the warmest quarter) | 0 | 0 | No -- static fetch | Covered by this spike's `bio1` measurements above (identical acquisition shape); part of the already-budgeted 44-read / ~102.7 MB / ~329.3 s projection | N/A -- not a GDD variable at all | N/A -- no new library | None. `08-04` through `08-10` are written for exactly this acquisition shape and execute as planned with no re-planning step |

### Concrete identifier proposals

Any true-GDD outcome (`gdd-heavy`, `gdd-light`, or `gdd5`) resolves to the same downstream strings,
since all three present as "GDD" to the visitor and differ only in acquisition mechanism and formula
fidelity:

- variable id `gdd`, KPI `variable_key` `gdd5_degc_days`, unit EN `degC-day` / DE `degC-Tag`, heat
  ramp family, legend note per `08-UI-SPEC.md`'s GDD row (EN: "Heat accumulated above 5 degC over the
  year -- a measure of how much growing season a crop gets."; DE: "Ueber das Jahr summierte Waerme
  oberhalb von 5 degC -- ein Mass dafuer, wie viel Vegetationszeit eine Kultur erhaelt.")

The `bio10` fallback resolves to a different set, needing fresh copy since `08-UI-SPEC.md` only
drafted GDD's:

- variable id `bio10`, KPI `variable_key` `warm_quarter_temp_degc`, unit EN/DE `degC`, heat ramp
  family, legend note needing fresh EN/DE wording ("Mean air temperature of the warmest three-month
  quarter." / "Mittlere Lufttemperatur des waermsten Vierteljahres.")

The other three variables are fixed regardless of the W-05 outcome (D-05's count of four variables and
60 rasters is unchanged either way):

| id | `variable_key` | unit EN | unit DE | ramp family |
|---|---|---|---|---|
| `bio1` | `mean_annual_temp_degc` | `degC` | `degC` | heat |
| `bio12` | `annual_precip_mm` | `mm` | `mm` | water |
| `bio18` | `warm_quarter_precip_mm` | `mm` | `mm` | water |

### Separate sign-off items (worth locking regardless of the W-05 outcome)

- **W-06 -- URL templates (from W-01).** Future-period:
  `https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/{period}/{GCM_UPPER}/{ssp}/bio/CHELSA_{variable}_{period}_{gcm}_{ssp}_V.2.1.tif`.
  Baseline: `https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/1981-2010/bio/CHELSA_{variable}_1981-2010_V.2.1.tif`.
  Both re-confirmed live this session with a 40/40 HTTP 200 matrix (4 variables x 2 periods x 5 GCMs).

- **W-07 -- Provenance text (from W-03).** `license`: CC0-1.0. `attribution`: CHELSA V2.1 (WSL), (c)
  Dirk Nikolaus Karger, Olaf Conrad, Juergen Boehner et al., DOI 10.16904/envidat.228. `citation`:
  Karger DN. et al., *Scientific Data*, 4, 170122 (2017), DOI 10.1038/sdata.2017.122. `note`: this
  EnviDat entry's umbrella CC0 license was confirmed for the baseline climatology dataset page; the
  underlying CMIP6 GCM model outputs additionally carry their own WCRP CMIP6 Terms of Use
  (conventionally CC-BY-4.0-style, naming the modelling centre per GCM) which this spike could **not**
  independently re-verify against a live WSL-hosted page. `sources.yaml` must not assert an
  unqualified CC0 for the CMIP6-derived product until that gap is either closed or the conservative
  wording is explicitly approved here.

- **W-08 -- Acquisition budget cap (from W-04).** Measured proxy: 300 s per windowed read observed
  with headroom (actual measured read: 7.48 s); projected total transfer for the 44-read/4-variable
  matrix under the `bio10` shape: ~102.7 MB, ~329.3 s wall. W-04's own recommendation: "use this
  measured projection as the baseline budget, revisited once `bio12`/`bio18` (larger files) are
  individually measured in a later plan." Note W-04 states the cap only as "300 s per read, 5 GB
  projected total" without pinning an exact byte integer for the 5 GB figure -- the human sign-off
  should also pin the literal integer (e.g. `5368709120` for 5 GiB, or `5000000000` for 5 GB) so
  `fetch_climate.py`'s hard `SystemExit` has an unambiguous threshold. If `gdd5` is chosen, note this
  budget was not sized with `gdd5`'s larger full-file class in mind (see the comparison table above).

- **D-06 base temperature confirmation.** 5 degC, matching `chelsa_cmip6`'s own default
  (`growing_degree_days(tas, threshold=None)`'s default). `08-RESEARCH.md` recommends no change. This
  item asks the human to confirm rather than re-open it.

### Package legitimacy precondition (only if `gdd-heavy` is chosen)

`chelsa-cmip6==1.4` itself already carries a live `slopcheck` `[OK]` verdict recorded in
`08-RESEARCH.md`'s Package Legitimacy Audit. Its ~10 transitive dependencies (`xarray`, `dask`,
`zarr`, `gcsfs`, `netcdf4`, `h5netcdf`, `esgf-pyclient`, `siphon`, the `google-cloud-storage` family,
`aiohttp`) were **not** individually audited and must each pass `slopcheck` before any `pip install`
runs. This gate is never auto-approvable (T-08-SC) and, per this brief's downstream-cost analysis
above, only becomes relevant after a fresh `/gsd:plan-phase 8 --gaps` pass, since `gdd-heavy` halts
this phase before any install step is reachable.

## Locked decisions

### W-05 — Fourth variable

**Locked 2026-07-30.** Chosen option id: **`gdd5`** — CHELSA's own directly-published static
growing-degree-days-above-5degC file (the W-01 bonus finding), approved by the human at the Task 2
checkpoint on 2026-07-30. This was **not** one of the three option ids this phase's earlier planning
documents originally framed for this decision; it is a fourth possibility this plan's Decision brief
surfaced after `08-01`'s live probe found it. Do not re-derive the values below; transcribe as-is.

- Variable id: `gdd`
- KPI `variable_key`: `gdd5_degc_days`
- Unit EN: `degC-day`; Unit DE: `degC-Tag`
- Ramp family: heat
- Legend note EN: "Heat accumulated above 5 degC over the year -- a measure of how much growing
  season a crop gets."
- Legend note DE: "Ueber das Jahr summierte Waerme oberhalb von 5 degC -- ein Mass dafuer, wie viel
  Vegetationszeit eine Kultur erhaelt."
- Formula verdict: CHELSA's own `gdd5` formula was **not** independently re-derived against CHELSA's
  technical documentation in this session (no PDF-extraction tooling was available at `08-01`) and
  remains an **open verification item**, not a locked fact -- carry this caveat into any user-facing
  claim of textbook agronomic GDD fidelity until it is confirmed.
- Acquisition shape: one directly-published CHELSA raster per (variable, period, GCM), fetched with
  the same `requests`/`rasterio` mechanism as `bio1`/`bio12`/`bio18`/`bio10` -- the same shape `08-04`
  already implements for `bio10`.

**Downstream:** `gdd5` -- same static per-variable GeoTIFF acquisition shape as `bio10`; `08-04`
onwards execute as written. See `## Phase status` below.

**Required follow-up (flagged here so it is not silently forgotten):**
1. `08-04` Task 1's execution precondition currently checks `08-SPIKE.md`'s `### W-05` value against
   three literal option-id strings only, none of which is `gdd5`. Whoever executes `08-04` next must
   recognize `gdd5` as a `bio10`-shaped outcome and update that precondition-check wording (a one-line
   fix inside `08-04-PLAN.md`, not a re-planned acquisition wave). This plan's `files_modified`
   frontmatter is `08-SPIKE.md` only, so that edit is out of scope here and is recorded as a Deviation
   in `08-03-SUMMARY.md` for the orchestrator/next dispatch to apply before Wave 3 executes.
2. `gdd5`'s full remote file sizes (452,334,119 bytes baseline; 499,682,878-531,940,694 bytes future
   per GCM) are 3.9x-4.4x larger than `bio1`'s equivalent files, and no windowed `/vsicurl/`
   Germany-extent read has been measured for `gdd5` specifically. `08-04`'s Stage-1 measure-then-decide
   gate (Task 3) will produce that measurement for the first time; the W-08 budget cap below was set
   from `bio1`'s measured proxy and may need re-confirming once `gdd5`'s real read cost is known.

### W-06 — Source URL templates

**Locked 2026-07-30**, approved as-is.

- Future-period template:
  `https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/{period}/{GCM_UPPER}/{ssp}/bio/CHELSA_{variable}_{period}_{gcm}_{ssp}_V.2.1.tif`
- Baseline template:
  `https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/1981-2010/bio/CHELSA_{variable}_1981-2010_V.2.1.tif`

Both re-confirmed live at `08-01` with a 40/40 HTTP 200 matrix (4 variables x 2 periods x 5 GCMs). Do
not re-derive; transcribe as-is into `sources.yaml`.

### W-07 — Provenance text

**Locked 2026-07-30**, approved as proposed (conservative wording, not the baseline product's
unqualified CC0).

- `license`: CC0-1.0 (Creative Commons Zero - No Rights Reserved (CC0 1.0)) for the CHELSA V2.1
  baseline climatology dataset page (confirmed live at `08-01`).
- `attribution`: CHELSA V2.1 (WSL), (c) Dirk Nikolaus Karger, Olaf Conrad, Juergen Boehner et al.,
  DOI 10.16904/envidat.228.
- `citation`: Karger DN. et al. Climatologies at high resolution for the earth's land surface areas,
  Scientific Data, 4, 170122 (2017), DOI 10.1038/sdata.2017.122.
- `note`: This EnviDat entry (DOI 10.16904/envidat.228, license CC0-1.0) is the umbrella
  "Climatologies at high resolution" dataset page confirmed live at `08-01`. **The underlying CMIP6
  GCM model outputs additionally carry their own WCRP CMIP6 Terms of Use (conventionally
  CC-BY-4.0-style, naming the modelling centre per GCM), which this phase could not independently
  re-verify against a live WSL-hosted page.** `sources.yaml`'s `chelsa-climate` entry must carry this
  note verbatim rather than asserting an unqualified CC0 for the CMIP6-derived product.

### W-08 — Acquisition budget cap

**Locked 2026-07-30**, approved.

- `max_seconds_per_read`: **300** seconds (measured actual: 7.48s on the one windowed read performed
  at `08-01`, so this cap carries wide headroom).
- `max_total_transfer_bytes`: **5368709120** bytes (5 GiB, binary convention).
  - Chosen-convention rationale: this codebase already uses the binary MiB/GiB convention for byte
    caps elsewhere in this same phase -- `08-08-PLAN.md`'s committed-footprint cap is the literal
    integer `209715200` bytes, i.e. exactly `200 * 1024 * 1024` (200 MiB) -- and `sources.yaml`
    already carries `max_response_bytes: 104857600` (100 MiB) and `max_response_bytes: 209715200`
    (200 MiB) for other layers. `5368709120 = 5 * 1024**3` follows that same local precedent rather
    than the decimal `5000000000` alternative.
  - W-04's own measured projection for the `bio10`-shaped 44-read/4-variable matrix: ~102.7 MB
    transfer, ~329.3 s wall -- both comfortably inside this cap. `gdd5`'s own read cost is not yet
    measured (see the W-05 follow-up above); `08-04` must re-check this cap against `gdd5`'s first
    real Stage-1 measurement rather than assuming the `bio10`/`bio1` proxy applies unchanged.
- D-06 base temperature: **5 degC**, confirmed unchanged, matching `chelsa_cmip6`'s own default
  (`growing_degree_days(tas, threshold=None)`) and `08-RESEARCH.md`'s recommendation.

## Locked four-variable table

| id | `variable_key` | unit EN | unit DE | ramp family | i18n label key | legend-note key |
|---|---|---|---|---|---|---|
| `gdd` | `gdd5_degc_days` | `degC-day` | `degC-Tag` | heat | `climateVariable.gdd` | `legend.climate.note.gdd` |
| `bio1` | `mean_annual_temp_degc` | `degC` | `degC` | heat | `climateVariable.bio1` | `legend.climate.note.bio1` |
| `bio12` | `annual_precip_mm` | `mm` | `mm` | water | `climateVariable.bio12` | `legend.climate.note.bio12` |
| `bio18` | `warm_quarter_precip_mm` | `mm` | `mm` | water | `climateVariable.bio18` | `legend.climate.note.bio18` |

## Naming contract (transcribe, do not invent)

- PMTiles pattern: `data/pmtiles/climate-{variable}-{period}-{slug}.pmtiles`
- Period tokens: `baseline`, `2041_2070`, `2071_2100`
- Germany-extent intermediate rasters: `data/climate_source/chelsa-{variable}-{period}.tif`
- New `source_host` enum value: `chelsa` (D-23)
- Computed KPI file: `data/climate_kpis.json`
- Shared colour breaks file: `data/climate_color_breaks.json`
- `sources.yaml` layer id: `chelsa-climate`, `app_layer: climate`, `classification: continuous`

## Phase status

`08-04` may proceed as written under the `gdd5` outcome (identical static per-variable acquisition
shape to `bio10`), subject to the two follow-up items recorded in the `### W-05` subsection above --
neither blocks starting `08-04`, but both must be resolved inside it (the precondition-check wording
addition before Task 1 runs, and the `gdd5` read-cost re-check as part of Task 3's Stage-1
measurement).

