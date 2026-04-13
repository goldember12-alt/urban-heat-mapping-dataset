from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config import MODELING_REPORTING_FIGURES, MODELING_REPORTING_OUTPUTS, PROJECT_ROOT

logger = logging.getLogger(__name__)

DEFAULT_BASELINE_SUMMARY_PATH = PROJECT_ROOT / "outputs" / "modeling" / "baselines" / "metrics_summary.csv"
DEFAULT_LOGISTIC_5K_RUN_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "modeling"
    / "logistic_saga"
    / "full_allfolds_s5000_sampled-full-allfolds_2026-04-07_235825"
)
DEFAULT_LOGISTIC_10K_RUN_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "modeling"
    / "logistic_saga"
    / "full_allfolds_s10000_samplecurve-10k_2026-04-08_004723"
)
DEFAULT_LOGISTIC_20K_RUN_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "modeling"
    / "logistic_saga"
    / "full_allfolds_s20000_samplecurve-20k_2026-04-08_021152"
)
DEFAULT_RF_SMOKE_RUN_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "modeling"
    / "random_forest"
    / "smoke_allfolds_s5000_nonlinear-check_2026-04-11_163814"
)
DEFAULT_RF_FRONTIER_RUN_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "modeling"
    / "random_forest"
    / "frontier_allfolds_s5000_frontier-check_2026-04-11_173430"
)


@dataclass(frozen=True)
class ReportingPaths:
    markdown_path: Path
    output_dir: Path
    tables_dir: Path
    figures_dir: Path


@dataclass(frozen=True)
class BenchmarkRunSpec:
    label: str
    run_dir: Path
    notes: str


@dataclass(frozen=True)
class ModelingReportingResult:
    markdown_path: Path
    benchmark_table_path: Path
    city_error_table_path: Path
    climate_summary_path: Path
    benchmark_metrics_figure_path: Path
    runtime_figure_path: Path
    city_delta_figure_path: Path
    phase1_candidate_table_path: Path | None = None
    phase1_candidate_climate_summary_path: Path | None = None
    phase2_candidate_table_path: Path | None = None
    phase2_candidate_climate_summary_path: Path | None = None
    phase2_candidate_disparity_summary_path: Path | None = None
    phase3_candidate_table_path: Path | None = None
    phase3_candidate_climate_summary_path: Path | None = None


def resolve_modeling_report_paths(
    report_slug: str,
    outputs_root: Path = MODELING_REPORTING_OUTPUTS,
    figures_root: Path = MODELING_REPORTING_FIGURES,
) -> ReportingPaths:
    """Return canonical markdown, table, and figure paths for a modeling report."""
    resolved_output_dir = outputs_root.resolve()
    resolved_figures_dir = figures_root.resolve()
    markdown_path = resolved_output_dir / f"{report_slug}.md"
    tables_dir = resolved_output_dir / "tables"
    return ReportingPaths(
        markdown_path=markdown_path,
        output_dir=resolved_output_dir,
        tables_dir=tables_dir,
        figures_dir=resolved_figures_dir,
    )


