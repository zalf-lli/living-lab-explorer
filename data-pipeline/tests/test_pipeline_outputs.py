from __future__ import annotations

import json

import geopandas as gpd
import yaml

from conftest import LL_SLUGS, repo_root

# Must match fetch_destatis.py's ALL_NUTS3 / LL_NUTS3.
DESTATIS_ALL_NUTS3 = [
    "DE409", "DE40A", "DE40B", "DE40C", "DE406", "DE408", "DE734", "DE737",
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

    assert len(data) == 17, f"Expected 17 curated KPI entries, got {len(data)}"

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
        # source_host must be one of the known hosts for a resolved slot, or None for an
        # honestly-unresolved slot (D-15) -- never fabricated or omitted (Plan 04-07).
        assert entry["source_host"] in ("genesis", "regionalstatistik", None), entry

    tab_counts: dict[str, int] = {}
    for entry in data:
        tab_counts[entry["tab"]] = tab_counts.get(entry["tab"], 0) + 1

    assert tab_counts == {
        "landuse": 4,
        "soil": 3,
        "climate": 2,
        "landscape": 4,
        "economic": 4,
    }


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
        "landuse": 4,
        "soil": 3,
        "climate": 2,
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
    """
    manifest_path = repo_root() / "data" / "destatis_curated_kpis.json"
    nuts3_path = repo_root() / "data" / "destatis_nuts3.json"

    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    with nuts3_path.open("r", encoding="utf-8") as handle:
        nuts3 = json.load(handle)

    for entry in manifest:
        if entry["source_host"] is None:
            continue
        variable_key = entry["variable_key"]
        values = [rec.get(variable_key) for rec in nuts3.values()]
        assert any(v is not None for v in values), (
            f"Manifest marks {variable_key!r} resolved (source_host={entry['source_host']!r}) "
            "but destatis_nuts3.json has no non-null values for it across any Kreis"
        )
