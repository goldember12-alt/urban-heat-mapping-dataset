from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.env_bootstrap import load_local_env, log_loaded_local_env

_LOADED_ENV_PATH = load_local_env(Path(__file__).resolve().parents[1])
from src.acquisition_orchestration import run_acquisition_orchestration


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run raw support acquisition, support prep, and AppEEARS NDVI/ECOSTRESS acquisition in sequence."
    )
    parser.add_argument("--city-ids", type=str, default="", help="Optional comma-separated subset of city IDs")
    parser.add_argument(
        "--all-missing",
        action="store_true",
        help="Target only missing support outputs and incomplete AppEEARS cities",
    )
    parser.add_argument("--start-date", type=str, required=True, help="Start date in YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, required=True, help="End date in YYYY-MM-DD")
    parser.add_argument("--resolution", type=float, default=30, help="Grid resolution in meters")
    parser.add_argument("--force-raw", action="store_true", help="Rebuild raw support outputs even if they already exist")
    parser.add_argument("--overwrite-support", action="store_true", help="Rebuild prepared support outputs even if they already exist")
    return parser


def _parse_city_ids(city_ids_arg: str) -> list[int] | None:
    if not city_ids_arg.strip():
        return None
    return [int(value.strip()) for value in city_ids_arg.split(",") if value.strip()]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    log_loaded_local_env(_LOADED_ENV_PATH)
    args = _build_arg_parser().parse_args()

    result = run_acquisition_orchestration(
        start_date=args.start_date.strip(),
        end_date=args.end_date.strip(),
        city_ids=_parse_city_ids(args.city_ids),
        all_missing=args.all_missing,
        resolution=args.resolution,
        force_raw=args.force_raw,
        overwrite_support=args.overwrite_support,
    )

    print(result.summary_json_path)
    print(result.summary_csv_path)
    if not result.summary.empty:
        print(result.summary[["stage", "n_effective_cities"]].to_string(index=False))


if __name__ == "__main__":
    main()
