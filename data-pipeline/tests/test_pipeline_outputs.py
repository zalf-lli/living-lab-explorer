from __future__ import annotations

import json

import geopandas as gpd
import numpy as np
import pytest
import yaml
from shapely.geometry import box

from conftest import LL_SLUGS, repo_root

# Must match fetch_destatis.py's ALL_NUTS3 / LL_NUTS3.
DESTATIS_ALL_NUTS3 = [
    "DE409", "DE40A", "DE40B", "DE40C", "DE408", "DE734", "DE737",
    "DE721", "DE722", "DE723", "DE724", "DE725", "DE71D",
]


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


def test_pmtiles_fixture_exists_and_is_nonzero() -> None:
    pmtiles_path = repo_root() / "app" / "public" / "data" / "pmtiles" / "landuse-croptypes.pmtiles"
    assert pmtiles_path.exists(), f"Missing PMTiles fixture: {pmtiles_path}"
    assert pmtiles_path.stat().st_size > 0, f"PMTiles fixture is empty: {pmtiles_path}"


def test_land_cover_pmtiles_fixtures_exist_and_are_nonzero() -> None:
    """
    Phase 06: mirrors test_pmtiles_fixture_exists_and_is_nonzero for the per-LL
    io-lulc-landcover raster, turning the five committed land-cover-{slug}.pmtiles
    files into a permanent contract rather than a one-off manual observation.
    """
    pmtiles_dir = repo_root() / "app" / "public" / "data" / "pmtiles"
    for slug in LL_SLUGS:
        pmtiles_path = pmtiles_dir / f"land-cover-{slug}.pmtiles"
        assert pmtiles_path.exists(), f"Missing land cover PMTiles fixture: {pmtiles_path}"
        assert pmtiles_path.stat().st_size > 0, f"Land cover PMTiles fixture is empty: {pmtiles_path}"


def test_buek250_layer_contract_declared() -> None:
    layer = get_layer("buek250")
    assert layer["kind"] == "vector"
    assert layer["input"]["path"] == "data/buek250_mgm_utm_v60/buek250_mgm_utm_v60.gpkg"
    assert layer["input"]["crs"] == "EPSG:25832"
    assert layer["build"]["script"] == "python/build_vector.py"
    assert layer["vector"]["keep_fields"] == ["SYM_NR", "GEN_ID", "BEMERKUNG"]
    assert layer["vector"]["semantics"]["sqlite_path"] == "data/buek250_mgm_utm_v60/buek250_sachdatenbank_v10.sqlite"
    assert layer["vector"]["semantics"]["contract_version"] == "buek250-soil-semantics-v1"
    assert layer["vector"]["semantics"]["tables"]["legend"] == "buek250_Legendeneinheit__v10_tbl"
    assert layer["vector"]["semantics"]["tables"]["general_legend"] == "buek250_GL_Einheit_v10_tbl"
    assert layer["vector"]["semantics"]["tables"]["parent_material"] == "buek250_GL_BAGFlaechentyp_v10_tbl"
    assert layer["vector"]["semantics"]["tables"]["profile"] == "buek250_Profil__v10_tbl"
    assert layer["vector"]["semantics"]["tables"]["horizon"] == "buek250_Horizont__v10_tbl"
    assert layer["output"]["geojson_pattern"] == "data/geojson/buek250-{slug}.geojson"


def test_buek250_geojson_fixtures_exist_and_match_contract() -> None:
    pattern = get_layer("buek250")["output"]["geojson_pattern"]

    for slug in LL_SLUGS:
        path = repo_root() / pattern.format(slug=slug)
        assert path.exists(), f"Missing GeoJSON fixture: {path}"

        gdf = gpd.read_file(path)
        assert str(gdf.crs) == "EPSG:4326", f"Unexpected CRS for {path.name}: {gdf.crs}"
        assert len(gdf) > 0, f"Fixture has no features: {path.name}"
        assert set(["SYM_NR", "GEN_ID", "BEMERKUNG"]).issubset(gdf.columns)
        assert set(
            [
                "feature_kind",
                "soil_label_de",
                "soil_label_en",
                "soil_group_key",
                "soil_group_de",
                "soil_group_en",
                "general_unit_de",
                "general_unit_en",
                "parent_material_code",
                "parent_material_de",
                "parent_material_en",
                "profile_summary_de",
                "profile_summary_en",
                "profile_count",
                "lead_horizon_count",
                "semantic_source",
                "semantic_version",
            ]
        ).issubset(gdf.columns)
        assert gdf.loc[gdf["feature_kind"] == "soil_unit", "soil_label_en"].notna().any(), (
            f"Missing translated soil labels: {path.name}"
        )
        assert gdf.loc[gdf["feature_kind"] != "soil_unit", "feature_kind"].isin(["water_area", "special_area"]).all()
        assert gdf.geometry.notna().all(), f"Fixture has null geometries: {path.name}"


