import pytest

from cadparts import derive, instantiate
from cadparts.errors import InvalidParameterError


def test_stepper_profile_exposes_mounting_evidence_and_overrides():
    instance = instantiate("motor.stepper.square.42", body_length=60, shaft_length=20)
    assert instance.spec["envelope"]["size_mm"] == pytest.approx([42, 42, 80])
    assert {item["id"] for item in instance.interfaces} >= {"mounting_face", "pilot", "output_shaft"}
    assert len(instance.interfaces) == 7
    assert instance.spec["compatibility"]["level"] == "series_compatible"
    assert instance.spec["keepouts"][0]["id"] == "body_and_rear_connector"


def test_servo_nominal_class_is_explicitly_not_universal():
    instance = instantiate("motor.servo.square_flange.110")
    assert instance.spec["derived"]["pilot_diameter"] == 95
    assert "not a universal" in instance.spec["compatibility"]["claim"]


def test_iec_b3_and_b5_resolve_different_mounting_interfaces():
    b3 = instantiate("motor.induction.iec.80-b3")
    b5 = instantiate("motor.induction.iec.80-b5")
    assert {item["id"] for item in b3.interfaces} >= {"foot_plane", "foot_hole_1", "output_shaft"}
    assert {item["id"] for item in b5.interfaces} == {"output_shaft", "shaft_axis", "drive_flange"}
    assert b5.spec["derived"]["flange_pitch_circle"] == 165
    assert b5.spec["compatibility"]["level"] == "normative"


def test_square_motor_rejects_impossible_shaft():
    with pytest.raises(InvalidParameterError, match="smaller than pilot"):
        derive("motor.stepper.square", frame="42", shaft_diameter=30)
