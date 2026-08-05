---
phase: 12-export-a-pdf-of-the-content-for-a-given-living-lab
plan: 01
subsystem: app-i18n-and-hooks
tags: [i18n, react-hooks, pdf-report, foundations]
dependency-graph:
  requires: []
  provides:
    - app/src/i18n_resources.js (pure, node-importable `resources` export)
    - app/src/hooks/useReportAvailability.js (D-18 existence probe hook)
    - llDetail.downloadReport* i18n keys (EN/DE)
    - report.* i18n namespace (EN/DE, 11 keys)
  affects:
    - app/src/i18n.js (now imports resources instead of declaring them inline)
tech-stack:
  added: []
  patterns:
    - "Pure, side-effect-free ES modules importable by plain node (mirrors app/src/data/soil_legend.js)"
    - "HEAD-probe existence hook with module-level cache + in-flight de-duplication (mirrors app/src/hooks/useChartData.js)"
    - "Fail-closed boolean hooks with no error channel, optimistic pending state"
key-files:
  created:
    - app/src/i18n_resources.js
    - app/src/hooks/useReportAvailability.js
    - .planning/phases/12-export-a-pdf-of-the-content-for-a-given-living-lab/deferred-items.md
  modified:
    - app/src/i18n.js
decisions:
  - "useReportAvailability's internal state shape is {key, available} (not useChartData's {key, data, loading, error}) since this hook has no data payload and no error channel by design (UI-SPEC fail-closed contract)"
metrics:
  duration: "~45 minutes"
  completed: 2026-08-05
---

# Phase 12 Plan 01: App-side i18n and availability-probe foundations Summary

Extracted the app's full bilingual `resources` object into a new pure, dependency-free
`app/src/i18n_resources.js` module (importable by plain `node`, mirroring the
`app/src/data/soil_legend.js` convention) so `data-pipeline/`'s future token-export bridge
(plan 12-04) can read the web app's own EN/DE strings instead of duplicating them. Added the
five UI-SPEC-locked `llDetail.downloadReport*` copy strings and a new eleven-key `report.*`
namespace for the offline PDF's own headings, in both languages. Created
`useReportAvailability(slug, lang)`, a HEAD-probe existence-check hook that is optimistic while
unresolved, fails closed on 404/non-2xx/network error with no error channel, and refuses to
build a fetch URL from a slug outside `/^[a-z0-9-]+$/`.

## What Was Built

### Task 1 — `app/src/i18n_resources.js` extraction
Moved the ~400-line `resources` literal verbatim out of `app/src/i18n.js` into a new module
with zero imports (`export const resources = { en: {...}, de: {...} }`). `app/src/i18n.js` now
does `import { resources } from './i18n_resources.js'` and is otherwise byte-for-byte unchanged
in behaviour — `STORAGE_KEY`, `normalizeLanguage`, `getInitialLanguage`, and the
`i18n.use(initReactI18next).init({...})` call are untouched.

### Task 2 — Download-control and report-namespace i18n keys
Added to both `resources.en.translation.llDetail` and `resources.de.translation.llDetail`,
immediately after `compareCompactAction`: `downloadReportTitle`, `downloadReportBody`,
`downloadReportAction`, `downloadReportCompactAction`, `downloadReportAria` — copied verbatim
from `12-UI-SPEC.md`'s locked Copywriting Contract table (real umlauts preserved in DE, not
ASCII-transliterated, per the plan's explicit instruction).

Added a new top-level `report` namespace (11 keys: `documentTitle`, `subtitle`, `regions`,
`locatorCaption`, `contents`, `kpiHeading`, `mapHeading`, `chartHeading`, `generated`,
`basemapCredit`, `noData`) to both language blocks, sited immediately after the existing
`climate` namespace. These are the offline R/Typst report's own headings — nothing in the web
app renders them yet; plan 12-04's token-export bridge will consume them.

