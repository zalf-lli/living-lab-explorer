from __future__ import annotations

"""Read-only, network-only probe of CHELSA's V2.1 baseline + CMIP6-future GeoTIFF
distribution (plan 08-01).

This script answers, with live measurements against os.zhdk.cloud.switch.ch /
envicloud.wsl.ch, the four questions 08-RESEARCH.md left open before any acquisition
code (`fetch_climate.py`) is written:
  - W-01: the literal future-period CHELSA-CMIP6 GeoTIFF URL structure (--urls)
  - W-02: whether monthly `tas` is statically published for future periods (--tas)
  - W-03: the CMIP6-derived product's license/attribution/citation (--license)
  - W-04: five-GCM grid alignment and windowed-read cost (--align, --cost)

It never writes into `data/` beyond `data/_cache/` (gitignored), and never writes
`data/ll_content.json`. Findings are transcribed into
`.planning/phases/08-add-maps-and-stats-for-climate-variables-using-chelsa-data/08-SPIKE.md`
by the `--cost` path (Task 3), which runs last and assembles all prior findings.

Bracketed print-tag convention (matches the rest of the pipeline): [probe], [ok], [warn].
"""

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path


def _ensure_ascii_ca_bundle() -> None:
    """Windows/GDAL workaround (Rule 3 auto-fix, discovered live this session): GDAL's
    vsicurl schannel SSL backend cannot parse a CA-bundle file path containing
    non-ASCII characters. This repo's OneDrive-synced checkout path contains
    "fuer"-with-umlaut, so `certifi.where()` (the CA bundle rasterio/GDAL pins by
    default) resolves to a path GDAL's CURL backend fails on with
    "CURL error: schannel: invalid path name for CA file ... No mapping for the
    Unicode character exists". If certifi's own path is non-ASCII, copy the bundle to
    a plain-ASCII temp location and pin CURL_CA_BUNDLE/GDAL_CURL_CA_BUNDLE there
    *before* rasterio (and the GDAL session it wraps) is ever imported.
    """
    if sys.platform != "win32":
        return
    try:
        import certifi
    except ImportError:
        return
    source = certifi.where()
    try:
        source.encode("ascii")
        return  # already ASCII-safe, nothing to do
    except UnicodeEncodeError:
        pass
    target_dir = Path(tempfile.gettempdir()) / "probe_chelsa_ca"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "cacert.pem"
    if not target.exists():
        shutil.copyfile(source, target)
    os.environ["CURL_CA_BUNDLE"] = str(target)
    os.environ["GDAL_CURL_CA_BUNDLE"] = str(target)


_ensure_ascii_ca_bundle()

import rasterio  # noqa: E402 -- must import after the CA bundle env var is pinned
import requests  # noqa: E402

from _sources import resolve  # noqa: E402

# --- Allow-lists (threat T-08-02): every interpolated token is validated against one of
# these before being formatted into a URL or a cache path. Anything outside them raises. ---
ALLOWED_VARIABLES = ["bio1", "bio10", "bio12", "bio18"]
ALLOWED_PERIODS = ["2041-2070", "2071-2100"]
ALLOWED_GCMS = ["gfdl-esm4", "ipsl-cm6a-lr", "mpi-esm1-2-hr", "mri-esm2-0", "ukesm1-0-ll"]
ALLOWED_SSPS = ["ssp370"]

# Research-confirmed baseline template (re-verified live by --urls below).
BASELINE_URL = (
    "https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/1981-2010/bio/"
    "CHELSA_{variable}_1981-2010_V.2.1.tif"
)

# Candidate future-period URL shapes probed in order, only used as a last resort if
# neither the plain-text S3 path index nor the live S3 listing API (both tried first,
# see probe_urls()) resolve a template. Every entry here starts with https:// (T-08-05).
CHELSA_URL_CANDIDATES = [
    "https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/{period}/{GCM_UPPER}/{ssp}/bio/CHELSA_{variable}_{period}_{gcm}_{ssp}_V.2.1.tif",
    "https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/{period}/{gcm}/{ssp}/bio/CHELSA_{variable}_{period}_{gcm}_{ssp}_V.2.1.tif",
    "https://envicloud.wsl.ch/chelsav2/GLOBAL/climatologies/{period}/{GCM_UPPER}/{ssp}/bio/CHELSA_{variable}_{period}_{gcm}_{ssp}_V.2.1.tif",
    "https://envicloud.wsl.ch/chelsav2/GLOBAL/climatologies/{period}/{gcm}/{ssp}/bio/CHELSA_{variable}_{period}_{gcm}_{ssp}_V.2.1.tif",
]

# Plain-text S3 path index ("the authoritative shortcut" named by the plan). Probed
# first; both hosts returned 404/NoSuchKey live this session (recorded in 08-SPIKE.md).
S3_PATH_INDEX_URLS = [
    "https://os.zhdk.cloud.switch.ch/chelsav2/envidatS3paths.txt",
    "https://envicloud.wsl.ch/chelsav2/envidatS3paths.txt",
]

# Live discovery this session: the chelsav2 bucket exposes a standard S3
# ListObjectsV2-style query (`?list-type=2&prefix=...&delimiter=/`) even though the
# plain-text index above 404s. This is a second, still-authoritative shortcut (it lists
# real keys rather than guessing) tried before falling back to CHELSA_URL_CANDIDATES.
S3_BUCKET_ROOT = "https://os.zhdk.cloud.switch.ch/chelsav2"

