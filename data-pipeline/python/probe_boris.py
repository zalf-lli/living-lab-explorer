from __future__ import annotations

"""Read-only diagnostic CLI for the Wave-0 BORIS spike (plan 07-03).

This script answers, with live measurements, the three questions 07-RESEARCH.md
flagged as blocking before any production BORIS fetch is written:
  - W-01: committed-file volume under a grid of trimming/precision/simplification settings
  - W-02: the has_current_value recency threshold for Brandenburg's Stichtag mix
  - W-03: the actual Hessen nutzung.art / entwicklungszustand code sets

It never writes into `data/geojson/` or `app/public/`. Every artefact lands in
`data/_cache/boris/` (gitignored via the existing `data/_cache/` rule) or in
`07-SPIKE.md`.
"""

import argparse
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

import geopandas as gpd
import pandas as pd

from _sources import resolve
from boris_wfs import (
    ADV_NS,
    FES_NS,
    GEOMETRY_PROPERTY,
    GML_NS,
    STATE_NS,
    WFS_NS,
    build_intersects_body,
    crs_urn,
    extract_counts,
    geometry_to_multisurface,
    http_get,
    http_post,
    read_gml_frame,
)

# --- Probe-only endpoint constants (production values move into sources.yaml in plan 07-06) ---
BB_URL = "https://isk.geobasis-bb.de/ows/boris_wfs"
HE_URL = "https://www.gds.hessen.de/wfs2/boris/cgi-bin/brw/2024/wfs"
BB_EPSG = 25833
HE_EPSG = 25832
BB_ZONE_TYPENAME = "br:BR_BodenrichtwertFlaeche"
BB_VALUE_TYPENAME = "br:BR_Bodenrichtwert"
HE_ZONE_TYPENAME = "boris:BR_BodenrichtwertZonal"

LL_STATES = {
    "rheingau": "he",
    "north-hessian-loess": "he",
    "hessian-low-mountain": "he",
    "havellandisches-luch": "bb",
    "east-brandenburg": "bb",
}

# 200 MiB: deliberately above the ~130 MB statewide BB point fetch total and the
# 12.96 MB single-LL GML measured for rheingau (07-RESEARCH.md section 5.2).
MAX_RESPONSE_BYTES = 209715200

EXPECTED_ENTWICKLUNGSZUSTAND_HE = {"B", "R", "E", "LF", "SF"}

# GDI-DE national codelist `de.adv-online.gid/BR_Art_Nutzung`, enumerated live and
# recorded in 07-RESEARCH.md section 3.1. Note: the research doc's prose calls this
# "44 entries", but the actual table it recorded has 42 distinct codes (verified by
# counting the table rows in this repo's copy) -- this probe treats the 42 codes
# actually enumerated in the table as ground truth for the UNMAPPABLE/UNEXPECTED
# check, not the "44" figure in the prose.
BB_ART_NUTZUNG_CODES = {
    "1100", "1110", "1120", "1130", "1140", "1200", "1210", "1220", "1230", "1240",
    "1250", "1300", "1310", "1320", "1400", "1410", "1420", "1500", "2000", "2100",
    "2200", "2300", "2400", "2500", "2600", "2700", "2800", "3010", "3020", "3030",
    "3040", "3050", "3060", "3070", "3080", "3090", "3100", "3110", "3120", "3130",
    "3140", "9998",
}

# code -> (BB's own parenthetical abbreviation, German label), from the same
# 07-RESEARCH.md section 3.1 table. Used only to PROPOSE a W-03 canonical target for
# each observed HE code by exact abbreviation match; this is evidence for the 07-05
# checkpoint, not a locked decision.
BB_ART_NUTZUNG_TABLE = {
    "1100": ("W", "Wohnbauflaeche"),
    "1110": ("WS", "Kleinsiedlungsgebiet"),
    "1120": ("WR", "reines Wohngebiet"),
    "1130": ("WA", "allgemeines Wohngebiet"),
    "1140": ("WB", "besonderes Wohngebiet"),
    "1200": ("M", "gemischte Baufl."),
    "1210": ("MD", "Dorfgebiet"),
    "1220": ("MDW", "Doerfliches Wohngebiet"),
    "1230": ("MI", "Mischgebiet"),
    "1240": ("MK", "Kerngebiet"),
    "1250": ("MU", "Urbanes Gebiet"),
    "1300": ("G", "gewerbliche Baufl."),
    "1310": ("GE", "Gewerbegebiet"),
    "1320": ("GI", "Industriegebiet"),
    "1400": ("S", "Sonderbaufl."),
    "1410": ("SE", "Sondergebiet fuer Erholung"),
    "1420": ("SO", "sonstige Sondergebiete"),
    "1500": ("GB", "Baufl. fuer Gemeinbedarf"),
    "2000": ("L", "landwirtschaftliche Fl."),
    "2100": ("A", "Acker"),
    "2200": ("GR", "Gruenland"),
    "2300": ("EGA", "Erwerbsgartenbaufl."),
    "2400": ("SK", "Anbaufl. f. Sonderkulturen"),
    "2500": ("WG", "Weingarten"),
    "2600": ("KUP", "Kurzumtriebsplantagen, Agroforst"),
    "2700": ("UN", "Unland, Geringstland, Bergweide, Moor"),
    "2800": ("F", "forstwirtschaftliche Fl."),
    "3010": ("PG", "private Gruenfl."),
    "3020": ("KGA", "Kleingartenfl."),
    "3030": ("FGA", "Freizeitgartenfl."),
    "3040": ("CA", "Campingplatz"),
    "3050": ("SPO", "Sportfl."),
    "3060": ("SG", "sonstige private Fl."),
    "3070": ("FH", "Friedhof"),
    "3080": ("WF", "Wasserfl."),
    "3090": ("FP", "Flughafen, Flugplaetze"),
    "3100": ("PP", "private Parkplaetze"),
    "3110": ("LG", "Lagerfl."),
    "3120": ("AB", "Abbauland"),
    "3130": ("GF", "Gemeinbedarfsfl., kein Bauland"),
    "3140": ("SN", "Sondernutzungsfl."),
    "9998": (None, "Nach Quellenlage nicht zu spezifizieren"),
}
BB_ABBREVIATION_TO_CODE = {
    abbrev: code for code, (abbrev, _label) in BB_ART_NUTZUNG_TABLE.items() if abbrev
}


