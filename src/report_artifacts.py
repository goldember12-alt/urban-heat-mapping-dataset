"""Generate final-report tables and figures from project artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from src.load_cities import load_cities


CLIMATE_LABELS = {
    "hot_arid": "Hot-arid",
    "hot_humid": "Hot-humid",
    "mild_cool": "Mild-cool",
}

CLIMATE_COLORS = {
    "Hot-arid": "#c65d32",
    "Hot-humid": "#2f7f6f",
    "Mild-cool": "#4f6fb3",
}

FINAL_DATASET_COLUMNS = [
    {
        "Column": "city_id",
        "Definition": "Integer city identifier used for joins and grouped cross-validation.",
        "Role in report": "Grouping / metadata",
        "Used in headline model?": "No",
    },
    {
        "Column": "city_name",
        "Definition": "Human-readable city name.",
        "Role in report": "Metadata",
        "Used in headline model?": "No",
    },
    {
        "Column": "climate_group",
        "Definition": "Broad climate grouping label for the city.",
        "Role in report": "Predictor / stratifier",
        "Used in headline model?": "Yes",
    },
    {
        "Column": "cell_id",
        "Definition": "Cell identifier within the city grid.",
        "Role in report": "Cell metadata",
        "Used in headline model?": "No",
    },
    {
        "Column": "centroid_lon",
        "Definition": "Cell centroid longitude in WGS84.",
        "Role in report": "Mapping metadata",
        "Used in headline model?": "No",
    },
    {
        "Column": "centroid_lat",
        "Definition": "Cell centroid latitude in WGS84.",
        "Role in report": "Mapping metadata",
        "Used in headline model?": "No",
    },
    {
        "Column": "impervious_pct",
        "Definition": "NLCD impervious percentage for the cell.",
        "Role in report": "Predictor",
        "Used in headline model?": "Yes",
    },
    {
        "Column": "land_cover_class",
        "Definition": "NLCD land-cover class code for the cell.",
        "Role in report": "Predictor / water filter",
        "Used in headline model?": "Yes",
    },
    {
        "Column": "elevation_m",
        "Definition": "DEM-derived elevation in meters.",
        "Role in report": "Predictor",
        "Used in headline model?": "Yes",
    },
    {
        "Column": "dist_to_water_m",
        "Definition": "Distance from the cell to the nearest hydro feature in meters.",
        "Role in report": "Predictor",
        "Used in headline model?": "Yes",
    },
    {
        "Column": "ndvi_median_may_aug",
        "Definition": "Median May-August NDVI derived from AppEEARS MODIS/Terra MOD13A1.061 inputs.",
        "Role in report": "Predictor",
        "Used in headline model?": "Yes",
    },
    {
        "Column": "lst_median_may_aug",
        "Definition": "Median May-August 2023 daytime land surface temperature derived from ECOSTRESS/AppEEARS inputs.",
        "Role in report": "Outcome ingredient",
        "Used in headline model?": "No",
    },
    {
        "Column": "n_valid_ecostress_passes",
        "Definition": "Number of valid ECOSTRESS observations contributing to the cell-level LST summary.",
        "Role in report": "Quality filter / support field",
        "Used in headline model?": "No",
    },
    {
        "Column": "hotspot_10pct",
        "Definition": "Binary indicator for whether the cell falls in the within-city top 10% of valid LST values.",
        "Role in report": "Target",
        "Used in headline model?": "Target only",
    },
    {
        "Column": "tree_cover_proxy_pct_270m",
        "Definition": "Share of nearby 30 m cells within an approximately 270 m neighborhood in NLCD forest classes 41/42/43.",
        "Role in report": "Supplemental neighborhood-context feature",
        "Used in headline model?": "No",
    },
    {
        "Column": "vegetated_cover_proxy_pct_270m",
        "Definition": "Share of nearby 30 m cells within an approximately 270 m neighborhood in selected NLCD vegetated classes.",
        "Role in report": "Supplemental neighborhood-context feature",
        "Used in headline model?": "No",
    },
    {
        "Column": "impervious_pct_mean_270m",
        "Definition": "Neighborhood mean NLCD impervious percentage within an approximately 270 m window.",
        "Role in report": "Supplemental neighborhood-context feature",
        "Used in headline model?": "No",
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
    logistic_run_dir: Path
    rf_run_dir: Path
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
            "Raw product / layer": "2020 Census TIGERweb urban-area polygon containing each selected city center",
            "Constructed final variable(s)": "Study-area and core-city geometry; 30 m city grid",
            "Spatial role": "Defines the city footprint, 2 km buffered study area, and grid alignment target",
            "Used in headline model?": "No",
        },
        {
            "Source": "NLCD",
            "Raw product / layer": "Annual NLCD 2021 Collection 1 land-cover class raster",
            "Constructed final variable(s)": "land_cover_class",
            "Spatial role": "Categorical built and natural surface-cover predictor; open-water filter where class 11 is present",
            "Used in headline model?": "Yes",
        },
        {
            "Source": "NLCD",
            "Raw product / layer": "Annual NLCD 2021 Collection 1 impervious percentage raster",
            "Constructed final variable(s)": "impervious_pct",
            "Spatial role": "Cell-level built-intensity predictor aligned to the 30 m grid",
            "Used in headline model?": "Yes",
        },
        {
            "Source": "USGS 3DEP",
            "Raw product / layer": "3DEP 1 arc-second digital elevation model",
            "Constructed final variable(s)": "elevation_m",
            "Spatial role": "Terrain predictor aligned to the 30 m grid",
            "Used in headline model?": "Yes",
        },
        {
            "Source": "NHDPlus HR",
            "Raw product / layer": "NHDPlus High Resolution hydrography water features",
            "Constructed final variable(s)": "dist_to_water_m",
            "Spatial role": "Distance-to-nearest-water predictor derived from clipped vector water features",
            "Used in headline model?": "Yes",
        },
        {
            "Source": "MODIS/Terra via AppEEARS",
            "Raw product / layer": "MOD13A1.061 500 m 16-day NDVI observations, May 1-August 31, 2023",
            "Constructed final variable(s)": "ndvi_median_may_aug",
            "Spatial role": "Summertime vegetation predictor summarized to each grid cell",
            "Used in headline model?": "Yes",
        },
        {
            "Source": "ECOSTRESS via AppEEARS",
            "Raw product / layer": "ECO_L2T_LSTE.002 daytime land-surface-temperature observations, May 1-August 31, 2023",
            "Constructed final variable(s)": "lst_median_may_aug; n_valid_ecostress_passes; hotspot_10pct",
            "Spatial role": "Thermal outcome source, LST quality support field, and within-city top-decile target",
            "Used in headline model?": "No",
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
    return grouped


def build_benchmark_report_table(
    benchmark_table: pd.DataFrame,
    baseline_summary: pd.DataFrame,
) -> pd.DataFrame:
    """Return a compact benchmark table for the report Tables/Figures section."""

    tuned_labels = {
        "full_allfolds_s5000_sampled-full-allfolds_2026-04-07_235825": "Logistic SAGA 5k",
        "full_allfolds_s20000_samplecurve-20k_2026-04-08_021152": "Logistic SAGA 20k context",
        "frontier_allfolds_s5000_frontier-check_2026-04-11_173430": "Random forest 5k",
    }
    tuned_notes = {
        "full_allfolds_s5000_sampled-full-allfolds_2026-04-07_235825": "Matched 5k linear comparison for random forest.",
        "full_allfolds_s20000_samplecurve-20k_2026-04-08_021152": "Higher-sample logistic context, not the matched RF comparison.",
        "frontier_allfolds_s5000_frontier-check_2026-04-11_173430": "Best current 5k random-forest specification.",
    }
    baseline_labels = {
        "global_mean_baseline": "Global-mean baseline",
        "climate_only_baseline": "Climate-only baseline",
        "impervious_only_baseline": "Impervious-only baseline",
        "land_cover_only_baseline": "Land-cover-only baseline",
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
            "Rows per city": "5,000 sampled",
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
                "Rows per city": "5,000 sampled",
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
                "Rows per city": f"{int(tuned_row['rows_per_city']):,} sampled",
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
    table["Mean recall-at-top-10% delta"] = table["mean_recall_delta"].round(4)
    table["Median PR AUC delta"] = table["median_pr_auc_delta"].round(4)
    table["Median recall-at-top-10% delta"] = table["median_recall_delta"].round(4)
    return table[
        [
            "Climate group",
            "city_count",
            "rf_pr_auc_wins",
            "logistic_pr_auc_wins",
            "Mean PR AUC delta",
            "rf_recall_wins",
            "logistic_recall_wins",
            "Mean recall-at-top-10% delta",
        ]
    ].rename(
        columns={
            "city_count": "City count",
            "rf_pr_auc_wins": "RF PR AUC wins",
            "logistic_pr_auc_wins": "Logistic PR AUC wins",
            "rf_recall_wins": "RF recall wins",
            "logistic_recall_wins": "Logistic recall wins",
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
    merged["RF minus logistic PR AUC"] = merged["pr_auc_rf"] - merged["pr_auc_logistic"]
    merged["RF minus logistic recall@top10"] = (
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
            "RF minus logistic PR AUC",
            "recall_at_top_10pct_logistic",
            "recall_at_top_10pct_rf",
            "RF minus logistic recall@top10",
        ]
    ].rename(
        columns={
            "outer_fold": "Outer fold",
            "train_row_count": "Train rows",
            "test_row_count": "Test rows",
            "test_positive_count": "Test positives",
            "test_prevalence": "Test prevalence",
            "pr_auc_logistic": "Logistic PR AUC",
            "pr_auc_rf": "RF PR AUC",
            "recall_at_top_10pct_logistic": "Logistic recall@top10",
            "recall_at_top_10pct_rf": "RF recall@top10",
        }
    )
    numeric_columns = [
        "Test prevalence",
        "Logistic PR AUC",
        "RF PR AUC",
        "RF minus logistic PR AUC",
        "Logistic recall@top10",
        "RF recall@top10",
        "RF minus logistic recall@top10",
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
        ("City recall@top10", "recall_delta_rf_minus_logistic"),
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
    table["Hotspot prevalence"] = table["hotspot_prevalence"].round(4)
    return table[
        [
            "city_id",
            "city_name",
            "Climate group",
            "row_count",
            "hotspot_positive_count",
            "Hotspot prevalence",
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
            "Scoring": "PR AUC and recall@top10",
            "Grouped CV?": "Reference only",
        },
        {
            "Model / baseline": "Global-mean baseline",
            "Predictors": "None",
            "Preprocessing": "Training-city target mean",
            "Tuning grid or rule": "Predict the training-city hotspot prevalence for all held-out rows.",
            "Scoring": "PR AUC and recall@top10",
            "Grouped CV?": "Outer city folds only",
        },
        {
            "Model / baseline": "Climate-only baseline",
            "Predictors": "climate_group",
            "Preprocessing": "Training-city category means",
            "Tuning grid or rule": "Predict training-city hotspot prevalence by climate group.",
            "Scoring": "PR AUC and recall@top10",
            "Grouped CV?": "Outer city folds only",
        },
        {
            "Model / baseline": "Land-cover-only baseline",
            "Predictors": "land_cover_class",
            "Preprocessing": "Training-city category means",
            "Tuning grid or rule": "Predict training-city hotspot prevalence by land-cover class.",
            "Scoring": "PR AUC and recall@top10",
            "Grouped CV?": "Outer city folds only",
        },
        {
            "Model / baseline": "Impervious-only baseline",
            "Predictors": "impervious_pct",
            "Preprocessing": "Training-city decile bins",
            "Tuning grid or rule": "Predict training-city hotspot prevalence by imperviousness bin.",
            "Scoring": "PR AUC and recall@top10",
            "Grouped CV?": "Outer city folds only",
        },
        {
            "Model / baseline": "Logistic SAGA 5k",
            "Predictors": "impervious_pct, land_cover_class, elevation_m, dist_to_water_m, ndvi_median_may_aug, climate_group",
            "Preprocessing": "Training-only imputation, numeric scaling, and categorical one-hot encoding inside sklearn Pipeline",
            "Tuning grid or rule": "C = 0.01, 0.1, 1.0, 10.0; l1_ratio = 0.0, 0.2, 0.5, 0.8, 1.0",
            "Scoring": "Inner-CV average precision; held-out PR AUC and recall@top10",
            "Grouped CV?": "Yes, grouped outer folds and grouped inner CV",
        },
        {
            "Model / baseline": "Random forest 5k",
            "Predictors": "Same six non-thermal predictors as logistic SAGA",
            "Preprocessing": "Training-only imputation and categorical one-hot encoding inside sklearn Pipeline",
            "Tuning grid or rule": "n_estimators = 200, 300; max_depth = 10, 20; max_features = sqrt; min_samples_leaf = 1, 5",
            "Scoring": "Inner-CV average precision; held-out PR AUC and recall@top10",
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
                "Model checkpoint": label,
                "Model family": metadata["model_name"],
                "Tuning preset": metadata["tuning_preset"],
                "Rows per city": metadata["sample_rows_per_city"],
                "Outer folds": ", ".join(str(fold) for fold in metadata["selected_outer_folds"]),
                "Inner CV splits": metadata["inner_cv_splits_requested"],
                "Scoring": metadata["scoring"],
                "Parameter candidates": metadata["search_space"]["param_candidate_count"],
                "Estimated inner fits": metadata["search_space"][
                    "estimated_total_inner_fits"
                ],
                "Pooled PR AUC": round(metrics_row["pooled_pr_auc"], 4),
                "Mean city PR AUC": round(metrics_row["mean_city_pr_auc"], 4),
                "Recall at top 10%": round(
                    metrics_row["pooled_recall_at_top_10pct"], 4
                ),
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
                "Impervious-only baseline",
                "Land-cover-only baseline",
                "Logistic SAGA 5k",
                "Logistic SAGA 20k context",
                "Random forest 5k",
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
        "Impervious-only baseline": "#8f6f4f",
        "Land-cover-only baseline": "#8f6f4f",
        "Logistic SAGA 5k": "#2f6c8f",
        "Logistic SAGA 20k context": "#9fb8c8",
        "Random forest 5k": "#9b3d2f",
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

    fig, ax = plt.subplots(figsize=(12, 4.8))
    ax.set_xlim(0, 1200)
    ax.set_ylim(0, 480)
    ax.axis("off")
    ax.set_facecolor("#fbf8f2")
    fig.patch.set_facecolor("#fbf8f2")

    _diagram_box(ax, 40, 255, 290, 165, "Benchmark\nPopulation", ["30 cities total", "10 hot-arid", "10 hot-humid", "10 mild-cool"], fill="#eef4f7")
    _diagram_box(ax, 380, 240, 360, 190, "Outer Folds", ["5 deterministic folds", "6 held-out cities per fold", "24 training cities per fold"])
    _diagram_box(ax, 790, 255, 360, 165, "Leakage Guardrail", ["Imputation, scaling, encoding,", "feature processing, and tuning", "fit on training-city rows only"], fill="#eef4f7")
    _diagram_box(ax, 190, 75, 820, 150, "Fold k", ["Train on cities in C \\ F_k, tune inside training cities,", "then evaluate on held-out cities in F_k.", "No city appears in both training and testing."])

    for i in range(6):
        ax.add_patch(FancyBboxPatch((422 + i * 45, 272), 36, 18, boxstyle="round,pad=0,rounding_size=4", facecolor="#b34a33", edgecolor="none", alpha=0.95))
    for row in range(2):
        for i in range(7):
            ax.add_patch(FancyBboxPatch((422 + i * 45, 240 - row * 30), 36, 18, boxstyle="round,pad=0,rounding_size=4", facecolor="#7aa0b8", edgecolor="none", alpha=0.85))

    _diagram_arrow(ax, (330, 337), (380, 337))
    _diagram_arrow(ax, (740, 337), (790, 337))
    _diagram_arrow(ax, (600, 240), (600, 200))
    ax.text(
        600,
        30,
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
    city_delta_figure_path = paths.figures_dir / "city_metric_deltas.png"
    city_rf_pr_auc_figure_path = paths.figures_dir / "city_rf_pr_auc.png"

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
    plot_city_metric_deltas(city_error, city_delta_figure_path)
    plot_city_rf_pr_auc(city_error, city_rf_pr_auc_figure_path)

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
        city_delta_figure_path,
        city_rf_pr_auc_figure_path,
    ]
