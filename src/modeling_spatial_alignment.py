from __future__ import annotations

import json
import logging
import math
import re
import warnings
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Sequence

import numpy as np
import pandas as pd
from pyproj import CRS, Transformer
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree
from scipy.stats import ConstantInputWarning, spearmanr
from sklearn.metrics import get_scorer
from sklearn.model_selection import GridSearchCV, GroupKFold

from src.config import MODELING_OUTPUTS, MODELING_SUPPLEMENTAL_FIGURES, MODELING_SUPPLEMENTAL_OUTPUTS
from src.modeling_config import (
    CITY_NAME_COLUMN,
    DEFAULT_FEATURE_COLUMNS,
    DEFAULT_FINAL_DATASET_PATH,
    DEFAULT_FOLDS_PARQUET_PATH,
    DEFAULT_PR_SCORING,
    DEFAULT_RANDOM_STATE,
    DEFAULT_TOP_FRACTION,
    FOLD_COLUMN,
    GROUP_COLUMN,
    TARGET_COLUMN,
    get_model_tuning_spec,
)
from src.modeling_data import (
    drop_missing_target_rows,
    load_city_outer_folds,
    load_modeling_rows,
    load_sampled_modeling_rows_with_diagnostics,
    validate_model_feature_columns,
)
from src.modeling_prep import get_final_dataset_columns, validate_required_final_columns
from src.modeling_runner import build_random_forest_pipeline

LOGGER = logging.getLogger(__name__)

DEFAULT_REFERENCE_RUN_DIR = (
    MODELING_OUTPUTS / "random_forest" / "frontier_allfolds_s5000_frontier-check_2026-04-11_173430"
)
DEFAULT_SPATIAL_ALIGNMENT_OUTPUT_DIR = MODELING_SUPPLEMENTAL_OUTPUTS / "spatial_alignment"
DEFAULT_SPATIAL_ALIGNMENT_FIGURE_DIR = MODELING_SUPPLEMENTAL_FIGURES / "spatial_alignment"
DEFAULT_SMOOTHING_RADII_M = (150.0, 300.0, 600.0)
DEFAULT_PREDICTION_BATCH_SIZE = 250_000
PREDICTION_SCOPE_FULL_CITY = "full_city"

REQUIRED_PREDICTION_COLUMNS = [
    GROUP_COLUMN,
    CITY_NAME_COLUMN,
    "climate_group",
    FOLD_COLUMN,
    "cell_id",
    "centroid_lon",
    "centroid_lat",
    TARGET_COLUMN,
    "model_name",
    "predicted_probability",
    "prediction_scope",
    "training_sample_rows_per_city",
    "source_reference_run_dir",
]

METRICS_COLUMNS = [
    GROUP_COLUMN,
    CITY_NAME_COLUMN,
    "climate_group",
    FOLD_COLUMN,
    "model_name",
    "source_reference_run_dir",
    "training_sample_rows_per_city",
    "prediction_scope",
    "row_count",
    "valid_cell_count",
    "scale_label",
    "smoothing_radius_m",
    "smoothing_method",
    "smoothing_sigma_m",
    "threshold_fraction",
    "spearman_surface_corr",
    "top_region_overlap_fraction",
    "observed_mass_captured",
    "centroid_distance_m",
    "median_nearest_region_distance_m",
    "observed_top_cell_count",
    "predicted_top_cell_count",
    "overlap_cell_count",
    "grid_cell_size_m",
    "projected_crs",
    "grid_reconstruction_status",
]

MAP_MANIFEST_COLUMNS = [
    GROUP_COLUMN,
    CITY_NAME_COLUMN,
    "climate_group",
    FOLD_COLUMN,
    "model_name",
    "scale_label",
    "smoothing_radius_m",
    "smoothing_method",
    "smoothing_sigma_m",
    "threshold_fraction",
    "row_count",
    "valid_cell_count",
    "grid_cell_size_m",
    "projected_crs",
    "grid_reconstruction_status",
    "prediction_path",
    "figure_path",
]


@dataclass(frozen=True)
class SpatialAlignmentResult:
    """Paths written by the supplemental spatial-alignment workflow."""

    output_dir: Path
    selection_table_path: Path
    metrics_table_path: Path
    summary_markdown_path: Path
    prediction_paths: tuple[Path, ...]
    map_manifest_table_path: Path | None = None
    map_paths: tuple[Path, ...] = ()


@dataclass(frozen=True)
class GridReconstruction:
    """Raster-like city grid reconstructed from projected cell centroids."""

    x_m: np.ndarray
    y_m: np.ndarray
    row_index: np.ndarray
    col_index: np.ndarray
    shape: tuple[int, int]
    valid_mask: np.ndarray
    observed: np.ndarray
    predicted: np.ndarray
    grid_cell_size_m: float
    projected_crs: str
    status: str


@dataclass(frozen=True)
class MapSurfaceBundle:
    """Smoothed surfaces and top-region masks used by maps and map manifests."""

    grid: GridReconstruction
    observed_surface: np.ndarray
    predicted_surface: np.ndarray
    observed_top_mask: np.ndarray
    predicted_top_mask: np.ndarray
    overlap_category: np.ndarray
    x_grid: np.ndarray
    y_grid: np.ndarray
    radius_m: float
    sigma_m: float
    scale_label: str


def _slugify(value: object) -> str:
    text = str(value).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "city"


def _read_reference_metadata(reference_run_dir: Path) -> dict[str, object]:
    metadata_path = reference_run_dir / "run_metadata.json"
    if not metadata_path.exists():
        return {}
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def _normalize_reference_run_dir(reference_run_dir: Path) -> Path:
    return reference_run_dir.resolve()


def _scale_label(radius_m: float) -> str:
    rounded = int(round(float(radius_m)))
    if rounded == 150:
        return "fine"
    if rounded == 300:
        return "medium"
    if rounded == 600:
        return "broad"
    return f"r{rounded}m"


def _radius_for_scale_label(scale_label: str) -> float:
    normalized_label = scale_label.strip().lower()
    if normalized_label == "medium":
        return 300.0
    raise ValueError("Only medium spatial-alignment maps are implemented in this pass")


def _table_filenames_for_selection(city_selection: str, city_ids: Sequence[int] | None) -> tuple[str, str]:
    normalized_selection = city_selection.strip().lower()
    if city_ids is None and normalized_selection == "all":
        return ("all_city_selection.csv", "spatial_alignment_metrics_all_cities.csv")
    return ("representative_city_selection.csv", "spatial_alignment_metrics_representative_cities.csv")


