"""Linear-motion proxies for rails, screws, supports and round shafts."""

from __future__ import annotations

from dataclasses import dataclass
from math import floor
from typing import Any

from build123d import Align, Box, Compound, Cylinder, Pos

from .catalog import register
from .errors import InvalidParameterError
from .models import FamilyDefinition, ParameterSpec, StandardReference
from .proxy import CENTER_MIN, axial_cylinder, box_keepout, choice, compound, real


X_MIN = (Align.MIN, Align.CENTER, Align.MIN)

HIWIN_GUIDEWAYS = StandardReference(
    system="manufacturer", designation="HIWIN Linear Guideways",
    title="Linear Guideways product families", edition="accessed 2026-08-27",
    status="current product families", url="https://hiwin.com/products/linear-guideways/",
    relationship="series-family-and-interface-reference",
    note="The library stores finite planning profiles; manufacturer drawings remain authoritative.",
)

HIWIN_SCREWS = StandardReference(
    system="manufacturer", designation="HIWIN Ballscrews and Supports",
    title="Ballscrews & Supports", edition="accessed 2026-08-27",
    status="current product families", url="https://hiwin.com/products/ballscrews-supports/",
    relationship="product-family-reference",
)


@dataclass(frozen=True, slots=True)
class GuideProfile:
    rail_width: float; rail_height: float; rail_pitch: float; rail_hole: float
    block_width: float; block_length: float; assembly_height: float; block_pitch_x: float; block_pitch_y: float


GUIDES = {
    ("MGN", "7"): GuideProfile(7, 4.8, 15, 2.5, 17, 30.8, 8, 16, 12),
    ("MGN", "9"): GuideProfile(9, 6.5, 20, 3.5, 20, 39.9, 10, 20, 15),
    ("MGN", "12"): GuideProfile(12, 8, 25, 3.5, 27, 45.4, 13, 25, 20),
    ("MGN", "15"): GuideProfile(15, 10, 40, 4.5, 32, 58.8, 16, 40, 25),
    ("MGW", "7"): GuideProfile(14, 5.2, 20, 3.5, 25, 31, 9, 15, 19),
    ("MGW", "9"): GuideProfile(18, 7, 20, 3.5, 30, 39.9, 12, 20, 23),
    ("MGW", "12"): GuideProfile(24, 8.5, 25, 4.5, 40, 45.4, 14, 25, 30),
    ("MGW", "15"): GuideProfile(42, 9.5, 40, 4.5, 60, 59.4, 16, 40, 45),
    ("HGR", "15"): GuideProfile(15, 15, 60, 7, 34, 61.4, 28, 26, 26),
    ("HGR", "20"): GuideProfile(20, 17.5, 60, 9.5, 44, 77.5, 30, 32, 32),
    ("HGR", "25"): GuideProfile(23, 22, 60, 11, 48, 84, 40, 35, 35),
    ("HGR", "30"): GuideProfile(28, 26, 80, 14, 60, 97.4, 45, 40, 40),
    ("HGR", "35"): GuideProfile(34, 29, 80, 14, 70, 112.4, 55, 50, 50),
    ("HGW", "15"): GuideProfile(15, 15, 60, 7, 47, 61.4, 28, 26, 38),
    ("HGW", "20"): GuideProfile(20, 17.5, 60, 9.5, 63, 77.5, 30, 32, 53),
    ("HGW", "25"): GuideProfile(23, 22, 60, 11, 70, 84, 40, 35, 57),
    ("HGW", "30"): GuideProfile(28, 26, 80, 14, 90, 97.4, 45, 40, 72),
    ("HGW", "35"): GuideProfile(34, 29, 80, 14, 100, 112.4, 55, 50, 82),
}


def linear_guide_dimensions(series: str, size: str | int, *, rail_length: float = 300, block_position: float | None = None) -> dict[str, Any]:
    family = choice("series", str(series).upper(), ("MGN", "MGW", "HGR", "HGW"))
    code = str(size)
    if (family, code) not in GUIDES:
        raise InvalidParameterError(f"unsupported linear-guide designation {family}{code}")
    p = GUIDES[(family, code)]
    length = real("rail_length", rail_length, positive=True)
    position = length / 2 if block_position is None else real("block_position", block_position, minimum=0)
    if position - p.block_length / 2 < 0 or position + p.block_length / 2 > length:
        raise InvalidParameterError("block_position must keep the complete carriage on the rail")
    hole_count = max(1, floor(length / p.rail_pitch))
    return {
        "guide_series": family, "size": code, "rail_length": length,
        "rail_width": p.rail_width, "rail_height": p.rail_height,
        "rail_mounting_pitch": p.rail_pitch, "rail_hole_diameter": p.rail_hole,
        "rail_hole_count": hole_count, "block_position": position,
        "block_width": p.block_width, "block_length": p.block_length,
        "assembly_height": p.assembly_height, "block_hole_pitch_x": p.block_pitch_x,
        "block_hole_pitch_y": p.block_pitch_y, "unit": "mm",
        "keepout_envelopes": [box_keepout(
            "carriage_sweep", (length, p.block_width, p.assembly_height),
            (length / 2, 0, p.assembly_height / 2), "Moving carriage sweep across usable rail length.",
        )],
    }


