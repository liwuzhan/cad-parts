"""Parametric involute gear families."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import atan, atan2, cos, degrees, isfinite, pi, radians, sin, sqrt, tan

from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Circle,
    Cylinder,
    Mode,
    Part,
    Plane,
    Polygon,
    extrude,
    loft,
)

from .catalog import register
from .errors import InvalidParameterError
from .models import FamilyDefinition, ParameterSpec, StandardReference


GB_T_1356_2001 = StandardReference(
    system="GB/T",
    designation="GB/T 1356-2001",
    title="通用机械和重型机械用圆柱齿轮 标准基本齿条齿廓",
    edition="2001",
    status="current",
    url="https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=7D44A15888B2E686063491408AB63CC8",
    relationship="basic-rack-basis",
    note="The library implements a 20-degree full-depth reference profile by default; rating and tolerance are out of scope.",
)

ISO_53_1998 = StandardReference(
    system="ISO",
    designation="ISO 53:1998",
    title="Cylindrical gears for general and heavy engineering — Standard basic rack tooth profile",
    edition="1998",
    status="current-confirmed-2026",
    url="https://www.iso.org/standard/22643.html",
    relationship="basic-rack-basis",
    note="The generated working flanks are involutes; the root transition is a deterministic radial approximation, not a hob trochoid.",
)

AGMA_1003_H07 = StandardReference(
    system="AGMA",
    designation="ANSI/AGMA 1003-H07",
    title="Tooth Proportions for Fine-Pitch Spur and Helical Gearing",
    edition="H07",
    status="published",
    url="https://members.agma.org/ItemDetail?Category=STANDARDS&WebsiteKey=1fa29655-e8c0-41f6-b6a8-418a374ae587&iProductCode=1003_H07",
    relationship="conditional-scope-cross-reference",
    note="Applies only to 20–120 diametral pitch and 20-degree profiles; inclusion does not make arbitrary module inputs AGMA-compliant.",
)

GB_T_12369_1990 = StandardReference(
    system="GB/T",
    designation="GB/T 12369-1990",
    title="直齿及斜齿锥齿轮基本齿廓",
    edition="1990",
    status="current",
    url="https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=27174F3824CCFC3370B47C1DA0B89314",
    relationship="basic-profile-and-terminology-basis",
    note="The generated solid is a layout loft, not a production tooth-surface implementation of the standard.",
)

ISO_23509_1_2025 = StandardReference(
    system="ISO",
    designation="ISO 23509-1:2025",
    title="Bevel and hypoid gear geometry — Part 1: Basic methods",
    edition="2025",
    status="current",
    url="https://www.iso.org/standard/85503.html",
    relationship="macro-geometry-basis",
    note="Pitch-cone angles and cone distance follow standard macro-geometry relationships; detailed flank generation is out of scope.",
)

AGMA_ISO_23509_B17 = StandardReference(
    system="AGMA",
    designation="ANSI/AGMA ISO 23509-B17",
    title="Bevel and Hypoid Gear Geometry",
    edition="B17",
    status="published",
    url="https://members.agma.org/MyAGMA/MyAGMA/Store/Item_Detail.aspx?Category=STANDARDS&iProductCode=23509_B17",
    relationship="macro-geometry-cross-reference",
    note="The library does not claim AGMA accuracy, rating or manufacturing compliance.",
)


@dataclass(frozen=True, slots=True)
class SpurGearDimensions:
    gear_type: str
    module: float
    teeth: int
    pressure_angle_deg: float
    profile_shift: float
    bore_diameter: float
    face_width: float
    pitch_diameter: float
    base_diameter: float
    outside_diameter: float
    root_diameter: float
    circular_pitch: float
    tooth_thickness_at_pitch: float
    reference_center_distance_to_identical: float
    undercut_guidance: str
    unit: str = "mm"

    def to_dict(self) -> dict[str, str | float | int]:
        return asdict(self)


def _real(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise InvalidParameterError(f"{name} must be a finite real number")
    return float(value)


def spur_gear_dimensions(
    module: float,
    teeth: int,
    bore: float,
    width: float,
    *,
    pressure_angle: float = 20.0,
    profile_shift: float = 0.0,
) -> dict[str, str | float | int]:
    """Calculate nominal reference dimensions for one external spur gear."""

    nominal_module = _real("module", module)
    bore_diameter = _real("bore", bore)
    face_width = _real("width", width)
    angle_degrees = _real("pressure_angle", pressure_angle)
    shift = _real("profile_shift", profile_shift)
    if isinstance(teeth, bool) or not isinstance(teeth, int):
        raise InvalidParameterError("teeth must be an integer")
    if nominal_module <= 0:
        raise InvalidParameterError("module must be > 0")
    if teeth < 8:
        raise InvalidParameterError("teeth must be >= 8")
    if bore_diameter < 0:
        raise InvalidParameterError("bore must be >= 0")
    if face_width <= 0:
        raise InvalidParameterError("width must be > 0")
    if not 14.5 <= angle_degrees <= 30:
        raise InvalidParameterError("pressure_angle must be between 14.5 and 30 degrees")
    if not -0.5 <= shift <= 1.0:
        raise InvalidParameterError("profile_shift must be between -0.5 and 1.0")

    angle = radians(angle_degrees)
    pitch_diameter = nominal_module * teeth
    base_diameter = pitch_diameter * cos(angle)
    outside_diameter = nominal_module * (teeth + 2 + 2 * shift)
    root_diameter = nominal_module * (teeth - 2.5 + 2 * shift)
    if root_diameter <= 0:
        raise InvalidParameterError("parameters produce a non-positive root diameter")
    if bore_diameter >= root_diameter:
        raise InvalidParameterError(f"bore must be smaller than root diameter {root_diameter:g} mm")

    dimensions = SpurGearDimensions(
        gear_type="external_spur_involute",
        module=nominal_module,
        teeth=teeth,
        pressure_angle_deg=angle_degrees,
        profile_shift=shift,
        bore_diameter=bore_diameter,
        face_width=face_width,
        pitch_diameter=pitch_diameter,
        base_diameter=base_diameter,
        outside_diameter=outside_diameter,
        root_diameter=root_diameter,
        circular_pitch=pi * nominal_module,
        tooth_thickness_at_pitch=(pi * nominal_module / 2) + 2 * shift * nominal_module * tan(angle),
        reference_center_distance_to_identical=pitch_diameter,
        undercut_guidance=(
            "Below 17 teeth at 20 degrees and zero profile shift, a generated production tooth normally needs undercut analysis; "
            "this model keeps exact involute working flanks but approximates the root transition."
            if teeth < 17 and abs(angle_degrees - 20) < 1e-9 and abs(shift) < 1e-9
            else "Check undercut, contact ratio, backlash and strength for the intended mating gear and process."
        ),
    )
    return dimensions.to_dict()


def _involute_value(parameter: float) -> float:
    return parameter - atan(parameter)


def _gear_outline(
    dimensions: dict[str, str | float | int],
    *,
    flank_samples: int = 12,
) -> list[tuple[float, float]]:
    """Return a counter-clockwise sampled external gear boundary."""

    teeth = int(dimensions["teeth"])
    angle = radians(float(dimensions["pressure_angle_deg"]))
    shift = float(dimensions["profile_shift"])
    base_radius = float(dimensions["base_diameter"]) / 2
    outside_radius = float(dimensions["outside_diameter"]) / 2
    root_radius = float(dimensions["root_diameter"]) / 2

    half_thickness_angle = pi / (2 * teeth) + 2 * shift * tan(angle) / teeth
    base_rotation = half_thickness_angle + _involute_value(tan(angle))
    involute_start_radius = max(base_radius, root_radius)
    start_parameter = sqrt(max((involute_start_radius / base_radius) ** 2 - 1, 0))
    tip_parameter = sqrt((outside_radius / base_radius) ** 2 - 1)
    start_half_angle = base_rotation - _involute_value(start_parameter)
    tip_half_angle = base_rotation - _involute_value(tip_parameter)
    angular_pitch = 2 * pi / teeth
    if tip_half_angle <= 0:
        raise InvalidParameterError("parameters produce zero or crossed top land; reduce profile shift or pressure angle")
    if 2 * start_half_angle >= angular_pitch:
        raise InvalidParameterError("parameters produce overlapping tooth roots")

    points: list[tuple[float, float]] = []
    tip_arc_segments = 4
    root_arc_segments = 4
    for tooth in range(teeth):
        center = tooth * angular_pitch
        points.append((
            root_radius * cos(center - start_half_angle),
            root_radius * sin(center - start_half_angle),
        ))

        for sample in range(flank_samples + 1):
            parameter = start_parameter + (tip_parameter - start_parameter) * sample / flank_samples
            radius = base_radius * sqrt(1 + parameter * parameter)
            polar = center - base_rotation + _involute_value(parameter)
            points.append((radius * cos(polar), radius * sin(polar)))

        for sample in range(1, tip_arc_segments + 1):
            polar = center - tip_half_angle + 2 * tip_half_angle * sample / tip_arc_segments
            points.append((outside_radius * cos(polar), outside_radius * sin(polar)))

        for sample in range(flank_samples, -1, -1):
            parameter = start_parameter + (tip_parameter - start_parameter) * sample / flank_samples
            radius = base_radius * sqrt(1 + parameter * parameter)
            polar = center + base_rotation - _involute_value(parameter)
            points.append((radius * cos(polar), radius * sin(polar)))

        points.append((
            root_radius * cos(center + start_half_angle),
            root_radius * sin(center + start_half_angle),
        ))

        root_gap = angular_pitch - 2 * start_half_angle
        for sample in range(1, root_arc_segments):
            polar = center + start_half_angle + root_gap * sample / root_arc_segments
            points.append((root_radius * cos(polar), root_radius * sin(polar)))
    return points


def spur_gear(
    module: float,
    teeth: int,
    bore: float,
    width: float,
    *,
    pressure_angle: float = 20.0,
    profile_shift: float = 0.0,
) -> Part:
    """Create an external spur gear with sampled true involute flanks.

    The reference plane is XY and face width extends along +Z. Tooth tips and
    root lands are circular. The short transition below the base circle is
    radial rather than a manufacturing-process-specific trochoidal fillet.
    """

    dimensions = spur_gear_dimensions(
        module,
        teeth,
        bore,
        width,
        pressure_angle=pressure_angle,
        profile_shift=profile_shift,
    )
    outline = _gear_outline(dimensions)
    with BuildPart() as gear:
        with BuildSketch():
            Polygon(*outline, align=None)
            if float(dimensions["bore_diameter"]) > 0:
                Circle(float(dimensions["bore_diameter"]) / 2, mode=Mode.SUBTRACT)
        extrude(amount=float(dimensions["face_width"]))
    result = gear.part
    result.label = (
        f"Spur gear m{float(dimensions['module']):g} z{dimensions['teeth']} "
        f"bore{float(dimensions['bore_diameter']):g} width{float(dimensions['face_width']):g}"
    )
    return result


def straight_bevel_gear_dimensions(
    module: float,
    teeth: int,
    mate_teeth: int,
    bore: float,
    face_width: float,
    *,
    shaft_angle: float = 90.0,
    pressure_angle: float = 20.0,
) -> dict[str, str | float | int]:
    """Derive the layout macro geometry for one straight bevel-gear member."""

    nominal_module = _real("module", module)
    bore_diameter = _real("bore", bore)
    width = _real("face_width", face_width)
    shaft_angle_degrees = _real("shaft_angle", shaft_angle)
    pressure_angle_degrees = _real("pressure_angle", pressure_angle)
    for name, value in (("teeth", teeth), ("mate_teeth", mate_teeth)):
        if isinstance(value, bool) or not isinstance(value, int):
            raise InvalidParameterError(f"{name} must be an integer")
        if value < 8:
            raise InvalidParameterError(f"{name} must be >= 8")
    if nominal_module <= 0:
        raise InvalidParameterError("module must be > 0")
    if bore_diameter < 0:
        raise InvalidParameterError("bore must be >= 0")
    if width <= 0:
        raise InvalidParameterError("face_width must be > 0")
    if not 10 <= shaft_angle_degrees <= 170:
        raise InvalidParameterError("shaft_angle must be between 10 and 170 degrees")
    if not 14.5 <= pressure_angle_degrees <= 30:
        raise InvalidParameterError("pressure_angle must be between 14.5 and 30 degrees")

    shaft_angle_radians = radians(shaft_angle_degrees)
    pitch_cone_angle = atan2(
        sin(shaft_angle_radians),
        mate_teeth / teeth + cos(shaft_angle_radians),
    )
    mate_pitch_cone_angle = shaft_angle_radians - pitch_cone_angle
    if pitch_cone_angle <= 0 or mate_pitch_cone_angle <= 0:
        raise InvalidParameterError("teeth ratio and shaft_angle do not produce positive pitch-cone angles")
    pitch_radius = nominal_module * teeth / 2
    cone_distance = pitch_radius / sin(pitch_cone_angle)
    maximum_recommended_width = cone_distance / 3
    if width > maximum_recommended_width:
        raise InvalidParameterError(
            f"face_width must be <= one third of cone distance ({maximum_recommended_width:g} mm)"
        )
    toe_scale = (cone_distance - width) / cone_distance
    toe_module = nominal_module * toe_scale
    axial_height = width * cos(pitch_cone_angle)
    if axial_height <= 1e-6:
        raise InvalidParameterError("pitch-cone angle is too close to 90 degrees for this axial layout model")
    heel_root_diameter = nominal_module * (teeth - 2.5)
    toe_root_diameter = heel_root_diameter * toe_scale
    if bore_diameter >= toe_root_diameter:
        raise InvalidParameterError(
            f"bore must be smaller than toe root diameter {toe_root_diameter:g} mm"
        )
    return {
        "gear_type": "straight_bevel_layout",
        "model_fidelity": "scaled-involute-section loft; assembly/layout only",
        "module_at_heel": nominal_module,
        "module_at_toe": toe_module,
        "teeth": teeth,
        "mate_teeth": mate_teeth,
        "shaft_angle_deg": shaft_angle_degrees,
        "pressure_angle_deg": pressure_angle_degrees,
        "pitch_cone_angle_deg": degrees(pitch_cone_angle),
        "mate_pitch_cone_angle_deg": degrees(mate_pitch_cone_angle),
        "cone_distance": cone_distance,
        "face_width_along_cone": width,
        "maximum_recommended_face_width": maximum_recommended_width,
        "axial_height": axial_height,
        "toe_scale": toe_scale,
        "heel_pitch_diameter": 2 * pitch_radius,
        "toe_pitch_diameter": 2 * pitch_radius * toe_scale,
        "model_heel_outside_diameter": nominal_module * (teeth + 2),
        "model_toe_outside_diameter": nominal_module * (teeth + 2) * toe_scale,
        "heel_root_diameter": heel_root_diameter,
        "toe_root_diameter": toe_root_diameter,
        "bore_diameter": bore_diameter,
        "unit": "mm",
        "manufacturing_warning": (
            "Not a generated spherical-involute production flank. Select manufacturing method, backlash, bearing pattern, "
            "accuracy, crowning and rating in dedicated bevel-gear design software before manufacture."
        ),
    }


def straight_bevel_gear(
    module: float,
    teeth: int,
    mate_teeth: int,
    bore: float,
    face_width: float,
    *,
    shaft_angle: float = 90.0,
    pressure_angle: float = 20.0,
) -> Part:
    """Create a straight-bevel assembly/layout model by lofting involute sections."""

    dimensions = straight_bevel_gear_dimensions(
        module,
        teeth,
        mate_teeth,
        bore,
        face_width,
        shaft_angle=shaft_angle,
        pressure_angle=pressure_angle,
    )
    heel_dimensions = spur_gear_dimensions(
        module,
        teeth,
        0,
        float(dimensions["axial_height"]),
        pressure_angle=pressure_angle,
    )
    heel_outline = _gear_outline(heel_dimensions)
    toe_scale = float(dimensions["toe_scale"])
    toe_outline = [(x * toe_scale, y * toe_scale) for x, y in heel_outline]
    axial_height = float(dimensions["axial_height"])
    with BuildPart() as bevel:
        with BuildSketch(Plane.XY):
            Polygon(*heel_outline, align=None)
        with BuildSketch(Plane.XY.offset(axial_height)):
            Polygon(*toe_outline, align=None)
        loft()
        if bore > 0:
            Cylinder(
                bore / 2,
                axial_height,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
    result = bevel.part
    result.label = (
        f"Straight bevel layout m{module:g} z{teeth}/{mate_teeth} "
        f"delta{float(dimensions['pitch_cone_angle_deg']):.3f}deg"
    )
    return result


register(
    FamilyDefinition(
        key="gear.spur",
        category="gear",
        title="External involute spur gear / 外啮合渐开线直齿轮",
        description="Parametric external spur gear with real involute working flanks and derived reference dimensions.",
        factory=spur_gear,
        derive=spur_gear_dimensions,
        parameters=(
            ParameterSpec("module", "number", "Normal metric module", "mm", minimum=0.0),
            ParameterSpec("teeth", "integer", "Number of teeth", minimum=8),
            ParameterSpec("bore", "number", "Central bore diameter; use 0 for solid", "mm", minimum=0.0),
            ParameterSpec("width", "number", "Face width along +Z", "mm", minimum=0.0),
            ParameterSpec(
                "pressure_angle",
                "number",
                "Reference pressure angle; 20 degrees is the standards-based default",
                "degree",
                required=False,
                default=20.0,
                minimum=14.5,
                maximum=30.0,
            ),
            ParameterSpec(
                "profile_shift",
                "number",
                "Profile-shift coefficient x",
                required=False,
                default=0.0,
                minimum=-0.5,
                maximum=1.0,
            ),
        ),
        standards=(GB_T_1356_2001, ISO_53_1998, AGMA_1003_H07),
        aliases=("spur_gear", "gear.spur_gear"),
        orientation="axis +Z; lower face on XY; one tooth centered on +X",
        detail="true sampled involute flanks; approximate root transition",
        validation="derived diameters, tooth periodicity, bbox, bore, monotonic volume, solid and STEP/PNG tested",
        example="create('gear.spur', module=2, teeth=24, bore=10, width=12)",
        notes=(
            "Use derive() first to obtain pitch/base/outside/root diameters and selection warnings.",
            "No backlash, crowning, tip relief, tolerance class, material, heat treatment or strength rating is implied.",
            "For low tooth counts, undercut and mating contact ratio require an engineering check.",
        ),
    )
)

register(
    FamilyDefinition(
        key="gear.bevel_straight",
        category="gear",
        title="Straight bevel gear layout / 直齿伞齿轮布局模型",
        description="Macro-geometry-driven straight bevel member with pitch-cone angles derived from ratio and shaft angle.",
        factory=straight_bevel_gear,
        derive=straight_bevel_gear_dimensions,
        parameters=(
            ParameterSpec("module", "number", "Outer/heel module", "mm", minimum=0.0),
            ParameterSpec("teeth", "integer", "This member's tooth count", minimum=8),
            ParameterSpec("mate_teeth", "integer", "Mating member's tooth count", minimum=8),
            ParameterSpec("bore", "number", "Cylindrical center bore diameter", "mm", minimum=0.0),
            ParameterSpec("face_width", "number", "Tooth face width measured along cone distance", "mm", minimum=0.0),
            ParameterSpec(
                "shaft_angle",
                "number",
                "Included angle between mating shaft axes",
                "degree",
                required=False,
                default=90.0,
                minimum=10.0,
                maximum=170.0,
            ),
            ParameterSpec(
                "pressure_angle",
                "number",
                "Reference pressure angle",
                "degree",
                required=False,
                default=20.0,
                minimum=14.5,
                maximum=30.0,
            ),
        ),
        standards=(GB_T_12369_1990, ISO_23509_1_2025, AGMA_ISO_23509_B17),
        aliases=("straight_bevel_gear", "bevel_gear"),
        orientation="axis +Z; heel at Z=0 and toe toward +Z; one tooth centered on +X",
        detail="assembly/layout loft, not a production flank",
        validation="ratio-derived cone angles, cone-width guard, bbox, bore, one solid and STEP/PNG tested",
        example=(
            "create('gear.bevel_straight', module=2, teeth=20, mate_teeth=40, "
            "bore=10, face_width=10, shaft_angle=90)"
        ),
        notes=(
            "derive() returns both pitch-cone angles, cone distance, toe scale and a manufacturing warning.",
            "The lofted sections are useful for space claims and visualization but are not spherical-involute generated flanks.",
            "Do not use for tooth contact, backlash, bearing pattern, cutting data or strength certification.",
        ),
    )
)
