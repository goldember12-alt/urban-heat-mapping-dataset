from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.modeling_reporting import (
    DEFAULT_BASELINE_SUMMARY_PATH,
    DEFAULT_LOGISTIC_5K_RUN_DIR,
    DEFAULT_RF_FRONTIER_RUN_DIR,
    generate_modeling_reporting_artifacts,
)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate cross-city modeling reporting tables, markdown, and figures from retained run artifacts."
    )
    parser.add_argument("--report-slug", default="cross_city_benchmark_report")
    parser.add_argument("--baseline-summary-path", type=Path, default=DEFAULT_BASELINE_SUMMARY_PATH)
    parser.add_argument("--logistic-run-dir", type=Path, default=DEFAULT_LOGISTIC_5K_RUN_DIR)
    parser.add_argument("--random-forest-run-dir", type=Path, default=DEFAULT_RF_FRONTIER_RUN_DIR)
    parser.add_argument(
        "--hist-gradient-boosting-run-dir",
        type=Path,
        default=None,
        help="Optional bounded Phase 1 HGB smoke run to include in the shared reporting outputs without replacing the retained logistic/RF story.",
    )
    parser.add_argument(
        "--logistic-climate-interactions-run-dir",
        type=Path,
        default=None,
        help=(
            "Optional Phase 2 climate-conditioned logistic run to include in the shared reporting outputs "
            "without replacing the retained logistic/RF story."
        ),
    )
    parser.add_argument(
        "--phase3-richer-logistic-run-dir",
        type=Path,
        default=None,
        help=(
            "Optional Phase 3A richer-predictor logistic run to compare against the retained six-feature logistic "
            "benchmark slice without replacing the retained project narrative."
        ),
    )
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()
    result = generate_modeling_reporting_artifacts(
        report_slug=args.report_slug,
        baseline_summary_path=args.baseline_summary_path,
        logistic_run_dir=args.logistic_run_dir,
        random_forest_run_dir=args.random_forest_run_dir,
        hist_gradient_boosting_run_dir=args.hist_gradient_boosting_run_dir,
        logistic_climate_interactions_run_dir=args.logistic_climate_interactions_run_dir,
        phase3_richer_logistic_run_dir=args.phase3_richer_logistic_run_dir,
    )
    print(result.markdown_path)
    print(result.benchmark_table_path)
    print(result.city_error_table_path)
    print(result.climate_summary_path)
    print(result.benchmark_metrics_figure_path)
    print(result.runtime_figure_path)
    print(result.city_delta_figure_path)
    if result.phase1_candidate_table_path is not None:
        print(result.phase1_candidate_table_path)
    if result.phase1_candidate_climate_summary_path is not None:
        print(result.phase1_candidate_climate_summary_path)
    if result.phase2_candidate_table_path is not None:
        print(result.phase2_candidate_table_path)
    if result.phase2_candidate_climate_summary_path is not None:
        print(result.phase2_candidate_climate_summary_path)
    if result.phase2_candidate_disparity_summary_path is not None:
        print(result.phase2_candidate_disparity_summary_path)
    if result.phase3_candidate_table_path is not None:
        print(result.phase3_candidate_table_path)
    if result.phase3_candidate_climate_summary_path is not None:
        print(result.phase3_candidate_climate_summary_path)


if __name__ == "__main__":
    main()
