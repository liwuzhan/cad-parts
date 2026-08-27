import pytest

from cadparts import instantiate, search
from cadparts.errors import InvalidParameterError


@pytest.mark.parametrize("designation, interface_count", [("UCP206", 5), ("UCF206", 6), ("UCFL206", 4)])
def test_mounted_bearing_designations_resolve_without_source_scan(designation, interface_count):
    instance = instantiate(designation)
    assert instance.catalog_id.endswith(designation.lower())
    assert instance.spec["shape"]["valid"] is True
    assert len(instance.interfaces) == interface_count
    assert instance.spec["derived"]["bore_diameter"] == 30
    assert instance.spec["keepouts"][0]["id"] == "housing_and_grease_access"


def test_mounted_bearing_search_finds_exact_designation():
    assert search("UCF208")[0]["id"] == "bearing.unit.mounted.ucf208"


def test_flexible_coupling_keeps_two_independent_bores():
    instance = instantiate("coupling.flexible.jaw19", bore_a=8, bore_b=14)
    assert instance.spec["derived"]["bore_a"] == 8
    assert instance.spec["derived"]["bore_b"] == 14
    assert {item["id"] for item in instance.interfaces} == {"shaft_bore_a", "shaft_bore_b", "rotation_axis", "shaft_end_a", "shaft_end_b"}
    assert instance.spec["keepouts"][0]["diameter_mm"] == 46


def test_flexible_coupling_rejects_bore_beyond_profile():
    with pytest.raises(InvalidParameterError, match="bore must be"):
        instantiate("coupling.flexible.jaw19", bore_a=20)
