# Deferred Items — Phase 04 Plan 05

- `app/src/data/kpi_icons.js` (`KPI_ICONS` catalogue) is now unreferenced anywhere in
  `app/src/` after `KPIStrip.jsx` (its only consumer) was deleted in Task 2 of this plan.
  Not deleted here: it is out of this plan's declared `files_modified` scope, and Task 1's
  `StatPanel` intentionally does not use per-field icons (UI-SPEC marks icons "optional
  scope," not mandated). Leaving the file in place is harmless (unused export, no runtime
  cost) but a future cleanup pass could remove it if no tab ever adopts icons.