def cache_dir() -> Path:
    path = resolve("data/_cache/boris")
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_boundaries() -> gpd.GeoDataFrame:
    """Read data/ll_boundaries.geojson and assert the shape probe_boris depends on."""
    boundaries = gpd.read_file(resolve("data/ll_boundaries.geojson"))
    assert "ll_slug" in boundaries.columns, "ll_boundaries.geojson missing ll_slug column"
    assert boundaries.crs is not None and str(boundaries.crs) == "EPSG:4326", (
        "ll_boundaries.geojson must have EPSG:4326 CRS"
    )
    return boundaries


def _geom_for_slug(boundaries: gpd.GeoDataFrame, slug: str):
    matches = boundaries.loc[boundaries["ll_slug"] == slug, "geometry"]
    if matches.empty:
        raise RuntimeError(f"Living Lab slug {slug!r} not found in ll_boundaries.geojson")
    return matches.iloc[0]


def fetch_zones(slug: str, geom_wgs84, state: str, refresh: bool) -> gpd.GeoDataFrame:
    """Fetch every zone polygon intersecting an LL boundary for one state, paged and cached.

    Returns a GeoDataFrame reprojected to EPSG:4326. Raises RuntimeError if the
    concatenated feature count does not match the server-reported numberMatched.
    """
    if state not in STATE_NS:
        raise ValueError(f"Unknown BORIS state key: {state}")

    epsg = BB_EPSG if state == "bb" else HE_EPSG
    typename = BB_ZONE_TYPENAME if state == "bb" else HE_ZONE_TYPENAME
    url = BB_URL if state == "bb" else HE_URL

    geom_native = gpd.GeoSeries([geom_wgs84], crs="EPSG:4326").to_crs(epsg).iloc[0]

    page_count = 5000
    pages: list[gpd.GeoDataFrame] = []
    page_num = 0
    startindex = 0
    matched = None
    total_returned = 0
    cdir = cache_dir()

    while True:
        cache_path = cdir / f"zones__{slug}__p{page_num}.gml"
        if cache_path.exists() and not refresh:
            raw = cache_path.read_bytes()
        else:
            body = build_intersects_body(
                state, typename, geom_native, epsg, count=page_count, startindex=startindex
            )
            raw = http_post(url, body, MAX_RESPONSE_BYTES)
            cache_path.write_bytes(raw)

        page_matched, page_returned = extract_counts(raw)
        if matched is None:
            # -1 means the server reported numberMatched="unknown" (verified live
            # against BORIS-HE's GetFeature response for this typename); paging
            # then terminates on a short page instead of a running-total check.
            matched = page_matched

        frame = read_gml_frame(raw, f"EPSG:{epsg}", f"zones__{slug}__p{page_num}")
        pages.append(frame)

        total_returned += page_returned
        page_num += 1
        startindex += page_returned

        if page_returned == 0:
            break
        if matched != -1 and total_returned >= matched:
            break
        if page_returned < page_count:
            break

    if not pages:
        raise RuntimeError(f"No zone pages fetched for {slug} ({state})")

    combined = gpd.GeoDataFrame(pd.concat(pages, ignore_index=True), crs=f"EPSG:{epsg}")
    combined = combined.to_crs("EPSG:4326")

    if matched != -1:
        if len(combined) != matched:
            raise RuntimeError(
                f"Zone count mismatch for {slug} ({state}): concatenated {len(combined)} "
                f"features, server reported numberMatched={matched}"
            )
    else:
        print(
            f"  [note] {slug} ({state}): server reported numberMatched=unknown; using the "
            f"paged total ({len(combined)} features, summed numberReturned={total_returned}) "
            "as the measured count"
        )
        if len(combined) != total_returned:
            raise RuntimeError(
                f"Zone count mismatch for {slug} ({state}): concatenated {len(combined)} "
                f"features but paged numberReturned summed to {total_returned}"
            )

    return combined


def _count_property_occurrences(raw: bytes, local_name: str) -> Counter:
    """Count every occurrence (not deduplicated) of a GetPropertyValue result.

    Mirrors boris_wfs.parse_property_values's regex shape but preserves per-feature
    occurrence counts instead of collapsing to distinct values, since the he-codes
    probe reports raw_code -> occurrence count. Falls back to bare
    `<wfs:member>value</wfs:member>` text when no nested element matches the
    requested local_name — verified live against BORIS-HE, which returns
    GetPropertyValue results as plain member text with no nested element.
    """
    import re

    text = raw.decode("utf-8", errors="replace")
    escaped_name = re.escape(local_name)
    value_pattern = re.compile(rf"<[A-Za-z0-9_]+:{escaped_name}>([^<]*)</", flags=re.MULTILINE)
    href_pattern = re.compile(
        rf'<[A-Za-z0-9_]+:{escaped_name}[^>]*xlink:href="([^"]*)"', flags=re.MULTILINE
    )
    counter: Counter = Counter()
    for match in re.finditer(
        rf"{value_pattern.pattern}|{href_pattern.pattern}", text, flags=re.MULTILINE
    ):
        value = next(group for group in match.groups() if group is not None)
        counter[value] += 1

    if not counter:
        member_pattern = re.compile(r"<wfs:member>([^<]*)</wfs:member>", flags=re.MULTILINE)
        for match in member_pattern.finditer(text):
            counter[match.group(1)] += 1

    return counter


def _find_column(frame: gpd.GeoDataFrame, keyword: str) -> str | None:
    """Find a GML-derived column name matching keyword: exact match, then suffix, then substring.

    Prefers an exact (case-insensitive) match first. This matters concretely for
    HE's zone schema, which carries both a plain `art` column (nutzung.art) and an
    unrelated `bodenrichtwertArt` column -- a suffix-only match would have picked
    `bodenrichtwertArt` before `art` depending on column order, silently returning
    the wrong field.
    """
    keyword_lower = keyword.lower()
    candidates = [c for c in frame.columns if keyword_lower in c.lower()]
    if not candidates:
        return None
    exact = [c for c in candidates if c.lower() == keyword_lower]
    if exact:
        return exact[0]
    exact_suffix = [c for c in candidates if c.lower().endswith(keyword_lower)]
    return exact_suffix[0] if exact_suffix else candidates[0]


