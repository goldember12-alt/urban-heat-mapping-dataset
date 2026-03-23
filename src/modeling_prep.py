from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
import pyarrow.parquet as pq

from src.config import FINAL, MODELING
from src.feature_assembly import FINAL_COLUMNS

logger = logging.getLogger(__name__)

DEFAULT_TARGET_COLUMN = "hotspot_10pct"
DEFAULT_GROUP_COLUMN = "city_id"
DEFAULT_FEATURE_COLUMNS = [
    "impervious_pct",
    "land_cover_class",
    "elevation_m",
    "dist_to_water_m",
    "ndvi_median_may_aug",
    "climate_group",
]
DEFAULT_EXCLUDED_COLUMNS = [
    "hotspot_10pct",
    "lst_median_may_aug",
    "cell_id",
    "city_id",
    "city_name",
    "centroid_lon",
    "centroid_lat",
    "n_valid_ecostress_passes",
]


@dataclass(frozen=True)
class FinalDatasetAuditResult:
    dataset_path: Path
    row_count: int
    city_count: int
    city_summary_csv_path: Path
    missingness_csv_path: Path
    missingness_by_city_csv_path: Path
    summary_json_path: Path
    summary_markdown_path: Path


@dataclass(frozen=True)
class ModelFoldResult:
    dataset_path: Path
    n_rows: int
    n_cities: int
    fold_table: pd.DataFrame
    parquet_path: Path
    csv_path: Path


def _deduplicate_columns(columns: Iterable[str]) -> list[str]:
    """Return columns in first-seen order without duplicates."""
    return list(dict.fromkeys(columns))


