from __future__ import annotations

import json
import re

import yaml

from conftest import repo_root

# New module (plan 12-04) rather than an addition to test_pipeline_outputs.py, so plan
# 12-11 can add the report-PDF tests to that file in a later wave without a merge conflict.
#
# These tests read the committed data/report_tokens.json artifact only -- they never
# re-invoke the JS generator (D-21's "tests run from a clean state without re-invoking the
# generator" convention).

HEX_COLOR_RE = re.compile(r"^#[0-9a-f]{6}$", re.IGNORECASE)


def load_report_tokens() -> dict:
    path = repo_root() / "data" / "report_tokens.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_sources() -> dict:
    path = repo_root() / "data-pipeline" / "sources" / "sources.yaml"
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def get_layer(layer_id: str) -> dict:
    sources = load_sources()
    for layer in sources.get("layers", []):
        if layer["id"] == layer_id:
            return layer
    raise AssertionError(f"Layer {layer_id!r} not found in sources.yaml")


def test_report_tokens_shape() -> None:
    """
    Locks the top-level contract data-pipeline/R/theme_llexplorer.R (plan 12-06) reads:
    exact top-level keys, exact chart/palettes/soil sub-keys, and that every colour-bearing
    value in the bundle is a plain #rrggbb literal (T-12-15 -- a value that could act as a
    Typst or R expression rather than a colour literal must never reach the render).
    """
    tokens = load_report_tokens()

    assert set(tokens) == {"theme", "font", "palettes", "chart", "strings"}

    chart = tokens["chart"]
    assert chart["maxBars"] == 6
    assert len(chart["rankColors"]) == 6
    assert "otherColor" in chart

    palettes = tokens["palettes"]
    assert set(palettes) == {"agriculture", "landscape", "soil", "economic", "climate"}

    soil = palettes["soil"]
    assert set(soil) == {
        "groups",
        "fallback",
        "waterFill",
        "waterStroke",
        "specialFill",
        "specialStroke",
        "unitStroke",
    }

    # Every colour-bearing location named in 12-04-PLAN.md's <interfaces> block must hold a
    # plain #rrggbb literal.
    colors: list[tuple[str, object]] = []
    colors.extend((f"theme.{key}", value) for key, value in tokens["theme"].items())
    colors.extend(
        (f"palettes.agriculture[{i}].color", entry["color"])
        for i, entry in enumerate(palettes["agriculture"])
    )
    colors.extend(
        (f"palettes.landscape[{i}].color", entry["color"])
        for i, entry in enumerate(palettes["landscape"])
    )
    colors.extend((f"palettes.soil.groups.{key}", value) for key, value in soil["groups"].items())
    colors.extend((f"palettes.soil.fallback[{i}]", value) for i, value in enumerate(soil["fallback"]))
    colors.append(("palettes.soil.waterFill", soil["waterFill"]))
    colors.append(("palettes.soil.waterStroke", soil["waterStroke"]))
    colors.append(("palettes.soil.specialFill", soil["specialFill"]))
    colors.append(("palettes.soil.specialStroke", soil["specialStroke"]))
    colors.append(("palettes.soil.unitStroke", soil["unitStroke"]))
    colors.extend(
        (f"palettes.economic.ramp[{i}]", value) for i, value in enumerate(palettes["economic"]["ramp"])
    )
    colors.append(("palettes.economic.noDataFill", palettes["economic"]["noDataFill"]))
    for variable_id, per_variable in palettes["climate"]["legend"].items():
        for i, band in enumerate(per_variable["baseline"]):
            colors.append((f"palettes.climate.legend.{variable_id}.baseline[{i}].color", band["color"]))
        for period, bands in per_variable["change"].items():
            for i, band in enumerate(bands):
                colors.append(
                    (f"palettes.climate.legend.{variable_id}.change.{period}[{i}].color", band["color"])
                )
    colors.extend((f"chart.rankColors[{i}]", value) for i, value in enumerate(chart["rankColors"]))
    colors.append(("chart.otherColor", chart["otherColor"]))

    for path, value in colors:
        assert isinstance(value, str) and HEX_COLOR_RE.match(value), (
            f"{path} = {value!r} is not a #rrggbb colour literal"
        )


