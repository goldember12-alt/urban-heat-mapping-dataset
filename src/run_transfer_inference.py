from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.modeling_transfer_inference import (
    DEFAULT_TOP_FRACTION,
    DEFAULT_TRANSFER_PACKAGE_DIR,
    run_transfer_inference,
)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Apply the retained six-feature transfer package to one new-city feature parquet."
    )
    parser.add_argument("--input-parquet", type=Path, required=True)
    parser.add_argument("--package-dir", type=Path, default=DEFAULT_TRANSFER_PACKAGE_DIR)
    parser.add_argument(
        "--inference-id",
        default=None,
        help="Optional deterministic output-stem override. Defaults to the input parquet stem.",
    )
    parser.add_argument("--top-fraction", type=float, default=DEFAULT_TOP_FRACTION)
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()
    result = run_transfer_inference(
        input_parquet_path=args.input_parquet,
        package_dir=args.package_dir,
        inference_id=args.inference_id,
        top_fraction=args.top_fraction,
    )
    print(result.output_dir)
    print(result.predictions_parquet_path)
    print(result.predictions_csv_path)
    print(result.summary_csv_path)
    print(result.deciles_csv_path)
    print(result.feature_missingness_path)
    print(result.markdown_path)
    print(result.metadata_path)
    print(result.figure_path)


if __name__ == "__main__":
    main()
