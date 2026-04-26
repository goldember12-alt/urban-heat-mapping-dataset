"""CLI entrypoint for final-report artifact generation."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.report_artifacts import generate_report_artifacts


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Generate final-report tables and figures from retained artifacts."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root. Defaults to the current working directory.",
    )
    return parser.parse_args()


def main() -> None:
    """Run final-report artifact generation."""

    args = parse_args()
    outputs = generate_report_artifacts(args.project_root.resolve())
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
