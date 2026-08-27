"""Gearbox assembly proxies for common market interface families."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from build123d import Box, Compound

from .catalog import register
from .errors import InvalidParameterError
from .models import FamilyDefinition, ParameterSpec, StandardReference
from .proxy import CENTER_MIN, axial_cylinder, box_keepout, choice, compound, cut_z_holes, four_positions, real


@dataclass(frozen=True, slots=True)
class RightAngleProfile:
    length: float; width: float; height: float; axis_height: float; output_bore: float
    foot_x: float; foot_y: float; foot_hole: float; input_pilot: float; input_pcd: float


RIGHT_ANGLE = {
    ("NMRV", "025"): RightAngleProfile(90, 70, 72, 25, 11, 60, 45, 7, 50, 65),
    ("NMRV", "030"): RightAngleProfile(103, 80, 82, 30, 14, 70, 50, 7, 60, 75),
    ("NMRV", "040"): RightAngleProfile(130, 100, 103, 40, 18, 90, 65, 9, 80, 100),
    ("NMRV", "050"): RightAngleProfile(150, 120, 125, 50, 25, 105, 80, 9, 95, 115),
    ("NMRV", "063"): RightAngleProfile(180, 144, 148, 63, 25, 130, 95, 11, 110, 130),
    ("NMRV", "075"): RightAngleProfile(205, 172, 175, 75, 28, 150, 115, 13, 130, 165),
    ("NMRV", "090"): RightAngleProfile(238, 197, 205, 90, 35, 175, 130, 13, 130, 165),
    ("NMRV", "110"): RightAngleProfile(290, 238, 250, 110, 42, 215, 160, 17, 180, 215),
    ("NMRV", "130"): RightAngleProfile(335, 270, 285, 130, 45, 250, 180, 17, 230, 265),
    ("BKM", "050"): RightAngleProfile(165, 128, 132, 50, 25, 115, 85, 11, 95, 115),
    ("BKM", "063"): RightAngleProfile(195, 152, 158, 63, 30, 140, 100, 13, 110, 130),
    ("BKM", "075"): RightAngleProfile(225, 180, 185, 75, 35, 165, 120, 13, 130, 165),
    ("BKM", "090"): RightAngleProfile(265, 210, 215, 90, 40, 195, 140, 15, 130, 165),
    ("BKM", "110"): RightAngleProfile(315, 250, 260, 110, 50, 235, 170, 17, 180, 215),
    ("BKM", "130"): RightAngleProfile(365, 290, 300, 130, 60, 275, 200, 19, 230, 265),
}

MOTOVARIO_NMRV = StandardReference(
    system="manufacturer", designation="Motovario NMRV / NMRVpower",
    title="Worm gear reducers and combined units", edition="accessed 2026-08-27",
    status="current product family",
    url="https://www.motovario.com/eng/products/worm-gear-reducers--vsf-series/worm-gear-reducers-combined-and-with-pre-stage-reduction-unit",
    relationship="series-name-and-size-range",
    note="Library planning profiles are not Motovario manufacturing drawings.",
)


def right_angle_dimensions(series: str, size: str | int, *, output_bore: float | None = None) -> dict[str, Any]:
    family = choice("series", str(series).upper(), ("NMRV", "BKM"))
    code = str(size).strip().zfill(3)
    if (family, code) not in RIGHT_ANGLE:
        available = ", ".join(item for name, item in RIGHT_ANGLE if name == family)
        raise InvalidParameterError(f"unsupported {family} size {code!r}; available: {available}")
    p = RIGHT_ANGLE[(family, code)]
    bore = p.output_bore if output_bore is None else real("output_bore", output_bore, positive=True)
    if bore >= min(p.height, p.width) * 0.65:
        raise InvalidParameterError("output_bore is too large for the housing envelope")
    return {
        "gearbox_type": "right_angle_market_series", "series": family, "size": code,
        "body_length": p.length, "body_width": p.width, "body_height": p.height,
        "output_axis_height": p.axis_height, "output_bore": bore,
        "foot_hole_pitch_x": p.foot_x, "foot_hole_pitch_y": p.foot_y,
        "foot_hole_diameter": p.foot_hole, "input_pilot_diameter": p.input_pilot,
        "input_bolt_circle": p.input_pcd, "unit": "mm",
        "keepout_envelopes": [
            box_keepout("housing", (p.length, p.width, p.height), (0, 0, p.height / 2), "Conservative housing envelope."),
            {"id": "output_member_both_sides", "shape": "coaxial_cylinders", "purpose": "Output hub/coupling access on both sides.", "frame": {"origin_mm": [0, 0, p.axis_height], "axis": [1, 0, 0]}, "diameter_mm": max(2 * bore, 40), "length_each_side_mm": max(20, 1.5 * bore)},
            box_keepout("input_motor", (p.length * 0.75, max(60, p.input_pilot), max(60, p.input_pilot)), (0, -p.width / 2 - p.length * 0.375, p.height / 2), "Motor/adapter clearance; replace with chosen motor instance."),
        ],
    }


def right_angle_gearbox(series: str, size: str | int, *, output_bore: float | None = None) -> Compound:
    d = right_angle_dimensions(series, size, output_bore=output_bore)
    length, width, height = (float(d[key]) for key in ("body_length", "body_width", "body_height"))
    axis_height = float(d["output_axis_height"])
    body = Box(length, width, height, align=CENTER_MIN)
    body = cut_z_holes(body, four_positions(float(d["foot_hole_pitch_x"]), float(d["foot_hole_pitch_y"])), float(d["foot_hole_diameter"]), -1, min(16, height))
    body = body - axial_cylinder(float(d["output_bore"]), length + 4, origin=(-length / 2 - 2, 0, axis_height), axis="+X")
    input_flange = axial_cylinder(float(d["input_bolt_circle"]) + 18, 10, origin=(0, -width / 2 - 10, height / 2), axis="+Y")
    input_flange = input_flange - axial_cylinder(float(d["input_pilot_diameter"]), 12, origin=(0, -width / 2 - 11, height / 2), axis="+Y")
    hub_diameter = max(float(d["output_bore"]) + 20, 42)
    hub_min = axial_cylinder(hub_diameter, 10, origin=(-length / 2 - 10, 0, axis_height), axis="+X") - axial_cylinder(float(d["output_bore"]), 12, origin=(-length / 2 - 11, 0, axis_height), axis="+X")
    hub_max = axial_cylinder(hub_diameter, 10, origin=(length / 2, 0, axis_height), axis="+X") - axial_cylinder(float(d["output_bore"]), 12, origin=(length / 2 - 1, 0, axis_height), axis="+X")
    return compound(f"{d['series']} {d['size']} gearbox", body, input_flange, hub_min, hub_max)


@dataclass(frozen=True, slots=True)
class PlanetaryProfile:
    input_face: float; input_pitch: float; input_pilot: float; body_diameter: float; body_length: float
    output_flange: float; output_pilot: float; output_pitch: float; shaft: float; shaft_length: float


PLANETARY = {
    "42": PlanetaryProfile(42, 31, 22, 42, 65, 48, 35, 40, 12, 25),
    "60": PlanetaryProfile(60, 50, 50, 60, 85, 70, 55, 58, 16, 30),
    "80": PlanetaryProfile(80, 70, 70, 80, 110, 90, 70, 75, 22, 40),
    "90": PlanetaryProfile(90, 80, 80, 90, 120, 100, 80, 85, 22, 40),
    "110": PlanetaryProfile(110, 95, 95, 110, 150, 130, 100, 110, 32, 50),
    "130": PlanetaryProfile(130, 110, 110, 130, 175, 150, 120, 130, 35, 55),
}


def planetary_dimensions(motor_interface: str | int, *, ratio: float = 10) -> dict[str, Any]:
    code = choice("motor_interface", str(motor_interface), PLANETARY)
    reduction = real("ratio", ratio, positive=True)
    p = PLANETARY[code]
    return {
        "gearbox_type": "inline_planetary_planning_profile", "motor_interface": code, "ratio": reduction,
        "input_face": p.input_face, "input_hole_pitch": p.input_pitch, "input_pilot_diameter": p.input_pilot,
        "body_diameter": p.body_diameter, "body_length": p.body_length,
        "output_flange_diameter": p.output_flange, "output_pilot_diameter": p.output_pilot,
        "output_hole_pitch": p.output_pitch, "output_shaft_diameter": p.shaft,
        "output_shaft_length": p.shaft_length, "unit": "mm",
        "keepout_envelopes": [box_keepout("gearbox", (p.output_flange, p.output_flange, p.body_length + p.shaft_length), (0, 0, (p.body_length + p.shaft_length) / 2), "Gearbox, flange and shaft envelope.")],
    }


def inline_planetary(motor_interface: str | int, *, ratio: float = 10) -> Compound:
    d = planetary_dimensions(motor_interface, ratio=ratio)
    body = axial_cylinder(float(d["body_diameter"]), float(d["body_length"]), axis="+Z")
    input_face = Box(float(d["input_face"]), float(d["input_face"]), 8, align=CENTER_MIN)
    output = axial_cylinder(float(d["output_flange_diameter"]), 8, origin=(0, 0, float(d["body_length"]) - 8), axis="+Z")
    shaft = axial_cylinder(float(d["output_shaft_diameter"]), float(d["output_shaft_length"]), origin=(0, 0, float(d["body_length"])), axis="+Z")
    return compound(f"Planetary {d['motor_interface']} ratio {d['ratio']:g}", input_face, body, output, shaft)


register(FamilyDefinition(
    key="gearbox.right_angle.market", category="gearbox", title="Right-angle market gearbox / 市场型直角减速机",
    description="NMRV worm and BKM hypoid planning profiles with perpendicular input/output interfaces.",
    factory=right_angle_gearbox, derive=right_angle_dimensions,
    parameters=(ParameterSpec("series", "string", "Market series", choices=("NMRV", "BKM")), ParameterSpec("size", "string", "Series size code"), ParameterSpec("output_bore", "number|null", "Hollow-output bore override", "mm", required=False, default=None)),
    standards=(MOTOVARIO_NMRV,), aliases=("nmrv", "bkm", "worm_gearbox", "蜗轮蜗杆减速机", "准双曲面减速机"),
    orientation="feet on Z=0; hollow output +X; motor input +Y", detail="conservative market-series planning proxy",
    validation="finite table, bore continuity, foot holes, named axes and STEP/PNG review", example="instantiate('gearbox.right_angle.market.nmrv063')",
    notes=("Series names alone do not prove cross-vendor mounting interchangeability.",),
))

register(FamilyDefinition(
    key="gearbox.planetary.inline", category="gearbox", title="Inline planetary gearbox / 行星减速机",
    description="Common motor-interface planning profiles with coaxial input and output evidence.",
    factory=inline_planetary, derive=planetary_dimensions,
    parameters=(ParameterSpec("motor_interface", "string", "Nominal motor-interface class", choices=tuple(PLANETARY)), ParameterSpec("ratio", "number", "Reduction ratio for purchase direction", required=False, default=10, minimum=1)),
    aliases=("planetary_gearbox", "行星减速机"), orientation="input face Z=0; output +Z",
    detail="series planning proxy", validation="finite profiles, coaxial axes, bbox and STEP/PNG review",
    example="instantiate('gearbox.planetary.inline.80', ratio=10)", notes=("Compare every bolt/pilot field with the chosen catalog.",),
))
