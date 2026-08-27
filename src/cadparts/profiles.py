"""Structural profile families."""

from __future__ import annotations

from math import pi

from build123d import Align, BuildPart, BuildSketch, Cylinder, Mode, Part, Rectangle, RectangleRounded, extrude

from .catalog import register
from .errors import InvalidParameterError
from .models import FamilyDefinition, ParameterSpec, StandardReference


GB_T_6728_2025 = StandardReference(
    system="GB/T",
    designation="GB/T 6728-2025",
    title="结构用冷弯型钢",
    edition="2025",
    status="current",
    url="https://openstd.samr.gov.cn/bzgk/std/showGb?hcno=D2862F3B35CBDC75C7262BEAEE5B47FD&request_locale=zh&type=online",
    relationship="nominal-envelope",
    note="The factory models ideal nominal geometry; material, mass and tolerances are out of scope.",
)

ASTM_A500_2023 = StandardReference(
    system="ASTM",
    designation="ASTM A500/A500M-23",
    title="Cold-Formed Welded and Seamless Carbon Steel Structural Tubing in Rounds and Shapes",
    edition="2023",
    status="current",
    url="https://store.astm.org/a0500_a0500m-23.html",
    relationship="nominal-envelope",
    note="The factory models geometry only and does not assert grade or mechanical properties.",
)

GB_T_706_2016 = StandardReference(
    system="GB/T",
    designation="GB/T 706-2016",
    title="热轧型钢",
    edition="2016",
    status="current",
    url="https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=80EC2383403568E9F0F850B044C0DC5F",
    relationship="shape-family-only",
    note="The factory takes explicit nominal leg and thickness inputs; it does not claim a catalog designation or rolling tolerance.",
)

_AXIAL_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


def square_tube_dimensions(
    side: float,
    wall: float,
    length: float,
    *,
    corner_radius: float = 0.0,
) -> dict[str, str | float]:
    """Validate and calculate ideal nominal SHS dimensions without geometry."""

    values = {"side": side, "wall": wall, "length": length, "corner_radius": corner_radius}
    for name, value in values.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise InvalidParameterError(f"{name} must be a real number")
    if side <= 0:
        raise InvalidParameterError("side must be > 0")
    if length <= 0:
        raise InvalidParameterError("length must be > 0")
    if wall <= 0 or wall * 2 >= side:
        raise InvalidParameterError("wall must satisfy 0 < 2*wall < side")
    if corner_radius < 0:
        raise InvalidParameterError("corner_radius must be >= 0")
    if corner_radius > side / 2:
        raise InvalidParameterError("corner_radius must be <= side/2")
    inner_side = side - wall * 2
    sharp_area = side**2 - inner_side**2
    return {
        "profile_type": "square_hollow_section",
        "outside_side": float(side),
        "inside_side": float(inner_side),
        "wall": float(wall),
        "length": float(length),
        "outside_corner_radius": float(corner_radius),
        "inside_corner_radius": float(max(corner_radius - wall, 0.0)),
        "sharp_corner_cross_section_area": float(sharp_area),
        "sharp_corner_volume": float(sharp_area * length),
        "unit": "mm",
    }


def square_tube(
    side: float,
    wall: float,
    length: float,
    *,
    corner_radius: float = 0.0,
) -> Part:
    """Create an ideal square hollow section along +Z.

    ``corner_radius=0`` is the default simplified interference envelope. A
    positive radius uses an inside radius of ``max(corner_radius - wall, 0)``
    to preserve the nominal wall offset around the corners.
    """

    derived = square_tube_dimensions(side, wall, length, corner_radius=corner_radius)
    inner_side = float(derived["inside_side"])
    inner_radius = float(derived["inside_corner_radius"])
    with BuildPart() as tube:
        with BuildSketch():
            if corner_radius > 0:
                RectangleRounded(side, side, corner_radius)
            else:
                Rectangle(side, side)
            if inner_radius > 0:
                RectangleRounded(inner_side, inner_side, inner_radius, mode=Mode.SUBTRACT)
            else:
                Rectangle(inner_side, inner_side, mode=Mode.SUBTRACT)
        extrude(amount=length)
    result = tube.part

    result.label = f"SHS {side:g}x{side:g}x{wall:g} L={length:g}"
    return result


