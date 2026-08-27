"""Metric fastener envelopes for layout, assembly and BOM workflows."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from build123d import Align, BuildPart, BuildSketch, Cylinder, Mode, Part, Pos, RegularPolygon, extrude

from .catalog import register
from .errors import InvalidParameterError
from .models import FamilyDefinition, ParameterSpec, StandardReference


GB_T_5783_2025 = StandardReference(
    system="GB/T",
    designation="GB/T 5783-2025",
    title="紧固件 六角头螺栓 全螺纹",
    edition="2025",
    status="current",
    url="https://openstd.samr.gov.cn/bzgk/std/nd?no=2561",
    relationship="family-and-nominal-envelope",
    note="Effective 2026-02-01; this model omits thread helices, tolerances, chamfers and product grades.",
)

ISO_4017_2022 = StandardReference(
    system="ISO",
    designation="ISO 4017:2022",
    title="Fasteners — Hexagon head screws — Product grades A and B",
    edition="2022",
    status="current",
    url="https://www.iso.org/standard/72585.html",
    relationship="family-and-nominal-envelope",
    note="The shank is represented by the nominal major-diameter thread envelope.",
)

GB_T_6170_2015 = StandardReference(
    system="GB/T",
    designation="GB/T 6170-2015",
    title="1型六角螺母",
    edition="2015",
    status="current",
    url="https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=BDDE5AF77AC2FBC2D194289F10C69A4B",
    relationship="family-and-nominal-envelope",
    note="Internal threads, tolerances, chamfers and strength classes are out of scope.",
)

ISO_4032_2023 = StandardReference(
    system="ISO",
    designation="ISO 4032:2023",
    title="Fasteners — Hexagon regular nuts (style 1)",
    edition="2023",
    status="current",
    url="https://www.iso.org/standard/75016.html",
    relationship="family-and-nominal-envelope",
    note="This family covers the library's common coarse-pitch M5–M24 subset plus M3/M4 compatibility entries.",
)

GB_T_97_1_2002 = StandardReference(
    system="GB/T",
    designation="GB/T 97.1-2002",
    title="平垫圈 A级",
    edition="2002",
    status="current",
    url="https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=199E0585386FDF8B9CACF6225BA5F924",
    relationship="family-and-nominal-envelope",
    note="Ideal nominal washer with no tolerance, edge break, material or hardness claim.",
)

ISO_7089_2000 = StandardReference(
    system="ISO",
    designation="ISO 7089:2000",
    title="Plain washers — Normal series — Product grade A",
    edition="2000",
    status="current-confirmed-2021",
    url="https://www.iso.org/standard/13666.html",
    relationship="family-and-nominal-envelope",
    note="Nominal normal-series washer envelope only.",
)


@dataclass(frozen=True, slots=True)
class MetricFastenerDimensions:
    diameter: float
    coarse_pitch: float
    across_flats: float
    head_height: float
    nut_height: float
    washer_inside: float
    washer_outside: float
    washer_thickness: float


# Common coarse-pitch selection. Head values are nominal ISO 4017 envelopes;
# nut/washer values are nominal regular/normal-series catalog dimensions.
METRIC_FASTENERS: dict[str, MetricFastenerDimensions] = {
    "M3": MetricFastenerDimensions(3, 0.5, 5.5, 2.0, 2.4, 3.2, 7, 0.5),
    "M4": MetricFastenerDimensions(4, 0.7, 7, 2.8, 3.2, 4.3, 9, 0.8),
    "M5": MetricFastenerDimensions(5, 0.8, 8, 3.5, 4.7, 5.3, 10, 1.0),
    "M6": MetricFastenerDimensions(6, 1.0, 10, 4.0, 5.2, 6.4, 12, 1.6),
    "M8": MetricFastenerDimensions(8, 1.25, 13, 5.3, 6.8, 8.4, 16, 1.6),
    "M10": MetricFastenerDimensions(10, 1.5, 16, 6.4, 8.4, 10.5, 20, 2.0),
    "M12": MetricFastenerDimensions(12, 1.75, 18, 7.5, 10.8, 13, 24, 2.5),
    "M14": MetricFastenerDimensions(14, 2.0, 21, 8.8, 12.8, 15, 28, 2.5),
    "M16": MetricFastenerDimensions(16, 2.0, 24, 10.0, 14.8, 17, 30, 3.0),
    "M18": MetricFastenerDimensions(18, 2.5, 27, 11.5, 15.8, 19, 34, 3.0),
    "M20": MetricFastenerDimensions(20, 2.5, 30, 12.5, 18.0, 21, 37, 3.0),
    "M22": MetricFastenerDimensions(22, 2.5, 34, 14.0, 19.4, 23, 39, 3.0),
    "M24": MetricFastenerDimensions(24, 3.0, 36, 15.0, 21.5, 25, 44, 4.0),
}

_AXIAL_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


def _metric_size(size: str | int | float) -> tuple[str, MetricFastenerDimensions]:
    if isinstance(size, bool) or not isinstance(size, (str, int, float)):
        raise InvalidParameterError("size must be a metric designation such as 'M8' or 8")
    if isinstance(size, str):
        value = size.strip().upper()
        key = value if value.startswith("M") else f"M{value}"
    else:
        key = f"M{size:g}"
    if key not in METRIC_FASTENERS:
        available = ", ".join(METRIC_FASTENERS)
        raise InvalidParameterError(f"unsupported metric fastener size {key!r}; available: {available}")
    return key, METRIC_FASTENERS[key]


def _positive_length(length: float) -> float:
    if isinstance(length, bool) or not isinstance(length, (int, float)):
        raise InvalidParameterError("length must be a real number")
    if length <= 0:
        raise InvalidParameterError("length must be > 0")
    return float(length)


def _hex_prism(across_flats: float, height: float) -> Part:
    # RegularPolygon uses a circumradius; s = 2 R cos(30°) = sqrt(3) R.
    with BuildPart() as prism:
        with BuildSketch():
            RegularPolygon(across_flats / sqrt(3), 6, rotation=30)
        extrude(amount=height)
    return prism.part


def hex_bolt_metric_dimensions(size: str | int | float, length: float) -> dict[str, str | float]:
    """Return nominal metric hex-head screw envelope dimensions."""

    key, dimensions = _metric_size(size)
    nominal_length = _positive_length(length)
    return {
        "fastener_type": "metric_hex_head_fully_threaded",
        "designation": f"{key}x{nominal_length:g}",
        "size": key,
        "nominal_diameter": dimensions.diameter,
        "coarse_pitch": dimensions.coarse_pitch,
        "across_flats": dimensions.across_flats,
        "head_height": dimensions.head_height,
        "nominal_length_below_head": nominal_length,
        "total_height": dimensions.head_height + nominal_length,
        "thread_geometry": "smooth nominal major-diameter envelope",
        "unit": "mm",
    }


def hex_nut_metric_dimensions(size: str | int | float) -> dict[str, str | float]:
    """Return nominal regular hex-nut envelope dimensions."""

    key, dimensions = _metric_size(size)
    return {
        "fastener_type": "metric_regular_hex_nut",
        "designation": key,
        "size": key,
        "nominal_thread_diameter": dimensions.diameter,
        "coarse_pitch": dimensions.coarse_pitch,
        "across_flats": dimensions.across_flats,
        "height": dimensions.nut_height,
        "thread_geometry": "cylindrical nominal-diameter envelope",
        "unit": "mm",
    }


def plain_washer_metric_dimensions(size: str | int | float) -> dict[str, str | float]:
    """Return nominal normal-series plain-washer envelope dimensions."""

    key, dimensions = _metric_size(size)
    return {
        "fastener_type": "metric_plain_washer_normal_series",
        "designation": key,
        "size": key,
        "inside_diameter": dimensions.washer_inside,
        "outside_diameter": dimensions.washer_outside,
        "thickness": dimensions.washer_thickness,
        "unit": "mm",
    }


def hex_bolt_metric(size: str | int | float, length: float) -> Part:
    """Create a fully-threaded metric hex-head screw envelope along +Z.

    The head occupies Z=0..k and the nominal thread envelope Z=k..k+length.
    No helical thread is generated, keeping assemblies light and deterministic.
    """

    derived = hex_bolt_metric_dimensions(size, length)
    key, dimensions = _metric_size(str(derived["size"]))
    nominal_length = float(derived["nominal_length_below_head"])
    head = _hex_prism(dimensions.across_flats, dimensions.head_height)
    shank = Pos(0, 0, dimensions.head_height) * Cylinder(
        dimensions.diameter / 2,
        nominal_length,
        align=_AXIAL_MIN,
    )
    result = head + shank
    result.label = f"{key}x{nominal_length:g} hex bolt (thread envelope)"
    return result


def hex_nut_metric(size: str | int | float) -> Part:
    """Create a regular style-1 metric hex nut envelope on the XY plane."""

    key, dimensions = _metric_size(size)
    body = _hex_prism(dimensions.across_flats, dimensions.nut_height)
    bore = Cylinder(dimensions.diameter / 2, dimensions.nut_height, align=_AXIAL_MIN)
    result = (body - bore).solid()
    result.label = f"{key} hex nut (thread envelope)"
    return result


def plain_washer_metric(size: str | int | float) -> Part:
    """Create a normal-series metric plain washer envelope on the XY plane."""

    key, dimensions = _metric_size(size)
    outside = Cylinder(dimensions.washer_outside / 2, dimensions.washer_thickness, align=_AXIAL_MIN)
    inside = Cylinder(dimensions.washer_inside / 2, dimensions.washer_thickness, align=_AXIAL_MIN)
    result = (outside - inside).solid()
    result.label = f"{key} plain washer"
    return result


_SIZE_PARAMETER = ParameterSpec(
    "size",
    "string|number",
    "Metric nominal thread designation",
    choices=tuple(METRIC_FASTENERS),
)

register(
    FamilyDefinition(
        key="fastener.hex_bolt_metric",
        category="fastener",
        title="Metric hex-head screw / 公制六角头全螺纹螺栓",
        description="Lightweight nominal head and major-diameter thread envelope for assemblies and BOMs.",
        factory=hex_bolt_metric,
        derive=hex_bolt_metric_dimensions,
        parameters=(
            _SIZE_PARAMETER,
            ParameterSpec("length", "number", "Nominal length below the head", "mm", minimum=0.0),
        ),
        standards=(GB_T_5783_2025, ISO_4017_2022),
        aliases=("hex_bolt", "metric_hex_bolt"),
        orientation="axis +Z; head lower face on XY; nominal length starts below head",
        detail="simplified thread envelope",
        validation="size table, head/shank bbox, total height, solid and STEP export tested",
        example="create('fastener.hex_bolt_metric', size='M8', length=30)",
        notes=("A smooth cylinder represents the external thread's nominal major-diameter envelope.",),
    )
)

register(
    FamilyDefinition(
        key="fastener.hex_nut_metric",
        category="fastener",
        title="Metric regular hex nut / 公制1型六角螺母",
        description="Regular hex-nut nominal envelope with a cylindrical thread envelope bore.",
        factory=hex_nut_metric,
        derive=hex_nut_metric_dimensions,
        parameters=(_SIZE_PARAMETER,),
        standards=(GB_T_6170_2015, ISO_4032_2023),
        aliases=("hex_nut", "metric_hex_nut"),
        orientation="axis +Z; lower face on XY",
        detail="simplified thread envelope",
        validation="size table, across-flats envelope, height, bore, solid and STEP export tested",
        example="create('fastener.hex_nut_metric', size='M8')",
        notes=("The through-cylinder is an assembly envelope, not a modeled internal thread profile.",),
    )
)

register(
    FamilyDefinition(
        key="fastener.plain_washer_metric",
        category="fastener",
        title="Metric normal-series plain washer / 公制A级平垫圈",
        description="Nominal washer inside diameter, outside diameter and thickness envelope.",
        factory=plain_washer_metric,
        derive=plain_washer_metric_dimensions,
        parameters=(_SIZE_PARAMETER,),
        standards=(GB_T_97_1_2002, ISO_7089_2000),
        aliases=("plain_washer", "metric_washer"),
        orientation="axis +Z; lower face on XY",
        detail="nominal envelope",
        validation="size table, d1/d2/s bbox, bore, solid and STEP export tested",
        example="create('fastener.plain_washer_metric', size='M8')",
        notes=("Chamfers, edge breaks, tolerance, material and hardness are intentionally omitted.",),
    )
)
