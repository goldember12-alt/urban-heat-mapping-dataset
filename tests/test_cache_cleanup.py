import os
import time
from pathlib import Path

import pytest

from src.cache_cleanup import build_cache_cleanup_report, prune_cache


def _write_bytes(path: Path, size_bytes: int = 16) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size_bytes)
    return path


def _set_age_hours(path: Path, age_hours: float) -> None:
    timestamp = time.time() - age_hours * 3600.0
    os.utime(path, (timestamp, timestamp))


def test_build_cache_cleanup_report_classifies_categories_and_safe_candidates(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    nlcd_bundle = _write_bytes(cache_dir / "nlcd" / "bundles" / "Annual_NLCD_LndCov_2015-2024_CU_C1V1.zip")
    nlcd_extracted = _write_bytes(cache_dir / "nlcd" / "extracted" / "Annual_NLCD_LndCov_2021_CU_C1V1.tif")
    hydro_package = _write_bytes(cache_dir / "hydro" / "packages" / "1504" / "NHDPLUS_H_1504_HU4_GPKG.zip")
    hydro_extracted = _write_bytes(cache_dir / "hydro" / "extracted" / "NHDPLUS_H_1504_HU4_GPKG.gpkg")
    dem_tile = _write_bytes(cache_dir / "dem" / "tiles" / "n33w111" / "USGS_1_n33w111_20240401.tif")
    old_partial = _write_bytes(cache_dir / "hydro" / "packages" / "0304" / "NHDPLUS_H_0304_HU4_GPKG.zip.part")
    recent_partial = _write_bytes(cache_dir / "hydro" / "packages" / "1019" / "NHDPLUS_H_1019_HU4_GPKG.zip.part")

    for path in [nlcd_bundle, nlcd_extracted, hydro_package, hydro_extracted, dem_tile, old_partial]:
        _set_age_hours(path, age_hours=72)
    _set_age_hours(recent_partial, age_hours=1)

    report = build_cache_cleanup_report(
        cache_dir=cache_dir,
        prune_modes=["regenerable"],
        protect_recent_hours=24,
    )

    categories = {row["category"]: row for row in report["category_summary"]}
    assert categories["nlcd_bundle"]["retention_class"] == "must_keep"
    assert categories["dem_tile"]["retention_class"] == "useful_to_keep_temporarily"
    assert categories["hydro_extracted"]["retention_class"] == "safe_to_delete_regenerate"

    candidate_paths = {row["relative_path"] for row in report["prune_candidates"]}
    assert "nlcd/extracted/Annual_NLCD_LndCov_2021_CU_C1V1.tif" in candidate_paths
    assert "hydro/extracted/NHDPLUS_H_1504_HU4_GPKG.gpkg" in candidate_paths
    assert "hydro/packages/0304/NHDPLUS_H_0304_HU4_GPKG.zip.part" in candidate_paths
    assert "hydro/packages/1019/NHDPLUS_H_1019_HU4_GPKG.zip.part" not in candidate_paths

    blocked = {row["relative_path"]: row["prune_block_reason"] for row in report["blocked_candidates"]}
    assert blocked["hydro/packages/1019/NHDPLUS_H_1019_HU4_GPKG.zip.part"] == "recent_file_under_24_hours"


def test_build_cache_cleanup_report_blocks_extracted_files_without_source_archives(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    nlcd_extracted = _write_bytes(cache_dir / "nlcd" / "extracted" / "Annual_NLCD_FctImp_2021_CU_C1V1.tif")
    hydro_extracted = _write_bytes(cache_dir / "hydro" / "extracted" / "NHDPLUS_H_1505_HU4_GPKG.gpkg")
    _set_age_hours(nlcd_extracted, age_hours=48)
    _set_age_hours(hydro_extracted, age_hours=48)

    report = build_cache_cleanup_report(
        cache_dir=cache_dir,
        prune_modes=["extracted"],
        protect_recent_hours=24,
    )

    assert report["prune_summary"]["candidate_files"] == 0
    blocked = {row["relative_path"]: row["prune_block_reason"] for row in report["blocked_candidates"]}
    assert blocked["nlcd/extracted/Annual_NLCD_FctImp_2021_CU_C1V1.tif"] == "missing_source_bundle"
    assert blocked["hydro/extracted/NHDPLUS_H_1505_HU4_GPKG.gpkg"] == "missing_source_package"


def test_prune_cache_execute_deletes_only_safe_candidates_and_writes_report(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    bundle = _write_bytes(cache_dir / "nlcd" / "bundles" / "Annual_NLCD_FctImp_2015-2024_CU_C1V1.zip")
    extracted = _write_bytes(cache_dir / "nlcd" / "extracted" / "Annual_NLCD_FctImp_2021_CU_C1V1.tif")
    partial = _write_bytes(cache_dir / "hydro" / "packages" / "0304" / "NHDPLUS_H_0304_HU4_GPKG.zip.part")
    dem_tile = _write_bytes(cache_dir / "dem" / "tiles" / "n30w095" / "USGS_1_n30w095_20240229.tif")
    for path in [bundle, extracted, partial, dem_tile]:
        _set_age_hours(path, age_hours=48)

    report_path = tmp_path / "outputs" / "cache_cleanup_report.json"
    report = prune_cache(
        cache_dir=cache_dir,
        prune_modes=["regenerable"],
        protect_recent_hours=24,
        execute=True,
        report_json_path=report_path,
    )

    assert report["deleted_files"] == 2
    assert not extracted.exists()
    assert not partial.exists()
    assert bundle.exists()
    assert dem_tile.exists()
    assert report_path.exists()


def test_build_cache_cleanup_report_rejects_non_cache_directory(tmp_path: Path):
    with pytest.raises(ValueError, match="non-cache directory"):
        build_cache_cleanup_report(cache_dir=tmp_path / "not_cache")
