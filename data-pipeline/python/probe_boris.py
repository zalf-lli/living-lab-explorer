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
    """Find a GML-derived column name containing keyword (case-insensitive substring)."""
    keyword_lower = keyword.lower()
    candidates = [c for c in frame.columns if keyword_lower in c.lower()]
    if not candidates:
        return None
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


def probe_volume(refresh: bool, ll_filter: str | None = None) -> dict:
    raise NotImplementedError("volume probe is implemented in plan 07-03 Task 3")


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