def get_final_dataset_columns(dataset_path: Path = FINAL / "final_dataset.parquet") -> list[str]:
    """Read parquet schema column names without materializing the full dataset."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Final dataset not found: {dataset_path}")
    return list(pq.read_schema(dataset_path).names)


def load_final_dataset(
    dataset_path: Path = FINAL / "final_dataset.parquet",
    columns: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Load the canonical merged final dataset."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Final dataset not found: {dataset_path}")
    selected_columns = _deduplicate_columns(columns) if columns is not None else None
    if selected_columns is None:
        logger.info("Loading final dataset from %s", dataset_path)
    else:
        logger.info("Loading %s selected columns from %s", len(selected_columns), dataset_path)
    return pd.read_parquet(dataset_path, columns=selected_columns)


def validate_required_final_columns(
    df_or_columns: pd.DataFrame | Iterable[str],
    required_columns: Iterable[str] = FINAL_COLUMNS,
) -> None:
    """Raise when the final dataset is missing required contract columns."""
    available_columns = df_or_columns.columns if isinstance(df_or_columns, pd.DataFrame) else df_or_columns
    missing_columns = sorted(set(required_columns) - set(available_columns))
    if missing_columns:
        raise ValueError(f"Final dataset missing required columns: {', '.join(missing_columns)}")


def validate_binary_target(df: pd.DataFrame, target_column: str = DEFAULT_TARGET_COLUMN) -> None:
    """Raise when the target column contains non-binary non-null values."""
    if target_column not in df.columns:
        raise ValueError(f"Target column not found: {target_column}")

    normalized_values: set[int] = set()
    invalid_values: set[str] = set()

    for raw_value in df[target_column].dropna().tolist():
        if isinstance(raw_value, str):
            value = raw_value.strip().lower()
            if value in {"0", "false"}:
                normalized_values.add(0)
                continue
            if value in {"1", "true"}:
                normalized_values.add(1)
                continue
            invalid_values.add(str(raw_value))
            continue

        try:
            numeric = float(raw_value)
        except (TypeError, ValueError):
            invalid_values.add(str(raw_value))
            continue

        if numeric in (0.0, 1.0):
            normalized_values.add(int(numeric))
            continue

        invalid_values.add(str(raw_value))

    if invalid_values:
        invalid_text = ", ".join(sorted(invalid_values))
        raise ValueError(f"Target column {target_column} must be binary. Found non-binary values: {invalid_text}")

    if not normalized_values:
        logger.warning("Target column %s contains only missing values in the current dataset", target_column)


def summarize_feature_missingness(
    df: pd.DataFrame,
    feature_columns: Iterable[str] = DEFAULT_FEATURE_COLUMNS,
) -> pd.DataFrame:
    """Summarize missingness for candidate modeling features across the full dataset."""
    records: list[dict[str, object]] = []
    n_rows = len(df)

    for column in feature_columns:
        if column not in df.columns:
            records.append(
                {
                    "column": column,
                    "present_in_dataset": False,
                    "non_missing_count": 0,
                    "missing_count": n_rows,
                    "missing_pct": 1.0 if n_rows else 0.0,
                    "dtype": "",
                }
            )
            continue

        missing_count = int(df[column].isna().sum())
        records.append(
            {
                "column": column,
                "present_in_dataset": True,
                "non_missing_count": int(n_rows - missing_count),
                "missing_count": missing_count,
                "missing_pct": float(missing_count / n_rows) if n_rows else 0.0,
                "dtype": str(df[column].dtype),
            }
        )

    return pd.DataFrame(records)


def summarize_feature_missingness_by_city(
    df: pd.DataFrame,
    feature_columns: Iterable[str] = DEFAULT_FEATURE_COLUMNS,
    group_column: str = DEFAULT_GROUP_COLUMN,
) -> pd.DataFrame:
    """Summarize candidate-feature missingness within each city."""
    if group_column not in df.columns:
        raise ValueError(f"Grouping column not found: {group_column}")

    city_name_column = "city_name" if "city_name" in df.columns else None
    records: list[dict[str, object]] = []

    for city_id, city_df in df.groupby(group_column, sort=True, dropna=False):
        city_name = city_df[city_name_column].iloc[0] if city_name_column else ""
        n_rows = len(city_df)
        for column in feature_columns:
            if column not in city_df.columns:
                missing_count = n_rows
                present = False
                dtype = ""
            else:
                missing_count = int(city_df[column].isna().sum())
                present = True
                dtype = str(city_df[column].dtype)
            records.append(
                {
                    group_column: city_id,
                    "city_name": city_name,
                    "column": column,
                    "present_in_dataset": present,
                    "non_missing_count": int(n_rows - missing_count),
                    "missing_count": missing_count,
                    "missing_pct": float(missing_count / n_rows) if n_rows else 0.0,
                    "dtype": dtype,
                }
            )

    return pd.DataFrame(records)


def summarize_by_city(
    df: pd.DataFrame,
    target_column: str = DEFAULT_TARGET_COLUMN,
    group_column: str = DEFAULT_GROUP_COLUMN,
) -> pd.DataFrame:
    """Summarize per-city row counts, target prevalence, and ECOSTRESS pass counts."""
    if group_column not in df.columns:
        raise ValueError(f"Grouping column not found: {group_column}")

    city_name_column = "city_name" if "city_name" in df.columns else None
    climate_column = "climate_group" if "climate_group" in df.columns else None
    pass_column = "n_valid_ecostress_passes" if "n_valid_ecostress_passes" in df.columns else None
    rows: list[dict[str, object]] = []

    for city_id, city_df in df.groupby(group_column, sort=True, dropna=False):
        city_name = city_df[city_name_column].iloc[0] if city_name_column else ""
        climate_group = city_df[climate_column].iloc[0] if climate_column else ""

        if target_column in city_df.columns:
            target_series = pd.to_numeric(city_df[target_column], errors="coerce")
            hotspot_non_missing = int(target_series.notna().sum())
            hotspot_positive_count = int(target_series.fillna(0).sum())
            hotspot_prevalence = float(target_series.mean()) if hotspot_non_missing else None
        else:
            hotspot_non_missing = 0
            hotspot_positive_count = 0
            hotspot_prevalence = None

        if pass_column:
            pass_series = pd.to_numeric(city_df[pass_column], errors="coerce")
            pass_non_missing = int(pass_series.notna().sum())
            pass_min = float(pass_series.min()) if pass_non_missing else None
            pass_median = float(pass_series.median()) if pass_non_missing else None
            pass_mean = float(pass_series.mean()) if pass_non_missing else None
            pass_max = float(pass_series.max()) if pass_non_missing else None
        else:
            pass_non_missing = 0
            pass_min = None
            pass_median = None
            pass_mean = None
            pass_max = None

        rows.append(
            {
                group_column: city_id,
                "city_name": city_name,
                "climate_group": climate_group,
                "row_count": int(len(city_df)),
                "hotspot_positive_count": hotspot_positive_count,
                "hotspot_non_missing_count": hotspot_non_missing,
                "hotspot_prevalence": hotspot_prevalence,
                "n_valid_ecostress_passes_non_missing_count": pass_non_missing,
                "n_valid_ecostress_passes_min": pass_min,
                "n_valid_ecostress_passes_median": pass_median,
                "n_valid_ecostress_passes_mean": pass_mean,
                "n_valid_ecostress_passes_max": pass_max,
            }
        )

    return pd.DataFrame(rows).sort_values(group_column).reset_index(drop=True)


def audit_final_dataset(
    dataset_path: Path = FINAL / "final_dataset.parquet",
    output_dir: Path = MODELING,
    feature_columns: Iterable[str] = DEFAULT_FEATURE_COLUMNS,
    target_column: str = DEFAULT_TARGET_COLUMN,
    group_column: str = DEFAULT_GROUP_COLUMN,
) -> FinalDatasetAuditResult:
    """Validate and summarize the canonical final dataset for modeling handoff."""
    available_columns = get_final_dataset_columns(dataset_path=dataset_path)
    validate_required_final_columns(available_columns)

    selected_columns = _deduplicate_columns(
        [
            group_column,
            "city_name",
            "climate_group",
            "n_valid_ecostress_passes",
            target_column,
            *feature_columns,
        ]
    )
    df = load_final_dataset(dataset_path=dataset_path, columns=selected_columns)
    validate_binary_target(df, target_column=target_column)

    feature_columns = list(feature_columns)
    output_dir.mkdir(parents=True, exist_ok=True)

    city_summary = summarize_by_city(df, target_column=target_column, group_column=group_column)
    missingness = summarize_feature_missingness(df, feature_columns=feature_columns)
    missingness_by_city = summarize_feature_missingness_by_city(
        df,
        feature_columns=feature_columns,
        group_column=group_column,
    )

    city_summary_csv_path = output_dir / "final_dataset_city_summary.csv"
    missingness_csv_path = output_dir / "final_dataset_feature_missingness.csv"
    missingness_by_city_csv_path = output_dir / "final_dataset_feature_missingness_by_city.csv"
    summary_json_path = output_dir / "final_dataset_audit_summary.json"
    summary_markdown_path = output_dir / "final_dataset_audit.md"

    city_summary.to_csv(city_summary_csv_path, index=False)
    missingness.to_csv(missingness_csv_path, index=False)
    missingness_by_city.to_csv(missingness_by_city_csv_path, index=False)

    hotspot_series = pd.to_numeric(df[target_column], errors="coerce") if target_column in df.columns else pd.Series(dtype="float64")
    summary_payload = {
        "generated_at_utc": pd.Timestamp.now("UTC").isoformat(),
        "dataset_path": str(dataset_path),
        "row_count": int(len(df)),
        "city_count": int(df[group_column].nunique(dropna=True)),
        "required_columns_present": True,
        "feature_columns_audited": feature_columns,
        "target_column": target_column,
        "target_is_binary": True,
        "hotspot_value_counts": {
            "0": int((hotspot_series == 0).sum()),
            "1": int((hotspot_series == 1).sum()),
            "missing": int(hotspot_series.isna().sum()),
        },
        "output_files": {
            "city_summary_csv": str(city_summary_csv_path),
            "feature_missingness_csv": str(missingness_csv_path),
            "feature_missingness_by_city_csv": str(missingness_by_city_csv_path),
            "summary_markdown": str(summary_markdown_path),
        },
    }
    summary_json_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")

    lines = [
        "# Final Dataset Audit",
        "",
        f"- Dataset path: `{dataset_path}`",
        f"- Row count: `{len(df):,}`",
        f"- City count: `{int(df[group_column].nunique(dropna=True))}`",
        f"- Required columns present: `True`",
        f"- Target column: `{target_column}`",
        f"- Target binary validation: `passed`",
        f"- Candidate feature columns audited: `{', '.join(feature_columns)}`",
        "",
        "## Saved Outputs",
        "",
        f"- `{city_summary_csv_path}`",
        f"- `{missingness_csv_path}`",
        f"- `{missingness_by_city_csv_path}`",
        f"- `{summary_json_path}`",
    ]
    summary_markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    logger.info("Saved final-dataset audit summary: %s", summary_json_path)
    logger.info("Saved per-city audit summary: %s", city_summary_csv_path)
    logger.info("Saved feature missingness summary: %s", missingness_csv_path)
    logger.info("Saved per-city feature missingness summary: %s", missingness_by_city_csv_path)

    return FinalDatasetAuditResult(
        dataset_path=dataset_path,
        row_count=int(len(df)),
        city_count=int(df[group_column].nunique(dropna=True)),
        city_summary_csv_path=city_summary_csv_path,
        missingness_csv_path=missingness_csv_path,
        missingness_by_city_csv_path=missingness_by_city_csv_path,
        summary_json_path=summary_json_path,
        summary_markdown_path=summary_markdown_path,
    )


def build_city_fold_table(
    df: pd.DataFrame,
    n_splits: int = 5,
    group_column: str = DEFAULT_GROUP_COLUMN,
    target_column: str = DEFAULT_TARGET_COLUMN,
) -> pd.DataFrame:
    """Assign each city to one deterministic outer fold using greedy row-count balancing."""
    if n_splits < 2:
        raise ValueError("n_splits must be at least 2")
    if group_column not in df.columns:
        raise ValueError(f"Grouping column not found: {group_column}")

    city_summary = summarize_by_city(df, target_column=target_column, group_column=group_column)
    n_cities = len(city_summary)
    if n_splits > n_cities:
        raise ValueError(f"n_splits={n_splits} exceeds available city count={n_cities}")

    working = city_summary.sort_values(["row_count", group_column], ascending=[False, True]).reset_index(drop=True)
    fold_row_totals = [0] * n_splits
    fold_city_totals = [0] * n_splits
    assignments: list[int] = []

    for row in working.itertuples(index=False):
        candidate_fold = min(
            range(n_splits),
            key=lambda fold_idx: (fold_row_totals[fold_idx], fold_city_totals[fold_idx], fold_idx),
        )
        fold_row_totals[candidate_fold] += int(row.row_count)
        fold_city_totals[candidate_fold] += 1
        assignments.append(candidate_fold)

    working["outer_fold"] = assignments
    return working.sort_values(group_column).reset_index(drop=True)


def make_model_folds(
    dataset_path: Path = FINAL / "final_dataset.parquet",
    output_dir: Path = MODELING,
    n_splits: int = 5,
    group_column: str = DEFAULT_GROUP_COLUMN,
    target_column: str = DEFAULT_TARGET_COLUMN,
) -> ModelFoldResult:
    """Create a deterministic city-level outer-fold assignment artifact."""
    available_columns = get_final_dataset_columns(dataset_path=dataset_path)
    validate_required_final_columns(available_columns)

    selected_columns = _deduplicate_columns(
        [
            group_column,
            "city_name",
            "climate_group",
            "n_valid_ecostress_passes",
            target_column,
        ]
    )
    df = load_final_dataset(dataset_path=dataset_path, columns=selected_columns)
    validate_binary_target(df, target_column=target_column)

    output_dir.mkdir(parents=True, exist_ok=True)
    fold_table = build_city_fold_table(
        df,
        n_splits=n_splits,
        group_column=group_column,
        target_column=target_column,
    )

    parquet_path = output_dir / "city_outer_folds.parquet"
    csv_path = output_dir / "city_outer_folds.csv"
    fold_table.to_parquet(parquet_path, index=False)
    fold_table.to_csv(csv_path, index=False)

    logger.info("Saved city-level fold assignments parquet: %s", parquet_path)
    logger.info("Saved city-level fold assignments csv: %s", csv_path)

    return ModelFoldResult(
        dataset_path=dataset_path,
        n_rows=int(len(df)),
        n_cities=int(fold_table[group_column].nunique(dropna=True)),
        fold_table=fold_table,
        parquet_path=parquet_path,
        csv_path=csv_path,
    )
