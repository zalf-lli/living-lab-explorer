---
phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data
plan: 01
subsystem: pipeline
tags: [chelsa, cmip6, spike, network-probe, gdal, rasterio]

# Dependency graph
requires: []
provides:
  - data-pipeline/python/probe_chelsa.py — re-runnable, network-only probe (--urls/--tas/--license/--align/--cost) of CHELSA's baseline + CMIP6-future GeoTIFF distribution
  - 08-SPIKE.md — locked W-01..W-04 findings plus a three-way (chelsa-cmip6 / bio10 / gdd5) Recommendation, feeding the 08-03 checkpoint:decision
  - Live-verified future-period URL template — https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/{period}/{GCM_UPPER}/{ssp}/bio/CHELSA_{variable}_{period}_{gcm}_{ssp}_V.2.1.tif
  - A directly-published static `gdd5` file (heat sum >=5C, D-06's exact index) — a third, previously-uncompared option for the D-07 GDD slot
affects: ["08-03 (checkpoint:decision consumes W-01..W-04 and the gdd5 finding)", "08-04 onward (acquisition wave depends on which of chelsa-cmip6/bio10/gdd5 is chosen)"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Index-first, listing-second, candidate-probing-last URL discovery: try the plain-text envidatS3paths.txt path index, then the bucket's public S3 ListObjectsV2-style query (?list-type=2&prefix=...&delimiter=/, discovered live this session since the index 404s), then brute-force candidate templates only as a last resort"
    - "Windows/GDAL CA-bundle ASCII-path workaround (_ensure_ascii_ca_bundle): copies certifi's cacert.pem to an ASCII-safe temp path and pins CURL_CA_BUNDLE/GDAL_CURL_CA_BUNDLE before rasterio/GDAL import, whenever the process's own dependency path contains non-ASCII characters"

key-files:
  created:
    - data-pipeline/python/probe_chelsa.py
    - .planning/phases/08-add-maps-and-stats-for-climate-variables-using-chelsa-data/08-SPIKE.md
  modified: []

key-decisions:
  - "The plain-text envidatS3paths.txt index (the plan's named 'authoritative shortcut') 404s on both os.zhdk.cloud.switch.ch and envicloud.wsl.ch; the chelsav2 bucket instead exposes a public S3 ListObjectsV2-style listing query, used as an equivalent authoritative source (derives the template from a real listed key) before ever falling back to candidate probing — the candidate-probing fallback was implemented but never needed live"
  - "Verified live, not trusted secondhand from the prior halted attempt: CHELSA's own bio/ folder additionally publishes gdd5 (growing degree days >=5C base) as a first-class static bioclim variable, independent of the chelsa_cmip6 Python package, for both the 1981-2010 baseline and all 5 D-04 GCMs at 2071-2100/ssp370. This is a third option for the D-07 GDD slot beyond the two 08-RESEARCH.md compared (chelsa-cmip6 heavy path vs bio10 fallback) — recorded as a finding for 08-03 to weigh, not decided here"
  - "Rule 3 auto-fix: added _ensure_ascii_ca_bundle() after every /vsicurl/ rasterio.open() call failed with UnicodeDecodeError — GDAL's schannel CURL backend cannot parse a CA-bundle path containing non-ASCII characters, and this repo's OneDrive-synced checkout path contains an umlaut ('fuer'). The fix copies certifi's cacert.pem to a plain-ASCII temp path and pins CURL_CA_BUNDLE/GDAL_CURL_CA_BUNDLE before rasterio is imported; without it, every /vsicurl/ read on this machine fails"

requirements-completed: [D-01, D-02, D-03, D-04, D-07]

# Metrics
duration: ~75min (across Task 1-3 commits; a long idle gap between Task 3's completion and its commit was a stream-timeout interruption, not active work)
completed: 2026-07-30
---

# Phase 8 Plan 01: CHELSA URL Structure, License, Alignment and Cost Spike Summary

**Live-verified the future-period CHELSA-CMIP6 URL template, confirmed static monthly `tas` publication, the CMIP6 product's CC0 license, 5-GCM grid alignment, and windowed-read cost — plus discovered and independently verified a directly-published static `gdd5` file that reframes the D-07 GDD decision as a three-way choice.**

## Performance

- **Duration:** ~75 min of active work (Task 1 at 20:02, Task 2 at 21:08, Task 3 completed same session but its commit landed the next day after a stream-timeout interruption — no work was lost or redone)
- **Completed:** 2026-07-30
- **Tasks:** 3
- **Files modified:** 2 (both newly created)

## Accomplishments

- **W-01 (URL structure):** Confirmed the plain-text `envidatS3paths.txt` index 404s on both hosts, then discovered and used the bucket's public S3 `ListObjectsV2`-style listing API to derive the future-period template from a real listed key. All 40 combinations (4 variables x 2 periods x 5 GCMs) resolve HTTP 200 under `https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/{period}/{GCM_UPPER}/{ssp}/bio/CHELSA_{variable}_{period}_{gcm}_{ssp}_V.2.1.tif`. `BASELINE_URL` re-confirmed live for `bio1`/`bio10`/`bio12`/`bio18`.
- **W-02 (monthly tas):** Confirmed **PUBLISHED** for future periods — `.../ssp370/tas/CHELSA_{gcm}_r1i1p1f1_w5e5_ssp370_tas_{MM}_{start}_{end}_norm.tif` resolves live, a different naming convention than the baseline `ncdf/CHELSA_tas_{MM}_...` path but present nonetheless.
- **W-03 (license):** Fetched EnviDat's CKAN `package_show` API live for the CHELSA V2.1 umbrella dataset (DOI 10.16904/envidat.228): CC0-1.0, matching the baseline climatology's license (confirms research Assumption A2). Flagged an unresolved gap: the underlying CMIP6 GCM outputs' own WCRP terms-of-use attribution obligation could not be independently re-verified this session (no live WSL page found stating it explicitly) — recommended for 08-03 sign-off.
- **W-04 (alignment + cost):** All 5 D-04 GCM rasters (bio1, 2071-2100, ssp370) share an identical transform/shape/crs/dtype/nodata via metadata-only `/vsicurl/` opens (confirms research Assumption A3). One Germany-window read measured 5.3-7.5s wall time and a 2.33 MB in-memory array against a 114.1 MB full remote file; extrapolated to the full 44-read acquisition matrix: ~102.7 MB, well within the 300s/5GB caps.
- **Bonus finding (live-verified, not trusted secondhand):** CHELSA's own `bio/` folder listing surfaced a directly-published static `gdd5` file (heat sum >=5C base — exactly D-06's index) for both the baseline and all 5 future-period GCMs, entirely independent of the `chelsa_cmip6` Python package. This is a third option for the D-07 GDD slot that neither `08-RESEARCH.md` nor the plan's own task list anticipated; recorded in `08-SPIKE.md`'s Recommendation as a three-way comparison, decision deferred to 08-03.

## Task Commits

Each task was committed atomically:

1. **Task 1: Probe the future-period CHELSA-CMIP6 GeoTIFF URL structure** - `928d1b8` (feat)
2. **Task 2: Probe static monthly tas, the CMIP6 product license, and 5-GCM grid alignment** - `bff74ff` (feat)
3. **Task 3: Measure windowed-read cost and write 08-SPIKE.md** - `549409b` (feat)

**Plan metadata:** (this commit, made after SUMMARY.md is written)

## Files Created/Modified

- `data-pipeline/python/probe_chelsa.py` - New network-only probe script exposing `--urls`, `--tas`, `--license`, `--align`, `--cost`. Never writes under `data/` (verified: `git status --porcelain data/` stays clean across all runs). Includes `_ensure_ascii_ca_bundle()`, a Windows/GDAL workaround for a live-discovered CA-bundle path bug.
- `.planning/phases/08-add-maps-and-stats-for-climate-variables-using-chelsa-data/08-SPIKE.md` - New spike record with `## W-01` through `## W-04` and `## Recommendation for the 08-03 checkpoint`, every figure printed by the script in this session.

## Decisions Made

- Used the bucket's S3 `ListObjectsV2`-style listing query as the "authoritative shortcut" once the plan's named plain-text index 404'd on both hosts — this is still evidence derived from real listed keys, not a guess, matching the plan's intent even though the literal named mechanism didn't exist.
- Verified the `gdd5` lead live (per this retry's explicit instruction) rather than trusting the prior halted attempt's secondhand note; confirmed it independently across the baseline and all 5 GCMs, and folded it into the Recommendation as a third option rather than silently substituting it for `bio10` or `chelsa-cmip6` — D-07 explicitly reserves that decision for the human at 08-03.
- Applied Rule 3 (auto-fix blocking issue) for the CA-bundle bug: this is a local machine/environment fix (the OneDrive path contains an umlaut), not a plan requirement, but every `/vsicurl/` call failed without it, blocking Task 2/3 entirely.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] GDAL/rasterio `/vsicurl/` opens failed with `UnicodeDecodeError` on this machine**
- **Found during:** Task 2 (`--align`)
- **Issue:** Every `rasterio.open("/vsicurl/https://...")` call raised `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xfc in position 96`. Root cause: GDAL's schannel CURL SSL backend tried to open `certifi`'s `cacert.pem` CA bundle, whose path (inherited from this repo's OneDrive-synced checkout, which contains "für") includes a non-ASCII character schannel cannot handle, producing an undecodable native error string.
- **Fix:** Added `_ensure_ascii_ca_bundle()`, which copies `certifi.where()`'s CA bundle to a plain-ASCII temp path and pins `CURL_CA_BUNDLE`/`GDAL_CURL_CA_BUNDLE` before `rasterio` (and the GDAL session it wraps) is ever imported. Only activates on Windows and only when the certifi path is genuinely non-ASCII.
- **Files modified:** `data-pipeline/python/probe_chelsa.py`
- **Commit:** `bff74ff`

No other deviations — Tasks 1 and 3 executed as written, with the `gdd5` bonus finding treated as additional evidence (per the plan's own instruction to verify it live) rather than a plan deviation.

## Issues Encountered

- The EnviDat CKAN `package_show` response for `chelsa-climatologies` contains non-ASCII characters (author names, smart quotes) that don't print cleanly to this Windows console's default codepage (mojibake `?` boxes appear in terminal output for names like "Jürgen Böhner"); the in-memory strings and the file written to disk are correct UTF-8 — this is a console display artifact only, verified by reading `08-SPIKE.md` back with `encoding="utf-8"`.
- Could not independently verify the exact `gdd5` computation formula (whether it matches the textbook `sum(max(T-5,0))` or a non-standard variant, mirroring the `chelsa_cmip6.BioClim.gdd()` pitfall research already flagged) — no PDF-text-extraction library (`pypdf`, `PyPDF2`, `pdfplumber`, `fitz`) was available in the environment to read CHELSA's technical documentation PDF, and installing one was out of scope for a read-only network probe. Flagged explicitly in `08-SPIKE.md`'s Recommendation table as an open item for 08-03.

## User Setup Required

None - no external service configuration required. All probed endpoints (`os.zhdk.cloud.switch.ch`, `envicloud.wsl.ch`, `www.envidat.ch`) are public and unauthenticated.

## Next Phase Readiness

- `08-03` (the blocking `checkpoint:decision`) now has three options to present to the human instead of two: `chelsa-cmip6==1.4` (heavy, ~10 transitive deps, non-standard GDD formula), `bio10` fallback (light, zero new deps, not actually GDD), and `gdd5` static file (light, zero new deps, matches D-06's literal index but formula unverified against CHELSA's own spec). `08-SPIKE.md`'s Recommendation section presents all three with measured costs and does not pre-empt the decision.
- `08-04` onward can proceed with the confirmed baseline + future-period URL templates and the measured/extrapolated acquisition-cost budget (~102.7 MB / ~230-330s projected for the 44-read matrix) regardless of which GDD path 08-03 chooses, since bio1/bio12/bio18's acquisition shape is unaffected by that decision.
- Before `sources.yaml` is finalized, a human should confirm the CMIP6 GCM outputs' own WCRP attribution obligation (flagged as unconfirmed in W-03) and, if the `gdd5` path is chosen, independently verify its exact formula against CHELSA's technical documentation PDF.

---
*Phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data*
*Completed: 2026-07-30*

## Self-Check: PASSED

- FOUND: data-pipeline/python/probe_chelsa.py
- FOUND: .planning/phases/08-add-maps-and-stats-for-climate-variables-using-chelsa-data/08-SPIKE.md
- FOUND commit: 928d1b8 (Task 1)
- FOUND commit: bff74ff (Task 2)
- FOUND commit: 549409b (Task 3)