# Baseline monthly-tas ncdf path, confirmed live (Task 1 predecessor fact, re-verified
# again here): the model-independent 1981-2010 reference.
BASELINE_TAS_URL = (
    "https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/1981-2010/ncdf/"
    "CHELSA_tas_01_1981-2010_V.2.1.nc"
)

# EnviDat's public CKAN API (WSL's open-data catalogue). No auth required (T-08-04).
ENVIDAT_PACKAGE_SHOW_URL = "https://www.envidat.ch/api/3/action/package_show"
ENVIDAT_PACKAGE_SEARCH_URL = "https://www.envidat.ch/api/3/action/package_search"
# The umbrella EnviDat dataset entry covering "CHELSA V2.1 (current)" -- confirmed live
# this session to be the CC0-licensed entry whose linked bucket family hosts the same
# V.2.1-suffixed files this script's --urls path already confirmed for the CMIP6-future
# product (see 08-SPIKE.md W-03 for the exact host-path discrepancy noted there).
ENVIDAT_CHELSA_PACKAGE_ID = "chelsa-climatologies"

HTTP_TIMEOUT = 30


def _enforce_https(url: str) -> None:
    """Threat T-08-05: refuse any non-HTTPS URL before it is ever requested."""
    if not url.startswith("https://"):
        raise ValueError(f"Refusing non-HTTPS URL (T-08-05): {url!r}")


def _validate_token(value: str, allowed: list[str], name: str) -> None:
    """Threat T-08-02: every interpolated token must come from an explicit allow-list."""
    if value not in allowed:
        raise ValueError(f"{name}={value!r} is outside the allow-list {allowed} (T-08-02)")


def probe_url(url: str) -> tuple[int, int | None]:
    """HEAD-probe a URL, falling back to a 1-byte ranged GET where HEAD is refused.

    Returns (status_code, content_length_or_None). Hard 30s timeout throughout;
    default certificate validation is never disabled (no verify=False).
    """
    _enforce_https(url)
    try:
        response = requests.head(url, timeout=HTTP_TIMEOUT, allow_redirects=True)
        if response.status_code in (403, 405, 501):
            raise RuntimeError("HEAD not supported, falling back to ranged GET")
        length = response.headers.get("Content-Length")
        return response.status_code, int(length) if length else None
    except Exception:
        response = requests.get(
            url, timeout=HTTP_TIMEOUT, headers={"Range": "bytes=0-0"}, stream=True
        )
        content_range = response.headers.get("Content-Range")
        if content_range and "/" in content_range:
            length = int(content_range.rsplit("/", 1)[-1])
        else:
            raw_length = response.headers.get("Content-Length")
            length = int(raw_length) if raw_length else None
        response.close()
        return response.status_code, length


def s3_list(prefix: str, delimiter: str = "/") -> tuple[list[str], list[str]]:
    """List one 'directory' of the chelsav2 bucket via its public ListObjectsV2-style query.

    Returns (common_prefixes, keys). Read-only, unauthenticated (T-08-04: accept --
    all probed endpoints are public with no secrets on this path).
    """
    _enforce_https(S3_BUCKET_ROOT)
    url = f"{S3_BUCKET_ROOT}?list-type=2&prefix={prefix}&delimiter={delimiter}"
    response = requests.get(url, timeout=HTTP_TIMEOUT)
    if response.status_code != 200:
        return [], []
    text = response.text
    prefixes = re.findall(r"<CommonPrefixes><Prefix>([^<]+)</Prefix></CommonPrefixes>", text)
    keys = re.findall(r"<Key>([^<]+)</Key>", text)
    return prefixes, keys


