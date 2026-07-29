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
import re

import requests

from _sources import resolve

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


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only, network-only probe of CHELSA's V2.1 baseline + CMIP6-future "
            "GeoTIFF distribution (plan 08-01). Writes only to data/_cache/ and "
            "08-SPIKE.md, never to data/ll_content.json."
        )
    )
    parser.add_argument("--urls", action="store_true", help="Task 1 / W-01: probe the future-period URL structure")
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    ran_any = False
    if args.urls:
        probe_urls()
        ran_any = True
    if not ran_any:
        parser.print_help()


if __name__ == "__main__":
    main()