def test_protected_areas_layer_contract_declared() -> None:
    """
    Phase 05-01 Task 1: Assert the bfn-schutzgebiete layer is declared with correct WFS config,
    build script, output pattern, and coordinate precision (chosen via Task 0).
    """
    layer = get_layer("bfn-schutzgebiete")
    assert layer["kind"] == "vector"
    assert layer["app_layer"] == "protected-areas"
    assert layer["build"]["script"] == "python/fetch_protected_areas.py"
    assert layer["wfs"]["url"] == "https://geodienste.bfn.de/ogc/wfs/schutzgebiet"
    assert layer["wfs"]["version"] == "2.0.0"
    assert layer["wfs"]["bbox_crs"] == "urn:ogc:def:crs:EPSG::4326"
    assert layer["wfs"]["source_crs"] == "EPSG:25832"
    assert layer["wfs"]["bbox_pad_deg"] == 0.05
    assert layer["wfs"]["typenames"]["natura2000-sci"] == "bfn_sch_Schutzgebiet:Fauna_Flora_Habitat_Gebiete"
    assert layer["wfs"]["typenames"]["natura2000-spa"] == "bfn_sch_Schutzgebiet:Vogelschutzgebiete"
    assert layer["wfs"]["typenames"]["naturschutzgebiet"] == "bfn_sch_Schutzgebiet:Naturschutzgebiete"
    assert layer["output"]["geojson_pattern"] == "data/geojson/protected-areas-{slug}.geojson"
    # Task 0 decision: precision is 0.000001 (Option B)
    assert "coordinate_precision" in layer["wfs"]
    assert layer["wfs"]["coordinate_precision"] in (None, 0.000001, 0.00001), \
        f"Expected coordinate_precision to be one of (None, 0.000001, 0.00001), got {layer['wfs']['coordinate_precision']}"


def test_boris_layer_contract_declared() -> None:
    """
    Plan 07-06: assert the boris layer is declared with per-state WFS config, the W-01
    tuning values, the five-slug ll_states map, and the semantics block -- mirroring
    test_protected_areas_layer_contract_declared's shape.
    """
    layer = get_layer("boris")
    assert layer["kind"] == "vector"
    assert layer["app_layer"] == "economic"
    assert layer["build"]["script"] == "python/fetch_boris.py"

    wfs = layer["wfs"]
    assert wfs["states"]["bb"]["url"] == "https://isk.geobasis-bb.de/ows/boris_wfs"
    assert wfs["states"]["bb"]["source_crs"] == "EPSG:25833"
    assert wfs["states"]["bb"]["zone_typename"] == "br:BR_BodenrichtwertFlaeche"
    assert wfs["states"]["bb"]["value_typename"] == "br:BR_Bodenrichtwert"
    assert wfs["states"]["he"]["url"] == "https://www.gds.hessen.de/wfs2/boris/cgi-bin/brw/2024/wfs"
    assert wfs["states"]["he"]["source_crs"] == "EPSG:25832"
    assert wfs["states"]["he"]["zone_typename"] == "boris:BR_BodenrichtwertZonal"
    assert wfs["bbox_crs"] == "urn:ogc:def:crs:EPSG::4326"
    # CRS-confusion guard (T-07-06): a future refactor must never collapse the two
    # states' source_crs values into one shared top-level key.
    assert "source_crs" not in wfs

    assert layer["output"]["geojson_pattern"] == "data/geojson/boris-{slug}.geojson"

    assert set(layer["ll_states"]) == set(LL_SLUGS)
    assert set(layer["ll_states"].values()) <= {"bb", "he"}

    semantics = layer["semantics"]
    assert semantics["contract_version"] == "boris-usage-semantics-v1"
    assert semantics.get("recency_rule")

    sources_by_state = layer["sources_by_state"]
    assert set(sources_by_state) == {"bb", "he"}
    for state_entry in sources_by_state.values():
        assert state_entry.get("provider")
        assert state_entry.get("license")
        assert state_entry.get("url")


def test_boris_usage_codes_are_state_discriminated() -> None:
    """
    Plan 07-06: pure unit test (no network, no fixtures) proving the harmonization
    contract -- both states' raw usage codes converge onto one canonical bilingual
    vocabulary, and a code from one state can never resolve through the other state's
    table (07-RESEARCH.md section 3.2 anti-pattern).
    """
    from boris_semantics import (
        BR_ART_NUTZUNG,
        ENTWICKLUNGSZUSTAND,
        UNMAPPED_USAGE,
        resolve_development_status,
        resolve_usage,
    )

    assert len(BR_ART_NUTZUNG) == 42
    assert len(ENTWICKLUNGSZUSTAND) == 10

    # A Hessen code resolved under "bb" must fall to the fallback.
    assert resolve_usage("bb", "LW")[1:] == UNMAPPED_USAGE

    # A Brandenburg numeric code resolved under "he" must fall to the fallback.
    assert resolve_usage("he", "2100")[1:] == UNMAPPED_USAGE

    # A full GDI-DE codelist href resolves under "bb" to its bare code.
    href = "https://registry.gdi-de.org/codelist/de.adv-online.gid/BR_Art_Nutzung/1100"
    code, en, de = resolve_usage("bb", href)
    assert code == "1100"
    assert en == "Residential building land"

    # Both alphabets converge on the same English label for the same concept.
    assert resolve_development_status("bb", "3000")[0] == resolve_development_status("he", "E")[0]

    with pytest.raises(ValueError):
        resolve_usage("xx", "1100")


