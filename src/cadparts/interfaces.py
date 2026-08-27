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

    return []
