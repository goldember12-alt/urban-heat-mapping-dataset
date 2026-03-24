from __future__ import annotations

import argparse
import logging

from src.data_processing_reporting import generate_all_city_data_reports


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate per-city data-processing report outputs and figures.")
    parser.add_argument("--city-ids", type=str, default="", help="Optional comma-separated subset of city IDs")
    parser.add_argument("--stop-on-error", action="store_true", help="Stop on the first city report failure")
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()
    city_ids = [int(value.strip()) for value in args.city_ids.split(",") if value.strip()] if args.city_ids else None
    result = generate_all_city_data_reports(city_ids=city_ids, continue_on_error=not args.stop_on_error)
    print(result.summary_path)
    if not result.summary.empty:
        print(result.summary[["status"]].value_counts().to_string())


if __name__ == "__main__":
    main()
