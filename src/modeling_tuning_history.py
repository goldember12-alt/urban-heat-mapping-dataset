from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

TUNING_HISTORY_FILENAME = "tuning_history.csv"
TUNING_HISTORY_ANNOTATIONS_FILENAME = "tuning_history_annotations.csv"

MANUAL_ANNOTATION_COLUMNS = [
    "manual_history_status_label",
    "manual_decision_note",
    "manual_comparability_note",
    "manual_supersedes_run_id",
    "manual_paper_include",
]


def infer_tuning_history_path(registry_path: Path) -> Path:
    """Return the canonical machine-readable tuning-history table path."""
    return registry_path.with_name(TUNING_HISTORY_FILENAME)


def infer_tuning_history_annotations_path(registry_path: Path) -> Path:
    """Return the durable manual-annotation sidecar path for tuning history."""
    return registry_path.with_name(TUNING_HISTORY_ANNOTATIONS_FILENAME)


def refresh_tuning_history_artifacts(registry_path: Path) -> tuple[Path, Path]:
    """Rebuild the tuning-history CSV and annotation template from the run registry."""
    resolved_registry_path = registry_path.resolve()
    history_path = infer_tuning_history_path(resolved_registry_path)
    annotations_path = infer_tuning_history_annotations_path(resolved_registry_path)

    records = _load_registry_records(resolved_registry_path)
    history_df = _build_tuning_history_dataframe(records)
    annotations_df = _sync_annotation_template(history_df, annotations_path)
    merged_df = _merge_annotations(history_df, annotations_df)

    history_path.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(history_path, index=False)
    return history_path, annotations_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rebuild the cross-run modeling tuning-history table from outputs/modeling/run_registry.jsonl.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--registry-path",
        type=Path,
        default=Path("outputs") / "modeling" / "run_registry.jsonl",
        help="Path to the shared modeling run registry JSONL file.",
    )
    args = parser.parse_args()

    history_path, annotations_path = refresh_tuning_history_artifacts(args.registry_path)
    print(history_path)
    print(annotations_path)


def _load_registry_records(registry_path: Path) -> list[dict[str, Any]]:
    if not registry_path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in registry_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        records.append(json.loads(stripped))
    return records


def _build_tuning_history_dataframe(records: list[dict[str, Any]]) -> pd.DataFrame:
    rows = [_build_tuning_history_row(record) for record in records]
    if not rows:
        return pd.DataFrame(columns=_history_output_columns())

    history_df = pd.DataFrame(rows)
    history_df["timestamp_utc"] = pd.to_datetime(history_df["timestamp_utc"], utc=True, errors="coerce")
    history_df = history_df.sort_values(["timestamp_utc", "run_id"], kind="stable").reset_index(drop=True)
    history_df["run_order"] = history_df.index + 1
    history_df["run_date"] = history_df["timestamp_utc"].dt.strftime("%Y-%m-%d")
    history_df["timestamp_utc"] = history_df["timestamp_utc"].dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    history_df["timestamp_utc"] = history_df["timestamp_utc"].str.replace(r"(\+0000)$", "+00:00", regex=True)

    history_df = _add_frontier_fields(history_df)
    history_df = _add_previous_run_comparability_fields(history_df)
    return history_df.reindex(columns=_history_output_columns())


