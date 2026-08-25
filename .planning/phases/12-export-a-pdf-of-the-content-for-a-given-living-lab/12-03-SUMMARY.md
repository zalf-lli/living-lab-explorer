---
phase: 12-export-a-pdf-of-the-content-for-a-given-living-lab
plan: 03
subsystem: app-ui
tags: [react, download-cta, pdf-report, i18n, ui-spec]
dependency-graph:
  requires:
    - app/src/hooks/useReportAvailability.js (12-01)
    - llDetail.downloadReport* i18n keys (12-01)
  provides:
    - app/src/components/DownloadReportCTA.jsx (compact + full variants, exports DownloadReportCTA)
    - Both LLDetail.jsx CompareCTA call sites now render DownloadReportCTA as a shrinking sibling
  affects:
    - app/src/pages/LLDetail.jsx (LayoutSplit, LayoutStacked)
tech-stack:
  added: []
  patterns:
    - "Conditional-render-null gate before any JSX construction (ContactManagerButton pattern), implementing D-18"
    - "flex: '1 1 auto', minWidth: 0 wrapper for the shrink-leftward sibling layout (D-15)"
    - "normalizeLanguage(i18n.resolvedLanguage) as the single source of active-language derivation, replacing ad-hoc startsWith('de') ternaries"
key-files:
  created:
    - app/src/components/DownloadReportCTA.jsx
  modified:
    - app/src/pages/LLDetail.jsx
decisions:
  - "Header comment names D-15 through D-18 and 12-UI-SPEC.md but avoids the literal word 'dashed' (acceptance criteria requires zero occurrences of that string in the file) while still explaining the solid-vs-dashed border distinction in different words"
metrics:
  duration: "~40 minutes"
  completed: 2026-08-05
---

# Phase 12 Plan 03: Download PDF report control (DownloadReportCTA) Summary

Built the one new user-facing UI surface this phase adds: a "Download PDF report" control beside
`CompareCTA` on the Living Lab detail page, implementing every locked value in `12-UI-SPEC.md`
literally (spacing, typography, colour, copy, accessibility) with zero deviation. The control is
a self-contained component gated by the `useReportAvailability` hook built in plan 12-01 — it
renders nothing until that hook's HEAD-probe confirms a `report-{slug}-{lang}.pdf` exists, and
disappears entirely (not greyed out) if it doesn't.

## What Was Built

### Task 1 — `app/src/components/DownloadReportCTA.jsx`
New component exporting `DownloadReportCTA({ compact = false, ll, lang })`. Calls
`useReportAvailability(ll.slug, lang)` first and returns `null` immediately if unavailable,
before any JSX is constructed — mirrors `ContactManagerButton`'s `if (!manager) return null`
early-exit and implements D-18's "whole section omitted, not disabled" contract.

The anchor is a plain `<a href="data/reports/report-{slug}-{lang}.pdf" download="report-{slug}-{lang}.pdf">`
(relative path, no leading slash, `base: './'`-safe) with no `onClick`, `target`, `rel`, or
disabled-while-downloading state — the browser's native download UI takes over on click.
Accessibility: `aria-label`/`title` both set from `t('llDetail.downloadReportAria', { name: ll.name })`,
and the `⬇` glyph wrapped in `<span aria-hidden="true">`.

Full variant (`compact === false`) mirrors `CompareCTA`'s card DOM 1:1 (`C.limePale` background,
`14px` radius, `16px 24px` padding, flex row) with one deliberate difference locked by UI-SPEC:
a **solid** `2px ${C.lime}` border (not dashed) — a finished-artifact affordance, not an
"add / not-yet-configured" one. Title/body text use `C.green`/`C.greenMid` at the UI-SPEC-locked
sizes. Compact variant renders the pill anchor alone, no outer card, per UI-SPEC's "Deliberate
content-density difference" section. All spacing literals are on the project's 4px grid
(8/16/24px), intentionally not copying `CompareCTA`'s own off-grid `7px`/`20px` values. No hover
or focus-override styling was added (`outline: 'none'` never appears in the file).

### Task 2 — Wiring into both `LLDetail.jsx` call sites
Imported `DownloadReportCTA` and `normalizeLanguage` (from `../i18n.js`) into `LLDetail.jsx`.
Both `LayoutSplit` and `LayoutStacked` now destructure `i18n` alongside `t` from
`useTranslation()` and derive `const lang = normalizeLanguage(i18n.resolvedLanguage)` — reusing
the project's single normalization helper rather than adding a sixth `startsWith('de')` ternary
(STATE.md TODO-03 / WR-03 debt was not compounded).

Compact call site (`LayoutSplit`, sidebar): `CompareCTA compact` now sits inside
`<div style={{ flex: '1 1 auto', minWidth: 0 }}>`, sibling to `<DownloadReportCTA compact ll={ll} lang={lang} />`,
both wrapped in a `display: flex, gap: 16, alignItems: 'center'` row.

Full call site (`LayoutStacked`, bottom of page): the existing `{ padding: '16px 32px 32px' }`
wrapper gained `display: flex, gap: 16, alignItems: 'stretch'`; `CompareCTA` moved into the same
`flex: '1 1 auto', minWidth: 0` wrapper, with `<DownloadReportCTA ll={ll} lang={lang} />` beside
it inside a `flexShrink: 0` div.

