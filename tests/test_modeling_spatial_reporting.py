from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.modeling_spatial_reporting import (
    derive_heldout_map_labels,
    generate_heldout_spatial_reporting_artifacts,
    resolve_spatial_reporting_paths,
    select_representative_cities_for_maps,
    summarize_selected_map_cities,
)


def _write_spatial_reporting_fixture(run_dir: Path) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    city_metrics = pd.DataFrame(
        [
            {
                "model_name": "random_forest",
                "outer_fold": 0,
                "city_id": 1,
                "city_name": "Arroyo",
                "climate_group": "hot_arid",
                "row_count": 10,
                "positive_count": 1,
                "prevalence": 0.1,
                "pr_auc": 0.20,
                "recall_at_top_10pct": 0.30,
            },
            {
                "model_name": "random_forest",
                "outer_fold": 1,
                "city_id": 2,
                "city_name": "Basin",
                "climate_group": "hot_arid",
                "row_count": 10,
                "positive_count": 1,
                "prevalence": 0.1,
                "pr_auc": 0.24,
                "recall_at_top_10pct": 0.32,
            },
            {
                "model_name": "random_forest",
                "outer_fold": 4,
                "city_id": 5,
                "city_name": "Dune",
                "climate_group": "hot_arid",
                "row_count": 10,
                "positive_count": 1,
                "prevalence": 0.1,
                "pr_auc": 0.40,
                "recall_at_top_10pct": 0.42,
            },
            {
                "model_name": "random_forest",
                "outer_fold": 2,
                "city_id": 3,
                "city_name": "Cedar",
                "climate_group": "mild_cool",
                "row_count": 10,
                "positive_count": 1,
                "prevalence": 0.1,
                "pr_auc": 0.40,
                "recall_at_top_10pct": 0.44,
            },
            {
                "model_name": "random_forest",
                "outer_fold": 3,
                "city_id": 4,
                "city_name": "Delta",
                "climate_group": "mild_cool",
                "row_count": 10,
                "positive_count": 1,
                "prevalence": 0.1,
                "pr_auc": 0.48,
                "recall_at_top_10pct": 0.46,
            },
            {
                "model_name": "random_forest",
                "outer_fold": 5,
                "city_id": 6,
                "city_name": "Evergreen",
                "climate_group": "mild_cool",
                "row_count": 10,
                "positive_count": 1,
                "prevalence": 0.1,
                "pr_auc": 0.60,
                "recall_at_top_10pct": 0.50,
            },
        ]
    )
    predictions = pd.DataFrame(
        [
            {
                "model_name": "random_forest",
                "outer_fold": 1,
                "city_id": 2,
                "city_name": "Basin",
                "climate_group": "hot_arid",
                "cell_id": 200 + idx,
                "centroid_lon": -112.0 + (idx * 0.01),
                "centroid_lat": 33.0 + (idx * 0.01),
                "hotspot_10pct": idx == 0,
                "predicted_probability": score,
            }
            for idx, score in enumerate([0.90, 0.55, 0.20, 0.10])
        ]
        + [
            {
                "model_name": "random_forest",
                "outer_fold": 3,
                "city_id": 4,
                "city_name": "Delta",
                "climate_group": "mild_cool",
                "cell_id": 400 + idx,
                "centroid_lon": -122.0 + (idx * 0.01),
                "centroid_lat": 47.0 + (idx * 0.01),
                "hotspot_10pct": idx in {0, 2},
                "predicted_probability": score,
            }
            for idx, score in enumerate([0.80, 0.60, 0.40, 0.05])
        ]
    )
    city_metrics.to_csv(run_dir / "metrics_by_city.csv", index=False)
    predictions.to_parquet(run_dir / "heldout_predictions.parquet", index=False)
    (run_dir / "run_metadata.json").write_text(
        json.dumps(
            {
                "model_name": "random_forest",
                "tuning_preset": "frontier",
                "sample_rows_per_city": 5000,
                "output_dir": str(run_dir),
            }
        ),
        encoding="utf-8",
    )


