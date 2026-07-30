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

