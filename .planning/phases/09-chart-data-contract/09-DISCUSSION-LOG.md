# Phase 9: Chart Data Contract - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions captured in `09-CONTEXT.md` — this log preserves the discussion.

**Date:** 2026-08-03
**Phase:** 09-chart-data-contract
**Mode:** discuss (default)
**Areas discussed:** mock field semantics, chart_type vocabulary, schema doc location,
source field shape, then (after a scope-expansion correction) per-layer chart content
for all 5 tabs, a dedicated line-chart schema shape, and reconciling
REQUIREMENTS.md/ROADMAP.md with the expanded scope.

## Prior Context Loaded

- `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`,
  `.planning/ROADMAP.md`
- Prior phase CONTEXT.md files: Phase 10 (comparison view, depends on Phase 9), Phase 8
  (CHELSA climate — closest precedent for a new `sources.yaml` kind-specific stanza and
  a `unit:{en,de}` generated JSON), Phase 7 (BORIS — bilingual semantic-contract
  precedent)
- No `.planning/DECISIONS-INDEX.md` existed.

## Codebase Scout

Dispatched an Explore agent to research `sources.yaml` layer-entry conventions,
`sync.py` structure/logging, `data-pipeline/README.md` structure, `BarChart.jsx`'s
current (unrelated) data shape, existing bilingual-field conventions, the `mock` flag's
current status, and the `data-pipeline/tests/` smoke-test pattern. Key discovery: the
`mock` flag and its badge component were fully deleted from the app in commit `a37a9b4`
(July 2026) — zero references remain in `app/src` or `data-pipeline`, confirmed
independently via direct grep. Also directly inspected `data/land_cover_class_histogram.json`
(confirmed per-LL keyed) and `app/src/data/chart_data.js` (confirmed placeholder shapes
per tab, including a monthly-values placeholder for climate unrelated to the eventual
line-chart design).

## Todo Cross-Reference

| Todo | Score | Decision |
|------|-------|----------|
| `single-copy-public-data.md` (stop duplicating `app/public/data/` in git) | 0.6 | Reviewed, not folded — repo-size/CI concern, unrelated to the chart data contract |

## Round 1 — Contract-only framing (matched ROADMAP.md's original text)

### `mock` field semantics
**Selected:** Placeholder-data flag — `mock: true` means synthetic/dry-run values, not
real computed data. Recorded as **D-02** (renumbered after scope expansion).

### `chart_type` vocabulary
**Selected:** Open string, "bar" documented as the only current value (at the time).
Superseded by Round 2's discriminator decision (**D-01**) once "line" entered scope.

### Schema documentation location
**Selected:** New section in `data-pipeline/README.md`. Recorded as **D-03**.

### `source` field shape
**Selected:** Plain string — sources.yaml layer id reference. Recorded as **D-04**.

## Scope correction

After drafting the initial CONTEXT.md (matching ROADMAP.md/REQUIREMENTS.md's original
"contract + one-layer dry-run" text) and attempting to commit it, the human rejected the
commit: *"I don't think the context is clear yet — this phase needs to add scripts that
produce the real charts from the spatial data used for each tab."*

Asked to clarify scope directly (full expansion vs. partial vs. revert to original).
**Selected:** Expand Phase 9 to include real chart scripts for every tab.

## Round 2 — Per-layer chart content (after scope expansion)

### Agriculture (landuse-croptypes)
**Options presented:** % area per crop type per LL (new per-LL histogram needed) / count
of distinct crop types / skip for now.
**Selected:** % area per crop type per LL. Recorded as **D-05**.

