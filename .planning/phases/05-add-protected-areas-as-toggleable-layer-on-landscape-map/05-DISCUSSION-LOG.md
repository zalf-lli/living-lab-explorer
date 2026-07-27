# Phase 5: Add protected areas as toggleable layer on landscape map - Discussion Log

> **Audit trail only.** Do not use as input to planning or execution. Decisions captured in CONTEXT.md — this log preserves the discussion flow.

**Date:** 2026-07-25
**Phase:** 05-add-protected-areas-as-toggleable-layer-on-landscape-map
**Mode:** discuss (standard interactive discussion)
**Areas discussed:** Data sources & coverage, Layer interaction & stacking, Data loading & performance

---

## Discussion Summary

### Area 1: Data Sources & Coverage

**Question:** Which protected area types should Phase 5 cover?
- **Options presented:** Natura 2000 sites, Nature reserves (Naturschutzgebiete), All available in variables_catalogue.xlsx
- **User selection:** Natura 2000 sites + Nature reserves (Naturschutzgebiete)
- **Decision:** D-01, D-02 — Include both Natura 2000 (SCIs/SPAs) and German nature reserves

**Question:** Geographic scope — Living Lab regions only or all of Germany?
- **Options presented:** LL regions only (clipped), All of Germany
- **User selection:** Show full polygon boundaries for any protected area intersecting LL regions
- **Rationale:** Preserves conservation site context even if boundary extends beyond LL region
- **Decision:** D-03 — Display complete polygon boundaries for intersecting areas

**Question:** Data acquisition method?
- **Options presented:** Manual download + commit to repo (like BÜK), Live fetch from WFS service
- **User selection:** Live fetch from WFS service
- **Rationale:** Keeps protected areas data fresher than manual updates
- **Decision:** D-04 — Acquire via live WFS queries at pipeline runtime

### Area 2: Layer Interaction & Stacking

**Question:** How should protected areas interact with other overlays on Landscape tab?
- **Options presented:** Separate independent toggle, Primary toggle with protected as overlay
- **User selection:** Separate independent toggle
- **Rationale:** Allows users to see both land-use and protected areas simultaneously
- **Decision:** D-05 — Protected areas is an independent toggle, can be shown alongside land-use

**Question:** Layer stacking — always on top or user-reorderable?
- **Options presented:** Protected areas always on top, User-configurable layer order
- **User selection:** Protected areas always on top
- **Rationale:** Simplifies implementation; protected area outlines remain clearly visible
- **Decision:** D-06 — Protected areas always renders on top of land-use layer

### Area 3: Data Loading & Performance

**Question:** When should protected areas GeoJSON load?
- **Options presented:** On toggle (lazy load), With other landscape data (upfront)
- **User selection:** On toggle (lazy load)
- **Rationale:** Reduces initial bundle; protected areas are secondary context layer
- **Decision:** D-07 — Lazy load protected areas on toggle

**Question:** Large dataset handling?
- **Options presented:** Show all polygons (accept slowness), Simplify/downsample for performance
- **User selection:** Show all polygons, accept potential slowness
- **Rationale:** Data fidelity preferred over performance optimization
- **Decision:** D-08 — Render all features without simplification

---

## Areas NOT Discussed

**Visual treatment & interactivity** — Not selected by user. Deferred to planner's discretion and existing component patterns.

---

## Deferred Ideas Captured

- User-configurable layer stacking order
- Protected areas filtering by designation type
- Detailed info panels with management authority & conservation objectives
- Polygon simplification for performance

---

*Discussion completed: 2026-07-25*
