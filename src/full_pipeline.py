from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.batch_city_processing import BatchCityProcessingSummary, process_all_cities
from src.feature_assembly import BatchFeatureResult, FinalDatasetResult, assemble_final_dataset, extract_features_for_all_cities

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineRunResult:
    city_processing_summary: BatchCityProcessingSummary | None
    feature_extraction_summary: BatchFeatureResult | None
    final_dataset_result: FinalDatasetResult | None
    blocked_stages: list[str]


def _blocked_stages_from_feature_summary(summary_df: pd.DataFrame | None) -> list[str]:
    if summary_df is None or summary_df.empty or "blocked_stages" not in summary_df.columns:
        return []

    blocked: set[str] = set()
    for value in summary_df["blocked_stages"].fillna(""):
        for stage in str(value).split(";"):
            stage_name = stage.strip()
            if stage_name:
                blocked.add(stage_name)
    return sorted(blocked)


def run_full_pipeline(
    buffer_m: float = 2000,
    resolution: float = 30,
    timeout: int = 60,
    save_outputs: bool = True,
    continue_on_error: bool = True,
    city_ids: list[int] | None = None,
    max_cells: int | None = None,
    run_city_processing: bool = True,
    run_feature_extraction: bool = True,
    run_final_assembly: bool = True,
    existing_grids_only: bool = False,
) -> PipelineRunResult:
    """Run boundary/grid batch, per-city feature assembly, and final merge."""
    city_processing_summary: BatchCityProcessingSummary | None = None
    feature_extraction_summary: BatchFeatureResult | None = None
    final_dataset_result: FinalDatasetResult | None = None

    if run_city_processing:
        logger.info("Running stage 1: batch city processing")
        city_processing_summary = process_all_cities(
            buffer_m=buffer_m,
            resolution=resolution,
            timeout=timeout,
            save_outputs=save_outputs,
            continue_on_error=continue_on_error,
            city_ids=city_ids,
        )

    if run_feature_extraction:
        logger.info("Running stages 2-6: feature extraction")
        feature_extraction_summary = extract_features_for_all_cities(
            resolution=resolution,
            save_outputs=save_outputs,
            continue_on_error=continue_on_error,
            city_ids=city_ids,
            existing_grids_only=existing_grids_only,
            max_cells=max_cells,
        )

    if run_final_assembly:
        logger.info("Running stage 7: final dataset assembly")
        try:
            final_dataset_result = assemble_final_dataset()
        except FileNotFoundError:
            logger.warning("Final dataset assembly skipped because no per-city feature tables were found")

    blocked_stages = _blocked_stages_from_feature_summary(
        feature_extraction_summary.summary if feature_extraction_summary is not None else None
    )

    return PipelineRunResult(
        city_processing_summary=city_processing_summary,
        feature_extraction_summary=feature_extraction_summary,
        final_dataset_result=final_dataset_result,
        blocked_stages=blocked_stages,
    )


def _parse_city_ids(city_ids_arg: str) -> list[int] | None:
    if not city_ids_arg.strip():
        return None
    return [int(x.strip()) for x in city_ids_arg.split(",") if x.strip()]


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run full urban heat pipeline across available stages.")
    parser.add_argument("--buffer-m", type=float, default=2000, help="Study-area buffer distance in meters")
    parser.add_argument("--resolution", type=float, default=30, help="Grid resolution in meters")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout per city boundary lookup in seconds")
    parser.add_argument("--city-ids", type=str, default="", help="Optional comma-separated subset of city IDs")
    parser.add_argument("--no-save", action="store_true", help="Run without writing outputs")
    parser.add_argument("--stop-on-error", action="store_true", help="Stop on first city failure")
    parser.add_argument(
        "--max-cells",
        type=int,
        default=0,
        help="Optional limit on grid cells per city (for partial/debug runs)",
    )
    parser.add_argument(
        "--skip-city-processing",
        action="store_true",
        help="Skip stage 1 (batch city study-area and grid generation)",
    )
    parser.add_argument(
        "--skip-feature-extraction",
        action="store_true",
        help="Skip stages 2-6 (feature extraction and per-city assembly)",
    )
    parser.add_argument(
        "--skip-final-assembly",
        action="store_true",
        help="Skip stage 7 (merged final dataset assembly)",
    )
    parser.add_argument(
        "--existing-grids-only",
        action="store_true",
        help="Skip feature extraction for cities missing the expected grid file",
    )
    return parser


def _print_if_path(value: Path | None) -> None:
    if value is not None:
        print(value)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()

    max_cells = args.max_cells if args.max_cells > 0 else None
    result = run_full_pipeline(
        buffer_m=args.buffer_m,
        resolution=args.resolution,
        timeout=args.timeout,
        save_outputs=not args.no_save,
        continue_on_error=not args.stop_on_error,
        city_ids=_parse_city_ids(args.city_ids),
        max_cells=max_cells,
        run_city_processing=not args.skip_city_processing,
        run_feature_extraction=not args.skip_feature_extraction,
        run_final_assembly=not args.skip_final_assembly,
        existing_grids_only=args.existing_grids_only,
    )

    if result.city_processing_summary is not None:
        _print_if_path(result.city_processing_summary.summary_path)
        if not result.city_processing_summary.summary.empty:
            print(result.city_processing_summary.summary[["status"]].value_counts().to_string())

    if result.feature_extraction_summary is not None:
        _print_if_path(result.feature_extraction_summary.summary_path)
        if not result.feature_extraction_summary.summary.empty:
            print(result.feature_extraction_summary.summary[["status"]].value_counts().to_string())

    if result.final_dataset_result is not None:
        _print_if_path(result.final_dataset_result.parquet_path)
        _print_if_path(result.final_dataset_result.csv_path)
        print(f"rows={len(result.final_dataset_result.final_df)}")

    if result.blocked_stages:
        print(f"blocked_stages={';'.join(result.blocked_stages)}")


if __name__ == "__main__":
    main()