def _build_tuning_history_row(record: dict[str, Any]) -> dict[str, Any]:
    metadata_payload = _load_metadata_payload(record.get("metadata_path"))
    metrics_payload = record.get("metrics") if isinstance(record.get("metrics"), dict) else {}

    selected_features = metadata_payload.get("selected_feature_columns", [])
    selected_outer_folds = _normalize_int_list(
        metadata_payload.get("selected_outer_folds", record.get("outer_folds_used"))
    )
    param_grid = metadata_payload.get("param_grid")
    if not isinstance(param_grid, list):
        param_grid = []

    search_contract_version, search_contract_descriptor = _describe_search_contract(
        model_type=str(record.get("model_type") or ""),
        preset=_coerce_string(record.get("preset")),
        inner_cv_splits=_coerce_int(metadata_payload.get("inner_cv_splits_requested")),
        param_candidate_count=_coerce_int(metadata_payload.get("search_space", {}).get("param_candidate_count")),
        param_grid=param_grid,
    )
    search_contract_signature = _make_signature(
        {
            "model_type": record.get("model_type"),
            "preset": record.get("preset"),
            "selected_feature_columns": selected_features,
            "inner_cv_splits_requested": metadata_payload.get("inner_cv_splits_requested"),
            "param_grid": param_grid,
        }
    )
    comparison_signature = _make_signature(
        {
            "model_type": record.get("model_type"),
            "search_contract_signature": search_contract_signature,
            "dataset_path": record.get("dataset_path"),
            "dataset_format": record.get("dataset_format"),
            "selected_outer_folds": selected_outer_folds,
            "sample_rows_per_city": metadata_payload.get("sample_rows_per_city", record.get("sample_rows_per_city")),
        }
    )

    return {
        "run_id": _coerce_string(record.get("run_id")),
        "timestamp_utc": record.get("timestamp_utc"),
        "run_date": None,
        "run_order": None,
        "model_type": _coerce_string(record.get("model_type")),
        "preset": _coerce_string(record.get("preset")),
        "run_status": _coerce_string(record.get("status")),
        "output_dir": _coerce_string(record.get("output_dir")),
        "output_dir_name": Path(str(record.get("output_dir") or "")).name if record.get("output_dir") else None,
        "git_commit": _coerce_string(record.get("git_commit")),
        "dataset_path": _coerce_string(record.get("dataset_path")),
        "dataset_format": _coerce_string(record.get("dataset_format")),
        "dataset_row_count": _coerce_int(record.get("dataset_row_count")),
        "folds_path": _coerce_string(record.get("folds_path")),
        "outer_folds_used": _format_int_list(selected_outer_folds),
        "outer_fold_count": len(selected_outer_folds),
        "sample_rows_per_city": _coerce_int(
            metadata_payload.get("sample_rows_per_city", record.get("sample_rows_per_city"))
        ),
        "grid_search_n_jobs": _coerce_int(metadata_payload.get("grid_search_n_jobs", record.get("grid_search_n_jobs"))),
        "model_n_jobs": _coerce_int(metadata_payload.get("model_n_jobs", record.get("model_n_jobs"))),
        "selected_feature_columns": json.dumps(selected_features, sort_keys=True),
        "feature_contract_signature": _make_signature(selected_features),
        "inner_cv_splits_requested": _coerce_int(metadata_payload.get("inner_cv_splits_requested")),
        "param_candidate_count": _coerce_int(metadata_payload.get("search_space", {}).get("param_candidate_count")),
        "estimated_total_inner_fits": _coerce_int(
            metadata_payload.get("search_space", {}).get("estimated_total_inner_fits")
        ),
        "search_contract_version": search_contract_version,
        "search_contract_descriptor": search_contract_descriptor,
        "search_contract_signature": search_contract_signature,
        "comparison_signature": comparison_signature,
        "comparison_descriptor": _build_comparison_descriptor(
            search_contract_version=search_contract_version,
            selected_outer_folds=selected_outer_folds,
            sample_rows_per_city=_coerce_int(
                metadata_payload.get("sample_rows_per_city", record.get("sample_rows_per_city"))
            ),
            dataset_format=_coerce_string(record.get("dataset_format")),
        ),
        "pooled_pr_auc": _coerce_float(metrics_payload.get("pooled_pr_auc")),
        "mean_fold_pr_auc": _coerce_float(metrics_payload.get("mean_fold_pr_auc")),
        "mean_city_pr_auc": _coerce_float(metrics_payload.get("mean_city_pr_auc")),
        "pooled_recall_at_top_10pct": _coerce_float(metrics_payload.get("pooled_recall_at_top_10pct")),
        "mean_fold_recall_at_top_10pct": _coerce_float(metrics_payload.get("mean_fold_recall_at_top_10pct")),
        "wall_clock_seconds": _coerce_float(record.get("wall_clock_seconds")),
        "registry_notes": _format_notes(record.get("notes")),
        "metadata_path": _coerce_string(record.get("metadata_path")),
        "error_type": _coerce_string(record.get("error_type")),
        "error_message": _coerce_string(record.get("error_message")),
        "auto_history_status_label": "failed" if str(record.get("status") or "").lower() != "success" else "unreviewed",
        "manual_history_status_label": None,
        "history_status_label": None,
        "auto_comparability_note": None,
        "manual_decision_note": None,
        "decision_note": None,
        "manual_comparability_note": None,
        "comparability_note": None,
        "manual_supersedes_run_id": None,
        "manual_paper_include": None,
        "prior_best_pooled_pr_auc_same_comparison": None,
        "delta_pooled_pr_auc_vs_prior_best_same_comparison": None,
        "moved_frontier_same_comparison": None,
        "contract_changed_vs_previous_same_model": None,
        "comparison_changed_vs_previous_same_model": None,
        "previous_same_model_run_id": None,
    }


