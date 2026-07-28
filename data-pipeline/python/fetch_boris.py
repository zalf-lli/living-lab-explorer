from __future__ import annotations

"""Fetch BORIS (Bodenrichtwertinformationssystem) standard land values per Living Lab.

Writes `data/geojson/boris-{slug}.geojson` (EPSG:4326) from the BORIS-BB (Brandenburg)
and BORIS-HE (Hessen) WFS services. The two states are genuinely different code paths,
not a field-name-configured variant of one fetch function:

- Hessen's `boris:BR_BodenrichtwertZonal` zone feature type is self-contained -- value,
  valuation date, and usage type live directly on the polygon. No join runs.
- Brandenburg's `br:BR_BodenrichtwertFlaeche` zone feature type carries geometry only.
  Values live on a separate, geometry-less `br:BR_Bodenrichtwert` point feature type
  and must be joined locally by `gehoertZu`, selecting the newest Stichtag per zone.

Both paths converge on one shared harmonization step (`boris_semantics.py`,
D-11 bilingual usage-type/development-status contract), one shared geometry treatment
(clip / simplify / precision-round, per the W-01 locked decision in 07-SPIKE.md), and
one shared validated write.

This script writes only per-Living-Lab GeoJSON under `data/geojson/`. It never touches
the separately human-authored Living Lab content manifest and never writes into the
app's public runtime data directory -- publishing app-runtime copies is `sync.py`'s job.
"""

import argparse
import json
import math
import re
from datetime import date
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely import set_precision

from _sources import get_layer, resolve
from boris_semantics import apply_boris_contract, is_current_value
from boris_wfs import (
    build_intersects_body,
    extract_counts,
    http_get,
    http_post,
    read_gml_frame,
)

# Ten-key frontend property contract (07-UI-SPEC.md "Runtime asset"). Every other raw
# GML column (verbose repeated committee names, zone-name free text, etc.) is dropped.
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

# Accepted per-Living-Lab-per-copy byte budget from the W-01 locked decision
# (07-SPIKE.md, variant E, ~33 MB). Diagnostic only -- never gates or fails the write.
BUDGET_BYTES_PER_LL_PER_COPY = 33_000_000

HE_BRW_CANDIDATES = ["bodenrichtwert"]
HE_STICHTAG_CANDIDATES = ["stichtag"]
HE_BRW_NUMMER_CANDIDATES = ["bodenrichtwertNummer", "bodenrichtwertnummer"]
HE_ART_CANDIDATES = ["nutzung.art", "nutzung_art", "art"]
HE_ENTW_CANDIDATES = ["entwicklungszustand"]
BB_OID_CANDIDATES = ["gml_id", "id"]

# Regex extraction of br:BR_Bodenrichtwert point records, lifted from probe_boris.py
# (plan 07-03), proven live: GDAL's GML driver drops href-only reference elements
# (gehoertZu, art) from the flattened attribute table gpd.read_file() returns, so
# every field is extracted directly from the raw GML text instead (T-07-01: no XML
# parser is imported, matching boris_wfs.py's own numberMatched/numberReturned
# byte-slicing approach).
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


def _write_geojson(frame: gpd.GeoDataFrame, output_path: Path) -> None:
    """Write GeoDataFrame as sorted-key GeoJSON (CLAUDE.md rule)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = frame.to_json(drop_id=True, sort_keys=True)
    output_path.write_text(payload + "\n", encoding="utf-8")


def _find_column(frame: gpd.GeoDataFrame, candidates: list[str]) -> str:
    """Resolve a raw GML column against an ordered candidate-name list.

    Tries an exact (case-sensitive) match against every candidate first, then a
    case-insensitive match. Raises RuntimeError naming the columns actually present
    if none match, rather than silently producing all-null values -- the GDAL GML
    driver may flatten a nested element (`nutzung.art`) to `nutzung.art`,
    `nutzung_art`, or `art` depending on driver version.
    """
    columns = list(frame.columns)
    for candidate in candidates:
        if candidate in columns:
            return candidate
    lowered = {c.lower(): c for c in columns}
    for candidate in candidates:
        match = lowered.get(candidate.lower())
        if match:
            return match
    raise RuntimeError(
        f"None of the candidate columns {candidates} were found. Columns present: {columns}"
    )


def _coerce_date_str(value) -> str | None:
    """Coerce a raw stichtag value (str, datetime, NaT, None) to an ISO date string or None."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    if not text or text.lower() in ("nat", "none"):
        return None
    return text[:10]


