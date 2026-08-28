"""Load and validate the self-declaring, model-facing parts catalog."""

from __future__ import annotations

import json
from copy import deepcopy
from importlib.resources import files
from pathlib import Path
from typing import Any, Iterable, Mapping

from .errors import CatalogDataError, UnknownPartError


CATALOG_SCHEMA = "cadparts.catalog-family/v1"
INDEX_SCHEMA = "cadparts.catalog-index/v1"
COMPATIBILITY_LEVELS = {
    "normative",
    "cross_vendor_verified",
    "series_compatible",
    "catalog_specific",
}


def catalog_root():
    """Return the installed package resource containing catalog declarations."""

    return files("cadparts.data").joinpath("catalog")


def _manifest_resources() -> list[Any]:
    root = catalog_root()
    resources: list[Any] = []
    for category in root.iterdir():
        if not category.is_dir():
            continue
        resources.extend(
            item
            for item in category.iterdir()
            if item.is_file() and item.name.endswith(".json") and item.name != "index.json"
        )
    return sorted(resources, key=lambda item: str(item))


def _validate_manifest(data: Mapping[str, Any], *, source: str) -> None:
    required = {"schema", "id", "category", "name", "summary", "geometry", "sample"}
    missing = sorted(required - set(data))
    if missing:
        raise CatalogDataError(f"{source}: missing required fields: {', '.join(missing)}")
    if data["schema"] != CATALOG_SCHEMA:
        raise CatalogDataError(f"{source}: unsupported schema {data['schema']!r}")
    if not isinstance(data["geometry"], Mapping) or "fidelity" not in data["geometry"]:
        raise CatalogDataError(f"{source}: geometry.fidelity is required")
    if not isinstance(data["sample"], Mapping) or "params" not in data["sample"]:
        raise CatalogDataError(f"{source}: sample.params is required")
    parameters = data.get("parameters")
    if not isinstance(parameters, list) or not parameters:
        raise CatalogDataError(f"{source}: parameters must be a non-empty list")
    names: set[str] = set()
    for parameter in parameters:
        if not isinstance(parameter, Mapping) or not {"name", "type", "description", "required"} <= set(parameter):
            raise CatalogDataError(f"{source}: every parameter needs name, type, description and required")
        name = str(parameter["name"])
        if name in names:
            raise CatalogDataError(f"{source}: duplicate parameter name {name!r}")
        names.add(name)
        if not isinstance(parameter["required"], bool):
            raise CatalogDataError(f"{source}: parameter {name!r} required must be a boolean")
        if not parameter["required"] and "default" not in parameter:
            raise CatalogDataError(f"{source}: optional parameter {name!r} needs a default")
    for interface in data.get("interfaces", []):
        if not isinstance(interface, Mapping) or not {"id", "type", "role"} <= set(interface):
            raise CatalogDataError(f"{source}: every interface needs id, type and role")
    compatibility = data.get("compatibility")
    if compatibility is not None:
        if not isinstance(compatibility, Mapping) or compatibility.get("level") not in COMPATIBILITY_LEVELS:
            choices = ", ".join(sorted(COMPATIBILITY_LEVELS))
            raise CatalogDataError(f"{source}: compatibility.level must be one of: {choices}")
        if "claim" not in compatibility:
            raise CatalogDataError(f"{source}: compatibility.claim is required")
    for keepout in data.get("keepouts", []):
        if not isinstance(keepout, Mapping) or not {"id", "purpose"} <= set(keepout):
            raise CatalogDataError(f"{source}: every keepout needs id and purpose")


