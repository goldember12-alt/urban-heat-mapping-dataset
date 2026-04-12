from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.modeling_data import write_feature_contract
from src.modeling_runner import build_random_forest_pipeline
from src.modeling_transfer_inference import (
    build_transfer_inference_id,
    load_transfer_package,
    resolve_transfer_inference_paths,
    run_transfer_inference,
    validate_transfer_input_schema,
)

FEATURE_COLUMNS = [
    "impervious_pct",
    "elevation_m",
    "dist_to_water_m",
    "ndvi_median_may_aug",
    "land_cover_class",
    "climate_group",
]


def _build_training_df() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for idx in range(16):
        hotspot = idx >= 8
        rows.append(
            {
                "impervious_pct": float(10 + idx),
                "elevation_m": float(100 + idx),
                "dist_to_water_m": float(600 - (idx * 15)),
                "ndvi_median_may_aug": float(0.15 + (idx * 0.02)),
                "land_cover_class": 21 if idx < 8 else 24,
                "climate_group": "hot_arid" if idx % 2 == 0 else "hot_humid",
                "hotspot_10pct": hotspot,
            }
        )
    return pd.DataFrame(rows)


def _build_input_df(*, include_centroids: bool = True) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for idx in range(10):
        row: dict[str, object] = {
            "city_id": 99,
            "city_name": "Testopolis",
            "cell_id": 9000 + idx,
            "impervious_pct": float(12 + idx),
            "elevation_m": float(120 + idx),
            "dist_to_water_m": float(500 - (idx * 12)),
            "ndvi_median_may_aug": float(0.20 + (idx * 0.015)),
            "land_cover_class": 21 if idx < 5 else 24,
            "climate_group": "hot_arid",
        }
        if include_centroids:
            row["centroid_lon"] = -111.95 + (idx * 0.01)
            row["centroid_lat"] = 33.40 + (idx * 0.01)
        rows.append(row)
    return pd.DataFrame(rows)