def _build_property_value_intersects_body(
    state: str, typename: str, value_reference: str, geom_native, epsg_code, count
) -> str:
    """Build a WFS 2.0 GetPropertyValue POST body scoped by a fes:Intersects filter.

    Deviation from the plan's literal wording (a plain GetPropertyValue GET with no
    spatial component): a live probe confirmed the unscoped GET returns the same
    statewide sample regardless of which Living Lab is being probed (identical
    counts across all three Hessen LLs), which defeats the whole point of a
    per-LL vocabulary census. This mirrors boris_wfs.build_intersects_body's
    GetFeature shape but for the GetPropertyValue operation, whose root element
    additionally carries a `valueReference` attribute (WFS 2.0 SS11.3).
    """
    if state not in STATE_NS:
        raise ValueError(f"Unknown BORIS state key: {state}")

    ns = STATE_NS[state]
    state_prefix = ns["prefix"]
    srs_name = crs_urn(epsg_code)
    multisurface = geometry_to_multisurface(geom_native, srs_name)

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<wfs:GetPropertyValue service="WFS" version="2.0.0" count="{count}" '
        f'valueReference="{value_reference}"\n'
        f'  xmlns:wfs="{WFS_NS}" xmlns:fes="{FES_NS}"\n'
        f'  xmlns:gml="{GML_NS}"\n'
        f'  xmlns:adv="{ADV_NS}"\n'
        f'  xmlns:{state_prefix}="{ns["uri"]}">\n'
        f'  <wfs:Query typeNames="{typename}">\n'
        "    <fes:Filter><fes:Intersects>\n"
        f"      <fes:ValueReference>{GEOMETRY_PROPERTY}</fes:ValueReference>\n"
        f"      {multisurface}\n"
        "    </fes:Intersects></fes:Filter>\n"
        "  </wfs:Query>\n"
        "</wfs:GetPropertyValue>"
    )


def _sample_he_property(
    slug: str, value_reference: str, local_name: str, boundaries: gpd.GeoDataFrame, refresh: bool
) -> tuple[Counter, str]:
    """Sample one HE property's distinct values via a spatially-scoped GetPropertyValue,
    with a fetch_zones fallback.

    Returns (Counter of raw_code -> occurrence count, provenance label).
    """
    cdir = cache_dir()
    cache_path = cdir / f"he_propval__{slug}__{local_name}.xml"

    status_ok = True
    if cache_path.exists() and not refresh:
        raw = cache_path.read_bytes()
    else:
        geom_wgs84 = _geom_for_slug(boundaries, slug)
        geom_native = gpd.GeoSeries([geom_wgs84], crs="EPSG:4326").to_crs(HE_EPSG).iloc[0]
        body = _build_property_value_intersects_body(
            "he", HE_ZONE_TYPENAME, value_reference, geom_native, HE_EPSG, count=10000
        )
        try:
            raw = http_post(HE_URL, body, MAX_RESPONSE_BYTES)
        except RuntimeError as exc:
            print(f"  [warn] GetPropertyValue request failed for {slug}/{local_name}: {exc}")
            raw = b""
            status_ok = False
        if status_ok:
            cache_path.write_bytes(raw)

    is_exception = b"ExceptionReport" in raw
    counts = _count_property_occurrences(raw, local_name) if raw else Counter()

    if not status_ok or is_exception or not counts:
        if is_exception:
            print(
                f"  [warn] {slug}/{local_name}: OGC ExceptionReport in GetPropertyValue "
                "response, falling back to fetch_zones"
            )
        elif not counts and status_ok:
            print(
                f"  [warn] {slug}/{local_name}: empty value list from GetPropertyValue, "
                "falling back to fetch_zones"
            )
        geom = _geom_for_slug(boundaries, slug)
        frame = fetch_zones(slug, geom, "he", refresh)
        column = _find_column(frame, local_name)
        if column is None:
            raise RuntimeError(
                f"Could not locate a column matching '{local_name}' in the fetch_zones "
                f"fallback frame for {slug}; columns were: {list(frame.columns)}"
            )
        counts = Counter(str(v) for v in frame[column].dropna())
        return counts, "fallback:fetch_zones"

    return counts, "GetPropertyValue"


def probe_he_codes(refresh: bool, ll_filter: str | None = None) -> dict:
    """Task 1: enumerate the Hessen nutzung.art and entwicklungszustand vocabularies."""
    boundaries = load_boundaries()
    he_slugs = [slug for slug, state in LL_STATES.items() if state == "he"]
    if ll_filter:
        he_slugs = [s for s in he_slugs if s == ll_filter]
        if not he_slugs:
            raise RuntimeError(f"--ll {ll_filter!r} is not a Hessen Living Lab")

    per_ll: dict[str, dict] = {}
    for slug in he_slugs:
        print(f"\n[he-codes] {slug}")
        art_counts, art_source = _sample_he_property(
            slug, "boris:nutzung/boris:BR_Nutzung/boris:art", "art", boundaries, refresh
        )
        ez_counts, ez_source = _sample_he_property(
            slug, "boris:entwicklungszustand", "entwicklungszustand", boundaries, refresh
        )
        per_ll[slug] = {
            "art": art_counts,
            "art_source": art_source,
            "entwicklungszustand": ez_counts,
            "ez_source": ez_source,
        }

        print(f"  nutzung.art (source: {art_source}):")
        for code, count in art_counts.most_common():
            print(f"    {code}: {count}  [source: {art_source}]")

        print(f"  entwicklungszustand (source: {ez_source}):")
        for code, count in ez_counts.most_common():
            flag = "" if code in EXPECTED_ENTWICKLUNGSZUSTAND_HE else " UNEXPECTED"
            print(f"    {code}: {count}  [source: {ez_source}]{flag}")

    union_art: Counter = Counter()
    union_ez: Counter = Counter()
    for data in per_ll.values():
        union_art.update(data["art"])
        union_ez.update(data["entwicklungszustand"])

    print("\n[he-codes] UNION across Hessen Living Labs")
    print("  nutzung.art:")
    for code, count in union_art.most_common():
        print(f"    {code}: {count}")

    print("  entwicklungszustand:")
    unexpected = []
    for code, count in union_ez.most_common():
        if code in EXPECTED_ENTWICKLUNGSZUSTAND_HE:
            print(f"    {code}: {count}")
        else:
            unexpected.append(code)
    if unexpected:
        print("  UNEXPECTED entwicklungszustand codes (outside {B, R, E, LF, SF}):")
        for code in unexpected:
            print(f"    {code}: {union_ez[code]}")
    else:
        print("  (no UNEXPECTED entwicklungszustand codes observed)")

    return {"per_ll": per_ll, "union_art": union_art, "union_entwicklungszustand": union_ez}


