from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer

import src.modeling_spatial_alignment as spatial_alignment
from src.final_dataset_contract import CORE_FINAL_COLUMNS
from src.modeling_config import DEFAULT_FEATURE_COLUMNS
from src.modeling_spatial_alignment import (
    MAP_MANIFEST_COLUMNS,
    METRICS_COLUMNS,
    compute_city_spatial_alignment_metrics,
    compute_alignment_metrics_from_surfaces,
    generate_spatial_alignment_maps,
    reconstruct_city_grid,
    run_spatial_alignment_workflow,
    select_representative_cities,
    select_top_fraction_mask,
    spatial_alignment_map_path,
)


def test_select_representative_cities_uses_climate_medians_and_forces_denver() -> None:
    city_metrics = pd.DataFrame(
        {
            "model_name": ["random_forest"] * 7,
            "outer_fold": [0, 0, 1, 1, 2, 2, 3],
            "city_id": [1, 2, 3, 4, 5, 6, 7],
            "city_name": ["A", "B", "C", "D", "E", "F", "Denver"],
            "climate_group": ["hot_arid", "hot_arid", "hot_humid", "hot_humid", "mild_cool", "mild_cool", "hot_arid"],
            "row_count": [5000] * 7,
            "positive_count": [500] * 7,
            "prevalence": [0.1] * 7,
            "pr_auc": [0.10, 0.30, 0.12, 0.20, 0.16, 0.18, 0.50],
            "recall_at_top_10pct": [0.1] * 7,
        }
    )

    selected = select_representative_cities(city_metrics, city_selection="representative_with_denver")

    assert selected["city_id"].tolist() == [2, 3, 5, 7]
    assert selected.loc[selected["city_name"] == "Denver", "selection_reason"].item() == "forced_denver"
    median_rows = selected.loc[selected["selection_reason"] == "climate_group_median_nearest"]
    assert set(median_rows["climate_group"]) == {"hot_arid", "hot_humid", "mild_cool"}


def test_select_top_fraction_mask_is_count_based_and_deterministic_on_ties() -> None:
    values = np.array([5.0, 5.0, 4.0, 3.0, 2.0])
    valid_mask = np.ones_like(values, dtype=bool)

    top_mask = select_top_fraction_mask(values, valid_mask, threshold_fraction=0.40)

    assert top_mask.tolist() == [True, True, False, False, False]
    assert int(top_mask.sum()) == 2


def test_compute_alignment_metrics_from_tiny_surfaces() -> None:
    observed = np.array(
        [
            [0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0],
        ]
    )
    predicted = observed.copy()
    valid_mask = np.ones_like(observed, dtype=bool)
    x_grid = np.array(
        [
            [0.0, 30.0, 60.0],
            [0.0, 30.0, 60.0],
            [0.0, 30.0, 60.0],
        ]
    )
    y_grid = np.array(
        [
            [60.0, 60.0, 60.0],
            [30.0, 30.0, 30.0],
            [0.0, 0.0, 0.0],
        ]
    )

    metrics = compute_alignment_metrics_from_surfaces(
        observed,
        predicted,
        valid_mask,
        x_grid,
        y_grid,
        threshold_fraction=1 / 9,
    )

    assert metrics["valid_cell_count"] == 9
    assert math.isclose(float(metrics["spearman_surface_corr"]), 1.0)
    assert math.isclose(float(metrics["top_region_overlap_fraction"]), 1.0)
    assert math.isclose(float(metrics["observed_mass_captured"]), 1.0)
    assert math.isclose(float(metrics["centroid_distance_m"]), 0.0)
    assert math.isclose(float(metrics["median_nearest_region_distance_m"]), 0.0)
    assert metrics["observed_top_cell_count"] == 1
    assert metrics["predicted_top_cell_count"] == 1
    assert metrics["overlap_cell_count"] == 1


