# Phase 12: Export a PDF of the content for a given Living Lab - Pattern Map

**Mapped:** 2026-08-04
**Files analyzed:** 12 (app-side: 3 modified/new; pipeline-side: 6 new + 2 modified; docs: 1)
**Analogs found:** 10 / 12

Note: this phase's R/Quarto/Typst content (`.qmd`, `_brand.yml`, `theme_llexplorer.R`) has **no
codebase analog** — it is genuinely new tooling (D-01/D-02/D-03/D-08/D-22). Those files are listed
under "No Analog Found" with RESEARCH.md's own Code Examples/Architecture Patterns sections as the
only available reference. Everything else in this phase (the `sync.py` plumbing, the `sources.yaml`
declaration shape, the `LLDetail.jsx` trigger control, the availability-check hook, the i18n keys,
and the pytest smoke tests) has a strong, direct in-repo analog.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `data-pipeline/sync.py` (`sync_reports()` addition) | service (sync/publish function) | batch / file-I/O | `sync_charts()` (`data-pipeline/sync.py:378-413`) | exact |
| `data-pipeline/sources/sources.yaml` (new `reports:`/pattern declaration) | config | declarative manifest | `output.chart_pattern` stanza (`landuse-croptypes`, lines 51-56) | role-match (adapted: no natural per-layer home, see note below) |
| `app/src/pages/LLDetail.jsx` (`DownloadReportCTA` component, new) | component | request-response (static file link) | `CompareCTA` (`LLDetail.jsx:1130-1192`) for structure/styling; `ContactManagerButton` (`app/src/components/ContactManagerButton.jsx`) for the conditional-render-null + `<a>`-download pattern | exact (composite of two analogs) |
| `app/src/pages/LLDetail.jsx` (2 call-site edits, compact ~552 and full ~726-728) | component (call site) | request-response | Same file, existing `CompareCTA` call sites | exact |
| `app/src/hooks/useReportAvailability.js` (new) | hook | request-response (fetch-with-404-as-null) | `useChartData.js` (`app/src/hooks/useChartData.js:1-70`) | exact |
| `app/src/i18n.js` (new `llDetail.downloadReport*` keys, EN block ~190-207 and DE block ~392-410) | config (i18n resource) | — | Existing `llDetail.compare*` / `llDetail.contactManager*` key pairs, same file | exact |
| `data-pipeline/tests/test_pipeline_outputs.py` (new report smoke tests) | test | batch / file-I/O verification | `test_chart_stanzas_declared`, `test_bar_chart_fixtures_exist_and_match_contract`, `test_chart_fixtures_published_to_app_public` (lines 723-936) | exact |
| `data-pipeline/R/render_reports.py` (new) | utility (manual build script) | batch / subprocess orchestration | No direct R/Quarto analog in-repo; closest *shape* analog is `data-pipeline/python/build_pmtiles.py` (a manual, `sync.py`-independent build script per D-04's own stated precedent) | role-match |
| `data-pipeline/R/report/template.qmd` (new) | template (Quarto document) | transform (data -> rendered PDF) | none | no analog |
| `data-pipeline/R/theme_llexplorer.R` (new) | utility (shared theme/palette module) | transform | `app/src/theme.js` (conceptual analog only — same *purpose*, not portable code) | no analog (cross-language) |
| `data-pipeline/R/report/_extensions/ll-explorer-typst/` (new, brand configs + Typst partials) | config/template | transform | none in-repo; external `iat-internal-typst` extension (RESEARCH.md Code Examples) is the only reference | no analog |
| `CLAUDE.md` (External CLI deps line extension, D-19) | config (docs) | — | Existing "External CLI deps: `pmtiles`, `rio`" line, same file | exact |

## Pattern Assignments

### `data-pipeline/sync.py` — `sync_reports()` (service, batch/file-I/O)

**Analog:** `sync_charts()`, `data-pipeline/sync.py:378-413`, plus its two helpers
`_pattern_to_glob()` (lines 15-26) and `_sync_matched_pattern()` (lines 320-346).

**Imports pattern** (top of file, lines 1-9):
```python
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from python._sources import get_layer, load_sources, repo_root, resolve
from python.generate_metadata import write_metadata
```
No new imports are needed for `sync_reports()` itself — it reuses `json`, `resolve`, `repo_root`,
and `_sync_matched_pattern` already imported/defined in this file.

**Core pattern — per-slug-and-lang existence check, then delegate to the shared glob copier**
(verbatim source, `sync.py:378-413`):
```python
def sync_charts() -> None:
    """Publish per-(layer, Living Lab) chart JSON files declared via output.chart_pattern
    (D-10). Like every other sync_* function, this never computes chart data -- it only
    copies already-produced files (D-11); the five compute_*_chart.py scripts are run by
    hand, never invoked from here.

    Unlike _sync_matched_pattern()'s pure-glob report (which can only say "found N of
    however-many"), D-15 requires naming each individually missing (layer, Living Lab)
    file. So this function first loops the known LL slugs (read from
    data/ll_boundaries.geojson -- sync.py cannot import the test-only conftest.py) and
    prints one `[chart] skipped - not yet built: ...` line per missing file, then
    delegates the actual copy to _sync_matched_pattern(pattern, tag="chart") so the copy
    path keeps inheriting _pattern_to_glob() and the repo-root-escape guard (D-10).
    """
    root = repo_root()
    boundaries_path = resolve("data/ll_boundaries.geojson")
    boundaries = json.loads(boundaries_path.read_text(encoding="utf-8"))
    ll_slugs = sorted(
        {feature["properties"]["ll_slug"] for feature in boundaries["features"]}
    )
    if not ll_slugs:
        raise RuntimeError(
            f"No ll_slug values found in {boundaries_path.relative_to(root)}"
        )

    sources = load_sources()
    for layer in sources["layers"]:
        output = layer.get("output", {})
        pattern = output.get("chart_pattern")
        if not pattern:
            continue
        for slug in ll_slugs:
            expected = resolve(pattern.format(slug=slug))
            if not expected.exists():
                print(f"[chart] skipped - not yet built: {expected.relative_to(root)}")
        _sync_matched_pattern(pattern, tag="chart")
```

**Adaptation required — the two-axis (slug × lang) extension:** `sync_reports()` needs to loop
`ll_slugs x ("en", "de")` instead of `ll_slugs` alone, and it has **no per-layer home** in
`sources.yaml` (reports span all 5 tabs in one document — RESEARCH.md's Open Question #2 flags
this explicitly, recommending a standalone module-level constant over forcing a `sources.yaml`
layer entry). Concrete shape (RESEARCH.md Pattern 4, already drafted against the real function):
```python
REPORT_PATTERN = "data/reports/report-{slug}-{lang}.pdf"  # D-20, D-05: no natural sources.yaml
                                                             # layer home; standalone constant
                                                             # mirrors sync_charts()'s pattern var

def sync_reports() -> None:
    root = repo_root()
    boundaries_path = resolve("data/ll_boundaries.geojson")
    boundaries = json.loads(boundaries_path.read_text(encoding="utf-8"))
    ll_slugs = sorted(
        {feature["properties"]["ll_slug"] for feature in boundaries["features"]}
    )
    for slug in ll_slugs:
        for lang in ("en", "de"):
            expected = resolve(REPORT_PATTERN.format(slug=slug, lang=lang))
            if not expected.exists():
                print(f"[report] skipped - not yet built: {expected.relative_to(root)}")
    _sync_matched_pattern(REPORT_PATTERN, tag="report")
```
`_pattern_to_glob()` (lines 15-26) already tolerates any number of `{...}` placeholders — it was
purpose-built for climate's 3-placeholder pattern — so the 2-placeholder report pattern glob-matches
with **zero changes** to that shared helper.

**Bracketed-tag logging convention (shared across every `sync_*` function):** `[report]` (not a
generic message) mirrors `[chart]` exactly per D-20 — see the `print(f"[chart] skipped ...")` line
above.

**Integration point — orchestration list**, `sync_to_app()` (lines 416-429):
```python
def sync_to_app() -> None:
    write_metadata()
    print("[sync] generated data/ll_metadata.json from data/ll_content.json")
    for rel_path in STATIC_DATA_FILES:
        source = resolve(rel_path)
        sync_file(source, resolve(f"app/public/{rel_path}"))
    sync_pmtiles()
    sync_pmtiles_per_ll()
    sync_vector_geojson()
    sync_charts()
    generate_landuse_legend()
    generate_land_cover_legend()
    generate_climate_legend()
    generate_layer_sources()
```
Add `sync_reports()` as a new call, sited next to `sync_charts()` (same file-copy category,
D-04's "never invoke the renderer, only copy" contract applies identically).

---

### `data-pipeline/sources/sources.yaml` — new report declaration (config)

**Analog:** the `chart:`/`output.chart_pattern` sibling-stanza shape inside a layer entry, e.g.
`landuse-croptypes` (lines 39-56):
```yaml
    build:
      script: python/build_pmtiles.py
      target_crs: "EPSG:3857"
      min_zoom: 6
      max_zoom: 12
      tile_size: 512
      resampling: nearest
    chart:
      # D-05: agriculture bar-chart compute script. D-11: sync.py only ever copies this
      # script's output, never invokes it -- this path is documentation for a human
      # running the script by hand.
      script: python/compute_agriculture_chart.py
    output:
      pmtiles: data/pmtiles/landuse-croptypes.pmtiles
      sync_to: app/public/data/pmtiles/landuse-croptypes.pmtiles
      # D-10: per-(layer, Living Lab) chart output pattern. Lives under output: (not
      # chart:) because every other *_pattern key in this file lives under output:.
      chart_pattern: "data/charts/landuse-croptypes-{slug}.json"
```

**Adaptation note (RESEARCH.md Pattern 4 / Open Question #2, explicitly flagged for planner
decision):** a report is not a per-layer artifact — it spans all 5 tabs in one document — so it
does not fit inside a single `layers:` entry's `chart:`/`output:` stanza shape the way every other
`*_pattern` key does. Two defensible options, either acceptable:
- **(a) Standalone constant** in `sync.py` (no `sources.yaml` change at all) — lower friction,
  matches `sync_reports()`'s self-contained nature. **Recommended** per RESEARCH.md.
- **(b) New top-level `reports:` stanza**, sibling to `layers:` in `sources.yaml`, e.g.:
  ```yaml
  reports:
    script: R/render_reports.py  # comment matching the chart: script comment's phrasing —
                                   # documentation only; sync.py never invokes this (D-04)
    output:
      report_pattern: "data/reports/report-{slug}-{lang}.pdf"
  ```
  If chosen, the smoke-test analog `test_chart_stanzas_declared()` (see Test section below) is the
  direct pattern for asserting this new stanza's shape.

---

### `app/src/hooks/useReportAvailability.js` (new hook, fetch-with-404-as-null)

**Analog:** `app/src/hooks/useChartData.js` (full file, 70 lines) — copy this pattern nearly
verbatim, swapping the chart-cache-key/URL shape for a report one.

**Full source** (analog, verbatim):
```javascript
import { useEffect, useState } from 'react'
import { LAYER_SOURCE_INDEX } from '../data/layer_sources.js'

const cache = new Map()
const inflight = new Map()

function fetchChart(url) {
  if (cache.has(url)) return Promise.resolve(cache.get(url))
  if (inflight.has(url)) return inflight.get(url)
  const p = fetch(url)
    .then((r) => {
      if (r.status === 404) return null
      if (!r.ok) throw new Error(`Failed to load ${url}: ${r.status}`)
      return r.json()
    })
    .then((data) => {
      cache.set(url, data)
      inflight.delete(url)
      return data
    })
    .catch((err) => {
      inflight.delete(url)
      throw err
    })
  inflight.set(url, p)
  return p
}

// Fetch the per-(layer, LL) chart JSON, cached forever per session (files are static). A 404
// resolves to data: null with no error - the pipeline's documented "not yet built" case - while
// any other failure (bad status, network error, JSON parse failure) surfaces as a real error.
export function useChartData(layer, slug) {
  const source = layer ? LAYER_SOURCE_INDEX.get(layer) : undefined
  const isEnabled = Boolean(layer) && Boolean(slug) && Boolean(source)
  const key = layer + '|' + slug
  const [state, setState] = useState({ key, data: null, loading: isEnabled, error: null })

  useEffect(() => {
    let cancelled = false
    if (!isEnabled)
      return () => {
        cancelled = true
      }
    const url = 'data/charts/' + source.id + '-' + slug + '.json'
    fetchChart(url)
      .then((data) => {
        if (cancelled) return
        setState({ key, data, loading: false, error: null })
      })
      .catch((error) => {
        if (cancelled) return
        setState({ key, data: null, loading: false, error })
      })
    return () => {
      cancelled = true
    }
    // key is a stable string derived from layer/slug; source/isEnabled are re-derived from it
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])

  if (!isEnabled) {
    return { data: null, loading: false, error: null }
  }

  if (state.key !== key) {
    return { data: null, loading: true, error: null }
  }

  return state
}
```

**Adaptation for the report use case — important divergence from the UI-SPEC's `checking` state:**
UI-SPEC.md's Interaction States table (lines 250-254) specifies `checking` renders **optimistically
as `available`** (not a loading/null state like `useChartData`'s `loading: true` branch) — this is
a deliberate deviation from the chart hook's own consumer behavior, only relevant to how
`DownloadReportCTA` *uses* the hook's return value, not to the hook's internal fetch/cache
mechanics (those should be copied as-is: session-level `Map` cache, in-flight de-dup, 404-as-null,
non-404-non-2xx-as-thrown-error). A HEAD request (instead of a full GET) is worth considering for
this hook specifically, since the consumer never needs the PDF bytes, only an existence signal —
but a plain `fetch(url)` + immediately aborting/ignoring the body (mirroring the chart hook exactly)
is also acceptable and lower-risk if HEAD support against the static host is unverified.

**URL construction convention to copy** (same file, line 44): `'data/charts/' + source.id + '-' +
slug + '.json'` — i.e. relative path (no leading `/`), consistent with the project's `base: './'`
sub-path-hosting constraint (CLAUDE.md). The report hook's URL should follow the identical
relative-path shape: `` `data/reports/report-${slug}-${lang}.pdf` ``.

---

### `app/src/pages/LLDetail.jsx` — `DownloadReportCTA` (component, request-response)

**Primary analog (structure/styling):** `CompareCTA`, `LLDetail.jsx:1130-1192` (full source above
in sync.py section's sibling context — reproduced here for the component-specific excerpt):
```jsx
function CompareCTA({ compact = false, options, onPick }) {
  const { t } = useTranslation()
  const [pickerOpen, setPickerOpen] = useState(false)
  const pickerRef = useDismissOnOutside(pickerOpen, () => setPickerOpen(false))
  const pickerId = useId()

  return (
    <div ref={pickerRef} style={{ position: 'relative' }}>
      <div
        style={{
          background: C.limePale,
          borderRadius: compact ? 12 : 14,
          padding: compact ? '14px 18px' : '16px 24px',
          border: `${compact ? 1.5 : 2}px dashed ${C.lime}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div>
          <div style={{ fontSize: compact ? 13 : 14, fontWeight: 700, color: C.green }}>
            {compact ? t('llDetail.compareCompactTitle') : t('llDetail.compareTitle')}
          </div>
          {compact ? null : (
            <div style={{ fontSize: 12, color: C.greenMid, marginTop: 2 }}>
              {t('llDetail.compareBody')}
            </div>
          )}
        </div>
        <button
          type="button"
          aria-haspopup="menu"
          aria-controls={pickerOpen ? pickerId : undefined}
          aria-expanded={pickerOpen}
          onClick={() => setPickerOpen((open) => !open)}
          style={{
            padding: compact ? '7px 16px' : '8px 20px',
            borderRadius: 20,
            background: C.orange,
            color: C.white,
            border: 'none',
            fontSize: compact ? 12 : 13,
            fontWeight: 700,
            cursor: 'pointer',
          }}
        >
          + {compact ? t('llDetail.compareCompactAction') : t('llDetail.compareAction')}
        </button>
      </div>
      {pickerOpen ? (
        <ComparePicker ... />
      ) : null}
    </div>
  )
}
```
Note per UI-SPEC.md: `DownloadReportCTA`'s **full** instance should mirror this card shape closely
(bordered card, title, body, pill button) but with a **solid** `C.lime` border (not dashed — UI-SPEC
Color section, "solid vs. dashed is the one intentional visual differentiator"). The **compact**
instance should render as a bare pill only (no outer card) — see secondary analog below.

**Secondary analog (conditional-render-null + `<a>`-download + aria pattern):**
`app/src/components/ContactManagerButton.jsx` (full file, 65 lines):
```jsx
import { useTranslation } from 'react-i18next'
import { C } from '../theme.js'

// mailto link to a Living Lab's regional network manager.
// Renders nothing when no manager email is authored in data/ll_content.json.
// `variant="inverted"` is for the dark teal header in the stacked layout.
export function ContactManagerButton({ ll, variant = 'light' }) {
  const { t } = useTranslation()
  const manager = ll.manager
  if (!manager) return null

  const label = t('llDetail.contactManager')
  const subject = t('llDetail.contactManagerSubject', { name: ll.name })
  const href = `mailto:${manager.email}?subject=${encodeURIComponent(subject)}`
  const inverted = variant === 'inverted'

  return (
    <div style={{ marginLeft: 'auto', display: 'flex', flexDirection: 'column',
                   alignItems: 'flex-end', gap: 4, flexShrink: 0 }}>
      <a
        href={href}
        aria-label={manager.name ? `${label} - ${manager.name}` : label}
        title={manager.name ? `${manager.name} <${manager.email}>` : manager.email}
        style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '8px 16px',
                  borderRadius: 20, background: C.orange, color: C.white, border: 'none',
                  fontSize: 12, fontWeight: 700, lineHeight: 1.2, textDecoration: 'none',
                  cursor: 'pointer', textAlign: 'right' }}
      >
        <span aria-hidden="true">✉</span>
        {label}
      </a>
      {manager.name ? (
        <div style={{ fontSize: 11, color: inverted ? 'rgba(255,255,255,0.7)' : C.greenMid,
                       textAlign: 'right' }}>
          {manager.name}
        </div>
      ) : null}
    </div>
  )
}
```
This is the **exact** template for: (1) the top-of-function `if (!X) return null` early-exit that
implements D-18's "whole section omitted, not disabled" contract, (2) building an `aria-label` via
`t('llDetail.xAria', { name: ll.name })` interpolation, (3) the `<span aria-hidden="true">GLYPH
</span>{label}` pattern for the icon+text button body (swap `✉` for `⬇` per UI-SPEC.md), (4) plain
`<a href=...>` with inline styles reading `C.orange`/`C.white` for the pill button, no click
handler, no custom hover — matches UI-SPEC's Interaction States exactly ("No custom click feedback
... matches `ContactManagerButton`'s plain `mailto:` anchor").

**Composite shape to build** (combining both analogs, per UI-SPEC.md's exact prop contract and copy):
```jsx
function DownloadReportCTA({ compact = false, ll, lang }) {
  const { t } = useTranslation()
  const available = useReportAvailability(ll.slug, lang)  // true | false, optimistic-true while checking
  if (!available) return null

  const href = `data/reports/report-${ll.slug}-${lang}.pdf`
  const filename = `report-${ll.slug}-${lang}.pdf`
  const label = compact
    ? t('llDetail.downloadReportCompactAction')
    : t('llDetail.downloadReportAction')
  const ariaLabel = t('llDetail.downloadReportAria', { name: ll.name })

  // compact: bare pill, no card (UI-SPEC "Deliberate content-density difference")
  // full: bordered card (C.lime, SOLID not dashed) + title + body + pill, mirroring CompareCTA's
  //       full DOM shape 1:1 per D-15
  return ( /* see UI-SPEC.md Layout & Placement + Color sections for exact JSX shape */ )
}
```

**Call-site edits** — exact before/after already drafted in RESEARCH.md Pattern 5 and UI-SPEC.md
Layout & Placement section. Compact instance (`LLDetail.jsx:552`):
```jsx
// before
<CompareCTA compact options={compareOptions} onPick={onPickCompare} />
// after
<div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
  <div style={{ flex: '1 1 auto', minWidth: 0 }}>
    <CompareCTA compact options={compareOptions} onPick={onPickCompare} />
  </div>
  <DownloadReportCTA compact ll={ll} lang={lang} />