_BB_POINT_RECORD_RE = re.compile(
    r'<br:BR_Bodenrichtwert gml:id="([^"]+)">(.*?)</br:BR_Bodenrichtwert>', flags=re.DOTALL
)
_BB_SIMPLE_FIELD_RES = {
    "bodenrichtwert": re.compile(r"<br:bodenrichtwert>([^<]*)</br:bodenrichtwert>"),
    "stichtag": re.compile(r"<br:stichtag>([^<]*)</br:stichtag>"),
    "bodenrichtwertNummer": re.compile(
        r"<br:bodenrichtwertNummer>([^<]*)</br:bodenrichtwertNummer>"
    ),
    "entwicklungszustand": re.compile(
        r"<br:entwicklungszustand>([^<]*)</br:entwicklungszustand>"
    ),
}
_BB_ART_HREF_RE = re.compile(r'<br:art xlink:href="([^"]*)"')
_BB_GEHOERT_ZU_RE = re.compile(r'<br:gehoertZu xlink:href="urn:adv:oid:([^"]*)"')


def _parse_bb_point_records(raw: bytes) -> list[dict]:
    """Regex-parse br:BR_Bodenrichtwert records into flat dicts, keyed by gehoertZu.

    Deviation from the plan's literal wording (`gpd.read_file()` then extract
    fields): a live probe confirmed GDAL's GML driver drops href-only reference
    elements (`br:gehoertZu`, `br:art`) entirely from the flattened attribute
    table it returns via `gpd.read_file()` -- there is no column to extract them
    from. Since `gehoertZu` is the entire join key this feature type exists for,
    this is a Rule 1 correctness fix: every field is instead extracted directly
    from the raw GML text via regex, matching the parser-free extraction pattern
    boris_wfs.py already uses for numberMatched/numberReturned and property
    values (T-07-01's mitigation: no XML parser is imported).
    """
    text = raw.decode("utf-8", errors="replace")
    records: list[dict] = []
    for gml_id, block in _BB_POINT_RECORD_RE.findall(text):
        record: dict = {"gml_id": gml_id}
        for field, pattern in _BB_SIMPLE_FIELD_RES.items():
            match = pattern.search(block)
            record[field] = match.group(1) if match else None

        if record["bodenrichtwert"] is not None:
            try:
                record["bodenrichtwert"] = float(record["bodenrichtwert"])
            except ValueError:
                record["bodenrichtwert"] = None

        art_match = _BB_ART_HREF_RE.search(block)
        record["nutzung_art"] = art_match.group(1).rsplit("/", 1)[-1] if art_match else None

        gehoert_match = _BB_GEHOERT_ZU_RE.search(block)
        record["gehoertZu"] = gehoert_match.group(1) if gehoert_match else None

        records.append(record)
    return records


def _fetch_bb_point_pages(refresh: bool) -> tuple[list[bytes], int | None, int]:
    """Page br:BR_Bodenrichtwert statewide (no BBOX/spatial filter) with on-disk caching."""
    cdir = cache_dir()
    page_count = 5000
    page_num = 0
    startindex = 0
    matched: int | None = None
    total_returned = 0
    pages_raw: list[bytes] = []

    while True:
        cache_path = cdir / f"bb_points__p{page_num:03d}.gml"
        if cache_path.exists() and not refresh:
            raw = cache_path.read_bytes()
        else:
            params = {
                "SERVICE": "WFS",
                "VERSION": "2.0.0",
                "REQUEST": "GetFeature",
                "TYPENAMES": BB_VALUE_TYPENAME,
                "COUNT": page_count,
                "STARTINDEX": startindex,
            }
            raw = http_get(BB_URL, params, MAX_RESPONSE_BYTES)
            cache_path.write_bytes(raw)

        page_matched, page_returned = extract_counts(raw)
        if matched is None:
            matched = page_matched

        pages_raw.append(raw)
        total_returned += page_returned
        page_num += 1
        startindex += page_returned

        if page_returned == 0:
            if matched != -1 and total_returned < matched:
                raise RuntimeError(
                    f"BB statewide point paging stalled: page {page_num} returned 0 "
                    f"features but running total {total_returned} is short of "
                    f"numberMatched={matched}"
                )
            break
        if matched != -1 and total_returned >= matched:
            break

    return pages_raw, matched, total_returned


def build_bb_point_index(refresh: bool) -> dict[str, list[dict]]:
    """Fetch (or load from cache) the full-state BB point index, keyed by bare OID."""
    index_path = cache_dir() / "bb_point_index.json"
    if index_path.exists() and not refresh:
        print(f"[bb-values] loading cached point index from {index_path.name}")
        with index_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    pages_raw, matched, total_returned = _fetch_bb_point_pages(refresh)
    print(
        f"[bb-values] statewide point fetch: {len(pages_raw)} pages, "
        f"{total_returned} records (server numberMatched={matched})"
    )
    if matched is not None and matched != -1:
        drift_pct = abs(total_returned - matched) / matched * 100
        if drift_pct > 5:
            print(
                f"  [warn] DRIFT: paged total {total_returned} differs from server "
                f"numberMatched={matched} by {drift_pct:.1f}%"
            )

    index: dict[str, list[dict]] = {}
    for raw in pages_raw:
        for record in _parse_bb_point_records(raw):
            oid = record.pop("gehoertZu")
            if oid is None:
                continue
            index.setdefault(oid, []).append(record)

    with index_path.open("w", encoding="utf-8") as fh:
        json.dump(index, fh, sort_keys=True)

    return index


def _max_stichtag(records: list[dict]) -> str | None:
    stichtags = [r["stichtag"] for r in records if r.get("stichtag")]
    return max(stichtags) if stichtags else None


