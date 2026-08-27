import pytest

from cadparts import instantiate, search
from cadparts.errors import InvalidParameterError


def test_profile_guide_exports_motion_axis_carriage_interface_and_sweep():
    instance = instantiate("MGN12", rail_length=400, block_position=120)
    assert {item["id"] for item in instance.interfaces} == {"rail_base", "motion_axis", "carriage_top", "rail_hole_pattern"}
    assert instance.spec["derived"]["block_position"] == 120
    assert instance.spec["keepouts"][0]["size_mm"][0] == 400


def test_ball_screw_keeps_lead_and_nut_motion_separate_from_thread_detail():
    instance = instantiate("SFU1605", length=800, nut_position=300)
    assert instance.spec["derived"]["lead"] == 5
    assert instance.spec["derived"]["nut_position"] == 300
    assert {item["id"] for item in instance.interfaces} == {"screw_axis", "fixed_end", "floating_end", "nut_flange"}
    with pytest.raises(InvalidParameterError, match="complete nut"):
        instantiate("SFU1605", length=100, nut_position=5)


def test_support_units_state_fixed_or_floating_role():
    assert instantiate("BK20").spec["derived"]["support_role"] == "fixed"
    assert instantiate("BF20").spec["derived"]["support_role"] == "floating"


def test_supported_round_guide_and_linear_bushing_are_discoverable():
    guide = instantiate("SBR20", length=600)
    bushing = instantiate("LMF20")
    assert guide.spec["derived"]["shaft_diameter"] == 20
    assert bushing.spec["derived"]["flange_shape"] == "round"
    assert {item["id"] for item in bushing.interfaces} == {"shaft_bore", "motion_axis", "mounting_flange"}


def test_timing_and_chain_pitch_references_are_geometry_free_evidence():
    pulley = instantiate("drive.timing_pulley.gt2-20-5")
    sprocket = instantiate("08B-20T")
    assert pulley.spec["derived"]["pitch_diameter"] == pytest.approx(40 / 3.141592653589793)
    assert sprocket.spec["derived"]["pitch"] == 12.7
    assert {item["id"] for item in sprocket.interfaces} >= {"shaft_bore", "pitch_reference"}


def test_taper_lock_limits_bore_and_exposes_extraction_keepout():
    instance = instantiate("drive.taper_lock_bush.2012")
    assert instance.spec["derived"]["bore_diameter"] == 35
    assert instance.spec["keepouts"][0]["id"] == "bushing_and_extraction_access"
    with pytest.raises(InvalidParameterError, match="bore must be"):
        instantiate("drive.taper_lock_bush", code="1008", bore=30)


def test_search_returns_linear_candidate_without_scanning_source():
    assert search("MGN12")[0]["id"] == "linear.guide.rail.mgn12"
