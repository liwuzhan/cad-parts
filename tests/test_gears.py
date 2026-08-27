import pytest
from build123d import Pos, Rot

from cadparts import create, derive, spur_gear, spur_gear_dimensions
from cadparts.errors import InvalidParameterError


def test_spur_gear_derived_reference_dimensions():
    dimensions = spur_gear_dimensions(module=2, teeth=24, bore=10, width=12)
    assert dimensions["pitch_diameter"] == pytest.approx(48)
    assert dimensions["outside_diameter"] == pytest.approx(52)
    assert dimensions["root_diameter"] == pytest.approx(43)
    assert dimensions["circular_pitch"] == pytest.approx(2 * 3.141592653589793)
    assert dimensions["reference_center_distance_to_identical"] == pytest.approx(48)


def test_generic_derive_avoids_geometry_and_exposes_warnings():
    dimensions = derive("spur_gear", module=1, teeth=12, bore=3, width=5)
    assert dimensions["gear_type"] == "external_spur_involute"
    assert "undercut" in dimensions["undercut_guidance"].lower()


@pytest.mark.parametrize("module,teeth,bore,width", [(1, 20, 5, 6), (2, 24, 10, 12), (3, 40, 20, 18)])
def test_spur_gear_bbox_bore_and_single_solid(module, teeth, bore, width):
    gear = spur_gear(module, teeth, bore, width)
    expected_outside = module * (teeth + 2)
    size = gear.bounding_box().size
    assert (size.X, size.Y, size.Z) == pytest.approx((expected_outside, expected_outside, width), abs=1e-6)
    assert len(gear.solids()) == 1
    assert gear.is_valid


def test_volume_scales_monotonically_with_module():
    small = spur_gear(module=1, teeth=24, bore=0, width=8)
    large = spur_gear(module=2, teeth=24, bore=0, width=8)
    assert large.volume > small.volume * 3.9


def test_profile_shift_changes_reference_envelope():
    standard = derive("gear.spur", module=2, teeth=24, bore=8, width=10)
    shifted = derive("gear.spur", module=2, teeth=24, bore=8, width=10, profile_shift=0.5)
    assert shifted["outside_diameter"] == pytest.approx(standard["outside_diameter"] + 2)
    assert shifted["root_diameter"] == pytest.approx(standard["root_diameter"] + 2)
    assert shifted["tooth_thickness_at_pitch"] > standard["tooth_thickness_at_pitch"]


def test_identical_gears_at_reference_center_distance_do_not_interpenetrate():
    module = 2
    teeth = 24
    first = spur_gear(module, teeth, bore=10, width=8)
    second = Pos(module * teeth, 0, 0) * Rot(0, 0, 180 / teeth) * spur_gear(
        module, teeth, bore=10, width=8
    )
    assert (first & second).volume == pytest.approx(0, abs=1e-8)


def test_spur_gear_rejects_invalid_engineering_inputs():
    with pytest.raises(InvalidParameterError, match="teeth must be >= 8"):
        create("gear.spur", module=2, teeth=6, bore=0, width=10)
    with pytest.raises(InvalidParameterError, match="bore must be smaller"):
        spur_gear(module=1, teeth=20, bore=18, width=5)