def test_protected_areas_bbox_param_axis_order() -> None:
    """
    Phase 05-01 Task 1: Assert the _bbox_param helper returns lat,lon order with the
    urn:ogc:def:crs:EPSG::4326 suffix. This is a pure unit test (no network) that guards against
    the silent-failure mode where any other bbox spelling returns HTTP 200 with zero features.
    """
    from fetch_protected_areas import _bbox_param

    # Rheingau bounds from data/ll_boundaries.geojson: lon 7.7726-8.4108, lat 49.9720-50.2960
    rheingau = box(7.7726, 49.9720, 8.4108, 50.2960)

    # With default pad=0.05 and bbox_crs="urn:ogc:def:crs:EPSG::4326"
    bbox = _bbox_param(rheingau)
    assert bbox == "49.9220,7.7226,50.3460,8.4608,urn:ogc:def:crs:EPSG::4326", \
        f"Expected lat,lon ordering with urn: prefix and 0.05 degree padding, got {bbox}"

    # With pad=0.0, verify it's a real parameter
    bbox_no_pad = _bbox_param(rheingau, pad=0.0)
    assert bbox_no_pad.startswith("49.9720,7.7726,50.2960,8.4108,"), \
        f"Expected lat,lon ordering with zero padding at start, got {bbox_no_pad}"


def test_destatis_nuts3_fixture_exists_and_matches_codes() -> None:
    path = repo_root() / "data" / "destatis_nuts3.json"
    assert path.exists(), f"Missing Destatis NUTS3 fixture: {path}"

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    assert set(data.keys()) == set(DESTATIS_ALL_NUTS3)


def test_destatis_ll_fixture_exists_and_matches_slugs() -> None:
    path = repo_root() / "data" / "destatis_ll.json"
    assert path.exists(), f"Missing Destatis LL fixture: {path}"

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    assert set(data.keys()) == set(LL_SLUGS)


def test_destatis_curated_kpis_manifest_matches_contract() -> None:
    path = repo_root() / "data" / "destatis_curated_kpis.json"
    assert path.exists(), f"Missing Destatis curated KPI manifest: {path}"

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    assert len(data) == 19, f"Expected 19 curated KPI entries, got {len(data)}"

    expected_keys = {
        "tab",
        "variable_key",
        "genesis_table",
        "source_host",
        "label_en",
        "label_de",
        "unit_en",
        "unit_de",
    }
    for entry in data:
        assert set(entry.keys()) == expected_keys, entry
        # source_host names the upstream source: a Destatis platform, bfn_wfs for a value
        # derived from the BfN protected-areas geometry (Phase 05.1), chelsa for a value
        # computed from CHELSA climate rasters at build time (Phase 08), or None for an
        # honestly-unresolved slot (D-15) -- never fabricated or omitted (Plan 04-07).
        assert entry["source_host"] in ("genesis", "regionalstatistik", "bfn_wfs", None, "chelsa"), entry

    tab_counts: dict[str, int] = {}
    for entry in data:
        tab_counts[entry["tab"]] = tab_counts.get(entry["tab"], 0) + 1

    assert tab_counts == {
        "agriculture": 4,
        "soil": 3,
        "climate": 4,
        "landscape": 4,
        "economic": 4,
    }

    # Phase 06 D-01: guard against a future partial revert reintroducing the pre-rename
    # `landuse` tab key on only one side of the pipeline/app join.
    assert not any(entry["tab"] == "landuse" for entry in data), (
        "Found a stale 'landuse' tab id -- Phase 06 D-01 renamed the app tab id to "
        "'agriculture'; check fetch_destatis.CURATED_KPIS and this manifest together"
    )


def test_ll_metadata_kpi_by_tab_contract() -> None:
    """
    Plan 04-03: app/public/data/ll_metadata.json must carry a kpiByTab field per Living Lab,
    built from real Destatis data, matching the locked per-tab field counts (D-09), and never
    leaking the legacy "-" placeholder sentinel that used to live in ll_content.json's
    kpi/production/socio blocks (Pitfall 3 / D-10 / D-11).
    """
    path = repo_root() / "app" / "public" / "data" / "ll_metadata.json"
    assert path.exists(), f"Missing ll_metadata.json fixture: {path}"

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    assert data, "ll_metadata.json is empty"

    expected_tab_counts = {
        "agriculture": 4,
        "soil": 3,
        "climate": 4,
        "landscape": 4,
        "economic": 4,
    }

    def _assert_no_placeholder(value: object) -> None:
        if isinstance(value, dict):
            for v in value.values():
                _assert_no_placeholder(v)
        elif isinstance(value, list):
            for v in value:
                _assert_no_placeholder(v)
        else:
            assert value != "-", "Found leaked '-' placeholder value inside kpiByTab"

    for slug, record in data.items():
        assert "kpiByTab" in record, f"Missing kpiByTab for {slug}"
        kpi_by_tab = record["kpiByTab"]
        assert set(kpi_by_tab) <= set(expected_tab_counts), f"Unexpected tab keys for {slug}: {set(kpi_by_tab)}"
        for tab, expected_count in expected_tab_counts.items():
            assert len(kpi_by_tab.get(tab, [])) == expected_count, (
                f"{slug}: expected {expected_count} fields for tab {tab!r}, got {len(kpi_by_tab.get(tab, []))}"
            )
        _assert_no_placeholder(kpi_by_tab)

        assert "destatisRetrievedAt" in record, f"Missing destatisRetrievedAt for {slug}"
        assert isinstance(record["destatisRetrievedAt"], str) and record["destatisRetrievedAt"], (
            f"destatisRetrievedAt for {slug} must be a non-empty string"
        )


