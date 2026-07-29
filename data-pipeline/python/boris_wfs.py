from __future__ import annotations

"""Shared BORIS-BB/BORIS-HE WFS transport for probe_boris.py and fetch_boris.py."""

import re
import tempfile
import time
from pathlib import Path

import geopandas as gpd
import requests

USER_AGENT = "ll-explorer-pipeline/1.0 (+https://zalf.de)"
GEOMETRY_PROPERTY = "adv:position"
ADV_NS = "http://www.adv-online.de/namespaces/adv/gid/7.1"
STATE_NS = {
    "bb": {
        "prefix": "br",
        "uri": "http://www.adv-online.de/namespaces/adv/br/3.0",
    },
    "he": {
        "prefix": "boris",
        "uri": "http://www.adv-online.de/namespaces/adv/brm/2.1",
    },
}

WFS_NS = "http://www.opengis.net/wfs/2.0"
FES_NS = "http://www.opengis.net/fes/2.0"
GML_NS = "http://www.opengis.net/gml/3.2"
XLINK_NS = "http://www.w3.org/1999/xlink"
OID_RE = re.compile(r"^[A-Za-z0-9]+$")


def crs_urn(epsg_code) -> str:
    """Return the BORIS-required EPSG CRS URN with the mandatory double colon."""
    return f"urn:ogc:def:crs:EPSG::{int(epsg_code)}"


def polygon_to_gml(polygon, gml_id, srs_name) -> str:
    """Render a Polygon exterior ring as the GML filter geometry BORIS accepts."""
    pos_list = " ".join(f"{x:.3f} {y:.3f}" for x, y in polygon.exterior.coords)
    return (
        f'<gml:Polygon gml:id="{gml_id}" srsName="{srs_name}">'
        "<gml:exterior>"
        "<gml:LinearRing>"
        f"<gml:posList>{pos_list}</gml:posList>"
        "</gml:LinearRing>"
        "</gml:exterior>"
        "</gml:Polygon>"
    )


def geometry_to_multisurface(geom, srs_name, gml_id="ms1") -> str:
    """Wrap Polygon or MultiPolygon geometry parts in a GML MultiSurface."""
    parts = geom.geoms if hasattr(geom, "geoms") else [geom]
    members = "".join(
        f"<gml:surfaceMember>{polygon_to_gml(part, f'p{index}', srs_name)}</gml:surfaceMember>"
        for index, part in enumerate(parts)
    )
    return (
        f'<gml:MultiSurface gml:id="{gml_id}" srsName="{srs_name}">'
        f"{members}"
        "</gml:MultiSurface>"
    )


def build_intersects_body(
    state,
    typename,
    geom_native,
    epsg_code,
    count,
    startindex=None,
    result_type=None,
    geometry_property=GEOMETRY_PROPERTY,
) -> str:
    """Build a WFS 2.0 GetFeature POST body with a fes:Intersects filter."""
    if state not in STATE_NS:
        raise ValueError(f"Unknown BORIS state key: {state}")

    ns = STATE_NS[state]
    state_prefix = ns["prefix"]
    srs_name = crs_urn(epsg_code)
    multisurface = geometry_to_multisurface(geom_native, srs_name)
    optional_attrs = ""
    if startindex is not None:
        optional_attrs += f' startIndex="{startindex}"'
    if result_type == "hits":
        optional_attrs += ' resultType="hits"'

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<wfs:GetFeature service="WFS" version="2.0.0" count="{count}"{optional_attrs}\n'
        f'  xmlns:wfs="{WFS_NS}" xmlns:fes="{FES_NS}"\n'
        f'  xmlns:gml="{GML_NS}"\n'
        f'  xmlns:adv="{ADV_NS}"\n'
        f'  xmlns:{state_prefix}="{ns["uri"]}">\n'
        f'  <wfs:Query typeNames="{typename}">\n'
        "    <fes:Filter><fes:Intersects>\n"
        f"      <fes:ValueReference>{geometry_property}</fes:ValueReference>\n"
        f"      {multisurface}\n"
        "    </fes:Intersects></fes:Filter>\n"
        "  </wfs:Query>\n"
        "</wfs:GetFeature>"
    )


def build_gehoert_zu_filter_body(oid, count=10) -> str:
    """Build the Brandenburg value-record lookup body for a referenced zone OID."""
    if not OID_RE.fullmatch(oid):
        raise ValueError(f"Invalid BORIS OID for XML interpolation: {oid}")

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<wfs:GetFeature service="WFS" version="2.0.0" count="{count}"\n'
        f'  xmlns:wfs="{WFS_NS}" xmlns:fes="{FES_NS}"\n'
        f'  xmlns:gml="{GML_NS}"\n'
        f'  xmlns:adv="{ADV_NS}"\n'
        f'  xmlns:xlink="{XLINK_NS}"\n'
        f'  xmlns:br="{STATE_NS["bb"]["uri"]}">\n'
        '  <wfs:Query typeNames="br:BR_Bodenrichtwert">\n'
        "    <fes:Filter><fes:PropertyIsEqualTo>\n"
        "      <fes:ValueReference>br:gehoertZu/@xlink:href</fes:ValueReference>\n"
        f"      <fes:Literal>urn:adv:oid:{oid}</fes:Literal>\n"
        "    </fes:PropertyIsEqualTo></fes:Filter>\n"
        "  </wfs:Query>\n"
        "</wfs:GetFeature>"
    )


