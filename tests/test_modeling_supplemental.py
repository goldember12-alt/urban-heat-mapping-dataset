from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.modeling_config import DEFAULT_FEATURE_COLUMNS
from src.modeling_runner import run_logistic_saga_model, run_random_forest_model
from src.modeling_supplemental import (
    assign_within_city_spatial_blocks,
    generate_feature_importance_artifacts,
    generate_within_city_spatial_sensitivity_artifacts,
    generate_within_city_supplemental_artifacts,
    make_within_city_spatial_block_splits,
    plot_within_city_recall_contrast,
    plot_within_city_spatial_pr_auc_contrast,
    select_representative_within_city_cities,
)


def _build_within_city_fixture() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    city_specs = [
        (1, "Reno", "hot_arid", 180),
        (2, "Charlotte", "hot_humid", 185),
        (3, "Detroit", "mild_cool", 190),
    ]
    for city_id, city_name, climate_group, elevation_base in city_specs:
        for idx in range(80):
            hotspot = idx >= 56
            rows.append(
                {
                    "city_id": city_id,
                    "city_name": city_name,
                    "climate_group": climate_group,
                    "cell_id": (city_id * 10_000) + idx,
                    "centroid_lon": -120.0 + city_id + (idx * 0.001),
                    "centroid_lat": 35.0 + city_id + (idx * 0.001),
                    "impervious_pct": float(8 + (idx % 20) * 4 + (15 if hotspot else 0)),
                    "land_cover_class": 24 if hotspot else (21 if idx % 3 else 31),
                    "elevation_m": float(elevation_base + idx),
                    "dist_to_water_m": float(900 - idx * 7 - (140 if hotspot else 0)),
                    "ndvi_median_may_aug": float(0.52 - idx * 0.003 - (0.12 if hotspot else 0.0)),
                    "lst_median_may_aug": float(30 + city_id + idx * 0.04),
                    "n_valid_ecostress_passes": 5,
                    "hotspot_10pct": hotspot,
                }
            )
    return pd.DataFrame(rows)


def _build_grouped_fixture() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    city_specs = [
        (1, "Phoenix", "hot_arid"),
        (2, "Tucson", "hot_arid"),
        (3, "Charlotte", "hot_humid"),
        (4, "Atlanta", "hot_humid"),
    ]
    for city_id, city_name, climate_group in city_specs:
        for idx in range(32):
            hotspot = idx >= 22
            rows.append(
                {
                    "city_id": city_id,
                    "city_name": city_name,
                    "climate_group": climate_group,
                    "cell_id": (city_id * 1000) + idx,
                    "centroid_lon": -110.0 - city_id - (idx * 0.01),
                    "centroid_lat": 30.0 + city_id + (idx * 0.01),
                    "impervious_pct": float(6 + idx * 2 + (18 if hotspot else 0)),
                    "land_cover_class": 24 if hotspot else 21,
                    "elevation_m": float((city_id * 40) + idx),
                    "dist_to_water_m": float(850 - idx * 12 - (120 if hotspot else 0)),
                    "ndvi_median_may_aug": float(0.48 - idx * 0.006 - (0.08 if hotspot else 0.0)),
                    "lst_median_may_aug": float(31 + city_id + idx * 0.03),
                    "n_valid_ecostress_passes": 5,
                    "hotspot_10pct": hotspot,
                }
            )
    return pd.DataFrame(rows)


def _build_spatial_within_city_fixture() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    city_specs = [
        (1, "Reno", "hot_arid", 130),
        (2, "Charlotte", "hot_humid", 160),
        (3, "Detroit", "mild_cool", 190),
    ]
    for city_id, city_name, climate_group, elevation_base in city_specs:
        for row_idx in range(8):
            for col_idx in range(8):
                idx = (row_idx * 8) + col_idx
                hotspot = int((row_idx + col_idx) >= 8 or ((row_idx + col_idx) % 3 == 0))
                rows.append(
                    {
                        "city_id": city_id,
                        "city_name": city_name,
                        "climate_group": climate_group,
                        "cell_id": (city_id * 10_000) + idx,
                        "centroid_lon": -120.0 + city_id + (col_idx * 0.01),
                        "centroid_lat": 35.0 + city_id + (row_idx * 0.01),
                        "impervious_pct": float(10 + (col_idx * 4) + (12 * hotspot)),
                        "land_cover_class": 24 if hotspot else (21 if (idx % 2) else 31),
                        "elevation_m": float(elevation_base + row_idx * 5 + col_idx),
                        "dist_to_water_m": float(950 - row_idx * 35 - col_idx * 22 - (90 * hotspot)),
                        "ndvi_median_may_aug": float(0.58 - row_idx * 0.025 - col_idx * 0.015 - (0.08 * hotspot)),
                        "lst_median_may_aug": float(31 + city_id + row_idx * 0.05 + col_idx * 0.05),
                        "n_valid_ecostress_passes": 5,
                        "hotspot_10pct": hotspot,
                    }
                )
    return pd.DataFrame(rows)


