"""Acceptance tests for the declarative stepped-shaft generator.

The headline property is that a caller declares *relationships* — which library
part seats where — and never types a seat diameter. These tests pin that down by
swapping catalogue parts and asserting the shaft follows.
"""

from math import isclose, pi

import pytest

from cadparts import (
    Free,
    Seat,
    ShaftSpec,
    derive,
    shaft_dimensions,
    shaft_reference_checks,
    stepped_shaft,
)
from cadparts.errors import InvalidParameterError
from cadparts.interfaces import resolve_interfaces


def single_seat_shaft(code: str):
    return ShaftSpec(stations=(
        Seat("bearing.deep_groove", {"code": code}, "shaft_bore", role="support_a"),
    ))


def twin_seat_shaft(code: str):
    return ShaftSpec(stations=(
        Seat("bearing.deep_groove", {"code": code}, "shaft_bore", role="support_a"),
        Free(30.0, 12.0, role="spacer"),
        Seat("bearing.deep_groove", {"code": code}, "shaft_bore", role="support_b"),
    ))


def analytical_volume(stations) -> float:
    return pi / 4 * sum(item["diameter"] ** 2 * item["length"] for item in stations)


# --------------------------------------------------------------------------
# The headline property: declare the relationship, not the size
# --------------------------------------------------------------------------

@pytest.mark.parametrize("code,bore,width", [("6204", 20.0, 14.0), ("6205", 25.0, 15.0)])
def test_seat_size_is_derived_from_the_bearing_interface(code, bore, width):
    station = shaft_dimensions(single_seat_shaft(code))["stations"][0]
    assert station["diameter"] == pytest.approx(bore)
    assert station["length"] == pytest.approx(width)
    assert station["source"]["family"] == "bearing.deep_groove"
    assert station["source"]["interface"] == "shaft_bore"


def test_swapping_the_bearing_moves_the_whole_shaft():
    """Only the catalogue designation changes; every size must follow."""

    small = shaft_dimensions(twin_seat_shaft("6204"))
    large = shaft_dimensions(twin_seat_shaft("6205"))

    assert [s["diameter"] for s in small["stations"]] == pytest.approx([20.0, 30.0, 20.0])
    assert [s["diameter"] for s in large["stations"]] == pytest.approx([25.0, 30.0, 25.0])
    # The spacer length is literal, so total length grows only by the bearings.
    assert small["total_length"] == pytest.approx(40.0)
    assert large["total_length"] == pytest.approx(42.0)


def test_shaft_spec_carries_no_seat_diameter_literal():
    """Guard the design intent: a seat station must not accept a diameter."""

    assert "diameter" not in Seat.__dataclass_fields__
    assert "diameter" in Free.__dataclass_fields__


# --------------------------------------------------------------------------
# Geometry
# --------------------------------------------------------------------------

@pytest.mark.parametrize("code", ["6204", "6205"])
def test_shaft_is_one_solid_with_analytical_volume(code):
    spec = twin_seat_shaft(code)
    part = stepped_shaft(spec)
    stations = shaft_dimensions(spec)["stations"]

    assert len(part.solids()) == 1
    assert part.volume == pytest.approx(analytical_volume(stations), rel=1e-9)


def test_shaft_bounding_box_is_the_axial_stack():
    spec = twin_seat_shaft("6204")
    part = stepped_shaft(spec)
    derived = shaft_dimensions(spec)

    assert tuple(part.bounding_box().size) == pytest.approx(
        (derived["max_diameter"], derived["max_diameter"], derived["total_length"])
    )


def test_single_station_shaft_revolves_without_degenerate_faces():
    part = stepped_shaft(single_seat_shaft("6204"))
    assert len(part.solids()) == 1
    assert part.volume == pytest.approx(pi / 4 * 20.0**2 * 14.0, rel=1e-9)


# --------------------------------------------------------------------------
# Interfaces and the mating judgement
# --------------------------------------------------------------------------

def bearing_bore(code: str) -> dict:
    derived = derive("bearing.deep_groove", code=code)
    interfaces = resolve_interfaces("bearing.deep_groove", {"code": code}, derived)
    return next(item for item in interfaces if item["id"] == "shaft_bore")


def shaft_interface(spec: ShaftSpec, interface_id: str) -> dict:
    interfaces = resolve_interfaces("shaft.stepped", {}, shaft_dimensions(spec))
    return next(item for item in interfaces if item["id"] == interface_id)


