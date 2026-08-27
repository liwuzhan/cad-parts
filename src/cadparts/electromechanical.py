"""Generic electric actuators, proximity sensors and axial fans."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from build123d import Align, Box, Compound, Cylinder, Pos

from .catalog import register
from .errors import InvalidParameterError
from .models import FamilyDefinition, ParameterSpec
from .proxy import CENTER_MIN, axial_cylinder, box_keepout, choice, compound, cut_z_holes, four_positions, real


@dataclass(frozen=True, slots=True)
class ActuatorProfile:
    width: float; height: float; base_length: float; rod: float; mount_pitch_y: float; mount_pitch_z: float; hole: float


ACTUATORS = {
    "40": ActuatorProfile(40, 40, 120, 12, 30, 30, 5.5),
    "60": ActuatorProfile(60, 60, 160, 16, 45, 45, 6.6),
    "80": ActuatorProfile(80, 80, 220, 22, 60, 60, 9),
    "100": ActuatorProfile(100, 100, 280, 28, 75, 75, 11),
}


def electric_actuator_dimensions(kind: str, frame: str | int, stroke: float, *, position: float = 0) -> dict[str, Any]:
    style = choice("kind", kind.lower(), ("rod", "slider"))
    code = choice("frame", str(frame), ACTUATORS)
    travel = real("stroke", stroke, positive=True)
    current = real("position", position, minimum=0)
    if current > travel:
        raise InvalidParameterError("position must be between 0 and stroke")
    p = ACTUATORS[code]
    body_length = p.base_length + (travel if style == "slider" else travel * 0.45)
    output_x = body_length + p.width * 0.75 + current if style == "rod" else p.width / 2 + current
    return {
        "actuator_type": style, "frame": code, "stroke": travel, "position": current,
        "body_width": p.width, "body_height": p.height, "body_length": body_length,
        "output_position_x": output_x,
        "rod_diameter": p.rod, "mount_hole_pitch_y": p.mount_pitch_y,
        "mount_hole_pitch_z": p.mount_pitch_z, "mount_hole_diameter": p.hole, "unit": "mm",
        "keepout_envelopes": [
            box_keepout("actuator_body_and_motor", (body_length, p.width, p.height), (body_length / 2, 0, 0), "Actuator body, drive and motor allowance."),
            box_keepout("moving_output_sweep", (travel + p.width, p.width, p.height), (body_length + travel / 2, 0, 0), "Rod-end or slider-carriage sweep through the commanded stroke."),
        ],
    }


def electric_actuator(kind: str, frame: str | int, stroke: float, *, position: float = 0) -> Compound:
    d = electric_actuator_dimensions(kind, frame, stroke, position=position)
    body_length, width, height = (float(d[key]) for key in ("body_length", "body_width", "body_height"))
    body = Pos(body_length / 2, 0, -height / 2) * Box(body_length, width, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    children = [body]
    if d["actuator_type"] == "rod":
        children.append(axial_cylinder(float(d["rod_diameter"]), float(d["output_position_x"]) - body_length, origin=(body_length, 0, 0), axis="+X"))
    else:
        carriage_x = float(d["output_position_x"])
        children.append(Pos(carriage_x - width / 2, 0, height / 2) * Box(width, width * 0.9, height * 0.25, align=(Align.MIN, Align.CENTER, Align.MIN)))
    return compound(f"Electric {d['actuator_type']} actuator {d['frame']}", *children)


@dataclass(frozen=True, slots=True)
class SensorProfile:
    diameter: float; body_length: float; thread_length: float; cable: float


SENSORS = {"M8": SensorProfile(8, 45, 30, 25), "M12": SensorProfile(12, 55, 40, 30), "M18": SensorProfile(18, 65, 50, 35), "M30": SensorProfile(30, 80, 60, 45)}


def proximity_sensor_dimensions(thread: str, *, connector: str = "cable") -> dict[str, Any]:
    code = choice("thread", thread.upper(), SENSORS)
    termination = choice("connector", connector.lower(), ("cable", "m8", "m12"))
    p = SENSORS[code]
    tail = p.cable if termination == "cable" else 25
    return {
        "sensor_type": "cylindrical_proximity", "thread": code, "connector": termination,
        "body_diameter": p.diameter, "body_length": p.body_length,
        "thread_length": p.thread_length, "rear_connection_length": tail, "unit": "mm",
        "keepout_envelopes": [
            {"id": "sensing_clearance", "shape": "cylinder", "purpose": "Unobstructed target approach volume in front of sensing face.", "frame": {"origin_mm": [0, 0, 0], "axis": [0, 0, -1]}, "diameter_mm": p.diameter * 2, "length_mm": p.diameter * 1.5},
            {"id": "rear_connector_and_bend", "shape": "cylinder", "purpose": "Rear connector/cable and minimum bend allowance.", "frame": {"origin_mm": [0, 0, p.body_length], "axis": [0, 0, 1]}, "diameter_mm": max(20, p.diameter), "length_mm": tail},
        ],
    }


def proximity_sensor(thread: str, *, connector: str = "cable") -> Compound:
    d = proximity_sensor_dimensions(thread, connector=connector)
    body = axial_cylinder(float(d["body_diameter"]), float(d["body_length"]))
    connector_body = axial_cylinder(max(8, float(d["body_diameter"]) * 0.8), float(d["rear_connection_length"]), origin=(0, 0, float(d["body_length"])))
    return compound(f"{d['thread']} proximity sensor", body, connector_body)


@dataclass(frozen=True, slots=True)
class FanProfile:
    side: float; thickness: float; hole_pitch: float; hole: float


FANS = {
    "40": FanProfile(40, 10, 32, 3.5), "60": FanProfile(60, 15, 50, 4.3),
    "80": FanProfile(80, 25, 71.5, 4.3), "92": FanProfile(92, 25, 82.5, 4.3),
    "120": FanProfile(120, 25, 105, 4.5), "140": FanProfile(140, 38, 124.5, 4.5),
}


def axial_fan_dimensions(size: str | int) -> dict[str, Any]:
    code = choice("size", str(size), FANS)
    p = FANS[code]
    opening = p.side * 0.78
    return {
        "fan_type": "square_axial", "size": code, "side": p.side, "thickness": p.thickness,
        "mount_hole_pitch": p.hole_pitch, "mount_hole_diameter": p.hole,
        "air_opening_diameter": opening, "unit": "mm",
        "keepout_envelopes": [
            box_keepout("intake_clearance", (p.side, p.side, p.side * 0.5), (0, 0, -p.side * 0.25), "Unobstructed intake planning volume."),
            box_keepout("exhaust_clearance", (p.side, p.side, p.side * 0.5), (0, 0, p.thickness + p.side * 0.25), "Unobstructed exhaust planning volume."),
        ],
    }


def axial_fan(size: str | int) -> Compound:
    d = axial_fan_dimensions(size)
    side, thickness = float(d["side"]), float(d["thickness"])
    frame = Box(side, side, thickness, align=(Align.CENTER, Align.CENTER, Align.MIN))
    frame = frame - Cylinder(float(d["air_opening_diameter"]) / 2, thickness + 2, align=CENTER_MIN)
    frame = cut_z_holes(frame, four_positions(float(d["mount_hole_pitch"]), float(d["mount_hole_pitch"])), float(d["mount_hole_diameter"]), -1, thickness + 1)
    hub = axial_cylinder(side * 0.28, thickness)
    return compound(f"Axial fan {d['size']}", frame, hub)


register(FamilyDefinition(key="actuator.linear.electric", category="actuator", title="Electric linear actuator / 电动执行器", description="Rod and slider actuator planning envelopes with complete output sweep.", factory=electric_actuator, derive=electric_actuator_dimensions, parameters=(ParameterSpec("kind", "string", "Output type", choices=("rod", "slider")), ParameterSpec("frame", "string", "Planning frame", choices=tuple(ACTUATORS)), ParameterSpec("stroke", "number", "Commanded stroke", "mm", minimum=0), ParameterSpec("position", "number", "Current output position", "mm", required=False, default=0)), aliases=("electric_actuator", "electric_cylinder", "电动缸", "电动推杆", "直线模组"), orientation="rear X=0; extension +X", detail="body/output envelope and sweep", validation="finite profiles, position bounds, interfaces and STEP/PNG review", example="instantiate('actuator.linear.electric.rod60', stroke=300)"))

register(FamilyDefinition(key="sensor.proximity.threaded", category="sensor", title="Threaded proximity sensor / 螺纹接近传感器", description="M8/M12/M18/M30 cylindrical sensor, sensing and cable-clearance proxy.", factory=proximity_sensor, derive=proximity_sensor_dimensions, parameters=(ParameterSpec("thread", "string", "Metric threaded body", choices=tuple(SENSORS)), ParameterSpec("connector", "string", "Rear termination", required=False, default="cable", choices=("cable", "m8", "m12"))), aliases=("proximity_sensor", "接近开关", "接近传感器"), orientation="sensing face Z=0 toward -Z; cable +Z", detail="threaded body and functional clearances", validation="finite sizes, interfaces and STEP/PNG review", example="instantiate('sensor.proximity.threaded.m18')"))

register(FamilyDefinition(key="fan.axial.square", category="fan", title="Square axial fan / 方形轴流风扇", description="Common 40–140 mm fan frame, mounting and airflow-clearance proxy.", factory=axial_fan, derive=axial_fan_dimensions, parameters=(ParameterSpec("size", "string", "Nominal square frame", choices=tuple(FANS)),), aliases=("axial_fan", "cooling_fan", "散热风扇", "轴流风扇"), orientation="mounting face XY at Z=0; airflow +Z", detail="frame, opening, hub and intake/exhaust keepouts", validation="finite profiles, holes, interfaces and STEP/PNG review", example="instantiate('fan.axial.square.120')"))