def linear_guide(series: str, size: str | int, *, rail_length: float = 300, block_position: float | None = None) -> Compound:
    d = linear_guide_dimensions(series, size, rail_length=rail_length, block_position=block_position)
    length = float(d["rail_length"])
    rail = Box(length, float(d["rail_width"]), float(d["rail_height"]), align=X_MIN)
    count, pitch = int(d["rail_hole_count"]), float(d["rail_mounting_pitch"])
    offset = (length - (count - 1) * pitch) / 2
    for index in range(count):
        rail = rail - Pos(offset + index * pitch, 0, -1) * Cylinder(float(d["rail_hole_diameter"]) / 2, float(d["rail_height"]) + 2, align=CENTER_MIN)
    block = Pos(float(d["block_position"]) - float(d["block_length"]) / 2, 0, float(d["rail_height"])) * Box(float(d["block_length"]), float(d["block_width"]), float(d["assembly_height"]) - float(d["rail_height"]), align=X_MIN)
    return compound(f"{d['guide_series']}{d['size']} L{length:g}", rail, block)


@dataclass(frozen=True, slots=True)
class ScrewProfile:
    diameter: float; lead: float; nut_od: float; nut_length: float; flange_od: float; flange_thickness: float; flange_pcd: float; flange_hole: float


SCREWS = {
    "SFU1204": ScrewProfile(12, 4, 24, 40, 42, 8, 32, 4.5),
    "SFU1605": ScrewProfile(16, 5, 28, 42, 48, 10, 38, 5.5),
    "SFU1610": ScrewProfile(16, 10, 28, 48, 48, 10, 38, 5.5),
    "SFU2005": ScrewProfile(20, 5, 36, 52, 58, 10, 47, 6.6),
    "SFU2010": ScrewProfile(20, 10, 36, 60, 58, 10, 47, 6.6),
    "SFU2505": ScrewProfile(25, 5, 40, 57, 62, 10, 51, 6.6),
    "SFU3205": ScrewProfile(32, 5, 50, 68, 80, 12, 65, 9),
}


def ball_screw_dimensions(code: str, *, length: float = 500, nut_position: float | None = None) -> dict[str, Any]:
    designation = choice("code", code.upper(), SCREWS)
    p = SCREWS[designation]
    total = real("length", length, positive=True)
    position = total / 2 if nut_position is None else real("nut_position", nut_position, minimum=0)
    if position - p.nut_length / 2 < 0 or position + p.nut_length / 2 > total:
        raise InvalidParameterError("nut_position must keep the complete nut on the screw")
    return {
        "designation": designation, "screw_diameter": p.diameter, "lead": p.lead,
        "screw_length": total, "nut_position": position, "nut_outer_diameter": p.nut_od,
        "nut_length": p.nut_length, "nut_flange_diameter": p.flange_od,
        "nut_flange_thickness": p.flange_thickness, "nut_flange_pitch_circle": p.flange_pcd,
        "nut_flange_hole_diameter": p.flange_hole, "unit": "mm",
        "keepout_envelopes": [box_keepout(
            "nut_sweep", (total, p.flange_od, p.flange_od), (total / 2, 0, 0),
            "Ball-nut flange sweep along the screw axis.",
        )],
    }


def ball_screw(code: str, *, length: float = 500, nut_position: float | None = None) -> Compound:
    d = ball_screw_dimensions(code, length=length, nut_position=nut_position)
    screw = axial_cylinder(float(d["screw_diameter"]), float(d["screw_length"]), axis="+X")
    position, nut_length = float(d["nut_position"]), float(d["nut_length"])
    nut = axial_cylinder(float(d["nut_outer_diameter"]), nut_length, origin=(position - nut_length / 2, 0, 0), axis="+X") - axial_cylinder(float(d["screw_diameter"]), nut_length + 2, origin=(position - nut_length / 2 - 1, 0, 0), axis="+X")
    flange = axial_cylinder(float(d["nut_flange_diameter"]), float(d["nut_flange_thickness"]), origin=(position - nut_length / 2, 0, 0), axis="+X") - axial_cylinder(float(d["screw_diameter"]), float(d["nut_flange_thickness"]) + 2, origin=(position - nut_length / 2 - 1, 0, 0), axis="+X")
    return compound(str(d["designation"]), screw, nut, flange)