def _to_float_or_none(value) -> float | None:
    """Coerce a raw bodenrichtwert value to a Python float or None (never a string)."""
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(result):
        return None
    return result


def load_boundaries(ll_states: dict, ll_filter: str | None) -> gpd.GeoDataFrame:
    """Read data/ll_boundaries.geojson, assert the state-assignment invariant, filter.

    Every boundary slug must be a key of `ll_states` (sources.yaml boris.ll_states) --
    an unassigned Living Lab fails loudly here rather than silently defaulting to a state.
    """
    boundaries = gpd.read_file(resolve("data/ll_boundaries.geojson"))
    assert "ll_slug" in boundaries.columns, "ll_boundaries.geojson missing ll_slug column"
    assert boundaries.crs is not None and str(boundaries.crs) == "EPSG:4326", (
        "ll_boundaries.geojson must have EPSG:4326 CRS"
    )

    unassigned = [s for s in boundaries["ll_slug"] if s not in ll_states]
    if unassigned:
        raise RuntimeError(
            f"Living Lab slug(s) {unassigned} have no state assignment in sources.yaml "
            "boris.ll_states -- an unassigned Living Lab must fail loudly, never default "
            "to a state."
        )

    if ll_filter:
        if ll_filter not in boundaries["ll_slug"].values:
            available = list(boundaries["ll_slug"].values)
            raise SystemExit(f"Living Lab {ll_filter!r} not found. Available: {available}")
        boundaries = boundaries[boundaries["ll_slug"] == ll_filter]

    return boundaries


def fetch_zones(
    slug: str,
    ll_geom_wgs84,
    state: str,
    state_cfg: dict,
    wfs_cfg: dict,
    cache_dir: Path,
    refresh: bool,
) -> gpd.GeoDataFrame:
    """Fetch every zone polygon intersecting an LL boundary for one state, paged and cached.

    Uses a server-side fes:Intersects filter -- never a padded bounding-box parameter;
    a verified overselection test measured 3.6x extra features on havellandisches-luch
    with that approach (07-RESEARCH.md). Raises RuntimeError on a paging stall or a
    silently empty (numberMatched=0) response.
    """
    epsg = int(state_cfg["source_crs"].split(":")[-1])
    typename = state_cfg["zone_typename"]
    geometry_property = state_cfg.get("geometry_property", "adv:position")
    url = state_cfg["url"]
    count = wfs_cfg["count"]
    max_bytes = wfs_cfg["max_response_bytes"]

    geom_native = gpd.GeoSeries([ll_geom_wgs84], crs="EPSG:4326").to_crs(state_cfg["source_crs"]).iloc[0]

    cache_dir.mkdir(parents=True, exist_ok=True)
    pages: list[gpd.GeoDataFrame] = []
    page_num = 0
    startindex = 0
    matched: int | None = None
    total_returned = 0

    while True:
        cache_path = cache_dir / f"zones__{slug}__p{page_num:03d}.gml"
        if cache_path.exists() and not refresh:
            print(f"  [cache] {slug} zones page {page_num}")
            raw = cache_path.read_bytes()
        else:
            body = build_intersects_body(
                state,
                typename,
                geom_native,
                epsg,
                count=count,
                startindex=startindex,
                geometry_property=geometry_property,
            )
            raw = http_post(url, body, max_bytes)
            cache_path.write_bytes(raw)

        page_matched, page_returned = extract_counts(raw)
        if matched is None:
            matched = page_matched
            if matched == 0:
                raise RuntimeError(
                    f"{slug} ({state}): numberMatched=0 on the zone fetch. A silently "
                    "empty response is a request-shape bug, not a legitimate empty state "
                    "-- every Living Lab is known to intersect thousands of zones."
                )

        # A 0-feature page has no layer schema for GDAL to detect -- parsing it raises
        # IndexError deep inside pyogrio. Only parse pages that actually returned features.
        if page_returned > 0:
            frame = read_gml_frame(raw, state_cfg["source_crs"], f"zones__{slug}__p{page_num}")
            pages.append(frame)

        total_returned += page_returned
        page_num += 1
        startindex += page_returned

        if page_returned == 0:
            if matched != -1 and total_returned < matched:
                raise RuntimeError(
                    f"{slug} ({state}): zone paging stalled -- page {page_num} returned 0 "
                    f"features but the running total {total_returned} is short of "
                    f"numberMatched={matched}"
                )
            break
        if matched != -1 and total_returned >= matched:
            break

    if not pages:
        raise RuntimeError(f"No zone pages fetched for {slug} ({state})")

    combined = gpd.GeoDataFrame(pd.concat(pages, ignore_index=True), crs=state_cfg["source_crs"])
    combined = combined.to_crs("EPSG:4326")
    print(f"  [ok] {slug} ({state}): fetched {len(combined)} zones across {page_num} page(s)")
    return combined


