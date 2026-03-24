from pathlib import Path

import pandas as pd

from src.modeling_baselines import run_modeling_baselines
from src.modeling_config import DEFAULT_FEATURE_COLUMNS
from src.modeling_runner import run_logistic_saga_model, run_random_forest_model


def _build_modeling_fixture() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    city_specs = [
        (1, "Phoenix", "hot_arid", 0),
        (2, "Tucson", "hot_arid", 0),
        (3, "Miami", "humid_subtropical", 1),
        (4, "Atlanta", "humid_subtropical", 1),
    ]
    for city_id, city_name, climate_group, fold_id in city_specs:
        for idx in range(10):
            impervious = 8 + (idx * 9) + (city_id * 2)
            ndvi = 0.15 + (idx * 0.035)
            hotspot = idx >= 5
            rows.append(
                {
                    "city_id": city_id,
                    "city_name": city_name,
                    "climate_group": climate_group,
                    "cell_id": (city_id * 1000) + idx,
                    "centroid_lon": -100.0 - city_id - (idx * 0.01),
                    "centroid_lat": 30.0 + city_id + (idx * 0.01),
                    "impervious_pct": float(impervious),
                    "land_cover_class": 21 if idx < 5 else 24,
                    "elevation_m": float((city_id * 50) + idx),
                    "dist_to_water_m": float(600 - (idx * 45) + (city_id * 3)),
                    "ndvi_median_may_aug": float(ndvi),
                    "lst_median_may_aug": float(32 + city_id + idx),
                    "n_valid_ecostress_passes": 5,
                    "hotspot_10pct": hotspot,
                }
            )
    return pd.DataFrame(rows)


def _build_fold_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "city_id": [1, 2, 3, 4],
            "city_name": ["Phoenix", "Tucson", "Miami", "Atlanta"],
            "climate_group": ["hot_arid", "hot_arid", "humid_subtropical", "humid_subtropical"],
            "row_count": [10, 10, 10, 10],
            "hotspot_positive_count": [5, 5, 5, 5],
            "hotspot_non_missing_count": [10, 10, 10, 10],
            "hotspot_prevalence": [0.5, 0.5, 0.5, 0.5],
            "outer_fold": [0, 0, 1, 1],
        }
    )


def test_run_modeling_baselines_writes_expected_artifacts(tmp_path: Path):
    dataset_path = tmp_path / "final_dataset.parquet"
    folds_path = tmp_path / "city_outer_folds.parquet"
    output_dir = tmp_path / "outputs" / "modeling" / "baselines"
    _build_modeling_fixture().to_parquet(dataset_path, index=False)
    _build_fold_fixture().to_parquet(folds_path, index=False)

    result = run_modeling_baselines(
        dataset_path=dataset_path,
        folds_path=folds_path,
        output_dir=output_dir,
    )

    assert result.fold_metrics_path.exists()
    assert result.city_metrics_path.exists()
    assert result.summary_metrics_path.exists()
    assert result.predictions_path.exists()
    assert result.calibration_curve_path.exists()
    assert result.metadata_path.exists()

    fold_metrics = pd.read_csv(result.fold_metrics_path)
    assert set(fold_metrics["model_name"]) == {
        "global_mean_baseline",
        "land_cover_only_baseline",
        "impervious_only_baseline",
        "climate_only_baseline",
    }

    predictions = pd.read_parquet(result.predictions_path)
    assert {"predicted_probability", "hotspot_10pct", "centroid_lon", "centroid_lat"}.issubset(predictions.columns)


def test_run_logistic_and_random_forest_write_expected_artifacts(tmp_path: Path):
    dataset_path = tmp_path / "final_dataset.parquet"
    folds_path = tmp_path / "city_outer_folds.parquet"
    _build_modeling_fixture().to_parquet(dataset_path, index=False)
    _build_fold_fixture().to_parquet(folds_path, index=False)

    logistic_output_dir = tmp_path / "outputs" / "modeling" / "logistic_saga"
    random_forest_output_dir = tmp_path / "outputs" / "modeling" / "random_forest"

    logistic_result = run_logistic_saga_model(
        dataset_path=dataset_path,
        folds_path=folds_path,
        output_dir=logistic_output_dir,
        feature_columns=DEFAULT_FEATURE_COLUMNS,
        param_grid=[{"model__penalty": ["l2"], "model__C": [0.1, 1.0]}],
    )
    forest_result = run_random_forest_model(
        dataset_path=dataset_path,
        folds_path=folds_path,
        output_dir=random_forest_output_dir,
        feature_columns=DEFAULT_FEATURE_COLUMNS,
        param_grid=[
            {
                "model__n_estimators": [10],
                "model__max_depth": [3],
                "model__max_features": ["sqrt"],
                "model__min_samples_leaf": [1],
            }
        ],
    )

    for result in (logistic_result, forest_result):
        assert result.fold_metrics_path.exists()
        assert result.city_metrics_path.exists()
        assert result.summary_metrics_path.exists()
        assert result.best_params_path.exists()
        assert result.predictions_path.exists()
        assert result.calibration_curve_path.exists()
        assert result.metadata_path.exists()

        fold_metrics = pd.read_csv(result.fold_metrics_path)
        assert {"pr_auc", "recall_at_top_10pct", "best_inner_cv_average_precision"}.issubset(fold_metrics.columns)

        city_metrics = pd.read_csv(result.city_metrics_path)
        assert {"city_id", "city_name", "pr_auc"}.issubset(city_metrics.columns)

        predictions = pd.read_parquet(result.predictions_path)
        assert {"predicted_probability", "centroid_lon", "centroid_lat"}.issubset(predictions.columns)