def test_report_tokens_agree_with_sources_yaml() -> None:
    """
    T-12-18: fails the suite when the app's legends change without a regenerated bundle,
    so a PDF can never quietly ship a stale legend.

    palettes.agriculture reproduces landuse-croptypes' legend: stanza exactly -- that
    codegen path (sync.py::generate_landuse_legend) has no filtering.

    palettes.landscape reproduces io-lulc-landcover's legend: stanza minus the classes
    sync.py::generate_land_cover_legend() itself drops before ever writing
    app/src/data/land_cover_legend.js: value 0 ("no data"), and -- when the class histogram
    is available -- any class with zero pixels across every Living Lab (Snow / ice, value 9,
    per data/land_cover_class_histogram.json). Comparing against the raw, unfiltered
    sources.yaml stanza would make this test permanently red against intentional,
    already-shipped app behaviour; replicating sync.py's own filter is what makes this test
    agree with what the app (and therefore report_tokens.json) actually paints.
    """
    tokens = load_report_tokens()
    palettes = tokens["palettes"]

    agriculture_stanza = get_layer("landuse-croptypes")["legend"]
    expected_agriculture = [
        {"value": entry["value"], "en": entry["label"]["en"], "de": entry["label"]["de"], "color": entry["color"]}
        for entry in agriculture_stanza
    ]
    assert palettes["agriculture"] == expected_agriculture

    landscape_layer = get_layer("io-lulc-landcover")
    landscape_stanza = landscape_layer["legend"]
    histogram_path = repo_root() / landscape_layer["output"]["class_histogram"]
    assert histogram_path.exists(), f"Missing {histogram_path}"
    with histogram_path.open("r", encoding="utf-8") as handle:
        histograms = json.load(handle)
    histogram_totals: dict[int, int] = {}
    for per_slug in histograms.values():
        for value_str, count in per_slug.items():
            value = int(value_str)
            histogram_totals[value] = histogram_totals.get(value, 0) + count

    expected_landscape = [
        {"value": int(entry["value"]), "en": entry["label"]["en"], "de": entry["label"]["de"], "color": entry["color"]}
        for entry in landscape_stanza
        if int(entry["value"]) != 0 and histogram_totals.get(int(entry["value"]), 0) > 0
    ]
    assert palettes["landscape"] == expected_landscape


def test_report_tokens_strings_cover_report_namespace() -> None:
    """
    Asserts strings.en/de each carry the namespaces the report needs, that both languages'
    key sets are identical at every level of the report namespace, and that the eleven
    report.* keys plan 12-01 introduced are all present and non-empty in both languages.
    """
    tokens = load_report_tokens()
    strings = tokens["strings"]
    assert set(strings) == {"en", "de"}

    required_namespaces = {"report", "kpi", "layers", "legend", "climate", "llDetail"}
    for lang in ("en", "de"):
        assert required_namespaces <= set(strings[lang]), (
            f"strings.{lang} is missing namespaces {required_namespaces - set(strings[lang])}"
        )

    def keys_deep(value, prefix: str = "") -> set[str]:
        if not isinstance(value, dict):
            return {prefix}
        keys: set[str] = set()
        for key, sub_value in value.items():
            path = f"{prefix}.{key}" if prefix else key
            keys |= keys_deep(sub_value, path)
        return keys

    en_report_keys = keys_deep(strings["en"]["report"])
    de_report_keys = keys_deep(strings["de"]["report"])
    assert en_report_keys == de_report_keys, (
        f"report namespace key sets differ: en-only={en_report_keys - de_report_keys}, "
        f"de-only={de_report_keys - en_report_keys}"
    )

    expected_report_keys = {
        "documentTitle",
        "subtitle",
        "regions",
        "locatorCaption",
        "contents",
        "kpiHeading",
        "mapHeading",
        "chartHeading",
        # Checkpoint review round 2 (plan 12-10), Defect 4: specific, source-aware figure
        # captions -- added alongside the pre-existing generic mapHeading/chartHeading pair
        # above (still used elsewhere), not as a replacement for them.
        "mapCaption",
        "chartCaption",
        "generated",
        "basemapCredit",
        "noData",
    }
    assert len(expected_report_keys) == 13
    assert set(strings["en"]["report"]) == expected_report_keys
    assert set(strings["de"]["report"]) == expected_report_keys
    for lang in ("en", "de"):
        for key, value in strings[lang]["report"].items():
            assert isinstance(value, str) and value.strip(), f"strings.{lang}.report.{key} is empty"
