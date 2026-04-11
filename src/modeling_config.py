from __future__ import annotations

from dataclasses import dataclass
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
DEFAULT_LOGISTIC_MAX_ITER = 4000
DEFAULT_LOGISTIC_TOL = 5e-4
DEFAULT_INNER_CV_SPLITS = 4
SMOKE_INNER_CV_SPLITS = 3
DEFAULT_CALIBRATION_BINS = 10
TUNING_PRESET_SMOKE = "smoke"
TUNING_PRESET_FRONTIER = "frontier"
TUNING_PRESET_FULL = "full"
DEFAULT_TUNING_PRESET = TUNING_PRESET_SMOKE
VALID_TUNING_PRESETS = (TUNING_PRESET_SMOKE, TUNING_PRESET_FRONTIER, TUNING_PRESET_FULL)

# sklearn 1.8 deprecates explicit LogisticRegression penalty values. When penalty
# is left at its default sentinel, l1_ratio selects the effective family:
#   0.0 -> l2
#   1.0 -> l1
#   0 < l1_ratio < 1 -> elasticnet
LOGISTIC_L2_RATIO = 0.0
LOGISTIC_L1_RATIO = 1.0

LOGISTIC_SMOKE_PARAM_GRID = [
    {
        "model__C": [0.1, 1.0],
        "model__l1_ratio": [LOGISTIC_L2_RATIO],
    },
    {
        "model__C": [1.0],
        "model__l1_ratio": [LOGISTIC_L1_RATIO],
    },
    {
        "model__C": [1.0],
        "model__l1_ratio": [0.5],
    },
]
LOGISTIC_FULL_PARAM_GRID = [
    {
        "model__C": [0.01, 0.1, 1.0, 10.0],
        "model__l1_ratio": [LOGISTIC_L2_RATIO],
    },
    {
        "model__C": [0.01, 0.1, 1.0, 10.0],
        "model__l1_ratio": [LOGISTIC_L1_RATIO],
    },
    {
        "model__C": [0.01, 0.1, 1.0, 10.0],
        "model__l1_ratio": [0.2, 0.5, 0.8],
    },
]
LOGISTIC_PARAM_GRID = LOGISTIC_SMOKE_PARAM_GRID

RANDOM_FOREST_SMOKE_PARAM_GRID = [
    {
        "model__n_estimators": [200],
        "model__max_depth": [10, None],
        "model__max_features": ["sqrt"],
        "model__min_samples_leaf": [1, 5],
    }
]
RANDOM_FOREST_FRONTIER_INNER_CV_SPLITS = SMOKE_INNER_CV_SPLITS
RANDOM_FOREST_FRONTIER_PARAM_GRID = [
    {
        "model__n_estimators": [200, 300],
        "model__max_depth": [10, 20],
        "model__max_features": ["sqrt"],
        "model__min_samples_leaf": [1, 5],
    }
]
RANDOM_FOREST_FULL_PARAM_GRID = [
    {
        "model__n_estimators": [100, 300, 500],
        "model__max_depth": [10, 20, None],
        "model__max_features": ["sqrt", 0.5, None],
        "model__min_samples_leaf": [1, 5, 10],
    }
]
RANDOM_FOREST_PARAM_GRID = RANDOM_FOREST_SMOKE_PARAM_GRID


@dataclass(frozen=True)
class ModelTuningSpec:
    preset_name: str
    inner_cv_splits: int
    param_grid: list[dict[str, object]]


def get_valid_tuning_presets(model_name: str) -> tuple[str, ...]:
    """Return the supported tuning presets for one model family."""
    normalized_model_name = model_name.strip().lower()
    if normalized_model_name == "logistic_saga":
        return (TUNING_PRESET_SMOKE, TUNING_PRESET_FULL)
    if normalized_model_name == "random_forest":
        return (TUNING_PRESET_SMOKE, TUNING_PRESET_FRONTIER, TUNING_PRESET_FULL)
    raise ValueError(f"Unsupported tuning-preset request for model family: {model_name}")


def get_tuning_preset_help_text(model_name: str) -> str:
    """Return model-specific CLI help text for staged tuning presets."""
    normalized_model_name = model_name.strip().lower()
    if normalized_model_name == "logistic_saga":
        return "Use 'smoke' for the bounded default verification search or 'full' for the broader tuning search."
    if normalized_model_name == "random_forest":
        return (
            "Use 'smoke' for the bounded default verification path and cheap nonlinear comparison against logistic, "
            "'frontier' for a targeted follow-up search around the promising RF region, or 'full' for expensive "
            "confirmation only after earlier RF stages justify it."
        )
    raise ValueError(f"Unsupported tuning-preset help request for model family: {model_name}")


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


def get_model_tuning_spec(model_name: str, preset_name: str = DEFAULT_TUNING_PRESET) -> ModelTuningSpec:
    """Return the tuning search-space preset for a supported model."""
    normalized_model_name = model_name.strip().lower()
    normalized_preset = preset_name.strip().lower()
    valid_presets = get_valid_tuning_presets(normalized_model_name)
    if normalized_preset not in valid_presets:
        valid_text = ", ".join(valid_presets)
        raise ValueError(f"Unsupported tuning preset '{preset_name}'. Expected one of: {valid_text}")

    if normalized_model_name == "logistic_saga":
        if normalized_preset == TUNING_PRESET_SMOKE:
            return ModelTuningSpec(
                preset_name=normalized_preset,
                inner_cv_splits=SMOKE_INNER_CV_SPLITS,
                param_grid=list(LOGISTIC_SMOKE_PARAM_GRID),
            )
        return ModelTuningSpec(
            preset_name=normalized_preset,
            inner_cv_splits=DEFAULT_INNER_CV_SPLITS,
            param_grid=list(LOGISTIC_FULL_PARAM_GRID),
        )

    if normalized_model_name == "random_forest":
        if normalized_preset == TUNING_PRESET_SMOKE:
            return ModelTuningSpec(
                preset_name=normalized_preset,
                inner_cv_splits=SMOKE_INNER_CV_SPLITS,
                param_grid=list(RANDOM_FOREST_SMOKE_PARAM_GRID),
            )
        if normalized_preset == TUNING_PRESET_FRONTIER:
            return ModelTuningSpec(
                preset_name=normalized_preset,
                inner_cv_splits=RANDOM_FOREST_FRONTIER_INNER_CV_SPLITS,
                param_grid=list(RANDOM_FOREST_FRONTIER_PARAM_GRID),
            )
        return ModelTuningSpec(
            preset_name=normalized_preset,
            inner_cv_splits=DEFAULT_INNER_CV_SPLITS,
            param_grid=list(RANDOM_FOREST_FULL_PARAM_GRID),
        )

    raise ValueError(f"Unsupported model tuning spec request: {model_name}")


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
