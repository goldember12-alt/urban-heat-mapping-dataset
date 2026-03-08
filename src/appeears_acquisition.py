from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.appeears_aoi import city_slug, export_appeears_aois, load_aoi_feature_collection
from src.appeears_client import AppEEARSClient, AppEEARSRequestError, build_area_task_payload
from src.config import (
    APPEEARS_AOI,
    APPEEARS_STATUS,
    ECOSTRESS_DEFAULT_LAYER,
    ECOSTRESS_PRODUCT_CANDIDATES,
    NDVI_DEFAULT_LAYER,
    NDVI_DEFAULT_PRODUCT,
    RAW_ECOSTRESS,
    RAW_NDVI,
    STUDY_AREAS,
)
from src.load_cities import load_cities

logger = logging.getLogger(__name__)

STATUS_BLOCKED = "blocked"
STATUS_PENDING = "pending"
STATUS_SUBMITTED = "submitted"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

_PRODUCT_TYPE_NDVI = "ndvi"
_PRODUCT_TYPE_ECOSTRESS = "ecostress"


@dataclass(frozen=True)
class ProductSpec:
    product_type: str
    layer: str
    product_candidates: tuple[str, ...]


@dataclass(frozen=True)
class AcquisitionRunResult:
    summary: pd.DataFrame
    summary_json_path: Path
    summary_csv_path: Path


def build_product_spec(product_type: str, product: str | None = None, layer: str | None = None) -> ProductSpec:
    normalized = product_type.strip().lower()
    if normalized == _PRODUCT_TYPE_NDVI:
        return ProductSpec(
            product_type=normalized,
            layer=layer or NDVI_DEFAULT_LAYER,
            product_candidates=(product or NDVI_DEFAULT_PRODUCT,),
        )

    if normalized == _PRODUCT_TYPE_ECOSTRESS:
        if product:
            product_candidates = (product,)
        else:
            product_candidates = ECOSTRESS_PRODUCT_CANDIDATES

        return ProductSpec(
            product_type=normalized,
            layer=layer or ECOSTRESS_DEFAULT_LAYER,
            product_candidates=product_candidates,
        )

    raise ValueError("product_type must be one of: ndvi, ecostress")


def resolve_city_download_dir(
    product_type: str,
    city_name: str,
    raw_ndvi_dir: Path = RAW_NDVI,
    raw_ecostress_dir: Path = RAW_ECOSTRESS,
) -> Path:
    """Route downloads to product-specific immutable raw-data folders."""
    slug = city_slug(city_name)
    normalized = product_type.strip().lower()
    if normalized == _PRODUCT_TYPE_NDVI:
        return raw_ndvi_dir / slug
    if normalized == _PRODUCT_TYPE_ECOSTRESS:
        return raw_ecostress_dir / slug
    raise ValueError("Unsupported product type for download routing")


def is_incomplete_status(status: str | None) -> bool:
    normalized = (status or "").strip().lower()
    return normalized in {"", STATUS_BLOCKED, STATUS_PENDING, STATUS_SUBMITTED, STATUS_FAILED}


def filter_cities_for_retry(
    cities: pd.DataFrame,
    existing_records: dict[int, dict[str, Any]],
    retry_incomplete: bool,
) -> pd.DataFrame:
    """Return cities that should be attempted in the current run."""
    if not retry_incomplete:
        return cities.copy()

    keep_rows: list[bool] = []
    for _, city in cities.iterrows():
        city_id = int(city["city_id"])
        previous = existing_records.get(city_id, {})
        keep_rows.append(is_incomplete_status(str(previous.get("status", ""))))
    return cities.loc[keep_rows].copy()


def _summary_paths(product_type: str, status_dir: Path = APPEEARS_STATUS) -> tuple[Path, Path]:
    summary_json = status_dir / f"appeears_{product_type}_acquisition_summary.json"
    summary_csv = status_dir / f"appeears_{product_type}_acquisition_summary.csv"
    return summary_json, summary_csv


