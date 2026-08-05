# Deferred Items — Phase 12

## 12-01: `npm run check:soil-palette` failure (pre-existing, out of scope)

**Found during:** 12-01 Task 3 verification (the plan's overall `<verification>` block lists
`check:soil-palette` as a gate).

**Failure:**
```
FAILED:
  - havellandisches-luch: legend minimum pairwise ΔE76 is 19.0, expected >= 20
```

**Why deferred, not fixed:** This check exercises `app/src/data/soil_legend.js`, a file no task
in 12-01 reads, modifies, or is scoped to touch (its `files_modified` list is
`app/src/i18n_resources.js`, `app/src/i18n.js`, `app/src/hooks/useReportAvailability.js` only).
`git log` confirms the soil-palette files were last changed by an unrelated prior commit
(`fbe9914`, "colour soil bar chart from the map palette"), pre-dating this plan's work. `STATE.md`
already tracks this exact palette work as TODO-01 / quick-task `260804-acf`, "pending human visual
check" — this is a known, already-flagged, pre-existing condition, not a regression introduced by
12-01.

**Scope boundary rule applied:** "Only auto-fix issues DIRECTLY caused by the current task's
changes. Pre-existing warnings, linting errors, or failures in unrelated files are out of scope."

**Recommended next step:** Resolve as part of the existing TODO-01 / `260804-acf` follow-up, not
as part of Phase 12.

## 12-03: same `check:soil-palette` failure recurs (still pre-existing, still out of scope)

**Found during:** 12-03 Task 2 verification (`npm run check:soil-palette` is one of Task 2's
listed acceptance criteria).

**Failure:** identical to the 12-01 entry above — `havellandisches-luch` legend ΔE76 19.0 < 20.

**Why deferred, not fixed:** 12-03's `files_modified` list is
`app/src/components/DownloadReportCTA.jsx`, `app/src/pages/LLDetail.jsx` — neither touches
`app/src/data/soil_legend.js` or any `app/public/data/geojson/*` fixture; `git diff --stat` between
this plan's base commit and its final commit confirms zero changes to either. Same pre-existing,
already-tracked condition (TODO-01 / `260804-acf`), not a regression introduced by 12-03.
