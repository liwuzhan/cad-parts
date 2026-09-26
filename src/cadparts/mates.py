"""Mate graph evaluation — the assembly's IR, checked without any geometry.

The point of this module is ordering: a compiler type-checks its IR *before* it
generates code. Here the IR is the assembly's interface graph, and evaluating it
must not require building a single solid — otherwise the check can only ever run
after the expensive step it was supposed to guard.

Two things are deliberately kept apart:

* **Rules** (this module) decide whether two named ports may join. They read only
  declared numbers and axes.
* **Resolution** (the toolchain) decides *where* a port comes from — a catalogue
  family, another package, or the package's own ``ports.py``.

Verdicts are three-valued. ``UNKNOWN`` is a first-class outcome, never a silent
``PASS``: a pair with no rule is an admission that nothing was verified, and the
caller is expected to surface that rather than bury it.
"""

from __future__ import annotations

from math import isclose
from typing import Any, Iterable, Mapping, Sequence

VERDICT_PASS = "PASS"
VERDICT_WARN = "WARN"
VERDICT_FAIL = "FAIL"
VERDICT_UNKNOWN = "UNKNOWN"

MATE_SCHEMA = "cadparts.mate-check/v1"

# Tolerance for declared-vs-declared comparisons. Declarations are nominal, so
# this only absorbs float representation, never manufacturing variation.
_NOMINAL_TOL = 1e-9

_PASS = (VERDICT_PASS, "")
_UNKNOWN = (VERDICT_UNKNOWN, "没有适用于该类型组合的配对规则，此项未被验证")

# Higher outranks lower when summarising a whole graph. A definite problem beats
# a caution, and a caution beats not knowing — but all three beat a bare pass.
_SEVERITY = [VERDICT_PASS, VERDICT_UNKNOWN, VERDICT_WARN, VERDICT_FAIL]


def _dims(port: Mapping[str, Any]) -> Mapping[str, Any]:
    return port.get("dimensions_mm") or {}


def _number(port: Mapping[str, Any], key: str) -> float | None:
    value = _dims(port).get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _axis(port: Mapping[str, Any]) -> tuple[float, float, float] | None:
    frame = port.get("frame") or {}
    raw = frame.get("axis")
    if not isinstance(raw, (list, tuple)) or len(raw) != 3:
        return None
    try:
        return (float(raw[0]), float(raw[1]), float(raw[2]))
    except (TypeError, ValueError):
        return None


def _antiparallel(a: Mapping[str, Any], b: Mapping[str, Any]) -> bool | None:
    """Two faces meet when their outward axes are opposed. None = not declared."""

    axis_a, axis_b = _axis(a), _axis(b)
    if axis_a is None or axis_b is None:
        return None
    # A degenerate axis is the zero vector. An axis merely *having* zero
    # components (e.g. (0, 0, 1)) is perfectly normal and must not be refused.
    if sum(component * component for component in axis_a) < _NOMINAL_TOL:
        return None
    if sum(component * component for component in axis_b) < _NOMINAL_TOL:
        return None
    dot = sum(x * y for x, y in zip(axis_a, axis_b))
    return isclose(dot, -1.0, rel_tol=0.0, abs_tol=1e-6)


def _split_by_type(
    a: Mapping[str, Any],
    b: Mapping[str, Any],
    type_a: str,
    type_b: str,
) -> tuple[Mapping[str, Any], Mapping[str, Any]] | None:
    """Return ``(port_of_type_a, port_of_type_b)`` regardless of argument order.

    Rules are written against *typed roles*, never against positional order —
    otherwise calling a rule with its arguments swapped silently judges the
    wrong thing (a 30 mm shaft in a 20 mm bore reads as a pass).
    """

    if a.get("type") == type_a and b.get("type") == type_b:
        return a, b
    if a.get("type") == type_b and b.get("type") == type_a:
        return b, a
    return None


# --------------------------------------------------------------------------
# Rules: one predicate per port-type pairing. Order-independent.
# --------------------------------------------------------------------------

