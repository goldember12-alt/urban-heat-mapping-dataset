from __future__ import annotations

import argparse
import logging

from src.support_layers import audit_support_layer_readiness, prepare_support_layers


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit and prepare deterministic support-layer inputs.")
    parser.add_argument("--city-ids", type=str, default="", help="Optional comma-separated subset of city IDs")
    parser.add_argument("--resolution", type=float, default=30, help="Grid resolution in meters")
    parser.add_argument("--preflight-only", action="store_true", help="Audit support-layer readiness only")
    parser.add_argument("--overwrite", action="store_true", help="Rebuild prepared outputs even if they already exist")
    return parser


def _parse_city_ids(city_ids_arg: str) -> list[int] | None:
    if not city_ids_arg.strip():
        return None
    return [int(value.strip()) for value in city_ids_arg.split(",") if value.strip()]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()

    city_ids = _parse_city_ids(args.city_ids)
    if args.preflight_only:
        result = audit_support_layer_readiness(city_ids=city_ids, resolution=args.resolution)
        print(result.summary_json_path)
        print(result.summary_csv_path)
        if not result.summary.empty:
            print(result.summary[["support_prep_ready", "feature_extraction_ready"]].value_counts().to_string())
        return

    result = prepare_support_layers(city_ids=city_ids, resolution=args.resolution, overwrite=args.overwrite)
    print(result.summary_json_path)
    print(result.summary_csv_path)
    if not result.summary.empty:
        print(result.summary[["status"]].value_counts().to_string())


if __name__ == "__main__":
    main()
