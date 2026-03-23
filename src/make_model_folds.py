from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.config import FINAL, MODELING
from src.modeling_prep import make_model_folds


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create deterministic city-level outer folds for modeling.")
    parser.add_argument(
        "--input-path",
        type=Path,
        default=FINAL / "final_dataset.parquet",
        help="Path to the canonical final dataset parquet",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=MODELING,
        help="Directory where fold artifacts should be written",
    )
    parser.add_argument(
        "--n-splits",
        type=int,
        default=5,
        help="Number of deterministic city-level outer folds to create",
    )
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()

    result = make_model_folds(
        dataset_path=args.input_path,
        output_dir=args.output_dir,
        n_splits=args.n_splits,
    )

    print(f"dataset_path={result.dataset_path}")
    print(f"rows={result.n_rows}")
    print(f"cities={result.n_cities}")
    print(f"folds={result.fold_table['outer_fold'].nunique()}")
    print(result.parquet_path)
    print(result.csv_path)


if __name__ == "__main__":
    main()