def _scope_note_for_selection(city_selection: str, city_ids: Sequence[int] | None) -> str:
    normalized_selection = city_selection.strip().lower()
    if city_ids is None and normalized_selection == "all":
        return (
            "supplemental all-city full-city spatial placement diagnostics; "
            "not a new canonical benchmark and not a replacement for retained sampled "
            "held-out-city PR AUC / recall results"
        )
    return (
        "supplemental representative-city full-city scoring; not a full 30-city benchmark "
        "and not a replacement for retained sampled held-out-city PR AUC / recall results"
    )


def _utm_crs_from_lon_lat(lon: float, lat: float) -> CRS:
    zone = int(math.floor((float(lon) + 180.0) / 6.0) + 1)
    zone = min(max(zone, 1), 60)
    epsg = (32600 if float(lat) >= 0 else 32700) + zone
    return CRS.from_epsg(epsg)


def _infer_spacing(values: np.ndarray) -> float:
    unique_values = np.unique(np.round(values.astype("float64"), 2))
    diffs = np.diff(np.sort(unique_values))
    diffs = diffs[diffs > 1.0]
    if diffs.size == 0:
        raise ValueError("Could not infer grid spacing from projected coordinates")
    return float(np.median(diffs))


def select_representative_cities(
    city_metrics: pd.DataFrame,
    *,
    city_selection: str = "representative_with_denver",
    city_ids: Sequence[int] | None = None,
    denver_city_name: str = "Denver",
) -> pd.DataFrame:
    """Select representative cities from retained city-level RF metrics."""
    required_columns = {GROUP_COLUMN, CITY_NAME_COLUMN, "climate_group", "pr_auc", FOLD_COLUMN}
    missing_columns = sorted(required_columns - set(city_metrics.columns))
    if missing_columns:
        raise ValueError(f"City metrics table missing required columns: {', '.join(missing_columns)}")

    metrics = city_metrics.copy()
    metrics[GROUP_COLUMN] = metrics[GROUP_COLUMN].astype(int)
    metrics["pr_auc"] = metrics["pr_auc"].astype(float)

    if city_ids is not None:
        requested_ids = [int(value) for value in city_ids]
        selected = metrics.loc[metrics[GROUP_COLUMN].isin(requested_ids)].copy()
        missing_requested = sorted(set(requested_ids) - set(selected[GROUP_COLUMN].astype(int)))
        if missing_requested:
            raise ValueError(f"Requested city_ids not found in reference metrics: {missing_requested}")
        selected["selection_reason"] = "explicit_city_ids"
        selected["climate_group_median_pr_auc"] = np.nan
        selected["abs_delta_from_climate_median_pr_auc"] = np.nan
        selected["selection_rule"] = "explicit_city_ids"
        return selected.sort_values([FOLD_COLUMN, GROUP_COLUMN]).reset_index(drop=True)

    normalized_selection = city_selection.strip().lower()
    if normalized_selection == "denver_only":
        denver_mask = metrics[CITY_NAME_COLUMN].astype(str).str.casefold() == denver_city_name.casefold()
        selected = metrics.loc[denver_mask].copy()
        if selected.empty:
            raise ValueError("Denver was requested but not found in reference city metrics")
        selected["selection_reason"] = "denver_only"
        selected["climate_group_median_pr_auc"] = np.nan
        selected["abs_delta_from_climate_median_pr_auc"] = np.nan
        selected["selection_rule"] = normalized_selection
        return selected.sort_values([FOLD_COLUMN, GROUP_COLUMN]).reset_index(drop=True)

    if normalized_selection == "all":
        selected = metrics.copy()
        selected["selection_reason"] = "all_cities"
        selected["climate_group_median_pr_auc"] = np.nan
        selected["abs_delta_from_climate_median_pr_auc"] = np.nan
        selected["selection_rule"] = normalized_selection
        return selected.sort_values([FOLD_COLUMN, GROUP_COLUMN]).reset_index(drop=True)

    if normalized_selection != "representative_with_denver":
        raise ValueError(
            "Unsupported city_selection. Expected one of: representative_with_denver, denver_only, all"
        )

    selected_rows: list[pd.Series] = []
    for climate_group, group_df in metrics.groupby("climate_group", sort=True):
        median_pr_auc = float(group_df["pr_auc"].median())
        ranked = group_df.assign(
            climate_group_median_pr_auc=median_pr_auc,
            abs_delta_from_climate_median_pr_auc=(group_df["pr_auc"] - median_pr_auc).abs(),
        ).sort_values(
            ["abs_delta_from_climate_median_pr_auc", "pr_auc", GROUP_COLUMN],
            ascending=[True, True, True],
        )
        row = ranked.iloc[0].copy()
        row["selection_reason"] = "climate_group_median_nearest"
        row["selection_rule"] = normalized_selection
        selected_rows.append(row)

    selected = pd.DataFrame(selected_rows)
    denver_mask = metrics[CITY_NAME_COLUMN].astype(str).str.casefold() == denver_city_name.casefold()
    denver_rows = metrics.loc[denver_mask].copy()
    if denver_rows.empty:
        LOGGER.warning("Denver was not found in retained city metrics; representative selection will omit it")
    else:
        denver_row = denver_rows.iloc[0].copy()
        denver_city_id = int(denver_row[GROUP_COLUMN])
        already_selected_mask = selected[GROUP_COLUMN].astype(int) == denver_city_id
        if already_selected_mask.any():
            selected.loc[already_selected_mask, "selection_reason"] = (
                selected.loc[already_selected_mask, "selection_reason"].astype(str)
                + ";denver_already_selected"
            )
        else:
            denver_row["selection_reason"] = "forced_denver"
            denver_row["climate_group_median_pr_auc"] = np.nan
            denver_row["abs_delta_from_climate_median_pr_auc"] = np.nan
            denver_row["selection_rule"] = normalized_selection
            selected = pd.concat([selected, pd.DataFrame([denver_row])], ignore_index=True)

    return selected.sort_values([FOLD_COLUMN, GROUP_COLUMN]).reset_index(drop=True)


def select_top_fraction_mask(values: np.ndarray, valid_mask: np.ndarray, threshold_fraction: float) -> np.ndarray:
    """Return a deterministic top-fraction mask by cell count."""
    values_array = np.asarray(values, dtype="float64")
    valid_array = np.asarray(valid_mask, dtype=bool) & np.isfinite(values_array)
    if values_array.shape != valid_array.shape:
        raise ValueError("values and valid_mask must have the same shape")
    valid_flat_indices = np.flatnonzero(valid_array.ravel())
    top_mask = np.zeros(values_array.size, dtype=bool)
    if valid_flat_indices.size == 0:
        return top_mask.reshape(values_array.shape)
    top_count = int(math.ceil(valid_flat_indices.size * float(threshold_fraction)))
    top_count = min(max(top_count, 1), valid_flat_indices.size)
    valid_values = values_array.ravel()[valid_flat_indices]
    order = np.lexsort((valid_flat_indices, -valid_values))
    top_indices = valid_flat_indices[order[:top_count]]
    top_mask[top_indices] = True
    return top_mask.reshape(values_array.shape)


