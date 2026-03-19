from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config import CITY_FEATURES, FINAL, RAW_CACHE, RAW_DEM, RAW_HYDRO, RAW_NLCD, SUPPORT_LAYERS

RETENTION_MUST_KEEP = "must_keep"
RETENTION_USEFUL_TEMPORARY = "useful_to_keep_temporarily"
RETENTION_SAFE_DELETE = "safe_to_delete_regenerate"

CATEGORY_DEM_TILE = "dem_tile"
CATEGORY_NLCD_BUNDLE = "nlcd_bundle"
CATEGORY_NLCD_EXTRACTED = "nlcd_extracted"
CATEGORY_HYDRO_PACKAGE = "hydro_package"
CATEGORY_HYDRO_EXTRACTED = "hydro_extracted"
CATEGORY_PARTIAL_DOWNLOAD = "partial_download"
CATEGORY_UNKNOWN = "unknown"

PRUNE_MODE_PARTIALS = "partials"
PRUNE_MODE_NLCD_EXTRACTED = "nlcd-extracted"
PRUNE_MODE_HYDRO_EXTRACTED = "hydro-extracted"
PRUNE_MODE_EXTRACTED = "extracted"
PRUNE_MODE_REGENERABLE = "regenerable"

PRUNE_MODES = {
    PRUNE_MODE_PARTIALS,
    PRUNE_MODE_NLCD_EXTRACTED,
    PRUNE_MODE_HYDRO_EXTRACTED,
    PRUNE_MODE_EXTRACTED,
    PRUNE_MODE_REGENERABLE,
}

_CATEGORY_METADATA = {
    CATEGORY_DEM_TILE: {
        "retention_class": RETENTION_USEFUL_TEMPORARY,
        "duplicate_status": "Feeds city raw DEM rasters; downstream raw/prepared DEM files are clipped derivatives, not direct duplicates.",
    },
    CATEGORY_NLCD_BUNDLE: {
        "retention_class": RETENTION_MUST_KEEP,
        "duplicate_status": "Compressed upstream archive for the extracted 2021 NLCD rasters; city raw/prepared NLCD files are clipped derivatives.",
    },
    CATEGORY_NLCD_EXTRACTED: {
        "retention_class": RETENTION_SAFE_DELETE,
        "duplicate_status": "Extracted copy of the NLCD bundle member; duplicates bundle content in larger uncompressed form and feeds city raw/prepared NLCD clips.",
    },
    CATEGORY_HYDRO_PACKAGE: {
        "retention_class": RETENTION_USEFUL_TEMPORARY,
        "duplicate_status": "Compressed upstream HU4 archive for extracted GeoPackages; city raw/prepared hydro layers are clipped derivatives.",
    },
    CATEGORY_HYDRO_EXTRACTED: {
        "retention_class": RETENTION_SAFE_DELETE,
        "duplicate_status": "Extracted GeoPackage copy of a hydro package; duplicates package content in larger uncompressed form and feeds city raw/prepared hydro clips.",
    },
    CATEGORY_PARTIAL_DOWNLOAD: {
        "retention_class": RETENTION_SAFE_DELETE,
        "duplicate_status": "Incomplete transfer artifact; not a reproducible input and safe to remove once reported.",
    },
    CATEGORY_UNKNOWN: {
        "retention_class": RETENTION_USEFUL_TEMPORARY,
        "duplicate_status": "Unrecognized cache artifact; review manually before deleting.",
    },
}

_PRUNE_MODE_TO_CATEGORIES = {
    PRUNE_MODE_PARTIALS: {CATEGORY_PARTIAL_DOWNLOAD},
    PRUNE_MODE_NLCD_EXTRACTED: {CATEGORY_NLCD_EXTRACTED},
    PRUNE_MODE_HYDRO_EXTRACTED: {CATEGORY_HYDRO_EXTRACTED},
    PRUNE_MODE_EXTRACTED: {CATEGORY_NLCD_EXTRACTED, CATEGORY_HYDRO_EXTRACTED},
    PRUNE_MODE_REGENERABLE: {CATEGORY_PARTIAL_DOWNLOAD, CATEGORY_NLCD_EXTRACTED, CATEGORY_HYDRO_EXTRACTED},
}


@dataclass(frozen=True)
class CacheArtifact:
    """One file under the cache root with retention metadata and prune eligibility."""

    path: Path
    relative_path: str
    category: str
    retention_class: str
    duplicate_status: str
    size_bytes: int
    modified_at_utc: str
    age_hours: float
    prune_eligible: bool
    prune_block_reason: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["path"] = str(self.path)
        payload["size_gb"] = round(self.size_bytes / (1024**3), 3)
        payload["age_hours"] = round(self.age_hours, 2)
        return payload


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_cache_root(cache_dir: Path) -> Path:
    resolved = cache_dir.resolve()
    if resolved.name.lower() != "cache":
        raise ValueError(f"Refusing to operate on a non-cache directory: {resolved}")
    return resolved


