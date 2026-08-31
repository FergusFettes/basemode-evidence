"""Command-line interface for validation and compilation."""

from __future__ import annotations

import argparse
import json
import sys

from .compile import compile_dataset
from .validate import ValidationError, validate_bundle, validate_pr


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="basemode-evidence")
    commands = root.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="validate one evidence bundle")
    validate.add_argument("path")
    validate.add_argument(
        "--no-path-check", action="store_true", help="skip repository path/id/month checks"
    )

    pr = commands.add_parser("validate-pr", help="validate a contribution-only revision range")
    pr.add_argument("--base", required=True)
    pr.add_argument("--head", required=True)

    compile_command = commands.add_parser("compile", help="compile public dataset artifacts")
    compile_command.add_argument("--output", default=None)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "validate":
            result = validate_bundle(args.path, enforce_path=not args.no_path_check)
            print(result.summary)
        elif args.command == "validate-pr":
            result = validate_pr(args.base, args.head)
            print(result.summary)
        else:
            manifest = compile_dataset(output=args.output)
            print(json.dumps(manifest, indent=2, sort_keys=True))
    except ValidationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
