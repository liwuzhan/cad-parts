import pytest

from cadparts import create, deep_groove_bearing, derive, describe
from cadparts.errors import InvalidParameterError


def test_6204_simplified_has_exact_boundary_dimensions_and_bore():
    bearing = deep_groove_bearing("6204")
    size = bearing.bounding_box().size
    assert size.X == pytest.approx(47)
    assert size.Y == pytest.approx(47)
    assert size.Z == pytest.approx(14)
    assert len(bearing.solids()) == 1
    expected = pytest.approx(3.141592653589793 * (47**2 - 20**2) / 4 * 14)
    assert bearing.volume == expected


def test_rings_detail_preserves_boundary_and_has_multiple_solids():
    bearing = create("bearing.deep_groove", code=6305, detail="rings")
    size = bearing.bounding_box().size
    assert (size.X, size.Y, size.Z) == pytest.approx((62, 62, 17))
    assert len(bearing.solids()) > 3


def test_bearing_contract_exposes_supported_designations():
    contract = describe("deep_groove_bearing")
    assert contract["family"] == "bearing.deep_groove"
    assert "6204" in contract["parameters"][0]["choices"]
    assert contract["supports_derive"] is True
    assert derive("bearing", code="6204")["outside_diameter"] == 47


def test_unknown_bearing_code_is_actionable():
    with pytest.raises(InvalidParameterError, match="available: 6200"):
        deep_groove_bearing("9999")
