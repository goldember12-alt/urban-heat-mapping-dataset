"""Generate final-report tables and figures from project artifacts."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from src.load_cities import load_cities


CLIMATE_LABELS = {
    "hot_arid": "Hot arid",
    "hot_humid": "Hot humid",
    "mild_cool": "Mild cool",
}

CLIMATE_COLORS = {
    "Hot arid": "#c65d32",
    "Hot humid": "#2f7f6f",
    "Mild cool": "#4f6fb3",
}

FINAL_DATASET_COLUMNS = [
    {
        "Column": "city_id",
        "Definition": "Integer city identifier used for joins and grouped cross-validation.",
        "Role in report": "Grouping / metadata",
        "Primary predictor?": "No",
    },
    {
        "Column": "city_name",
        "Definition": "Human-readable city name.",
        "Role in report": "Metadata",
        "Primary predictor?": "No",
    },
    {
        "Column": "climate_group",
        "Definition": "Broad climate grouping label for the city.",
        "Role in report": "Predictor / stratifier",
        "Primary predictor?": "Yes",
    },
    {
        "Column": "cell_id",
        "Definition": "Cell identifier within the city grid.",
        "Role in report": "Cell metadata",
        "Primary predictor?": "No",
    },
    {
        "Column": "centroid_lon",
        "Definition": "Cell centroid longitude in WGS84.",
        "Role in report": "Mapping metadata",
        "Primary predictor?": "No",
    },
    {
        "Column": "centroid_lat",
        "Definition": "Cell centroid latitude in WGS84.",
        "Role in report": "Mapping metadata",
        "Primary predictor?": "No",
    },
    {
        "Column": "impervious_pct",
        "Definition": "NLCD impervious percentage for the cell.",
        "Role in report": "Predictor",
        "Primary predictor?": "Yes",
    },
    {
        "Column": "land_cover_class",
        "Definition": "NLCD land-cover class code for the cell.",
        "Role in report": "Predictor / water filter",
        "Primary predictor?": "Yes",
    },
    {
        "Column": "elevation_m",
        "Definition": "DEM-derived elevation in meters.",
        "Role in report": "Predictor",
        "Primary predictor?": "Yes",
    },
    {
        "Column": "dist_to_water_m",
        "Definition": "Distance from the cell to the nearest hydro feature in meters.",
        "Role in report": "Predictor",
        "Primary predictor?": "Yes",
    },
    {
        "Column": "ndvi_median_may_aug",
        "Definition": "Median May-August NDVI derived from AppEEARS MODIS/Terra MOD13A1.061 inputs.",
        "Role in report": "Predictor",
        "Primary predictor?": "Yes",
    },
    {
        "Column": "lst_median_may_aug",
        "Definition": "Median May-August 2023 daytime land surface temperature derived from ECOSTRESS/AppEEARS inputs.",
        "Role in report": "Outcome ingredient",
        "Primary predictor?": "No",
    },
    {
        "Column": "n_valid_ecostress_passes",
        "Definition": "Number of valid ECOSTRESS observations contributing to the cell-level LST summary.",
        "Role in report": "Quality filter / support field",
        "Primary predictor?": "No",
    },
    {
        "Column": "hotspot_10pct",
        "Definition": "Binary indicator for whether the cell falls in the within-city top 10% of valid LST values.",
        "Role in report": "Target",
        "Primary predictor?": "Target only",
    },
    {
        "Column": "tree_cover_proxy_pct_270m",
        "Definition": "Share of nearby 30 m cells within an approximately 270 m neighborhood in NLCD forest classes 41/42/43.",
        "Role in report": "Supplemental neighborhood-context feature",
        "Primary predictor?": "No",
    },
    {
        "Column": "vegetated_cover_proxy_pct_270m",
        "Definition": "Share of nearby 30 m cells within an approximately 270 m neighborhood in selected NLCD vegetated classes.",
        "Role in report": "Supplemental neighborhood-context feature",
        "Primary predictor?": "No",
    },
    {
        "Column": "impervious_pct_mean_270m",
        "Definition": "Neighborhood mean NLCD impervious percentage within an approximately 270 m window.",
        "Role in report": "Supplemental neighborhood-context feature",
        "Primary predictor?": "No",
    },
]


@dataclass(frozen=True)
class ReportArtifactPaths:
    """Input and output paths for the final-report artifact pass."""

    city_summary_path: Path
    city_outer_folds_path: Path
    benchmark_table_path: Path
    baseline_summary_path: Path
    climate_delta_path: Path
    city_error_comparison_path: Path
    within_transfer_city_comparison_path: Path
    spatial_alignment_metrics_path: Path
    logistic_run_dir: Path
    rf_run_dir: Path
    heldout_map_points_path: Path
    within_vs_cross_gap_source_path: Path
    nashville_alignment_map_source_path: Path
    san_francisco_alignment_map_source_path: Path
    tables_dir: Path
    figures_dir: Path

    @classmethod
    def from_project_root(cls, project_root: Path) -> "ReportArtifactPaths":
        """Build default report artifact paths from the repository root."""

        return cls(
            city_summary_path=project_root
            / "data_processed"
            / "modeling"
            / "final_dataset_city_summary.csv",
            city_outer_folds_path=project_root
            / "data_processed"
            / "modeling"
            / "city_outer_folds.csv",
            benchmark_table_path=project_root
            / "outputs"
            / "modeling"
            / "reporting"
            / "tables"
            / "cross_city_benchmark_report_benchmark_table.csv",
            baseline_summary_path=project_root
            / "outputs"
            / "modeling"
            / "baselines"
            / "metrics_summary.csv",
            climate_delta_path=project_root
            / "outputs"
            / "modeling"
            / "reporting"
            / "tables"
            / "cross_city_benchmark_report_city_error_by_climate.csv",
            city_error_comparison_path=project_root
            / "outputs"
            / "modeling"
            / "reporting"
            / "tables"
            / "cross_city_benchmark_report_city_error_comparison.csv",
            within_transfer_city_comparison_path=project_root
            / "outputs"
            / "modeling"
            / "partner_data"
            / "per_city_logistic_rf_results"
            / "tables"
            / "partner_vs_repo_city_comparison.csv",
            spatial_alignment_metrics_path=project_root
            / "outputs"
            / "modeling"
            / "supplemental"
            / "spatial_alignment_all_cities"
            / "tables"
            / "spatial_alignment_metrics_all_cities.csv",
            logistic_run_dir=project_root
            / "outputs"
            / "modeling"
            / "logistic_saga"
            / "full_allfolds_s5000_sampled-full-allfolds_2026-04-07_235825",
            rf_run_dir=project_root
            / "outputs"
            / "modeling"
            / "random_forest"
            / "frontier_allfolds_s5000_frontier-check_2026-04-11_173430",
            heldout_map_points_path=project_root
            / "outputs"
            / "modeling"
            / "reporting"
            / "heldout_city_maps"
            / "heldout_city_map_points.parquet",
            within_vs_cross_gap_source_path=project_root
            / "figures"
            / "modeling"
            / "supplemental"
            / "within_city_all_cities"
            / "within_city_all_cities_within_vs_cross_gap.png",
            nashville_alignment_map_source_path=project_root
            / "figures"
            / "modeling"
            / "supplemental"
            / "spatial_alignment_all_cities"
            / "nashville_city20_random_forest_medium_surface_alignment.png",
            san_francisco_alignment_map_source_path=project_root
            / "figures"
            / "modeling"
            / "supplemental"
            / "spatial_alignment_all_cities"
            / "san_francisco_city23_random_forest_medium_surface_alignment.png",
            tables_dir=project_root / "docs" / "report" / "tables",
            figures_dir=project_root / "docs" / "report" / "figures",
        )


def _format_climate_group(value: str) -> str:
    return CLIMATE_LABELS.get(value, value.replace("_", "-").title())


def build_data_sources_table() -> pd.DataFrame:
    """Return the source-to-variable table used by the final report."""

    rows = [
        {
            "Source": "U.S. Census urban areas",
            "Product/layer": "2020 TIGERweb urban-area polygon",
            "Constructed variable(s)": "Study-area and core-city geometry; 30 m city grid",
            "Role": "Study region and grid target",
        },
        {
            "Source": "NLCD",
            "Product/layer": "2021 land-cover raster",
            "Constructed variable(s)": "land_cover_class",
            "Role": "Predictor; open-water filter",
        },
        {
            "Source": "NLCD",
            "Product/layer": "2021 impervious percentage raster",
            "Constructed variable(s)": "impervious_pct",
            "Role": "Built-intensity predictor",
        },
        {
            "Source": "USGS 3DEP",
            "Product/layer": "1 arc-second DEM",
            "Constructed variable(s)": "elevation_m",
            "Role": "Terrain predictor",
        },
        {
            "Source": "NHDPlus HR",
            "Product/layer": "High-resolution hydrography",
            "Constructed variable(s)": "dist_to_water_m",
            "Role": "Water-proximity predictor",
        },
        {
            "Source": "MODIS/Terra via AppEEARS",
            "Product/layer": "MOD13A1.061 NDVI, May-Aug. 2023",
            "Constructed variable(s)": "ndvi_median_may_aug",
            "Role": "Vegetation predictor",
        },
        {
            "Source": "ECOSTRESS via AppEEARS",
            "Product/layer": "ECO_L2T_LSTE.002 LST, May-Aug. 2023",
            "Constructed variable(s)": "lst_median_may_aug; n_valid_ecostress_passes; hotspot_10pct",
            "Role": "Outcome source and quality support",
        },
    ]
    return pd.DataFrame(rows)


def build_final_dataset_columns_table() -> pd.DataFrame:
    """Return a concise schema table for the report appendix."""

    return pd.DataFrame(FINAL_DATASET_COLUMNS)


def build_climate_summary_table(city_summary: pd.DataFrame) -> pd.DataFrame:
    """Aggregate city-level audit rows into a climate-group dataset summary."""

    summary = city_summary.copy()
    summary["climate_group"] = summary["climate_group"].map(_format_climate_group)
    grouped = (
        summary.groupby("climate_group", sort=False)
        .agg(
            city_count=("city_id", "nunique"),
            total_rows=("row_count", "sum"),
            total_hotspot_positives=("hotspot_positive_count", "sum"),
            hotspot_non_missing_count=("hotspot_non_missing_count", "sum"),
            min_city_rows=("row_count", "min"),
            median_city_rows=("row_count", "median"),
            max_city_rows=("row_count", "max"),
            median_valid_ecostress_passes=("n_valid_ecostress_passes_median", "median"),
        )
        .reset_index()
    )
    grouped["hotspot_prevalence"] = (
        grouped["total_hotspot_positives"] / grouped["hotspot_non_missing_count"]
    )
    grouped = grouped[
        [
            "climate_group",
            "city_count",
            "total_rows",
            "total_hotspot_positives",
            "hotspot_prevalence",
            "min_city_rows",
            "median_city_rows",
            "max_city_rows",
            "median_valid_ecostress_passes",
        ]
    ]
    grouped["median_city_rows"] = grouped["median_city_rows"].round().astype("int64")
    grouped["median_valid_ecostress_passes"] = grouped[
        "median_valid_ecostress_passes"
    ].round(1)
    grouped["hotspot_prevalence"] = grouped["hotspot_prevalence"].round(4)
    return grouped.rename(
        columns={
            "climate_group": "Climate group",
            "city_count": "City count",
            "total_rows": "Total rows",
            "total_hotspot_positives": "Hotspot count",
            "hotspot_prevalence": "Hotspot prev.",
            "min_city_rows": "Min rows",
            "median_city_rows": "Median rows",
            "max_city_rows": "Max rows",
            "median_valid_ecostress_passes": "Median valid passes",
        }
    )


def build_benchmark_report_table(
    benchmark_table: pd.DataFrame,
    baseline_summary: pd.DataFrame,
) -> pd.DataFrame:
    """Return a compact benchmark table for the report Tables/Figures section."""

    def _sample_label(rows_per_city: int) -> str:
        return f"{rows_per_city // 1000}k sampled" if rows_per_city % 1000 == 0 else f"{rows_per_city:,} sampled"

    tuned_labels = {
        "full_allfolds_s5000_sampled-full-allfolds_2026-04-07_235825": "Logistic 5k",
        "full_allfolds_s20000_samplecurve-20k_2026-04-08_021152": "Logistic 20k",
        "frontier_allfolds_s5000_frontier-check_2026-04-11_173430": "RF 5k",
    }
    tuned_notes = {
        "full_allfolds_s5000_sampled-full-allfolds_2026-04-07_235825": "Matched 5k linear comparison for random forest.",
        "full_allfolds_s20000_samplecurve-20k_2026-04-08_021152": "Higher-sample logistic context, not the matched RF comparison.",
        "frontier_allfolds_s5000_frontier-check_2026-04-11_173430": "Best current 5k random-forest specification.",
    }
    baseline_labels = {
        "global_mean_baseline": "Global mean",
        "climate_only_baseline": "Climate only",
        "impervious_only_baseline": "Impervious only",
        "land_cover_only_baseline": "Land cover only",
    }
    baseline_notes = {
        "global_mean_baseline": "Training-city prevalence assigned to held-out rows.",
        "climate_only_baseline": "Training-city prevalence by climate group.",
        "impervious_only_baseline": "Training-city prevalence by imperviousness bin.",
        "land_cover_only_baseline": "Training-city prevalence by land-cover class.",
    }
    rows: list[dict[str, object]] = [
        {
            "Model checkpoint": "No-skill / prevalence reference",
            "Rows per city": "5k sampled",
            "Pooled PR AUC": 0.1000,
            "Mean city PR AUC": 0.1000,
            "Recall at top 10%": 0.1000,
            "Runtime (min)": pd.NA,
            "Report note": "Random ranking reference for a 10% hotspot target.",
        }
    ]
    for model_name, label in baseline_labels.items():
        baseline_row = baseline_summary.loc[baseline_summary["model_name"] == model_name].iloc[0]
        rows.append(
            {
                "Model checkpoint": label,
                "Rows per city": "5k sampled",
                "Pooled PR AUC": round(float(baseline_row["pooled_pr_auc"]), 4),
                "Mean city PR AUC": round(float(baseline_row["mean_city_pr_auc"]), 4),
                "Recall at top 10%": round(float(baseline_row["pooled_recall_at_top_10pct"]), 4),
                "Runtime (min)": pd.NA,
                "Report note": baseline_notes[model_name],
            }
        )
    for run_label, label in tuned_labels.items():
        tuned_row = benchmark_table.loc[benchmark_table["run_label"] == run_label].iloc[0]
        rows.append(
            {
                "Model checkpoint": label,
                "Rows per city": _sample_label(int(tuned_row["rows_per_city"])),
                "Pooled PR AUC": round(float(tuned_row["pooled_pr_auc"]), 4),
                "Mean city PR AUC": round(float(tuned_row["mean_city_pr_auc"]), 4),
                "Recall at top 10%": round(float(tuned_row["pooled_recall_at_top_10pct"]), 4),
                "Runtime (min)": round(float(tuned_row["runtime_minutes"]), 1),
                "Report note": tuned_notes[run_label],
            }
        )
    return pd.DataFrame(rows)


def build_climate_delta_report_table(climate_delta: pd.DataFrame) -> pd.DataFrame:
    """Return a compact RF-minus-logistic climate-delta table for the report."""

    table = climate_delta.copy()
    table["Climate group"] = table["climate_group"].map(_format_climate_group)
    table["Mean PR AUC delta"] = table["mean_pr_auc_delta"].round(4)
    table["Mean recall delta"] = table["mean_recall_delta"].round(4)
    table["Median PR AUC delta"] = table["median_pr_auc_delta"].round(4)
    table["Median recall delta"] = table["median_recall_delta"].round(4)
    return table[
        [
            "Climate group",
            "city_count",
            "rf_pr_auc_wins",
            "logistic_pr_auc_wins",
            "Mean PR AUC delta",
            "rf_recall_wins",
            "logistic_recall_wins",
            "Mean recall delta",
        ]
    ].rename(
        columns={
            "city_count": "City count",
            "rf_pr_auc_wins": "RF PR AUC wins",
            "logistic_pr_auc_wins": "Logit PR AUC wins",
            "rf_recall_wins": "RF recall wins",
            "logistic_recall_wins": "Logit recall wins",
        }
    )


def build_fold_level_comparison_table(logistic_run_dir: Path, rf_run_dir: Path) -> pd.DataFrame:
    """Return RF-minus-logistic metrics by outer city-held-out fold."""

    logistic = pd.read_csv(logistic_run_dir / "metrics_by_fold.csv")
    rf = pd.read_csv(rf_run_dir / "metrics_by_fold.csv")
    merged = logistic.merge(
        rf,
        on=[
            "outer_fold",
            "train_city_count",
            "test_city_count",
            "train_row_count",
            "test_row_count",
            "test_positive_count",
            "test_prevalence",
        ],
        suffixes=("_logistic", "_rf"),
        validate="one_to_one",
    )
    merged["RF - Logit PR AUC"] = merged["pr_auc_rf"] - merged["pr_auc_logistic"]
    merged["RF - Logit R@10"] = (
        merged["recall_at_top_10pct_rf"] - merged["recall_at_top_10pct_logistic"]
    )
    table = merged[
        [
            "outer_fold",
            "train_row_count",
            "test_row_count",
            "test_positive_count",
            "test_prevalence",
            "pr_auc_logistic",
            "pr_auc_rf",
            "RF - Logit PR AUC",
            "recall_at_top_10pct_logistic",
            "recall_at_top_10pct_rf",
            "RF - Logit R@10",
        ]
    ].rename(
        columns={
            "outer_fold": "Outer fold",
            "train_row_count": "Train rows",
            "test_row_count": "Test rows",
            "test_positive_count": "Pos.",
            "test_prevalence": "Test prev.",
            "pr_auc_logistic": "Logit PR AUC",
            "pr_auc_rf": "RF PR AUC",
            "recall_at_top_10pct_logistic": "Logit R@10",
            "recall_at_top_10pct_rf": "RF R@10",
        }
    )
    numeric_columns = [
        "Test prev.",
        "Logit PR AUC",
        "RF PR AUC",
        "RF - Logit PR AUC",
        "Logit R@10",
        "RF R@10",
        "RF - Logit R@10",
    ]
    table[numeric_columns] = table[numeric_columns].round(4)
    return table


def _paired_metric_summary(series: pd.Series) -> dict[str, object]:
    return {
        "Mean delta": round(float(series.mean()), 4),
        "Median delta": round(float(series.median()), 4),
        "SD delta": round(float(series.std(ddof=1)), 4),
        "Min delta": round(float(series.min()), 4),
        "Max delta": round(float(series.max()), 4),
        "RF wins": int((series > 0).sum()),
        "Logistic wins": int((series < 0).sum()),
        "Ties": int((series == 0).sum()),
    }


def build_city_paired_summary_table(city_error: pd.DataFrame) -> pd.DataFrame:
    """Summarize city-level paired RF-minus-logistic deltas."""

    rows = []
    for label, column in [
        ("City PR AUC", "pr_auc_delta_rf_minus_logistic"),
        ("City R@10", "recall_delta_rf_minus_logistic"),
    ]:
        summary = _paired_metric_summary(city_error[column])
        summary["Metric"] = label
        rows.append(summary)
    return pd.DataFrame(rows)[
        [
            "Metric",
            "Mean delta",
            "Median delta",
            "SD delta",
            "Min delta",
            "Max delta",
            "RF wins",
            "Logistic wins",
            "Ties",
        ]
    ]


def build_city_fold_appendix_table(city_outer_folds: pd.DataFrame) -> pd.DataFrame:
    """Return city/fold composition with final dataset row and target counts."""

    table = city_outer_folds.copy()
    table["Climate group"] = table["climate_group"].map(_format_climate_group)
    table["Hotspot prev."] = table["hotspot_prevalence"].round(4)
    return table[
        [
            "city_id",
            "city_name",
            "Climate group",
            "row_count",
            "hotspot_positive_count",
            "Hotspot prev.",
            "outer_fold",
        ]
    ].rename(
        columns={
            "city_id": "City ID",
            "city_name": "City",
            "row_count": "Final rows",
            "hotspot_positive_count": "Hotspot count",
            "outer_fold": "Outer fold",
        }
    )


def build_model_specification_table() -> pd.DataFrame:
    """Return auditable model and baseline specifications for the appendix."""

    rows = [
        {
            "Model / baseline": "No-skill / prevalence reference",
            "Predictors": "None",
            "Preprocessing": "None",
            "Tuning grid or rule": "Reference PR AUC and top-decile recall equal to the 10% target rate.",
            "Scoring": "PR AUC; R@10",
            "Grouped CV?": "Reference only",
        },
        {
            "Model / baseline": "Global-mean baseline",
            "Predictors": "None",
            "Preprocessing": "Training-city target mean",
            "Tuning grid or rule": "Predict the training-city hotspot prevalence for all held-out rows.",
            "Scoring": "PR AUC; R@10",
            "Grouped CV?": "Outer city folds only",
        },
        {
            "Model / baseline": "Climate-only baseline",
            "Predictors": "climate_group",
            "Preprocessing": "Training-city category means",
            "Tuning grid or rule": "Predict training-city hotspot prevalence by climate group.",
            "Scoring": "PR AUC; R@10",
            "Grouped CV?": "Outer city folds only",
        },
        {
            "Model / baseline": "Land-cover-only baseline",
            "Predictors": "land_cover_class",
            "Preprocessing": "Training-city category means",
            "Tuning grid or rule": "Predict training-city hotspot prevalence by land-cover class.",
            "Scoring": "PR AUC; R@10",
            "Grouped CV?": "Outer city folds only",
        },
        {
            "Model / baseline": "Impervious-only baseline",
            "Predictors": "impervious_pct",
            "Preprocessing": "Training-city decile bins",
            "Tuning grid or rule": "Predict training-city hotspot prevalence by imperviousness bin.",
            "Scoring": "PR AUC; R@10",
            "Grouped CV?": "Outer city folds only",
        },
        {
            "Model / baseline": "Logistic SAGA 5k",
            "Predictors": "impervious_pct, land_cover_class, elevation_m, dist_to_water_m, ndvi_median_may_aug, climate_group",
            "Preprocessing": "Training-only imputation, numeric scaling, and categorical one-hot encoding inside sklearn Pipeline",
            "Tuning grid or rule": "C = 0.01, 0.1, 1.0, 10.0; l1_ratio = 0.0, 0.2, 0.5, 0.8, 1.0",
            "Scoring": "Inner-CV AP; held-out PR AUC; R@10",
            "Grouped CV?": "Yes, grouped outer folds and grouped inner CV",
        },
        {
            "Model / baseline": "Random forest 5k",
            "Predictors": "Same six non-thermal predictors as logistic SAGA",
            "Preprocessing": "Training-only imputation and categorical one-hot encoding inside sklearn Pipeline",
            "Tuning grid or rule": "n_estimators = 200, 300; max_depth = 10, 20; max_features = sqrt; min_samples_leaf = 1, 5",
            "Scoring": "Inner-CV AP; held-out PR AUC; R@10",
            "Grouped CV?": "Yes, grouped outer folds and grouped inner CV",
        },
    ]
    return pd.DataFrame(rows)


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _summarize_param_grid(param_grid: list[dict]) -> str:
    summaries = []
    for grid in param_grid:
        parts = []
        for key, value in grid.items():
            display_key = key.replace("model__", "")
            if isinstance(value, list):
                value_text = "/".join(str(item) for item in value)
            else:
                value_text = str(value)
            parts.append(f"{display_key}: {value_text}")
        summaries.append("; ".join(parts))
    return " | ".join(summaries)


def _summarize_best_params(best_params: pd.DataFrame) -> str:
    unique_params = best_params["best_params_json"].dropna().drop_duplicates().tolist()
    parsed = [json.loads(value) for value in unique_params]
    summaries = []
    for params in parsed:
        pieces = [
            f"{key.replace('model__', '')}={value}"
            for key, value in sorted(params.items())
        ]
        summaries.append(", ".join(pieces))
    return "Fold-specific winners: " + " | ".join(summaries)


def build_retained_model_metadata_table(
    benchmark_table: pd.DataFrame,
    logistic_run_dir: Path,
    rf_run_dir: Path,
) -> pd.DataFrame:
    """Return appendix metadata for the retained logistic and RF benchmark runs."""

    run_specs = [
        ("Logistic SAGA 5k", logistic_run_dir),
        ("Random forest 5k", rf_run_dir),
    ]
    rows = []
    for label, run_dir in run_specs:
        metadata = _load_json(run_dir / "run_metadata.json")
        best_params = pd.read_csv(run_dir / "best_params_by_fold.csv")
        metrics_row = benchmark_table[
            benchmark_table["source_path"].astype(str).str.endswith(run_dir.name)
        ].iloc[0]
        rows.append(
            {
                "Model": label,
                "Model family": metadata["model_name"],
                "Tuning preset": metadata["tuning_preset"],
                "Rows/city": metadata["sample_rows_per_city"],
                "Outer folds": ", ".join(str(fold) for fold in metadata["selected_outer_folds"]),
                "Inner CV splits": metadata["inner_cv_splits_requested"],
                "Scoring": "AP" if metadata["scoring"] == "average_precision" else metadata["scoring"],
                "Candidates": metadata["search_space"]["param_candidate_count"],
                "Inner fits": metadata["search_space"]["estimated_total_inner_fits"],
                "Pooled PR AUC": round(metrics_row["pooled_pr_auc"], 4),
                "Mean city PR AUC": round(metrics_row["mean_city_pr_auc"], 4),
                "Recall@top10": round(metrics_row["pooled_recall_at_top_10pct"], 4),
                "Grid summary": _summarize_param_grid(metadata["param_grid"]),
                "Selected parameters": _summarize_best_params(best_params),
                "Run directory": str(run_dir),
            }
        )
    return pd.DataFrame(rows)


def plot_city_row_counts(city_summary: pd.DataFrame, output_path: Path) -> None:
    """Write a horizontal bar chart of city row counts by climate group."""

    plot_df = city_summary.copy()
    plot_df["climate_group_display"] = plot_df["climate_group"].map(_format_climate_group)
    plot_df["row_count_millions"] = plot_df["row_count"] / 1_000_000
    plot_df = plot_df.sort_values(
        ["climate_group_display", "row_count_millions"],
        ascending=[True, True],
    )

    height = max(7.5, len(plot_df) * 0.28)
    fig, ax = plt.subplots(figsize=(9, height))
    ax.barh(
        plot_df["city_name"],
        plot_df["row_count_millions"],
        color=[CLIMATE_COLORS[group] for group in plot_df["climate_group_display"]],
    )
    ax.set_xlabel("Final dataset rows (millions)")
    ax.set_ylabel("")
    ax.set_title("Final Dataset Row Counts by City and Climate Group")
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)

    handles = [
        plt.Rectangle((0, 0), 1, 1, color=color)
        for _, color in CLIMATE_COLORS.items()
    ]
    ax.legend(
        handles,
        list(CLIMATE_COLORS.keys()),
        title="Climate group",
        loc="lower right",
        frameon=False,
    )
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_study_city_locations(output_path: Path) -> None:
    """Write a climate-colored point map of the 30 selected city centers."""

    cities = load_cities().copy()
    cities["Climate group"] = cities["climate_group"].map(_format_climate_group)
    cities["label"] = cities["city_name"] + ", " + cities["state"]

    fig, ax = plt.subplots(figsize=(12, 7.2))
    ax.set_facecolor("#f7f7f2")
    ax.set_xlim(-126, -66)
    ax.set_ylim(24, 50)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Study City Locations by Climate Group")
    ax.grid(color="#d0d0c8", linewidth=0.7, alpha=0.7)
    ax.set_axisbelow(True)

    for group, group_df in cities.groupby("Climate group", sort=False):
        ax.scatter(
            group_df["lon"],
            group_df["lat"],
            s=72,
            color=CLIMATE_COLORS[group],
            edgecolor="white",
            linewidth=0.8,
            label=group,
            zorder=3,
        )

    label_offsets = {
        "Phoenix": (0.4, -0.65),
        "Tucson": (0.4, -0.85),
        "Las Vegas": (0.35, 0.45),
        "Albuquerque": (0.35, 0.45),
        "El Paso": (0.35, -0.6),
        "Denver": (0.4, 0.45),
        "Salt Lake City": (0.35, 0.45),
        "Fresno": (0.35, 0.45),
        "Bakersfield": (0.35, -0.6),
        "Reno": (0.35, 0.45),
        "Houston": (0.35, -0.6),
        "Columbia": (0.35, 0.45),
        "Richmond": (0.35, 0.45),
        "New Orleans": (0.35, -0.6),
        "Tampa": (0.35, 0.45),
        "Miami": (0.35, -0.55),
        "Jacksonville": (0.35, 0.45),
        "Atlanta": (0.35, -0.6),
        "Charlotte": (0.35, 0.45),
        "Nashville": (0.35, 0.45),
        "Seattle": (0.35, 0.45),
        "Portland": (0.35, -0.55),
        "San Francisco": (0.35, 0.45),
        "San Jose": (0.35, -0.55),
        "Los Angeles": (0.35, 0.45),
        "San Diego": (0.35, -0.55),
        "Chicago": (0.35, 0.45),
        "Minneapolis": (0.35, 0.45),
        "Detroit": (0.35, 0.45),
        "Boston": (0.35, 0.45),
    }
    for _, row in cities.iterrows():
        dx, dy = label_offsets[row["city_name"]]
        ax.text(
            row["lon"] + dx,
            row["lat"] + dy,
            row["city_name"],
            fontsize=7.2,
            color="#222222",
            bbox={
                "boxstyle": "round,pad=0.15",
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.72,
            },
            zorder=4,
        )

    ax.legend(title="Climate group", loc="lower left", frameon=True, framealpha=0.95)
    fig.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_benchmark_metric_comparison(benchmark_report: pd.DataFrame, output_path: Path) -> None:
    """Write the report benchmark figure with a no-skill reference line."""

    plot_df = benchmark_report.loc[
        benchmark_report["Model checkpoint"].isin(
            [
                "No-skill / prevalence reference",
                "Impervious only",
                "Land cover only",
                "Logistic 5k",
                "Logistic 20k",
                "RF 5k",
            ]
        )
    ].copy()
    metric_specs = [
        ("Pooled PR AUC", "Pooled PR AUC"),
        ("Mean city PR AUC", "Mean City PR AUC"),
        ("Recall at top 10%", "Recall At Top 10%"),
    ]
    color_map = {
        "No-skill / prevalence reference": "#999999",
        "Impervious only": "#8f6f4f",
        "Land cover only": "#8f6f4f",
        "Logistic 5k": "#2f6c8f",
        "Logistic 20k": "#9fb8c8",
        "RF 5k": "#9b3d2f",
    }
    fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(14, 4.6), constrained_layout=True)
    x = np.arange(len(plot_df))
    labels = plot_df["Model checkpoint"].str.replace(" / ", " /\n").str.replace(" context", "\ncontext")
    for axis, (column, title) in zip(axes, metric_specs):
        axis.bar(x, plot_df[column].to_numpy(dtype="float64"), color=[color_map[label] for label in plot_df["Model checkpoint"]])
        axis.axhline(0.10, color="#333333", linewidth=1.0, linestyle="--", alpha=0.8)
        axis.text(len(plot_df) - 0.6, 0.102, "10% reference", ha="right", va="bottom", fontsize=8)
        axis.set_title(title)
        axis.set_xticks(x)
        axis.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
        axis.set_ylim(0.0, 0.22)
        axis.grid(axis="y", alpha=0.25)
        axis.set_axisbelow(True)
    fig.suptitle("City-Held-Out Benchmark Metrics", fontsize=13)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def _diagram_box(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    lines: list[str],
    *,
    fill: str = "#ffffff",
) -> None:
    box = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=18",
        linewidth=2,
        edgecolor="#304b5a",
        facecolor=fill,
    )
    ax.add_patch(box)
    ax.text(x + width / 2, y + height - 40, title, ha="center", va="center", fontsize=13, fontweight="bold", color="#20333d")
    start_y = y + height - 80
    for index, line in enumerate(lines):
        ax.text(x + width / 2, start_y - index * 25, line, ha="center", va="center", fontsize=9.5, color="#304b5a")


def _diagram_arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float]) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=24,
            linewidth=2.2,
            color="#8b5e3c",
            shrinkA=0,
            shrinkB=0,
        )
    )


def plot_workflow_overview(output_path: Path) -> None:
    """Write the report workflow diagram as a PNG."""

    fig, ax = plt.subplots(figsize=(14, 5.2))
    ax.set_xlim(0, 1400)
    ax.set_ylim(0, 520)
    ax.axis("off")
    ax.set_facecolor("#fbf8f2")
    fig.patch.set_facecolor("#fbf8f2")

    _diagram_box(ax, 40, 300, 230, 150, "Study Design", ["30 cities", "Census urban area", "plus 2 km buffer"], fill="#eef4f7")
    _diagram_box(ax, 310, 300, 260, 150, "City Grids", ["Local UTM master grid", "30 m cells", "core and buffered extents"])
    _diagram_box(
        ax,
        620,
        260,
        320,
        230,
        "Input Layers",
        [
            "MODIS/Terra MOD13A1.061",
            "NDVI via AppEEARS, May-Aug 2023",
            "ECOSTRESS LST via AppEEARS",
            "NLCD land cover and impervious",
            "DEM and hydrography",
        ],
    )
    _diagram_box(ax, 1010, 300, 300, 150, "Per-City Features", ["Aligned to the master grid", "Cell-level feature table", "per city"], fill="#eef4f7")
    _diagram_box(ax, 170, 50, 320, 150, "Final Dataset", ["71,394,894 rows", "17 columns", "one row per 30 m grid cell"])
    _diagram_box(ax, 540, 50, 360, 150, "Audit And Split Contract", ["Required columns and missingness audit", "Binary target validation", "Deterministic city-held-out folds"], fill="#eef4f7")
    _diagram_box(ax, 970, 50, 380, 150, "Modeling And Delivery", ["Leakage-safe cross-city benchmarking", "Held-out prediction tables and maps", "Transfer-oriented model package"])

    _diagram_arrow(ax, (270, 375), (310, 375))
    _diagram_arrow(ax, (570, 375), (620, 375))
    _diagram_arrow(ax, (940, 375), (1010, 375))
    _diagram_arrow(ax, (1160, 300), (1160, 235))
    ax.plot([1160, 330, 330], [235, 235, 200], color="#8b5e3c", linewidth=2.2)
    _diagram_arrow(ax, (490, 125), (540, 125))
    _diagram_arrow(ax, (900, 125), (970, 125))
    ax.text(
        700,
        22,
        "Canonical benchmark story: data construction leads to a city-held-out transfer test, not a same-city interpolation exercise.",
        ha="center",
        va="center",
        fontsize=10,
        color="#304b5a",
    )
    fig.savefig(output_path, dpi=200, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


def plot_evaluation_design(output_path: Path) -> None:
    """Write the report city-held-out evaluation diagram as a PNG."""

    fig, ax = plt.subplots(figsize=(12.6, 5.0))
    ax.set_xlim(0, 1200)
    ax.set_ylim(0, 500)
    ax.axis("off")
    ax.set_facecolor("#fbf8f2")
    fig.patch.set_facecolor("#fbf8f2")

    ax.text(
        42,
        455,
        "City-held-out transfer design",
        ha="left",
        va="center",
        fontsize=18,
        fontweight="bold",
        color="#253b47",
    )
    ax.text(
        42,
        426,
        "Each fold withholds complete cities; model fitting never sees those cities until final scoring.",
        ha="left",
        va="center",
        fontsize=11,
        color="#304b5a",
    )

    _diagram_box(
        ax,
        40,
        250,
        250,
        130,
        "30-City Panel",
        ["Balanced climate groups", "One grid-cell table"],
        fill="#eef4f7",
    )
    _diagram_box(
        ax,
        360,
        250,
        500,
        130,
        "One Outer Fold",
        [],
    )
    _diagram_box(
        ax,
        930,
        250,
        230,
        130,
        "Final Scoring",
        ["Predict held-out cities", "Report PR AUC and R@10"],
        fill="#eef4f7",
    )

    square_size = 22
    x0, y0 = 405, 304
    for index in range(30):
        row = index // 15
        col = index % 15
        is_heldout = index >= 24
        color = "#b34a33" if is_heldout else "#7aa0b8"
        ax.add_patch(
            FancyBboxPatch(
                (x0 + col * 27, y0 - row * 31),
                square_size,
                square_size,
                boxstyle="round,pad=0,rounding_size=3",
                facecolor=color,
                edgecolor="white",
                linewidth=0.8,
                alpha=0.96,
            )
        )
    ax.text(
        610,
        266,
        "24 training cities; 6 held-out cities",
        ha="center",
        va="center",
        fontsize=10.0,
        color="#304b5a",
    )
    ax.add_patch(FancyBboxPatch((432, 214), 18, 18, boxstyle="round,pad=0,rounding_size=3", facecolor="#7aa0b8", edgecolor="none"))
    ax.text(457, 223, "Training cities", ha="left", va="center", fontsize=10.5, color="#304b5a")
    ax.add_patch(FancyBboxPatch((610, 214), 18, 18, boxstyle="round,pad=0,rounding_size=3", facecolor="#b34a33", edgecolor="none"))
    ax.text(635, 223, "Held-out cities", ha="left", va="center", fontsize=10.5, color="#304b5a")

    _diagram_arrow(ax, (290, 315), (360, 315))
    _diagram_arrow(ax, (860, 315), (930, 315))

    _diagram_box(
        ax,
        190,
        55,
        820,
        145,
        "Leakage Control",
        [
            "Imputation, scaling, encoding, feature processing, and tuning",
            "are fit on training cities only.",
            "Held-out cities are used once, for final evaluation.",
        ],
    )
    ax.text(
        600,
        24,
        "Primary metric: PR AUC. Supporting metric: recall among the top 10% highest-risk held-out cells.",
        ha="center",
        va="center",
        fontsize=10,
        color="#304b5a",
    )
    fig.savefig(output_path, dpi=200, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


def plot_city_metric_deltas(city_error: pd.DataFrame, output_path: Path) -> None:
    """Write readable city-level RF-minus-logistic deltas with climate-group coloring."""

    ordered = city_error.copy()
    ordered["Climate group"] = ordered["climate_group"].map(_format_climate_group)
    ordered = ordered.sort_values("pr_auc_delta_rf_minus_logistic", ascending=True).reset_index(drop=True)
    y_positions = np.arange(len(ordered))
    colors = [CLIMATE_COLORS[group] for group in ordered["Climate group"]]
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(13, 10.5), constrained_layout=True, sharey=True)
    for axis, column, title, xlabel in [
        (
            axes[0],
            "pr_auc_delta_rf_minus_logistic",
            "RF - Logistic PR AUC by City",
            "Delta in PR AUC",
        ),
        (
            axes[1],
            "recall_delta_rf_minus_logistic",
            "RF - Logistic Recall@10% by City",
            "Delta in recall at top 10%",
        ),
    ]:
        axis.barh(y_positions, ordered[column], color=colors)
        axis.axvline(0.0, color="black", linewidth=1)
        axis.set_title(title)
        axis.set_xlabel(xlabel)
        axis.set_ylim(-0.7, len(ordered) - 0.3)
        axis.grid(axis="x", alpha=0.25)
        axis.set_axisbelow(True)
    axes[0].set_yticks(y_positions)
    axes[0].set_yticklabels(ordered["city_name"], fontsize=9)
    axes[1].set_yticks(y_positions)
    axes[1].set_yticklabels([])

    x_limits = [(-0.14, 0.21), (-0.09, 0.37)]
    for axis, limit in zip(axes, x_limits):
        axis.set_xlim(*limit)
        axis.tick_params(axis="y", length=0)

    for y_position, city_name in zip(y_positions, ordered["city_name"]):
        axes[0].text(
            -0.128,
            y_position,
            city_name,
            ha="left",
            va="center",
            fontsize=8.8,
            color="#222222",
        )

    handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in CLIMATE_COLORS.values()]
    axes[0].legend(handles, list(CLIMATE_COLORS.keys()), title="Climate group", loc="lower right", frameon=False)
    fig.suptitle("City-Level Random-Forest Minus Logistic Performance", fontsize=13)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_city_rf_pr_auc(city_error: pd.DataFrame, output_path: Path) -> None:
    """Write absolute retained random-forest PR AUC by held-out city."""

    plot_df = city_error.copy()
    plot_df["Climate group"] = plot_df["climate_group"].map(_format_climate_group)
    plot_df = plot_df.sort_values("pr_auc_rf", ascending=True).reset_index(drop=True)
    y_positions = np.arange(len(plot_df))
    colors = [CLIMATE_COLORS[group] for group in plot_df["Climate group"]]

    fig, ax = plt.subplots(figsize=(9, 10.5))
    ax.barh(y_positions, plot_df["pr_auc_rf"], color=colors)
    ax.axvline(0.10, color="#333333", linewidth=1.2, linestyle="--", alpha=0.85)
    ax.text(0.103, len(plot_df) - 1.0, "10% reference", ha="left", va="center", fontsize=8.5)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(plot_df["city_name"], fontsize=9)
    ax.set_xlabel("Random-forest city PR AUC")
    ax.set_ylabel("")
    ax.set_title("Absolute Random-Forest Performance by Held-Out City")
    ax.set_xlim(0.06, max(0.48, float(plot_df["pr_auc_rf"].max()) + 0.03))
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)

    handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in CLIMATE_COLORS.values()]
    ax.legend(handles, list(CLIMATE_COLORS.keys()), title="Climate group", loc="lower right", frameon=False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def _select_spatial_alignment_labels(plot_df: pd.DataFrame) -> set[str]:
    """Select a small deterministic set of high/low cities for the report plot."""

    label_cities: set[str] = set()
    for column in [
        "spearman_surface_corr",
        "observed_mass_captured",
        "top_region_overlap_fraction",
    ]:
        label_cities.add(str(plot_df.loc[plot_df[column].idxmax(), "city_name"]))
        label_cities.add(str(plot_df.loc[plot_df[column].idxmin(), "city_name"]))

    # Nashville and San Francisco anchor the companion map contrast in the appendix.
    for city_name in ["Nashville", "San Francisco"]:
        if city_name in set(plot_df["city_name"].astype(str)):
            label_cities.add(city_name)
    return label_cities


def plot_spatial_alignment_medium_summary(metrics: pd.DataFrame, output_path: Path) -> None:
    """Write a report-ready medium-scale all-city spatial-alignment summary."""

    plot_df = metrics.loc[metrics["scale_label"].astype(str).eq("medium")].copy()
    if plot_df.empty:
        raise ValueError("No medium-scale spatial-alignment rows found")
    if plot_df["city_id"].nunique() != len(plot_df):
        raise ValueError("Expected one medium-scale spatial-alignment row per city")

    plot_df["Climate group"] = plot_df["climate_group"].map(_format_climate_group)
    plot_df = plot_df.sort_values("spearman_surface_corr").reset_index(drop=True)
    label_cities = _select_spatial_alignment_labels(plot_df)
    size_values = plot_df["top_region_overlap_fraction"].astype(float)
    marker_sizes = 115 + (size_values - size_values.min()) / max(float(size_values.max() - size_values.min()), 1e-9) * 265

    fig, ax = plt.subplots(figsize=(10.4, 7.4), dpi=240)
    for climate_label, climate_df in plot_df.groupby("Climate group", sort=False):
        row_indices = climate_df.index.to_numpy()
        ax.scatter(
            climate_df["spearman_surface_corr"],
            climate_df["observed_mass_captured"],
            s=marker_sizes[row_indices],
            color=CLIMATE_COLORS[climate_label],
            edgecolor="white",
            linewidth=0.9,
            alpha=0.92,
            label=climate_label,
        )

    mean_spearman = float(plot_df["spearman_surface_corr"].mean())
    mean_mass = float(plot_df["observed_mass_captured"].mean())
    ax.axvline(mean_spearman, color="#525252", linewidth=1.0, linestyle="--", alpha=0.7)
    ax.axhline(mean_mass, color="#525252", linewidth=1.0, linestyle="--", alpha=0.7)
    ax.text(
        mean_spearman + 0.012,
        0.055,
        f"Mean Spearman = {mean_spearman:.2f}",
        fontsize=9.2,
        color="#333333",
    )
    ax.text(
        -0.12,
        mean_mass + 0.010,
        f"Mean mass captured = {mean_mass:.2f}",
        fontsize=9.2,
        color="#333333",
    )

    label_offsets = [
        (7, 6),
        (7, -7),
        (-7, 6),
        (-7, -7),
        (10, 0),
        (-10, 0),
        (0, 10),
        (0, -10),
    ]
    for label_index, row in enumerate(plot_df.loc[plot_df["city_name"].isin(label_cities)].itertuples(index=False)):
        dx, dy = label_offsets[label_index % len(label_offsets)]
        ax.annotate(
            str(row.city_name),
            (float(row.spearman_surface_corr), float(row.observed_mass_captured)),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=8.8,
            ha="left" if dx >= 0 else "right",
            va="bottom" if dy >= 0 else "top",
            color="#252525",
            bbox={
                "boxstyle": "round,pad=0.16",
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.82,
            },
        )

    ax.set_title("Medium-Scale Spatial Alignment Varies Across Held-Out Cities", loc="left", fontsize=14, fontweight="bold")
    ax.set_xlabel("Spearman correlation between smoothed predicted and observed surfaces", fontsize=10.5)
    ax.set_ylabel("Observed hotspot mass captured in predicted top regions", fontsize=10.5)
    ax.set_xlim(-0.16, 0.84)
    ax.set_ylim(0.00, 0.56)
    ax.grid(True, color="#ddd2bf", linewidth=0.7, alpha=0.72)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    climate_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=color,
            markeredgecolor="white",
            markersize=8,
            label=label,
        )
        for label, color in CLIMATE_COLORS.items()
    ]
    size_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor="#bdbdbd",
            markeredgecolor="white",
            markersize=size,
            label=label,
        )
        for size, label in [(6, "Lower overlap"), (10, "Higher overlap")]
    ]
    first_legend = ax.legend(handles=climate_handles, title="Climate group", loc="upper left", frameon=False, fontsize=9.5)
    ax.add_artist(first_legend)
    ax.legend(handles=size_handles, title="Top-region overlap", loc="lower right", frameon=False, fontsize=9.5)
    fig.text(
        0.02,
        0.01,
        "Supplemental RF full-city diagnostic at 300 m smoothing. Points summarize broad spatial placement, not exact-cell retrieval.",
        fontsize=9.0,
        color="#4a4a4a",
    )
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    fig.savefig(output_path, dpi=240, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


def plot_selected_spatial_alignment_map_contrast(
    metrics: pd.DataFrame,
    nashville_map_path: Path,
    san_francisco_map_path: Path,
    output_path: Path,
) -> None:
    """Write a focused high/low spatial-alignment map contrast for the appendix."""

    medium = metrics.loc[metrics["scale_label"].astype(str).eq("medium")].copy()
    by_city = {str(row.city_name): row for row in medium.itertuples(index=False)}
    for city_name in ["Nashville", "San Francisco"]:
        if city_name not in by_city:
            raise ValueError(f"Missing medium-scale spatial-alignment metrics for {city_name}")

    rows = [
        ("Nashville", nashville_map_path, by_city["Nashville"]),
        ("San Francisco", san_francisco_map_path, by_city["San Francisco"]),
    ]

    crop_specs = [
        ("Observed smoothed hotspot surface", (0.015, 0.180)),
        ("Predicted smoothed risk surface", (0.205, 0.375)),
        ("Top-region overlap", (0.800, 0.985)),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(11.2, 6.4), dpi=240)
    for row_index, (city_name, image_path, metric_row) in enumerate(rows):
        if not image_path.exists():
            raise FileNotFoundError(image_path)
        image = plt.imread(image_path)
        height, width = image.shape[:2]
        y0 = int(height * 0.115)
        y1 = int(height * 0.705)
        if width < 1000:
            crop_specs = [
                ("Observed smoothed hotspot surface", (0.00, 0.333)),
                ("Predicted smoothed risk surface", (0.333, 0.666)),
                ("Top-region overlap", (0.666, 1.00)),
            ]

        for col_index, (panel_title, (x0_frac, x1_frac)) in enumerate(crop_specs):
            axis = axes[row_index, col_index]
            x0 = int(width * x0_frac)
            x1 = int(width * x1_frac)
            axis.imshow(image[y0:y1, x0:x1])
            axis.set_xticks([])
            axis.set_yticks([])
            for spine in axis.spines.values():
                spine.set_visible(False)
            if row_index == 0:
                axis.set_title(panel_title, fontsize=8.8, fontweight="bold", pad=4)

        row_y = 0.925 if row_index == 0 else 0.485
        fig.text(
            0.015,
            row_y,
            (
                f"{city_name}: Spearman {float(metric_row.spearman_surface_corr):.2f}, "
                f"mass {float(metric_row.observed_mass_captured):.2f}, "
                f"overlap {float(metric_row.top_region_overlap_fraction):.2f}"
            ),
            fontsize=9.0,
            fontweight="bold",
            ha="left",
            va="top",
        )

    fig.text(
        0.01,
        0.018,
        (
            "Selected 300 m smoothing contrast from held-out random-forest full-city spatial diagnostics. "
            "Overlap colors: gray = neither, orange = observed only, blue = predicted only, green = overlap."
        ),
        fontsize=7.7,
        color="#4a4a4a",
    )
    fig.subplots_adjust(left=0.015, right=0.995, top=0.88, bottom=0.075, hspace=0.18, wspace=0.02)
    fig.savefig(output_path, dpi=240, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


def _plot_signal_panel(
    axis: plt.Axes,
    data: pd.DataFrame,
    x_column: str,
    y_column: str,
    title: str,
    x_label: str,
    y_label: str,
    *,
    annotate_points: bool = False,
) -> None:
    """Draw one within-city versus city-held-out signal panel."""

    for climate_key, climate_df in data.groupby("climate_group", sort=False):
        label = _format_climate_group(str(climate_key))
        axis.scatter(
            climate_df[x_column],
            climate_df[y_column],
            s=36,
            color=CLIMATE_COLORS[label],
            edgecolor="white",
            linewidth=0.6,
            alpha=0.9,
            label=label,
        )
    if annotate_points:
        x_min = float(data[x_column].min())
        x_max = float(data[x_column].max())
        y_min = float(data[y_column].min())
        y_max = float(data[y_column].max())
        x_pad = max(0.012, (x_max - x_min) * 0.14)
        y_pad = max(0.012, (y_max - y_min) * 0.16)
        axis.set_xlim(x_min - x_pad, x_max + x_pad)
        axis.set_ylim(y_min - y_pad, y_max + y_pad)
    r_value = float(data[[x_column, y_column]].corr(method="pearson").iloc[0, 1])
    axis.set_title(title, loc="left", fontsize=12.5, fontweight="bold")
    axis.text(0.02, 0.93, f"Pearson r = {r_value:.2f}", transform=axis.transAxes, fontsize=9)
    axis.set_xlabel(x_label)
    axis.set_ylabel(y_label)
    axis.grid(True, color="#dbc7aa", linewidth=0.7, alpha=0.6)
    axis.set_axisbelow(True)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    if annotate_points:
        _annotate_signal_points(axis, data, x_column, y_column)


def _build_signal_label_order(
    data: pd.DataFrame,
    x_column: str,
    y_column: str,
) -> pd.DataFrame:
    """Return a stable crowded-first ordering for signal-point labels."""

    points = data[[x_column, y_column]].to_numpy(dtype=float)
    x_span = max(float(np.ptp(points[:, 0])), 1e-9)
    y_span = max(float(np.ptp(points[:, 1])), 1e-9)
    normalized = np.column_stack(
        ((points[:, 0] - float(points[:, 0].min())) / x_span, (points[:, 1] - float(points[:, 1].min())) / y_span)
    )
    crowding_scores: list[float] = []
    for idx, point in enumerate(normalized):
        deltas = normalized - point
        distances = np.sqrt(np.square(deltas).sum(axis=1))
        distances[idx] = np.inf
        nearest = np.sort(distances)[:3]
        crowding_scores.append(float(nearest.sum()))

    ordered = data.copy()
    ordered["_crowding_score"] = crowding_scores
    ordered["_label_length"] = ordered["city_name"].astype(str).str.len()
    ordered = ordered.sort_values(
        by=["_crowding_score", "_label_length", "city_name"],
        ascending=[True, False, True],
        kind="mergesort",
    )
    return ordered.drop(columns=["_crowding_score", "_label_length"])


def _estimate_label_box_pixels(text: str, dpi: float, font_size: float) -> tuple[float, float]:
    """Approximate a text-label bounding box in display pixels."""

    px_per_point = dpi / 72.0
    width_px = max(36.0, (len(text) * font_size * 0.62 + 8.0) * px_per_point)
    height_px = (font_size * 1.65 + 4.0) * px_per_point
    return width_px, height_px


def _build_label_box(
    point_x_px: float,
    point_y_px: float,
    width_px: float,
    height_px: float,
    dx_points: float,
    dy_points: float,
    dpi: float,
) -> tuple[float, float, float, float, str, str]:
    """Translate an offset-point annotation into a display-pixel rectangle."""

    px_per_point = dpi / 72.0
    dx_px = dx_points * px_per_point
    dy_px = dy_points * px_per_point
    if dx_points >= 0:
        x0 = point_x_px + dx_px
        x1 = x0 + width_px
        ha = "left"
    else:
        x1 = point_x_px + dx_px
        x0 = x1 - width_px
        ha = "right"
    if dy_points >= 0:
        y0 = point_y_px + dy_px
        y1 = y0 + height_px
        va = "bottom"
    else:
        y1 = point_y_px + dy_px
        y0 = y1 - height_px
        va = "top"
    return x0, y0, x1, y1, ha, va


def _overlap_area(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> float:
    """Return the display-space overlap area between two label boxes."""

    x_overlap = max(0.0, min(first[2], second[2]) - max(first[0], second[0]))
    y_overlap = max(0.0, min(first[3], second[3]) - max(first[1], second[1]))
    return x_overlap * y_overlap


def _annotate_signal_points(
    axis: plt.Axes,
    data: pd.DataFrame,
    x_column: str,
    y_column: str,
) -> None:
    """Annotate city signal points with deterministic low-overlap labels."""

    ordered = _build_signal_label_order(data, x_column, y_column)
    axis.figure.canvas.draw()
    axis_box = axis.get_window_extent()
    dpi = float(axis.figure.dpi)
    candidate_offsets = [
        (7.0, 6.0),
        (7.0, -6.0),
        (-7.0, 6.0),
        (-7.0, -6.0),
        (0.0, 9.0),
        (0.0, -9.0),
        (10.0, 0.0),
        (-10.0, 0.0),
        (11.0, 10.0),
        (11.0, -10.0),
        (-11.0, 10.0),
        (-11.0, -10.0),
    ]
    placed_boxes: list[tuple[float, float, float, float]] = []
    for row in ordered.itertuples(index=False):
        label = str(row.city_name)
        point_x_px, point_y_px = axis.transData.transform(
            (float(getattr(row, x_column)), float(getattr(row, y_column)))
        )
        label_width_px, label_height_px = _estimate_label_box_pixels(label, dpi, font_size=7.0)

        best_choice: tuple[float, float, float, float, str, str, float, float] | None = None
        best_penalty: float | None = None
        for dx_points, dy_points in candidate_offsets:
            x0, y0, x1, y1, ha, va = _build_label_box(
                point_x_px,
                point_y_px,
                label_width_px,
                label_height_px,
                dx_points,
                dy_points,
                dpi,
            )
            outside_penalty = (
                max(0.0, axis_box.x0 - x0)
                + max(0.0, x1 - axis_box.x1)
                + max(0.0, axis_box.y0 - y0)
                + max(0.0, y1 - axis_box.y1)
            ) * 12.0
            overlap_penalty = sum(
                _overlap_area((x0, y0, x1, y1), placed_box) for placed_box in placed_boxes
            )
            distance_penalty = abs(dx_points) + abs(dy_points) * 0.8
            total_penalty = outside_penalty + overlap_penalty + distance_penalty
            if best_penalty is None or total_penalty < best_penalty:
                best_penalty = total_penalty
                best_choice = (x0, y0, x1, y1, ha, va, dx_points, dy_points)

        if best_choice is None:
            continue

        box = best_choice[:4]
        placed_boxes.append(box)
        _, _, _, _, ha, va, dx_points, dy_points = best_choice
        axis.annotate(
            label,
            (float(getattr(row, x_column)), float(getattr(row, y_column))),
            xytext=(dx_points, dy_points),
            textcoords="offset points",
            ha=ha,
            va=va,
            fontsize=7.0,
            color="#2f2618",
            bbox={
                "boxstyle": "round,pad=0.16",
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.82,
            },
            zorder=6,
        )


def plot_city_signal_transfer_relationship(comparison: pd.DataFrame, output_path: Path) -> None:
    """Write the report-facing city signal-shift figure with consistent climate labels."""

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.9), dpi=240)
    _plot_signal_panel(
        axes[0],
        comparison,
        "class_1_f1_rf",
        "pr_auc_rf",
        "RF City Ranking Shifts",
        "Within-City RF Hotspot F1",
        "City-Held-Out RF PR AUC",
    )
    _plot_signal_panel(
        axes[1],
        comparison,
        "class_1_recall_rf",
        "recall_at_top_10pct_rf",
        "Retrieval Signal Shifts",
        "Within-City Hotspot Recall",
        "City-Held-Out RF Recall @ Top 10%",
    )
    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=color,
            markeredgecolor="white",
            markersize=7,
            label=label,
        )
        for label, color in CLIMATE_COLORS.items()
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, fontsize=10.5)
    fig.subplots_adjust(left=0.095, right=0.985, top=0.90, bottom=0.17, wspace=0.25)
    fig.savefig(output_path, dpi=240, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


def plot_city_signal_transfer_relationship_labeled(
    comparison: pd.DataFrame,
    output_path: Path,
) -> None:
    """Write a labeled Figure 5 variant with city names on both panels."""

    fig, axes = plt.subplots(1, 2, figsize=(13.6, 6.7), dpi=240)
    _plot_signal_panel(
        axes[0],
        comparison,
        "class_1_f1_rf",
        "pr_auc_rf",
        "RF City Ranking Shifts",
        "Within-City RF Hotspot F1",
        "City-Held-Out RF PR AUC",
        annotate_points=True,
    )
    _plot_signal_panel(
        axes[1],
        comparison,
        "class_1_recall_rf",
        "recall_at_top_10pct_rf",
        "Retrieval Signal Shifts",
        "Within-City Hotspot Recall",
        "City-Held-Out RF Recall @ Top 10%",
        annotate_points=True,
    )
    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=color,
            markeredgecolor="white",
            markersize=7,
            label=label,
        )
        for label, color in CLIMATE_COLORS.items()
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, fontsize=10.5)
    fig.subplots_adjust(left=0.075, right=0.992, top=0.92, bottom=0.13, wspace=0.23)
    fig.savefig(output_path, dpi=240, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


def _draw_report_map_panel(
    axis: plt.Axes,
    city_df: pd.DataFrame,
    colors: pd.Series,
    title: str,
    *,
    marker_size: float,
) -> None:
    axis.scatter(
        city_df["map_x"],
        city_df["map_y"],
        c=colors,
        s=marker_size,
        linewidths=0,
        alpha=0.96,
    )
    x_min = float(city_df["map_x"].min())
    x_max = float(city_df["map_x"].max())
    y_min = float(city_df["map_y"].min())
    y_max = float(city_df["map_y"].max())
    x_pad = max(0.0015, (x_max - x_min) * 0.018)
    y_pad = max(0.0015, (y_max - y_min) * 0.018)
    axis.set_xlim(x_min - x_pad, x_max + x_pad)
    axis.set_ylim(y_min - y_pad, y_max + y_pad)
    axis.set_aspect("equal", adjustable="box")
    axis.set_xticks([])
    axis.set_yticks([])
    axis.set_title(title, fontsize=13.5, fontweight="bold", pad=8)
    axis.set_facecolor("white")
    for spine in axis.spines.values():
        spine.set_visible(False)


def plot_denver_heldout_map_focus(map_points: pd.DataFrame, output_path: Path) -> None:
    """Write the report-facing Denver held-out triptych from retained map points."""

    city_df = map_points.loc[
        map_points["city_name"].astype(str).str.casefold() == "denver"
    ].copy()
    if city_df.empty:
        raise ValueError("No Denver rows found in held-out map points")

    lat_scale = float(np.cos(np.deg2rad(city_df["centroid_lat"].mean())))
    city_df["map_x"] = city_df["centroid_lon"] * lat_scale
    city_df["map_y"] = city_df["centroid_lat"]
    marker_size = float(min(12.0, max(5.0, 42000.0 / max(1, len(city_df)))))

    fig, axes = plt.subplots(1, 3, figsize=(14.5, 6.1), dpi=260)
    neutral = "#cfcfcf"
    predicted_color = "#c64a32"
    observed_color = "#6f1d1b"
    false_positive_color = "#ef8a62"
    false_negative_color = "#4f9fc4"
    predicted_colors = city_df["predicted_hotspot_10pct"].astype(bool).map(
        {True: predicted_color, False: neutral}
    )
    observed_colors = city_df["hotspot_10pct"].astype(bool).map(
        {True: observed_color, False: neutral}
    )
    error_colors = city_df["error_type"].map(
        {
            "true_positive": "#7f0000",
            "false_positive": false_positive_color,
            "false_negative": false_negative_color,
            "true_negative": neutral,
        }
    )

    _draw_report_map_panel(
        axes[0],
        city_df,
        predicted_colors,
        "Predicted Top-Decile Cells",
        marker_size=marker_size,
    )
    _draw_report_map_panel(
        axes[1],
        city_df,
        observed_colors,
        "Observed Hotspot Cells",
        marker_size=marker_size,
    )
    _draw_report_map_panel(
        axes[2],
        city_df,
        error_colors,
        "Error Pattern",
        marker_size=marker_size,
    )

    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor="#7f0000",
            markersize=8,
            label="True positive",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=false_positive_color,
            markersize=8,
            label="False positive",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=false_negative_color,
            markersize=8,
            label="False negative",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=neutral,
            markersize=8,
            label="Other cells",
        ),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=10.5)
    fig.subplots_adjust(left=0.01, right=0.995, top=0.91, bottom=0.14, wspace=0.035)
    fig.savefig(output_path, dpi=260, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def generate_report_artifacts(project_root: Path) -> list[Path]:
    """Generate high-priority report tables and the optional row-count figure."""

    paths = ReportArtifactPaths.from_project_root(project_root)
    paths.tables_dir.mkdir(parents=True, exist_ok=True)
    paths.figures_dir.mkdir(parents=True, exist_ok=True)

    city_summary = pd.read_csv(paths.city_summary_path)
    city_outer_folds = pd.read_csv(paths.city_outer_folds_path)
    benchmark_table = pd.read_csv(paths.benchmark_table_path)
    baseline_summary = pd.read_csv(paths.baseline_summary_path)
    climate_delta = pd.read_csv(paths.climate_delta_path)
    city_error = pd.read_csv(paths.city_error_comparison_path)
    within_transfer_comparison = pd.read_csv(paths.within_transfer_city_comparison_path)
    spatial_alignment_metrics = pd.read_csv(paths.spatial_alignment_metrics_path)
    map_points = pd.read_parquet(paths.heldout_map_points_path)
    data_sources = build_data_sources_table()
    final_columns = build_final_dataset_columns_table()
    climate_summary = build_climate_summary_table(city_summary)
    benchmark_report = build_benchmark_report_table(benchmark_table, baseline_summary)
    climate_delta_report = build_climate_delta_report_table(climate_delta)
    fold_comparison = build_fold_level_comparison_table(paths.logistic_run_dir, paths.rf_run_dir)
    city_paired_summary = build_city_paired_summary_table(city_error)
    city_fold_appendix = build_city_fold_appendix_table(city_outer_folds)
    model_specifications = build_model_specification_table()
    retained_metadata = build_retained_model_metadata_table(
        benchmark_table,
        paths.logistic_run_dir,
        paths.rf_run_dir,
    )

    data_sources_path = paths.tables_dir / "data_sources_variables.csv"
    final_columns_path = paths.tables_dir / "final_dataset_columns.csv"
    climate_summary_path = paths.tables_dir / "final_dataset_by_climate_group.csv"
    benchmark_report_path = paths.tables_dir / "benchmark_metrics.csv"
    climate_delta_report_path = paths.tables_dir / "rf_vs_logistic_by_climate.csv"
    fold_comparison_path = paths.tables_dir / "rf_vs_logistic_by_fold.csv"
    city_paired_summary_path = paths.tables_dir / "rf_vs_logistic_city_paired_summary.csv"
    city_fold_appendix_path = paths.tables_dir / "city_fold_composition.csv"
    model_specifications_path = paths.tables_dir / "model_baseline_specifications.csv"
    retained_metadata_path = paths.tables_dir / "retained_model_run_metadata.csv"
    row_counts_path = paths.figures_dir / "final_dataset_city_row_counts.png"
    study_locations_path = paths.figures_dir / "study_city_points.png"
    workflow_overview_path = paths.figures_dir / "workflow_overview.png"
    evaluation_design_path = paths.figures_dir / "evaluation_design.png"
    benchmark_figure_path = paths.figures_dir / "benchmark_metrics.png"
    city_signal_transfer_path = paths.figures_dir / "city_signal_transfer_relationship.png"
    city_signal_transfer_labeled_path = paths.figures_dir / "city_signal_transfer_relationship_labeled.png"
    city_delta_figure_path = paths.figures_dir / "city_metric_deltas.png"
    city_rf_pr_auc_figure_path = paths.figures_dir / "city_rf_pr_auc.png"
    denver_map_path = paths.figures_dir / "heldout_denver_map_focus.png"
    spatial_alignment_summary_path = paths.figures_dir / "spatial_alignment_medium_summary.png"
    within_vs_cross_gap_path = paths.figures_dir / "within_vs_cross_gap.png"
    selected_alignment_contrast_path = paths.figures_dir / "selected_spatial_alignment_map_contrast.png"
    nashville_alignment_map_path = (
        paths.figures_dir / "nashville_city20_random_forest_medium_surface_alignment.png"
    )
    san_francisco_alignment_map_path = (
        paths.figures_dir / "san_francisco_city23_random_forest_medium_surface_alignment.png"
    )

    data_sources.to_csv(data_sources_path, index=False)
    final_columns.to_csv(final_columns_path, index=False)
    climate_summary.to_csv(climate_summary_path, index=False)
    benchmark_report.to_csv(benchmark_report_path, index=False)
    climate_delta_report.to_csv(climate_delta_report_path, index=False)
    fold_comparison.to_csv(fold_comparison_path, index=False)
    city_paired_summary.to_csv(city_paired_summary_path, index=False)
    city_fold_appendix.to_csv(city_fold_appendix_path, index=False)
    model_specifications.to_csv(model_specifications_path, index=False)
    retained_metadata.to_csv(retained_metadata_path, index=False)
    plot_city_row_counts(city_summary, row_counts_path)
    plot_study_city_locations(study_locations_path)
    plot_workflow_overview(workflow_overview_path)
    plot_evaluation_design(evaluation_design_path)
    plot_benchmark_metric_comparison(benchmark_report, benchmark_figure_path)
    plot_city_signal_transfer_relationship(within_transfer_comparison, city_signal_transfer_path)
    plot_city_signal_transfer_relationship_labeled(
        within_transfer_comparison,
        city_signal_transfer_labeled_path,
    )
    plot_city_metric_deltas(city_error, city_delta_figure_path)
    plot_city_rf_pr_auc(city_error, city_rf_pr_auc_figure_path)
    plot_denver_heldout_map_focus(map_points, denver_map_path)
    plot_spatial_alignment_medium_summary(spatial_alignment_metrics, spatial_alignment_summary_path)
    plot_selected_spatial_alignment_map_contrast(
        spatial_alignment_metrics,
        paths.nashville_alignment_map_source_path,
        paths.san_francisco_alignment_map_source_path,
        selected_alignment_contrast_path,
    )
    shutil.copy2(paths.within_vs_cross_gap_source_path, within_vs_cross_gap_path)
    shutil.copy2(paths.nashville_alignment_map_source_path, nashville_alignment_map_path)
    shutil.copy2(paths.san_francisco_alignment_map_source_path, san_francisco_alignment_map_path)

    return [
        data_sources_path,
        final_columns_path,
        climate_summary_path,
        benchmark_report_path,
        climate_delta_report_path,
        fold_comparison_path,
        city_paired_summary_path,
        city_fold_appendix_path,
        model_specifications_path,
        retained_metadata_path,
        row_counts_path,
        study_locations_path,
        workflow_overview_path,
        evaluation_design_path,
        benchmark_figure_path,
        city_signal_transfer_path,
        city_signal_transfer_labeled_path,
        city_delta_figure_path,
        city_rf_pr_auc_figure_path,
        denver_map_path,
        spatial_alignment_summary_path,
        within_vs_cross_gap_path,
        selected_alignment_contrast_path,
        nashville_alignment_map_path,
        san_francisco_alignment_map_path,
    ]