def _bore_and_shaft(a: Mapping[str, Any], b: Mapping[str, Any]) -> tuple[str, str]:
    """A cylindrical bore receives a cylindrical surface.

    Three outcomes, because "will it go in" and "is this the right part" are
    different questions and collapsing them loses the useful one:

    * bore smaller than the shaft — it cannot be assembled: **FAIL**;
    * equal nominal diameters — a nominal match: **PASS**;
    * bore larger than the shaft — it assembles, but the nominal sizes disagree,
      which is either a deliberate clearance fit or simply the wrong part. That
      cannot be decided from declarations alone, so it is reported rather than
      silently accepted: **WARN**.
    """

    pair = _split_by_type(a, b, "cylindrical_bore", "cylindrical_surface")
    if pair is None:
        return _UNKNOWN
    bore, shaft = pair
    bore_d = _number(bore, "diameter")
    shaft_d = _number(shaft, "diameter")
    if bore_d is None or shaft_d is None:
        return VERDICT_UNKNOWN, "孔或轴的声明缺少 diameter，无法判定"
    if shaft_d > bore_d + _NOMINAL_TOL:
        return VERDICT_FAIL, f"轴径 ⌀{shaft_d:g} 大于孔径 ⌀{bore_d:g}，装不进去"
    if bore_d > shaft_d + _NOMINAL_TOL:
        return VERDICT_WARN, (
            f"孔径 ⌀{bore_d:g} 大于轴径 ⌀{shaft_d:g}，能装配但公称尺寸不符；"
            "若是间隙配合请显式声明，否则可能选错件"
        )
    return _PASS


def _thread_pair(a: Mapping[str, Any], b: Mapping[str, Any]) -> tuple[str, str]:
    """Threads join only on equal nominal diameter *and* equal pitch."""

    pair = _split_by_type(a, b, "male_thread_envelope", "female_thread_envelope")
    if pair is None:
        return _UNKNOWN
    male, female = pair
    d_m, d_f = _number(male, "nominal_diameter"), _number(female, "nominal_diameter")
    p_m, p_f = _number(male, "pitch"), _number(female, "pitch")
    if None in (d_m, d_f, p_m, p_f):
        return VERDICT_UNKNOWN, "螺纹声明缺少 nominal_diameter 或 pitch，无法判定"
    if not isclose(d_m, d_f, rel_tol=0.0, abs_tol=_NOMINAL_TOL):
        return VERDICT_FAIL, f"公称直径不符：{d_m:g} vs {d_f:g}"
    if not isclose(p_m, p_f, rel_tol=0.0, abs_tol=_NOMINAL_TOL):
        return VERDICT_FAIL, f"螺距不符：{p_m:g} vs {p_f:g}"
    return _PASS


def _clearance_hole_and_shank(a: Mapping[str, Any], b: Mapping[str, Any]) -> tuple[str, str]:
    """A screw shank passes through a clearance hole."""

    pair = _split_by_type(a, b, "clearance_hole", "male_thread_envelope")
    if pair is None:
        pair = _split_by_type(a, b, "clearance_hole", "male_shaft")
    if pair is None:
        return _UNKNOWN
    hole, shank = pair
    hole_d = _number(hole, "diameter")
    shank_d = _number(shank, "nominal_diameter")
    if shank_d is None:
        shank_d = _number(shank, "diameter")
    if hole_d is None or shank_d is None:
        return VERDICT_UNKNOWN, "通孔或杆件声明缺少直径，无法判定"
    if shank_d > hole_d + _NOMINAL_TOL:
        return VERDICT_FAIL, f"杆径 ⌀{shank_d:g} 大于通孔 ⌀{hole_d:g}，穿不过去"
    return _PASS


def _planar_pair(a: Mapping[str, Any], b: Mapping[str, Any]) -> tuple[str, str]:
    """Two planar faces mate when their outward normals are opposed."""

    opposed = _antiparallel(a, b)
    if opposed is None:
        return VERDICT_UNKNOWN, "平面声明缺少可用的 axis，无法判定朝向"
    if not opposed:
        return VERDICT_FAIL, "两个平面的外法线不是反向，贴合不上"
    return _PASS


def _shaft_and_shaft_end(a: Mapping[str, Any], b: Mapping[str, Any]) -> tuple[str, str]:
    return VERDICT_UNKNOWN, "轴端与其它轴端之间没有可判定的配合语义"


_RULES: dict[frozenset, Any] = {
    frozenset({"cylindrical_bore", "cylindrical_surface"}): _bore_and_shaft,
    frozenset({"male_thread_envelope", "female_thread_envelope"}): _thread_pair,
    frozenset({"clearance_hole", "male_thread_envelope"}): _clearance_hole_and_shank,
    frozenset({"clearance_hole", "male_shaft"}): _clearance_hole_and_shank,
    frozenset({"planar_face", "planar_face"}): _planar_pair,
}


def rule_for(type_a: str, type_b: str):
    """Return the rule for a port-type pairing, or None when nothing applies."""

    return _RULES.get(frozenset({type_a, type_b}))


def evaluate_pair(port_a: Mapping[str, Any], port_b: Mapping[str, Any]) -> tuple[str, str]:
    """Judge one pair of declared ports. Pure: reads only the two dicts.

    Order-independent: every rule locates its own roles by port type, so swapping
    the arguments cannot change the verdict.
    """

    rule = rule_for(str(port_a.get("type")), str(port_b.get("type")))
    if rule is None:
        return _UNKNOWN
    return rule(port_a, port_b)