def _build_grouped_folds() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "city_id": [1, 2, 3, 4],
            "city_name": ["Phoenix", "Tucson", "Charlotte", "Atlanta"],
            "climate_group": ["hot_arid", "hot_arid", "hot_humid", "hot_humid"],
            "row_count": [32, 32, 32, 32],
            "hotspot_positive_count": [10, 10, 10, 10],
            "hotspot_non_missing_count": [32, 32, 32, 32],
            "hotspot_prevalence": [10 / 32] * 4,
            "outer_fold": [0, 0, 1, 1],
        }
    )


def test_select_representative_within_city_cities_prefers_nearest_median_defaults(tmp_path: Path) -> None:
    comparison_path = tmp_path / "city_error.csv"
    pd.DataFrame(
        [
            {"city_id": 1, "city_name": "Reno", "climate_group": "hot_arid", "pr_auc_logistic": 0.14},
            {"city_id": 2, "city_name": "Phoenix", "climate_group": "hot_arid", "pr_auc_logistic": 0.08},
            {"city_id": 3, "city_name": "Charlotte", "climate_group": "hot_humid", "pr_auc_logistic": 0.18},
            {"city_id": 4, "city_name": "Miami", "climate_group": "hot_humid", "pr_auc_logistic": 0.24},
            {"city_id": 5, "city_name": "Detroit", "climate_group": "mild_cool", "pr_auc_logistic": 0.17},
            {"city_id": 6, "city_name": "Boston", "climate_group": "mild_cool", "pr_auc_logistic": 0.21},
        ]
    ).to_csv(comparison_path, index=False)

    selected_df = select_representative_within_city_cities(city_error_table_path=comparison_path)

    assert selected_df["city_name"].tolist() == ["Reno", "Charlotte", "Detroit"]
    assert set(selected_df["selection_rule"]) == {"nearest_median_logistic_pr_auc_within_climate_group"}