def probe_bb_values(refresh: bool, ll_filter: str | None = None) -> dict:
    """Task 2: measure the BB gehoertZu join at full scale and the Stichtag distribution."""
    boundaries = load_boundaries()
    bb_slugs = [slug for slug, state in LL_STATES.items() if state == "bb"]
    if ll_filter:
        bb_slugs = [s for s in bb_slugs if s == ll_filter]
        if not bb_slugs:
            raise RuntimeError(f"--ll {ll_filter!r} is not a Brandenburg Living Lab")

    point_index = build_bb_point_index(refresh)

    per_ll: dict[str, dict] = {}
    for slug in bb_slugs:
        print(f"\n[bb-values] {slug}")
        geom = _geom_for_slug(boundaries, slug)
        zone_frame = fetch_zones(slug, geom, "bb", refresh)
        zone_count = len(zone_frame)

        has_brw_col = "bodenrichtwert" in zone_frame.columns
        if has_brw_col:
            assert zone_frame["bodenrichtwert"].isna().all(), (
                f"{slug}: expected br:BR_BodenrichtwertFlaeche to carry no non-null "
                "bodenrichtwert values (value lives on the separate point feature "
                "type); found at least one non-null value -- join design assumption "
                "invalidated"
            )
            print("  bodenrichtwert column on zone frame: present but entirely null (expected)")
        else:
            print("  bodenrichtwert column on zone frame: absent (expected)")

        assert "gml_id" in zone_frame.columns, f"{slug}: zone frame missing gml_id join key"

        matched_zone_records: dict[str, list[dict]] = {}
        for oid in zone_frame["gml_id"]:
            records = point_index.get(oid)
            if records:
                matched_zone_records[oid] = records

        matched_count = len(matched_zone_records)
        unmatched_count = zone_count - matched_count
        counts_per_matched_zone = [len(recs) for recs in matched_zone_records.values()]
        mean_records = (
            sum(counts_per_matched_zone) / len(counts_per_matched_zone)
            if counts_per_matched_zone
            else 0.0
        )
        max_records = max(counts_per_matched_zone) if counts_per_matched_zone else 0

        print(f"  zones: {zone_count}")
        print(f"  matched (>=1 point record): {matched_count}")
        print(f"  unmatched (0 point records, D-08 no-data floor): {unmatched_count}")
        print(f"  point records per matched zone: mean={mean_records:.2f}, max={max_records}")

        max_stichtag_by_zone: dict[str, str] = {}
        for oid, recs in matched_zone_records.items():
            ms = _max_stichtag(recs)
            if ms:
                max_stichtag_by_zone[oid] = ms

        year_histogram: Counter = Counter(
            int(ms[:4]) for ms in max_stichtag_by_zone.values()
        )
        print("  max(stichtag).year histogram (matched zones only):")
        for year, count in sorted(year_histogram.items()):
            print(f"    {year}: {count}")

        ll_max_year = max(year_histogram) if year_histogram else None

        def _flagged_false(rule: str) -> int:
            flagged = unmatched_count
            for oid, ms in max_stichtag_by_zone.items():
                year = int(ms[:4])
                if rule == "R1":
                    if ll_max_year is not None and year != ll_max_year:
                        flagged += 1
                elif rule == "R2":
                    if ms < "2022-01-01":
                        flagged += 1
                elif rule == "R3":
                    if ms < "2024-01-01":
                        flagged += 1
            return flagged

        rule_pcts = {}
        for rule in ("R1", "R2", "R3"):
            flagged = _flagged_false(rule)
            pct = (flagged / zone_count * 100) if zone_count else 0.0
            rule_pcts[rule] = pct

        print("  W-02 has_current_value=false percentage by candidate rule:")
        for rule in ("R1", "R2", "R3"):
            print(f"    {rule}: {rule_pcts[rule]:.1f}%")

        art_counts: Counter = Counter()
        for recs in matched_zone_records.values():
            for rec in recs:
                if rec.get("nutzung_art"):
                    art_counts[rec["nutzung_art"]] += 1

        print("  nutzung.art codes in matched records:")
        unexpected_codes = []
        for code, count in art_counts.most_common():
            flag = "" if code in BB_ART_NUTZUNG_CODES else " NOT-IN-44-ENTRY-CODELIST"
            print(f"    {code}: {count}{flag}")
            if code not in BB_ART_NUTZUNG_CODES:
                unexpected_codes.append(code)

        per_ll[slug] = {
            "zone_count": zone_count,
            "matched_count": matched_count,
            "unmatched_count": unmatched_count,
            "mean_records_per_matched_zone": mean_records,
            "max_records_per_matched_zone": max_records,
            "year_histogram": dict(year_histogram),
            "rule_pcts": rule_pcts,
            "art_counts": dict(art_counts),
            "unexpected_art_codes": unexpected_codes,
        }

    print(
        "\n[bb-values] W-02 comparison table (has_current_value=false %, "
        f"as of {date.today().isoformat()}):"
    )
    header = "rule".ljust(6) + "".join(slug.rjust(24) for slug in per_ll) + "hessen (all HE LLs)".rjust(24)
    print(f"  {header}")
    for rule in ("R1", "R2", "R3"):
        row = rule.ljust(6) + "".join(
            f"{per_ll[slug]['rule_pcts'][rule]:.1f}%".rjust(24) for slug in per_ll
        )
        # Hessen: 0% by construction -- the year-versioned /2024/wfs endpoint only
        # ever returns the 2024 vintage, so every HE zone is always "current" under
        # every one of these three rules.
        row += "0.0%".rjust(24)
        print(f"  {row}")

    return {"per_ll": per_ll, "point_index_size": len(point_index)}


# Exact server-side fes:Intersects zone counts per Living Lab, verified live and
# recorded in 07-RESEARCH.md section 5.1 (2026-07-27). Used only to extrapolate the
# two un-measured HE Living Labs' projected byte size from the measured rheingau
# per-feature average; the three probed LLs use their own live-measured counts.
KNOWN_ZONE_COUNTS = {
    "rheingau": 1668,
    "north-hessian-loess": 3435,
    "hessian-low-mountain": 9531,
    "havellandisches-luch": 19083,
    "east-brandenburg": 30018,
}

VOLUME_PROBE_SLUGS = ["east-brandenburg", "havellandisches-luch", "rheingau"]

CONTRACT_KEYS = [
    "bodenrichtwert",
    "has_current_value",
    "stichtag",
    "usage_type_code",
    "usage_type_en",
    "usage_type_de",
    "development_status_en",
    "development_status_de",
    "bodenrichtwertNummer",
    "ll_slug",
]

# Placeholder bilingual labels of realistic length -- the real harmonization table
# lands in plan 07-06 (D-11). Label length, not correctness, drives byte count here.
_PLACEHOLDER_USAGE_EN = "Residential building land"
_PLACEHOLDER_USAGE_DE = "Wohnbauflaeche"
_PLACEHOLDER_DEV_EN = "Building-ready land"
_PLACEHOLDER_DEV_DE = "Bauland"

# variant letter -> (use 10-key contract?, gpd.clip()?, coordinate_precision, simplify_tolerance)
VARIANT_SPECS: dict[str, dict] = {
    "N": {"contract": False, "clip": False, "precision": None, "simplify": None},
    "A": {"contract": True, "clip": True, "precision": 0.000001, "simplify": None},
    "B": {"contract": True, "clip": True, "precision": 0.00001, "simplify": None},
    "C": {"contract": True, "clip": True, "precision": 0.00001, "simplify": 0.0001},
    "D": {"contract": True, "clip": True, "precision": 0.0001, "simplify": 0.0001},
    "E": {"contract": True, "clip": True, "precision": 0.0001, "simplify": 0.0005},
    "F": {"contract": True, "clip": True, "precision": 0.0005, "simplify": 0.001},
}

