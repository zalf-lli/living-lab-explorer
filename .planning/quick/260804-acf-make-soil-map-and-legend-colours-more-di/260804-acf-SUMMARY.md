---
phase: quick-260804-acf
plan: 01
status: incomplete
date: 2026-08-04
commits:
  - bf3748c  # Task 1: palette module + distinctness gate
  - aa42a93  # Task 2: rewire map + legend consumers
checkpoint_pending: "Task 3 — human visual verification (blocking gate)"
---

# Quick Task 260804-acf — Make soil map and legend colours more distinct

## What the problem actually was

The reported symptom was "colours too similar to distinguish". Investigation found the
cause is stronger than similarity: the colours were **exactly identical**.

`app/src/components/LLMap/index.jsx` held an 8-entry `SOIL_PALETTE` of near-identical
browns and assigned them by hashing the soil class key with a weak `acc * 31 + charCode`
reduce. Across the 16 distinct soil-group keys present in the five committed BÜK250
fixtures this collapsed into collisions:

- `hessian-low-mountain`: `brown-soils`, `stagnic-soils` and `alluvial-soils` all rendered
  `#b88752` — 3 of the 5 legend swatches were byte-identical.
- `east-brandenburg` and `havellandisches-luch`: `fens` and `ah-c-soils` both `#d0b385`.
- `podzols` and `pelosols` both `#a87445` everywhere.
- 3 of the 8 palette entries were never assigned at all.

A second, independent colour source existed in `app/src/data/layers.js` (`SOIL_LEGEND`,
the pre-load fallback legend), duplicating hexes that could drift from the map fill.

## What shipped

**Task 1 — `bf3748c`**
- New `app/src/data/soil_legend.js`: pure, dependency-free ES module holding the single
  source of truth — `SOIL_GROUP_COLORS` (12 named groups), `SOIL_FALLBACK_PALETTE` (5),
  the water/special/stroke constants, and `getSoilColor()`.
- Palette designed to separate classes on **lightness and hue**, not hue alone (L\* spans
  24 → 89), drawing hues from an Okabe-Ito-style CVD-safe set tinted earthward.
- The weak hash is replaced by FNV-1a (32-bit, `Math.imul`), which the old hash needed
  because it bucketed 3 of the 4 unnamed anthropogenic keys identically.
- `getSoilColor` uses an own-property check so a crafted key (`__proto__`, `constructor`)
  cannot resolve to a prototype member — threat T-acf-01, same defect class as the
  Phase 10 `bySlug` finding.
- New `app/scripts/check_soil_palette.mjs` + `npm run check:soil-palette`: a committed
  regression gate that recomputes CIELAB ΔE76 distinctness over the palette and all five
  committed GeoJSON fixtures. No dependency added (sRGB→XYZ→Lab implemented inline).

**Task 2 — `aa42a93`**
- `LLMap/index.jsx`: removed `SOIL_PALETTE`, `hashSoilKey` and the local `getSoilColor`;
  style constants and the polygon hairline now reference the shared `SOIL_*` tokens.
- `layers.js`: `SOIL_LEGEND` now derives its colours from `SOIL_GROUP_COLORS` /
  `SOIL_WATER_FILL` instead of duplicating hexes, so the pre-load legend cannot drift
  from the loaded one. Also repaired two mojibaked German labels that were wrong against
  the data (`Lessives` → `Lessivés`, `Gewaesser / Sonderflaechen` → `Gewässer /
  Sonderflächen`).

## Verification — actual output

`npm run check:soil-palette` → exit 0:

```
east-brandenburg:      classes=14 uniqueColors=14 mapMinDeltaE=18.0 legendSwatches=7 legendMinDeltaE=22.8
havellandisches-luch:  classes=13 uniqueColors=13 mapMinDeltaE=19.0 legendSwatches=7 legendMinDeltaE=22.8
hessian-low-mountain:  classes=12 uniqueColors=12 mapMinDeltaE=22.0 legendSwatches=7 legendMinDeltaE=22.8
north-hessian-loess:   classes=12 uniqueColors=12 mapMinDeltaE=22.8 legendSwatches=7 legendMinDeltaE=22.8
rheingau:              classes=9  uniqueColors=9  mapMinDeltaE=22.0 legendSwatches=7 legendMinDeltaE=22.8
OK
```

Unique colours now equal class count in every Living Lab; minimum legend swatch
separation is 22.8 ΔE76, previously 0.

- Retired-hex grep over both rewired files: **0 matches**
- `npm run lint` → exit 0
- `npm run build` → exit 0 (127 modules, built in 4.83s)
- No change under `data-pipeline/`; `sync.py` does not generate these files, so
  `python sync.py` will not revert the change.

## Still open

**Task 3 is a blocking `checkpoint:human-verify` gate and has NOT been performed.**
The numbers above are computed distinctness, not a visual check. Someone needs to run
`cd app && npm run dev` and confirm in the browser, per the plan's how-to-verify steps:
the five Living Labs' soil legends read as distinct, water still reads as water, special
areas now read as neutral grey rather than blue-grey, and the DE labels are correct.

## Execution notes (honest record)

- The executor subagent was terminated twice by transient API errors (ENOTFOUND, then
  529 Overloaded) partway through Task 2. It left `LLMap/index.jsx` in a **broken**
  intermediate state: `SOIL_PALETTE` had been deleted while a local `getSoilColor`
  still referenced it and redeclared the imported binding. Task 2 was completed inline
  by the orchestrator and the broken state was fixed before any commit.
- The executor also produced an **out-of-scope commit `ed6e699`** ("docs(phase-11):
  reconcile close-out bookkeeping") touching `.planning/ROADMAP.md`, `.planning/STATE.md`
  and `11-REVIEW.md`. This was not part of this quick task and the executor had been told
  not to update `ROADMAP.md`. It is docs-only and non-destructive; left in place, flagged
  for the user to keep or revert.
- Backlog `TODO-01` is **partially** closed: the colour-divergence half is done; the
  tooltip verbosity and mixed-language half remains open.
