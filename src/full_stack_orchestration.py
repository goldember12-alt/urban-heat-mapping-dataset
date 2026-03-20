from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.appeears_acquisition import load_appeears_status_records, run_appeears_acquisition
from src.config import CITY_FEATURES, INTERMEDIATE, ORCHESTRATION_STATUS
from src.feature_assembly import (
    CELL_FILTER_STUDY_AREA,
    assemble_city_features,
    expected_city_feature_output_paths,
)
from src.load_cities import load_cities
from src.raw_data_acquisition import run_raw_data_acquisition
from src.stage_status import (
    STATUS_BLOCKED_MISSING_CREDENTIALS,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_NOT_STARTED,
    STATUS_SKIPPED_EXISTING,
    is_success_status,
)
from src.support_layers import audit_support_layer_readiness, prepare_support_layers

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FullStackOrchestrationResult:
    summary: pd.DataFrame
    summary_json_path: Path
    summary_csv_path: Path


def _summary_paths(orchestration_dir: Path = ORCHESTRATION_STATUS) -> tuple[Path, Path]:
    return (
        orchestration_dir / "full_stack_city_orchestration_summary.json",
        orchestration_dir / "full_stack_city_orchestration_summary.csv",
    )


def _write_summary_outputs(
    records: list[dict[str, Any]],
    payload: dict[str, Any],
    summary_json_path: Path,
    summary_csv_path: Path,
) -> pd.DataFrame:
    summary = pd.DataFrame(records)
    summary_json_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_json_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    summary.to_csv(summary_csv_path, index=False)
    return summary


def _empty_stage_result(message: str = "") -> dict[str, Any]:
    return {"status": STATUS_NOT_STARTED, "error": "", "failure_reason": "", "recoverable": False, "message": message}


def _failed_stage_result(
    error: str,
    message: str = "",
    *,
    failure_reason: str = "",
    recoverable: bool = False,
) -> dict[str, Any]:
    return {
        "status": STATUS_FAILED,
        "error": error,
        "failure_reason": failure_reason,
        "recoverable": recoverable,
        "message": message or error,
    }


def _normalize_stage_status(
    status: str | None,
    *,
    error: str = "",
    failure_reason: str = "",
    recoverable: bool = False,
    message: str = "",
) -> dict[str, Any]:
    normalized = (status or "").strip().lower()
    if normalized in {STATUS_COMPLETED, STATUS_SKIPPED_EXISTING, STATUS_BLOCKED_MISSING_CREDENTIALS, STATUS_FAILED}:
        return {
            "status": normalized,
            "error": error,
            "failure_reason": failure_reason,
            "recoverable": recoverable,
            "message": message,
        }
    if normalized in {"submitted", "pending", STATUS_NOT_STARTED, ""}:
        final_message = message or "stage incomplete; rerun to continue"
        return {
            "status": STATUS_NOT_STARTED,
            "error": error,
            "failure_reason": failure_reason,
            "recoverable": recoverable,
            "message": final_message,
        }
    if normalized == "blocked":
        final_message = message or error or "stage blocked by missing prerequisites"
        return {
            "status": STATUS_FAILED,
            "error": error or "stage_blocked",
            "failure_reason": failure_reason or "stage_blocked",
            "recoverable": recoverable,
            "message": final_message,
        }
    final_message = message or error or f"unrecognized stage status: {normalized}"
    return {
        "status": STATUS_FAILED,
        "error": error or f"unexpected_status:{normalized}",
        "failure_reason": failure_reason or f"unexpected_status:{normalized}",
        "recoverable": recoverable,
        "message": final_message,
    }