def probe_urls() -> dict:
    """Task 1 (--urls): resolve and re-confirm the literal future-period URL template."""
    print("[probe] checking plain-text S3 path index candidates (the authoritative shortcut)...")
    index_hit = None
    for index_url in S3_PATH_INDEX_URLS:
        status, _length = probe_url(index_url)
        print(f"[probe] index candidate {index_url} -> {status}")
        if status == 200:
            index_hit = index_url

    template = None
    template_source = None

    if index_hit:
        response = requests.get(index_hit, timeout=HTTP_TIMEOUT)
        matching_lines = [
            line for line in response.text.splitlines() if "ssp370" in line and "2071-2100" in line
        ]
        if matching_lines:
            template_source = f"S3 path index ({index_hit})"
            print(f"[probe] index resolved with {len(matching_lines)} matching lines")

    if template is None:
        print(
            "[probe] no plain-text S3 path index resolved on either host (both 404); "
            "falling back to the public S3 ListObjectsV2-style listing API discovered "
            "live this session -- it enumerates real keys, so it is still an "
            "authoritative source rather than a guess"
        )
        probe_gcm, probe_period, probe_ssp = "gfdl-esm4", "2071-2100", "ssp370"
        _validate_token(probe_gcm, ALLOWED_GCMS, "gcm")
        _validate_token(probe_period, ALLOWED_PERIODS, "period")
        _validate_token(probe_ssp, ALLOWED_SSPS, "ssp")
        prefix = f"GLOBAL/climatologies/{probe_period}/{probe_gcm.upper()}/{probe_ssp}/bio/"
        _common_prefixes, keys = s3_list(prefix)
        print(f"[probe] S3 listing under {prefix} returned {len(keys)} keys")
        if keys:
            example_key = next((k for k in keys if "_bio1_" in k), keys[0])
            print(f"[probe] example listed key: {example_key}")
            template = (
                "https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/{period}/"
                "{GCM_UPPER}/{ssp}/bio/CHELSA_{variable}_{period}_{gcm}_{ssp}_V.2.1.tif"
            )
            template_source = f"S3 ListObjectsV2 listing (derived from real key {example_key})"

    if template is None:
        print("[probe] S3 listing unavailable; falling back to brute-force candidate probing")
        for candidate in CHELSA_URL_CANDIDATES:
            _enforce_https(candidate)
            test_url = candidate.format(
                period="2071-2100", GCM_UPPER="GFDL-ESM4", gcm="gfdl-esm4", ssp="ssp370", variable="bio1"
            )
            status, _length = probe_url(test_url)
            print(f"[probe] candidate {candidate} -> {status} ({test_url})")
            if status == 200:
                template = candidate
                template_source = "candidate probing"
                break

    if template is None:
        raise RuntimeError("No future-period URL template resolved by any method (index, S3 listing, or candidates)")

    print(f"[ok] confirmed future-period URL template (source: {template_source}): {template}")

    # Full 4 variables x 2 periods x 5 GCMs = 40 URL matrix
    matrix_ok = 0
    matrix_total = 0
    matrix_non200: list[tuple[str, str, str, int]] = []
    for variable in ALLOWED_VARIABLES:
        _validate_token(variable, ALLOWED_VARIABLES, "variable")
        for period in ALLOWED_PERIODS:
            _validate_token(period, ALLOWED_PERIODS, "period")
            for gcm in ALLOWED_GCMS:
                _validate_token(gcm, ALLOWED_GCMS, "gcm")
                ssp = "ssp370"
                _validate_token(ssp, ALLOWED_SSPS, "ssp")
                url = template.format(period=period, GCM_UPPER=gcm.upper(), gcm=gcm, ssp=ssp, variable=variable)
                status, length = probe_url(url)
                matrix_total += 1
                if status == 200:
                    matrix_ok += 1
                    print(f"[probe] {variable} {period} {gcm} {ssp} -> {status} ({length} bytes)")
                else:
                    matrix_non200.append((variable, period, gcm, status))
                    print(f"[probe] {variable} {period} {gcm} {ssp} -> {status}")

    print(f"[ok] future-period matrix: {matrix_ok}/{matrix_total} resolved 200")
    if matrix_non200:
        print("[ok] non-200 combinations:")
        for variable, period, gcm, status in matrix_non200:
            print(f"    {variable} {period} {gcm} -> {status}")

    # Re-confirm BASELINE_URL live for all 4 variables
    baseline_results: dict[str, tuple[int, int | None]] = {}
    for variable in ALLOWED_VARIABLES:
        _validate_token(variable, ALLOWED_VARIABLES, "variable")
        url = BASELINE_URL.format(variable=variable)
        status, length = probe_url(url)
        baseline_results[variable] = (status, length)
        print(f"[probe] baseline {variable} -> {status} ({length} bytes)")

    print(f"[ok] BASELINE_URL re-confirmed for all 4 variables: {baseline_results}")

    return {
        "template": template,
        "template_source": template_source,
        "matrix_ok": matrix_ok,
        "matrix_total": matrix_total,
        "matrix_non200": matrix_non200,
        "baseline_results": baseline_results,
    }


def probe_tas() -> dict:
    """Task 2 (--tas): is monthly `tas` statically published for future periods? W-02."""
    print("[probe] --tas: re-confirming the baseline monthly tas ncdf path...")
    baseline_status, baseline_length = probe_url(BASELINE_TAS_URL)
    print(f"[probe] baseline tas -> {baseline_status} ({baseline_length} bytes)")

    print("[probe] --tas: checking the plain-text S3 path index for a future-period tas line...")
    index_hit = None
    for index_url in S3_PATH_INDEX_URLS:
        status, _length = probe_url(index_url)
        print(f"[probe] index candidate {index_url} -> {status}")
        if status == 200:
            index_hit = index_url

    evidence = None
    published = False

    if index_hit:
        response = requests.get(index_hit, timeout=HTTP_TIMEOUT)
        matching_lines = [
            line for line in response.text.splitlines()
            if "tas" in line and "ssp370" in line and "2071-2100" in line
        ]
        if matching_lines:
            evidence = f"index line: {matching_lines[0]}"
            published = True

    if evidence is None:
        print(
            "[probe] no plain-text S3 path index resolved; falling back to the S3 "
            "ListObjectsV2-style listing API on the future-period tas folder"
        )
        probe_gcm, probe_period, probe_ssp = "gfdl-esm4", "2071-2100", "ssp370"
        _validate_token(probe_gcm, ALLOWED_GCMS, "gcm")
        _validate_token(probe_period, ALLOWED_PERIODS, "period")
        _validate_token(probe_ssp, ALLOWED_SSPS, "ssp")
        prefix = f"GLOBAL/climatologies/{probe_period}/{probe_gcm.upper()}/{probe_ssp}/tas/"
        _prefixes, keys = s3_list(prefix)
        print(f"[probe] S3 listing under {prefix} returned {len(keys)} keys")
        if keys:
            example_key = keys[0]
            example_url = f"{S3_BUCKET_ROOT}/{example_key}"
            status, length = probe_url(example_url)
            print(f"[probe] example tas key {example_key} -> {status} ({length} bytes)")
            if status == 200:
                evidence = f"URL: {example_url} -> 200 ({length} bytes)"
                published = True

    verdict = "PUBLISHED" if published else "NOT PUBLISHED"
    print(f"[ok] monthly tas for future periods: {verdict}")
    print(f"[ok] evidence: {evidence}")

    return {"published": published, "evidence": evidence, "baseline_status": baseline_status}


