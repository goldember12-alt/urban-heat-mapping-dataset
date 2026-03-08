from __future__ import annotations

import argparse
import logging

from src.feature_assembly import extract_features_for_all_cities


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract features for all cities with available grids.")
    parser.add_argument("--resolution", type=float, default=30, help="Grid resolution in meters")
    parser.add_argument("--no-save", action="store_true", help="Run extraction without writing outputs")
    parser.add_argument("--stop-on-error", action="store_true", help="Stop on first city failure")
    parser.add_argument("--city-ids", type=str, default="", help="Optional comma-separated subset of city IDs")
    parser.add_argument(
        "--existing-grids-only",
        action="store_true",
        help="Skip cities where the expected grid file does not exist",
    )
    parser.add_argument(
        "--max-cells",
        type=int,
        default=0,
        help="Optional limit on number of grid cells per city (for partial/debug runs)",
    )
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()

    city_ids = [int(x.strip()) for x in args.city_ids.split(",") if x.strip()] if args.city_ids else None
    max_cells = args.max_cells if args.max_cells > 0 else None
    result = extract_features_for_all_cities(
        resolution=args.resolution,
        save_outputs=not args.no_save,
        continue_on_error=not args.stop_on_error,
        city_ids=city_ids,
        existing_grids_only=args.existing_grids_only,
        max_cells=max_cells,
    )

    print(result.summary_path)
    if not result.summary.empty:
        print(result.summary[["status"]].value_counts().to_string())


if __name__ == "__main__":
    main()