BUDGET_BYTES_PER_LL_PER_COPY = 8_000_000
BUDGET_ANCHOR_LARGEST_LL_BYTES = 7_582_567  # protected-areas-east-brandenburg.geojson
BUDGET_ANCHOR_TREE_MB = 29


def _materialize_contract_frame(
    zone_frame: gpd.GeoDataFrame, slug: str, state: str, point_index: dict
) -> gpd.GeoDataFrame:
    """Build the 10-key frontend property contract frame (07-UI-SPEC.md "Runtime asset")."""
    contract = gpd.GeoDataFrame(
        {"geometry": list(zone_frame.geometry.values)}, crs=zone_frame.crs
    )

    if state == "bb":
        assert "gml_id" in zone_frame.columns, f"{slug}: zone frame missing gml_id join key"
        bodenrichtwert, stichtag, usage_code, brw_nummer, has_current = [], [], [], [], []
        for oid in zone_frame["gml_id"]:
            recs = point_index.get(oid, [])
            ms = _max_stichtag(recs) if recs else None
            if not recs or ms is None:
                bodenrichtwert.append(None)
                stichtag.append(None)
                usage_code.append(None)
                brw_nummer.append(None)
                has_current.append(False)
                continue
            current = next((r for r in recs if r.get("stichtag") == ms), recs[-1])
            bodenrichtwert.append(current.get("bodenrichtwert"))
            stichtag.append(ms)
            usage_code.append(current.get("nutzung_art"))
            brw_nummer.append(current.get("bodenrichtwertNummer"))
            # Placeholder recency rule (R3, >=2024-01-01) for byte-count measurement
            # only -- the actual rule is a 07-05 checkpoint decision (W-02), not
            # fixed by this spike.
            has_current.append(ms >= "2024-01-01")
        contract["bodenrichtwert"] = bodenrichtwert
        contract["stichtag"] = stichtag
        contract["usage_type_code"] = usage_code
        contract["bodenrichtwertNummer"] = brw_nummer
        contract["has_current_value"] = has_current
    else:
        brw_col = _find_column(zone_frame, "bodenrichtwert")
        stichtag_col = _find_column(zone_frame, "stichtag")
        art_col = _find_column(zone_frame, "art")
        brwnr_col = _find_column(zone_frame, "bodenrichtwertNummer")
        contract["bodenrichtwert"] = zone_frame[brw_col].tolist() if brw_col else None
        contract["stichtag"] = zone_frame[stichtag_col].tolist() if stichtag_col else None
        contract["usage_type_code"] = zone_frame[art_col].tolist() if art_col else None
        contract["bodenrichtwertNummer"] = (
            zone_frame[brwnr_col].tolist() if brwnr_col else None
        )
        # HE's endpoint is year-versioned (2024 vintage only) -- every record it
        # returns is already current by construction.
        contract["has_current_value"] = True

    contract["usage_type_en"] = _PLACEHOLDER_USAGE_EN
    contract["usage_type_de"] = _PLACEHOLDER_USAGE_DE
    contract["development_status_en"] = _PLACEHOLDER_DEV_EN
    contract["development_status_de"] = _PLACEHOLDER_DEV_DE
    contract["ll_slug"] = slug

    return contract[CONTRACT_KEYS + ["geometry"]]


def _count_vertices(geom) -> int:
    """Count coordinate pairs in a geometry, regardless of geometry type.

    Uses shapely.get_coordinates rather than a Polygon-only `.exterior`/`.interiors`
    walk: a live run against east-brandenburg's zone data surfaced at least one
    non-Polygon geometry (a bare LineString) after clip/simplify/precision
    processing, which the Polygon-only walk raised AttributeError on (Rule 1 bug
    fix -- get_coordinates handles every shapely geometry type uniformly).
    """
    if geom is None or geom.is_empty:
        return 0
    from shapely import get_coordinates

    return len(get_coordinates(geom))


def _run_variant_grid(
    slug: str, ll_geom_wgs84, zone_frame: gpd.GeoDataFrame, contract_frame: gpd.GeoDataFrame
) -> dict:
    """Write and measure the seven W-01 volume/fidelity variants for one Living Lab."""
    from shapely import set_precision

    spike_dir = cache_dir() / "spike"
    spike_dir.mkdir(parents=True, exist_ok=True)

    baseline_frame: gpd.GeoDataFrame | None = None
    results: dict = {}

    for letter, spec in VARIANT_SPECS.items():
        source = contract_frame if spec["contract"] else zone_frame
        frame = source.copy()

        if spec["clip"]:
            mask = gpd.GeoDataFrame(
                {"ll_slug": [slug]}, geometry=[ll_geom_wgs84], crs="EPSG:4326"
            )
            frame = gpd.clip(frame, mask)

        if spec["simplify"] is not None:
            frame.geometry = frame.geometry.simplify(spec["simplify"], preserve_topology=True)

        if spec["precision"] is not None:
            frame.geometry = frame.geometry.apply(
                lambda g, p=spec["precision"]: set_precision(g, grid_size=p)
            )
            frame.geometry = frame.geometry.make_valid()

        empty_count = int(frame.geometry.is_empty.sum())
        frame_nonempty = frame[~frame.geometry.is_empty].copy()

        if len(frame_nonempty) == 0:
            print(f"  [warn] variant {letter} ({slug}): all geometries empty after processing, skipping")
            results[letter] = None
            continue

        if not frame_nonempty.geometry.is_valid.all():
            frame_nonempty.geometry = frame_nonempty.geometry.make_valid()
        if not frame_nonempty.geometry.is_valid.all():
            print(f"  [warn] variant {letter} ({slug}): invalid geometry could not be repaired, skipping")
            results[letter] = None
            continue

        output_path = spike_dir / f"boris-spike-{slug}-{letter}.geojson"
        payload = frame_nonempty.to_json(drop_id=True, sort_keys=True)
        output_path.write_text(payload + "\n", encoding="utf-8")

        size_bytes = output_path.stat().st_size
        vertex_count = int(frame_nonempty.geometry.apply(_count_vertices).sum())

        if letter == "N":
            baseline_frame = frame_nonempty

        area_change = None
        if baseline_frame is not None and letter != "N":
            common_idx = frame_nonempty.index.intersection(baseline_frame.index)
            if len(common_idx):
                # Reproject to a metric CRS (EPSG:3035, ETRS89-extended LAEA Europe)
                # for the area comparison only -- geographic-CRS (degree) area has
                # no physical meaning and geopandas warns accordingly. The written
                # GeoJSON stays in EPSG:4326; only this fidelity ratio uses 3035.
                base_areas = (
                    baseline_frame.loc[common_idx].geometry.to_crs("EPSG:3035").area
                )
                var_areas = (
                    frame_nonempty.loc[common_idx].geometry.to_crs("EPSG:3035").area
                )
                denom = base_areas.replace(0, pd.NA)
                rel_change = ((var_areas - base_areas).abs() / denom).dropna()
                if len(rel_change):
                    area_change = float(rel_change.mean())

        results[letter] = {
            "bytes": size_bytes,
            "mb": size_bytes / (1024 * 1024),
            "feature_count": len(frame_nonempty),
            "vertex_count": vertex_count,
            "empty_count": empty_count,
            "mean_abs_rel_area_change_vs_N": area_change,
        }
        area_str = f"{area_change:.4f}" if area_change is not None else "n/a"
        print(
            f"  variant {letter}: {size_bytes:,} bytes ({size_bytes / 1024 / 1024:.2f} MB), "
            f"{len(frame_nonempty)} features, {vertex_count} vertices, {empty_count} empty, "
            f"mean_abs_rel_area_change_vs_N={area_str}"
        )

    return results


