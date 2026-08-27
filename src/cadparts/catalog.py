"""Family registry and generic model-facing creation API."""

from __future__ import annotations

import inspect
import re
from copy import deepcopy
from string import Formatter
from typing import Any

from .errors import InvalidParameterError, UnknownFamilyError, UnknownPartError
from .interfaces import resolve_interfaces
from .metadata import entry_by_id, load_catalog_index, manifest_for_family
from .models import FamilyDefinition, PartInstance
from ._version import __version__


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

    definition = get_family(family)
    result = definition.to_dict()
    manifest = manifest_for_family(definition.key)
    result["catalog"] = _manifest_summary(manifest)
    return result


def _manifest_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    """Remove large per-model tables from progressive-disclosure responses."""

    result = deepcopy(manifest)
    for key in [key for key in result if key.startswith("_")]:
        result.pop(key)
    items = result.pop("items", [])
    result["item_count"] = len(items)
    if items:
        result["item_ids"] = [item["id"] for item in items]
    return result


def describe_part(identifier: str) -> dict[str, Any]:
    """Describe a family or one purchasable catalog item without geometry."""

    try:
        entry = entry_by_id(identifier)
    except UnknownPartError:
        return describe(identifier)
    family = str(entry["family"])
    result = {
        "entry": entry,
        "family_contract": describe(family),
    }
    if entry["kind"] == "item":
        result["generator_params"] = deepcopy(entry.get("generator", {}).get("params", {}))
    return result


