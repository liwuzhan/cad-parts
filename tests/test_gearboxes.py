import pytest

from cadparts import instantiate
from cadparts.errors import InvalidParameterError


def test_nmrv63_exposes_perpendicular_axes_and_mounting_points():
    instance = instantiate("RV63")
    ids = {item["id"] for item in instance.interfaces}
    assert {"output_bore", "output_axis", "input_motor_pilot", "base_plane", "foot_hole_1"} <= ids
    assert instance.spec["derived"]["output_bore"] == 25
    assert len(instance.spec["keepouts"]) == 3
    assert instance.spec["shape"]["valid"] is True


def test_right_angle_output_bore_can_follow_selected_vendor_catalog():
    instance = instantiate("gearbox.right_angle.market.nmrv063", output_bore=30)
    assert instance.spec["derived"]["output_bore"] == 30
    with pytest.raises(InvalidParameterError, match="too large"):
        instantiate("gearbox.right_angle.market.nmrv063", output_bore=100)


def test_planetary_ratio_is_purchase_evidence_not_geometry_guess():
    first = instantiate("gearbox.planetary.inline.80", ratio=5)
    second = instantiate("gearbox.planetary.inline.80", ratio=20)
    assert first.spec["envelope"] == second.spec["envelope"]
    assert first.spec["derived"]["ratio"] == 5
    assert {item["id"] for item in first.interfaces} == {"motor_input", "output_flange", "output_shaft", "rotation_axis"}