def probe_volume(refresh: bool, ll_filter: str | None = None) -> dict:
    """Task 3: measure the seven W-01 variants and write 07-SPIKE.md with all evidence."""
    print("[volume] gathering W-03 (Hessen codes) and W-02 (BB Stichtag) evidence for the report...")
    he_results = probe_he_codes(False)
    bb_results = probe_bb_values(False)

    boundaries = load_boundaries()
    target_slugs = [s for s in VOLUME_PROBE_SLUGS if not ll_filter or s == ll_filter]
    if ll_filter and not target_slugs:
        raise RuntimeError(f"--ll {ll_filter!r} is not one of the three volume-probe Living Labs")

    point_index = None
    volume_results: dict[str, dict] = {}

    for slug in target_slugs:
        print(f"\n[volume] {slug}")
        state = LL_STATES[slug]
        geom = _geom_for_slug(boundaries, slug)
        zone_frame = fetch_zones(slug, geom, state, refresh)

        if state == "bb":
            if point_index is None:
                point_index = build_bb_point_index(refresh)
            contract_frame = _materialize_contract_frame(zone_frame, slug, state, point_index)
        else:
            contract_frame = _materialize_contract_frame(zone_frame, slug, state, {})

        variants = _run_variant_grid(slug, geom, zone_frame, contract_frame)
        volume_results[slug] = {
            "zone_count": len(zone_frame),
            "variants": variants,
        }

    print("\n[volume] Projected repository impact (2x, both data/geojson/ and app/public/ copies):")
    projected: dict[str, float] = {}
    for letter in VARIANT_SPECS:
        total_bytes = 0
        measured_total = 0
        for slug in VOLUME_PROBE_SLUGS:
            if slug not in volume_results:
                continue
            variant = volume_results[slug]["variants"].get(letter)
            if variant is None:
                continue
            total_bytes += variant["bytes"]
            measured_total += 1

        rheingau_variant = volume_results.get("rheingau", {}).get("variants", {}).get(letter)
        if rheingau_variant is not None:
            rheingau_count = volume_results["rheingau"]["zone_count"]
            bytes_per_feature = rheingau_variant["bytes"] / rheingau_count if rheingau_count else 0
            for unmeasured_slug in ("north-hessian-loess", "hessian-low-mountain"):
                if unmeasured_slug in volume_results:
                    continue
                total_bytes += bytes_per_feature * KNOWN_ZONE_COUNTS[unmeasured_slug]

        projected[letter] = total_bytes * 2
        print(f"  variant {letter}: projected total {projected[letter] / 1024 / 1024:.1f} MB")

    write_spike_report(he_results, bb_results, volume_results, projected)

    return {"volume": volume_results, "projected_repo_impact_bytes": projected}


def _propose_w03_target(code: str) -> tuple[str, str]:
    """Propose a canonical BB target for an observed HE code by exact abbreviation match.

    Returns (proposed_target_text, status) where status is "mapped" or "UNMAPPABLE".
    This is a proposal for the 07-05 checkpoint, not a locked decision.
    """
    bb_code = BB_ABBREVIATION_TO_CODE.get(code)
    if bb_code is None:
        return "UNMAPPABLE", "UNMAPPABLE"
    _abbrev, label_de = BB_ART_NUTZUNG_TABLE[bb_code]
    return f"{bb_code} ({label_de})", "mapped"


