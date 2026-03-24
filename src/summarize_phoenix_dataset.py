from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.city_processing import load_city_record
from src.config import DATA_PROCESSING_OUTPUTS, PROJECT_ROOT
from src.data_processing_reporting import (
    DatasetChoice,
    SummaryPaths,
    choose_city_dataset,
    compute_preprocessing_audit,
    generate_city_data_report,
)

PHOENIX_CITY_ID = 1
PHOENIX_CITY_STEM = "01_phoenix_az"
DEFAULT_MARKDOWN_PATH = DATA_PROCESSING_OUTPUTS / PHOENIX_CITY_STEM / "phoenix_data_summary.md"
DEFAULT_ASSET_DIR: Path | None = None


def choose_phoenix_dataset(project_root: Path = PROJECT_ROOT) -> DatasetChoice:
    """Return the best available Phoenix analysis dataset using the generic city-report selection logic."""
    phoenix = load_city_record(city_id=PHOENIX_CITY_ID)
    return choose_city_dataset(city=phoenix, project_root=project_root)


def generate_phoenix_summary(
    markdown_path: Path = DEFAULT_MARKDOWN_PATH,
    asset_dir: Path | None = DEFAULT_ASSET_DIR,
    project_root: Path = PROJECT_ROOT,
) -> SummaryPaths:
    """Build the Phoenix summary using the shared city data-processing reporting pipeline."""
    if asset_dir is not None:
        result = generate_city_data_report(
            city_id=PHOENIX_CITY_ID,
            markdown_path=markdown_path,
            tables_dir=asset_dir / "tables",
            figures_dir=asset_dir / "figures",
            project_root=project_root,
        )
        return result.paths

    result = generate_city_data_report(
        city_id=PHOENIX_CITY_ID,
        markdown_path=markdown_path,
        project_root=project_root,
    )
    return result.paths


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a Phoenix data-processing summary deliverable.")
    parser.add_argument(
        "--markdown-path",
        type=Path,
        default=DEFAULT_MARKDOWN_PATH,
        help="Output markdown path for the Phoenix summary.",
    )
    parser.add_argument(
        "--asset-dir",
        type=Path,
        default=None,
        help="Optional legacy bundled asset directory. When omitted, tables and figures use the split data-processing roots.",
    )
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()
    result = generate_phoenix_summary(markdown_path=args.markdown_path, asset_dir=args.asset_dir)
    print(result.markdown_path)
    print(result.tables_dir)
    print(result.figures_dir)


if __name__ == "__main__":
    main()
