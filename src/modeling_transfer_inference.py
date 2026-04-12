from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from joblib import load

from src.config import (
    MODELING_FINAL_TRAIN_OUTPUTS,
    MODELING_TRANSFER_INFERENCE_FIGURES,
    MODELING_TRANSFER_INFERENCE_OUTPUTS,
)

LOGGER = logging.getLogger(__name__)

DEFAULT_TRANSFER_PACKAGE_DIR = (
    MODELING_FINAL_TRAIN_OUTPUTS / "random_forest_frontier_s5000_all_cities_transfer_package"
)
DEFAULT_TOP_FRACTION = 0.10
REQUIRED_IDENTIFIER_COLUMNS = ["cell_id"]
OPTIONAL_REPORTING_COLUMNS = ["city_id", "city_name", "centroid_lon", "centroid_lat"]
_NON_ALNUM_PATTERN = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class LoadedTransferPackage:
    package_dir: Path
    model_artifact_path: Path
    feature_contract_path: Path
    preprocessing_manifest_path: Path
    metadata_path: Path
    model: Any
    selected_feature_columns: list[str]
    feature_type_map: dict[str, str]
    identifier_columns: list[str]
    preprocessing_manifest: dict[str, object]
    metadata: dict[str, object]


@dataclass(frozen=True)
class TransferInferencePaths:
    inference_id: str
    output_dir: Path
    figures_dir: Path
    predictions_parquet_path: Path
    predictions_csv_path: Path
    summary_csv_path: Path
    deciles_csv_path: Path
    feature_missingness_path: Path
    markdown_path: Path
    metadata_path: Path
    figure_path: Path


@dataclass(frozen=True)
class TransferInferenceResult:
    inference_id: str
    output_dir: Path
    figures_dir: Path
    predictions_parquet_path: Path
    predictions_csv_path: Path
    summary_csv_path: Path
    deciles_csv_path: Path
    feature_missingness_path: Path
    markdown_path: Path
    metadata_path: Path
    figure_path: Path


