from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.report_artifacts import (
    plot_city_signal_transfer_relationship,
    plot_city_signal_transfer_relationship_labeled,
    plot_selected_spatial_alignment_map_contrast,
    plot_spatial_alignment_medium_summary,
)


def test_city_signal_transfer_figures_render(tmp_path: Path) -> None:
    comparison = pd.DataFrame(
        [
            {
                "city_name": "Phoenix",
                "climate_group": "hot_arid",
                "class_1_f1_rf": 0.50,
                "class_1_recall_rf": 0.36,
                "pr_auc_rf": 0.14,
                "recall_at_top_10pct_rf": 0.18,
            },
            {
                "city_name": "Denver",
                "climate_group": "hot_arid",
                "class_1_f1_rf": 0.48,
                "class_1_recall_rf": 0.35,
                "pr_auc_rf": 0.15,
                "recall_at_top_10pct_rf": 0.20,
            },
            {
                "city_name": "New Orleans",
                "climate_group": "hot_humid",
                "class_1_f1_rf": 0.31,
                "class_1_recall_rf": 0.21,
                "pr_auc_rf": 0.18,
                "recall_at_top_10pct_rf": 0.18,
            },
            {
                "city_name": "Atlanta",
                "climate_group": "hot_humid",
                "class_1_f1_rf": 0.27,
                "class_1_recall_rf": 0.18,
                "pr_auc_rf": 0.18,
                "recall_at_top_10pct_rf": 0.24,
            },
            {
                "city_name": "Seattle",
                "climate_group": "mild_cool",
                "class_1_f1_rf": 0.38,
                "class_1_recall_rf": 0.26,
                "pr_auc_rf": 0.21,
                "recall_at_top_10pct_rf": 0.26,
            },
            {
                "city_name": "Portland",
                "climate_group": "mild_cool",
                "class_1_f1_rf": 0.45,
                "class_1_recall_rf": 0.32,
                "pr_auc_rf": 0.25,
                "recall_at_top_10pct_rf": 0.31,
            },
        ]
    )
    plain_path = tmp_path / "city_signal_transfer_relationship.png"
    labeled_path = tmp_path / "city_signal_transfer_relationship_labeled.png"

    plot_city_signal_transfer_relationship(comparison, plain_path)
    plot_city_signal_transfer_relationship_labeled(comparison, labeled_path)

    assert plain_path.exists()
    assert labeled_path.exists()
    assert plain_path.stat().st_size > 0
    assert labeled_path.stat().st_size > plain_path.stat().st_size


def test_spatial_alignment_medium_summary_renders(tmp_path: Path) -> None:
    metrics = pd.DataFrame(
        [
            {
                "city_id": 1,
                "city_name": "Phoenix",
                "climate_group": "hot_arid",
                "scale_label": "medium",
                "spearman_surface_corr": 0.21,
                "observed_mass_captured": 0.18,
                "top_region_overlap_fraction": 0.11,
            },
            {
                "city_id": 2,
                "city_name": "Nashville",
                "climate_group": "hot_humid",
                "scale_label": "medium",
                "spearman_surface_corr": 0.74,
                "observed_mass_captured": 0.49,
                "top_region_overlap_fraction": 0.41,
            },
            {
                "city_id": 3,
                "city_name": "San Francisco",
                "climate_group": "mild_cool",
                "scale_label": "medium",
                "spearman_surface_corr": -0.12,
                "observed_mass_captured": 0.04,
                "top_region_overlap_fraction": 0.02,
            },
            {
                "city_id": 4,
                "city_name": "Portland",
                "climate_group": "mild_cool",
                "scale_label": "medium",
                "spearman_surface_corr": 0.55,
                "observed_mass_captured": 0.31,
                "top_region_overlap_fraction": 0.25,
            },
            {
                "city_id": 5,
                "city_name": "Tucson",
                "climate_group": "hot_arid",
                "scale_label": "fine",
                "spearman_surface_corr": 0.31,
                "observed_mass_captured": 0.26,
                "top_region_overlap_fraction": 0.18,
            },
        ]
    )
    output_path = tmp_path / "spatial_alignment_medium_summary.png"

    plot_spatial_alignment_medium_summary(metrics, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_selected_spatial_alignment_map_contrast_renders(tmp_path: Path) -> None:
    metrics = pd.DataFrame(
        [
            {
                "city_name": "Nashville",
                "scale_label": "medium",
                "spearman_surface_corr": 0.75,
                "observed_mass_captured": 0.51,
                "top_region_overlap_fraction": 0.42,
            },
            {
                "city_name": "San Francisco",
                "scale_label": "medium",
                "spearman_surface_corr": 0.05,
                "observed_mass_captured": 0.04,
                "top_region_overlap_fraction": 0.02,
            },
        ]
    )
    nashville_path = tmp_path / "nashville.png"
    san_francisco_path = tmp_path / "san_francisco.png"
    output_path = tmp_path / "selected_spatial_alignment_map_contrast.png"

    nashville_image = np.ones((80, 240, 3), dtype=float)
    nashville_image[:, :, 0] = 0.75
    san_francisco_image = np.ones((80, 240, 3), dtype=float)
    san_francisco_image[:, :, 2] = 0.75
    plt.imsave(nashville_path, nashville_image)
    plt.imsave(san_francisco_path, san_francisco_image)

    plot_selected_spatial_alignment_map_contrast(
        metrics,
        nashville_path,
        san_francisco_path,
        output_path,
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0
