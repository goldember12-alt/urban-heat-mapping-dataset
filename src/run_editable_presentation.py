from __future__ import annotations

import argparse
from pathlib import Path

from src.presentation_editable_pptx_builder import build_editable_presentation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the editable native PowerPoint presentation deck."
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("docs/presentation_2026/urban_heat_transfer_presentation.pptx"),
        help="Where to write the editable pptx deck.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    output = build_editable_presentation(repo_root=repo_root, output_path=args.output_path)
    print(f"Built editable PowerPoint deck at {output}")


if __name__ == "__main__":
    main()
