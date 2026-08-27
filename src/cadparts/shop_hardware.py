"""Leveling-foot and caster assembly proxies for machine frames."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from build123d import Align, Box, Compound, Pos

from .catalog import register
from .errors import InvalidParameterError
from .models import FamilyDefinition, ParameterSpec
from .proxy import axial_cylinder, choice, compound, cylinder_keepout, real


@dataclass(frozen=True, slots=True)
class FootProfile:
    stem: float; foot: float; foot_height: float; default_stem: float


FEET = {
    "M8": FootProfile(8, 30, 8, 40), "M10": FootProfile(10, 40, 10, 50),
    "M12": FootProfile(12, 50, 12, 60), "M16": FootProfile(16, 60, 14, 80),
    "M20": FootProfile(20, 80, 18, 100), "M24": FootProfile(24, 100, 20, 120),
    "M30": FootProfile(30, 120, 24, 150),
}


def leveling_foot_dimensions(thread: str, *, stem_length: float | None = None) -> dict[str, Any]:
    code = choice("thread", thread.upper(), FEET)
    p = FEET[code]
    length = p.default_stem if stem_length is None else real("stem_length", stem_length, positive=True)
    return {
        "hardware_type": "leveling_foot", "thread": code, "stem_diameter": p.stem,
        "stem_length": length, "foot_diameter": p.foot, "foot_height": p.foot_height, "unit": "mm",
        "keepout_envelopes": [cylinder_keepout("adjustment_and_spanner_access", p.foot + 20, p.foot_height + length, (0, 0, 0), (0, 0, 1), "Foot, vertical adjustment and spanner access.")],
    }


def leveling_foot(thread: str, *, stem_length: float | None = None) -> Compound:
    d = leveling_foot_dimensions(thread, stem_length=stem_length)
    foot = axial_cylinder(float(d["foot_diameter"]), float(d["foot_height"]))
    stem = axial_cylinder(float(d["stem_diameter"]), float(d["stem_length"]), origin=(0, 0, float(d["foot_height"])))
    return compound(f"Leveling foot {d['thread']}", foot, stem)


@dataclass(frozen=True, slots=True)
class CasterProfile:
    wheel: float; width: float; overall_height: float; plate_x: float; plate_y: float; pitch_x: float; pitch_y: float; hole: float; stem: float


CASTERS = {
    "50": CasterProfile(50, 20, 70, 60, 45, 45, 30, 6.6, 10),
    "75": CasterProfile(75, 25, 100, 80, 60, 60, 40, 9, 12),
    "100": CasterProfile(100, 32, 130, 100, 80, 75, 55, 11, 16),
    "125": CasterProfile(125, 40, 160, 110, 85, 85, 60, 11, 16),
    "150": CasterProfile(150, 45, 190, 120, 90, 90, 65, 14, 20),
    "200": CasterProfile(200, 50, 245, 140, 110, 105, 80, 14, 24),
}


def caster_dimensions(size: str | int, *, mount: str = "plate", swivel: bool = True, brake: bool = False) -> dict[str, Any]:
    code = choice("size", str(size), CASTERS)
    mounting = choice("mount", mount.lower(), ("plate", "stem"))
    p = CASTERS[code]
    sweep = max(p.plate_x, p.wheel * 1.35) if swivel else p.wheel
    return {
        "hardware_type": "caster", "size": code, "mount": mounting, "swivel": bool(swivel), "brake": bool(brake),
        "wheel_diameter": p.wheel, "wheel_width": p.width, "overall_height": p.overall_height,
        "plate_size_x": p.plate_x, "plate_size_y": p.plate_y,
        "mount_hole_pitch_x": p.pitch_x, "mount_hole_pitch_y": p.pitch_y,
        "mount_hole_diameter": p.hole, "stem_diameter": p.stem, "unit": "mm",
        "keepout_envelopes": [cylinder_keepout("wheel_or_swivel_sweep", sweep, p.overall_height, (0, 0, 0), (0, 0, 1), "Wheel envelope or full swivel sweep below the mounting interface.")],
    }


def caster(size: str | int, *, mount: str = "plate", swivel: bool = True, brake: bool = False) -> Compound:
    d = caster_dimensions(size, mount=mount, swivel=swivel, brake=brake)
    radius = float(d["wheel_diameter"]) / 2
    wheel = axial_cylinder(float(d["wheel_diameter"]), float(d["wheel_width"]), origin=(0, -float(d["wheel_width"]) / 2, radius), axis="+Y")
    fork = Pos(0, 0, radius) * Box(float(d["wheel_diameter"]) * 0.55, float(d["wheel_width"]) + 12, float(d["overall_height"]) - radius, align=(Align.CENTER, Align.CENTER, Align.MIN))
    children = [wheel, fork]
    if d["mount"] == "plate":
        plate = Pos(0, 0, float(d["overall_height"]) - 8) * Box(float(d["plate_size_x"]), float(d["plate_size_y"]), 8, align=(Align.CENTER, Align.CENTER, Align.MIN))
        for x in (-float(d["mount_hole_pitch_x"]) / 2, float(d["mount_hole_pitch_x"]) / 2):
            for y in (-float(d["mount_hole_pitch_y"]) / 2, float(d["mount_hole_pitch_y"]) / 2):
                plate = plate - axial_cylinder(
                    float(d["mount_hole_diameter"]),
                    10,
                    origin=(x, y, float(d["overall_height"]) - 9),
                )
        children.append(plate)
    else:
        stem = axial_cylinder(float(d["stem_diameter"]), float(d["stem_diameter"]) * 3, origin=(0, 0, float(d["overall_height"])))
        children.append(stem)
    return compound(f"Caster {d['size']} {d['mount']}", *children)


register(FamilyDefinition(key="hardware.leveling_foot", category="hardware", title="Machine leveling foot / 设备调平脚", description="Common metric threaded leveling-foot envelope with adjustment access.", factory=leveling_foot, derive=leveling_foot_dimensions, parameters=(ParameterSpec("thread", "string", "Metric stem", choices=tuple(FEET)), ParameterSpec("stem_length", "number|null", "Threaded stem length", "mm", required=False, default=None)), aliases=("leveling_foot", "adjustable_foot", "调平脚", "地脚"), orientation="floor contact Z=0; stem +Z", detail="foot pad, threaded stem and adjustment keepout", validation="finite profiles, interfaces and STEP/PNG review", example="instantiate('hardware.leveling_foot.m16')"))

register(FamilyDefinition(key="hardware.caster", category="hardware", title="Industrial caster / 工业脚轮", description="Plate/stem, rigid/swivel industrial-caster planning proxy.", factory=caster, derive=caster_dimensions, parameters=(ParameterSpec("size", "string", "Wheel diameter class", choices=tuple(CASTERS)), ParameterSpec("mount", "string", "Machine attachment", required=False, default="plate", choices=("plate", "stem")), ParameterSpec("swivel", "boolean", "Swivel fork", required=False, default=True), ParameterSpec("brake", "boolean", "Brake selection evidence", required=False, default=False)), aliases=("caster", "industrial_caster", "脚轮", "万向轮"), orientation="floor contact Z=0; machine mount at +Z", detail="wheel/fork/mount envelope and swivel sweep", validation="finite profiles, interfaces and STEP/PNG review", example="instantiate('hardware.caster.100-plate')"))
