"""High-reuse motor envelopes with explicit mounting interfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from build123d import Box, Compound, Cylinder, Pos

from .catalog import register
from .errors import InvalidParameterError
from .models import FamilyDefinition, ParameterSpec, StandardReference
from .proxy import CENTER_MIN, axial_cylinder, box_keepout, choice, compound, cut_z_holes, four_positions, real


@dataclass(frozen=True, slots=True)
class SquareFace:
    face: float
    pitch: float
    hole: float
    pilot: float
    pilot_depth: float
    shaft: float
    shaft_length: float
    body_length: float


STEPPER_FACES = {
    "42": SquareFace(42, 31, 3.5, 22, 2, 5, 24, 48),
    "56.4": SquareFace(56.4, 47.14, 5.2, 38.1, 1.6, 6.35, 21, 76),
    "60": SquareFace(60, 50, 5.5, 36, 2, 8, 25, 75),
    "85": SquareFace(85, 69.6, 6.5, 73, 2, 12.7, 32, 118),
}

SERVO_FACES = {
    "40": SquareFace(40, 30, 4.5, 30, 2.5, 8, 25, 80),
    "60": SquareFace(60, 50, 5.5, 50, 3, 14, 30, 100),
    "80": SquareFace(80, 70, 6.5, 70, 3, 19, 35, 130),
    "90": SquareFace(90, 80, 7, 80, 3, 19, 35, 140),
    "110": SquareFace(110, 95, 9, 95, 3.5, 19, 40, 160),
    "130": SquareFace(130, 110, 9, 110, 3.5, 22, 45, 180),
}

FRAME_GUIDE = StandardReference(
    system="market",
    designation="Oriental Motor frame-size guide",
    title="Stepper Motor Frame Sizes",
    edition="accessed 2026-08-27",
    status="manufacturer guidance",
    url="https://www.orientalmotor.com/stepper-motors/stepper-motor-frame-sizes.html",
    relationship="frame-size nomenclature",
    note="NEMA equivalence is based on frame size only; shaft and body remain product-specific.",
)

IEC_60072 = StandardReference(
    system="IEC",
    designation="IEC 60072-1:2022",
    title="Dimensions and output series for rotating electrical machines — Part 1",
    edition="2022",
    status="current",
    url="https://webstore.iec.ch/en/publication/67088",
    relationship="governing-mounting-dimensions",
    note="Body outline and terminal box remain manufacturer-specific.",
)


def _square_dimensions(table: dict[str, SquareFace], motor_type: str, frame: Any, body_length: float | None, shaft_diameter: float | None, shaft_length: float | None) -> dict[str, Any]:
    code = choice("frame", str(frame), table)
    p = table[code]
    body = p.body_length if body_length is None else real("body_length", body_length, positive=True)
    shaft = p.shaft if shaft_diameter is None else real("shaft_diameter", shaft_diameter, positive=True)
    extension = p.shaft_length if shaft_length is None else real("shaft_length", shaft_length, positive=True)
    if shaft >= p.pilot:
        raise InvalidParameterError("shaft_diameter must be smaller than pilot_diameter")
    rear = max(20.0, p.face * 0.35)
    return {
        "motor_type": motor_type, "frame": code, "face_size": p.face,
        "body_length": body, "mounting_hole_pitch": p.pitch,
        "mounting_hole_diameter": p.hole, "pilot_diameter": p.pilot,
        "pilot_depth": p.pilot_depth, "shaft_diameter": shaft,
        "shaft_length": extension, "unit": "mm",
        "keepout_envelopes": [box_keepout(
            "body_and_rear_connector", (p.face, p.face, body + rear),
            (0, 0, (body + rear) / 2),
            "Conservative motor body and rear cable/connector clearance.",
        )],
    }


def _square_shape(d: dict[str, Any], label: str) -> Compound:
    face, depth = float(d["face_size"]), float(d["body_length"])
    body = Box(face, face, depth, align=CENTER_MIN)
    body = cut_z_holes(body, four_positions(float(d["mounting_hole_pitch"]), float(d["mounting_hole_pitch"])), float(d["mounting_hole_diameter"]), -1, min(depth, 8))
    pilot = Pos(0, 0, -float(d["pilot_depth"])) * Cylinder(float(d["pilot_diameter"]) / 2, float(d["pilot_depth"]), align=CENTER_MIN)
    shaft = axial_cylinder(float(d["shaft_diameter"]), float(d["shaft_length"]), axis="-Z")
    return compound(label, body, pilot, shaft)


def stepper_square_dimensions(frame: Any, *, body_length: float | None = None, shaft_diameter: float | None = None, shaft_length: float | None = None) -> dict[str, Any]:
    return _square_dimensions(STEPPER_FACES, "square_stepper", frame, body_length, shaft_diameter, shaft_length)


def stepper_square(frame: Any, *, body_length: float | None = None, shaft_diameter: float | None = None, shaft_length: float | None = None) -> Compound:
    d = stepper_square_dimensions(frame, body_length=body_length, shaft_diameter=shaft_diameter, shaft_length=shaft_length)
    return _square_shape(d, f"Stepper frame {d['frame']}")


def servo_square_dimensions(flange: Any, *, body_length: float | None = None, shaft_diameter: float | None = None, shaft_length: float | None = None) -> dict[str, Any]:
    return _square_dimensions(SERVO_FACES, "square_flange_servo", flange, body_length, shaft_diameter, shaft_length)


def servo_square(flange: Any, *, body_length: float | None = None, shaft_diameter: float | None = None, shaft_length: float | None = None) -> Compound:
    d = servo_square_dimensions(flange, body_length=body_length, shaft_diameter=shaft_diameter, shaft_length=shaft_length)
    return _square_shape(d, f"Servo flange {d['frame']}")


@dataclass(frozen=True, slots=True)
class IECFrame:
    a: float; b: float; c: float; h: float; shaft: float; shaft_length: float; foot_hole: float
    body_diameter: float; body_length: float
    b5_pcd: float; b5_pilot: float; b5_outer: float; b5_hole: float
    b14_pcd: float; b14_pilot: float; b14_outer: float; b14_hole: float


IEC_FRAMES = {
    "63": IECFrame(100, 80, 40, 63, 11, 23, 7, 120, 190, 115, 95, 140, 10, 75, 60, 90, 5),
    "71": IECFrame(112, 90, 45, 71, 14, 30, 7, 136, 220, 130, 110, 160, 10, 85, 70, 105, 6),
    "80": IECFrame(125, 100, 50, 80, 19, 40, 10, 152, 250, 165, 130, 200, 12, 100, 80, 120, 6),
    "90S": IECFrame(140, 100, 56, 90, 24, 50, 10, 170, 280, 165, 130, 200, 12, 115, 95, 140, 8),
    "90L": IECFrame(140, 125, 56, 90, 24, 50, 10, 170, 305, 165, 130, 200, 12, 115, 95, 140, 8),
    "100L": IECFrame(160, 140, 63, 100, 28, 60, 12, 190, 340, 215, 180, 250, 15, 130, 110, 160, 8),
    "112M": IECFrame(190, 140, 70, 112, 28, 60, 12, 215, 370, 215, 180, 250, 15, 130, 110, 160, 8),
    "132S": IECFrame(216, 140, 89, 132, 38, 80, 12, 255, 430, 265, 230, 300, 15, 165, 130, 200, 10),
    "132M": IECFrame(216, 178, 89, 132, 38, 80, 12, 255, 470, 265, 230, 300, 15, 165, 130, 200, 10),
}


def iec_motor_dimensions(frame: str, *, mount: str = "B3") -> dict[str, Any]:
    code = choice("frame", frame, IEC_FRAMES)
    mounting = choice("mount", mount, ("B3", "B5", "B14", "B35"))
    p = IEC_FRAMES[code]
    d: dict[str, Any] = {
        "motor_type": "iec_induction", "frame": code, "mount": mounting,
        "shaft_height": p.h, "shaft_diameter": p.shaft, "shaft_length": p.shaft_length,
        "body_diameter": p.body_diameter, "body_length": p.body_length,
        "foot_hole_pitch_axial": p.a, "foot_hole_pitch_transverse": p.b,
        "drive_end_to_first_foot_hole": p.c, "foot_hole_diameter": p.foot_hole, "unit": "mm",
    }
    flange = "b5" if mounting in {"B5", "B35"} else "b14" if mounting == "B14" else None
    if flange:
        d.update({
            "flange_kind": flange.upper(), "flange_pitch_circle": getattr(p, f"{flange}_pcd"),
            "flange_pilot_diameter": getattr(p, f"{flange}_pilot"),
            "flange_outer_diameter": getattr(p, f"{flange}_outer"),
            "flange_hole_diameter": getattr(p, f"{flange}_hole"),
        })
    radial = max(p.body_diameter / 2, p.h)
    d["keepout_envelopes"] = [box_keepout(
        "motor_and_terminal_box", (p.body_length, 2 * radial, 2 * radial + p.h),
        (p.body_length / 2, 0, p.h),
        "Conservative body, fan cover and terminal-box envelope; verify the chosen vendor outline.",
    )]
    return d


def iec_motor(frame: str, *, mount: str = "B3") -> Compound:
    d = iec_motor_dimensions(frame, mount=mount)
    h = float(d["shaft_height"])
    body = Pos(0, 0, h) * axial_cylinder(float(d["body_diameter"]), float(d["body_length"]), axis="+X")
    shaft = axial_cylinder(float(d["shaft_diameter"]), float(d["shaft_length"]), origin=(0, 0, h), axis="-X")
    children = [body, shaft]
    if d["mount"] in {"B3", "B35"}:
        a, b, c, hole = (float(d[key]) for key in ("foot_hole_pitch_axial", "foot_hole_pitch_transverse", "drive_end_to_first_foot_hole", "foot_hole_diameter"))
        foot = Pos(c + a / 2, 0, 0) * Box(a + 2 * hole, b + 2 * hole, 8, align=CENTER_MIN)
        for x in (c, c + a):
            for y in (-b / 2, b / 2):
                foot = foot - Pos(x, y, -1) * Cylinder(hole / 2, 10, align=CENTER_MIN)
        children.append(foot)
    if "flange_outer_diameter" in d:
        children.extend([
            axial_cylinder(float(d["flange_outer_diameter"]), 8, origin=(0, 0, h), axis="+X"),
            axial_cylinder(float(d["flange_pilot_diameter"]), 3, origin=(-3, 0, h), axis="+X"),
        ])
    return compound(f"IEC {d['frame']} {d['mount']} motor", *children)


register(FamilyDefinition(
    key="motor.stepper.square", category="motor", title="Square stepper motor / 方形步进电机",
    description="Finite frame-interface profiles with product-specific body and shaft overrides.",
    factory=stepper_square, derive=stepper_square_dimensions,
    parameters=(ParameterSpec("frame", "string", "Frame face size", choices=tuple(STEPPER_FACES)), ParameterSpec("body_length", "number|null", "Product body length override", "mm", required=False, default=None), ParameterSpec("shaft_diameter", "number|null", "Product shaft diameter override", "mm", required=False, default=None), ParameterSpec("shaft_length", "number|null", "Product shaft extension override", "mm", required=False, default=None)),
    standards=(FRAME_GUIDE,), aliases=("stepper_motor", "步进电机", "nema_stepper"),
    orientation="mounting face XY at Z=0; body +Z; output shaft -Z", detail="mounting and conservative envelope proxy",
    validation="finite frame table, interface coordinates, bbox and STEP/PNG review", example="instantiate('motor.stepper.square.42')",
    notes=("NEMA equivalence describes frame size only; compare the resolved shaft and pilot interfaces.",),
))

register(FamilyDefinition(
    key="motor.servo.square_flange", category="motor", title="Square-flange servo motor / 方形法兰伺服电机",
    description="Market planning profiles for common 40–130 mm servo flange classes.",
    factory=servo_square, derive=servo_square_dimensions,
    parameters=(ParameterSpec("flange", "string", "Nominal square flange class", choices=tuple(SERVO_FACES)), ParameterSpec("body_length", "number|null", "Catalog body length override", "mm", required=False, default=None), ParameterSpec("shaft_diameter", "number|null", "Catalog shaft diameter override", "mm", required=False, default=None), ParameterSpec("shaft_length", "number|null", "Catalog shaft extension override", "mm", required=False, default=None)),
    aliases=("servo_motor", "伺服电机"), orientation="mounting face XY at Z=0; body +Z; output shaft -Z",
    detail="series planning proxy; not a universal flange standard", validation="finite profiles, explicit overrides, bbox and STEP/PNG review",
    example="instantiate('motor.servo.square_flange.110')", notes=("A nominal 110 mm class is not sufficient evidence of interchangeability.",),
))

register(FamilyDefinition(
    key="motor.induction.iec", category="motor", title="IEC induction motor / IEC 异步电机",
    description="IEC 60072 mounting interfaces with a conservative manufacturer-dependent body outline.",
    factory=iec_motor, derive=iec_motor_dimensions,
    parameters=(ParameterSpec("frame", "string", "IEC frame designation", choices=tuple(IEC_FRAMES)), ParameterSpec("mount", "string", "Mounting arrangement", required=False, default="B3", choices=("B3", "B5", "B14", "B35"))),
    standards=(IEC_60072,), aliases=("iec_motor", "三相异步电机"), orientation="output shaft -X; shaft center at Z=H; feet on Z=0",
    detail="normative mounting coordinates plus conservative body envelope", validation="IEC frame table, mount variants, interfaces and STEP/PNG review",
    example="instantiate('motor.induction.iec.80-b5')", notes=("Confirm vendor overall outline before final enclosure release.",),
))
