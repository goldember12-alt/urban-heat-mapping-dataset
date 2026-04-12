from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Sequence

import matplotlib
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import get_scorer
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.config import (
    MODELING_REPORTING_OUTPUTS,
    MODELING_SUPPLEMENTAL_FEATURE_IMPORTANCE_FIGURES,
    MODELING_SUPPLEMENTAL_FEATURE_IMPORTANCE_OUTPUTS,
    MODELING_SUPPLEMENTAL_WITHIN_CITY_FIGURES,
    MODELING_SUPPLEMENTAL_WITHIN_CITY_OUTPUTS,
    PROJECT_ROOT,
)
from src.modeling_config import (
    CITY_NAME_COLUMN,
    DEFAULT_FEATURE_COLUMNS,
    DEFAULT_PR_SCORING,
    DEFAULT_RANDOM_STATE,
    DEFAULT_TOP_FRACTION,
    GROUP_COLUMN,
    TARGET_COLUMN,
    get_model_tuning_spec,
    split_model_feature_columns,
)
from src.modeling_data import (
    drop_missing_target_rows,
    load_outer_fold_data,
    load_sampled_modeling_rows_with_diagnostics,
)
from src.modeling_metrics import (
    build_calibration_curve_table,
    compute_prediction_metrics,
    safe_average_precision,
)
from src.modeling_reporting import (
    DEFAULT_LOGISTIC_20K_RUN_DIR,
    DEFAULT_RF_FRONTIER_RUN_DIR,
    DEFAULT_RF_SMOKE_RUN_DIR,
)
from src.modeling_runner import build_logistic_saga_pipeline, build_random_forest_pipeline

LOGGER = logging.getLogger(__name__)

DEFAULT_WITHIN_CITY_CITY_ERROR_TABLE_PATH = (
    MODELING_REPORTING_OUTPUTS / "tables" / "cross_city_benchmark_report_city_error_comparison.csv"
)
DEFAULT_WITHIN_CITY_CITY_BY_CLIMATE = {
    "hot_arid": "Reno",
    "hot_humid": "Charlotte",
    "mild_cool": "Detroit",
}
DEFAULT_WITHIN_CITY_SAMPLE_ROWS_PER_CITY = 20_000
DEFAULT_WITHIN_CITY_TEST_SIZE = 0.20
DEFAULT_WITHIN_CITY_SPLIT_SEEDS = (42, 43, 44)
DEFAULT_WITHIN_CITY_LOGISTIC_PRESET = "smoke"
DEFAULT_WITHIN_CITY_RF_PRESET = "smoke"
DEFAULT_WITHIN_CITY_LOGISTIC_REFERENCE_RUN_DIR = DEFAULT_LOGISTIC_20K_RUN_DIR
DEFAULT_WITHIN_CITY_RF_REFERENCE_RUN_DIR = DEFAULT_RF_SMOKE_RUN_DIR
DEFAULT_FEATURE_IMPORTANCE_LOGISTIC_RUN_DIR = DEFAULT_LOGISTIC_20K_RUN_DIR
DEFAULT_FEATURE_IMPORTANCE_RF_RUN_DIR = DEFAULT_RF_FRONTIER_RUN_DIR
DEFAULT_RF_PERMUTATION_REPEATS = 10


@dataclass(frozen=True)
class SupplementalPaths:
    output_dir: Path
    tables_dir: Path
    figures_dir: Path
    metadata_path: Path


@dataclass(frozen=True)
class WithinCitySupplementResult:
    summary_markdown_path: Path
    city_selection_path: Path
    sample_diagnostics_path: Path
    split_metrics_path: Path
    summary_table_path: Path
    contrast_table_path: Path
    best_params_path: Path
    predictions_path: Path
    calibration_curve_path: Path
    metadata_path: Path
    figure_path: Path


@dataclass(frozen=True)
class FeatureImportanceAnalysisResult:
    summary_markdown_path: Path
    logistic_feature_names_path: Path
    logistic_coefficients_by_fold_path: Path
    logistic_coefficients_summary_path: Path
    logistic_refit_metrics_path: Path
    rf_permutation_by_fold_path: Path
    rf_permutation_summary_path: Path
    rf_refit_metrics_path: Path
    metadata_path: Path
    figure_path: Path


def resolve_supplemental_paths(
    *,
    output_dir: Path,
    figures_dir: Path,
) -> SupplementalPaths:
    resolved_output_dir = output_dir.resolve()
    resolved_figures_dir = figures_dir.resolve()
    tables_dir = resolved_output_dir / "tables"
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    resolved_figures_dir.mkdir(parents=True, exist_ok=True)
    return SupplementalPaths(
        output_dir=resolved_output_dir,
        tables_dir=tables_dir,
        figures_dir=resolved_figures_dir,
        metadata_path=resolved_output_dir / "run_metadata.json",
    )


def _resolve_project_path(path: Path | str | None) -> Path | None:
    if path is None:
        return None
    candidate = Path(path)
    return candidate if candidate.is_absolute() else (PROJECT_ROOT / candidate)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


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
    header = "| " + " | ".join(df.columns.astype(str)) + " |"
    separator = "| " + " | ".join(["---"] * len(df.columns)) + " |"
    rows = [header, separator]
    for _, row in df.iterrows():
        formatted: list[str] = []
        for column_name in df.columns:
            value = row[column_name]
            decimals = 4 if column_name in decimal_columns else 0
            formatted.append(_format_scalar(value, decimals=decimals))
        rows.append("| " + " | ".join(formatted) + " |")
    return "\n".join(rows)


