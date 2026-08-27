import pytest

from cadparts import instantiate, search
from cadparts.errors import InvalidParameterError


@pytest.mark.parametrize("identifier", ["pneumatic.cylinder.iso6432.20", "pneumatic.cylinder.iso15552.63", "SDA40"])
def test_pneumatic_cylinders_expose_mounts_motion_and_rod_sweep(identifier):
    instance = instantiate(identifier)
    assert {item["id"] for item in instance.interfaces} == {"rear_mount", "front_mount", "rod_end", "motion_axis"}
    assert {item["id"] for item in instance.spec["keepouts"]} == {"cylinder_body", "rod_sweep"}
    assert instance.spec["shape"]["valid"] is True


def test_sda_is_not_misrepresented_as_iso_interchangeability():
    instance = instantiate("SDA40")
    assert instance.spec["derived"]["market_series"] == "SDA"
    assert instance.spec["compatibility"]["level"] == "series_compatible"


def test_electric_actuator_position_is_bounded_and_reflected_in_output_frame():
    instance = instantiate("actuator.linear.electric.rod60", position=120)
    output = next(item for item in instance.interfaces if item["id"] == "output")
    assert output["frame"]["origin_mm"][0] == instance.spec["derived"]["output_position_x"]
    with pytest.raises(InvalidParameterError, match="between 0 and stroke"):
        instantiate("actuator.linear.electric", kind="rod", frame="60", stroke=100, position=101)


def test_sensor_exposes_functional_clearances_beyond_body_envelope():
    instance = instantiate("M18接近开关")
    assert {item["id"] for item in instance.interfaces} == {"threaded_mount", "sensing_face", "cable_exit"}
    assert {item["id"] for item in instance.spec["keepouts"]} == {"sensing_clearance", "rear_connector_and_bend"}


def test_square_fan_exposes_mount_pattern_and_airflow_keepouts():
    instance = instantiate("fan.axial.square.120")
    assert len(instance.interfaces) == 6
    assert {item["id"] for item in instance.spec["keepouts"]} == {"intake_clearance", "exhaust_clearance"}


def test_leveling_foot_and_caster_publish_floor_datums():
    foot = instantiate("hardware.leveling_foot.m16")
    caster = instantiate("hardware.caster.100-plate")
    assert "floor_contact" in {item["id"] for item in foot.interfaces}
    assert {"floor_contact", "mounting_plate", "swivel_axis"} <= {item["id"] for item in caster.interfaces}
    assert caster.spec["keepouts"][0]["id"] == "wheel_or_swivel_sweep"


def test_catalog_search_finds_common_purchased_hardware():
    assert search("120mm 散热风扇")[0]["id"] == "fan.axial.square.120"
