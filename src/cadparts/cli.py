"""Small JSON-first command line interface for language models and scripts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from build123d import export_step, export_stl

from . import __version__
from .catalog import create, derive, describe, list_families
from .errors import CadPartsError


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cadparts", description="Parametric standard parts catalog")
    parser.add_argument("--version", action="version", version=f"cadparts {__version__}")
    subcommands = parser.add_subparsers(dest="command", required=True)

    list_command = subcommands.add_parser("list", help="list registered families")
    list_command.add_argument("--category")
    list_command.add_argument("--standard-system")

    describe_command = subcommands.add_parser("describe", help="describe one family")
    describe_command.add_argument("family")

    derive_command = subcommands.add_parser("derive", help="calculate dimensions without building geometry")
    derive_command.add_argument("family")
    derive_command.add_argument("--params", required=True, help="JSON object of family parameters")

    build_command = subcommands.add_parser("build", help="create and export one part")
    build_command.add_argument("family")
    build_command.add_argument("--params", required=True, help="JSON object of family parameters")
    build_command.add_argument("--output", required=True, type=Path)
    build_command.add_argument("--format", choices=("step", "stl"), default="step")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            print(_json(list_families(category=args.category, standard_system=args.standard_system)))
            return 0
        if args.command == "describe":
            print(_json(describe(args.family)))
            return 0

        try:
            parameters = json.loads(args.params)
        except json.JSONDecodeError as exc:
            parser.error(f"--params is not valid JSON: {exc.msg}")
        if not isinstance(parameters, dict):
            parser.error("--params must decode to a JSON object")

        if args.command == "derive":
            print(_json(derive(args.family, **parameters)))
            return 0

        shape = create(args.family, **parameters)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.format == "step":
            export_step(shape, args.output)
        else:
            export_stl(shape, args.output)
        print(_json({
            "family": args.family,
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