</div>
```
Full instance (`LLDetail.jsx:726-728`):
```jsx
// before
<div style={{ padding: '16px 32px 32px' }}>
  <CompareCTA options={compareOptions} onPick={onPickCompare} />
</div>
// after
<div style={{ padding: '16px 32px 32px', display: 'flex', gap: 16, alignItems: 'stretch' }}>
  <div style={{ flex: '1 1 auto', minWidth: 0 }}>
    <CompareCTA options={compareOptions} onPick={onPickCompare} />
  </div>
  <div style={{ flexShrink: 0 }}>
    <DownloadReportCTA ll={ll} lang={lang} />
  </div>
</div>
```
`lang` should be sourced the same way the rest of `LLDetail.jsx` derives the active language (check
existing `normalizeLanguage(i18n.language)` usage at each call site's enclosing component — both
`CompareCTA` call sites already sit inside components that call `useTranslation()`, so `i18n.language`
is available without new plumbing).

**D-17 (hide during comparison) — no new conditional needed:** confirmed by direct read that
`ComparisonColumn` (the component mounted when `isComparing` is true) never imports/renders
`CompareCTA` at all — placing `DownloadReportCTA` as a sibling of `CompareCTA` at both call sites
means it inherits the same hide-during-comparison behavior automatically, with zero extra `if`
logic required.

---

### `app/src/i18n.js` — new `llDetail.downloadReport*` keys (config)

**Analog:** existing `llDetail.compare*` / `llDetail.contactManager*` key pairs, same file, EN
block (lines ~190-207) and DE block (~392-410):
```javascript
// EN, lines 190-207 (excerpt)
llDetail: {
  ...
  compareTitle: 'Compare with another Living Lab',
  compareCompactTitle: 'Want to compare with another Living Lab?',
  compareBody: 'Secondary feature - select any two LLs to view side-by-side metrics',
  compareAction: 'Compare',
  compareCompactAction: 'Add for comparison',
  ...
},
```
```javascript
// DE, lines 392-410 (excerpt)
llDetail: {
  ...
  compareTitle: 'Mit einem anderen Living Lab vergleichen',
  compareCompactTitle: 'Mit einem anderen Living Lab vergleichen?',
  compareBody: 'Sekundaere Funktion - zwei Living Labs fuer einen Seitenvergleich auswaehlen',
  compareAction: 'Vergleichen',
  compareCompactAction: 'Zum Vergleich hinzufuegen',
  ...
},
```
New keys to add, sibling to these, per UI-SPEC.md's locked Copywriting Contract table (exact EN/DE
strings already specified there — copy verbatim, do not re-translate):
```javascript
downloadReportTitle: 'Download the full report',              // DE: 'Gesamten Bericht herunterladen'
downloadReportBody: 'Every KPI, map and chart for this Living Lab in one PDF document',
                                                                 // DE: 'Alle Kennzahlen, Karten und Diagramme für dieses Living Lab in einem PDF-Dokument'