### Soil (buek250)
**Options presented:** % area per soil_group_key per LL (the original v2-planned "first
chart," now pulled forward) / % area by feature_kind only / skip for now.
**Selected:** % area per soil_group_key per LL. Recorded as **D-06**.

### Landscape (io-lulc-landcover)
**Options presented:** % area per land-cover class per LL (reuses existing
land_cover_class_histogram.json) / skip for now.
**Selected:** % area per land-cover class per LL. Recorded as **D-07**.

### Economic (BORIS)
**Options presented:** % of zones per usage-type category / count of zones per value
quantile bucket / skip for now.
**Selected:** % of zones per usage-type category. Recorded as **D-08**.

### Climate (CHELSA)
**Options presented:** Skip climate's chart entirely (recommended) / % change from
baseline to 2071-2100, one bar per variable.
**User response (free text, not a listed option):** "Line chart with % change per
variable with X axis points for both the intermediate and final future time points."
This introduced a genuinely new requirement — a time-series line chart, not a bar —
which does not fit CHARTS-01's original flat `series:[{label,value,pct}]` shape.

**Follow-up 1 — how to represent multi-point lines in the schema:**
Options presented: add an optional `x` field to flat series items / nest points inside
each series item.
**User response (free text):** "Add a new chart type and expand this decision" — read
as wanting `chart_type` to be a real structural discriminator rather than either
proposed retrofit.

**Follow-up 2 — clarification check:**
Asked directly whether "line" should get its own dedicated schema shape (not reusing
`series` at all), with `chart_type` acting as a discriminator.
**Confirmed:** Yes.

**Follow-up 3 — proposed concrete line shape:**
Proposed `x_axis:[{key,label:{en,de}}]` + `lines:[{label:{en,de}, points:[{x,value}]}]`
as a parallel structure to bar's `series`, sharing the common envelope fields.
**Confirmed:** Yes, use this shape.

Recorded as **D-01** (chart_type as discriminator, both shapes) and **D-09** (climate's
specific line-chart content: % change per variable across the 2 horizons).

## Docs reconciliation

Asked whether to update REQUIREMENTS.md/ROADMAP.md now (since they currently list
"Generic chart logic implementation" as Out of Scope and defer the first real chart to
v2) or leave the discrepancy for the planner to reconcile via CONTEXT.md alone.
**Selected:** Update REQUIREMENTS.md and ROADMAP.md now.

**Actions taken:**
- `.planning/REQUIREMENTS.md` — added CHARTS-03..07 to v1 under a renamed "Chart Data
  Contract & Implementation (Phase 9)" heading; updated CHARTS-01's schema text to the
  chart_type-discriminated bar/line shapes; removed "Generic chart logic applicable to
  all layer types" from Out of Scope; removed the now-superseded "first chart
  implementation" line from v2; added a new v2 Out-of-Scope line clarifying that
  wiring the JSON into the UI (not producing it) is still deferred; updated the
  traceability table with CHARTS-03..07 rows.
- `.planning/ROADMAP.md` — rewrote Phase 9's Goal, Requirements list, added a "Scope
  expanded 2026-08-03" note to the existing Note paragraph, and added success criteria
  #3 (all 5 layers get real chart scripts) and #4 (per-layer content summary),
  replacing the original single crop-types-dry-run criterion #3.

## Locked decisions (final numbering, see 09-CONTEXT.md for full text)

- D-01: `chart_type` is a structural discriminator — "bar" (series shape) vs. "line"
  (x_axis + lines shape)
- D-02: `mock` = fresh placeholder-data flag, decoupled from the deleted Phase 1 badge
- D-03: schema documented in `data-pipeline/README.md`
- D-04: `source` = plain string, sources.yaml layer id
- D-05: agriculture chart = % area per crop type per LL (new pipeline work)
- D-06: soil chart = % area per soil_group_key per LL
- D-07: landscape chart = % area per land-cover class per LL (reuse existing histogram)
- D-08: economic chart = % of zones per usage-type category per LL
- D-09: climate chart = line, % change per variable across 2 horizons
- D-10: chart output is per-(layer, LL) file, all 5 layers get a `chart:` stanza, synced
  via the existing glob-based `_sync_matched_pattern()` helper
- D-11: `sync.py` copies only, never invokes chart scripts
- D-12: pytest smoke tests are required (not discretionary) for all 5 real chart
  outputs

## Claude's Discretion (not asked, left flexible)

- Exact `chart:` stanza key names in `sources.yaml`
- One script per layer vs. a shared driver script (established precedent strongly
  favors one-per-layer)
- Exact projected CRS for soil's area computation (follow
  `compute_protected_area_coverage.py`)
- `sort_keys=True` compliance for new code only (not fixing `sync.py`'s pre-existing
  gap in its other four `json.dumps()` calls)

## Deferred Ideas

- `useChartData()` hook + wiring `BarChart.jsx`/a line-chart component to the new
  contract — v2 requirement
- `--build-all` flag, replacing placeholder KPIs, adding layers beyond the current 5 —
  unchanged v2 items
- De-duplicating `app/public/data/` (the reviewed-not-folded todo)
- Reconciling the project's two competing bilingual-field conventions project-wide

---

*Phase: 09-chart-data-contract*
*Discussion logged: 2026-08-03*
