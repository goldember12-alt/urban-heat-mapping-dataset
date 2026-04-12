from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.modeling_config import DEFAULT_FEATURE_COLUMNS, DEFAULT_FINAL_DATASET_PATH
from src.modeling_supplemental import (
    DEFAULT_FEATURE_IMPORTANCE_LOGISTIC_RUN_DIR,
    DEFAULT_FEATURE_IMPORTANCE_RF_RUN_DIR,
    DEFAULT_RF_PERMUTATION_REPEATS,
    DEFAULT_WITHIN_CITY_CITY_ERROR_TABLE_PATH,
    DEFAULT_WITHIN_CITY_LOGISTIC_REFERENCE_RUN_DIR,
    DEFAULT_WITHIN_CITY_RF_REFERENCE_RUN_DIR,
    DEFAULT_WITHIN_CITY_SAMPLE_ROWS_PER_CITY,
    DEFAULT_WITHIN_CITY_SPLIT_SEEDS,
    DEFAULT_WITHIN_CITY_SPATIAL_DEFAULT_SUMMARY_PATH,
    generate_feature_importance_artifacts,
    generate_within_city_all_cities_supplemental_artifacts,
    generate_within_city_spatial_sensitivity_artifacts,
    generate_within_city_supplemental_artifacts,
)


