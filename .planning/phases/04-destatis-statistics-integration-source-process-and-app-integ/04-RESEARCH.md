# Phase 4: Destatis Statistics Integration - Research

**Researched:** 2026-07-24
**Domain:** Destatis GENESIS-Online REST API (statistics fetch) + Python data pipeline + static-file app integration
**Confidence:** MEDIUM (API request structure is HIGH confidence from primary sources; regional-key/table-availability details are MEDIUM/LOW and need live-API verification once auth is fixed)

## Summary

Phase 4 resumes previously paused work. Three files already exist and are the starting point, not a
green field: `data-pipeline/python/fetch_destatis.py` (fetch/aggregate/export logic, currently
broken), `data/destatis_variables_catalogue.csv` (71-row candidate indicator catalogue with EN/DE
labels and GENESIS table IDs, not yet expert-reviewed), and the already-wired-but-all-null outputs
`data/destatis_nuts3.json` / `data/destatis_ll.json` / `data/destatis_nuts3_export.csv` /
`data/destatis_variables.csv`. All fetched values are currently `null` because every API call failed.

The root cause, per Destatis support (2026-07) and confirmed against the **official GENESIS POST-migration
guide** (`20250505_python_post_logincheck_tablefile_cubefile.pdf`, last edited 2026-06), is that
`fetch_destatis.py` sends `username`/`password` as **body** parameters mixed in with `data/tablefile`'s
other params. Since GET support was permanently switched off on **30 June 2025**, the API now requires
POST with `Content-Type: application/x-www-form-urlencoded`, and **credentials must be the `username`
and `password` fields of the HTTP header dict**, not the request body. The **base URL has migrated** from
`www-genesis.destatis.de` to `https://genesis.destatis.de/genesisWS/rest/2020/` — the code comment in
`fetch_destatis.py` documents this migration as a future date but that date (28 May 2026) has already
passed; the new host is confirmed live and current as of the official example code dated June 2026.

A second, more consequential unknown surfaced during research: the phase brief's assumption that GENESIS
result code 104 signals an **auth** failure is incorrect per the official documentation — **code 104 means
"no objects matched the given selection criteria"** (an Information-type response, not an auth Error).
Auth failures use a different code path (documented but not enumerated with a specific number in the
excerpts reviewed; must be observed empirically once real credentials are wired in). This matters for
building correct retry/error-handling logic in the fixed fetcher.

A third open risk, not previously flagged: the existing script filters rows by matching `ALL_NUTS3` alpha
codes (e.g. `"DE409"`) directly against a CSV column it assumes is named `Kreiskennziffer`. Official GENESIS
docs show that regional filtering is done via `classifyingvariable`/`classifyingkey` pairs referencing the
**"regionalkey"** classification, populated with the **Amtlicher Gemeindeschlüssel (AGS)** — a 5-digit
numeric Kreis code, not the alpha NUTS3 code format used throughout this project's `LL_NUTS3` mapping. This
must be verified against a real API response before trusting any values; an AGS↔NUTS3 crosswalk may be
required.

**Primary recommendation:** Fix the auth/request-structure bug first in isolation (small script, 1-2 tables,
verify against `helloworld/logincheck`), verify column-naming/regional-key assumptions against one real
response, only then re-run the full 34-table fetch across all indicators. Keep the existing
aggregate/CSV-export architecture — it is sound and does not need to be rebuilt, only the HTTP layer needs
to change. Land the app-facing writes through `generate_metadata.py`'s existing computed/authored merge
so `data/ll_content.json` is never touched by pipeline code, per CLAUDE.md.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| GENESIS API auth + HTTP fetch | Data pipeline (Python, `fetch_destatis.py`) | — | External API credentials must never reach the browser; fetch happens at build time only |
| Per-NUTS3 record assembly + per-LL aggregation | Data pipeline (Python) | — | Pure data transform, no UI concerns; existing `build_nuts3_records`/`aggregate_ll` already do this |
| Expert-review CSV export | Data pipeline (Python) | — | Output for human decision-making (variable selection), not consumed by the app |
| `data/destatis_nuts3.json`, `data/destatis_ll.json` | Data pipeline output (git-committed) | — | File-on-disk contract; app never calls Destatis directly |
| Merge of computed Destatis values into `ll_metadata.json` | Data pipeline (`generate_metadata.py`) | — | Must respect CONTENT-02: authored `ll_content.json` fields win on conflict; computed fields (Destatis) are the "base" layer |
| KPI/production/socio rendering | Browser / Client (React) | — | `KPIStrip`, `LLDetail`'s `TextBlock`/production/socio sections read only from `ll_metadata.json`, fetched once via `useLLMetadata` |
| Chart-style distribution rendering (if selected indicators become bar charts) | Browser / Client (React) | CDN/Static (`app/public/data/charts/`) | Phase 3's chart contract (`CHARTS-01/02`) exists on paper but `BarChart.jsx` still reads a hardcoded `chart_data.js`; Destatis charts would need real wiring, out of Phase 3.1/3 scope until decided |

