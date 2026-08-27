"""Standard and de-facto-market pneumatic cylinder proxies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from build123d import Align, Box, Compound, Pos

from .catalog import register
from .errors import InvalidParameterError
from .models import FamilyDefinition, ParameterSpec, StandardReference
from .proxy import axial_cylinder, box_keepout, choice, compound, real


ISO_6432 = StandardReference(system="ISO", designation="ISO 6432:2015", title="Pneumatic fluid power — Single rod cylinders, 8 mm to 25 mm bores", edition="2015", status="current", url="https://www.iso.org/standard/66468.html", relationship="mounting-interface-basis")
ISO_15552 = StandardReference(system="ISO", designation="ISO 15552:2018", title="Pneumatic fluid power — Cylinders with detachable mountings, 32 mm to 320 mm bores", edition="2018", status="current", url="https://www.iso.org/standard/72672.html", relationship="mounting-interface-basis")
ISO_21287 = StandardReference(system="ISO", designation="ISO 21287:2004", title="Pneumatic fluid power — Compact cylinders, 20 mm to 100 mm bores", edition="2004", status="current", url="https://www.iso.org/standard/32705.html", relationship="compact-cylinder-interface-basis")


@dataclass(frozen=True, slots=True)
class CylinderProfile:
    body: float; rod: float; base_length: float; mount_pitch: float; mount_hole: float


ROUND = {
    "8": CylinderProfile(12, 4, 58, 16, 3.5), "10": CylinderProfile(12, 4, 58, 16, 3.5),
    "12": CylinderProfile(16, 6, 66, 20, 4.5), "16": CylinderProfile(19, 6, 75, 24, 4.5),
    "20": CylinderProfile(24, 8, 89, 28, 5.5), "25": CylinderProfile(30, 10, 102, 34, 5.5),
    "32": CylinderProfile(37, 12, 120, 42, 6.6),
}

PROFILE = {
    "32": CylinderProfile(45, 12, 142, 32, 6.6), "40": CylinderProfile(52, 16, 161, 38, 6.6),
    "50": CylinderProfile(64, 20, 179, 46.5, 9), "63": CylinderProfile(75, 20, 194, 56.5, 9),
    "80": CylinderProfile(95, 25, 214, 72, 11), "100": CylinderProfile(115, 25, 229, 89, 11),
    "125": CylinderProfile(140, 32, 275, 110, 14),
}

COMPACT = {
    "20": CylinderProfile(36, 10, 32, 28, 5.5), "25": CylinderProfile(40, 10, 35, 32, 5.5),
    "32": CylinderProfile(48, 12, 39, 38, 6.6), "40": CylinderProfile(56, 16, 44, 44, 6.6),
    "50": CylinderProfile(68, 20, 50, 54, 9), "63": CylinderProfile(82, 20, 57, 68, 9),
    "80": CylinderProfile(104, 25, 68, 86, 11), "100": CylinderProfile(128, 25, 78, 106, 11),
}


def _cylinder_dimensions(standard: str, table: dict[str, CylinderProfile], bore: str | int, stroke: float, *, rod_extension: float | None = None, series: str | None = None) -> dict[str, Any]:
    code = choice("bore", str(bore), table)
    travel = real("stroke", stroke, positive=True)
    p = table[code]
    extension = max(20, p.rod * 1.5) if rod_extension is None else real("rod_extension", rod_extension, positive=True)
    body_length = p.base_length + travel
    return {
        "cylinder_standard": standard, "market_series": series, "bore_diameter": float(code),
        "stroke": travel, "body_cross_section": p.body, "body_length": body_length,
        "rod_diameter": p.rod, "rod_extension_retracted": extension,
        "front_mount_pitch": p.mount_pitch, "front_mount_hole_diameter": p.mount_hole,
        "unit": "mm",
        "keepout_envelopes": [
            box_keepout("cylinder_body", (body_length, p.body, p.body), (body_length / 2, 0, 0), "Cylinder body and end-cap envelope."),
            {"id": "rod_sweep", "shape": "cylinder", "purpose": "Piston rod from retracted tip through full commanded stroke.", "frame": {"origin_mm": [body_length, 0, 0], "axis": [1, 0, 0]}, "diameter_mm": p.rod + 4, "length_mm": extension + travel},
        ],
    }


def iso6432_dimensions(bore: str | int, stroke: float, *, rod_extension: float | None = None) -> dict[str, Any]:
    return _cylinder_dimensions("ISO 6432", ROUND, bore, stroke, rod_extension=rod_extension)


def iso15552_dimensions(bore: str | int, stroke: float, *, rod_extension: float | None = None) -> dict[str, Any]:
    return _cylinder_dimensions("ISO 15552", PROFILE, bore, stroke, rod_extension=rod_extension)


def compact_cylinder_dimensions(series: str, bore: str | int, stroke: float, *, rod_extension: float | None = None) -> dict[str, Any]:
    family = choice("series", series.upper(), ("ISO21287", "SDA"))
    relationship = "ISO 21287" if family == "ISO21287" else "SDA market planning profile"
    return _cylinder_dimensions(relationship, COMPACT, bore, stroke, rod_extension=rod_extension, series=family)


def _cylinder_shape(d: dict[str, Any], *, round_body: bool) -> Compound:
    body_length, cross = float(d["body_length"]), float(d["body_cross_section"])
    if round_body:
        body = axial_cylinder(cross, body_length, axis="+X")
    else:
        body = Pos(body_length / 2, 0, -cross / 2) * Box(body_length, cross, cross, align=(Align.CENTER, Align.CENTER, Align.MIN))
    rod = axial_cylinder(float(d["rod_diameter"]), float(d["rod_extension_retracted"]), origin=(body_length, 0, 0), axis="+X")
    front = axial_cylinder(cross * 1.08, max(4, cross * 0.1), origin=(body_length - max(4, cross * 0.1), 0, 0), axis="+X")
    return compound(f"{d['cylinder_standard']} bore {d['bore_diameter']:g} stroke {d['stroke']:g}", body, front, rod)


def iso6432_cylinder(bore: str | int, stroke: float, *, rod_extension: float | None = None) -> Compound:
    return _cylinder_shape(iso6432_dimensions(bore, stroke, rod_extension=rod_extension), round_body=True)


def iso15552_cylinder(bore: str | int, stroke: float, *, rod_extension: float | None = None) -> Compound:
    return _cylinder_shape(iso15552_dimensions(bore, stroke, rod_extension=rod_extension), round_body=False)


def compact_cylinder(series: str, bore: str | int, stroke: float, *, rod_extension: float | None = None) -> Compound:
    return _cylinder_shape(compact_cylinder_dimensions(series, bore, stroke, rod_extension=rod_extension), round_body=False)


register(FamilyDefinition(key="pneumatic.cylinder.iso6432", category="pneumatic", title="ISO 6432 round cylinder / ISO 6432圆形气缸", description="Small-bore round pneumatic cylinder proxy with body, mount and rod sweep.", factory=iso6432_cylinder, derive=iso6432_dimensions, parameters=(ParameterSpec("bore", "string", "Nominal bore", choices=tuple(ROUND)), ParameterSpec("stroke", "number", "Cylinder stroke", "mm", minimum=0), ParameterSpec("rod_extension", "number|null", "Retracted rod extension", "mm", required=False, default=None)), standards=(ISO_6432,), aliases=("iso6432_cylinder", "迷你气缸"), orientation="rear at X=0; extension +X", detail="body, rod and complete rod sweep", validation="finite bores, stroke, interfaces and STEP/PNG review", example="instantiate('pneumatic.cylinder.iso6432.20', stroke=100)"))

register(FamilyDefinition(key="pneumatic.cylinder.iso15552", category="pneumatic", title="ISO 15552 profile cylinder / ISO 15552型材气缸", description="Profile pneumatic cylinder proxy for 32–125 mm bores.", factory=iso15552_cylinder, derive=iso15552_dimensions, parameters=(ParameterSpec("bore", "string", "Nominal bore", choices=tuple(PROFILE)), ParameterSpec("stroke", "number", "Cylinder stroke", "mm", minimum=0), ParameterSpec("rod_extension", "number|null", "Retracted rod extension", "mm", required=False, default=None)), standards=(ISO_15552,), aliases=("iso15552_cylinder", "标准气缸"), orientation="rear at X=0; extension +X", detail="body, mount, rod and complete rod sweep", validation="finite bores, stroke, interfaces and STEP/PNG review", example="instantiate('pneumatic.cylinder.iso15552.63', stroke=200)"))

register(FamilyDefinition(key="pneumatic.cylinder.compact", category="pneumatic", title="Compact pneumatic cylinder / 薄型气缸", description="ISO 21287 and SDA market planning proxies with compact body and rod sweep.", factory=compact_cylinder, derive=compact_cylinder_dimensions, parameters=(ParameterSpec("series", "string", "Interface family", choices=("ISO21287", "SDA")), ParameterSpec("bore", "string", "Nominal bore", choices=tuple(COMPACT)), ParameterSpec("stroke", "number", "Cylinder stroke", "mm", minimum=0), ParameterSpec("rod_extension", "number|null", "Retracted rod extension", "mm", required=False, default=None)), standards=(ISO_21287,), aliases=("compact_cylinder", "SDA气缸", "薄型气缸"), orientation="rear at X=0; extension +X", detail="compact body, rod and complete rod sweep", validation="finite profiles, stroke, interfaces and STEP/PNG review", example="instantiate('pneumatic.cylinder.compact.sda40', stroke=50)", notes=("SDA is a market family, not an ISO interchangeability claim.",)))