downloadReportAction: 'Download PDF',                          // DE: 'PDF herunterladen'
downloadReportCompactAction: 'PDF',                             // DE: 'PDF'
downloadReportAria: 'Download the {{name}} PDF report',        // DE: 'PDF-Bericht für {{name}} herunterladen'
```
Note the project's existing ASCII-transliteration convention for German strings elsewhere in this
file (`Sekundaere`, `fuer`, `auswaehlen` — no umlauts) is **inconsistent** with UI-SPEC.md's locked
DE copy, which uses real umlauts (`für`, `herunterladen`). Follow UI-SPEC.md's locked strings
exactly as written (it is the authoritative, checker-approved copy contract for this phase) rather
than retrofitting ASCII transliteration — this is a pre-existing file inconsistency, not something
this phase should "fix" by degrading the new, correctly-accented strings.

---

### `data-pipeline/tests/test_pipeline_outputs.py` — new PDF smoke tests (test)

**Analog 1 — file-existence + magic-bytes shape**, adapt from `test_pmtiles_fixture_exists_and_is_nonzero`
(lines 34-37) and `test_land_cover_pmtiles_fixtures_exist_and_are_nonzero` (lines 40-50):
```python
def test_land_cover_pmtiles_fixtures_exist_and_are_nonzero() -> None:
    """
    Phase 06: mirrors test_pmtiles_fixture_exists_and_is_nonzero for the per-LL
    io-lulc-landcover raster, turning the five committed land-cover-{slug}.pmtiles
    files into a permanent contract rather than a one-off manual observation.
    """
    pmtiles_dir = repo_root() / "app" / "public" / "data" / "pmtiles"
    for slug in LL_SLUGS:
        pmtiles_path = pmtiles_dir / f"land-cover-{slug}.pmtiles"
        assert pmtiles_path.exists(), f"Missing land cover PMTiles fixture: {pmtiles_path}"
        assert pmtiles_path.stat().st_size > 0, f"Land cover PMTiles fixture is empty: {pmtiles_path}"
