from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq

from src.config import PROJECT_ROOT

RUN_REGISTRY_FILENAME = "run_registry.jsonl"


def create_run_id() -> str:
    """Return a stable unique identifier for one modeling run."""
    return uuid.uuid4().hex


def build_cli_command(argv: list[str] | None = None) -> str:
    """Return a shell-ready command string for registry logging."""
    effective_argv = argv or getattr(sys, "orig_argv", None) or [sys.executable, *sys.argv]
    return subprocess.list2cmdline([str(part) for part in effective_argv])


def infer_run_registry_path(output_dir: Path) -> Path:
    """Infer the shared modeling run-registry path from one run output directory."""
    resolved_output_dir = output_dir.resolve()
    if resolved_output_dir.name == "modeling":
        return resolved_output_dir / RUN_REGISTRY_FILENAME

    for parent in resolved_output_dir.parents:
        if parent.name == "modeling":
            return parent / RUN_REGISTRY_FILENAME

    return resolved_output_dir.parent / RUN_REGISTRY_FILENAME


def get_dataset_format(dataset_path: Path) -> str:
    """Return the normalized file format label for a dataset path."""
    return dataset_path.suffix.lower().lstrip(".") or "unknown"


def get_dataset_row_count_if_known(dataset_path: Path) -> int | None:
    """Return the dataset row count when it is inexpensive to determine."""
    if not dataset_path.exists():
        return None
    if dataset_path.suffix.lower() != ".parquet":
        return None
    return int(pq.ParquetFile(dataset_path).metadata.num_rows)


def get_git_commit_if_available() -> str | None:
    """Return the current git commit hash when available."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    commit = result.stdout.strip()
    return commit or None


def summarize_metrics_for_registry(summary_df: pd.DataFrame) -> dict[str, Any] | list[dict[str, Any]] | None:
    """Convert a metrics summary dataframe into a JSON-ready payload."""
    if summary_df.empty:
        return None
    records = [_normalize_json_value(record) for record in summary_df.to_dict(orient="records")]
    if len(records) == 1:
        return records[0]
    return records


def append_run_registry_record(registry_path: Path, record: dict[str, Any]) -> None:
    """Append one JSONL record to the modeling run registry."""
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with registry_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_normalize_json_value(record), ensure_ascii=True))
        handle.write("\n")


def record_model_run(
    *,
    model_type: str,
    preset: str | None,
    command: str | None,
    output_dir: Path,
    dataset_path: Path,
    folds_path: Path | None,
    sample_rows_per_city: int | None,
    selected_outer_folds: list[int] | None,
    grid_search_n_jobs: int | None = None,
    model_n_jobs: int | None = None,
    summary_metrics_path: Path | None = None,
    metadata_path: Path | None = None,
    status: str,
    notes: list[str] | None = None,
    error: Exception | None = None,
) -> Path:
    """Append one modeling run record from a CLI boundary."""
    registry_path = infer_run_registry_path(output_dir)
    metadata_payload: dict[str, Any] = {}
    if metadata_path is not None and metadata_path.exists():
        metadata_payload = json.loads(metadata_path.read_text(encoding="utf-8"))

    resolved_dataset_path = Path(metadata_payload.get("dataset_path", dataset_path))
    resolved_output_dir = Path(metadata_payload.get("output_dir", output_dir))
    resolved_folds_path = metadata_payload.get("folds_path")
    metrics = None
    if summary_metrics_path is not None and summary_metrics_path.exists():
        metrics = summarize_metrics_for_registry(pd.read_csv(summary_metrics_path))

    record: dict[str, Any] = {
        "run_id": metadata_payload.get("run_id", create_run_id()),
        "timestamp_utc": pd.Timestamp.now("UTC").isoformat(),
        "status": status,
        "model_type": model_type,
        "preset": preset,
        "command": command,
        "interpreter_path": sys.executable,
        "dataset_path": resolved_dataset_path,
        "dataset_format": get_dataset_format(resolved_dataset_path),
        "dataset_row_count": get_dataset_row_count_if_known(resolved_dataset_path),
        "folds_path": resolved_folds_path if resolved_folds_path is not None else folds_path,
        "outer_folds_used": metadata_payload.get("selected_outer_folds", selected_outer_folds),
        "sample_rows_per_city": metadata_payload.get("sample_rows_per_city", sample_rows_per_city),
        "grid_search_n_jobs": metadata_payload.get("grid_search_n_jobs", grid_search_n_jobs),
        "model_n_jobs": metadata_payload.get("model_n_jobs", model_n_jobs),
        "output_dir": resolved_output_dir,
        "metrics": metrics,
        "wall_clock_seconds": metadata_payload.get("timing_seconds", {}).get("total_wall_clock"),
        "git_commit": get_git_commit_if_available(),
        "notes": notes,
        "metadata_path": metadata_path,
    }
    if error is not None:
        record["error_type"] = type(error).__name__
        record["error_message"] = str(error)
    append_run_registry_record(registry_path, record)
    from src.modeling_tuning_history import refresh_tuning_history_artifacts

    refresh_tuning_history_artifacts(registry_path)
    return registry_path


def _normalize_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _normalize_json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_json_value(item) for item in value]
    if isinstance(value, tuple):
        return [_normalize_json_value(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if value is pd.NA:
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    if pd.isna(value):
        return None
    return value
