from __future__ import annotations

import pytest
from shapely.geometry import MultiPolygon, Polygon

from boris_wfs import (
    build_gehoert_zu_filter_body,
    build_intersects_body,
    crs_urn,
    extract_counts,
    geometry_to_multisurface,
    parse_property_values,
    polygon_to_gml,
)


def _square(x=300000, y=5800000):
    return Polygon([(x, y), (x + 10, y), (x + 10, y + 10), (x, y)])


def test_crs_urn_uses_double_colon_form() -> None:
    assert crs_urn(25833) == "urn:ogc:def:crs:EPSG::25833"
    assert crs_urn(25833) != "urn:ogc:def:crs:EPSG:25833"


def test_polygon_to_gml_emits_easting_northing_pairs() -> None:
    polygon = Polygon(
        [
            (300000, 5800000),
            (300010, 5800000),
            (300010, 5800010),
            (300000, 5800000),
        ]
    )

    body = polygon_to_gml(polygon, "p-test", "urn:ogc:def:crs:EPSG::25833")

    assert "gml:posList" in body
    assert "300000.000 5800000.000" in body
    assert 'srsName="urn:ogc:def:crs:EPSG::25833"' in body
    assert 'gml:id="p-test"' in body


def test_geometry_to_multisurface_wraps_every_part() -> None:
    geom = MultiPolygon([_square(), _square(300100, 5800100)])

    body = geometry_to_multisurface(geom, "urn:ogc:def:crs:EPSG::25833")

    assert body.count("<gml:surfaceMember>") == 2
    assert 'gml:id="p0"' in body
    assert 'gml:id="p1"' in body


def test_build_intersects_body_bb_declares_br_namespace() -> None:
    body = build_intersects_body(
        "bb",
        "br:BR_BodenrichtwertFlaeche",
        _square(),
        25833,
        count=5000,
    )

    assert 'xmlns:br="http://www.adv-online.de/namespaces/adv/br/3.0"' in body
    assert 'typeNames="br:BR_BodenrichtwertFlaeche"' in body
    assert "<fes:ValueReference>adv:position</fes:ValueReference>" in body
    assert 'srsName="urn:ogc:def:crs:EPSG::25833"' in body
    assert 'version="2.0.0"' in body


def test_build_intersects_body_he_declares_boris_namespace() -> None:
    body = build_intersects_body(
        "he",
        "boris:BR_BodenrichtwertZonal",
        _square(),
        25832,
        count=5000,
    )

    assert 'xmlns:boris="http://www.adv-online.de/namespaces/adv/brm/2.1"' in body
    assert 'typeNames="boris:BR_BodenrichtwertZonal"' in body
    assert 'srsName="urn:ogc:def:crs:EPSG::25832"' in body
    assert "xmlns:br=" not in body


def test_build_intersects_body_hits_and_paging() -> None:
    body = build_intersects_body(
        "he",
        "boris:BR_BodenrichtwertZonal",
        _square(),
        25832,
        count=5000,
        startindex=5000,
        result_type="hits",
    )
    body_without_start = build_intersects_body(
        "he",
        "boris:BR_BodenrichtwertZonal",
        _square(),
        25832,
        count=5000,
    )

    assert 'resultType="hits"' in body
    assert 'startIndex="5000"' in body
    assert "startIndex" not in body_without_start


def test_build_intersects_body_rejects_unknown_state() -> None:
    with pytest.raises(ValueError):
        build_intersects_body("xx", "br:BR_BodenrichtwertFlaeche", _square(), 25833, count=10)


def test_gehoert_zu_filter_declares_xlink_and_rejects_injection() -> None:
    body = build_gehoert_zu_filter_body("DEBBBR004WQ0GD1f")

    assert 'xmlns:xlink="http://www.w3.org/1999/xlink"' in body
    assert "br:gehoertZu/@xlink:href" in body
    assert "urn:adv:oid:DEBBBR004WQ0GD1f" in body
    with pytest.raises(ValueError):
        build_gehoert_zu_filter_body('DEBB"BR004')
    with pytest.raises(ValueError):
        build_gehoert_zu_filter_body("DEBB<BR004")


def test_extract_counts_byte_slices() -> None:
    raw = b'<wfs:FeatureCollection numberMatched="30018" numberReturned="5000">'
    unknown = b'<wfs:FeatureCollection numberMatched="unknown" numberReturned="5000">'

    assert extract_counts(raw) == (30018, 5000)
    assert extract_counts(unknown) == (-1, 5000)
    with pytest.raises(RuntimeError):
        extract_counts(b"<wfs:FeatureCollection>")


def test_parse_property_values_dedupes_in_order() -> None:
    raw = b"""
    <wfs:ValueCollection>
      <wfs:member><boris:art>G</boris:art></wfs:member>
      <wfs:member><boris:art>LW</boris:art></wfs:member>
      <wfs:member><boris:art>G</boris:art></wfs:member>
    </wfs:ValueCollection>
    """
    href_raw = b"""
    <wfs:ValueCollection>
      <wfs:member>
        <br:art xlink:href="https://registry.gdi-de.org/codelist/de.adv-online.gid/BR_Art_Nutzung/1100" />
      </wfs:member>
    </wfs:ValueCollection>
    """

    assert parse_property_values(raw, "art") == ["G", "LW"]
    assert parse_property_values(href_raw, "art") == [
        "https://registry.gdi-de.org/codelist/de.adv-online.gid/BR_Art_Nutzung/1100"
    ]


def test_parse_property_values_falls_back_to_bare_member_text() -> None:
    # Verified live 2026-07-28: BORIS-HE's GetPropertyValue response wraps each
    # returned value directly in <wfs:member>, with no nested element carrying
    # the requested property's local name.
    raw = b"""
    <wfs:ValueCollection>
      <wfs:member>LW</wfs:member>
      <wfs:member>W</wfs:member>
      <wfs:member>W</wfs:member>
    </wfs:ValueCollection>
    """

    assert parse_property_values(raw, "art") == ["LW", "W"]