```

**Analog 2 — declared-contract lock**, `test_chart_stanzas_declared()` (lines 723-763, excerpted):
```python
def test_chart_stanzas_declared() -> None:
    """
    Plan 09-06: locks the five chart.script / output.chart_pattern declarations plan
    09-02 added to sources.yaml, transcribed from that plan's own interface table.
    ...
    """
    expectations = {
        "landuse-croptypes": (
            "python/compute_agriculture_chart.py",
            "data/charts/landuse-croptypes-{slug}.json",
        ),
        ...
    }
    assert set(expectations) == set(CHART_LAYER_IDS)

    for layer_id, (script, pattern) in expectations.items():
        layer = get_layer(layer_id)
        assert layer["chart"]["script"] == script, layer_id
        assert layer["output"]["chart_pattern"] == pattern, layer_id
```

**Analog 3 — publish-parity lock (source vs. app/public byte-identical copy)**,
`test_chart_fixtures_published_to_app_public()` (lines 913-936, verbatim):
```python
def test_chart_fixtures_published_to_app_public() -> None:
    """
    Plan 09-06: locks the sync_charts() publish step -- every committed data/charts/
    source has a byte-identical published copy under app/public/data/charts/, and the
    published directory holds exactly the 25 files this contract defines (no orphans
    left behind by a renamed pattern).
    """
    published_dir = repo_root() / "app" / "public" / "data" / "charts"

    for layer_id in CHART_LAYER_IDS:
        pattern = get_layer(layer_id)["output"]["chart_pattern"]
        for slug in LL_SLUGS:
            source_path = repo_root() / pattern.format(slug=slug)
            published_path = published_dir / source_path.name
            assert published_path.exists(), f"Missing published chart fixture: {published_path}"
            assert published_path.read_bytes() == source_path.read_bytes(), (
                f"{published_path.name}: published copy is not byte-identical to {source_path}"
            )

    published_files = sorted(published_dir.glob("*.json"))
    assert len(published_files) == 25, (
        f"Expected exactly 25 published chart files, got {len(published_files)}: "
        f"{[p.name for p in published_files]}"
    )