def test_resolve_spatial_reporting_paths_uses_new_roots(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs" / "modeling" / "reporting" / "heldout_city_maps"
    figures_root = tmp_path / "figures" / "modeling" / "heldout_city_maps"

    paths = resolve_spatial_reporting_paths(outputs_root=outputs_root, figures_root=figures_root)

    assert paths.markdown_path == outputs_root / "heldout_city_maps.md"
    assert paths.selection_table_path == outputs_root / "heldout_city_map_selection.csv"
    assert paths.figures_dir == figures_root


def test_select_representative_cities_for_maps_uses_climate_median_distance() -> None:
    city_metrics = pd.DataFrame(
        [
            {"city_id": 1, "city_name": "Arroyo", "climate_group": "hot_arid", "outer_fold": 0, "pr_auc": 0.20, "recall_at_top_10pct": 0.30},
            {"city_id": 2, "city_name": "Basin", "climate_group": "hot_arid", "outer_fold": 1, "pr_auc": 0.24, "recall_at_top_10pct": 0.32},
            {"city_id": 5, "city_name": "Dune", "climate_group": "hot_arid", "outer_fold": 4, "pr_auc": 0.40, "recall_at_top_10pct": 0.42},
            {"city_id": 3, "city_name": "Cedar", "climate_group": "mild_cool", "outer_fold": 2, "pr_auc": 0.40, "recall_at_top_10pct": 0.44},
            {"city_id": 4, "city_name": "Delta", "climate_group": "mild_cool", "outer_fold": 3, "pr_auc": 0.48, "recall_at_top_10pct": 0.46},
            {"city_id": 6, "city_name": "Evergreen", "climate_group": "mild_cool", "outer_fold": 5, "pr_auc": 0.60, "recall_at_top_10pct": 0.50},
        ]
    )

    selected = select_representative_cities_for_maps(city_metrics)

    assert selected["city_name"].tolist() == ["Basin", "Delta"]


def test_derive_heldout_map_labels_and_summary_compute_expected_error_types() -> None:
    predictions = pd.DataFrame(
        [
            {
                "model_name": "random_forest",
                "outer_fold": 0,
                "city_id": 1,
                "city_name": "Arroyo",
                "climate_group": "hot_arid",
                "cell_id": idx,
                "centroid_lon": -112.0 + idx,
                "centroid_lat": 33.0 + idx,
                "hotspot_10pct": hotspot,
                "predicted_probability": probability,
            }
            for idx, (hotspot, probability) in enumerate(
                [
                    (True, 0.95),
                    (False, 0.60),
                    (True, 0.20),
                    (False, 0.10),
                ]
            )
        ]
    )

    labeled = derive_heldout_map_labels(predictions, top_fraction=0.25)
    summary = summarize_selected_map_cities(labeled)

    assert labeled["predicted_hotspot_10pct"].sum() == 1
    assert set(labeled["error_type"]) == {"true_positive", "false_negative", "true_negative"}
    assert int(summary.loc[0, "true_positive_count"]) == 1
    assert int(summary.loc[0, "false_negative_count"]) == 1


def test_generate_heldout_spatial_reporting_artifacts_writes_outputs_and_figures(workspace_tmp_path: Path) -> None:
    run_dir = workspace_tmp_path / "outputs" / "modeling" / "random_forest" / "rf_frontier"
    _write_spatial_reporting_fixture(run_dir)

    result = generate_heldout_spatial_reporting_artifacts(
        reference_run_dir=run_dir,
        outputs_root=workspace_tmp_path / "outputs" / "modeling" / "reporting" / "heldout_city_maps",
        figures_root=workspace_tmp_path / "figures" / "modeling" / "heldout_city_maps",
    )

    assert result.markdown_path.exists()
    assert result.selection_table_path.exists()
    assert result.selected_points_path.exists()
    assert result.selected_city_summary_path.exists()
    assert len(result.figure_paths) == 2
    assert all(path.exists() for path in result.figure_paths)

    markdown_text = result.markdown_path.read_text(encoding="utf-8")
    assert "Held-Out City Maps" in markdown_text
    assert "retained benchmark predictions" in markdown_text
