from __future__ import annotations

import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq

from src.config import FINAL, MODELING
from src.modeling_prep import (
    DEFAULT_EXCLUDED_COLUMNS,
    DEFAULT_FEATURE_COLUMNS,
    DEFAULT_GROUP_COLUMN,
    DEFAULT_TARGET_COLUMN,
    get_final_dataset_columns,
    validate_binary_target,
    validate_required_final_columns,
)

logger = logging.getLogger(__name__)

DEFAULT_BASELINE_OUTPUT_DIR = MODELING / "baselines"
DEFAULT_BATCH_SIZE = 250_000
DEFAULT_MAX_LOGISTIC_ITERATIONS = 6
DEFAULT_LOGISTIC_L2 = 1.0
DEFAULT_TREE_SAMPLE_PER_CITY = 5_000
DEFAULT_DECISION_STUMP_MIN_LEAF_ROWS = 250

DEFAULT_NUMERIC_FEATURE_COLUMNS = [
    "impervious_pct",
    "elevation_m",
    "dist_to_water_m",
    "ndvi_median_may_aug",
]
DEFAULT_CATEGORICAL_FEATURE_COLUMNS = [
    "land_cover_class",
    "climate_group",
]
DEFAULT_BASELINE_MODELS = [
    "logistic_regression",
    "decision_stump",
]

PREDICTION_ID_COLUMNS = [
    "city_id",
    "city_name",
    "cell_id",
]
MISSING_CATEGORY_TOKEN = "__MISSING__"
UNSEEN_CATEGORY_TOKEN = "__UNSEEN__"


@dataclass(frozen=True)
class PreprocessingState:
    numeric_columns: list[str]
    categorical_columns: list[str]
    numeric_means: dict[str, float]
    numeric_stds: dict[str, float]
    categorical_levels: dict[str, list[str]]
    categorical_offsets: dict[str, int]
    categorical_index_maps: dict[str, dict[str, int]]
    feature_names: list[str]


@dataclass(frozen=True)
class TrainingScanSummary:
    n_rows: int
    n_positive: int
    n_missing_target_rows: int
    n_missing_fold_rows: int


@dataclass(frozen=True)
class LogisticRegressionModel:
    coefficients: np.ndarray
    feature_names: list[str]
    n_iterations: int
    converged: bool
    final_max_abs_step: float

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        linear = np.clip(x @ self.coefficients, -35.0, 35.0)
        return 1.0 / (1.0 + np.exp(-linear))


@dataclass(frozen=True)
class DecisionStumpModel:
    feature_index: int | None
    threshold: float | None
    left_probability: float
    right_probability: float
    default_probability: float
    split_feature_name: str | None
    sample_rows: int

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        if self.feature_index is None or self.threshold is None:
            return np.full(x.shape[0], self.default_probability, dtype=np.float64)

        return np.where(
            x[:, self.feature_index] <= self.threshold,
            self.left_probability,
            self.right_probability,
        )


@dataclass(frozen=True)
class BaselineRunResult:
    fold_metrics_path: Path
    overall_metrics_path: Path
    predictions_dir: Path
    assumptions_path: Path
    summary_json_path: Path
    model_artifacts_dir: Path


def _deduplicate_columns(columns: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(columns))


def resolve_fold_table_path(folds_path: Path | None = None) -> Path:
    """Return the preferred city-level fold artifact path."""
    if folds_path is not None:
        return folds_path

    parquet_path = MODELING / "city_outer_folds.parquet"
    if parquet_path.exists():
        return parquet_path

    csv_path = MODELING / "city_outer_folds.csv"
    if csv_path.exists():
        return csv_path

    raise FileNotFoundError("No city-level outer fold artifact found under data_processed/modeling/")


def load_city_outer_folds(folds_path: Path | None = None) -> pd.DataFrame:
    """Load the city-level outer-fold assignment artifact from parquet or CSV."""
    resolved_path = resolve_fold_table_path(folds_path=folds_path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"Fold table not found: {resolved_path}")

    if resolved_path.suffix.lower() == ".parquet":
        fold_table = pd.read_parquet(resolved_path)
    elif resolved_path.suffix.lower() == ".csv":
        fold_table = pd.read_csv(resolved_path)
    else:
        raise ValueError(f"Unsupported fold table format: {resolved_path.suffix}")

    required_columns = {"city_id", "outer_fold"}
    missing_columns = sorted(required_columns - set(fold_table.columns))
    if missing_columns:
        raise ValueError(f"Fold table missing required columns: {', '.join(missing_columns)}")

    if fold_table["city_id"].isna().any():
        raise ValueError("Fold table contains missing city_id values")
    if fold_table["outer_fold"].isna().any():
        raise ValueError("Fold table contains missing outer_fold values")
    if fold_table["city_id"].duplicated().any():
        duplicate_ids = sorted(fold_table.loc[fold_table["city_id"].duplicated(), "city_id"].astype(int).tolist())
        duplicate_text = ", ".join(str(city_id) for city_id in duplicate_ids)
        raise ValueError(f"Fold table contains duplicate city assignments: {duplicate_text}")
    if int(fold_table["outer_fold"].nunique()) < 2:
        raise ValueError("Fold table must contain at least two distinct folds")

    return fold_table.sort_values(["outer_fold", "city_id"]).reset_index(drop=True)