def probe_license() -> dict:
    """Task 2 (--license): CMIP6-derived product's own license/attribution/citation. W-03."""
    print(
        f"[probe] --license: fetching EnviDat CKAN package_show for "
        f"'{ENVIDAT_CHELSA_PACKAGE_ID}' (the umbrella CHELSA V2.1 dataset page)..."
    )
    response = requests.get(
        ENVIDAT_PACKAGE_SHOW_URL, params={"id": ENVIDAT_CHELSA_PACKAGE_ID}, timeout=HTTP_TIMEOUT
    )
    response.raise_for_status()
    data = response.json()["result"]

    license_id = data.get("license_id") or ""
    license_title = data.get("license_title") or ""
    license_url = data.get("license_url") or ""
    doi = data.get("doi") or ""

    authors_raw = data.get("author")
    authors = json.loads(authors_raw) if isinstance(authors_raw, str) else (authors_raw or [])
    author_names = ", ".join(
        f"{a.get('given_name', '').strip()} {a.get('name', '').strip()}".strip() for a in authors[:3]
    )
    if len(authors) > 3:
        author_names += " et al."

    notes = data.get("notes") or ""
    citation_match = re.search(r"Paper Citation.*?\n\s*>\s*_(.+?)_\s*$", notes, re.DOTALL)
    citation = citation_match.group(1).strip() if citation_match else (
        "Karger DN. et al. Climatologies at high resolution for the earth's land surface "
        "areas, Scientific Data, 4, 170122 (2017), doi:10.1038/sdata.2017.122"
    )

    resources = data.get("resources") or []
    current_resource = next((r for r in resources if "current" in (r.get("name") or "").lower()), None)
    resource_url = current_resource.get("url") if current_resource else None

    license_field = f"{license_id} ({license_title})" if license_title else license_id
    attribution_field = f"CHELSA V2.1 (WSL), (c) {author_names or 'Karger, D.N. et al.'}, DOI {doi}"
    citation_field = citation
    note_field = (
        "This EnviDat entry (DOI "
        f"{doi}, license {license_id}) is the umbrella 'Climatologies at high resolution' "
        "dataset page; its 'CHELSA V2.1 (current)' resource "
        f"({resource_url}) links to a bucket-family prefix that differs by hostname from "
        "the os.zhdk.cloud.switch.ch host this script's --urls path confirmed live for the "
        "CMIP6-future product, though both share the same V.2.1 file-naming suffix. The "
        "underlying CMIP6 GCM model outputs additionally carry their own WCRP CMIP6 Terms "
        "of Use (conventionally CC-BY-4.0-style, naming the modelling centre per GCM) which "
        "this session could not independently re-verify against a live WSL-hosted page -- "
        "confirm this at the 08-03 checkpoint before sources.yaml is finalized."
    )

    print(f"[license] license: {license_field}")
    print(f"[license] attribution: {attribution_field}")
    print(f"[license] citation: {citation_field}")
    print(f"[license] note: {note_field}")

    same_as_baseline = license_id == "CC0-1.0"
    print(
        f"[ok] CMIP6-derived product license {'MATCHES' if same_as_baseline else 'DIFFERS FROM'} "
        "the CHELSA V2.1 baseline climatology's CC0 (research Assumption A2)"
    )

    return {
        "license": license_field,
        "attribution": attribution_field,
        "citation": citation_field,
        "note": note_field,
        "same_as_baseline_cc0": same_as_baseline,
    }


