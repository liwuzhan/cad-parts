"""Tests for the mate graph evaluator.

Two properties matter beyond the individual rules:

* ``UNKNOWN`` must never collapse into ``PASS``. A pairing nobody wrote a rule
  for is an admission that nothing was verified.
* Evaluation must stay free of geometry. The compiler type-checks its IR before
  codegen; a "cheap check" that quietly builds solids has lost the plot.
"""

from pathlib import Path

import pytest

from cadparts import (
    MATE_SCHEMA,
    VERDICT_FAIL,
    VERDICT_NONE,
    VERDICT_PASS,
    VERDICT_UNKNOWN,
    VERDICT_WARN,
    derive,
    evaluate_mates,
    evaluate_pair,
    rule_for,
)
from cadparts.interfaces import resolve_interfaces


# --------------------------------------------------------------------------
# Port builders (same shape as cadparts.interfaces emits)
# --------------------------------------------------------------------------

def port(port_id: str, port_type: str, **dimensions):
    return {
        "id": port_id,
        "type": port_type,
        "role": f"test port {port_id}",
        "frame": {"origin_mm": [0.0, 0.0, 0.0], "axis": [0.0, 0.0, 1.0]},
        **({"dimensions_mm": dimensions} if dimensions else {}),
    }


def port_axis(port_id: str, port_type: str, axis, **dimensions):
    item = port(port_id, port_type, **dimensions)
    item["frame"]["axis"] = list(axis)
    return item


# --------------------------------------------------------------------------
# Rule lookup
# --------------------------------------------------------------------------

def test_rule_lookup_is_order_independent():
    forward = rule_for("cylindrical_bore", "cylindrical_surface")
    backward = rule_for("cylindrical_surface", "cylindrical_bore")
    assert forward is not None and forward is backward


def test_unknown_pairing_has_no_rule():
    assert rule_for("planar_face", "wheel_contact") is None


# --------------------------------------------------------------------------
# Individual rules
# --------------------------------------------------------------------------

def test_bore_passes_only_on_a_nominal_match():
    bore = port("b", "cylindrical_bore", diameter=25.0)
    assert evaluate_pair(bore, port("s", "cylindrical_surface", diameter=25.0))[0] == VERDICT_PASS


def test_oversized_bore_warns_rather_than_passing_silently():
    """It assembles, but the nominal sizes disagree — that must not read as PASS.

    A 6205 bearing on a 6204 shaft is exactly this case: it goes on, and it is
    the wrong part (or a deliberate clearance fit nobody declared).
    """

    bore = port("b", "cylindrical_bore", diameter=25.0)
    verdict, reason = evaluate_pair(bore, port("s", "cylindrical_surface", diameter=20.0))
    assert verdict == VERDICT_WARN
    assert "公称尺寸不符" in reason


def test_bore_rejects_a_shaft_that_cannot_enter():
    bore = port("b", "cylindrical_bore", diameter=20.0)
    verdict, reason = evaluate_pair(bore, port("s", "cylindrical_surface", diameter=25.0))
    assert verdict == VERDICT_FAIL
    assert "装不进去" in reason


def test_bore_pairing_is_symmetric_in_argument_order():
    bore = port("b", "cylindrical_bore", diameter=20.0)
    shaft = port("s", "cylindrical_surface", diameter=25.0)
    assert evaluate_pair(bore, shaft)[0] == evaluate_pair(shaft, bore)[0] == VERDICT_FAIL


def test_threads_require_matching_diameter_and_pitch():
    male = port("m", "male_thread_envelope", nominal_diameter=8.0, pitch=1.25)
    assert evaluate_pair(male, port("f", "female_thread_envelope",
                                    nominal_diameter=8.0, pitch=1.25))[0] == VERDICT_PASS

    verdict, reason = evaluate_pair(male, port("f", "female_thread_envelope",
                                               nominal_diameter=10.0, pitch=1.25))
    assert verdict == VERDICT_FAIL and "公称直径不符" in reason

    verdict, reason = evaluate_pair(male, port("f", "female_thread_envelope",
                                               nominal_diameter=8.0, pitch=1.0))
    assert verdict == VERDICT_FAIL and "螺距不符" in reason


def test_missing_dimensions_yield_unknown_not_pass():
    male = port("m", "male_thread_envelope")
    female = port("f", "female_thread_envelope", nominal_diameter=8.0, pitch=1.25)
    verdict, reason = evaluate_pair(male, female)
    assert verdict == VERDICT_UNKNOWN
    assert "无法判定" in reason