## Project Constraints (from CLAUDE.md)

- **Never write `data/ll_content.json` from any pipeline script** — it is human-owned. Any Destatis
  values that reach the app must flow through the *computed* side of `generate_metadata.py`'s merge, not
  by editing `ll_content.json`.
- **`json.dumps(..., sort_keys=True)`** everywhere in `sync.py` to avoid noisy git diffs. `fetch_destatis.py`
  already does this for `destatis_nuts3.json`/`destatis_ll.json`; any new sync-path code must match.
- Static-only hosting: must work at any sub-path (`base: './'`). No new server-side code; Destatis data must
  land as a static JSON file the SPA fetches, exactly like `ll_metadata.json`.
- Python 3.12 required on Windows for geospatial wheel compatibility — `fetch_destatis.py` has no geospatial
  dependency, so this constraint is not directly load-bearing for Phase 4, but pipeline scripts should stay
  runnable in the same `.venv`.
- No TypeScript, no CSS frameworks, no SSR — any new frontend components (KPI/production/socio consumers)
  follow the existing inline-style-with-theme pattern (`C` theme object), matching `KPIStrip.jsx`/`BarChart.jsx`.
- Pipeline–app contract is **files on disk only** — no runtime coupling between Python and React. Destatis
  data must never be fetched client-side from the GENESIS API (would leak credentials and violate this rule
  anyway, since GENESIS requires authenticated POST).

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `requests` | >=2.31 (currently installed: 2.32.5; latest: 2.34.2) [VERIFIED: pip index versions] | HTTP client for GENESIS POST calls | Already the project's sole HTTP client (`fetch_nuts.py`, `_sources.py` use it); no reason to add a second one |
| `python-dotenv` | >=1.0 (currently installed: 1.2.1; latest: 1.2.2) [VERIFIED: pip index versions] | Loads `DESTATIS_USERNAME`/`DESTATIS_API_TOKEN` from `.env` | Already used by `fetch_destatis.py`; `.env.example` already documents the two variables |

No new external packages are required for Phase 4. Both dependencies above are already declared in
`data-pipeline/requirements.txt` and already installed in `.venv`. **Package Legitimacy Audit is not
applicable this phase** — no new packages are being introduced.

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `csv` (stdlib) | 3.12 | Parsing GENESIS `format=csv`/`ffcsv` responses | Already used; no change needed |
| `pytest` | >=7.0 | Smoke tests for pipeline outputs | Extend `data-pipeline/tests/test_pipeline_outputs.py` with Destatis fixture assertions (file exists, non-null values, correct NUTS3 key set) — mirrors the BÜK pattern already in that file |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Hand-rolled `requests.post` calls (current approach) | `genesispy` (github.com/KonradUdoHannes/genesispy) or `restatis` (R, not usable — project is Python) | [ASSUMED] Both are thin community wrappers with unclear maintenance/currency against the June 2026 POST-only spec; the official Destatis-published `20250505_python_post_logincheck_tablefile_cubefile.pdf` example is authoritative and small enough to adapt directly. Recommend continuing hand-rolled requests using that example as the reference implementation rather than adding a third-party dependency of unverified currency. |
| `format=csv` (current, multi-line-preamble wide format) | `format=ffcsv` (flat, one-row-per-value, officially recommended for pandas) | ffcsv avoids the current script's fragile `header_idx` heuristic (`next(i for i, ln in enumerate(lines) if ln.startswith('"') and ";" in ln)`) but requires a different parsing shape (long/tidy rather than wide-with-code-column) and gzip unwrapping if `compress=true` is set. Worth considering as a robustness improvement but not required to fix the immediate bug — [ASSUMED] recommendation, not verified against this project's specific table shapes. |

**Installation:** No installation changes required.

## Package Legitimacy Audit

Not applicable — this phase introduces no new external packages. `requests` and `python-dotenv` are
existing, already-vetted, already-installed dependencies used elsewhere in the pipeline (`fetch_nuts.py`,
`_sources.py`).

## Architecture Patterns

### System Architecture Diagram

