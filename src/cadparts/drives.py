"""Timing-belt, roller-chain and taper-lock transmission proxies."""

from __future__ import annotations

from dataclasses import dataclass
from math import pi, sin
from typing import Any

from build123d import Compound

from .catalog import register
from .errors import InvalidParameterError
from .models import FamilyDefinition, ParameterSpec, StandardReference
from .proxy import axial_cylinder, choice, compound, cylinder_keepout, integer, real


ISO_606 = StandardReference(
    system="ISO", designation="ISO 606:2015",
    title="Short-pitch transmission precision roller and bush chains",
    edition="2015", status="current", url="https://www.iso.org/standard/61232.html",
    relationship="chain-pitch-and-roller-dimension-basis",
    note="The sprocket proxy preserves pitch layout, not production tooth form.",
)


TIMING_PROFILES = {"GT2": (2.0, 0.75), "HTD3M": (3.0, 1.2), "HTD5M": (5.0, 2.1), "HTD8M": (8.0, 3.4)}


def timing_pulley_dimensions(profile: str, teeth: int, bore: float, belt_width: float, *, flange: bool = True) -> dict[str, Any]:
    family = choice("profile", profile.upper(), TIMING_PROFILES)
    count = integer("teeth", teeth, minimum=10)
    shaft_bore = real("bore", bore, minimum=0)
    width = real("belt_width", belt_width, positive=True)
    pitch, tooth_depth = TIMING_PROFILES[family]
    pitch_diameter = pitch * count / pi
    outside = pitch_diameter - 2 * tooth_depth * 0.35
    if shaft_bore >= outside * 0.72:
        raise InvalidParameterError("bore is too large for the pulley envelope")
    flange_diameter = outside + max(4, pitch) if flange else outside
    total_width = width + (2.0 if flange else 0.0)
    return {
        "drive_type": "timing_pulley", "profile": family, "pitch": pitch, "teeth": count,
        "pitch_diameter": pitch_diameter, "outside_diameter": outside,
        "bore_diameter": shaft_bore, "belt_width": width, "flanged": flange,
        "flange_diameter": flange_diameter, "overall_width": total_width, "unit": "mm",
        "keepout_envelopes": [cylinder_keepout("rotating_pulley_and_belt", flange_diameter + 4, total_width, (0, 0, 0), (0, 0, 1), "Pulley flanges and nearby moving belt clearance.")],
    }


def timing_pulley(profile: str, teeth: int, bore: float, belt_width: float, *, flange: bool = True) -> Compound:
    d = timing_pulley_dimensions(profile, teeth, bore, belt_width, flange=flange)
    core = axial_cylinder(float(d["outside_diameter"]), float(d["belt_width"]), origin=(0, 0, 1 if d["flanged"] else 0))
    core = core - axial_cylinder(float(d["bore_diameter"]), float(d["overall_width"]) + 2, origin=(0, 0, -1)) if float(d["bore_diameter"]) > 0 else core
    children = [core]
    if d["flanged"]:
        for z in (0, float(d["belt_width"]) + 1):
            flange_shape = axial_cylinder(float(d["flange_diameter"]), 1, origin=(0, 0, z))
            if float(d["bore_diameter"]) > 0:
                flange_shape = flange_shape - axial_cylinder(float(d["bore_diameter"]), 3, origin=(0, 0, z - 1))
            children.append(flange_shape)
    return compound(f"{d['profile']} {d['teeth']}T pulley", *children)


CHAIN_PROFILES = {"06B": (9.525, 6.35), "08B": (12.7, 8.51), "10B": (15.875, 10.16), "12B": (19.05, 12.07)}


def chain_sprocket_dimensions(series: str, teeth: int, bore: float, width: float | None = None) -> dict[str, Any]:
    family = choice("series", series.upper(), CHAIN_PROFILES)
    count = integer("teeth", teeth, minimum=9)
    shaft_bore = real("bore", bore, minimum=0)
    pitch, roller = CHAIN_PROFILES[family]
    face = roller * 0.9 if width is None else real("width", width, positive=True)
    pitch_diameter = pitch / sin(pi / count)
    outside = pitch_diameter + roller
    if shaft_bore >= pitch_diameter * 0.72:
        raise InvalidParameterError("bore is too large for the sprocket pitch envelope")
    return {
        "drive_type": "roller_chain_sprocket", "series": family, "pitch": pitch,
        "roller_diameter": roller, "teeth": count, "pitch_diameter": pitch_diameter,
        "outside_diameter": outside, "bore_diameter": shaft_bore, "face_width": face, "unit": "mm",
        "keepout_envelopes": [cylinder_keepout("rotating_sprocket_and_chain", outside + roller, face + 2 * roller, (0, 0, -roller), (0, 0, 1), "Sprocket and nearby moving chain clearance.")],
    }


