from __future__ import annotations

import json
import logging
import shutil
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Callable, Sequence

import numpy as np
import pandas as pd
from joblib import Memory
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, GroupKFold, ParameterGrid
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, OrdinalEncoder, StandardScaler

from src.modeling_config import (
    CITY_NAME_COLUMN,
    DEFAULT_CALIBRATION_BINS,
    DEFAULT_FINAL_DATASET_PATH,
    DEFAULT_PR_SCORING,
    DEFAULT_RANDOM_STATE,
    DEFAULT_TUNING_PRESET,
    DEFAULT_TOP_FRACTION,
    GROUP_COLUMN,
    LOGISTIC_OUTPUT_DIR,
    RANDOM_FOREST_OUTPUT_DIR,
    TARGET_COLUMN,
    get_first_pass_feature_columns,
    get_model_tuning_spec,
    get_prediction_output_columns,
    split_model_feature_columns,
)
from src.modeling_data import (
    OuterFoldData,
    drop_missing_target_rows,
    get_requested_outer_folds,
    load_city_outer_folds,
    load_modeling_rows,
    load_outer_fold_data,
    validate_model_feature_columns,
    write_feature_contract,
)
from src.modeling_metrics import (
    build_calibration_curve_table,
    build_metrics_summary,
    compute_prediction_metrics,
    summarize_predictions_by_group,
)
from src.modeling_prep import get_final_dataset_columns, validate_required_final_columns

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class GridSearchRunResult:
    fold_metrics_path: Path
    city_metrics_path: Path
    summary_metrics_path: Path
    best_params_path: Path
    predictions_path: Path
    calibration_curve_path: Path
    metadata_path: Path


@contextmanager
def _managed_cache_directory(base_dir: Path, prefix: str):
    cache_dir = base_dir / f"{prefix}{uuid.uuid4().hex}"
    cache_dir.mkdir(parents=True, exist_ok=False)
    try:
        yield cache_dir
    finally:
        shutil.rmtree(cache_dir, ignore_errors=True)


def _split_feature_types(feature_columns: Sequence[str]) -> tuple[list[str], list[str]]:
    return split_model_feature_columns(feature_columns)


def _coerce_numeric_frame(X: pd.DataFrame) -> pd.DataFrame:
    numeric_df = pd.DataFrame(X).copy()
    for column_name in numeric_df.columns:
        numeric_df[column_name] = pd.to_numeric(numeric_df[column_name], errors="coerce")
    return numeric_df


def _coerce_categorical_frame(X: pd.DataFrame) -> pd.DataFrame:
    categorical_df = pd.DataFrame(X).copy()
    for column_name in categorical_df.columns:
        values = categorical_df[column_name].astype("string").str.strip()
        missing_mask = values.isna() | values.eq("")
        categorical_df[column_name] = values.astype(object)
        categorical_df.loc[missing_mask, column_name] = np.nan
    return categorical_df


def _count_parameter_combinations(param_grid: Sequence[dict[str, object]]) -> int:
    return len(list(ParameterGrid(list(param_grid))))


def _resolve_tuning_configuration(
    model_name: str,
    param_grid: Sequence[dict[str, object]] | None,
    inner_cv_splits: int | None,
    tuning_preset: str,
) -> tuple[str, list[dict[str, object]], int]:
    tuning_spec = get_model_tuning_spec(model_name=model_name, preset_name=tuning_preset)
    resolved_param_grid = list(tuning_spec.param_grid) if param_grid is None else list(param_grid)
    resolved_inner_cv_splits = tuning_spec.inner_cv_splits if inner_cv_splits is None else int(inner_cv_splits)
    return tuning_spec.preset_name, resolved_param_grid, resolved_inner_cv_splits


