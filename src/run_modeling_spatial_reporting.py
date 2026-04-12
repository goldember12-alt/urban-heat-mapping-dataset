from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.modeling_reporting import DEFAULT_RF_FRONTIER_RUN_DIR
from src.modeling_spatial_reporting import generate_heldout_spatial_reporting_artifacts


def _parse_city_ids(raw_value: str | None) -> list[int] | None:
    if raw_value is None:
        return None
    return [int(item.strip()) for item in raw_value.split(",") if item.strip()]


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate held-out-city map exports from retained benchmark prediction artifacts."
    )
    parser.add_argument("--reference-run-dir", type=Path, default=DEFAULT_RF_FRONTIER_RUN_DIR)
    parser.add_argument("--city-ids", default=None, help="Optional comma-delimited city_id override.")
    parser.add_argument("--cities-per-climate", type=int, default=1)
    parser.add_argument("--top-fraction", type=float, default=0.10)
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()
    result = generate_heldout_spatial_reporting_artifacts(
        reference_run_dir=args.reference_run_dir,
        city_ids=_parse_city_ids(args.city_ids),
        cities_per_climate=args.cities_per_climate,
        top_fraction=args.top_fraction,
    )
    print(result.markdown_path)
    print(result.selection_table_path)
    print(result.selected_points_path)
    print(result.selected_city_summary_path)
    for figure_path in result.figure_paths:
        print(figure_path)


if __name__ == "__main__":
    main()
