from __future__ import annotations

import argparse
import math
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from _sources import ensure_input_available, find_pmtiles_bin, find_rio_bin, get_layer, load_sources, repo_root, resolve


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build raster PMTiles from sources.yaml entries.")
    parser.add_argument("--layer", help="Layer id from sources.yaml")
    parser.add_argument("--list", action="store_true", help="List available layer ids")
    return parser.parse_args()


def hex_to_rgba(color: str) -> tuple[int, int, int, int]:
    value = color.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Expected 6-digit hex color, got {color}")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4)) + (255,)


def build_colormap(layer: dict, nodata: int | float | None) -> dict[int, tuple[int, int, int, int]]:
    cmap = {int(entry["value"]): hex_to_rgba(entry["color"]) for entry in layer["legend"]}
    if nodata is not None:
        cmap[int(nodata)] = (0, 0, 0, 0)
    return cmap


def build_clip_geometry(layer: dict, source_crs, slug: str | None = None) -> object:
    import geopandas as gpd

    defaults = layer["defaults"]
    clip_path = resolve(defaults["clip_to"])
    clip_buffer_m = defaults.get("clip_buffer_m", 0)
    gdf = gpd.read_file(clip_path)
    if slug is not None:
        gdf = gdf[gdf["ll_slug"] == slug]
        # CLAUDE.md rule: assert non-empty to catch silent clip failures
        assert len(gdf) > 0, f"No features in {clip_path} with ll_slug={slug!r}"
    buffered = gdf.to_crs("EPSG:3857").geometry.union_all().buffer(clip_buffer_m)
    clip_geom = gpd.GeoSeries([buffered], crs="EPSG:3857").to_crs(source_crs).iloc[0]
    return clip_geom


def build_paletted_geotiff(
    layer: dict, input_path: Path, output_tif: Path, slug: str | None = None
) -> tuple[float, float, float, float]:
    import numpy as np
    import rasterio
    from rasterio.enums import ColorInterp, Resampling
    from rasterio.mask import mask
    from rasterio.transform import array_bounds
    from rasterio.warp import calculate_default_transform, reproject

    build_cfg = layer.get("build", {})
    target_crs = build_cfg.get("target_crs") or layer["defaults"]["target_crs"]
    input_cfg = layer["input"]

    with rasterio.open(input_path) as src:
        if src.count != 1:
            raise RuntimeError(f"Expected a single-band categorical raster, found {src.count} bands in {input_path}")

        declared_nodata = input_cfg.get("nodata")
        source_nodata = src.nodata if src.nodata is not None else declared_nodata
        if source_nodata is None:
            source_nodata = 0
        if declared_nodata is not None and src.nodata is not None and declared_nodata != src.nodata:
            print(f"[warn] YAML nodata={declared_nodata} but source nodata={src.nodata}; using source value")

        clip_geom = build_clip_geometry(layer, src.crs, slug=slug)
        clipped, clipped_transform = mask(
            src,
            [clip_geom.__geo_interface__],
            crop=True,
            all_touched=True,
            nodata=source_nodata,
        )

        clipped_nodata_mask = clipped[0] == source_nodata
        if bool(np.all(clipped_nodata_mask)):
            raise RuntimeError(
                f"Clipped raster for layer {layer.get('id')!r} (slug={slug!r}) contains only nodata "
                f"({source_nodata!r}) — the clip geometry likely does not overlap the source raster."
            )

        bounds = array_bounds(clipped.shape[1], clipped.shape[2], clipped_transform)
        dst_transform, dst_width, dst_height = calculate_default_transform(
            src.crs,
            target_crs,
            clipped.shape[2],
            clipped.shape[1],
            *bounds,
        )

        class_profile = src.profile.copy()
        class_profile.update(
            driver="GTiff",
            height=dst_height,
            width=dst_width,
            transform=dst_transform,
            crs=target_crs,
            count=1,
            dtype="uint8",
            nodata=source_nodata,
            compress="deflate",
            tiled=True,
        )

        output_tif.parent.mkdir(parents=True, exist_ok=True)
        class_data = np.full((dst_height, dst_width), source_nodata, dtype=np.uint8)
        reproject(
            source=clipped[0],
            destination=class_data,
            src_transform=clipped_transform,
            src_crs=src.crs,
            src_nodata=source_nodata,
            dst_transform=dst_transform,
            dst_crs=target_crs,
            dst_nodata=source_nodata,
            resampling=Resampling.nearest,
        )

        rgba = np.zeros((4, dst_height, dst_width), dtype=np.uint8)
        for value, color in build_colormap(layer, source_nodata).items():
            mask_value = class_data == value
            if not np.any(mask_value):
                continue
            rgba[0][mask_value] = color[0]
            rgba[1][mask_value] = color[1]
            rgba[2][mask_value] = color[2]
            rgba[3][mask_value] = color[3]

        rgba_profile = class_profile.copy()
        rgba_profile.pop("nodata", None)
        rgba_profile.update(count=4, dtype="uint8", photometric="RGBA")

        with rasterio.open(output_tif, "w", **rgba_profile) as dst:
            dst.write(rgba)
            dst.colorinterp = (
                ColorInterp.red,
                ColorInterp.green,
                ColorInterp.blue,
                ColorInterp.alpha,
            )
            return dst.bounds


