"""Fetch BfN Schutzgebiete (Natura 2000 SCI/SPA + NSG) per Living Lab via WFS.

Writes data/geojson/protected-areas-{slug}.geojson (EPSG:4326).
Full polygons for every site intersecting the LL boundary (not clipped).
"""
from __future__ import annotations

import argparse
import tempfile
import time
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from _sources import get_layer, repo_root, resolve

# Bundesland (state) code to bilingual authority name mapping
BUNDESLAND = {
    "BW": ("Baden-Württemberg", "Baden-Württemberg"),
    "BY": ("Bavaria", "Bayern"),
    "BE": ("Berlin", "Berlin"),
    "BB": ("Brandenburg", "Brandenburg"),
    "HB": ("Bremen", "Bremen"),
    "HH": ("Hamburg", "Hamburg"),
    "HE": ("Hesse", "Hessen"),
    "MV": ("Mecklenburg-Vorpommern", "Mecklenburg-Vorpommern"),
    "NI": ("Lower Saxony", "Niedersachsen"),
    "NW": ("North Rhine-Westphalia", "Nordrhein-Westfalen"),
    "RP": ("Rhineland-Palatinate", "Rheinland-Pfalz"),
    "SL": ("Saarland", "Saarland"),
    "SN": ("Saxony", "Sachsen"),
    "ST": ("Saxony-Anhalt", "Sachsen-Anhalt"),
    "SH": ("Schleswig-Holstein", "Schleswig-Holstein"),
    "TH": ("Thuringia", "Thüringen"),
}

# Per-designation metadata: field names, UI labels, and data details
DESIGNATIONS = {
    "natura2000-sci": {
        "designation": "Natura 2000 SCI",
        "name_field": "Gebietsname",
        "state_field": "Bundesland",
        "site_code_field": "Gebietsnummer",
        "area_field": "FLAECHE",
        "date_field": "Datum_der_gueltigen_Verordnung",
        "year_field": None,
        "label_en": "Special Conservation Area",
        "label_de": "FFH-Gebiet",
    },
    "natura2000-spa": {
        "designation": "Natura 2000 SPA",
        "name_field": "NAME",
        "state_field": "BL",
        "site_code_field": "SITECODE",
        "area_field": "FLAECHE",
        "date_field": "LEG_DATE",
        "year_field": None,
        "label_en": "Special Protection Area",
        "label_de": "Vogelschutzgebiet",
    },
    "naturschutzgebiet": {
        "designation": "Naturschutzgebiet",
        "name_field": "NAME",
        "state_field": "BL",
        "site_code_field": "ID",
        "area_field": "FLAECHE",
        "date_field": "LEG_DATE",
        "year_field": "JAHR",
        "label_en": "Nature Reserve",
        "label_de": "Naturschutzgebiet",
    },
}


