"""Rolling-bearing families with exact nominal boundary envelopes."""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin

from build123d import Align, Compound, Cylinder, Part, Pos, Sphere

from .catalog import register
from .errors import InvalidParameterError
from .models import FamilyDefinition, ParameterSpec, StandardReference


GB_T_276_2013 = StandardReference(
    system="GB/T",
    designation="GB/T 276-2013",
    title="滚动轴承 深沟球轴承 外形尺寸",
    edition="2013",
    status="current",
    url="https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=E58A2862B90502BB3A7EF18F835504BD",
    relationship="governing-boundary-envelope",
    note="The library uses nominal bore, outside diameter and width only; tolerances are out of scope.",
)

ISO_15_2017 = StandardReference(
    system="ISO",
    designation="ISO 15:2017",
    title="Rolling bearings — Radial bearings — Boundary dimensions, general plan",
    edition="2017",
    status="current",
    url="https://www.iso.org/standard/69977.html",
    relationship="boundary-dimension-basis",
    note="Internal ring, raceway, cage and ball proportions are not defined by this reference.",
)


@dataclass(frozen=True, slots=True)
class BearingBoundary:
    bore: float
    outside: float
    width: float


# Common 62 and 63 dimension-series selection. Values are nominal millimetres.
# The deliberately finite table prevents a model from inventing a designation.
DEEP_GROOVE_BOUNDARIES: dict[str, BearingBoundary] = {
    "6200": BearingBoundary(10, 30, 9),
    "6201": BearingBoundary(12, 32, 10),
    "6202": BearingBoundary(15, 35, 11),
    "6203": BearingBoundary(17, 40, 12),
    "6204": BearingBoundary(20, 47, 14),
    "6205": BearingBoundary(25, 52, 15),
    "6206": BearingBoundary(30, 62, 16),
    "6207": BearingBoundary(35, 72, 17),
    "6208": BearingBoundary(40, 80, 18),
    "6209": BearingBoundary(45, 85, 19),
    "6210": BearingBoundary(50, 90, 20),
    "6300": BearingBoundary(10, 35, 11),
    "6301": BearingBoundary(12, 37, 12),
    "6302": BearingBoundary(15, 42, 13),
    "6303": BearingBoundary(17, 47, 14),
    "6304": BearingBoundary(20, 52, 15),
    "6305": BearingBoundary(25, 62, 17),
    "6306": BearingBoundary(30, 72, 19),
    "6307": BearingBoundary(35, 80, 21),
    "6308": BearingBoundary(40, 90, 23),
    "6309": BearingBoundary(45, 100, 25),
    "6310": BearingBoundary(50, 110, 27),
}

_AXIAL_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


def _bearing_code(code: str | int) -> str:
    if isinstance(code, bool) or not isinstance(code, (str, int)):
        raise InvalidParameterError("code must be a bearing designation such as '6204'")
    normalized = str(code).strip()
    if normalized not in DEEP_GROOVE_BOUNDARIES:
        available = ", ".join(DEEP_GROOVE_BOUNDARIES)
        raise InvalidParameterError(f"unsupported deep-groove bearing code {normalized!r}; available: {available}")
    return normalized


def _annulus(outside_radius: float, inside_radius: float, width: float) -> Part:
    outer = Cylinder(outside_radius, width, align=_AXIAL_MIN)
    inner = Cylinder(inside_radius, width, align=_AXIAL_MIN)
    return (outer - inner).solid()


def deep_groove_dimensions(code: str | int, *, detail: str = "simplified") -> dict[str, str | float]:
    """Return designation and nominal boundary dimensions without geometry."""

    normalized = _bearing_code(code)
    if detail not in {"simplified", "rings"}:
        raise InvalidParameterError("detail must be 'simplified' or 'rings'")
    boundary = DEEP_GROOVE_BOUNDARIES[normalized]
    return {
        "bearing_type": "deep_groove_radial_ball",
        "designation": normalized,
        "detail": detail,
        "bore_diameter": boundary.bore,
        "outside_diameter": boundary.outside,
        "width": boundary.width,
        "unit": "mm",
        "internal_geometry": (
            "none; single exact boundary envelope"
            if detail == "simplified"
            else "heuristic rings and balls; not manufacturer dimensions"
        ),
    }


def deep_groove_bearing(code: str | int, *, detail: str = "simplified") -> Part | Compound:
    """Create a deep-groove radial bearing on the XY plane, width along +Z.

    ``simplified`` is a single annular interference/BOM envelope with exact
    nominal d/D/B dimensions. ``rings`` keeps the same exact outer envelope
    but adds heuristic rings and balls for recognizable previews; those
    internal proportions are explicitly not manufacturing dimensions.
    """

    derived = deep_groove_dimensions(code, detail=detail)
    normalized = str(derived["designation"])
    boundary = DEEP_GROOVE_BOUNDARIES[normalized]

    if detail == "simplified":
        result = _annulus(boundary.outside / 2, boundary.bore / 2, boundary.width)
        result.label = normalized
        return result

    radial_space = (boundary.outside - boundary.bore) / 2
    ball_diameter = min(boundary.width * 0.62, radial_space * 0.58)
    ball_radius = ball_diameter / 2
    pitch_radius = (boundary.outside + boundary.bore) / 4
    shoulder = ball_radius * 0.62
    inner_ring_outer = pitch_radius - shoulder
    outer_ring_inner = pitch_radius + shoulder

    inner_ring = _annulus(inner_ring_outer, boundary.bore / 2, boundary.width)
    outer_ring = _annulus(boundary.outside / 2, outer_ring_inner, boundary.width)
    circumference = 2 * pi * pitch_radius
    ball_count = max(6, int(circumference / (ball_diameter * 1.35)))
    balls = [
        Pos(
            pitch_radius * cos(2 * pi * index / ball_count),
            pitch_radius * sin(2 * pi * index / ball_count),
            boundary.width / 2,
        )
        * Sphere(ball_radius)
        for index in range(ball_count)
    ]
    result = Compound(children=[outer_ring, inner_ring, *balls])
    result.label = f"{normalized} (heuristic rings)"
    return result


register(
    FamilyDefinition(
        key="bearing.deep_groove",
        category="bearing",
        title="Deep-groove ball bearing / 深沟球轴承",
        description="Designation-driven radial bearing with exact nominal d/D/B boundary dimensions.",
        factory=deep_groove_bearing,
        derive=deep_groove_dimensions,
        parameters=(
            ParameterSpec(
                "code",
                "string",
                "Bearing designation",
                choices=tuple(DEEP_GROOVE_BOUNDARIES),
            ),
            ParameterSpec(
                "detail",
                "string",
                "simplified envelope or recognizable heuristic rings and balls",
                required=False,
                default="simplified",
                choices=("simplified", "rings"),
            ),
        ),
        standards=(GB_T_276_2013, ISO_15_2017),
        aliases=("deep_groove_bearing", "bearing"),
        orientation="axis +Z; lower face on XY; nominal width extends from Z=0",
        detail="exact boundary envelope; optional heuristic internals",
        validation="designation table, d/D/B bbox, bore, solids and STEP export tested",
        example="create('bearing.deep_groove', code='6204', detail='simplified')",
        notes=(
            "The simplified model is preferred for assembly and interference checks.",
            "The rings view does not reproduce manufacturer-specific raceways, cages, seals or ball counts.",
        ),
    )
)