def http_get(url, params, max_bytes, timeout=300, retries=4) -> bytes:
    """Fetch a WFS URL with retry/backoff and a hard response-size ceiling."""
    for attempt in range(retries):
        try:
            r = requests.get(
                url,
                params=params,
                headers={"User-Agent": USER_AGENT},
                timeout=timeout,
            )
            if r.status_code == 403 and attempt < retries - 1:
                wait = 2**attempt
                print(f"  [retry {attempt+1}/{retries-1} in {wait}s] WFS returned 403")
                time.sleep(wait)
                continue
            r.raise_for_status()
            if len(r.content) > max_bytes:
                raise RuntimeError(
                    f"Response size {len(r.content)} bytes exceeds max_bytes {max_bytes}"
                )
            return r.content
        except requests.RequestException as exc:
            if attempt == retries - 1:
                raise RuntimeError(
                    f"Failed to fetch {url} after {retries} attempts. "
                    "A sustained 403 may be server-side WAF blocking; report and retry later."
                ) from exc
            wait = 2**attempt
            print(f"  [retry {attempt+1}/{retries-1} in {wait}s] {exc.__class__.__name__}")
            time.sleep(wait)
    raise RuntimeError(f"Failed to fetch {url} after {retries} attempts")


def http_post(url, body, max_bytes, timeout=300, retries=4) -> bytes:
    """POST a WFS body with retry/backoff and a hard response-size ceiling."""
    for attempt in range(retries):
        try:
            r = requests.post(
                url,
                data=body.encode("utf-8"),
                headers={"Content-Type": "application/xml", "User-Agent": USER_AGENT},
                timeout=timeout,
            )
            if r.status_code == 403 and attempt < retries - 1:
                wait = 2**attempt
                print(f"  [retry {attempt+1}/{retries-1} in {wait}s] WFS returned 403")
                time.sleep(wait)
                continue
            r.raise_for_status()
            if len(r.content) > max_bytes:
                raise RuntimeError(
                    f"Response size {len(r.content)} bytes exceeds max_bytes {max_bytes}"
                )
            return r.content
        except requests.RequestException as exc:
            if attempt == retries - 1:
                raise RuntimeError(
                    f"Failed to post to {url} after {retries} attempts. "
                    "A sustained 403 may be server-side WAF blocking; report and retry later."
                ) from exc
            wait = 2**attempt
            print(f"  [retry {attempt+1}/{retries-1} in {wait}s] {exc.__class__.__name__}")
            time.sleep(wait)
    raise RuntimeError(f"Failed to post to {url} after {retries} attempts")


def _extract_quoted(raw: bytes, marker: bytes) -> bytes:
    if marker not in raw:
        raise RuntimeError(f"Missing WFS count marker {marker.decode('ascii')}")
    return raw.split(marker, 1)[1].split(b'"', 1)[0]


def extract_counts(raw) -> tuple[int, int]:
    """Extract numberMatched/numberReturned using byte slicing only."""
    matched_bytes = _extract_quoted(raw, b'numberMatched="')
    returned_bytes = _extract_quoted(raw, b'numberReturned="')
    matched = -1 if matched_bytes == b"unknown" else int(matched_bytes)
    returned = int(returned_bytes)
    return matched, returned


def read_gml_frame(raw, expected_crs, label):
    """Read a GML response with GDAL, validate native CRS, and repair geometry."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"{label}.gml"
        path.write_bytes(raw)
        frame = gpd.read_file(path)

    if str(frame.crs) != expected_crs:
        raise RuntimeError(f"{label}: expected CRS {expected_crs}, got {frame.crs}")

    frame.geometry = frame.geometry.make_valid()
    return frame


def parse_property_values(raw, local_name) -> list[str]:
    """Extract distinct property values from a WFS ValueCollection by regex.

    Tries a nested-element-or-href match first (`<ns:{local_name}>v</...>` or an
    `xlink:href="..."` attribute on that element). If neither matches, falls back
    to bare `<wfs:member>v</wfs:member>` text — verified live against BORIS-HE's
    GetPropertyValue response, which returns the selected property as plain text
    directly inside `wfs:member` with no nested element carrying the property name.
    """
    text = raw.decode("utf-8", errors="replace")
    escaped_name = re.escape(local_name)
    value_pattern = re.compile(
        rf"<[A-Za-z0-9_]+:{escaped_name}>([^<]*)</",
        flags=re.MULTILINE,
    )
    href_pattern = re.compile(
        rf'<[A-Za-z0-9_]+:{escaped_name}[^>]*xlink:href="([^"]*)"',
        flags=re.MULTILINE,
    )
    member_pattern = re.compile(
        r"<wfs:member>([^<]*)</wfs:member>",
        flags=re.MULTILINE,
    )

    values: list[str] = []
    seen: set[str] = set()
    for match in re.finditer(
        rf'{value_pattern.pattern}|{href_pattern.pattern}',
        text,
        flags=re.MULTILINE,
    ):
        value = next(group for group in match.groups() if group is not None)
        if value not in seen:
            seen.add(value)
            values.append(value)

    if not values:
        for match in member_pattern.finditer(text):
            value = match.group(1)
            if value not in seen:
                seen.add(value)
                values.append(value)

    return values
