from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config import MODELING_SPATIAL_REPORTING_FIGURES, MODELING_SPATIAL_REPORTING_OUTPUTS
from src.modeling_config import DEFAULT_TOP_FRACTION, GROUP_COLUMN, TARGET_COLUMN
from src.modeling_reporting import DEFAULT_RF_FRONTIER_RUN_DIR

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SpatialReportingPaths:
    output_dir: Path
    figures_dir: Path
    markdown_path: Path
    selection_table_path: Path
    selected_points_path: Path
    selected_city_summary_path: Path


@dataclass(frozen=True)
class SpatialReportingResult:
    markdown_path: Path
    selection_table_path: Path
    selected_points_path: Path
    selected_city_summary_path: Path
    figure_paths: list[Path]


def resolve_spatial_reporting_paths(
    *,
    outputs_root: Path = MODELING_SPATIAL_REPORTING_OUTPUTS,
    figures_root: Path = MODELING_SPATIAL_REPORTING_FIGURES,
) -> SpatialReportingPaths:
    """Return the canonical held-out spatial reporting paths."""
    resolved_output_dir = outputs_root.resolve()
    resolved_figures_dir = figures_root.resolve()
    return SpatialReportingPaths(
        output_dir=resolved_output_dir,
        figures_dir=resolved_figures_dir,
        markdown_path=resolved_output_dir / "heldout_city_maps.md",
        selection_table_path=resolved_output_dir / "heldout_city_map_selection.csv",
        selected_points_path=resolved_output_dir / "heldout_city_map_points.parquet",
        selected_city_summary_path=resolved_output_dir / "heldout_city_map_city_summary.csv",
    )


