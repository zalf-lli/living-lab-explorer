# Phase 8: Add maps and stats for climate variables using CHELSA data - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `08-CONTEXT.md` — this log preserves how they were reached.

**Date:** 2026-07-29
**Phase:** 08-add-maps-and-stats-for-climate-variables-using-chelsa-data
**Mode:** discuss (default, interactive)
**Areas discussed:** Historic period maps, Future change maps, Variable selection, Climate stats (StatPanel)

User's opening framing: *"specifically I want to discuss how to include maps from the historic time
period as well as change maps for the future and which variables should be included"* — all four
presented gray areas were selected.

---

## Area 1 — Historic period maps

### Q1: What should the "historic" climate map actually show?
- **1981–2010 normal** ← selected — one static climatological normal per variable, matching
  `chelsa_cmip6`'s own internal reference period
- Two historic normals (1901–1930 vs 1981–2010) via CHELSAcruts
- Browsable decade-by-decade time series via CHELSAcruts

### Q2: How does a visitor get from baseline to future change, given one map slot?
- **In-tab period switcher** ← selected — segmented control, raster swaps in place
- Change map only, baseline in tooltip/StatPanel
- Two stacked mini-maps

### Q3: Shared colour scale across LLs, or fitted per LL?
- **Shared across all 5 LLs** ← selected — deliberately inverts Phase 7 D-09
- Per-LL fitted scale (the Phase 7 precedent)
- Shared, plus an explanatory note

### Q4: Should the map allow reading the actual numeric value?
- Hover value readout (ship the numeric grid alongside)
- **Legend only** ← selected — reuses the Phase 6 paletted-PMTiles path verbatim
- LL-wide numbers only, in the StatPanel

**Note:** Q3's recommendation flagged that the shared-scale choice contradicts Phase 7 D-09; the user
selected it anyway, so the inversion is deliberate and is recorded as such in CONTEXT D-09 and in
`<specifics>` to stop a downstream agent "correcting" it back.

---

## Area 2 — Future change maps

Framing given: raster count multiplies as variables × scenarios × horizons × 5 LLs, and Phase 6's
per-LL build already peaked near 2.2 GB.

### Q1: Which scenario(s) and horizon(s)?
- One scenario, one horizon
- **One scenario, two horizons** ← selected
- Two scenarios, one horizon
- Three scenarios, one horizon

### Q2: Which single scenario?
- **SSP3-7.0** ← selected — medium-high, closest to current policies
- SSP5-8.5
- SSP1-2.6

### Q3: Single GCM or ensemble?
- **Multi-model mean of all 5** ← selected — accepts 5× build cost
- Single GCM (MPI-ESM1-2-HR)
- Mean plus model-agreement indicator

### Q4: How is "change" expressed?
- **Per-variable convention** ← selected — temperature absolute, precipitation percent
- Absolute delta everywhere
- Percent everywhere

**User chose "More questions" at the first area-completion check.**

### Q5: How should the change ramp work, given one-signed temperature change?
- **Ramp follows the sign** ← selected — diverging only where sign varies, sequential otherwise
- Always diverging at zero
- Always sequential

### Q6: What does the switcher look like with two horizons?
- Flat three-state
- **Two-level control** ← selected — `[Baseline | Change]`, horizon sub-toggle only in Change mode
- Baseline plus slider

### Q7: Where does the switcher live in Phase 10's comparison view?
- **Shared, one row** ← selected — both columns always show the same epoch
- Per column
- Decide during planning

---

## Area 3 — Variable selection

Framing given: each variable now needs 3 rasters per LL × 5 LLs = 15 rasters.

### Q1: How many variables?
- **Four agro-relevant** ← selected (60 rasters)
- Two headline
- Six to eight
- Full 19-variable bioclim set

### Q2: Which exact four?
- bio1, bio12, bio10, bio18 (all directly emitted by the library)
- bio1, bio12, bio5, bio18
- **Swap in an agronomic index** ← selected

The recommendation explicitly flagged that agronomic indices may not be available from
`chelsa_cmip6`'s CMIP6 output and would need verifying in research. The user selected it regardless,
so a named fallback was established in the follow-up rather than leaving the risk open.

### Q3: Which agronomic index, and what does it displace?
- **Growing degree days (GDD, 5 °C base), replacing bio10** ← selected — fallback `bio10`
- Climatic water balance / aridity, replacing bio18
- Growing season length, replacing bio10

### Q4: How do the variable picker and period switcher sit together?
- **Variable row, period below** ← selected — variable reads as a second tab level
- Variable dropdown
- One combined control row

**User chose "More questions" at the area-completion check.**

### Q5: Which variable is the default on tab open?
- Mean annual temperature (bio1)
- **Growing degree days** ← selected
- Annual precipitation (bio12)

Consequence noted back to the user immediately: leading with an unfamiliar index makes explanatory
copy a requirement, not a nicety. This directly motivated Q7.

### Q6: Should the ramp differ by variable type?
- **Two families by type** ← selected — warm for heat variables, cool for water variables
- One family for all four
- Four distinct ramps

### Q7: What explanatory copy ships with GDD?
- **Per-variable legend note** ← selected — reuses the existing `legendNoteKey` pattern
- Note plus an info popover
- Legend label only

---

## Area 4 — Climate stats (StatPanel)

Framing given: the tab's only two KPI slots are both permanently `null`, live-confirmed unavailable
at Kreis level on both Destatis platforms.

### Q1: What happens to the two null GHG slots?
- **Drop them** ← selected — Climate tab becomes fully CHELSA-sourced
- Keep alongside
- Repurpose in place (D-14 substitution precedent)

### Q2: What does each climate KPI tile show?
- **Baseline plus change** ← selected — accepts a new two-line tile shape in `StatPanel.jsx`
- Baseline only
- Follow the map switcher

### Q3: Which horizon does the tile's change line report?
- **Far horizon only (2071–2100)** ← selected
- Both horizons
- Near horizon only

### Q4: Do the KPI tiles mirror the map variables?
- **Exact mirror** ← selected — four tiles for four variables, nothing else
- Mirror plus number-only extras
- Fewer than four

### Q5: How is a ~1 km grid collapsed to one number per LL?
- **Area-weighted mean** ← selected
- Unweighted cell mean
- Mean plus within-LL range

---

## Deferred ideas captured

- CHELSAcruts observed time series / a second historic normal (from Area 1 Q1)
- Additional SSP scenarios (from Area 2 Q1–Q2)
- Per-pixel hover value readout (from Area 1 Q4)
- Model-agreement stippling (from Area 2 Q3)
- Number-only climate stats with no map (from Area 4 Q4)
- Within-LL min–max range on KPI tiles (from Area 4 Q5)
- Fuller info popover for variable definitions (from Area 3 Q7)

## Claude's discretion (explicitly left open)

Ramp hex values, legend band counts, control styling, GDD base temperature if research contradicts
5 °C, raster build mechanics and file naming, whether a new build script is needed, and gitignore
policy for source downloads.

## Scope creep

None — the discussion stayed inside the Climate tab's map slot and StatPanel throughout.

## Unresolved, flagged as blocking for research

**D-07 / GDD derivability.** `chelsa_cmip6`'s output is bioclim-focused; whether GDD can be derived
from its downscaled monthly temperature fields within this phase is unverified. Fallback `bio10` was
agreed in advance so research can resolve it without a second round of user questions.
