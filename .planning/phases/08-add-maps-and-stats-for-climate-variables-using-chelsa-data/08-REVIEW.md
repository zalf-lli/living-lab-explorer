---
phase: 08-add-maps-and-stats-for-climate-variables-using-chelsa-data
reviewed: 2026-07-30T00:00:00Z
depth: standard
files_reviewed: 19
files_reviewed_list:
  - .gitignore
  - app/src/components/PeriodSwitcher.jsx
  - app/src/components/StatPanel.jsx
  - app/src/components/VariablePicker.jsx
  - app/src/data/climate_legend.js
  - app/src/data/layer_sources.js
  - app/src/data/layers.js
  - app/src/i18n.js
  - data-pipeline/python/build_climate_pmtiles.py
  - data-pipeline/python/build_pmtiles.py
  - data-pipeline/python/compute_climate_color_breaks.py
  - data-pipeline/python/compute_climate_kpis.py
  - data-pipeline/python/fetch_climate.py
  - data-pipeline/python/probe_chelsa.py
  - data-pipeline/sources/sources.yaml
  - data-pipeline/sync.py
  - data-pipeline/tests/check_color_breaks.py
  - data-pipeline/tests/test_pipeline_outputs.py
  - data/climate_color_breaks.json
  - data/climate_kpis.json
findings:
  critical: 1
  warning: 2
  info: 1
  total: 4
status: issues_found
---

# Phase 8: Code Review Report

**Reviewed:** 2026-07-30T00:00:00Z
**Depth:** standard
**Files Reviewed:** 19
**Status:** issues_found

## Summary

Phase 8 adds a full CHELSA-climate acquisition/build pipeline (`fetch_climate.py`,
`compute_climate_color_breaks.py`, `compute_climate_kpis.py`, `build_climate_pmtiles.py`)
plus the app-side codegen and UI plumbing (`climate_legend.js`, `layer_sources.js`,
`layers.js`, `i18n.js`, `PeriodSwitcher.jsx`, `VariablePicker.jsx`, `StatPanel.jsx`
delta rendering). The generated legend bands, ramp colours, and JSON artifacts were
cross-checked against their producers and are internally consistent (breaks strictly
increasing, hex stops match the locked 9-stop palette, JS/Python ramp colour arrays
byte-match, band label formatting matches `climate_color_breaks.json` exactly).

One correctness defect was found in the newly-added change-field derivation
(`fetch_climate.py::_derive_change_field`): it does not actually implement the
nodata guard its own docstring claims, for either the absolute or the percent
branch. Any nodata pixel inside the Germany-extent fetch window (plausible near
the North Sea/Baltic coastline and lake bodies within the configured bbox) silently
produces a wrong, non-nodata, finite value that survives every downstream
`!= nodata` / `isfinite` filter in `compute_climate_color_breaks.py` and
`compute_climate_kpis.py`, corrupting the pooled percentile breaks and the
area-weighted KPI means without any test or assertion catching it. This is
classified Critical because it's exactly the "silent failure" class of bug
CLAUDE.md's own rules (assert non-empty, catch silent failures) are meant to guard
against, and no existing test exercises it.

Two lower-severity issues were also found: a dead logic branch in the spike tool
`probe_chelsa.py` (harmless today because of a working fallback, but proves a stale
code path), and an Info-level observation that `resolveLayerAsset`'s new
variable/period token support has no live caller yet (the `climate` `LAYERS` entry
is still `type: 'placeholder'`), which is presumably intentional (map wiring
deferred to a later wave) but is worth flagging so it isn't lost.

## Critical Issues

### CR-01: `_derive_change_field` does not guard against nodata baseline/future pixels, contradicting its own docstring

**File:** `data-pipeline/python/fetch_climate.py:233-246`

**Issue:** The function's docstring states: *"The percent branch guards against a
zero/nodata baseline denominator so a division by a dry cell cannot produce an
infinity that later poisons 08-06's colour breaks."* The implementation does not
do this:

```python
def _derive_change_field(future: "np.ndarray", baseline: "np.ndarray", *, change_mode: str, nodata) -> "np.ndarray":
    if change_mode == "absolute":
        return (future - baseline).astype(np.float32)          # <-- no nodata guard at all
    if change_mode == "percent":
        result = np.full_like(baseline, nodata, dtype=np.float32)
        safe = np.isfinite(baseline) & (baseline != 0)          # <-- never excludes baseline==nodata or future==nodata
        result[safe] = ((future[safe] - baseline[safe]) / baseline[safe] * 100.0).astype(np.float32)
        return result
    raise ValueError(f"Unknown change_mode {change_mode!r}")
```

`baseline`/`future` pixels that were nodata in the source raster are converted to
the sentinel `-9999.0` in `_read_window` (a perfectly finite float, not `NaN`), so
`np.isfinite(-9999.0)` is `True` and `-9999.0 != 0` is `True`. Concretely:

- **Absolute branch (`gdd`, `bio1`):** if either `baseline` or `future` is `-9999`
  for a pixel, `future - baseline` produces a huge, finite, wrong number (e.g.
  `5 - (-9999) = 10004`) that is written straight into the change-field GeoTIFF.
  There is no fallback to `nodata` in this branch at all.
- **Percent branch (`bio12`, `bio18`):** `safe` only excludes `baseline == 0`; a
  `-9999` baseline or a `-9999` future both pass `safe` and produce a wrong,
  finite percentage (e.g. two nodata pixels: `((-9999) - (-9999)) / (-9999) * 100 = -0.0`,
  read back downstream as a *real* zero-percent-change data point instead of nodata).