def _weighted_centroid(mask: np.ndarray, weights: np.ndarray, x_grid: np.ndarray, y_grid: np.ndarray) -> tuple[float, float]:
    selected = np.asarray(mask, dtype=bool)
    weight_values = np.where(selected, np.asarray(weights, dtype="float64"), 0.0)
    total_weight = float(np.nansum(weight_values))
    if total_weight <= 0 or not np.isfinite(total_weight):
        weight_values = selected.astype("float64")
        total_weight = float(weight_values.sum())
    if total_weight <= 0:
        return (float("nan"), float("nan"))
    return (
        float(np.nansum(weight_values * x_grid) / total_weight),
        float(np.nansum(weight_values * y_grid) / total_weight),
    )


def compute_alignment_metrics_from_surfaces(
    observed_surface: np.ndarray,
    predicted_surface: np.ndarray,
    valid_mask: np.ndarray,
    x_grid: np.ndarray,
    y_grid: np.ndarray,
    *,
    threshold_fraction: float = DEFAULT_TOP_FRACTION,
) -> dict[str, float | int]:
    """Compute surface-correlation and top-region alignment metrics."""
    observed = np.asarray(observed_surface, dtype="float64")
    predicted = np.asarray(predicted_surface, dtype="float64")
    valid = np.asarray(valid_mask, dtype=bool) & np.isfinite(observed) & np.isfinite(predicted)
    if observed.shape != predicted.shape or observed.shape != valid.shape:
        raise ValueError("observed_surface, predicted_surface, and valid_mask must have matching shapes")

    valid_count = int(valid.sum())
    if valid_count == 0:
        return {
            "valid_cell_count": 0,
            "spearman_surface_corr": np.nan,
            "top_region_overlap_fraction": np.nan,
            "observed_mass_captured": np.nan,
            "centroid_distance_m": np.nan,
            "median_nearest_region_distance_m": np.nan,
            "observed_top_cell_count": 0,
            "predicted_top_cell_count": 0,
            "overlap_cell_count": 0,
        }

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=ConstantInputWarning)
        spearman_result = spearmanr(observed[valid], predicted[valid], nan_policy="omit")
    spearman_corr = float(spearman_result.correlation) if spearman_result.correlation is not None else np.nan

    observed_top = select_top_fraction_mask(observed, valid, threshold_fraction)
    predicted_top = select_top_fraction_mask(predicted, valid, threshold_fraction)
    overlap = observed_top & predicted_top
    union = observed_top | predicted_top
    overlap_count = int(overlap.sum())
    union_count = int(union.sum())
    overlap_fraction = float(overlap_count / union_count) if union_count else np.nan

    observed_mass_total = float(np.nansum(np.where(valid, observed, 0.0)))
    observed_mass_predicted_top = float(np.nansum(np.where(predicted_top, observed, 0.0)))
    observed_mass_captured = (
        float(observed_mass_predicted_top / observed_mass_total) if observed_mass_total > 0 else np.nan
    )

    observed_centroid = _weighted_centroid(observed_top, observed, x_grid, y_grid)
    predicted_centroid = _weighted_centroid(predicted_top, predicted, x_grid, y_grid)
    if np.isfinite(observed_centroid).all() and np.isfinite(predicted_centroid).all():
        centroid_distance = float(math.dist(observed_centroid, predicted_centroid))
    else:
        centroid_distance = np.nan

    observed_points = np.column_stack([x_grid[observed_top], y_grid[observed_top]])
    predicted_points = np.column_stack([x_grid[predicted_top], y_grid[predicted_top]])
    if len(observed_points) and len(predicted_points):
        nearest_distances, _ = cKDTree(predicted_points).query(observed_points, k=1)
        median_nearest_distance = float(np.median(nearest_distances))
    else:
        median_nearest_distance = np.nan

    return {
        "valid_cell_count": valid_count,
        "spearman_surface_corr": spearman_corr,
        "top_region_overlap_fraction": overlap_fraction,
        "observed_mass_captured": observed_mass_captured,
        "centroid_distance_m": centroid_distance,
        "median_nearest_region_distance_m": median_nearest_distance,
        "observed_top_cell_count": int(observed_top.sum()),
        "predicted_top_cell_count": int(predicted_top.sum()),
        "overlap_cell_count": overlap_count,
    }


