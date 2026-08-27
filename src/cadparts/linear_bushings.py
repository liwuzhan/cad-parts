"""Round-shaft linear-ball-bushing envelopes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from build123d import Box, Compound, Cylinder, Pos

from .catalog import register
from .errors import InvalidParameterError
from .models import FamilyDefinition, ParameterSpec
from .proxy import CENTER_MIN, axial_cylinder, choice, compound, cylinder_keepout


@dataclass(frozen=True, slots=True)
class Profile:
    bore: float; outside: float; length: float; flange: float; flange_thickness: float; flange_pitch: float; flange_hole: float


PROFILES = {
    "8": Profile(8, 15, 24, 32, 6, 24, 4.5), "10": Profile(10, 19, 29, 40, 6, 30, 5.5),
    "12": Profile(12, 21, 30, 42, 6, 32, 5.5), "16": Profile(16, 28, 37, 48, 8, 38, 5.5),
    "20": Profile(20, 32, 42, 54, 8, 43, 6.6), "25": Profile(25, 40, 59, 62, 8, 51, 6.6),
    "30": Profile(30, 45, 64, 74, 10, 60, 9), "40": Profile(40, 60, 80, 96, 12, 78, 11),
}


def linear_bushing_dimensions(style: str, bore: str | int) -> dict[str, Any]:
    family = choice("style", style.upper(), ("LM", "LME", "LMF", "LMK"))
    code = choice("bore", str(bore), PROFILES)
    p = PROFILES[code]
    flanged = family in {"LMF", "LMK"}
    return {
        "bushing_style": family, "bore_diameter": p.bore, "outside_diameter": p.outside,
        "body_length": p.length, "flanged": flanged,
        "flange_shape": "round" if family == "LMF" else "square" if family == "LMK" else "none",
        "flange_size": p.flange if flanged else 0, "flange_thickness": p.flange_thickness if flanged else 0,
        "flange_hole_pitch": p.flange_pitch if flanged else 0, "flange_hole_diameter": p.flange_hole if flanged else 0,
        "unit": "mm",
        "keepout_envelopes": [cylinder_keepout("moving_bushing", p.flange if flanged else p.outside, p.length, (0, 0, 0), (0, 0, 1), "Bushing outer envelope while translating on the shaft.")],
    }


def linear_bushing(style: str, bore: str | int) -> Compound:
    d = linear_bushing_dimensions(style, bore)
    body = axial_cylinder(float(d["outside_diameter"]), float(d["body_length"])) - axial_cylinder(float(d["bore_diameter"]), float(d["body_length"]) + 2, origin=(0, 0, -1))
    children = [body]
    if d["flanged"]:
        thickness = float(d["flange_thickness"])
        if d["flange_shape"] == "round":
            flange = Cylinder(float(d["flange_size"]) / 2, thickness, align=CENTER_MIN)
        else:
            flange = Box(float(d["flange_size"]), float(d["flange_size"]), thickness, align=CENTER_MIN)
        flange = flange - Cylinder(float(d["bore_diameter"]) / 2, thickness + 2, align=CENTER_MIN)
        pitch = float(d["flange_hole_pitch"])
        for x in (-pitch / 2, pitch / 2):
            for y in (-pitch / 2, pitch / 2):
                flange = flange - Pos(x, y, -1) * Cylinder(float(d["flange_hole_diameter"]) / 2, thickness + 2, align=CENTER_MIN)
        children.append(flange)
    return compound(f"{d['bushing_style']}{int(d['bore_diameter'])}", *children)


register(FamilyDefinition(
    key="linear.bushing.ball", category="linear", title="Linear ball bushing / 直线轴承",
    description="LM/LME cylindrical and LMF/LMK flanged linear-ball-bushing proxies.",
    factory=linear_bushing, derive=linear_bushing_dimensions,
    parameters=(ParameterSpec("style", "string", "Bushing style", choices=("LM", "LME", "LMF", "LMK")), ParameterSpec("bore", "string", "Nominal shaft diameter", choices=tuple(PROFILES))),
    aliases=("linear_bushing", "linear_bearing", "直线轴承"), orientation="shaft and travel +Z; flange at Z=0",
    detail="body/bore and optional flange mounting proxy", validation="finite sizes, bore, flange holes, interfaces and STEP/PNG review",
    example="instantiate('linear.bushing.ball.lmf20')", notes=("Suffixes for length, seals and accuracy are outside this planning family.",),
))
