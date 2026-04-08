from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

from src.modeling_config import (
    CITY_NAME_COLUMN,
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

LOGGER = logging.getLogger(__name__)
_WARNED_CSV_DATASET_PATHS: set[Path] = set()


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
    """Return the city-level fold artifact path, preferring parquet over CSV fallback."""
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
    if dataset_path.suffix.lower() == ".csv":
        read_kwargs: dict[str, object] = {"usecols": list(columns)}
        if city_ids is None:
            return pd.read_csv(dataset_path, **read_kwargs)

        city_id_set = {int(city_id) for city_id in city_ids}
        parts: list[pd.DataFrame] = []
        for chunk in pd.read_csv(dataset_path, chunksize=250_000, **read_kwargs):
            filtered = chunk.loc[chunk[GROUP_COLUMN].isin(city_id_set)].copy()
            if not filtered.empty:
                parts.append(filtered)
        return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=list(columns))

    if city_ids is None:
        return pd.read_parquet(dataset_path, columns=list(columns))
    filters = [(GROUP_COLUMN, "in", [int(city_id) for city_id in city_ids])]
    return pd.read_parquet(dataset_path, columns=list(columns), filters=filters)


def _sample_csv_rows_by_city(
    dataset_path: Path,
    columns: Sequence[str],
    city_ids: Sequence[int],
    sample_rows_per_city: int,
    random_state: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    city_id_set = {int(city_id) for city_id in city_ids}
    rng = np.random.default_rng(int(random_state))
    sampled_parts: dict[tuple[int, int], pd.DataFrame] = {}
    city_stats: dict[int, dict[str, object]] = {}

    for chunk in pd.read_csv(dataset_path, usecols=list(columns), chunksize=250_000):
        filtered = chunk.loc[chunk[GROUP_COLUMN].isin(city_id_set)].copy()
        if filtered.empty:
            continue

        normalized_target = normalize_binary_target(filtered[TARGET_COLUMN], column_name=TARGET_COLUMN)
        valid_mask = normalized_target.notna()
        filtered = filtered.loc[valid_mask].copy()
        if filtered.empty:
            continue
        filtered[TARGET_COLUMN] = normalized_target.loc[valid_mask].astype("int8")
        filtered["_sample_priority"] = rng.random(len(filtered))
        for city_id, city_chunk in filtered.groupby(GROUP_COLUMN, sort=False, dropna=False):
            normalized_city_id = int(city_id)
            city_summary = city_stats.setdefault(
                normalized_city_id,
                {
                    GROUP_COLUMN: normalized_city_id,
                    CITY_NAME_COLUMN: city_chunk[CITY_NAME_COLUMN].iloc[0] if CITY_NAME_COLUMN in city_chunk.columns else None,
                    "full_row_count": 0,
                    "full_positive_count": 0,
                },
            )
            city_summary["full_row_count"] = int(city_summary["full_row_count"]) + int(len(city_chunk))
            city_summary["full_positive_count"] = int(city_summary["full_positive_count"]) + int(
                city_chunk[TARGET_COLUMN].sum()
            )
            for target_value, target_chunk in city_chunk.groupby(TARGET_COLUMN, sort=False, dropna=False):
                key = (normalized_city_id, int(target_value))
                existing = sampled_parts.get(key)
                combined = target_chunk if existing is None else pd.concat([existing, target_chunk], ignore_index=True)
                sampled_parts[key] = combined.nsmallest(
                    int(sample_rows_per_city),
                    columns="_sample_priority",
                )

    final_parts: list[pd.DataFrame] = []
    diagnostic_rows: list[dict[str, object]] = []
    for city_id in [int(city_id) for city_id in city_ids]:
        city_summary = city_stats.get(city_id)
        if city_summary is None:
            continue
        positive_take, negative_take, strategy = _allocate_city_sample_sizes(
            full_row_count=int(city_summary["full_row_count"]),
            full_positive_count=int(city_summary["full_positive_count"]),
            sample_rows_per_city=int(sample_rows_per_city),
        )
        positive_reservoir = sampled_parts.get((city_id, 1))
        negative_reservoir = sampled_parts.get((city_id, 0))
        positive_sample = (
            positive_reservoir.nsmallest(positive_take, columns="_sample_priority")
            if positive_reservoir is not None and positive_take > 0
            else pd.DataFrame(columns=list(columns) + ["_sample_priority"])
        )
        negative_sample = (
            negative_reservoir.nsmallest(negative_take, columns="_sample_priority")
            if negative_reservoir is not None and negative_take > 0
            else pd.DataFrame(columns=list(columns) + ["_sample_priority"])
        )
        city_sample = pd.concat([positive_sample, negative_sample], ignore_index=True)
        if not city_sample.empty:
            final_parts.append(city_sample.drop(columns="_sample_priority").reset_index(drop=True))
        sampled_positive_count = int(city_sample[TARGET_COLUMN].sum()) if not city_sample.empty else 0
        sampled_row_count = int(len(city_sample))
        full_row_count = int(city_summary["full_row_count"])
        full_positive_count = int(city_summary["full_positive_count"])
        diagnostic_rows.append(
            {
                GROUP_COLUMN: city_id,
                CITY_NAME_COLUMN: city_summary.get(CITY_NAME_COLUMN),
                "sampling_strategy": strategy,
                "full_row_count": full_row_count,
                "full_positive_count": full_positive_count,
                "sampled_row_count": sampled_row_count,
                "sampled_positive_count": sampled_positive_count,
                "full_positive_rate": (full_positive_count / full_row_count) if full_row_count else np.nan,
                "sampled_positive_rate": (sampled_positive_count / sampled_row_count) if sampled_row_count else np.nan,
            }
        )

    sampled_df = pd.concat(final_parts, ignore_index=True) if final_parts else pd.DataFrame(columns=list(columns))
    diagnostics_df = pd.DataFrame(diagnostic_rows)
    if not diagnostics_df.empty:
        diagnostics_df = diagnostics_df.sort_values(GROUP_COLUMN).reset_index(drop=True)
    return sampled_df, diagnostics_df


def _allocate_city_sample_sizes(
    *,
    full_row_count: int,
    full_positive_count: int,
    sample_rows_per_city: int,
) -> tuple[int, int, str]:
    sample_size = min(int(sample_rows_per_city), int(full_row_count))
    if sample_size <= 0 or full_row_count <= 0:
        return 0, 0, "empty"

    full_negative_count = int(full_row_count) - int(full_positive_count)
    if full_positive_count <= 0 or full_negative_count <= 0:
        return min(sample_size, full_positive_count), min(sample_size, full_negative_count), "uniform_single_class"

    positive_take = int(round(sample_size * (full_positive_count / full_row_count)))
    positive_take = max(1, positive_take)
    negative_take = sample_size - positive_take
    if negative_take <= 0:
        negative_take = 1
        positive_take = sample_size - negative_take

    positive_take = min(positive_take, full_positive_count)
    negative_take = min(negative_take, full_negative_count)

    allocated = positive_take + negative_take
    if allocated < sample_size:
        remaining = sample_size - allocated
        positive_room = full_positive_count - positive_take
        take_more_positive = min(remaining, positive_room)
        positive_take += take_more_positive
        remaining -= take_more_positive
        negative_room = full_negative_count - negative_take
        negative_take += min(remaining, negative_room)

    return positive_take, negative_take, "target_rate_stratified"


def _sample_city_frame_with_diagnostics(
    city_df: pd.DataFrame,
    *,
    sample_rows_per_city: int,
    random_state: int,
) -> tuple[pd.DataFrame, dict[str, object]]:
    normalized_target = normalize_binary_target(city_df[TARGET_COLUMN], column_name=TARGET_COLUMN)
    valid_mask = normalized_target.notna()
    valid_city_df = city_df.loc[valid_mask].copy().reset_index(drop=True)
    valid_city_df[TARGET_COLUMN] = normalized_target.loc[valid_mask].astype("int8").reset_index(drop=True)
    if city_df.empty:
        return pd.DataFrame(columns=city_df.columns), {
            GROUP_COLUMN: np.nan,
            CITY_NAME_COLUMN: None,
            "sampling_strategy": "empty",
            "full_row_count": 0,
            "full_positive_count": 0,
            "sampled_row_count": 0,
            "sampled_positive_count": 0,
            "full_positive_rate": np.nan,
            "sampled_positive_rate": np.nan,
        }
    city_id = int(valid_city_df[GROUP_COLUMN].iloc[0]) if not valid_city_df.empty else int(city_df[GROUP_COLUMN].iloc[0])
    city_name = (
        valid_city_df[CITY_NAME_COLUMN].iloc[0]
        if CITY_NAME_COLUMN in valid_city_df.columns and not valid_city_df.empty
        else (city_df[CITY_NAME_COLUMN].iloc[0] if CITY_NAME_COLUMN in city_df.columns and not city_df.empty else None)
    )
    full_row_count = int(len(valid_city_df))
    full_positive_count = int(valid_city_df[TARGET_COLUMN].sum()) if full_row_count else 0

    if full_row_count <= int(sample_rows_per_city):
        sampled_df = valid_city_df.copy()
        strategy = "all_rows"
    else:
        positive_take, negative_take, strategy = _allocate_city_sample_sizes(
            full_row_count=full_row_count,
            full_positive_count=full_positive_count,
            sample_rows_per_city=int(sample_rows_per_city),
        )
        if strategy == "uniform_single_class":
            sampled_df = valid_city_df.sample(
                n=min(int(sample_rows_per_city), full_row_count),
                random_state=int(random_state) + city_id,
            )
        else:
            positives = valid_city_df.loc[valid_city_df[TARGET_COLUMN] == 1].sample(
                n=positive_take,
                random_state=int(random_state) + city_id,
            )
            negatives = valid_city_df.loc[valid_city_df[TARGET_COLUMN] == 0].sample(
                n=negative_take,
                random_state=int(random_state) + city_id + 10_000,
            )
            sampled_df = pd.concat([positives, negatives], ignore_index=True).sample(
                frac=1.0,
                random_state=int(random_state) + city_id + 20_000,
            )
    sampled_df = sampled_df.reset_index(drop=True)
    sampled_row_count = int(len(sampled_df))
    sampled_positive_count = int(sampled_df[TARGET_COLUMN].sum()) if sampled_row_count else 0
    diagnostics = {
        GROUP_COLUMN: city_id,
        CITY_NAME_COLUMN: city_name,
        "sampling_strategy": strategy,
        "full_row_count": full_row_count,
        "full_positive_count": full_positive_count,
        "sampled_row_count": sampled_row_count,
        "sampled_positive_count": sampled_positive_count,
        "full_positive_rate": (full_positive_count / full_row_count) if full_row_count else np.nan,
        "sampled_positive_rate": (sampled_positive_count / sampled_row_count) if sampled_row_count else np.nan,
    }
    return sampled_df, diagnostics


def load_sampled_modeling_rows_with_diagnostics(
    dataset_path: Path = DEFAULT_FINAL_DATASET_PATH,
    feature_columns: Sequence[str] | None = None,
    city_ids: Sequence[int] | None = None,
    sample_rows_per_city: int | None = None,
    random_state: int = 42,
    extra_columns: Sequence[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load a bounded per-city modeling sample plus per-city signal-preservation diagnostics."""
    if sample_rows_per_city is None:
        raise ValueError("sample_rows_per_city is required to build sampled modeling diagnostics")
    if city_ids is None:
        raise ValueError("sample_rows_per_city requires an explicit list of city_ids")

    resolved_dataset_path = dataset_path.resolve()
    if resolved_dataset_path.suffix.lower() == ".csv" and resolved_dataset_path not in _WARNED_CSV_DATASET_PATHS:
        LOGGER.warning(
            "Using CSV modeling input %s. CSV support is a compatibility fallback and must not be assumed row-equivalent to the canonical parquet without an explicit audit.",
            resolved_dataset_path,
        )
        _WARNED_CSV_DATASET_PATHS.add(resolved_dataset_path)

    available_columns = get_final_dataset_columns(dataset_path=dataset_path)
    validate_required_final_columns(available_columns)
    selected_columns = get_selected_modeling_columns(feature_columns=feature_columns, extra_columns=extra_columns)
    validate_model_feature_columns(
        feature_columns=DEFAULT_FEATURE_COLUMNS if feature_columns is None else feature_columns,
        available_columns=available_columns,
    )

    if dataset_path.suffix.lower() == ".csv":
        sampled_df, diagnostics_df = _sample_csv_rows_by_city(
            dataset_path=dataset_path,
            columns=selected_columns,
            city_ids=city_ids,
            sample_rows_per_city=int(sample_rows_per_city),
            random_state=int(random_state),
        )
        return sampled_df.reset_index(drop=True), diagnostics_df

    sampled_parts: list[pd.DataFrame] = []
    diagnostic_rows: list[dict[str, object]] = []
    for city_id in [int(value) for value in city_ids]:
        city_df = _read_dataset_subset(
            dataset_path=dataset_path,
            columns=selected_columns,
            city_ids=[city_id],
        )
        city_sample, diagnostics = _sample_city_frame_with_diagnostics(
            city_df=city_df,
            sample_rows_per_city=int(sample_rows_per_city),
            random_state=int(random_state),
        )
        if not city_sample.empty:
            sampled_parts.append(city_sample)
        diagnostic_rows.append(diagnostics)

    sampled_df = pd.concat(sampled_parts, ignore_index=True) if sampled_parts else pd.DataFrame(columns=selected_columns)
    diagnostics_df = pd.DataFrame(diagnostic_rows)
    if not diagnostics_df.empty:
        diagnostics_df = diagnostics_df.sort_values(GROUP_COLUMN).reset_index(drop=True)
    return sampled_df, diagnostics_df


def load_modeling_rows(
    dataset_path: Path = DEFAULT_FINAL_DATASET_PATH,
    feature_columns: Sequence[str] | None = None,
    city_ids: Sequence[int] | None = None,
    sample_rows_per_city: int | None = None,
    random_state: int = 42,
    extra_columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Load modeling rows from the canonical parquet path or an explicit CSV fallback path."""
    resolved_dataset_path = dataset_path.resolve()
    if resolved_dataset_path.suffix.lower() == ".csv" and resolved_dataset_path not in _WARNED_CSV_DATASET_PATHS:
        LOGGER.warning(
            "Using CSV modeling input %s. CSV support is a compatibility fallback and must not be assumed row-equivalent to the canonical parquet without an explicit audit.",
            resolved_dataset_path,
        )
        _WARNED_CSV_DATASET_PATHS.add(resolved_dataset_path)

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
        df, _ = load_sampled_modeling_rows_with_diagnostics(
            dataset_path=dataset_path,
            feature_columns=feature_columns,
            city_ids=city_ids,
            sample_rows_per_city=sample_rows_per_city,
            random_state=random_state,
            extra_columns=extra_columns,
        )

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
