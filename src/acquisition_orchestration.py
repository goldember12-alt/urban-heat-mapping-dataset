from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.appeears_acquisition import AcquisitionRunResult, run_appeears_acquisition
from src.config import ORCHESTRATION_STATUS
from src.raw_data_acquisition import RawAcquisitionResult, run_raw_data_acquisition
from src.support_layers import (
    SupportLayerPreflightResult,
    SupportLayerPrepResult,
    audit_support_layer_readiness,
    prepare_support_layers,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AcquisitionOrchestrationResult:
    summary: pd.DataFrame
    summary_json_path: Path
    summary_csv_path: Path


def _summary_paths(orchestration_dir: Path = ORCHESTRATION_STATUS) -> tuple[Path, Path]:
    return (
        orchestration_dir / "acquisition_orchestration_summary.json",
        orchestration_dir / "acquisition_orchestration_summary.csv",
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


def _status_counts(summary: pd.DataFrame, status_column: str = "status") -> dict[str, int]:
    if summary.empty or status_column not in summary.columns:
        return {}
    counts = summary[status_column].fillna("").astype(str).value_counts().sort_index()
    return {str(key): int(value) for key, value in counts.items() if str(key)}


def _effective_city_ids(summary: pd.DataFrame) -> list[int]:
    if summary.empty or "city_id" not in summary.columns:
        return []
    values = pd.to_numeric(summary["city_id"], errors="coerce").dropna().astype(int).tolist()
    return sorted(set(values))


def _city_ids_missing_prepared_support(preflight: SupportLayerPreflightResult) -> list[int]:
    summary = preflight.summary
    if summary.empty:
        return []

    prepared_missing = ~(
        summary["dem_prepared_exists"].astype(bool)
        & summary["nlcd_land_cover_prepared_exists"].astype(bool)
        & summary["nlcd_impervious_prepared_exists"].astype(bool)
        & summary["hydro_prepared_exists"].astype(bool)
    )
    ready_for_prep = summary["support_prep_ready"].astype(bool)
    city_ids = summary.loc[ready_for_prep & prepared_missing, "city_id"].astype(int).tolist()
    return sorted(set(city_ids))


def _append_stage_record(
    records: list[dict[str, Any]],
    *,
    stage: str,
    requested_city_ids: list[int] | None,
    effective_city_ids: list[int],
    selection_mode: str,
    summary: pd.DataFrame,
    summary_json_path: Path,
    summary_csv_path: Path,
    notes: str = "",
) -> None:
    status_counts = _status_counts(summary)
    records.append(
        {
            "stage": stage,
            "selection_mode": selection_mode,
            "requested_city_ids": "" if not requested_city_ids else ",".join(str(value) for value in requested_city_ids),
            "effective_city_ids": "" if not effective_city_ids else ",".join(str(value) for value in effective_city_ids),
            "n_effective_cities": len(effective_city_ids),
            "n_records": int(len(summary)),
            "status_counts_json": json.dumps(status_counts, sort_keys=True),
            "summary_json_path": str(summary_json_path),
            "summary_csv_path": str(summary_csv_path),
            "notes": notes,
        }
    )


def run_acquisition_orchestration(
    start_date: str,
    end_date: str,
    city_ids: list[int] | None = None,
    all_missing: bool = False,
    resolution: float = 30,
    force_raw: bool = False,
    overwrite_support: bool = False,
    orchestration_dir: Path = ORCHESTRATION_STATUS,
) -> AcquisitionOrchestrationResult:
    """Run raw support acquisition, support prep, and AppEEARS acquisition in sequence."""
    if all_missing and city_ids:
        raise ValueError("--all-missing cannot be combined with explicit city_ids")
    if not start_date.strip() or not end_date.strip():
        raise ValueError("start_date and end_date are required")

    selection_mode = "all_missing" if all_missing else ("city_subset" if city_ids else "all")
    requested_city_ids = sorted(set(city_ids or [])) or None
    records: list[dict[str, Any]] = []

    logger.info("Running orchestration stage: raw support acquisition")
    raw_result: RawAcquisitionResult = run_raw_data_acquisition(
        dataset="all",
        city_ids=requested_city_ids,
        resolution=resolution,
        all_missing=all_missing,
        force=force_raw,
    )
    _append_stage_record(
        records,
        stage="raw_support_acquisition",
        requested_city_ids=requested_city_ids,
        effective_city_ids=_effective_city_ids(raw_result.summary),
        selection_mode=selection_mode,
        summary=raw_result.summary,
        summary_json_path=raw_result.summary_json_path,
        summary_csv_path=raw_result.summary_csv_path,
        notes="dataset=all",
    )

    prep_city_ids = requested_city_ids
    if all_missing:
        logger.info("Auditing support readiness to identify cities still missing prepared support layers")
        support_preflight = audit_support_layer_readiness(
            city_ids=None,
            resolution=resolution,
            write_outputs=False,
        )
        prep_city_ids = _city_ids_missing_prepared_support(support_preflight)
        logger.info("Support prep will target %s cities with missing prepared outputs", len(prep_city_ids))

    logger.info("Running orchestration stage: support-layer prep")
    support_result: SupportLayerPrepResult = prepare_support_layers(
        city_ids=prep_city_ids,
        resolution=resolution,
        overwrite=overwrite_support,
    )
    _append_stage_record(
        records,
        stage="support_layer_prep",
        requested_city_ids=prep_city_ids,
        effective_city_ids=_effective_city_ids(support_result.summary),
        selection_mode=selection_mode,
        summary=support_result.summary,
        summary_json_path=support_result.summary_json_path,
        summary_csv_path=support_result.summary_csv_path,
    )

    logger.info("Running orchestration stage: AppEEARS NDVI")
    ndvi_result: AcquisitionRunResult = run_appeears_acquisition(
        product_type="ndvi",
        city_ids=requested_city_ids,
        start_date=start_date,
        end_date=end_date,
        retry_incomplete=True,
    )
    _append_stage_record(
        records,
        stage="appeears_ndvi",
        requested_city_ids=requested_city_ids,
        effective_city_ids=_effective_city_ids(ndvi_result.summary),
        selection_mode=selection_mode,
        summary=ndvi_result.summary,
        summary_json_path=ndvi_result.summary_json_path,
        summary_csv_path=ndvi_result.summary_csv_path,
        notes="retry_incomplete=true",
    )

    logger.info("Running orchestration stage: AppEEARS ECOSTRESS")
    ecostress_result: AcquisitionRunResult = run_appeears_acquisition(
        product_type="ecostress",
        city_ids=requested_city_ids,
        start_date=start_date,
        end_date=end_date,
        retry_incomplete=True,
    )
    _append_stage_record(
        records,
        stage="appeears_ecostress",
        requested_city_ids=requested_city_ids,
        effective_city_ids=_effective_city_ids(ecostress_result.summary),
        selection_mode=selection_mode,
        summary=ecostress_result.summary,
        summary_json_path=ecostress_result.summary_json_path,
        summary_csv_path=ecostress_result.summary_csv_path,
        notes="retry_incomplete=true",
    )

    summary_json_path, summary_csv_path = _summary_paths(orchestration_dir=orchestration_dir)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "selection_mode": selection_mode,
        "requested_city_ids": requested_city_ids or [],
        "records": records,
    }
    summary = _write_summary_outputs(
        records=records,
        payload=payload,
        summary_json_path=summary_json_path,
        summary_csv_path=summary_csv_path,
    )
    return AcquisitionOrchestrationResult(
        summary=summary,
        summary_json_path=summary_json_path,
        summary_csv_path=summary_csv_path,
    )