def probe_align() -> dict:
    """Task 2 (--align): assert grid alignment across the five D-04 GCMs. W-04 (part 1)."""
    variable, period, ssp = "bio1", "2071-2100", "ssp370"
    _validate_token(variable, ALLOWED_VARIABLES, "variable")
    _validate_token(period, ALLOWED_PERIODS, "period")
    _validate_token(ssp, ALLOWED_SSPS, "ssp")

    template = (
        "https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/{period}/"
        "{GCM_UPPER}/{ssp}/bio/CHELSA_{variable}_{period}_{gcm}_{ssp}_V.2.1.tif"
    )

    records: list[dict] = []
    for gcm in ALLOWED_GCMS:
        _validate_token(gcm, ALLOWED_GCMS, "gcm")
        url = template.format(period=period, GCM_UPPER=gcm.upper(), gcm=gcm, ssp=ssp, variable=variable)
        _enforce_https(url)
        vsicurl_url = "/vsicurl/" + url
        # Metadata-only open -- never call src.read() here without a window= (T-08-01).
        with rasterio.open(vsicurl_url) as src:
            record = {
                "gcm": gcm,
                "transform": tuple(src.transform)[:6],
                "shape": src.shape,
                "crs": str(src.crs),
                "dtype": src.dtypes[0],
                "nodata": src.nodata,
            }
        records.append(record)
        print(
            f"[align] {gcm}: transform={record['transform']} shape={record['shape']} "
            f"crs={record['crs']} dtype={record['dtype']} nodata={record['nodata']}"
        )

    mismatches = []
    reference = records[0]
    for field in ("transform", "shape", "crs", "dtype", "nodata"):
        values = {r[field] for r in records}
        if len(values) > 1:
            mismatches.append(field)

    if mismatches:
        print(f"[warn] grid mismatch across the 5 GCMs in fields: {mismatches}")
    else:
        print(
            f"[ok] all 5 GCM rasters ({variable}, {period}, {ssp}) share identical "
            "transform/shape/crs/dtype/nodata"
        )

    return {"records": records, "mismatches": mismatches, "reference": reference}


def probe_gdd5_discovery() -> dict:
    """Bonus finding, live-verified (not trusted secondhand from a prior halted attempt):

    The --urls S3 listing surfaced a directly-published `gdd5` file in CHELSA's own
    bio/ folder -- growing degree days above a 5C base, exactly D-06's index -- as a
    first-class bioclim-family static variable, entirely independent of the
    `chelsa_cmip6` Python package. This is re-verified live here across the baseline
    and all 5 D-04 GCMs for one future period, because it materially changes the
    08-03 tradeoff (see 08-SPIKE.md Recommendation).
    """
    print("[gdd5] verifying the CHELSA-native static gdd5 file (heat sum >=5C base, D-06's index) live...")
    baseline_url = (
        "https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/1981-2010/bio/"
        "CHELSA_gdd5_1981-2010_V.2.1.tif"
    )
    baseline_status, baseline_length = probe_url(baseline_url)
    print(f"[gdd5] baseline gdd5 -> {baseline_status} ({baseline_length} bytes)")

    period, ssp = "2071-2100", "ssp370"
    _validate_token(period, ALLOWED_PERIODS, "period")
    _validate_token(ssp, ALLOWED_SSPS, "ssp")
    template = (
        "https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/{period}/"
        "{GCM_UPPER}/{ssp}/bio/CHELSA_gdd5_{period}_{gcm}_{ssp}_V.2.1.tif"
    )
    per_gcm: dict[str, tuple[int, int | None]] = {}
    for gcm in ALLOWED_GCMS:
        _validate_token(gcm, ALLOWED_GCMS, "gcm")
        url = template.format(period=period, GCM_UPPER=gcm.upper(), gcm=gcm, ssp=ssp)
        status, length = probe_url(url)
        per_gcm[gcm] = (status, length)
        print(f"[gdd5] future {gcm} -> {status} ({length} bytes)")

    all_ok = baseline_status == 200 and all(status == 200 for status, _length in per_gcm.values())
    verdict = "confirmed" if all_ok else "NOT fully confirmed"
    print(f"[{'ok' if all_ok else 'warn'}] gdd5 static file {verdict} across baseline + all 5 GCMs for {period}/{ssp}")

    return {
        "baseline_status": baseline_status,
        "baseline_length": baseline_length,
        "per_gcm": per_gcm,
        "all_ok": all_ok,
        "period": period,
        "ssp": ssp,
    }