def test_destatis_resolved_slots_have_real_values() -> None:
    """
    Plan 04-07: every curated slot the manifest marks as resolved (non-null genesis_table /
    source_host) must carry at least one non-null value across the 14 Kreise in
    destatis_nuts3.json -- a "resolved" slot with no real data anywhere would silently violate
    D-15's "never fabricate, never silently drop" contract.

    Non-Destatis hosts such as bfn_wfs are intentionally excluded here because they are not
    Kreis-level series; see test_protected_area_kpis_reach_ll_metadata instead.
    """
    manifest_path = repo_root() / "data" / "destatis_curated_kpis.json"
    nuts3_path = repo_root() / "data" / "destatis_nuts3.json"

    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    with nuts3_path.open("r", encoding="utf-8") as handle:
        nuts3 = json.load(handle)

    for entry in manifest:
        # Skip non-Destatis hosts; they have their own test contracts
        if entry["source_host"] not in ("genesis", "regionalstatistik"):
            continue
        variable_key = entry["variable_key"]
        values = [rec.get(variable_key) for rec in nuts3.values()]
        assert any(v is not None for v in values), (
            f"Manifest marks {variable_key!r} resolved (source_host={entry['source_host']!r}) "
            "but destatis_nuts3.json has no non-null values for it across any Kresis"
        )


def test_protected_area_kpis_are_populated() -> None:
    """
    Phase 05.1: protected_area_kpis.json exists, carries all 5 LL slugs as keys (excluding _meta),
    and each LL has non-zero natura2000_ha and nature_reserves_ha values. This guards against
    Pitfall 6: silent computation failure, where the protected area coverage computation stops
    running but nothing in the suite fails because test_destatis_resolved_slots_have_real_values
    deliberately skips non-Destatis hosts.
    """
    path = repo_root() / "data" / "protected_area_kpis.json"
    assert path.exists(), f"Missing protected_area_kpis.json: {path}"

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    # Verify _meta block exists and has correct source
    assert "_meta" in data, "Missing _meta block in protected_area_kpis.json"
    assert data["_meta"].get("source") == "bfn_wfs", f"Expected source='bfn_wfs', got {data['_meta'].get('source')}"

    # Verify all 5 LL slugs are present (excluding _meta)
    ll_data = {k: v for k, v in data.items() if k != "_meta"}
    assert set(ll_data.keys()) == set(LL_SLUGS), (
        f"Expected LL_SLUGS {set(LL_SLUGS)}, got {set(ll_data.keys())}"
    )

    # Verify each LL has non-zero coverage values
    for slug in LL_SLUGS:
        record = ll_data[slug]
        assert record.get("natura2000_ha") is not None, f"{slug}: natura2000_ha is null"
        assert record["natura2000_ha"] > 0, f"{slug}: natura2000_ha is {record['natura2000_ha']}, expected > 0"
        assert record.get("nature_reserves_ha") is not None, f"{slug}: nature_reserves_ha is null"
        assert record["nature_reserves_ha"] > 0, f"{slug}: nature_reserves_ha is {record['nature_reserves_ha']}, expected > 0"


def test_protected_area_kpis_reach_ll_metadata() -> None:
    """
    Phase 05.1: the merge in generate_metadata.py successfully propagates protected_area_kpis
    values into app/public/data/ll_metadata.json's kpiByTab.landscape. This guards against
    Pitfall 6: regression where the merge is reverted or disabled but no test fails.
    """
    metadata_path = repo_root() / "app" / "public" / "data" / "ll_metadata.json"
    assert metadata_path.exists(), f"Missing ll_metadata.json: {metadata_path}"

    with metadata_path.open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)

    for slug in LL_SLUGS:
        assert slug in metadata, f"Missing {slug} in ll_metadata.json"
        record = metadata[slug]
        assert "kpiByTab" in record, f"Missing kpiByTab for {slug}"
        assert "landscape" in record["kpiByTab"], f"Missing landscape tab for {slug}"

        # Find natura2000_ha and nature_reserves_ha in the landscape tab
        landscape = record["kpiByTab"]["landscape"]
        kpi_map = {kpi["key"]: kpi for kpi in landscape}

        for key in ("natura2000_ha", "nature_reserves_ha"):
            assert key in kpi_map, f"{slug}: missing {key} in landscape KPIs"
            kpi = kpi_map[key]
            assert kpi["value"] is not None, f"{slug}.{key}: value is null"
            assert kpi["value"] > 0, f"{slug}.{key}: value is {kpi['value']}, expected > 0"
            assert kpi["sourceHost"] == "bfn_wfs", f"{slug}.{key}: sourceHost is {kpi['sourceHost']}, expected 'bfn_wfs'"
            assert kpi["genesisTable"] is None, f"{slug}.{key}: genesisTable should be null, got {kpi['genesisTable']}"
            assert kpi["unit"] == {"en": "ha", "de": "ha"}, f"{slug}.{key}: unexpected unit {kpi['unit']}"


# Accepted per-Living-Lab-per-copy byte budget, transcribed from the W-01 locked decision
# in 07-SPIKE.md ("## Locked Wave-0 Decisions" -> "W-01 Geometry fidelity and size budget").
# The 07-SPIKE.md text itself records east-brandenburg's own measured variant-E size as
# 33,954,375 bytes immediately below the "~33 MB (33,000,000 bytes)" label, so the real
# locked ceiling for this suite is the larger, explicitly-measured figure -- not the
# rounded label -- to avoid a false failure on the exact number the checkpoint approved.
BORIS_BUDGET_BYTES_PER_LL_PER_COPY = 33_954_375