def round_tube_dimensions(outer_diameter: float, wall: float, length: float) -> dict[str, str | float]:
    """Validate and calculate ideal circular hollow-section dimensions."""

    values = {"outer_diameter": outer_diameter, "wall": wall, "length": length}
    for name, value in values.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise InvalidParameterError(f"{name} must be a real number")
    if outer_diameter <= 0:
        raise InvalidParameterError("outer_diameter must be > 0")
    if wall <= 0 or wall * 2 >= outer_diameter:
        raise InvalidParameterError("wall must satisfy 0 < 2*wall < outer_diameter")
    if length <= 0:
        raise InvalidParameterError("length must be > 0")
    inside = outer_diameter - wall * 2
    area = pi * (outer_diameter**2 - inside**2) / 4
    return {
        "profile_type": "circular_hollow_section",
        "outside_diameter": float(outer_diameter),
        "inside_diameter": float(inside),
        "wall": float(wall),
        "length": float(length),
        "cross_section_area": area,
        "volume": area * length,
        "unit": "mm",
    }


def round_tube(outer_diameter: float, wall: float, length: float) -> Part:
    """Create an ideal circular hollow section along +Z."""

    dimensions = round_tube_dimensions(outer_diameter, wall, length)
    outside = Cylinder(float(dimensions["outside_diameter"]) / 2, length, align=_AXIAL_MIN)
    inside = Cylinder(float(dimensions["inside_diameter"]) / 2, length, align=_AXIAL_MIN)
    result = (outside - inside).solid()
    result.label = f"CHS OD{outer_diameter:g}x{wall:g} L={length:g}"
    return result


def round_rod_dimensions(diameter: float, length: float) -> dict[str, str | float]:
    """Validate and calculate an ideal solid round-bar envelope."""

    for name, value in {"diameter": diameter, "length": length}.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise InvalidParameterError(f"{name} must be a real number")
        if value <= 0:
            raise InvalidParameterError(f"{name} must be > 0")
    area = pi * diameter**2 / 4
    return {
        "profile_type": "solid_round_bar",
        "diameter": float(diameter),
        "length": float(length),
        "cross_section_area": area,
        "volume": area * length,
        "unit": "mm",
    }


def round_rod(diameter: float, length: float) -> Part:
    """Create an ideal solid circular bar along +Z."""

    round_rod_dimensions(diameter, length)
    result = Cylinder(diameter / 2, length, align=_AXIAL_MIN)
    result.label = f"Round rod D{diameter:g} L={length:g}"
    return result


def equal_angle_dimensions(leg: float, thickness: float, length: float) -> dict[str, str | float]:
    """Validate and calculate a sharp-corner equal-angle envelope."""

    for name, value in {"leg": leg, "thickness": thickness, "length": length}.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise InvalidParameterError(f"{name} must be a real number")
    if leg <= 0:
        raise InvalidParameterError("leg must be > 0")
    if thickness <= 0 or thickness >= leg:
        raise InvalidParameterError("thickness must satisfy 0 < thickness < leg")
    if length <= 0:
        raise InvalidParameterError("length must be > 0")
    area = 2 * leg * thickness - thickness**2
    return {
        "profile_type": "equal_angle_sharp_envelope",
        "leg": float(leg),
        "thickness": float(thickness),
        "length": float(length),
        "cross_section_area": float(area),
        "volume": float(area * length),
        "root_and_toe_radii": "omitted",
        "unit": "mm",
    }


def equal_angle(leg: float, thickness: float, length: float) -> Part:
    """Create a simplified equal-leg L section in the +X/+Y quadrant."""

    equal_angle_dimensions(leg, thickness, length)
    with BuildPart() as angle:
        with BuildSketch():
            Rectangle(leg, thickness, align=(Align.MIN, Align.MIN))
            Rectangle(thickness, leg, align=(Align.MIN, Align.MIN))
        extrude(amount=length)
    result = angle.part
    result.label = f"Equal angle L{leg:g}x{leg:g}x{thickness:g} L={length:g}"
    return result