def test_clearance_hole_admits_the_shank_but_not_a_larger_one():
    hole = port("h", "clearance_hole", diameter=9.0)
    assert evaluate_pair(hole, port("s", "male_thread_envelope", nominal_diameter=8.0))[0] == VERDICT_PASS
    assert evaluate_pair(hole, port("s", "male_thread_envelope", nominal_diameter=10.0))[0] == VERDICT_FAIL


def test_planar_faces_must_face_each_other():
    up = port_axis("a", "planar_face", (0.0, 0.0, 1.0))
    down = port_axis("b", "planar_face", (0.0, 0.0, -1.0))
    same_way = port_axis("c", "planar_face", (0.0, 0.0, 1.0))

    assert evaluate_pair(up, down)[0] == VERDICT_PASS
    verdict, reason = evaluate_pair(up, same_way)
    assert verdict == VERDICT_FAIL and "不是反向" in reason


def test_degenerate_axis_is_refused_rather_than_guessed():
    up = port_axis("a", "planar_face", (0.0, 0.0, 1.0))
    degenerate = port_axis("b", "planar_face", (0.0, 0.0, 0.0))
    assert evaluate_pair(up, degenerate)[0] == VERDICT_UNKNOWN


# --------------------------------------------------------------------------
# Graph evaluation, coverage and the verification boundary
# --------------------------------------------------------------------------

def test_graph_pass_reports_coverage_of_unmated_ports():
    instances = {
        "shaft": [port("seat", "cylindrical_surface", diameter=20.0),
                  port("spare", "planar_face")],
        "bearing": [port("bore", "cylindrical_bore", diameter=20.0)],
    }
    result = evaluate_mates(instances, [{"a": "shaft.seat", "b": "bearing.bore", "why": "seat"}])

    assert result["schema"] == MATE_SCHEMA
    assert result["overall"] == VERDICT_PASS
    assert result["summary"] == {VERDICT_PASS: 1, VERDICT_WARN: 0, VERDICT_FAIL: 0, VERDICT_UNKNOWN: 0}
    assert result["coverage"]["declared_ports"] == 3
    assert result["coverage"]["mated_ports"] == 2
    assert result["coverage"]["unmated_ports"] == ["shaft.spare"]


def test_overall_severity_order_fail_warn_unknown_pass():
    """FAIL > WARN > UNKNOWN > PASS. A caution outranks not knowing, and every
    one of them outranks a bare pass — otherwise a warning hides behind silence."""

    def overall(pairs, instances):
        return evaluate_mates(instances, [{"a": a, "b": b} for a, b in pairs])["overall"]

    # One definite failure plus everything else benign.
    instances = {
        "a": [port("p", "cylindrical_surface", diameter=30.0)],
        "b": [port("q", "cylindrical_bore", diameter=20.0)],
        "c": [port("r", "wheel_contact")],
    }
    assert overall([("a.p", "b.q"), ("a.p", "c.r")], instances) == VERDICT_FAIL
    assert overall([("a.p", "c.r")], instances) == VERDICT_UNKNOWN

    mixed = {
        "a": [port("p", "cylindrical_surface", diameter=20.0)],
        "b": [port("q", "cylindrical_bore", diameter=25.0)],
        "c": [port("r", "wheel_contact")],
    }
    assert overall([("a.p", "b.q")], mixed) == VERDICT_WARN
    assert overall([("a.p", "b.q"), ("a.p", "c.r")], mixed) == VERDICT_WARN

    passing = {
        "a": [port("p", "cylindrical_surface", diameter=20.0)],
        "b": [port("q", "cylindrical_bore", diameter=20.0)],
    }
    assert overall([("a.p", "b.q")], passing) == VERDICT_PASS


def test_unknown_pairing_is_reported_as_unknown_with_a_reason():
    instances = {"x": [port("p", "planar_face")], "y": [port("q", "wheel_contact")]}
    result = evaluate_mates(instances, [{"a": "x.p", "b": "y.q"}])
    entry = result["verdicts"][0]
    assert entry["verdict"] == VERDICT_UNKNOWN
    assert "未被验证" in entry["reason"]


@pytest.mark.parametrize("ref_a,ref_b,expected", [
    ("shaft", "b.bore", "不是 '实例.接口' 形式"),
    ("nope.port", "b.bore", "没有实例"),
    ("s.missing", "b.bore", "没有接口"),
])
def test_declaration_errors_fail_with_an_actionable_reason(ref_a, ref_b, expected):
    instances = {"s": [port("seat", "cylindrical_surface", diameter=20.0)],
                 "b": [port("bore", "cylindrical_bore", diameter=20.0)]}
    result = evaluate_mates(instances, [{"a": ref_a, "b": ref_b}])
    entry = result["verdicts"][0]
    assert entry["verdict"] == VERDICT_FAIL
    assert expected in entry["reason"]


