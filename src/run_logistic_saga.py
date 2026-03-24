from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.modeling_config import (
    DEFAULT_FEATURE_COLUMNS,
    DEFAULT_FINAL_DATASET_PATH,
    DEFAULT_TUNING_PRESET,
    LOGISTIC_OUTPUT_DIR,
    VALID_TUNING_PRESETS,
)
from src.modeling_runner import run_logistic_saga_model


def _parse_csv_list(raw_value: str) -> list[str]:
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _parse_fold_list(raw_value: str | None) -> list[int] | None:
    if raw_value is None:
        return None
    return [int(item.strip()) for item in raw_value.split(",") if item.strip()]


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run grouped logistic SAGA hotspot modeling.")
    parser.add_argument("--dataset-path", type=Path, default=DEFAULT_FINAL_DATASET_PATH)
    parser.add_argument("--folds-path", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=LOGISTIC_OUTPUT_DIR)
    parser.add_argument("--feature-columns", default=",".join(DEFAULT_FEATURE_COLUMNS))
    parser.add_argument("--outer-folds", default=None, help="Optional comma-delimited subset of outer folds")
    parser.add_argument("--sample-rows-per-city", type=int, default=None)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--inner-cv-splits", type=int, default=None)
    parser.add_argument("--grid-search-n-jobs", type=int, default=-1)
    parser.add_argument(
        "--tuning-preset",
        choices=VALID_TUNING_PRESETS,
        default=DEFAULT_TUNING_PRESET,
        help="Use 'smoke' for faster sampled verification defaults or 'full' for the heavier historical search.",
    )
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()
    result = run_logistic_saga_model(
        dataset_path=args.dataset_path,
        folds_path=args.folds_path,
        output_dir=args.output_dir,
        feature_columns=_parse_csv_list(args.feature_columns),
        selected_outer_folds=_parse_fold_list(args.outer_folds),
        sample_rows_per_city=args.sample_rows_per_city,
        random_state=args.random_state,
        inner_cv_splits=args.inner_cv_splits,
        grid_search_n_jobs=args.grid_search_n_jobs,
        tuning_preset=args.tuning_preset,
    )
    print(result.fold_metrics_path)
    print(result.city_metrics_path)
    print(result.summary_metrics_path)
    print(result.best_params_path)
    print(result.predictions_path)
    print(result.calibration_curve_path)
    print(result.metadata_path)


if __name__ == "__main__":
    main()