def _aggregate_raw_stage(summary: pd.DataFrame, city_id: int) -> dict[str, Any]:
    rows = summary.loc[summary["city_id"] == city_id].copy() if not summary.empty else pd.DataFrame()
    if rows.empty:
        return _empty_stage_result("raw support acquisition did not run for this city")

    dataset_parts = [f"{row['dataset']}={row['status']}" for _, row in rows.iterrows()]
    errors = [str(value).strip() for value in rows.get("error", pd.Series(dtype=str)).fillna("") if str(value).strip()]
    failure_reasons = [
        str(value).strip()
        for value in rows.get("failure_reason", pd.Series(dtype=str)).fillna("")
        if str(value).strip()
    ]
    recoverable = bool(rows.get("recoverable", pd.Series(dtype=bool)).fillna(False).astype(bool).any())
    statuses = {str(value).strip().lower() for value in rows["status"].fillna("")}

    if STATUS_FAILED in statuses:
        return _failed_stage_result(
            "; ".join(errors) or "raw support acquisition failed",
            "; ".join(dataset_parts),
            failure_reason="; ".join(failure_reasons),
            recoverable=recoverable,
        )
    if "blocked" in statuses:
        return _failed_stage_result(
            "; ".join(errors) or "raw support acquisition blocked",
            "; ".join(dataset_parts),
            failure_reason="; ".join(failure_reasons) or "stage_blocked",
            recoverable=recoverable,
        )
    if statuses == {STATUS_SKIPPED_EXISTING}:
        return {
            "status": STATUS_SKIPPED_EXISTING,
            "error": "",
            "failure_reason": "",
            "recoverable": False,
            "message": "; ".join(dataset_parts),
        }
    if statuses.issubset({STATUS_COMPLETED, STATUS_SKIPPED_EXISTING}):
        final_status = STATUS_COMPLETED if STATUS_COMPLETED in statuses else STATUS_SKIPPED_EXISTING
        return {
            "status": final_status,
            "error": "",
            "failure_reason": "",
            "recoverable": False,
            "message": "; ".join(dataset_parts),
        }

    return _failed_stage_result(
        "raw_support_status_unrecognized",
        "; ".join(dataset_parts),
        failure_reason="raw_support_status_unrecognized",
        recoverable=recoverable,
    )


def _single_row_stage(summary: pd.DataFrame, city_id: int, default_message: str) -> dict[str, Any]:
    rows = summary.loc[summary["city_id"] == city_id].copy() if not summary.empty else pd.DataFrame()
    if rows.empty:
        return _empty_stage_result(default_message)

    row = rows.iloc[0]
    return _normalize_stage_status(
        str(row.get("status", "")),
        error=str(row.get("error", "") or ""),
        failure_reason=str(row.get("failure_reason", "") or ""),
        recoverable=bool(row.get("recoverable", False)),
        message=str(row.get("message", "") or ""),
    )


def _feature_stage_prerequisites(stage_results: dict[str, dict[str, str]]) -> list[str]:
    prerequisites = [
        ("raw_support_acquisition", "raw support acquisition"),
        ("support_layer_prep", "support-layer prep"),
        ("appeears_ndvi", "AppEEARS NDVI"),
        ("appeears_ecostress", "AppEEARS ECOSTRESS"),
    ]
    blocked = [
        label
        for key, label in prerequisites
        if not is_success_status(stage_results.get(key, {}).get("status"))
    ]
    return blocked


def _feature_stage_result(
    city: pd.Series,
    stage_results: dict[str, dict[str, str]],
    *,
    resolution: float,
    cell_filter_mode: str,
    max_cells: int | None,
    overwrite_features: bool,
    city_features_dir: Path,
    intermediate_dir: Path,
) -> dict[str, str]:
    blocked_prereqs = _feature_stage_prerequisites(stage_results)
    if blocked_prereqs:
        return _empty_stage_result(
            "waiting on prerequisites: " + "; ".join(blocked_prereqs)
        )

    output_paths = expected_city_feature_output_paths(
        city=city,
        city_features_dir=city_features_dir,
        intermediate_dir=intermediate_dir,
    )
    if (
        not overwrite_features
        and output_paths.city_features_gpkg_path.exists()
        and output_paths.city_features_parquet_path.exists()
    ):
        return {
            "status": STATUS_SKIPPED_EXISTING,
            "error": "",
            "failure_reason": "",
            "recoverable": False,
            "message": "existing city feature outputs retained",
        }

    try:
        result = assemble_city_features(
            city_id=int(city["city_id"]),
            resolution=resolution,
            cell_filter_mode=cell_filter_mode,
            save_outputs=True,
            max_cells=max_cells,
            city_features_dir=city_features_dir,
            intermediate_dir=intermediate_dir,
        )
    except Exception as exc:  # pragma: no cover - exercised in integration/manual runs
        logger.exception("Feature assembly failed for city_id=%s", int(city["city_id"]))
        return _failed_stage_result(str(exc), failure_reason="feature_assembly_error")

    if result.blocked_stages:
        blocked = ";".join(result.blocked_stages)
        return _failed_stage_result(
            f"feature_blocked_stages:{blocked}",
            f"feature assembly returned blocked stages: {blocked}",
            failure_reason="feature_blocked_stages",
        )

    return {
        "status": STATUS_COMPLETED,
        "error": "",
        "failure_reason": "",
        "recoverable": False,
        "message": f"rows={result.n_rows}",
    }


