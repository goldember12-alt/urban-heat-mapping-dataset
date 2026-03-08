from __future__ import annotations

import argparse
import logging

from src.raw_data_acquisition import run_raw_data_acquisition


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Acquire deterministic raw DEM, NLCD, and hydro inputs.")
    parser.add_argument(
        "--city-ids",
        nargs="+",
        type=int,
        help="Optional subset of city IDs. Accepts space-separated values, for example: --city-ids 1 2 3",
    )
    parser.add_argument(
        "--dataset",
        default="all",
        choices=["all", "dem", "nlcd", "hydro"],
        help="Support-layer dataset group to acquire",
    )
    parser.add_argument("--resolution", type=float, default=30, help="Grid resolution in meters")
    parser.add_argument(
        "--all-missing",
        action="store_true",
        help="Only run cities/datasets that are currently missing from support-layer readiness",
    )
    parser.add_argument("--force", action="store_true", help="Rebuild requested outputs even if they already exist")
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()

    result = run_raw_data_acquisition(
        dataset=args.dataset,
        city_ids=args.city_ids,
        resolution=args.resolution,
        all_missing=args.all_missing,
        force=args.force,
    )

    print(result.summary_json_path)
    print(result.summary_csv_path)
    if not result.summary.empty:
        print(result.summary[["dataset", "status"]].value_counts().to_string())


if __name__ == "__main__":
    main()
