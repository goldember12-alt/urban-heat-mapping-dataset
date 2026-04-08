from __future__ import annotations

import csv
import json
import logging
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

LOGGER = logging.getLogger(__name__)

PROGRESS_FILENAME = "progress.json"
PROGRESS_LOG_FILENAME = "progress_log.csv"
FOLD_STATUS_FILENAME = "fold_status.json"
FOLD_ARTIFACTS_DIRNAME = "fold_artifacts"
SAMPLED_DIAGNOSTICS_FILENAME = "sample_diagnostics_by_city.csv"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _normalize_json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_json_value(item) for item in value]
    if isinstance(value, tuple):
        return [_normalize_json_value(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def atomic_write_json(output_path: Path, payload: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(_normalize_json_value(payload), indent=2)
    temp_path = output_path.with_name(f"{output_path.name}.{os.getpid()}.tmp")
    temp_path.write_text(serialized, encoding="utf-8")
    try:
        temp_path.replace(output_path)
    except PermissionError:
        output_path.write_text(serialized, encoding="utf-8")
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass


class _LockFile:
    def __init__(self, lock_path: Path, timeout_seconds: float = 30.0, stale_seconds: float = 300.0) -> None:
        self.lock_path = lock_path
        self.timeout_seconds = float(timeout_seconds)
        self.stale_seconds = float(stale_seconds)
        self._fd: int | None = None

    def __enter__(self) -> "_LockFile":
        deadline = time.time() + self.timeout_seconds
        while True:
            try:
                self.lock_path.parent.mkdir(parents=True, exist_ok=True)
                self._fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                return self
            except FileExistsError:
                try:
                    age_seconds = time.time() - self.lock_path.stat().st_mtime
                except FileNotFoundError:
                    continue
                if age_seconds > self.stale_seconds:
                    try:
                        self.lock_path.unlink()
                    except FileNotFoundError:
                        pass
                    continue
                if time.time() >= deadline:
                    raise TimeoutError(f"Timed out waiting for progress lock: {self.lock_path}")
                time.sleep(0.05)

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        try:
            self.lock_path.unlink()
        except FileNotFoundError:
            pass


class ProgressScorer:
    """Wrap an sklearn scorer and persist fit-level progress after each CV score."""

    def __init__(
        self,
        *,
        base_scorer: Any,
        tracker: "ModelRunProgressTracker",
        outer_fold: int,
        effective_inner_cv_splits: int,
        param_names: Sequence[str],
    ) -> None:
        self.base_scorer = base_scorer
        self.tracker = tracker
        self.outer_fold = int(outer_fold)
        self.effective_inner_cv_splits = int(effective_inner_cv_splits)
        self.param_names = list(param_names)

    def __call__(self, estimator, X, y) -> float:
        score = float(self.base_scorer(estimator, X, y))
        params = _extract_current_params(estimator=estimator, param_names=self.param_names)
        self.tracker.record_completed_fit(
            outer_fold=self.outer_fold,
            effective_inner_cv_splits=self.effective_inner_cv_splits,
            current_params=params,
        )
        return score


def _extract_current_params(estimator: Any, param_names: Sequence[str]) -> dict[str, Any] | None:
    try:
        all_params = estimator.get_params(deep=True)
    except Exception:
        return None
    filtered = {param_name: all_params.get(param_name) for param_name in param_names if param_name in all_params}
    return filtered or None


class ModelRunProgressTracker:
    def __init__(
        self,
        *,
        output_dir: Path,
        run_id: str,
        model_family: str,
        tuning_preset: str,
        selected_outer_folds: Sequence[int],
        candidate_count: int,
        inner_cv_splits_requested: int,
        estimated_total_inner_fits: int,
        dataset_path: Path,
        folds_path: Path | None,
        feature_columns: Sequence[str],
        sample_rows_per_city: int | None,
        random_state: int,
    ) -> None:
        self.output_dir = output_dir
        self.run_id = str(run_id)
        self.model_family = model_family
        self.tuning_preset = tuning_preset
        self.selected_outer_folds = [int(value) for value in selected_outer_folds]
        self.candidate_count = int(candidate_count)
        self.inner_cv_splits_requested = int(inner_cv_splits_requested)
        self.estimated_total_inner_fits = int(estimated_total_inner_fits)
        self.dataset_path = str(dataset_path)
        self.folds_path = None if folds_path is None else str(folds_path)
        self.feature_columns = list(feature_columns)
        self.sample_rows_per_city = sample_rows_per_city
        self.random_state = int(random_state)
        self.run_start_unix = time.time()
        self.run_started_at_utc = _utc_now_iso()
        self.progress_path = self.output_dir / PROGRESS_FILENAME
        self.progress_log_path = self.output_dir / PROGRESS_LOG_FILENAME
        self.fold_status_path = self.output_dir / FOLD_STATUS_FILENAME
        self.lock_path = self.output_dir / ".progress.lock"

    @property
    def fold_artifacts_root(self) -> Path:
        return self.output_dir / FOLD_ARTIFACTS_DIRNAME

    @property
    def sampled_diagnostics_path(self) -> Path:
        return self.output_dir / SAMPLED_DIAGNOSTICS_FILENAME

    def fold_artifact_dir(self, outer_fold: int) -> Path:
        return self.fold_artifacts_root / f"outer_fold_{int(outer_fold):02d}"

    def initialize(self) -> set[int]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with self._locked_state() as state:
            existing_status = state["fold_status"]
            completed_folds = self._safe_completed_folds(existing_status)
            fold_entries = existing_status.get("folds", {}) if existing_status else {}
            for outer_fold in self.selected_outer_folds:
                fold_entries.setdefault(str(int(outer_fold)), {"status": "pending"})
            fold_status = {
                "run_id": self.run_id,
                "output_dir": str(self.output_dir),
                "model_family": self.model_family,
                "tuning_preset": self.tuning_preset,
                "selected_outer_folds": list(self.selected_outer_folds),
                "dataset_path": self.dataset_path,
                "folds_path": self.folds_path,
                "feature_columns": list(self.feature_columns),
                "sample_rows_per_city": self.sample_rows_per_city,
                "random_state": self.random_state,
                "candidate_count": self.candidate_count,
                "inner_cv_splits_requested": self.inner_cv_splits_requested,
                "estimated_total_inner_fits": self.estimated_total_inner_fits,
                "run_started_at_utc": existing_status.get("run_started_at_utc", self.run_started_at_utc)
                if existing_status
                else self.run_started_at_utc,
                "last_updated_utc": _utc_now_iso(),
                "completed_outer_folds": sorted(completed_folds),
                "remaining_outer_folds": [fold for fold in self.selected_outer_folds if fold not in completed_folds],
                "folds": fold_entries,
                "last_error": existing_status.get("last_error") if existing_status else None,
            }
            self._validate_resume_contract(fold_status=fold_status)
            progress = self._build_progress_payload(
                phase="startup",
                outer_fold=None,
                fold_status=fold_status,
                current_params=None,
                note="run_initialized",
            )
            state["fold_status"] = fold_status
            state["progress"] = progress
            self._write_locked_state(state["progress"], state["fold_status"], append_log=True, note="startup")
        return completed_folds

    def mark_phase(
        self,
        *,
        phase: str,
        outer_fold: int | None = None,
        effective_inner_cv_splits: int | None = None,
        current_params: dict[str, Any] | None = None,
        note: str | None = None,
    ) -> None:
        with self._locked_state() as state:
            fold_status = state["fold_status"]
            if outer_fold is not None:
                fold_entry = fold_status.setdefault("folds", {}).setdefault(str(int(outer_fold)), {"status": "pending"})
                if effective_inner_cv_splits is not None:
                    fold_entry["effective_inner_cv_splits"] = int(effective_inner_cv_splits)
            progress = self._build_progress_payload(
                phase=phase,
                outer_fold=outer_fold,
                fold_status=fold_status,
                current_params=current_params,
                note=note,
            )
            state["fold_status"] = self._refresh_fold_status_summary(fold_status)
            state["progress"] = progress
            self._write_locked_state(state["progress"], state["fold_status"], append_log=True, note=note)

    def mark_fold_started(
        self,
        *,
        outer_fold: int,
        effective_inner_cv_splits: int,
        estimated_inner_fit_count: int,
        train_row_count: int,
        test_row_count: int,
        train_city_count: int,
        test_city_count: int,
    ) -> None:
        with self._locked_state() as state:
            fold_status = state["fold_status"]
            fold_entry = fold_status.setdefault("folds", {}).setdefault(str(int(outer_fold)), {})
            fold_entry.update(
                {
                    "status": "running",
                    "started_at_utc": fold_entry.get("started_at_utc", _utc_now_iso()),
                    "last_updated_utc": _utc_now_iso(),
                    "effective_inner_cv_splits": int(effective_inner_cv_splits),
                    "estimated_inner_fit_count": int(estimated_inner_fit_count),
                    "completed_inner_fits": int(fold_entry.get("completed_inner_fits", 0)),
                    "train_row_count": int(train_row_count),
                    "test_row_count": int(test_row_count),
                    "train_city_count": int(train_city_count),
                    "test_city_count": int(test_city_count),
                }
            )
            fold_status["last_error"] = None
            fold_status = self._refresh_fold_status_summary(fold_status)
            progress = self._build_progress_payload(
                phase="data_load",
                outer_fold=outer_fold,
                fold_status=fold_status,
                current_params=None,
                note="outer_fold_started",
            )
            state["fold_status"] = fold_status
            state["progress"] = progress
            self._write_locked_state(state["progress"], state["fold_status"], append_log=True, note="outer_fold_started")

    def record_completed_fit(
        self,
        *,
        outer_fold: int,
        effective_inner_cv_splits: int,
        current_params: dict[str, Any] | None,
    ) -> None:
        with self._locked_state() as state:
            fold_status = state["fold_status"]
            fold_entry = fold_status.setdefault("folds", {}).setdefault(str(int(outer_fold)), {"status": "running"})
            completed_inner_fits = int(fold_entry.get("completed_inner_fits", 0)) + 1
            fold_entry["completed_inner_fits"] = completed_inner_fits
            fold_entry["effective_inner_cv_splits"] = int(effective_inner_cv_splits)
            fold_entry["last_updated_utc"] = _utc_now_iso()
            fold_status = self._refresh_fold_status_summary(fold_status)
            progress = self._build_progress_payload(
                phase="tuning",
                outer_fold=outer_fold,
                fold_status=fold_status,
                current_params=current_params,
                note="inner_fit_completed",
            )
            state["fold_status"] = fold_status
            state["progress"] = progress
            self._write_locked_state(state["progress"], state["fold_status"], append_log=True, note="inner_fit_completed")

    def mark_fold_complete(
        self,
        *,
        outer_fold: int,
        effective_inner_cv_splits: int,
        artifact_paths: dict[str, Path],
        best_score: float,
        fold_wall_clock_seconds: float,
    ) -> None:
        with self._locked_state() as state:
            fold_status = state["fold_status"]
            fold_entry = fold_status.setdefault("folds", {}).setdefault(str(int(outer_fold)), {})
            fold_entry.update(
                {
                    "status": "completed",
                    "last_updated_utc": _utc_now_iso(),
                    "completed_at_utc": _utc_now_iso(),
                    "effective_inner_cv_splits": int(effective_inner_cv_splits),
                    "estimated_inner_fit_count": int(
                        fold_entry.get("estimated_inner_fit_count", self.candidate_count * effective_inner_cv_splits)
                    ),
                    "completed_inner_fits": int(
                        fold_entry.get("estimated_inner_fit_count", self.candidate_count * effective_inner_cv_splits)
                    ),
                    "best_inner_cv_average_precision": float(best_score),
                    "fold_wall_clock_seconds": float(fold_wall_clock_seconds),
                    "artifact_paths": {name: str(path) for name, path in artifact_paths.items()},
                }
            )
            fold_status = self._refresh_fold_status_summary(fold_status)
            progress = self._build_progress_payload(
                phase="metrics",
                outer_fold=outer_fold,
                fold_status=fold_status,
                current_params=None,
                note="outer_fold_completed",
            )
            state["fold_status"] = fold_status
            state["progress"] = progress
            self._write_locked_state(state["progress"], state["fold_status"], append_log=True, note="outer_fold_completed")

    def mark_failed(self, *, phase: str, error: Exception, outer_fold: int | None = None) -> None:
        with self._locked_state() as state:
            fold_status = state["fold_status"]
            fold_status["last_error"] = {
                "phase": phase,
                "outer_fold": outer_fold,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "timestamp_utc": _utc_now_iso(),
            }
            if outer_fold is not None:
                fold_entry = fold_status.setdefault("folds", {}).setdefault(str(int(outer_fold)), {})
                if fold_entry.get("status") != "completed":
                    fold_entry["status"] = "failed"
                    fold_entry["last_updated_utc"] = _utc_now_iso()
            fold_status = self._refresh_fold_status_summary(fold_status)
            progress = self._build_progress_payload(
                phase="failed",
                outer_fold=outer_fold,
                fold_status=fold_status,
                current_params=None,
                note=str(error),
            )
            progress["error_type"] = type(error).__name__
            progress["error_message"] = str(error)
            state["fold_status"] = fold_status
            state["progress"] = progress
            self._write_locked_state(state["progress"], state["fold_status"], append_log=True, note="failed")

    def mark_complete(self) -> None:
        with self._locked_state() as state:
            fold_status = self._refresh_fold_status_summary(state["fold_status"])
            progress = self._build_progress_payload(
                phase="complete",
                outer_fold=None,
                fold_status=fold_status,
                current_params=None,
                note="run_complete",
            )
            state["fold_status"] = fold_status
            state["progress"] = progress
            self._write_locked_state(state["progress"], state["fold_status"], append_log=True, note="complete")

    def write_sample_diagnostics(self, diagnostics_df) -> None:
        diagnostics_df.to_csv(self.sampled_diagnostics_path, index=False)

    def _validate_resume_contract(self, *, fold_status: dict[str, Any]) -> None:
        existing_completed = fold_status.get("completed_outer_folds", [])
        if not existing_completed:
            return
        mismatches: list[str] = []
        if fold_status.get("model_family") != self.model_family:
            mismatches.append("model_family")
        if fold_status.get("tuning_preset") != self.tuning_preset:
            mismatches.append("tuning_preset")
        if fold_status.get("dataset_path") != self.dataset_path:
            mismatches.append("dataset_path")
        if fold_status.get("folds_path") != self.folds_path:
            mismatches.append("folds_path")
        if list(fold_status.get("feature_columns", [])) != self.feature_columns:
            mismatches.append("feature_columns")
        if fold_status.get("sample_rows_per_city") != self.sample_rows_per_city:
            mismatches.append("sample_rows_per_city")
        if int(fold_status.get("candidate_count", self.candidate_count)) != self.candidate_count:
            mismatches.append("candidate_count")
        if int(fold_status.get("inner_cv_splits_requested", self.inner_cv_splits_requested)) != self.inner_cv_splits_requested:
            mismatches.append("inner_cv_splits_requested")
        if mismatches:
            mismatch_text = ", ".join(sorted(mismatches))
            raise ValueError(
                f"Existing completed fold artifacts under {self.output_dir} do not match the requested run contract: {mismatch_text}"
            )

    def _safe_completed_folds(self, fold_status: dict[str, Any] | None) -> set[int]:
        if not fold_status:
            return set()
        completed: set[int] = set()
        for raw_fold, fold_entry in fold_status.get("folds", {}).items():
            outer_fold = int(raw_fold)
            if fold_entry.get("status") != "completed":
                continue
            artifact_paths = fold_entry.get("artifact_paths", {})
            required_names = {
                "predictions",
                "fold_metrics",
                "best_params",
                "calibration_curve",
                "runtime",
            }
            if required_names.issubset(artifact_paths) and all(Path(artifact_paths[name]).exists() for name in required_names):
                completed.add(outer_fold)
        return completed

    def _build_progress_payload(
        self,
        *,
        phase: str,
        outer_fold: int | None,
        fold_status: dict[str, Any],
        current_params: dict[str, Any] | None,
        note: str | None,
    ) -> dict[str, Any]:
        completed_outer_folds = [int(value) for value in fold_status.get("completed_outer_folds", [])]
        current_fold_key = None if outer_fold is None else str(int(outer_fold))
        current_fold_state = {} if current_fold_key is None else fold_status.get("folds", {}).get(current_fold_key, {})
        completed_inner_fits = sum(
            int(fold_entry.get("completed_inner_fits", 0))
            for fold_entry in fold_status.get("folds", {}).values()
            if int(fold_entry.get("completed_inner_fits", 0)) > 0
        )
        elapsed_wall_time_seconds = max(0.0, time.time() - self.run_start_unix)
        average_seconds_per_completed_fit = (
            elapsed_wall_time_seconds / completed_inner_fits if completed_inner_fits > 0 else None
        )
        remaining_inner_fits = max(0, int(self.estimated_total_inner_fits) - int(completed_inner_fits))
        eta_seconds = (
            remaining_inner_fits * average_seconds_per_completed_fit
            if average_seconds_per_completed_fit is not None
            else None
        )
        current_effective_splits = current_fold_state.get("effective_inner_cv_splits")
        completed_candidates = len(completed_outer_folds) * self.candidate_count
        if current_fold_state.get("status") == "running" and current_effective_splits:
            completed_candidates += int(current_fold_state.get("completed_inner_fits", 0)) // int(current_effective_splits)
        progress = {
            "run_id": self.run_id,
            "output_dir": str(self.output_dir),
            "model_family": self.model_family,
            "tuning_preset": self.tuning_preset,
            "phase": phase,
            "outer_fold_index": outer_fold,
            "selected_outer_folds": list(self.selected_outer_folds),
            "candidate_count": self.candidate_count,
            "inner_cv_split_count_requested": self.inner_cv_splits_requested,
            "current_inner_cv_split_count": current_effective_splits,
            "estimated_total_inner_fits": self.estimated_total_inner_fits,
            "completed_inner_fits": int(completed_inner_fits),
            "completed_candidates": int(completed_candidates),
            "elapsed_wall_time_seconds": float(elapsed_wall_time_seconds),
            "average_seconds_per_completed_fit": average_seconds_per_completed_fit,
            "eta_seconds": eta_seconds,
            "current_params": current_params,
            "completed_outer_folds": completed_outer_folds,
            "remaining_outer_folds": [fold for fold in self.selected_outer_folds if fold not in completed_outer_folds],
            "current_outer_fold_completed_inner_fits": int(current_fold_state.get("completed_inner_fits", 0)),
            "current_outer_fold_estimated_inner_fits": current_fold_state.get("estimated_inner_fit_count"),
            "last_updated_utc": _utc_now_iso(),
            "note": note,
            "sample_rows_per_city": self.sample_rows_per_city,
        }
        return progress

    def _refresh_fold_status_summary(self, fold_status: dict[str, Any]) -> dict[str, Any]:
        completed = sorted(self._safe_completed_folds(fold_status))
        fold_status["completed_outer_folds"] = completed
        fold_status["remaining_outer_folds"] = [fold for fold in self.selected_outer_folds if fold not in completed]
        fold_status["last_updated_utc"] = _utc_now_iso()
        return fold_status

    def _write_locked_state(
        self,
        progress: dict[str, Any],
        fold_status: dict[str, Any],
        *,
        append_log: bool,
        note: str | None,
    ) -> None:
        atomic_write_json(self.progress_path, progress)
        atomic_write_json(self.fold_status_path, fold_status)
        if append_log:
            self._append_progress_log(progress=progress, note=note)

    def _append_progress_log(self, *, progress: dict[str, Any], note: str | None) -> None:
        row = {
            "timestamp_utc": progress.get("last_updated_utc"),
            "phase": progress.get("phase"),
            "outer_fold_index": progress.get("outer_fold_index"),
            "completed_inner_fits": progress.get("completed_inner_fits"),
            "completed_candidates": progress.get("completed_candidates"),
            "estimated_total_inner_fits": progress.get("estimated_total_inner_fits"),
            "current_inner_cv_split_count": progress.get("current_inner_cv_split_count"),
            "elapsed_wall_time_seconds": progress.get("elapsed_wall_time_seconds"),
            "average_seconds_per_completed_fit": progress.get("average_seconds_per_completed_fit"),
            "eta_seconds": progress.get("eta_seconds"),
            "current_params_json": json.dumps(_normalize_json_value(progress.get("current_params")), sort_keys=True)
            if progress.get("current_params") is not None
            else "",
            "note": note or "",
        }
        self.progress_log_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(row)
        file_exists = self.progress_log_path.exists()
        with self.progress_log_path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

    @contextmanager
    def _locked_state(self):
        with _LockFile(self.lock_path):
            progress = json.loads(self.progress_path.read_text(encoding="utf-8")) if self.progress_path.exists() else {}
            fold_status = (
                json.loads(self.fold_status_path.read_text(encoding="utf-8"))
                if self.fold_status_path.exists()
                else {}
            )
            yield {"progress": progress, "fold_status": fold_status}