def test_narrative_by_tab_contract() -> None:
    """
    Quick task 260729-bsg: generate_metadata.build_metadata must emit a normalized
    narrativeByTab[<tab>][<slot>][<lang>] cube for every Living Lab, per D-02/D-03/D-04.
    Covers both the in-memory fixture behaviours and the committed runtime asset shape.
    """
    import sys

    sys.path.insert(0, str(repo_root() / "data-pipeline" / "python"))
    from generate_metadata import NARRATIVE_SLOTS, NARRATIVE_TABS, build_metadata

    # In-memory fixture: soil.about authored in English only, whitespace-only elsewhere,
    # an unknown tab key that must be dropped, and a second LL authoring no narrative at all.
    fixture = {
        "slug-a": {
            "slug": "slug-a",
            "en": {
                "narrative": {
                    "soil": {"about": "Soil types are highly variable.", "challenges": "   "},
                    "protected-areas": {"about": "should be dropped"},
                },
            },
            "de": {},
        },
        "slug-b": {
            "slug": "slug-b",
            "en": {},
            "de": {},
        },
    }
    metadata = build_metadata(ll_content=fixture)

    slug_a_narrative = metadata["slug-a"]["narrativeByTab"]
    assert slug_a_narrative["soil"]["about"]["en"] == "Soil types are highly variable."
    assert slug_a_narrative["soil"]["about"]["de"] is None
    # Whitespace-only authored string normalizes to None, never "" (D-04).
    assert slug_a_narrative["soil"]["challenges"]["en"] is None
    # Unknown authored tab key is dropped, not propagated.
    assert "protected-areas" not in slug_a_narrative
    assert set(slug_a_narrative) == set(NARRATIVE_TABS)

    slug_b_narrative = metadata["slug-b"]["narrativeByTab"]
    for tab in NARRATIVE_TABS:
        assert tab in slug_b_narrative
        for slot in NARRATIVE_SLOTS:
            assert slug_b_narrative[tab][slot] == {"en": None, "de": None}

    # Committed runtime asset: every slug carries a complete five-tab narrativeByTab cube,
    # values are str or None, and the legacy "-" sentinel never leaks in.
    path = repo_root() / "app" / "public" / "data" / "ll_metadata.json"
    assert path.exists(), f"Missing ll_metadata.json fixture: {path}"
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    for slug in LL_SLUGS:
        assert slug in data, f"Missing {slug} in ll_metadata.json"
        record = data[slug]
        assert "narrativeByTab" in record, f"Missing narrativeByTab for {slug}"
        narrative_by_tab = record["narrativeByTab"]
        assert set(narrative_by_tab) == set(NARRATIVE_TABS), (
            f"{slug}: expected tabs {set(NARRATIVE_TABS)}, got {set(narrative_by_tab)}"
        )
        for tab in NARRATIVE_TABS:
            for slot in NARRATIVE_SLOTS:
                slot_block = narrative_by_tab[tab][slot]
                assert set(slot_block) == {"en", "de"}
                for lang_value in slot_block.values():
                    assert lang_value is None or isinstance(lang_value, str), (
                        f"{slug}.{tab}.{slot}: expected str or None, got {type(lang_value)}"
                    )
                    assert lang_value != "-", f"{slug}.{tab}.{slot}: leaked '-' sentinel"


def test_boris_geojson_fixtures_exist_and_match_contract() -> None:
    """
    Plan 07-08: mirrors test_buek250_geojson_fixtures_exist_and_match_contract's shape --
    existence, CRS, non-empty, and the ten-key 07-UI-SPEC.md "Runtime asset" contract --
    plus the JSON-type and size-budget guarantees the frontend and the W-01 checkpoint
    depend on.
    """
    pattern = get_layer("boris")["output"]["geojson_pattern"]

    contract_keys = {
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
    }

    for slug in LL_SLUGS:
        path = repo_root() / pattern.format(slug=slug)
        assert path.exists(), f"Missing GeoJSON fixture: {path}"

        gdf = gpd.read_file(path)
        assert str(gdf.crs) == "EPSG:4326", f"Unexpected CRS for {path.name}: {gdf.crs}"
        assert len(gdf) > 0, f"Fixture has no features: {path.name}"

        non_geometry_columns = set(gdf.columns) - {"geometry"}
        assert non_geometry_columns == contract_keys, (
            f"{path.name}: expected exactly the ten-key contract, got {sorted(non_geometry_columns)}"
        )

        assert gdf.geometry.notna().all(), f"Fixture has null geometries: {path.name}"
        assert gdf["ll_slug"].unique().tolist() == [slug], (
            f"{path.name}: ll_slug values must all equal {slug!r}"
        )

        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)

        for feature in raw["features"]:
            props = feature["properties"]
            assert isinstance(props["has_current_value"], bool), (
                f"{path.name}: has_current_value must be a real bool, got {type(props['has_current_value'])}"
            )
            brw = props["bodenrichtwert"]
            assert brw is None or isinstance(brw, (int, float)), (
                f"{path.name}: bodenrichtwert must be None or a number, got {type(brw)}: {brw!r}"
            )
            assert not isinstance(brw, bool), f"{path.name}: bodenrichtwert must never be a bool"

        assert any(f["properties"].get("usage_type_en") for f in raw["features"]), (
            f"{path.name}: no feature has a non-null usage_type_en"
        )
        assert any(f["properties"].get("usage_type_de") for f in raw["features"]), (
            f"{path.name}: no feature has a non-null usage_type_de"
        )

        size_bytes = path.stat().st_size
        assert size_bytes <= BORIS_BUDGET_BYTES_PER_LL_PER_COPY, (
            f"{path.name}: {size_bytes:,} bytes exceeds the W-01 budget of "
            f"{BORIS_BUDGET_BYTES_PER_LL_PER_COPY:,} bytes (07-SPIKE.md)"
        )