def test_compute_city_spatial_alignment_metrics_reconstructs_tiny_projected_grid() -> None:
    rows = _tiny_prediction_rows()

    metrics_df = compute_city_spatial_alignment_metrics(
        pd.DataFrame(rows),
        smoothing_radii_m=[30.0],
        threshold_fraction=1 / 9,
    )

    assert metrics_df.columns.tolist() == METRICS_COLUMNS
    assert len(metrics_df) == 1
    assert metrics_df.loc[0, "valid_cell_count"] == 9
    assert math.isclose(float(metrics_df.loc[0, "grid_cell_size_m"]), 30.0, abs_tol=0.1)
    assert metrics_df.loc[0, "grid_reconstruction_status"] == "ok"
    assert math.isclose(float(metrics_df.loc[0, "spearman_surface_corr"]), 1.0)


def test_reconstruct_city_grid_uses_vectorized_no_duplicate_path(monkeypatch) -> None:
    rows = _tiny_prediction_rows()

    def fail_groupby(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("no-duplicate reconstruction should not use DataFrame.groupby")

    monkeypatch.setattr(pd.DataFrame, "groupby", fail_groupby)

    grid = reconstruct_city_grid(pd.DataFrame(rows))

    assert grid.status == "ok"
    assert grid.shape == (3, 3)
    assert int(grid.valid_mask.sum()) == 9
    assert math.isclose(float(grid.grid_cell_size_m), 30.0, abs_tol=0.1)
    assert math.isclose(float(grid.observed[1, 1]), 1.0)
    assert math.isclose(float(grid.predicted[1, 1]), 1.0)


def test_reconstruct_city_grid_aggregates_duplicate_cells() -> None:
    rows = _tiny_prediction_rows()
    duplicate = rows[4].copy()
    duplicate["hotspot_10pct"] = 0
    duplicate["predicted_probability"] = 0.5
    rows.append(duplicate)

    grid = reconstruct_city_grid(pd.DataFrame(rows))

    assert "duplicate_grid_cells_1" in grid.status
    assert int(grid.valid_mask.sum()) == 9
    assert math.isclose(float(grid.observed[1, 1]), 0.5)
    assert math.isclose(float(grid.predicted[1, 1]), 0.75)


def test_run_spatial_alignment_workflow_skip_existing_predictions_avoids_fit(tmp_path: Path, monkeypatch) -> None:
    reference_run_dir = tmp_path / "reference_run"
    reference_run_dir.mkdir()
    pd.DataFrame(
        {
            "model_name": ["random_forest"],
            "outer_fold": [1],
            "city_id": [6],
            "city_name": ["Denver"],
            "climate_group": ["hot_arid"],
            "row_count": [9],
            "positive_count": [1],
            "prevalence": [1 / 9],
            "pr_auc": [0.5],
            "recall_at_top_10pct": [1.0],
        }
    ).to_csv(reference_run_dir / "metrics_by_city.csv", index=False)

    dataset_path = tmp_path / "final_dataset.parquet"
    final_row = {column: 0 for column in CORE_FINAL_COLUMNS}
    final_row.update(
        {
            "city_id": 6,
            "city_name": "Denver",
            "climate_group": "hot_arid",
            "cell_id": 1,
            "centroid_lon": -105.0,
            "centroid_lat": 39.7,
            "land_cover_class": 21,
            "hotspot_10pct": 0,
        }
    )
    for column in DEFAULT_FEATURE_COLUMNS:
        final_row.setdefault(column, 0)
    pd.DataFrame([final_row]).to_parquet(dataset_path, index=False)

    folds_path = tmp_path / "city_outer_folds.parquet"
    pd.DataFrame(
        {
            "city_id": [1, 6],
            "city_name": ["Phoenix", "Denver"],
            "climate_group": ["hot_arid", "hot_arid"],
            "row_count": [9, 9],
            "outer_fold": [0, 1],
        }
    ).to_parquet(folds_path, index=False)

    output_dir = tmp_path / "spatial_alignment"
    prediction_dir = output_dir / "full_city_predictions"
    prediction_dir.mkdir(parents=True)
    existing_prediction_path = prediction_dir / "denver_city06_random_forest_full_city_predictions.parquet"
    pd.DataFrame(_tiny_prediction_rows()).to_parquet(existing_prediction_path, index=False)

    def fail_fit(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("existing fold predictions should skip fitting")

    monkeypatch.setattr(spatial_alignment, "_fit_random_forest_for_fold", fail_fit)
    monkeypatch.setattr(spatial_alignment, "load_sampled_modeling_rows_with_diagnostics", fail_fit)
    monkeypatch.setattr(spatial_alignment, "_load_full_city_rows", fail_fit)

    result = run_spatial_alignment_workflow(
        reference_run_dir=reference_run_dir,
        dataset_path=dataset_path,
        folds_path=folds_path,
        output_dir=output_dir,
        model_name="random_forest",
        sample_rows_per_city=5000,
        city_selection="all",
        smoothing_radii_m=[30.0],
        skip_existing_predictions=True,
    )

    assert result.prediction_paths == (existing_prediction_path,)
    assert result.selection_table_path.name == "all_city_selection.csv"
    assert result.metrics_table_path.name == "spatial_alignment_metrics_all_cities.csv"
    metrics_df = pd.read_csv(result.metrics_table_path)
    assert len(metrics_df) == 1
    assert metrics_df.loc[0, "city_id"] == 6
    assert metrics_df.loc[0, "grid_reconstruction_status"] == "ok"


def test_spatial_alignment_map_path_is_deterministic() -> None:
    path = spatial_alignment_map_path(
        Path("figures") / "modeling" / "supplemental" / "spatial_alignment",
        "New Orleans",
        14,
        "random_forest",
        "medium",
    )

    assert path.as_posix().endswith(
        "figures/modeling/supplemental/spatial_alignment/new_orleans_city14_random_forest_medium_surface_alignment.png"
    )


def test_generate_spatial_alignment_maps_writes_manifest_and_png(tmp_path: Path) -> None:
    prediction_path = tmp_path / "denver_city06_random_forest_full_city_predictions.parquet"
    pd.DataFrame(_tiny_prediction_rows()).to_parquet(prediction_path, index=False)
    manifest_path = tmp_path / "tables" / "spatial_alignment_map_manifest.csv"

    manifest_df = generate_spatial_alignment_maps(
        prediction_paths=[prediction_path],
        figures_dir=tmp_path / "figures",
        manifest_path=manifest_path,
        scale_label="medium",
        threshold_fraction=1 / 9,
    )

    assert manifest_df.columns.tolist() == MAP_MANIFEST_COLUMNS
    assert len(manifest_df) == 1
    assert manifest_path.exists()
    figure_path = Path(manifest_df.loc[0, "figure_path"])
    assert figure_path.exists()
    assert figure_path.name == "denver_city06_random_forest_medium_surface_alignment.png"
    saved_manifest = pd.read_csv(manifest_path)
    assert saved_manifest.columns.tolist() == MAP_MANIFEST_COLUMNS
    assert saved_manifest.loc[0, "scale_label"] == "medium"
    assert saved_manifest.loc[0, "valid_cell_count"] == 9


def _tiny_prediction_rows() -> list[dict[str, object]]:
    transformer = Transformer.from_crs("EPSG:32613", "EPSG:4326", always_xy=True)
    rows: list[dict[str, object]] = []
    cell_id = 1
    for row_index in range(3):
        for col_index in range(3):
            x_m = 500_000.0 + (col_index * 30.0)
            y_m = 4_400_000.0 - (row_index * 30.0)
            lon, lat = transformer.transform(x_m, y_m)
            hotspot = row_index == 1 and col_index == 1
            rows.append(
                {
                    "city_id": 6,
                    "city_name": "Denver",
                    "climate_group": "hot_arid",
                    "outer_fold": 1,
                    "cell_id": cell_id,
                    "centroid_lon": lon,
                    "centroid_lat": lat,
                    "hotspot_10pct": int(hotspot),
                    "model_name": "random_forest",
                    "predicted_probability": 1.0 if hotspot else 0.0,
                    "prediction_scope": "full_city",
                    "training_sample_rows_per_city": 5000,
                    "source_reference_run_dir": "reference",
                }
            )
            cell_id += 1
    return rows
