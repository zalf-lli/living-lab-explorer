from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from python._sources import get_layer, load_sources, repo_root, resolve
from python.generate_metadata import write_metadata


_PLACEHOLDER_RE = re.compile(r"\{[^{}]+\}")


def _pattern_to_glob(pattern: str) -> str:
    """Substitute every `{...}` placeholder in a sources.yaml pattern with `*`.

    Land cover's `pmtiles_pattern` carries one placeholder (`{slug}`); climate's
    carries three (`{variable}`, `{period}`, `{slug}`). A plain
    `.replace("{slug}", "*")` only ever widened the one land-cover/BORIS knew about, so
    it silently matched nothing for climate's three-placeholder pattern. This regex
    substitution tolerates any number of placeholders (including zero, which round-trips
    unchanged), so both per-LL sync functions can share one implementation without
    drifting from each other.
    """
    return _PLACEHOLDER_RE.sub("*", pattern)


STATIC_DATA_FILES = [
    "data/ll_metadata.json",
    "data/nuts1_de.geojson",
    "data/nuts3_ll.geojson",
    "data/nuts3_ll_simplified.geojson",
    "data/ll_boundaries.geojson",
]


def sync_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    print(f"[sync] {source.relative_to(repo_root())} -> {destination.relative_to(repo_root())}")