def build_mbtiles(paletted_tif: Path, output_mbtiles: Path, min_zoom: int, max_zoom: int, tile_size: int) -> None:
    import mercantile
    import rasterio
    from rasterio.enums import ColorInterp, Resampling
    from rasterio.io import MemoryFile
    from rasterio.warp import transform_bounds

    def png_bytes(tile_data) -> bytes:
        profile = {
            "driver": "PNG",
            "width": tile_size,
            "height": tile_size,
            "count": 4,
            "dtype": "uint8",
        }
        with MemoryFile() as memfile:
            with memfile.open(**profile) as dataset:
                dataset.write(tile_data)
                dataset.colorinterp = (
                    ColorInterp.red,
                    ColorInterp.green,
                    ColorInterp.blue,
                    ColorInterp.alpha,
                )
            return memfile.read()

    output_mbtiles.parent.mkdir(parents=True, exist_ok=True)
    if output_mbtiles.exists():
        output_mbtiles.unlink()

    print(f"[run] python mbtiles writer {paletted_tif} -> {output_mbtiles}")

    # NOTE: sqlite3.Connection's context manager only commits/rolls back the active
    # transaction on exit -- it does NOT close the connection (this is documented
    # sqlite3 behaviour, not a bug in this code). Left as `with ... as conn:`, the
    # file handle stays open after this function returns, which is harmless on Linux
    # but locks the file on Windows and breaks a caller that tries to unlink() the
    # temp mbtiles immediately afterward (as build_land_cover.py's per-LL loop does
    # to avoid accumulating 5x the temp files). Manage the connection lifecycle
    # explicitly with try/finally so it is always closed before this function returns.
    conn = sqlite3.connect(output_mbtiles)
    try:
        with rasterio.open(paletted_tif) as src:
            west, south, east, north = transform_bounds(src.crs, "EPSG:4326", *src.bounds, densify_pts=21)
            west = max(-180 + 1.0e-10, west)
            south = max(-85.051129, south)
            east = min(180 - 1.0e-10, east)
            north = min(85.051129, north)

            cur = conn.cursor()
            cur.execute(
                "CREATE TABLE tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob);"
            )
            cur.execute("CREATE UNIQUE INDEX idx_zcr ON tiles (zoom_level, tile_column, tile_row);")
            cur.execute("CREATE TABLE metadata (name text, value text);")

            metadata = [
                ("name", output_mbtiles.stem),
                ("type", "overlay"),
                ("version", "1.1"),
                ("description", paletted_tif.name),
                ("format", "png"),
                ("bounds", f"{west:.6f},{south:.6f},{east:.6f},{north:.6f}"),
                ("minzoom", str(min_zoom)),
                ("maxzoom", str(max_zoom)),
            ]
            cur.executemany("INSERT INTO metadata (name, value) VALUES (?, ?);", metadata)

            total_tiles = 0
            written_tiles = 0

            for zoom in range(min_zoom, max_zoom + 1):
                for tile in mercantile.tiles(west, south, east, north, [zoom]):
                    total_tiles += 1
                    bounds = mercantile.xy_bounds(tile)
                    window = src.window(bounds.left, bounds.bottom, bounds.right, bounds.top)
                    tile_data = src.read(
                        out_shape=(4, tile_size, tile_size),
                        window=window,
                        boundless=True,
                        fill_value=0,
                        resampling=Resampling.nearest,
                    )
                    if tile_data.shape[0] < 4 or not tile_data[3].any():
                        continue

                    tile_row = int(math.pow(2, zoom)) - tile.y - 1
                    cur.execute(
                        "INSERT INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?);",
                        (zoom, tile.x, tile_row, sqlite3.Binary(png_bytes(tile_data))),
                    )
                    written_tiles += 1

            conn.commit()
            print(f"[ok] wrote {written_tiles}/{total_tiles} tiles to {output_mbtiles.name}")
    finally:
        conn.close()