def _require_file(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return path


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(_require_file(path).read_text(encoding="utf-8"))


def _slugify(value: str) -> str:
    normalized = _NON_ALNUM_PATTERN.sub("_", str(value).strip().lower()).strip("_")
    return normalized or "transfer_inference"


def build_transfer_inference_id(input_parquet_path: Path, inference_id: str | None = None) -> str:
    """Return a deterministic transfer-inference identifier."""
    if inference_id is not None and str(inference_id).strip():
        return _slugify(str(inference_id))
    stem = input_parquet_path.stem
    if stem.endswith("_features"):
        stem = stem[: -len("_features")]
    return _slugify(stem)


def resolve_transfer_inference_paths(
    *,
    inference_id: str,
    outputs_root: Path = MODELING_TRANSFER_INFERENCE_OUTPUTS,
    figures_root: Path = MODELING_TRANSFER_INFERENCE_FIGURES,
) -> TransferInferencePaths:
    """Return deterministic transfer-inference output and figure paths."""
    output_dir = outputs_root.resolve() / inference_id
    figures_dir = figures_root.resolve() / inference_id
    return TransferInferencePaths(
        inference_id=inference_id,
        output_dir=output_dir,
        figures_dir=figures_dir,
        predictions_parquet_path=output_dir / "predictions.parquet",
        predictions_csv_path=output_dir / "predictions.csv",
        summary_csv_path=output_dir / "prediction_summary.csv",
        deciles_csv_path=output_dir / "prediction_deciles.csv",
        feature_missingness_path=output_dir / "feature_missingness.csv",
        markdown_path=output_dir / "transfer_inference_summary.md",
        metadata_path=output_dir / "transfer_inference_metadata.json",
        figure_path=figures_dir / "predicted_risk_map.png",
    )


def load_transfer_package(package_dir: Path = DEFAULT_TRANSFER_PACKAGE_DIR) -> LoadedTransferPackage:
    """Load the retained final-train transfer package and validate its contract files."""
    resolved_dir = package_dir.resolve()
    model_artifact_path = _require_file(resolved_dir / "model.joblib")
    feature_contract_path = _require_file(resolved_dir / "feature_contract.json")
    preprocessing_manifest_path = _require_file(resolved_dir / "preprocessing_manifest.json")
    metadata_path = _require_file(resolved_dir / "transfer_package_metadata.json")

    feature_contract = _load_json(feature_contract_path)
    preprocessing_manifest = _load_json(preprocessing_manifest_path)
    metadata = _load_json(metadata_path)

    feature_columns = list(feature_contract.get("selected_feature_columns", []))
    if not feature_columns:
        raise ValueError(f"Transfer package feature contract is missing selected_feature_columns: {feature_contract_path}")
    manifest_feature_columns = list(preprocessing_manifest.get("selected_feature_columns", []))
    if manifest_feature_columns != feature_columns:
        raise ValueError(
            "Transfer package selected_feature_columns mismatch between feature_contract.json and "
            "preprocessing_manifest.json"
        )
    metadata_feature_columns = list(metadata.get("selected_feature_columns", []))
    if metadata_feature_columns and metadata_feature_columns != feature_columns:
        raise ValueError(
            "Transfer package selected_feature_columns mismatch between feature_contract.json and "
            "transfer_package_metadata.json"
        )

    model = load(model_artifact_path)
    if not hasattr(model, "predict_proba"):
        raise ValueError(f"Loaded transfer package model does not expose predict_proba(): {model_artifact_path}")

    return LoadedTransferPackage(
        package_dir=resolved_dir,
        model_artifact_path=model_artifact_path,
        feature_contract_path=feature_contract_path,
        preprocessing_manifest_path=preprocessing_manifest_path,
        metadata_path=metadata_path,
        model=model,
        selected_feature_columns=feature_columns,
        feature_type_map=dict(feature_contract.get("feature_type_map", {})),
        identifier_columns=list(feature_contract.get("identifier_columns", [])),
        preprocessing_manifest=preprocessing_manifest,
        metadata=metadata,
    )


def get_parquet_columns(input_parquet_path: Path) -> list[str]:
    """Read parquet schema column names without materializing the full table."""
    return list(pq.ParquetFile(input_parquet_path).schema.names)


def validate_transfer_input_schema(
    input_columns: list[str],
    *,
    required_feature_columns: list[str],
    required_identifier_columns: list[str] = REQUIRED_IDENTIFIER_COLUMNS,
) -> dict[str, list[str]]:
    """Validate the required input columns for transfer inference."""
    required_columns = list(dict.fromkeys([*required_identifier_columns, *required_feature_columns]))
    missing_columns = sorted(set(required_columns) - set(input_columns))
    if missing_columns:
        raise ValueError(
            "Transfer input parquet is missing required columns: " + ", ".join(missing_columns)
        )

    available_optional_columns = [
        column_name for column_name in OPTIONAL_REPORTING_COLUMNS if column_name in input_columns
    ]
    return {
        "required_columns": required_columns,
        "available_optional_columns": available_optional_columns,
    }


def read_transfer_input_parquet(
    input_parquet_path: Path,
    *,
    transfer_package: LoadedTransferPackage,
) -> pd.DataFrame:
    """Read the bounded set of required and optional transfer-inference columns."""
    available_columns = get_parquet_columns(input_parquet_path)
    validation = validate_transfer_input_schema(
        available_columns,
        required_feature_columns=transfer_package.selected_feature_columns,
    )
    selected_columns = list(
        dict.fromkeys(
            [
                *validation["required_columns"],
                *validation["available_optional_columns"],
            ]
        )
    )
    return pd.read_parquet(input_parquet_path, columns=selected_columns)


def _validate_transfer_input_values(
    input_df: pd.DataFrame,
    *,
    required_feature_columns: list[str],
) -> None:
    if input_df.empty:
        raise ValueError("Transfer input parquet contains no rows")
    if input_df["cell_id"].isna().any():
        raise ValueError("Transfer input parquet contains missing cell_id values")
    if input_df["cell_id"].duplicated().any():
        duplicate_count = int(input_df["cell_id"].duplicated().sum())
        raise ValueError(f"Transfer input parquet contains duplicate cell_id values: {duplicate_count}")
    for column_name in ("city_id", "city_name"):
        if column_name in input_df.columns:
            distinct_values = pd.Series(input_df[column_name]).dropna().astype(str).unique()
            if len(distinct_values) > 1:
                raise ValueError(
                    f"Transfer input parquet should represent one city. Column {column_name} has multiple values."
                )
    missing_feature_columns = sorted(set(required_feature_columns) - set(input_df.columns))
    if missing_feature_columns:
        raise ValueError(
            "Transfer input parquet is missing required feature columns: " + ", ".join(missing_feature_columns)
        )


def _add_prediction_labels(
    prediction_df: pd.DataFrame,
    *,
    top_fraction: float = DEFAULT_TOP_FRACTION,
) -> pd.DataFrame:
    ordered = prediction_df.sort_values(
        ["predicted_probability", "cell_id"],
        ascending=[False, True],
        kind="mergesort",
    ).reset_index(drop=True)
    ordered["prediction_rank"] = np.arange(1, len(ordered) + 1, dtype=int)
    top_n = max(1, int(np.ceil(len(ordered) * float(top_fraction))))
    ordered["predicted_hotspot_10pct"] = ordered["prediction_rank"] <= top_n
    ordered["prediction_decile"] = np.ceil(
        ordered["prediction_rank"].to_numpy(dtype="float64") * 10.0 / float(len(ordered))
    ).astype(int)
    ordered["prediction_decile"] = ordered["prediction_decile"].clip(1, 10)
    return ordered


def _build_feature_missingness_table(
    input_df: pd.DataFrame,
    *,
    feature_columns: list[str],
) -> pd.DataFrame:
    rows = []
    total_rows = len(input_df)
    for column_name in feature_columns:
        missing_count = int(input_df[column_name].isna().sum())
        rows.append(
            {
                "column_name": column_name,
                "missing_count": missing_count,
                "missing_fraction": (missing_count / total_rows) if total_rows else np.nan,
            }
        )
    return pd.DataFrame(rows).sort_values(["missing_count", "column_name"], ascending=[False, True]).reset_index(drop=True)


def _build_prediction_summary(prediction_df: pd.DataFrame, *, feature_missingness_df: pd.DataFrame) -> pd.DataFrame:
    top_hotspot_df = prediction_df.loc[prediction_df["predicted_hotspot_10pct"]].copy()
    summary_row = {
        "row_count": int(len(prediction_df)),
        "predicted_hotspot_count": int(prediction_df["predicted_hotspot_10pct"].sum()),
        "predicted_hotspot_fraction": float(prediction_df["predicted_hotspot_10pct"].mean()),
        "predicted_probability_min": float(prediction_df["predicted_probability"].min()),
        "predicted_probability_mean": float(prediction_df["predicted_probability"].mean()),
        "predicted_probability_median": float(prediction_df["predicted_probability"].median()),
        "predicted_probability_max": float(prediction_df["predicted_probability"].max()),
        "top_decile_probability_threshold": (
            float(top_hotspot_df["predicted_probability"].min()) if not top_hotspot_df.empty else np.nan
        ),
        "rows_with_any_missing_features": int(
            prediction_df[[column_name for column_name in feature_missingness_df["column_name"]]].isna().any(axis=1).sum()
        ),
    }
    for column_name in ("city_id", "city_name", "centroid_lon", "centroid_lat"):
        if column_name in prediction_df.columns and prediction_df[column_name].notna().any():
            summary_row[column_name] = prediction_df[column_name].iloc[0]
    return pd.DataFrame([summary_row])


def _build_prediction_deciles(prediction_df: pd.DataFrame) -> pd.DataFrame:
    deciles = (
        prediction_df.groupby("prediction_decile", dropna=False)
        .agg(
            row_count=("cell_id", "count"),
            predicted_probability_min=("predicted_probability", "min"),
            predicted_probability_mean=("predicted_probability", "mean"),
            predicted_probability_max=("predicted_probability", "max"),
            predicted_hotspot_count=("predicted_hotspot_10pct", "sum"),
        )
        .reset_index()
        .sort_values("prediction_decile")
        .reset_index(drop=True)
    )
    return deciles


def _marker_size(n_rows: int) -> float:
    return float(min(8.0, max(1.5, 20000.0 / max(1, n_rows))))


def _style_map_axis(axis: plt.Axes, prediction_df: pd.DataFrame, title: str) -> None:
    lon_min = float(prediction_df["centroid_lon"].min())
    lon_max = float(prediction_df["centroid_lon"].max())
    lat_min = float(prediction_df["centroid_lat"].min())
    lat_max = float(prediction_df["centroid_lat"].max())
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


def plot_transfer_inference_figure(prediction_df: pd.DataFrame, output_path: Path) -> tuple[Path, str]:
    """Write a centroid-based map when available, otherwise a probability histogram."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if {"centroid_lon", "centroid_lat"}.issubset(prediction_df.columns):
        marker_size = _marker_size(len(prediction_df))
        fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(11.5, 5.0), constrained_layout=True)

        scatter = axes[0].scatter(
            prediction_df["centroid_lon"],
            prediction_df["centroid_lat"],
            c=prediction_df["predicted_probability"],
            cmap="inferno",
            s=marker_size,
            linewidths=0,
            alpha=0.95,
        )
        _style_map_axis(axes[0], prediction_df, "Predicted hotspot risk")
        colorbar = fig.colorbar(scatter, ax=axes[0], fraction=0.046, pad=0.04)
        colorbar.set_label("Predicted probability")

        hotspot_colors = prediction_df["predicted_hotspot_10pct"].map({True: "#c64a32", False: "#d9d9d9"})
        axes[1].scatter(
            prediction_df["centroid_lon"],
            prediction_df["centroid_lat"],
            c=hotspot_colors,
            s=marker_size,
            linewidths=0,
            alpha=0.95,
        )
        _style_map_axis(axes[1], prediction_df, "Predicted top-decile hotspot cells")

        city_name = (
            str(prediction_df["city_name"].iloc[0])
            if "city_name" in prediction_df.columns and prediction_df["city_name"].notna().any()
            else "Transfer inference"
        )
        fig.suptitle(f"{city_name} transfer inference", fontsize=13)
        fig.savefig(output_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        return output_path, "centroid_map"

    fig, axis = plt.subplots(figsize=(7.5, 4.5))
    axis.hist(prediction_df["predicted_probability"], bins=20, color="#9b3d2f", edgecolor="white")
    axis.set_title("Predicted hotspot risk distribution")
    axis.set_xlabel("Predicted probability")
    axis.set_ylabel("Cell count")
    axis.grid(axis="y", alpha=0.25)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path, "score_distribution"


def _dataframe_to_markdown(df: pd.DataFrame, decimal_columns: set[str] | None = None) -> str:
    decimal_columns = decimal_columns or set()
    header = "| " + " | ".join(df.columns.astype(str)) + " |"
    separator = "| " + " | ".join(["---"] * len(df.columns)) + " |"
    rows = [header, separator]
    for _, row in df.iterrows():
        formatted_cells: list[str] = []
        for column_name in df.columns:
            value = row[column_name]
            if pd.isna(value):
                formatted_cells.append("n/a")
            elif column_name in decimal_columns:
                formatted_cells.append(f"{float(value):.4f}")
            elif isinstance(value, (float, np.floating)):
                formatted_cells.append(f"{float(value):.4f}")
            else:
                formatted_cells.append(str(value))
        rows.append("| " + " | ".join(formatted_cells) + " |")
    return "\n".join(rows)


def _build_markdown_summary(
    *,
    transfer_package: LoadedTransferPackage,
    input_parquet_path: Path,
    summary_df: pd.DataFrame,
    deciles_df: pd.DataFrame,
    figure_path: Path,
    figure_kind: str,
    paths: TransferInferencePaths,
) -> str:
    summary_display = summary_df.copy()
    decile_display = deciles_df.copy()
    return "\n".join(
        [
            "# Transfer Inference Summary",
            "",
            "Purpose:",
            "",
            "- apply the retained final-train transfer package to one new-city feature parquet",
            "- keep this scoring path separate from held-out-city benchmark evaluation",
            "- write deterministic prediction tables, a compact summary, and one map-style or fallback figure",
            "",
            "Benchmark framing note:",
            "",
            "This inference output is an application artifact derived from the retained transfer package. "
            "It is not a new held-out-city benchmark result and should be read underneath the canonical "
            "`outputs/modeling/reporting/cross_city_benchmark_report.md` benchmark narrative.",
            "",
            "Inputs:",
            "",
            f"- package dir: `{transfer_package.package_dir}`",
            f"- input parquet: `{input_parquet_path.resolve()}`",
            f"- selected feature columns: `{', '.join(transfer_package.selected_feature_columns)}`",
            f"- figure kind: `{figure_kind}`",
            "",
            "Prediction summary:",
            "",
            _dataframe_to_markdown(
                summary_display,
                decimal_columns={
                    "predicted_hotspot_fraction",
                    "predicted_probability_min",
                    "predicted_probability_mean",
                    "predicted_probability_median",
                    "predicted_probability_max",
                    "top_decile_probability_threshold",
                },
            ),
            "",
            "Prediction deciles:",
            "",
            _dataframe_to_markdown(
                decile_display,
                decimal_columns={
                    "predicted_probability_min",
                    "predicted_probability_mean",
                    "predicted_probability_max",
                },
            ),
            "",
            "Artifacts:",
            "",
            f"- predictions parquet: `{paths.predictions_parquet_path}`",
            f"- predictions csv: `{paths.predictions_csv_path}`",
            f"- summary csv: `{paths.summary_csv_path}`",
            f"- deciles csv: `{paths.deciles_csv_path}`",
            f"- feature missingness csv: `{paths.feature_missingness_path}`",
            f"- figure: `{figure_path}`",
            f"- metadata: `{paths.metadata_path}`",
            "",
        ]
    )


def run_transfer_inference(
    *,
    input_parquet_path: Path,
    package_dir: Path = DEFAULT_TRANSFER_PACKAGE_DIR,
    inference_id: str | None = None,
    top_fraction: float = DEFAULT_TOP_FRACTION,
    outputs_root: Path = MODELING_TRANSFER_INFERENCE_OUTPUTS,
    figures_root: Path = MODELING_TRANSFER_INFERENCE_FIGURES,
) -> TransferInferenceResult:
    """Apply the retained six-feature transfer package to one new-city feature parquet."""
    resolved_input_path = _require_file(input_parquet_path).resolve()
    transfer_package = load_transfer_package(package_dir=package_dir)
    input_df = read_transfer_input_parquet(
        input_parquet_path=resolved_input_path,
        transfer_package=transfer_package,
    )
    _validate_transfer_input_values(
        input_df=input_df,
        required_feature_columns=transfer_package.selected_feature_columns,
    )

    resolved_inference_id = build_transfer_inference_id(
        input_parquet_path=resolved_input_path,
        inference_id=inference_id,
    )
    paths = resolve_transfer_inference_paths(
        inference_id=resolved_inference_id,
        outputs_root=outputs_root,
        figures_root=figures_root,
    )
    paths.output_dir.mkdir(parents=True, exist_ok=True)
    paths.figures_dir.mkdir(parents=True, exist_ok=True)

    probabilities = transfer_package.model.predict_proba(
        input_df[transfer_package.selected_feature_columns]
    )[:, 1]

    prediction_columns = list(
        dict.fromkeys(
            [
                "cell_id",
                *[column for column in OPTIONAL_REPORTING_COLUMNS if column in input_df.columns],
                *transfer_package.selected_feature_columns,
            ]
        )
    )
    prediction_df = input_df[prediction_columns].copy()
    prediction_df["predicted_probability"] = probabilities.astype("float64")
    prediction_df = _add_prediction_labels(prediction_df, top_fraction=top_fraction)

    feature_missingness_df = _build_feature_missingness_table(
        input_df=input_df,
        feature_columns=transfer_package.selected_feature_columns,
    )
    summary_df = _build_prediction_summary(
        prediction_df=prediction_df,
        feature_missingness_df=feature_missingness_df,
    )
    deciles_df = _build_prediction_deciles(prediction_df)
    figure_path, figure_kind = plot_transfer_inference_figure(prediction_df=prediction_df, output_path=paths.figure_path)

    prediction_df.to_parquet(paths.predictions_parquet_path, index=False)
    prediction_df.to_csv(paths.predictions_csv_path, index=False)
    summary_df.to_csv(paths.summary_csv_path, index=False)
    deciles_df.to_csv(paths.deciles_csv_path, index=False)
    feature_missingness_df.to_csv(paths.feature_missingness_path, index=False)

    metadata_payload: dict[str, object] = {
        "artifact_kind": "transfer_inference",
        "benchmark_framing_note": (
            "This transfer inference artifact is subordinate to the canonical cross-city city-held-out benchmark "
            "and does not constitute a new evaluation run."
        ),
        "inference_id": resolved_inference_id,
        "input_parquet_path": str(resolved_input_path),
        "package_dir": str(transfer_package.package_dir),
        "package_metadata_path": str(transfer_package.metadata_path),
        "source_reference_run_dir": transfer_package.metadata.get("source_reference_run_dir"),
        "source_reference_model_name": transfer_package.metadata.get("source_reference_model_name"),
        "source_reference_tuning_preset": transfer_package.metadata.get("source_reference_tuning_preset"),
        "selected_feature_columns": transfer_package.selected_feature_columns,
        "feature_type_map": transfer_package.feature_type_map,
        "required_identifier_columns": REQUIRED_IDENTIFIER_COLUMNS,
        "available_optional_columns": [column for column in OPTIONAL_REPORTING_COLUMNS if column in input_df.columns],
        "row_count": int(len(prediction_df)),
        "predicted_hotspot_count": int(prediction_df["predicted_hotspot_10pct"].sum()),
        "predicted_hotspot_fraction": float(prediction_df["predicted_hotspot_10pct"].mean()),
        "figure_kind": figure_kind,
        "top_fraction": float(top_fraction),
        "output_files": {
            "predictions_parquet": str(paths.predictions_parquet_path),
            "predictions_csv": str(paths.predictions_csv_path),
            "prediction_summary_csv": str(paths.summary_csv_path),
            "prediction_deciles_csv": str(paths.deciles_csv_path),
            "feature_missingness_csv": str(paths.feature_missingness_path),
            "summary_markdown": str(paths.markdown_path),
            "figure": str(figure_path),
        },
    }
    paths.metadata_path.write_text(json.dumps(metadata_payload, indent=2), encoding="utf-8")
    paths.markdown_path.write_text(
        _build_markdown_summary(
            transfer_package=transfer_package,
            input_parquet_path=resolved_input_path,
            summary_df=summary_df,
            deciles_df=deciles_df,
            figure_path=figure_path,
            figure_kind=figure_kind,
            paths=paths,
        ),
        encoding="utf-8",
    )
    LOGGER.info("Wrote transfer inference artifacts under %s", paths.output_dir)
    return TransferInferenceResult(
        inference_id=resolved_inference_id,
        output_dir=paths.output_dir,
        figures_dir=paths.figures_dir,
        predictions_parquet_path=paths.predictions_parquet_path,
        predictions_csv_path=paths.predictions_csv_path,
        summary_csv_path=paths.summary_csv_path,
        deciles_csv_path=paths.deciles_csv_path,
        feature_missingness_path=paths.feature_missingness_path,
        markdown_path=paths.markdown_path,
        metadata_path=paths.metadata_path,
        figure_path=figure_path,
    )