def generate_landuse_legend() -> None:
    layer = get_layer("landuse-croptypes")
    legend = [
        {
            "value": entry["value"],
            "en": entry["label"]["en"],
            "de": entry["label"]["de"],
            "color": entry["color"],
        }
        for entry in layer["legend"]
    ]
    target = resolve("app/src/data/landuse_legend.js")
    body = (
        "// Generated from data-pipeline/sources/sources.yaml (landuse-croptypes).\n"
        "// Do not edit by hand; run `python data-pipeline/sync.py` after changing sources.yaml.\n"
        f"export const LANDUSE_LEGEND = {json.dumps(legend, indent=2, ensure_ascii=False)}\n"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    print(f"[sync] generated {target.relative_to(repo_root())}")


def generate_land_cover_legend() -> None:
    """Codegen LAND_COVER_LEGEND from the io-lulc-landcover legend in sources.yaml.

    Two filters are applied so the generated legend can never drift from what the
    raster actually contains:
    - value 0 ("no data") is always dropped; build_colormap() already maps nodata to
      transparent from src.nodata, so a "no data" swatch is pure UI noise (the same
      bug CONCERNS.md records against the crop-types legend).
    - when the class histogram (built by build_land_cover.py) is available, any class
      with zero pixels across every Living Lab is dropped too, so classes like
      Snow/Ice or Clouds do not occupy dead legend rows.
    """
    layer = get_layer("io-lulc-landcover")
    histogram_path = resolve(layer["output"]["class_histogram"])

    histogram_totals: dict[int, int] | None = None
    if histogram_path.exists():
        histograms = json.loads(histogram_path.read_text(encoding="utf-8"))
        histogram_totals = {}
        for per_slug in histograms.values():
            for value_str, count in per_slug.items():
                value = int(value_str)
                histogram_totals[value] = histogram_totals.get(value, 0) + count
    else:
        print(
            "[warn] land cover class histogram missing "
            f"({histogram_path.relative_to(repo_root())}); legend not filtered by observed classes"
        )

    legend = []
    for entry in layer["legend"]:
        value = int(entry["value"])
        if value == 0:
            continue
        if histogram_totals is not None and histogram_totals.get(value, 0) == 0:
            continue
        legend.append(
            {
                "value": value,
                "en": entry["label"]["en"],
                "de": entry["label"]["de"],
                "color": entry["color"],
            }
        )

    target = resolve("app/src/data/land_cover_legend.js")
    body = (
        "// Generated from data-pipeline/sources/sources.yaml (io-lulc-landcover).\n"
        "// Do not edit by hand; run `python data-pipeline/sync.py` after changing sources.yaml.\n"
        f"export const LAND_COVER_LEGEND = {json.dumps(legend, indent=2, ensure_ascii=False)}\n"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    print(f"[sync] generated {target.relative_to(repo_root())}")


def generate_layer_sources() -> None:
    """Emit per-layer provenance metadata for the in-app info control."""
    sources = load_sources()
    entries = []
    for layer in sources.get("layers", []):
        app_layer = layer.get("app_layer")
        if not app_layer:
            continue
        src = layer.get("source", {}) or {}
        title = layer.get("title", {}) or {}
        description = layer.get("description", {}) or {}
        entry = {
            "id": layer.get("id"),
            "appLayer": app_layer,
            "title": {"en": title.get("en", ""), "de": title.get("de", "")},
            "description": {"en": description.get("en", ""), "de": description.get("de", "")},
            "provider": src.get("provider", ""),
            "dataset": src.get("dataset", ""),
            "url": src.get("url", ""),
            "license": src.get("license", ""),
            "attribution": src.get("attribution", ""),
            "citation": src.get("citation", ""),
        }
        # Layers published by more than one state authority (e.g. boris) declare a
        # sources_by_state map alongside the flat `source` fallback above. Only those
        # layers gain these two extra keys, so every pre-existing generated record stays
        # byte-identical (T-07-13).
        sources_by_state = layer.get("sources_by_state")
        if sources_by_state:
            entry["providersByState"] = sources_by_state
            entry["llStates"] = layer.get("ll_states", {}) or {}
        entries.append(entry)

    target = resolve("app/src/data/layer_sources.js")
    body = (
        "// Generated from data-pipeline/sources/sources.yaml.\n"
        "// Do not edit by hand; run `python data-pipeline/sync.py` after changing sources.yaml.\n"
        f"export const LAYER_SOURCES = {json.dumps(entries, indent=2, ensure_ascii=False)}\n\n"
        "export const LAYER_SOURCE_INDEX = new Map(LAYER_SOURCES.map((s) => [s.appLayer, s]))\n"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    print(f"[sync] generated {target.relative_to(repo_root())}")


def sync_pmtiles() -> None:
    sources = load_sources()
    for layer in sources["layers"]:
        output = layer.get("output", {})
        pmtiles_path = output.get("pmtiles")
        sync_target = output.get("sync_to")
        if not pmtiles_path or not sync_target:
            continue
        source = resolve(pmtiles_path)
        if not source.exists():
            print(f"[skip] missing {source.relative_to(repo_root())}")
            continue
        sync_file(source, resolve(sync_target))


def _sync_matched_pattern(pattern: str) -> int:
    """Glob a sources.yaml pattern (any number of `{...}` placeholders) and mirror every
    match into app/public/, deriving the destination purely from the match's repo-relative
    path. Returns the number of files synced.

    A wildcarded glob is a wider match surface than a literal path, so any match whose
    resolved path escapes the repo root is skipped with a [warn] rather than copied --
    this guards against a stray symlink or an unexpected match writing outside
    app/public/data/ (T-08-16).
    """
    root = repo_root()
    matches = sorted(root.glob(_pattern_to_glob(pattern)))
    if not matches:
        print(f"[skip] no files matched {pattern}")
        return 0
    synced = 0
    for source in matches:
        resolved_source = source.resolve()
        resolved_root = root.resolve()
        if resolved_root not in resolved_source.parents and resolved_source != resolved_root:
            print(f"[warn] match escapes repo root, skipping: {source}")
            continue
        rel_path = source.relative_to(root)
        sync_file(source, resolve(Path("app/public") / rel_path))
        synced += 1
    print(f"[sync] {synced}/{len(matches)} files matched {pattern}")
    return synced


def sync_pmtiles_per_ll() -> None:
    # Unlike sync_pmtiles() (which honors an explicit output.sync_to), this
    # function has no separate "sync pattern" config key. The destination for
    # each matched file is always derived from its path relative to the repo
    # root, prefixed with app/public/ -- sources.yaml intentionally has no
    # output.sync_pattern key for per-LL layers. The glob tolerates any number of
    # `{...}` placeholders (via _pattern_to_glob), since the climate pattern carries
    # three (`{variable}`, `{period}`, `{slug}`) where land cover and BORIS carry one.
    sources = load_sources()
    for layer in sources["layers"]:
        output = layer.get("output", {})
        pattern = output.get("pmtiles_pattern")
        if not pattern:
            continue
        _sync_matched_pattern(pattern)


def sync_vector_geojson() -> None:
    sources = load_sources()
    for layer in sources["layers"]:
        if layer.get("kind") != "vector":
            continue
        output = layer.get("output", {})
        geojson_pattern = output.get("geojson_pattern")
        if not geojson_pattern:
            continue
        _sync_matched_pattern(geojson_pattern)


def sync_to_app() -> None:
    write_metadata()
    print("[sync] generated data/ll_metadata.json from data/ll_content.json")
    for rel_path in STATIC_DATA_FILES:
        source = resolve(rel_path)
        sync_file(source, resolve(f"app/public/{rel_path}"))
    sync_pmtiles()
    sync_pmtiles_per_ll()
    sync_vector_geojson()
    generate_landuse_legend()
    generate_land_cover_legend()
    generate_layer_sources()


if __name__ == "__main__":
    sync_to_app()
