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


def _format_climate_number(value: float, lang: str, *, signed: bool) -> str:
    """Format one legend-band boundary value. `signed` forces an explicit +/- prefix
    (change-mode bands, D-11); baseline bands pass signed=False so a positive baseline
    reading never grows a spurious "+". English uses a point decimal separator, German a
    comma -- both formatted here so the app never re-derives locale-aware number text."""
    text = f"{value:+.1f}" if signed else f"{value:.1f}"
    if lang == "de":
        text = text.replace(".", ",")
    return text


def _format_climate_band_label(
    low: float | None, high: float | None, unit: str, lang: str, *, signed: bool
) -> str:
    """One band's bilingual range label. `low is None` marks the lowest band (open
    below -- a less-than form); `high is None` marks the highest band (open above -- a
    greater-than form); a clamped extreme pixel is honestly labelled either way rather
    than falsely bounded. An en dash (not a hyphen) separates the two bounds of a
    two-sided band so a negative-to-negative change band (e.g. bio18's precipitation
    percent change) never reads as an ambiguous double hyphen."""
    if low is None:
        return f"< {_format_climate_number(high, lang, signed=signed)} {unit}"
    if high is None:
        return f"> {_format_climate_number(low, lang, signed=signed)} {unit}"
    return (
        f"{_format_climate_number(low, lang, signed=signed)}"
        f" – {_format_climate_number(high, lang, signed=signed)} {unit}"
    )


def _climate_bands_for_mode(breaks: list, colors: list, unit: dict, *, signed: bool) -> list:
    """Build the {value, en, de, color} band array for one (variable, mode).

    `breaks` carries N+1 boundary values for N colours (build_continuous_colormap's own
    invariant, data/climate_color_breaks.json). The *interior* breaks (breaks[1:-1]) are
    the values classify() actually bins against -- the outermost two breaks are the
    pooled data's observed min/max, not a hard cutoff, so the lowest and highest bands
    are intentionally open-ended.
    """
    interior = breaks[1:-1]
    bounds = [None, *interior, None]
    bands = []
    for index, color in enumerate(colors):
        low = bounds[index]
        high = bounds[index + 1]
        bands.append(
            {
                "value": f"b{index}",
                "en": _format_climate_band_label(low, high, unit["en"], "en", signed=signed),
                "de": _format_climate_band_label(low, high, unit["de"], "de", signed=signed),
                "color": color,
            }
        )
    return bands


def generate_climate_legend() -> None:
    """Codegen CLIMATE_VARIABLES / CLIMATE_LEGEND / CLIMATE_RAMP_SHAPE from sources.yaml's
    chelsa-climate `climate.variables` block (ordering, family, unit, delta unit) and
    data/climate_color_breaks.json (the Pass-0 shared cross-Living-Lab breakpoints, D-09).

    Modelled on generate_land_cover_legend() in spirit, but unlike land cover's flat
    per-value legend, climate's legend is per-variable and per-mode (baseline/change),
    since D-11/D-12 make it unit-aware and sign-aware in a way no categorical layer
    needed to be.

    `change` is now per-horizon (climate-coarse-change-bins debug fix, 2026-07-31): each
    of the two horizon tokens (`2041_2070`, `2071_2100`) gets its own band array and ramp
    verdict, since the two horizons no longer share one pooled colour scale. `baseline`
    is unchanged -- one flat block, one band array.
    """
    layer = get_layer("chelsa-climate")
    breaks_path = resolve(layer["output"]["color_breaks"])
    if not breaks_path.exists():
        print(
            "[warn] climate colour breaks missing "
            f"({breaks_path.relative_to(repo_root())}); climate_legend.js not generated -- "
            "run data-pipeline/python/compute_climate_color_breaks.py first"
        )
        return

    color_breaks = json.loads(breaks_path.read_text(encoding="utf-8"))
    variables = layer["climate"]["variables"]  # dict preserves sources.yaml key order

    climate_variables = []
    climate_legend: dict = {}
    climate_ramp_shape: dict = {}
    for variable_id, config in variables.items():
        climate_variables.append(
            {
                "id": variable_id,
                "family": config["family"],
                "unit": {"en": config["unit"]["en"], "de": config["unit"]["de"]},
                "deltaUnit": {"en": config["delta_unit"]["en"], "de": config["delta_unit"]["de"]},
                "labelKey": f"climate.variable.{variable_id}",
                "legendNoteKey": f"legend.climate.note.{variable_id}",
            }
        )

        variable_breaks = color_breaks[variable_id]

        baseline_block = variable_breaks["baseline"]
        baseline_bands = _climate_bands_for_mode(
            baseline_block["breaks"], baseline_block["colors"], baseline_block["unit"], signed=False
        )

        change_bands_by_horizon: dict = {}
        change_ramp_by_horizon: dict = {}
        for horizon, block in variable_breaks["change"].items():
            change_bands_by_horizon[horizon] = _climate_bands_for_mode(
                block["breaks"], block["colors"], block["unit"], signed=True
            )
            change_ramp_by_horizon[horizon] = block["ramp"]

        climate_legend[variable_id] = {"baseline": baseline_bands, "change": change_bands_by_horizon}
        climate_ramp_shape[variable_id] = {"baseline": baseline_block["ramp"], "change": change_ramp_by_horizon}

    assert len(climate_variables) == 4, (
        f"CLIMATE_VARIABLES must carry exactly 4 entries (D-05), got {len(climate_variables)}"
    )
    assert climate_variables[0]["family"] == "heat", (
        "CLIMATE_VARIABLES[0] must be a heat-family variable "
        "(D-08: GDD is the Climate tab's default variable)"
    )

    target = resolve("app/src/data/climate_legend.js")
    body = (
        "// Generated from data-pipeline/sources/sources.yaml (chelsa-climate) and data/climate_color_breaks.json.\n"
        "// Do not edit by hand; run `python data-pipeline/sync.py` after changing sources.yaml.\n"
        f"export const CLIMATE_VARIABLES = {json.dumps(climate_variables, indent=2, ensure_ascii=False)}\n\n"
        f"export const CLIMATE_LEGEND = {json.dumps(climate_legend, indent=2, ensure_ascii=False)}\n\n"
        f"export const CLIMATE_RAMP_SHAPE = {json.dumps(climate_ramp_shape, indent=2, ensure_ascii=False)}\n"
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
    generate_climate_legend()
    generate_layer_sources()


if __name__ == "__main__":
    sync_to_app()