def test_generate_within_city_supplemental_artifacts_integrates_city_prevalence_baseline(tmp_path: Path) -> None:
    dataset_path = tmp_path / "final_dataset.parquet"
    comparison_path = tmp_path / "city_error.csv"
    _build_within_city_fixture().to_parquet(dataset_path, index=False)
    pd.DataFrame(
        [
            {"outer_fold": 0, "city_id": 1, "city_name": "Reno", "climate_group": "hot_arid", "pr_auc_logistic": 0.13},
            {"outer_fold": 1, "city_id": 2, "city_name": "Charlotte", "climate_group": "hot_humid", "pr_auc_logistic": 0.17},
            {"outer_fold": 2, "city_id": 3, "city_name": "Detroit", "climate_group": "mild_cool", "pr_auc_logistic": 0.15},
        ]
    ).to_csv(comparison_path, index=False)

    logistic_ref_dir = tmp_path / "outputs" / "modeling" / "logistic_saga" / "retained_logistic"
    rf_ref_dir = tmp_path / "outputs" / "modeling" / "random_forest" / "retained_rf"
    logistic_ref_dir.mkdir(parents=True, exist_ok=True)
    rf_ref_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {"model_name": "logistic_saga", "outer_fold": 0, "city_id": 1, "city_name": "Reno", "climate_group": "hot_arid", "row_count": 80, "positive_count": 24, "prevalence": 0.3, "pr_auc": 0.13, "recall_at_top_10pct": 0.20},
            {"model_name": "logistic_saga", "outer_fold": 1, "city_id": 2, "city_name": "Charlotte", "climate_group": "hot_humid", "row_count": 80, "positive_count": 24, "prevalence": 0.3, "pr_auc": 0.17, "recall_at_top_10pct": 0.21},
            {"model_name": "logistic_saga", "outer_fold": 2, "city_id": 3, "city_name": "Detroit", "climate_group": "mild_cool", "row_count": 80, "positive_count": 24, "prevalence": 0.3, "pr_auc": 0.15, "recall_at_top_10pct": 0.19},
        ]
    ).to_csv(logistic_ref_dir / "metrics_by_city.csv", index=False)
    pd.DataFrame(
        [
            {"model_name": "random_forest", "outer_fold": 0, "city_id": 1, "city_name": "Reno", "climate_group": "hot_arid", "row_count": 80, "positive_count": 24, "prevalence": 0.3, "pr_auc": 0.16, "recall_at_top_10pct": 0.24},
            {"model_name": "random_forest", "outer_fold": 1, "city_id": 2, "city_name": "Charlotte", "climate_group": "hot_humid", "row_count": 80, "positive_count": 24, "prevalence": 0.3, "pr_auc": 0.18, "recall_at_top_10pct": 0.23},
            {"model_name": "random_forest", "outer_fold": 2, "city_id": 3, "city_name": "Detroit", "climate_group": "mild_cool", "row_count": 80, "positive_count": 24, "prevalence": 0.3, "pr_auc": 0.16, "recall_at_top_10pct": 0.20},
        ]
    ).to_csv(rf_ref_dir / "metrics_by_city.csv", index=False)

    result = generate_within_city_supplemental_artifacts(
        dataset_path=dataset_path,
        city_error_table_path=comparison_path,
        output_dir=tmp_path / "outputs" / "modeling" / "supplemental" / "within_city",
        figures_dir=tmp_path / "figures" / "modeling" / "supplemental" / "within_city",
        sample_rows_per_city=60,
        split_seeds=[7, 8, 9],
        logistic_reference_run_dir=logistic_ref_dir,
        random_forest_reference_run_dir=rf_ref_dir,
        grid_search_n_jobs=1,
        model_n_jobs=1,
    )

    assert result.summary_markdown_path.exists()
    assert result.contrast_table_path.exists()
    assert result.best_params_path.exists()
    assert result.predictions_path.exists()
    assert result.figure_path.exists()
    assert result.recall_figure_path.exists()

    contrast_df = pd.read_csv(result.contrast_table_path)
    assert set(contrast_df["city_name"]) == {"Reno", "Charlotte", "Detroit"}
    assert set(contrast_df["model_name"]) == {"city_prevalence_baseline", "logistic_saga", "random_forest"}
    assert {"within_city_pr_auc_mean", "cross_city_pr_auc", "pr_auc_gap"}.issubset(contrast_df.columns)
    baseline_rows = contrast_df.loc[contrast_df["model_name"] == "city_prevalence_baseline"].reset_index(drop=True)
    assert len(baseline_rows) == 3
    assert baseline_rows["cross_city_pr_auc"].isna().all()
    assert baseline_rows["cross_city_recall_at_top_10pct"].isna().all()

    best_params_df = pd.read_csv(result.best_params_path)
    baseline_best_params = best_params_df.loc[best_params_df["model_name"] == "city_prevalence_baseline"]
    assert len(baseline_best_params) == 9
    assert set(baseline_best_params["best_params_json"]) == {"{}"}

    summary_text = result.summary_markdown_path.read_text(encoding="utf-8")
    assert "city_prevalence_baseline" in summary_text
    assert "within-city-only contextual baseline" in summary_text

    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    assert metadata["sample_rows_per_city"] == 60
    assert metadata["supplemental_within_city_baseline_model"] == "city_prevalence_baseline"
    assert metadata["output_files"]["recall_figure"] == str(result.recall_figure_path)