```

**Adaptation for D-21 (10 committed reports, well-formed PDF, run from clean state)** — combine all
three analog shapes into report-specific tests:
```python
REPORT_LANGS = ("en", "de")

def test_report_fixtures_exist_and_are_well_formed_pdfs() -> None:
    """D-21: 5 LLs x 2 langs = 10 committed report files; each must exist under
    data/reports/ and start with the %PDF- magic bytes. No Quarto invocation --
    reads already-committed files only, matching D-04's manual-render contract."""
    reports_dir = repo_root() / "data" / "reports"
    for slug in LL_SLUGS:
        for lang in REPORT_LANGS:
            path = reports_dir / f"report-{slug}-{lang}.pdf"
            assert path.exists(), f"Missing report fixture: {path}"
            with path.open("rb") as handle:
                header = handle.read(5)
            assert header == b"%PDF-", f"{path.name}: not a well-formed PDF (bad magic bytes)"


def test_report_fixtures_published_to_app_public() -> None:
    """Mirrors test_chart_fixtures_published_to_app_public() for sync_reports()'s
    publish step -- byte-identical copy under app/public/data/reports/, exactly 10 files."""
    published_dir = repo_root() / "app" / "public" / "data" / "reports"
    for slug in LL_SLUGS:
        for lang in REPORT_LANGS:
            source_path = repo_root() / "data" / "reports" / f"report-{slug}-{lang}.pdf"
            published_path = published_dir / source_path.name
            assert published_path.exists(), f"Missing published report fixture: {published_path}"
            assert published_path.read_bytes() == source_path.read_bytes(), (
                f"{published_path.name}: published copy is not byte-identical to {source_path}"
            )
    published_files = sorted(published_dir.glob("*.pdf"))
    assert len(published_files) == 10, (
        f"Expected exactly 10 published report files, got {len(published_files)}: "
        f"{[p.name for p in published_files]}"
    )