No `isComparing` conditional was added (count in the file is unchanged from before this plan,
still 3 occurrences, all pre-existing). `ComparisonColumn` — confirmed by direct read and by a
`sed`-scoped grep — never renders `CompareCTA` or `DownloadReportCTA`, so D-17's "hides during
comparison" requirement is satisfied structurally by the sibling placement alone.

## Verification

- `cd app && npm run lint` — exits 0 (both commits)
- `cd app && npm run build` — exits 0 (both commits)
- All plan-listed `grep`-based acceptance criteria for both tasks — pass (component exports,
  early-return gate, `download={`/no `target=`, solid-not-dashed border, no `outline: 'none'`,
  `aria-hidden`, `downloadReportAria`, zero literal hex colours, zero `:hover`, exactly 2
  `<DownloadReportCTA` call sites, exact import line, `normalizeLanguage` present /
  `startsWith('de')` absent, exactly 2 `flex: '1 1 auto', minWidth: 0` wrappers, `isComparing`
  count unchanged, `ComparisonColumn` scope contains zero `DownloadReportCTA`)
- Manual fail-closed smoke test: confirmed `app/public/data/reports/` does not exist yet in this
  tree (plan 12-10 hasn't landed), so `useReportAvailability`'s HEAD probe against a real static
  host will 404 and the control will render `null` — see Deviations for a caveat found while
  attempting to reproduce this locally via `vite preview`
- `cd app && npm run check:soil-palette` — **fails**, pre-existing and out of scope (see
  Deviations below, same condition already logged for plan 12-01)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - blocking] `node_modules` was not installed in this worktree**
- **Found during:** Task 1 verification (`npm run lint` reported `eslint` not recognized)
- **Fix:** ran `npm install` in `app/` to restore the existing pinned dependencies from
  `package-lock.json` (no new packages added, no version changes — a plain reinstall)
- **Files modified:** none tracked (`node_modules/` is gitignored)

**2. [Rule 1 - bug in own draft] Header comment for Task 1 accidentally contained the literal
word "dashed"**
- **Found during:** Task 1's own acceptance-criteria self-check (`grep -c "dashed"` must return 0)
- **Fix:** reworded the comment to explain the solid-vs-dashed border distinction without using
  that literal token
- **Files modified:** `app/src/components/DownloadReportCTA.jsx`
- **Commit:** folded into the Task 1 commit (`9b1a7e9`) since it was caught before that commit
  was made

### Scope-boundary items (not fixed, logged)

**1. [Scope boundary] `npm run check:soil-palette` fails on `havelland`** — identical,
pre-existing condition already logged for plan 12-01 (TODO-01 / quick-task `260804-acf`,
"pending human visual check"). `git diff --stat` between this plan's base commit and its final
commit confirms zero changes to `app/src/data/soil_legend.js` or any `app/public/data/geojson/*`
fixture. Logged as a recurrence in `deferred-items.md` rather than re-investigated.

**2. [Informational, not a defect] `vite preview`'s SPA history fallback masks 404s for missing
static assets under any path** — while smoke-testing the plan's fail-closed verification step
locally, a `HEAD` request to a genuinely-missing `data/reports/report-rheingau-en.pdf` returned
`200` with `index.html`'s body, not a real `404`, because Vite's built-in dev/preview server
serves the SPA fallback for any unmatched route regardless of file extension or `Accept` header.
Reproduced the identical behavior against an already-missing `data/charts/*.json` path, confirming
this is a pre-existing characteristic shared by `useChartData.js`'s own 404-as-null fetch pattern,
not something introduced by `useReportAvailability` or `DownloadReportCTA`. It does not affect
real static hosting (GitHub Pages / TYPO3), where only the SPA's own entry route is rewritten to
`index.html`, and a genuinely missing file under `data/reports/` returns a real `404`. No fix
applied — out of this plan's scope (`files_modified` does not include `vite.config.js`), and
correctness at the actual deployment target is unaffected. Not logged to `deferred-items.md`
since it is not a defect requiring future resolution, only a local-dev-testing caveat worth
recording for whoever runs 12-03's manual verification step again.

## Known Stubs

None. `DownloadReportCTA` is fully wired at both call sites and will render live, correct content
as soon as plan 12-10 commits the ten PDF report files — no data source is stubbed or mocked.

## Threat Flags

None beyond what the plan's own `<threat_model>` already registers (T-12-05, T-12-12, T-12-13,
T-12-14, T-12-SC) — this plan implements exactly those mitigations (slug/lang validation lives in
the already-built `useReportAvailability` hook; React's own attribute-escaping handles `ll.name`;
the `download` filename is derived from the same validated slug/lang pair as `href`) and
introduces no new network endpoints, auth paths, or schema changes.

## Self-Check: PASSED

- FOUND: app/src/components/DownloadReportCTA.jsx
- FOUND: app/src/pages/LLDetail.jsx (modified)
- FOUND: commit 9b1a7e9 (Task 1)
- FOUND: commit fa4994b (Task 2)