def test_climate_kpis_fixture_matches_contract() -> None:
    """
    Plan 08-07: climate_kpis.json (produced by compute_climate_kpis.py) exists, carries a
    chelsa-sourced _meta block with D-21 delta-horizon metadata plus a four-variable
    manifest, and every LL slug object carries exactly the eight numeric keys (baseline +
    far-horizon delta per variable, D-19/D-20) implied by that manifest -- mirroring
    test_destatis_curated_kpis_manifest_matches_contract's shape.
    """
    import math

    path = repo_root() / "data" / "climate_kpis.json"
    assert path.exists(), f"Missing climate_kpis.json (producer: compute_climate_kpis.py): {path}"

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    assert "_meta" in data, "Missing _meta block in climate_kpis.json"
    meta = data["_meta"]
    assert meta.get("computed_at"), "Missing _meta.computed_at"
    assert meta.get("source") == "chelsa", f"Expected _meta.source=='chelsa', got {meta.get('source')!r}"
    assert meta.get("metric_crs") == "EPSG:25832", f"Expected _meta.metric_crs=='EPSG:25832', got {meta.get('metric_crs')!r}"
    assert meta.get("input_pattern"), "Missing _meta.input_pattern"
    assert meta.get("delta_horizon") == "2071_2100", f"Expected _meta.delta_horizon=='2071_2100', got {meta.get('delta_horizon')!r}"
    assert meta.get("delta_horizon_label") == "2071-2100", (
        f"Expected _meta.delta_horizon_label=='2071-2100', got {meta.get('delta_horizon_label')!r}"
    )

    variables = meta.get("variables")
    assert isinstance(variables, dict), "Missing or malformed _meta.variables block"
    assert len(variables) == 4, f"Expected exactly 4 entries in _meta.variables, got {len(variables)}"

    variable_keys = set(variables.keys())
    for variable_key, entry in variables.items():
        assert entry.get("unit", {}).get("en"), f"{variable_key}: missing non-empty unit.en"
        assert entry.get("unit", {}).get("de"), f"{variable_key}: missing non-empty unit.de"
        assert entry.get("delta_unit", {}).get("en"), f"{variable_key}: missing non-empty delta_unit.en"
        assert entry.get("delta_unit", {}).get("de"), f"{variable_key}: missing non-empty delta_unit.de"

    ll_data = {k: v for k, v in data.items() if k != "_meta"}
    assert set(ll_data.keys()) == set(LL_SLUGS), (
        f"Expected LL_SLUGS {set(LL_SLUGS)}, got {set(ll_data.keys())}"
    )

    # Every slug object's key set must be matched against the manifest's own variable_key
    # set, so this test cannot silently drift from _meta.variables.
    expected_keys = variable_keys | {f"{key}_delta" for key in variable_keys}
    for slug, record in ll_data.items():
        assert set(record.keys()) == expected_keys, (
            f"{slug}: expected exactly {sorted(expected_keys)}, got {sorted(record.keys())}"
        )
        for key, value in record.items():
            assert isinstance(value, (int, float)) and not isinstance(value, bool), (
                f"{slug}.{key}: expected a number, got {type(value)}: {value!r}"
            )
            assert math.isfinite(value), f"{slug}.{key}: value is not finite: {value!r}"


def test_climate_color_breaks_contract() -> None:
    """
    Plan 08-06: enforces the D-09/D-12/D-13 shared-colour-scale contract on
    data/climate_color_breaks.json via check_color_breaks.check_color_breaks. If the
    artifact is missing, the producer is compute_climate_color_breaks.py, matching how
    test_destatis_curated_kpis_manifest_matches_contract names its own producer.
    """
    import sys

    sys.path.insert(0, str(repo_root() / "data-pipeline" / "tests"))
    from check_color_breaks import check_color_breaks

    path = repo_root() / "data" / "climate_color_breaks.json"
    assert path.exists(), (
        f"Missing {path} -- run data-pipeline/python/compute_climate_color_breaks.py first"
    )
    check_color_breaks(path)


def test_derive_change_field_guards_nodata() -> None:
    """
    Code review CR-01 (phase 08): fetch_climate._derive_change_field must resolve a pixel
    to `nodata` -- never a finite-but-wrong value -- whenever its baseline or future input
    is nodata (the pipeline's finite -9999 sentinel) or NaN (the marker
    _multi_model_mean leaves when every GCM agreed nodata for a pixel), for both the
    absolute and percent change_mode branches.
    """
    import sys

    sys.path.insert(0, str(repo_root() / "data-pipeline" / "python"))
    from fetch_climate import _derive_change_field

    nodata = -9999.0
    # Column order: [normal pixel, nodata baseline, nodata future, NaN future, zero baseline]
    baseline = np.array([5.0, nodata, 5.0, 5.0, 0.0], dtype=np.float64)
    future = np.array([8.0, 8.0, nodata, np.nan, 8.0], dtype=np.float64)

    absolute = _derive_change_field(future, baseline, change_mode="absolute", nodata=nodata)
    assert absolute[0] == pytest.approx(3.0)
    assert absolute[1] == nodata, f"nodata baseline must resolve to nodata, got {absolute[1]!r}"
    assert absolute[2] == nodata, f"nodata future must resolve to nodata, got {absolute[2]!r}"
    assert absolute[3] == nodata, f"NaN future must resolve to nodata, got {absolute[3]!r}"

    percent = _derive_change_field(future, baseline, change_mode="percent", nodata=nodata)
    assert percent[0] == pytest.approx(60.0)
    assert percent[1] == nodata, f"nodata baseline must resolve to nodata, got {percent[1]!r}"
    assert percent[2] == nodata, f"nodata future must resolve to nodata, got {percent[2]!r}"
    assert percent[3] == nodata, f"NaN future must resolve to nodata, got {percent[3]!r}"
    assert percent[4] == nodata, f"zero baseline must resolve to nodata, got {percent[4]!r}"