```
RESEARCH.md's Pitfall 3 also recommends adding an explicit file-size upper-bound assertion to catch
oversized PDFs (e.g. `assert path.stat().st_size < 15 * 1024 * 1024`) — flagged for planner, not
locked by any CONTEXT.md decision, so treat the exact threshold as an open implementation choice.

`LL_SLUGS` import — reuse directly, no changes needed:
```python
from conftest import LL_SLUGS, repo_root
```
(already the existing import at the top of this file, line 11).

---

## Shared Patterns

### Bracketed single-word logging tag convention
**Source:** every `sync_*` function in `data-pipeline/sync.py` (`[sync]`, `[chart]`, `[skip]`,
`[warn]`)
**Apply to:** `sync_reports()` — use `[report]` exactly, both for the "skipped - not yet built" line
and by inheritance for `_sync_matched_pattern(..., tag="report")`'s own `[report] N/M files matched`
summary line.
```python
print(f"[chart] skipped - not yet built: {expected.relative_to(root)}")
```

### Fetch-with-404-as-null hook pattern
**Source:** `app/src/hooks/useChartData.js` (full file)
**Apply to:** `app/src/hooks/useReportAvailability.js` — session `Map` cache + in-flight dedup +
404-resolves-to-null + any-other-non-2xx-throws.

### Conditional-render-null component pattern (D-18's "whole section omitted, not disabled")
**Source:** `app/src/components/ContactManagerButton.jsx:10` (`if (!manager) return null`)
**Apply to:** `DownloadReportCTA` — `if (!available) return null` as the very first statement after
hook calls, before any JSX is constructed.

### `t('namespace.key', { interpolatedVar })` aria-label pattern
**Source:** `ContactManagerButton.jsx:12-13` (`t('llDetail.contactManager')`,
`t('llDetail.contactManagerSubject', { name: ll.name })`)
**Apply to:** `DownloadReportCTA`'s `aria-label`/`title` via `t('llDetail.downloadReportAria', {
name: ll.name })` exactly as UI-SPEC.md locks it.

### Relative (sub-path-safe) static asset URL construction
**Source:** `useChartData.js:44` — `'data/charts/' + source.id + '-' + slug + '.json'` (no leading
slash, satisfies `base: './'` in `vite.config.js` per CLAUDE.md's static-hosting constraint)
**Apply to:** both the `useReportAvailability` hook's fetch URL and `DownloadReportCTA`'s anchor
`href` — always `` `data/reports/report-${slug}-${lang}.pdf` ``, never a leading-`/` absolute path.

### "Reuse what the project owns" brand-color sourcing
**Source:** `app/src/theme.js`'s `C` token object (full file, 56 lines) — per-LL `color`/
`colorDark`/`outlineColor` live in `app/public/data/ll_metadata.json`, not `theme.js` itself, but
`theme.js` is the canonical *app-wide* palette (orange/teal/green/lime families) D-07 requires the
Typst report to reuse conceptually.
**Apply to:** `data-pipeline/R/theme_llexplorer.R` and the 5 per-LL `_brand.yml` files — R has no
mechanism to *import* a `.js` file, so this is a conceptual/value-level analog only (copy the hex
values, not the code) — flagged under "No Analog Found" below for the R-side files themselves.

### Manual, `sync.py`-independent build script precedent (D-04)
**Source:** every existing `data-pipeline/python/build_*.py` script (e.g. `build_pmtiles.py`) is
run by hand per `CLAUDE.md`'s own Development Quick Start section (`python
python/build_pmtiles.py --layer landuse-croptypes`) — `sync.py` never imports or calls these.
**Apply to:** `data-pipeline/R/render_reports.py` — same "developer runs this by hand, `sync.py`
only copies its output" contract, now crossing a language boundary (Python subprocess shelling out
to the external `quarto` CLI) but the *responsibility* split is identical.

## No Analog Found

Files with no close match in the codebase (planner should rely on RESEARCH.md's own Code Examples /
Architecture Patterns / Common Pitfalls sections instead — RESEARCH.md is HIGH confidence for the
Quarto/R mechanics since they were live-verified on this machine):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `data-pipeline/R/report/template.qmd` | template (Quarto doc) | transform | Greenfield capability — no prior Quarto/R/Typst document exists anywhere in this repo (D-01/D-02/D-03 activate a previously-stubbed, empty `R/` directory). See RESEARCH.md's "Minimal working `.qmd` -> Typst PDF render" and "One parameterized `.qmd`" Code Examples/Patterns for the only available concrete reference (live-verified on this machine). |
| `data-pipeline/R/theme_llexplorer.R` | utility (shared theme module) | transform | No R code exists in this repo at all prior to this phase; `app/src/theme.js` is a same-purpose but cross-language non-code analog (hex values only, see Shared Patterns above) |
| `data-pipeline/R/report/_extensions/ll-explorer-typst/` (`_extension.yml`, `_brand.yml`, `brands/*.yml`, `typst-template.typ`, `typst-show.typ`) | config/template | transform | No Typst/Quarto-extension content exists in-repo; RESEARCH.md's fetched raw `_extension.yml` from the external `iat-internal-typst` repo (Code Examples section) is the only available concrete reference, and even that is CITED/MEDIUM confidence per RESEARCH.md's own Metadata section (fetched via WebFetch summarization for `_brand.yml`/`typst-template.typ` internals — recommend cloning the repo during execution to re-confirm exact key names) |
| `data-pipeline/R/renv.lock` | config (dependency pin file) | — | Auto-generated by `renv::snapshot()`, not hand-authored; no analog needed, `requirements.txt` is the conceptual (not structural) Python-ecosystem parallel per D-19 |
| `data-pipeline/R/render_reports.py` | utility (manual build driver) | batch/subprocess | Partial analog only (`build_pmtiles.py`'s manual-script *responsibility* shape, see Shared Patterns) — no existing script in this repo shells out to an external CLI the way this one must to `quarto render`; closest *mechanics* precedent is `python/_sources.py::find_rio_bin()`'s `shutil.which()`-based external-binary discovery pattern, worth reading directly during planning (not excerpted here — RESEARCH.md Pitfall 1 already describes the exact PATH/`R_HOME` probing this script should replicate) |

## Metadata

**Analog search scope:** `data-pipeline/sync.py` (full file), `data-pipeline/sources/sources.yaml`
(header + `landuse-croptypes` stanza), `app/src/pages/LLDetail.jsx` (full file structure via grep +
targeted reads of lines 480-560, 690-730, 1130-1230), `app/src/hooks/*.js` (all 3 hooks located,
`useChartData.js` read in full), `app/src/i18n.js` (structure + `llDetail` namespace grep),
`app/src/components/ContactManagerButton.jsx` (full file), `app/src/theme.js` (full file),
`data-pipeline/tests/test_pipeline_outputs.py` (full-file grep + targeted reads of lines 1-52 and
700-936), `data-pipeline/tests/conftest.py` (full file).
**Files scanned:** 12 read directly (7 full-file reads, 5 targeted range reads); `data-pipeline/R/`
confirmed present but empty (stub, consistent with CONTEXT.md D-03's framing).
**Pattern extraction date:** 2026-08-04
