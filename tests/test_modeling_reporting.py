from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.modeling_reporting import (
    BenchmarkRunSpec,
    build_city_error_comparison,
    build_phase1_candidate_comparison,
    build_phase2_candidate_comparison,
    build_phase3_candidate_comparison,
    generate_modeling_reporting_artifacts,
    resolve_modeling_report_paths,
    summarize_city_error_by_climate,
    summarize_phase1_candidate_by_climate,
    summarize_phase2_candidate_by_climate,
    summarize_phase2_climate_disparity,
    summarize_phase3_candidate_by_climate,
)


def _write_run_artifacts(
    run_dir: Path,
    *,
    model_name: str,
    tuning_preset: str,
    sample_rows_per_city: int,
    param_candidate_count: int,
    estimated_total_inner_fits: int,
    total_wall_clock_seconds: float,
    summary_row: dict[str, object],
    city_rows: list[dict[str, object]],
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([summary_row]).to_csv(run_dir / "metrics_summary.csv", index=False)
    pd.DataFrame(city_rows).to_csv(run_dir / "metrics_by_city.csv", index=False)
    metadata = {
        "model_name": model_name,
        "tuning_preset": tuning_preset,
        "sample_rows_per_city": sample_rows_per_city,
        "search_space": {
            "param_candidate_count": param_candidate_count,
            "estimated_total_inner_fits": estimated_total_inner_fits,
        },
        "timing_seconds": {
            "total_wall_clock": total_wall_clock_seconds,
        },
    }
    (run_dir / "run_metadata.json").write_text(json.dumps(metadata), encoding="utf-8")


def test_resolve_modeling_report_paths_uses_reporting_roots(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs" / "modeling" / "reporting"
    figures_root = tmp_path / "figures" / "modeling" / "reporting"

    paths = resolve_modeling_report_paths(
        report_slug="cross_city_benchmark_report",
        outputs_root=outputs_root,
        figures_root=figures_root,
    )

    assert paths.markdown_path == outputs_root / "cross_city_benchmark_report.md"
    assert paths.tables_dir == outputs_root / "tables"
    assert paths.figures_dir == figures_root


def test_build_city_error_comparison_and_climate_summary(tmp_path: Path) -> None:
    logistic_dir = tmp_path / "logistic"
    rf_dir = tmp_path / "rf"
    common_summary = {
        "model_name": "placeholder",
        "outer_fold_count": 2,
        "heldout_city_count": 4,
        "heldout_row_count": 20000,
        "heldout_positive_count": 2000,
        "heldout_prevalence": 0.1,
        "pooled_pr_auc": 0.14,
        "mean_fold_pr_auc": 0.15,
        "mean_city_pr_auc": 0.16,
        "pooled_recall_at_top_10pct": 0.17,
        "mean_fold_recall_at_top_10pct": 0.18,
    }
    logistic_city_rows = [
        {
            "model_name": "logistic_saga",
            "outer_fold": 0,
            "city_id": 1,
            "city_name": "Phoenix",
            "climate_group": "hot_arid",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.12,
            "recall_at_top_10pct": 0.15,
        },
        {
            "model_name": "logistic_saga",
            "outer_fold": 1,
            "city_id": 2,
            "city_name": "Seattle",
            "climate_group": "mild_cool",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.22,
            "recall_at_top_10pct": 0.24,
        },
    ]
    rf_city_rows = [
        {
            "model_name": "random_forest",
            "outer_fold": 0,
            "city_id": 1,
            "city_name": "Phoenix",
            "climate_group": "hot_arid",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.18,
            "recall_at_top_10pct": 0.21,
        },
        {
            "model_name": "random_forest",
            "outer_fold": 1,
            "city_id": 2,
            "city_name": "Seattle",
            "climate_group": "mild_cool",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.19,
            "recall_at_top_10pct": 0.20,
        },
    ]
    _write_run_artifacts(
        logistic_dir,
        model_name="logistic_saga",
        tuning_preset="full",
        sample_rows_per_city=5000,
        param_candidate_count=20,
        estimated_total_inner_fits=400,
        total_wall_clock_seconds=120.0,
        summary_row={**common_summary, "model_name": "logistic_saga"},
        city_rows=logistic_city_rows,
    )
    _write_run_artifacts(
        rf_dir,
        model_name="random_forest",
        tuning_preset="frontier",
        sample_rows_per_city=5000,
        param_candidate_count=8,
        estimated_total_inner_fits=120,
        total_wall_clock_seconds=180.0,
        summary_row={**common_summary, "model_name": "random_forest"},
        city_rows=rf_city_rows,
    )

    city_error_df = build_city_error_comparison(logistic_run_dir=logistic_dir, random_forest_run_dir=rf_dir)
    assert city_error_df["city_name"].tolist() == ["Phoenix", "Seattle"]
    assert city_error_df.loc[0, "pr_auc_winner"] == "random_forest"
    assert city_error_df.loc[1, "pr_auc_winner"] == "logistic_saga"

    climate_summary_df = summarize_city_error_by_climate(city_error_df)
    hot_arid_row = climate_summary_df.loc[climate_summary_df["climate_group"] == "hot_arid"].iloc[0]
    mild_cool_row = climate_summary_df.loc[climate_summary_df["climate_group"] == "mild_cool"].iloc[0]
    assert int(hot_arid_row["rf_pr_auc_wins"]) == 1
    assert int(mild_cool_row["logistic_pr_auc_wins"]) == 1


def test_build_phase1_candidate_comparison_and_climate_summary(tmp_path: Path) -> None:
    rf_dir = tmp_path / "rf"
    hgb_dir = tmp_path / "hgb"
    common_summary = {
        "model_name": "placeholder",
        "outer_fold_count": 2,
        "heldout_city_count": 4,
        "heldout_row_count": 20000,
        "heldout_positive_count": 2000,
        "heldout_prevalence": 0.1,
        "pooled_pr_auc": 0.14,
        "mean_fold_pr_auc": 0.15,
        "mean_city_pr_auc": 0.16,
        "pooled_recall_at_top_10pct": 0.17,
        "mean_fold_recall_at_top_10pct": 0.18,
    }
    rf_city_rows = [
        {
            "model_name": "random_forest",
            "outer_fold": 0,
            "city_id": 1,
            "city_name": "Phoenix",
            "climate_group": "hot_arid",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.18,
            "recall_at_top_10pct": 0.21,
        },
        {
            "model_name": "random_forest",
            "outer_fold": 1,
            "city_id": 2,
            "city_name": "Seattle",
            "climate_group": "mild_cool",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.19,
            "recall_at_top_10pct": 0.20,
        },
    ]
    hgb_city_rows = [
        {
            "model_name": "hist_gradient_boosting",
            "outer_fold": 0,
            "city_id": 1,
            "city_name": "Phoenix",
            "climate_group": "hot_arid",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.20,
            "recall_at_top_10pct": 0.22,
        },
        {
            "model_name": "hist_gradient_boosting",
            "outer_fold": 1,
            "city_id": 2,
            "city_name": "Seattle",
            "climate_group": "mild_cool",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.17,
            "recall_at_top_10pct": 0.18,
        },
    ]
    _write_run_artifacts(
        rf_dir,
        model_name="random_forest",
        tuning_preset="frontier",
        sample_rows_per_city=5000,
        param_candidate_count=8,
        estimated_total_inner_fits=120,
        total_wall_clock_seconds=180.0,
        summary_row={**common_summary, "model_name": "random_forest"},
        city_rows=rf_city_rows,
    )
    _write_run_artifacts(
        hgb_dir,
        model_name="hist_gradient_boosting",
        tuning_preset="smoke",
        sample_rows_per_city=5000,
        param_candidate_count=4,
        estimated_total_inner_fits=60,
        total_wall_clock_seconds=150.0,
        summary_row={**common_summary, "model_name": "hist_gradient_boosting"},
        city_rows=hgb_city_rows,
    )

    candidate_df = build_phase1_candidate_comparison(
        hist_gradient_boosting_run_dir=hgb_dir,
        random_forest_run_dir=rf_dir,
    )
    assert candidate_df["city_name"].tolist() == ["Phoenix", "Seattle"]
    assert candidate_df.loc[0, "pr_auc_winner"] == "hist_gradient_boosting"
    assert candidate_df.loc[1, "pr_auc_winner"] == "random_forest"

    climate_summary_df = summarize_phase1_candidate_by_climate(candidate_df)
    hot_arid_row = climate_summary_df.loc[climate_summary_df["climate_group"] == "hot_arid"].iloc[0]
    mild_cool_row = climate_summary_df.loc[climate_summary_df["climate_group"] == "mild_cool"].iloc[0]
    assert int(hot_arid_row["hgb_pr_auc_wins"]) == 1
    assert int(mild_cool_row["rf_pr_auc_wins"]) == 1


def test_build_phase2_candidate_comparison_and_climate_disparity_summary(tmp_path: Path) -> None:
    logistic_dir = tmp_path / "logistic"
    logistic_ci_dir = tmp_path / "logistic_ci"
    common_summary = {
        "model_name": "placeholder",
        "outer_fold_count": 3,
        "heldout_city_count": 6,
        "heldout_row_count": 30000,
        "heldout_positive_count": 3000,
        "heldout_prevalence": 0.1,
        "pooled_pr_auc": 0.14,
        "mean_fold_pr_auc": 0.15,
        "mean_city_pr_auc": 0.16,
        "pooled_recall_at_top_10pct": 0.17,
        "mean_fold_recall_at_top_10pct": 0.18,
    }
    logistic_city_rows = [
        {
            "model_name": "logistic_saga",
            "outer_fold": 0,
            "city_id": 1,
            "city_name": "Phoenix",
            "climate_group": "hot_arid",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.12,
            "recall_at_top_10pct": 0.15,
        },
        {
            "model_name": "logistic_saga",
            "outer_fold": 1,
            "city_id": 2,
            "city_name": "Miami",
            "climate_group": "hot_humid",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.18,
            "recall_at_top_10pct": 0.20,
        },
        {
            "model_name": "logistic_saga",
            "outer_fold": 2,
            "city_id": 3,
            "city_name": "Seattle",
            "climate_group": "mild_cool",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.24,
            "recall_at_top_10pct": 0.27,
        },
    ]
    logistic_ci_city_rows = [
        {
            "model_name": "logistic_saga_climate_interactions",
            "outer_fold": 0,
            "city_id": 1,
            "city_name": "Phoenix",
            "climate_group": "hot_arid",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.16,
            "recall_at_top_10pct": 0.19,
        },
        {
            "model_name": "logistic_saga_climate_interactions",
            "outer_fold": 1,
            "city_id": 2,
            "city_name": "Miami",
            "climate_group": "hot_humid",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.19,
            "recall_at_top_10pct": 0.21,
        },
        {
            "model_name": "logistic_saga_climate_interactions",
            "outer_fold": 2,
            "city_id": 3,
            "city_name": "Seattle",
            "climate_group": "mild_cool",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.22,
            "recall_at_top_10pct": 0.25,
        },
    ]
    _write_run_artifacts(
        logistic_dir,
        model_name="logistic_saga",
        tuning_preset="full",
        sample_rows_per_city=5000,
        param_candidate_count=20,
        estimated_total_inner_fits=400,
        total_wall_clock_seconds=120.0,
        summary_row={**common_summary, "model_name": "logistic_saga"},
        city_rows=logistic_city_rows,
    )
    _write_run_artifacts(
        logistic_ci_dir,
        model_name="logistic_saga_climate_interactions",
        tuning_preset="smoke",
        sample_rows_per_city=5000,
        param_candidate_count=4,
        estimated_total_inner_fits=60,
        total_wall_clock_seconds=130.0,
        summary_row={**common_summary, "model_name": "logistic_saga_climate_interactions"},
        city_rows=logistic_ci_city_rows,
    )

    candidate_df = build_phase2_candidate_comparison(
        logistic_run_dir=logistic_dir,
        logistic_climate_interactions_run_dir=logistic_ci_dir,
    )
    climate_summary_df = summarize_phase2_candidate_by_climate(candidate_df)
    disparity_df = summarize_phase2_climate_disparity(climate_summary_df)

    assert candidate_df["city_name"].tolist() == ["Phoenix", "Miami", "Seattle"]
    assert candidate_df.loc[0, "pr_auc_winner"] == "logistic_saga_climate_interactions"
    assert candidate_df.loc[2, "pr_auc_winner"] == "logistic_saga"
    assert float(
        disparity_df.loc[disparity_df["metric"] == "pr_auc", "range_delta_interaction_minus_baseline"].iloc[0]
    ) < 0.0


def test_build_phase3_candidate_comparison_and_climate_summary(tmp_path: Path) -> None:
    logistic_dir = tmp_path / "logistic"
    phase3_dir = tmp_path / "logistic_phase3a"
    common_summary = {
        "model_name": "placeholder",
        "outer_fold_count": 2,
        "heldout_city_count": 4,
        "heldout_row_count": 20000,
        "heldout_positive_count": 2000,
        "heldout_prevalence": 0.1,
        "pooled_pr_auc": 0.14,
        "mean_fold_pr_auc": 0.15,
        "mean_city_pr_auc": 0.16,
        "pooled_recall_at_top_10pct": 0.17,
        "mean_fold_recall_at_top_10pct": 0.18,
    }
    logistic_city_rows = [
        {
            "model_name": "logistic_saga",
            "outer_fold": 0,
            "city_id": 1,
            "city_name": "Phoenix",
            "climate_group": "hot_arid",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.12,
            "recall_at_top_10pct": 0.15,
        },
        {
            "model_name": "logistic_saga",
            "outer_fold": 1,
            "city_id": 2,
            "city_name": "Seattle",
            "climate_group": "mild_cool",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.22,
            "recall_at_top_10pct": 0.24,
        },
    ]
    phase3_city_rows = [
        {
            "model_name": "logistic_saga",
            "outer_fold": 0,
            "city_id": 1,
            "city_name": "Phoenix",
            "climate_group": "hot_arid",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.16,
            "recall_at_top_10pct": 0.20,
        },
        {
            "model_name": "logistic_saga",
            "outer_fold": 1,
            "city_id": 2,
            "city_name": "Seattle",
            "climate_group": "mild_cool",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.20,
            "recall_at_top_10pct": 0.22,
        },
    ]
    _write_run_artifacts(
        logistic_dir,
        model_name="logistic_saga",
        tuning_preset="full",
        sample_rows_per_city=5000,
        param_candidate_count=20,
        estimated_total_inner_fits=400,
        total_wall_clock_seconds=120.0,
        summary_row={**common_summary, "model_name": "logistic_saga"},
        city_rows=logistic_city_rows,
    )
    _write_run_artifacts(
        phase3_dir,
        model_name="logistic_saga",
        tuning_preset="full",
        sample_rows_per_city=5000,
        param_candidate_count=20,
        estimated_total_inner_fits=400,
        total_wall_clock_seconds=140.0,
        summary_row={**common_summary, "model_name": "logistic_saga"},
        city_rows=phase3_city_rows,
    )

    candidate_df = build_phase3_candidate_comparison(
        logistic_run_dir=logistic_dir,
        richer_predictor_run_dir=phase3_dir,
    )
    climate_summary_df = summarize_phase3_candidate_by_climate(candidate_df)

    assert candidate_df["city_name"].tolist() == ["Phoenix", "Seattle"]
    assert candidate_df.loc[0, "pr_auc_winner"] == "logistic_saga_phase3a"
    assert candidate_df.loc[1, "pr_auc_winner"] == "logistic_saga"
    hot_arid_row = climate_summary_df.loc[climate_summary_df["climate_group"] == "hot_arid"].iloc[0]
    assert int(hot_arid_row["phase3a_pr_auc_wins"]) == 1


def test_generate_modeling_reporting_artifacts_writes_tables_markdown_and_figures(tmp_path: Path) -> None:
    baseline_summary_path = tmp_path / "outputs" / "modeling" / "baselines" / "metrics_summary.csv"
    baseline_summary_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "model_name": "impervious_only_baseline",
                "outer_fold_count": 2,
                "heldout_city_count": 4,
                "heldout_row_count": 20000,
                "heldout_positive_count": 2000,
                "heldout_prevalence": 0.1,
                "pooled_pr_auc": 0.13,
                "mean_fold_pr_auc": 0.14,
                "mean_city_pr_auc": 0.15,
                "pooled_recall_at_top_10pct": 0.18,
                "mean_fold_recall_at_top_10pct": 0.17,
            },
            {
                "model_name": "land_cover_only_baseline",
                "outer_fold_count": 2,
                "heldout_city_count": 4,
                "heldout_row_count": 20000,
                "heldout_positive_count": 2000,
                "heldout_prevalence": 0.1,
                "pooled_pr_auc": 0.131,
                "mean_fold_pr_auc": 0.141,
                "mean_city_pr_auc": 0.149,
                "pooled_recall_at_top_10pct": 0.17,
                "mean_fold_recall_at_top_10pct": 0.16,
            },
        ]
    ).to_csv(baseline_summary_path, index=False)

    logistic_dir = tmp_path / "outputs" / "modeling" / "logistic_saga" / "log5k"
    logistic10_dir = tmp_path / "outputs" / "modeling" / "logistic_saga" / "log10k"
    logistic20_dir = tmp_path / "outputs" / "modeling" / "logistic_saga" / "log20k"
    logistic_phase3_dir = tmp_path / "outputs" / "modeling" / "logistic_saga" / "logphase3a"
    logistic_ci_dir = tmp_path / "outputs" / "modeling" / "logistic_saga_climate_interactions" / "logci"
    rf_smoke_dir = tmp_path / "outputs" / "modeling" / "random_forest" / "rfsmoke"
    rf_frontier_dir = tmp_path / "outputs" / "modeling" / "random_forest" / "rffrontier"
    hgb_dir = tmp_path / "outputs" / "modeling" / "hist_gradient_boosting" / "hgbsmoke"

    common_city_rows_logistic = [
        {
            "model_name": "logistic_saga",
            "outer_fold": 0,
            "city_id": 1,
            "city_name": "Phoenix",
            "climate_group": "hot_arid",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.12,
            "recall_at_top_10pct": 0.15,
        },
        {
            "model_name": "logistic_saga",
            "outer_fold": 1,
            "city_id": 2,
            "city_name": "Seattle",
            "climate_group": "mild_cool",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.22,
            "recall_at_top_10pct": 0.24,
        },
    ]
    common_city_rows_rf = [
        {
            "model_name": "random_forest",
            "outer_fold": 0,
            "city_id": 1,
            "city_name": "Phoenix",
            "climate_group": "hot_arid",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.18,
            "recall_at_top_10pct": 0.21,
        },
        {
            "model_name": "random_forest",
            "outer_fold": 1,
            "city_id": 2,
            "city_name": "Seattle",
            "climate_group": "mild_cool",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.19,
            "recall_at_top_10pct": 0.20,
        },
    ]
    common_city_rows_hgb = [
        {
            "model_name": "hist_gradient_boosting",
            "outer_fold": 0,
            "city_id": 1,
            "city_name": "Phoenix",
            "climate_group": "hot_arid",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.20,
            "recall_at_top_10pct": 0.22,
        },
        {
            "model_name": "hist_gradient_boosting",
            "outer_fold": 1,
            "city_id": 2,
            "city_name": "Seattle",
            "climate_group": "mild_cool",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.17,
            "recall_at_top_10pct": 0.18,
        },
    ]
    common_city_rows_logistic_ci = [
        {
            "model_name": "logistic_saga_climate_interactions",
            "outer_fold": 0,
            "city_id": 1,
            "city_name": "Phoenix",
            "climate_group": "hot_arid",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.17,
            "recall_at_top_10pct": 0.19,
        },
        {
            "model_name": "logistic_saga_climate_interactions",
            "outer_fold": 1,
            "city_id": 2,
            "city_name": "Seattle",
            "climate_group": "mild_cool",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.20,
            "recall_at_top_10pct": 0.22,
        },
    ]
    common_city_rows_logistic_phase3 = [
        {
            "model_name": "logistic_saga",
            "outer_fold": 0,
            "city_id": 1,
            "city_name": "Phoenix",
            "climate_group": "hot_arid",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.16,
            "recall_at_top_10pct": 0.19,
        },
        {
            "model_name": "logistic_saga",
            "outer_fold": 1,
            "city_id": 2,
            "city_name": "Seattle",
            "climate_group": "mild_cool",
            "row_count": 5000,
            "positive_count": 500,
            "prevalence": 0.1,
            "pr_auc": 0.20,
            "recall_at_top_10pct": 0.22,
        },
    ]
    _write_run_artifacts(
        logistic_dir,
        model_name="logistic_saga",
        tuning_preset="full",
        sample_rows_per_city=5000,
        param_candidate_count=20,
        estimated_total_inner_fits=400,
        total_wall_clock_seconds=120.0,
        summary_row={
            "model_name": "logistic_saga",
            "outer_fold_count": 2,
            "heldout_city_count": 4,
            "heldout_row_count": 20000,
            "heldout_positive_count": 2000,
            "heldout_prevalence": 0.1,
            "pooled_pr_auc": 0.142,
            "mean_fold_pr_auc": 0.15,
            "mean_city_pr_auc": 0.18,
            "pooled_recall_at_top_10pct": 0.165,
            "mean_fold_recall_at_top_10pct": 0.19,
        },
        city_rows=common_city_rows_logistic,
    )
    _write_run_artifacts(
        logistic10_dir,
        model_name="logistic_saga",
        tuning_preset="full",
        sample_rows_per_city=10000,
        param_candidate_count=20,
        estimated_total_inner_fits=400,
        total_wall_clock_seconds=300.0,
        summary_row={
            "model_name": "logistic_saga",
            "outer_fold_count": 2,
            "heldout_city_count": 4,
            "heldout_row_count": 40000,
            "heldout_positive_count": 4000,
            "heldout_prevalence": 0.1,
            "pooled_pr_auc": 0.144,
            "mean_fold_pr_auc": 0.151,
            "mean_city_pr_auc": 0.179,
            "pooled_recall_at_top_10pct": 0.168,
            "mean_fold_recall_at_top_10pct": 0.196,
        },
        city_rows=common_city_rows_logistic,
    )
    _write_run_artifacts(
        logistic20_dir,
        model_name="logistic_saga",
        tuning_preset="full",
        sample_rows_per_city=20000,
        param_candidate_count=20,
        estimated_total_inner_fits=400,
        total_wall_clock_seconds=600.0,
        summary_row={
            "model_name": "logistic_saga",
            "outer_fold_count": 2,
            "heldout_city_count": 4,
            "heldout_row_count": 80000,
            "heldout_positive_count": 8000,
            "heldout_prevalence": 0.1,
            "pooled_pr_auc": 0.146,
            "mean_fold_pr_auc": 0.152,
            "mean_city_pr_auc": 0.18,
            "pooled_recall_at_top_10pct": 0.171,
            "mean_fold_recall_at_top_10pct": 0.197,
        },
        city_rows=common_city_rows_logistic,
    )
    _write_run_artifacts(
        logistic_phase3_dir,
        model_name="logistic_saga",
        tuning_preset="full",
        sample_rows_per_city=5000,
        param_candidate_count=20,
        estimated_total_inner_fits=400,
        total_wall_clock_seconds=180.0,
        summary_row={
            "model_name": "logistic_saga",
            "outer_fold_count": 2,
            "heldout_city_count": 4,
            "heldout_row_count": 20000,
            "heldout_positive_count": 2000,
            "heldout_prevalence": 0.1,
            "pooled_pr_auc": 0.150,
            "mean_fold_pr_auc": 0.156,
            "mean_city_pr_auc": 0.182,
            "pooled_recall_at_top_10pct": 0.181,
            "mean_fold_recall_at_top_10pct": 0.199,
        },
        city_rows=common_city_rows_logistic_phase3,
    )
    _write_run_artifacts(
        logistic_ci_dir,
        model_name="logistic_saga_climate_interactions",
        tuning_preset="smoke",
        sample_rows_per_city=5000,
        param_candidate_count=4,
        estimated_total_inner_fits=60,
        total_wall_clock_seconds=150.0,
        summary_row={
            "model_name": "logistic_saga_climate_interactions",
            "outer_fold_count": 2,
            "heldout_city_count": 4,
            "heldout_row_count": 20000,
            "heldout_positive_count": 2000,
            "heldout_prevalence": 0.1,
            "pooled_pr_auc": 0.147,
            "mean_fold_pr_auc": 0.153,
            "mean_city_pr_auc": 0.185,
            "pooled_recall_at_top_10pct": 0.174,
            "mean_fold_recall_at_top_10pct": 0.196,
        },
        city_rows=common_city_rows_logistic_ci,
    )
    _write_run_artifacts(
        rf_smoke_dir,
        model_name="random_forest",
        tuning_preset="smoke",
        sample_rows_per_city=5000,
        param_candidate_count=4,
        estimated_total_inner_fits=60,
        total_wall_clock_seconds=180.0,
        summary_row={
            "model_name": "random_forest",
            "outer_fold_count": 2,
            "heldout_city_count": 4,
            "heldout_row_count": 20000,
            "heldout_positive_count": 2000,
            "heldout_prevalence": 0.1,
            "pooled_pr_auc": 0.148,
            "mean_fold_pr_auc": 0.156,
            "mean_city_pr_auc": 0.178,
            "pooled_recall_at_top_10pct": 0.194,
            "mean_fold_recall_at_top_10pct": 0.198,
        },
        city_rows=common_city_rows_rf,
    )
    _write_run_artifacts(
        rf_frontier_dir,
        model_name="random_forest",
        tuning_preset="frontier",
        sample_rows_per_city=5000,
        param_candidate_count=8,
        estimated_total_inner_fits=120,
        total_wall_clock_seconds=360.0,
        summary_row={
            "model_name": "random_forest",
            "outer_fold_count": 2,
            "heldout_city_count": 4,
            "heldout_row_count": 20000,
            "heldout_positive_count": 2000,
            "heldout_prevalence": 0.1,
            "pooled_pr_auc": 0.149,
            "mean_fold_pr_auc": 0.155,
            "mean_city_pr_auc": 0.178,
            "pooled_recall_at_top_10pct": 0.196,
            "mean_fold_recall_at_top_10pct": 0.198,
        },
        city_rows=common_city_rows_rf,
    )
    _write_run_artifacts(
        hgb_dir,
        model_name="hist_gradient_boosting",
        tuning_preset="smoke",
        sample_rows_per_city=5000,
        param_candidate_count=4,
        estimated_total_inner_fits=60,
        total_wall_clock_seconds=150.0,
        summary_row={
            "model_name": "hist_gradient_boosting",
            "outer_fold_count": 2,
            "heldout_city_count": 4,
            "heldout_row_count": 20000,
            "heldout_positive_count": 2000,
            "heldout_prevalence": 0.1,
            "pooled_pr_auc": 0.151,
            "mean_fold_pr_auc": 0.157,
            "mean_city_pr_auc": 0.176,
            "pooled_recall_at_top_10pct": 0.193,
            "mean_fold_recall_at_top_10pct": 0.197,
        },
        city_rows=common_city_rows_hgb,
    )

    run_specs = [
        BenchmarkRunSpec(label="logistic_full_5k", run_dir=logistic_dir, notes="Retained 5k linear baseline rung"),
        BenchmarkRunSpec(label="logistic_full_10k", run_dir=logistic10_dir, notes="Retained 10k linear baseline rung"),
        BenchmarkRunSpec(label="logistic_full_20k", run_dir=logistic20_dir, notes="Retained 20k linear baseline rung"),
        BenchmarkRunSpec(
            label="logistic_saga_phase3a",
            run_dir=logistic_phase3_dir,
            notes="Phase 3A richer-predictor logistic checkpoint",
        ),
        BenchmarkRunSpec(
            label="logistic_saga_climate_interactions",
            run_dir=logistic_ci_dir,
            notes="Phase 2 climate-conditioned logistic benchmark",
        ),
        BenchmarkRunSpec(label="random_forest_smoke_5k", run_dir=rf_smoke_dir, notes="Cheap nonlinear checkpoint"),
        BenchmarkRunSpec(label="random_forest_frontier_5k", run_dir=rf_frontier_dir, notes="Targeted follow-up"),
        BenchmarkRunSpec(
            label="hist_gradient_boosting_smoke_5k",
            run_dir=hgb_dir,
            notes="Bounded Phase 1 better-learner checkpoint",
        ),
    ]

    result = generate_modeling_reporting_artifacts(
        report_slug="cross_city_benchmark_report",
        baseline_summary_path=baseline_summary_path,
        logistic_run_dir=logistic_dir,
        random_forest_run_dir=rf_frontier_dir,
        hist_gradient_boosting_run_dir=hgb_dir,
        logistic_climate_interactions_run_dir=logistic_ci_dir,
        phase3_richer_logistic_run_dir=logistic_phase3_dir,
        benchmark_run_specs=run_specs,
        outputs_root=tmp_path / "outputs" / "modeling" / "reporting",
        figures_root=tmp_path / "figures" / "modeling" / "reporting",
    )

    assert result.markdown_path.exists()
    assert result.benchmark_table_path.exists()
    assert result.city_error_table_path.exists()
    assert result.climate_summary_path.exists()
    assert result.benchmark_metrics_figure_path.exists()
    assert result.runtime_figure_path.exists()
    assert result.city_delta_figure_path.exists()
    assert result.phase1_candidate_table_path is not None
    assert result.phase1_candidate_table_path.exists()
    assert result.phase1_candidate_climate_summary_path is not None
    assert result.phase1_candidate_climate_summary_path.exists()
    assert result.phase2_candidate_table_path is not None
    assert result.phase2_candidate_table_path.exists()
    assert result.phase2_candidate_climate_summary_path is not None
    assert result.phase2_candidate_climate_summary_path.exists()
    assert result.phase2_candidate_disparity_summary_path is not None
    assert result.phase2_candidate_disparity_summary_path.exists()
    assert result.phase3_candidate_table_path is not None
    assert result.phase3_candidate_table_path.exists()
    assert result.phase3_candidate_climate_summary_path is not None
    assert result.phase3_candidate_climate_summary_path.exists()

    markdown_text = result.markdown_path.read_text(encoding="utf-8")
    assert "Cross-City Modeling Report" in markdown_text
    assert "City-Level Error Analysis" in markdown_text
    assert "Phase 1 Candidate Checkpoint" in markdown_text
    assert "Phase 2 Climate-Conditioned Checkpoint" in markdown_text
    assert "Phase 3 Richer-Predictor Checkpoint" in markdown_text
    benchmark_df = pd.read_csv(result.benchmark_table_path)
    assert set(benchmark_df["model_family"]) == {
        "baseline",
        "logistic_saga",
        "logistic_saga",
        "logistic_saga_climate_interactions",
        "random_forest",
        "hist_gradient_boosting",
    }