@dataclass(frozen=True, slots=True)
class SupportProfile:
    bore: float; width: float; height: float; length: float; axis_height: float; pitch_x: float; pitch_y: float; hole: float


SUPPORT_SIZES = {
    "10": SupportProfile(10, 60, 39, 25, 22, 46, 24, 6.6), "12": SupportProfile(12, 60, 43, 25, 25, 46, 24, 6.6),
    "15": SupportProfile(15, 70, 48, 27, 28, 54, 30, 7), "17": SupportProfile(17, 86, 64, 35, 39, 68, 42, 9),
    "20": SupportProfile(20, 88, 60, 34, 34, 70, 40, 9), "25": SupportProfile(25, 105, 80, 41, 48, 85, 54, 11),
    "30": SupportProfile(30, 120, 89, 48, 53, 98, 62, 14), "35": SupportProfile(35, 140, 96, 54, 58, 116, 66, 14),
    "40": SupportProfile(40, 160, 110, 60, 65, 132, 78, 18),
}


def screw_support_dimensions(unit_type: str, size: str | int) -> dict[str, Any]:
    kind = choice("unit_type", unit_type.upper(), ("BK", "BF", "EK", "EF", "FK", "FF"))
    code = choice("size", str(size), SUPPORT_SIZES)
    p = SUPPORT_SIZES[code]
    fixed = kind in {"BK", "EK", "FK"}
    return {
        "support_type": kind, "size": code, "support_role": "fixed" if fixed else "floating",
        "shaft_bore": p.bore, "body_width": p.width, "body_height": p.height,
        "body_length": p.length, "shaft_axis_height": p.axis_height,
        "mount_hole_pitch_y": p.pitch_x, "mount_hole_pitch_z": p.pitch_y,
        "mount_hole_diameter": p.hole, "unit": "mm",
        "keepout_envelopes": [box_keepout("support_and_locknut_access", (p.length + 25, p.width, p.height), (0, 0, p.height / 2), "Support unit and shaft locknut access.")],
    }


