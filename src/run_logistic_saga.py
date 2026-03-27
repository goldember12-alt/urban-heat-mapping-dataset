from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.modeling_config import (
    DEFAULT_FEATURE_COLUMNS,
    DEFAULT_FINAL_DATASET_PATH,
    DEFAULT_LOGISTIC_MAX_ITER,
    DEFAULT_LOGISTIC_TOL,
    DEFAULT_TUNING_PRESET,
    LOGISTIC_OUTPUT_DIR,
    VALID_TUNING_PRESETS,
)
from src.modeling_run_registry import build_cli_command, record_model_run
from src.modeling_runner import run_logistic_saga_model


def _parse_csv_list(raw_value: str) -> list[str]:
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _parse_fold_list(raw_value: str | None) -> list[int] | None:
    if raw_value is None:
        return None
    return [int(item.strip()) for item in raw_value.split(",") if item.strip()]


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run grouped logistic SAGA hotspot modeling on the canonical parquet-first dataset.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=DEFAULT_FINAL_DATASET_PATH,
        help="Canonical modeling input. Defaults to final_dataset.parquet; CSV remains supported as a compatibility fallback only.",
    )
    parser.add_argument(
        "--folds-path",
        type=Path,
        default=None,
        help="Optional explicit folds path. When omitted, the runner prefers city_outer_folds.parquet and falls back to CSV only if parquet is absent.",
    )
    parser.add_argument("--output-dir", type=Path, default=LOGISTIC_OUTPUT_DIR)
    parser.add_argument("--feature-columns", default=",".join(DEFAULT_FEATURE_COLUMNS))
    parser.add_argument("--outer-folds", default=None, help="Optional comma-delimited subset of outer folds")
    parser.add_argument(
        "--sample-rows-per-city",
        type=int,
        default=None,
        help="Optional per-city sample cap for bounded smoke verification without changing the parquet-first default input path.",
    )
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--inner-cv-splits", type=int, default=None)
    parser.add_argument(
        "--max-iter",
        type=int,
        default=DEFAULT_LOGISTIC_MAX_ITER,
        help="Maximum SAGA iterations for each logistic fit. Increase this if real-data elastic-net candidates still emit convergence warnings.",
    )
    parser.add_argument(
        "--tol",
        type=float,
        default=DEFAULT_LOGISTIC_TOL,
        help="SAGA convergence tolerance. A slightly looser tolerance can remove real-data convergence warnings without the runtime cost of much larger max_iter values.",
    )
    parser.add_argument(
        "--grid-search-n-jobs",
        type=int,
        default=-1,
        help="GridSearchCV worker count. Keep the default for normal runs; constrained sandboxes may still prefer 1 for smoke verification.",
    )
    parser.add_argument(
        "--tuning-preset",
        choices=VALID_TUNING_PRESETS,
        default=DEFAULT_TUNING_PRESET,
        help="Use 'smoke' for the bounded default verification search or 'full' for the broader tuning search.",
    )
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()
    command = build_cli_command()
    selected_outer_folds = _parse_fold_list(args.outer_folds)
    notes = (
        [
            "CSV compatibility fallback input used; do not assume equivalence to canonical parquet without an explicit artifact audit."
        ]
        if args.dataset_path.suffix.lower() == ".csv"
        else None
    )
    try:
        result = run_logistic_saga_model(
            dataset_path=args.dataset_path,
            folds_path=args.folds_path,
            output_dir=args.output_dir,
            feature_columns=_parse_csv_list(args.feature_columns),
            selected_outer_folds=selected_outer_folds,
            sample_rows_per_city=args.sample_rows_per_city,
            random_state=args.random_state,
            inner_cv_splits=args.inner_cv_splits,
            grid_search_n_jobs=args.grid_search_n_jobs,
            max_iter=args.max_iter,
            tol=args.tol,
            tuning_preset=args.tuning_preset,
            command=command,
        )
    except Exception as exc:
        record_model_run(
            model_type="logistic_saga",
            preset=args.tuning_preset,
            command=command,
            output_dir=args.output_dir,
            dataset_path=args.dataset_path,
            folds_path=args.folds_path,
            sample_rows_per_city=args.sample_rows_per_city,
            selected_outer_folds=selected_outer_folds,
            grid_search_n_jobs=args.grid_search_n_jobs,
            status="failure",
            notes=notes,
            error=exc,
        )
        raise

    record_model_run(
        model_type="logistic_saga",
        preset=args.tuning_preset,
        command=command,
        output_dir=args.output_dir,
        dataset_path=args.dataset_path,
        folds_path=args.folds_path,
        sample_rows_per_city=args.sample_rows_per_city,
        selected_outer_folds=selected_outer_folds,
        grid_search_n_jobs=args.grid_search_n_jobs,
        summary_metrics_path=result.summary_metrics_path,
        metadata_path=result.metadata_path,
        status="success",
        notes=notes,
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
