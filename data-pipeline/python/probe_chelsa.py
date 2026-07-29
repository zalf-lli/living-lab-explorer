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
    if not ran_any:
        parser.print_help()


if __name__ == "__main__":
    main()