def validate_model_feature_columns(
    feature_columns: Iterable[str],
    available_columns: Iterable[str],
    excluded_columns: Iterable[str] = DEFAULT_EXCLUDED_COLUMNS,
    target_column: str = DEFAULT_TARGET_COLUMN,
    group_column: str = DEFAULT_GROUP_COLUMN,
) -> list[str]:
    """Validate that requested model features are present and exclude leakage columns."""
    requested = _deduplicate_columns(feature_columns)
    available = set(available_columns)
    excluded = set(excluded_columns) | {target_column, group_column}

    missing_columns = sorted(set(requested) - available)
    if missing_columns:
        raise ValueError(f"Requested feature columns missing from dataset: {', '.join(missing_columns)}")

    leaked_columns = sorted(set(requested) & excluded)
    if leaked_columns:
        raise ValueError(f"Feature columns include leakage-prone fields: {', '.join(leaked_columns)}")

    numeric_and_categorical = set(DEFAULT_NUMERIC_FEATURE_COLUMNS) | set(DEFAULT_CATEGORICAL_FEATURE_COLUMNS)
    unsupported_columns = sorted(set(requested) - numeric_and_categorical)
    if unsupported_columns:
        unsupported_text = ", ".join(unsupported_columns)
        raise ValueError(
            "Baseline pipeline currently supports only the safe numeric/categorical baseline features. "
            f"Unsupported columns: {unsupported_text}"
        )

    return requested


def join_batch_to_outer_folds(
    batch_df: pd.DataFrame,
    fold_lookup: dict[int, int],
    group_column: str = DEFAULT_GROUP_COLUMN,
) -> pd.DataFrame:
    """Join a parquet batch to the city-level outer folds via city_id."""
    if group_column not in batch_df.columns:
        raise ValueError(f"Grouping column not found in batch: {group_column}")

    joined = batch_df.copy()
    city_ids = pd.to_numeric(joined[group_column], errors="coerce").astype("Int64")
    joined["outer_fold"] = city_ids.map(fold_lookup)
    return joined


