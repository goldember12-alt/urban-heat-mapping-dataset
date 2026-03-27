import json
import warnings
from pathlib import Path

import pandas as pd
import pytest
from sklearn.model_selection import ParameterGrid

from src.modeling_baselines import run_modeling_baselines
from src.modeling_config import (
    DEFAULT_FEATURE_COLUMNS,
    DEFAULT_LOGISTIC_MAX_ITER,
    DEFAULT_LOGISTIC_TOL,
    get_model_tuning_spec,
)
from src.modeling_data import load_modeling_rows as load_modeling_rows_from_disk
from src.modeling_run_registry import build_cli_command, infer_run_registry_path, record_model_run
from src.modeling_runner import (
    build_logistic_saga_pipeline,
    build_random_forest_pipeline,
    _get_pipeline_cache_base_dir,
    run_logistic_saga_model,
    run_random_forest_model,
)
from src.run_logistic_saga import _build_arg_parser as build_logistic_arg_parser
from src.run_random_forest import _build_arg_parser as build_random_forest_arg_parser


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


def _build_mixed_type_feature_fixture() -> tuple[pd.DataFrame, pd.Series]:
    X = pd.DataFrame(
        {
            "impervious_pct": [10.0, 20.0, None, 35.0, 42.0, 55.0],
            "elevation_m": [100.0, None, 110.0, 115.0, 120.0, 125.0],
            "dist_to_water_m": [300.0, 280.0, 260.0, None, 220.0, 200.0],
            "ndvi_median_may_aug": [0.20, 0.22, 0.24, 0.26, None, 0.30],
            "land_cover_class": [21, None, 24, 24, 31, 31],
            "climate_group": ["hot_arid", None, "hot_arid", "humid_subtropical", "marine", "marine"],
        }
    )
    y = pd.Series([0, 0, 0, 1, 1, 1], dtype="int8")
    return X, y


def test_run_modeling_baselines_writes_expected_artifacts(workspace_tmp_path: Path):
    dataset_path = workspace_tmp_path / "final_dataset.parquet"
    folds_path = workspace_tmp_path / "city_outer_folds.parquet"
    output_dir = workspace_tmp_path / "outputs" / "modeling" / "baselines"
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


def test_logistic_preprocessor_routes_contract_categoricals_away_from_numeric_branch():
    pipeline = build_logistic_saga_pipeline(DEFAULT_FEATURE_COLUMNS)
    preprocessor = pipeline.named_steps["preprocess"]
    transformer_columns = {name: columns for name, _, columns in preprocessor.transformers}

    assert "climate_group" in transformer_columns["categorical"]
    assert "climate_group" not in transformer_columns["numeric"]
    assert "land_cover_class" in transformer_columns["categorical"]
    assert "land_cover_class" not in transformer_columns["numeric"]


def test_logistic_pipeline_defaults_to_configured_max_iter():
    pipeline = build_logistic_saga_pipeline(DEFAULT_FEATURE_COLUMNS)

    assert pipeline.named_steps["model"].max_iter == DEFAULT_LOGISTIC_MAX_ITER
    assert pipeline.named_steps["model"].tol == DEFAULT_LOGISTIC_TOL


@pytest.mark.parametrize(
    ("builder", "builder_kwargs"),
    [
        (build_logistic_saga_pipeline, {"max_iter": 200}),
        (build_random_forest_pipeline, {"n_jobs": 1}),
    ],
)
def test_tuned_pipelines_fit_with_mixed_type_categorical_missing_values(builder, builder_kwargs):
    X, y = _build_mixed_type_feature_fixture()
    pipeline = builder(DEFAULT_FEATURE_COLUMNS, **builder_kwargs)

    pipeline.fit(X, y)
    probabilities = pipeline.predict_proba(X)

    assert probabilities.shape == (len(X), 2)