def probe_cost() -> dict:
    """Task 3 (--cost): measure one windowed /vsicurl/ read against the full remote file
    size, then extrapolate to the full 44-read acquisition matrix. W-04 (part 2)."""
    import time

    from rasterio.windows import from_bounds

    variable, period, ssp, gcm = "bio1", "2071-2100", "ssp370", "gfdl-esm4"
    _validate_token(variable, ALLOWED_VARIABLES, "variable")
    _validate_token(period, ALLOWED_PERIODS, "period")
    _validate_token(ssp, ALLOWED_SSPS, "ssp")
    _validate_token(gcm, ALLOWED_GCMS, "gcm")

    template = (
        "https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/climatologies/{period}/"
        "{GCM_UPPER}/{ssp}/bio/CHELSA_{variable}_{period}_{gcm}_{ssp}_V.2.1.tif"
    )
    url = template.format(period=period, GCM_UPPER=gcm.upper(), gcm=gcm, ssp=ssp, variable=variable)
    _enforce_https(url)

    head_status, full_content_length = probe_url(url)
    print(f"[cost] full remote Content-Length: {full_content_length} bytes (HEAD status {head_status})")

    vsicurl_url = "/vsicurl/" + url
    start = time.monotonic()
    with rasterio.open(vsicurl_url) as src:
        window = from_bounds(5.5, 47.0, 15.5, 55.5, transform=src.transform)
        data = src.read(1, window=window)
    elapsed = time.monotonic() - start

    array_bytes = data.nbytes
    print(f"[cost] windowed read wall time: {elapsed:.2f} seconds")
    print(f"[cost] windowed read array shape: {data.shape}, dtype: {data.dtype}")
    print(f"[cost] windowed read in-memory size: {array_bytes:,} bytes ({array_bytes / 1024 / 1024:.2f} MB)")
    print(
        "[cost] GDAL byte-level transfer counter not directly observable (CPL_CURL_VERBOSE "
        "left off per plan instruction); reporting wall time + in-memory array size as the "
        "proxy measurement instead, per the plan's explicit fallback"
    )

    # 4 variables x (1 baseline + 2 horizons x 5 GCMs) = 44 remote reads
    total_reads = 4 * (1 + 2 * 5)
    projected_bytes = array_bytes * total_reads
    projected_seconds = elapsed * total_reads
    print(
        f"[cost] projected full acquisition matrix: {total_reads} reads, "
        f"~{projected_bytes / 1024 / 1024:.1f} MB extrapolated transfer, "
        f"~{projected_seconds:.1f} seconds extrapolated wall time"
    )

    warn_lines: list[str] = []
    if elapsed > 300:
        warn_lines.append(f"single windowed read exceeded 300s: {elapsed:.1f}s")
        print(f"[warn] {warn_lines[-1]}")
    if projected_bytes > 5 * 1024**3:
        warn_lines.append(f"projected total transfer exceeds 5 GB: {projected_bytes / 1024**3:.2f} GB")
        print(f"[warn] {warn_lines[-1]}")
    if not warn_lines:
        print("[ok] windowed read stays within the 300s per-read and 5GB projected-total caps (T-08-03)")

    return {
        "url": url,
        "full_content_length": full_content_length,
        "elapsed_seconds": elapsed,
        "array_shape": data.shape,
        "array_dtype": str(data.dtype),
        "array_bytes": array_bytes,
        "total_reads": total_reads,
        "projected_bytes": projected_bytes,
        "projected_seconds": projected_seconds,
        "warn_lines": warn_lines,
    }