```
[Destatis GENESIS-Online REST API]
   https://genesis.destatis.de/genesisWS/rest/2020/
        |
        | POST, Content-Type: application/x-www-form-urlencoded
        | headers: { username: <token-or-user>, password: <""-or-password> }
        | body:    { name: <table-id>, startyear, endyear, format, language, ... }
        v
[fetch_destatis.py]  --caches raw CSV-->  [data/destatis_raw/*.csv]
        |
        | build_nuts3_records() -- per-Kreis lookup by regional key
        v
[data/destatis_nuts3.json]  (per-NUTS3, sort_keys=True)
        |
        | aggregate_ll() -- sum/mean per LL depending on field semantics
        v
[data/destatis_ll.json]  (per-LL, sort_keys=True)
        |
        | _write_expert_csvs() -- side channel, NOT consumed by app
        v
[data/destatis_nuts3_export.csv, data/destatis_variables.csv]  (human expert review only)


--- separately, once indicators are expert-approved ---

[data/destatis_ll.json] + [data/ll_content.json (human-authored, NEVER written by pipeline)]
        |
        v
[generate_metadata.py: build_metadata()]
    _build_computed_record(slug, authored)  <-- EXTEND HERE to inject Destatis kpi/production/socio fields
        |
        | _deep_merge(computed, authored) -- authored wins on key conflict (CONTENT-02)
        v
[data/ll_metadata.json]
        |
        | sync.py: sync_to_app() copies to app/public/data/ll_metadata.json
        v
[app/src/hooks/useLLMetadata.js] --fetch('./data/ll_metadata.json')--> [App.jsx bySlug]
        |
        v
[LLDetail.jsx] --ll object--> [KPIStrip.jsx (area/farms/tempRange/soil)]
                           --> [production/socio TextBlock consumers, if wired]
```

### Recommended Project Structure

No new directories needed. Changes are localized to:

```
data-pipeline/
├── python/
│   ├── fetch_destatis.py       # fix auth/header bug here (Wave 1)
│   └── generate_metadata.py    # extend _build_computed_record() to merge Destatis values (Wave 3)
├── sources/sources.yaml         # optionally: add a non-build-script `stat` entry documenting Destatis
│                                 provenance for the app's info panel (mirrors layer_sources.js pattern)
├── tests/test_pipeline_outputs.py  # add Destatis output assertions (Wave 2)
data/
├── destatis_raw/                # existing cache dir, unchanged
├── destatis_nuts3.json          # existing output, will finally get non-null values
├── destatis_ll.json             # existing output, will finally get non-null values
├── destatis_nuts3_export.csv    # existing expert-review artifact
├── destatis_variables.csv       # existing expert-review artifact
└── destatis_variables_catalogue.csv  # existing candidate catalogue (needs table-ID verification pass)
```

### Pattern 1: Header-based auth for GENESIS POST requests

**What:** Per the official Destatis-published example (`20250505_python_post_logincheck_tablefile_cubefile.pdf`,
last edited June 2026), credentials go in the `headers` dict alongside `Content-Type`; the `data` dict
carries only the endpoint-specific parameters.

**When to use:** Every GENESIS-Online REST call in `fetch_destatis.py`.

**Example (official Destatis pattern, adapted):**
```python
# Source: https://genesis.destatis.de/datenbank/online/docs/20250505_python_post_logincheck_tablefile_cubefile.pdf
BASE_URL = "https://genesis.destatis.de/genesisWS/rest/2020/"

headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "username": TOKEN,   # API token recommended; put in "username" field
    "password": "",      # empty when using a token
}

response = requests.post(
    BASE_URL + "data/tablefile",
    headers=headers,
    data={
        "name": table_id,
        "startyear": startyear,
        "endyear": endyear,
        "compress": "true",
        "format": "ffcsv",
        "language": "de",
    },
)
```

**Note on token vs username/password:** a personal **API token** (shown in the GENESIS web UI under
"Webservice-Schnittstelle (API)" after login) can be used as the `username` header value with an empty
`password`, for all read-only calls. Token auth **cannot** be used for `job=true` batch queue requests or
`profile/*` write endpoints — those require the real `username`/`password` pair in headers. [CITED:
GENESIS-Anwenderdokumentation Webservice/API v5.1, section 2.1.3]. The existing `.env.example` already
anticipates this with `DESTATIS_USERNAME`/`DESTATIS_API_TOKEN` — recommend using the token as `username`
header value (simpler, no password needed) and reserving real username/password only if a table turns out
to require `job=true` (>40,000 values).

### Pattern 2: Verify auth before bulk fetch

**What:** Call `helloworld/logincheck` first; a successful response confirms credentials and host are
correct before spending a fetch cycle on all 34 tables.

**Example:**
```python
# Source: https://genesis.destatis.de/datenbank/online/docs/20250505_python_post_logincheck_tablefile_cubefile.pdf
hello = requests.post(BASE_URL + "helloworld/logincheck", headers=headers, data={"language": "de"})
# success: {"Status":{"Code":0,"Content":"Sie wurden erfolgreich an- und abgemeldet! ..."}}
```

### Pattern 3: Table/cube discovery before trusting the catalogue CSV