def _overall_status(stage_results: dict[str, dict[str, str]]) -> tuple[str, str]:
    ordered_keys = [
        "raw_support_acquisition",
        "support_layer_prep",
        "appeears_ndvi",
        "appeears_ecostress",
        "feature_assembly",
    ]
    ordered = [stage_results[key] for key in ordered_keys]

    if all(is_success_status(item["status"]) for item in ordered):
        return STATUS_COMPLETED, "all stages completed or reused existing outputs"
    if any(item["status"] == STATUS_BLOCKED_MISSING_CREDENTIALS for item in ordered):
        return STATUS_BLOCKED_MISSING_CREDENTIALS, "AppEEARS-dependent stages are blocked on missing credentials"
    if any(item["status"] == STATUS_FAILED for item in ordered):
        return STATUS_FAILED, "one or more stages failed"
    return STATUS_NOT_STARTED, "one or more stages remain incomplete"


def city_ids_missing_full_stack_outputs(
    *,
    resolution: float = 30,
    city_features_dir: Path = CITY_FEATURES,
    intermediate_dir: Path = INTERMEDIATE,
) -> list[int]:
    cities = load_cities()
    support_preflight = audit_support_layer_readiness(
        city_ids=None,
        resolution=resolution,
        write_outputs=False,
    )
    support_by_city = {
        int(row["city_id"]): row
        for row in support_preflight.summary.to_dict(orient="records")
    }
    ndvi_records = load_appeears_status_records("ndvi")
    ecostress_records = load_appeears_status_records("ecostress")

    selected: list[int] = []
    for _, city in cities.iterrows():
        city_id = int(city["city_id"])
        support = support_by_city.get(city_id, {})
        feature_paths = expected_city_feature_output_paths(
            city=city,
            city_features_dir=city_features_dir,
            intermediate_dir=intermediate_dir,
        )
        features_ready = (
            feature_paths.city_features_gpkg_path.exists()
            and feature_paths.city_features_parquet_path.exists()
        )
        raw_ready = bool(
            support.get("dem_source_available", False)
            and support.get("nlcd_land_cover_source_available", False)
            and support.get("nlcd_impervious_source_available", False)
            and support.get("hydro_source_available", False)
        )
        prepared_ready = bool(
            support.get("dem_prepared_exists", False)
            and support.get("nlcd_land_cover_prepared_exists", False)
            and support.get("nlcd_impervious_prepared_exists", False)
            and support.get("hydro_prepared_exists", False)
        )
        ndvi_ready = is_success_status(str(ndvi_records.get(city_id, {}).get("status", "")))
        ecostress_ready = is_success_status(str(ecostress_records.get(city_id, {}).get("status", "")))

        if not (raw_ready and prepared_ready and ndvi_ready and ecostress_ready and features_ready):
            selected.append(city_id)

    return selected