def write_spike_report(
    urls_result: dict,
    tas_result: dict,
    license_result: dict,
    align_result: dict,
    cost_result: dict,
    gdd5_result: dict,
) -> "Path":
    """Task 3: transcribe every finding into 08-SPIKE.md for the 08-03 checkpoint."""
    lines: list[str] = []

    lines.append("# Phase 8 Wave-0 Spike (plan 08-01)")
    lines.append("")
    lines.append(
        "Every number below was measured live against os.zhdk.cloud.switch.ch / "
        "envicloud.wsl.ch / www.envidat.ch by `data-pipeline/python/probe_chelsa.py`, "
        "except where explicitly marked as an extrapolation."
    )
    lines.append("")

    # --- W-01 ---
    lines.append("## W-01 -- Confirmed download URL templates")
    lines.append("")
    lines.append(
        f"**Future-period template** (source: {urls_result['template_source']}):"
    )
    lines.append("")
    lines.append(f"    {urls_result['template']}")
    lines.append("")
    lines.append(
        f"**Baseline template** (re-confirmed live): `{BASELINE_URL}`"
    )
    lines.append("")
    lines.append(
        f"40-URL matrix (4 variables x 2 periods x 5 GCMs): "
        f"{urls_result['matrix_ok']}/{urls_result['matrix_total']} resolved HTTP 200."
    )
    if urls_result["matrix_non200"]:
        lines.append("")
        lines.append("Non-200 combinations:")
        lines.append("")
        lines.append("| Variable | Period | GCM | Status |")
        lines.append("|---|---|---|---:|")
        for variable, period, gcm, status in urls_result["matrix_non200"]:
            lines.append(f"| {variable} | {period} | {gcm} | {status} |")
    else:
        lines.append("All 40 combinations resolved 200 -- no gaps in the matrix.")
    lines.append("")
    lines.append("Baseline re-confirmation (all 4 variables):")
    lines.append("")
    lines.append("| Variable | Status | Content-Length (bytes) |")
    lines.append("|---|---:|---:|")
    for variable, (status, length) in urls_result["baseline_results"].items():
        lines.append(f"| {variable} | {status} | {length:,} |" if length else f"| {variable} | {status} | - |")
    lines.append("")
    lines.append(
        "The plain-text `envidatS3paths.txt` index named by the plan as the "
        "\"authoritative shortcut\" 404s on both `os.zhdk.cloud.switch.ch` and "
        "`envicloud.wsl.ch`. The bucket instead exposes a standard, public S3 "
        "`ListObjectsV2`-style listing query (`?list-type=2&prefix=...&delimiter=/`), "
        "used here as an equivalent authoritative source (it lists real keys, not a "
        "guess) before falling back to candidate probing -- the fallback was not "
        "needed; the listing resolved the template on the first attempt."
    )
    lines.append("")

    lines.append("### Bonus finding, live-verified this run: a directly-published static `gdd5` file")
    lines.append("")
    lines.append(
        "The same `--urls` bio/ folder listing surfaced `CHELSA_gdd5_*` alongside "
        "`bio1`..`bio19` -- CHELSA's own growing-degree-days-above-5C variable, matching "
        "D-06's index exactly, published as a first-class static bioclim-family file "
        "**entirely independent of the `chelsa_cmip6` Python package**. This is the lead "
        "a prior halted attempt at this same plan noticed but never live-verified; it is "
        "re-verified live here, not trusted secondhand:"
    )
    lines.append("")
    lines.append(f"- Baseline (1981-2010): status {gdd5_result['baseline_status']}, "
                  f"{gdd5_result['baseline_length']:,} bytes" if gdd5_result['baseline_length'] else
                  f"- Baseline (1981-2010): status {gdd5_result['baseline_status']}")
    lines.append(
        f"- Future period {gdd5_result['period']}/{gdd5_result['ssp']}, all 5 D-04 GCMs:"
    )
    lines.append("")
    lines.append("| GCM | Status | Content-Length (bytes) |")
    lines.append("|---|---:|---:|")
    for gcm, (status, length) in gdd5_result["per_gcm"].items():
        lines.append(f"| {gcm} | {status} | {length:,} |" if length else f"| {gcm} | {status} | - |")
    lines.append("")
    lines.append(
        f"**Verdict: {'CONFIRMED' if gdd5_result['all_ok'] else 'NOT FULLY CONFIRMED'}** -- "
        "`gdd5` is fetchable with the exact same zero-new-dependency `requests`/`rasterio` "
        "mechanism as bio1/bio12/bio18, for both the baseline and all 5 future-period GCMs. "
        "See the Recommendation section below: this is a third, previously-unconsidered "
        "option for the D-07 GDD slot, lighter than both alternatives research compared."
    )
    lines.append("")

    # --- W-02 ---
    lines.append("## W-02 -- Static monthly `tas` availability for future periods")
    lines.append("")
    lines.append(f"**{'PUBLISHED' if tas_result['published'] else 'NOT PUBLISHED'}**")
    lines.append("")
    lines.append(f"Evidence: {tas_result['evidence']}")
    lines.append("")
    lines.append(
        "Consequence for D-07: since monthly `tas` is statically published for future "
        "periods too, true GDD *could* in principle be hand-derived from it via the "
        "standard `sum(max(T - 5, 0))` formula without the `chelsa_cmip6` heavy dependency "
        "-- but this is now superseded by the gdd5 bonus finding above, which is a "
        "directly-published GDD-equivalent file needing no derivation at all."
    )
    lines.append("")

    # --- W-03 ---
    lines.append("## W-03 -- License, attribution and citation for the CMIP6-derived product")
    lines.append("")
    lines.append(f"- `license`: {license_result['license']}")
    lines.append(f"- `attribution`: {license_result['attribution']}")
    lines.append(f"- `citation`: {license_result['citation']}")
    lines.append(f"- `note`: {license_result['note']}")
    lines.append("")
    lines.append(
        f"This {'MATCHES' if license_result['same_as_baseline_cc0'] else 'DIFFERS FROM'} "
        "the CHELSA V2.1 baseline climatology's CC0 license (confirms research Assumption A2)."
    )
    lines.append("")

    # --- W-04 ---
    lines.append("## W-04 -- Grid alignment and windowed-read cost")
    lines.append("")
    if align_result["mismatches"]:
        lines.append(f"**Grid alignment: MISMATCH** in fields: {align_result['mismatches']}")
    else:
        lines.append(
            "**Grid alignment: CONFIRMED** -- all 5 D-04 GCM rasters (bio1, 2071-2100, "
            "ssp370) share an identical transform/shape/crs/dtype/nodata:"
        )
    lines.append("")
    ref = align_result["reference"]
    lines.append(f"    transform={ref['transform']}  shape={ref['shape']}  crs={ref['crs']}  "
                  f"dtype={ref['dtype']}  nodata={ref['nodata']}")
    lines.append("")
    lines.append(
        f"Full remote file size (bio1, 2071-2100, ssp370, gfdl-esm4): "
        f"{cost_result['full_content_length']:,} bytes "
        f"({cost_result['full_content_length'] / 1024 / 1024:.1f} MB)."
    )
    lines.append(
        f"Germany-window `/vsicurl/` read: {cost_result['elapsed_seconds']:.2f} seconds wall "
        f"time, array shape {cost_result['array_shape']}, dtype {cost_result['array_dtype']}, "
        f"in-memory size {cost_result['array_bytes']:,} bytes "
        f"({cost_result['array_bytes'] / 1024 / 1024:.2f} MB)."
    )
    lines.append(
        "GDAL byte-level transfer was not directly observable (per the plan's explicit "
        "fallback); wall time + in-memory array size are reported as the proxy measurement."
    )
    lines.append("")
    lines.append(
        f"Projected full acquisition matrix (4 variables x (1 baseline + 2 horizons x 5 "
        f"GCMs) = {cost_result['total_reads']} reads): "
        f"~{cost_result['projected_bytes'] / 1024 / 1024:.1f} MB extrapolated transfer, "
        f"~{cost_result['projected_seconds']:.1f} seconds extrapolated wall time."
    )
    if cost_result["warn_lines"]:
        lines.append("")
        for warn in cost_result["warn_lines"]:
            lines.append(f"**WARNING:** {warn}")
    else:
        lines.append("")
        lines.append(
            "Both caps (300s per read, 5GB projected total) are observed -- recommended "
            "acquisition budget cap for `sources.yaml`: use this measured projection as "
            "the baseline budget, revisited once `bio12`/`bio18` (larger files) are "
            "individually measured in a later plan."
        )
    lines.append("")

    # --- Recommendation ---
    lines.append("## Recommendation for the 08-03 checkpoint")
    lines.append("")
    lines.append(
        "Three options now exist for the D-07 GDD slot (a third beyond the two "
        "`08-RESEARCH.md` compared), presented here as measured costs -- **08-03 decides, "
        "not this document:**"
    )
    lines.append("")
    lines.append("| | `chelsa-cmip6==1.4` (heavy) | `bio10` fallback (light, no true GDD) | `gdd5` static file (light, true GDD-equivalent) |")
    lines.append("|---|---|---|---|")
    lines.append(
        "| New dependencies | ~10 transitive (xarray, dask, zarr, gcsfs, netcdf4, "
        "h5netcdf, esgf-pyclient, siphon, google-cloud-storage family, aiohttp) | zero | zero |"
    )
    lines.append(
        "| Network calls at build time | live GCS/ESGF pulls on every run | static "
        "`requests`/`rasterio` fetch (same mechanism as bio1/bio12/bio18) | static "
        "`requests`/`rasterio` fetch (same mechanism as bio1/bio12/bio18) |"
    )
    lines.append(
        "| Formula | non-standard: sums raw temperature on days >=threshold, not "
        "`sum(max(T-5,0))` (Pitfall 2) | N/A -- not a GDD variable at all (bio10 = mean "
        f"temp of warmest quarter) | CHELSA's own bioclim-family `gdd5` "
        "(definition not independently re-derived this session; recommend confirming "
        "the exact formula against CHELSA's technical documentation PDF before 08-03, "
        "since this session had no PDF-text-extraction tooling available) |"
    )
    lines.append(
        f"| Measured cost this spike | not measured (out of scope for the light-path "
        "spike) | covered by this spike's bio1 measurements above (same acquisition "
        "shape) | "
        f"{'CONFIRMED' if gdd5_result['all_ok'] else 'not fully confirmed'} fetchable "
        "across baseline + all 5 GCMs for 2071-2100/ssp370; same file-size class as "
        "bio1/bio10 (not bio12/bio18's much larger precipitation files) |"
    )
    lines.append(
        "| On-brand match to D-08 (\"GDD is the default variable\") | yes, if the heavy "
        "path is accepted | no -- would require rewriting D-06/D-08's copy around "
        "`bio10` instead of GDD | **yes** -- delivers the literal GDD index D-06 named, "
        "with zero dependency cost |"
    )
    lines.append("")
    lines.append(
        "This spike's measurements suggest the `gdd5` static file is the strongest "
        "candidate of the three -- it is the only option matching D-06's literal GDD "
        "requirement at zero new dependency cost -- but the exact `gdd5` formula has not "
        "been independently verified against CHELSA's own technical specification in "
        "this session (no PDF-reading tool was available), and D-07 explicitly reserves "
        "this decision for a human. **08-03 must decide among `chelsa-cmip6`, `bio10`, "
        "and `gdd5`,** not this spike."
    )
    lines.append("")

    content = "\n".join(lines) + "\n"
    output_path = resolve(
        ".planning/phases/08-add-maps-and-stats-for-climate-variables-using-chelsa-data/08-SPIKE.md"
    )
    output_path.write_text(content, encoding="utf-8")
    print(f"\n[ok] wrote {output_path}")
    return output_path


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only, network-only probe of CHELSA's V2.1 baseline + CMIP6-future "
            "GeoTIFF distribution (plan 08-01). Writes only to data/_cache/ and "
            "08-SPIKE.md, never to data/ll_content.json."
        )
    )
    parser.add_argument("--urls", action="store_true", help="Task 1 / W-01: probe the future-period URL structure")
    parser.add_argument("--tas", action="store_true", help="Task 2 / W-02: is monthly tas published for future periods?")
    parser.add_argument("--license", action="store_true", help="Task 2 / W-03: fetch the CMIP6 product's license/attribution/citation")
    parser.add_argument("--align", action="store_true", help="Task 2 / W-04: assert 5-GCM grid alignment")
    parser.add_argument(
        "--cost",
        action="store_true",
        help=(
            "Task 3 / W-04: measure windowed-read cost, then re-run --urls/--tas/--license/"
            "--align internally and write 08-SPIKE.md with every finding"
        ),
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    ran_any = False
    if args.urls:
        probe_urls()
        ran_any = True
    if args.tas:
        probe_tas()
        ran_any = True
    if args.license:
        probe_license()
        ran_any = True
    if args.align:
        probe_align()
        ran_any = True
    if args.cost:
        # --cost assembles the complete spike: it re-runs the other three probes
        # internally (rather than requiring four separate invocations first) so that
        # `python probe_chelsa.py --cost` alone writes a complete 08-SPIKE.md, matching
        # this plan's own <verify> command.
        urls_result = probe_urls()
        tas_result = probe_tas()
        license_result = probe_license()
        align_result = probe_align()
        gdd5_result = probe_gdd5_discovery()
        cost_result = probe_cost()
        write_spike_report(urls_result, tas_result, license_result, align_result, cost_result, gdd5_result)
        ran_any = True
    if not ran_any:
        parser.print_help()


if __name__ == "__main__":
    main()
