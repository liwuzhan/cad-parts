import json

import pytest

from cadparts import compare, describe_part, instantiate, search
from cadparts.errors import InvalidParameterError
from cadparts.metadata import build_catalog_index, load_catalog_index
from cadparts.review import validate_catalog


def test_checked_in_index_is_deterministic_and_covers_every_family():
    checked_in = load_catalog_index()
    assert checked_in == build_catalog_index()
    assert checked_in["schema"] == "cadparts.catalog-index/v1"
    minimum_categories = {
        "bearing": 1,
        "fastener": 3,
        "gear": 2,
        "key": 1,
        "profile": 4,
    }
    assert all(checked_in["categories"].get(key, 0) >= value for key, value in minimum_categories.items())
    assert checked_in["categories"]["motor"] == 3
    assert len(checked_in["entries"]) >= 54


def test_natural_language_search_prioritizes_dimensional_bearing_match():
    results = search("防水防尘 20mm内径轴承", limit=4)
    assert results[0]["id"] == "bearing.deep_groove.6204"
    assert results[0]["dimensions_mm"] == {
        "bore": 20,
        "outside_diameter": 47,
        "width": 14,
    }
    assert "2RS" in results[0]["selectors"]["closure"]


def test_structured_constraints_do_not_require_geometry():
    results = search(
        "轴承",
        category="bearing",
        constraints={"bore": 20, "outside_diameter": {"max": 50}},
    )
    assert [item["id"] for item in results] == ["bearing.deep_groove.6204"]


def test_item_description_and_comparison_follow_explicit_paths():
    description = describe_part("6204-2RS")
    assert description["entry"]["id"] == "bearing.deep_groove.6204"
    assert description["generator_params"] == {"code": "6204"}
    comparison = compare("6204", "6304")
    assert [item["dimensions_mm"]["outside_diameter"] for item in comparison["candidates"]] == [47, 52]


def test_catalog_item_instantiates_rich_proxy_without_passing_geometry_params():
    instance = instantiate("6204", selections={"closure": "2RS", "clearance": "C3"})
    assert instance.spec["schema"] == "cadparts.instance/v2"
    assert instance.catalog_id == "bearing.deep_groove.6204"
    assert instance.spec["parameters"] == {"code": "6204"}
    assert instance.spec["purchase"]["order_code"] == "6204-2RS-C3"
    assert instance.spec["envelope"]["size_mm"] == [47.0, 47.0, 14.0]
    assert {item["id"] for item in instance.interfaces} == {
        "shaft_bore",
        "housing_seat",
        "axial_face_min",
        "axial_face_max",
    }


def test_item_identity_and_declared_purchase_selections_cannot_silently_drift():
    with pytest.raises(InvalidParameterError, match="pins code='6204'"):
        instantiate("6204", code="6304")
    with pytest.raises(InvalidParameterError, match="invalid closure"):
        instantiate("6204", selections={"closure": "waterproof-ish"})
    with pytest.raises(InvalidParameterError, match="unknown selection"):
        instantiate("6204", selections={"load_rating": "probably enough"})


def test_validation_builds_all_declared_family_samples():
    report = validate_catalog(build_samples=True)
    assert report["family_count"] == sum(report["categories"].values())
    assert report["entry_count"] == len(load_catalog_index()["entries"])
    assert all(item["solid_count"] >= 1 for item in report["samples"])
    assert all(item["interface_count"] >= 1 for item in report["samples"])


def test_index_is_plain_utf8_json_for_tooling():
    serialized = json.dumps(load_catalog_index(), ensure_ascii=False)
    assert "深沟球轴承" in serialized
