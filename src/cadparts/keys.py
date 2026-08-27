"""Parallel-key families."""

from __future__ import annotations

from math import pi

from build123d import Align, Box, Cylinder, Part, Pos

from .catalog import register
from .errors import InvalidParameterError
from .models import FamilyDefinition, ParameterSpec, StandardReference


GB_T_1096_2003 = StandardReference(
    system="GB/T",
    designation="GB/T 1096-2003",
    title="普通型 平键",
    edition="2003",
    status="current",
    url="https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=AF989792A444C725A4F3FFB90F183772",
    relationship="shape-family",
    note="The caller supplies b, h and length explicitly; fits, keyway depths and tolerances are not modeled.",
)

ASME_B17_1_1967 = StandardReference(
    system="ASME",
    designation="ASME B17.1-1967 (S2023)",
    title="Keys and Keyseats",
    edition="1967 stabilized 2023",
    status="current-stabilized",
    url="https://www.asme.org/codes-standards/find-codes-standards/b17-1-keys-keyseats",
    relationship="shape-family-cross-reference",
    note="This metric explicit-size model does not reproduce ASME inch tables or tolerances.",
)

_AXIAL_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


def parallel_key_dimensions(
    width: float,
    height: float,
    length: float,
    *,
    end_type: str = "A",
) -> dict[str, str | float]:
    """Validate an explicit-size ordinary parallel key."""

    for name, value in {"width": width, "height": height, "length": length}.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise InvalidParameterError(f"{name} must be a real number")
        if value <= 0:
            raise InvalidParameterError(f"{name} must be > 0")
    normalized_type = end_type.strip().upper() if isinstance(end_type, str) else ""
    if normalized_type not in {"A", "B", "C"}:
        raise InvalidParameterError("end_type must be 'A', 'B' or 'C'")
    minimum_length = width if normalized_type == "A" else width / 2 if normalized_type == "C" else 0
    if length < minimum_length:
        raise InvalidParameterError(f"length must be >= {minimum_length:g} for end_type {normalized_type}")
    plan_area = (
        width * (length - width) + pi * width**2 / 4
        if normalized_type == "A"
        else width * length
        if normalized_type == "B"
        else width * (length - width / 2) + pi * width**2 / 8
    )
    return {
        "key_type": f"parallel_{normalized_type}",
        "width": float(width),
        "height": float(height),
        "length": float(length),
        "end_type": normalized_type,
        "plan_area": float(plan_area),
        "volume": float(plan_area * height),
        "unit": "mm",
    }


def parallel_key(
    width: float,
    height: float,
    length: float,
    *,
    end_type: str = "A",
) -> Part:
    """Create a type A (round/round), B (square/square), or C key."""

    dimensions = parallel_key_dimensions(width, height, length, end_type=end_type)
    normalized_type = str(dimensions["end_type"])
    if normalized_type == "B":
        result = Box(length, width, height, align=(Align.MIN, Align.CENTER, Align.MIN))
    elif normalized_type == "A":
        first_end = Pos(width / 2, 0, 0) * Cylinder(width / 2, height, align=_AXIAL_MIN)
        if length == width:
            result = first_end
        else:
            center = Pos(width / 2, 0, 0) * Box(
                length - width,
                width,
                height,
                align=(Align.MIN, Align.CENTER, Align.MIN),
            )
            second_end = Pos(length - width / 2, 0, 0) * Cylinder(width / 2, height, align=_AXIAL_MIN)
            result = (center + first_end + second_end).solid()
    else:
        rounded_end = Pos(length - width / 2, 0, 0) * Cylinder(width / 2, height, align=_AXIAL_MIN)
        if length == width / 2:
            clip = Box(width / 2, width, height, align=(Align.MIN, Align.CENTER, Align.MIN))
            result = (rounded_end & clip).solid()
        else:
            body = Box(length - width / 2, width, height, align=(Align.MIN, Align.CENTER, Align.MIN))
            result = (body + rounded_end).solid()
    result.label = f"Parallel key {width:g}x{height:g}x{length:g} type {normalized_type}"
    return result


register(
    FamilyDefinition(
        key="key.parallel",
        category="key",
        title="Ordinary parallel key / 普通型平键",
        description="Explicit b×h×L parallel key with selectable standard end form.",
        factory=parallel_key,
        derive=parallel_key_dimensions,
        parameters=(
            ParameterSpec("width", "number", "Nominal key width b", "mm", minimum=0.0),
            ParameterSpec("height", "number", "Nominal key height h", "mm", minimum=0.0),
            ParameterSpec("length", "number", "Overall key length L", "mm", minimum=0.0),
            ParameterSpec(
                "end_type",
                "string",
                "A round/round, B square/square, C square/round",
                required=False,
                default="A",
                choices=("A", "B", "C"),
            ),
        ),
        standards=(GB_T_1096_2003, ASME_B17_1_1967),
        aliases=("parallel_key",),
        orientation="length +X; width centered on Y; height +Z",
        detail="nominal solid key; keyway omitted",
        validation="end form, bbox, analytical volume, one solid and STEP export tested",
        example="create('key.parallel', width=8, height=7, length=32, end_type='A')",
        notes=(
            "Width and height are explicit to prevent the model from guessing a shaft-to-key selection table.",
            "Fits, shaft/hub keyways, chamfers, tolerances and material are out of scope.",
        ),
    )
)