def convert_pmtiles(output_mbtiles: Path, output_pmtiles: Path) -> None:
    output_pmtiles.parent.mkdir(parents=True, exist_ok=True)
    cmd = [find_pmtiles_bin(), "convert", str(output_mbtiles), str(output_pmtiles)]
    print("[run]", " ".join(cmd))
    subprocess.run(cmd, check=True)


def cleanup_temp_dir(path: Path, attempts: int = 6, delay_s: float = 0.5) -> None:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            shutil.rmtree(path)
            return
        except PermissionError as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(delay_s)
                continue
            break
    if last_error is not None:
        print(f"[warn] could not remove temp dir {path}: {last_error}")


def list_layers() -> None:
    sources = load_sources()
    for layer in sources["layers"]:
        print(layer["id"])


def build_layer(layer_id: str) -> None:
    layer = get_layer(layer_id)
    input_path = ensure_input_available(layer)

    build_cfg = layer.get("build", {})
    min_zoom = int(build_cfg.get("min_zoom", layer["defaults"]["min_zoom"]))
    max_zoom = int(build_cfg.get("max_zoom", layer["defaults"]["max_zoom"]))
    tile_size = int(build_cfg.get("tile_size", layer["defaults"]["tile_size"]))
    output_pmtiles = resolve(layer["output"]["pmtiles"])

    cache_root = repo_root() / "data" / "_cache"
    cache_root.mkdir(parents=True, exist_ok=True)

    temp_dir_path = Path(tempfile.mkdtemp(prefix=f"{layer_id}-", dir=cache_root))
    try:
        paletted_tif = temp_dir_path / f"{layer_id}.tif"
        temp_mbtiles = temp_dir_path / f"{layer_id}.mbtiles"

        bounds = build_paletted_geotiff(layer, input_path, paletted_tif)
        build_mbtiles(paletted_tif, temp_mbtiles, min_zoom, max_zoom, tile_size)
        convert_pmtiles(temp_mbtiles, output_pmtiles)
    finally:
        cleanup_temp_dir(temp_dir_path)

    size_mb = output_pmtiles.stat().st_size / 1024 / 1024
    print(f"[ok] wrote {output_pmtiles.relative_to(repo_root())} ({size_mb:.1f} MB)")
    print(f"[ok] bounds {bounds}")


def main() -> None:
    args = parse_args()
    if args.list:
        list_layers()
        return
    if not args.layer:
        raise SystemExit("Pass --layer <id> or --list")
    build_layer(args.layer)


if __name__ == "__main__":
    main()
