from pathlib import Path

import pandas as pd
import pytest

from src.model_baselines import (
    join_batch_to_outer_folds,
    load_city_outer_folds,
    run_baseline_modeling,
    validate_model_feature_columns,
)


def _build_baseline_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "city_id": [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4],
            "city_name": [
                "Phoenix",
                "Phoenix",
                "Phoenix",
                "Phoenix",
                "Tucson",
                "Tucson",
                "Tucson",
                "Tucson",
                "Miami",
                "Miami",
                "Miami",
                "Miami",
                "Atlanta",
                "Atlanta",
                "Atlanta",
                "Atlanta",
            ],
            "climate_group": [
                "hot_arid",
                "hot_arid",
                "hot_arid",
                "hot_arid",
                "hot_arid",
                "hot_arid",
                "hot_arid",
                "hot_arid",
                "humid_subtropical",
                "humid_subtropical",
                "humid_subtropical",
                "humid_subtropical",
                "humid_subtropical",
                "humid_subtropical",
                "humid_subtropical",
                "humid_subtropical",
            ],
            "cell_id": list(range(1, 17)),
            "centroid_lon": [-112.1] * 4 + [-110.9] * 4 + [-80.2] * 4 + [-84.3] * 4,
            "centroid_lat": [33.4] * 4 + [32.2] * 4 + [25.7] * 4 + [33.7] * 4,
            "impervious_pct": [10, 25, 50, 75, 12, 28, 55, 78, 20, 35, 60, 85, 18, 33, 58, 82],
            "land_cover_class": [21, 21, 22, 24, 21, 22, 22, 24, 11, 21, 22, 24, 21, 22, 22, 24],
            "elevation_m": [350, 355, 360, 365, 700, 705, 710, 715, 4, 5, 6, 7, 300, 305, 310, 315],
            "dist_to_water_m": [500, 400, 200, 50, 600, 450, 240, 40, 50, 45, 30, 20, 550, 430, 210, 55],
            "ndvi_median_may_aug": [0.20, 0.21, 0.24, 0.18, 0.25, 0.26, 0.22, 0.19, 0.45, 0.44, 0.38, 0.36, 0.41, 0.39, None, 0.33],
            "lst_median_may_aug": [38.0, 39.0, 41.0, 44.0, 34.0, 35.0, 37.0, 39.0, 31.0, 32.0, 34.0, 36.0, 33.0, 34.0, 36.0, 38.0],
            "n_valid_ecostress_passes": [5, 6, 5, 6, 4, 4, 5, 5, 9, 9, 8, 8, 7, 7, 6, 6],
            "hotspot_10pct": [
                False,
                False,
                True,
                True,
                False,
                False,
                True,
                True,
                False,
                False,
                True,
                True,
                False,
                False,
                True,
                True,
            ],
        }
    )


def _build_fold_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "city_id": [1, 2, 3, 4],
            "city_name": ["Phoenix", "Tucson", "Miami", "Atlanta"],
            "climate_group": ["hot_arid", "hot_arid", "humid_subtropical", "humid_subtropical"],
            "row_count": [4, 4, 4, 4],
            "hotspot_positive_count": [2, 2, 2, 2],
            "hotspot_non_missing_count": [4, 4, 4, 4],
            "hotspot_prevalence": [0.5, 0.5, 0.5, 0.5],
            "n_valid_ecostress_passes_non_missing_count": [4, 4, 4, 4],
            "n_valid_ecostress_passes_min": [5, 4, 8, 6],
            "n_valid_ecostress_passes_median": [5.5, 4.5, 8.5, 6.5],
            "n_valid_ecostress_passes_mean": [5.5, 4.5, 8.5, 6.5],
            "n_valid_ecostress_passes_max": [6, 5, 9, 7],
            "outer_fold": [0, 0, 1, 1],
        }
    )


def test_validate_model_feature_columns_rejects_leakage_columns():
    available_columns = _build_baseline_fixture().columns.tolist()

    with pytest.raises(ValueError, match="lst_median_may_aug"):
        validate_model_feature_columns(
            feature_columns=["impervious_pct", "lst_median_may_aug"],
            available_columns=available_columns,
        )


def test_join_batch_to_outer_folds_maps_city_ids():
    batch_df = pd.DataFrame({"city_id": [1, 2, 99], "value": [1, 2, 3]})

    joined = join_batch_to_outer_folds(batch_df=batch_df, fold_lookup={1: 0, 2: 1})

    assert joined["outer_fold"].tolist()[:2] == [0, 1]
    assert pd.isna(joined.loc[2, "outer_fold"])


def test_load_city_outer_folds_reads_csv_and_validates_duplicates(tmp_path: Path):
    folds_path = tmp_path / "city_outer_folds.csv"
    duplicate_folds = _build_fold_fixture()
    duplicate_folds.loc[3, "city_id"] = 3
    duplicate_folds.to_csv(folds_path, index=False)

    with pytest.raises(ValueError, match="duplicate city assignments"):
        load_city_outer_folds(folds_path)


def test_run_baseline_modeling_writes_metrics_predictions_and_artifacts(tmp_path: Path):
    dataset_path = tmp_path / "final_dataset.parquet"
    folds_path = tmp_path / "city_outer_folds.parquet"
    output_dir = tmp_path / "modeling_baselines"

    _build_baseline_fixture().to_parquet(dataset_path, index=False)
    _build_fold_fixture().to_parquet(folds_path, index=False)

    result = run_baseline_modeling(
        dataset_path=dataset_path,
        folds_path=folds_path,
        output_dir=output_dir,
        batch_size=5,
        max_logistic_iterations=4,
        tree_sample_per_city=3,
        decision_stump_min_leaf_rows=1,
    )

    assert result.fold_metrics_path.exists()
    assert result.overall_metrics_path.exists()
    assert result.assumptions_path.exists()
    assert result.summary_json_path.exists()
    assert result.model_artifacts_dir.exists()

    fold_metrics = pd.read_csv(result.fold_metrics_path)
    assert set(fold_metrics["model_name"]) == {"logistic_regression", "decision_stump"}
    assert fold_metrics.shape[0] == 4
    assert {"roc_auc", "pr_auc", "validation_prevalence"}.issubset(fold_metrics.columns)

    overall_metrics = pd.read_csv(result.overall_metrics_path)
    assert overall_metrics.shape[0] == 2
    assert set(overall_metrics["model_name"]) == {"logistic_regression", "decision_stump"}

    logistic_predictions = pd.read_parquet(result.predictions_dir / "logistic_regression" / "outer_fold=0.parquet")
    assert set(logistic_predictions["city_id"]) == {1, 2}
    assert {"predicted_probability", "hotspot_10pct"}.issubset(logistic_predictions.columns)

    stump_predictions = pd.read_parquet(result.predictions_dir / "decision_stump" / "outer_fold=1.parquet")
    assert set(stump_predictions["city_id"]) == {3, 4}

    logistic_coefficients = pd.read_csv(result.model_artifacts_dir / "logistic_regression_coefficients.csv")
    assert "feature_name" in logistic_coefficients.columns
    stump_rules = pd.read_csv(result.model_artifacts_dir / "decision_stump_rules.csv")
    assert stump_rules.shape[0] == 2

    assumptions_text = result.assumptions_path.read_text(encoding="utf-8")
    assert "Overall metrics are aggregated from fold-level metrics" in assumptions_text
    assert "Explicitly excluded leakage-prone columns" in assumptions_text