def _build_comparison_descriptor(
    *,
    search_contract_version: str,
    selected_outer_folds: list[int],
    sample_rows_per_city: int | None,
    dataset_format: str | None,
) -> str:
    folds_text = "all_folds" if not selected_outer_folds else "folds_" + "-".join(str(value) for value in selected_outer_folds)
    sample_text = "all_rows" if sample_rows_per_city is None else f"sample_{sample_rows_per_city}_per_city"
    format_text = dataset_format or "unknown"
    return f"{search_contract_version}; {folds_text}; {sample_text}; dataset={format_text}"


def _describe_search_contract(
    *,
    model_type: str,
    preset: str | None,
    inner_cv_splits: int | None,
    param_candidate_count: int | None,
    param_grid: list[dict[str, Any]],
) -> tuple[str, str]:
    if model_type == "logistic_saga":
        logistic_contract_slug, logistic_contract_text = _describe_logistic_contract(param_grid)
        version = f"{model_type}__{preset or 'custom'}__{logistic_contract_slug}__cv{inner_cv_splits or 'na'}__pc{param_candidate_count or 'na'}"
        descriptor = (
            f"logistic_saga preset={preset or 'custom'}; {logistic_contract_text}; "
            f"inner_cv={inner_cv_splits or 'na'}; candidates={param_candidate_count or 'na'}"
        )
        return version, descriptor

    version = f"{model_type}__{preset or 'custom'}__generic_grid__cv{inner_cv_splits or 'na'}__pc{param_candidate_count or 'na'}"
    descriptor = (
        f"{model_type} preset={preset or 'custom'}; generic param grid; "
        f"inner_cv={inner_cv_splits or 'na'}; candidates={param_candidate_count or 'na'}"
    )
    return version, descriptor


def _describe_logistic_contract(param_grid: list[dict[str, Any]]) -> tuple[str, str]:
    if any("model__penalty" in candidate for candidate in param_grid):
        return "explicit_penalty_grid", "explicit penalty grid"

    l1_ratios: set[float] = set()
    for candidate in param_grid:
        raw_values = candidate.get("model__l1_ratio", [])
        if isinstance(raw_values, list):
            for value in raw_values:
                if value is not None:
                    l1_ratios.add(float(value))
    has_l2 = 0.0 in l1_ratios
    has_l1 = 1.0 in l1_ratios
    has_elasticnet = any(0.0 < value < 1.0 for value in l1_ratios)

    if has_l2 and has_l1 and has_elasticnet:
        return "l1_ratio_family_complete", "l1_ratio family-complete grid"
    if has_l2 and has_elasticnet and not has_l1:
        return "l1_ratio_missing_l1", "l1_ratio grid missing pure l1 branch"
    if has_l2 and has_l1 and not has_elasticnet:
        return "l1_ratio_l1_l2_only", "l1_ratio l1/l2-only grid"
    if has_elasticnet and not (has_l2 or has_l1):
        return "elasticnet_only", "elastic-net-only grid"
    return "custom_l1_ratio_grid", "custom l1_ratio grid"


