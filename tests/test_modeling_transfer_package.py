from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from joblib import load

from src.modeling_transfer_package import (
    build_final_transfer_package,
    build_transfer_package_dirname,
    select_consensus_hyperparameters,
)


def _build_transfer_dataset() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    city_specs = [
        (1, "Phoenix", "hot_arid"),
        (2, "Tucson", "hot_arid"),
        (3, "Seattle", "mild_cool"),
        (4, "Portland", "mild_cool"),
    ]
    for city_id, city_name, climate_group in city_specs:
        for idx in range(12):
            hotspot = idx >= 6
            rows.append(
                {
                    "city_id": city_id,
                    "city_name": city_name,
                    "climate_group": climate_group,
                    "cell_id": (city_id * 1000) + idx,
                    "centroid_lon": -120.0 + city_id + (idx * 0.01),
                    "centroid_lat": 30.0 + city_id + (idx * 0.01),
                    "impervious_pct": float(10 + idx + city_id),
                    "land_cover_class": 21 if idx < 6 else 24,
                    "elevation_m": float(100 + city_id + idx),
                    "dist_to_water_m": float(500 - (idx * 10)),
                    "ndvi_median_may_aug": float(0.20 + (idx * 0.01)),
                    "lst_median_may_aug": float(30 + city_id + idx),
                    "n_valid_ecostress_passes": 5,
                    "hotspot_10pct": hotspot,
                }
            )
    return pd.DataFrame(rows)


def _build_transfer_folds() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "city_id": [1, 2, 3, 4],
            "city_name": ["Phoenix", "Tucson", "Seattle", "Portland"],
            "climate_group": ["hot_arid", "hot_arid", "mild_cool", "mild_cool"],
            "row_count": [12, 12, 12, 12],
            "hotspot_positive_count": [6, 6, 6, 6],
            "hotspot_non_missing_count": [12, 12, 12, 12],
            "hotspot_prevalence": [0.5, 0.5, 0.5, 0.5],
            "outer_fold": [0, 1, 2, 3],
        }
    )


def _write_reference_run_fixture(run_dir: Path, folds_path: Path) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "model_name": "random_forest",
                "outer_fold": 0,
                "inner_cv_splits": 3,
                "best_inner_cv_average_precision": 0.18,
                "best_params_json": json.dumps(
                    {
                        "model__max_depth": 10,
                        "model__max_features": "sqrt",
                        "model__min_samples_leaf": 5,
                        "model__n_estimators": 200,
                    },
                    sort_keys=True,
                ),
            },
            {
                "model_name": "random_forest",
                "outer_fold": 1,
                "inner_cv_splits": 3,
                "best_inner_cv_average_precision": 0.22,
                "best_params_json": json.dumps(
                    {
                        "model__max_depth": 10,
                        "model__max_features": "sqrt",
                        "model__min_samples_leaf": 5,
                        "model__n_estimators": 300,
                    },
                    sort_keys=True,
                ),
            },
            {
                "model_name": "random_forest",
                "outer_fold": 2,
                "inner_cv_splits": 3,
                "best_inner_cv_average_precision": 0.24,
                "best_params_json": json.dumps(
                    {
                        "model__max_depth": 10,
                        "model__max_features": "sqrt",
                        "model__min_samples_leaf": 5,
                        "model__n_estimators": 300,
                    },
                    sort_keys=True,
                ),
            },
        ]
    ).to_csv(run_dir / "best_params_by_fold.csv", index=False)
    (run_dir / "feature_contract.json").write_text(
        json.dumps(
            {
                "selected_feature_columns": [
                    "impervious_pct",
                    "elevation_m",
                    "dist_to_water_m",
                    "ndvi_median_may_aug",
                    "land_cover_class",
                    "climate_group",
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (run_dir / "run_metadata.json").write_text(
        json.dumps(
            {
                "model_name": "random_forest",
                "tuning_preset": "frontier",
                "sample_rows_per_city": 8,
                "random_state": 42,
                "model_n_jobs": 1,
                "pipeline_builder_kwargs": {},
                "folds_path": str(folds_path),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def test_build_transfer_package_dirname_is_deterministic() -> None:
    assert (
        build_transfer_package_dirname(
            model_name="random_forest",
            tuning_preset="frontier",
            sample_rows_per_city=5000,
        )
        == "random_forest_frontier_s5000_all_cities_transfer_package"
    )


def test_select_consensus_hyperparameters_prefers_mode_then_score() -> None:
    best_params_df = pd.DataFrame(
        [
            {
                "outer_fold": 0,
                "best_inner_cv_average_precision": 0.18,
                "best_params_json": json.dumps({"model__n_estimators": 200}, sort_keys=True),
            },
            {
                "outer_fold": 1,
                "best_inner_cv_average_precision": 0.21,
                "best_params_json": json.dumps({"model__n_estimators": 300}, sort_keys=True),
            },
            {
                "outer_fold": 2,
                "best_inner_cv_average_precision": 0.24,
                "best_params_json": json.dumps({"model__n_estimators": 300}, sort_keys=True),
            },
        ]
    )

    result = select_consensus_hyperparameters(best_params_df)

    assert result.selected_params == {"model__n_estimators": 300}
    assert int(result.summary_df.loc[0, "fold_count"]) == 2


def test_build_final_transfer_package_writes_expected_artifacts(workspace_tmp_path: Path) -> None:
    dataset_path = workspace_tmp_path / "data_processed" / "final" / "final_dataset.parquet"
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    folds_path = workspace_tmp_path / "data_processed" / "modeling" / "city_outer_folds.parquet"
    folds_path.parent.mkdir(parents=True, exist_ok=True)
    run_dir = workspace_tmp_path / "outputs" / "modeling" / "random_forest" / "rf_frontier"

    _build_transfer_dataset().to_parquet(dataset_path, index=False)
    _build_transfer_folds().to_parquet(folds_path, index=False)
    _write_reference_run_fixture(run_dir, folds_path)

    result = build_final_transfer_package(
        reference_run_dir=run_dir,
        dataset_path=dataset_path,
        folds_path=folds_path,
        output_dir=workspace_tmp_path / "outputs" / "modeling" / "final_train" / "transfer_package",
    )

    assert result.model_artifact_path.exists()
    assert result.metadata_path.exists()
    assert result.feature_contract_path.exists()
    assert result.preprocessing_manifest_path.exists()
    assert result.hyperparameter_summary_path.exists()
    assert result.selected_hyperparameters_path.exists()
    assert result.training_city_summary_path.exists()
    assert result.training_sample_diagnostics_path is not None
    assert result.training_sample_diagnostics_path.exists()

    package_metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    assert package_metadata["source_reference_model_name"] == "random_forest"
    assert package_metadata["sample_rows_per_city"] == 8
    assert package_metadata["training_city_count"] == 4

    model = load(result.model_artifact_path)
    sample_df = _build_transfer_dataset().iloc[:4].copy()
    probabilities = model.predict_proba(
        sample_df[
            [
                "impervious_pct",
                "elevation_m",
                "dist_to_water_m",
                "ndvi_median_may_aug",
                "land_cover_class",
                "climate_group",
            ]
        ]
    )
    assert probabilities.shape == (4, 2)
