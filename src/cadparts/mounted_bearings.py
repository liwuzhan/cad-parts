"""UCP, UCF and UCFL mounted-bearing assembly proxies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from build123d import Box, Compound, Cylinder, Pos

from .catalog import register
from .errors import InvalidParameterError
from .models import FamilyDefinition, ParameterSpec
from .proxy import CENTER_MIN, axial_cylinder, box_keepout, choice, compound


@dataclass(frozen=True, slots=True)
class Profile:
    bore: float; overall_x: float; overall_z: float; thickness: float; axis_height: float
    pitch_x: float; pitch_z: float; hole: float


BORES = dict(zip((str(value) for value in range(201, 219)), (12, 15, 17, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90), strict=True))

UCP = {
    "201": (127, 62, 38, 30.2, 95, 0, 13), "202": (127, 62, 38, 30.2, 95, 0, 13), "203": (127, 62, 38, 30.2, 95, 0, 13), "204": (127, 62, 38, 30.2, 95, 0, 13),
    "205": (140, 71, 38, 36.5, 105, 0, 13), "206": (165, 83, 48, 42.9, 121, 0, 17), "207": (167, 93, 48, 47.6, 127, 0, 17), "208": (184, 101, 54, 49.2, 137, 0, 17),
    "209": (190, 106, 54, 54, 146, 0, 17), "210": (206, 114, 60, 57.2, 159, 0, 20), "211": (219, 126, 60, 63.5, 171, 0, 20), "212": (241, 138, 70, 69.8, 184, 0, 20),
    "213": (265, 150, 70, 76.2, 203, 0, 25), "214": (266, 157, 72, 79.4, 210, 0, 25), "215": (275, 162, 78, 82.6, 217, 0, 25), "216": (292, 175, 83, 88.9, 232, 0, 25),
    "217": (310, 187, 87, 95.2, 247, 0, 25), "218": (327, 200, 96, 101.6, 262, 0, 27),
}

UCF = {
    "201": (86, 86, 25.5, 43, 64, 64, 12), "202": (86, 86, 25.5, 43, 64, 64, 12), "203": (86, 86, 25.5, 43, 64, 64, 12), "204": (86, 86, 25.5, 43, 64, 64, 12),
    "205": (95, 95, 27, 47.5, 70, 70, 12), "206": (108, 108, 31, 54, 83, 83, 14), "207": (117, 117, 34, 58.5, 92, 92, 14), "208": (130, 130, 36, 65, 102, 102, 16),
    "209": (137, 137, 38, 68.5, 105, 105, 16), "210": (143, 143, 40, 71.5, 111, 111, 16), "211": (162, 162, 43, 81, 130, 130, 19), "212": (175, 175, 48, 87.5, 143, 143, 19),
    "213": (187, 187, 50, 93.5, 149, 149, 19), "214": (193, 193, 54, 96.5, 152, 152, 19), "215": (200, 200, 56, 100, 159, 159, 19), "216": (208, 208, 58, 104, 165, 165, 23),
    "217": (220, 220, 63, 110, 175, 175, 23), "218": (235, 235, 68, 117.5, 187, 187, 23),
}

UCFL = {
    "201": (113, 60, 25.5, 30, 90, 0, 12), "202": (113, 60, 25.5, 30, 90, 0, 12), "203": (113, 60, 25.5, 30, 90, 0, 12), "204": (113, 60, 25.5, 30, 90, 0, 12),
    "205": (130, 68, 27, 34, 99, 0, 16), "206": (148, 80, 31, 40, 117, 0, 16), "207": (161, 90, 34, 45, 130, 0, 16), "208": (175, 100, 36, 50, 144, 0, 16),
    "209": (188, 108, 38, 54, 148, 0, 19), "210": (197, 115, 40, 57.5, 157, 0, 19), "211": (224, 130, 43, 65, 184, 0, 19), "212": (250, 140, 48, 70, 202, 0, 23),
    "213": (258, 155, 50, 77.5, 210, 0, 23), "214": (265, 160, 54, 80, 216, 0, 23), "215": (275, 165, 56, 82.5, 225, 0, 23), "216": (290, 180, 58, 90, 233, 0, 25),
    "217": (305, 190, 63, 95, 248, 0, 25), "218": (320, 205, 68, 102.5, 262, 0, 27),
}

PROFILES = {
    (unit_type, code): Profile(float(BORES[code]), *values)
    for unit_type, table in (("UCP", UCP), ("UCF", UCF), ("UCFL", UCFL))
    for code, values in table.items()
}


def mounted_bearing_dimensions(unit_type: str, code: str | int) -> dict[str, Any]:
    kind = choice("unit_type", str(unit_type).upper(), ("UCP", "UCF", "UCFL"))
    number = str(code).strip()
    if (kind, number) not in PROFILES:
        raise InvalidParameterError(f"unsupported mounted-bearing designation {kind}{number}")
    p = PROFILES[(kind, number)]
    return {
        "bearing_unit_type": kind, "insert_code": number, "designation": f"{kind}{number}",
        "bore_diameter": p.bore, "overall_x": p.overall_x, "overall_z": p.overall_z,
        "axial_thickness": p.thickness, "shaft_axis_height": p.axis_height,
        "mount_hole_pitch_x": p.pitch_x, "mount_hole_pitch_z": p.pitch_z,
        "mount_hole_diameter": p.hole, "unit": "mm",
        "keepout_envelopes": [box_keepout(
            "housing_and_grease_access", (p.overall_x, p.thickness + 20, p.overall_z + 15),
            (0, 0, (p.overall_z + 15) / 2), "Housing, insert projection and grease-access clearance.",
        )],
    }


def mounted_bearing(unit_type: str, code: str | int) -> Compound:
    d = mounted_bearing_dimensions(unit_type, code)
    kind, width, height, thickness, axis_height = str(d["bearing_unit_type"]), float(d["overall_x"]), float(d["overall_z"]), float(d["axial_thickness"]), float(d["shaft_axis_height"])
    if kind == "UCP":
        base_height = max(10, height * 0.2)
        base = Box(width, thickness, base_height, align=CENTER_MIN)
        for x in (-float(d["mount_hole_pitch_x"]) / 2, float(d["mount_hole_pitch_x"]) / 2):
            base = base - Pos(x, 0, -1) * Cylinder(float(d["mount_hole_diameter"]) / 2, base_height + 2, align=CENTER_MIN)
        body = base + Pos(0, 0, base_height) * Box(width * 0.46, thickness, height - base_height, align=CENTER_MIN)
    elif kind == "UCF":
        body = Box(width, thickness, height, align=CENTER_MIN)
        for x in (-float(d["mount_hole_pitch_x"]) / 2, float(d["mount_hole_pitch_x"]) / 2):
            for z in (axis_height - float(d["mount_hole_pitch_z"]) / 2, axis_height + float(d["mount_hole_pitch_z"]) / 2):
                body = body - axial_cylinder(float(d["mount_hole_diameter"]), thickness + 2, origin=(x, -thickness / 2 - 1, z), axis="+Y")
    else:
        body = Box(width, thickness, height, align=CENTER_MIN)
        for x in (-float(d["mount_hole_pitch_x"]) / 2, float(d["mount_hole_pitch_x"]) / 2):
            body = body - axial_cylinder(float(d["mount_hole_diameter"]), thickness + 2, origin=(x, -thickness / 2 - 1, axis_height), axis="+Y")
    body = body - axial_cylinder(float(d["bore_diameter"]), thickness + 4, origin=(0, -thickness / 2 - 2, axis_height), axis="+Y")
    insert_diameter = max(float(d["bore_diameter"]) + 18, height * 0.45)
    insert = axial_cylinder(insert_diameter, thickness + 8, origin=(0, -thickness / 2 - 4, axis_height), axis="+Y") - axial_cylinder(float(d["bore_diameter"]), thickness + 10, origin=(0, -thickness / 2 - 5, axis_height), axis="+Y")
    return compound(str(d["designation"]), body, insert)


register(FamilyDefinition(
    key="bearing.unit.mounted", category="bearing", title="Mounted bearing unit / 带座轴承",
    description="UCP, UCF and UCFL housing proxies with named shaft and mounting interfaces.",
    factory=mounted_bearing, derive=mounted_bearing_dimensions,
    parameters=(ParameterSpec("unit_type", "string", "Housing form", choices=("UCP", "UCF", "UCFL")), ParameterSpec("code", "string", "Insert code 201–218", choices=tuple(str(value) for value in range(201, 219)))),
    aliases=("mounted_bearing", "pillow_block", "带座轴承"), orientation="shaft +Y; base/flange datum Z=0",
    detail="catalog planning envelope with bore and mounting coordinates", validation="54 finite profiles, bore, holes, interfaces and STEP/PNG review",
    example="instantiate('bearing.unit.mounted.ucp206')", notes=("Verify manufacturer outline before releasing the surrounding enclosure.",),
))