def _require_file(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return path


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(_require_file(path).read_text(encoding="utf-8"))


def _default_benchmark_run_specs() -> list[BenchmarkRunSpec]:
    return [
        BenchmarkRunSpec(
            label="logistic_full_5k",
            run_dir=DEFAULT_LOGISTIC_5K_RUN_DIR,
            notes="Retained 5k linear baseline rung",
        ),
        BenchmarkRunSpec(
            label="logistic_full_10k",
            run_dir=DEFAULT_LOGISTIC_10K_RUN_DIR,
            notes="Retained 10k linear baseline rung",
        ),
        BenchmarkRunSpec(
            label="logistic_full_20k",
            run_dir=DEFAULT_LOGISTIC_20K_RUN_DIR,
            notes="Highest-capacity retained linear rung on this workstation",
        ),
        BenchmarkRunSpec(
            label="random_forest_smoke_5k",
            run_dir=DEFAULT_RF_SMOKE_RUN_DIR,
            notes="Cheap nonlinear comparison checkpoint",
        ),
        BenchmarkRunSpec(
            label="random_forest_frontier_5k",
            run_dir=DEFAULT_RF_FRONTIER_RUN_DIR,
            notes="Targeted follow-up search around the smoke-winning RF region",
        ),
    ]


def _load_baseline_benchmark_rows(baseline_summary_path: Path) -> pd.DataFrame:
    baseline_df = pd.read_csv(_require_file(baseline_summary_path))
    keep_rows = baseline_df["model_name"].isin(["impervious_only_baseline", "land_cover_only_baseline"])
    filtered = baseline_df.loc[keep_rows].copy().reset_index(drop=True)
    filtered["run_label"] = filtered["model_name"]
    filtered["model_family"] = "baseline"
    filtered["preset"] = "n/a"
    filtered["rows_per_city"] = "all available"
    filtered["param_candidate_count"] = np.nan
    filtered["estimated_total_inner_fits"] = np.nan
    filtered["runtime_minutes"] = np.nan
    filtered["notes"] = filtered["model_name"].map(
        {
            "impervious_only_baseline": "Strongest simple baseline on recall",
            "land_cover_only_baseline": "Strongest simple baseline on pooled PR AUC",
        }
    )
    filtered["source_path"] = str(baseline_summary_path)
    return filtered[
        [
            "run_label",
            "model_family",
            "preset",
            "rows_per_city",
            "param_candidate_count",
            "estimated_total_inner_fits",
            "pooled_pr_auc",
            "mean_city_pr_auc",
            "pooled_recall_at_top_10pct",
            "runtime_minutes",
            "notes",
            "source_path",
        ]
    ]


def _load_tuned_benchmark_row(spec: BenchmarkRunSpec) -> dict[str, object]:
    metrics_summary_path = _require_file(spec.run_dir / "metrics_summary.csv")
    metadata_path = _require_file(spec.run_dir / "run_metadata.json")
    summary_row = pd.read_csv(metrics_summary_path).iloc[0].to_dict()
    metadata = _load_json(metadata_path)
    search_space = dict(metadata.get("search_space", {}))
    timing = dict(metadata.get("timing_seconds", {}))
    return {
        "run_label": spec.run_dir.name,
        "model_family": str(summary_row["model_name"]),
        "preset": str(metadata.get("tuning_preset", "")),
        "rows_per_city": metadata.get("sample_rows_per_city"),
        "param_candidate_count": search_space.get("param_candidate_count"),
        "estimated_total_inner_fits": search_space.get("estimated_total_inner_fits"),
        "pooled_pr_auc": float(summary_row["pooled_pr_auc"]),
        "mean_city_pr_auc": float(summary_row["mean_city_pr_auc"]),
        "pooled_recall_at_top_10pct": float(summary_row["pooled_recall_at_top_10pct"]),
        "runtime_minutes": float(timing.get("total_wall_clock", 0.0)) / 60.0,
        "notes": spec.notes,
        "source_path": str(spec.run_dir),
    }


def build_benchmark_comparison_table(
    baseline_summary_path: Path = DEFAULT_BASELINE_SUMMARY_PATH,
    run_specs: list[BenchmarkRunSpec] | None = None,
) -> pd.DataFrame:
    """Build the retained benchmark comparison table for reporting."""
    tuned_specs = _default_benchmark_run_specs() if run_specs is None else list(run_specs)
    baseline_rows = _load_baseline_benchmark_rows(baseline_summary_path=baseline_summary_path)
    tuned_rows = pd.DataFrame([_load_tuned_benchmark_row(spec) for spec in tuned_specs])
    combined = pd.concat([baseline_rows, tuned_rows], ignore_index=True)
    return combined


def _build_pairwise_city_metric_comparison(
    *,
    left_run_dir: Path,
    right_run_dir: Path,
    left_model_label: str,
    right_model_label: str,
    left_short_label: str,
    right_short_label: str,
) -> pd.DataFrame:
    left_city_path = _require_file(left_run_dir / "metrics_by_city.csv")
    right_city_path = _require_file(right_run_dir / "metrics_by_city.csv")
    left_df = pd.read_csv(left_city_path).rename(
        columns={
            "model_name": f"model_name_{left_short_label}",
            "row_count": f"row_count_{left_short_label}",
            "positive_count": f"positive_count_{left_short_label}",
            "prevalence": f"prevalence_{left_short_label}",
            "pr_auc": f"pr_auc_{left_short_label}",
            "recall_at_top_10pct": f"recall_at_top_10pct_{left_short_label}",
        }
    )
    right_df = pd.read_csv(right_city_path).rename(
        columns={
            "model_name": f"model_name_{right_short_label}",
            "row_count": f"row_count_{right_short_label}",
            "positive_count": f"positive_count_{right_short_label}",
            "prevalence": f"prevalence_{right_short_label}",
            "pr_auc": f"pr_auc_{right_short_label}",
            "recall_at_top_10pct": f"recall_at_top_10pct_{right_short_label}",
        }
    )
    merged = left_df.merge(
        right_df,
        on=["outer_fold", "city_id", "city_name", "climate_group"],
        how="inner",
        validate="one_to_one",
    )
    merged[f"pr_auc_delta_{right_short_label}_minus_{left_short_label}"] = (
        merged[f"pr_auc_{right_short_label}"] - merged[f"pr_auc_{left_short_label}"]
    )
    merged[f"recall_delta_{right_short_label}_minus_{left_short_label}"] = (
        merged[f"recall_at_top_10pct_{right_short_label}"] - merged[f"recall_at_top_10pct_{left_short_label}"]
    )
    merged["pr_auc_winner"] = np.where(
        merged[f"pr_auc_delta_{right_short_label}_minus_{left_short_label}"] > 0,
        right_model_label,
        np.where(
            merged[f"pr_auc_delta_{right_short_label}_minus_{left_short_label}"] < 0,
            left_model_label,
            "tie",
        ),
    )
    merged["recall_winner"] = np.where(
        merged[f"recall_delta_{right_short_label}_minus_{left_short_label}"] > 0,
        right_model_label,
        np.where(
            merged[f"recall_delta_{right_short_label}_minus_{left_short_label}"] < 0,
            left_model_label,
            "tie",
        ),
    )
    merged["row_count"] = merged[f"row_count_{left_short_label}"]
    merged["positive_count"] = merged[f"positive_count_{left_short_label}"]
    merged["prevalence"] = merged[f"prevalence_{left_short_label}"]
    return merged


def build_city_error_comparison(
    logistic_run_dir: Path = DEFAULT_LOGISTIC_5K_RUN_DIR,
    random_forest_run_dir: Path = DEFAULT_RF_FRONTIER_RUN_DIR,
) -> pd.DataFrame:
    """Compare city-level metrics between the matched logistic and RF reporting slices."""
    merged = _build_pairwise_city_metric_comparison(
        left_run_dir=logistic_run_dir,
        right_run_dir=random_forest_run_dir,
        left_model_label="logistic_saga",
        right_model_label="random_forest",
        left_short_label="logistic",
        right_short_label="rf",
    )
    columns = [
        "outer_fold",
        "city_id",
        "city_name",
        "climate_group",
        "row_count",
        "positive_count",
        "prevalence",
        "pr_auc_logistic",
        "pr_auc_rf",
        "pr_auc_delta_rf_minus_logistic",
        "pr_auc_winner",
        "recall_at_top_10pct_logistic",
        "recall_at_top_10pct_rf",
        "recall_delta_rf_minus_logistic",
        "recall_winner",
    ]
    return merged[columns].sort_values("pr_auc_delta_rf_minus_logistic", ascending=False).reset_index(drop=True)


def build_phase1_candidate_comparison(
    *,
    hist_gradient_boosting_run_dir: Path,
    random_forest_run_dir: Path = DEFAULT_RF_FRONTIER_RUN_DIR,
) -> pd.DataFrame:
    """Compare the bounded Phase 1 HGB checkpoint against the retained RF frontier run."""
    merged = _build_pairwise_city_metric_comparison(
        left_run_dir=random_forest_run_dir,
        right_run_dir=hist_gradient_boosting_run_dir,
        left_model_label="random_forest",
        right_model_label="hist_gradient_boosting",
        left_short_label="rf",
        right_short_label="hgb",
    )
    columns = [
        "outer_fold",
        "city_id",
        "city_name",
        "climate_group",
        "row_count",
        "positive_count",
        "prevalence",
        "pr_auc_rf",
        "pr_auc_hgb",
        "pr_auc_delta_hgb_minus_rf",
        "pr_auc_winner",
        "recall_at_top_10pct_rf",
        "recall_at_top_10pct_hgb",
        "recall_delta_hgb_minus_rf",
        "recall_winner",
    ]
    return merged[columns].sort_values("pr_auc_delta_hgb_minus_rf", ascending=False).reset_index(drop=True)


def build_phase2_candidate_comparison(
    *,
    logistic_run_dir: Path = DEFAULT_LOGISTIC_5K_RUN_DIR,
    logistic_climate_interactions_run_dir: Path,
) -> pd.DataFrame:
    """Compare the Phase 2 climate-conditioned logistic run against the retained logistic benchmark slice."""
    merged = _build_pairwise_city_metric_comparison(
        left_run_dir=logistic_run_dir,
        right_run_dir=logistic_climate_interactions_run_dir,
        left_model_label="logistic_saga",
        right_model_label="logistic_saga_climate_interactions",
        left_short_label="logistic",
        right_short_label="logistic_climate_interactions",
    )
    columns = [
        "outer_fold",
        "city_id",
        "city_name",
        "climate_group",
        "row_count",
        "positive_count",
        "prevalence",
        "pr_auc_logistic",
        "pr_auc_logistic_climate_interactions",
        "pr_auc_delta_logistic_climate_interactions_minus_logistic",
        "pr_auc_winner",
        "recall_at_top_10pct_logistic",
        "recall_at_top_10pct_logistic_climate_interactions",
        "recall_delta_logistic_climate_interactions_minus_logistic",
        "recall_winner",
    ]
    return merged[columns].sort_values(
        "pr_auc_delta_logistic_climate_interactions_minus_logistic",
        ascending=False,
    ).reset_index(drop=True)


def build_phase3_candidate_comparison(
    *,
    logistic_run_dir: Path = DEFAULT_LOGISTIC_5K_RUN_DIR,
    richer_predictor_run_dir: Path,
) -> pd.DataFrame:
    """Compare the bounded Phase 3 richer-predictor logistic run against the retained logistic benchmark slice."""
    merged = _build_pairwise_city_metric_comparison(
        left_run_dir=logistic_run_dir,
        right_run_dir=richer_predictor_run_dir,
        left_model_label="logistic_saga",
        right_model_label="logistic_saga_phase3a",
        left_short_label="logistic",
        right_short_label="phase3a",
    )
    columns = [
        "outer_fold",
        "city_id",
        "city_name",
        "climate_group",
        "row_count",
        "positive_count",
        "prevalence",
        "pr_auc_logistic",
        "pr_auc_phase3a",
        "pr_auc_delta_phase3a_minus_logistic",
        "pr_auc_winner",
        "recall_at_top_10pct_logistic",
        "recall_at_top_10pct_phase3a",
        "recall_delta_phase3a_minus_logistic",
        "recall_winner",
    ]
    return merged[columns].sort_values(
        "pr_auc_delta_phase3a_minus_logistic",
        ascending=False,
    ).reset_index(drop=True)


def summarize_city_error_by_climate(city_error_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize RF-vs-logistic city-level error deltas by climate group."""
    summary = (
        city_error_df.groupby("climate_group", dropna=False)
        .agg(
            city_count=("city_id", "count"),
            rf_pr_auc_wins=("pr_auc_winner", lambda values: int((pd.Series(values) == "random_forest").sum())),
            logistic_pr_auc_wins=("pr_auc_winner", lambda values: int((pd.Series(values) == "logistic_saga").sum())),
            rf_recall_wins=("recall_winner", lambda values: int((pd.Series(values) == "random_forest").sum())),
            logistic_recall_wins=("recall_winner", lambda values: int((pd.Series(values) == "logistic_saga").sum())),
            mean_pr_auc_delta=("pr_auc_delta_rf_minus_logistic", "mean"),
            median_pr_auc_delta=("pr_auc_delta_rf_minus_logistic", "median"),
            mean_recall_delta=("recall_delta_rf_minus_logistic", "mean"),
            median_recall_delta=("recall_delta_rf_minus_logistic", "median"),
        )
        .reset_index()
        .sort_values("climate_group")
        .reset_index(drop=True)
    )
    return summary


def summarize_phase1_candidate_by_climate(candidate_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize HGB-vs-RF city-level deltas by climate group for the optional Phase 1 checkpoint."""
    summary = (
        candidate_df.groupby("climate_group", dropna=False)
        .agg(
            city_count=("city_id", "count"),
            hgb_pr_auc_wins=("pr_auc_winner", lambda values: int((pd.Series(values) == "hist_gradient_boosting").sum())),
            rf_pr_auc_wins=("pr_auc_winner", lambda values: int((pd.Series(values) == "random_forest").sum())),
            hgb_recall_wins=("recall_winner", lambda values: int((pd.Series(values) == "hist_gradient_boosting").sum())),
            rf_recall_wins=("recall_winner", lambda values: int((pd.Series(values) == "random_forest").sum())),
            mean_pr_auc_delta=("pr_auc_delta_hgb_minus_rf", "mean"),
            median_pr_auc_delta=("pr_auc_delta_hgb_minus_rf", "median"),
            mean_recall_delta=("recall_delta_hgb_minus_rf", "mean"),
            median_recall_delta=("recall_delta_hgb_minus_rf", "median"),
        )
        .reset_index()
        .sort_values("climate_group")
        .reset_index(drop=True)
    )
    return summary


def summarize_phase2_candidate_by_climate(candidate_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize climate-conditioned logistic deltas by climate group."""
    summary = (
        candidate_df.groupby("climate_group", dropna=False)
        .agg(
            city_count=("city_id", "count"),
            mean_pr_auc_logistic=("pr_auc_logistic", "mean"),
            mean_pr_auc_logistic_climate_interactions=("pr_auc_logistic_climate_interactions", "mean"),
            interaction_pr_auc_wins=(
                "pr_auc_winner",
                lambda values: int((pd.Series(values) == "logistic_saga_climate_interactions").sum()),
            ),
            logistic_pr_auc_wins=("pr_auc_winner", lambda values: int((pd.Series(values) == "logistic_saga").sum())),
            mean_pr_auc_delta=("pr_auc_delta_logistic_climate_interactions_minus_logistic", "mean"),
            median_pr_auc_delta=("pr_auc_delta_logistic_climate_interactions_minus_logistic", "median"),
            mean_recall_at_top_10pct_logistic=("recall_at_top_10pct_logistic", "mean"),
            mean_recall_at_top_10pct_logistic_climate_interactions=(
                "recall_at_top_10pct_logistic_climate_interactions",
                "mean",
            ),
            interaction_recall_wins=(
                "recall_winner",
                lambda values: int((pd.Series(values) == "logistic_saga_climate_interactions").sum()),
            ),
            logistic_recall_wins=(
                "recall_winner",
                lambda values: int((pd.Series(values) == "logistic_saga").sum()),
            ),
            mean_recall_delta=("recall_delta_logistic_climate_interactions_minus_logistic", "mean"),
            median_recall_delta=("recall_delta_logistic_climate_interactions_minus_logistic", "median"),
        )
        .reset_index()
        .sort_values("climate_group")
        .reset_index(drop=True)
    )
    return summary


def summarize_phase2_climate_disparity(candidate_climate_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize whether the Phase 2 variant narrows mean climate-group performance spread."""
    if candidate_climate_df.empty:
        return pd.DataFrame(
            columns=[
                "metric",
                "baseline_climate_group_range",
                "interaction_climate_group_range",
                "range_delta_interaction_minus_baseline",
            ]
        )

    disparity_df = pd.DataFrame(
        [
            {
                "metric": "pr_auc",
                "baseline_climate_group_range": (
                    candidate_climate_df["mean_pr_auc_logistic"].max()
                    - candidate_climate_df["mean_pr_auc_logistic"].min()
                ),
                "interaction_climate_group_range": (
                    candidate_climate_df["mean_pr_auc_logistic_climate_interactions"].max()
                    - candidate_climate_df["mean_pr_auc_logistic_climate_interactions"].min()
                ),
            },
            {
                "metric": "recall_at_top_10pct",
                "baseline_climate_group_range": (
                    candidate_climate_df["mean_recall_at_top_10pct_logistic"].max()
                    - candidate_climate_df["mean_recall_at_top_10pct_logistic"].min()
                ),
                "interaction_climate_group_range": (
                    candidate_climate_df["mean_recall_at_top_10pct_logistic_climate_interactions"].max()
                    - candidate_climate_df["mean_recall_at_top_10pct_logistic_climate_interactions"].min()
                ),
            },
        ]
    )
    disparity_df["range_delta_interaction_minus_baseline"] = (
        disparity_df["interaction_climate_group_range"] - disparity_df["baseline_climate_group_range"]
    )
    return disparity_df


def summarize_phase3_candidate_by_climate(candidate_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize the richer-predictor Phase 3 checkpoint by climate group."""
    summary = (
        candidate_df.groupby("climate_group", dropna=False)
        .agg(
            city_count=("city_id", "count"),
            mean_pr_auc_logistic=("pr_auc_logistic", "mean"),
            mean_pr_auc_phase3a=("pr_auc_phase3a", "mean"),
            phase3a_pr_auc_wins=("pr_auc_winner", lambda values: int((pd.Series(values) == "logistic_saga_phase3a").sum())),
            logistic_pr_auc_wins=("pr_auc_winner", lambda values: int((pd.Series(values) == "logistic_saga").sum())),
            mean_pr_auc_delta=("pr_auc_delta_phase3a_minus_logistic", "mean"),
            median_pr_auc_delta=("pr_auc_delta_phase3a_minus_logistic", "median"),
            mean_recall_at_top_10pct_logistic=("recall_at_top_10pct_logistic", "mean"),
            mean_recall_at_top_10pct_phase3a=("recall_at_top_10pct_phase3a", "mean"),
            phase3a_recall_wins=(
                "recall_winner",
                lambda values: int((pd.Series(values) == "logistic_saga_phase3a").sum()),
            ),
            logistic_recall_wins=("recall_winner", lambda values: int((pd.Series(values) == "logistic_saga").sum())),
            mean_recall_delta=("recall_delta_phase3a_minus_logistic", "mean"),
            median_recall_delta=("recall_delta_phase3a_minus_logistic", "median"),
        )
        .reset_index()
        .sort_values("climate_group")
        .reset_index(drop=True)
    )
    return summary


def _benchmark_display_label(row: pd.Series) -> str:
    run_label = str(row["run_label"])
    model_family = str(row["model_family"])
    preset = str(row["preset"])
    rows_per_city = row["rows_per_city"]

    if run_label == "impervious_only_baseline":
        return "Imp.\nbase"
    if run_label == "land_cover_only_baseline":
        return "LC\nbase"
    if model_family == "logistic_saga":
        return f"Log\n{int(rows_per_city) // 1000}k" if pd.notna(rows_per_city) else "Log"
    if model_family == "logistic_saga_climate_interactions":
        return f"Log+CI\n{int(rows_per_city) // 1000}k" if pd.notna(rows_per_city) else "Log+CI"
    if model_family == "random_forest":
        if preset == "smoke":
            return "RF\nsmoke"
        if preset == "frontier":
            return "RF\nfrontier"
        if preset == "full":
            return "RF\nfull"
    if model_family == "hist_gradient_boosting":
        return "HGB\nsmoke" if preset == "smoke" else "HGB"
    return run_label


def _format_scalar(value: object, decimals: int = 4) -> str:
    if pd.isna(value):
        return "n/a"
    if isinstance(value, str):
        return value
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return f"{float(value):.{decimals}f}"


def _dataframe_to_markdown(df: pd.DataFrame, decimal_columns: set[str] | None = None) -> str:
    decimal_columns = decimal_columns or set()
    integer_like_columns = {
        "param_candidate_count",
        "estimated_total_inner_fits",
        "city_count",
        "rf_pr_auc_wins",
        "logistic_pr_auc_wins",
        "rf_recall_wins",
        "logistic_recall_wins",
        "hgb_pr_auc_wins",
        "hgb_recall_wins",
        "interaction_pr_auc_wins",
        "interaction_recall_wins",
    }
    header = "| " + " | ".join(df.columns.astype(str)) + " |"
    separator = "| " + " | ".join(["---"] * len(df.columns)) + " |"
    rows: list[str] = [header, separator]
    for _, row in df.iterrows():
        formatted = []
        for column_name in df.columns:
            value = row[column_name]
            formatted.append(
                _format_scalar(
                    value,
                    decimals=(
                        4
                        if column_name in decimal_columns
                        else 1
                        if column_name == "runtime_minutes"
                        else 0
                        if column_name in integer_like_columns
                        else 4
                    ),
                )
            )
        rows.append("| " + " | ".join(formatted) + " |")
    return "\n".join(rows)


def plot_benchmark_metric_comparison(benchmark_df: pd.DataFrame, output_path: Path) -> Path:
    """Write a benchmark comparison figure across retained runs."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    display_labels = [_benchmark_display_label(row) for _, row in benchmark_df.iterrows()]
    metric_specs = [
        ("pooled_pr_auc", "Pooled PR AUC"),
        ("mean_city_pr_auc", "Mean City PR AUC"),
        ("pooled_recall_at_top_10pct", "Recall At Top 10%"),
    ]
    colors = {
        "baseline": "#8f6f4f",
        "logistic_saga": "#2f6c8f",
        "logistic_saga_climate_interactions": "#4f8d5d",
        "random_forest": "#9b3d2f",
        "hist_gradient_boosting": "#3f7d3a",
    }
    fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(13, 4.5), constrained_layout=True)
    x = np.arange(len(benchmark_df))
    for axis, (metric_column, title) in zip(axes, metric_specs):
        axis.bar(
            x,
            benchmark_df[metric_column].to_numpy(dtype="float64"),
            color=[colors.get(model_family, "#666666") for model_family in benchmark_df["model_family"]],
        )
        axis.set_title(title)
        axis.set_xticks(x)
        axis.set_xticklabels(display_labels, fontsize=9)
        axis.set_ylim(0.0, max(0.22, benchmark_df[metric_column].max() * 1.15))
        axis.grid(axis="y", alpha=0.25)
    fig.suptitle("Cross-City Benchmark Metrics", fontsize=13)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_runtime_vs_performance(benchmark_df: pd.DataFrame, output_path: Path) -> Path:
    """Write a runtime-versus-performance scatter plot for tuned runs."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tuned_df = benchmark_df.loc[benchmark_df["runtime_minutes"].notna()].copy().reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(7, 5))
    color_map = {
        "logistic_saga": "#2f6c8f",
        "logistic_saga_climate_interactions": "#4f8d5d",
        "random_forest": "#9b3d2f",
        "hist_gradient_boosting": "#3f7d3a",
    }
    for _, row in tuned_df.iterrows():
        ax.scatter(
            float(row["runtime_minutes"]),
            float(row["pooled_pr_auc"]),
            s=75,
            color=color_map.get(str(row["model_family"]), "#666666"),
        )
        ax.annotate(
            _benchmark_display_label(row),
            (float(row["runtime_minutes"]), float(row["pooled_pr_auc"])),
            textcoords="offset points",
            xytext=(5, 4),
            fontsize=8,
        )
    ax.set_title("Runtime vs Pooled PR AUC")
    ax.set_xlabel("Runtime (minutes)")
    ax.set_ylabel("Pooled PR AUC")
    ax.grid(alpha=0.25)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_city_metric_deltas(city_error_df: pd.DataFrame, output_path: Path) -> Path:
    """Write a city-level RF-minus-logistic delta figure."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ordered = city_error_df.sort_values("pr_auc_delta_rf_minus_logistic").reset_index(drop=True)
    y_positions = np.arange(len(ordered))
    colors = ["#2f6c8f" if delta < 0 else "#9b3d2f" for delta in ordered["pr_auc_delta_rf_minus_logistic"]]
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(14, 9), constrained_layout=True)

    axes[0].barh(y_positions, ordered["pr_auc_delta_rf_minus_logistic"], color=colors)
    axes[0].axvline(0.0, color="black", linewidth=1)
    axes[0].set_yticks(y_positions)
    axes[0].set_yticklabels(ordered["city_name"], fontsize=8)
    axes[0].set_title("RF Frontier - Logistic 5k PR AUC by City")
    axes[0].set_xlabel("Delta in PR AUC")
    axes[0].grid(axis="x", alpha=0.25)

    recall_colors = ["#2f6c8f" if delta < 0 else "#9b3d2f" for delta in ordered["recall_delta_rf_minus_logistic"]]
    axes[1].barh(y_positions, ordered["recall_delta_rf_minus_logistic"], color=recall_colors)
    axes[1].axvline(0.0, color="black", linewidth=1)
    axes[1].set_yticks(y_positions)
    axes[1].set_yticklabels([])
    axes[1].set_title("RF Frontier - Logistic 5k Recall@10% by City")
    axes[1].set_xlabel("Delta in Recall At Top 10%")
    axes[1].grid(axis="x", alpha=0.25)

    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def _top_city_delta_table(city_error_df: pd.DataFrame, metric_column: str, top_n: int, ascending: bool) -> pd.DataFrame:
    columns = [
        "city_name",
        "climate_group",
        "pr_auc_logistic",
        "pr_auc_rf",
        "pr_auc_delta_rf_minus_logistic",
        "recall_at_top_10pct_logistic",
        "recall_at_top_10pct_rf",
        "recall_delta_rf_minus_logistic",
    ]
    return (
        city_error_df.sort_values(metric_column, ascending=ascending)
        .loc[:, columns]
        .head(top_n)
        .reset_index(drop=True)
    )


def write_modeling_report_markdown(
    benchmark_df: pd.DataFrame,
    city_error_df: pd.DataFrame,
    climate_summary_df: pd.DataFrame,
    paths: ReportingPaths,
    benchmark_metrics_figure_path: Path,
    runtime_figure_path: Path,
    city_delta_figure_path: Path,
    phase1_candidate_df: pd.DataFrame | None = None,
    phase1_candidate_climate_df: pd.DataFrame | None = None,
    phase2_candidate_df: pd.DataFrame | None = None,
    phase2_candidate_climate_df: pd.DataFrame | None = None,
    phase2_candidate_disparity_df: pd.DataFrame | None = None,
    phase3_candidate_df: pd.DataFrame | None = None,
    phase3_candidate_climate_df: pd.DataFrame | None = None,
) -> Path:
    """Write the markdown report for the current benchmark and city-error analysis."""
    benchmark_display = benchmark_df.copy()
    benchmark_display = benchmark_display[
        [
            "run_label",
            "model_family",
            "preset",
            "rows_per_city",
            "param_candidate_count",
            "estimated_total_inner_fits",
            "pooled_pr_auc",
            "mean_city_pr_auc",
            "pooled_recall_at_top_10pct",
            "runtime_minutes",
            "notes",
        ]
    ]
    top_gains = _top_city_delta_table(city_error_df, metric_column="pr_auc_delta_rf_minus_logistic", top_n=5, ascending=False)
    top_losses = _top_city_delta_table(city_error_df, metric_column="pr_auc_delta_rf_minus_logistic", top_n=5, ascending=True)

    rf_pr_auc_wins = int((city_error_df["pr_auc_delta_rf_minus_logistic"] > 0).sum())
    logistic_pr_auc_wins = int((city_error_df["pr_auc_delta_rf_minus_logistic"] < 0).sum())
    rf_recall_wins = int((city_error_df["recall_delta_rf_minus_logistic"] > 0).sum())
    logistic_recall_wins = int((city_error_df["recall_delta_rf_minus_logistic"] < 0).sum())

    report_lines = [
        "# Cross-City Modeling Report",
        "",
        "Purpose:",
        "",
        "- summarize the retained logistic and random-forest benchmark checkpoints most relevant for reporting",
        "- compare city-level performance between the matched logistic `5000` slice and the current RF `frontier` checkpoint",
        "- capture the current stop / escalate interpretation without requiring any new model runs",
        "",
        "## Benchmark Comparison",
        "",
        _dataframe_to_markdown(
            benchmark_display,
            decimal_columns={"pooled_pr_auc", "mean_city_pr_auc", "pooled_recall_at_top_10pct"},
        ),
        "",
        "## City-Level Error Analysis",
        "",
        f"- RF frontier beats logistic 5k on PR AUC in `{rf_pr_auc_wins}` cities and trails in `{logistic_pr_auc_wins}`.",
        f"- RF frontier beats logistic 5k on recall at top 10% in `{rf_recall_wins}` cities and trails in `{logistic_recall_wins}`.",
        f"- Mean PR AUC delta (RF minus logistic) is `{city_error_df['pr_auc_delta_rf_minus_logistic'].mean():.4f}`.",
        f"- Mean recall-at-top-10% delta (RF minus logistic) is `{city_error_df['recall_delta_rf_minus_logistic'].mean():.4f}`.",
        "",
        "### Climate Summary",
        "",
        _dataframe_to_markdown(
            climate_summary_df,
            decimal_columns={"mean_pr_auc_delta", "median_pr_auc_delta", "mean_recall_delta", "median_recall_delta"},
        ),
        "",
        "### Top RF Gains By City",
        "",
        _dataframe_to_markdown(
            top_gains,
            decimal_columns={
                "pr_auc_logistic",
                "pr_auc_rf",
                "pr_auc_delta_rf_minus_logistic",
                "recall_at_top_10pct_logistic",
                "recall_at_top_10pct_rf",
                "recall_delta_rf_minus_logistic",
            },
        ),
        "",
        "### Top RF Losses By City",
        "",
        _dataframe_to_markdown(
            top_losses,
            decimal_columns={
                "pr_auc_logistic",
                "pr_auc_rf",
                "pr_auc_delta_rf_minus_logistic",
                "recall_at_top_10pct_logistic",
                "recall_at_top_10pct_rf",
                "recall_delta_rf_minus_logistic",
            },
        ),
        "",
        "## Figure Outputs",
        "",
        f"- benchmark metric comparison: `{benchmark_metrics_figure_path}`",
        f"- runtime versus pooled PR AUC: `{runtime_figure_path}`",
        f"- city-level RF-minus-logistic deltas: `{city_delta_figure_path}`",
        "",
        "## Current Interpretation",
        "",
        "The retained logistic and RF checkpoints all outperform the strongest simple transfer baselines on pooled PR AUC. "
        "At the matched `5000` rows-per-city slice, RF still improves pooled PR AUC and top-decile recall relative to logistic, but logistic remains slightly stronger on mean city PR AUC. "
        "The city-level deltas show that RF's gains are concentrated mainly in hot-arid cities, while logistic remains steadier across hot-humid and mild-cool cities. "
        "That supports the current project conclusion: RF adds a real but uneven nonlinear benefit, and the current frontier checkpoint is informative enough for reporting without automatically justifying a broader RF search.",
        "",
    ]
    if phase1_candidate_df is not None and phase1_candidate_climate_df is not None:
        hgb_pr_auc_wins = int((phase1_candidate_df["pr_auc_delta_hgb_minus_rf"] > 0).sum())
        rf_phase1_pr_auc_wins = int((phase1_candidate_df["pr_auc_delta_hgb_minus_rf"] < 0).sum())
        hgb_recall_wins = int((phase1_candidate_df["recall_delta_hgb_minus_rf"] > 0).sum())
        rf_phase1_recall_wins = int((phase1_candidate_df["recall_delta_hgb_minus_rf"] < 0).sum())
        report_lines.extend(
            [
                "## Phase 1 Candidate Checkpoint",
                "",
                "This section is optional and does not replace the retained logistic/RF benchmark story. "
                "It records how the bounded histogram-gradient-boosting smoke run compares with the retained RF frontier checkpoint on the same six-feature contract.",
                "",
                f"- HGB smoke beats RF frontier on PR AUC in `{hgb_pr_auc_wins}` city-fold rows and trails in `{rf_phase1_pr_auc_wins}`.",
                f"- HGB smoke beats RF frontier on recall at top 10% in `{hgb_recall_wins}` city-fold rows and trails in `{rf_phase1_recall_wins}`.",
                f"- Mean PR AUC delta (HGB minus RF frontier) is `{phase1_candidate_df['pr_auc_delta_hgb_minus_rf'].mean():.4f}`.",
                f"- Mean recall-at-top-10% delta (HGB minus RF frontier) is `{phase1_candidate_df['recall_delta_hgb_minus_rf'].mean():.4f}`.",
                "",
                "### HGB vs RF Frontier Climate Summary",
                "",
                _dataframe_to_markdown(
                    phase1_candidate_climate_df,
                    decimal_columns={
                        "mean_pr_auc_delta",
                        "median_pr_auc_delta",
                        "mean_recall_delta",
                        "median_recall_delta",
                    },
                ),
                "",
            ]
        )
    if (
        phase2_candidate_df is not None
        and phase2_candidate_climate_df is not None
        and phase2_candidate_disparity_df is not None
    ):
        interaction_pr_auc_wins = int(
            (phase2_candidate_df["pr_auc_delta_logistic_climate_interactions_minus_logistic"] > 0).sum()
        )
        logistic_phase2_pr_auc_wins = int(
            (phase2_candidate_df["pr_auc_delta_logistic_climate_interactions_minus_logistic"] < 0).sum()
        )
        interaction_recall_wins = int(
            (phase2_candidate_df["recall_delta_logistic_climate_interactions_minus_logistic"] > 0).sum()
        )
        logistic_phase2_recall_wins = int(
            (phase2_candidate_df["recall_delta_logistic_climate_interactions_minus_logistic"] < 0).sum()
        )
        report_lines.extend(
            [
                "## Phase 2 Climate-Conditioned Checkpoint",
                "",
                "This section is optional and does not replace the retained logistic/RF benchmark story. "
                "It records how a separate logistic SAGA variant with training-only climate-by-numeric interactions "
                "compares against the retained logistic benchmark slice on the same six-feature contract.",
                "",
                f"- The climate-interaction logistic variant beats retained logistic on PR AUC in `{interaction_pr_auc_wins}` city-fold rows and trails in `{logistic_phase2_pr_auc_wins}`.",
                f"- The climate-interaction logistic variant beats retained logistic on recall at top 10% in `{interaction_recall_wins}` city-fold rows and trails in `{logistic_phase2_recall_wins}`.",
                (
                    f"- Mean PR AUC delta (interaction logistic minus retained logistic) is "
                    f"`{phase2_candidate_df['pr_auc_delta_logistic_climate_interactions_minus_logistic'].mean():.4f}`."
                ),
                (
                    f"- Mean recall-at-top-10% delta (interaction logistic minus retained logistic) is "
                    f"`{phase2_candidate_df['recall_delta_logistic_climate_interactions_minus_logistic'].mean():.4f}`."
                ),
                "",
                "### Climate Summary",
                "",
                _dataframe_to_markdown(
                    phase2_candidate_climate_df,
                    decimal_columns={
                        "mean_pr_auc_logistic",
                        "mean_pr_auc_logistic_climate_interactions",
                        "mean_pr_auc_delta",
                        "median_pr_auc_delta",
                        "mean_recall_at_top_10pct_logistic",
                        "mean_recall_at_top_10pct_logistic_climate_interactions",
                        "mean_recall_delta",
                        "median_recall_delta",
                    },
                ),
                "",
                "### Climate-Group Disparity Summary",
                "",
                _dataframe_to_markdown(
                    phase2_candidate_disparity_df,
                    decimal_columns={
                        "baseline_climate_group_range",
                        "interaction_climate_group_range",
                        "range_delta_interaction_minus_baseline",
                    },
                ),
                "",
            ]
        )
    if phase3_candidate_df is not None and phase3_candidate_climate_df is not None:
        phase3_pr_auc_wins = int((phase3_candidate_df["pr_auc_delta_phase3a_minus_logistic"] > 0).sum())
        logistic_phase3_pr_auc_wins = int((phase3_candidate_df["pr_auc_delta_phase3a_minus_logistic"] < 0).sum())
        phase3_recall_wins = int((phase3_candidate_df["recall_delta_phase3a_minus_logistic"] > 0).sum())
        logistic_phase3_recall_wins = int((phase3_candidate_df["recall_delta_phase3a_minus_logistic"] < 0).sum())
        report_lines.extend(
            [
                "## Phase 3 Richer-Predictor Checkpoint",
                "",
                "This section is optional and does not replace the retained six-feature benchmark story. "
                "It records one bounded Phase 3A expansion: a logistic SAGA run on the retained `5000` rows-per-city "
                "slice with an NLCD neighborhood-context bundle added to the frozen six-feature contract. "
                "The added predictors are a `270 m` tree-cover proxy, a `270 m` vegetated-cover proxy, and a `270 m` local impervious mean.",
                "",
                f"- The richer-feature logistic variant beats retained logistic on PR AUC in `{phase3_pr_auc_wins}` city-fold rows and trails in `{logistic_phase3_pr_auc_wins}`.",
                f"- The richer-feature logistic variant beats retained logistic on recall at top 10% in `{phase3_recall_wins}` city-fold rows and trails in `{logistic_phase3_recall_wins}`.",
                (
                    f"- Mean PR AUC delta (Phase 3A richer logistic minus retained logistic) is "
                    f"`{phase3_candidate_df['pr_auc_delta_phase3a_minus_logistic'].mean():.4f}`."
                ),
                (
                    f"- Mean recall-at-top-10% delta (Phase 3A richer logistic minus retained logistic) is "
                    f"`{phase3_candidate_df['recall_delta_phase3a_minus_logistic'].mean():.4f}`."
                ),
                "",
                "### Climate Summary",
                "",
                _dataframe_to_markdown(
                    phase3_candidate_climate_df,
                    decimal_columns={
                        "mean_pr_auc_logistic",
                        "mean_pr_auc_phase3a",
                        "mean_pr_auc_delta",
                        "median_pr_auc_delta",
                        "mean_recall_at_top_10pct_logistic",
                        "mean_recall_at_top_10pct_phase3a",
                        "mean_recall_delta",
                        "median_recall_delta",
                    },
                ),
                "",
            ]
        )
    paths.output_dir.mkdir(parents=True, exist_ok=True)
    paths.markdown_path.write_text("\n".join(report_lines), encoding="utf-8")
    return paths.markdown_path


def generate_modeling_reporting_artifacts(
    *,
    report_slug: str = "cross_city_benchmark_report",
    baseline_summary_path: Path = DEFAULT_BASELINE_SUMMARY_PATH,
    logistic_run_dir: Path = DEFAULT_LOGISTIC_5K_RUN_DIR,
    random_forest_run_dir: Path = DEFAULT_RF_FRONTIER_RUN_DIR,
    hist_gradient_boosting_run_dir: Path | None = None,
    logistic_climate_interactions_run_dir: Path | None = None,
    phase3_richer_logistic_run_dir: Path | None = None,
    benchmark_run_specs: list[BenchmarkRunSpec] | None = None,
    outputs_root: Path = MODELING_REPORTING_OUTPUTS,
    figures_root: Path = MODELING_REPORTING_FIGURES,
) -> ModelingReportingResult:
    """Generate reporting tables, figures, and markdown from retained modeling outputs."""
    paths = resolve_modeling_report_paths(report_slug=report_slug, outputs_root=outputs_root, figures_root=figures_root)
    paths.output_dir.mkdir(parents=True, exist_ok=True)
    paths.tables_dir.mkdir(parents=True, exist_ok=True)
    paths.figures_dir.mkdir(parents=True, exist_ok=True)

    resolved_run_specs = _default_benchmark_run_specs() if benchmark_run_specs is None else list(benchmark_run_specs)
    if hist_gradient_boosting_run_dir is not None:
        resolved_hgb_dir = hist_gradient_boosting_run_dir.resolve()
        if all(spec.run_dir.resolve() != resolved_hgb_dir for spec in resolved_run_specs):
            resolved_run_specs.append(
                BenchmarkRunSpec(
                    label="hist_gradient_boosting_smoke_5k",
                    run_dir=resolved_hgb_dir,
                    notes="Bounded Phase 1 better-learner checkpoint on the fixed six-feature contract",
                )
            )
    if logistic_climate_interactions_run_dir is not None:
        resolved_phase2_dir = logistic_climate_interactions_run_dir.resolve()
        if all(spec.run_dir.resolve() != resolved_phase2_dir for spec in resolved_run_specs):
            resolved_run_specs.append(
                BenchmarkRunSpec(
                    label="logistic_saga_climate_interactions",
                    run_dir=resolved_phase2_dir,
                    notes=(
                        "Phase 2 climate-conditioned logistic benchmark on the fixed six-feature contract "
                        "with training-only climate-by-numeric interactions"
                    ),
                )
            )
    if phase3_richer_logistic_run_dir is not None:
        resolved_phase3_dir = phase3_richer_logistic_run_dir.resolve()
        if all(spec.run_dir.resolve() != resolved_phase3_dir for spec in resolved_run_specs):
            resolved_run_specs.append(
                BenchmarkRunSpec(
                    label="logistic_saga_phase3a",
                    run_dir=resolved_phase3_dir,
                    notes=(
                        "Phase 3A richer-predictor logistic checkpoint with bounded NLCD neighborhood-context "
                        "features added to the retained six-feature contract"
                    ),
                )
            )

    benchmark_df = build_benchmark_comparison_table(
        baseline_summary_path=baseline_summary_path,
        run_specs=resolved_run_specs,
    )
    city_error_df = build_city_error_comparison(
        logistic_run_dir=logistic_run_dir,
        random_forest_run_dir=random_forest_run_dir,
    )
    climate_summary_df = summarize_city_error_by_climate(city_error_df)
    phase1_candidate_df: pd.DataFrame | None = None
    phase1_candidate_climate_df: pd.DataFrame | None = None
    phase2_candidate_df: pd.DataFrame | None = None
    phase2_candidate_climate_df: pd.DataFrame | None = None
    phase2_candidate_disparity_df: pd.DataFrame | None = None
    phase3_candidate_df: pd.DataFrame | None = None
    phase3_candidate_climate_df: pd.DataFrame | None = None

    benchmark_table_path = paths.tables_dir / f"{report_slug}_benchmark_table.csv"
    city_error_table_path = paths.tables_dir / f"{report_slug}_city_error_comparison.csv"
    climate_summary_path = paths.tables_dir / f"{report_slug}_city_error_by_climate.csv"
    benchmark_df.to_csv(benchmark_table_path, index=False)
    city_error_df.to_csv(city_error_table_path, index=False)
    climate_summary_df.to_csv(climate_summary_path, index=False)
    phase1_candidate_table_path: Path | None = None
    phase1_candidate_climate_summary_path: Path | None = None
    phase2_candidate_table_path: Path | None = None
    phase2_candidate_climate_summary_path: Path | None = None
    phase2_candidate_disparity_summary_path: Path | None = None
    phase3_candidate_table_path: Path | None = None
    phase3_candidate_climate_summary_path: Path | None = None
    if hist_gradient_boosting_run_dir is not None:
        phase1_candidate_df = build_phase1_candidate_comparison(
            hist_gradient_boosting_run_dir=hist_gradient_boosting_run_dir,
            random_forest_run_dir=random_forest_run_dir,
        )
        phase1_candidate_climate_df = summarize_phase1_candidate_by_climate(phase1_candidate_df)
        phase1_candidate_table_path = paths.tables_dir / f"{report_slug}_phase1_hgb_vs_rf.csv"
        phase1_candidate_climate_summary_path = (
            paths.tables_dir / f"{report_slug}_phase1_hgb_vs_rf_by_climate.csv"
        )
        phase1_candidate_df.to_csv(phase1_candidate_table_path, index=False)
        phase1_candidate_climate_df.to_csv(phase1_candidate_climate_summary_path, index=False)
    if logistic_climate_interactions_run_dir is not None:
        phase2_candidate_df = build_phase2_candidate_comparison(
            logistic_run_dir=logistic_run_dir,
            logistic_climate_interactions_run_dir=logistic_climate_interactions_run_dir,
        )
        phase2_candidate_climate_df = summarize_phase2_candidate_by_climate(phase2_candidate_df)
        phase2_candidate_disparity_df = summarize_phase2_climate_disparity(phase2_candidate_climate_df)
        phase2_candidate_table_path = paths.tables_dir / f"{report_slug}_phase2_logistic_ci_vs_logistic.csv"
        phase2_candidate_climate_summary_path = (
            paths.tables_dir / f"{report_slug}_phase2_logistic_ci_vs_logistic_by_climate.csv"
        )
        phase2_candidate_disparity_summary_path = (
            paths.tables_dir / f"{report_slug}_phase2_logistic_ci_vs_logistic_disparity.csv"
        )
        phase2_candidate_df.to_csv(phase2_candidate_table_path, index=False)
        phase2_candidate_climate_df.to_csv(phase2_candidate_climate_summary_path, index=False)
        phase2_candidate_disparity_df.to_csv(phase2_candidate_disparity_summary_path, index=False)
    if phase3_richer_logistic_run_dir is not None:
        phase3_candidate_df = build_phase3_candidate_comparison(
            logistic_run_dir=logistic_run_dir,
            richer_predictor_run_dir=phase3_richer_logistic_run_dir,
        )
        phase3_candidate_climate_df = summarize_phase3_candidate_by_climate(phase3_candidate_df)
        phase3_candidate_table_path = paths.tables_dir / f"{report_slug}_phase3_richer_vs_logistic.csv"
        phase3_candidate_climate_summary_path = (
            paths.tables_dir / f"{report_slug}_phase3_richer_vs_logistic_by_climate.csv"
        )
        phase3_candidate_df.to_csv(phase3_candidate_table_path, index=False)
        phase3_candidate_climate_df.to_csv(phase3_candidate_climate_summary_path, index=False)

    benchmark_metrics_figure_path = paths.figures_dir / f"{report_slug}_benchmark_metrics.png"
    runtime_figure_path = paths.figures_dir / f"{report_slug}_runtime_vs_pr_auc.png"
    city_delta_figure_path = paths.figures_dir / f"{report_slug}_city_metric_deltas.png"
    plot_benchmark_metric_comparison(benchmark_df=benchmark_df, output_path=benchmark_metrics_figure_path)
    plot_runtime_vs_performance(benchmark_df=benchmark_df, output_path=runtime_figure_path)
    plot_city_metric_deltas(city_error_df=city_error_df, output_path=city_delta_figure_path)

    markdown_path = write_modeling_report_markdown(
        benchmark_df=benchmark_df,
        city_error_df=city_error_df,
        climate_summary_df=climate_summary_df,
        paths=paths,
        benchmark_metrics_figure_path=benchmark_metrics_figure_path,
        runtime_figure_path=runtime_figure_path,
        city_delta_figure_path=city_delta_figure_path,
        phase1_candidate_df=phase1_candidate_df,
        phase1_candidate_climate_df=phase1_candidate_climate_df,
        phase2_candidate_df=phase2_candidate_df,
        phase2_candidate_climate_df=phase2_candidate_climate_df,
        phase2_candidate_disparity_df=phase2_candidate_disparity_df,
        phase3_candidate_df=phase3_candidate_df,
        phase3_candidate_climate_df=phase3_candidate_climate_df,
    )
    logger.info("Wrote cross-city modeling reporting artifacts under %s", paths.output_dir)
    return ModelingReportingResult(
        markdown_path=markdown_path,
        benchmark_table_path=benchmark_table_path,
        city_error_table_path=city_error_table_path,
        climate_summary_path=climate_summary_path,
        benchmark_metrics_figure_path=benchmark_metrics_figure_path,
        runtime_figure_path=runtime_figure_path,
        city_delta_figure_path=city_delta_figure_path,
        phase1_candidate_table_path=phase1_candidate_table_path,
        phase1_candidate_climate_summary_path=phase1_candidate_climate_summary_path,
        phase2_candidate_table_path=phase2_candidate_table_path,
        phase2_candidate_climate_summary_path=phase2_candidate_climate_summary_path,
        phase2_candidate_disparity_summary_path=phase2_candidate_disparity_summary_path,
        phase3_candidate_table_path=phase3_candidate_table_path,
        phase3_candidate_climate_summary_path=phase3_candidate_climate_summary_path,
    )