def test_plot_within_city_recall_contrast_writes_figure(tmp_path: Path) -> None:
    contrast_df = pd.DataFrame(
        [
            {
                "city_name": "Reno",
                "climate_group": "hot_arid",
                "model_name": "logistic_saga",
                "within_city_recall_at_top_10pct_mean": 0.52,
                "cross_city_recall_at_top_10pct": 0.24,
            },
            {
                "city_name": "Charlotte",
                "climate_group": "hot_humid",
                "model_name": "random_forest",
                "within_city_recall_at_top_10pct_mean": 0.48,
                "cross_city_recall_at_top_10pct": 0.22,
            },
            {
                "city_name": "Detroit",
                "climate_group": "mild_cool",
                "model_name": "city_prevalence_baseline",
                "within_city_recall_at_top_10pct_mean": 0.30,
                "cross_city_recall_at_top_10pct": float("nan"),
            },
        ]
    )

    output_path = tmp_path / "figures" / "within_city_recall_contrast.png"
    returned_path = plot_within_city_recall_contrast(contrast_df=contrast_df, output_path=output_path)

    assert returned_path == output_path
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_assign_within_city_spatial_blocks_is_deterministic_quadrant_rule() -> None:
    city_df = pd.DataFrame(
        {
            "centroid_lon": [-1.0, 1.0, -1.0, 1.0, 0.0],
            "centroid_lat": [-1.0, -1.0, 1.0, 1.0, 0.0],
        }
    )

    blocked_df = assign_within_city_spatial_blocks(city_df)

    assert blocked_df["spatial_block_id"].tolist() == [
        "southwest",
        "southeast",
        "northwest",
        "northeast",
        "northeast",
    ]


def test_make_within_city_spatial_block_splits_hold_out_non_overlapping_blocks() -> None:
    city_df = assign_within_city_spatial_blocks(_build_spatial_within_city_fixture().loc[lambda df: df["city_id"] == 1])

    splits = make_within_city_spatial_block_splits(city_df)

    assert {split.held_out_block for split in splits} == {"southwest", "southeast", "northwest", "northeast"}
    for split in splits:
        train_ids = set(city_df.iloc[split.train_index]["cell_id"].tolist())
        test_ids = set(city_df.iloc[split.test_index]["cell_id"].tolist())
        assert train_ids.isdisjoint(test_ids)
        assert set(city_df.iloc[split.test_index]["spatial_block_id"]) == {split.held_out_block}
        assert split.held_out_block not in set(city_df.iloc[split.train_index]["spatial_block_id"])