def _build_outer_fold_data_from_preloaded_rows(
    outer_fold: int,
    fold_table: pd.DataFrame,
    modeling_rows: pd.DataFrame,
) -> OuterFoldData:
    validation_rows = fold_table.loc[fold_table["outer_fold"] == int(outer_fold)].copy()
    training_rows = fold_table.loc[fold_table["outer_fold"] != int(outer_fold)].copy()

    train_city_ids = training_rows[GROUP_COLUMN].astype(int).tolist()
    test_city_ids = validation_rows[GROUP_COLUMN].astype(int).tolist()
    if set(train_city_ids) & set(test_city_ids):
        raise ValueError(f"Leakage detected in outer_fold={outer_fold}: train/test cities overlap")

    test_mask = modeling_rows[GROUP_COLUMN].isin(test_city_ids)
    test_df = modeling_rows.loc[test_mask].copy().reset_index(drop=True)
    train_df = modeling_rows.loc[~test_mask].copy().reset_index(drop=True)

    return OuterFoldData(
        outer_fold=int(outer_fold),
        train_df=train_df,
        test_df=test_df,
        train_city_ids=train_city_ids,
        test_city_ids=test_city_ids,
    )


def _summarize_feature_matrix(feature_matrix: object) -> dict[str, float | int | None]:
    row_count, feature_count = feature_matrix.shape
    density: float | None = None
    if row_count and feature_count:
        if hasattr(feature_matrix, "nnz"):
            density = float(feature_matrix.nnz) / float(row_count * feature_count)
        else:
            density = 1.0
    return {
        "row_count": int(row_count),
        "feature_count": int(feature_count),
        "density": density,
    }


def build_logistic_saga_pipeline(
    feature_columns: Sequence[str],
    random_state: int = DEFAULT_RANDOM_STATE,
    n_jobs: int | None = None,
    max_iter: int = 2000,
    memory: Memory | str | Path | None = None,
) -> Pipeline:
    """Build the first-pass logistic SAGA pipeline with train-only preprocessing."""
    del n_jobs
    numeric_columns, categorical_columns = _split_feature_types(feature_columns)
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline(
                    steps=[
                        ("cast", FunctionTransformer(_coerce_numeric_frame, validate=False)),
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_columns,
            ),
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("cast", FunctionTransformer(_coerce_categorical_frame, validate=False)),
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_columns,
            ),
        ],
        remainder="drop",
    )
    return Pipeline(
        steps=[
            ("preprocess", preprocessor),
            (
                "model",
                LogisticRegression(
                    solver="saga",
                    max_iter=max_iter,
                    random_state=random_state,
                ),
            ),
        ],
        memory=memory,
    )


def build_random_forest_pipeline(
    feature_columns: Sequence[str],
    random_state: int = DEFAULT_RANDOM_STATE,
    n_jobs: int | None = None,
    memory: Memory | str | Path | None = None,
) -> Pipeline:
    """Build the first-pass random-forest pipeline with train-only preprocessing."""
    numeric_columns, categorical_columns = _split_feature_types(feature_columns)
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline(
                    steps=[
                        ("cast", FunctionTransformer(_coerce_numeric_frame, validate=False)),
                        ("imputer", SimpleImputer(strategy="median")),
                    ]
                ),
                numeric_columns,
            ),
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("cast", FunctionTransformer(_coerce_categorical_frame, validate=False)),
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "encoder",
                            OrdinalEncoder(
                                handle_unknown="use_encoded_value",
                                unknown_value=-1,
                            ),
                        ),
                    ]
                ),
                categorical_columns,
            ),
        ],
        remainder="drop",
    )
    return Pipeline(
        steps=[
            ("preprocess", preprocessor),
            (
                "model",
                RandomForestClassifier(
                    random_state=random_state,
                    n_jobs=n_jobs,
                ),
            ),
        ],
        memory=memory,
    )


def _build_prediction_frame(
    test_df: pd.DataFrame,
    model_name: str,
    outer_fold: int,
    probabilities: Sequence[float],
) -> pd.DataFrame:
    prediction_columns = get_prediction_output_columns()
    predictions = test_df[prediction_columns + [TARGET_COLUMN]].copy()
    predictions["outer_fold"] = int(outer_fold)
    predictions["model_name"] = model_name
    predictions["predicted_probability"] = probabilities
    return predictions