# --------------------------------------------------------------------------
# Graph evaluation
# --------------------------------------------------------------------------

def _lookup(instances: Mapping[str, Sequence[Mapping[str, Any]]], ref: str):
    """Resolve ``instance.port`` into ``(instance, port)`` or an error string."""

    if "." not in ref:
        return None, f"引用 {ref!r} 不是 '实例.接口' 形式"
    instance_name, port_id = ref.split(".", 1)
    ports = instances.get(instance_name)
    if ports is None:
        known = sorted(instances)
        return None, f"没有实例 {instance_name!r}；已知实例：{known}"
    match = next((item for item in ports if item.get("id") == port_id), None)
    if match is None:
        known = sorted(str(item.get("id")) for item in ports)
        return None, f"实例 {instance_name!r} 没有接口 {port_id!r}；可用：{known}"
    return (instance_name, port_id, match), None


def evaluate_mates(
    instances: Mapping[str, Sequence[Mapping[str, Any]]],
    mates: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Evaluate declared mates over named ports. Builds no geometry.

    Parameters
    ----------
    instances:
        ``{instance_name: [port, ...]}``. Every port is the same shape as
        ``cadparts.interfaces.resolve_interfaces`` emits, so a catalogue part and
        a model-authored part are indistinguishable here.
    mates:
        ``[{"a": "instance.port", "b": "instance.port", "why": "..."}, ...]``.
    """

    verdicts: list[dict[str, Any]] = []
    mated: set[str] = set()

    for index, mate in enumerate(mates):
        ref_a, ref_b = str(mate.get("a", "")), str(mate.get("b", ""))
        entry: dict[str, Any] = {
            "index": index,
            "a": ref_a,
            "b": ref_b,
        }
        if mate.get("why"):
            entry["why"] = str(mate["why"])

        found_a, err_a = _lookup(instances, ref_a)
        found_b, err_b = _lookup(instances, ref_b)
        if err_a or err_b:
            entry.update(verdict=VERDICT_FAIL, reason=err_a or err_b,
                         type_a=None, type_b=None)
            verdicts.append(entry)
            continue

        instance_a, port_a_id, port_a = found_a
        instance_b, port_b_id, port_b = found_b
        mated.add(f"{instance_a}.{port_a_id}")
        mated.add(f"{instance_b}.{port_b_id}")

        verdict, reason = evaluate_pair(port_a, port_b)
        entry.update(
            verdict=verdict,
            reason=reason,
            type_a=port_a.get("type"),
            type_b=port_b.get("type"),
        )
        verdicts.append(entry)

    # Coverage is the part that keeps a green result honest: it states which
    # declared ports no mate referenced, so "PASS" is never mistaken for
    # "everything was verified".
    declared = {
        f"{name}.{port.get('id')}"
        for name, ports in instances.items()
        for port in ports
    }
    unmated = sorted(declared - mated)

    summary = {
        VERDICT_PASS: sum(1 for item in verdicts if item["verdict"] == VERDICT_PASS),
        VERDICT_WARN: sum(1 for item in verdicts if item["verdict"] == VERDICT_WARN),
        VERDICT_FAIL: sum(1 for item in verdicts if item["verdict"] == VERDICT_FAIL),
        VERDICT_UNKNOWN: sum(1 for item in verdicts if item["verdict"] == VERDICT_UNKNOWN),
    }
    # Worst wins; an empty graph is vacuously a pass.
    overall = next(
        (level for level in reversed(_SEVERITY) if summary[level]),
        VERDICT_PASS,
    )

    return {
        "schema": MATE_SCHEMA,
        "verdicts": verdicts,
        "summary": summary,
        "coverage": {
            "declared_ports": len(declared),
            "mated_ports": len(mated),
            "unmated_ports": unmated,
            "note": "未被任何 mate 引用的接口不在本次判定范围内",
        },
        "boundary": {
            "checked": "已声明的接口之间是否可配合（纯几何语义，不涉及强度、公差与工艺）",
            "not_checked": [
                "未声明 matcher 的接口",
                "配合公差与 ISO 286 配合带",
                "强度、寿命、热、振动",
                "装配可达性与工具空间",
            ],
        },
        "overall": overall,
    }


__all__ = [
    "MATE_SCHEMA",
    "VERDICT_FAIL",
    "VERDICT_PASS",
    "VERDICT_UNKNOWN",
    "VERDICT_WARN",
    "evaluate_mates",
    "evaluate_pair",
    "rule_for",
]
