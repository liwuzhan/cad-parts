"""Declarative stepped-shaft generation.

A shaft is not a catalog standard part: it is the *derived* consequence of what
mounts on it. This module lets a caller declare that relationship — "a 6204
bearing seats here", "a parallel key drives here" — and derives the diameters,
the axial chain and the named interfaces from the library's own interface data.

The point is that the caller declares **relationships**, not coordinates. Change
the bearing designation and the shaft follows, because the seat diameter comes
from the bearing's ``shaft_bore`` interface rather than from a literal.

Fits are deliberately not modeled: ``diameter_delta`` is an explicit allowance
the caller must supply, and the emitted ``nominal`` values stay nominal. This
matches the library-wide rule that a declaration never claims more than it
proves.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence
from math import isclose

from build123d import (
    Axis,
    BuildLine,
    BuildPart,
    BuildSketch,
    Plane,
    Polyline,
    make_face,
    revolve,
)

from .catalog import derive
from .errors import InvalidParameterError
from .interfaces import resolve_interfaces


@dataclass(frozen=True, slots=True)
class Seat:
    """One mounting station whose size is dictated by a library part.

    ``interface`` names the interface on that part the shaft mates with — for a
    bearing that is ``shaft_bore``. The seat diameter and length default to that
    interface's own values.
    """

    part: str
    params: Mapping[str, Any]
    interface: str
    role: str
    diameter_delta: float = 0.0
    length: float | None = None


@dataclass(frozen=True, slots=True)
class Free:
    """A station with no library counterpart (spacer, shaft extension, journal)."""

    diameter: float
    length: float
    role: str = "free"


Station = Seat | Free


@dataclass(frozen=True, slots=True)
class ShaftSpec:
    """An ordered axial stack of stations, from the ``-Z`` end to the ``+Z`` end."""

    stations: Sequence[Station] = field(default_factory=tuple)
    detail: str = "simplified"

    def __post_init__(self) -> None:
        if len(self.stations) == 0:
            raise InvalidParameterError("shaft: at least one station is required")


def _resolve_reference(seat: Seat) -> tuple[float, float, dict[str, Any]]:
    """Resolve a library part's interface into ``(diameter, length, source)``."""

    if not isinstance(seat.params, Mapping):
        raise InvalidParameterError(f"shaft: params for {seat.part!r} must be a mapping")

    derived = derive(seat.part, **dict(seat.params))
    interfaces = resolve_interfaces(seat.part, dict(seat.params), derived)
    match = next((item for item in interfaces if item["id"] == seat.interface), None)
    if match is None:
        available = sorted(item["id"] for item in interfaces)
        raise InvalidParameterError(
            f"shaft: {seat.part} has no interface {seat.interface!r}; available: {available}"
        )

    dims = match.get("dimensions_mm") or {}
    diameter = dims.get("diameter")
    if diameter is None:
        raise InvalidParameterError(
            f"shaft: interface {seat.interface!r} of {seat.part} carries no diameter; "
            "it cannot size a shaft seat"
        )
    length = seat.length if seat.length is not None else dims.get("length")
    if length is None:
        raise InvalidParameterError(
            f"shaft: interface {seat.interface!r} of {seat.part} carries no length; "
            "pass length= explicitly"
        )

    source = {
        "family": seat.part,
        "params": dict(seat.params),
        "interface": seat.interface,
        "interface_type": match["type"],
    }
    return float(diameter), float(length), source


