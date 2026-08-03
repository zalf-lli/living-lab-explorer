# LL-Explorer — Phase 4: Data Pipeline & Content System

## What This Is

LL-Explorer is a bilingual (EN/DE) Vite+React SPA for exploring Germany's five Living Lab (LL) regions.
It presents an SVG overview map, interactive Leaflet detail maps with PMTiles raster overlays, and KPI
summaries. Content is produced offline by a Python geodata pipeline and committed as static files served
alongside the app — no server or API at runtime.

Phases 0–3 are complete. This milestone covers Phase 4: replacing ad-hoc hardcoded data with a
structured content system (4.1), extending the pipeline to handle vector sources with a BKG BÜK soil
example (4.2), and defining the contract for per-source chart summaries (4.3).

## Core Value

A researcher or stakeholder can open the app and immediately see accurate, up-to-date geodata and
statistics for any of the five Living Labs — without any server infrastructure.

## Requirements

### Validated

- ✓ Landing page with SVG Germany overview map + 5 LL cards — Phase 1
- ✓ LL detail page with react-leaflet map bounded to the selected LL — Phase 1
- ✓ Layer tabs (active layer swap, "coming soon" states for unavailable layers) — Phase 1
- ✓ Bilingual EN/DE UI with language toggle and localStorage persistence — Phase 2
- ✓ Hash-based routing compatible with TYPO3 sub-path and GitHub Pages — Phase 1
- ✓ PMTiles raster overlay (landuse / crop types layer) — Phase 3
- ✓ Declarative pipeline layer registry via `sources.yaml` — Phase 3
- ✓ Static Vite build deployable to GitHub Pages and TYPO3 — Phase 3
- ✓ Per-source chart data contract (schema + `sources.yaml`/`sync.py` plumbing) plus real computed chart data for all 5 chart-bearing layers across all 5 Living Labs, bilingual human-approved — Phase 9

### Active

- [ ] Hand-authored LL content JSON capturing taglines, descriptions, NUTS-3 codes, colours, and display icons
- [ ] `sync.py` merges hand-authored content with pipeline-computed KPIs into a single `ll_metadata.json`
- [ ] BKG BÜK soil layer processed through the pipeline as a working vector data example
- [ ] `--all` flag (or equivalent) rebuilds every layer declared in `sources.yaml` in one command
- [ ] Smoke tests verify pipeline outputs: file existence, correct CRS, non-empty geometry/tiles

### Out of Scope

- TypeScript — project is confirmed JavaScript only
- SSR / Next.js — Vite static build is the target
- Authentication — public anonymous site
- Generic chart logic implementation — data too varied; contract only in this milestone
- Tailwind / CSS-in-JS / CSS modules migration — inline-style-with-theme pattern stays
- React Native / Expo — not applicable

## Context

- Five Living Labs: each is a set of NUTS-3 regions with an `ll_slug` identifier shared between
  pipeline and frontend (`east-brandenburg`, `uelzen`, etc.)
- Currently, LL display config (colours, icons, KPI values, taglines) is split across
  `fetch_nuts.py` (NUTS codes, metadata) and `app/src/data/ll_display.js` (display config).
  Phase 4.1 consolidates this into a single hand-authored JSON.
- The pipeline–app contract is files on disk: `app/public/data/` (fetched at runtime) and
  `app/src/data/` (imported at build time). `sync.py` is the bridge.
- BKG BÜK is a German federal soil classification vector dataset (polygon layer). It requires
  a different pipeline path than raster PMTiles, making it the right forcing function for
  extending the pipeline to handle vector sources.
- Chart data is source-specific (e.g. % area per soil class for BÜK, % area per crop type
  for landuse). Phase 9 delivered both the schema/plumbing contract and real computed
  chart-computation scripts for all 5 chart-bearing layers; wiring that JSON into UI chart
  components is deferred to a later phase (chart data contract only, not rendering).
- The `data-pipeline/R/` directory is a stub; R-based fetchers are out of scope for this milestone.

## Constraints

- **Tech stack**: Vite + React 19, JavaScript only (no TypeScript), no CSS frameworks
- **Deployment**: Must work as plain static files at any sub-path (`base: './'` in Vite config)
- **Pipeline runtime**: Python 3.12 on Windows (geospatial wheel compatibility); external CLIs `pmtiles` and `rio` required
- **Tooling simplicity**: No new heavy dependencies without a clear forcing function
- **Data privacy**: Source rasters are gitignored and must be downloaded separately; BKG BÜK access method TBD
- **No tests (existing)**: Project has no test runner; smoke tests added in 4.2 will be the first

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Single `ll_metadata.json` output (merged) | App reads one file; sync.py owns the merge | — Pending |
| Hand-authored JSON in repo (not CMS) | Researchers are comfortable with git; no backend needed | — Pending |
| BKG BÜK as vector pipeline example | Open federal dataset, polygon layer, meaningful for all 5 LLs | — Pending |
| Chart contract only (no generic logic) | Data too varied to generalise until real examples exist | — Pending |
| Smoke tests only | Fast to write, fast to run, appropriate for prototype stage | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-08-03 after Phase 9 (Chart Data Contract) completion*