def run_grouped_grid_search_model(
    model_name: str,
    pipeline_builder: Callable[..., Pipeline],
    param_grid: Sequence[dict[str, object]] | None = None,
    dataset_path: Path = DEFAULT_FINAL_DATASET_PATH,
    folds_path: Path | None = None,
    output_dir: Path | None = None,
    feature_columns: Sequence[str] | None = None,
    selected_outer_folds: Sequence[int] | None = None,
    sample_rows_per_city: int | None = None,
    random_state: int = DEFAULT_RANDOM_STATE,
    scoring: str = DEFAULT_PR_SCORING,
    inner_cv_splits: int | None = None,
    top_fraction: float = DEFAULT_TOP_FRACTION,
    calibration_bins: int = DEFAULT_CALIBRATION_BINS,
    grid_search_n_jobs: int | None = -1,
    model_n_jobs: int | None = None,
    tuning_preset: str = DEFAULT_TUNING_PRESET,
    pipeline_cache_enabled: bool = True,
) -> GridSearchRunResult:
    """Run held-out-city evaluation with inner grouped tuning for one sklearn model."""
    total_start = perf_counter()
    selected_features = get_first_pass_feature_columns() if feature_columns is None else list(feature_columns)
    tuning_preset_name, resolved_param_grid, resolved_inner_cv_splits = _resolve_tuning_configuration(
        model_name=model_name,
        param_grid=param_grid,
        inner_cv_splits=inner_cv_splits,
        tuning_preset=tuning_preset,
    )

    contract_start = perf_counter()
    available_columns = get_final_dataset_columns(dataset_path=dataset_path)
    validate_required_final_columns(available_columns)
    selected_features = validate_model_feature_columns(
        feature_columns=selected_features,
        available_columns=available_columns,
    )
    contract_enforcement_seconds = perf_counter() - contract_start

    fold_load_start = perf_counter()
    fold_table = load_city_outer_folds(folds_path=folds_path)
    requested_folds = get_requested_outer_folds(fold_table=fold_table, selected_outer_folds=selected_outer_folds)
    fold_table_load_seconds = perf_counter() - fold_load_start
    param_candidate_count = _count_parameter_combinations(resolved_param_grid)

    resolved_output_dir = output_dir or (
        LOGISTIC_OUTPUT_DIR if model_name == "logistic_saga" else RANDOM_FOREST_OUTPUT_DIR
    )
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    write_feature_contract(resolved_output_dir / "feature_contract.json", feature_columns=selected_features)

    all_city_ids = fold_table[GROUP_COLUMN].astype(int).tolist()
    preloaded_modeling_rows: pd.DataFrame | None = None
    sampled_preload_seconds: float | None = None
    data_loading_strategy = "per_outer_fold_load"
    if sample_rows_per_city is not None:
        preload_start = perf_counter()
        preloaded_modeling_rows = drop_missing_target_rows(
            load_modeling_rows(
                dataset_path=dataset_path,
                feature_columns=selected_features,
                city_ids=all_city_ids,
                sample_rows_per_city=sample_rows_per_city,
                random_state=random_state,
            )
        )
        sampled_preload_seconds = perf_counter() - preload_start
        data_loading_strategy = "sampled_city_preload"

    effective_split_counts = [
        min(
            int(resolved_inner_cv_splits),
            int(fold_table.loc[fold_table["outer_fold"] != int(outer_fold), GROUP_COLUMN].nunique()),
        )
        for outer_fold in requested_folds
    ]
    estimated_total_inner_fits = int(sum(param_candidate_count * split_count for split_count in effective_split_counts))
    LOGGER.info(
        "Tuning setup model=%s preset=%s outer_folds=%s param_candidates=%s estimated_inner_fits=%s",
        model_name,
        tuning_preset_name,
        len(requested_folds),
        param_candidate_count,
        estimated_total_inner_fits,
    )
    LOGGER.info(
        "Setup timing contract=%.2fs folds=%.2fs data_strategy=%s preload=%.2fs sample_rows_per_city=%s",
        contract_enforcement_seconds,
        fold_table_load_seconds,
        data_loading_strategy,
        0.0 if sampled_preload_seconds is None else sampled_preload_seconds,
        sample_rows_per_city,
    )

    all_predictions: list[pd.DataFrame] = []
    fold_metrics_rows: list[dict[str, object]] = []
    best_params_rows: list[dict[str, object]] = []
    calibration_frames: list[pd.DataFrame] = []
    fold_runtime_rows: list[dict[str, object]] = []

    for outer_fold in requested_folds:
        fold_start = perf_counter()
        data_load_start = perf_counter()
        if preloaded_modeling_rows is not None:
            fold_data = _build_outer_fold_data_from_preloaded_rows(
                outer_fold=outer_fold,
                fold_table=fold_table,
                modeling_rows=preloaded_modeling_rows,
            )
        else:
            fold_data = load_outer_fold_data(
                outer_fold=outer_fold,
                dataset_path=dataset_path,
                folds_path=folds_path,
                feature_columns=selected_features,
                sample_rows_per_city=sample_rows_per_city,
                random_state=random_state,
            )
        data_load_seconds = perf_counter() - data_load_start
        train_df = fold_data.train_df
        test_df = fold_data.test_df
        if train_df.empty or test_df.empty:
            raise ValueError(f"outer_fold={outer_fold} produced an empty train or test split")

        train_group_count = int(train_df[GROUP_COLUMN].nunique())
        effective_inner_splits = min(int(resolved_inner_cv_splits), train_group_count)
        if effective_inner_splits < 2:
            raise ValueError(
                f"outer_fold={outer_fold} has only {train_group_count} training cities, so GroupKFold needs at least 2"
            )

        with _managed_cache_directory(
            base_dir=resolved_output_dir,
            prefix=f"{model_name}_outer_fold_{outer_fold}_",
        ) as cache_dir:
            pipeline_cache = Memory(location=str(cache_dir), verbose=0) if pipeline_cache_enabled else None
            preprocess_build_start = perf_counter()
            pipeline = pipeline_builder(
                feature_columns=selected_features,
                random_state=random_state,
                n_jobs=model_n_jobs,
                memory=pipeline_cache,
            )
            preprocess_build_seconds = perf_counter() - preprocess_build_start

            preprocess_probe_start = perf_counter()
            probe_preprocessor = clone(pipeline.named_steps["preprocess"])
            probe_matrix = probe_preprocessor.fit_transform(
                train_df[selected_features],
                train_df[TARGET_COLUMN].to_numpy(dtype="int8"),
            )
            preprocess_probe_seconds = perf_counter() - preprocess_probe_start
            feature_matrix_summary = _summarize_feature_matrix(probe_matrix)
            del probe_matrix

            LOGGER.info(
                "outer_fold=%s rows train=%s test=%s data_load=%.2fs inner_cv=%s candidates=%s",
                outer_fold,
                len(train_df),
                len(test_df),
                data_load_seconds,
                effective_inner_splits,
                param_candidate_count,
            )
            LOGGER.info(
                "outer_fold=%s preprocess build=%.2fs probe_fit_transform=%.2fs matrix=%sx%s density=%s",
                outer_fold,
                preprocess_build_seconds,
                preprocess_probe_seconds,
                feature_matrix_summary["row_count"],
                feature_matrix_summary["feature_count"],
                (
                    "n/a"
                    if feature_matrix_summary["density"] is None
                    else f"{float(feature_matrix_summary['density']):.4f}"
                ),
            )

            grid_search = GridSearchCV(
                estimator=pipeline,
                param_grid=resolved_param_grid,
                cv=GroupKFold(n_splits=effective_inner_splits),
                scoring=scoring,
                n_jobs=grid_search_n_jobs,
                refit=True,
                error_score="raise",
            )
            grid_search_start = perf_counter()
            grid_search.fit(
                train_df[selected_features],
                train_df[TARGET_COLUMN].to_numpy(dtype="int8"),
                groups=train_df[GROUP_COLUMN].to_numpy(),
            )
            grid_search_seconds = perf_counter() - grid_search_start
        fold_wall_clock_seconds = perf_counter() - fold_start

        probabilities = grid_search.best_estimator_.predict_proba(test_df[selected_features])[:, 1]
        prediction_df = _build_prediction_frame(
            test_df=test_df,
            model_name=model_name,
            outer_fold=outer_fold,
            probabilities=probabilities,
        )
        all_predictions.append(prediction_df)

        metrics = compute_prediction_metrics(
            y_true=prediction_df[TARGET_COLUMN].to_numpy(dtype="int8"),
            y_score=prediction_df["predicted_probability"].to_numpy(dtype="float64"),
            top_fraction=top_fraction,
        )
        fold_metrics_rows.append(
            {
                "model_name": model_name,
                "outer_fold": int(outer_fold),
                "train_city_count": int(len(fold_data.train_city_ids)),
                "test_city_count": int(len(fold_data.test_city_ids)),
                "train_row_count": int(len(train_df)),
                "test_row_count": int(metrics["row_count"]),
                "test_positive_count": int(metrics["positive_count"]),
                "test_prevalence": float(metrics["prevalence"]),
                "pr_auc": float(metrics["pr_auc"]),
                "recall_at_top_10pct": float(metrics["recall_at_top_10pct"]),
                "inner_cv_splits": int(effective_inner_splits),
                "best_inner_cv_average_precision": float(grid_search.best_score_),
                "param_candidate_count": int(param_candidate_count),
                "estimated_inner_fit_count": int(param_candidate_count * effective_inner_splits),
                "data_load_seconds": float(data_load_seconds),
                "preprocess_build_seconds": float(preprocess_build_seconds),
                "preprocess_probe_fit_transform_seconds": float(preprocess_probe_seconds),
                "grid_search_seconds": float(grid_search_seconds),
                "fold_wall_clock_seconds": float(fold_wall_clock_seconds),
            }
        )
        best_params_rows.append(
            {
                "model_name": model_name,
                "outer_fold": int(outer_fold),
                "inner_cv_splits": int(effective_inner_splits),
                "best_inner_cv_average_precision": float(grid_search.best_score_),
                "best_params_json": json.dumps(grid_search.best_params_, sort_keys=True),
            }
        )
        fold_runtime_rows.append(
            {
                "outer_fold": int(outer_fold),
                "train_row_count": int(len(train_df)),
                "test_row_count": int(len(test_df)),
                "train_city_count": int(len(fold_data.train_city_ids)),
                "test_city_count": int(len(fold_data.test_city_ids)),
                "inner_cv_splits": int(effective_inner_splits),
                "param_candidate_count": int(param_candidate_count),
                "estimated_inner_fit_count": int(param_candidate_count * effective_inner_splits),
                "data_load_seconds": float(data_load_seconds),
                "preprocess_build_seconds": float(preprocess_build_seconds),
                "preprocess_probe_fit_transform_seconds": float(preprocess_probe_seconds),
                "preprocess_output_row_count": int(feature_matrix_summary["row_count"]),
                "preprocess_output_feature_count": int(feature_matrix_summary["feature_count"]),
                "preprocess_output_density": feature_matrix_summary["density"],
                "grid_search_seconds": float(grid_search_seconds),
                "fold_wall_clock_seconds": float(fold_wall_clock_seconds),
            }
        )
        calibration_frames.append(
            build_calibration_curve_table(
                predictions_df=prediction_df,
                model_name=model_name,
                scope_name="outer_fold",
                scope_value=str(outer_fold),
                n_bins=calibration_bins,
            )
        )
        LOGGER.info(
            "outer_fold=%s grid_search=%.2fs total=%.2fs best_score=%.4f",
            outer_fold,
            grid_search_seconds,
            fold_wall_clock_seconds,
            float(grid_search.best_score_),
        )

    predictions_df = pd.concat(all_predictions, ignore_index=True).sort_values(
        ["outer_fold", GROUP_COLUMN, "cell_id"]
    )
    fold_metrics_df = pd.DataFrame(fold_metrics_rows).sort_values("outer_fold").reset_index(drop=True)
    city_metrics_df = summarize_predictions_by_group(
        predictions_df=predictions_df,
        group_columns=["model_name", "outer_fold", GROUP_COLUMN, CITY_NAME_COLUMN, "climate_group"],
        top_fraction=top_fraction,
    ).sort_values(["outer_fold", GROUP_COLUMN]).reset_index(drop=True)
    summary_df = build_metrics_summary(
        predictions_df=predictions_df,
        fold_metrics_df=fold_metrics_df,
        city_metrics_df=city_metrics_df,
        model_name=model_name,
        top_fraction=top_fraction,
    )
    calibration_frames.append(
        build_calibration_curve_table(
            predictions_df=predictions_df,
            model_name=model_name,
            scope_name="overall",
            scope_value="overall",
            n_bins=calibration_bins,
        )
    )
    calibration_df = pd.concat(calibration_frames, ignore_index=True) if calibration_frames else pd.DataFrame()
    best_params_df = pd.DataFrame(best_params_rows).sort_values("outer_fold").reset_index(drop=True)
    total_wall_clock_seconds = perf_counter() - total_start

    predictions_path = resolved_output_dir / "heldout_predictions.parquet"
    fold_metrics_path = resolved_output_dir / "metrics_by_fold.csv"
    city_metrics_path = resolved_output_dir / "metrics_by_city.csv"
    summary_metrics_path = resolved_output_dir / "metrics_summary.csv"
    best_params_path = resolved_output_dir / "best_params_by_fold.csv"
    calibration_curve_path = resolved_output_dir / "calibration_curve.csv"
    metadata_path = resolved_output_dir / "run_metadata.json"

    predictions_df.to_parquet(predictions_path, index=False)
    fold_metrics_df.to_csv(fold_metrics_path, index=False)
    city_metrics_df.to_csv(city_metrics_path, index=False)
    summary_df.to_csv(summary_metrics_path, index=False)
    best_params_df.to_csv(best_params_path, index=False)
    calibration_df.to_csv(calibration_curve_path, index=False)

    metadata = {
        "model_name": model_name,
        "dataset_path": str(dataset_path),
        "folds_path": str(folds_path) if folds_path is not None else None,
        "output_dir": str(resolved_output_dir),
        "selected_feature_columns": list(selected_features),
        "tuning_preset": tuning_preset_name,
        "scoring": scoring,
        "selected_outer_folds": requested_folds,
        "sample_rows_per_city": sample_rows_per_city,
        "random_state": random_state,
        "inner_cv_splits_requested": int(resolved_inner_cv_splits),
        "grid_search_n_jobs": grid_search_n_jobs,
        "model_n_jobs": model_n_jobs,
        "pipeline_cache_enabled": pipeline_cache_enabled,
        "data_loading_strategy": data_loading_strategy,
        "search_space": {
            "param_candidate_count": int(param_candidate_count),
            "estimated_total_inner_fits": int(estimated_total_inner_fits),
            "requested_outer_fold_count": int(len(requested_folds)),
        },
        "timing_seconds": {
            "contract_enforcement": float(contract_enforcement_seconds),
            "fold_table_load": float(fold_table_load_seconds),
            "sampled_city_preload": sampled_preload_seconds,
            "total_wall_clock": float(total_wall_clock_seconds),
        },
        "fold_runtime": fold_runtime_rows,
        "param_grid": list(resolved_param_grid),
        "output_files": {
            "predictions": str(predictions_path),
            "metrics_by_fold": str(fold_metrics_path),
            "metrics_by_city": str(city_metrics_path),
            "metrics_summary": str(summary_metrics_path),
            "best_params_by_fold": str(best_params_path),
            "calibration_curve": str(calibration_curve_path),
        },
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    LOGGER.info(
        "Completed model=%s preset=%s total_wall_clock=%.2fs metadata=%s",
        model_name,
        tuning_preset_name,
        total_wall_clock_seconds,
        metadata_path,
    )

    return GridSearchRunResult(
        fold_metrics_path=fold_metrics_path,
        city_metrics_path=city_metrics_path,
        summary_metrics_path=summary_metrics_path,
        best_params_path=best_params_path,
        predictions_path=predictions_path,
        calibration_curve_path=calibration_curve_path,
        metadata_path=metadata_path,
    )


def run_logistic_saga_model(
    dataset_path: Path = DEFAULT_FINAL_DATASET_PATH,
    folds_path: Path | None = None,
    output_dir: Path = LOGISTIC_OUTPUT_DIR,
    feature_columns: Sequence[str] | None = None,
    selected_outer_folds: Sequence[int] | None = None,
    sample_rows_per_city: int | None = None,
    random_state: int = DEFAULT_RANDOM_STATE,
    inner_cv_splits: int | None = None,
    top_fraction: float = DEFAULT_TOP_FRACTION,
    calibration_bins: int = DEFAULT_CALIBRATION_BINS,
    param_grid: Sequence[dict[str, object]] | None = None,
    grid_search_n_jobs: int | None = -1,
    tuning_preset: str = DEFAULT_TUNING_PRESET,
    pipeline_cache_enabled: bool = True,
) -> GridSearchRunResult:
    """Run the grouped logistic SAGA experiment."""
    return run_grouped_grid_search_model(
        model_name="logistic_saga",
        pipeline_builder=build_logistic_saga_pipeline,
        param_grid=param_grid,
        dataset_path=dataset_path,
        folds_path=folds_path,
        output_dir=output_dir,
        feature_columns=feature_columns,
        selected_outer_folds=selected_outer_folds,
        sample_rows_per_city=sample_rows_per_city,
        random_state=random_state,
        inner_cv_splits=inner_cv_splits,
        top_fraction=top_fraction,
        calibration_bins=calibration_bins,
        grid_search_n_jobs=grid_search_n_jobs,
        tuning_preset=tuning_preset,
        pipeline_cache_enabled=pipeline_cache_enabled,
    )


def run_random_forest_model(
    dataset_path: Path = DEFAULT_FINAL_DATASET_PATH,
    folds_path: Path | None = None,
    output_dir: Path = RANDOM_FOREST_OUTPUT_DIR,
    feature_columns: Sequence[str] | None = None,
    selected_outer_folds: Sequence[int] | None = None,
    sample_rows_per_city: int | None = None,
    random_state: int = DEFAULT_RANDOM_STATE,
    inner_cv_splits: int | None = None,
    top_fraction: float = DEFAULT_TOP_FRACTION,
    calibration_bins: int = DEFAULT_CALIBRATION_BINS,
    param_grid: Sequence[dict[str, object]] | None = None,
    grid_search_n_jobs: int | None = -1,
    model_n_jobs: int | None = None,
    tuning_preset: str = DEFAULT_TUNING_PRESET,
    pipeline_cache_enabled: bool = True,
) -> GridSearchRunResult:
    """Run the grouped random-forest experiment."""
    return run_grouped_grid_search_model(
        model_name="random_forest",
        pipeline_builder=build_random_forest_pipeline,
        param_grid=param_grid,
        dataset_path=dataset_path,
        folds_path=folds_path,
        output_dir=output_dir,
        feature_columns=feature_columns,
        selected_outer_folds=selected_outer_folds,
        sample_rows_per_city=sample_rows_per_city,
        random_state=random_state,
        inner_cv_splits=inner_cv_splits,
        top_fraction=top_fraction,
        calibration_bins=calibration_bins,
        grid_search_n_jobs=grid_search_n_jobs,
        model_n_jobs=model_n_jobs,
        tuning_preset=tuning_preset,
        pipeline_cache_enabled=pipeline_cache_enabled,
    )
