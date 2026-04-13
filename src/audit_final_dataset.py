from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.config import FINAL, MODELING
from src.modeling_config import PHASE3A_FEATURE_COLUMNS
from src.modeling_prep import audit_final_dataset


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit the canonical final dataset for modeling handoff.")
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
        help="Directory where audit artifacts should be written",
    )
    parser.add_argument(
        "--feature-columns",
        type=str,
        default=",".join(PHASE3A_FEATURE_COLUMNS),
        help="Comma-separated candidate feature columns to audit for missingness",
    )
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()
    feature_columns = [column.strip() for column in args.feature_columns.split(",") if column.strip()]

    result = audit_final_dataset(
        dataset_path=args.input_path,
        output_dir=args.output_dir,
        feature_columns=feature_columns,
    )

    print(f"dataset_path={result.dataset_path}")
    print(f"rows={result.row_count}")
    print(f"cities={result.city_count}")
    print(result.summary_json_path)
    print(result.summary_markdown_path)
    print(result.city_summary_csv_path)
    print(result.missingness_csv_path)
    print(result.missingness_by_city_csv_path)


if __name__ == "__main__":
    main()