def _write_transfer_package_fixture(package_dir: Path) -> None:
    package_dir.mkdir(parents=True, exist_ok=True)
    training_df = _build_training_df()
    pipeline = build_random_forest_pipeline(feature_columns=FEATURE_COLUMNS, random_state=42, n_jobs=1)
    pipeline.set_params(
        model__n_estimators=25,
        model__max_depth=4,
        model__max_features="sqrt",
        model__min_samples_leaf=1,
    )
    pipeline.fit(training_df[FEATURE_COLUMNS], training_df["hotspot_10pct"].astype("int8"))

    from joblib import dump

    dump(pipeline, package_dir / "model.joblib")
    write_feature_contract(package_dir / "feature_contract.json", feature_columns=FEATURE_COLUMNS)
    (package_dir / "preprocessing_manifest.json").write_text(
        json.dumps(
            {
                "model_name": "random_forest",
                "selected_feature_columns": FEATURE_COLUMNS,
                "feature_type_map": {
                    "impervious_pct": "numeric",
                    "elevation_m": "numeric",
                    "dist_to_water_m": "numeric",
                    "ndvi_median_may_aug": "numeric",
                    "land_cover_class": "categorical",
                    "climate_group": "categorical",
                },
                "preprocessing_steps": {
                    "numeric": ["coerce_numeric", "median_imputer"],
                    "categorical": ["coerce_categorical", "most_frequent_imputer", "ordinal_encoder_unknown=-1"],
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (package_dir / "transfer_package_metadata.json").write_text(
        json.dumps(
            {
                "artifact_kind": "final_train_transfer_package",
                "source_reference_run_dir": "outputs/modeling/random_forest/retained_rf_frontier",
                "source_reference_model_name": "random_forest",
                "source_reference_tuning_preset": "frontier",
                "selected_feature_columns": FEATURE_COLUMNS,
                "benchmark_framing_note": "This package supports the canonical cross-city benchmark story.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def test_load_transfer_package_reads_contract_and_model(workspace_tmp_path: Path) -> None:
    package_dir = workspace_tmp_path / "outputs" / "modeling" / "final_train" / "transfer_package"
    _write_transfer_package_fixture(package_dir)

    loaded_package = load_transfer_package(package_dir=package_dir)

    assert loaded_package.package_dir == package_dir.resolve()
    assert loaded_package.selected_feature_columns == FEATURE_COLUMNS
    assert "climate_group" in loaded_package.feature_type_map
    assert hasattr(loaded_package.model, "predict_proba")


def test_validate_transfer_input_schema_raises_on_missing_columns() -> None:
    input_columns = ["cell_id", "impervious_pct", "elevation_m", "dist_to_water_m", "land_cover_class"]

    try:
        validate_transfer_input_schema(input_columns, required_feature_columns=FEATURE_COLUMNS)
    except ValueError as exc:
        assert "ndvi_median_may_aug" in str(exc)
        assert "climate_group" in str(exc)
    else:
        raise AssertionError("Expected validate_transfer_input_schema to reject missing required columns")


def test_resolve_transfer_inference_paths_is_deterministic(workspace_tmp_path: Path) -> None:
    inference_id = build_transfer_inference_id(Path("05_el_paso_tx_features.parquet"))
    first = resolve_transfer_inference_paths(
        inference_id=inference_id,
        outputs_root=workspace_tmp_path / "outputs" / "modeling" / "transfer_inference",
        figures_root=workspace_tmp_path / "figures" / "modeling" / "transfer_inference",
    )
    second = resolve_transfer_inference_paths(
        inference_id=inference_id,
        outputs_root=workspace_tmp_path / "outputs" / "modeling" / "transfer_inference",
        figures_root=workspace_tmp_path / "figures" / "modeling" / "transfer_inference",
    )

    assert inference_id == "05_el_paso_tx"
    assert first.output_dir == second.output_dir
    assert first.figure_path == second.figure_path


def test_run_transfer_inference_writes_prediction_tables_and_map_artifacts(workspace_tmp_path: Path) -> None:
    package_dir = workspace_tmp_path / "outputs" / "modeling" / "final_train" / "transfer_package"
    input_parquet_path = workspace_tmp_path / "data_processed" / "city_features" / "99_testopolis_features.parquet"
    _write_transfer_package_fixture(package_dir)
    input_parquet_path.parent.mkdir(parents=True, exist_ok=True)
    _build_input_df(include_centroids=True).to_parquet(input_parquet_path, index=False)

    result = run_transfer_inference(
        input_parquet_path=input_parquet_path,
        package_dir=package_dir,
        outputs_root=workspace_tmp_path / "outputs" / "modeling" / "transfer_inference",
        figures_root=workspace_tmp_path / "figures" / "modeling" / "transfer_inference",
    )

    assert result.predictions_parquet_path.exists()
    assert result.predictions_csv_path.exists()
    assert result.summary_csv_path.exists()
    assert result.deciles_csv_path.exists()
    assert result.feature_missingness_path.exists()
    assert result.markdown_path.exists()
    assert result.metadata_path.exists()
    assert result.figure_path.exists()

    predictions_df = pd.read_parquet(result.predictions_parquet_path)
    summary_df = pd.read_csv(result.summary_csv_path)
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert len(predictions_df) == 10
    assert predictions_df["prediction_rank"].tolist() == list(range(1, 11))
    assert int(predictions_df["predicted_hotspot_10pct"].sum()) == 1
    assert "prediction_decile" in predictions_df.columns
    assert int(summary_df.loc[0, "row_count"]) == 10
    assert metadata["figure_kind"] == "centroid_map"


def test_run_transfer_inference_writes_distribution_figure_without_centroids(workspace_tmp_path: Path) -> None:
    package_dir = workspace_tmp_path / "outputs" / "modeling" / "final_train" / "transfer_package"
    input_parquet_path = workspace_tmp_path / "data_processed" / "city_features" / "test_no_centroids.parquet"
    _write_transfer_package_fixture(package_dir)
    input_parquet_path.parent.mkdir(parents=True, exist_ok=True)
    _build_input_df(include_centroids=False).to_parquet(input_parquet_path, index=False)

    result = run_transfer_inference(
        input_parquet_path=input_parquet_path,
        package_dir=package_dir,
        outputs_root=workspace_tmp_path / "outputs" / "modeling" / "transfer_inference",
        figures_root=workspace_tmp_path / "figures" / "modeling" / "transfer_inference",
        inference_id="test_no_centroids",
    )

    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    assert result.figure_path.exists()
    assert metadata["figure_kind"] == "score_distribution"
