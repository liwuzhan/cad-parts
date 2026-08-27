"""Flexible coupling envelopes for coaxial assembly layout."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from build123d import Compound

from .catalog import register
from .errors import InvalidParameterError
from .models import FamilyDefinition, ParameterSpec
from .proxy import axial_cylinder, choice, compound, cylinder_keepout, real


@dataclass(frozen=True, slots=True)
class Profile:
    diameter: float; length: float; max_bore: float; gap: float


PROFILES = {
    ("jaw", "14"): Profile(30, 35, 14, 3), ("jaw", "19"): Profile(40, 50, 19, 4),
    ("jaw", "24"): Profile(55, 65, 24, 5), ("jaw", "28"): Profile(65, 75, 28, 5), ("jaw", "38"): Profile(85, 90, 38, 6),
    ("disc", "14"): Profile(32, 40, 14, 6), ("disc", "20"): Profile(45, 55, 20, 8),
    ("disc", "25"): Profile(55, 65, 25, 9), ("disc", "35"): Profile(75, 85, 35, 12),
    ("clamp", "8"): Profile(20, 25, 8, 2), ("clamp", "12"): Profile(30, 35, 12, 3),
    ("clamp", "16"): Profile(40, 45, 16, 4), ("clamp", "20"): Profile(50, 55, 20, 5),
}


def flexible_coupling_dimensions(kind: str, size: str | int, *, bore_a: float | None = None, bore_b: float | None = None) -> dict[str, Any]:
    family = choice("kind", str(kind).lower(), ("jaw", "disc", "clamp"))
    code = str(size)
    if (family, code) not in PROFILES:
        available = ", ".join(value for name, value in PROFILES if name == family)
        raise InvalidParameterError(f"unsupported {family} coupling size {code!r}; available: {available}")
    p = PROFILES[(family, code)]
    first = min(p.max_bore, max(4, p.max_bore * 0.5)) if bore_a is None else real("bore_a", bore_a, positive=True)
    second = first if bore_b is None else real("bore_b", bore_b, positive=True)
    if max(first, second) > p.max_bore:
        raise InvalidParameterError(f"bore must be <= {p.max_bore:g} mm for {family} size {code}")
    half = (p.length - p.gap) / 2
    return {
        "coupling_type": family, "size": code, "outside_diameter": p.diameter,
        "overall_length": p.length, "flexible_gap": p.gap,
        "hub_length_a": half, "hub_length_b": half, "bore_a": first, "bore_b": second,
        "maximum_bore": p.max_bore, "unit": "mm",
        "keepout_envelopes": [cylinder_keepout(
            "rotating_coupling", p.diameter + 6, p.length, (0, 0, 0), (0, 0, 1),
            "Rotating outside envelope plus 3 mm radial planning clearance.",
        )],
    }


def flexible_coupling(kind: str, size: str | int, *, bore_a: float | None = None, bore_b: float | None = None) -> Compound:
    d = flexible_coupling_dimensions(kind, size, bore_a=bore_a, bore_b=bore_b)
    half, gap = float(d["hub_length_a"]), float(d["flexible_gap"])
    hub_a = axial_cylinder(float(d["outside_diameter"]), half) - axial_cylinder(float(d["bore_a"]), half + 2, origin=(0, 0, -1))
    hub_b = axial_cylinder(float(d["outside_diameter"]), float(d["hub_length_b"]), origin=(0, 0, half + gap)) - axial_cylinder(float(d["bore_b"]), float(d["hub_length_b"]) + 2, origin=(0, 0, half + gap - 1))
    middle = axial_cylinder(float(d["outside_diameter"]) * (0.86 if d["coupling_type"] == "jaw" else 0.72), gap, origin=(0, 0, half))
    return compound(f"{d['coupling_type']} coupling {d['size']}", hub_a, middle, hub_b)


register(FamilyDefinition(
    key="coupling.flexible", category="coupling", title="Flexible shaft coupling / 弹性联轴器",
    description="Jaw, disc and clamp-style coupling envelopes with independent shaft bores.",
    factory=flexible_coupling, derive=flexible_coupling_dimensions,
    parameters=(ParameterSpec("kind", "string", "Coupling construction", choices=("jaw", "disc", "clamp")), ParameterSpec("size", "string", "Finite planning size"), ParameterSpec("bore_a", "number|null", "First shaft bore", "mm", required=False, default=None), ParameterSpec("bore_b", "number|null", "Second shaft bore", "mm", required=False, default=None)),
    aliases=("flexible_coupling", "jaw_coupling", "plum_coupling", "联轴器", "梅花联轴器"),
    orientation="coaxial bores +Z; shaft A enters at Z=0", detail="rotating envelope, two bores and flexible gap",
    validation="finite profiles, bore bounds, interfaces and STEP/PNG review", example="instantiate('coupling.flexible.jaw19', bore_a=8, bore_b=14)",
    notes=("Torque, misalignment rating, keyways and clamp-screw detail remain purchase attributes.",),
))
