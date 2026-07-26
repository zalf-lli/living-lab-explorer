"""Per-Living-Lab land cover PMTiles orchestrator.

Builds `data/pmtiles/land-cover-{slug}.pmtiles` one Living Lab at a time from the
Impact Observatory / Esri / Microsoft 10 m Annual Land Use Land Cover (9-class)
source tiles registered as `io-lulc-landcover` in sources.yaml.

Processing one Living Lab at a time (rather than mosaicking all tiles and clipping
to the union of all five LLs) keeps peak memory around ~2.2 GB instead of ~11.6 GB,
which is the only variant that reliably builds on a 16 GB machine.

Debugging note: the venv on this machine lives under a non-ASCII OneDrive path.
Any GDAL failure inside rasterio surfaces as a `UnicodeDecodeError` raised from
`rasterio/_err.pyx`, which destroys the real GDAL error message. Never interpret
that as file corruption — check path existence, file size, and URL reachability
independently instead.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from _sources import ensure_input_available, get_layer, repo_root, resolve
from build_pmtiles import (
    build_clip_geometry,
    build_mbtiles,
    build_paletted_geotiff,
    cleanup_temp_dir,
    convert_pmtiles,
)

# Raw ESRI/Impact Observatory v3 class values. 3 and 6 were retired when the v3
# model merged the former "Grass" and "Scrub/Shrub" classes into "Rangeland" (11).
# They must never appear in a valid source raster.
VALID_CLASS_VALUES = {0, 1, 2, 4, 5, 7, 8, 9, 10, 11}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build per-Living-Lab land cover PMTiles from sources.yaml."
    )
    parser.add_argument(
        "--layer", default="io-lulc-landcover", help="Layer id from sources.yaml"
    )
    parser.add_argument(
        "--slug",
        nargs="+",
        help="One or more Living Lab slugs to build (default: all slugs in input.tiles)",
    )
    parser.add_argument(
        "--list", action="store_true", help="Print the slug-to-tile assignment and exit"
    )
    return parser.parse_args()


def list_slugs(layer: dict) -> None:
    tiles = layer["input"]["tiles"]
    for slug, tile in tiles.items():
        print(f"{slug}: {tile}")


def _tile_shim(layer: dict, tile: str) -> dict:
    """Build an ensure_input_available()-compatible shim for a single source tile."""
    input_cfg = layer["input"]
    path = input_cfg["path_pattern"].format(tile=tile)
    download_url = input_cfg["download_url_pattern"].format(tile=tile)
    sha256 = (input_cfg.get("sha256_by_tile") or {}).get(tile)
    return {"input": {"path": path, "download_url": download_url, "sha256": sha256}}


def _sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sweep_stale_temp_dirs(cache_root: Path, layer_id: str) -> None:
    """Remove any leftover temp dirs from earlier interrupted runs before starting a new one."""
    for stale in sorted(cache_root.glob(f"{layer_id}-*")):
        if stale.is_dir():
            print(f"[sweep] removing stale temp dir {stale.name}")
            cleanup_temp_dir(stale)


def _validate_source_raster(tile_path: Path, expected_nodata) -> None:
    """Metadata-only validation — never reads pixel data, so it is cheap even on a 4 GB tile."""
    import rasterio

    with rasterio.open(tile_path) as src:
        if src.count != 1:
            raise RuntimeError(
                f"{tile_path}: expected a single-band raster (count==1), found count={src.count}"
            )
        if src.dtypes[0] != "uint8":
            raise RuntimeError(
                f"{tile_path}: expected dtype=='uint8', found dtype={src.dtypes[0]!r}"
            )
        if src.nodata != expected_nodata:
            raise RuntimeError(
                f"{tile_path}: expected nodata=={expected_nodata!r}, found nodata={src.nodata!r}"
            )


def _class_histogram_for_slug(layer: dict, tile_path: Path, slug: str) -> dict[int, int]:
    """Mask the source tile to one Living Lab and return a {class_value: pixel_count} histogram.

    Also enforces the two highest-value guards in this phase: observed class values must be a
    subset of the valid ESRI v3 taxonomy, and every observed non-zero class must be present in
    the sources.yaml legend (an unlisted class renders fully transparent with no error).
    """
    import numpy as np
    import rasterio
    from rasterio.mask import mask

    with rasterio.open(tile_path) as src:
        clip_geom = build_clip_geometry(layer, src.crs, slug=slug)
        clipped, _ = mask(
            src,
            [clip_geom.__geo_interface__],
            crop=True,
            all_touched=True,
            nodata=src.nodata,
        )

    values, counts = np.unique(clipped[0], return_counts=True)
    histogram = {int(v): int(c) for v, c in zip(values, counts)}

    observed = set(histogram)
    unexpected = observed - VALID_CLASS_VALUES
    assert not unexpected, (
        f"{slug}: unexpected class value(s) {sorted(unexpected)} — values 3 and 6 were retired "
        "in the v3 model; their presence means the wrong source product was fetched"
    )

    legend_values = {int(entry["value"]) for entry in layer["legend"]}
    missing = observed - legend_values - {0}
    assert not missing, (
        f"{slug}: class value(s) {sorted(missing)} present in the data but absent from the "
        "sources.yaml legend — they would render fully transparent"
    )

    return histogram


def _load_histogram_file(histogram_path: Path) -> dict:
    if histogram_path.exists():
        return json.loads(histogram_path.read_text(encoding="utf-8"))
    return {}


def _write_histogram_file(histogram_path: Path, all_histograms: dict) -> None:
    histogram_path.parent.mkdir(parents=True, exist_ok=True)
    histogram_path.write_text(
        json.dumps(all_histograms, indent=2, sort_keys=True), encoding="utf-8"
    )


def build_land_cover(layer_id: str, slugs: list[str] | None) -> None:
    layer = get_layer(layer_id)
    tiles_by_slug = layer["input"]["tiles"]
    target_slugs = slugs or list(tiles_by_slug.keys())

    unknown = [slug for slug in target_slugs if slug not in tiles_by_slug]
    if unknown:
        raise SystemExit(
            f"Unknown slug(s) {unknown}; available slugs: {sorted(tiles_by_slug)}"
        )

    # Fetch and validate each distinct source tile once, even if multiple slugs share it.
    needed_tiles = sorted({tiles_by_slug[slug] for slug in target_slugs})
    tile_paths: dict[str, Path] = {}
    for tile in needed_tiles:
        shim = _tile_shim(layer, tile)
        tile_path = ensure_input_available(shim)
        _validate_source_raster(tile_path, layer["input"].get("nodata", 0))

        pinned = (layer["input"].get("sha256_by_tile") or {}).get(tile)
        if not pinned:
            computed = _sha256_of(tile_path)
            print(
                f"[info] tile {tile} has no pinned digest in input.sha256_by_tile; "
                f"computed sha256={computed} — paste this into sources.yaml "
                f"input.sha256_by_tile.{tile!r} to pin it"
            )
        tile_paths[tile] = tile_path

    cache_root = repo_root() / "data" / "_cache"
    cache_root.mkdir(parents=True, exist_ok=True)
    _sweep_stale_temp_dirs(cache_root, layer_id)

    histogram_path = resolve(layer["output"]["class_histogram"])
    all_histograms = _load_histogram_file(histogram_path)

    build_cfg = layer.get("build", {})
    min_zoom = int(build_cfg.get("min_zoom", layer["defaults"]["min_zoom"]))
    max_zoom = int(build_cfg.get("max_zoom", layer["defaults"]["max_zoom"]))
    tile_size = int(build_cfg.get("tile_size", layer["defaults"]["tile_size"]))

    temp_dir_path = Path(tempfile.mkdtemp(prefix=f"{layer_id}-", dir=cache_root))
    try:
        for slug in target_slugs:
            tile = tiles_by_slug[slug]
            tile_path = tile_paths[tile]

            histogram = _class_histogram_for_slug(layer, tile_path, slug)
            print(f"[histogram] {slug}: {histogram}")
            all_histograms[slug] = {str(k): v for k, v in sorted(histogram.items())}
            _write_histogram_file(histogram_path, all_histograms)

            paletted_tif = temp_dir_path / f"{layer_id}-{slug}.tif"
            temp_mbtiles = temp_dir_path / f"{layer_id}-{slug}.mbtiles"
            output_pmtiles = resolve(
                layer["output"]["pmtiles_pattern"].format(slug=slug)
            )

            build_paletted_geotiff(layer, tile_path, paletted_tif, slug=slug)
            build_mbtiles(paletted_tif, temp_mbtiles, min_zoom, max_zoom, tile_size)
            convert_pmtiles(temp_mbtiles, output_pmtiles)

            paletted_tif.unlink(missing_ok=True)
            temp_mbtiles.unlink(missing_ok=True)

            size_mb = output_pmtiles.stat().st_size / 1024 / 1024
            print(f"[ok] wrote {output_pmtiles.relative_to(repo_root())} ({size_mb:.1f} MB)")
    finally:
        cleanup_temp_dir(temp_dir_path)


def main() -> None:
    args = parse_args()
    layer = get_layer(args.layer)
    if args.list:
        list_slugs(layer)
        return
    build_land_cover(args.layer, args.slug)


if __name__ == "__main__":
    main()