def _text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(f"{key} {_text(item)}" for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return " ".join(_text(item) for item in value)
    return str(value)


def _lookup(entry: dict[str, Any], key: str) -> Any:
    current: Any = entry
    for component in key.split("."):
        if not isinstance(current, dict) or component not in current:
            current = None
            break
        current = current[component]
    if current is not None:
        return current
    for section in ("dimensions_mm", "selectors"):
        value = entry.get(section, {})
        if isinstance(value, dict) and key in value:
            return value[key]
    return None


def _matches_constraint(actual: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        if actual is None:
            return False
        if "eq" in expected and actual != expected["eq"]:
            return False
        if "min" in expected and (not isinstance(actual, (int, float)) or actual < expected["min"]):
            return False
        if "max" in expected and (not isinstance(actual, (int, float)) or actual > expected["max"]):
            return False
        return True
    if isinstance(actual, (list, tuple)):
        return any(str(item).casefold() == str(expected).casefold() for item in actual)
    if isinstance(actual, str) or isinstance(expected, str):
        return str(actual).casefold() == str(expected).casefold()
    return actual == expected


def search(
    query: str = "",
    *,
    category: str | None = None,
    constraints: dict[str, Any] | None = None,
    limit: int = 8,
) -> list[dict[str, Any]]:
    """Search compact family/item declarations without loading CAD geometry.

    Search is deliberately local and deterministic.  It recognizes aliases,
    Chinese/English procurement terms and exact dimensional constraints, and
    returns only a small candidate set to protect an agent's context window.
    """

    if limit < 1 or limit > 50:
        raise InvalidParameterError("limit must be between 1 and 50")
    constraints = constraints or {}
    normalized_query = query.strip().casefold()
    terms = [item for item in re.split(r"[\s,，;；/]+", normalized_query) if item]
    scored: list[tuple[int, dict[str, Any]]] = []
    for entry in load_catalog_index()["entries"]:
        if category is not None and entry["category"].casefold() != category.casefold():
            continue
        if any(not _matches_constraint(_lookup(entry, key), value) for key, value in constraints.items()):
            continue

        score = 1 if not normalized_query else 0
        identifiers = [entry["id"], *entry.get("aliases", [])]
        if normalized_query and any(normalized_query == str(item).casefold() for item in identifiers):
            score += 200
        haystack = _text(entry).casefold()
        if normalized_query and normalized_query in haystack:
            score += 80
        for keyword in entry.get("keywords", []):
            if str(keyword).casefold() in normalized_query:
                score += 30
        for term in terms:
            if term in haystack:
                score += 10
        if normalized_query and score == 0:
            continue
        compact = {
            key: deepcopy(entry[key])
            for key in (
                "id", "family", "kind", "category", "name", "summary",
                "dimensions_mm", "selectors", "geometry_fidelity", "path",
            )
            if key in entry
        }
        compact["score"] = score
        scored.append((score, compact))
    scored.sort(key=lambda item: (-item[0], item[1]["id"]))
    return [item for _, item in scored[:limit]]


def compare(*identifiers: str) -> dict[str, Any]:
    """Return selection-relevant fields for two or more catalog candidates."""

    if len(identifiers) < 2:
        raise InvalidParameterError("compare requires at least two catalog ids")
    entries = [entry_by_id(identifier) for identifier in identifiers]
    return {
        "schema": "cadparts.comparison/v1",
        "candidates": [
            {
                key: deepcopy(entry.get(key))
                for key in (
                    "id", "family", "name", "summary", "dimensions_mm",
                    "selectors", "geometry_fidelity", "path",
                )
                if key in entry
            }
            for entry in entries
        ],
    }


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


def _purchase_spec(
    definition: FamilyDefinition,
    manifest: dict[str, Any],
    parameters: dict[str, Any],
    selections: dict[str, Any],
    derived_values: dict[str, Any],
) -> dict[str, Any]:
    purchase = deepcopy(manifest.get("purchase", {}))
    values = {**parameters, **derived_values, **selections}
    template = purchase.get("designation_template")
    if template:
        fields = [name for _, name, _, _ in Formatter().parse(template) if name]
        if all(name in values for name in fields):
            purchase["query"] = template.format(**values)
    if definition.key == "bearing.deep_groove":
        order_code = str(derived_values["designation"])
        for key, normal_values in (("closure", {None, "", "open"}), ("clearance", {None, "", "normal"})):
            value = selections.get(key)
            if value not in normal_values:
                order_code += f"-{value}"
        purchase["order_code"] = order_code
        purchase["query"] = f"{order_code} deep-groove bearing 深沟球轴承"
    return purchase


def _validate_selections(manifest: dict[str, Any], selections: dict[str, Any]) -> None:
    declared = manifest.get("selectors", {})
    for key, value in selections.items():
        if key not in declared:
            available = ", ".join(sorted(declared)) or "<none>"
            raise InvalidParameterError(
                f"unknown selection {key!r} for {manifest['id']}; available: {available}"
            )
        choices = declared[key]
        if isinstance(choices, list) and not any(
            str(value).casefold() == str(choice).casefold() for choice in choices
        ):
            raise InvalidParameterError(
                f"invalid {key}={value!r} for {manifest['id']}; choices: {choices}"
            )


def instance_spec(
    family: str,
    /,
    *,
    catalog_id: str | None = None,
    selections: dict[str, Any] | None = None,
    **parameters: Any,
) -> dict[str, Any]:
    """Create a canonical, JSON-serializable and geometry-free instance spec."""

    definition = get_family(family)
    try:
        inspect.signature(definition.factory).bind(**parameters)
    except TypeError as exc:
        raise InvalidParameterError(f"{family}: {exc}") from exc
    selected = dict(selections or {})
    derived_values = derive(definition.key, **parameters) if definition.derive is not None else {}
    manifest = manifest_for_family(definition.key)
    _validate_selections(manifest, selected)
    result: dict[str, Any] = {
        "schema": "cadparts.instance/v2",
        "library": "cad-parts",
        "library_version": __version__,
        "catalog_id": catalog_id or definition.key,
        "family": definition.key,
        "parameters": dict(parameters),
        "selection": selected,
        "intent": "assembly proxy, interface layout, BOM and purchase direction",
        "geometry_fidelity": manifest["geometry"]["fidelity"],
        "interfaces": resolve_interfaces(definition.key, parameters, derived_values),
        "purchase": _purchase_spec(definition, manifest, dict(parameters), selected, derived_values),
        "standards": [
            {
                "system": reference.system,
                "designation": reference.designation,
                "edition": reference.edition,
                "relationship": reference.relationship,
            }
            for reference in definition.standards
        ],
    }
    if derived_values:
        result["derived"] = derived_values
    return result


def instantiate(
    identifier: str,
    /,
    *,
    selections: dict[str, Any] | None = None,
    **parameters: Any,
) -> PartInstance:
    """Resolve a catalog item or family into a proxy shape and rich spec."""

    try:
        entry = entry_by_id(identifier)
        family = str(entry["family"])
        base_parameters = dict(entry.get("generator", {}).get("params", {}))
        catalog_id = str(entry["id"])
        for key, value in base_parameters.items():
            if key in parameters and parameters[key] != value:
                raise InvalidParameterError(
                    f"{catalog_id} pins {key}={value!r}; search for another item instead of overriding it"
                )
    except UnknownPartError:
        definition = get_family(identifier)
        family = definition.key
        base_parameters = {}
        catalog_id = definition.key
    resolved_parameters = {**base_parameters, **parameters}
    shape = create(family, **resolved_parameters)
    spec = instance_spec(
        family,
        catalog_id=catalog_id,
        selections=selections,
        **resolved_parameters,
    )
    bbox = shape.bounding_box()
    spec["envelope"] = {
        "min_mm": [bbox.min.X, bbox.min.Y, bbox.min.Z],
        "max_mm": [bbox.max.X, bbox.max.Y, bbox.max.Z],
        "size_mm": [bbox.size.X, bbox.size.Y, bbox.size.Z],
    }
    spec["shape"] = {
        "label": shape.label,
        "valid": bool(shape.is_valid),
        "solid_count": len(shape.solids()),
    }
    return PartInstance(shape=shape, spec=spec)


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