def select_representative_within_city_cities(
    *,
    city_error_table_path: Path = DEFAULT_WITHIN_CITY_CITY_ERROR_TABLE_PATH,
    fallback_city_by_climate: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Select one representative city per climate group using nearest-median logistic PR AUC."""
    comparison_df = pd.read_csv(_resolve_project_path(city_error_table_path))
    fallback_map = dict(DEFAULT_WITHIN_CITY_CITY_BY_CLIMATE if fallback_city_by_climate is None else fallback_city_by_climate)

    required_columns = {"city_id", "city_name", "climate_group", "pr_auc_logistic"}
    missing_columns = sorted(required_columns - set(comparison_df.columns))
    if missing_columns:
        raise ValueError(
            "City comparison table is missing required columns: " + ", ".join(missing_columns)
        )

    unique_cities = (
        comparison_df[["city_id", "city_name", "climate_group", "pr_auc_logistic"]]
        .drop_duplicates(subset=["city_id", "city_name", "climate_group"])
        .reset_index(drop=True)
    )

    selected_rows: list[dict[str, Any]] = []
    for climate_group, fallback_city in fallback_map.items():
        group_df = unique_cities.loc[unique_cities["climate_group"] == climate_group].copy()
        if group_df.empty:
            raise ValueError(f"No cities found for climate_group={climate_group}")

        group_median = float(group_df["pr_auc_logistic"].median())
        group_df["abs_diff_to_group_median"] = (group_df["pr_auc_logistic"] - group_median).abs()
        group_df["fallback_priority"] = np.where(group_df["city_name"] == fallback_city, 0, 1)
        group_df = group_df.sort_values(
            ["abs_diff_to_group_median", "fallback_priority", "pr_auc_logistic", "city_name"],
            ascending=[True, True, True, True],
        ).reset_index(drop=True)
        selected = group_df.iloc[0]
        selected_rows.append(
            {
                "city_id": int(selected["city_id"]),
                "city_name": str(selected["city_name"]),
                "climate_group": climate_group,
                "pr_auc_logistic": float(selected["pr_auc_logistic"]),
                "climate_group_logistic_pr_auc_median": group_median,
                "abs_diff_to_group_median": float(selected["abs_diff_to_group_median"]),
                "fallback_default_city_name": fallback_city,
                "selection_rule": "nearest_median_logistic_pr_auc_within_climate_group",
            }
        )

    return pd.DataFrame(selected_rows).sort_values(["climate_group", "city_name"]).reset_index(drop=True)


def _load_cross_city_reference_metrics(
    *,
    logistic_run_dir: Path,
    random_forest_run_dir: Path,
) -> pd.DataFrame:
    logistic_df = pd.read_csv(_resolve_project_path(logistic_run_dir) / "metrics_by_city.csv").copy()
    rf_df = pd.read_csv(_resolve_project_path(random_forest_run_dir) / "metrics_by_city.csv").copy()

    logistic_df["model_name"] = "logistic_saga"
    rf_df["model_name"] = "random_forest"
    combined = pd.concat([logistic_df, rf_df], ignore_index=True)
    combined["cross_city_reference_run_dir"] = np.where(
        combined["model_name"] == "logistic_saga",
        str(_resolve_project_path(logistic_run_dir)),
        str(_resolve_project_path(random_forest_run_dir)),
    )
    combined["cross_city_reference_run_label"] = np.where(
        combined["model_name"] == "logistic_saga",
        Path(logistic_run_dir).name,
        Path(random_forest_run_dir).name,
    )
    combined = combined.rename(
        columns={
            "pr_auc": "cross_city_pr_auc",
            "recall_at_top_10pct": "cross_city_recall_at_top_10pct",
            "row_count": "cross_city_row_count",
            "positive_count": "cross_city_positive_count",
            "prevalence": "cross_city_prevalence",
        }
    )
    keep_columns = [
        "model_name",
        "city_id",
        "city_name",
        "climate_group",
        "cross_city_row_count",
        "cross_city_positive_count",
        "cross_city_prevalence",
        "cross_city_pr_auc",
        "cross_city_recall_at_top_10pct",
        "cross_city_reference_run_dir",
        "cross_city_reference_run_label",
    ]
    return combined[keep_columns].drop_duplicates(
        subset=["model_name", "city_id", "city_name", "climate_group"]
    )


def _resolve_effective_stratified_cv_splits(y: Sequence[int], requested_splits: int) -> int:
    class_counts = pd.Series(y).value_counts(dropna=False)
    if class_counts.empty:
        raise ValueError("Cannot fit a stratified model on an empty target vector")
    effective_splits = min(int(requested_splits), int(class_counts.min()))
    if effective_splits < 2:
        raise ValueError(
            "At least two observations in each class are required for stratified CV inside a within-city split"
        )
    return effective_splits


def _fit_within_city_model(
    *,
    model_name: str,
    feature_columns: Sequence[str],
    train_df: pd.DataFrame,
    random_state: int,
    tuning_preset: str,
    grid_search_n_jobs: int,
    model_n_jobs: int | None = None,
) -> tuple[Any, float, dict[str, Any], int]:
    tuning_spec = get_model_tuning_spec(model_name, tuning_preset)
    effective_inner_splits = _resolve_effective_stratified_cv_splits(
        train_df[TARGET_COLUMN].to_numpy(dtype="int8"),
        tuning_spec.inner_cv_splits,
    )

    if model_name == "logistic_saga":
        estimator = build_logistic_saga_pipeline(
            feature_columns=feature_columns,
            random_state=random_state,
        )
    elif model_name == "random_forest":
        estimator = build_random_forest_pipeline(
            feature_columns=feature_columns,
            random_state=random_state,
            n_jobs=model_n_jobs,
        )
    else:
        raise ValueError(f"Unsupported within-city model_name: {model_name}")

    grid_search = GridSearchCV(
        estimator=estimator,
        param_grid=list(tuning_spec.param_grid),
        cv=StratifiedKFold(
            n_splits=effective_inner_splits,
            shuffle=True,
            random_state=int(random_state),
        ),
        scoring=get_scorer(DEFAULT_PR_SCORING),
        n_jobs=grid_search_n_jobs,
        refit=True,
        error_score="raise",
    )
    grid_search.fit(
        train_df[list(feature_columns)],
        train_df[TARGET_COLUMN].to_numpy(dtype="int8"),
    )
    return grid_search.best_estimator_, float(grid_search.best_score_), dict(grid_search.best_params_), effective_inner_splits


def _build_within_city_prediction_frame(
    *,
    test_df: pd.DataFrame,
    probabilities: np.ndarray,
    model_name: str,
    repeat_id: int,
    split_seed: int,
) -> pd.DataFrame:
    prediction_df = test_df[
        [GROUP_COLUMN, CITY_NAME_COLUMN, "climate_group", "cell_id", "centroid_lon", "centroid_lat", TARGET_COLUMN]
    ].copy()
    prediction_df["model_name"] = model_name
    prediction_df["repeat_id"] = int(repeat_id)
    prediction_df["split_seed"] = int(split_seed)
    prediction_df["predicted_probability"] = probabilities
    return prediction_df


def plot_within_city_contrast(contrast_df: pd.DataFrame, output_path: Path) -> Path:
    """Plot within-city versus retained cross-city PR AUC for the selected city-model pairs."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ordered = contrast_df.sort_values(["climate_group", "city_name", "model_name"]).reset_index(drop=True)
    y_positions = np.arange(len(ordered))
    model_colors = {"logistic_saga": "#2f6c8f", "random_forest": "#9b3d2f"}

    fig, ax = plt.subplots(figsize=(10, 6.5), constrained_layout=True)
    for index, row in ordered.iterrows():
        color = model_colors.get(str(row["model_name"]), "#666666")
        cross_value = float(row["cross_city_pr_auc"])
        within_value = float(row["within_city_pr_auc_mean"])
        ax.plot([cross_value, within_value], [index, index], color=color, linewidth=2, alpha=0.8)
        ax.scatter(cross_value, index, color="white", edgecolor=color, s=65, zorder=3)
        ax.scatter(within_value, index, color=color, edgecolor=color, s=65, zorder=3)

    ax.set_yticks(y_positions)
    ax.set_yticklabels(
        [
            f"{row.city_name} ({row.climate_group}, {'log' if row.model_name == 'logistic_saga' else 'rf'})"
            for row in ordered.itertuples(index=False)
        ],
        fontsize=9,
    )
    ax.set_xlabel("PR AUC")
    ax.set_title("Exploratory Within-City PR AUC vs Retained Cross-City Benchmark")
    ax.grid(axis="x", alpha=0.25)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def generate_within_city_supplemental_artifacts(
    *,
    dataset_path: Path,
    city_error_table_path: Path = DEFAULT_WITHIN_CITY_CITY_ERROR_TABLE_PATH,
    output_dir: Path = MODELING_SUPPLEMENTAL_WITHIN_CITY_OUTPUTS,
    figures_dir: Path = MODELING_SUPPLEMENTAL_WITHIN_CITY_FIGURES,
    feature_columns: Sequence[str] = DEFAULT_FEATURE_COLUMNS,
    sample_rows_per_city: int = DEFAULT_WITHIN_CITY_SAMPLE_ROWS_PER_CITY,
    split_seeds: Sequence[int] = DEFAULT_WITHIN_CITY_SPLIT_SEEDS,
    test_size: float = DEFAULT_WITHIN_CITY_TEST_SIZE,
    random_state: int = DEFAULT_RANDOM_STATE,
    logistic_tuning_preset: str = DEFAULT_WITHIN_CITY_LOGISTIC_PRESET,
    random_forest_tuning_preset: str = DEFAULT_WITHIN_CITY_RF_PRESET,
    logistic_reference_run_dir: Path = DEFAULT_WITHIN_CITY_LOGISTIC_REFERENCE_RUN_DIR,
    random_forest_reference_run_dir: Path = DEFAULT_WITHIN_CITY_RF_REFERENCE_RUN_DIR,
    grid_search_n_jobs: int = 1,
    model_n_jobs: int | None = 1,
) -> WithinCitySupplementResult:
    """Run the bounded exploratory within-city contrast layer."""
    start = perf_counter()
    paths = resolve_supplemental_paths(output_dir=output_dir, figures_dir=figures_dir)

    city_selection_df = select_representative_within_city_cities(
        city_error_table_path=city_error_table_path,
    )
    selected_city_ids = city_selection_df[GROUP_COLUMN].astype(int).tolist()
    sampled_rows_df, sample_diagnostics_df = load_sampled_modeling_rows_with_diagnostics(
        dataset_path=_resolve_project_path(dataset_path),
        feature_columns=feature_columns,
        city_ids=selected_city_ids,
        sample_rows_per_city=int(sample_rows_per_city),
        random_state=int(random_state),
    )
    sampled_rows_df = drop_missing_target_rows(sampled_rows_df)

    prediction_frames: list[pd.DataFrame] = []
    split_metric_rows: list[dict[str, Any]] = []
    best_param_rows: list[dict[str, Any]] = []

    for city_row in city_selection_df.itertuples(index=False):
        city_df = sampled_rows_df.loc[sampled_rows_df[GROUP_COLUMN] == int(city_row.city_id)].copy().reset_index(drop=True)
        if city_df.empty:
            raise ValueError(f"No within-city rows were loaded for city_id={city_row.city_id}")

        y = city_df[TARGET_COLUMN].to_numpy(dtype="int8")
        if np.unique(y).size < 2:
            raise ValueError(f"Within-city sampling produced a single-class dataset for city_id={city_row.city_id}")

        for repeat_id, split_seed in enumerate(split_seeds, start=1):
            train_index, test_index = train_test_split(
                np.arange(len(city_df)),
                test_size=float(test_size),
                random_state=int(split_seed),
                stratify=y,
            )
            train_df = city_df.iloc[train_index].reset_index(drop=True)
            test_df = city_df.iloc[test_index].reset_index(drop=True)

            for model_name, tuning_preset in (
                ("logistic_saga", logistic_tuning_preset),
                ("random_forest", random_forest_tuning_preset),
            ):
                estimator, best_score, best_params, effective_inner_splits = _fit_within_city_model(
                    model_name=model_name,
                    feature_columns=feature_columns,
                    train_df=train_df,
                    random_state=int(split_seed),
                    tuning_preset=tuning_preset,
                    grid_search_n_jobs=int(grid_search_n_jobs),
                    model_n_jobs=model_n_jobs if model_name == "random_forest" else None,
                )
                probabilities = estimator.predict_proba(test_df[list(feature_columns)])[:, 1]
                prediction_df = _build_within_city_prediction_frame(
                    test_df=test_df,
                    probabilities=probabilities,
                    model_name=model_name,
                    repeat_id=repeat_id,
                    split_seed=int(split_seed),
                )
                prediction_frames.append(prediction_df)

                metrics = compute_prediction_metrics(
                    y_true=prediction_df[TARGET_COLUMN].to_numpy(dtype="int8"),
                    y_score=prediction_df["predicted_probability"].to_numpy(dtype="float64"),
                    top_fraction=DEFAULT_TOP_FRACTION,
                )
                split_metric_rows.append(
                    {
                        "city_id": int(city_row.city_id),
                        "city_name": str(city_row.city_name),
                        "climate_group": str(city_row.climate_group),
                        "model_name": model_name,
                        "repeat_id": int(repeat_id),
                        "split_seed": int(split_seed),
                        "tuning_preset": tuning_preset,
                        "sample_rows_per_city_cap": int(sample_rows_per_city),
                        "effective_city_row_count": int(len(city_df)),
                        "train_row_count": int(len(train_df)),
                        "test_row_count": int(metrics["row_count"]),
                        "test_positive_count": int(metrics["positive_count"]),
                        "test_prevalence": float(metrics["prevalence"]),
                        "pr_auc": float(metrics["pr_auc"]),
                        "recall_at_top_10pct": float(metrics["recall_at_top_10pct"]),
                        "best_inner_cv_average_precision": float(best_score),
                        "effective_inner_cv_splits": int(effective_inner_splits),
                    }
                )
                best_param_rows.append(
                    {
                        "city_id": int(city_row.city_id),
                        "city_name": str(city_row.city_name),
                        "climate_group": str(city_row.climate_group),
                        "model_name": model_name,
                        "repeat_id": int(repeat_id),
                        "split_seed": int(split_seed),
                        "tuning_preset": tuning_preset,
                        "best_params_json": json.dumps(best_params, sort_keys=True),
                        "best_inner_cv_average_precision": float(best_score),
                    }
                )

    predictions_df = pd.concat(prediction_frames, ignore_index=True).sort_values(
        ["city_id", "model_name", "repeat_id", "cell_id"]
    )
    split_metrics_df = pd.DataFrame(split_metric_rows).sort_values(
        ["city_id", "model_name", "repeat_id"]
    ).reset_index(drop=True)
    best_params_df = pd.DataFrame(best_param_rows).sort_values(
        ["city_id", "model_name", "repeat_id"]
    ).reset_index(drop=True)

    summary_df = (
        split_metrics_df.groupby(["city_id", "city_name", "climate_group", "model_name"], dropna=False)
        .agg(
            repeat_count=("repeat_id", "count"),
            sample_rows_per_city_cap=("sample_rows_per_city_cap", "first"),
            effective_city_row_count=("effective_city_row_count", "first"),
            within_city_pr_auc_mean=("pr_auc", "mean"),
            within_city_pr_auc_std=("pr_auc", "std"),
            within_city_recall_at_top_10pct_mean=("recall_at_top_10pct", "mean"),
            within_city_recall_at_top_10pct_std=("recall_at_top_10pct", "std"),
            within_city_best_inner_cv_average_precision_mean=("best_inner_cv_average_precision", "mean"),
        )
        .reset_index()
        .sort_values(["climate_group", "city_name", "model_name"])
        .reset_index(drop=True)
    )
    for column_name in ["within_city_pr_auc_std", "within_city_recall_at_top_10pct_std"]:
        summary_df[column_name] = summary_df[column_name].fillna(0.0)

    cross_city_reference_df = _load_cross_city_reference_metrics(
        logistic_run_dir=logistic_reference_run_dir,
        random_forest_run_dir=random_forest_reference_run_dir,
    )
    contrast_df = summary_df.merge(
        cross_city_reference_df,
        on=["city_id", "city_name", "climate_group", "model_name"],
        how="left",
        validate="one_to_one",
    )
    contrast_df["pr_auc_gap"] = contrast_df["within_city_pr_auc_mean"] - contrast_df["cross_city_pr_auc"]
    contrast_df["recall_gap"] = (
        contrast_df["within_city_recall_at_top_10pct_mean"] - contrast_df["cross_city_recall_at_top_10pct"]
    )
    contrast_df = contrast_df.sort_values(["climate_group", "city_name", "model_name"]).reset_index(drop=True)

    calibration_frames: list[pd.DataFrame] = []
    for (city_id, city_name, climate_group, model_name), group_df in predictions_df.groupby(
        ["city_id", "city_name", "climate_group", "model_name"],
        sort=True,
        dropna=False,
    ):
        calibration_df = build_calibration_curve_table(
            predictions_df=group_df,
            model_name=str(model_name),
            scope_name="within_city_city_model",
            scope_value=f"{city_name}:{model_name}",
        )
        calibration_df["city_id"] = int(city_id)
        calibration_df["city_name"] = str(city_name)
        calibration_df["climate_group"] = str(climate_group)
        calibration_frames.append(calibration_df)
    calibration_curve_df = pd.concat(calibration_frames, ignore_index=True) if calibration_frames else pd.DataFrame()

    city_selection_path = paths.tables_dir / "within_city_selected_cities.csv"
    sample_diagnostics_path = paths.tables_dir / "within_city_sampling_diagnostics.csv"
    split_metrics_path = paths.tables_dir / "within_city_repeat_metrics.csv"
    summary_table_path = paths.tables_dir / "within_city_summary.csv"
    contrast_table_path = paths.tables_dir / "within_city_city_model_contrast.csv"
    best_params_path = paths.tables_dir / "within_city_best_params.csv"
    predictions_path = paths.output_dir / "within_city_predictions.parquet"
    calibration_curve_path = paths.tables_dir / "within_city_calibration_curve.csv"
    figure_path = paths.figures_dir / "within_city_pr_auc_contrast.png"
    summary_markdown_path = paths.output_dir / "within_city_contrast_summary.md"

    city_selection_df.to_csv(city_selection_path, index=False)
    sample_diagnostics_df.to_csv(sample_diagnostics_path, index=False)
    split_metrics_df.to_csv(split_metrics_path, index=False)
    summary_df.to_csv(summary_table_path, index=False)
    contrast_df.to_csv(contrast_table_path, index=False)
    best_params_df.to_csv(best_params_path, index=False)
    predictions_df.to_parquet(predictions_path, index=False)
    calibration_curve_df.to_csv(calibration_curve_path, index=False)
    plot_within_city_contrast(contrast_df=contrast_df, output_path=figure_path)

    average_gaps_df = (
        contrast_df.groupby("model_name", dropna=False)
        .agg(
            mean_pr_auc_gap=("pr_auc_gap", "mean"),
            mean_recall_gap=("recall_gap", "mean"),
        )
        .reset_index()
    )
    markdown_lines = [
        "# Within-City Exploratory Contrast",
        "",
        "This supplement is exploratory and easier than the canonical project benchmark because training and testing both occur inside the same city.",
        "The main project narrative remains the cross-city city-held-out benchmark.",
        "",
        "## Selected Cities",
        "",
        _dataframe_to_markdown(
            city_selection_df[
                [
                    "city_name",
                    "climate_group",
                    "pr_auc_logistic",
                    "climate_group_logistic_pr_auc_median",
                    "abs_diff_to_group_median",
                ]
            ],
            decimal_columns={
                "pr_auc_logistic",
                "climate_group_logistic_pr_auc_median",
                "abs_diff_to_group_median",
            },
        ),
        "",
        "## Within-City vs Cross-City Contrast",
        "",
        _dataframe_to_markdown(
            contrast_df[
                [
                    "city_name",
                    "climate_group",
                    "model_name",
                    "within_city_pr_auc_mean",
                    "cross_city_pr_auc",
                    "pr_auc_gap",
                    "within_city_recall_at_top_10pct_mean",
                    "cross_city_recall_at_top_10pct",
                    "recall_gap",
                ]
            ],
            decimal_columns={
                "within_city_pr_auc_mean",
                "cross_city_pr_auc",
                "pr_auc_gap",
                "within_city_recall_at_top_10pct_mean",
                "cross_city_recall_at_top_10pct",
                "recall_gap",
            },
        ),
        "",
        "## Average Gap By Model",
        "",
        _dataframe_to_markdown(
            average_gaps_df,
            decimal_columns={"mean_pr_auc_gap", "mean_recall_gap"},
        ),
        "",
        f"Figure: `{figure_path}`",
        "",
    ]
    summary_markdown_path.write_text("\n".join(markdown_lines), encoding="utf-8")

    _write_json(
        paths.metadata_path,
        {
            "dataset_path": str(_resolve_project_path(dataset_path)),
            "city_error_table_path": str(_resolve_project_path(city_error_table_path)),
            "selected_feature_columns": list(feature_columns),
            "sample_rows_per_city": int(sample_rows_per_city),
            "split_seeds": [int(seed) for seed in split_seeds],
            "test_size": float(test_size),
            "logistic_tuning_preset": logistic_tuning_preset,
            "random_forest_tuning_preset": random_forest_tuning_preset,
            "logistic_reference_run_dir": str(_resolve_project_path(logistic_reference_run_dir)),
            "random_forest_reference_run_dir": str(_resolve_project_path(random_forest_reference_run_dir)),
            "grid_search_n_jobs": int(grid_search_n_jobs),
            "model_n_jobs": model_n_jobs,
            "timing_seconds": {
                "total_wall_clock": float(perf_counter() - start),
            },
            "output_files": {
                "summary_markdown": str(summary_markdown_path),
                "city_selection": str(city_selection_path),
                "sampling_diagnostics": str(sample_diagnostics_path),
                "repeat_metrics": str(split_metrics_path),
                "summary_table": str(summary_table_path),
                "contrast_table": str(contrast_table_path),
                "best_params": str(best_params_path),
                "predictions": str(predictions_path),
                "calibration_curve": str(calibration_curve_path),
                "figure": str(figure_path),
            },
        },
    )

    return WithinCitySupplementResult(
        summary_markdown_path=summary_markdown_path,
        city_selection_path=city_selection_path,
        sample_diagnostics_path=sample_diagnostics_path,
        split_metrics_path=split_metrics_path,
        summary_table_path=summary_table_path,
        contrast_table_path=contrast_table_path,
        best_params_path=best_params_path,
        predictions_path=predictions_path,
        calibration_curve_path=calibration_curve_path,
        metadata_path=paths.metadata_path,
        figure_path=figure_path,
    )


def _load_best_params_table(run_dir: Path) -> pd.DataFrame:
    best_params_df = pd.read_csv(_resolve_project_path(run_dir) / "best_params_by_fold.csv").copy()
    best_params_df["best_params"] = best_params_df["best_params_json"].map(json.loads)
    return best_params_df.sort_values("outer_fold").reset_index(drop=True)


def _load_reference_run_metadata(run_dir: Path) -> dict[str, Any]:
    return json.loads((_resolve_project_path(run_dir) / "run_metadata.json").read_text(encoding="utf-8"))


def _build_post_preprocessing_feature_names(feature_columns: Sequence[str], fitted_pipeline: Any) -> list[str]:
    numeric_columns, categorical_columns = split_model_feature_columns(feature_columns)
    preprocessor = fitted_pipeline.named_steps["preprocess"]
    feature_names = list(numeric_columns)
    categorical_encoder = preprocessor.named_transformers_["categorical"].named_steps["encoder"]
    feature_names.extend(categorical_encoder.get_feature_names_out(categorical_columns).tolist())
    return feature_names


def _strip_transformer_prefix(feature_name: str) -> str:
    normalized = str(feature_name)
    for prefix in ("numeric__", "categorical__", "remainder__"):
        if normalized.startswith(prefix):
            return normalized[len(prefix) :]
    return normalized


def _infer_base_feature_name(feature_name: str, feature_columns: Sequence[str]) -> str:
    cleaned_name = _strip_transformer_prefix(feature_name)
    for raw_feature_name in sorted(feature_columns, key=len, reverse=True):
        if cleaned_name == raw_feature_name or cleaned_name.startswith(f"{raw_feature_name}_"):
            return raw_feature_name
    return cleaned_name


def _summarize_logistic_coefficients(coefficients_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for feature_name, group_df in coefficients_df.groupby("feature_name", sort=False, dropna=False):
        sign_series = np.sign(group_df["coefficient"].to_numpy(dtype="float64"))
        sign_counts = pd.Series(sign_series).value_counts()
        majority_sign = float(sign_counts.index[0]) if not sign_counts.empty else 0.0
        majority_sign_label = (
            "positive" if majority_sign > 0 else "negative" if majority_sign < 0 else "zero"
        )
        rows.append(
            {
                "feature_name": str(feature_name),
                "base_feature_name": str(group_df["base_feature_name"].iloc[0]),
                "fold_count": int(len(group_df)),
                "median_coefficient": float(group_df["coefficient"].median()),
                "median_abs_coefficient": float(group_df["abs_coefficient"].median()),
                "median_absolute_rank": float(group_df["absolute_rank"].median()),
                "majority_sign": majority_sign_label,
                "sign_consistency": float((sign_series == majority_sign).mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["median_absolute_rank", "median_abs_coefficient"],
        ascending=[True, False],
    ).reset_index(drop=True)


def _summarize_rf_permutation_importance(permutation_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for feature_name, group_df in permutation_df.groupby("feature_name", sort=False, dropna=False):
        mean_drop_series = group_df["pr_auc_drop_mean"].to_numpy(dtype="float64")
        rows.append(
            {
                "feature_name": str(feature_name),
                "fold_count": int(len(group_df)),
                "mean_pr_auc_drop": float(np.mean(mean_drop_series)),
                "std_pr_auc_drop_across_folds": float(np.std(mean_drop_series, ddof=0)),
                "median_rank": float(group_df["importance_rank"].median()),
                "rank_std_across_folds": float(np.std(group_df["importance_rank"].to_numpy(dtype="float64"), ddof=0)),
                "stability_positive_drop_fraction": float((mean_drop_series > 0).mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["mean_pr_auc_drop", "median_rank"],
        ascending=[False, True],
    ).reset_index(drop=True)


def plot_feature_importance_summary(
    *,
    logistic_summary_df: pd.DataFrame,
    rf_summary_df: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Plot concise ranked logistic and random-forest interpretation summaries."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(14, 8), constrained_layout=True)

    logistic_ordered = logistic_summary_df.sort_values("median_absolute_rank", ascending=True).reset_index(drop=True)
    logistic_y = np.arange(len(logistic_ordered))
    logistic_colors = [
        "#2f6c8f" if sign == "positive" else "#9b3d2f" if sign == "negative" else "#666666"
        for sign in logistic_ordered["majority_sign"]
    ]
    axes[0].barh(logistic_y, logistic_ordered["median_coefficient"], color=logistic_colors)
    axes[0].axvline(0.0, color="black", linewidth=1)
    axes[0].set_yticks(logistic_y)
    axes[0].set_yticklabels(logistic_ordered["feature_name"], fontsize=8)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("Median Logistic Coefficient")
    axes[0].set_title("Logistic Coefficient Summary")
    axes[0].grid(axis="x", alpha=0.25)

    rf_ordered = rf_summary_df.sort_values("mean_pr_auc_drop", ascending=True).reset_index(drop=True)
    rf_y = np.arange(len(rf_ordered))
    axes[1].barh(rf_y, rf_ordered["mean_pr_auc_drop"], color="#9b3d2f")
    axes[1].set_yticks(rf_y)
    axes[1].set_yticklabels(rf_ordered["feature_name"], fontsize=9)
    axes[1].set_xlabel("Mean Held-Out PR AUC Drop")
    axes[1].set_title("Random-Forest Permutation Importance")
    axes[1].grid(axis="x", alpha=0.25)

    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def generate_feature_importance_artifacts(
    *,
    logistic_run_dir: Path = DEFAULT_FEATURE_IMPORTANCE_LOGISTIC_RUN_DIR,
    random_forest_run_dir: Path = DEFAULT_FEATURE_IMPORTANCE_RF_RUN_DIR,
    output_dir: Path = MODELING_SUPPLEMENTAL_FEATURE_IMPORTANCE_OUTPUTS,
    figures_dir: Path = MODELING_SUPPLEMENTAL_FEATURE_IMPORTANCE_FIGURES,
    rf_permutation_repeats: int = DEFAULT_RF_PERMUTATION_REPEATS,
    permutation_n_jobs: int | None = 1,
) -> FeatureImportanceAnalysisResult:
    """Refit retained outer-fold winners and export bounded interpretation artifacts."""
    start = perf_counter()
    paths = resolve_supplemental_paths(output_dir=output_dir, figures_dir=figures_dir)

    logistic_metadata = _load_reference_run_metadata(logistic_run_dir)
    rf_metadata = _load_reference_run_metadata(random_forest_run_dir)
    logistic_best_params_df = _load_best_params_table(logistic_run_dir)
    rf_best_params_df = _load_best_params_table(random_forest_run_dir)
    logistic_retained_metrics_df = pd.read_csv(_resolve_project_path(logistic_run_dir) / "metrics_by_fold.csv")
    rf_retained_metrics_df = pd.read_csv(_resolve_project_path(random_forest_run_dir) / "metrics_by_fold.csv")

    logistic_feature_columns = list(logistic_metadata.get("selected_feature_columns", DEFAULT_FEATURE_COLUMNS))
    rf_feature_columns = list(rf_metadata.get("selected_feature_columns", DEFAULT_FEATURE_COLUMNS))

    logistic_dataset_path = _resolve_project_path(logistic_metadata.get("dataset_path"))
    logistic_folds_path = _resolve_project_path(logistic_metadata.get("folds_path"))
    rf_dataset_path = _resolve_project_path(rf_metadata.get("dataset_path"))
    rf_folds_path = _resolve_project_path(rf_metadata.get("folds_path"))

    logistic_rows: list[dict[str, Any]] = []
    logistic_feature_name_rows: list[dict[str, Any]] = []
    logistic_refit_metric_rows: list[dict[str, Any]] = []
    logistic_intercepts: list[dict[str, Any]] = []

    for fold_row in logistic_best_params_df.itertuples(index=False):
        outer_fold = int(fold_row.outer_fold)
        fold_data = load_outer_fold_data(
            outer_fold=outer_fold,
            dataset_path=logistic_dataset_path,
            folds_path=logistic_folds_path,
            feature_columns=logistic_feature_columns,
            sample_rows_per_city=logistic_metadata.get("sample_rows_per_city"),
            random_state=int(logistic_metadata.get("random_state", DEFAULT_RANDOM_STATE)),
        )
        estimator = build_logistic_saga_pipeline(
            feature_columns=logistic_feature_columns,
            random_state=int(logistic_metadata.get("random_state", DEFAULT_RANDOM_STATE)),
            max_iter=int(logistic_metadata.get("pipeline_builder_kwargs", {}).get("max_iter", 4000)),
            tol=float(logistic_metadata.get("pipeline_builder_kwargs", {}).get("tol", 5e-4)),
        )
        estimator.set_params(**dict(fold_row.best_params))
        estimator.fit(
            fold_data.train_df[logistic_feature_columns],
            fold_data.train_df[TARGET_COLUMN].to_numpy(dtype="int8"),
        )
        probabilities = estimator.predict_proba(fold_data.test_df[logistic_feature_columns])[:, 1]
        refit_pr_auc = safe_average_precision(
            fold_data.test_df[TARGET_COLUMN].to_numpy(dtype="int8"),
            probabilities,
        )
        retained_pr_auc = float(
            logistic_retained_metrics_df.loc[
                logistic_retained_metrics_df["outer_fold"] == outer_fold,
                "pr_auc",
            ].iloc[0]
        )
        logistic_refit_metric_rows.append(
            {
                "outer_fold": outer_fold,
                "retained_pr_auc": retained_pr_auc,
                "refit_pr_auc": float(refit_pr_auc),
                "pr_auc_refit_minus_retained": float(refit_pr_auc - retained_pr_auc),
                "train_row_count": int(len(fold_data.train_df)),
                "test_row_count": int(len(fold_data.test_df)),
            }
        )

        fitted_feature_names = _build_post_preprocessing_feature_names(logistic_feature_columns, estimator)
        coefficients = estimator.named_steps["model"].coef_.ravel()
        if len(fitted_feature_names) != len(coefficients):
            raise ValueError(
                f"Feature-name count {len(fitted_feature_names)} did not match coefficient count {len(coefficients)}"
            )
        absolute_ranks = pd.Series(np.abs(coefficients)).rank(method="dense", ascending=False).astype(int).tolist()
        logistic_intercepts.append(
            {
                "outer_fold": outer_fold,
                "intercept": float(estimator.named_steps["model"].intercept_[0]),
            }
        )
        for feature_name, coefficient, absolute_rank in zip(
            fitted_feature_names,
            coefficients,
            absolute_ranks,
            strict=True,
        ):
            cleaned_feature_name = _strip_transformer_prefix(feature_name)
            base_feature_name = _infer_base_feature_name(cleaned_feature_name, logistic_feature_columns)
            category_level = (
                cleaned_feature_name[len(base_feature_name) + 1 :]
                if cleaned_feature_name != base_feature_name and cleaned_feature_name.startswith(f"{base_feature_name}_")
                else None
            )
            logistic_feature_name_rows.append(
                {
                    "outer_fold": outer_fold,
                    "feature_name": cleaned_feature_name,
                    "base_feature_name": base_feature_name,
                    "category_level": category_level,
                }
            )
            logistic_rows.append(
                {
                    "outer_fold": outer_fold,
                    "feature_name": cleaned_feature_name,
                    "base_feature_name": base_feature_name,
                    "category_level": category_level,
                    "coefficient": float(coefficient),
                    "abs_coefficient": float(abs(coefficient)),
                    "absolute_rank": int(absolute_rank),
                }
            )

    logistic_feature_names_df = pd.DataFrame(logistic_feature_name_rows).drop_duplicates().sort_values(
        ["outer_fold", "feature_name"]
    )
    logistic_coefficients_df = pd.DataFrame(logistic_rows).sort_values(
        ["outer_fold", "absolute_rank", "feature_name"]
    )
    logistic_coefficients_summary_df = _summarize_logistic_coefficients(logistic_coefficients_df)
    logistic_refit_metrics_df = pd.DataFrame(logistic_refit_metric_rows).sort_values("outer_fold").reset_index(drop=True)
    logistic_intercepts_df = pd.DataFrame(logistic_intercepts).sort_values("outer_fold").reset_index(drop=True)

    rf_rows: list[dict[str, Any]] = []
    rf_refit_metric_rows: list[dict[str, Any]] = []
    for fold_row in rf_best_params_df.itertuples(index=False):
        outer_fold = int(fold_row.outer_fold)
        fold_data = load_outer_fold_data(
            outer_fold=outer_fold,
            dataset_path=rf_dataset_path,
            folds_path=rf_folds_path,
            feature_columns=rf_feature_columns,
            sample_rows_per_city=rf_metadata.get("sample_rows_per_city"),
            random_state=int(rf_metadata.get("random_state", DEFAULT_RANDOM_STATE)),
        )
        estimator = build_random_forest_pipeline(
            feature_columns=rf_feature_columns,
            random_state=int(rf_metadata.get("random_state", DEFAULT_RANDOM_STATE)),
            n_jobs=rf_metadata.get("model_n_jobs"),
        )
        estimator.set_params(**dict(fold_row.best_params))
        estimator.fit(
            fold_data.train_df[rf_feature_columns],
            fold_data.train_df[TARGET_COLUMN].to_numpy(dtype="int8"),
        )
        probabilities = estimator.predict_proba(fold_data.test_df[rf_feature_columns])[:, 1]
        refit_pr_auc = safe_average_precision(
            fold_data.test_df[TARGET_COLUMN].to_numpy(dtype="int8"),
            probabilities,
        )
        retained_pr_auc = float(
            rf_retained_metrics_df.loc[
                rf_retained_metrics_df["outer_fold"] == outer_fold,
                "pr_auc",
            ].iloc[0]
        )
        rf_refit_metric_rows.append(
            {
                "outer_fold": outer_fold,
                "retained_pr_auc": retained_pr_auc,
                "refit_pr_auc": float(refit_pr_auc),
                "pr_auc_refit_minus_retained": float(refit_pr_auc - retained_pr_auc),
                "train_row_count": int(len(fold_data.train_df)),
                "test_row_count": int(len(fold_data.test_df)),
            }
        )

        importance = permutation_importance(
            estimator=estimator,
            X=fold_data.test_df[rf_feature_columns],
            y=fold_data.test_df[TARGET_COLUMN].to_numpy(dtype="int8"),
            scoring=DEFAULT_PR_SCORING,
            n_repeats=int(rf_permutation_repeats),
            random_state=int(rf_metadata.get("random_state", DEFAULT_RANDOM_STATE)) + outer_fold,
            n_jobs=permutation_n_jobs,
        )
        importance_ranks = pd.Series(importance.importances_mean).rank(
            method="dense",
            ascending=False,
        ).astype(int).tolist()
        for feature_name, mean_drop, std_drop, importance_rank in zip(
            rf_feature_columns,
            importance.importances_mean.tolist(),
            importance.importances_std.tolist(),
            importance_ranks,
            strict=True,
        ):
            rf_rows.append(
                {
                    "outer_fold": outer_fold,
                    "feature_name": str(feature_name),
                    "pr_auc_drop_mean": float(mean_drop),
                    "pr_auc_drop_std": float(std_drop),
                    "importance_rank": int(importance_rank),
                    "baseline_pr_auc": float(refit_pr_auc),
                }
            )

    rf_permutation_df = pd.DataFrame(rf_rows).sort_values(
        ["outer_fold", "importance_rank", "feature_name"]
    ).reset_index(drop=True)
    rf_permutation_summary_df = _summarize_rf_permutation_importance(rf_permutation_df)
    rf_refit_metrics_df = pd.DataFrame(rf_refit_metric_rows).sort_values("outer_fold").reset_index(drop=True)

    logistic_feature_names_path = paths.tables_dir / "logistic_post_preprocessing_feature_names.csv"
    logistic_coefficients_by_fold_path = paths.tables_dir / "logistic_coefficients_by_fold.csv"
    logistic_coefficients_summary_path = paths.tables_dir / "logistic_coefficients_summary.csv"
    logistic_refit_metrics_path = paths.tables_dir / "logistic_refit_fold_metrics.csv"
    logistic_intercepts_path = paths.tables_dir / "logistic_intercepts_by_fold.csv"
    rf_permutation_by_fold_path = paths.tables_dir / "rf_permutation_importance_by_fold.csv"
    rf_permutation_summary_path = paths.tables_dir / "rf_permutation_importance_summary.csv"
    rf_refit_metrics_path = paths.tables_dir / "rf_refit_fold_metrics.csv"
    figure_path = paths.figures_dir / "feature_importance_ranked_summary.png"
    summary_markdown_path = paths.output_dir / "feature_importance_summary.md"

    logistic_feature_names_df.to_csv(logistic_feature_names_path, index=False)
    logistic_coefficients_df.to_csv(logistic_coefficients_by_fold_path, index=False)
    logistic_coefficients_summary_df.to_csv(logistic_coefficients_summary_path, index=False)
    logistic_refit_metrics_df.to_csv(logistic_refit_metrics_path, index=False)
    logistic_intercepts_df.to_csv(logistic_intercepts_path, index=False)
    rf_permutation_df.to_csv(rf_permutation_by_fold_path, index=False)
    rf_permutation_summary_df.to_csv(rf_permutation_summary_path, index=False)
    rf_refit_metrics_df.to_csv(rf_refit_metrics_path, index=False)
    plot_feature_importance_summary(
        logistic_summary_df=logistic_coefficients_summary_df,
        rf_summary_df=rf_permutation_summary_df,
        output_path=figure_path,
    )

    logistic_top = logistic_coefficients_summary_df.head(8)
    rf_top = rf_permutation_summary_df.head(6)
    markdown_lines = [
        "# Feature-Importance Summary",
        "",
        "These artifacts refit only the saved outer-fold winners from retained benchmark runs.",
        "They describe predictive reliance under the current six-feature contract and should not be read causally.",
        "",
        "## Logistic Coefficient Summary",
        "",
        _dataframe_to_markdown(
            logistic_top[
                [
                    "feature_name",
                    "base_feature_name",
                    "median_coefficient",
                    "median_abs_coefficient",
                    "median_absolute_rank",
                    "majority_sign",
                    "sign_consistency",
                ]
            ],
            decimal_columns={
                "median_coefficient",
                "median_abs_coefficient",
                "median_absolute_rank",
                "sign_consistency",
            },
        ),
        "",
        "## Random-Forest Held-Out Permutation Importance",
        "",
        _dataframe_to_markdown(
            rf_top[
                [
                    "feature_name",
                    "mean_pr_auc_drop",
                    "std_pr_auc_drop_across_folds",
                    "median_rank",
                    "stability_positive_drop_fraction",
                ]
            ],
            decimal_columns={
                "mean_pr_auc_drop",
                "std_pr_auc_drop_across_folds",
                "median_rank",
                "stability_positive_drop_fraction",
            },
        ),
        "",
        f"Figure: `{figure_path}`",
        "",
    ]
    summary_markdown_path.write_text("\n".join(markdown_lines), encoding="utf-8")

    _write_json(
        paths.metadata_path,
        {
            "logistic_run_dir": str(_resolve_project_path(logistic_run_dir)),
            "random_forest_run_dir": str(_resolve_project_path(random_forest_run_dir)),
            "logistic_dataset_path": str(logistic_dataset_path),
            "random_forest_dataset_path": str(rf_dataset_path),
            "rf_permutation_repeats": int(rf_permutation_repeats),
            "permutation_n_jobs": permutation_n_jobs,
            "timing_seconds": {
                "total_wall_clock": float(perf_counter() - start),
            },
            "output_files": {
                "summary_markdown": str(summary_markdown_path),
                "logistic_feature_names": str(logistic_feature_names_path),
                "logistic_coefficients_by_fold": str(logistic_coefficients_by_fold_path),
                "logistic_coefficients_summary": str(logistic_coefficients_summary_path),
                "logistic_refit_metrics": str(logistic_refit_metrics_path),
                "logistic_intercepts": str(logistic_intercepts_path),
                "rf_permutation_by_fold": str(rf_permutation_by_fold_path),
                "rf_permutation_summary": str(rf_permutation_summary_path),
                "rf_refit_metrics": str(rf_refit_metrics_path),
                "figure": str(figure_path),
            },
        },
    )

    return FeatureImportanceAnalysisResult(
        summary_markdown_path=summary_markdown_path,
        logistic_feature_names_path=logistic_feature_names_path,
        logistic_coefficients_by_fold_path=logistic_coefficients_by_fold_path,
        logistic_coefficients_summary_path=logistic_coefficients_summary_path,
        logistic_refit_metrics_path=logistic_refit_metrics_path,
        rf_permutation_by_fold_path=rf_permutation_by_fold_path,
        rf_permutation_summary_path=rf_permutation_summary_path,
        rf_refit_metrics_path=rf_refit_metrics_path,
        metadata_path=paths.metadata_path,
        figure_path=figure_path,
    )
