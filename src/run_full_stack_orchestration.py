from __future__ import annotations

import argparse
import logging

from src.feature_assembly import CELL_FILTER_CORE_CITY, CELL_FILTER_STUDY_AREA
from src.full_stack_orchestration import run_full_stack_orchestration


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run per-city raw support acquisition, support prep, AppEEARS acquisition, and feature assembly."
    )
    parser.add_argument("--city-ids", type=str, default="", help="Optional comma-separated subset of city IDs")
    parser.add_argument(
        "--all-missing",
        action="store_true",
        help="Target only cities missing some full-stack output or stage completion",
    )
    parser.add_argument("--start-date", type=str, required=True, help="Start date in YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, required=True, help="End date in YYYY-MM-DD")
    parser.add_argument("--resolution", type=float, default=30, help="Grid resolution in meters")
    parser.add_argument(
        "--cell-filter-mode",
        type=str,
        default=CELL_FILTER_STUDY_AREA,
        choices=[CELL_FILTER_STUDY_AREA, CELL_FILTER_CORE_CITY],
        help="Keep all study-area cells or only core-city cells in feature assembly outputs",
    )
    parser.add_argument("--force-raw", action="store_true", help="Rebuild raw support outputs even if they already exist")
    parser.add_argument("--overwrite-support", action="store_true", help="Rebuild prepared support outputs even if they already exist")
    parser.add_argument("--overwrite-features", action="store_true", help="Rebuild city feature outputs even if they already exist")
    parser.add_argument(
        "--max-cells",
        type=int,
        default=0,
        help="Optional limit on number of grid cells per city during feature assembly",
    )
    return parser


def _parse_city_ids(city_ids_arg: str) -> list[int] | None:
    if not city_ids_arg.strip():
        return None
    return [int(value.strip()) for value in city_ids_arg.split(",") if value.strip()]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()

    result = run_full_stack_orchestration(
        start_date=args.start_date.strip(),
        end_date=args.end_date.strip(),
        city_ids=_parse_city_ids(args.city_ids),
        all_missing=args.all_missing,
        resolution=args.resolution,
        cell_filter_mode=args.cell_filter_mode,
        force_raw=args.force_raw,
        overwrite_support=args.overwrite_support,
        overwrite_features=args.overwrite_features,
        max_cells=args.max_cells if args.max_cells > 0 else None,
    )

    print(result.summary_json_path)
    print(result.summary_csv_path)
    if not result.summary.empty:
        print(result.summary[["overall_status"]].value_counts().to_string())


if __name__ == "__main__":
    main()
