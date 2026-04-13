from __future__ import annotations

import argparse
import logging

from src.feature_assembly import (
    backfill_phase3a_bundle_for_all_cities,
    backfill_phase3a_bundle_for_city,
)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Backfill the bounded Phase 3A NLCD neighborhood-context bundle into existing per-city feature artifacts "
            "without rerunning NDVI or ECOSTRESS acquisition."
        )
    )
    selector = parser.add_mutually_exclusive_group(required=False)
    selector.add_argument("--city-id", type=int, help="Optional single city ID from cities.csv")
    selector.add_argument("--city-name", type=str, help="Optional single city name from cities.csv")
    parser.add_argument("--city-ids", type=str, default="", help="Optional comma-separated subset of city IDs")
    parser.add_argument("--resolution", type=float, default=30, help="Grid resolution in meters")
    parser.add_argument(
        "--update-gpkg",
        action="store_true",
        help="Also rewrite existing per-city GeoPackages. Leave this off for the faster parquet-first batch backfill path.",
    )
    parser.add_argument("--stop-on-error", action="store_true", help="Stop on first city failure in batch mode")
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()

    if args.city_id is not None or args.city_name is not None:
        result = backfill_phase3a_bundle_for_city(
            city_id=args.city_id,
            city_name=args.city_name,
            resolution=args.resolution,
            update_gpkg=args.update_gpkg,
        )
        print(f"city_id={int(result.city['city_id'])} city_name={result.city['city_name']}")
        print(f"rows={result.n_rows}")
        print(f"updated_columns={';'.join(result.updated_columns)}")
        if result.city_features_parquet_path:
            print(result.city_features_parquet_path)
        if result.city_features_gpkg_path:
            print(result.city_features_gpkg_path)
        return

    city_ids = [int(value.strip()) for value in args.city_ids.split(",") if value.strip()] if args.city_ids else None
    result = backfill_phase3a_bundle_for_all_cities(
        resolution=args.resolution,
        city_ids=city_ids,
        continue_on_error=not args.stop_on_error,
        update_gpkg=args.update_gpkg,
    )
    print(result.summary_path)
    if not result.summary.empty:
        print(result.summary[["status"]].value_counts().to_string())


if __name__ == "__main__":
    main()
