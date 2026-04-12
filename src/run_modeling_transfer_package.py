from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.modeling_reporting import DEFAULT_RF_FRONTIER_RUN_DIR
from src.modeling_transfer_package import build_final_transfer_package


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fit the retained benchmark-selected model on all cities and package it for transfer-oriented use."
    )
    parser.add_argument("--reference-run-dir", type=Path, default=DEFAULT_RF_FRONTIER_RUN_DIR)
    parser.add_argument("--dataset-path", type=Path, default=Path("data_processed/final/final_dataset.parquet"))
    parser.add_argument("--folds-path", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument(
        "--sample-rows-per-city",
        type=int,
        default=None,
        help="Optional override. When omitted, the package reuses the retained reference run's sample cap.",
    )
    parser.add_argument("--model-n-jobs", type=int, default=None)
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()
    result = build_final_transfer_package(
        reference_run_dir=args.reference_run_dir,
        dataset_path=args.dataset_path,
        folds_path=args.folds_path,
        output_dir=args.output_dir,
        sample_rows_per_city=args.sample_rows_per_city,
        model_n_jobs=args.model_n_jobs,
    )
    print(result.output_dir)
    print(result.model_artifact_path)
    print(result.metadata_path)
    print(result.feature_contract_path)
    print(result.preprocessing_manifest_path)
    print(result.hyperparameter_summary_path)
    print(result.selected_hyperparameters_path)
    print(result.training_city_summary_path)
    if result.training_sample_diagnostics_path is not None:
        print(result.training_sample_diagnostics_path)


if __name__ == "__main__":
    main()