def write_spike_report(
    he_results: dict, bb_results: dict, volume_results: dict, projected: dict
) -> Path:
    """Write 07-SPIKE.md with the W-01/W-02/W-03 evidence for the 07-05 checkpoint."""
    lines: list[str] = []
    run_date = date.today().isoformat()

    lines.append("# Phase 7 Wave-0 Spike")
    lines.append("")
    lines.append(
        f"Run date: {run_date}. Every number below was measured live against the "
        "BORIS-BB and BORIS-HE WFS services by `data-pipeline/python/probe_boris.py` "
        "(plan 07-03), except where explicitly marked as an extrapolation."
    )
    lines.append("")

    # --- W-01 ---
    lines.append("## W-01 Volume and geometry fidelity")
    lines.append("")
    for slug in VOLUME_PROBE_SLUGS:
        if slug not in volume_results:
            continue
        lines.append(f"### {slug} ({volume_results[slug]['zone_count']} zones)")
        lines.append("")
        lines.append(
            "| Variant | Bytes | MB | Features | Vertices | Empty | Mean abs rel area change vs N |"
        )
        lines.append("|---|---:|---:|---:|---:|---:|---:|")
        for letter in VARIANT_SPECS:
            variant = volume_results[slug]["variants"].get(letter)
            if variant is None:
                lines.append(f"| {letter} | skipped | skipped | - | - | - | - |")
                continue
            area = (
                f"{variant['mean_abs_rel_area_change_vs_N']:.4f}"
                if variant["mean_abs_rel_area_change_vs_N"] is not None
                else "n/a"
            )
            lines.append(
                f"| {letter} | {variant['bytes']:,} | {variant['mb']:.2f} | "
                f"{variant['feature_count']} | {variant['vertex_count']} | "
                f"{variant['empty_count']} | {area} |"
            )
        lines.append("")

    lines.append(
        "### Projected repository impact (both `data/geojson/` and `app/public/` copies, "
        "measured LLs summed + the two un-measured HE LLs extrapolated from rheingau's "
        "per-feature average size)"
    )
    lines.append("")
    lines.append("| Variant | Projected total bytes | Projected total MB |")
    lines.append("|---|---:|---:|")
    for letter in VARIANT_SPECS:
        total = projected.get(letter, 0)
        lines.append(f"| {letter} | {total:,.0f} | {total / 1024 / 1024:.1f} |")
    lines.append("")

    lines.append(
        f"Budget anchor: the largest per-LL vector GeoJSON committed today is "
        f"`protected-areas-east-brandenburg.geojson` at {BUDGET_ANCHOR_LARGEST_LL_BYTES:,} "
        f"bytes ({BUDGET_ANCHOR_LARGEST_LL_BYTES / 1024 / 1024:.1f} MiB); the whole "
        f"`data/geojson/` tree is ~{BUDGET_ANCHOR_TREE_MB} MB; every file in that tree is "
        "committed twice."
    )
    lines.append("")

    eb_variants = volume_results.get("east-brandenburg", {}).get("variants", {})
    qualifying = [
        letter
        for letter, v in eb_variants.items()
        if v is not None and v["bytes"] <= BUDGET_BYTES_PER_LL_PER_COPY
    ]
    if qualifying:
        lines.append(
            f"Variants meeting a <={BUDGET_BYTES_PER_LL_PER_COPY:,} byte "
            f"(<=8 MB) per-LL-per-copy budget for east-brandenburg: "
            f"{', '.join(qualifying)}."
        )
    else:
        lines.append(
            f"No measured variant meets a <={BUDGET_BYTES_PER_LL_PER_COPY:,} byte "
            "(<=8 MB) per-LL-per-copy budget for east-brandenburg; a structural change "
            "(per-LL PMTiles for the two Brandenburg LLs, or a larger accepted budget) "
            "would be required to fit within it."
        )
    lines.append("")

    # --- W-02 ---
    lines.append("## W-02 has_current_value recency threshold")
    lines.append("")
    bb_per_ll = bb_results.get("per_ll", {})
    if bb_per_ll:
        lines.append("| Rule | " + " | ".join(bb_per_ll.keys()) + " | hessen (all HE LLs) |")
        lines.append("|---|" + "---:|" * (len(bb_per_ll) + 1))
        for rule in ("R1", "R2", "R3"):
            row = [f"{bb_per_ll[slug]['rule_pcts'][rule]:.1f}%" for slug in bb_per_ll]
            lines.append(f"| {rule} | " + " | ".join(row) + " | 0.0% |")
        lines.append("")
        lines.append(
            "Hessen is 0% by construction: the year-versioned `/2024/wfs` endpoint only "
            "ever returns the 2024 vintage, so every HE zone is current under every rule."
        )
        lines.append("")

        for slug, data in bb_per_ll.items():
            lines.append(f"### {slug} max(stichtag).year histogram (matched zones only)")
            lines.append("")
            lines.append("| Year | Zones |")
            lines.append("|---:|---:|")
            for year, count in sorted(data["year_histogram"].items()):
                lines.append(f"| {year} | {count} |")
            lines.append("")
    else:
        lines.append("(no Brandenburg Living Labs probed)")
        lines.append("")

    # --- W-03 ---
    lines.append("## W-03 Hessen usage-code vocabulary")
    lines.append("")
    union_art = he_results.get("union_art", {})
    lines.append("| HE code | Occurrences (3 Hessen LLs) | Proposed canonical target |")
    lines.append("|---|---:|---|")
    items = union_art.items() if isinstance(union_art, dict) else union_art.most_common()
    for code, count in sorted(items, key=lambda kv: -kv[1]):
        target, _status = _propose_w03_target(code)
        lines.append(f"| {code} | {count} | {target} |")
    lines.append("")

    union_ez = he_results.get("union_entwicklungszustand", {})
    lines.append("### entwicklungszustand union (3 Hessen LLs)")
    lines.append("")
    lines.append("| Code | Occurrences | In expected {B,R,E,LF,SF}? |")
    lines.append("|---|---:|---|")
    ez_items = union_ez.items() if isinstance(union_ez, dict) else union_ez.most_common()
    for code, count in sorted(ez_items, key=lambda kv: -kv[1]):
        flag = "yes" if code in EXPECTED_ENTWICKLUNGSZUSTAND_HE else "UNEXPECTED"
        lines.append(f"| {code} | {count} | {flag} |")
    lines.append("")

    # --- Open items ---
    lines.append("## Open items for the checkpoint")
    lines.append("")
    lines.append(
        "1. Which W-01 volume/fidelity variant (or a structural alternative such as "
        "per-LL PMTiles for the two Brandenburg Living Labs) to lock for the committed "
        "BORIS GeoJSON output, given the measured per-LL-per-copy byte budget above."
    )
    lines.append(
        "2. Which W-02 recency rule (R1 relative, R2 >=2022-01-01, or R3 >=2024-01-01) "
        "sets `has_current_value`, given the measured false-percentage per rule per "
        "Brandenburg Living Lab above."
    )
    lines.append(
        "3. Which proposed W-03 HE-to-canonical usage-code mappings to confirm or "
        "adjust, and how to handle any UNMAPPABLE HE code (for example `LW`, which "
        "does not exactly match any BB abbreviation)."
    )
    lines.append("")

    content = "\n".join(lines) + "\n"
    output_path = resolve(
        ".planning/phases/07-add-boris-land-value-maps-as-spatial-layer-for-socio-economi/07-SPIKE.md"
    )
    output_path.write_text(content, encoding="utf-8")
    print(f"\n[volume] wrote {output_path}")
    return output_path


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only BORIS WFS diagnostic probes for the Wave-0 spike. "
            "Writes only to data/_cache/boris/ (gitignored) and 07-SPIKE.md."
        )
    )
    parser.add_argument(
        "probe",
        choices=["he-codes", "bb-values", "volume"],
        help="Which probe to run: he-codes, bb-values, or volume",
    )
    parser.add_argument("--refresh", action="store_true", help="Bypass cache and re-fetch from WFS")
    parser.add_argument("--ll", default=None, help="Restrict the probe to a single Living Lab slug")
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.probe == "he-codes":
        probe_he_codes(args.refresh, args.ll)
    elif args.probe == "bb-values":
        probe_bb_values(args.refresh, args.ll)
    elif args.probe == "volume":
        probe_volume(args.refresh, args.ll)


if __name__ == "__main__":
    main()
