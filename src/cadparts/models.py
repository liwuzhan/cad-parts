"""Serializable catalog metadata.

The metadata classes intentionally contain no build123d objects. They can be
returned to a language model as compact JSON without loading or tessellating a
shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping


@dataclass(frozen=True, slots=True)
class StandardReference:
    """A traceable standards reference attached to a part family."""

    system: str
    designation: str
    title: str
    edition: str
    status: str
    url: str
    relationship: str = "governing"
    note: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "system": self.system,
            "designation": self.designation,
            "title": self.title,
            "edition": self.edition,
            "status": self.status,
            "url": self.url,
            "relationship": self.relationship,
            "note": self.note,
        }


@dataclass(frozen=True, slots=True)
class ParameterSpec:
    """A compact, model-readable parameter contract."""

    name: str
    type: str
    description: str
    unit: str | None = None
    required: bool = True
    default: Any = None
    minimum: float | None = None
    maximum: float | None = None
    choices: tuple[Any, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "required": self.required,
        }
        if self.unit is not None:
            result["unit"] = self.unit
        if not self.required:
            result["default"] = self.default
        if self.minimum is not None:
            result["minimum"] = self.minimum
        if self.maximum is not None:
            result["maximum"] = self.maximum
        if self.choices:
            result["choices"] = list(self.choices)
        return result


@dataclass(frozen=True, slots=True)
class FamilyDefinition:
    """Registered parametric part family and its discovery metadata."""

    key: str
    category: str
    title: str
    description: str
    factory: Callable[..., Any] = field(repr=False, compare=False)
    derive: Callable[..., Mapping[str, Any]] | None = field(default=None, repr=False, compare=False)
    parameters: tuple[ParameterSpec, ...] = ()
    standards: tuple[StandardReference, ...] = ()
    aliases: tuple[str, ...] = ()
    orientation: str = "+Z"
    detail: str = "simplified"
    validation: str = "tested"
    example: str = ""
    notes: tuple[str, ...] = ()

    def to_dict(self, *, include_standards: bool = True) -> dict[str, Any]:
        result: dict[str, Any] = {
            "family": self.key,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "supports_derive": self.derive is not None,
            "parameters": [item.to_dict() for item in self.parameters],
            "aliases": list(self.aliases),
            "orientation": self.orientation,
            "detail": self.detail,
            "validation": self.validation,
            "example": self.example,
            "notes": list(self.notes),
        }
        if include_standards:
            result["standards"] = [item.to_dict() for item in self.standards]
        return result

    def summary(self) -> Mapping[str, Any]:
        return {
            "family": self.key,
            "title": self.title,
            "parameters": [item.name for item in self.parameters],
            "validation": self.validation,
        }
