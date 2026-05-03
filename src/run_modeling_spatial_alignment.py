from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.modeling_config import DEFAULT_FINAL_DATASET_PATH, DEFAULT_FOLDS_PARQUET_PATH
from src.modeling_spatial_alignment import (
    DEFAULT_PREDICTION_BATCH_SIZE,
    DEFAULT_REFERENCE_RUN_DIR,
    DEFAULT_SMOOTHING_RADII_M,
    DEFAULT_SPATIAL_ALIGNMENT_FIGURE_DIR,
    DEFAULT_SPATIAL_ALIGNMENT_OUTPUT_DIR,
    run_spatial_alignment_workflow,
)


def _parse_int_list(raw_value: str | None) -> list[int] | None:
    if raw_value is None or not raw_value.strip():
        return None
    return [int(item.strip()) for item in raw_value.split(",") if item.strip()]


def _parse_float_list(raw_value: str) -> list[float]:
    return [float(item.strip()) for item in raw_value.split(",") if item.strip()]


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run supplemental full-city held-out smoothed-surface spatial alignment diagnostics "
            "for representative cities or all held-out cities."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--reference-run-dir", type=Path, default=DEFAULT_REFERENCE_RUN_DIR)
    parser.add_argument("--dataset-path", type=Path, default=DEFAULT_FINAL_DATASET_PATH)
    parser.add_argument("--folds-path", type=Path, default=DEFAULT_FOLDS_PARQUET_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_SPATIAL_ALIGNMENT_OUTPUT_DIR)
    parser.add_argument("--figures-dir", type=Path, default=DEFAULT_SPATIAL_ALIGNMENT_FIGURE_DIR)
    parser.add_argument("--model-name", default="random_forest", choices=["random_forest"])
    parser.add_argument("--sample-rows-per-city", type=int, default=5000)
    parser.add_argument(
        "--city-selection",
        default="representative_with_denver",
        choices=["representative_with_denver", "denver_only", "all"],
        help="Representative-city selection rule. Ignored when --city-ids is provided.",
    )
    parser.add_argument("--city-ids", default=None, help="Optional comma-delimited explicit city_id list.")
    parser.add_argument(
        "--smoothing-radii-m",
        default=",".join(str(int(value)) for value in DEFAULT_SMOOTHING_RADII_M),
        help="Comma-delimited smoothing radii in meters.",
    )
    parser.add_argument("--threshold-fraction", type=float, default=0.10)
    parser.add_argument("--grid-search-n-jobs", type=int, default=1)
    parser.add_argument("--model-n-jobs", type=int, default=1)
    parser.add_argument(
        "--prediction-batch-size",
        type=int,
        default=DEFAULT_PREDICTION_BATCH_SIZE,
        help="Rows per predict_proba batch for full-city scoring. Use 0 to score in one batch.",
    )
    parser.add_argument(
        "--skip-existing-predictions",
        action="store_true",
        help="Reuse existing full-city prediction parquet files when present.",
    )
    parser.add_argument(
        "--make-maps",
        action="store_true",
        help="Generate optional five-panel smoothed-surface spatial-alignment maps from full-city predictions.",
    )
    parser.add_argument(
        "--map-scale-label",
        default="medium",
        choices=["medium"],
        help="Smoothing scale to map. Medium is the only implemented map scale in this pass.",
    )
    parser.add_argument(
        "--map-city-ids",
        default=None,
        help="Optional comma-delimited city_id list for map generation only.",
    )
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()
    prediction_batch_size = None if int(args.prediction_batch_size) <= 0 else int(args.prediction_batch_size)
    result = run_spatial_alignment_workflow(
        reference_run_dir=args.reference_run_dir,
        dataset_path=args.dataset_path,
        folds_path=args.folds_path,
        output_dir=args.output_dir,
        model_name=args.model_name,
        sample_rows_per_city=args.sample_rows_per_city,
        city_selection=args.city_selection,
        city_ids=_parse_int_list(args.city_ids),
        smoothing_radii_m=_parse_float_list(args.smoothing_radii_m),
        threshold_fraction=args.threshold_fraction,
        grid_search_n_jobs=args.grid_search_n_jobs,
        model_n_jobs=args.model_n_jobs,
        prediction_batch_size=prediction_batch_size,
        skip_existing_predictions=args.skip_existing_predictions,
        make_maps=args.make_maps,
        map_scale_label=args.map_scale_label,
        map_city_ids=_parse_int_list(args.map_city_ids),
        figures_dir=args.figures_dir,
    )
    print(result.selection_table_path)
    print(result.metrics_table_path)
    print(result.summary_markdown_path)
    if result.map_manifest_table_path is not None:
        print(result.map_manifest_table_path)
    for prediction_path in result.prediction_paths:
        print(prediction_path)
    for map_path in result.map_paths:
        print(map_path)


if __name__ == "__main__":
    main()