def test_run_logistic_and_random_forest_write_expected_artifacts(workspace_tmp_path: Path):
    dataset_path = workspace_tmp_path / "final_dataset.parquet"
    folds_path = workspace_tmp_path / "city_outer_folds.parquet"
    _build_modeling_fixture().to_parquet(dataset_path, index=False)
    _build_fold_fixture().to_parquet(folds_path, index=False)

    logistic_output_dir = workspace_tmp_path / "outputs" / "modeling" / "logistic_saga"
    random_forest_output_dir = workspace_tmp_path / "outputs" / "modeling" / "random_forest"

    logistic_result = run_logistic_saga_model(
        dataset_path=dataset_path,
        folds_path=folds_path,
        output_dir=logistic_output_dir,
        feature_columns=DEFAULT_FEATURE_COLUMNS,
        param_grid=[{"model__C": [0.1, 1.0], "model__l1_ratio": [0.0]}],
        grid_search_n_jobs=1,
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
        grid_search_n_jobs=1,
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


def test_record_model_run_appends_registry_entries(workspace_tmp_path: Path):
    dataset_path = workspace_tmp_path / "final_dataset.parquet"
    folds_path = workspace_tmp_path / "city_outer_folds.parquet"
    logistic_output_dir = workspace_tmp_path / "outputs" / "modeling" / "logistic_saga"
    random_forest_output_dir = workspace_tmp_path / "outputs" / "modeling" / "random_forest"
    _build_modeling_fixture().to_parquet(dataset_path, index=False)
    _build_fold_fixture().to_parquet(folds_path, index=False)

    logistic_result = run_logistic_saga_model(
        dataset_path=dataset_path,
        folds_path=folds_path,
        output_dir=logistic_output_dir,
        feature_columns=DEFAULT_FEATURE_COLUMNS,
        param_grid=[{"model__C": [0.1], "model__l1_ratio": [0.0]}],
        grid_search_n_jobs=1,
    )
    random_forest_result = run_random_forest_model(
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
        grid_search_n_jobs=1,
    )

    record_model_run(
        model_type="logistic_saga",
        preset="smoke",
        command="python -m src.run_logistic_saga",
        output_dir=logistic_output_dir,
        dataset_path=dataset_path,
        folds_path=folds_path,
        sample_rows_per_city=None,
        selected_outer_folds=None,
        grid_search_n_jobs=1,
        summary_metrics_path=logistic_result.summary_metrics_path,
        metadata_path=logistic_result.metadata_path,
        status="success",
    )
    record_model_run(
        model_type="random_forest",
        preset="smoke",
        command="python -m src.run_random_forest",
        output_dir=random_forest_output_dir,
        dataset_path=dataset_path,
        folds_path=folds_path,
        sample_rows_per_city=None,
        selected_outer_folds=None,
        grid_search_n_jobs=1,
        summary_metrics_path=random_forest_result.summary_metrics_path,
        metadata_path=random_forest_result.metadata_path,
        status="success",
    )

    registry_path = infer_run_registry_path(logistic_output_dir)
    records = [json.loads(line) for line in registry_path.read_text(encoding="utf-8").splitlines()]

    assert [record["model_type"] for record in records] == ["logistic_saga", "random_forest"]
    assert all(record["status"] == "success" for record in records)
    assert all(record["dataset_format"] == "parquet" for record in records)
    assert all("pooled_pr_auc" in record["metrics"] for record in records)


def test_build_cli_command_prefers_module_style_argv():
    command = build_cli_command(
        [
            r"C:\\repo\\.venv\\Scripts\\python.exe",
            "-m",
            "src.run_logistic_saga",
            "--outer-folds",
            "0",
        ]
    )

    assert "-m src.run_logistic_saga" in command
    assert "--outer-folds 0" in command


def test_tuning_specs_make_smoke_mode_smaller_than_full_mode():
    logistic_smoke = get_model_tuning_spec("logistic_saga", "smoke")
    logistic_full = get_model_tuning_spec("logistic_saga", "full")
    forest_smoke = get_model_tuning_spec("random_forest", "smoke")
    forest_full = get_model_tuning_spec("random_forest", "full")

    assert len(list(ParameterGrid(logistic_smoke.param_grid))) < len(list(ParameterGrid(logistic_full.param_grid)))
    assert len(list(ParameterGrid(forest_smoke.param_grid))) < len(list(ParameterGrid(forest_full.param_grid)))
    assert logistic_smoke.inner_cv_splits < logistic_full.inner_cv_splits
    assert forest_smoke.inner_cv_splits < forest_full.inner_cv_splits
    assert all("model__penalty" not in candidate for candidate in logistic_smoke.param_grid)
    assert all("model__penalty" not in candidate for candidate in logistic_full.param_grid)


def test_tuned_runner_metadata_records_runtime_and_smoke_preset_defaults(workspace_tmp_path: Path):
    dataset_path = workspace_tmp_path / "final_dataset.parquet"
    folds_path = workspace_tmp_path / "city_outer_folds.parquet"
    output_dir = workspace_tmp_path / "outputs" / "modeling" / "logistic_saga"
    _build_modeling_fixture().to_parquet(dataset_path, index=False)
    _build_fold_fixture().to_parquet(folds_path, index=False)

    result = run_logistic_saga_model(
        dataset_path=dataset_path,
        folds_path=folds_path,
        output_dir=output_dir,
        feature_columns=DEFAULT_FEATURE_COLUMNS,
        selected_outer_folds=[0],
        grid_search_n_jobs=1,
    )

    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    expected_candidates = len(list(ParameterGrid(get_model_tuning_spec("logistic_saga", "smoke").param_grid)))

    assert metadata["tuning_preset"] == "smoke"
    assert metadata["inner_cv_splits_requested"] == get_model_tuning_spec("logistic_saga", "smoke").inner_cv_splits
    assert metadata["pipeline_cache_enabled"] is True
    assert metadata["pipeline_cache_root"] == str(_get_pipeline_cache_base_dir())
    assert metadata["pipeline_builder_kwargs"] == {
        "max_iter": DEFAULT_LOGISTIC_MAX_ITER,
        "tol": DEFAULT_LOGISTIC_TOL,
    }
    assert metadata["data_loading_strategy"] == "per_outer_fold_load"
    assert metadata["search_space"]["param_candidate_count"] == expected_candidates
    assert metadata["search_space"]["estimated_total_inner_fits"] == expected_candidates * 2
    assert len(metadata["fold_runtime"]) == 1
    assert metadata["fold_runtime"][0]["inner_cv_splits"] == 2
    assert metadata["fold_runtime"][0]["preprocess_output_feature_count"] >= len(DEFAULT_FEATURE_COLUMNS)
    assert metadata["fold_runtime"][0]["grid_search_seconds"] >= 0.0


def test_sampled_tuned_runs_preload_city_rows_once(monkeypatch: pytest.MonkeyPatch, workspace_tmp_path: Path):
    dataset_path = workspace_tmp_path / "final_dataset.parquet"
    folds_path = workspace_tmp_path / "city_outer_folds.parquet"
    output_dir = workspace_tmp_path / "outputs" / "modeling" / "logistic_saga"
    _build_modeling_fixture().to_parquet(dataset_path, index=False)
    _build_fold_fixture().to_parquet(folds_path, index=False)

    load_calls: list[list[int]] = []

    def counting_load_modeling_rows(*args, **kwargs):
        load_calls.append(list(kwargs["city_ids"]))
        return load_modeling_rows_from_disk(*args, **kwargs)

    def fail_load_outer_fold_data(*args, **kwargs):
        raise AssertionError("sampled runs should reuse a preloaded city sample instead of loading each fold separately")

    monkeypatch.setattr("src.modeling_runner.load_modeling_rows", counting_load_modeling_rows)
    monkeypatch.setattr("src.modeling_runner.load_outer_fold_data", fail_load_outer_fold_data)

    result = run_logistic_saga_model(
        dataset_path=dataset_path,
        folds_path=folds_path,
        output_dir=output_dir,
        feature_columns=DEFAULT_FEATURE_COLUMNS,
        selected_outer_folds=[0],
        sample_rows_per_city=5,
        param_grid=[{"model__C": [0.1], "model__l1_ratio": [0.0]}],
        grid_search_n_jobs=1,
    )

    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert len(load_calls) == 1
    assert sorted(load_calls[0]) == [1, 2, 3, 4]
    assert metadata["data_loading_strategy"] == "sampled_city_preload"
    assert metadata["timing_seconds"]["sampled_city_preload"] is not None


def test_logistic_l1_ratio_tuning_avoids_penalty_future_warning():
    X, y = _build_mixed_type_feature_fixture()
    pipeline = build_logistic_saga_pipeline(DEFAULT_FEATURE_COLUMNS, max_iter=200)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        pipeline.set_params(model__C=1.0, model__l1_ratio=0.0)
        pipeline.fit(X, y)

    messages = [str(item.message) for item in caught]
    assert not any("'penalty' was deprecated" in message for message in messages)


def test_tuned_runner_clis_default_to_explicit_smoke_preset():
    logistic_args = build_logistic_arg_parser().parse_args([])
    forest_args = build_random_forest_arg_parser().parse_args([])

    assert logistic_args.tuning_preset == "smoke"
    assert logistic_args.max_iter == DEFAULT_LOGISTIC_MAX_ITER
    assert logistic_args.tol == DEFAULT_LOGISTIC_TOL
    assert forest_args.tuning_preset == "smoke"
    assert logistic_args.inner_cv_splits is None
    assert forest_args.inner_cv_splits is None


def test_tuned_runner_cli_help_reflects_parquet_first_defaults_and_csv_fallback():
    logistic_help = build_logistic_arg_parser().format_help()
    forest_help = build_random_forest_arg_parser().format_help()

    for help_text in (logistic_help, forest_help):
        assert "final_dataset.parquet" in help_text
        assert "compatibility fallback only" in help_text
        assert "prefers city_outer_folds.parquet" in help_text
        assert "bounded default verification" in help_text
        assert "broader tuning search" in help_text