def _load_existing_records(summary_json_path: Path) -> dict[int, dict[str, Any]]:
    if not summary_json_path.exists():
        return {}

    with summary_json_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    records = payload.get("records", []) if isinstance(payload, dict) else []
    results: dict[int, dict[str, Any]] = {}
    for row in records:
        if not isinstance(row, dict):
            continue
        city_id = row.get("city_id")
        if city_id is None:
            continue
        results[int(city_id)] = row
    return results


def _run_mode(submit_only: bool, poll_only: bool, download_only: bool) -> tuple[bool, bool, bool]:
    n_flags = int(submit_only) + int(poll_only) + int(download_only)
    if n_flags > 1:
        raise ValueError("Only one of --submit-only, --poll-only, --download-only can be used")

    if submit_only:
        return True, False, False
    if poll_only:
        return False, True, False
    if download_only:
        return False, True, True

    # default run: submit, poll once, and download if task is complete
    return True, True, True


def _infer_remote_task_status(task_payload: dict[str, Any]) -> str:
    for key in ("status", "task_status", "state"):
        value = task_payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    return "unknown"


def _is_remote_complete(remote_status: str) -> bool:
    return remote_status in {"done", "complete", "completed", "success", "succeeded"}


def _is_remote_failed(remote_status: str) -> bool:
    return remote_status in {"error", "failed", "failure", "canceled", "cancelled"}