def screw_support(unit_type: str, size: str | int) -> Compound:
    d = screw_support_dimensions(unit_type, size)
    width, height, length, axis_height = (float(d[key]) for key in ("body_width", "body_height", "body_length", "shaft_axis_height"))
    body = Box(length, width, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    body = body - axial_cylinder(float(d["shaft_bore"]), length + 2, origin=(-length / 2 - 1, 0, axis_height), axis="+X")
    pitch_y, pitch_z = float(d["mount_hole_pitch_y"]), float(d["mount_hole_pitch_z"])
    for y in (-pitch_y / 2, pitch_y / 2):
        for z in (height / 2 - pitch_z / 2, height / 2 + pitch_z / 2):
            body = body - axial_cylinder(
                float(d["mount_hole_diameter"]),
                length + 2,
                origin=(-length / 2 - 1, y, z),
                axis="+X",
            )
    body.label = f"{d['support_type']}{d['size']}"
    return compound(body.label, body)


@dataclass(frozen=True, slots=True)
class RoundGuideProfile:
    shaft_support_width: float; shaft_axis_height: float; block_width: float; block_length: float; block_height: float


ROUND_GUIDES = {
    "12": RoundGuideProfile(40, 22, 40, 39, 27), "16": RoundGuideProfile(45, 27, 45, 45, 33),
    "20": RoundGuideProfile(50, 31, 50, 50, 39), "25": RoundGuideProfile(60, 37, 60, 60, 47),
    "30": RoundGuideProfile(70, 44, 70, 70, 56), "35": RoundGuideProfile(80, 50, 80, 80, 64),
    "40": RoundGuideProfile(90, 56, 90, 90, 72),
}


def supported_round_guide_dimensions(series: str, diameter: str | int, *, length: float = 500, block_position: float | None = None) -> dict[str, Any]:
    family = choice("series", series.upper(), ("SBR", "TBR"))
    code = choice("diameter", str(diameter), ROUND_GUIDES)
    p = ROUND_GUIDES[code]
    total = real("length", length, positive=True)
    position = total / 2 if block_position is None else real("block_position", block_position, minimum=0)
    if position - p.block_length / 2 < 0 or position + p.block_length / 2 > total:
        raise InvalidParameterError("block_position must keep the complete block on the shaft")
    return {
        "guide_series": family, "shaft_diameter": float(code), "length": total,
        "shaft_axis_height": p.shaft_axis_height, "support_width": p.shaft_support_width,
        "block_position": position, "block_width": p.block_width,
        "block_length": p.block_length, "block_height": p.block_height, "unit": "mm",
        "keepout_envelopes": [box_keepout("block_sweep", (total, p.block_width, p.block_height), (total / 2, 0, p.block_height / 2), "Bearing-block sweep along supported shaft.")],
    }


def supported_round_guide(series: str, diameter: str | int, *, length: float = 500, block_position: float | None = None) -> Compound:
    d = supported_round_guide_dimensions(series, diameter, length=length, block_position=block_position)
    total, axis_height = float(d["length"]), float(d["shaft_axis_height"])
    support = Box(total, float(d["support_width"]), axis_height * 0.45, align=X_MIN)
    shaft = axial_cylinder(float(d["shaft_diameter"]), total, origin=(0, 0, axis_height), axis="+X")
    block = Pos(float(d["block_position"]) - float(d["block_length"]) / 2, 0, 0) * Box(float(d["block_length"]), float(d["block_width"]), float(d["block_height"]), align=X_MIN)
    block = block - axial_cylinder(float(d["shaft_diameter"]), float(d["block_length"]) + 2, origin=(float(d["block_position"]) - float(d["block_length"]) / 2 - 1, 0, axis_height), axis="+X")
    return compound(f"{d['guide_series']}{int(d['shaft_diameter'])} L{total:g}", support, shaft, block)


register(FamilyDefinition(key="linear.guide.rail", category="linear", title="Profile linear guide / 直线导轨", description="MGN/MGW miniature and HGR/HGW profile-rail planning proxies.", factory=linear_guide, derive=linear_guide_dimensions, parameters=(ParameterSpec("series", "string", "Guide family", choices=("MGN", "MGW", "HGR", "HGW")), ParameterSpec("size", "string", "Nominal size"), ParameterSpec("rail_length", "number", "Rail length", "mm", required=False, default=300), ParameterSpec("block_position", "number|null", "Carriage center from rail start", "mm", required=False, default=None)), standards=(HIWIN_GUIDEWAYS,), aliases=("linear_guide", "直线导轨"), orientation="motion +X; rail base Z=0", detail="rail, mounting holes, carriage and sweep", validation="finite profiles, positions, interfaces and STEP/PNG review", example="instantiate('linear.guide.rail.mgn12', rail_length=400)"))

register(FamilyDefinition(key="linear.ball_screw", category="linear", title="SFU ball screw / SFU滚珠丝杆", description="Common SFU screw/nut envelopes with lead, nut flange and moving sweep.", factory=ball_screw, derive=ball_screw_dimensions, parameters=(ParameterSpec("code", "string", "Finite SFU designation", choices=tuple(SCREWS)), ParameterSpec("length", "number", "Screw length", "mm", required=False, default=500), ParameterSpec("nut_position", "number|null", "Nut center from fixed end", "mm", required=False, default=None)), standards=(HIWIN_SCREWS,), aliases=("ball_screw", "滚珠丝杆", "滚珠丝杠"), orientation="screw and travel +X", detail="shaft/nut/flange planning proxy", validation="finite table, nut bounds, interfaces and STEP/PNG review", example="instantiate('linear.ball_screw.sfu1605', length=800)"))

register(FamilyDefinition(key="linear.screw_support", category="linear", title="Ball-screw support unit / 丝杆支撑座", description="BK/BF, EK/EF and FK/FF fixed/floating support proxies.", factory=screw_support, derive=screw_support_dimensions, parameters=(ParameterSpec("unit_type", "string", "Support family", choices=("BK", "BF", "EK", "EF", "FK", "FF")), ParameterSpec("size", "string", "Nominal shaft-end size", choices=tuple(SUPPORT_SIZES))), aliases=("screw_support", "丝杆支撑座"), orientation="shaft +X; base Z=0", detail="support envelope, bore and mounting pattern", validation="finite profiles, interfaces and STEP/PNG review", example="instantiate('linear.screw_support.bk20')"))

register(FamilyDefinition(key="linear.guide.supported_round", category="linear", title="Supported round-shaft guide / 支撑圆导轨", description="SBR/TBR supported shaft and carriage planning proxies.", factory=supported_round_guide, derive=supported_round_guide_dimensions, parameters=(ParameterSpec("series", "string", "Support family", choices=("SBR", "TBR")), ParameterSpec("diameter", "string", "Shaft diameter", choices=tuple(ROUND_GUIDES)), ParameterSpec("length", "number", "Rail length", "mm", required=False, default=500), ParameterSpec("block_position", "number|null", "Block center", "mm", required=False, default=None)), aliases=("supported_round_guide", "SBR", "TBR", "支撑光轴"), orientation="motion +X; base Z=0", detail="supported shaft, block and sweep", validation="finite profiles, positions, interfaces and STEP/PNG review", example="instantiate('linear.guide.supported_round.sbr20', length=800)"))
