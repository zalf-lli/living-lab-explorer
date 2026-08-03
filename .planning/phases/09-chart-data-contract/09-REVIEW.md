---
phase: 09-chart-data-contract
reviewed: 2026-08-03T00:00:00Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - data-pipeline/README.md
  - data-pipeline/python/chart_contract.py
  - data-pipeline/python/compute_agriculture_chart.py
  - data-pipeline/python/compute_climate_chart.py
  - data-pipeline/python/compute_economic_chart.py
  - data-pipeline/python/compute_landscape_chart.py
  - data-pipeline/python/compute_soil_chart.py
  - data-pipeline/sources/README.md
  - data-pipeline/sources/sources.yaml
  - data-pipeline/sync.py
  - data-pipeline/tests/test_pipeline_outputs.py
findings:
  critical: 0
  warning: 8
  info: 2
  total: 10
status: issues_found
---

# Phase 09: Code Review Report

**Reviewed:** 2026-08-03
**Depth:** standard
**Files Reviewed:** 11
**Status:** issues_found

## Summary

Reviewed the five new chart-computation scripts, the shared `chart_contract.py` envelope
writer, `sync.py`'s chart-publishing plumbing, `sources.yaml`'s chart stanzas, and the
pytest contract suite. No crashes, injection vectors, or hardcoded secrets were found, and
the `json.dumps` direct-call ban (`chart_contract.py`'s own rule) is correctly honored by
every compute script. However, several correctness/consistency gaps were confirmed —
one of which (the economic chart's missing "never show 0%" floor) is not hypothetical: it
is already present in the currently-committed `data/charts/boris-*.json` fixtures. The
remaining findings are unguarded division-by-zero edge cases, an unguarded rounding path
that could reintroduce the exact "looks dropped" bug the pct floor was built to prevent,
non-trivial duplication across the four bar-chart scripts, a `sync.py`-wide violation of
the project's own `sort_keys=True` convention, and a stale `sources/README.md` layer
inventory that omits two of the six declared layers (including `boris` and
`chelsa-climate`, both central to this phase).

## Warnings

### WR-01: Economic chart ships real 0.0% rows today, contradicting the "never drop a row" floor every other bar-chart script implements

**File:** `data-pipeline/python/compute_economic_chart.py:69-77`
**Issue:** `compute_agriculture_chart.py` (lines 113-123) and `compute_landscape_chart.py` /
`compute_soil_chart.py` (`_round_pct`, lines 33-46 / 33-44) both explicitly floor a
genuinely-observed category's displayed `pct` above `0.0` so it never reads as a dropped
row — this is called out as a deliberate, load-bearing "never-drop-a-row" convention in
all three docstrings. `compute_economic_chart.py`'s `series_for_slug` computes
`pct = round(n / total * 100, 1)` with no equivalent floor. This is not a theoretical gap:
the currently-committed fixtures already contain it, e.g.
`data/charts/boris-east-brandenburg.json` has 7 categories at `pct: 0.0` (Campsite,
Public-facility building land, Sports facility, etc., each with `value >= 1`), and
`test_pipeline_outputs.py::test_bar_chart_fixtures_exist_and_match_contract` had to be
loosened from `pct > 0` to `pct >= 0` specifically to tolerate this (see its own
docstring, lines 790-796). A user viewing the Economic tab's bar chart today sees several
categories rendered indistinguishably from an absent/dropped category, which is exactly
what the same convention was designed to prevent on every other tab.
**Fix:** Apply the same floor helper used by soil/landscape (`_round_pct`) to
`compute_economic_chart.py`'s pct calculation, e.g.:
```python
def _round_pct(raw_pct: float) -> float:
    pct = round(raw_pct, 1)
    if pct == 0.0 and raw_pct > 0:
        for decimals in range(2, 6):
            pct = round(raw_pct, decimals)
            if pct > 0:
                break
    return pct

series = [
    {"label": {"en": en, "de": de}, "value": int(n), "pct": _round_pct(n / total * 100)}
    for (en, de), n in counts.items()
]
```
Then relax `test_bar_chart_fixtures_exist_and_match_contract` back to `pct > 0` once the
producer guarantees it, and regenerate the boris chart fixtures.

### WR-02: Unguarded division by zero in three bar-chart scripts when the pixel/area total is zero

**File:** `data-pipeline/python/compute_agriculture_chart.py:109-114`, `data-pipeline/python/compute_landscape_chart.py:63,82`, `data-pipeline/python/compute_soil_chart.py:94,99`
**Issue:** `total_pixels = sum(histogram.values())` (agriculture), `total = sum(non_nodata.values())`
(landscape), and `total = sum(areas.values())` (soil) are all used as a division
denominator (`count / total_pixels * 100`, `count / total * 100`, `value / total * 100`)
with no guard for `total == 0`. This can't happen with any of the five currently-committed
Living Labs, but there is no explicit assertion or friendly error message protecting
against it (unlike the "missing legend value" `RuntimeError`s these same scripts raise
elsewhere for other invalid states) — a future Living Lab whose clip genuinely contains
zero classified pixels, or a soil GeoJSON whose dissolved group areas sum to zero due to
degenerate geometry, would surface as a raw `ZeroDivisionError` traceback instead of an
actionable message.
**Fix:** Add an explicit guard before the division, consistent with this file's existing
`RuntimeError` style, e.g.:
```python
if total_pixels == 0:
    raise RuntimeError(f"{slug}: no classified pixels found for {LAYER_ID} — cannot compute percentages.")
```

### WR-03: Rounded hectare `value` can legitimately round to 0.0, silently reintroducing the "looks dropped" bug the pct floor exists to prevent

**File:** `data-pipeline/python/compute_agriculture_chart.py:127`, `data-pipeline/python/compute_landscape_chart.py:81`
**Issue:** Both scripts use 10 m resolution rasters (`pixel_area_ha = 0.01`). A class with a
single observed pixel yields `value = round(1 * 0.01, 1) == 0.0`. Both docstrings
explicitly acknowledge this trade-off ("`value` (hectares) is left untouched; only the
rounded percentage floor is adjusted") but that means a genuinely-present, single-pixel
class would ship as `value: 0.0, pct: 0.1` — visually indistinguishable from a dropped row
on the `value` axis even though `pct` was carefully protected. This would also violate
`test_pipeline_outputs.py::test_bar_chart_fixtures_exist_and_match_contract`'s own
`assert value > 0` (line 838), i.e. a future raster refresh with a sparse crop/land-cover
class would fail CI rather than silently ship a bad row. No currently-committed fixture
triggers this (smallest values are well above this threshold), but the code has no guard
against it.
**Fix:** Either floor `value` the same way `pct` is floored (e.g. `max(round(count * pixel_area_ha, 1), 0.1)` when `count > 0`), or explicitly document in `chart_contract.py`/the
README that `value` may legitimately show `0.0` for sub-pixel-area classes and relax the
test's `value > 0` assertion to `value >= 0` to match — pick one and make code, docs, and
test agree.

### WR-04: Significant duplicated logic across the four bar-chart compute scripts

**File:** `data-pipeline/python/compute_agriculture_chart.py:66-69`, `data-pipeline/python/compute_economic_chart.py:34-36`, `data-pipeline/python/compute_landscape_chart.py:49-51`, `data-pipeline/python/compute_soil_chart.py:47-49`
**Issue:** `_available_slugs()` / `_ll_slugs()` (four near-identical implementations reading
`data/ll_boundaries.geojson` and extracting the sorted `ll_slug` set), `_round_pct()`
(copy-pasted verbatim between `compute_landscape_chart.py` lines 33-46 and
`compute_soil_chart.py` lines 33-44), and the series sort key
`series.sort(key=lambda entry: (-entry["pct"], entry["label"]["en"]))` (repeated
identically in all four scripts) are all duplicated rather than centralized. Any future
change to one of these behaviors (e.g. tie-break rule, rounding-floor precision) risks
drifting silently between scripts since there is nothing enforcing they stay in sync.
**Fix:** Move `_ll_slugs`, `_round_pct`, and the sort key into a shared helper — either
`chart_contract.py` (since it is already the shared module all five scripts import) or a
new `chart_common.py` — and have all four bar-chart scripts import from it.

### WR-05: `chart_contract.py`'s writers duplicate almost all their logic and enforce no shape invariants at write time

**File:** `data-pipeline/python/chart_contract.py:25-80`
**Issue:** `write_bar_chart` and `write_line_chart` are near-identical (path creation,
`generated_at` timestamp, `json.dumps(..., sort_keys=True)`, print) apart from 2-3 payload
keys. More importantly, despite the module docstring's claim that this is "the single
writer... so the envelope's ... field shape can never drift," neither function validates
its own inputs — e.g. `write_bar_chart` will happily write an empty `series` list, a
`series` entry missing `label`/`value`/`pct`, or a `unit` dict missing `en`/`de`. All of
those invariants are only caught later by the separate pytest suite
(`test_bar_chart_fixtures_exist_and_match_contract`), so running a compute script by hand
(as the docs say is the normal workflow) with a subtly broken input gives no immediate
feedback that the written file is malformed.
**Fix:** Factor the shared envelope-building/write logic into one private helper, and add
a minimal shape assertion (non-empty `series`/`lines`, required keys present) before
writing, so a bad payload fails loudly at the point of computation rather than only in CI:
```python
def _write_chart(*, output_path, payload) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"[ok] wrote {output_path}")
```

### WR-06: `sync.py` codegen functions violate the project's own `sort_keys=True` rule

**File:** `data-pipeline/sync.py:59, 115, 251-253, 297`
**Issue:** CLAUDE.md states explicitly: "`json.dumps(..., sort_keys=True)` everywhere in
`sync.py` to avoid noisy git diffs." `chart_contract.py`'s writers correctly follow this
rule (`sort_keys=True` at line 47/77), but `sync.py` itself does not: `generate_landuse_legend`
(line 59), `generate_land_cover_legend` (line 115), `generate_climate_legend` (lines
251-253), and `generate_layer_sources` (line 297) all call `json.dumps(...)` without
`sort_keys=True`. This means any accidental dict-key reordering upstream (e.g. a
`sources.yaml` edit that changes iteration order, or a Python dict-construction change)
can silently produce a large, noisy diff across `landuse_legend.js`, `land_cover_legend.js`,
`climate_legend.js`, and `layer_sources.js` — exactly the failure mode the rule exists to
prevent.
**Fix:** Add `sort_keys=True` to each of the four `json.dumps` calls listed above, and
regenerate the four `app/src/data/*.js` files to confirm the resulting diff is
key-order-only (verify list ordering, which `sort_keys` does not affect, is unchanged).

### WR-07: `sources/README.md`'s layer inventory is stale — omits `boris` and `chelsa-climate`

**File:** `data-pipeline/sources/README.md:5-10`
**Issue:** The README states "The current file contains four layer entries" and lists only
`landuse-croptypes`, `io-lulc-landcover`, `buek250`, and `bfn-schutzgebiete`. `sources.yaml`
actually declares six layers — `boris` and `chelsa-climate` are both present (and both are
chart-bearing layers this very phase's `chart.script` / `output.chart_pattern` stanzas
target). A developer reading this file to understand "what belongs in each layer entry"
would not learn that two of the six layers, including both newer ones, even exist.
**Fix:** Update the count and bullet list to include all six layers:
```markdown
The current file contains six layer entries:

- `landuse-croptypes`: ...
- `io-lulc-landcover`: ...
- `buek250`: ...
- `bfn-schutzgebiete`: ...
- `boris`: BORIS standard-land-value vector layer, built per Living Lab and packaged as GeoJSON.
- `chelsa-climate`: CHELSA V2.1 climate raster layer, built per (variable, period, Living Lab) and packaged as PMTiles.
```

### WR-08: `pct_change_for_horizon`'s absolute-mode branch divides by `baseline_mean` with no zero/negative guard

**File:** `data-pipeline/python/compute_climate_chart.py:80-82`
**Issue:** `return round(horizon_value / baseline_mean * 100.0, 1)` has no check that
`baseline_mean != 0`. For the current four variables (gdd, bio1 over German Living Labs)
this is very unlikely to be exactly zero or negative, but there is no defensive check, so
a future heat-family variable (or a pathological small-area LL where `area_weighted_mean`
returns exactly 0) would silently produce `inf`/`nan`/a sign-flipped, meaningless
percentage instead of a clear, actionable error like the ones this same file raises
elsewhere (`_guard_rasters_exist`, unknown `change_mode`).
**Fix:**
```python
if change_mode == "absolute":
    if baseline_mean == 0:
        raise RuntimeError(
            f"{slug}/{variable_id}/{horizon}: baseline_mean is 0 — percent change is undefined."
        )
    return round(horizon_value / baseline_mean * 100.0, 1)
```

## Info

### IN-01: `compute_climate_chart.py`'s `--ll` help text is garbled

**File:** `data-pipeline/python/compute_climate_chart.py:132`
**Issue:** `parser.add_argument("--ll", help="Compute only for a single LL slug (implies --dry-run behaviour with --dry-run)")` — the parenthetical is self-referential and doesn't describe real behavior (`--ll` does not imply `--dry-run`; they are independent flags, as `main()` shows).
**Fix:** Simplify to match the other four scripts' consistent phrasing, e.g. `help="Compute only for a single LL slug"`.

### IN-02: Boris `series_for_slug` groups by `(usage_type_en, usage_type_de)` tuple rather than a single canonical key

**File:** `data-pipeline/python/compute_economic_chart.py:70`
**Issue:** `frame.groupby(["usage_type_en", "usage_type_de"])` implicitly assumes the two
columns are always in perfect 1:1 correspondence for every row. If `boris_semantics.py`'s
lookup ever produced a case where the same `usage_type_en` maps to two different
`usage_type_de` strings (or vice versa) — e.g. a future edit that adds a second raw code
resolving to the same English label but a differently-worded German one — this would
silently split into two separate series rows with the same English label, which is easy to
miss visually in the English UI but would show as two distinct bars in the German UI.
**Fix:** Group by whichever field is the true canonical key (likely `usage_type_code` or a
dedicated canonical id from `boris_semantics.py`) and derive the bilingual label from a
single lookup, rather than trusting groupby to preserve 1:1 pairing across two label
columns.

---

_Reviewed: 2026-08-03_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
