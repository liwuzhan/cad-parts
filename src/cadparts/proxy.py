"""Shared validation, transform and keepout helpers for assembly proxies."""

from __future__ import annotations

from typing import Any, Iterable

from build123d import Align, Box, Compound, Cylinder, Part, Pos, Rot

from .errors import InvalidParameterError


CENTER_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


def real(name: str, value: Any, *, positive: bool = False, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidParameterError(f"{name} must be a real number")
    result = float(value)
    if positive and result <= 0:
        raise InvalidParameterError(f"{name} must be > 0")
    if minimum is not None and result < minimum:
        raise InvalidParameterError(f"{name} must be >= {minimum:g}")
    return result


def integer(name: str, value: Any, *, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise InvalidParameterError(f"{name} must be an integer >= {minimum}")
    return value


def choice(name: str, value: Any, choices: Iterable[str]) -> str:
    normalized = str(value).strip()
    available = tuple(choices)
    if normalized not in available:
        raise InvalidParameterError(f"unsupported {name} {normalized!r}; available: {', '.join(available)}")
    return normalized


def box_keepout(identifier: str, size: tuple[float, float, float], center: tuple[float, float, float], purpose: str) -> dict[str, Any]:
    return {
        "id": identifier,
        "shape": "box",
        "purpose": purpose,
        "frame": {"center_mm": list(center), "axes": "+X,+Y,+Z"},
        "size_mm": list(size),
    }


def cylinder_keepout(identifier: str, diameter: float, length: float, origin: tuple[float, float, float], axis: tuple[float, float, float], purpose: str) -> dict[str, Any]:
    return {
        "id": identifier,
        "shape": "cylinder",
        "purpose": purpose,
        "frame": {"origin_mm": list(origin), "axis": list(axis)},
        "diameter_mm": float(diameter),
        "length_mm": float(length),
    }


def axial_cylinder(diameter: float, length: float, *, origin: tuple[float, float, float] = (0, 0, 0), axis: str = "+Z") -> Part:
    base = Cylinder(diameter / 2, length, align=CENTER_MIN)
    rotations = {"+Z": (0, 0, 0), "-Z": (180, 0, 0), "+X": (0, 90, 0), "-X": (0, -90, 0), "+Y": (-90, 0, 0), "-Y": (90, 0, 0)}
    if axis not in rotations:
        raise InvalidParameterError(f"unsupported axis {axis!r}")
    return Pos(*origin) * Rot(*rotations[axis]) * base


def four_positions(pitch_x: float, pitch_y: float) -> tuple[tuple[float, float], ...]:
    return tuple((sx * pitch_x / 2, sy * pitch_y / 2) for sx in (-1, 1) for sy in (-1, 1))


def cut_z_holes(shape: Part, positions: Iterable[tuple[float, float]], diameter: float, z_min: float, z_max: float) -> Part:
    result = shape
    for x, y in positions:
        result = result - Pos(x, y, z_min) * Cylinder(diameter / 2, z_max - z_min, align=CENTER_MIN)
    return result


def compound(label: str, *children: Part) -> Compound:
    result = Compound(children=list(children))
    result.label = label
    return result
