# LL-Explorer — Claude Code Project Guide

## Project Overview

LL-Explorer is a bilingual (EN/DE) Vite+React SPA for visualizing Germany's 5 Living Lab regions.
It is driven by a Python geodata pipeline that produces static files committed to git.

See `.planning/PROJECT.md` for full project context and requirements.

## GSD Workflow

This project uses the Get Shit Done planning system:

- `.planning/ROADMAP.md` — 3-phase roadmap (current milestone: Phase 4)
- `.planning/REQUIREMENTS.md` — 9 v1 requirements with REQ-IDs
- `.planning/STATE.md` — current progress and open questions
- `.planning/research/` — BÜK vector pipeline and content system research

**Current phase:** Phase 1 — LL Content System

**To start executing:** `/gsd-discuss-phase 1` or `/gsd-plan-phase 1`

## Architecture

- `app/` — Vite + React 19 SPA (JavaScript only, no TypeScript)
- `data-pipeline/` — Python 3.12 geodata pipeline
- `data-pipeline/sync.py` — orchestrator: copies outputs + codegens JS source files
- `data-pipeline/sources/sources.yaml` — declarative layer registry
- `app/public/data/` — runtime data (fetched by browser)
- `app/src/data/` — build-time data (imported by JS)

**Pipeline–app contract:** files on disk only. No runtime coupling between Python and React.

## Key Constraints

- Static-only hosting: must work at any sub-path (`base: './'` in `vite.config.js`)
- Python 3.12 required on Windows (geospatial wheel compatibility)
- No TypeScript, no CSS frameworks, no SSR
- External CLI deps: `pmtiles`, `rio`, `quarto`, `R` (must be on PATH or set `PMTILES_BIN`,
  `QUARTO_BIN`, `R_HOME` respectively — R is commonly installed but absent from PATH on Windows)

## Critical Rules (from research)

- **Never write `data/ll_content.json` from any pipeline script** — it is human-owned
- **Always call `make_valid()` after `gpd.read_file()`** for BÜK vector data
- **Always align CRS before clipping** and assert `len(clipped) > 0` to catch silent failures
- **`json.dumps(..., sort_keys=True)`** everywhere in `sync.py` to avoid noisy git diffs

## Development Quick Start

```powershell
cd app
npm install
npm run dev         # dev server with hot reload
npm run build       # production build → app/dist/
npm run lint        # ESLint check
```

Pipeline:
```powershell
cd data-pipeline
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python sync.py                            # copy data + codegen JS files
python python/fetch_nuts.py              # refresh LL boundaries + metadata
python python/build_pmtiles.py --layer landuse-croptypes  # rebuild raster layer
python R/render_reports.py                # render per-LL PDF reports (manual, not in sync.py)
```