def _is_within(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
    except ValueError:
        return False
    return True


def _classify_artifact(relative_path: Path) -> str:
    lower = relative_path.as_posix().lower()
    if lower.endswith(".part"):
        return CATEGORY_PARTIAL_DOWNLOAD
    if lower.startswith("dem/tiles/"):
        return CATEGORY_DEM_TILE
    if lower.startswith("nlcd/bundles/"):
        return CATEGORY_NLCD_BUNDLE
    if lower.startswith("nlcd/extracted/"):
        return CATEGORY_NLCD_EXTRACTED
    if lower.startswith("hydro/packages/"):
        return CATEGORY_HYDRO_PACKAGE
    if lower.startswith("hydro/extracted/"):
        return CATEGORY_HYDRO_EXTRACTED
    return CATEGORY_UNKNOWN


def _matching_nlcd_bundle_exists(cache_dir: Path, path: Path) -> bool:
    name = path.name.lower()
    bundles_dir = cache_dir / "nlcd" / "bundles"
    if "lndcov" in name:
        return any(bundles_dir.glob("*LndCov*.zip"))
    if "fctimp" in name:
        return any(bundles_dir.glob("*FctImp*.zip"))
    return any(bundles_dir.glob("*.zip"))


def _matching_hydro_package_exists(cache_dir: Path, path: Path) -> bool:
    stem = path.stem
    return any(match.suffix.lower() == ".zip" for match in (cache_dir / "hydro" / "packages").rglob(f"{stem}.*"))


def _prune_block_reason(
    category: str,
    path: Path,
    cache_dir: Path,
    selected_categories: set[str],
    protect_recent_hours: float,
) -> str:
    if category not in selected_categories:
        return "mode_excluded"

    modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    age_hours = (_utc_now() - modified_at).total_seconds() / 3600.0
    if age_hours < protect_recent_hours:
        return f"recent_file_under_{protect_recent_hours:g}_hours"

    if category == CATEGORY_NLCD_EXTRACTED and not _matching_nlcd_bundle_exists(cache_dir=cache_dir, path=path):
        return "missing_source_bundle"
    if category == CATEGORY_HYDRO_EXTRACTED and not _matching_hydro_package_exists(cache_dir=cache_dir, path=path):
        return "missing_source_package"
    if category == CATEGORY_UNKNOWN:
        return "unknown_category"

    return ""


def _iter_cache_files(cache_dir: Path) -> list[Path]:
    return sorted(path for path in cache_dir.rglob("*") if path.is_file())


def _artifact_from_path(
    path: Path,
    cache_dir: Path,
    selected_categories: set[str],
    protect_recent_hours: float,
) -> CacheArtifact:
    relative_path = path.resolve().relative_to(cache_dir.resolve())
    category = _classify_artifact(relative_path)
    metadata = _CATEGORY_METADATA[category]
    modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    age_hours = (_utc_now() - modified_at).total_seconds() / 3600.0
    block_reason = _prune_block_reason(
        category=category,
        path=path,
        cache_dir=cache_dir,
        selected_categories=selected_categories,
        protect_recent_hours=protect_recent_hours,
    )
    return CacheArtifact(
        path=path.resolve(),
        relative_path=relative_path.as_posix(),
        category=category,
        retention_class=str(metadata["retention_class"]),
        duplicate_status=str(metadata["duplicate_status"]),
        size_bytes=path.stat().st_size,
        modified_at_utc=modified_at.isoformat(),
        age_hours=age_hours,
        prune_eligible=block_reason == "",
        prune_block_reason=block_reason,
    )


def _summarize_artifacts(
    artifacts: list[CacheArtifact],
    key_name: str,
    key_getter: Any,
    *,
    include_metadata: bool,
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        key = str(key_getter(artifact))
        row = grouped.setdefault(
            key,
            {
                key_name: key,
                "size_bytes": 0,
                "file_count": 0,
            },
        )
        row["size_bytes"] += artifact.size_bytes
        row["file_count"] += 1
        if include_metadata:
            row.setdefault("retention_class", artifact.retention_class)
            row.setdefault("duplicate_status", artifact.duplicate_status)

    rows = []
    for row in grouped.values():
        row["size_gb"] = round(row["size_bytes"] / (1024**3), 3)
        rows.append(row)
    return sorted(rows, key=lambda item: int(item["size_bytes"]), reverse=True)


def _downstream_summary_rows() -> list[dict[str, Any]]:
    rows = []
    for label, path in [
        ("raw_dem_outputs", RAW_DEM),
        ("raw_nlcd_outputs", RAW_NLCD),
        ("raw_hydro_outputs", RAW_HYDRO),
        ("prepared_support_outputs", SUPPORT_LAYERS),
        ("city_feature_outputs", CITY_FEATURES),
        ("final_outputs", FINAL),
    ]:
        files = [item for item in path.rglob("*") if item.is_file()] if path.exists() else []
        size_bytes = sum(item.stat().st_size for item in files)
        rows.append(
            {
                "label": label,
                "path": str(path.resolve()),
                "size_bytes": size_bytes,
                "size_gb": round(size_bytes / (1024**3), 3),
                "file_count": len(files),
            }
        )
    return rows


def _selected_categories(prune_modes: list[str]) -> set[str]:
    categories: set[str] = set()
    for mode in prune_modes:
        if mode not in PRUNE_MODES:
            raise ValueError(f"Unsupported prune mode: {mode}")
        categories.update(_PRUNE_MODE_TO_CATEGORIES[mode])
    return categories


def build_cache_cleanup_report(
    *,
    cache_dir: Path = RAW_CACHE,
    prune_modes: list[str] | None = None,
    protect_recent_hours: float = 24.0,
) -> dict[str, Any]:
    """Build a storage report and safe prune plan for the configured cache tree."""

    cache_root = _ensure_cache_root(cache_dir)
    requested_modes = prune_modes or []
    selected_categories = _selected_categories(requested_modes)
    artifacts = [
        _artifact_from_path(
            path=path,
            cache_dir=cache_root,
            selected_categories=selected_categories,
            protect_recent_hours=protect_recent_hours,
        )
        for path in _iter_cache_files(cache_root)
    ]

    prune_candidates = [artifact for artifact in artifacts if artifact.prune_eligible]
    blocked_candidates = [
        artifact
        for artifact in artifacts
        if artifact.category in selected_categories and not artifact.prune_eligible
    ]

    inventory_total_bytes = sum(artifact.size_bytes for artifact in artifacts)
    prune_total_bytes = sum(artifact.size_bytes for artifact in prune_candidates)
    blocked_total_bytes = sum(artifact.size_bytes for artifact in blocked_candidates)

    return {
        "generated_at_utc": _utc_now().isoformat(),
        "cache_root": str(cache_root),
        "protect_recent_hours": protect_recent_hours,
        "requested_prune_modes": requested_modes,
        "inventory_summary": {
            "size_bytes": inventory_total_bytes,
            "size_gb": round(inventory_total_bytes / (1024**3), 3),
            "file_count": len(artifacts),
        },
        "subfolder_summary": _summarize_artifacts(
            artifacts=artifacts,
            key_name="subfolder",
            key_getter=lambda artifact: artifact.relative_path.split("/", 1)[0],
            include_metadata=False,
        ),
        "category_summary": _summarize_artifacts(
            artifacts=artifacts,
            key_name="category",
            key_getter=lambda artifact: artifact.category,
            include_metadata=True,
        ),
        "downstream_output_summary": _downstream_summary_rows(),
        "prune_summary": {
            "candidate_files": len(prune_candidates),
            "candidate_bytes": prune_total_bytes,
            "candidate_gb": round(prune_total_bytes / (1024**3), 3),
            "blocked_files": len(blocked_candidates),
            "blocked_bytes": blocked_total_bytes,
            "blocked_gb": round(blocked_total_bytes / (1024**3), 3),
        },
        "prune_candidates": [artifact.to_dict() for artifact in prune_candidates],
        "blocked_candidates": [artifact.to_dict() for artifact in blocked_candidates],
        "artifacts": [artifact.to_dict() for artifact in artifacts],
    }


def write_cache_cleanup_report(report: dict[str, Any], output_path: Path) -> Path:
    """Write a cache storage report to JSON outside the cache root."""

    cache_root = Path(str(report["cache_root"]))
    if _is_within(output_path, cache_root):
        raise ValueError(f"Refusing to write metadata inside cache root: {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    return output_path


def _remove_empty_parent_dirs(start_path: Path, stop_dir: Path) -> None:
    current = start_path.parent
    while _is_within(current, stop_dir) and current != stop_dir:
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def prune_cache(
    *,
    cache_dir: Path = RAW_CACHE,
    prune_modes: list[str] | None = None,
    protect_recent_hours: float = 24.0,
    execute: bool = False,
    report_json_path: Path | None = None,
) -> dict[str, Any]:
    """Create a prune plan and optionally delete safe cache artifacts."""

    report = build_cache_cleanup_report(
        cache_dir=cache_dir,
        prune_modes=prune_modes,
        protect_recent_hours=protect_recent_hours,
    )
    deleted: list[dict[str, Any]] = []
    if execute:
        cache_root = _ensure_cache_root(cache_dir)
        for candidate in report["prune_candidates"]:
            path = Path(str(candidate["path"]))
            if not _is_within(path, cache_root):
                raise ValueError(f"Refusing to delete outside cache root: {path}")
            if not path.exists():
                continue
            path.unlink()
            _remove_empty_parent_dirs(path, cache_root)
            deleted.append(candidate)

    report["execute"] = execute
    report["deleted_files"] = len(deleted)
    report["deleted_bytes"] = sum(int(item["size_bytes"]) for item in deleted)
    report["deleted_gb"] = round(report["deleted_bytes"] / (1024**3), 3)
    report["deleted_artifacts"] = deleted

    if report_json_path is not None:
        write_cache_cleanup_report(report=report, output_path=report_json_path)
        report["report_json_path"] = str(report_json_path.resolve())

    return report