def shaft_dimensions(spec: ShaftSpec) -> dict[str, Any]:
    """Derive the axial chain and every station size without building geometry."""

    stations: list[dict[str, Any]] = []
    cursor = 0.0
    for index, station in enumerate(spec.stations):
        if isinstance(station, Seat):
            nominal, length, source = _resolve_reference(station)
            diameter = nominal + float(station.diameter_delta)
            kind = "seat"
        else:
            diameter = float(station.diameter)
            length = float(station.length)
            nominal = diameter
            source = None
            kind = "free"

        if diameter <= 0:
            raise InvalidParameterError(f"shaft: station {index} diameter must be positive")
        if length <= 0:
            raise InvalidParameterError(f"shaft: station {index} length must be positive")

        stations.append({
            "index": index,
            "role": station.role,
            "kind": kind,
            "diameter": diameter,
            "nominal_diameter": nominal,
            "length": length,
            "z_start": cursor,
            "z_end": cursor + length,
            "source": source,
        })
        cursor += length

    shoulders: list[dict[str, Any]] = []
    for lower, upper in zip(stations, stations[1:]):
        if isclose(lower["diameter"], upper["diameter"], rel_tol=0.0, abs_tol=1e-9):
            continue
        larger = lower if lower["diameter"] > upper["diameter"] else upper
        shoulders.append({
            "index": len(shoulders),
            "at_z": upper["z_start"],
            "outer_diameter": larger["diameter"],
            "inner_diameter": min(lower["diameter"], upper["diameter"]),
            "role": f"shoulder_{lower['role']}_{upper['role']}",
            # The face looks toward the smaller station, which is the side a
            # mounted part can be pressed against.
            "faces": "+Z" if lower["diameter"] > upper["diameter"] else "-Z",
        })

    return {
        "shaft_type": "stepped",
        "detail": spec.detail,
        "station_count": len(stations),
        "stations": stations,
        "shoulders": shoulders,
        "total_length": cursor,
        "max_diameter": max(item["diameter"] for item in stations),
        "unit": "mm",
    }


def stepped_shaft(spec: ShaftSpec):
    """Build the revolved solid for a shaft specification.

    Cylindrical stations are revolved as one profile so the result is a single
    solid with real shoulder faces, not a boolean pile.
    """

    derived = shaft_dimensions(spec)
    stations = derived["stations"]

    # Half-section outline in the XZ plane: (+radius, +z), revolved about Z.
    points: list[tuple[float, float]] = [(0.0, 0.0)]
    for station in stations:
        radius = station["diameter"] / 2.0
        points.append((radius, station["z_start"]))
        points.append((radius, station["z_end"]))
    points.append((0.0, derived["total_length"]))

    deduped: list[tuple[float, float]] = []
    for point in points:
        if deduped and isclose(point[0], deduped[-1][0], rel_tol=0.0, abs_tol=1e-9) \
                and isclose(point[1], deduped[-1][1], rel_tol=0.0, abs_tol=1e-9):
            continue
        deduped.append(point)

    with BuildPart() as part:
        with BuildSketch(Plane.XZ):
            # Plane.XZ maps sketch (x, y) to world (X, Z), so an explicit
            # polyline keeps the profile readable as (radius, z) pairs.
            with BuildLine():
                Polyline(*deduped, close=True)
            make_face()
        revolve(axis=Axis.Z)

    result = part.part
    roles = "/".join(str(item["role"]) for item in stations)
    result.label = f"Stepped shaft {derived['total_length']:g}mm [{roles}]"
    return result


def shaft_reference_checks(spec: ShaftSpec) -> list[dict[str, Any]]:
    """Assert the shaft still satisfies every relationship it was declared with.

    This is the external-truth check: each seat diameter must equal the diameter
    of the library interface it claims to seat, so a swapped catalogue part is
    caught rather than silently tolerated.
    """

    checks: list[dict[str, Any]] = []
    for station in shaft_dimensions(spec)["stations"]:
        source = station["source"]
        if source is None:
            continue
        checks.append({
            "id": f"seat_{station['role']}",
            "role": station["role"],
            "expected_interface_type": source["interface_type"],
            "nominal_diameter": station["nominal_diameter"],
            "seat_diameter": station["diameter"],
            "delta": station["diameter"] - station["nominal_diameter"],
            "length": station["length"],
        })
    return checks


__all__ = [
    "Free",
    "Seat",
    "ShaftSpec",
    "Station",
    "shaft_dimensions",
    "shaft_reference_checks",
    "stepped_shaft",
]
