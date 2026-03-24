from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

from src.modeling_config import (
    BASELINE_OUTPUT_DIR,
    CITY_NAME_COLUMN,
    DEFAULT_FINAL_DATASET_PATH,
    DEFAULT_RANDOM_STATE,
    DEFAULT_TOP_FRACTION,
    GROUP_COLUMN,
    TARGET_COLUMN,
    get_prediction_output_columns,
)
from src.modeling_data import (
    get_requested_outer_folds,
    load_city_outer_folds,
    load_outer_fold_data,
    write_feature_contract,
)
from src.modeling_metrics import (
    build_calibration_curve_table,
    build_metrics_summary,
    compute_prediction_metrics,
    summarize_predictions_by_group,
)

MISSING_CATEGORY_TOKEN = "__MISSING__"


@dataclass(frozen=True)
class BaselineRunResult:
    fold_metrics_path: Path
    city_metrics_path: Path
    summary_metrics_path: Path
    predictions_path: Path
    calibration_curve_path: Path
    metadata_path: Path


class GlobalMeanBaseline:
    """Predict the train-fold hotspot prevalence for every held-out row."""

    def __init__(self) -> None:
        self.probability_: float = 0.0

    def fit(self, train_df: pd.DataFrame) -> "GlobalMeanBaseline":
        self.probability_ = float(train_df[TARGET_COLUMN].mean())
        return self

    def predict_proba(self, test_df: pd.DataFrame) -> np.ndarray:
        return np.full(len(test_df), self.probability_, dtype=np.float64)


class MeanByCategoryBaseline:
    """Predict train-fold target prevalence by a single categorical feature."""

    def __init__(self, column_name: str) -> None:
        self.column_name = column_name
        self.global_probability_: float = 0.0
        self.lookup_: dict[str, float] = {}

    def fit(self, train_df: pd.DataFrame) -> "MeanByCategoryBaseline":
        series = train_df[self.column_name].astype("string").fillna(MISSING_CATEGORY_TOKEN).str.strip()
        series = series.where(series.ne(""), MISSING_CATEGORY_TOKEN)
        grouped = pd.DataFrame({self.column_name: series, TARGET_COLUMN: train_df[TARGET_COLUMN]})
        self.global_probability_ = float(grouped[TARGET_COLUMN].mean())
        self.lookup_ = grouped.groupby(self.column_name, dropna=False)[TARGET_COLUMN].mean().astype(float).to_dict()
        return self

    def predict_proba(self, test_df: pd.DataFrame) -> np.ndarray:
        series = test_df[self.column_name].astype("string").fillna(MISSING_CATEGORY_TOKEN).str.strip()
        series = series.where(series.ne(""), MISSING_CATEGORY_TOKEN)
        probabilities = series.map(self.lookup_).fillna(self.global_probability_)
        return probabilities.to_numpy(dtype=np.float64)


class ImperviousQuantileBaseline:
    """Predict train-fold target prevalence by imperviousness quantile bin."""

    def __init__(self, column_name: str = "impervious_pct", n_bins: int = 10) -> None:
        self.column_name = column_name
        self.n_bins = n_bins
        self.global_probability_: float = 0.0
        self.bin_edges_: np.ndarray | None = None
        self.lookup_: dict[int, float] = {}

    def fit(self, train_df: pd.DataFrame) -> "ImperviousQuantileBaseline":
        values = pd.to_numeric(train_df[self.column_name], errors="coerce")
        self.global_probability_ = float(train_df[TARGET_COLUMN].mean())
        valid_values = values.dropna()
        if valid_values.empty:
            self.bin_edges_ = None
            self.lookup_ = {}
            return self

        quantiles = np.linspace(0.0, 1.0, self.n_bins + 1)
        bin_edges = np.unique(np.quantile(valid_values.to_numpy(dtype=np.float64), quantiles))
        if len(bin_edges) < 2:
            self.bin_edges_ = None
            self.lookup_ = {}
            return self

        adjusted_edges = bin_edges.astype(np.float64).copy()
        adjusted_edges[0] = adjusted_edges[0] - 1e-9
        adjusted_edges[-1] = adjusted_edges[-1] + 1e-9
        bins = pd.cut(values, bins=adjusted_edges, labels=False, include_lowest=True)
        grouped = pd.DataFrame({"bin_id": bins, TARGET_COLUMN: train_df[TARGET_COLUMN]})
        self.bin_edges_ = adjusted_edges
        self.lookup_ = grouped.groupby("bin_id", dropna=True)[TARGET_COLUMN].mean().astype(float).to_dict()
        return self

    def predict_proba(self, test_df: pd.DataFrame) -> np.ndarray:
        if self.bin_edges_ is None:
            return np.full(len(test_df), self.global_probability_, dtype=np.float64)

        values = pd.to_numeric(test_df[self.column_name], errors="coerce")
        bins = pd.cut(values, bins=self.bin_edges_, labels=False, include_lowest=True)
        probabilities = bins.map(self.lookup_).fillna(self.global_probability_)
        return probabilities.to_numpy(dtype=np.float64)


