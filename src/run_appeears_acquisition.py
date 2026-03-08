from __future__ import annotations

import argparse
import logging

from src.appeears_acquisition import run_appeears_acquisition


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run AppEEARS acquisition for NDVI or ECOSTRESS.")
    parser.add_argument(
        "--product-type",
        required=True,
        choices=["ndvi", "ecostress"],
        help="Acquisition product group to run",
    )
    parser.add_argument("--city-ids", type=str, default="", help="Optional comma-separated subset of city IDs")
    parser.add_argument("--start-date", required=True, type=str, help="Start date in YYYY-MM-DD")
    parser.add_argument("--end-date", required=True, type=str, help="End date in YYYY-MM-DD")
    parser.add_argument("--product", type=str, default="", help="Optional AppEEARS product override")
    parser.add_argument("--layer", type=str, default="", help="Optional AppEEARS layer override")

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--submit-only", action="store_true", help="Submit tasks only")
    mode.add_argument("--poll-only", action="store_true", help="Poll existing tasks only")
    mode.add_argument("--download-only", action="store_true", help="Download completed tasks only")

    parser.add_argument(
        "--retry-incomplete",
        action="store_true",
        help="Attempt only cities that are not currently marked completed in summary state",
    )
    return parser


def _parse_city_ids(city_ids_arg: str) -> list[int] | None:
    if not city_ids_arg.strip():
        return None
    return [int(value.strip()) for value in city_ids_arg.split(",") if value.strip()]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()

    result = run_appeears_acquisition(
        product_type=args.product_type,
        city_ids=_parse_city_ids(args.city_ids),
        start_date=args.start_date,
        end_date=args.end_date,
        submit_only=args.submit_only,
        poll_only=args.poll_only,
        download_only=args.download_only,
        retry_incomplete=args.retry_incomplete,
        product=args.product.strip() or None,
        layer=args.layer.strip() or None,
    )

    print(result.summary_json_path)
    print(result.summary_csv_path)
    if not result.summary.empty:
        print(result.summary[["status"]].value_counts().to_string())


if __name__ == "__main__":
    main()