def collect_he(slug: str, zones: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Hessen self-contained value path: read raw value columns directly, no join.

    Applies no usage-type filter of any kind -- D-05 requires all zone types and D-07
    requires Bauerwartungsland to be included as an ordinary zone.
    """
    brw_col = _find_column(zones, HE_BRW_CANDIDATES)
    stichtag_col = _find_column(zones, HE_STICHTAG_CANDIDATES)
    brwnr_col = _find_column(zones, HE_BRW_NUMMER_CANDIDATES)
    art_col = _find_column(zones, HE_ART_CANDIDATES)
    entw_col = _find_column(zones, HE_ENTW_CANDIDATES)

    print(f"  [he] {slug}: resolved usage-type column {art_col!r}")

    frame = gpd.GeoDataFrame({"geometry": list(zones.geometry.values)}, crs=zones.crs)
    frame["bodenrichtwert"] = pd.to_numeric(zones[brw_col], errors="coerce")
    frame["stichtag"] = zones[stichtag_col].apply(_coerce_date_str)
    frame["bodenrichtwertNummer"] = zones[brwnr_col].apply(
        lambda v: str(v) if pd.notna(v) else None
    )
    frame["nutzung_art"] = zones[art_col]
    frame["entwicklungszustand"] = zones[entw_col]

    non_null_brw = int(frame["bodenrichtwert"].notna().sum())
    print(f"  [he] {slug}: {non_null_brw}/{len(frame)} zones have a non-null bodenrichtwert")

    return frame


def _parse_bb_point_records(raw: bytes) -> list[dict]:
    """Regex-parse br:BR_Bodenrichtwert records into flat dicts, keyed by gehoertZu.

    Lifted verbatim (proven logic) from probe_boris.py (plan 07-03): GDAL's GML driver
    drops href-only reference elements from the flattened attribute table, so every
    field is extracted directly from the raw GML text.
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


def load_bb_point_index(
    state_cfg: dict, wfs_cfg: dict, cache_dir: Path, refresh: bool
) -> dict[str, list[dict]]:
    """Fetch (or load from cache) the full-state BB point index, keyed by bare OID.

    Pages `br:BR_Bodenrichtwert` statewide with a plain GetFeature GET (no bounding
    box, no spatial filter of any kind -- this feature type has no geometry property
    and any spatial filter returns a server error). Each page is parsed and its raw
    bytes discarded
    before the next page is fetched, so the whole statewide response is never
    resident in memory at once (T-07-03). The resulting index is persisted to
    `bb_point_index.json` and reused on subsequent runs.
    """
    index_path = cache_dir / "bb_point_index.json"
    if index_path.exists() and not refresh:
        print(f"  [cache] loading BB point index from {index_path.name}")
        with index_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    url = state_cfg["url"]
    typename = state_cfg["value_typename"]
    version = state_cfg.get("version", "2.0.0")
    count = wfs_cfg["count"]
    max_bytes = wfs_cfg["max_response_bytes"]

    cache_dir.mkdir(parents=True, exist_ok=True)
    index: dict[str, list[dict]] = {}
    page_num = 0
    startindex = 0
    matched: int | None = None
    total_returned = 0

    while True:
        cache_path = cache_dir / f"bb_points__p{page_num:03d}.gml"
        if cache_path.exists() and not refresh:
            print(f"  [cache] BB statewide points page {page_num}")
            raw = cache_path.read_bytes()
        else:
            params = {
                "SERVICE": "WFS",
                "VERSION": version,
                "REQUEST": "GetFeature",
                "TYPENAMES": typename,
                "COUNT": count,
                "STARTINDEX": startindex,
            }
            raw = http_get(url, params, max_bytes)
            cache_path.write_bytes(raw)

        page_matched, page_returned = extract_counts(raw)
        if matched is None:
            matched = page_matched

        for record in _parse_bb_point_records(raw):
            oid = record.pop("gehoertZu")
            if oid is None:
                continue
            index.setdefault(oid, []).append(record)
        del raw

        total_returned += page_returned
        page_num += 1
        startindex += page_returned

        if page_returned == 0:
            if matched != -1 and total_returned < matched:
                raise RuntimeError(
                    f"BB statewide point paging stalled: page {page_num} returned 0 "
                    f"features but the running total {total_returned} is short of "
                    f"numberMatched={matched}"
                )
            break
        if matched != -1 and total_returned >= matched:
            break

    print(
        f"  [ok] BB statewide point fetch: {page_num} page(s), {total_returned} records "
        f"(server numberMatched={matched})"
    )
    if matched is not None and matched != -1 and matched:
        drift_pct = abs(total_returned - matched) / matched * 100
        if drift_pct > 5:
            print(
                f"  [warn] DRIFT: paged total {total_returned} differs from server "
                f"numberMatched={matched} by {drift_pct:.1f}%"
            )

    with index_path.open("w", encoding="utf-8") as fh:
        json.dump(index, fh, sort_keys=True)

    return index


def collect_bb(
    slug: str, zones: gpd.GeoDataFrame, point_index: dict[str, list[dict]], reference: str
) -> gpd.GeoDataFrame:
    """Brandenburg point/polygon join path: newest-Stichtag value per zone by gehoertZu.

    Zones with no matching point record, and zones whose newest Stichtag fails the
    recency predicate, keep their geometry -- D-08 requires geographic completeness so
    gaps are never misread as zero value. `has_current_value` itself is computed
    uniformly for both states by `harmonise()`/`apply_boris_contract()`; this function
    only prints the diagnostic counts using the same predicate for comparison against
    07-SPIKE.md.
    """
    oid_col = _find_column(zones, BB_OID_CANDIDATES)

    if "bodenrichtwert" in zones.columns:
        non_null = int(zones["bodenrichtwert"].notna().sum())
        if non_null:
            print(
                f"  [warn] {slug}: BR_BodenrichtwertFlaeche carries {non_null} non-null "
                "bodenrichtwert values -- expected this column absent/entirely null; the "
                "join design assumes it is absent, and the upstream schema may have changed."
            )

    bodenrichtwert: list = []
    stichtag: list = []
    brw_nummer: list = []
    nutzung_art: list = []
    entw: list = []
    matched_count = 0
    failing_recency_count = 0

    for oid in zones[oid_col]:
        records = point_index.get(oid)
        if not records:
            bodenrichtwert.append(None)
            stichtag.append(None)
            brw_nummer.append(None)
            nutzung_art.append(None)
            entw.append(None)
            continue

        matched_count += 1
        # Newest Stichtag wins. Never select by list position -- the endpoint returns
        # records in no meaningful order (07-RESEARCH.md section 4).
        best = max(records, key=lambda r: r.get("stichtag") or "")
        bodenrichtwert.append(best.get("bodenrichtwert"))
        stichtag.append(best.get("stichtag"))
        brw_nummer.append(best.get("bodenrichtwertNummer"))
        nutzung_art.append(best.get("nutzung_art"))
        entw.append(best.get("entwicklungszustand"))

        if not is_current_value(best.get("stichtag"), reference):
            failing_recency_count += 1

    zone_count = len(zones)
    unmatched_count = zone_count - matched_count
    assert matched_count + unmatched_count == zone_count, (
        f"{slug}: matched ({matched_count}) + unmatched ({unmatched_count}) != "
        f"zone_count ({zone_count})"
    )

    print(
        f"  [bb] {slug}: zones={zone_count} matched={matched_count} "
        f"unmatched={unmatched_count} failing_recency={failing_recency_count}"
    )

    frame = gpd.GeoDataFrame({"geometry": list(zones.geometry.values)}, crs=zones.crs)
    frame["bodenrichtwert"] = bodenrichtwert
    frame["stichtag"] = stichtag
    frame["bodenrichtwertNummer"] = brw_nummer
    frame["nutzung_art"] = nutzung_art
    frame["entwicklungszustand"] = entw

    return frame


def _compute_recency_reference(semantics_cfg: dict, today: date | None = None) -> str:
    """Compute the W-02 rolling-window recency cutoff fresh at run time.

    Predicate: max(stichtag) >= (run_year - recency_window_years)-01-01, per the
    07-SPIKE.md locked decision. Uses `semantics.recency_cutoff` verbatim only if
    sources.yaml sets an absolute override (it is intentionally null today, so no
    stale date literal is ever checked in).
    """
    absolute_cutoff = semantics_cfg.get("recency_cutoff")
    if absolute_cutoff:
        return absolute_cutoff

    window_years = semantics_cfg.get("recency_window_years", 10)
    run_date = today or date.today()
    return date(run_date.year - window_years, 1, 1).isoformat()


def harmonise(frame: gpd.GeoDataFrame, state: str, slug: str, reference: str) -> gpd.GeoDataFrame:
    """Apply the boris_semantics contract and trim to exactly the ten output columns.

    Coerces bodenrichtwert to a Python float or None (never a string), has_current_value
    to a Python bool (never a NumPy bool), and stichtag to an ISO date string or None.
    """
    frame = apply_boris_contract(frame, state, reference)
    frame["ll_slug"] = slug

    result = gpd.GeoDataFrame({"geometry": list(frame.geometry.values)}, crs="EPSG:4326")
    for key in CONTRACT_KEYS:
        result[key] = list(frame[key].values)

    result["bodenrichtwert"] = result["bodenrichtwert"].apply(_to_float_or_none)
    result["has_current_value"] = result["has_current_value"].apply(bool)
    result["stichtag"] = result["stichtag"].apply(_coerce_date_str)

    # NaN/numpy/datetime coercion loop, adapted from fetch_protected_areas._normalise
    # (lines 290-300): applied to every string-valued contract column so any numpy
    # scalar or NaT/NaN survives to JSON cleanly. bodenrichtwert and has_current_value
    # are deliberately excluded here -- the loop's `str(x) if pd.notna(x) else None`
    # step would stringify a legitimate numeric/boolean value, which the ten-key
    # contract forbids (07-UI-SPEC.md: "must be a plain number, never a string" /
    # "must be a boolean"). Applying it verbatim to every column would silently break
    # that contract, so it is scoped to the string-valued columns only.
    string_columns = [
        "stichtag",
        "usage_type_code",
        "usage_type_en",
        "usage_type_de",
        "development_status_en",
        "development_status_de",
        "bodenrichtwertNummer",
        "ll_slug",
    ]
    for col in string_columns:
        result[col] = result[col].apply(lambda x: str(x) if pd.notna(x) else None)
        result[col] = result[col].apply(lambda x: x.item() if hasattr(x, "item") else x)
        result[col] = result[col].apply(lambda x: None if pd.isna(x) else x)

    actual_keys = set(result.columns) - {"geometry"}
    expected_keys = set(CONTRACT_KEYS)
    if actual_keys != expected_keys:
        raise RuntimeError(
            f"{slug}: contract column mismatch. Expected {sorted(expected_keys)}, "
            f"got {sorted(actual_keys)}"
        )

    return result


def apply_geometry_treatment(
    frame: gpd.GeoDataFrame, slug: str, ll_geom_wgs84, wfs_cfg: dict
) -> gpd.GeoDataFrame:
    """Clip, simplify, precision-round, revalidate, and drop-empty, in that order.

    Uses the W-01 `coordinate_precision`/`simplify_tolerance` values read from
    sources.yaml (never hardcoded). Clipping differs deliberately from the
    protected-areas layer (which keeps full unclipped polygons by an explicit Phase 5
    decision) -- this phase has no such requirement, and clipping materially reduces
    committed geometry for boundary-straddling zones.
    """
    mask = gpd.GeoDataFrame({"ll_slug": [slug]}, geometry=[ll_geom_wgs84], crs="EPSG:4326")
    frame = gpd.clip(frame, mask)

    simplify_tolerance = wfs_cfg.get("simplify_tolerance")
    if simplify_tolerance is not None:
        frame.geometry = frame.geometry.simplify(simplify_tolerance, preserve_topology=True)

    coordinate_precision = wfs_cfg.get("coordinate_precision")
    if coordinate_precision is not None:
        frame.geometry = frame.geometry.apply(
            lambda g: set_precision(g, grid_size=coordinate_precision)
        )

    frame.geometry = frame.geometry.make_valid()
    assert frame.geometry.is_valid.all(), f"{slug}: invalid geometry survived make_valid()"

    before_count = len(frame)
    frame = frame[~frame.geometry.is_empty].copy()
    dropped_count = before_count - len(frame)
    if dropped_count:
        drop_pct = (dropped_count / before_count * 100) if before_count else 0.0
        message = (
            f"{slug}: dropped {dropped_count}/{before_count} zones with empty geometry "
            f"({drop_pct:.2f}%)"
        )
        if drop_pct > 0.5:
            print(f"  [warn] {message}")
        else:
            print(f"  [geometry] {message}")
    else:
        print(f"  [geometry] {slug}: 0 zones dropped to empty geometry")

    return frame


def _check_budget(slug: str, size_bytes: int) -> None:
    if size_bytes > BUDGET_BYTES_PER_LL_PER_COPY:
        print(
            f"  [over-budget] {slug}: {size_bytes:,} bytes exceeds the W-01 budget of "
            f"{BUDGET_BYTES_PER_LL_PER_COPY:,} bytes ({size_bytes / 1024 / 1024:.1f} MB vs "
            f"{BUDGET_BYTES_PER_LL_PER_COPY / 1024 / 1024:.0f} MB budget)"
        )


def write_and_validate(
    frame: gpd.GeoDataFrame, slug: str, output_dir: Path, dry_run: bool
) -> Path | None:
    """Write the ten-key contract frame to `{output_dir}/boris-{slug}.geojson`, revalidate.

    Under --dry-run, performs every step except the write and the re-read, and prints
    the size the file would have had.
    """
    contract_cols = sorted(c for c in frame.columns if c != "geometry")

    if dry_run:
        payload = frame.to_json(drop_id=True, sort_keys=True)
        size_bytes = len(payload.encode("utf-8"))
        print(
            f"  [dry-run] {slug}: would write {len(frame)} features, "
            f"~{size_bytes / 1024:.0f} KB, columns={contract_cols}"
        )
        _check_budget(slug, size_bytes)
        return None

    output_path = output_dir / f"boris-{slug}.geojson"
    _write_geojson(frame, output_path)

    validate = gpd.read_file(output_path)
    assert len(validate) > 0, f"Written file is empty: {output_path}"
    assert str(validate.crs) == "EPSG:4326", f"Written file has wrong CRS: {validate.crs}"

    size_bytes = output_path.stat().st_size
    print(
        f"  [ok] wrote {output_path.name} ({len(validate)} features, "
        f"{size_bytes / 1024:.0f} KB) columns={contract_cols}"
    )
    _check_budget(slug, size_bytes)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch BORIS (Bodenrichtwertinformationssystem) standard land values per "
            "Living Lab from the BORIS-BB and BORIS-HE WFS services."
        )
    )
    parser.add_argument("--layer", default="boris", help="Layer ID in sources.yaml")
    parser.add_argument("--ll", default=None, help="Restrict to a single Living Lab slug")
    parser.add_argument("--refresh", action="store_true", help="Bypass cache and re-fetch from WFS")
    parser.add_argument("--list", action="store_true", help="List available layer IDs")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and harmonize but do not write into output_dir",
    )

    args = parser.parse_args()

    try:
        layer = get_layer(args.layer)
    except KeyError:
        available = ["boris"]
        print(f"Layer {args.layer!r} not found. Available layers: {available}")
        return

    if args.list:
        print(layer["id"])
        return

    wfs_cfg = layer["wfs"]
    states_cfg = wfs_cfg["states"]
    ll_states = layer["ll_states"]
    semantics_cfg = layer["semantics"]
    output_dir = resolve(wfs_cfg["output_dir"])
    cache_dir = resolve(wfs_cfg["cache_dir"])

    try:
        boundaries = load_boundaries(ll_states, args.ll)
    except SystemExit as exc:
        print(str(exc))
        return

    reference = _compute_recency_reference(semantics_cfg)
    print(f"[boris] W-02 recency reference (rolling window): {reference}")
    print(f"[boris] fetching {layer['id']} for {len(boundaries)} Living Lab(s)...")

    bb_point_index: dict[str, list[dict]] | None = None

    for row in boundaries.itertuples(index=False):
        slug = row.ll_slug
        ll_geom = row.geometry
        state = ll_states[slug]
        state_cfg = states_cfg[state]

        print(f"\n[boris] {slug} ({state}):")

        zones = fetch_zones(slug, ll_geom, state, state_cfg, wfs_cfg, cache_dir, args.refresh)

        if state == "he":
            collected = collect_he(slug, zones)
        else:
            if bb_point_index is None:
                bb_point_index = load_bb_point_index(state_cfg, wfs_cfg, cache_dir, args.refresh)
            collected = collect_bb(slug, zones, bb_point_index, reference)

        harmonised = harmonise(collected, state, slug, reference)
        treated = apply_geometry_treatment(harmonised, slug, ll_geom, wfs_cfg)

        if len(treated) == 0:
            print(f"  [warn] {slug}: 0 features after geometry treatment")
            continue

        write_and_validate(treated, slug, output_dir, args.dry_run)


if __name__ == "__main__":
    main()