# Plan 09-06 D-10/D-16 fixture matrix: the five chart-bearing layer ids in this file's
# own declared id order, sibling to BORIS_BUDGET_BYTES_PER_LL_PER_COPY above.
CHART_LAYER_IDS = [
    "landuse-croptypes",
    "io-lulc-landcover",
    "buek250",
    "boris",
    "chelsa-climate",
]

BAR_CHART_LAYER_IDS = ["landuse-croptypes", "io-lulc-landcover", "buek250", "boris"]

BAR_CHART_ENVELOPE_KEYS = {
    "ll_slug", "layer_id", "chart_type", "unit", "series", "mock", "source", "generated_at",
}

LINE_CHART_ENVELOPE_KEYS = {
    "ll_slug", "layer_id", "chart_type", "unit", "x_axis", "lines", "mock", "source", "generated_at",
}


def test_chart_stanzas_declared() -> None:
    """
    Plan 09-06: locks the five chart.script / output.chart_pattern declarations plan
    09-02 added to sources.yaml, transcribed from that plan's own interface table.
    Also guards that bfn-schutzgebiete -- the one vector layer with no chart tab --
    never gains a chart stanza by accident.
    """
    expectations = {
        "landuse-croptypes": (
            "python/compute_agriculture_chart.py",
            "data/charts/landuse-croptypes-{slug}.json",
        ),
        "io-lulc-landcover": (
            "python/compute_landscape_chart.py",
            "data/charts/io-lulc-landcover-{slug}.json",
        ),
        "buek250": (
            "python/compute_soil_chart.py",
            "data/charts/buek250-{slug}.json",
        ),
        "boris": (
            "python/compute_economic_chart.py",
            "data/charts/boris-{slug}.json",
        ),
        "chelsa-climate": (
            "python/compute_climate_chart.py",
            "data/charts/chelsa-climate-{slug}.json",
        ),
    }
    assert set(expectations) == set(CHART_LAYER_IDS)

    for layer_id, (script, pattern) in expectations.items():
        layer = get_layer(layer_id)
        assert layer["chart"]["script"] == script, layer_id
        assert layer["output"]["chart_pattern"] == pattern, layer_id

    protected_areas = get_layer("bfn-schutzgebiete")
    assert "chart" not in protected_areas, "bfn-schutzgebiete must not declare a chart stanza"
    assert "chart_pattern" not in protected_areas.get("output", {}), (
        "bfn-schutzgebiete must not declare output.chart_pattern"
    )


def test_climate_variable_chart_labels_declared() -> None:
    """
    Plan 09-06: locks D-16's pipeline-owned bilingual chart-legend names together with
    the Phase 8 D-08 gdd-first variable ordering -- both read from the same
    sources.yaml climate.variables block that compute_climate_chart.py consumes.
    """
    layer = get_layer("chelsa-climate")
    variables = layer["climate"]["variables"]
    assert list(variables.keys()) == ["gdd", "bio1", "bio12", "bio18"]

    for variable_id, entry in variables.items():
        label = entry.get("label")
        assert label is not None, f"{variable_id}: missing label block"
        assert label.get("en"), f"{variable_id}: missing non-empty label.en"
        assert label.get("de"), f"{variable_id}: missing non-empty label.de"