Because the corrupted values are neither exactly `nodata` (`-9999`) nor `NaN`, they
pass every downstream filter unchanged:
- `compute_climate_color_breaks.py::_pooled_values_for_slug`: `valid = band[(band != nodata) & np.isfinite(band)]`
- `compute_climate_kpis.py::area_weighted_mean`: `band = np.where(band == src_nodata, np.nan, band)`

so the corrupted pixels silently enter the pooled percentile breaks (`data/climate_color_breaks.json`)
and the area-weighted KPI means (`data/climate_kpis.json`) — precisely the class of
silent-failure bug CLAUDE.md's "assert non-empty" / "catch silent failures" rules
exist to prevent, and no test in `test_pipeline_outputs.py` or
`check_color_breaks.py` exercises nodata-adjacent pixels to catch it. The
Germany-extent bbox (`xmin 5.5, ymin 47.0, xmax 15.5, ymax 55.5`) plausibly includes
North Sea/Baltic coastal water and inland lake bodies where CHELSA's terrestrial
rasters carry nodata, so this is not a purely theoretical edge case.

**Fix:**
```python
def _derive_change_field(future: "np.ndarray", baseline: "np.ndarray", *, change_mode: str, nodata) -> "np.ndarray":
    result = np.full_like(baseline, nodata, dtype=np.float32)
    valid = (
        np.isfinite(baseline) & np.isfinite(future)
        & (baseline != nodata) & (future != nodata)
    )
    if change_mode == "absolute":
        result[valid] = (future[valid] - baseline[valid]).astype(np.float32)
        return result
    if change_mode == "percent":
        safe = valid & (baseline != 0)
        result[safe] = ((future[safe] - baseline[safe]) / baseline[safe] * 100.0).astype(np.float32)
        return result
    raise ValueError(f"Unknown change_mode {change_mode!r}")
```
Also add a regression test (e.g. in `test_pipeline_outputs.py` or a new unit test
importing `_derive_change_field` directly) asserting that a `nodata`-valued
baseline or future pixel always resolves to `nodata` in the output for both
`change_mode` branches.

## Warnings

### WR-01: `probe_urls()` never assigns `template` from a resolved plain-text S3 path index, contradicting the surrounding logic

**File:** `data-pipeline/python/probe_chelsa.py:192-202`

**Issue:**
```python
if index_hit:
    response = requests.get(index_hit, timeout=HTTP_TIMEOUT)
    matching_lines = [
        line for line in response.text.splitlines() if "ssp370" in line and "2071-2100" in line
    ]
    if matching_lines:
        template_source = f"S3 path index ({index_hit})"
        print(f"[probe] index resolved with {len(matching_lines)} matching lines")

if template is None:
    ...  # falls through to S3 ListObjectsV2 listing / brute-force candidates
```
Even when `index_hit` is found and `matching_lines` is non-empty, `template`
itself is never assigned inside this branch (only `template_source` is set) — the
subsequent `if template is None:` block always evaluates `True` and always falls
through to the listing/candidate-probing fallback, silently discarding the work
done resolving `matching_lines`. Currently harmless in practice because both hosts'
plain-text index 404 (per the code's own comments), so the fallback always runs
anyway — but the branch is dead code that would misbehave (report a
`template_source` inconsistent with the `template` actually used) the moment the
plain-text index starts resolving.

**Fix:** Either derive `template` from the matched line (e.g. parse the URL out of
`matching_lines[0]` and assign it to `template`), or delete the dead branch
entirely and rely solely on the S3 listing / candidate fallback that already
works.

### WR-02: New `resolveLayerAsset` variable/period token support has no reachable caller

**File:** `app/src/data/layers.js:97-119`

**Issue:** `resolveLayerAsset` was extended in this phase to interpolate
`{variable}`/`{period}` tokens (in addition to `{slug}`) for raster layers, but the
only `LAYERS` entry for `climate` is still declared as
`{ id: 'climate', type: 'placeholder', pmtilesUrl: null, legend: null, available: true }`
(line 49) — there is no `type: 'raster'` / `pmtilesUrlPattern` entry that would
ever exercise the new branch. This is most likely intentional (the actual LLMap
wiring is deferred to a later wave/phase, matching `PeriodSwitcher.jsx`'s own
comment about "Phase 10's comparison columns"), but as shipped, the new
variable/period resolution logic is untested and unreachable dead code within this
phase's diff.

**Fix:** No action required if map wiring is confirmed to land in a later phase;
otherwise add the `climate` raster `LAYERS` entry (with
`pmtilesUrlPattern: 'data/pmtiles/climate-{variable}-{period}-{slug}.pmtiles'`) and
at least one call site/test exercising the variable/period substitution path in
this phase.

## Info

### IN-01: `check_color_breaks.py` / `test_pipeline_outputs.py` do not test nodata-boundary pixels

**File:** `data-pipeline/tests/check_color_breaks.py:46-123`, `data-pipeline/tests/test_pipeline_outputs.py:649-666`

**Issue:** Both the standalone contract checker and the pytest wrapper validate
`data/climate_color_breaks.json`'s shape (strictly-increasing breaks, permitted hex
stops, ramp/sign consistency) but never validate that the underlying per-pixel data
excludes corrupted nodata-adjacent values (see CR-01). This is why CR-01 shipped
without any test catching it.

**Fix:** Once CR-01 is fixed, consider adding a unit test around
`_derive_change_field` directly (pure function, no I/O) asserting the nodata
contract, rather than only asserting properties of the final aggregated JSON.

---

_Reviewed: 2026-07-30T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