def test_generate_within_city_spatial_sensitivity_artifacts_writes_separate_logistic_only_outputs(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "final_dataset.parquet"
    comparison_path = tmp_path / "city_error.csv"
    default_within_city_summary_path = (
        tmp_path / "outputs" / "modeling" / "supplemental" / "within_city" / "tables" / "within_city_summary.csv"
    )
    _build_spatial_within_city_fixture().to_parquet(dataset_path, index=False)
    pd.DataFrame(
        [
            {"outer_fold": 0, "city_id": 1, "city_name": "Reno", "climate_group": "hot_arid", "pr_auc_logistic": 0.13},
            {"outer_fold": 1, "city_id": 2, "city_name": "Charlotte", "climate_group": "hot_humid", "pr_auc_logistic": 0.17},
            {"outer_fold": 2, "city_id": 3, "city_name": "Detroit", "climate_group": "mild_cool", "pr_auc_logistic": 0.15},
        ]
    ).to_csv(comparison_path, index=False)
    default_within_city_summary_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "city_id": 1,
                "city_name": "Reno",
                "climate_group": "hot_arid",
                "model_name": "logistic_saga",
                "repeat_count": 3,
                "within_city_pr_auc_mean": 0.62,
                "within_city_recall_at_top_10pct_mean": 0.41,
            },
            {
                "city_id": 2,
                "city_name": "Charlotte",
                "climate_group": "hot_humid",
                "model_name": "logistic_saga",
                "repeat_count": 3,
                "within_city_pr_auc_mean": 0.59,
                "within_city_recall_at_top_10pct_mean": 0.38,
            },
            {
                "city_id": 3,
                "city_name": "Detroit",
                "climate_group": "mild_cool",
                "model_name": "logistic_saga",
                "repeat_count": 3,
                "within_city_pr_auc_mean": 0.57,
                "within_city_recall_at_top_10pct_mean": 0.36,
            },
        ]
    ).to_csv(default_within_city_summary_path, index=False)

    logistic_ref_dir = tmp_path / "outputs" / "modeling" / "logistic_saga" / "retained_logistic"
    logistic_ref_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "model_name": "logistic_saga",
                "outer_fold": 0,
                "city_id": 1,
                "city_name": "Reno",
                "climate_group": "hot_arid",
                "row_count": 64,
                "positive_count": 30,
                "prevalence": 30 / 64,
                "pr_auc": 0.23,
                "recall_at_top_10pct": 0.19,
            },
            {
                "model_name": "logistic_saga",
                "outer_fold": 1,
                "city_id": 2,
                "city_name": "Charlotte",
                "climate_group": "hot_humid",
                "row_count": 64,
                "positive_count": 30,
                "prevalence": 30 / 64,
                "pr_auc": 0.25,
                "recall_at_top_10pct": 0.18,
            },
            {
                "model_name": "logistic_saga",
                "outer_fold": 2,
                "city_id": 3,
                "city_name": "Detroit",
                "climate_group": "mild_cool",
                "row_count": 64,
                "positive_count": 30,
                "prevalence": 30 / 64,
                "pr_auc": 0.22,
                "recall_at_top_10pct": 0.17,
            },
        ]
    ).to_csv(logistic_ref_dir / "metrics_by_city.csv", index=False)

    result = generate_within_city_spatial_sensitivity_artifacts(
        dataset_path=dataset_path,
        city_error_table_path=comparison_path,
        default_within_city_summary_path=default_within_city_summary_path,
        output_dir=tmp_path / "outputs" / "modeling" / "supplemental" / "within_city_spatial",
        figures_dir=tmp_path / "figures" / "modeling" / "supplemental" / "within_city_spatial",
        sample_rows_per_city=64,
        logistic_reference_run_dir=logistic_ref_dir,
        grid_search_n_jobs=1,
    )

    assert result.summary_markdown_path.exists()
    assert result.split_metrics_path.exists()
    assert result.contrast_table_path.exists()
    assert result.best_params_path.exists()
    assert result.predictions_path.exists()
    assert result.figure_path.exists()

    split_metrics_df = pd.read_csv(result.split_metrics_path)
    contrast_df = pd.read_csv(result.contrast_table_path)
    predictions_df = pd.read_parquet(result.predictions_path)

    assert set(split_metrics_df["model_name"]) == {"logistic_saga"}
    assert set(split_metrics_df["held_out_block"]) == {"southwest", "southeast", "northwest", "northeast"}
    assert set(contrast_df["city_name"]) == {"Reno", "Charlotte", "Detroit"}
    assert {
        "default_within_city_pr_auc_mean",
        "spatial_within_city_pr_auc_mean",
        "cross_city_pr_auc",
        "spatial_minus_default_pr_auc_gap",
        "spatial_minus_cross_city_pr_auc_gap",
    }.issubset(contrast_df.columns)
    assert set(predictions_df["held_out_block"]) == {"southwest", "southeast", "northwest", "northeast"}
    assert set(predictions_df["spatial_block_id"]).issubset({"southwest", "southeast", "northwest", "northeast"})

    summary_text = result.summary_markdown_path.read_text(encoding="utf-8")
    assert "harder within-city sensitivity" in summary_text
    assert "not equivalent to the canonical cross-city city-held-out benchmark" in summary_text
    assert "logistic SAGA only" in summary_text

    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    assert metadata["model_name"] == "logistic_saga"
    assert "deterministic centroid quadrants" in metadata["spatial_block_rule"]
    assert metadata["output_files"]["metrics"] == str(result.split_metrics_path)


