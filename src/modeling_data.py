from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

from src.modeling_config import (
    DEFAULT_FEATURE_COLUMNS,
    DEFAULT_FINAL_DATASET_PATH,
    DEFAULT_FOLDS_CSV_PATH,
    DEFAULT_FOLDS_PARQUET_PATH,
    EXCLUDED_FEATURE_COLUMNS,
    FOLD_COLUMN,
    GROUP_COLUMN,
    IDENTIFIER_COLUMNS,
    MODEL_FEATURE_TYPES,
    TARGET_COLUMN,
    get_feature_type_map,
)
from src.modeling_prep import get_final_dataset_columns, validate_binary_target, validate_required_final_columns


@dataclass(frozen=True)
class OuterFoldData:
    outer_fold: int
    train_df: pd.DataFrame
    test_df: pd.DataFrame
    train_city_ids: list[int]
    test_city_ids: list[int]


def _deduplicate_columns(columns: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(columns))


def resolve_fold_table_path(folds_path: Path | None = None) -> Path:
    """Return the preferred city-level fold artifact path."""
    if folds_path is not None:
        return folds_path
    if DEFAULT_FOLDS_PARQUET_PATH.exists():
        return DEFAULT_FOLDS_PARQUET_PATH
    if DEFAULT_FOLDS_CSV_PATH.exists():
        return DEFAULT_FOLDS_CSV_PATH
    raise FileNotFoundError("No city-level outer fold artifact found under data_processed/modeling/")


def load_city_outer_folds(folds_path: Path | None = None) -> pd.DataFrame:
    """Load and validate the city-level outer-fold assignment table."""
    resolved_path = resolve_fold_table_path(folds_path=folds_path)
    if resolved_path.suffix.lower() == ".parquet":
        fold_table = pd.read_parquet(resolved_path)
    elif resolved_path.suffix.lower() == ".csv":
        fold_table = pd.read_csv(resolved_path)
    else:
        raise ValueError(f"Unsupported fold table format: {resolved_path.suffix}")

    required_columns = {GROUP_COLUMN, FOLD_COLUMN}
    missing_columns = sorted(required_columns - set(fold_table.columns))
    if missing_columns:
        raise ValueError(f"Fold table missing required columns: {', '.join(missing_columns)}")
    if fold_table[GROUP_COLUMN].isna().any():
        raise ValueError("Fold table contains missing city_id values")
    if fold_table[FOLD_COLUMN].isna().any():
        raise ValueError("Fold table contains missing outer_fold values")
    if fold_table[GROUP_COLUMN].duplicated().any():
        duplicate_ids = sorted(fold_table.loc[fold_table[GROUP_COLUMN].duplicated(), GROUP_COLUMN].astype(int).tolist())
        duplicate_text = ", ".join(str(city_id) for city_id in duplicate_ids)
        raise ValueError(f"Fold table contains duplicate city assignments: {duplicate_text}")
    if int(fold_table[FOLD_COLUMN].nunique()) < 2:
        raise ValueError("Fold table must contain at least two distinct folds")

    return fold_table.sort_values([FOLD_COLUMN, GROUP_COLUMN]).reset_index(drop=True)


def validate_model_feature_columns(
    feature_columns: Iterable[str],
    available_columns: Iterable[str],
    excluded_columns: Iterable[str] = EXCLUDED_FEATURE_COLUMNS,
) -> list[str]:
    """Validate that requested features exist and do not include leakage-prone columns."""
    requested = _deduplicate_columns(feature_columns)
    available = set(available_columns)
    missing_columns = sorted(set(requested) - available)
    if missing_columns:
        raise ValueError(f"Requested feature columns missing from dataset: {', '.join(missing_columns)}")

    leaked_columns = sorted(set(requested) & set(excluded_columns))
    if leaked_columns:
        raise ValueError(f"Feature columns include leakage-prone fields: {', '.join(leaked_columns)}")

    missing_type_contract = sorted(set(requested) - set(MODEL_FEATURE_TYPES))
    if missing_type_contract:
        raise ValueError(
            "Feature columns missing an explicit modeling type contract: "
            + ", ".join(missing_type_contract)
        )

    return requested


def normalize_binary_target(series: pd.Series, column_name: str = TARGET_COLUMN) -> pd.Series:
    """Normalize the binary target to nullable integer values."""
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


def get_selected_modeling_columns(
    feature_columns: Sequence[str] | None = None,
    extra_columns: Sequence[str] | None = None,
) -> list[str]:
    """Return the columns needed for a modeling run."""
    selected_features = DEFAULT_FEATURE_COLUMNS if feature_columns is None else list(feature_columns)
    selected_extra = [] if extra_columns is None else list(extra_columns)
    return _deduplicate_columns([*IDENTIFIER_COLUMNS, TARGET_COLUMN, *selected_features, *selected_extra])


def _read_dataset_subset(
    dataset_path: Path,
    columns: Sequence[str],
    city_ids: Sequence[int] | None = None,
) -> pd.DataFrame:
    if city_ids is None:
        return pd.read_parquet(dataset_path, columns=list(columns))
    filters = [(GROUP_COLUMN, "in", [int(city_id) for city_id in city_ids])]
    return pd.read_parquet(dataset_path, columns=list(columns), filters=filters)