def _parse_csv_list(raw_value: str) -> list[str]:
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _parse_int_list(raw_value: str) -> list[int]:
    return [int(item.strip()) for item in raw_value.split(",") if item.strip()]


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate bounded supplemental within-city, all-city within-city, spatial-sensitivity, and feature-importance artifacts without changing the canonical cross-city benchmark framing.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--dataset-path", type=Path, default=DEFAULT_FINAL_DATASET_PATH)
    parser.add_argument(
        "--feature-columns",
        default=",".join(DEFAULT_FEATURE_COLUMNS),
        help="Comma-delimited feature contract used for the supplemental analysis layer.",
    )
    parser.add_argument(
        "--city-error-table-path",
        type=Path,
        default=DEFAULT_WITHIN_CITY_CITY_ERROR_TABLE_PATH,
        help="Retained cross-city city comparison table used to select representative within-city cities.",
    )
    parser.add_argument(
        "--sample-rows-per-city",
        type=int,
        default=DEFAULT_WITHIN_CITY_SAMPLE_ROWS_PER_CITY,
        help="Per-city cap for the within-city exploratory supplement.",
    )
    parser.add_argument(
        "--split-seeds",
        default=",".join(str(value) for value in DEFAULT_WITHIN_CITY_SPLIT_SEEDS),
        help="Comma-delimited fixed seeds for the repeated within-city 80/20 splits.",
    )
    parser.add_argument(
        "--logistic-reference-run-dir",
        type=Path,
        default=DEFAULT_WITHIN_CITY_LOGISTIC_REFERENCE_RUN_DIR,
        help="Retained cross-city logistic run used for the within-city contrast join.",
    )
    parser.add_argument(
        "--random-forest-reference-run-dir",
        type=Path,
        default=DEFAULT_WITHIN_CITY_RF_REFERENCE_RUN_DIR,
        help="Retained cross-city random-forest run used for the within-city contrast join.",
    )
    parser.add_argument(
        "--run-within-city-spatial",
        action="store_true",
        help="Also run the separate supplemental spatial-block within-city sensitivity layer.",
    )
    parser.add_argument(
        "--within-city-spatial-default-summary-path",
        type=Path,
        default=DEFAULT_WITHIN_CITY_SPATIAL_DEFAULT_SUMMARY_PATH,
        help="Default within-city summary table used to contrast random splits against the spatial-block sensitivity.",
    )
    parser.add_argument(
        "--feature-importance-logistic-run-dir",
        type=Path,
        default=DEFAULT_FEATURE_IMPORTANCE_LOGISTIC_RUN_DIR,
        help="Retained logistic benchmark run whose saved outer-fold winners will be refit for coefficient export plus held-out permutation cross-check tables.",
    )
    parser.add_argument(
        "--feature-importance-random-forest-run-dir",
        type=Path,
        default=DEFAULT_FEATURE_IMPORTANCE_RF_RUN_DIR,
        help="Retained random-forest benchmark run whose saved outer-fold winners will be refit for held-out permutation importance plus secondary impurity appendix tables.",
    )
    parser.add_argument(
        "--rf-permutation-repeats",
        type=int,
        default=DEFAULT_RF_PERMUTATION_REPEATS,
        help="Held-out permutation repeats per outer fold for the retained interpretation exports.",
    )
    parser.add_argument(
        "--grid-search-n-jobs",
        type=int,
        default=1,
        help="GridSearchCV worker count for the within-city exploratory supplement.",
    )
    parser.add_argument(
        "--model-n-jobs",
        type=int,
        default=1,
        help="RandomForest worker count for the within-city exploratory supplement.",
    )
    parser.add_argument(
        "--permutation-n-jobs",
        type=int,
        default=1,
        help="Worker count for held-out permutation importance.",
    )
    parser.add_argument(
        "--skip-within-city",
        action="store_true",
        help="Skip the retained 3-city within-city exploratory supplement.",
    )
    parser.add_argument(
        "--run-within-city-all-cities",
        action="store_true",
        help="Also run the all-city within-city supplemental pass under outputs/modeling/supplemental/within_city_all_cities/.",
    )
    parser.add_argument(
        "--skip-feature-importance",
        action="store_true",
        help="Skip the retained-run interpretation export and only run the within-city supplement.",
    )
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()
    feature_columns = _parse_csv_list(args.feature_columns)
    split_seeds = _parse_int_list(args.split_seeds)

    if not args.skip_within_city:
        within_city_result = generate_within_city_supplemental_artifacts(
            dataset_path=args.dataset_path,
            city_error_table_path=args.city_error_table_path,
            feature_columns=feature_columns,
            sample_rows_per_city=args.sample_rows_per_city,
            split_seeds=split_seeds,
            logistic_reference_run_dir=args.logistic_reference_run_dir,
            random_forest_reference_run_dir=args.random_forest_reference_run_dir,
            grid_search_n_jobs=args.grid_search_n_jobs,
            model_n_jobs=args.model_n_jobs,
        )
        print(within_city_result.summary_markdown_path)
        print(within_city_result.contrast_table_path)
        print(within_city_result.figure_path)
        print(within_city_result.recall_figure_path)

    if args.run_within_city_all_cities:
        within_city_all_cities_result = generate_within_city_all_cities_supplemental_artifacts(
            dataset_path=args.dataset_path,
            city_error_table_path=args.city_error_table_path,
            feature_columns=feature_columns,
            sample_rows_per_city=args.sample_rows_per_city,
            split_seeds=split_seeds,
            grid_search_n_jobs=args.grid_search_n_jobs,
            model_n_jobs=args.model_n_jobs,
        )
        print(within_city_all_cities_result.summary_markdown_path)
        print(within_city_all_cities_result.gap_by_city_path)
        print(within_city_all_cities_result.pr_auc_figure_path)
        print(within_city_all_cities_result.recall_figure_path)
        print(within_city_all_cities_result.gap_figure_path)

    if args.run_within_city_spatial:
        within_city_spatial_result = generate_within_city_spatial_sensitivity_artifacts(
            dataset_path=args.dataset_path,
            city_error_table_path=args.city_error_table_path,
            default_within_city_summary_path=args.within_city_spatial_default_summary_path,
            feature_columns=feature_columns,
            sample_rows_per_city=args.sample_rows_per_city,
            logistic_reference_run_dir=args.logistic_reference_run_dir,
            grid_search_n_jobs=args.grid_search_n_jobs,
        )
        print(within_city_spatial_result.summary_markdown_path)
        print(within_city_spatial_result.contrast_table_path)
        print(within_city_spatial_result.figure_path)

    if not args.skip_feature_importance:
        feature_importance_result = generate_feature_importance_artifacts(
            logistic_run_dir=args.feature_importance_logistic_run_dir,
            random_forest_run_dir=args.feature_importance_random_forest_run_dir,
            rf_permutation_repeats=args.rf_permutation_repeats,
            permutation_n_jobs=args.permutation_n_jobs,
        )
        print(feature_importance_result.summary_markdown_path)
        print(feature_importance_result.logistic_coefficients_summary_path)
        print(feature_importance_result.rf_permutation_summary_path)
        print(feature_importance_result.figure_path)


if __name__ == "__main__":
    main()