def mate_passes(bore: dict, surface: dict) -> bool:
    """Smallest useful mating rule: a cylindrical bore fits a cylindrical surface
    of equal nominal diameter. This is a test-local seed of the eventual checker,
    not the checker itself — it carries no tolerance or fit model."""

    if (bore["type"], surface["type"]) != ("cylindrical_bore", "cylindrical_surface"):
        return False
    return isclose(
        float(bore["dimensions_mm"]["diameter"]),
        float(surface["dimensions_mm"]["diameter"]),
        rel_tol=0.0,
        abs_tol=1e-9,
    )


@pytest.mark.parametrize("code", ["6204", "6205"])
def test_seat_mates_with_the_bearing_it_was_declared_for(code):
    assert mate_passes(bearing_bore(code), shaft_interface(single_seat_shaft(code), "seat_support_a"))


def test_mating_judgement_rejects_a_mismatched_pair():
    """The negative case: a 6205 bearing against a shaft sized for 6204 must fail.

    Without this the positive case above would prove nothing.
    """

    shaft = single_seat_shaft("6204")
    assert not mate_passes(bearing_bore("6205"), shaft_interface(shaft, "seat_support_a"))


def test_shaft_emits_shoulders_and_datum_interfaces():
    ids = {
        item["id"]
        for item in resolve_interfaces("shaft.stepped", {}, shaft_dimensions(twin_seat_shaft("6204")))
    }
    assert ids == {
        "seat_support_a",
        "journal_spacer",
        "seat_support_b",
        "shoulder_support_a_spacer",
        "shoulder_spacer_support_b",
        "end_min",
        "end_max",
        "rotation_axis",
    }


def test_shoulder_reports_both_diameters():
    derived = shaft_dimensions(twin_seat_shaft("6204"))
    shoulder = derived["shoulders"][0]
    assert shoulder["outer_diameter"] == pytest.approx(30.0)
    assert shoulder["inner_diameter"] == pytest.approx(20.0)
    assert shoulder["at_z"] == pytest.approx(14.0)


def test_adjacent_equal_diameters_produce_no_shoulder():
    spec = ShaftSpec(stations=(
        Free(20.0, 10.0, role="a"),
        Free(20.0, 10.0, role="b"),
    ))
    assert shaft_dimensions(spec)["shoulders"] == []


# --------------------------------------------------------------------------
# Explicit allowances and error paths
# --------------------------------------------------------------------------

def test_diameter_delta_is_an_explicit_allowance_not_a_fit_claim():
    spec = ShaftSpec(stations=(
        Seat("bearing.deep_groove", {"code": "6204"}, "shaft_bore", role="support_a",
             diameter_delta=-0.01),
    ))
    station = shaft_dimensions(spec)["stations"][0]
    assert station["diameter"] == pytest.approx(19.99)
    assert station["nominal_diameter"] == pytest.approx(20.0)

    check = shaft_reference_checks(spec)[0]
    assert check["nominal_diameter"] == pytest.approx(20.0)
    assert check["delta"] == pytest.approx(-0.01)


def test_seat_length_can_be_overridden_for_a_narrower_shoulder():
    spec = ShaftSpec(stations=(
        Seat("bearing.deep_groove", {"code": "6204"}, "shaft_bore", role="support_a", length=20.0),
    ))
    assert shaft_dimensions(spec)["total_length"] == pytest.approx(20.0)


def test_unknown_interface_names_the_available_ones():
    spec = ShaftSpec(stations=(
        Seat("bearing.deep_groove", {"code": "6204"}, "not_an_interface", role="support_a"),
    ))
    with pytest.raises(InvalidParameterError, match="no interface"):
        shaft_dimensions(spec)


def test_unknown_catalogue_part_fails_loudly():
    spec = ShaftSpec(stations=(
        Seat("bearing.deep_groove", {"code": "9999"}, "shaft_bore", role="support_a"),
    ))
    with pytest.raises(InvalidParameterError):
        shaft_dimensions(spec)


def test_interface_without_a_diameter_cannot_size_a_seat():
    spec = ShaftSpec(stations=(
        Seat("bearing.deep_groove", {"code": "6204"}, "axial_face_min", role="support_a"),
    ))
    with pytest.raises(InvalidParameterError, match="no diameter"):
        shaft_dimensions(spec)


def test_empty_shaft_spec_is_rejected():
    with pytest.raises(InvalidParameterError, match="at least one station"):
        ShaftSpec(stations=())


def test_non_positive_station_is_rejected():
    with pytest.raises(InvalidParameterError, match="diameter must be positive"):
        shaft_dimensions(ShaftSpec(stations=(Free(0.0, 10.0),)))
    with pytest.raises(InvalidParameterError, match="length must be positive"):
        shaft_dimensions(ShaftSpec(stations=(Free(10.0, 0.0),)))