def _write_geojson(frame: gpd.GeoDataFrame, output_path: Path) -> None:
    """Write GeoDataFrame as sorted-key GeoJSON (CLAUDE.md rule)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = frame.to_json(drop_id=True, sort_keys=True)
    output_path.write_text(payload + "\n", encoding="utf-8")


def _bbox_param(geom, pad: float = 0.05, bbox_crs: str = "urn:ogc:def:crs:EPSG::4326") -> str:
    """Build a WFS BBOX parameter from a geometry with optional padding.

    lat,lon order with the urn:ogc:def:crs:EPSG::4326 suffix is MANDATORY.
    Any other spelling (lon,lat, plain EPSG:4326, native EPSG:25832, no suffix)
    returns HTTP 200 with zero features and no error message.
    """
    minx, miny, maxx, maxy = geom.bounds  # lon/lat, EPSG:4326
    return f"{miny - pad:.4f},{minx - pad:.4f},{maxy + pad:.4f},{maxx + pad:.4f},{bbox_crs}"


def _get(url: str, params: dict, max_bytes: int) -> bytes:
    """Fetch URL with exponential backoff retry on 403 / RequestException.

    Args:
        url: Base URL for the request
        params: Query parameters dict
        max_bytes: Maximum response size (raise if exceeded)

    Returns:
        Response bytes

    Raises:
        RuntimeError: On final failed attempt after 4 retries, or if response exceeds max_bytes
    """
    retries = 4
    for attempt in range(retries):
        try:
            r = requests.get(
                url,
                params=params,
                headers={"User-Agent": "ll-explorer-pipeline/1.0 (+https://zalf.de)"},
                timeout=300,
            )
            if r.status_code == 403 and attempt < retries - 1:
                wait = 2 ** attempt
                print(f"  [retry {attempt+1}/{retries-1} in {wait}s] BfN WAF returned 403")
                time.sleep(wait)
                continue
            r.raise_for_status()
            # Check response size before returning
            if len(r.content) > max_bytes:
                raise RuntimeError(
                    f"Response size {len(r.content)} bytes exceeds max_bytes {max_bytes}"
                )
            return r.content
        except requests.RequestException as exc:
            if attempt == retries - 1:
                raise RuntimeError(
                    f"Failed to fetch {url} after {retries} attempts. "
                    f"If the last {retries} failures were HTTP 403, the BfN WAF may be blocking. "
                    f"A sustained 403 is not a transient error — report and retry later rather than hammer the endpoint."
                ) from exc
            wait = 2 ** attempt
            print(f"  [retry {attempt+1}/{retries-1} in {wait}s] {exc.__class__.__name__}")
            time.sleep(wait)


def _fetch_designation(
    key: str, cfg: dict, typename: str, ll_slug: str, ll_geom, wfs_cfg: dict, cache_dir: Path, refresh: bool
) -> gpd.GeoDataFrame:
    """Fetch one designation (SCI/SPA/NSG) for one Living Lab, with caching.

    Args:
        key: Designation key (natura2000-sci, natura2000-spa, naturschutzgebiet)
        cfg: DESIGNATIONS[key] config dict
        typename: Full typename for the WFS TYPENAMES parameter
        ll_slug: Living Lab slug for cache key
        ll_geom: Living Lab geometry (EPSG:4326)
        wfs_cfg: WFS config from sources.yaml
        cache_dir: Directory to cache raw GML (gitignored)
        refresh: If True, skip cache and re-fetch

    Returns:
        GeoDataFrame with normalised features for this designation

    Raises:
        RuntimeError: On WFS error, CRS mismatch, geometry validation failure, etc.
    """
    cache_path = cache_dir / f"{ll_slug}__{key}.gml"

    # Try to use cached GML if available and not refreshing
    if cache_path.exists() and not refresh:
        print(f"  [cache] {ll_slug}/{key}")
        raw = cache_path.read_bytes()
    else:
        # Fetch from WFS
        bbox = _bbox_param(ll_geom, pad=wfs_cfg["bbox_pad_deg"], bbox_crs=wfs_cfg["bbox_crs"])
        params = {
            "SERVICE": "WFS",
            "VERSION": wfs_cfg["version"],
            "REQUEST": "GetFeature",
            "TYPENAMES": typename,
            "BBOX": bbox,
            "COUNT": wfs_cfg["count"],
            # NOTE: no SRSNAME (flips axis order) and no OUTPUTFORMAT (drops edge features)
        }
        raw = _get(wfs_cfg["url"], params, wfs_cfg["max_response_bytes"])

        # Cache the raw response
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(raw)

    # Extract numberMatched and numberReturned (byte-slicing, not XML parsing, to avoid XXE surface)
    matched_bytes = raw.split(b'numberMatched="')[1].split(b'"')[0]
    returned_bytes = raw.split(b'numberReturned="')[1].split(b'"')[0]
    matched = int(matched_bytes)
    returned = int(returned_bytes)

    if matched == 0:
        raise RuntimeError(
            f"[error] {ll_slug}/{key}: 0 features matched. "
            "BBOX axis order (lat,lon) and urn:ogc:def:crs:EPSG::4326 suffix are mandatory."
        )
    if matched != returned:
        raise RuntimeError(
            f"[error] {ll_slug}/{key}: server truncated {returned}/{matched}. "
            "Add STARTINDEX paging to fetch all features."
        )

    # Parse GML via GDAL, using a temp directory to keep .gfs sidecars out of the repo
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"{key}.gml"
        path.write_bytes(raw)
        frame = gpd.read_file(path)

    # Validate CRS
    if str(frame.crs) != wfs_cfg["source_crs"]:
        raise RuntimeError(
            f"[error] {ll_slug}/{key}: expected {wfs_cfg['source_crs']}, got {frame.crs}"
        )

    # Repair invalid geometries (CLAUDE.md rule: ~1% of BfN features are invalid on read)
    frame.geometry = frame.geometry.make_valid()
    frame = frame.to_crs("EPSG:4326")

    # Filter to features intersecting the LL (D-03: no clipping, full polygons)
    selected = frame[frame.geometry.intersects(ll_geom)].copy()

    return _normalise(selected, key, cfg)


def _normalise(frame: gpd.GeoDataFrame, key: str, cfg: dict) -> gpd.GeoDataFrame:
    """Normalise one designation's GeoDataFrame to the UI contract.

    The three BfN schemas are inconsistent (FFH vs SPA/NSG field names and types).
    This function maps all three onto one contract with these properties:
    name, name_de, name_en, designation, designation_de, designation_en,
    area_ha, established_year, authority_en, authority_de, site_code, geometry

    Args:
        frame: GeoDataFrame with raw BfN attributes
        key: Designation key (natura2000-sci, etc.)
        cfg: DESIGNATIONS[key] config dict

    Returns:
        Normalised GeoDataFrame with contract properties only
    """
    result = gpd.GeoDataFrame(crs="EPSG:4326")
    result["geometry"] = frame.geometry

    # Name fields (BfN publishes German only; set English equal to German)
    result["name_de"] = frame[cfg["name_field"]].astype(str)
    result["name_en"] = result["name_de"]
    result["name"] = result["name_de"]

    # Designation (frontend style-map keys)
    result["designation"] = cfg["designation"]
    result["designation_en"] = cfg["label_en"]
    result["designation_de"] = cfg["label_de"]

    # Area in hectares (confirmed as hectares in research)
    result["area_ha"] = frame[cfg["area_field"]].astype(float).round(1)

    # Established year (prefer year_field if present, else parse date_field)
    def extract_year(row):
        if cfg["year_field"] and cfg["year_field"] in row.index:
            year_val = row[cfg["year_field"]]
            if pd.notna(year_val):
                return int(year_val)
        # Try to extract 4-digit year from date field
        date_val = row[cfg["date_field"]]
        if pd.notna(date_val):
            date_str = str(date_val)[:4]
            try:
                return int(date_str)
            except ValueError:
                pass
        return None

    result["established_year"] = frame.apply(extract_year, axis=1)

    # Authority (state name from Bundesland code)
    def get_authority(row):
        code = row[cfg["state_field"]]
        if pd.notna(code):
            code_str = str(code).strip()
            return BUNDESLAND.get(code_str, (None, None))
        return (None, None)

    authorities = frame.apply(get_authority, axis=1)
    result["authority_en"] = authorities.apply(lambda x: x[0])
    result["authority_de"] = authorities.apply(lambda x: x[1])

    # Site code (stable identifier)
    result["site_code"] = frame[cfg["site_code_field"]].astype(str)

    # Coerce datetime columns to string, and numpy scalars to native Python types
    for col in result.columns:
        if col == "geometry":
            continue
        # Convert datetime to string
        if result[col].dtype == "object":
            result[col] = result[col].apply(lambda x: str(x) if pd.notna(x) else None)
        # Convert numpy scalars
        result[col] = result[col].apply(lambda x: x.item() if hasattr(x, "item") else x)
        # Convert NaN to None
        result[col] = result[col].apply(lambda x: None if pd.isna(x) else x)

    return result


def main():
    """Fetch BfN protected areas for Living Labs and write per-LL GeoJSON files."""
    parser = argparse.ArgumentParser(
        description="Fetch BfN Schutzgebiete (Natura 2000 SCI/SPA + NSG) per Living Lab via WFS"
    )
    parser.add_argument("--layer", default="bfn-schutzgebiete", help="Layer ID in sources.yaml")
    parser.add_argument("--ll", default=None, help="Restrict to single Living Lab slug")
    parser.add_argument("--refresh", action="store_true", help="Bypass cache and re-fetch from WFS")
    parser.add_argument("--list", action="store_true", help="List available layer IDs")

    args = parser.parse_args()

    # Load layer config
    try:
        layer = get_layer(args.layer)
    except KeyError:
        available = ["bfn-schutzgebiete"]
        print(f"Layer {args.layer!r} not found. Available layers: {available}")
        return

    if args.list:
        print(args.layer)
        return

    wfs_cfg = layer["wfs"]
    output_dir = resolve(wfs_cfg["output_dir"])
    cache_dir = resolve("data/_cache/protected-areas")

    # Read LL boundaries
    boundaries = gpd.read_file(resolve("data/ll_boundaries.geojson"))
    assert "ll_slug" in boundaries.columns, "ll_boundaries.geojson missing ll_slug column"
    assert boundaries.crs is not None and str(boundaries.crs) == "EPSG:4326", \
        "ll_boundaries.geojson must have EPSG:4326 CRS"

    # Optionally filter to one LL
    if args.ll:
        if args.ll not in boundaries["ll_slug"].values:
            available = list(boundaries["ll_slug"].values)
            print(f"Living Lab {args.ll!r} not found. Available: {available}")
            return
        boundaries = boundaries[boundaries["ll_slug"] == args.ll]

    print(f"[input] Fetching {layer['id']} for {len(boundaries)} Living Lab(s)...")

    # Fetch and write per-LL GeoJSON
    for row in boundaries.itertuples(index=False):
        ll_slug = row.ll_slug
        ll_geom = row.geometry

        print(f"\n[input] {ll_slug}:")

        # Fetch all three designations for this LL
        parts = []
        for key, typename in wfs_cfg["typenames"].items():
            cfg = DESIGNATIONS[key]
            part = _fetch_designation(key, cfg, typename, ll_slug, ll_geom, wfs_cfg, cache_dir, args.refresh)
            parts.append(part)

        # Concatenate all three designations into one GeoDataFrame
        merged = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), crs="EPSG:4326")
        merged["ll_slug"] = ll_slug

        # Apply coordinate precision rounding if configured (D-08: topology-aware rounding, not simplification)
        if wfs_cfg.get("coordinate_precision") is not None:
            from shapely import set_precision
            precision = wfs_cfg["coordinate_precision"]
            merged.geometry = merged.geometry.apply(lambda g: set_precision(g, grid_size=precision))
            merged.geometry = merged.geometry.make_valid()
            assert merged.geometry.is_valid.all(), f"Invalid geometries after precision rounding for {ll_slug}"

        if len(merged) == 0:
            print(f"  [warn] {ll_slug}: 0 features after intersect (legitimate empty state)")
        else:
            # Write and validate
            output_path = output_dir / f"protected-areas-{ll_slug}.geojson"
            _write_geojson(merged, output_path)

            # Re-read and validate
            validate = gpd.read_file(output_path)
            assert len(validate) > 0, f"Written file is empty: {output_path}"
            assert str(validate.crs) == "EPSG:4326", f"Written file has wrong CRS: {validate.crs}"

            file_size_kb = output_path.stat().st_size / 1024
            print(f"  [ok] wrote {output_path.name} ({len(validate)} features, {file_size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