def _build_prediction_frame(
    test_df: pd.DataFrame,
    model_name: str,
    outer_fold: int,
    probabilities: np.ndarray,
) -> pd.DataFrame:
    prediction_columns = get_prediction_output_columns()
    predictions = test_df[prediction_columns + [TARGET_COLUMN]].copy()
    predictions["outer_fold"] = int(outer_fold)
    predictions["model_name"] = model_name
    predictions["predicted_probability"] = probabilities.astype(np.float64)
    return predictions


def run_modeling_baselines(
    dataset_path: Path = DEFAULT_FINAL_DATASET_PATH,
    folds_path: Path | None = None,
    output_dir: Path = BASELINE_OUTPUT_DIR,
    sample_rows_per_city: int | None = None,
    selected_outer_folds: Sequence[int] | None = None,
    random_state: int = DEFAULT_RANDOM_STATE,
    top_fraction: float = DEFAULT_TOP_FRACTION,
    impervious_n_bins: int = 10,
) -> BaselineRunResult:
    """Run the first-pass held-out-city baseline models."""
    fold_table = load_city_outer_folds(folds_path=folds_path)
    requested_folds = get_requested_outer_folds(fold_table=fold_table, selected_outer_folds=selected_outer_folds)

    model_builders = {
        "global_mean_baseline": lambda: GlobalMeanBaseline(),
        "land_cover_only_baseline": lambda: MeanByCategoryBaseline("land_cover_class"),
        "impervious_only_baseline": lambda: ImperviousQuantileBaseline(n_bins=impervious_n_bins),
        "climate_only_baseline": lambda: MeanByCategoryBaseline("climate_group"),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_feature_contract(output_dir / "feature_contract.json", feature_columns=[])

    all_predictions: list[pd.DataFrame] = []
    fold_metrics_rows: list[dict[str, object]] = []
    calibration_frames: list[pd.DataFrame] = []

    for outer_fold in requested_folds:
        fold_data = load_outer_fold_data(
            outer_fold=outer_fold,
            dataset_path=dataset_path,
            folds_path=folds_path,
            feature_columns=["impervious_pct", "land_cover_class", "climate_group"],
            sample_rows_per_city=sample_rows_per_city,
            random_state=random_state,
        )
        train_df = fold_data.train_df
        test_df = fold_data.test_df

        for model_name, builder in model_builders.items():
            model = builder().fit(train_df)
            probabilities = model.predict_proba(test_df)
            prediction_df = _build_prediction_frame(
                test_df=test_df,
                model_name=model_name,
                outer_fold=outer_fold,
                probabilities=probabilities,
            )
            all_predictions.append(prediction_df)

            metrics = compute_prediction_metrics(
                y_true=prediction_df[TARGET_COLUMN].to_numpy(dtype=np.int8),
                y_score=prediction_df["predicted_probability"].to_numpy(dtype=np.float64),
                top_fraction=top_fraction,
            )
            fold_metrics_rows.append(
                {
                    "model_name": model_name,
                    "outer_fold": int(outer_fold),
                    "train_city_count": int(len(fold_data.train_city_ids)),
                    "test_city_count": int(len(fold_data.test_city_ids)),
                    "train_row_count": int(len(train_df)),
                    "test_row_count": int(metrics["row_count"]),
                    "test_positive_count": int(metrics["positive_count"]),
                    "test_prevalence": float(metrics["prevalence"]),
                    "pr_auc": float(metrics["pr_auc"]),
                    "recall_at_top_10pct": float(metrics["recall_at_top_10pct"]),
                }
            )
            calibration_frames.append(
                build_calibration_curve_table(
                    predictions_df=prediction_df,
                    model_name=model_name,
                    scope_name="outer_fold",
                    scope_value=str(outer_fold),
                )
            )

    predictions_df = pd.concat(all_predictions, ignore_index=True).sort_values(
        ["model_name", "outer_fold", GROUP_COLUMN, "cell_id"]
    )
    fold_metrics_df = pd.DataFrame(fold_metrics_rows).sort_values(["model_name", "outer_fold"]).reset_index(drop=True)
    city_metrics_df = summarize_predictions_by_group(
        predictions_df=predictions_df,
        group_columns=["model_name", "outer_fold", GROUP_COLUMN, CITY_NAME_COLUMN, "climate_group"],
        top_fraction=top_fraction,
    ).sort_values(["model_name", "outer_fold", GROUP_COLUMN]).reset_index(drop=True)

    summary_parts = []
    for model_name, model_predictions in predictions_df.groupby("model_name", sort=True):
        model_fold_metrics = fold_metrics_df.loc[fold_metrics_df["model_name"] == model_name].copy()
        model_city_metrics = city_metrics_df.loc[city_metrics_df["model_name"] == model_name].copy()
        summary_parts.append(
            build_metrics_summary(
                predictions_df=model_predictions,
                fold_metrics_df=model_fold_metrics,
                city_metrics_df=model_city_metrics,
                model_name=model_name,
                top_fraction=top_fraction,
            )
        )
        calibration_frames.append(
            build_calibration_curve_table(
                predictions_df=model_predictions,
                model_name=model_name,
                scope_name="overall",
                scope_value="overall",
            )
        )
    summary_df = pd.concat(summary_parts, ignore_index=True).sort_values("model_name").reset_index(drop=True)
    calibration_df = pd.concat(calibration_frames, ignore_index=True) if calibration_frames else pd.DataFrame()

    predictions_path = output_dir / "heldout_predictions.parquet"
    fold_metrics_path = output_dir / "metrics_by_fold.csv"
    city_metrics_path = output_dir / "metrics_by_city.csv"
    summary_metrics_path = output_dir / "metrics_summary.csv"
    calibration_curve_path = output_dir / "calibration_curve.csv"
    metadata_path = output_dir / "run_metadata.json"

    predictions_df.to_parquet(predictions_path, index=False)
    fold_metrics_df.to_csv(fold_metrics_path, index=False)
    city_metrics_df.to_csv(city_metrics_path, index=False)
    summary_df.to_csv(summary_metrics_path, index=False)
    calibration_df.to_csv(calibration_curve_path, index=False)

    metadata = {
        "dataset_path": str(dataset_path),
        "folds_path": str(folds_path) if folds_path is not None else None,
        "output_dir": str(output_dir),
        "selected_outer_folds": requested_folds,
        "sample_rows_per_city": sample_rows_per_city,
        "top_fraction": top_fraction,
        "baselines": {
            "global_mean_baseline": "Predicts the training-city hotspot prevalence for every held-out row.",
            "land_cover_only_baseline": "Predicts held-out probabilities from training-city land-cover prevalence.",
            "impervious_only_baseline": "Predicts held-out probabilities from training-city impervious quantile prevalence.",
            "climate_only_baseline": "Predicts held-out probabilities from training-city climate-group prevalence.",
        },
        "output_files": {
            "predictions": str(predictions_path),
            "metrics_by_fold": str(fold_metrics_path),
            "metrics_by_city": str(city_metrics_path),
            "metrics_summary": str(summary_metrics_path),
            "calibration_curve": str(calibration_curve_path),
        },
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return BaselineRunResult(
        fold_metrics_path=fold_metrics_path,
        city_metrics_path=city_metrics_path,
        summary_metrics_path=summary_metrics_path,
        predictions_path=predictions_path,
        calibration_curve_path=calibration_curve_path,
        metadata_path=metadata_path,
    )