def _add_frontier_fields(history_df: pd.DataFrame) -> pd.DataFrame:
    prior_best_values: list[float | None] = []
    delta_values: list[float | None] = []
    moved_values: list[bool | None] = []
    best_by_group: dict[str, float] = {}

    for row in history_df.itertuples(index=False):
        comparison_signature = str(row.comparison_signature)
        prior_best = best_by_group.get(comparison_signature)
        pooled_pr_auc = row.pooled_pr_auc
        run_status = str(row.run_status or "")

        prior_best_values.append(prior_best)
        if prior_best is None or pooled_pr_auc is None:
            delta_values.append(None)
        else:
            delta_values.append(float(pooled_pr_auc) - float(prior_best))

        if run_status != "success" or pooled_pr_auc is None:
            moved_values.append(None)
            continue

        if prior_best is None or float(pooled_pr_auc) > float(prior_best):
            moved_values.append(True)
            best_by_group[comparison_signature] = float(pooled_pr_auc)
        else:
            moved_values.append(False)

    history_df["prior_best_pooled_pr_auc_same_comparison"] = prior_best_values
    history_df["delta_pooled_pr_auc_vs_prior_best_same_comparison"] = delta_values
    history_df["moved_frontier_same_comparison"] = moved_values
    return history_df


def _add_previous_run_comparability_fields(history_df: pd.DataFrame) -> pd.DataFrame:
    previous_same_model: dict[str, dict[str, Any]] = {}
    previous_run_ids: list[str | None] = []
    contract_changed: list[bool | None] = []
    comparison_changed: list[bool | None] = []
    auto_notes: list[str] = []

    for row in history_df.itertuples(index=False):
        model_type = str(row.model_type or "")
        previous_row = previous_same_model.get(model_type)
        previous_run_ids.append(None if previous_row is None else previous_row["run_id"])
        if previous_row is None:
            contract_changed.append(None)
            comparison_changed.append(None)
            auto_notes.append("First recorded run for this model family in the registry.")
        else:
            contract_changed_flag = str(row.search_contract_signature) != str(previous_row["search_contract_signature"])
            comparison_changed_flag = str(row.comparison_signature) != str(previous_row["comparison_signature"])
            contract_changed.append(contract_changed_flag)
            comparison_changed.append(comparison_changed_flag)
            if contract_changed_flag:
                auto_notes.append("Search contract changed relative to the previous recorded run for this model family.")
            elif comparison_changed_flag:
                auto_notes.append("Evaluation slice changed relative to the previous recorded run for this model family.")
            else:
                auto_notes.append("Directly comparable to the previous recorded run for this model family.")
        previous_same_model[model_type] = {
            "run_id": row.run_id,
            "search_contract_signature": row.search_contract_signature,
            "comparison_signature": row.comparison_signature,
        }

    history_df["previous_same_model_run_id"] = previous_run_ids
    history_df["contract_changed_vs_previous_same_model"] = contract_changed
    history_df["comparison_changed_vs_previous_same_model"] = comparison_changed
    history_df["auto_comparability_note"] = auto_notes
    return history_df


def _sync_annotation_template(history_df: pd.DataFrame, annotations_path: Path) -> pd.DataFrame:
    context_columns = [
        "run_id",
        "timestamp_utc",
        "model_type",
        "preset",
        "run_status",
        "output_dir_name",
        "search_contract_version",
        "comparison_signature",
    ]
    context_df = history_df[context_columns].copy()

    if annotations_path.exists():
        annotations_df = pd.read_csv(annotations_path, dtype="string").fillna("")
    else:
        annotations_df = pd.DataFrame(columns=context_columns + MANUAL_ANNOTATION_COLUMNS)

    for column_name in MANUAL_ANNOTATION_COLUMNS:
        if column_name not in annotations_df.columns:
            annotations_df[column_name] = ""

    if "run_id" not in annotations_df.columns:
        annotations_df["run_id"] = ""

    manual_df = annotations_df[["run_id", *MANUAL_ANNOTATION_COLUMNS]].copy()
    merged = context_df.merge(manual_df, on="run_id", how="left")
    for column_name in MANUAL_ANNOTATION_COLUMNS:
        merged[column_name] = merged[column_name].fillna("")

    annotations_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(annotations_path, index=False)
    return merged