register(
    FamilyDefinition(
        key="profile.square_tube",
        category="profile",
        title="Square hollow section / 方管",
        description="Ideal nominal square structural tube for layout, interference and BOM geometry.",
        factory=square_tube,
        derive=square_tube_dimensions,
        parameters=(
            ParameterSpec("side", "number", "Outside side length", "mm", minimum=0.0),
            ParameterSpec("wall", "number", "Nominal wall thickness", "mm", minimum=0.0),
            ParameterSpec("length", "number", "Extrusion length along +Z", "mm", minimum=0.0),
            ParameterSpec(
                "corner_radius",
                "number",
                "Optional outside corner radius; 0 keeps the simplified sharp envelope",
                "mm",
                required=False,
                default=0.0,
                minimum=0.0,
            ),
        ),
        standards=(GB_T_6728_2025, ASTM_A500_2023),
        aliases=("square_tube", "shs"),
        orientation="cross-section centered on XY; length along +Z",
        detail="simplified by default",
        validation="bbox, volume, bore continuity and STEP export tested",
        example="create('profile.square_tube', side=40, wall=3, length=1000)",
        notes=(
            "Nominal geometry is not a certification of standard compliance.",
            "corner_radius=0 is deliberate: outside envelope and wall volume remain deterministic.",
        ),
    )
)

register(
    FamilyDefinition(
        key="profile.round_tube",
        category="profile",
        title="Circular hollow section / 圆管",
        description="Ideal nominal circular tube for layout, mass-property estimates and interference geometry.",
        factory=round_tube,
        derive=round_tube_dimensions,
        parameters=(
            ParameterSpec("outer_diameter", "number", "Outside diameter", "mm", minimum=0.0),
            ParameterSpec("wall", "number", "Nominal wall thickness", "mm", minimum=0.0),
            ParameterSpec("length", "number", "Length along +Z", "mm", minimum=0.0),
        ),
        standards=(GB_T_6728_2025, ASTM_A500_2023),
        aliases=("round_tube", "chs"),
        orientation="axis +Z; lower face on XY",
        detail="nominal envelope",
        validation="bbox, analytical volume, bore, solid and STEP export tested",
        example="create('profile.round_tube', outer_diameter=48.3, wall=3.2, length=1000)",
        notes=("Material grade, weld seam, ovality and tolerances are out of scope.",),
    )
)

register(
    FamilyDefinition(
        key="profile.round_rod",
        category="profile",
        title="Solid round bar / 圆棒",
        description="Generic explicit-diameter solid round-bar envelope.",
        factory=round_rod,
        derive=round_rod_dimensions,
        parameters=(
            ParameterSpec("diameter", "number", "Nominal diameter", "mm", minimum=0.0),
            ParameterSpec("length", "number", "Length along +Z", "mm", minimum=0.0),
        ),
        aliases=("round_rod", "rod"),
        orientation="axis +Z; lower face on XY",
        detail="generic nominal envelope",
        validation="bbox, analytical volume, solid and STEP export tested",
        example="create('profile.round_rod', diameter=20, length=500)",
        notes=("This is a generic geometry family; select material and dimensional tolerance separately.",),
    )
)

register(
    FamilyDefinition(
        key="profile.equal_angle",
        category="profile",
        title="Equal-leg angle / 等边角钢",
        description="Sharp-corner equal angle with explicit nominal leg and thickness inputs.",
        factory=equal_angle,
        derive=equal_angle_dimensions,
        parameters=(
            ParameterSpec("leg", "number", "Equal outside leg length", "mm", minimum=0.0),
            ParameterSpec("thickness", "number", "Nominal leg thickness", "mm", minimum=0.0),
            ParameterSpec("length", "number", "Length along +Z", "mm", minimum=0.0),
        ),
        standards=(GB_T_706_2016,),
        aliases=("equal_angle", "angle_steel"),
        orientation="cross-section in +X/+Y quadrant; length along +Z",
        detail="simplified sharp-corner envelope",
        validation="bbox, analytical area/volume, one solid and STEP export tested",
        example="create('profile.equal_angle', leg=50, thickness=5, length=1000)",
        notes=("Rolling root/toe radii and catalog mass are omitted; do not use this envelope as a rolling drawing.",),
    )
)
