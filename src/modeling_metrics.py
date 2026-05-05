from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import average_precision_score

from src.modeling_config import DEFAULT_CALIBRATION_BINS, DEFAULT_TOP_FRACTION, TARGET_COLUMN


def safe_average_precision(y_true: Sequence[int], y_score: Sequence[float]) -> float:
    """Return average precision, or NaN when the target has fewer than two classes."""
    y_true_array = np.asarray(y_true, dtype=np.int8)
    y_score_array = np.asarray(y_score, dtype=np.float64)
    if y_true_array.size == 0 or np.unique(y_true_array).size < 2:
        return float("nan")
    return float(average_precision_score(y_true_array, y_score_array))


def recall_at_top_fraction(
    y_true: Sequence[int],
    y_score: Sequence[float],
    fraction: float = DEFAULT_TOP_FRACTION,
) -> float:
    """Return recall among the highest-scoring fraction of rows."""
    y_true_array = np.asarray(y_true, dtype=np.int8)
    y_score_array = np.asarray(y_score, dtype=np.float64)
    if y_true_array.size == 0:
        return float("nan")

    positive_count = int(y_true_array.sum())
    if positive_count == 0:
        return float("nan")

    top_n = max(1, int(np.ceil(len(y_true_array) * float(fraction))))
    order = np.argsort(-y_score_array, kind="mergesort")
    return float(y_true_array[order][:top_n].sum() / positive_count)


def compute_prediction_metrics(
    y_true: Sequence[int],
    y_score: Sequence[float],
    top_fraction: float = DEFAULT_TOP_FRACTION,
) -> dict[str, float]:
    """Compute the core held-out classification metrics."""
    y_true_array = np.asarray(y_true, dtype=np.int8)
    prevalence = float(y_true_array.mean()) if y_true_array.size else float("nan")
    return {
        "row_count": int(y_true_array.size),
        "positive_count": int(y_true_array.sum()),
        "prevalence": prevalence,
        "pr_auc": safe_average_precision(y_true_array, y_score),
        "recall_at_top_10pct": recall_at_top_fraction(y_true_array, y_score, fraction=top_fraction),
    }


def summarize_predictions_by_group(
    predictions_df: pd.DataFrame,
    group_columns: Iterable[str],
    top_fraction: float = DEFAULT_TOP_FRACTION,
) -> pd.DataFrame:
    """Compute prediction metrics for each requested group."""
    rows: list[dict[str, object]] = []
    group_columns = list(group_columns)
    for group_keys, group_df in predictions_df.groupby(group_columns, sort=True, dropna=False):
        if not isinstance(group_keys, tuple):
            group_keys = (group_keys,)
        row = dict(zip(group_columns, group_keys, strict=True))
        row.update(
            compute_prediction_metrics(
                y_true=group_df[TARGET_COLUMN].to_numpy(dtype=np.int8),
                y_score=group_df["predicted_probability"].to_numpy(dtype=np.float64),
                top_fraction=top_fraction,
            )
        )
        rows.append(row)
    return pd.DataFrame(rows)


def build_metrics_summary(
    predictions_df: pd.DataFrame,
    fold_metrics_df: pd.DataFrame,
    city_metrics_df: pd.DataFrame,
    model_name: str,
    top_fraction: float = DEFAULT_TOP_FRACTION,
) -> pd.DataFrame:
    """Build one concise summary row for a model run."""
    pooled_metrics = compute_prediction_metrics(
        y_true=predictions_df[TARGET_COLUMN].to_numpy(dtype=np.int8),
        y_score=predictions_df["predicted_probability"].to_numpy(dtype=np.float64),
        top_fraction=top_fraction,
    )
    return pd.DataFrame(
        [
            {
                "model_name": model_name,
                "outer_fold_count": int(fold_metrics_df["outer_fold"].nunique()),
                "heldout_city_count": int(city_metrics_df["city_id"].nunique()) if not city_metrics_df.empty else 0,
                "heldout_row_count": int(pooled_metrics["row_count"]),
                "heldout_positive_count": int(pooled_metrics["positive_count"]),
                "heldout_prevalence": float(pooled_metrics["prevalence"]),
                "pooled_pr_auc": float(pooled_metrics["pr_auc"]),
                "mean_fold_pr_auc": float(fold_metrics_df["pr_auc"].mean()) if not fold_metrics_df.empty else float("nan"),
                "mean_city_pr_auc": float(city_metrics_df["pr_auc"].mean()) if not city_metrics_df.empty else float("nan"),
                "pooled_recall_at_top_10pct": float(pooled_metrics["recall_at_top_10pct"]),
                "mean_fold_recall_at_top_10pct": (
                    float(fold_metrics_df["recall_at_top_10pct"].mean()) if not fold_metrics_df.empty else float("nan")
                ),
            }
        ]
    )


def build_calibration_curve_table(
    predictions_df: pd.DataFrame,
    model_name: str,
    scope_name: str,
    scope_value: str,
    n_bins: int = DEFAULT_CALIBRATION_BINS,
) -> pd.DataFrame:
    """Return calibration-curve points for one prediction set."""
    y_true = predictions_df[TARGET_COLUMN].to_numpy(dtype=np.int8)
    y_score = predictions_df["predicted_probability"].to_numpy(dtype=np.float64)
    if y_true.size == 0 or np.unique(y_true).size < 2:
        return pd.DataFrame(
            columns=[
                "model_name",
                "scope_name",
                "scope_value",
                "bin_index",
                "predicted_probability_mean",
                "observed_positive_rate",
            ]
        )

    observed, predicted = calibration_curve(y_true, y_score, n_bins=n_bins, strategy="quantile")
    return pd.DataFrame(
        {
            "model_name": model_name,
            "scope_name": scope_name,
            "scope_value": scope_value,
            "bin_index": list(range(len(predicted))),
            "predicted_probability_mean": predicted,
            "observed_positive_rate": observed,
        }
    )