def _smooth_surface(values: np.ndarray, valid_mask: np.ndarray, sigma_cells: float) -> np.ndarray:
    numeric_values = np.where(valid_mask, np.asarray(values, dtype="float64"), 0.0)
    valid_weights = valid_mask.astype("float64")
    smoothed_values = gaussian_filter(numeric_values, sigma=float(sigma_cells), mode="constant", cval=0.0)
    smoothed_weights = gaussian_filter(valid_weights, sigma=float(sigma_cells), mode="constant", cval=0.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        normalized = smoothed_values / smoothed_weights
    normalized[~valid_mask] = np.nan
    normalized[smoothed_weights <= 0] = np.nan
    return normalized


def reconstruct_city_grid(predictions: pd.DataFrame) -> GridReconstruction:
    """Reconstruct a local projected raster grid from full-city centroid predictions."""
    required_columns = {"centroid_lon", "centroid_lat", TARGET_COLUMN, "predicted_probability"}
    missing_columns = sorted(required_columns - set(predictions.columns))
    if missing_columns:
        raise ValueError(f"Prediction table missing required grid columns: {', '.join(missing_columns)}")
    if predictions.empty:
        raise ValueError("Cannot reconstruct a grid from an empty prediction table")

    lon = predictions["centroid_lon"].astype("float64").to_numpy()
    lat = predictions["centroid_lat"].astype("float64").to_numpy()
    projected_crs = _utm_crs_from_lon_lat(float(np.nanmedian(lon)), float(np.nanmedian(lat)))
    transformer = Transformer.from_crs("EPSG:4326", projected_crs, always_xy=True)
    x_m, y_m = transformer.transform(lon, lat)
    x_m = np.asarray(x_m, dtype="float64")
    y_m = np.asarray(y_m, dtype="float64")

    status_parts: list[str] = []
    try:
        spacing_x = _infer_spacing(x_m)
        spacing_y = _infer_spacing(y_m)
        grid_cell_size_m = float(np.median([spacing_x, spacing_y]))
    except ValueError:
        spacing_by_neighbor = np.median(cKDTree(np.column_stack([x_m, y_m])).query(np.column_stack([x_m, y_m]), k=2)[0][:, 1])
        grid_cell_size_m = float(spacing_by_neighbor)
        status_parts.append("spacing_inferred_from_nearest_neighbor")

    if not 20.0 <= grid_cell_size_m <= 40.0:
        status_parts.append(f"unexpected_grid_cell_size_{grid_cell_size_m:.2f}m")

    col_index = np.rint((x_m - float(np.nanmin(x_m))) / grid_cell_size_m).astype(int)
    row_index_from_bottom = np.rint((y_m - float(np.nanmin(y_m))) / grid_cell_size_m).astype(int)
    row_index = int(row_index_from_bottom.max()) - row_index_from_bottom
    shape = (int(row_index.max()) + 1, int(col_index.max()) + 1)

    flat_index = (row_index * shape[1]) + col_index
    unique_flat_index, inverse_index, _cell_counts = np.unique(
        flat_index,
        return_inverse=True,
        return_counts=True,
    )
    duplicate_count = int(len(flat_index) - len(unique_flat_index))
    if duplicate_count:
        status_parts.append(f"duplicate_grid_cells_{duplicate_count}")

    observed_values = predictions[TARGET_COLUMN].astype("float64").to_numpy()
    predicted_values = predictions["predicted_probability"].astype("float64").to_numpy()
    observed = np.full(shape, np.nan, dtype="float64")
    predicted = np.full(shape, np.nan, dtype="float64")
    valid_mask = np.zeros(shape, dtype=bool)
    if duplicate_count == 0:
        observed[row_index, col_index] = observed_values
        predicted[row_index, col_index] = predicted_values
        valid_mask[row_index, col_index] = True
    else:
        valid_mask.ravel()[unique_flat_index] = True
        observed_valid = np.isfinite(observed_values)
        observed_sums = np.bincount(
            inverse_index[observed_valid],
            weights=observed_values[observed_valid],
            minlength=len(unique_flat_index),
        )
        observed_counts = np.bincount(
            inverse_index[observed_valid],
            minlength=len(unique_flat_index),
        )
        predicted_valid = np.isfinite(predicted_values)
        predicted_sums = np.bincount(
            inverse_index[predicted_valid],
            weights=predicted_values[predicted_valid],
            minlength=len(unique_flat_index),
        )
        predicted_counts = np.bincount(
            inverse_index[predicted_valid],
            minlength=len(unique_flat_index),
        )
        with np.errstate(divide="ignore", invalid="ignore"):
            observed_means = observed_sums / observed_counts
            predicted_means = predicted_sums / predicted_counts
        observed_means[observed_counts == 0] = np.nan
        predicted_means[predicted_counts == 0] = np.nan
        observed.ravel()[unique_flat_index] = observed_means
        predicted.ravel()[unique_flat_index] = predicted_means

    status = "ok" if not status_parts else ";".join(status_parts)
    return GridReconstruction(
        x_m=x_m,
        y_m=y_m,
        row_index=row_index,
        col_index=col_index,
        shape=shape,
        valid_mask=valid_mask,
        observed=observed,
        predicted=predicted,
        grid_cell_size_m=grid_cell_size_m,
        projected_crs=projected_crs.to_string(),
        status=status,
    )


def _grid_coordinate_arrays(grid: GridReconstruction) -> tuple[np.ndarray, np.ndarray]:
    row_grid = np.arange(grid.shape[0], dtype="float64")[:, None]
    col_grid = np.arange(grid.shape[1], dtype="float64")[None, :]
    x_grid = float(np.nanmin(grid.x_m)) + (col_grid * grid.grid_cell_size_m)
    y_grid = float(np.nanmax(grid.y_m)) - (row_grid * grid.grid_cell_size_m)
    return np.broadcast_to(x_grid, grid.shape), np.broadcast_to(y_grid, grid.shape)


def _build_map_surface_bundle(
    predictions: pd.DataFrame,
    *,
    scale_label: str,
    threshold_fraction: float = DEFAULT_TOP_FRACTION,
    smoothing_method: str = "gaussian",
) -> MapSurfaceBundle:
    if smoothing_method != "gaussian":
        raise ValueError("Only gaussian smoothing is implemented for spatial-alignment maps")
    radius_m = _radius_for_scale_label(scale_label)
    normalized_scale_label = _scale_label(radius_m)
    grid = reconstruct_city_grid(predictions)
    x_grid, y_grid = _grid_coordinate_arrays(grid)
    sigma_m = radius_m / 2.0
    sigma_cells = max(sigma_m / grid.grid_cell_size_m, 1e-6)
    observed_surface = _smooth_surface(grid.observed, grid.valid_mask, sigma_cells=sigma_cells)
    predicted_surface = _smooth_surface(grid.predicted, grid.valid_mask, sigma_cells=sigma_cells)
    observed_top_mask = select_top_fraction_mask(observed_surface, grid.valid_mask, threshold_fraction)
    predicted_top_mask = select_top_fraction_mask(predicted_surface, grid.valid_mask, threshold_fraction)
    overlap_category = np.full(grid.shape, np.nan, dtype="float64")
    overlap_category[grid.valid_mask] = 0.0
    overlap_category[observed_top_mask & ~predicted_top_mask] = 1.0
    overlap_category[predicted_top_mask & ~observed_top_mask] = 2.0
    overlap_category[observed_top_mask & predicted_top_mask] = 3.0
    return MapSurfaceBundle(
        grid=grid,
        observed_surface=observed_surface,
        predicted_surface=predicted_surface,
        observed_top_mask=observed_top_mask,
        predicted_top_mask=predicted_top_mask,
        overlap_category=overlap_category,
        x_grid=x_grid,
        y_grid=y_grid,
        radius_m=radius_m,
        sigma_m=sigma_m,
        scale_label=normalized_scale_label,
    )


def compute_city_spatial_alignment_metrics(
    predictions: pd.DataFrame,
    *,
    smoothing_radii_m: Sequence[float] = DEFAULT_SMOOTHING_RADII_M,
    threshold_fraction: float = DEFAULT_TOP_FRACTION,
    smoothing_method: str = "gaussian",
) -> pd.DataFrame:
    """Build smoothed observed/predicted surfaces and compute alignment metrics for one city."""
    if smoothing_method != "gaussian":
        raise ValueError("Only gaussian smoothing is implemented for the first spatial-alignment pass")
    grid = reconstruct_city_grid(predictions)
    x_grid, y_grid = _grid_coordinate_arrays(grid)

    first_row = predictions.iloc[0]
    rows: list[dict[str, object]] = []
    for radius_m in [float(value) for value in smoothing_radii_m]:
        sigma_m = radius_m / 2.0
        sigma_cells = max(sigma_m / grid.grid_cell_size_m, 1e-6)
        observed_surface = _smooth_surface(grid.observed, grid.valid_mask, sigma_cells=sigma_cells)
        predicted_surface = _smooth_surface(grid.predicted, grid.valid_mask, sigma_cells=sigma_cells)
        metrics = compute_alignment_metrics_from_surfaces(
            observed_surface=observed_surface,
            predicted_surface=predicted_surface,
            valid_mask=grid.valid_mask,
            x_grid=x_grid,
            y_grid=y_grid,
            threshold_fraction=threshold_fraction,
        )
        rows.append(
            {
                GROUP_COLUMN: int(first_row[GROUP_COLUMN]),
                CITY_NAME_COLUMN: first_row[CITY_NAME_COLUMN],
                "climate_group": first_row["climate_group"],
                FOLD_COLUMN: int(first_row[FOLD_COLUMN]),
                "model_name": first_row["model_name"],
                "source_reference_run_dir": first_row["source_reference_run_dir"],
                "training_sample_rows_per_city": int(first_row["training_sample_rows_per_city"]),
                "prediction_scope": first_row["prediction_scope"],
                "row_count": int(len(predictions)),
                "scale_label": _scale_label(radius_m),
                "smoothing_radius_m": radius_m,
                "smoothing_method": smoothing_method,
                "smoothing_sigma_m": sigma_m,
                "threshold_fraction": float(threshold_fraction),
                "grid_cell_size_m": grid.grid_cell_size_m,
                "projected_crs": grid.projected_crs,
                "grid_reconstruction_status": grid.status,
                **metrics,
            }
        )
    return pd.DataFrame(rows, columns=METRICS_COLUMNS)


def _fit_random_forest_for_fold(
    train_df: pd.DataFrame,
    *,
    feature_columns: Sequence[str],
    tuning_preset: str,
    random_state: int,
    grid_search_n_jobs: int,
    model_n_jobs: int,
    scoring: str,
) -> GridSearchCV:
    tuning_spec = get_model_tuning_spec("random_forest", tuning_preset)
    train_group_count = int(train_df[GROUP_COLUMN].nunique())
    effective_splits = min(int(tuning_spec.inner_cv_splits), train_group_count)
    if effective_splits < 2:
        raise ValueError("At least two training cities are required for grouped inner-CV tuning")
    pipeline = build_random_forest_pipeline(
        feature_columns=feature_columns,
        random_state=random_state,
        n_jobs=model_n_jobs,
    )
    grid_search = GridSearchCV(
        estimator=pipeline,
        param_grid=tuning_spec.param_grid,
        cv=GroupKFold(n_splits=effective_splits),
        scoring=get_scorer(scoring),
        n_jobs=grid_search_n_jobs,
        refit=True,
        error_score="raise",
    )
    grid_search.fit(
        train_df[list(feature_columns)],
        train_df[TARGET_COLUMN].to_numpy(dtype="int8"),
        groups=train_df[GROUP_COLUMN].to_numpy(),
    )
    return grid_search


def _predict_probabilities(
    estimator: object,
    feature_df: pd.DataFrame,
    *,
    feature_columns: Sequence[str],
    prediction_batch_size: int | None,
) -> np.ndarray:
    if prediction_batch_size is None or prediction_batch_size <= 0 or len(feature_df) <= prediction_batch_size:
        return estimator.predict_proba(feature_df[list(feature_columns)])[:, 1]

    probabilities = np.empty(len(feature_df), dtype="float64")
    for start in range(0, len(feature_df), int(prediction_batch_size)):
        stop = min(start + int(prediction_batch_size), len(feature_df))
        probabilities[start:stop] = estimator.predict_proba(feature_df.iloc[start:stop][list(feature_columns)])[:, 1]
    return probabilities


def _load_full_city_rows(
    *,
    dataset_path: Path,
    feature_columns: Sequence[str],
    city_id: int,
) -> pd.DataFrame:
    rows = load_modeling_rows(
        dataset_path=dataset_path,
        feature_columns=feature_columns,
        city_ids=[int(city_id)],
        sample_rows_per_city=None,
    )
    return drop_missing_target_rows(rows)


def _prediction_output_path(output_dir: Path, city_name: object, city_id: int, model_name: str) -> Path:
    slug = _slugify(city_name)
    return output_dir / "full_city_predictions" / f"{slug}_city{int(city_id):02d}_{model_name}_full_city_predictions.parquet"


def spatial_alignment_map_path(figures_dir: Path, city_name: object, city_id: int, model_name: str, scale_label: str) -> Path:
    """Return the deterministic spatial-alignment map path for a city/model/scale."""
    slug = _slugify(city_name)
    normalized_scale_label = scale_label.strip().lower()
    return (
        figures_dir
        / f"{slug}_city{int(city_id):02d}_{model_name}_{normalized_scale_label}_surface_alignment.png"
    )


def _plot_spatial_alignment_map(
    *,
    bundle: MapSurfaceBundle,
    prediction_df: pd.DataFrame,
    output_path: Path,
) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap
    from matplotlib.patches import Patch

    first_row = prediction_df.iloc[0]
    extent = [
        float(np.nanmin(bundle.x_grid)),
        float(np.nanmax(bundle.x_grid)),
        float(np.nanmin(bundle.y_grid)),
        float(np.nanmax(bundle.y_grid)),
    ]
    observed_top = np.where(bundle.observed_top_mask, 1.0, np.nan)
    predicted_top = np.where(bundle.predicted_top_mask, 1.0, np.nan)
    overlap_cmap = ListedColormap(["#f2f2f2", "#d55e00", "#0072b2", "#009e73"])
    overlap_norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], overlap_cmap.N)

    fig, axes = plt.subplots(1, 5, figsize=(18, 4.6), constrained_layout=True)
    fig.suptitle(
        (
            f"{first_row[CITY_NAME_COLUMN]} spatial alignment, {bundle.scale_label} "
            f"({int(bundle.radius_m)} m), {first_row['model_name']}"
        ),
        fontsize=12,
    )
    panels = [
        ("Observed smoothed hotspot surface", bundle.observed_surface, "magma", None),
        ("Predicted smoothed risk surface", bundle.predicted_surface, "viridis", None),
        ("Observed top 10% smoothed region", observed_top, "Reds", None),
        ("Predicted top 10% smoothed region", predicted_top, "Blues", None),
        ("Top-region overlap", bundle.overlap_category, overlap_cmap, overlap_norm),
    ]

    for axis, (title, image, cmap, norm) in zip(axes, panels, strict=True):
        axis.set_title(title, fontsize=9)
        axis.imshow(
            image,
            origin="upper",
            interpolation="nearest",
            extent=extent,
            cmap=cmap,
            norm=norm,
        )
        axis.set_xticks([])
        axis.set_yticks([])
        axis.set_aspect("equal")

    axes[-1].legend(
        handles=[
            Patch(facecolor="#f2f2f2", edgecolor="none", label="Neither"),
            Patch(facecolor="#d55e00", edgecolor="none", label="Observed only"),
            Patch(facecolor="#0072b2", edgecolor="none", label="Predicted only"),
            Patch(facecolor="#009e73", edgecolor="none", label="Overlap"),
        ],
        loc="lower center",
        bbox_to_anchor=(0.5, -0.22),
        ncol=2,
        fontsize=8,
        frameon=False,
    )
    fig.text(
        0.5,
        0.01,
        f"Grid reconstruction: {bundle.grid.status}; CRS: {bundle.grid.projected_crs}; cell size: {bundle.grid.grid_cell_size_m:.1f} m",
        ha="center",
        va="bottom",
        fontsize=8,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def generate_spatial_alignment_maps(
    *,
    prediction_paths: Sequence[Path],
    figures_dir: Path = DEFAULT_SPATIAL_ALIGNMENT_FIGURE_DIR,
    manifest_path: Path,
    scale_label: str = "medium",
    map_city_ids: Sequence[int] | None = None,
    threshold_fraction: float = DEFAULT_TOP_FRACTION,
    smoothing_method: str = "gaussian",
) -> pd.DataFrame:
    """Generate five-panel smoothed-surface alignment maps from full-city prediction files."""
    _radius_for_scale_label(scale_label)
    requested_city_ids = None if map_city_ids is None else {int(city_id) for city_id in map_city_ids}
    figures_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for prediction_path in prediction_paths:
        prediction_df = pd.read_parquet(prediction_path)
        if prediction_df.empty:
            continue
        first_row = prediction_df.iloc[0]
        city_id = int(first_row[GROUP_COLUMN])
        if requested_city_ids is not None and city_id not in requested_city_ids:
            continue
        bundle = _build_map_surface_bundle(
            prediction_df,
            scale_label=scale_label,
            threshold_fraction=float(threshold_fraction),
            smoothing_method=smoothing_method,
        )
        figure_path = spatial_alignment_map_path(
            figures_dir,
            first_row[CITY_NAME_COLUMN],
            city_id,
            str(first_row["model_name"]),
            bundle.scale_label,
        )
        LOGGER.info("Writing spatial-alignment map: %s", figure_path)
        _plot_spatial_alignment_map(
            bundle=bundle,
            prediction_df=prediction_df,
            output_path=figure_path,
        )
        rows.append(
            {
                GROUP_COLUMN: city_id,
                CITY_NAME_COLUMN: first_row[CITY_NAME_COLUMN],
                "climate_group": first_row["climate_group"],
                FOLD_COLUMN: int(first_row[FOLD_COLUMN]),
                "model_name": first_row["model_name"],
                "scale_label": bundle.scale_label,
                "smoothing_radius_m": bundle.radius_m,
                "smoothing_method": smoothing_method,
                "smoothing_sigma_m": bundle.sigma_m,
                "threshold_fraction": float(threshold_fraction),
                "row_count": int(len(prediction_df)),
                "valid_cell_count": int(bundle.grid.valid_mask.sum()),
                "grid_cell_size_m": bundle.grid.grid_cell_size_m,
                "projected_crs": bundle.grid.projected_crs,
                "grid_reconstruction_status": bundle.grid.status,
                "prediction_path": str(prediction_path),
                "figure_path": str(figure_path),
            }
        )

    manifest_df = pd.DataFrame(rows, columns=MAP_MANIFEST_COLUMNS)
    manifest_df.to_csv(manifest_path, index=False)
    return manifest_df


def _write_summary(
    *,
    output_path: Path,
    selection_df: pd.DataFrame,
    metrics_df: pd.DataFrame,
    reference_run_dir: Path,
    model_name: str,
    sample_rows_per_city: int,
    smoothing_radii_m: Sequence[float],
    threshold_fraction: float,
    prediction_paths: Sequence[Path],
    city_selection: str,
    selection_table_name: str,
    metrics_table_name: str,
    map_manifest_df: pd.DataFrame | None = None,
) -> None:
    is_all_city = city_selection.strip().lower() == "all"
    scope_phrase = "all selected held-out cities" if is_all_city else "selected representative cities"
    diagnostic_sentence = (
        "This supplemental diagnostic uses the retained random-forest frontier contract, with full eligible "
        f"held-out rows scored for spatial analysis across {scope_phrase}. Existing full-city prediction files "
        "can be reused for table and map generation without refitting. It is supplemental full-city spatial "
        "placement diagnostics, not a new canonical benchmark, and not a replacement for the retained sampled "
        "held-out-city PR AUC / recall benchmark."
    )
    selected_city_text = ", ".join(
        f"{row.city_name} (city_id={int(row.city_id)}, fold={int(row.outer_fold)})"
        for row in selection_df.itertuples(index=False)
    )
    lines = [
        "# Spatial Alignment Diagnostic Summary",
        "",
        diagnostic_sentence,
        "",
        f"- Model: `{model_name}`",
        f"- Reference run: `{reference_run_dir}`",
        f"- Training sample cap: `{sample_rows_per_city}` rows per training city",
        f"- City selection: `{city_selection}`",
        f"- Prediction scope: `{PREDICTION_SCOPE_FULL_CITY}` for {scope_phrase}",
        f"- Smoothing radii: `{', '.join(str(int(value)) for value in smoothing_radii_m)} m`",
        f"- Top-region threshold fraction: `{threshold_fraction:.2f}`",
        f"- Selected cities: {selected_city_text}",
        "",
        "## Outputs",
        "",
        f"- `tables/{selection_table_name}`",
        f"- `tables/{metrics_table_name}`",
        "- `full_city_predictions/*.parquet`",
        "",
        "## Metric Snapshot",
        "",
    ]
    if metrics_df.empty:
        lines.append("No metric rows were written.")
    else:
        snapshot_columns = [
            CITY_NAME_COLUMN,
            "scale_label",
            "spearman_surface_corr",
            "top_region_overlap_fraction",
            "observed_mass_captured",
            "centroid_distance_m",
            "median_nearest_region_distance_m",
            "grid_reconstruction_status",
        ]
        lines.extend(_format_markdown_table(metrics_df[snapshot_columns]))
    lines.extend(["", "## Full-City Prediction Files", ""])
    for path in prediction_paths:
        lines.append(f"- `{path}`")
    if map_manifest_df is not None:
        lines.extend(["", "## Map Files", ""])
        if map_manifest_df.empty:
            lines.append("No map files were generated.")
        else:
            lines.append(
                "Optional maps are supplemental full-city spatial placement diagnostics only; they do not "
                "replace the retained sampled held-out-city PR AUC / recall benchmark."
            )
            lines.append("")
            lines.append("- `tables/spatial_alignment_map_manifest.csv`")
            for path in map_manifest_df["figure_path"].tolist():
                lines.append(f"- `{path}`")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _format_markdown_table(table: pd.DataFrame) -> list[str]:
    """Format a compact markdown table without optional tabulate dependency."""
    if table.empty:
        return ["No rows."]
    formatted = table.copy()
    for column_name in formatted.columns:
        if pd.api.types.is_float_dtype(formatted[column_name]):
            formatted[column_name] = formatted[column_name].map(
                lambda value: "" if pd.isna(value) else f"{float(value):.4f}"
            )
        else:
            formatted[column_name] = formatted[column_name].map(lambda value: "" if pd.isna(value) else str(value))
    rows = [
        "| " + " | ".join(formatted.columns) + " |",
        "| " + " | ".join(["---"] * len(formatted.columns)) + " |",
    ]
    for row in formatted.itertuples(index=False, name=None):
        rows.append("| " + " | ".join(str(value) for value in row) + " |")
    return rows


def run_spatial_alignment_workflow(
    *,
    reference_run_dir: Path = DEFAULT_REFERENCE_RUN_DIR,
    dataset_path: Path = DEFAULT_FINAL_DATASET_PATH,
    folds_path: Path = DEFAULT_FOLDS_PARQUET_PATH,
    output_dir: Path = DEFAULT_SPATIAL_ALIGNMENT_OUTPUT_DIR,
    model_name: str = "random_forest",
    sample_rows_per_city: int = 5000,
    city_selection: str = "representative_with_denver",
    city_ids: Sequence[int] | None = None,
    smoothing_radii_m: Sequence[float] = DEFAULT_SMOOTHING_RADII_M,
    threshold_fraction: float = DEFAULT_TOP_FRACTION,
    grid_search_n_jobs: int = 1,
    model_n_jobs: int = 1,
    prediction_batch_size: int | None = DEFAULT_PREDICTION_BATCH_SIZE,
    skip_existing_predictions: bool = False,
    make_maps: bool = False,
    map_scale_label: str = "medium",
    map_city_ids: Sequence[int] | None = None,
    figures_dir: Path = DEFAULT_SPATIAL_ALIGNMENT_FIGURE_DIR,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> SpatialAlignmentResult:
    """Run RF full-city held-out spatial-alignment diagnostics for selected cities."""
    normalized_model_name = model_name.strip().lower()
    if normalized_model_name != "random_forest":
        raise ValueError("The first spatial-alignment implementation supports only model_name='random_forest'")

    reference_run_dir = _normalize_reference_run_dir(reference_run_dir)
    metadata = _read_reference_metadata(reference_run_dir)
    feature_columns = list(metadata.get("selected_feature_columns") or DEFAULT_FEATURE_COLUMNS)
    tuning_preset = str(metadata.get("tuning_preset") or "frontier")
    scoring = str(metadata.get("scoring") or DEFAULT_PR_SCORING)

    available_columns = get_final_dataset_columns(dataset_path=dataset_path)
    validate_required_final_columns(available_columns)
    validate_model_feature_columns(feature_columns=feature_columns, available_columns=available_columns)

    output_dir.mkdir(parents=True, exist_ok=True)
    tables_dir = output_dir / "tables"
    predictions_dir = output_dir / "full_city_predictions"
    tables_dir.mkdir(parents=True, exist_ok=True)
    predictions_dir.mkdir(parents=True, exist_ok=True)

    city_metrics_path = reference_run_dir / "metrics_by_city.csv"
    if not city_metrics_path.exists():
        raise FileNotFoundError(f"Reference city metrics not found: {city_metrics_path}")
    reference_city_metrics = pd.read_csv(city_metrics_path)
    selection_df = select_representative_cities(
        reference_city_metrics,
        city_selection=city_selection,
        city_ids=city_ids,
    )
    fold_table = load_city_outer_folds(folds_path=folds_path)
    selected_city_ids = [int(value) for value in selection_df[GROUP_COLUMN].tolist()]
    selected_folds = sorted(
        int(value)
        for value in fold_table.loc[fold_table[GROUP_COLUMN].isin(selected_city_ids), FOLD_COLUMN].unique()
    )
    selection_df = selection_df.merge(
        fold_table[[GROUP_COLUMN, FOLD_COLUMN]].rename(columns={FOLD_COLUMN: "fold_table_outer_fold"}),
        on=GROUP_COLUMN,
        how="left",
    )
    if (selection_df[FOLD_COLUMN].astype(int) != selection_df["fold_table_outer_fold"].astype(int)).any():
        raise ValueError("Reference city metrics outer_fold values do not match the fold table")
    selection_table_name, metrics_table_name = _table_filenames_for_selection(city_selection, city_ids)
    selection_table_path = tables_dir / selection_table_name
    selection_df.to_csv(selection_table_path, index=False)

    metric_frames: list[pd.DataFrame] = []
    prediction_paths: list[Path] = []
    workflow_start = perf_counter()

    for outer_fold in selected_folds:
        fold_selected = selection_df.loc[selection_df[FOLD_COLUMN].astype(int) == int(outer_fold)].copy()
        if fold_selected.empty:
            continue
        fold_prediction_requests = [
            (
                int(getattr(selected_city, GROUP_COLUMN)),
                getattr(selected_city, CITY_NAME_COLUMN),
                _prediction_output_path(
                    output_dir,
                    getattr(selected_city, CITY_NAME_COLUMN),
                    int(getattr(selected_city, GROUP_COLUMN)),
                    normalized_model_name,
                ),
            )
            for selected_city in fold_selected.itertuples(index=False)
        ]
        if skip_existing_predictions and all(prediction_path.exists() for _, _, prediction_path in fold_prediction_requests):
            LOGGER.info(
                "Reusing existing full-city predictions for outer_fold=%s; skipping model fit",
                outer_fold,
            )
            for _city_id, _city_name, prediction_path in fold_prediction_requests:
                prediction_df = pd.read_parquet(prediction_path)
                prediction_paths.append(prediction_path)
                city_metrics = compute_city_spatial_alignment_metrics(
                    prediction_df,
                    smoothing_radii_m=smoothing_radii_m,
                    threshold_fraction=float(threshold_fraction),
                )
                metric_frames.append(city_metrics)
            continue

        train_city_ids = (
            fold_table.loc[fold_table[FOLD_COLUMN].astype(int) != int(outer_fold), GROUP_COLUMN].astype(int).tolist()
        )
        LOGGER.info(
            "Fitting %s outer_fold=%s on %s training cities with sample_rows_per_city=%s",
            normalized_model_name,
            outer_fold,
            len(train_city_ids),
            sample_rows_per_city,
        )
        train_df, _diagnostics = load_sampled_modeling_rows_with_diagnostics(
            dataset_path=dataset_path,
            feature_columns=feature_columns,
            city_ids=train_city_ids,
            sample_rows_per_city=int(sample_rows_per_city),
            random_state=int(random_state),
        )
        train_df = drop_missing_target_rows(train_df)
        fitted_search = _fit_random_forest_for_fold(
            train_df,
            feature_columns=feature_columns,
            tuning_preset=tuning_preset,
            random_state=int(random_state),
            grid_search_n_jobs=int(grid_search_n_jobs),
            model_n_jobs=int(model_n_jobs),
            scoring=scoring,
        )

        for city_id, city_name, prediction_path in fold_prediction_requests:
            if skip_existing_predictions and prediction_path.exists():
                prediction_df = pd.read_parquet(prediction_path)
            else:
                LOGGER.info("Scoring full held-out city_id=%s (%s)", city_id, city_name)
                full_city_df = _load_full_city_rows(
                    dataset_path=dataset_path,
                    feature_columns=feature_columns,
                    city_id=city_id,
                )
                probabilities = _predict_probabilities(
                    fitted_search.best_estimator_,
                    full_city_df,
                    feature_columns=feature_columns,
                    prediction_batch_size=prediction_batch_size,
                )
                prediction_df = full_city_df[
                    [
                        GROUP_COLUMN,
                        CITY_NAME_COLUMN,
                        "climate_group",
                        "cell_id",
                        "centroid_lon",
                        "centroid_lat",
                        TARGET_COLUMN,
                    ]
                ].copy()
                prediction_df[FOLD_COLUMN] = int(outer_fold)
                prediction_df["model_name"] = normalized_model_name
                prediction_df["predicted_probability"] = probabilities.astype("float64")
                prediction_df["prediction_scope"] = PREDICTION_SCOPE_FULL_CITY
                prediction_df["training_sample_rows_per_city"] = int(sample_rows_per_city)
                prediction_df["source_reference_run_dir"] = str(reference_run_dir)
                prediction_df = prediction_df[REQUIRED_PREDICTION_COLUMNS]
                prediction_df.to_parquet(prediction_path, index=False)

            prediction_paths.append(prediction_path)
            city_metrics = compute_city_spatial_alignment_metrics(
                prediction_df,
                smoothing_radii_m=smoothing_radii_m,
                threshold_fraction=float(threshold_fraction),
            )
            metric_frames.append(city_metrics)

    metrics_df = pd.concat(metric_frames, ignore_index=True) if metric_frames else pd.DataFrame(columns=METRICS_COLUMNS)
    metrics_table_path = tables_dir / metrics_table_name
    metrics_df.to_csv(metrics_table_path, index=False)

    map_manifest_table_path: Path | None = None
    map_manifest_df: pd.DataFrame | None = None
    map_paths: tuple[Path, ...] = ()
    if make_maps:
        map_manifest_table_path = tables_dir / "spatial_alignment_map_manifest.csv"
        map_manifest_df = generate_spatial_alignment_maps(
            prediction_paths=prediction_paths,
            figures_dir=figures_dir,
            manifest_path=map_manifest_table_path,
            scale_label=map_scale_label,
            map_city_ids=map_city_ids,
            threshold_fraction=float(threshold_fraction),
        )
        map_paths = tuple(Path(path) for path in map_manifest_df["figure_path"].tolist())

    metadata_path = output_dir / "spatial_alignment_metadata.json"
    metadata_payload = {
        "model_name": normalized_model_name,
        "reference_run_dir": str(reference_run_dir),
        "dataset_path": str(dataset_path),
        "folds_path": str(folds_path),
        "sample_rows_per_city": int(sample_rows_per_city),
        "city_selection": city_selection,
        "selected_city_ids": selected_city_ids,
        "selected_outer_folds": selected_folds,
        "feature_columns": feature_columns,
        "tuning_preset": tuning_preset,
        "scoring": scoring,
        "smoothing_radii_m": [float(value) for value in smoothing_radii_m],
        "threshold_fraction": float(threshold_fraction),
        "prediction_scope": PREDICTION_SCOPE_FULL_CITY,
        "grid_search_n_jobs": int(grid_search_n_jobs),
        "model_n_jobs": int(model_n_jobs),
        "prediction_batch_size": None if prediction_batch_size is None else int(prediction_batch_size),
        "make_maps": bool(make_maps),
        "map_scale_label": map_scale_label if make_maps else None,
        "map_city_ids": None if map_city_ids is None else [int(value) for value in map_city_ids],
        "map_manifest_table_path": None if map_manifest_table_path is None else str(map_manifest_table_path),
        "map_paths": [str(path) for path in map_paths],
        "wall_clock_seconds": float(perf_counter() - workflow_start),
        "benchmark_scope_note": _scope_note_for_selection(city_selection, city_ids),
    }
    metadata_path.write_text(json.dumps(metadata_payload, indent=2), encoding="utf-8")

    summary_markdown_path = output_dir / "spatial_alignment_summary.md"
    _write_summary(
        output_path=summary_markdown_path,
        selection_df=selection_df,
        metrics_df=metrics_df,
        reference_run_dir=reference_run_dir,
        model_name=normalized_model_name,
        sample_rows_per_city=int(sample_rows_per_city),
        smoothing_radii_m=smoothing_radii_m,
        threshold_fraction=float(threshold_fraction),
        prediction_paths=prediction_paths,
        city_selection=city_selection,
        selection_table_name=selection_table_name,
        metrics_table_name=metrics_table_name,
        map_manifest_df=map_manifest_df,
    )

    return SpatialAlignmentResult(
        output_dir=output_dir,
        selection_table_path=selection_table_path,
        metrics_table_path=metrics_table_path,
        summary_markdown_path=summary_markdown_path,
        prediction_paths=tuple(prediction_paths),
        map_manifest_table_path=map_manifest_table_path,
        map_paths=map_paths,
    )
