from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.config import FINAL
from src.model_baselines import (
    DEFAULT_BASELINE_MODELS,
    DEFAULT_BASELINE_OUTPUT_DIR,
    DEFAULT_DECISION_STUMP_MIN_LEAF_ROWS,
    DEFAULT_LOGISTIC_L2,
    DEFAULT_MAX_LOGISTIC_ITERATIONS,
    DEFAULT_TREE_SAMPLE_PER_CITY,
    run_baseline_modeling,
)
from src.modeling_prep import DEFAULT_FEATURE_COLUMNS


def _parse_csv_list(raw_value: str) -> list[str]:
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _parse_fold_list(raw_value: str | None) -> list[int] | None:
    if raw_value is None:
        return None
    return [int(item.strip()) for item in raw_value.split(",") if item.strip()]


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train city-held-out baseline hotspot models.")
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=FINAL / "final_dataset.parquet",
        help="Path to the canonical final dataset parquet",
    )
    parser.add_argument(
        "--folds-path",
        type=Path,
        default=None,
        help="Optional explicit path to city_outer_folds.parquet or city_outer_folds.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_BASELINE_OUTPUT_DIR,
        help="Directory where baseline modeling artifacts should be written",
    )
    parser.add_argument(
        "--feature-columns",
        default=",".join(DEFAULT_FEATURE_COLUMNS),
        help="Comma-delimited safe baseline feature columns to load from parquet",
    )
    parser.add_argument(
        "--models",
        default=",".join(DEFAULT_BASELINE_MODELS),
        help="Comma-delimited baseline models to run: logistic_regression, decision_stump",
    )
    parser.add_argument(
        "--outer-folds",
        default=None,
        help="Optional comma-delimited subset of outer folds to run",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=250_000,
        help="Parquet scanner batch size",
    )
    parser.add_argument(
        "--max-logistic-iterations",
        type=int,
        default=DEFAULT_MAX_LOGISTIC_ITERATIONS,
        help="Maximum Newton iterations for the streaming logistic baseline",
    )
    parser.add_argument(
        "--logistic-l2-penalty",
        type=float,
        default=DEFAULT_LOGISTIC_L2,
        help="Ridge penalty applied to non-intercept logistic coefficients",
    )
    parser.add_argument(
        "--tree-sample-per-city",
        type=int,
        default=DEFAULT_TREE_SAMPLE_PER_CITY,
        help="Maximum train-fold rows per city used for the decision-stump comparison",
    )
    parser.add_argument(
        "--decision-stump-min-leaf-rows",
        type=int,
        default=DEFAULT_DECISION_STUMP_MIN_LEAF_ROWS,
        help="Minimum sample rows allowed on each side of a stump split",
    )
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()

    result = run_baseline_modeling(
        dataset_path=args.dataset_path,
        folds_path=args.folds_path,
        output_dir=args.output_dir,
        feature_columns=_parse_csv_list(args.feature_columns),
        models=_parse_csv_list(args.models),
        batch_size=args.batch_size,
        max_logistic_iterations=args.max_logistic_iterations,
        logistic_l2_penalty=args.logistic_l2_penalty,
        tree_sample_per_city=args.tree_sample_per_city,
        decision_stump_min_leaf_rows=args.decision_stump_min_leaf_rows,
        selected_outer_folds=_parse_fold_list(args.outer_folds),
    )

    print(result.fold_metrics_path)
    print(result.overall_metrics_path)
    print(result.predictions_dir)
    print(result.assumptions_path)
    print(result.summary_json_path)
    print(result.model_artifacts_dir)


if __name__ == "__main__":
    main()
