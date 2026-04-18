from __future__ import annotations

import argparse
from pathlib import Path

from src.presentation_deck_builder import build_presentation_assets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build slide art assets for the PowerPoint-first presentation deck."
    )
    parser.add_argument(
        "--presentation-dir",
        type=Path,
        default=Path("docs/presentation_2026"),
        help="Directory that holds the presentation source files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional override for the slide asset output directory.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    presentation_dir = args.presentation_dir
    output_dir = args.output_dir or presentation_dir / "build"
    written = build_presentation_assets(repo_root=repo_root, output_dir=output_dir)
    print(f"Built {len(written)} presentation asset files in {output_dir}")


if __name__ == "__main__":
    main()