def test_bar_chart_fixtures_exist_and_match_contract() -> None:
    """
    Plan 09-06: for each of the four bar chart_type layers, locks the envelope shape,
    the join-key coupling of layer_id to sources.yaml's own app_layer value (not a
    hardcoded string), and the plausibility guard that series pct values sum to
    roughly 100.

    Deviation from the plan's literal "pct > 0" wording: several boris economic
    fixtures carry real, legitimate categories with only 1-7 zones out of thousands,
    which round to 0.0 at one decimal place (e.g. boris-east-brandenburg.json's
    "Campsite" category: value=1, pct=0.0). Asserting pct > 0 would fail on correct,
    already-committed data, so this test asserts pct >= 0 instead. See
    09-06-SUMMARY.md Deviations for the full investigation.

    Same relaxation extends to value: compute_soil_chart.py deliberately never drops a
    dissolved soil group regardless of area (see its "never drop a row" docstring), so a
    group whose remaining area after a boundary edit is a boundary-adjacent sliver can
    round to 0.0 ha at one decimal place (e.g. buek250-havellandisches-luch.json's
    "Alluvial soils" category after the 2026-08-04 nuts3 boundary shrink: pct=1e-05,
    value=0.0). Asserting value > 0 would fail on correct, already-committed data, so
    this test asserts value >= 0 instead.
    """
    for layer_id in BAR_CHART_LAYER_IDS:
        layer = get_layer(layer_id)
        pattern = layer["output"]["chart_pattern"]
        expected_layer_id = layer["app_layer"]

        for slug in LL_SLUGS:
            path = repo_root() / pattern.format(slug=slug)
            assert path.exists(), f"Missing chart fixture: {path}"

            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)

            assert set(data.keys()) == BAR_CHART_ENVELOPE_KEYS, (
                f"{path.name}: expected exactly {sorted(BAR_CHART_ENVELOPE_KEYS)}, "
                f"got {sorted(data.keys())}"
            )
            assert data["chart_type"] == "bar", path.name
            assert data["ll_slug"] == slug, path.name
            assert data["source"] == layer_id, path.name
            assert data["layer_id"] == expected_layer_id, (
                f"{path.name}: expected layer_id {expected_layer_id!r} (sources.yaml "
                f"app_layer), got {data['layer_id']!r}"
            )
            assert data["mock"] is False, path.name
            assert set(data["unit"]) == {"en", "de"}, path.name

            series = data["series"]
            assert len(series) > 0, f"{path.name}: series is empty"

            pct_sum = 0.0
            for entry in series:
                label = entry["label"]
                assert set(label) == {"en", "de"}, f"{path.name}: label key set {sorted(label)}"
                assert label["en"], f"{path.name}: empty label.en"
                assert label["de"], f"{path.name}: empty label.de"

                value = entry["value"]
                assert isinstance(value, (int, float)) and not isinstance(value, bool), (
                    f"{path.name}: value must be int/float, got {type(value)}"
                )
                assert value >= 0, f"{path.name}: value must be >= 0, got {value}"

                pct = entry["pct"]
                assert isinstance(pct, (int, float)) and not isinstance(pct, bool), (
                    f"{path.name}: pct must be int/float, got {type(pct)}"
                )
                assert pct >= 0, f"{path.name}: pct must be >= 0, got {pct}"
                pct_sum += pct

            assert 95.0 <= pct_sum <= 105.0, (
                f"{path.name}: series pct values should sum near 100, got {pct_sum}"
            )


def test_climate_chart_fixtures_exist_and_match_line_contract() -> None:
    """
    Plan 09-06: locks the line chart_type envelope for chelsa-climate, proving no
    'series' key leaked into this variant, and that both horizons (in x_axis order)
    and all four variables (in D-08 gdd-first order) are present with numeric points.
    """
    layer = get_layer("chelsa-climate")
    pattern = layer["output"]["chart_pattern"]

    for slug in LL_SLUGS:
        path = repo_root() / pattern.format(slug=slug)
        assert path.exists(), f"Missing chart fixture: {path}"

        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        assert set(data.keys()) == LINE_CHART_ENVELOPE_KEYS, (
            f"{path.name}: expected exactly {sorted(LINE_CHART_ENVELOPE_KEYS)}, "
            f"got {sorted(data.keys())}"
        )
        assert data["chart_type"] == "line", path.name
        assert data["layer_id"] == "climate", path.name
        assert data["source"] == "chelsa-climate", path.name
        assert data["mock"] is False, path.name
        assert set(data["unit"]) == {"en", "de"}, path.name

        x_axis = data["x_axis"]
        x_axis_keys = [entry["key"] for entry in x_axis]
        assert x_axis_keys == ["2041_2070", "2071_2100"], (
            f"{path.name}: unexpected x_axis key order {x_axis_keys}"
        )
        for entry in x_axis:
            assert set(entry["label"]) == {"en", "de"}, f"{path.name}: x_axis label key set"

        lines = data["lines"]
        assert len(lines) == 4, f"{path.name}: expected exactly 4 lines, got {len(lines)}"
        for line in lines:
            label = line["label"]
            assert set(label) == {"en", "de"}, f"{path.name}: line label key set"
            assert label["en"], f"{path.name}: empty line label.en"
            assert label["de"], f"{path.name}: empty line label.de"

            points = line["points"]
            assert len(points) == 2, f"{path.name}: expected exactly 2 points, got {len(points)}"
            point_x_values = [point["x"] for point in points]
            assert point_x_values == ["2041_2070", "2071_2100"], (
                f"{path.name}: unexpected point x order {point_x_values}"
            )
            for point in points:
                assert isinstance(point["value"], (int, float)) and not isinstance(point["value"], bool), (
                    f"{path.name}: point value must be numeric, got {type(point['value'])}"
                )


def test_chart_fixtures_published_to_app_public() -> None:
    """
    Plan 09-06: locks the sync_charts() publish step -- every committed data/charts/
    source has a byte-identical published copy under app/public/data/charts/, and the
    published directory holds exactly the 25 files this contract defines (no orphans
    left behind by a renamed pattern).
    """
    published_dir = repo_root() / "app" / "public" / "data" / "charts"

    for layer_id in CHART_LAYER_IDS:
        pattern = get_layer(layer_id)["output"]["chart_pattern"]
        for slug in LL_SLUGS:
            source_path = repo_root() / pattern.format(slug=slug)
            published_path = published_dir / source_path.name
            assert published_path.exists(), f"Missing published chart fixture: {published_path}"
            assert published_path.read_bytes() == source_path.read_bytes(), (
                f"{published_path.name}: published copy is not byte-identical to {source_path}"
            )

    published_files = sorted(published_dir.glob("*.json"))
    assert len(published_files) == 25, (
        f"Expected exactly 25 published chart files, got {len(published_files)}: "
        f"{[p.name for p in published_files]}"
    )