### Task 3 — `useReportAvailability` hook
New `app/src/hooks/useReportAvailability.js`, copying `useChartData.js`'s fetch mechanics
(module-level `cache`/`inflight` Maps, one `fetch` per URL shared across concurrent callers,
`cancelled` cleanup flag) with three deliberate differences:
- Uses `fetch(url, { method: 'HEAD' })` — existence-only signal, no multi-MB GET per page view.
- Resolves to a plain boolean, never throws: `r.ok === true` -> `true`; 404, any other non-2xx,
  or a rejected promise all resolve to `false`. No error channel at all (UI-SPEC's "fail closed,
  no visible error UI" contract).
- Returns `true` while the probe is unresolved (optimistic `checking` state) and `true` when the
  memoized `key` changes ahead of the effect resolving — never a loading sentinel.
- Returns `false` immediately, with no fetch issued, when `slug`/`lang` are falsy or `slug` fails
  the `/^[a-z0-9-]+$/` allow-list / `lang` isn't exactly `'en'`/`'de'` (T-12-05 mitigation — a
  router param or `?compare=` value can never escape `data/reports/` or smuggle a query string).

URL is built as `` `data/reports/report-${slug}-${lang}.pdf` `` — relative, no leading slash,
keeping the app working under `base: './'` sub-path hosting.

## Verification

- `cd app && npm run lint` — exits 0 (all 3 commits)
- `cd app && npm run build` — exits 0 (all 3 commits)
- Node smoke import for Task 1 (`m.resources.en.translation` / `.de.translation` shape check) —
  prints `OK`
- Node smoke import for Task 2 (all 5 `llDetail.downloadReport*` + 11 `report.*` keys, both
  languages) — prints `OK`
- All `grep`-based acceptance criteria in the plan (zero imports, key counts, regex presence,
  absence of `throw`, absence of leading-slash absolute paths) — all pass
- `cd app && npm run check:soil-palette` — **fails**, pre-existing and out of scope (see
  Deviations below)

## Deviations from Plan

### Auto-fixed Issues

None — Tasks 1-3 executed exactly as written; no bugs, missing functionality, or blocking issues
were found in the plan's own instructions.

### Scope-boundary item (not fixed, logged)

**1. [Scope boundary] `npm run check:soil-palette` fails on `havellandisches-luch`**
- **Found during:** Plan-level overall `<verification>` run (this command is listed as one of
  the four overall verification gates, not per-task)
- **Issue:** `legend minimum pairwise ΔE76 is 19.0, expected >= 20` for one Living Lab's soil
  legend
- **Root cause:** Pre-existing condition in `app/src/data/soil_legend.js`, last touched by an
  unrelated commit (`fbe9914`, "colour soil bar chart from the map palette") that predates this
  plan. `STATE.md` already tracks this exact issue as TODO-01 / quick-task `260804-acf`,
  explicitly flagged "pending human visual check" before this plan started.
- **Why not fixed:** No task in 12-01 reads or is scoped to touch `app/src/data/soil_legend.js`
  or `app/scripts/check_soil_palette.mjs` (`files_modified` for this plan is
  `app/src/i18n_resources.js`, `app/src/i18n.js`, `app/src/hooks/useReportAvailability.js`
  only). Per the executor's scope-boundary rule, pre-existing failures in unrelated files are
  logged, not fixed.
- **Logged to:** `.planning/phases/12-export-a-pdf-of-the-content-for-a-given-living-lab/deferred-items.md`
- **Recommended resolution:** Track under the existing TODO-01 / `260804-acf` follow-up, not
  Phase 12.

## Known Stubs

None. `useReportAvailability` is not yet wired to any UI component (that is a later plan in this
phase, per the wave sequencing in `12-CONTEXT.md`/UI-SPEC) — it is a complete, correct,
independently-verifiable hook, not a stub. `report.*` and `llDetail.downloadReport*` i18n keys
are unused by any component yet for the same reason (consumed starting with the plan that builds
`DownloadReportCTA` and plan 12-04's token-export bridge).

## Threat Flags

None. Task 3's `useReportAvailability` implements the exact mitigations the plan's own
`<threat_model>` assigns to it (T-12-05 slug/lang allow-list, T-12-06 relative-URL same-origin
constraint, T-12-07 cache + in-flight de-duplication + HEAD-not-GET). No new network endpoints,
auth paths, or schema changes were introduced outside that register.

## Self-Check: PASSED

- FOUND: app/src/i18n_resources.js
- FOUND: app/src/hooks/useReportAvailability.js
- FOUND: app/src/i18n.js (modified)
- FOUND: .planning/phases/12-export-a-pdf-of-the-content-for-a-given-living-lab/deferred-items.md
- FOUND: commit 74e227d (Task 1)
- FOUND: commit 59505af (Task 2)
- FOUND: commit e328c73 (Task 3)
