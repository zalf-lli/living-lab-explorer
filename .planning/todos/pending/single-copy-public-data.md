---
id: single-copy-public-data
created: 2026-07-28
source: phase-07 W-01 checkpoint discussion
priority: high
---

# Stop committing `app/public/data/` as a duplicate of `data/`

## Problem

Every pipeline output is committed twice — once under `data/` and once under
`app/public/data/`. Today that is ~29 MB of GeoJSON plus ~51 MB of PMTiles
duplicated, and `.git` is already 541 MB against GitHub's 1 GB recommended
ceiling. Because the pipeline regenerates these files, each re-run appends
another full copy to history; GeoJSON deltas do not compress across versions.

Phase 07's BORIS layer (variant E) adds a projected 126.2 MB across both
copies. With this change it would add ~63 MB.

## Why it is safe

`.github/workflows/deploy-pages.yml` checks out the repo and runs only
`npm ci && npm run build` — it never runs Python. But `data/` -> `app/public/data/`
is a plain file copy with no geospatial dependencies, so it can run in CI.

## Fix

1. Add a copy step to `deploy-pages.yml` before `npm run build`.
2. Add `app/public/data/` to `.gitignore`.
3. `git rm -r --cached app/public/data/`.
4. Keep `sync.py`'s local copy behaviour unchanged so `npm run dev` still works.

## Impact

Halves the committed size of every current and future pipeline output and
reclaims ~80 MB from the working tree. Makes the higher-fidelity BORIS
variants (D, C) affordable if the Phase 07 W-01 decision is ever revisited.

## Notes

Deliberately kept out of Phase 07 scope — see the `## Locked Wave-0 Decisions`
section of `.planning/phases/07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi/07-SPIKE.md`.