def iter_dataset_batches(
    dataset_path: Path,
    columns: Iterable[str],
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> Iterator[pd.DataFrame]:
    """Yield parquet batches as pandas DataFrames while loading only selected columns."""
    selected_columns = _deduplicate_columns(columns)
    dataset = ds.dataset(dataset_path, format="parquet")
    scanner = dataset.scanner(columns=selected_columns, batch_size=batch_size)
    for batch in scanner.to_batches():
        yield batch.to_pandas()


def load_preview_rows(
    dataset_path: Path,
    columns: Iterable[str],
    max_rows: int = 50_000,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> pd.DataFrame:
    """Load a small preview sample without materializing the full parquet."""
    parts: list[pd.DataFrame] = []
    remaining = max_rows
    for batch_df in iter_dataset_batches(dataset_path=dataset_path, columns=columns, batch_size=batch_size):
        if remaining <= 0:
            break
        take = batch_df.head(remaining).copy()
        if not take.empty:
            parts.append(take)
            remaining -= len(take)
        if remaining <= 0:
            break

    if not parts:
        return pd.DataFrame(columns=_deduplicate_columns(columns))
    return pd.concat(parts, ignore_index=True)


def _normalize_binary_target_series(series: pd.Series, column_name: str) -> pd.Series:
    normalized = pd.Series(np.nan, index=series.index, dtype="float64")

    if pd.api.types.is_bool_dtype(series):
        normalized.loc[:] = series.astype("float64")
        return normalized

    for index, raw_value in series.items():
        if pd.isna(raw_value):
            continue
        if isinstance(raw_value, str):
            value = raw_value.strip().lower()
            if value in {"0", "false"}:
                normalized.at[index] = 0.0
                continue
            if value in {"1", "true"}:
                normalized.at[index] = 1.0
                continue
            raise ValueError(f"Target column {column_name} must be binary. Found non-binary value: {raw_value}")

        try:
            numeric = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Target column {column_name} must be binary. Found non-binary value: {raw_value}"
            ) from exc

        if numeric not in (0.0, 1.0):
            raise ValueError(f"Target column {column_name} must be binary. Found non-binary value: {raw_value}")
        normalized.at[index] = numeric

    return normalized


def _normalize_categorical_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        numeric = pd.to_numeric(series, errors="coerce")
        out = pd.Series(MISSING_CATEGORY_TOKEN, index=series.index, dtype="object")
        mask = numeric.notna()
        if mask.any():
            out.loc[mask] = numeric.loc[mask].round().astype(int).astype(str)
        return out

    text = series.astype("string")
    text = text.fillna(MISSING_CATEGORY_TOKEN).str.strip()
    text = text.where(text.ne(""), MISSING_CATEGORY_TOKEN)
    return text.astype("object")


def _feature_type_split(feature_columns: Sequence[str]) -> tuple[list[str], list[str]]:
    numeric_columns = [column for column in feature_columns if column in DEFAULT_NUMERIC_FEATURE_COLUMNS]
    categorical_columns = [column for column in feature_columns if column in DEFAULT_CATEGORICAL_FEATURE_COLUMNS]
    return numeric_columns, categorical_columns


def _build_preprocessing_state(
    numeric_columns: Sequence[str],
    categorical_columns: Sequence[str],
    numeric_counts: dict[str, int],
    numeric_sums: dict[str, float],
    numeric_sum_squares: dict[str, float],
    categorical_levels: dict[str, set[str]],
) -> PreprocessingState:
    numeric_means: dict[str, float] = {}
    numeric_stds: dict[str, float] = {}
    feature_names = ["intercept"]

    for column in numeric_columns:
        count = numeric_counts[column]
        if count == 0:
            numeric_means[column] = 0.0
            numeric_stds[column] = 1.0
        else:
            mean = float(numeric_sums[column] / count)
            variance = max(float(numeric_sum_squares[column] / count) - (mean**2), 0.0)
            std = float(np.sqrt(variance))
            numeric_means[column] = mean
            numeric_stds[column] = std if std > 0 else 1.0

        feature_names.append(f"{column}_zscore")
        feature_names.append(f"{column}_missing")

    ordered_categorical_levels: dict[str, list[str]] = {}
    categorical_offsets: dict[str, int] = {}
    categorical_index_maps: dict[str, dict[str, int]] = {}

    next_offset = len(feature_names)
    for column in categorical_columns:
        ordered_levels = sorted(categorical_levels[column] | {MISSING_CATEGORY_TOKEN, UNSEEN_CATEGORY_TOKEN})
        ordered_categorical_levels[column] = ordered_levels
        categorical_offsets[column] = next_offset
        categorical_index_maps[column] = {level: idx for idx, level in enumerate(ordered_levels)}
        for level in ordered_levels:
            feature_names.append(f"{column}={level}")
        next_offset += len(ordered_levels)

    return PreprocessingState(
        numeric_columns=list(numeric_columns),
        categorical_columns=list(categorical_columns),
        numeric_means=numeric_means,
        numeric_stds=numeric_stds,
        categorical_levels=ordered_categorical_levels,
        categorical_offsets=categorical_offsets,
        categorical_index_maps=categorical_index_maps,
        feature_names=feature_names,
    )


def scan_training_preprocessing(
    dataset_path: Path,
    fold_lookup: dict[int, int],
    current_fold: int,
    feature_columns: Sequence[str],
    target_column: str = DEFAULT_TARGET_COLUMN,
    group_column: str = DEFAULT_GROUP_COLUMN,
    batch_size: int = DEFAULT_BATCH_SIZE,
    tree_sample_per_city: int = DEFAULT_TREE_SAMPLE_PER_CITY,
) -> tuple[PreprocessingState, TrainingScanSummary, pd.DataFrame]:
    """Scan training rows only to fit train-fold preprocessing and collect a bounded stump sample."""
    numeric_columns, categorical_columns = _feature_type_split(feature_columns)
    selected_columns = [group_column, target_column, *feature_columns]

    numeric_counts = {column: 0 for column in numeric_columns}
    numeric_sums = {column: 0.0 for column in numeric_columns}
    numeric_sum_squares = {column: 0.0 for column in numeric_columns}
    categorical_levels = {column: set() for column in categorical_columns}
    per_city_tree_counts: dict[int, int] = defaultdict(int)
    tree_samples: list[pd.DataFrame] = []

    n_rows = 0
    n_positive = 0
    n_missing_target_rows = 0
    n_missing_fold_rows = 0

    for batch_index, batch_df in enumerate(
        iter_dataset_batches(dataset_path=dataset_path, columns=selected_columns, batch_size=batch_size),
        start=1,
    ):
        joined = join_batch_to_outer_folds(batch_df=batch_df, fold_lookup=fold_lookup, group_column=group_column)
        missing_fold_mask = joined["outer_fold"].isna()
        if missing_fold_mask.any():
            n_missing_fold_rows += int(missing_fold_mask.sum())
            joined = joined.loc[~missing_fold_mask].copy()

        train_df = joined.loc[joined["outer_fold"] != current_fold, selected_columns].copy()
        if train_df.empty:
            continue

        target_values = _normalize_binary_target_series(train_df[target_column], column_name=target_column)
        valid_target_mask = target_values.notna()
        n_missing_target_rows += int((~valid_target_mask).sum())
        train_df = train_df.loc[valid_target_mask].copy()
        target_values = target_values.loc[valid_target_mask].astype(np.int8)
        if train_df.empty:
            continue

        n_rows += int(len(train_df))
        n_positive += int(target_values.sum())

        for column in numeric_columns:
            values = pd.to_numeric(train_df[column], errors="coerce").to_numpy(dtype=np.float64)
            mask = np.isfinite(values)
            if not mask.any():
                continue
            observed = values[mask]
            numeric_counts[column] += int(mask.sum())
            numeric_sums[column] += float(observed.sum())
            numeric_sum_squares[column] += float(np.square(observed).sum())

        for column in categorical_columns:
            categorical_levels[column].update(_normalize_categorical_series(train_df[column]).tolist())

        if tree_sample_per_city > 0:
            sample_frame = train_df[[group_column, *feature_columns]].copy()
            sample_frame[target_column] = target_values.to_numpy(dtype=np.int8)
            for city_id, city_df in sample_frame.groupby(group_column, sort=False):
                city_id_int = int(city_id)
                remaining = tree_sample_per_city - per_city_tree_counts[city_id_int]
                if remaining <= 0:
                    continue
                take = city_df.head(remaining).copy()
                if take.empty:
                    continue
                per_city_tree_counts[city_id_int] += int(len(take))
                tree_samples.append(take)

        if batch_index % 25 == 0:
            logger.info(
                "Preprocessing scan fold=%s batches=%s rows=%s positives=%s",
                current_fold,
                batch_index,
                f"{n_rows:,}",
                f"{n_positive:,}",
            )

    if n_rows == 0:
        raise ValueError(f"Fold {current_fold} has no training rows after joining folds and dropping missing targets")
    if n_missing_fold_rows > 0:
        raise ValueError(
            f"Found {n_missing_fold_rows:,} dataset rows whose city_id was missing from the fold table during preprocessing"
        )

    state = _build_preprocessing_state(
        numeric_columns=numeric_columns,
        categorical_columns=categorical_columns,
        numeric_counts=numeric_counts,
        numeric_sums=numeric_sums,
        numeric_sum_squares=numeric_sum_squares,
        categorical_levels=categorical_levels,
    )
    summary = TrainingScanSummary(
        n_rows=n_rows,
        n_positive=n_positive,
        n_missing_target_rows=n_missing_target_rows,
        n_missing_fold_rows=n_missing_fold_rows,
    )
    sample_df = (
        pd.concat(tree_samples, ignore_index=True)
        if tree_samples
        else pd.DataFrame(columns=[*feature_columns, target_column])
    )
    return state, summary, sample_df


def transform_features_to_matrix(df: pd.DataFrame, state: PreprocessingState) -> np.ndarray:
    """Convert a feature frame into a dense design matrix using train-fold-only preprocessing."""
    n_rows = len(df)
    x = np.zeros((n_rows, len(state.feature_names)), dtype=np.float64)
    x[:, 0] = 1.0

    next_numeric_column = 1
    for column in state.numeric_columns:
        values = pd.to_numeric(df[column], errors="coerce").to_numpy(dtype=np.float64)
        missing_mask = ~np.isfinite(values)
        filled = values.copy()
        filled[missing_mask] = state.numeric_means[column]
        x[:, next_numeric_column] = (filled - state.numeric_means[column]) / state.numeric_stds[column]
        x[:, next_numeric_column + 1] = missing_mask.astype(np.float64)
        next_numeric_column += 2

    row_index = np.arange(n_rows)
    for column in state.categorical_columns:
        normalized = _normalize_categorical_series(df[column])
        index_map = state.categorical_index_maps[column]
        unseen_index = index_map[UNSEEN_CATEGORY_TOKEN]
        encoded = normalized.map(index_map).fillna(unseen_index).to_numpy(dtype=np.int32)
        offset = state.categorical_offsets[column]
        x[row_index, offset + encoded] = 1.0

    return x


def fit_logistic_regression_streaming(
    dataset_path: Path,
    fold_lookup: dict[int, int],
    current_fold: int,
    feature_columns: Sequence[str],
    preprocessing_state: PreprocessingState,
    target_column: str = DEFAULT_TARGET_COLUMN,
    group_column: str = DEFAULT_GROUP_COLUMN,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_iterations: int = DEFAULT_MAX_LOGISTIC_ITERATIONS,
    l2_penalty: float = DEFAULT_LOGISTIC_L2,
    convergence_tolerance: float = 1e-6,
) -> LogisticRegressionModel:
    """Fit a logistic regression baseline via streaming Newton updates on train-fold rows."""
    coefficients = np.zeros(len(preprocessing_state.feature_names), dtype=np.float64)
    selected_columns = [group_column, target_column, *feature_columns]

    converged = False
    final_max_abs_step = float("nan")

    for iteration in range(1, max_iterations + 1):
        gradient = np.zeros_like(coefficients)
        hessian = np.zeros((len(coefficients), len(coefficients)), dtype=np.float64)
        n_rows = 0

        for batch_df in iter_dataset_batches(dataset_path=dataset_path, columns=selected_columns, batch_size=batch_size):
            joined = join_batch_to_outer_folds(batch_df=batch_df, fold_lookup=fold_lookup, group_column=group_column)
            if joined["outer_fold"].isna().any():
                raise ValueError("Dataset contains rows whose city_id is missing from the fold table")

            train_df = joined.loc[joined["outer_fold"] != current_fold, [*feature_columns, target_column]].copy()
            if train_df.empty:
                continue

            target_values = _normalize_binary_target_series(train_df[target_column], column_name=target_column)
            valid_target_mask = target_values.notna()
            if not valid_target_mask.any():
                continue

            train_df = train_df.loc[valid_target_mask, feature_columns].copy()
            y = target_values.loc[valid_target_mask].to_numpy(dtype=np.float64)
            x = transform_features_to_matrix(train_df, preprocessing_state)

            linear = np.clip(x @ coefficients, -35.0, 35.0)
            probabilities = 1.0 / (1.0 + np.exp(-linear))
            weights = probabilities * (1.0 - probabilities)

            gradient += x.T @ (probabilities - y)
            hessian += x.T @ (x * weights[:, np.newaxis])
            n_rows += len(y)

        if n_rows == 0:
            raise ValueError(f"Fold {current_fold} has no training rows available for logistic regression")

        if l2_penalty > 0:
            gradient[1:] += l2_penalty * coefficients[1:]
            hessian[1:, 1:] += np.eye(len(coefficients) - 1, dtype=np.float64) * l2_penalty

        hessian += np.eye(len(coefficients), dtype=np.float64) * 1e-9

        try:
            step = np.linalg.solve(hessian, gradient)
        except np.linalg.LinAlgError:
            step = np.linalg.pinv(hessian) @ gradient

        coefficients -= step
        final_max_abs_step = float(np.max(np.abs(step)))
        logger.info(
            "Logistic regression fold=%s iteration=%s rows=%s max_abs_step=%.6e",
            current_fold,
            iteration,
            f"{n_rows:,}",
            final_max_abs_step,
        )

        if final_max_abs_step <= convergence_tolerance:
            converged = True
            break

    return LogisticRegressionModel(
        coefficients=coefficients,
        feature_names=preprocessing_state.feature_names,
        n_iterations=iteration,
        converged=converged,
        final_max_abs_step=final_max_abs_step,
    )


def _gini_impurity(y: np.ndarray) -> float:
    if y.size == 0:
        return 0.0
    positive_rate = float(y.mean())
    return 1.0 - (positive_rate**2) - ((1.0 - positive_rate) ** 2)


def fit_decision_stump_from_sample(
    sample_df: pd.DataFrame,
    feature_columns: Sequence[str],
    preprocessing_state: PreprocessingState,
    target_column: str = DEFAULT_TARGET_COLUMN,
    min_leaf_rows: int = DEFAULT_DECISION_STUMP_MIN_LEAF_ROWS,
) -> DecisionStumpModel:
    """Fit a one-split tree baseline on a bounded train-fold sample."""
    if sample_df.empty:
        return DecisionStumpModel(
            feature_index=None,
            threshold=None,
            left_probability=0.0,
            right_probability=0.0,
            default_probability=0.0,
            split_feature_name=None,
            sample_rows=0,
        )

    target_values = _normalize_binary_target_series(sample_df[target_column], column_name=target_column)
    valid_target_mask = target_values.notna()
    if not valid_target_mask.any():
        return DecisionStumpModel(
            feature_index=None,
            threshold=None,
            left_probability=0.0,
            right_probability=0.0,
            default_probability=0.0,
            split_feature_name=None,
            sample_rows=0,
        )

    valid_sample_df = sample_df.loc[valid_target_mask, feature_columns].copy()
    y = target_values.loc[valid_target_mask].to_numpy(dtype=np.float64)
    x = transform_features_to_matrix(valid_sample_df, preprocessing_state)

    default_probability = float(y.mean())
    best_loss = _gini_impurity(y)
    best_split: tuple[int, float, float, float] | None = None

    effective_min_leaf_rows = min(min_leaf_rows, max(1, y.size // 4))

    for feature_index in range(1, x.shape[1]):
        values = x[:, feature_index]
        unique_values = np.unique(values)
        if unique_values.size <= 1:
            continue

        if unique_values.size <= 2 and set(np.round(unique_values, 8).tolist()).issubset({0.0, 1.0}):
            thresholds = [0.5]
        else:
            thresholds = np.unique(
                np.quantile(values, [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
            ).tolist()

        for threshold in thresholds:
            left_mask = values <= threshold
            right_mask = ~left_mask
            left_count = int(left_mask.sum())
            right_count = int(right_mask.sum())
            if left_count < effective_min_leaf_rows or right_count < effective_min_leaf_rows:
                continue

            left_y = y[left_mask]
            right_y = y[right_mask]
            loss = ((left_count * _gini_impurity(left_y)) + (right_count * _gini_impurity(right_y))) / y.size
            if loss < best_loss:
                best_loss = loss
                best_split = (
                    feature_index,
                    float(threshold),
                    float(left_y.mean()) if left_y.size else default_probability,
                    float(right_y.mean()) if right_y.size else default_probability,
                )

    if best_split is None:
        return DecisionStumpModel(
            feature_index=None,
            threshold=None,
            left_probability=default_probability,
            right_probability=default_probability,
            default_probability=default_probability,
            split_feature_name=None,
            sample_rows=int(y.size),
        )

    feature_index, threshold, left_probability, right_probability = best_split
    return DecisionStumpModel(
        feature_index=feature_index,
        threshold=threshold,
        left_probability=left_probability,
        right_probability=right_probability,
        default_probability=default_probability,
        split_feature_name=preprocessing_state.feature_names[feature_index],
        sample_rows=int(y.size),
    )


def _compute_roc_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    positives = int(y_true.sum())
    negatives = int(y_true.size - positives)
    if positives == 0 or negatives == 0:
        return float("nan")

    order = np.argsort(y_score, kind="mergesort")
    sorted_scores = y_score[order]
    sorted_targets = y_true[order]

    sum_positive_ranks = 0.0
    index = 0
    while index < len(sorted_scores):
        next_index = index + 1
        while next_index < len(sorted_scores) and sorted_scores[next_index] == sorted_scores[index]:
            next_index += 1
        average_rank = (index + 1 + next_index) / 2.0
        positive_in_group = int(sorted_targets[index:next_index].sum())
        sum_positive_ranks += average_rank * positive_in_group
        index = next_index

    return float(
        (sum_positive_ranks - (positives * (positives + 1) / 2.0)) / (positives * negatives)
    )


def _compute_average_precision(y_true: np.ndarray, y_score: np.ndarray) -> float:
    positives = int(y_true.sum())
    if positives == 0:
        return float("nan")

    order = np.argsort(-y_score, kind="mergesort")
    sorted_scores = y_score[order]
    sorted_targets = y_true[order]

    true_positives = np.cumsum(sorted_targets)
    false_positives = np.cumsum(1 - sorted_targets)
    precision = true_positives / (true_positives + false_positives)
    recall = true_positives / positives

    distinct_indices = np.where(np.diff(sorted_scores))[0]
    threshold_indices = np.r_[distinct_indices, len(sorted_scores) - 1]

    precision_at_threshold = precision[threshold_indices]
    recall_at_threshold = recall[threshold_indices]
    prior_recall = np.r_[0.0, recall_at_threshold[:-1]]
    return float(np.sum((recall_at_threshold - prior_recall) * precision_at_threshold))


def compute_binary_classification_metrics(y_true: np.ndarray, y_score: np.ndarray) -> dict[str, float]:
    """Compute ROC-AUC, step PR-AUC, and prevalence from validation predictions."""
    y_true = y_true.astype(np.int8, copy=False)
    y_score = y_score.astype(np.float64, copy=False)
    positive_count = int(y_true.sum())
    row_count = int(y_true.size)
    prevalence = float(positive_count / row_count) if row_count else float("nan")
    return {
        "roc_auc": _compute_roc_auc(y_true=y_true, y_score=y_score),
        "pr_auc": _compute_average_precision(y_true=y_true, y_score=y_score),
        "validation_prevalence": prevalence,
        "validation_positive_count": positive_count,
        "validation_row_count": row_count,
    }


def _write_predictions_for_fold(
    dataset_path: Path,
    fold_lookup: dict[int, int],
    current_fold: int,
    model_name: str,
    model: LogisticRegressionModel | DecisionStumpModel,
    preprocessing_state: PreprocessingState,
    feature_columns: Sequence[str],
    output_path: Path,
    target_column: str = DEFAULT_TARGET_COLUMN,
    group_column: str = DEFAULT_GROUP_COLUMN,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> dict[str, float]:
    selected_columns = [*PREDICTION_ID_COLUMNS, target_column, *feature_columns]
    schema = pa.schema(
        [
            pa.field("model_name", pa.string()),
            pa.field("outer_fold", pa.int32()),
            pa.field("city_id", pa.int64()),
            pa.field("city_name", pa.string()),
            pa.field("cell_id", pa.int64()),
            pa.field("hotspot_10pct", pa.int8()),
            pa.field("predicted_probability", pa.float32()),
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    y_true_parts: list[np.ndarray] = []
    y_score_parts: list[np.ndarray] = []
    n_missing_fold_rows = 0
    n_missing_target_rows = 0

    with pq.ParquetWriter(output_path, schema=schema, compression="snappy") as writer:
        for batch_df in iter_dataset_batches(dataset_path=dataset_path, columns=selected_columns, batch_size=batch_size):
            joined = join_batch_to_outer_folds(batch_df=batch_df, fold_lookup=fold_lookup, group_column=group_column)
            missing_fold_mask = joined["outer_fold"].isna()
            if missing_fold_mask.any():
                n_missing_fold_rows += int(missing_fold_mask.sum())
                joined = joined.loc[~missing_fold_mask].copy()

            validation_df = joined.loc[joined["outer_fold"] == current_fold, selected_columns].copy()
            if validation_df.empty:
                continue

            target_values = _normalize_binary_target_series(validation_df[target_column], column_name=target_column)
            valid_target_mask = target_values.notna()
            n_missing_target_rows += int((~valid_target_mask).sum())
            validation_df = validation_df.loc[valid_target_mask].copy()
            target_values = target_values.loc[valid_target_mask].to_numpy(dtype=np.int8)
            if validation_df.empty:
                continue

            x = transform_features_to_matrix(validation_df[feature_columns], preprocessing_state)
            probabilities = model.predict_proba(x).astype(np.float32)

            y_true_parts.append(target_values)
            y_score_parts.append(probabilities.astype(np.float64))

            prediction_table = pa.Table.from_pydict(
                {
                    "model_name": np.repeat(model_name, len(validation_df)),
                    "outer_fold": np.repeat(int(current_fold), len(validation_df)),
                    "city_id": pd.to_numeric(validation_df["city_id"], errors="raise").to_numpy(dtype=np.int64),
                    "city_name": validation_df["city_name"].fillna("").astype(str).tolist(),
                    "cell_id": pd.to_numeric(validation_df["cell_id"], errors="raise").to_numpy(dtype=np.int64),
                    "hotspot_10pct": target_values.astype(np.int8),
                    "predicted_probability": probabilities,
                },
                schema=schema,
            )
            writer.write_table(prediction_table)

    if n_missing_fold_rows > 0:
        raise ValueError(
            f"Found {n_missing_fold_rows:,} dataset rows whose city_id was missing from the fold table during evaluation"
        )

    if not y_true_parts:
        raise ValueError(f"Fold {current_fold} produced no validation predictions for model {model_name}")

    metrics = compute_binary_classification_metrics(
        y_true=np.concatenate(y_true_parts),
        y_score=np.concatenate(y_score_parts),
    )
    metrics["n_missing_target_rows"] = int(n_missing_target_rows)
    return metrics


def _aggregate_overall_metrics(fold_metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if fold_metrics.empty:
        return pd.DataFrame(rows)

    for model_name, model_df in fold_metrics.groupby("model_name", sort=True):
        weights = model_df["n_validation_rows"].astype(float)
        total_rows = int(weights.sum())
        safe_weights = weights / weights.sum() if total_rows else np.zeros(len(model_df))
        rows.append(
            {
                "model_name": model_name,
                "n_folds": int(model_df["outer_fold"].nunique()),
                "total_validation_rows": total_rows,
                "total_validation_positive_count": int(model_df["validation_positive_count"].sum()),
                "mean_fold_roc_auc": float(model_df["roc_auc"].mean()),
                "weighted_mean_fold_roc_auc": float((model_df["roc_auc"] * safe_weights).sum()),
                "mean_fold_pr_auc": float(model_df["pr_auc"].mean()),
                "weighted_mean_fold_pr_auc": float((model_df["pr_auc"] * safe_weights).sum()),
                "mean_fold_validation_prevalence": float(model_df["validation_prevalence"].mean()),
                "weighted_mean_validation_prevalence": float((model_df["validation_prevalence"] * safe_weights).sum()),
            }
        )

    return pd.DataFrame(rows).sort_values("model_name").reset_index(drop=True)


def _write_assumptions_markdown(
    output_path: Path,
    dataset_path: Path,
    folds_path: Path,
    feature_columns: Sequence[str],
    models: Sequence[str],
    fold_metrics_path: Path,
    overall_metrics_path: Path,
    predictions_dir: Path,
) -> None:
    lines = [
        "# Baseline Modeling Assumptions",
        "",
        f"- Dataset path: `{dataset_path}`",
        f"- Fold table path: `{folds_path}`",
        f"- Target column: `{DEFAULT_TARGET_COLUMN}`",
        f"- Grouping column: `{DEFAULT_GROUP_COLUMN}`",
        f"- Baseline feature columns: `{', '.join(feature_columns)}`",
        f"- Explicitly excluded leakage-prone columns: `{', '.join(DEFAULT_EXCLUDED_COLUMNS)}`",
        f"- Models run: `{', '.join(models)}`",
        "- Rows are mapped to held-out folds via the city-level fold table on `city_id`.",
        "- Rows with missing `hotspot_10pct` or missing fold assignments are excluded from training/evaluation.",
        "- Numeric features use train-fold-only mean imputation, train-fold-only z-scoring, and explicit missing indicators.",
        "- Categorical features use train-fold-only vocabularies plus dedicated missing/unseen buckets.",
        "- Logistic regression is fit on the full train-fold rows with streaming Newton updates and ridge stabilization.",
        "- The tree comparison is a decision stump fit on a bounded per-city train-fold sample to keep memory usage predictable.",
        "- Overall metrics are aggregated from fold-level metrics; they are not a single pooled exact out-of-fold ROC/PR computation.",
        "",
        "## Output Files",
        "",
        f"- `{fold_metrics_path}`",
        f"- `{overall_metrics_path}`",
        f"- `{predictions_dir}`",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_baseline_modeling(
    dataset_path: Path = FINAL / "final_dataset.parquet",
    folds_path: Path | None = None,
    output_dir: Path = DEFAULT_BASELINE_OUTPUT_DIR,
    feature_columns: Iterable[str] = DEFAULT_FEATURE_COLUMNS,
    models: Iterable[str] = DEFAULT_BASELINE_MODELS,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_logistic_iterations: int = DEFAULT_MAX_LOGISTIC_ITERATIONS,
    logistic_l2_penalty: float = DEFAULT_LOGISTIC_L2,
    tree_sample_per_city: int = DEFAULT_TREE_SAMPLE_PER_CITY,
    decision_stump_min_leaf_rows: int = DEFAULT_DECISION_STUMP_MIN_LEAF_ROWS,
    selected_outer_folds: Iterable[int] | None = None,
) -> BaselineRunResult:
    """Train and evaluate leak-safe city-held-out baseline models."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Final dataset not found: {dataset_path}")

    resolved_folds_path = resolve_fold_table_path(folds_path=folds_path)
    fold_table = load_city_outer_folds(resolved_folds_path)
    fold_lookup = {
        int(city_id): int(outer_fold)
        for city_id, outer_fold in fold_table[["city_id", "outer_fold"]].itertuples(index=False)
    }

    available_columns = get_final_dataset_columns(dataset_path=dataset_path)
    validate_required_final_columns(available_columns)
    feature_columns = validate_model_feature_columns(
        feature_columns=feature_columns,
        available_columns=available_columns,
    )

    selected_models = _deduplicate_columns(models)
    unsupported_models = sorted(set(selected_models) - set(DEFAULT_BASELINE_MODELS))
    if unsupported_models:
        unsupported_text = ", ".join(unsupported_models)
        raise ValueError(f"Unsupported baseline model(s): {unsupported_text}")
    if not selected_models:
        raise ValueError("At least one baseline model must be selected")

    preview_columns = _deduplicate_columns([DEFAULT_GROUP_COLUMN, DEFAULT_TARGET_COLUMN, *feature_columns])
    preview_df = load_preview_rows(dataset_path=dataset_path, columns=preview_columns, max_rows=50_000, batch_size=batch_size)
    validate_binary_target(preview_df, target_column=DEFAULT_TARGET_COLUMN)

    output_dir.mkdir(parents=True, exist_ok=True)
    predictions_dir = output_dir / "validation_predictions"
    model_artifacts_dir = output_dir / "model_artifacts"
    predictions_dir.mkdir(parents=True, exist_ok=True)
    model_artifacts_dir.mkdir(parents=True, exist_ok=True)

    available_folds = sorted(int(value) for value in fold_table["outer_fold"].unique())
    requested_folds = (
        available_folds if selected_outer_folds is None else sorted({int(value) for value in selected_outer_folds})
    )
    missing_requested_folds = sorted(set(requested_folds) - set(available_folds))
    if missing_requested_folds:
        missing_text = ", ".join(str(fold_id) for fold_id in missing_requested_folds)
        raise ValueError(f"Requested outer folds not found in fold table: {missing_text}")

    fold_metrics_rows: list[dict[str, object]] = []
    logistic_rows: list[dict[str, object]] = []
    stump_rows: list[dict[str, object]] = []
    leakage_checks: list[dict[str, object]] = []

    for current_fold in requested_folds:
        validation_city_rows = fold_table.loc[fold_table["outer_fold"] == current_fold].copy()
        training_city_rows = fold_table.loc[fold_table["outer_fold"] != current_fold].copy()
        validation_city_ids = validation_city_rows["city_id"].astype(int).tolist()
        training_city_ids = training_city_rows["city_id"].astype(int).tolist()

        if set(validation_city_ids) & set(training_city_ids):
            raise ValueError(f"Leakage detected in fold table for outer_fold={current_fold}: overlapping train/validation cities")

        logger.info(
            "Starting fold=%s train_cities=%s validation_cities=%s",
            current_fold,
            len(training_city_ids),
            len(validation_city_ids),
        )

        preprocessing_state, training_summary, tree_sample_df = scan_training_preprocessing(
            dataset_path=dataset_path,
            fold_lookup=fold_lookup,
            current_fold=current_fold,
            feature_columns=feature_columns,
            batch_size=batch_size,
            tree_sample_per_city=tree_sample_per_city,
        )

        leakage_checks.append(
            {
                "outer_fold": int(current_fold),
                "train_city_count": int(len(training_city_ids)),
                "validation_city_count": int(len(validation_city_ids)),
                "train_validation_city_overlap_count": 0,
                "n_missing_fold_rows": int(training_summary.n_missing_fold_rows),
                "requested_feature_columns": ",".join(feature_columns),
                "excluded_columns": ",".join(DEFAULT_EXCLUDED_COLUMNS),
            }
        )

        fitted_models: dict[str, LogisticRegressionModel | DecisionStumpModel] = {}
        if "logistic_regression" in selected_models:
            logistic_model = fit_logistic_regression_streaming(
                dataset_path=dataset_path,
                fold_lookup=fold_lookup,
                current_fold=current_fold,
                feature_columns=feature_columns,
                preprocessing_state=preprocessing_state,
                batch_size=batch_size,
                max_iterations=max_logistic_iterations,
                l2_penalty=logistic_l2_penalty,
            )
            fitted_models["logistic_regression"] = logistic_model
            for feature_name, coefficient in zip(logistic_model.feature_names, logistic_model.coefficients, strict=True):
                logistic_rows.append(
                    {
                        "outer_fold": int(current_fold),
                        "feature_name": feature_name,
                        "coefficient": float(coefficient),
                        "n_iterations": int(logistic_model.n_iterations),
                        "converged": bool(logistic_model.converged),
                        "final_max_abs_step": float(logistic_model.final_max_abs_step),
                    }
                )

        if "decision_stump" in selected_models:
            stump_model = fit_decision_stump_from_sample(
                sample_df=tree_sample_df,
                feature_columns=feature_columns,
                preprocessing_state=preprocessing_state,
                min_leaf_rows=decision_stump_min_leaf_rows,
            )
            fitted_models["decision_stump"] = stump_model
            stump_rows.append(
                {
                    "outer_fold": int(current_fold),
                    "split_feature_name": stump_model.split_feature_name or "",
                    "threshold": float(stump_model.threshold) if stump_model.threshold is not None else np.nan,
                    "left_probability": float(stump_model.left_probability),
                    "right_probability": float(stump_model.right_probability),
                    "default_probability": float(stump_model.default_probability),
                    "sample_rows": int(stump_model.sample_rows),
                }
            )

        for model_name, model in fitted_models.items():
            prediction_path = predictions_dir / model_name / f"outer_fold={current_fold}.parquet"
            validation_metrics = _write_predictions_for_fold(
                dataset_path=dataset_path,
                fold_lookup=fold_lookup,
                current_fold=current_fold,
                model_name=model_name,
                model=model,
                preprocessing_state=preprocessing_state,
                feature_columns=feature_columns,
                output_path=prediction_path,
                batch_size=batch_size,
            )

            fold_metrics_rows.append(
                {
                    "model_name": model_name,
                    "outer_fold": int(current_fold),
                    "n_training_rows": int(training_summary.n_rows),
                    "training_positive_count": int(training_summary.n_positive),
                    "training_prevalence": float(training_summary.n_positive / training_summary.n_rows),
                    "n_validation_rows": int(validation_metrics["validation_row_count"]),
                    "validation_positive_count": int(validation_metrics["validation_positive_count"]),
                    "validation_prevalence": float(validation_metrics["validation_prevalence"]),
                    "n_training_cities": int(len(training_city_ids)),
                    "n_validation_cities": int(len(validation_city_ids)),
                    "validation_city_ids": ",".join(str(city_id) for city_id in validation_city_ids),
                    "validation_city_names": ",".join(validation_city_rows["city_name"].fillna("").astype(str).tolist()),
                    "roc_auc": float(validation_metrics["roc_auc"]),
                    "pr_auc": float(validation_metrics["pr_auc"]),
                    "missing_target_rows_dropped": int(
                        training_summary.n_missing_target_rows + validation_metrics["n_missing_target_rows"]
                    ),
                    "prediction_path": str(prediction_path),
                }
            )

    fold_metrics_df = pd.DataFrame(fold_metrics_rows).sort_values(["model_name", "outer_fold"]).reset_index(drop=True)
    overall_metrics_df = _aggregate_overall_metrics(fold_metrics_df)
    leakage_checks_df = pd.DataFrame(leakage_checks).sort_values("outer_fold").reset_index(drop=True)

    fold_metrics_path = output_dir / "baseline_metrics_by_fold.csv"
    overall_metrics_path = output_dir / "baseline_metrics_overall.csv"
    leakage_checks_path = output_dir / "baseline_leakage_checks.csv"
    assumptions_path = output_dir / "baseline_assumptions.md"
    summary_json_path = output_dir / "baseline_run_summary.json"

    fold_metrics_df.to_csv(fold_metrics_path, index=False)
    overall_metrics_df.to_csv(overall_metrics_path, index=False)
    leakage_checks_df.to_csv(leakage_checks_path, index=False)

    if logistic_rows:
        pd.DataFrame(logistic_rows).to_csv(model_artifacts_dir / "logistic_regression_coefficients.csv", index=False)
    if stump_rows:
        pd.DataFrame(stump_rows).to_csv(model_artifacts_dir / "decision_stump_rules.csv", index=False)

    _write_assumptions_markdown(
        output_path=assumptions_path,
        dataset_path=dataset_path,
        folds_path=resolved_folds_path,
        feature_columns=feature_columns,
        models=selected_models,
        fold_metrics_path=fold_metrics_path,
        overall_metrics_path=overall_metrics_path,
        predictions_dir=predictions_dir,
    )

    summary_payload = {
        "generated_at_utc": pd.Timestamp.now("UTC").isoformat(),
        "dataset_path": str(dataset_path),
        "folds_path": str(resolved_folds_path),
        "output_dir": str(output_dir),
        "feature_columns": feature_columns,
        "excluded_columns": list(DEFAULT_EXCLUDED_COLUMNS),
        "models": selected_models,
        "batch_size": int(batch_size),
        "max_logistic_iterations": int(max_logistic_iterations),
        "logistic_l2_penalty": float(logistic_l2_penalty),
        "tree_sample_per_city": int(tree_sample_per_city),
        "decision_stump_min_leaf_rows": int(decision_stump_min_leaf_rows),
        "outer_folds_run": requested_folds,
        "fold_metrics_path": str(fold_metrics_path),
        "overall_metrics_path": str(overall_metrics_path),
        "leakage_checks_path": str(leakage_checks_path),
        "assumptions_path": str(assumptions_path),
        "predictions_dir": str(predictions_dir),
        "model_artifacts_dir": str(model_artifacts_dir),
    }
    summary_json_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")

    return BaselineRunResult(
        fold_metrics_path=fold_metrics_path,
        overall_metrics_path=overall_metrics_path,
        predictions_dir=predictions_dir,
        assumptions_path=assumptions_path,
        summary_json_path=summary_json_path,
        model_artifacts_dir=model_artifacts_dir,
    )