def test_plot_within_city_spatial_pr_auc_contrast_writes_figure(tmp_path: Path) -> None:
    contrast_df = pd.DataFrame(
        [
            {
                "city_name": "Reno",
                "climate_group": "hot_arid",
                "default_within_city_pr_auc_mean": 0.61,
                "spatial_within_city_pr_auc_mean": 0.48,
                "cross_city_pr_auc": 0.24,
            },
            {
                "city_name": "Charlotte",
                "climate_group": "hot_humid",
                "default_within_city_pr_auc_mean": 0.58,
                "spatial_within_city_pr_auc_mean": 0.44,
                "cross_city_pr_auc": 0.22,
            },
        ]
    )

    output_path = tmp_path / "figures" / "within_city_spatial_pr_auc_contrast.png"
    returned_path = plot_within_city_spatial_pr_auc_contrast(contrast_df=contrast_df, output_path=output_path)

    assert returned_path == output_path
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_feature_importance_artifacts_refits_saved_outer_fold_winners(tmp_path: Path) -> None:
    dataset_path = tmp_path / "final_dataset.parquet"
    folds_path = tmp_path / "city_outer_folds.parquet"
    _build_grouped_fixture().to_parquet(dataset_path, index=False)
    _build_grouped_folds().to_parquet(folds_path, index=False)

    logistic_run_dir = tmp_path / "outputs" / "modeling" / "logistic_saga" / "retained_logistic"
    rf_run_dir = tmp_path / "outputs" / "modeling" / "random_forest" / "retained_rf"

    run_logistic_saga_model(
        dataset_path=dataset_path,
        folds_path=folds_path,
        output_dir=logistic_run_dir,
        selected_outer_folds=[0, 1],
        param_grid=[{"model__C": [0.1], "model__l1_ratio": [0.0]}],
        grid_search_n_jobs=1,
    )
    run_random_forest_model(
        dataset_path=dataset_path,
        folds_path=folds_path,
        output_dir=rf_run_dir,
        selected_outer_folds=[0, 1],
        param_grid=[
            {
                "model__n_estimators": [10],
                "model__max_depth": [3],
                "model__max_features": ["sqrt"],
                "model__min_samples_leaf": [1],
            }
        ],
        grid_search_n_jobs=1,
        model_n_jobs=1,
    )

    result = generate_feature_importance_artifacts(
        logistic_run_dir=logistic_run_dir,
        random_forest_run_dir=rf_run_dir,
        output_dir=tmp_path / "outputs" / "modeling" / "supplemental" / "feature_importance",
        figures_dir=tmp_path / "figures" / "modeling" / "supplemental" / "feature_importance",
        rf_permutation_repeats=3,
        permutation_n_jobs=1,
    )

    assert result.summary_markdown_path.exists()
    assert result.logistic_coefficients_summary_path.exists()
    assert result.logistic_permutation_by_fold_path.exists()
    assert result.logistic_permutation_summary_path.exists()
    assert result.rf_permutation_summary_path.exists()
    assert result.rf_impurity_by_fold_path.exists()
    assert result.rf_impurity_summary_path.exists()
    assert result.figure_path.exists()

    logistic_summary_df = pd.read_csv(result.logistic_coefficients_summary_path)
    logistic_permutation_by_fold_df = pd.read_csv(result.logistic_permutation_by_fold_path)
    logistic_permutation_summary_df = pd.read_csv(result.logistic_permutation_summary_path)
    rf_summary_df = pd.read_csv(result.rf_permutation_summary_path)
    rf_impurity_by_fold_df = pd.read_csv(result.rf_impurity_by_fold_path)
    rf_impurity_summary_df = pd.read_csv(result.rf_impurity_summary_path)

    assert "median_coefficient" in logistic_summary_df.columns
    assert "sign_consistency" in logistic_summary_df.columns
    assert set(logistic_permutation_by_fold_df["feature_name"]) == set(DEFAULT_FEATURE_COLUMNS)
    assert {
        "mean_pr_auc_drop",
        "median_rank",
        "stability_positive_drop_fraction",
    }.issubset(logistic_permutation_summary_df.columns)
    assert "mean_pr_auc_drop" in rf_summary_df.columns
    assert "stability_positive_drop_fraction" in rf_summary_df.columns
    assert set(rf_impurity_by_fold_df["feature_name"]) == set(DEFAULT_FEATURE_COLUMNS)
    assert {
        "mean_impurity_importance",
        "median_rank",
        "stability_positive_importance_fraction",
    }.issubset(rf_impurity_summary_df.columns)

    summary_markdown = result.summary_markdown_path.read_text(encoding="utf-8")
    assert "Logistic coefficients remain the primary logistic interpretation artifact." in summary_markdown
    assert "cross-check on that coefficient story" in summary_markdown
    assert "Random-forest held-out permutation importance remains the primary RF interpretation artifact." in summary_markdown
    assert "secondary appendix/debug output" in summary_markdown

    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    assert metadata["rf_permutation_repeats"] == 3
    assert metadata["logistic_permutation_repeats"] == 3
    assert "logistic_permutation_summary" in metadata["output_files"]
    assert "rf_impurity_summary" in metadata["output_files"]
