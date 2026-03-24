from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, OrdinalEncoder, StandardScaler

from src.modeling_config import (
    CITY_NAME_COLUMN,
    DEFAULT_CALIBRATION_BINS,
    DEFAULT_FINAL_DATASET_PATH,
    DEFAULT_INNER_CV_SPLITS,
    DEFAULT_PR_SCORING,
    DEFAULT_RANDOM_STATE,
    DEFAULT_TOP_FRACTION,
    GROUP_COLUMN,
    LOGISTIC_OUTPUT_DIR,
    LOGISTIC_PARAM_GRID,
    RANDOM_FOREST_OUTPUT_DIR,
    RANDOM_FOREST_PARAM_GRID,
    TARGET_COLUMN,
    get_first_pass_feature_columns,
    get_prediction_output_columns,
    split_model_feature_columns,
)
from src.modeling_data import (
    get_requested_outer_folds,
    load_city_outer_folds,
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


@dataclass(frozen=True)
class GridSearchRunResult:
    fold_metrics_path: Path
    city_metrics_path: Path
    summary_metrics_path: Path
    best_params_path: Path
    predictions_path: Path
    calibration_curve_path: Path
    metadata_path: Path


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


def build_logistic_saga_pipeline(
    feature_columns: Sequence[str],
    random_state: int = DEFAULT_RANDOM_STATE,
    n_jobs: int | None = None,
    max_iter: int = 2000,
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
        ]
    )


def build_random_forest_pipeline(
    feature_columns: Sequence[str],
    random_state: int = DEFAULT_RANDOM_STATE,
    n_jobs: int | None = None,
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
        ]
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
    param_grid: Sequence[dict[str, object]],
    dataset_path: Path = DEFAULT_FINAL_DATASET_PATH,
    folds_path: Path | None = None,
    output_dir: Path | None = None,
    feature_columns: Sequence[str] | None = None,
    selected_outer_folds: Sequence[int] | None = None,
    sample_rows_per_city: int | None = None,
    random_state: int = DEFAULT_RANDOM_STATE,
    scoring: str = DEFAULT_PR_SCORING,
    inner_cv_splits: int = DEFAULT_INNER_CV_SPLITS,
    top_fraction: float = DEFAULT_TOP_FRACTION,
    calibration_bins: int = DEFAULT_CALIBRATION_BINS,
    grid_search_n_jobs: int | None = -1,
    model_n_jobs: int | None = None,
) -> GridSearchRunResult:
    """Run held-out-city evaluation with inner grouped tuning for one sklearn model."""
    selected_features = get_first_pass_feature_columns() if feature_columns is None else list(feature_columns)
    available_columns = get_final_dataset_columns(dataset_path=dataset_path)
    validate_required_final_columns(available_columns)
    selected_features = validate_model_feature_columns(
        feature_columns=selected_features,
        available_columns=available_columns,
    )
    fold_table = load_city_outer_folds(folds_path=folds_path)
    requested_folds = get_requested_outer_folds(fold_table=fold_table, selected_outer_folds=selected_outer_folds)

    resolved_output_dir = output_dir or (
        LOGISTIC_OUTPUT_DIR if model_name == "logistic_saga" else RANDOM_FOREST_OUTPUT_DIR
    )
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    write_feature_contract(resolved_output_dir / "feature_contract.json", feature_columns=selected_features)

    all_predictions: list[pd.DataFrame] = []
    fold_metrics_rows: list[dict[str, object]] = []
    best_params_rows: list[dict[str, object]] = []
    calibration_frames: list[pd.DataFrame] = []

    for outer_fold in requested_folds:
        fold_data = load_outer_fold_data(
            outer_fold=outer_fold,
            dataset_path=dataset_path,
            folds_path=folds_path,
            feature_columns=selected_features,
            sample_rows_per_city=sample_rows_per_city,
            random_state=random_state,
        )
        train_df = fold_data.train_df
        test_df = fold_data.test_df
        if train_df.empty or test_df.empty:
            raise ValueError(f"outer_fold={outer_fold} produced an empty train or test split")

        train_group_count = int(train_df[GROUP_COLUMN].nunique())
        effective_inner_splits = min(int(inner_cv_splits), train_group_count)
        if effective_inner_splits < 2:
            raise ValueError(
                f"outer_fold={outer_fold} has only {train_group_count} training cities, so GroupKFold needs at least 2"
            )

        pipeline = pipeline_builder(
            feature_columns=selected_features,
            random_state=random_state,
            n_jobs=model_n_jobs,
        )
        grid_search = GridSearchCV(
            estimator=pipeline,
            param_grid=list(param_grid),
            cv=GroupKFold(n_splits=effective_inner_splits),
            scoring=scoring,
            n_jobs=grid_search_n_jobs,
            refit=True,
            error_score="raise",
        )
        grid_search.fit(
            train_df[selected_features],
            train_df[TARGET_COLUMN].to_numpy(dtype="int8"),
            groups=train_df[GROUP_COLUMN].to_numpy(),
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
        calibration_frames.append(
            build_calibration_curve_table(
                predictions_df=prediction_df,
                model_name=model_name,
                scope_name="outer_fold",
                scope_value=str(outer_fold),
                n_bins=calibration_bins,
            )
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
        "scoring": scoring,
        "selected_outer_folds": requested_folds,
        "sample_rows_per_city": sample_rows_per_city,
        "random_state": random_state,
        "inner_cv_splits_requested": int(inner_cv_splits),
        "grid_search_n_jobs": grid_search_n_jobs,
        "model_n_jobs": model_n_jobs,
        "param_grid": list(param_grid),
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
    inner_cv_splits: int = DEFAULT_INNER_CV_SPLITS,
    top_fraction: float = DEFAULT_TOP_FRACTION,
    calibration_bins: int = DEFAULT_CALIBRATION_BINS,
    param_grid: Sequence[dict[str, object]] = LOGISTIC_PARAM_GRID,
    grid_search_n_jobs: int | None = -1,
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
    )


def run_random_forest_model(
    dataset_path: Path = DEFAULT_FINAL_DATASET_PATH,
    folds_path: Path | None = None,
    output_dir: Path = RANDOM_FOREST_OUTPUT_DIR,
    feature_columns: Sequence[str] | None = None,
    selected_outer_folds: Sequence[int] | None = None,
    sample_rows_per_city: int | None = None,
    random_state: int = DEFAULT_RANDOM_STATE,
    inner_cv_splits: int = DEFAULT_INNER_CV_SPLITS,
    top_fraction: float = DEFAULT_TOP_FRACTION,
    calibration_bins: int = DEFAULT_CALIBRATION_BINS,
    param_grid: Sequence[dict[str, object]] = RANDOM_FOREST_PARAM_GRID,
    grid_search_n_jobs: int | None = -1,
    model_n_jobs: int | None = None,
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
    )