def _require_file(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return path


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(_require_file(path).read_text(encoding="utf-8"))


def select_representative_cities_for_maps(
    city_metrics_df: pd.DataFrame,
    *,
    cities_per_climate: int = 1,
) -> pd.DataFrame:
    """Pick representative held-out cities by choosing the nearest PR-AUC median within each climate group."""
    required_columns = {"city_id", "city_name", "climate_group", "pr_auc", "recall_at_top_10pct", "outer_fold"}
    missing_columns = sorted(required_columns - set(city_metrics_df.columns))
    if missing_columns:
        raise ValueError(
            "City metrics are missing required columns for held-out map selection: "
            + ", ".join(missing_columns)
        )

    selected_frames: list[pd.DataFrame] = []
    for _, climate_df in city_metrics_df.groupby("climate_group", sort=True, dropna=False):
        working = climate_df.copy()
        median_pr_auc = float(working["pr_auc"].median())
        working["climate_group_pr_auc_median"] = median_pr_auc
        working["pr_auc_distance_from_climate_median"] = (working["pr_auc"] - median_pr_auc).abs()
        working = working.sort_values(
            [
                "pr_auc_distance_from_climate_median",
                "city_name",
                "city_id",
                "outer_fold",
            ]
        ).reset_index(drop=True)
        selected_frames.append(working.head(int(cities_per_climate)))

    selected = pd.concat(selected_frames, ignore_index=True) if selected_frames else pd.DataFrame()
    if selected.empty:
        return selected
    return selected.sort_values(["climate_group", "city_name", "city_id"]).reset_index(drop=True)


def _read_prediction_subset(run_dir: Path, city_ids: Sequence[int]) -> pd.DataFrame:
    prediction_path = _require_file(run_dir / "heldout_predictions.parquet")
    selected_columns = [
        "model_name",
        "outer_fold",
        "city_id",
        "city_name",
        "climate_group",
        "cell_id",
        "centroid_lon",
        "centroid_lat",
        TARGET_COLUMN,
        "predicted_probability",
    ]
    return pd.read_parquet(
        prediction_path,
        columns=selected_columns,
        filters=[(GROUP_COLUMN, "in", [int(city_id) for city_id in city_ids])],
    )


def derive_heldout_map_labels(
    predictions_df: pd.DataFrame,
    *,
    top_fraction: float = DEFAULT_TOP_FRACTION,
) -> pd.DataFrame:
    """Add predicted-hotspot and categorical error labels for held-out map exports."""
    if predictions_df.empty:
        return predictions_df.copy()

    parts: list[pd.DataFrame] = []
    for _, city_df in predictions_df.groupby("city_id", sort=True, dropna=False):
        working = city_df.sort_values("predicted_probability", ascending=False, kind="mergesort").copy()
        top_n = max(1, int(np.ceil(len(working) * float(top_fraction))))
        working["predicted_hotspot_10pct"] = False
        working.iloc[:top_n, working.columns.get_loc("predicted_hotspot_10pct")] = True
        working["prediction_residual"] = (
            working["predicted_probability"].astype("float64") - working[TARGET_COLUMN].astype("int8")
        )
        working["error_type"] = np.select(
            condlist=[
                working["predicted_hotspot_10pct"] & working[TARGET_COLUMN].astype(bool),
                working["predicted_hotspot_10pct"] & ~working[TARGET_COLUMN].astype(bool),
                ~working["predicted_hotspot_10pct"] & working[TARGET_COLUMN].astype(bool),
            ],
            choicelist=["true_positive", "false_positive", "false_negative"],
            default="true_negative",
        )
        parts.append(working.sort_values(["outer_fold", "cell_id"]).reset_index(drop=True))
    return pd.concat(parts, ignore_index=True)


def summarize_selected_map_cities(map_points_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize selected-city held-out map counts and error totals."""
    if map_points_df.empty:
        return pd.DataFrame(
            columns=[
                "city_id",
                "city_name",
                "climate_group",
                "outer_fold",
                "row_count",
                "predicted_hotspot_count",
                "true_hotspot_count",
                "true_positive_count",
                "false_positive_count",
                "false_negative_count",
                "true_negative_count",
            ]
        )

    rows: list[dict[str, object]] = []
    for group_keys, city_df in map_points_df.groupby(
        ["city_id", "city_name", "climate_group", "outer_fold"], sort=True, dropna=False
    ):
        city_id, city_name, climate_group, outer_fold = group_keys
        error_counts = city_df["error_type"].value_counts(dropna=False)
        rows.append(
            {
                "city_id": int(city_id),
                "city_name": city_name,
                "climate_group": climate_group,
                "outer_fold": int(outer_fold),
                "row_count": int(len(city_df)),
                "predicted_hotspot_count": int(city_df["predicted_hotspot_10pct"].sum()),
                "true_hotspot_count": int(city_df[TARGET_COLUMN].sum()),
                "true_positive_count": int(error_counts.get("true_positive", 0)),
                "false_positive_count": int(error_counts.get("false_positive", 0)),
                "false_negative_count": int(error_counts.get("false_negative", 0)),
                "true_negative_count": int(error_counts.get("true_negative", 0)),
            }
        )
    return pd.DataFrame(rows).sort_values(["climate_group", "city_name"]).reset_index(drop=True)


def _city_slug(city_name: str) -> str:
    return "".join(character.lower() if character.isalnum() else "_" for character in city_name).strip("_")


def _marker_size(n_rows: int) -> float:
    return float(min(8.0, max(1.5, 20000.0 / max(1, n_rows))))


def _style_map_axis(axis: plt.Axes, city_df: pd.DataFrame, title: str) -> None:
    lon_min = float(city_df["centroid_lon"].min())
    lon_max = float(city_df["centroid_lon"].max())
    lat_min = float(city_df["centroid_lat"].min())
    lat_max = float(city_df["centroid_lat"].max())
    lon_pad = max(0.0025, (lon_max - lon_min) * 0.03)
    lat_pad = max(0.0025, (lat_max - lat_min) * 0.03)
    axis.set_xlim(lon_min - lon_pad, lon_max + lon_pad)
    axis.set_ylim(lat_min - lat_pad, lat_max + lat_pad)
    axis.set_aspect("equal", adjustable="box")
    axis.set_xticks([])
    axis.set_yticks([])
    axis.set_title(title, fontsize=11)
    for spine in axis.spines.values():
        spine.set_visible(False)


def plot_heldout_city_map_triptych(city_df: pd.DataFrame, output_path: Path) -> Path:
    """Write predicted, true, and categorical error maps for one held-out city."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    city_name = str(city_df["city_name"].iloc[0])
    climate_group = str(city_df["climate_group"].iloc[0])
    marker_size = _marker_size(len(city_df))

    fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(14, 4.8), constrained_layout=True)

    predicted_colors = city_df["predicted_hotspot_10pct"].map({True: "#c64a32", False: "#d9d9d9"})
    axes[0].scatter(
        city_df["centroid_lon"],
        city_df["centroid_lat"],
        c=predicted_colors,
        s=marker_size,
        linewidths=0,
        alpha=0.9,
    )
    _style_map_axis(axes[0], city_df, "Predicted hotspot (top 10% risk)")

    true_colors = city_df[TARGET_COLUMN].astype(bool).map({True: "#6f1d1b", False: "#d9d9d9"})
    axes[1].scatter(
        city_df["centroid_lon"],
        city_df["centroid_lat"],
        c=true_colors,
        s=marker_size,
        linewidths=0,
        alpha=0.9,
    )
    _style_map_axis(axes[1], city_df, "True hotspot")

    error_palette = {
        "true_positive": "#7f0000",
        "false_positive": "#ef8a62",
        "false_negative": "#67a9cf",
        "true_negative": "#d9d9d9",
    }
    axes[2].scatter(
        city_df["centroid_lon"],
        city_df["centroid_lat"],
        c=city_df["error_type"].map(error_palette),
        s=marker_size,
        linewidths=0,
        alpha=0.9,
    )
    _style_map_axis(axes[2], city_df, "Categorical error map")

    fig.suptitle(f"{city_name} held-out benchmark map snapshot ({climate_group})", fontsize=13)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def _build_markdown(
    selection_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    figure_paths: Sequence[Path],
    metadata: dict[str, object],
) -> str:
    def _format_value(value: object) -> str:
        if pd.isna(value):
            return "n/a"
        if isinstance(value, (float, np.floating)):
            return f"{float(value):.4f}"
        return str(value)

    def _dataframe_to_markdown(df: pd.DataFrame) -> str:
        header = "| " + " | ".join(df.columns.astype(str)) + " |"
        separator = "| " + " | ".join(["---"] * len(df.columns)) + " |"
        rows_local = [header, separator]
        for _, row in df.iterrows():
            rows_local.append("| " + " | ".join(_format_value(row[column]) for column in df.columns) + " |")
        return "\n".join(rows_local)

    rows: list[str] = [
        "# Held-Out City Maps",
        "",
        "Purpose:",
        "",
        "- export deterministic held-out-city map deliverables from retained benchmark predictions without rerunning the benchmark ladder",
        "- keep the city-held-out cross-city benchmark as the canonical narrative while adding map-ready appendix/reporting figures",
        "",
        "Reference run:",
        "",
        f"- model: `{metadata.get('model_name')}`",
        f"- tuning preset: `{metadata.get('tuning_preset')}`",
        f"- retained sample rows per city: `{metadata.get('sample_rows_per_city')}`",
        f"- source run dir: `{metadata.get('output_dir')}`",
        "",
        "Selected representative cities:",
        "",
        _dataframe_to_markdown(selection_df),
        "",
        "Selected city error summary:",
        "",
        _dataframe_to_markdown(summary_df),
        "",
        "Figure files:",
        "",
    ]
    rows.extend(f"- `{figure_path}`" for figure_path in figure_paths)
    rows.extend(
        [
            "",
            "Interpretation note:",
            "",
            "These figures use saved held-out prediction artifacts from the retained benchmark checkpoint. "
            "They support the existing cross-city benchmark story and do not replace the city-held-out evaluation methodology.",
            "",
        ]
    )
    return "\n".join(rows)


def generate_heldout_spatial_reporting_artifacts(
    *,
    reference_run_dir: Path = DEFAULT_RF_FRONTIER_RUN_DIR,
    city_ids: Sequence[int] | None = None,
    cities_per_climate: int = 1,
    top_fraction: float = DEFAULT_TOP_FRACTION,
    outputs_root: Path = MODELING_SPATIAL_REPORTING_OUTPUTS,
    figures_root: Path = MODELING_SPATIAL_REPORTING_FIGURES,
) -> SpatialReportingResult:
    """Generate held-out-city map exports from a retained prediction artifact directory."""
    paths = resolve_spatial_reporting_paths(outputs_root=outputs_root, figures_root=figures_root)
    paths.output_dir.mkdir(parents=True, exist_ok=True)
    paths.figures_dir.mkdir(parents=True, exist_ok=True)

    resolved_run_dir = reference_run_dir.resolve()
    metadata = _load_json(resolved_run_dir / "run_metadata.json")
    city_metrics_df = pd.read_csv(_require_file(resolved_run_dir / "metrics_by_city.csv"))
    if city_ids is None:
        selection_df = select_representative_cities_for_maps(
            city_metrics_df=city_metrics_df,
            cities_per_climate=cities_per_climate,
        )
    else:
        selection_df = (
            city_metrics_df.loc[city_metrics_df["city_id"].isin([int(city_id) for city_id in city_ids])]
            .sort_values(["climate_group", "city_name", "city_id"])
            .reset_index(drop=True)
        )
    if selection_df.empty:
        raise ValueError("No held-out cities were selected for map export")

    selection_df["source_run_dir"] = str(resolved_run_dir)
    selection_df.to_csv(paths.selection_table_path, index=False)

    map_points_df = derive_heldout_map_labels(
        _read_prediction_subset(resolved_run_dir, city_ids=selection_df["city_id"].astype(int).tolist()),
        top_fraction=top_fraction,
    )
    map_points_df.to_parquet(paths.selected_points_path, index=False)

    summary_df = summarize_selected_map_cities(map_points_df)
    summary_df.to_csv(paths.selected_city_summary_path, index=False)

    figure_paths: list[Path] = []
    for city_name, city_df in map_points_df.groupby("city_name", sort=True, dropna=False):
        figure_path = paths.figures_dir / f"{_city_slug(str(city_name))}_heldout_map_triptych.png"
        plot_heldout_city_map_triptych(city_df=city_df, output_path=figure_path)
        figure_paths.append(figure_path)

    paths.markdown_path.write_text(
        _build_markdown(selection_df=selection_df, summary_df=summary_df, figure_paths=figure_paths, metadata=metadata),
        encoding="utf-8",
    )
    LOGGER.info("Wrote held-out city spatial reporting artifacts under %s", paths.output_dir)
    return SpatialReportingResult(
        markdown_path=paths.markdown_path,
        selection_table_path=paths.selection_table_path,
        selected_points_path=paths.selected_points_path,
        selected_city_summary_path=paths.selected_city_summary_path,
        figure_paths=figure_paths,
    )
