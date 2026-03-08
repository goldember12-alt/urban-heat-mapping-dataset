from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.city_processing import process_city
from src.config import DATA_PROCESSED
from src.load_cities import load_cities

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BatchCityProcessingSummary:
    summary: pd.DataFrame
    summary_path: Path


def process_all_cities(
    buffer_m: float = 2000,
    resolution: float = 30,
    timeout: int = 60,
    save_outputs: bool = True,
    continue_on_error: bool = True,
    city_ids: list[int] | None = None,
) -> BatchCityProcessingSummary:
    """Run study-area and grid creation for all configured cities.

    Parameters
    ----------
    buffer_m
        Buffer distance in meters around each urban area polygon.
    resolution
        Grid resolution in meters.
    timeout
        Timeout in seconds for each Census urban-area lookup request.
    save_outputs
        Whether to persist study area and grid files.
    continue_on_error
        If True, proceed to next city when one city fails.
    city_ids
        Optional subset of city IDs to process.
    """
    cities = load_cities()
    if city_ids:
        cities = cities[cities["city_id"].isin(city_ids)].copy()

    rows: list[dict[str, object]] = []

    for _, city in cities.iterrows():
        city_id = int(city["city_id"])
        city_name = str(city["city_name"])
        state = str(city["state"])
        logger.info("Batch processing city_id=%s city=%s, %s", city_id, city_name, state)

        try:
            result = process_city(
                city_id=city_id,
                buffer_m=buffer_m,
                resolution=resolution,
                timeout=timeout,
                save_outputs=save_outputs,
            )
            rows.append(
                {
                    "city_id": city_id,
                    "city_name": city_name,
                    "state": state,
                    "status": "ok",
                    "n_grid_cells": len(result.grid),
                    "study_area_path": str(result.study_area_path) if result.study_area_path else "",
                    "grid_path": str(result.grid_path) if result.grid_path else "",
                    "error": "",
                }
            )
        except Exception as exc:  # pragma: no cover - exercised via integration/manual runs
            logger.exception("City processing failed for city_id=%s", city_id)
            rows.append(
                {
                    "city_id": city_id,
                    "city_name": city_name,
                    "state": state,
                    "status": "error",
                    "n_grid_cells": 0,
                    "study_area_path": "",
                    "grid_path": "",
                    "error": str(exc),
                }
            )
            if not continue_on_error:
                raise

    summary = pd.DataFrame(rows)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    summary_path = DATA_PROCESSED / f"batch_city_processing_summary_{int(resolution)}m.csv"
    summary.to_csv(summary_path, index=False)

    logger.info("Wrote batch city processing summary: %s", summary_path)
    return BatchCityProcessingSummary(summary=summary, summary_path=summary_path)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run study-area and grid processing for all cities.")
    parser.add_argument("--buffer-m", type=float, default=2000, help="Study area buffer in meters")
    parser.add_argument("--resolution", type=float, default=30, help="Grid resolution in meters")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout per city in seconds")
    parser.add_argument("--no-save", action="store_true", help="Run without writing city outputs")
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop immediately on first city failure",
    )
    parser.add_argument(
        "--city-ids",
        type=str,
        default="",
        help="Optional comma-separated subset of city IDs",
    )
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()

    city_ids = [int(x.strip()) for x in args.city_ids.split(",") if x.strip()] if args.city_ids else None
    result = process_all_cities(
        buffer_m=args.buffer_m,
        resolution=args.resolution,
        timeout=args.timeout,
        save_outputs=not args.no_save,
        continue_on_error=not args.stop_on_error,
        city_ids=city_ids,
    )

    print(result.summary_path)
    print(result.summary[["status"]].value_counts().to_string())


if __name__ == "__main__":
    main()
