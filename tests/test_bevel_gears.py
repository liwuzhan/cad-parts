from math import sqrt

import pytest

from cadparts import derive, straight_bevel_gear
from cadparts.errors import InvalidParameterError


def test_equal_ratio_right_angle_pair_derives_45_degree_cones():
    dimensions = derive(
        "bevel_gear",
        module=2,
        teeth=24,
        mate_teeth=24,
        bore=10,
        face_width=10,
    )
    assert dimensions["pitch_cone_angle_deg"] == pytest.approx(45)
    assert dimensions["mate_pitch_cone_angle_deg"] == pytest.approx(45)
    assert dimensions["cone_distance"] == pytest.approx(24 * sqrt(2))
    assert "Not a generated" in dimensions["manufacturing_warning"]


def test_ratio_derives_complementary_pitch_cone_angles():
    dimensions = derive(
        "gear.bevel_straight",
        module=2,
        teeth=20,
        mate_teeth=40,
        bore=8,
        face_width=8,
        shaft_angle=90,
    )
    assert dimensions["pitch_cone_angle_deg"] == pytest.approx(26.5650511771)
    assert dimensions["mate_pitch_cone_angle_deg"] == pytest.approx(63.4349488229)
    assert dimensions["pitch_cone_angle_deg"] + dimensions["mate_pitch_cone_angle_deg"] == pytest.approx(90)


def test_bevel_layout_is_valid_single_solid_with_exact_heel_envelope():
    gear = straight_bevel_gear(2, 24, 24, bore=10, face_width=10)
    size = gear.bounding_box().size
    assert (size.X, size.Y) == pytest.approx((52, 52), abs=1e-5)
    assert size.Z == pytest.approx(10 / sqrt(2), abs=1e-5)
    assert len(gear.solids()) == 1
    assert gear.is_valid


def test_bevel_face_width_is_guarded_by_cone_distance():
    with pytest.raises(InvalidParameterError, match="one third of cone distance"):
        straight_bevel_gear(2, 24, 24, bore=5, face_width=20)
