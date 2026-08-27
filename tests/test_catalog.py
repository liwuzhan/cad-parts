import pytest

from cadparts import create, describe, list_families
from cadparts.errors import InvalidParameterError, UnknownFamilyError


def test_catalog_lists_square_tube_compactly():
    square_tube = next(item for item in list_families() if item["family"] == "profile.square_tube")
    assert square_tube == {
        "family": "profile.square_tube",
        "title": "Square hollow section / 方管",
        "parameters": ["side", "wall", "length", "corner_radius"],
        "validation": "bbox, volume, bore continuity and STEP export tested",
    }


def test_alias_and_standard_filtering():
    assert describe("shs")["family"] == "profile.square_tube"
    assert any(item["family"] == "profile.square_tube" for item in list_families(standard_system="GB/T"))
    assert [item["family"] for item in list_families(standard_system="ASME")] == ["key.parallel"]


def test_unknown_family_is_short_and_actionable():
    with pytest.raises(UnknownFamilyError, match="profile.square_tube"):
        describe("missing.part")


def test_generic_create_rejects_unknown_parameter_before_ocp():
    with pytest.raises(InvalidParameterError, match="unexpected"):
        create("shs", side=40, wall=3, length=100, unexpected=True)
