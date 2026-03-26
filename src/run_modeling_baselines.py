from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

from src.modeling_baselines import run_modeling_baselines
from src.modeling_config import BASELINE_OUTPUT_DIR, DEFAULT_FINAL_DATASET_PATH
from src.modeling_run_registry import record_model_run


def _parse_fold_list(raw_value: str | None) -> list[int] | None:
    if raw_value is None:
        return None
    return [int(item.strip()) for item in raw_value.split(",") if item.strip()]


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run first-pass held-out-city baseline models.")
    parser.add_argument("--dataset-path", type=Path, default=DEFAULT_FINAL_DATASET_PATH)
    parser.add_argument("--folds-path", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=BASELINE_OUTPUT_DIR)
    parser.add_argument("--outer-folds", default=None, help="Optional comma-delimited subset of outer folds")
    parser.add_argument(
        "--sample-rows-per-city",
        type=int,
        default=None,
        help="Optional deterministic per-city sample size for a smaller first-pass run",
    )
    parser.add_argument("--random-state", type=int, default=42)
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()
    command = subprocess.list2cmdline([sys.executable, *sys.argv])
    selected_outer_folds = _parse_fold_list(args.outer_folds)
    notes = (
        [
            "CSV compatibility fallback input used; do not assume equivalence to canonical parquet without an explicit artifact audit."
        ]
        if args.dataset_path.suffix.lower() == ".csv"
        else None
    )
    try:
        result = run_modeling_baselines(
            dataset_path=args.dataset_path,
            folds_path=args.folds_path,
            output_dir=args.output_dir,
            selected_outer_folds=selected_outer_folds,
            sample_rows_per_city=args.sample_rows_per_city,
            random_state=args.random_state,
        )
    except Exception as exc:
        record_model_run(
            model_type="baselines",
            preset=None,
            command=command,
            output_dir=args.output_dir,
            dataset_path=args.dataset_path,
            folds_path=args.folds_path,
            sample_rows_per_city=args.sample_rows_per_city,
            selected_outer_folds=selected_outer_folds,
            status="failure",
            notes=notes,
            error=exc,
        )
        raise

    record_model_run(
        model_type="baselines",
        preset=None,
        command=command,
        output_dir=args.output_dir,
        dataset_path=args.dataset_path,
        folds_path=args.folds_path,
        sample_rows_per_city=args.sample_rows_per_city,
        selected_outer_folds=selected_outer_folds,
        summary_metrics_path=result.summary_metrics_path,
        metadata_path=result.metadata_path,
        status="success",
        notes=notes,
    )
    print(result.fold_metrics_path)
    print(result.city_metrics_path)
    print(result.summary_metrics_path)
    print(result.predictions_path)
    print(result.calibration_curve_path)
    print(result.metadata_path)


if __name__ == "__main__":
    main()