def chain_sprocket(series: str, teeth: int, bore: float, width: float | None = None) -> Compound:
    d = chain_sprocket_dimensions(series, teeth, bore, width)
    body = axial_cylinder(float(d["outside_diameter"]), float(d["face_width"]))
    if float(d["bore_diameter"]) > 0:
        body = body - axial_cylinder(float(d["bore_diameter"]), float(d["face_width"]) + 2, origin=(0, 0, -1))
    return compound(f"{d['series']} {d['teeth']}T sprocket", body)


@dataclass(frozen=True, slots=True)
class TaperProfile:
    outside: float; length: float; max_bore: float


TAPER_LOCK = {
    "1008": TaperProfile(35, 22.3, 25), "1210": TaperProfile(47.5, 25.4, 32),
    "1610": TaperProfile(57, 25.4, 42), "2012": TaperProfile(70, 31.8, 50),
    "2517": TaperProfile(85.5, 44.5, 65), "3020": TaperProfile(108, 50.8, 75),
    "3525": TaperProfile(127, 63.5, 90),
}


def taper_lock_dimensions(code: str | int, bore: float) -> dict[str, Any]:
    designation = choice("code", str(code), TAPER_LOCK)
    shaft_bore = real("bore", bore, positive=True)
    p = TAPER_LOCK[designation]
    if shaft_bore > p.max_bore:
        raise InvalidParameterError(f"bore must be <= {p.max_bore:g} mm for taper-lock {designation}")
    return {
        "designation": designation, "outside_diameter": p.outside, "length": p.length,
        "bore_diameter": shaft_bore, "maximum_bore": p.max_bore, "unit": "mm",
        "keepout_envelopes": [cylinder_keepout("bushing_and_extraction_access", p.outside + 10, p.length + 15, (0, 0, -7.5), (0, 0, 1), "Bushing envelope and axial extraction access.")],
    }


def taper_lock_bush(code: str | int, bore: float) -> Compound:
    d = taper_lock_dimensions(code, bore)
    body = axial_cylinder(float(d["outside_diameter"]), float(d["length"])) - axial_cylinder(float(d["bore_diameter"]), float(d["length"]) + 2, origin=(0, 0, -1))
    return compound(f"Taper-lock {d['designation']} bore {d['bore_diameter']:g}", body)


register(FamilyDefinition(key="drive.timing_pulley", category="drive", title="Timing-belt pulley / 同步带轮", description="GT2 and HTD metric pulley pitch/envelope proxies.", factory=timing_pulley, derive=timing_pulley_dimensions, parameters=(ParameterSpec("profile", "string", "Belt profile", choices=tuple(TIMING_PROFILES)), ParameterSpec("teeth", "integer", "Tooth count", minimum=10), ParameterSpec("bore", "number", "Shaft bore", "mm", minimum=0), ParameterSpec("belt_width", "number", "Belt face width", "mm", minimum=0), ParameterSpec("flange", "boolean", "Include guide flanges", required=False, default=True)), aliases=("timing_pulley", "同步带轮"), orientation="axis +Z", detail="pitch cylinder and rotating envelope; teeth omitted", validation="pitch formula, bore limits, interfaces and STEP/PNG review", example="instantiate('drive.timing_pulley.gt2-20-5')"))

register(FamilyDefinition(key="drive.chain_sprocket", category="drive", title="Roller-chain sprocket / 滚子链轮", description="06B–12B pitch-layout sprocket proxies.", factory=chain_sprocket, derive=chain_sprocket_dimensions, parameters=(ParameterSpec("series", "string", "ISO/BS chain series", choices=tuple(CHAIN_PROFILES)), ParameterSpec("teeth", "integer", "Tooth count", minimum=9), ParameterSpec("bore", "number", "Shaft bore", "mm", minimum=0), ParameterSpec("width", "number|null", "Face width override", "mm", required=False, default=None)), standards=(ISO_606,), aliases=("chain_sprocket", "链轮"), orientation="axis +Z", detail="pitch/outside envelope; tooth form omitted", validation="pitch formula, bore limits, interfaces and STEP/PNG review", example="instantiate('drive.chain_sprocket.08b-20', bore=20)"))

register(FamilyDefinition(key="drive.taper_lock_bush", category="drive", title="Taper-lock bushing / 锥套", description="Common 1008–3525 taper-lock bushing envelopes with explicit shaft bore.", factory=taper_lock_bush, derive=taper_lock_dimensions, parameters=(ParameterSpec("code", "string", "Bushing size", choices=tuple(TAPER_LOCK)), ParameterSpec("bore", "number", "Finished shaft bore", "mm", minimum=0)), aliases=("taper_lock", "taper_bush", "锥套"), orientation="axis +Z", detail="outside envelope, length and bore", validation="finite table, bore limit, interfaces and STEP/PNG review", example="instantiate('drive.taper_lock_bush.2012', bore=35)"))
