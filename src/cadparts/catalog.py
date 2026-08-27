"""Family registry and generic model-facing creation API."""

from __future__ import annotations

import inspect
from typing import Any

from .errors import InvalidParameterError, UnknownFamilyError
from .models import FamilyDefinition


_FAMILIES: dict[str, FamilyDefinition] = {}
_ALIASES: dict[str, str] = {}


def register(definition: FamilyDefinition) -> None:
    """Register one family and reject ambiguous keys or aliases."""

    if definition.key in _FAMILIES or definition.key in _ALIASES:
        raise ValueError(f"duplicate family key: {definition.key}")
    collisions = set(definition.aliases) & (set(_FAMILIES) | set(_ALIASES))
    if collisions:
        raise ValueError(f"duplicate family aliases: {sorted(collisions)}")

    _FAMILIES[definition.key] = definition
    for alias in definition.aliases:
        _ALIASES[alias] = definition.key


def get_family(family: str) -> FamilyDefinition:
    """Resolve a canonical family key or alias."""

    canonical = _ALIASES.get(family, family)
    try:
        return _FAMILIES[canonical]
    except KeyError as exc:
        available = ", ".join(sorted(_FAMILIES)) or "<none>"
        raise UnknownFamilyError(f"unknown family {family!r}; available: {available}") from exc


def list_families(*, category: str | None = None, standard_system: str | None = None) -> list[dict[str, Any]]:
    """Return a compact deterministic catalog suitable for an LLM tool result."""

    definitions = sorted(_FAMILIES.values(), key=lambda item: item.key)
    if category is not None:
        definitions = [item for item in definitions if item.category == category]
    if standard_system is not None:
        wanted = standard_system.casefold()
        definitions = [
            item for item in definitions
            if any(ref.system.casefold() == wanted for ref in item.standards)
        ]
    return [dict(item.summary()) for item in definitions]


def describe(family: str) -> dict[str, Any]:
    """Return the complete JSON-serializable contract for one family."""

    return get_family(family).to_dict()


def derive(family: str, /, **parameters: Any) -> dict[str, Any]:
    """Return calculated dimensions without creating or tessellating geometry."""

    definition = get_family(family)
    if definition.derive is None:
        raise InvalidParameterError(f"{family}: derived dimensions are not available")
    try:
        inspect.signature(definition.derive).bind(**parameters)
    except TypeError as exc:
        raise InvalidParameterError(f"{family}: {exc}") from exc
    return dict(definition.derive(**parameters))


def create(family: str, /, **parameters: Any) -> Any:
    """Instantiate a family from JSON-like keyword parameters.

    Signature binding happens before geometry creation so a model receives a
    short parameter error rather than a long OpenCascade traceback.
    """

    definition = get_family(family)
    try:
        inspect.signature(definition.factory).bind(**parameters)
    except TypeError as exc:
        raise InvalidParameterError(f"{family}: {exc}") from exc
    return definition.factory(**parameters)