**What:** `data/destatis_variables_catalogue.csv` lists 34+ GENESIS table IDs (e.g. `33111BJ001`,
`41120BJ001`) that were selected from training-data knowledge, not verified against the live API. Before
building the full fetch loop, verify each table ID actually exists and returns the expected regional depth
using `catalogue/tables` (search by code) or by directly probing `data/tablefile`/`metadata/table` and
checking for a `Code: 0` success status vs `Code: 104` ("no objects for the given selection").

**Example:**
```python
# Source: https://genesis.destatis.de/datenbank/online/docs/GENESIS-Webservices_Einfuehrung.pdf, sec 2.4.10 (tables)
resp = requests.post(BASE_URL + "catalogue/tables", headers=headers,
                      data={"selection": "41120*", "pagelength": 50, "language": "de"})
```

### Pattern 4: Regional filtering via classifyingvariable/classifyingkey

**What:** GENESIS `data/table` and `data/tablefile` filter by region using
`classifyingvariable1`/`classifyingkey1` referencing the `"regionalkey"` classification, populated with
**AGS (Amtlicher Gemeindeschlüssel)** values — not raw NUTS3 alpha codes. [CITED: GENESIS-Anwenderdokumentation
Webservice/API v5.1, table/tablefile parameter reference, section 2.5.11/2.5.12]. `*`-wildcard notation is
supported (e.g. `12*` for all of Brandenburg). This is a required verification step, not yet confirmed
against a real response for this project's specific 12 NUTS3 codes.

### Anti-Patterns to Avoid

- **Mixing credentials into the request body:** This is the exact bug being fixed. GENESIS silently accepts
  malformed/misplaced credential params in some cases and returns generic errors that look like data-shape
  problems rather than auth problems — always confirm auth via `helloworld/logincheck` first when debugging.
- **Assuming `Kreiskennziffer` is the literal response column name:** the current code hardcodes this string;
  the real column name in a `format=csv`/`ffcsv` response should be confirmed empirically (GENESIS typically
  names dimension columns things like `1_Auspraegung_Code`/`1_variable_attribute_code` in `ffcsv`, not a
  human label like `Kreiskennziffer`, which only appears in some legacy wide-CSV exports). [ASSUMED — needs
  live verification]
- **Writing to `data/ll_content.json` from any pipeline script:** violates CLAUDE.md's critical rule and
  CONTENT-02. Destatis output must feed the *computed* side of `generate_metadata.py`'s merge only.
- **Requesting tables with `job=true` using only a token:** will fail; large tables (>40,000 values) that
  require the batch queue need real username/password credentials, not the token alone. [CITED: GENESIS-
  Anwenderdokumentation v5.1, section 2.1.3]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| GENESIS response CSV parsing | A second bespoke wide-CSV parser | Prefer `format=ffcsv` + `pandas.read_csv(delimiter=';', decimal=',', na_values=["...",".","-","/","x"])` as shown in the official example, OR keep the existing `csv.DictReader` approach for `format=csv` if the header-detection heuristic is verified to still work | The official example already solved decimal/na-value handling (German locale: comma decimal, `...`/`.`/`-`/`/`/`x` as missing-value sentinels) — re-deriving this from scratch risks silent mis-parsing |
