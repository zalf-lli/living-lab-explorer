# Phase 4: Destatis Statistics Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-24
**Phase:** 04-destatis-statistics-integration-source-process-and-app-integ
**Areas discussed:** Placeholder resolution policy / KPI restructuring, Indicator review gate, Which stat groups go live, Table verification scope

---

## Placeholder resolution policy (initial framing)

| Option | Description | Selected |
|--------|-------------|----------|
| One-time human edit strips placeholders | Human edits `ll_content.json` once; merge logic unchanged | |
| Change merge policy: computed-wins for allowlist | New allowlist in `_deep_merge` | |
| Treat '-' as explicit sentinel | Merge skips literal '-' values | |

**User's choice:** Free-text — redirected the discussion entirely toward restructuring KPIs into
per-tab sets (Agriculture/Soil/Climate/Landscape/Socio-economic) instead of answering the merge-policy
options directly. Destatis variables would serve as "some of the KPIs" across each tab.
**Notes:** This reframed three of the four originally-selected areas at once (placeholder policy,
which stat groups go live, and implicitly review/verification scope).

---

## KPI layout restructuring

| Option | Description | Selected |
|--------|-------------|----------|
| Replace KPIStrip entirely | One tab-aware component replaces the fixed strip | ✓ |
| Add a new panel per tab, keep KPIStrip | KPIStrip stays, new panel added below | |

**User's choice:** Replace KPIStrip entirely.

| Option | Description | Selected |
|--------|-------------|----------|
| Flip to available once KPIs exist | Climate/Economic tabs go live independent of map layer | ✓ |
| Keep coming-soon until map layer also exists | Tabs stay gated until both map + KPIs ready | |

**User's choice:** Flip to available once KPIs exist.

---

## Catalogue group → tab mapping

| Option | Description | Selected |
|--------|-------------|----------|
| Agriculture→land use, Social→economic, Environment split | Emissions→climate, nitrate/sealed-surface→soil | (superseded, see below) |
| Agriculture→land use, Social→economic, Environment→climate (all) | Single bucket for Environment | |
| Let me assign this myself | Free-form per-variable mapping | (chosen path) |

**User's choice:** Free-text — introduced the tab rename (land use→Agriculture) and a brand-new
"Landscape" tab, rather than picking one of the two structured options.
**Notes:** "The map in the currently named land use tab actually reflect only crop types so this can
be re-named 'Agriculture' and a new tab for Landscape can be added... The currently named 'Economic'
tab can simply be re-named socio-economic and social variables mapped to it. Then split the
environment variables as per the suggestion."

### Follow-up: where do Environment variables land now that Landscape exists?

| Option | Description | Selected |
|--------|-------------|----------|
| Landscape tab gets most of it | Forest/protected-area/settlement/sealed-surface→Landscape; emissions→Climate; nitrate→Soil | ✓ |
| Landscape tab gets everything in Environment | All 10 vars in one bucket | |
| Let me assign this myself | Free-form | |

**User's choice:** Landscape tab gets most of it (recommended split).

### Follow-up: does Landscape get a map layer?

| Option | Description | Selected |
|--------|-------------|----------|
| KPI-only for now | No map overlay this phase | ✓ |
| Needs a map layer in this phase too | New map layer required | |

**User's choice:** KPI-only for now.

---

## Placeholder resolution policy (re-asked, adapted to per-tab shape)

| Option | Description | Selected |
|--------|-------------|----------|
| One-time human edit strips placeholders | Human/executor edits `ll_content.json` once | ✓ (as clarified below) |
| Change merge policy: computed-wins for allowlist | New allowlist in `_deep_merge` | |
| Treat '-' as explicit sentinel | Merge skips literal '-' | |

**User's choice:** Free-text — "All the values in ll_content.json can be considered as placeholder
only all can be overwritten and KPIs can be adjusted based on destatis variables if necessary."
**Notes:** Generalizes beyond the three options — the entire file's numeric content is fair game to
overwrite, not just specific flagged fields, and the KPI list itself can flex during implementation.

### Follow-up: who performs the ll_content.json edit?

| Option | Description | Selected |
|--------|-------------|----------|
| Executor edits it directly as a one-time content update | Satisfies CLAUDE.md (no pipeline-script write) | ✓ |
| I'll edit it myself after the pipeline runs | User does the edit by hand | |

**User's choice:** Executor edits it directly.

### Follow-up: fixed KPI count or driven by review outcome?

| Option | Description | Selected |
|--------|-------------|----------|
| Flexible — driven by review outcome | KPI count varies per tab based on include_yn | |
| Fixed count per tab, curated now | Pick specific variables now | ✓ |

**User's choice:** Fixed count per tab, curated now.

### Follow-up: proposed curated list confirmation

Claude proposed: Agriculture (cropland area, farm count, avg farm size, organic share); Soil (N
surplus, P surplus, groundwater nitrate); Climate (CH4, N2O emissions); Landscape (forest area,
protected area, sealed surface); Socio-economic (population, GDP/capita, unemployment, household
income).

| Option | Description | Selected |
|--------|-------------|----------|
| Looks right | Lock in the proposed list | ✓ |
| Let me adjust some picks | User specifies swaps | |

**User's choice:** Looks right.

---

## Indicator review gate

| Option | Description | Selected |
|--------|-------------|----------|
| Verify only the picked variables | Scope narrows to ~10-12 tables behind the curated picks | ✓ |
| Do the full 71-variable expert review now | Fill include_yn/priority for entire catalogue | |

**User's choice:** Verify only the picked variables.

---

## Table verification scope & fallback

| Option | Description | Selected |
|--------|-------------|----------|
| Swap in the next-best catalogue variable | Replace a failed table's variable with another from the same group | ✓ |
| Show that KPI as pending/unavailable | Leave the slot empty with the UI-SPEC pending state | |

**User's choice:** Swap in the next-best catalogue variable.

| Option | Description | Selected |
|--------|-------------|----------|
| Out of scope — swap/defer instead | Don't pursue Regionalstatistik.de registration | |
| Pursue Regionalstatistik.de if needed | Register for the second host if a table lives there | ✓ |

**User's choice:** Pursue Regionalstatistik.de if needed (diverges from the recommended default).

---

## Claude's Discretion

- Whether `LAYERS` array internal `id` values change or only display labels/i18n strings change.
- Exact `StatPanel`/`DataRow` layout differences for KPI-only tabs vs. map+KPI tabs.
- Whether the ~54 unpicked catalogue variables' `include_yn`/`priority_1_3` columns get touched at all.
- Exact copy/UX for a tab with real KPIs but no map layer yet.

## Deferred Ideas

- Full 71-variable expert review (Phase 3.1-style human-in-the-loop pass) — future phase if more
  indicators are wanted.
- Map layers for Climate, Landscape, and Socio-economic tabs — future phases.
- The ~54 unpicked catalogue variables — remain available for future consideration.