def _base_record(
    city: pd.Series,
    product_type: str,
    spec: ProductSpec,
    start_date: str,
    end_date: str,
    previous: dict[str, Any] | None,
) -> dict[str, Any]:
    previous = previous or {}
    return {
        "city_id": int(city["city_id"]),
        "city_name": str(city["city_name"]),
        "state": str(city["state"]),
        "city_slug": city_slug(str(city["city_name"])),
        "product_type": product_type,
        "product": str(previous.get("product", spec.product_candidates[0])),
        "layer": str(previous.get("layer", spec.layer)),
        "start_date": start_date,
        "end_date": end_date,
        "study_area_path": str(previous.get("study_area_path", "")),
        "aoi_path": str(previous.get("aoi_path", "")),
        "download_dir": str(previous.get("download_dir", "")),
        "task_id": str(previous.get("task_id", "")),
        "remote_task_status": str(previous.get("remote_task_status", "")),
        "status": str(previous.get("status", STATUS_PENDING)).lower(),
        "n_bundle_files": int(previous.get("n_bundle_files", 0) or 0),
        "n_files_downloaded": int(previous.get("n_files_downloaded", 0) or 0),
        "n_files_existing": int(previous.get("n_files_existing", 0) or 0),
        "error": str(previous.get("error", "")),
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def _download_completed_bundle(
    client: AppEEARSClient,
    task_id: str,
    download_dir: Path,
) -> tuple[int, int, int]:
    files = client.list_bundle_files(task_id)
    if len(files) == 0:
        raise RuntimeError("bundle_empty")

    n_downloaded = 0
    n_existing = 0

    for item in files:
        file_id = item.get("file_id") or item.get("fileID") or item.get("id")
        if file_id is None:
            raise RuntimeError("bundle_file_id_missing")

        file_name = item.get("file_name") or item.get("fileName") or item.get("name")
        if not isinstance(file_name, str) or not file_name:
            file_name = f"{file_id}.bin"

        destination = download_dir / file_name
        if destination.exists():
            n_existing += 1
            continue

        client.download_bundle_file(task_id=task_id, file_id=str(file_id), destination=destination)
        n_downloaded += 1

    return len(files), n_downloaded, n_existing


def run_appeears_acquisition(
    product_type: str,
    start_date: str,
    end_date: str,
    city_ids: list[int] | None = None,
    submit_only: bool = False,
    poll_only: bool = False,
    download_only: bool = False,
    retry_incomplete: bool = False,
    product: str | None = None,
    layer: str | None = None,
    study_areas_dir: Path = STUDY_AREAS,
    aoi_dir: Path = APPEEARS_AOI,
    status_dir: Path = APPEEARS_STATUS,
) -> AcquisitionRunResult:
    """Run AppEEARS acquisition for NDVI or ECOSTRESS with resumable status tracking."""
    normalized_product_type = product_type.strip().lower()
    run_submit, run_poll, run_download = _run_mode(
        submit_only=submit_only,
        poll_only=poll_only,
        download_only=download_only,
    )

    spec = build_product_spec(product_type=normalized_product_type, product=product, layer=layer)
    summary_json_path, summary_csv_path = _summary_paths(product_type=normalized_product_type, status_dir=status_dir)
    existing_records = _load_existing_records(summary_json_path)

    cities = load_cities()
    if city_ids:
        cities = cities[cities["city_id"].isin(city_ids)].copy()

    target_cities = filter_cities_for_retry(cities, existing_records=existing_records, retry_incomplete=retry_incomplete)
    target_city_ids = {int(x) for x in target_cities["city_id"].tolist()}

    aoi_summary = export_appeears_aois(cities=cities, study_areas_dir=study_areas_dir, aoi_dir=aoi_dir)
    aoi_by_city = {int(row["city_id"]): row for _, row in aoi_summary.iterrows()}

    records_by_city: dict[int, dict[str, Any]] = dict(existing_records)

    client: AppEEARSClient | None = None
    client_error: str | None = None

    def ensure_client() -> AppEEARSClient | None:
        nonlocal client, client_error
        if client is not None:
            return client
        if client_error is not None:
            return None
        try:
            client = AppEEARSClient.from_environment()
            return client
        except Exception as exc:
            client_error = str(exc)
            logger.error("AppEEARS authentication setup failed: %s", exc)
            return None

    for _, city in cities.iterrows():
        city_id = int(city["city_id"])
        previous = existing_records.get(city_id, {})
        previous_status = str(previous.get("status", "")).strip().lower()

        record = _base_record(
            city=city,
            product_type=normalized_product_type,
            spec=spec,
            start_date=start_date,
            end_date=end_date,
            previous=previous,
        )

        aoi_row = aoi_by_city.get(city_id)
        if aoi_row is None:
            record["status"] = STATUS_BLOCKED
            record["error"] = "aoi_stage_missing"
            records_by_city[city_id] = record
            continue

        record["study_area_path"] = str(aoi_row.get("study_area_path", ""))
        record["aoi_path"] = str(aoi_row.get("aoi_path", ""))

        aoi_status = str(aoi_row.get("status", ""))
        if aoi_status == STATUS_BLOCKED:
            record["status"] = STATUS_BLOCKED
            record["error"] = str(aoi_row.get("error", "")) or "study_area_missing"
            records_by_city[city_id] = record
            continue
        if aoi_status == STATUS_FAILED:
            record["status"] = STATUS_FAILED
            record["error"] = str(aoi_row.get("error", "")) or "aoi_export_failed"
            records_by_city[city_id] = record
            continue

        # retry-incomplete mode should avoid reprocessing already-completed cities
        if city_id not in target_city_ids:
            records_by_city[city_id] = record
            continue

        # default behavior: leave completed cities untouched unless explicitly retried
        if previous_status == STATUS_COMPLETED and not retry_incomplete:
            records_by_city[city_id] = record
            continue

        task_id = str(record.get("task_id", ""))

        if not run_submit and not task_id:
            record["status"] = STATUS_PENDING
            record["error"] = "task_id_missing"
            records_by_city[city_id] = record
            continue

        client_instance = ensure_client()
        if client_instance is None:
            record["status"] = STATUS_BLOCKED
            record["error"] = client_error or "auth_missing"
            records_by_city[city_id] = record
            continue

        should_submit = run_submit and (
            not task_id
            or (retry_incomplete and previous_status in {STATUS_BLOCKED, STATUS_PENDING, STATUS_FAILED})
        )

        if should_submit:
            submit_error: str | None = None
            try:
                aoi_payload = load_aoi_feature_collection(Path(record["aoi_path"]))
            except Exception as exc:
                record["status"] = STATUS_FAILED
                record["error"] = f"aoi_load_error:{exc}"
                records_by_city[city_id] = record
                continue

            for candidate_product in spec.product_candidates:
                task_name = f"{normalized_product_type}_{record['city_slug']}_{start_date}_{end_date}"
                payload = build_area_task_payload(
                    task_name=task_name,
                    product=candidate_product,
                    layer=spec.layer,
                    start_date=start_date,
                    end_date=end_date,
                    aoi_feature_collection=aoi_payload,
                )
                try:
                    response = client_instance.submit_area_task(payload)
                    task_id = response.task_id
                    record["product"] = candidate_product
                    record["layer"] = spec.layer
                    record["task_id"] = task_id
                    record["status"] = STATUS_SUBMITTED
                    record["error"] = ""
                    submit_error = None
                    break
                except AppEEARSRequestError as exc:
                    submit_error = str(exc)
                    logger.warning(
                        "Task submit failed for city_id=%s product=%s: %s",
                        city_id,
                        candidate_product,
                        exc,
                    )

            if submit_error is not None:
                record["status"] = STATUS_FAILED
                record["error"] = submit_error
                records_by_city[city_id] = record
                continue

        if run_poll and task_id:
            try:
                task_payload = client_instance.get_task(task_id)
                remote_status = _infer_remote_task_status(task_payload)
                record["remote_task_status"] = remote_status

                if _is_remote_failed(remote_status):
                    record["status"] = STATUS_FAILED
                    record["error"] = f"task_failed:{remote_status}"
                    records_by_city[city_id] = record
                    continue

                record["status"] = STATUS_SUBMITTED
                record["error"] = ""

                if not _is_remote_complete(remote_status):
                    records_by_city[city_id] = record
                    continue
            except AppEEARSRequestError as exc:
                record["status"] = STATUS_FAILED
                record["error"] = f"poll_error:{exc}"
                records_by_city[city_id] = record
                continue

        if run_download and task_id:
            remote_status = str(record.get("remote_task_status", "")).lower()
            if not _is_remote_complete(remote_status):
                record["status"] = STATUS_SUBMITTED
                record["error"] = ""
                records_by_city[city_id] = record
                continue

            download_dir = resolve_city_download_dir(
                product_type=normalized_product_type,
                city_name=str(record["city_name"]),
            )
            record["download_dir"] = str(download_dir)
            download_dir.mkdir(parents=True, exist_ok=True)

            try:
                n_bundle_files, n_downloaded, n_existing = _download_completed_bundle(
                    client=client_instance,
                    task_id=task_id,
                    download_dir=download_dir,
                )
                record["n_bundle_files"] = n_bundle_files
                record["n_files_downloaded"] = n_downloaded
                record["n_files_existing"] = n_existing
                if n_downloaded + n_existing > 0:
                    record["status"] = STATUS_COMPLETED
                    record["error"] = ""
                else:
                    record["status"] = STATUS_FAILED
                    record["error"] = "no_bundle_files_downloaded"
            except Exception as exc:
                record["status"] = STATUS_FAILED
                record["error"] = f"download_error:{exc}"

        records_by_city[city_id] = record

    final_records = sorted(records_by_city.values(), key=lambda x: int(x["city_id"]))
    final_summary = pd.DataFrame(final_records)

    status_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "product_type": normalized_product_type,
        "start_date": start_date,
        "end_date": end_date,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "records": final_records,
    }

    with summary_json_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    final_summary.to_csv(summary_csv_path, index=False)

    logger.info("Wrote AppEEARS acquisition summary JSON: %s", summary_json_path)
    logger.info("Wrote AppEEARS acquisition summary CSV: %s", summary_csv_path)

    return AcquisitionRunResult(
        summary=final_summary,
        summary_json_path=summary_json_path,
        summary_csv_path=summary_csv_path,
    )