| Retry/backoff for transient API failures | New retry framework | Existing `_post()` exponential backoff in `fetch_destatis.py` (already reasonable: 3 retries, `2**attempt` sleep) | Already implemented correctly; only the auth/header bug needs fixing, not the retry logic |
| AGS↔NUTS3 crosswalk (if confirmed necessary per Pattern 4) | Manual lookup table typed by hand | GISCO NUTS-LAU correspondence tables (already partially available via `fetch_nuts.py`'s GISCO NUTS3 fetch) or the Destatis "Gemeindeverzeichnis" reference data | Hand-typing 12 codes is low-risk for this specific case (5 Living Labs, 12 Kreise) but should still be sourced from an authoritative correspondence table, not guessed, since AGS/NUTS boundaries have historically diverged for a handful of German Kreise (e.g. post-2011 territorial reforms) |

**Key insight:** The existing pipeline architecture (fetch → cache raw CSV → build per-NUTS3 records →
aggregate per-LL → export expert CSVs) is well-designed and matches the project's established patterns
(mirrors `fetch_nuts.py`'s fetch/cache/transform/write structure). Phase 4's job is a **targeted bug fix
plus a data-quality verification pass**, not a rewrite.

## Common Pitfalls

### Pitfall 1: Auth headers vs body confusion resurfacing after partial fixes

**What goes wrong:** A fix that moves `username`/`password` to headers but leaves them also present in the
`data` body (defensive "just in case" duplication) may work by accident on some endpoints and fail
silently on others (e.g. `job=true` paths), masking the real bug.

**Why it happens:** GENESIS's parameter validation behavior across POST body vs header duplication is not
fully documented in the excerpts reviewed.

**How to avoid:** Remove `username`/`password` from `data` entirely; keep them only in `headers`. Verify
with `helloworld/logincheck` before touching the 34-table fetch loop.

**Warning signs:** Some tables fetch successfully (small ones, direct dialog) while others silently return
`null` (large ones needing `job=true`, which requires the stricter auth path).

### Pitfall 2: Trusting the catalogue CSV's table IDs without live verification

**What goes wrong:** Several of the 34-71 candidate table IDs in `destatis_variables_catalogue.csv` /
`fetch_destatis.py`'s `TABLES` list were plausibly generated from training-data pattern-matching on GENESIS
code conventions (`BJ`=Bund jährlich, `KJ`=Kreise jährlich, etc.) rather than confirmed against the live
catalogue. Some may not exist, may not resolve to Kreis-level regional depth, or may have been renamed/retired.

**Why it happens:** The catalogue was built before working API access existed (all values in the current
`data/destatis_variables.csv` are empty in the `genesis_table` cross-reference sense — the file exists but
was never validated end-to-end).

**How to avoid:** Before the full fetch, run each table ID through `catalogue/tables` (search) or
`metadata/table` to confirm it exists, is regionally scoped to Kreis level ("regionale Tiefe: Kreise und
krfr. Städte"), and has current data. Budget explicit time for this verification wave — it is not optional
given the number of tables involved.

**Warning signs:** A table returns `Code: 104` ("no objects for the given selection") or an empty CSV body.

### Pitfall 3: `ll_content.json`'s human-authored placeholder values silently winning over real Destatis data

**What goes wrong:** `data/ll_content.json` already contains `production`/`socio` blocks per LL (e.g.
`"population": "-"`, `"gdp_per_capita": "-"`) as hand-authored placeholders (see `MOCK_FACTSHEET_EN` origin
in `fetch_nuts.py` and the current `ll_content.json` content). `generate_metadata.py`'s merge policy is
**authored wins on key conflict** (`_deep_merge(computed, authored)` — for any key present in both, the
authored leaf value replaces the computed one). If Destatis data is injected into the *computed* side of
this merge without also clearing/updating the corresponding placeholder strings in `ll_content.json`, the
literal `"-"` placeholders will silently override the real numbers and the app will keep showing dashes.

**Why it happens:** CONTENT-02 intentionally makes human-authored content win, which is correct for
narrative text but wrong for numeric fields that are meant to become pipeline-computed once real data
exists.

**How to avoid:** This needs an explicit decision during planning — options include: (a) strip the
placeholder `production`/`socio`/`kpi` numeric sub-fields from `ll_content.json` for indicators that become
Destatis-sourced, letting the computed side populate them cleanly; (b) change the merge policy for a
specific allowlist of fields (kpi.area, kpi.farms, production.*, socio.*) to be computed-wins instead of
authored-wins; (c) treat `"-"` as an explicit "not yet authored" sentinel that the merge skips over. Each
has different blast radius — (a) requires editing the human-owned file (needs sign-off since it's meant to
be edited by humans, but this could be a one-time content update *by a human*, not by pipeline code, which
stays compliant with CLAUDE.md's rule); (b) requires new merge logic; (c) is the least invasive but changes
merge semantics project-wide. **Flag this as a decision point for `/gsd:discuss-phase 4`.**

**Warning signs:** Running `sync.py` after wiring Destatis data still shows `"-"` in `app/public/data/ll_metadata.json`.

### Pitfall 4: Regional key format mismatch (AGS vs NUTS3)

**What goes wrong:** If the real API response uses AGS 5-digit numeric Kreis codes and the existing
`ALL_NUTS3` list of `DE4xx`-style codes is matched directly against a response column, every `_latest()`
lookup silently returns `None` for every field — exactly the all-null state currently checked into
`data/destatis_nuts3.json` today (which may be explained by the auth bug alone, or may be a second bug
stacked on top of it).

**Why it happens:** NUTS3 and AGS are two different German administrative coding systems that are often
conflated in casual documentation but are not string-identical.

**How to avoid:** After fixing auth, fetch one small table and print the raw response headers/first rows
before writing any parsing logic that assumes a code format. Confirm whether an AGS↔NUTS3 crosswalk is
needed for the 12 specific Kreise this project covers.

**Warning signs:** All values remain `null` even after the auth fix is confirmed working via `logincheck`.

### Pitfall 5: Result code 104 misdiagnosed as an auth failure

**What goes wrong:** Treating GENESIS status code 104 as "credentials rejected" (as the original phase brief
assumed) leads to debugging effort in the wrong place — retrying auth, rotating tokens — when the actual
problem is a wrong table ID, wrong regional key, or overly narrow selection criteria.

**Why it happens:** [CITED: GENESIS-Anwenderdokumentation Webservice/API v5.1] Code 104's `Content` field
literally reads `"Es gibt keine Objekte zum angegebenen Selektionskriterium"` ("There are no objects for the
given selection criteria") and its `Type` is `"Information"`, not `"Error"`.

**How to avoid:** Treat 104 as "this specific table/filter combination returned nothing" — check the table
ID and classifying variables/keys, not the credentials, when this code appears.

## Code Examples

### Fixed `_post()` helper (drop-in replacement for the buggy version)

```python
# Source: adapted from https://genesis.destatis.de/datenbank/online/docs/20250505_python_post_logincheck_tablefile_cubefile.pdf
GENESIS_BASE = "https://genesis.destatis.de/genesisWS/rest/2020"  # note: host changed from www-genesis

def _headers() -> dict:
    return {
        "Content-Type": "application/x-www-form-urlencoded",
        "username": USERNAME,   # API token recommended here
        "password": PASSWORD,   # "" when using a token; real password only if job=true is needed
    }

def _post(endpoint: str, params: dict, retries: int = 3) -> requests.Response:
    url = f"{GENESIS_BASE}/{endpoint}"
    for attempt in range(retries):
        try:
            r = requests.post(url, headers=_headers(), data=params, timeout=90)
            r.raise_for_status()
            return r
        except requests.RequestException as exc:
            if attempt == retries - 1:
                raise
            wait = 2 ** attempt
            print(f"  [retry {attempt+1}/{retries-1} in {wait}s] {exc}")
            time.sleep(wait)
    raise RuntimeError("unreachable")
```

Note `params` passed to `_post()` must **no longer include `username`/`password`** — those moved to
`_headers()`. The call site `fetch_table_csv()`'s `{"name": table, "startyear": ..., "format": "csv", "language": "de"}`
dict stays otherwise unchanged.

### Pre-flight auth check to add before the fetch loop

```python
# Source: https://genesis.destatis.de/datenbank/online/docs/20250505_python_post_logincheck_tablefile_cubefile.pdf
def check_auth() -> None:
    r = requests.post(f"{GENESIS_BASE}/helloworld/logincheck", headers=_headers(), data={"language": "de"})
    r.raise_for_status()
    body = r.json()
    status = body.get("Status", {})
    if status.get("Code") not in (0, None):
        raise SystemExit(f"[error] GENESIS auth check failed: {status}")
    print(f"[ok] GENESIS auth verified ({status.get('Content', '')[:60]}...)")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| GET requests with credentials as query params | POST-only, credentials in headers, `Content-Type: application/x-www-form-urlencoded` | 30 June 2025 (GET permanently disabled) [CITED: GENESIS-Anwenderdokumentation v5.1, sec 1.5/1.7/2.1.3] | Every GENESIS client written before mid-2025 (including this project's paused `fetch_destatis.py`, and most older tutorials/StackOverflow snippets/community wrapper libraries found via web search) is broken until updated |
| `www-genesis.destatis.de` base host | `genesis.destatis.de` base host | Documented migration target date was 28 May 2026 (per phase context); the official June-2026-dated example PDF already uses the new host exclusively, so treat the new host as live and authoritative now | Update `GENESIS_BASE` in `fetch_destatis.py` |

**Deprecated/outdated:** Most search-indexed community examples (`sjockers/genesis-api-example`,
`bundesAPI/deutschland` docs, `genesispy` README as surfaced by search) still show GET-with-query-param auth
against the old host — these are stale relative to the June 2026 official documentation and should not be
copied as-is. Trust the two official Destatis PDFs fetched during this research over any third-party example
found via search.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The response column carrying the Kreis identifier is not literally named `Kreiskennziffer` in `format=csv`/`ffcsv` responses, and/or uses AGS numeric codes rather than NUTS3 alpha codes | Pattern 4, Pitfall 4 | If wrong, no crosswalk is needed and the existing `_latest()`/`apply()` logic in `build_nuts3_records()` works unchanged after the auth fix — low cost to verify, high cost to skip verifying |
| A2 | All 34-71 candidate GENESIS table IDs in the catalogue are plausible but unverified against the live API | Pitfall 2 | Some fetches may silently fail (code 104) or fetch the wrong statistic; expert-review CSVs would then contain misleading empty/wrong columns |
| A3 | `format=ffcsv` is a net robustness improvement over the current `format=csv` heuristic-header parsing | Alternatives Considered | Low risk either way — this is an optional refactor recommendation, not required for the auth fix |
| A4 | The API token (not username/password) is sufficient for all 34 tables' direct-dialog retrieval (i.e., none require `job=true` batch queue due to the >40,000-value limit) | Pattern 1, Pitfall 1 | If any table exceeds the limit, token-only auth will fail specifically for that table and real username/password must be used instead |
| A5 | GENESIS-Online (genesis.destatis.de) itself serves Kreis-level regional depth for all needed tables, rather than requiring the separate Regionalstatistik.de portal/database | Summary, Architectural Responsibility Map | If some indicators (especially agricultural census detail) are only available via Regionalstatistik.de, those tables need a second base URL / possibly separate registration & credentials, which changes the pipeline's auth model from single-host to multi-host |

## Open Questions

1. **Which database hosts each of the 34 candidate tables — GENESIS-Online (Bund) or Regionalstatistik.de?**
   - What we know: GENESIS-Online's federal database does include some Kreis-level tables directly (the
     official docs example table `"11111-0002 – Gebietsfläche: Kreise, Stichtag"` is Kreis-level and lives
     in the federal database). Regionalstatistik.de is a separate platform ("die zentrale Plattform
     Regionalstatistik.de") historically used for finer regional breakdowns, especially agricultural census
     data.
   - What's unclear: Whether Regionalstatistik.de requires separate registration/credentials and a different
     base URL (`www.regionalstatistik.de/...`), and whether any of the catalogue's agriculture-themed table
     IDs (`41xxxBJ*`, farm/livestock/land-use series) actually live there instead of on genesis.destatis.de.
   - Recommendation: During the Wave 1 auth-fix task, probe 2-3 representative table IDs from each theme
     (Agriculture, Social/Demography, Economy, Environment) against `genesis.destatis.de` first; only pursue
     Regionalstatistik.de registration if `catalogue/tables`/`metadata/table` calls come back empty for a
     given ID on the primary host.

2. **What does the fixed merge policy for computed-vs-authored numeric fields look like?**
   - What we know: The current `_deep_merge` in `generate_metadata.py` makes authored (`ll_content.json`)
     win unconditionally on any key present in both, and `ll_content.json` currently has literal `"-"`
     placeholder strings in its `production`/`socio` blocks and zero-valued `kpi` numbers for most LLs.
   - What's unclear: Whether the fix should be a merge-logic change, a one-time human edit to strip
     placeholders, or a sentinel-value convention (treat `"-"` as "no override").
   - Recommendation: Surface explicitly in `/gsd:discuss-phase 4` as a locked decision before planning Wave 3
     (app wiring) — this affects the shape of `generate_metadata.py`'s changes materially.

3. **Which of the 34-71 candidate indicators does the project actually want in the app (vs. only in the expert-review CSV)?**
   - What we know: `data/destatis_variables.csv` has `include_yn`/`priority_1_3`/`notes` columns meant for
     expert review, currently all empty. `docs/data-sources.md` and `.planning/STATE.md` reference an
     unresolved human-review step for the sibling Phase 3.1 catalogue (`data/variables_catalogue.xlsx`),
     which is a strong signal this project consistently gates data-source selection through human review
     before integration.
   - What's unclear: Whether Phase 4 should include the human-review step itself (mirroring Phase 3.1's
     Wave 3 pattern) or assume it happens out-of-band before/during planning.
   - Recommendation: Treat variable selection as an explicit wave/checkpoint in the plan, not an implicit
     step — this project's established pattern (Phase 3.1) is human-in-the-loop before integration.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `requests` (Python) | GENESIS API calls | Yes | 2.32.5 installed [VERIFIED: pip index versions] | — |
| `python-dotenv` (Python) | `.env` credential loading | Yes | 1.2.1 installed [VERIFIED: pip index versions] | — |
| `.env` with `DESTATIS_USERNAME`/`DESTATIS_API_TOKEN` | Auth | File exists at repo root (`.env` present per glob; contents not inspected — out of scope for research to read secrets) | — | If missing/empty, `fetch_destatis.py` already fails fast with a clear `SystemExit` message, which is correct behavior to keep |
| Network access to `genesis.destatis.de` | All fetch calls | Not verified in this research session (no live API call made) | — | None — this is a hard external dependency; if the CI/dev environment cannot reach the host, fetch must run manually and commit outputs, matching the existing "fetch once, commit static output" pipeline pattern used by `fetch_nuts.py`/`build_pmtiles.py` |
| `pdftotext`/poppler (research-only) | N/A — not a runtime dependency | Yes, present in this dev environment | — | Not relevant to the pipeline itself |

**Missing dependencies with no fallback:** None identified for the pipeline itself — all required Python
packages are already installed.

**Missing dependencies with fallback:** None required.

## Security Domain

`workflow.nyquist_validation` is `false` in `.planning/config.json`, so the Validation Architecture section
is skipped per instructions. `security_enforcement` is not set, so it is treated as enabled; this phase's
security surface is narrow (a build-time credential, no runtime auth/session in the app) but worth
documenting explicitly.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | The app itself has no user authentication; only the *pipeline* authenticates to an external API at build time |
| V3 Session Management | No | Static SPA, no sessions |
| V4 Access Control | No | Public anonymous site (per REQUIREMENTS.md "Out of Scope") |
| V5 Input Validation | Yes | External CSV/JSON responses from GENESIS must be parsed defensively — the existing `_num()` helper already handles German-locale decimal commas and sentinel missing-value strings (`-`, `/`, `...`, `x`); keep this pattern when adding `ffcsv` support |
| V6 Cryptography / Secrets | Yes | `DESTATIS_USERNAME`/`DESTATIS_API_TOKEN` must stay in `.env` (already gitignored per `.env.example` convention), never logged, never committed in `data/destatis_raw/*.csv` cache files (verify cached CSVs don't embed credentials — GENESIS response bodies do NOT echo credentials in the `data/tablefile` success path, only in error-diagnostic `Parameter` blocks shown in the docs with credentials masked as `********************`) |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Credential leakage via error logs/print statements | Information Disclosure | Never `print()` the full `headers` dict; the existing `print(f"User: {USERNAME} ...")` in `main()` prints the username but not the token/password — keep this asymmetry, do not add password/token to any print statement |
| Credential leakage via committed cache files | Information Disclosure | `data/destatis_raw/*.csv` are committed as pipeline cache; GENESIS success responses do not embed the request credentials in the body, but confirm this holds for whichever `format=` is chosen before committing new cache files |
| Malformed/oversized API responses (denial of service to the pipeline, not the app) | Denial of Service | Existing `timeout=90` and 3-retry exponential backoff in `_post()` already mitigate hangs; keep this when refactoring |

## Sources

### Primary (HIGH confidence)
- `20250505_python_post_logincheck_tablefile_cubefile.pdf` — https://genesis.destatis.de/datenbank/online/docs/20250505_python_post_logincheck_tablefile_cubefile.pdf — official Destatis Python POST-request code examples (logincheck, tablefile, cubefile, catalogue/cubes), last edited June 2026. Fetched and extracted via `pdftotext -layout` in this research session.
- `GENESIS-Webservices_Einfuehrung.pdf` (GENESIS-Anwenderdokumentation "Webservice/API" Version 5.1, 01.06.2026) — https://genesis.destatis.de/datenbank/online/docs/GENESIS-Webservices_Einfuehrung.pdf — full 123-page API reference: authentication model (2.1.3), all service/method list (table of contents, section 2), status code 104 definition (multiple examples), rate-limit note (section 1.7, "certain number of parallel requests," logincheck also terminates hung requests after >15 min per an embedded response example), classifyingvariable/regionalkey mechanism (table/tablefile parameter reference). Fetched and extracted via `pdftotext -layout`.

### Secondary (MEDIUM confidence)
- WebSearch results on GENESIS-Online REST API base URL migration and GET-deprecation date (30 June 2025 / 15 July 2025 — sources disagree by two weeks; the primary-source PDF's "30. Juni 2025" is treated as authoritative over search-snippet paraphrases).
- WebFetch of `github.com/StatistischesBundesamt/GENESIS-Online` and `github.com/bundesAPI/deutschland` — confirm GET removal and general endpoint shape, but their visible code examples are pre-migration (GET + query-param auth) and should not be copied directly.

### Tertiary (LOW confidence)
- WebSearch/WebFetch on Regionalstatistik.de vs GENESIS-Online table availability split — no authoritative source found that enumerates which specific tables live on which host; flagged as Open Question 1 rather than asserted as fact.
- `restatis` (R package) and `genesispy` documentation excerpts — acknowledge both databases exist but do not detail the split; not used as a basis for any claim in this document beyond confirming the two hosts exist.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages, existing versions confirmed live against PyPI
- Architecture (auth/request fix): HIGH — sourced directly from two official, dated (June 2026) Destatis PDFs, cross-checked against each other
- Architecture (regional key / table availability): LOW-MEDIUM — plausible mechanism documented, but not verified against a real response for this project's specific tables; flagged as Open Questions and Assumptions requiring a verification task early in Wave 1
- Pitfalls: MEDIUM-HIGH — pitfalls 1, 3, 5 are directly evidenced from source code + official docs; pitfalls 2, 4 are informed predictions that need empirical confirmation during implementation

**Research date:** 2026-07-24
**Valid until:** ~30 days (GENESIS API is mid-migration as of this research; Destatis has already moved the goalposts twice in the past year per the docs found — re-verify base URL and auth model if implementation starts more than a few weeks after this research)