def run_full_stack_orchestration(
    start_date: str,
    end_date: str,
    city_ids: list[int] | None = None,
    all_missing: bool = False,
    resolution: float = 30,
    cell_filter_mode: str = CELL_FILTER_STUDY_AREA,
    force_raw: bool = False,
    overwrite_support: bool = False,
    overwrite_features: bool = False,
    max_cells: int | None = None,
    orchestration_dir: Path = ORCHESTRATION_STATUS,
    city_features_dir: Path = CITY_FEATURES,
    intermediate_dir: Path = INTERMEDIATE,
) -> FullStackOrchestrationResult:
    """Run raw acquisition, support prep, AppEEARS acquisition, and feature assembly per city."""
    if all_missing and city_ids:
        raise ValueError("--all-missing cannot be combined with explicit city_ids")
    if not start_date.strip() or not end_date.strip():
        raise ValueError("start_date and end_date are required")

    selected_city_ids = sorted(set(city_ids or []))
    selection_mode = "city_subset"
    if all_missing:
        selected_city_ids = city_ids_missing_full_stack_outputs(
            resolution=resolution,
            city_features_dir=city_features_dir,
            intermediate_dir=intermediate_dir,
        )
        selection_mode = "all_missing"
    elif not selected_city_ids:
        selected_city_ids = load_cities()["city_id"].astype(int).tolist()
        selection_mode = "all"

    cities = load_cities()
    cities = cities[cities["city_id"].isin(selected_city_ids)].copy()

    if cities.empty:
        summary_json_path, summary_csv_path = _summary_paths(orchestration_dir=orchestration_dir)
        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "selection_mode": selection_mode,
            "requested_city_ids": selected_city_ids,
            "records": [],
        }
        summary = _write_summary_outputs([], payload, summary_json_path, summary_csv_path)
        return FullStackOrchestrationResult(summary=summary, summary_json_path=summary_json_path, summary_csv_path=summary_csv_path)

    logger.info("Running full-stack stage: raw support acquisition")
    raw_result = run_raw_data_acquisition(
        dataset="all",
        city_ids=selected_city_ids,
        resolution=resolution,
        all_missing=False,
        force=force_raw,
    )

    logger.info("Running full-stack stage: support-layer prep")
    support_result = prepare_support_layers(
        city_ids=selected_city_ids,
        resolution=resolution,
        overwrite=overwrite_support,
    )

    logger.info("Running full-stack stage: AppEEARS NDVI")
    ndvi_result = run_appeears_acquisition(
        product_type="ndvi",
        city_ids=selected_city_ids,
        start_date=start_date,
        end_date=end_date,
        retry_incomplete=True,
    )

    logger.info("Running full-stack stage: AppEEARS ECOSTRESS")
    ecostress_result = run_appeears_acquisition(
        product_type="ecostress",
        city_ids=selected_city_ids,
        start_date=start_date,
        end_date=end_date,
        retry_incomplete=True,
    )

    records: list[dict[str, Any]] = []
    generated_at_utc = datetime.now(timezone.utc).isoformat()

    for _, city in cities.iterrows():
        city_id = int(city["city_id"])
        city_name = str(city["city_name"])
        stage_results = {
            "raw_support_acquisition": _aggregate_raw_stage(raw_result.summary, city_id=city_id),
            "support_layer_prep": _single_row_stage(
                support_result.summary,
                city_id=city_id,
                default_message="support-layer prep did not run for this city",
            ),
            "appeears_ndvi": _single_row_stage(
                ndvi_result.summary,
                city_id=city_id,
                default_message="NDVI acquisition did not run for this city",
            ),
            "appeears_ecostress": _single_row_stage(
                ecostress_result.summary,
                city_id=city_id,
                default_message="ECOSTRESS acquisition did not run for this city",
            ),
        }
        stage_results["feature_assembly"] = _feature_stage_result(
            city=city,
            stage_results=stage_results,
            resolution=resolution,
            cell_filter_mode=cell_filter_mode,
            max_cells=max_cells,
            overwrite_features=overwrite_features,
            city_features_dir=city_features_dir,
            intermediate_dir=intermediate_dir,
        )

        feature_paths = expected_city_feature_output_paths(
            city=city,
            city_features_dir=city_features_dir,
            intermediate_dir=intermediate_dir,
        )
        overall_status, overall_message = _overall_status(stage_results)

        record: dict[str, Any] = {
            "city_id": city_id,
            "city_name": city_name,
            "state": str(city["state"]),
            "selection_mode": selection_mode,
            "raw_support_acquisition_status": stage_results["raw_support_acquisition"]["status"],
            "raw_support_acquisition_error": stage_results["raw_support_acquisition"]["error"],
            "raw_support_acquisition_failure_reason": stage_results["raw_support_acquisition"]["failure_reason"],
            "raw_support_acquisition_recoverable": stage_results["raw_support_acquisition"]["recoverable"],
            "raw_support_acquisition_message": stage_results["raw_support_acquisition"]["message"],
            "support_layer_prep_status": stage_results["support_layer_prep"]["status"],
            "support_layer_prep_error": stage_results["support_layer_prep"]["error"],
            "support_layer_prep_failure_reason": stage_results["support_layer_prep"]["failure_reason"],
            "support_layer_prep_recoverable": stage_results["support_layer_prep"]["recoverable"],
            "support_layer_prep_message": stage_results["support_layer_prep"]["message"],
            "appeears_ndvi_status": stage_results["appeears_ndvi"]["status"],
            "appeears_ndvi_error": stage_results["appeears_ndvi"]["error"],
            "appeears_ndvi_failure_reason": stage_results["appeears_ndvi"]["failure_reason"],
            "appeears_ndvi_recoverable": stage_results["appeears_ndvi"]["recoverable"],
            "appeears_ndvi_message": stage_results["appeears_ndvi"]["message"],
            "appeears_ecostress_status": stage_results["appeears_ecostress"]["status"],
            "appeears_ecostress_error": stage_results["appeears_ecostress"]["error"],
            "appeears_ecostress_failure_reason": stage_results["appeears_ecostress"]["failure_reason"],
            "appeears_ecostress_recoverable": stage_results["appeears_ecostress"]["recoverable"],
            "appeears_ecostress_message": stage_results["appeears_ecostress"]["message"],
            "feature_assembly_status": stage_results["feature_assembly"]["status"],
            "feature_assembly_error": stage_results["feature_assembly"]["error"],
            "feature_assembly_failure_reason": stage_results["feature_assembly"]["failure_reason"],
            "feature_assembly_recoverable": stage_results["feature_assembly"]["recoverable"],
            "feature_assembly_message": stage_results["feature_assembly"]["message"],
            "city_features_gpkg_path": str(feature_paths.city_features_gpkg_path),
            "city_features_parquet_path": str(feature_paths.city_features_parquet_path),
            "overall_status": overall_status,
            "overall_message": overall_message,
            "updated_at_utc": generated_at_utc,
        }
        records.append(record)

    summary_json_path, summary_csv_path = _summary_paths(orchestration_dir=orchestration_dir)
    payload = {
        "generated_at_utc": generated_at_utc,
        "selection_mode": selection_mode,
        "requested_city_ids": selected_city_ids,
        "records": records,
        "stage_outputs": {
            "raw_support_acquisition_summary_json": str(raw_result.summary_json_path),
            "raw_support_acquisition_summary_csv": str(raw_result.summary_csv_path),
            "support_layer_prep_summary_json": str(support_result.summary_json_path),
            "support_layer_prep_summary_csv": str(support_result.summary_csv_path),
            "appeears_ndvi_summary_json": str(ndvi_result.summary_json_path),
            "appeears_ndvi_summary_csv": str(ndvi_result.summary_csv_path),
            "appeears_ecostress_summary_json": str(ecostress_result.summary_json_path),
            "appeears_ecostress_summary_csv": str(ecostress_result.summary_csv_path),
        },
    }
    summary = _write_summary_outputs(
        records=records,
        payload=payload,
        summary_json_path=summary_json_path,
        summary_csv_path=summary_csv_path,
    )
    return FullStackOrchestrationResult(
        summary=summary,
        summary_json_path=summary_json_path,
        summary_csv_path=summary_csv_path,
    )