def _merge_annotations(history_df: pd.DataFrame, annotations_df: pd.DataFrame) -> pd.DataFrame:
    manual_df = annotations_df[["run_id", *MANUAL_ANNOTATION_COLUMNS]].copy()
    merged = history_df.merge(manual_df, on="run_id", how="left", suffixes=("", "_annotation"))

    for column_name in MANUAL_ANNOTATION_COLUMNS:
        annotation_column = f"{column_name}_annotation"
        if annotation_column in merged.columns:
            merged[column_name] = merged[annotation_column].where(
                merged[annotation_column].notna() & merged[annotation_column].ne(""),
                merged[column_name],
            )
            merged = merged.drop(columns=annotation_column)

    merged["history_status_label"] = merged["manual_history_status_label"].where(
        merged["manual_history_status_label"].notna() & merged["manual_history_status_label"].ne(""),
        merged["auto_history_status_label"],
    )
    merged["decision_note"] = merged["manual_decision_note"]
    merged["comparability_note"] = merged["manual_comparability_note"].where(
        merged["manual_comparability_note"].notna() & merged["manual_comparability_note"].ne(""),
        merged["auto_comparability_note"],
    )
    return merged


def _load_metadata_payload(metadata_path: Any) -> dict[str, Any]:
    if metadata_path is None:
        return {}
    path = Path(str(metadata_path))
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _history_output_columns() -> list[str]:
    return [
        "run_id",
        "timestamp_utc",
        "run_date",
        "run_order",
        "model_type",
        "preset",
        "run_status",
        "output_dir",
        "output_dir_name",
        "git_commit",
        "dataset_path",
        "dataset_format",
        "dataset_row_count",
        "folds_path",
        "outer_folds_used",
        "outer_fold_count",
        "sample_rows_per_city",
        "grid_search_n_jobs",
        "model_n_jobs",
        "selected_feature_columns",
        "feature_contract_signature",
        "inner_cv_splits_requested",
        "param_candidate_count",
        "estimated_total_inner_fits",
        "search_contract_version",
        "search_contract_descriptor",
        "search_contract_signature",
        "comparison_signature",
        "comparison_descriptor",
        "pooled_pr_auc",
        "mean_fold_pr_auc",
        "mean_city_pr_auc",
        "pooled_recall_at_top_10pct",
        "mean_fold_recall_at_top_10pct",
        "wall_clock_seconds",
        "prior_best_pooled_pr_auc_same_comparison",
        "delta_pooled_pr_auc_vs_prior_best_same_comparison",
        "moved_frontier_same_comparison",
        "previous_same_model_run_id",
        "contract_changed_vs_previous_same_model",
        "comparison_changed_vs_previous_same_model",
        "registry_notes",
        "metadata_path",
        "error_type",
        "error_message",
        "auto_history_status_label",
        "manual_history_status_label",
        "history_status_label",
        "auto_comparability_note",
        "manual_comparability_note",
        "comparability_note",
        "manual_decision_note",
        "decision_note",
        "manual_supersedes_run_id",
        "manual_paper_include",
    ]


def _normalize_int_list(values: Any) -> list[int]:
    if values is None:
        return []
    if isinstance(values, list):
        return [int(value) for value in values]
    if isinstance(values, str):
        stripped = values.strip()
        if not stripped:
            return []
        return [int(part.strip()) for part in stripped.split(",") if part.strip()]
    return [int(values)]


def _format_int_list(values: list[int]) -> str:
    if not values:
        return ""
    return ",".join(str(value) for value in values)


def _format_notes(notes: Any) -> str | None:
    if notes is None:
        return None
    if isinstance(notes, list):
        return " | ".join(str(note) for note in notes if str(note).strip())
    text = str(notes).strip()
    return text or None


def _make_signature(payload: Any) -> str:
    normalized_text = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha1(normalized_text.encode("utf-8")).hexdigest()[:12]


def _coerce_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    main()