def load_modeling_rows(
    dataset_path: Path = DEFAULT_FINAL_DATASET_PATH,
    feature_columns: Sequence[str] | None = None,
    city_ids: Sequence[int] | None = None,
    sample_rows_per_city: int | None = None,
    random_state: int = 42,
    extra_columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Load the selected modeling columns, optionally with deterministic per-city sampling."""
    available_columns = get_final_dataset_columns(dataset_path=dataset_path)
    validate_required_final_columns(available_columns)
    selected_columns = get_selected_modeling_columns(feature_columns=feature_columns, extra_columns=extra_columns)
    validate_model_feature_columns(
        feature_columns=DEFAULT_FEATURE_COLUMNS if feature_columns is None else feature_columns,
        available_columns=available_columns,
    )

    if sample_rows_per_city is None:
        df = _read_dataset_subset(dataset_path=dataset_path, columns=selected_columns, city_ids=city_ids)
    else:
        if city_ids is None:
            raise ValueError("sample_rows_per_city requires an explicit list of city_ids")
        parts: list[pd.DataFrame] = []
        for city_id in city_ids:
            city_df = _read_dataset_subset(dataset_path=dataset_path, columns=selected_columns, city_ids=[int(city_id)])
            if len(city_df) > sample_rows_per_city:
                city_df = city_df.sample(
                    n=sample_rows_per_city,
                    random_state=int(random_state) + int(city_id),
                )
            parts.append(city_df)
        df = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=selected_columns)

    if TARGET_COLUMN in df.columns and not df.empty:
        validate_binary_target(df, target_column=TARGET_COLUMN)
    return df


def drop_missing_target_rows(df: pd.DataFrame, target_column: str = TARGET_COLUMN) -> pd.DataFrame:
    """Return a copy with missing targets removed and target normalized to int8."""
    if target_column not in df.columns:
        raise ValueError(f"Target column not found: {target_column}")
    normalized = normalize_binary_target(df[target_column], column_name=target_column)
    valid_mask = normalized.notna()
    cleaned = df.loc[valid_mask].copy()
    cleaned[target_column] = normalized.loc[valid_mask].astype("int8")
    return cleaned.reset_index(drop=True)


def get_requested_outer_folds(
    fold_table: pd.DataFrame,
    selected_outer_folds: Sequence[int] | None = None,
) -> list[int]:
    """Return the outer folds that should be run."""
    available_folds = sorted(int(value) for value in fold_table[FOLD_COLUMN].unique())
    requested_folds = available_folds if selected_outer_folds is None else sorted({int(value) for value in selected_outer_folds})
    missing_requested = sorted(set(requested_folds) - set(available_folds))
    if missing_requested:
        missing_text = ", ".join(str(fold_id) for fold_id in missing_requested)
        raise ValueError(f"Requested outer folds not found in fold table: {missing_text}")
    return requested_folds


def load_outer_fold_data(
    outer_fold: int,
    dataset_path: Path = DEFAULT_FINAL_DATASET_PATH,
    folds_path: Path | None = None,
    feature_columns: Sequence[str] | None = None,
    sample_rows_per_city: int | None = None,
    random_state: int = 42,
) -> OuterFoldData:
    """Load train/test rows for one held-out city fold."""
    fold_table = load_city_outer_folds(folds_path=folds_path)
    validation_rows = fold_table.loc[fold_table[FOLD_COLUMN] == int(outer_fold)].copy()
    training_rows = fold_table.loc[fold_table[FOLD_COLUMN] != int(outer_fold)].copy()

    train_city_ids = training_rows[GROUP_COLUMN].astype(int).tolist()
    test_city_ids = validation_rows[GROUP_COLUMN].astype(int).tolist()
    if set(train_city_ids) & set(test_city_ids):
        raise ValueError(f"Leakage detected in outer_fold={outer_fold}: train/test cities overlap")

    train_df = drop_missing_target_rows(
        load_modeling_rows(
            dataset_path=dataset_path,
            feature_columns=feature_columns,
            city_ids=train_city_ids,
            sample_rows_per_city=sample_rows_per_city,
            random_state=random_state,
        )
    )
    test_df = drop_missing_target_rows(
        load_modeling_rows(
            dataset_path=dataset_path,
            feature_columns=feature_columns,
            city_ids=test_city_ids,
            sample_rows_per_city=sample_rows_per_city,
            random_state=random_state,
        )
    )

    return OuterFoldData(
        outer_fold=int(outer_fold),
        train_df=train_df,
        test_df=test_df,
        train_city_ids=train_city_ids,
        test_city_ids=test_city_ids,
    )


def write_feature_contract(output_path: Path, feature_columns: Sequence[str]) -> None:
    """Write the explicit modeling feature contract for a run."""
    feature_type_map = get_feature_type_map(feature_columns)
    payload = {
        "target_column": TARGET_COLUMN,
        "group_column": GROUP_COLUMN,
        "identifier_columns": IDENTIFIER_COLUMNS,
        "excluded_feature_columns": EXCLUDED_FEATURE_COLUMNS,
        "selected_feature_columns": list(feature_columns),
        "feature_type_map": feature_type_map,
        "numeric_feature_columns": [column for column, feature_type in feature_type_map.items() if feature_type == "numeric"],
        "categorical_feature_columns": [
            column for column, feature_type in feature_type_map.items() if feature_type == "categorical"
        ],
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
