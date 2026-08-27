"""Small JSON-first command line interface for language models and scripts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from build123d import export_step, export_stl

from . import __version__
from .catalog import (
    compare,
    create,
    derive,
    describe_part,
    instance_spec,
    instantiate,
    list_families,
    search,
)
from .errors import CadPartsError
from .metadata import write_catalog_index
from .review import review_catalog, review_part, validate_catalog


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _json_object(raw: str | None, parser: argparse.ArgumentParser, option: str) -> dict[str, Any]:
    if raw is None:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        parser.error(f"{option} is not valid JSON: {exc.msg}")
    if not isinstance(value, dict):
        parser.error(f"{option} must decode to a JSON object")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cadparts", description="Parametric standard parts catalog")
    parser.add_argument("--version", action="version", version=f"cadparts {__version__}")
    subcommands = parser.add_subparsers(dest="command", required=True)

    list_command = subcommands.add_parser("list", help="list registered families")
    list_command.add_argument("--category")
    list_command.add_argument("--standard-system")

    search_command = subcommands.add_parser("search", help="find parts without scanning files or loading geometry")
    search_command.add_argument("query", nargs="?", default="")
    search_command.add_argument("--category")
    search_command.add_argument("--constraints", help="JSON object; e.g. {\"bore\":20}")
    search_command.add_argument("--limit", type=int, default=8)

    compare_command = subcommands.add_parser("compare", help="compare catalog candidates")
    compare_command.add_argument("identifiers", nargs="+")

    describe_command = subcommands.add_parser("describe", help="describe one family or catalog item")
    describe_command.add_argument("identifier")

    derive_command = subcommands.add_parser("derive", help="calculate dimensions without building geometry")
    derive_command.add_argument("family")
    derive_command.add_argument("--params", required=True, help="JSON object of family parameters")

    spec_command = subcommands.add_parser("spec", help="emit a reproducible canonical instance spec")
    spec_command.add_argument("family")
    spec_command.add_argument("--params", required=True, help="JSON object of family parameters")

    build_command = subcommands.add_parser("build", help="create and export one part")
    build_command.add_argument("family")
    build_command.add_argument("--params", required=True, help="JSON object of family parameters")
    build_command.add_argument("--output", required=True, type=Path)
    build_command.add_argument("--format", choices=("step", "stl"), default="step")

    instantiate_command = subcommands.add_parser(
        "instantiate", help="resolve a catalog item and export its proxy plus instance JSON"
    )
    instantiate_command.add_argument("identifier")
    instantiate_command.add_argument("--params", help="JSON overrides for generator parameters")
    instantiate_command.add_argument("--selection", help="JSON purchase/selection attributes")
    instantiate_command.add_argument("--output", required=True, type=Path)
    instantiate_command.add_argument("--format", choices=("step", "stl"), default="step")

    review_command = subcommands.add_parser("review", help="generate STEP, instance JSON and standard-view PNGs")
    review_command.add_argument("identifier")
    review_command.add_argument("--params", help="JSON generator parameter overrides")
    review_command.add_argument("--selection", help="JSON purchase/selection attributes")
    review_command.add_argument("--output-dir", required=True, type=Path)
    review_command.add_argument("--views", default="iso,front,right,top")

    review_catalog_command = subcommands.add_parser(
        "review-catalog", help="generate representative review artifacts for every family"
    )
    review_catalog_command.add_argument("--output-dir", required=True, type=Path)
    review_catalog_command.add_argument("--views", default="iso")

    validate_command = subcommands.add_parser("validate-catalog", help="validate declarations and generated index")
    validate_command.add_argument("--build-samples", action="store_true")

    index_command = subcommands.add_parser("build-index", help="regenerate the deterministic catalog index")
    index_command.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            print(_json(list_families(category=args.category, standard_system=args.standard_system)))
            return 0
        if args.command == "search":
            print(_json(search(
                args.query,
                category=args.category,
                constraints=_json_object(args.constraints, parser, "--constraints"),
                limit=args.limit,
            )))
            return 0
        if args.command == "compare":
            print(_json(compare(*args.identifiers)))
            return 0
        if args.command == "describe":
            print(_json(describe_part(args.identifier)))
            return 0
        if args.command == "validate-catalog":
            print(_json(validate_catalog(build_samples=args.build_samples)))
            return 0
        if args.command == "build-index":
            print(_json({"output": str(write_catalog_index(args.output).resolve())}))
            return 0
        if args.command == "review":
            print(_json(review_part(
                args.identifier,
                parameters=_json_object(args.params, parser, "--params"),
                selections=_json_object(args.selection, parser, "--selection"),
                output_dir=args.output_dir,
                views=[item.strip() for item in args.views.split(",") if item.strip()],
            )))
            return 0
        if args.command == "review-catalog":
            print(_json(review_catalog(
                output_dir=args.output_dir,
                views=[item.strip() for item in args.views.split(",") if item.strip()],
            )))
            return 0

        parameters = _json_object(args.params, parser, "--params")

        if args.command == "derive":
            print(_json(derive(args.family, **parameters)))
            return 0
        if args.command == "spec":
            print(_json(instance_spec(args.family, **parameters)))
            return 0

        if args.command == "instantiate":
            selected = _json_object(args.selection, parser, "--selection")
            instance = instantiate(args.identifier, selections=selected, **parameters)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            if args.format == "step":
                export_step(instance.shape, args.output)
            else:
                export_stl(instance.shape, args.output)
            sidecar = args.output.with_suffix(args.output.suffix + ".json")
            sidecar.write_text(
                json.dumps(instance.spec, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            print(_json({
                "catalog_id": instance.catalog_id,
                "family": instance.spec["family"],
                "output": str(args.output.resolve()),
                "instance_spec": str(sidecar.resolve()),
                "interfaces": instance.interfaces,
                "purchase": instance.spec["purchase"],
            }))
            return 0

        shape = create(args.family, **parameters)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.format == "step":
            export_step(shape, args.output)
        else:
            export_stl(shape, args.output)
        spec = instance_spec(args.family, **parameters)
        print(_json({
            "family": spec["family"],
            "library_version": __version__,
            "parameters": parameters,
            "derived": spec.get("derived"),
            "output": str(args.output.resolve()),
            "format": args.format,
            "label": shape.label,
        }))
        return 0
    except CadPartsError as exc:
        print(_json({"error": type(exc).__name__, "message": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
