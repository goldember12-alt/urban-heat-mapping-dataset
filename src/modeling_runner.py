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
from sklearn.metrics import get_scorer
from sklearn.model_selection import GridSearchCV, GroupKFold, ParameterGrid
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, OrdinalEncoder, StandardScaler

from src.modeling_config import (
    CITY_NAME_COLUMN,
    DEFAULT_CALIBRATION_BINS,
    DEFAULT_FINAL_DATASET_PATH,
    DEFAULT_LOGISTIC_MAX_ITER,
    DEFAULT_LOGISTIC_TOL,
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
    get_requested_outer_folds,
    load_city_outer_folds,
    load_sampled_modeling_rows_with_diagnostics,
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
from src.modeling_progress import (
    FOLD_ARTIFACTS_DIRNAME,
    ProgressScorer,
    ModelRunProgressTracker,
    atomic_write_json,
)
from src.modeling_prep import get_final_dataset_columns, validate_required_final_columns
from src.modeling_run_registry import create_run_id

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PIPELINE_CACHE_ROOT = Path.home() / ".tmp" / f"{PROJECT_ROOT.name}" / "modeling-cache"


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
    cache_dir = base_dir / f"{prefix}{uuid.uuid4().hex[:8]}"
    cache_dir.mkdir(parents=True, exist_ok=False)
    try:
        yield cache_dir
    finally:
        shutil.rmtree(cache_dir, ignore_errors=True)


def _split_feature_types(feature_columns: Sequence[str]) -> tuple[list[str], list[str]]:
    return split_model_feature_columns(feature_columns)


def _get_pipeline_cache_base_dir() -> Path:
    """Return a short external cache root to stay under Windows path-length limits and keep the repo clean."""
    PIPELINE_CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    return PIPELINE_CACHE_ROOT


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
    max_iter: int = DEFAULT_LOGISTIC_MAX_ITER,
    tol: float = DEFAULT_LOGISTIC_TOL,
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
                # Keep penalty at sklearn's default sentinel so GridSearchCV can
                # vary l1_ratio across l2/l1/elastic-net families without the
                # deprecated explicit-penalty parameter path.
                LogisticRegression(
                    solver="saga",
                    max_iter=max_iter,
                    tol=tol,
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


def _fold_artifact_dir(output_dir: Path, outer_fold: int) -> Path:
    return output_dir / FOLD_ARTIFACTS_DIRNAME / f"outer_fold_{int(outer_fold):02d}"


def _write_fold_artifacts(
    *,
    output_dir: Path,
    outer_fold: int,
    prediction_df: pd.DataFrame,
    fold_metrics_row: dict[str, object],
    best_params_row: dict[str, object],
    calibration_df: pd.DataFrame,
    fold_runtime_row: dict[str, object],
) -> dict[str, Path]:
    artifact_dir = _fold_artifact_dir(output_dir=output_dir, outer_fold=outer_fold)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    predictions_path = artifact_dir / "heldout_predictions.parquet"
    fold_metrics_path = artifact_dir / "fold_metrics.json"
    best_params_path = artifact_dir / "best_params.json"
    calibration_curve_path = artifact_dir / "calibration_curve.csv"
    runtime_path = artifact_dir / "runtime.json"

    prediction_df.to_parquet(predictions_path, index=False)
    atomic_write_json(fold_metrics_path, fold_metrics_row)
    atomic_write_json(best_params_path, best_params_row)
    calibration_df.to_csv(calibration_curve_path, index=False)
    atomic_write_json(runtime_path, fold_runtime_row)

    return {
        "predictions": predictions_path,
        "fold_metrics": fold_metrics_path,
        "best_params": best_params_path,
        "calibration_curve": calibration_curve_path,
        "runtime": runtime_path,
    }


def _load_completed_fold_artifacts(
    *,
    output_dir: Path,
    outer_fold: int,
) -> tuple[pd.DataFrame, dict[str, object], dict[str, object], pd.DataFrame, dict[str, object]]:
    artifact_dir = _fold_artifact_dir(output_dir=output_dir, outer_fold=outer_fold)
    predictions_df = pd.read_parquet(artifact_dir / "heldout_predictions.parquet")
    fold_metrics_row = json.loads((artifact_dir / "fold_metrics.json").read_text(encoding="utf-8"))
    best_params_row = json.loads((artifact_dir / "best_params.json").read_text(encoding="utf-8"))
    calibration_df = pd.read_csv(artifact_dir / "calibration_curve.csv")
    fold_runtime_row = json.loads((artifact_dir / "runtime.json").read_text(encoding="utf-8"))
    return predictions_df, fold_metrics_row, best_params_row, calibration_df, fold_runtime_row


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
    pipeline_builder_kwargs: dict[str, object] | None = None,
    command: str | None = None,
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
    param_names = sorted({param_name for candidate in resolved_param_grid for param_name in candidate})

    resolved_output_dir = output_dir or (
        LOGISTIC_OUTPUT_DIR if model_name == "logistic_saga" else RANDOM_FOREST_OUTPUT_DIR
    )
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    write_feature_contract(resolved_output_dir / "feature_contract.json", feature_columns=selected_features)

    all_city_ids = fold_table[GROUP_COLUMN].astype(int).tolist()
    preloaded_modeling_rows: pd.DataFrame | None = None
    sampled_preload_seconds: float | None = None
    data_loading_strategy = "per_outer_fold_load"
    resolved_pipeline_builder_kwargs = dict(pipeline_builder_kwargs or {})

    effective_split_counts = [
        min(
            int(resolved_inner_cv_splits),
            int(fold_table.loc[fold_table["outer_fold"] != int(outer_fold), GROUP_COLUMN].nunique()),
        )
        for outer_fold in requested_folds
    ]
    estimated_total_inner_fits = int(sum(param_candidate_count * split_count for split_count in effective_split_counts))
    run_id = create_run_id()
    progress_tracker = ModelRunProgressTracker(
        output_dir=resolved_output_dir,
        run_id=run_id,
        model_family=model_name,
        tuning_preset=tuning_preset_name,
        selected_outer_folds=requested_folds,
        candidate_count=param_candidate_count,
        inner_cv_splits_requested=resolved_inner_cv_splits,
        estimated_total_inner_fits=estimated_total_inner_fits,
        dataset_path=dataset_path,
        folds_path=folds_path,
        feature_columns=selected_features,
        sample_rows_per_city=sample_rows_per_city,
        random_state=random_state,
    )
    completed_resume_folds = progress_tracker.initialize()
    skipped_completed_folds = sorted(fold for fold in requested_folds if fold in completed_resume_folds)
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

    if skipped_completed_folds:
        LOGGER.info(
            "Skipping already completed outer folds=%s from existing artifacts under %s",
            skipped_completed_folds,
            resolved_output_dir,
        )
        for outer_fold in skipped_completed_folds:
            (
                completed_predictions,
                completed_fold_metrics,
                completed_best_params,
                completed_calibration,
                completed_runtime,
            ) = _load_completed_fold_artifacts(output_dir=resolved_output_dir, outer_fold=outer_fold)
            all_predictions.append(completed_predictions)
            fold_metrics_rows.append(completed_fold_metrics)
            best_params_rows.append(completed_best_params)
            calibration_frames.append(completed_calibration)
            fold_runtime_rows.append(completed_runtime)

    current_phase = "startup"
    current_outer_fold: int | None = None
    try:
        if sample_rows_per_city is not None:
            current_phase = "data_load"
            progress_tracker.mark_phase(phase="data_load", note="sampled_city_preload_started")
            preload_start = perf_counter()
            preloaded_modeling_rows, sampling_diagnostics_df = load_sampled_modeling_rows_with_diagnostics(
                dataset_path=dataset_path,
                feature_columns=selected_features,
                city_ids=all_city_ids,
                sample_rows_per_city=sample_rows_per_city,
                random_state=random_state,
            )
            sampled_preload_seconds = perf_counter() - preload_start
            data_loading_strategy = "sampled_city_preload"
            progress_tracker.write_sample_diagnostics(sampling_diagnostics_df)
            LOGGER.info(
                "Sampled tuning rows loaded in %.2fs with diagnostics at %s",
                sampled_preload_seconds,
                progress_tracker.sampled_diagnostics_path,
            )

        for outer_fold in requested_folds:
            if outer_fold in skipped_completed_folds:
                continue

            current_outer_fold = int(outer_fold)
            fold_start = perf_counter()
            current_phase = "data_load"
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
            estimated_inner_fit_count = int(param_candidate_count * effective_inner_splits)
            progress_tracker.mark_fold_started(
                outer_fold=outer_fold,
                effective_inner_cv_splits=effective_inner_splits,
                estimated_inner_fit_count=estimated_inner_fit_count,
                train_row_count=len(train_df),
                test_row_count=len(test_df),
                train_city_count=len(fold_data.train_city_ids),
                test_city_count=len(fold_data.test_city_ids),
            )
            LOGGER.info(
                "outer_fold=%s start train_rows=%s test_rows=%s inner_cv=%s candidates=%s progress=%s",
                outer_fold,
                len(train_df),
                len(test_df),
                effective_inner_splits,
                param_candidate_count,
                progress_tracker.progress_path,
            )

            with _managed_cache_directory(
                base_dir=_get_pipeline_cache_base_dir(),
                prefix=f"f{outer_fold}_",
            ) as cache_dir:
                pipeline_cache = Memory(location=str(cache_dir), verbose=0) if pipeline_cache_enabled else None
                preprocess_build_start = perf_counter()
                pipeline = pipeline_builder(
                    feature_columns=selected_features,
                    random_state=random_state,
                    n_jobs=model_n_jobs,
                    memory=pipeline_cache,
                    **resolved_pipeline_builder_kwargs,
                )
                preprocess_build_seconds = perf_counter() - preprocess_build_start

                current_phase = "preprocess"
                preprocess_probe_start = perf_counter()
                probe_preprocessor = clone(pipeline.named_steps["preprocess"])
                probe_matrix = probe_preprocessor.fit_transform(
                    train_df[selected_features],
                    train_df[TARGET_COLUMN].to_numpy(dtype="int8"),
                )
                preprocess_probe_seconds = perf_counter() - preprocess_probe_start
                feature_matrix_summary = _summarize_feature_matrix(probe_matrix)
                del probe_matrix
                progress_tracker.mark_phase(
                    phase="preprocess",
                    outer_fold=outer_fold,
                    effective_inner_cv_splits=effective_inner_splits,
                    note="preprocess_complete",
                )

                LOGGER.info(
                    "outer_fold=%s preprocess complete build=%.2fs probe_fit_transform=%.2fs matrix=%sx%s density=%s",
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

                current_phase = "tuning"
                progress_tracker.mark_phase(
                    phase="tuning",
                    outer_fold=outer_fold,
                    effective_inner_cv_splits=effective_inner_splits,
                    note="grid_search_started",
                )
                LOGGER.info(
                    "outer_fold=%s tuning started estimated_inner_fits=%s grid_search_n_jobs=%s",
                    outer_fold,
                    estimated_inner_fit_count,
                    grid_search_n_jobs,
                )
                grid_search = GridSearchCV(
                    estimator=pipeline,
                    param_grid=resolved_param_grid,
                    cv=GroupKFold(n_splits=effective_inner_splits),
                    scoring=ProgressScorer(
                        base_scorer=get_scorer(scoring),
                        tracker=progress_tracker,
                        outer_fold=outer_fold,
                        effective_inner_cv_splits=effective_inner_splits,
                        param_names=param_names,
                    ),
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

            current_phase = "refit"
            progress_tracker.mark_phase(
                phase="refit",
                outer_fold=outer_fold,
                effective_inner_cv_splits=effective_inner_splits,
                current_params=grid_search.best_params_,
                note="grid_search_fit_complete",
            )

            current_phase = "prediction"
            progress_tracker.mark_phase(
                phase="prediction",
                outer_fold=outer_fold,
                effective_inner_cv_splits=effective_inner_splits,
                current_params=grid_search.best_params_,
                note="heldout_prediction_started",
            )
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
            fold_metrics_row = {
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
                "estimated_inner_fit_count": int(estimated_inner_fit_count),
                "data_load_seconds": float(data_load_seconds),
                "preprocess_build_seconds": float(preprocess_build_seconds),
                "preprocess_probe_fit_transform_seconds": float(preprocess_probe_seconds),
                "grid_search_seconds": float(grid_search_seconds),
                "fold_wall_clock_seconds": float(fold_wall_clock_seconds),
            }
            fold_metrics_rows.append(fold_metrics_row)
            best_params_row = {
                "model_name": model_name,
                "outer_fold": int(outer_fold),
                "inner_cv_splits": int(effective_inner_splits),
                "best_inner_cv_average_precision": float(grid_search.best_score_),
                "best_params_json": json.dumps(grid_search.best_params_, sort_keys=True),
            }
            best_params_rows.append(best_params_row)
            fold_runtime_row = {
                "outer_fold": int(outer_fold),
                "train_row_count": int(len(train_df)),
                "test_row_count": int(len(test_df)),
                "train_city_count": int(len(fold_data.train_city_ids)),
                "test_city_count": int(len(fold_data.test_city_ids)),
                "inner_cv_splits": int(effective_inner_splits),
                "param_candidate_count": int(param_candidate_count),
                "estimated_inner_fit_count": int(estimated_inner_fit_count),
                "data_load_seconds": float(data_load_seconds),
                "preprocess_build_seconds": float(preprocess_build_seconds),
                "preprocess_probe_fit_transform_seconds": float(preprocess_probe_seconds),
                "preprocess_output_row_count": int(feature_matrix_summary["row_count"]),
                "preprocess_output_feature_count": int(feature_matrix_summary["feature_count"]),
                "preprocess_output_density": feature_matrix_summary["density"],
                "grid_search_seconds": float(grid_search_seconds),
                "fold_wall_clock_seconds": float(fold_wall_clock_seconds),
            }
            fold_runtime_rows.append(fold_runtime_row)
            fold_calibration_df = build_calibration_curve_table(
                predictions_df=prediction_df,
                model_name=model_name,
                scope_name="outer_fold",
                scope_value=str(outer_fold),
                n_bins=calibration_bins,
            )
            calibration_frames.append(fold_calibration_df)
            fold_artifact_paths = _write_fold_artifacts(
                output_dir=resolved_output_dir,
                outer_fold=outer_fold,
                prediction_df=prediction_df,
                fold_metrics_row=fold_metrics_row,
                best_params_row=best_params_row,
                calibration_df=fold_calibration_df,
                fold_runtime_row=fold_runtime_row,
            )
            progress_tracker.mark_fold_complete(
                outer_fold=outer_fold,
                effective_inner_cv_splits=effective_inner_splits,
                artifact_paths=fold_artifact_paths,
                best_score=float(grid_search.best_score_),
                fold_wall_clock_seconds=float(fold_wall_clock_seconds),
            )
            LOGGER.info(
                "outer_fold=%s complete grid_search=%.2fs total=%.2fs best_score=%.4f",
                outer_fold,
                grid_search_seconds,
                fold_wall_clock_seconds,
                float(grid_search.best_score_),
            )
    except Exception as exc:
        progress_tracker.mark_failed(phase=current_phase, error=exc, outer_fold=current_outer_fold)
        raise

    if not all_predictions:
        raise ValueError("No completed outer-fold artifacts were available to assemble final modeling outputs")

    LOGGER.info("Writing final aggregate artifacts under %s", resolved_output_dir)
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
        "run_id": run_id,
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
        "pipeline_cache_root": str(_get_pipeline_cache_base_dir()) if pipeline_cache_enabled else None,
        "pipeline_builder_kwargs": resolved_pipeline_builder_kwargs,
        "data_loading_strategy": data_loading_strategy,
        "resume": {
            "resumed_from_existing_output_dir": bool(skipped_completed_folds),
            "skipped_completed_outer_folds": skipped_completed_folds,
            "fold_artifacts_dir": str(progress_tracker.fold_artifacts_root),
        },
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
            "progress": str(progress_tracker.progress_path),
            "progress_log": str(progress_tracker.progress_log_path),
            "fold_status": str(progress_tracker.fold_status_path),
            "sampled_diagnostics": (
                str(progress_tracker.sampled_diagnostics_path)
                if sample_rows_per_city is not None and progress_tracker.sampled_diagnostics_path.exists()
                else None
            ),
        },
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    progress_tracker.mark_complete()
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
    max_iter: int = DEFAULT_LOGISTIC_MAX_ITER,
    tol: float = DEFAULT_LOGISTIC_TOL,
    tuning_preset: str = DEFAULT_TUNING_PRESET,
    pipeline_cache_enabled: bool = True,
    command: str | None = None,
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
        pipeline_builder_kwargs={"max_iter": int(max_iter), "tol": float(tol)},
        tuning_preset=tuning_preset,
        pipeline_cache_enabled=pipeline_cache_enabled,
        command=command,
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
    command: str | None = None,
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
        command=command,
    )
