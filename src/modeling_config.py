from __future__ import annotations

from pathlib import Path
from typing import Sequence

from src.config import FINAL, MODELING, MODELING_FIGURES, MODELING_OUTPUTS

TARGET_COLUMN = "hotspot_10pct"
GROUP_COLUMN = "city_id"
CITY_NAME_COLUMN = "city_name"
FOLD_COLUMN = "outer_fold"

FEATURE_TYPE_NUMERIC = "numeric"
FEATURE_TYPE_CATEGORICAL = "categorical"

MODEL_FEATURE_TYPES = {
    "impervious_pct": FEATURE_TYPE_NUMERIC,
    "elevation_m": FEATURE_TYPE_NUMERIC,
    "dist_to_water_m": FEATURE_TYPE_NUMERIC,
    "ndvi_median_may_aug": FEATURE_TYPE_NUMERIC,
    "land_cover_class": FEATURE_TYPE_CATEGORICAL,
    "climate_group": FEATURE_TYPE_CATEGORICAL,
}

NUMERIC_FEATURE_COLUMNS = [
    column_name for column_name, feature_type in MODEL_FEATURE_TYPES.items() if feature_type == FEATURE_TYPE_NUMERIC
]
CATEGORICAL_FEATURE_COLUMNS = [
    column_name for column_name, feature_type in MODEL_FEATURE_TYPES.items() if feature_type == FEATURE_TYPE_CATEGORICAL
]
DEFAULT_FEATURE_COLUMNS = list(MODEL_FEATURE_TYPES)

EXCLUDED_FEATURE_COLUMNS = [
    TARGET_COLUMN,
    "lst_median_may_aug",
    "n_valid_ecostress_passes",
    "cell_id",
    GROUP_COLUMN,
    CITY_NAME_COLUMN,
    "centroid_lon",
    "centroid_lat",
]

IDENTIFIER_COLUMNS = [
    GROUP_COLUMN,
    CITY_NAME_COLUMN,
    "climate_group",
    "cell_id",
    "centroid_lon",
    "centroid_lat",
]

DEFAULT_FINAL_DATASET_PATH = FINAL / "final_dataset.parquet"
DEFAULT_FOLDS_PARQUET_PATH = MODELING / "city_outer_folds.parquet"
DEFAULT_FOLDS_CSV_PATH = MODELING / "city_outer_folds.csv"

BASELINE_OUTPUT_DIR = MODELING_OUTPUTS / "baselines"
LOGISTIC_OUTPUT_DIR = MODELING_OUTPUTS / "logistic_saga"
RANDOM_FOREST_OUTPUT_DIR = MODELING_OUTPUTS / "random_forest"
MODELING_FIGURE_ROOT = MODELING_FIGURES

DEFAULT_PR_SCORING = "average_precision"
DEFAULT_TOP_FRACTION = 0.10
DEFAULT_RANDOM_STATE = 42
DEFAULT_INNER_CV_SPLITS = 4
DEFAULT_CALIBRATION_BINS = 10

LOGISTIC_PARAM_GRID = [
    {
        "model__penalty": ["l2"],
        "model__C": [0.01, 0.1, 1.0, 10.0],
    },
    {
        "model__penalty": ["l1"],
        "model__C": [0.01, 0.1, 1.0, 10.0],
    },
    {
        "model__penalty": ["elasticnet"],
        "model__C": [0.01, 0.1, 1.0, 10.0],
        "model__l1_ratio": [0.2, 0.5, 0.8],
    },
]

RANDOM_FOREST_PARAM_GRID = [
    {
        "model__n_estimators": [100, 300, 500],
        "model__max_depth": [10, 20, None],
        "model__max_features": ["sqrt", 0.5, None],
        "model__min_samples_leaf": [1, 5, 10],
    }
]


def get_first_pass_feature_columns() -> list[str]:
    """Return the initial leakage-safe modeling feature set."""
    return list(DEFAULT_FEATURE_COLUMNS)


def get_feature_type_map(feature_columns: Sequence[str] | None = None) -> dict[str, str]:
    """Return the explicit modeling feature-type contract for the selected columns."""
    selected_columns = DEFAULT_FEATURE_COLUMNS if feature_columns is None else list(feature_columns)
    return {column_name: MODEL_FEATURE_TYPES[column_name] for column_name in selected_columns}


def split_model_feature_columns(feature_columns: Sequence[str]) -> tuple[list[str], list[str]]:
    """Split selected modeling features into numeric and categorical groups from the shared contract."""
    feature_type_map = get_feature_type_map(feature_columns)
    numeric_columns = [
        column_name
        for column_name in feature_columns
        if feature_type_map[column_name] == FEATURE_TYPE_NUMERIC
    ]
    categorical_columns = [
        column_name
        for column_name in feature_columns
        if feature_type_map[column_name] == FEATURE_TYPE_CATEGORICAL
    ]
    return numeric_columns, categorical_columns


def get_prediction_output_columns() -> list[str]:
    """Return the identifier columns saved with held-out predictions."""
    return list(IDENTIFIER_COLUMNS)


def get_default_output_dir(model_name: str) -> Path:
    """Return the standard output root for a named modeling stage."""
    if model_name == "baselines":
        return BASELINE_OUTPUT_DIR
    if model_name == "logistic_saga":
        return LOGISTIC_OUTPUT_DIR
    if model_name == "random_forest":
        return RANDOM_FOREST_OUTPUT_DIR
    return MODELING_OUTPUTS / model_name
