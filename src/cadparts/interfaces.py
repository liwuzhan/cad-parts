"""Concrete named interfaces for automated assembly placement."""

from __future__ import annotations

from typing import Any, Mapping


def _interface(
    identifier: str,
    interface_type: str,
    role: str,
    origin: tuple[float, float, float],
    axis: tuple[float, float, float],
    **dimensions: Any,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": identifier,
        "type": interface_type,
        "role": role,
        "frame": {"origin_mm": list(origin), "axis": list(axis)},
    }
    if dimensions:
        result["dimensions_mm"] = dimensions
    return result


def resolve_interfaces(
    family: str,
    parameters: Mapping[str, Any],
    derived: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Resolve a family's semantic interfaces to concrete frames and sizes."""

    z_axis = (0.0, 0.0, 1.0)
    minus_z = (0.0, 0.0, -1.0)

    if family == "bearing.deep_groove":
        width = float(derived["width"])
        return [
            _interface("shaft_bore", "cylindrical_bore", "shaft radial location", (0, 0, 0), z_axis,
                       diameter=float(derived["bore_diameter"]), length=width),
            _interface("housing_seat", "cylindrical_surface", "housing radial location", (0, 0, 0), z_axis,
                       diameter=float(derived["outside_diameter"]), length=width),
            _interface("axial_face_min", "planar_face", "axial location", (0, 0, 0), minus_z),
            _interface("axial_face_max", "planar_face", "axial location", (0, 0, width), z_axis),
        ]

    if family == "fastener.hex_bolt_metric":
        head_height = float(derived["head_height"])
        length = float(derived["nominal_length_below_head"])
        return [
            _interface("thread_axis", "male_thread_envelope", "coaxial fastener placement",
                       (0, 0, head_height), z_axis,
                       nominal_diameter=float(derived["nominal_diameter"]), length=length,
                       pitch=float(derived["coarse_pitch"])),
            _interface("head_bearing_face", "planar_face", "clamp location", (0, 0, head_height), minus_z,
                       across_flats=float(derived["across_flats"])),
        ]

    if family == "fastener.hex_nut_metric":
        height = float(derived["height"])
        return [
            _interface("thread_bore", "female_thread_envelope", "mate with bolt", (0, 0, 0), z_axis,
                       nominal_diameter=float(derived["nominal_thread_diameter"]), length=height,
                       pitch=float(derived["coarse_pitch"])),
            _interface("bearing_face_min", "planar_face", "clamp location", (0, 0, 0), minus_z),
            _interface("bearing_face_max", "planar_face", "clamp location", (0, 0, height), z_axis),
        ]

    if family == "fastener.plain_washer_metric":
        thickness = float(derived["thickness"])
        return [
            _interface("clearance_bore", "cylindrical_bore", "bolt clearance", (0, 0, 0), z_axis,
                       diameter=float(derived["inside_diameter"]), length=thickness),
            _interface("bearing_face_min", "planar_face", "load distribution", (0, 0, 0), minus_z,
                       outside_diameter=float(derived["outside_diameter"])),
            _interface("bearing_face_max", "planar_face", "load distribution", (0, 0, thickness), z_axis,
                       outside_diameter=float(derived["outside_diameter"])),
        ]

    if family == "gear.spur":
        width = float(derived["face_width"])
        interfaces = [
            _interface("rotation_axis", "axis", "assembly rotation axis", (0, 0, 0), z_axis),
            _interface("pitch_reference", "pitch_cylinder", "gear mesh layout", (0, 0, 0), z_axis,
                       diameter=float(derived["pitch_diameter"]), width=width),
        ]
        if float(derived["bore_diameter"]) > 0:
            interfaces.insert(0, _interface(
                "shaft_bore", "cylindrical_bore", "mount on shaft", (0, 0, 0), z_axis,
                diameter=float(derived["bore_diameter"]), length=width,
            ))
        return interfaces

    if family == "gear.bevel_straight":
        height = float(derived["axial_height"])
        interfaces = [
            _interface("rotation_axis", "axis", "assembly rotation axis", (0, 0, 0), z_axis),
            _interface("pitch_cone_reference", "pitch_cone", "mating layout", (0, 0, 0), z_axis,
                       heel_pitch_diameter=float(derived["heel_pitch_diameter"]),
                       cone_angle_deg=float(derived["pitch_cone_angle_deg"]),
                       cone_distance=float(derived["cone_distance"])),
        ]
        if float(derived["bore_diameter"]) > 0:
            interfaces.insert(0, _interface(
                "shaft_bore", "cylindrical_bore", "mount on shaft", (0, 0, 0), z_axis,
                diameter=float(derived["bore_diameter"]), length=height,
            ))
        return interfaces

    if family in {"profile.square_tube", "profile.round_tube", "profile.round_rod", "profile.equal_angle"}:
        length = float(derived["length"])
        interfaces = [
            _interface("end_min", "profile_end", "cut/join plane", (0, 0, 0), minus_z),
            _interface("end_max", "profile_end", "cut/join plane", (0, 0, length), z_axis),
        ]
        if family == "profile.round_tube":
            interfaces.insert(0, _interface(
                "inside_bore", "cylindrical_bore", "shaft/tube clearance", (0, 0, 0), z_axis,
                diameter=float(derived["inside_diameter"]), length=length,
            ))
        if family == "profile.round_rod":
            interfaces.insert(0, _interface("axis", "axis", "coaxial placement", (0, 0, 0), z_axis))
        return interfaces

    if family == "key.parallel":
        return [
            _interface(
                "shaft_keyway_contact", "rectangular_key_contact", "torque-transfer placement",
                (0, 0, 0), (1.0, 0.0, 0.0),
                width=float(derived["width"]), height=float(derived["height"]), length=float(derived["length"]),
            )
        ]

    if family in {"motor.stepper.square", "motor.servo.square_flange"}:
        pitch = float(derived["mounting_hole_pitch"])
        interfaces = [
            _interface("mounting_face", "planar_face", "axial location", (0, 0, 0), minus_z, face_size=float(derived["face_size"])),
            _interface("pilot", "cylindrical_surface", "radial location", (0, 0, 0), minus_z, diameter=float(derived["pilot_diameter"]), length=float(derived["pilot_depth"])),
            _interface("output_shaft", "male_shaft", "torque output", (0, 0, 0), minus_z, diameter=float(derived["shaft_diameter"]), length=float(derived["shaft_length"])),
        ]
        for sx in (-1, 1):
            for sy in (-1, 1):
                interfaces.append(_interface(
                    f"mount_hole_{'p' if sx > 0 else 'm'}x_{'p' if sy > 0 else 'm'}y",
                    "clearance_hole", "motor mounting", (sx * pitch / 2, sy * pitch / 2, 0), z_axis,
                    diameter=float(derived["mounting_hole_diameter"]),
                ))
        return interfaces

    if family == "motor.induction.iec":
        h = float(derived["shaft_height"])
        interfaces = [
            _interface("output_shaft", "male_shaft", "torque output", (0, 0, h), (-1.0, 0.0, 0.0), diameter=float(derived["shaft_diameter"]), length=float(derived["shaft_length"])),
            _interface("shaft_axis", "axis", "coaxial driven-part placement", (0, 0, h), (-1.0, 0.0, 0.0)),
        ]
        if derived["mount"] in {"B3", "B35"}:
            a, b, c = (float(derived[key]) for key in ("foot_hole_pitch_axial", "foot_hole_pitch_transverse", "drive_end_to_first_foot_hole"))
            for index, (x, y) in enumerate(((c, -b / 2), (c, b / 2), (c + a, -b / 2), (c + a, b / 2)), 1):
                interfaces.append(_interface(f"foot_hole_{index}", "clearance_hole", "foot mounting", (x, y, 0), z_axis, diameter=float(derived["foot_hole_diameter"])))
            interfaces.append(_interface("foot_plane", "planar_face", "base datum", (c + a / 2, 0, 0), minus_z))
        if "flange_pitch_circle" in derived:
            interfaces.append(_interface(
                "drive_flange", "circular_flange", "flange mounting and pilot",
                (0, 0, h), (-1.0, 0.0, 0.0), pitch_circle=float(derived["flange_pitch_circle"]),
                pilot_diameter=float(derived["flange_pilot_diameter"]), outer_diameter=float(derived["flange_outer_diameter"]),
                hole_diameter=float(derived["flange_hole_diameter"]), hole_count=4,
            ))
        return interfaces

    if family == "gearbox.right_angle.market":
        height = float(derived["body_height"])
        length = float(derived["body_length"])
        width = float(derived["body_width"])
        axis_height = float(derived["output_axis_height"])
        interfaces = [
            _interface("output_bore", "cylindrical_bore", "hollow torque output", (-length / 2, 0, axis_height), (1.0, 0.0, 0.0), diameter=float(derived["output_bore"]), length=length),
            _interface("output_axis", "axis", "output member placement", (0, 0, axis_height), (1.0, 0.0, 0.0)),
            _interface("input_motor_pilot", "circular_flange", "motor adapter location", (0, -width / 2, height / 2), (0.0, -1.0, 0.0), pilot_diameter=float(derived["input_pilot_diameter"]), bolt_circle=float(derived["input_bolt_circle"])),
            _interface("base_plane", "planar_face", "gearbox mounting datum", (0, 0, 0), minus_z),
        ]
        px, py = float(derived["foot_hole_pitch_x"]), float(derived["foot_hole_pitch_y"])
        for index, (x, y) in enumerate(((-px / 2, -py / 2), (-px / 2, py / 2), (px / 2, -py / 2), (px / 2, py / 2)), 1):
            interfaces.append(_interface(f"foot_hole_{index}", "clearance_hole", "base mounting", (x, y, 0), z_axis, diameter=float(derived["foot_hole_diameter"])))
        return interfaces

    if family == "gearbox.planetary.inline":
        body_length = float(derived["body_length"])
        return [
            _interface("motor_input", "square_motor_flange", "motor adapter", (0, 0, 0), minus_z, face=float(derived["input_face"]), hole_pitch=float(derived["input_hole_pitch"]), pilot_diameter=float(derived["input_pilot_diameter"])),
            _interface("output_flange", "circular_flange", "machine mounting", (0, 0, body_length), z_axis, outer_diameter=float(derived["output_flange_diameter"]), pilot_diameter=float(derived["output_pilot_diameter"]), hole_pitch=float(derived["output_hole_pitch"])),
            _interface("output_shaft", "male_shaft", "torque output", (0, 0, body_length), z_axis, diameter=float(derived["output_shaft_diameter"]), length=float(derived["output_shaft_length"])),
            _interface("rotation_axis", "axis", "coaxial placement", (0, 0, 0), z_axis),
        ]

    if family == "bearing.unit.mounted":
        kind = str(derived["bearing_unit_type"])
        axis_height = float(derived["shaft_axis_height"])
        interfaces = [
            _interface("shaft_bore", "cylindrical_bore", "shaft radial location", (0, -float(derived["axial_thickness"]) / 2, axis_height), (0.0, 1.0, 0.0), diameter=float(derived["bore_diameter"]), length=float(derived["axial_thickness"])),
            _interface("shaft_axis", "axis", "coaxial shaft placement", (0, 0, axis_height), (0.0, 1.0, 0.0)),
        ]
        if kind == "UCP":
            pitch = float(derived["mount_hole_pitch_x"])
            interfaces.append(_interface("base_plane", "planar_face", "base mounting datum", (0, 0, 0), minus_z))
            for index, x in enumerate((-pitch / 2, pitch / 2), 1):
                interfaces.append(_interface(f"mount_hole_{index}", "clearance_hole", "base mounting", (x, 0, 0), z_axis, diameter=float(derived["mount_hole_diameter"])))
        elif kind == "UCF":
            px, pz = float(derived["mount_hole_pitch_x"]), float(derived["mount_hole_pitch_z"])
            for index, (x, z) in enumerate(((-px / 2, axis_height - pz / 2), (-px / 2, axis_height + pz / 2), (px / 2, axis_height - pz / 2), (px / 2, axis_height + pz / 2)), 1):
                interfaces.append(_interface(f"mount_hole_{index}", "clearance_hole", "flange mounting", (x, -float(derived["axial_thickness"]) / 2, z), (0.0, 1.0, 0.0), diameter=float(derived["mount_hole_diameter"])))
        else:
            pitch = float(derived["mount_hole_pitch_x"])
            for index, x in enumerate((-pitch / 2, pitch / 2), 1):
                interfaces.append(_interface(f"mount_hole_{index}", "clearance_hole", "flange mounting", (x, -float(derived["axial_thickness"]) / 2, axis_height), (0.0, 1.0, 0.0), diameter=float(derived["mount_hole_diameter"])))
        return interfaces

    if family == "coupling.flexible":
        length = float(derived["overall_length"])
        return [
            _interface("shaft_bore_a", "cylindrical_bore", "first shaft location", (0, 0, 0), z_axis, diameter=float(derived["bore_a"]), length=float(derived["hub_length_a"])),
            _interface("shaft_bore_b", "cylindrical_bore", "second shaft location", (0, 0, length), minus_z, diameter=float(derived["bore_b"]), length=float(derived["hub_length_b"])),
            _interface("rotation_axis", "axis", "coaxial placement", (0, 0, 0), z_axis),
            _interface("shaft_end_a", "planar_face", "first shaft axial datum", (0, 0, 0), minus_z),
            _interface("shaft_end_b", "planar_face", "second shaft axial datum", (0, 0, length), z_axis),
        ]

    if family == "linear.guide.rail":
        position = float(derived["block_position"])
        return [
            _interface("rail_base", "planar_face", "rail mounting datum", (0, 0, 0), minus_z, length=float(derived["rail_length"]), width=float(derived["rail_width"])),
            _interface("motion_axis", "linear_axis", "carriage travel", (0, 0, float(derived["assembly_height"])), (1.0, 0.0, 0.0), travel=float(derived["rail_length"]) - float(derived["block_length"])),
            _interface("carriage_top", "planar_face", "moving-part mounting", (position, 0, float(derived["assembly_height"])), z_axis, width=float(derived["block_width"]), length=float(derived["block_length"]), hole_pitch_x=float(derived["block_hole_pitch_x"]), hole_pitch_y=float(derived["block_hole_pitch_y"])),
            _interface("rail_hole_pattern", "linear_hole_pattern", "rail mounting", (0, 0, 0), z_axis, pitch=float(derived["rail_mounting_pitch"]), diameter=float(derived["rail_hole_diameter"]), count=int(derived["rail_hole_count"])),
        ]

    if family == "linear.ball_screw":
        position = float(derived["nut_position"])
        return [
            _interface("screw_axis", "linear_rotation_axis", "screw/support alignment", (0, 0, 0), (1.0, 0.0, 0.0), diameter=float(derived["screw_diameter"]), length=float(derived["screw_length"]), lead=float(derived["lead"])),
            _interface("fixed_end", "shaft_end", "fixed support reference", (0, 0, 0), (-1.0, 0.0, 0.0), diameter=float(derived["screw_diameter"])),
            _interface("floating_end", "shaft_end", "floating support reference", (float(derived["screw_length"]), 0, 0), (1.0, 0.0, 0.0), diameter=float(derived["screw_diameter"])),
            _interface("nut_flange", "circular_flange", "moving load attachment", (position - float(derived["nut_length"]) / 2, 0, 0), (-1.0, 0.0, 0.0), outer_diameter=float(derived["nut_flange_diameter"]), pitch_circle=float(derived["nut_flange_pitch_circle"]), hole_diameter=float(derived["nut_flange_hole_diameter"])),
        ]

    if family == "linear.screw_support":
        height = float(derived["shaft_axis_height"])
        return [
            _interface("shaft_bore", "cylindrical_bore", f"{derived['support_role']} screw support", (-float(derived["body_length"]) / 2, 0, height), (1.0, 0.0, 0.0), diameter=float(derived["shaft_bore"]), length=float(derived["body_length"])),
            _interface("shaft_axis", "axis", "coaxial screw placement", (0, 0, height), (1.0, 0.0, 0.0)),
            _interface("base_plane", "planar_face", "support mounting datum", (0, 0, 0), minus_z),
            _interface("mount_hole_pattern", "rectangular_hole_pattern", "support mounting", (-float(derived["body_length"]) / 2, 0, float(derived["body_height"]) / 2), (-1.0, 0.0, 0.0), pitch_y=float(derived["mount_hole_pitch_y"]), pitch_z=float(derived["mount_hole_pitch_z"]), diameter=float(derived["mount_hole_diameter"]), count=4),
        ]

    if family == "linear.guide.supported_round":
        position = float(derived["block_position"])
        return [
            _interface("shaft_axis", "linear_axis", "round-guide travel", (0, 0, float(derived["shaft_axis_height"])), (1.0, 0.0, 0.0), diameter=float(derived["shaft_diameter"]), length=float(derived["length"])),
            _interface("support_base", "planar_face", "rail mounting datum", (0, 0, 0), minus_z, length=float(derived["length"]), width=float(derived["support_width"])),
            _interface("carriage_top", "planar_face", "moving-part mounting", (position, 0, float(derived["block_height"])), z_axis, width=float(derived["block_width"]), length=float(derived["block_length"])),
        ]

    if family == "linear.bushing.ball":
        interfaces = [
            _interface("shaft_bore", "cylindrical_bore", "round-shaft location and travel", (0, 0, 0), z_axis, diameter=float(derived["bore_diameter"]), length=float(derived["body_length"])),
            _interface("motion_axis", "linear_axis", "bushing translation", (0, 0, 0), z_axis),
        ]
        if derived["flanged"]:
            interfaces.append(_interface("mounting_flange", f"{derived['flange_shape']}_flange", "moving-load attachment", (0, 0, 0), minus_z, size=float(derived["flange_size"]), hole_pitch=float(derived["flange_hole_pitch"]), hole_diameter=float(derived["flange_hole_diameter"]), hole_count=4))
        return interfaces

    if family in {"drive.timing_pulley", "drive.chain_sprocket"}:
        width_key = "overall_width" if family == "drive.timing_pulley" else "face_width"
        pitch_key = "pitch_diameter"
        interfaces = [
            _interface("rotation_axis", "axis", "shaft and drive placement", (0, 0, 0), z_axis),
            _interface("pitch_reference", "pitch_cylinder", "belt/chain center-distance layout", (0, 0, 0), z_axis, diameter=float(derived[pitch_key]), width=float(derived[width_key])),
            _interface("axial_face_min", "planar_face", "axial location", (0, 0, 0), minus_z),
            _interface("axial_face_max", "planar_face", "axial location", (0, 0, float(derived[width_key])), z_axis),
        ]
        if float(derived["bore_diameter"]) > 0:
            interfaces.insert(0, _interface("shaft_bore", "cylindrical_bore", "mount on shaft", (0, 0, 0), z_axis, diameter=float(derived["bore_diameter"]), length=float(derived[width_key])))
        return interfaces

    if family == "drive.taper_lock_bush":
        length = float(derived["length"])
        return [
            _interface("shaft_bore", "cylindrical_bore", "shaft location", (0, 0, 0), z_axis, diameter=float(derived["bore_diameter"]), length=length),
            _interface("hub_seat", "tapered_surface_envelope", "mate with pulley/sprocket hub", (0, 0, 0), z_axis, maximum_diameter=float(derived["outside_diameter"]), length=length),
            _interface("axial_face_min", "planar_face", "axial datum", (0, 0, 0), minus_z),
            _interface("axial_face_max", "planar_face", "axial datum", (0, 0, length), z_axis),
        ]

    if family in {"pneumatic.cylinder.iso6432", "pneumatic.cylinder.iso15552", "pneumatic.cylinder.compact"}:
        body_length = float(derived["body_length"])
        tip = body_length + float(derived["rod_extension_retracted"])
        return [
            _interface("rear_mount", "cylinder_end", "rear cylinder attachment", (0, 0, 0), (-1.0, 0.0, 0.0), nominal_bore=float(derived["bore_diameter"])),
            _interface("front_mount", "cylinder_end", "front flange/attachment reference", (body_length, 0, 0), (1.0, 0.0, 0.0), hole_pitch=float(derived["front_mount_pitch"]), hole_diameter=float(derived["front_mount_hole_diameter"])),
            _interface("rod_end", "male_rod", "moving load attachment", (tip, 0, 0), (1.0, 0.0, 0.0), diameter=float(derived["rod_diameter"])),
            _interface("motion_axis", "linear_axis", "piston travel", (body_length, 0, 0), (1.0, 0.0, 0.0), stroke=float(derived["stroke"])),
        ]

    if family == "actuator.linear.electric":
        body_length = float(derived["body_length"])
        return [
            _interface("rear_mount", "rectangular_mount", "actuator body attachment", (0, 0, 0), (-1.0, 0.0, 0.0), pitch_y=float(derived["mount_hole_pitch_y"]), pitch_z=float(derived["mount_hole_pitch_z"]), hole_diameter=float(derived["mount_hole_diameter"])),
            _interface("output", f"{derived['actuator_type']}_output", "moving load attachment", (float(derived["output_position_x"]), 0, 0), (1.0, 0.0, 0.0), rod_diameter=float(derived["rod_diameter"])),
            _interface("motion_axis", "linear_axis", "commanded travel", (body_length, 0, 0), (1.0, 0.0, 0.0), stroke=float(derived["stroke"])),
        ]

    if family == "sensor.proximity.threaded":
        return [
            _interface("threaded_mount", "male_thread_envelope", "panel/bracket mounting", (0, 0, 0), z_axis, nominal_diameter=float(derived["body_diameter"]), length=float(derived["thread_length"])),
            _interface("sensing_face", "planar_face", "target reference", (0, 0, 0), minus_z, diameter=float(derived["body_diameter"])),
            _interface("cable_exit", "cable_axis", "connector/cable routing", (0, 0, float(derived["body_length"])), z_axis),
        ]

    if family == "fan.axial.square":
        pitch = float(derived["mount_hole_pitch"])
        interfaces = [
            _interface("mounting_face", "planar_face", "panel mounting datum", (0, 0, 0), minus_z, side=float(derived["side"])),
            _interface("airflow_axis", "flow_axis", "intake/exhaust alignment", (0, 0, 0), z_axis, opening_diameter=float(derived["air_opening_diameter"])),
        ]
        for index, (x, y) in enumerate(((-pitch / 2, -pitch / 2), (-pitch / 2, pitch / 2), (pitch / 2, -pitch / 2), (pitch / 2, pitch / 2)), 1):
            interfaces.append(_interface(f"mount_hole_{index}", "clearance_hole", "fan mounting", (x, y, 0), z_axis, diameter=float(derived["mount_hole_diameter"])))
        return interfaces

    if family == "hardware.leveling_foot":
        return [
            _interface("floor_contact", "planar_face", "machine support datum", (0, 0, 0), minus_z, diameter=float(derived["foot_diameter"])),
            _interface("threaded_stem", "male_thread_envelope", "attach to machine frame", (0, 0, float(derived["foot_height"])), z_axis, nominal_diameter=float(derived["stem_diameter"]), length=float(derived["stem_length"])),
            _interface("adjustment_axis", "axis", "height adjustment", (0, 0, 0), z_axis),
        ]

    if family == "hardware.caster":
        interfaces = [
            _interface("floor_contact", "wheel_contact", "floor datum", (0, 0, 0), minus_z, wheel_diameter=float(derived["wheel_diameter"]), wheel_width=float(derived["wheel_width"])),
            _interface("wheel_axis", "rotation_axis", "rolling direction", (0, 0, float(derived["wheel_diameter"]) / 2), (0.0, 1.0, 0.0)),
        ]
        if derived["mount"] == "plate":
            interfaces.append(_interface("mounting_plate", "rectangular_plate", "machine attachment", (0, 0, float(derived["overall_height"])), z_axis, size_x=float(derived["plate_size_x"]), size_y=float(derived["plate_size_y"]), hole_pitch_x=float(derived["mount_hole_pitch_x"]), hole_pitch_y=float(derived["mount_hole_pitch_y"]), hole_diameter=float(derived["mount_hole_diameter"]), hole_count=4))
        else:
            interfaces.append(_interface("mounting_stem", "male_thread_envelope", "machine attachment", (0, 0, float(derived["overall_height"])), z_axis, nominal_diameter=float(derived["stem_diameter"])))
        if derived["swivel"]:
            interfaces.append(_interface("swivel_axis", "rotation_axis", "caster steering", (0, 0, float(derived["overall_height"])), z_axis))
        return interfaces

    return []