def test_boundary_states_what_was_not_checked():
    result = evaluate_mates(
        {"p": [port("b", "cylindrical_bore", diameter=10.0),
               port("s", "cylindrical_surface", diameter=10.0)]},
        [{"a": "p.b", "b": "p.s"}],
    )
    assert result["overall"] == VERDICT_PASS
    assert "not_checked" in result["boundary"]
    assert any("公差" in item for item in result["boundary"]["not_checked"])


# --------------------------------------------------------------------------
# A vacuous pass is not a pass
# --------------------------------------------------------------------------

def test_nothing_compared_reports_nothing_to_check_not_pass():
    """An empty graph must not read as verified.

    Observed in practice: a package with six declared ports and no mates used to
    report ``overall: PASS``, which is the most misleading thing a checker can
    say — a reader sees the word and stops looking.
    """

    assert evaluate_mates({}, [])["overall"] == VERDICT_NONE


def test_declared_ports_without_any_mate_also_report_nothing_to_check():
    result = evaluate_mates(
        {"p": [port("b", "cylindrical_bore", diameter=10.0)]}, []
    )
    assert result["overall"] == VERDICT_NONE
    assert result["coverage"]["declared_ports"] == 1
    assert result["coverage"]["unmated_ports"] == ["p.b"]


def test_a_single_real_comparison_still_reports_pass():
    result = evaluate_mates(
        {"p": [port("b", "cylindrical_bore", diameter=10.0),
               port("s", "cylindrical_surface", diameter=10.0)]},
        [{"a": "p.b", "b": "p.s"}],
    )
    assert result["overall"] == VERDICT_PASS


def test_why_field_is_carried_through():
    instances = {"s": [port("seat", "cylindrical_surface", diameter=20.0)],
                 "b": [port("bore", "cylindrical_bore", diameter=20.0)]}
    result = evaluate_mates(instances, [{"a": "s.seat", "b": "b.bore", "why": "轴颈支撑"}])
    assert result["verdicts"][0]["why"] == "轴颈支撑"


# --------------------------------------------------------------------------
# Architectural guard
# --------------------------------------------------------------------------

def test_evaluator_module_imports_no_geometry_kernel():
    """The IR check must stay runnable without a geometry kernel.

    If someone later imports build123d here, the 'check before codegen' ordering
    silently stops being true, so fail loudly instead.
    """

    source = Path(__file__).resolve().parents[1] / "src" / "cadparts" / "mates.py"
    text = source.read_text(encoding="utf-8")
    assert "build123d" not in text
    assert "OCP" not in text


# --------------------------------------------------------------------------
# Integration with real library ports (the P4 shaft meets the P2 evaluator)
# --------------------------------------------------------------------------

def real_ports():
    from cadparts import Free, Seat, ShaftSpec, shaft_dimensions, stepped_shaft  # noqa: F401

    spec = ShaftSpec(stations=(
        Seat("bearing.deep_groove", {"code": "6204"}, "shaft_bore", role="support_a"),
    ))
    shaft_ports = resolve_interfaces("shaft.stepped", {}, shaft_dimensions(spec))
    bearing_ports = resolve_interfaces(
        "bearing.deep_groove", {"code": "6204"}, derive("bearing.deep_groove", code="6204")
    )
    return {"shaft": shaft_ports, "bearing": bearing_ports}


def test_real_shaft_seat_mates_with_its_bearing():
    instances = real_ports()
    result = evaluate_mates(instances, [{"a": "shaft.seat_support_a", "b": "bearing.shaft_bore"}])
    assert result["overall"] == VERDICT_PASS


def test_real_mismatched_bearing_is_caught():
    """6205 bearing against a shaft seated for 6204 must fail — the judgement needs teeth."""

    instances = real_ports()
    instances["bearing"] = resolve_interfaces(
        "bearing.deep_groove", {"code": "6205"}, derive("bearing.deep_groove", code="6205")
    )
    result = evaluate_mates(instances, [{"a": "shaft.seat_support_a", "b": "bearing.shaft_bore"}])
    # A 6205 bore (25) over a 6204-sized seat (20): it goes on, so this is not a
    # hard failure — but it must not read as a pass either.
    assert result["overall"] == VERDICT_WARN
    assert "公称尺寸不符" in result["verdicts"][0]["reason"]