def load_manifests() -> list[dict[str, Any]]:
    """Load every family declaration in deterministic order."""

    manifests: list[dict[str, Any]] = []
    seen: set[str] = set()
    for resource in _manifest_resources():
        try:
            data = json.loads(resource.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CatalogDataError(f"cannot read {resource}: {exc}") from exc
        if not isinstance(data, dict):
            raise CatalogDataError(f"{resource}: root must be an object")
        _validate_manifest(data, source=str(resource))
        if data["id"] in seen:
            raise CatalogDataError(f"duplicate catalog id: {data['id']}")
        seen.add(str(data["id"]))
        data["_source_path"] = (
            f"src/cadparts/data/catalog/{resource.parent.name}/{resource.name}"
        )
        manifests.append(data)
    return sorted(manifests, key=lambda item: item["id"])


def _compact_family(manifest: Mapping[str, Any], *, source_path: str) -> dict[str, Any]:
    result = {
        "id": manifest["id"],
        "family": manifest["id"],
        "kind": "family",
        "category": manifest["category"],
        "name": manifest["name"],
        "summary": manifest["summary"],
        "aliases": list(manifest.get("aliases", [])),
        "keywords": list(manifest.get("keywords", [])),
        "selectors": deepcopy(manifest.get("selectors", {})),
        "geometry_fidelity": manifest["geometry"]["fidelity"],
        "path": source_path,
    }
    if "compatibility" in manifest:
        result["compatibility"] = deepcopy(manifest["compatibility"])
    return result


def build_catalog_index(manifests: Iterable[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """Compile declarations into a compact progressive-disclosure index."""

    if manifests is None:
        manifests = load_manifests()
    entries: list[dict[str, Any]] = []
    categories: dict[str, int] = {}
    for manifest in manifests:
        source_path = str(manifest.get(
            "_source_path",
            f"src/cadparts/data/catalog/{manifest['category']}/{manifest['id'].replace('.', '_')}.json",
        ))
        entries.append(_compact_family(manifest, source_path=source_path))
        categories[manifest["category"]] = categories.get(manifest["category"], 0) + 1
        for item in manifest.get("items", []):
            if not isinstance(item, Mapping) or "id" not in item:
                raise CatalogDataError(f"{manifest['id']}: every item needs an id")
            item_id = str(item["id"])
            short_id = item_id.rsplit(".", 1)[-1]
            compact_item = {
                "id": item_id,
                "family": manifest["id"],
                "kind": "item",
                "category": manifest["category"],
                "name": item.get("name", item_id),
                "summary": item.get("summary", manifest["summary"]),
                "aliases": list(dict.fromkeys([short_id, *item.get("aliases", [])])),
                "keywords": list(dict.fromkeys([
                    *manifest.get("keywords", []),
                    *item.get("keywords", []),
                ])),
                "dimensions_mm": deepcopy(item.get("dimensions_mm", {})),
                "selectors": {
                    **deepcopy(manifest.get("selectors", {})),
                    **deepcopy(item.get("selectors", {})),
                    **deepcopy(item.get("generator", {}).get("params", {})),
                },
                "generator": deepcopy(item.get("generator", {})),
                "geometry_fidelity": manifest["geometry"]["fidelity"],
                "path": source_path,
            }
            compatibility = item.get("compatibility", manifest.get("compatibility"))
            if compatibility is not None:
                compact_item["compatibility"] = deepcopy(compatibility)
            entries.append(compact_item)
    return {
        "schema": INDEX_SCHEMA,
        "entrypoint": "CATALOG.md",
        "categories": dict(sorted(categories.items())),
        "entries": sorted(entries, key=lambda item: item["id"]),
    }


def load_catalog_index() -> dict[str, Any]:
    """Load the checked-in generated index."""

    resource = catalog_root().joinpath("index.json")
    try:
        data = json.loads(resource.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogDataError(f"cannot read catalog index: {exc}") from exc
    if data.get("schema") != INDEX_SCHEMA:
        raise CatalogDataError("catalog index schema is missing or unsupported")
    return data


def manifest_for_family(family: str) -> dict[str, Any]:
    for manifest in load_manifests():
        if manifest["id"] == family or family in manifest.get("aliases", []):
            return manifest
    raise UnknownPartError(f"catalog declaration not found for family {family!r}")


def entry_by_id(identifier: str) -> dict[str, Any]:
    index = load_catalog_index()
    normalized = identifier.casefold()
    for entry in index["entries"]:
        candidates = [entry["id"], *entry.get("aliases", [])]
        if any(str(candidate).casefold() == normalized for candidate in candidates):
            return deepcopy(entry)
    raise UnknownPartError(f"unknown catalog part {identifier!r}; use search() before inventing a model")


def write_catalog_index(destination: Path | None = None) -> Path:
    """Regenerate the deterministic JSON index used by tools and agents."""

    if destination is None:
        resource = catalog_root().joinpath("index.json")
        destination = Path(str(resource))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(build_catalog_index(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination
