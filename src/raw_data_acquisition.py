from __future__ import annotations

import json
import logging
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import requests
from rasterio.io import MemoryFile
from rasterio.mask import mask
from rasterio.merge import merge
from shapely.geometry import mapping

from src.appeears_aoi import city_slug
from src.city_processing import city_output_paths
from src.config import (
    CITY_GRIDS,
    MRLC_ANNUAL_NLCD_IMPERVIOUS_BUNDLE_URL,
    MRLC_ANNUAL_NLCD_LAND_COVER_BUNDLE_URL,
    RAW_CACHE_DEM,
    RAW_CACHE_HYDRO,
    RAW_CACHE_NLCD,
    RAW_DEM,
    RAW_HYDRO,
    RAW_NLCD,
    STUDY_AREAS,
    SUPPORT_LAYERS,
    TNM_3DEP_1ARCSEC_DATASET,
    TNM_ACCESS_BASE_URL,
    TNM_NHDPLUS_HR_DATASET,
)
from src.load_cities import load_cities
from src.support_layers import audit_support_layer_readiness, expected_support_layer_raw_paths

logger = logging.getLogger(__name__)

STATUS_BLOCKED = "blocked"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_SKIPPED_EXISTING = "skipped_existing"

DATASET_ALL = "all"
DATASET_DEM = "dem"
DATASET_NLCD = "nlcd"
DATASET_HYDRO = "hydro"

NLCD_TARGET_YEAR = 2021
REQUEST_TIMEOUT = (30, 300)
SUMMARY_JSON_NAME = "raw_data_acquisition_summary.json"
SUMMARY_CSV_NAME = "raw_data_acquisition_summary.csv"
NLCD_LAND_MEMBER_PATTERN = re.compile(rf"Annual_NLCD_LndCov_{NLCD_TARGET_YEAR}_.*\.tif$", re.IGNORECASE)
NLCD_IMPERVIOUS_MEMBER_PATTERN = re.compile(rf"Annual_NLCD_FctImp_{NLCD_TARGET_YEAR}_.*\.tif$", re.IGNORECASE)
_TILE_KEY_PATTERN = re.compile(r"([ns]\d{2}[ew]\d{3})", re.IGNORECASE)
_HU4_KEY_PATTERN = re.compile(r"(\d{4})_HU4_", re.IGNORECASE)
_HU4_TITLE_PATTERN = re.compile(r"HU\) 4 - (\d{4})", re.IGNORECASE)
_WATER_LAYER_CANDIDATES = ("NHDWaterbody", "NHDArea", "NHDFlowline")
_AREA_FTYPE_CODES = {390, 436, 445, 460, 484}
_FLOWLINE_FTYPE_CODES = {334, 336, 343, 428, 460, 558}


@dataclass(frozen=True)
class RawAcquisitionResult:
    """Summary artifact paths and per-city acquisition results for one run."""

    summary: pd.DataFrame
    summary_json_path: Path
    summary_csv_path: Path


def _summary_paths(support_layers_dir: Path = SUPPORT_LAYERS) -> tuple[Path, Path]:
    return (
        support_layers_dir / SUMMARY_JSON_NAME,
        support_layers_dir / SUMMARY_CSV_NAME,
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


def _union_geometry(geometry_series: gpd.GeoSeries) -> Any:
    if hasattr(geometry_series, "union_all"):
        return geometry_series.union_all()
    return geometry_series.unary_union  # pragma: no cover


def _study_area_geometry(study_area_path: Path) -> tuple[gpd.GeoDataFrame, Any]:
    study_area = gpd.read_file(study_area_path)
    if study_area.empty:
        raise ValueError(f"Study area is empty: {study_area_path}")
    if study_area.crs is None:
        raise ValueError(f"Study area has no CRS: {study_area_path}")

    geometry = _union_geometry(study_area.geometry)
    if geometry is None or geometry.is_empty:
        raise ValueError(f"Study area has empty geometry: {study_area_path}")
    return study_area, geometry


def _study_area_bbox_wgs84(study_area_path: Path) -> tuple[float, float, float, float]:
    study_area, _ = _study_area_geometry(study_area_path)
    bounds = study_area.to_crs(epsg=4326).total_bounds
    return (float(bounds[0]), float(bounds[1]), float(bounds[2]), float(bounds[3]))


def _download_file(session: requests.Session, url: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 0:
        return destination

    temp_path = destination.with_suffix(destination.suffix + ".part")
    if temp_path.exists():
        temp_path.unlink()

    logger.info("Downloading %s", url)
    with session.get(url, stream=True, timeout=REQUEST_TIMEOUT) as response:
        response.raise_for_status()
        with temp_path.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)

    temp_path.replace(destination)
    return destination


def _extract_zip_member(zip_path: Path, member_name: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 0:
        return destination

    temp_path = destination.with_suffix(destination.suffix + ".part")
    if temp_path.exists():
        temp_path.unlink()

    with zipfile.ZipFile(zip_path) as archive:
        with archive.open(member_name) as src, temp_path.open("wb") as dst:
            dst.write(src.read())

    temp_path.replace(destination)
    return destination


def _parse_product_datetime(item: dict[str, Any]) -> tuple[str, str]:
    publication = str(item.get("publicationDate", "") or "")
    updated = str(item.get("lastUpdated", "") or "")
    return publication, updated


def _select_latest_products_by_key(
    items: list[dict[str, Any]],
    key_parser: Callable[[dict[str, Any]], str | None],
) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for item in items:
        key = key_parser(item)
        if not key:
            continue
        current = selected.get(key)
        candidate_rank = (*_parse_product_datetime(item), str(item.get("downloadURL", "")))
        if current is None:
            selected[key] = item
            continue
        current_rank = (*_parse_product_datetime(current), str(current.get("downloadURL", "")))
        if candidate_rank > current_rank:
            selected[key] = item
    return [selected[key] for key in sorted(selected)]


def _dem_tile_key(item: dict[str, Any]) -> str | None:
    for value in (str(item.get("downloadURL", "")), str(item.get("title", ""))):
        match = _TILE_KEY_PATTERN.search(value)
        if match:
            return match.group(1).lower()
    return None


def _hu4_key(item: dict[str, Any]) -> str | None:
    for value in (str(item.get("downloadURL", "")), str(item.get("title", ""))):
        match = _HU4_KEY_PATTERN.search(value)
        if match:
            return match.group(1)
    match = _HU4_TITLE_PATTERN.search(str(item.get("title", "")))
    if match:
        return match.group(1)
    return None


def _tnm_products(
    session: requests.Session,
    dataset_name: str,
    bbox_wgs84: tuple[float, float, float, float],
    prod_formats: str | None = None,
) -> list[dict[str, Any]]:
    params: dict[str, str] = {
        "datasets": dataset_name,
        "bbox": ",".join(f"{value:.8f}" for value in bbox_wgs84),
    }
    if prod_formats:
        params["prodFormats"] = prod_formats

    response = session.get(f"{TNM_ACCESS_BASE_URL}/products", params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    return payload.get("items", []) if isinstance(payload, dict) else []


def _clip_raster_to_study_area(source_path: Path, study_area_path: Path, output_path: Path) -> Path:
    study_area, geometry = _study_area_geometry(study_area_path)
    with rasterio.open(source_path) as src:
        if src.crs is None:
            raise ValueError(f"Raster has no CRS: {source_path}")

        clip_geom = gpd.GeoSeries([geometry], crs=study_area.crs).to_crs(src.crs)
        clipped, transform = mask(
            src,
            [mapping(geom) for geom in clip_geom.geometry],
            crop=True,
            nodata=src.nodata,
            filled=True,
        )
        profile = src.profile.copy()
        profile.update(
            {
                "height": clipped.shape[1],
                "width": clipped.shape[2],
                "transform": transform,
                "count": clipped.shape[0],
                "dtype": str(clipped.dtype),
                "compress": "LZW",
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    if temp_path.exists():
        temp_path.unlink()
    with rasterio.open(temp_path, "w", **profile) as dst:
        dst.write(clipped)
    temp_path.replace(output_path)
    return output_path


def _mosaic_and_clip_rasters(source_paths: list[Path], study_area_path: Path, output_path: Path) -> Path:
    if len(source_paths) == 0:
        raise ValueError("source_paths must not be empty")
    if len(source_paths) == 1:
        return _clip_raster_to_study_area(source_paths[0], study_area_path, output_path)

    study_area, geometry = _study_area_geometry(study_area_path)
    datasets = [rasterio.open(path) for path in source_paths]
    try:
        if datasets[0].crs is None:
            raise ValueError(f"Raster has no CRS: {source_paths[0]}")

        mosaic, transform = merge(datasets)
        profile = datasets[0].profile.copy()
        nodata = profile.get("nodata")
        if nodata is None:
            nodata = np.nan if np.issubdtype(mosaic.dtype, np.floating) else 0
        profile.update(
            {
                "height": mosaic.shape[1],
                "width": mosaic.shape[2],
                "transform": transform,
                "count": mosaic.shape[0],
                "dtype": str(mosaic.dtype),
                "nodata": nodata,
                "compress": "LZW",
            }
        )

        with MemoryFile() as memory_file:
            with memory_file.open(**profile) as mem:
                mem.write(mosaic)
                clip_geom = gpd.GeoSeries([geometry], crs=study_area.crs).to_crs(mem.crs)
                clipped, clipped_transform = mask(
                    mem,
                    [mapping(geom) for geom in clip_geom.geometry],
                    crop=True,
                    nodata=nodata,
                    filled=True,
                )

        profile.update(
            {
                "height": clipped.shape[1],
                "width": clipped.shape[2],
                "transform": clipped_transform,
            }
        )
    finally:
        for dataset in datasets:
            dataset.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    if temp_path.exists():
        temp_path.unlink()
    with rasterio.open(temp_path, "w", **profile) as dst:
        dst.write(clipped)
    temp_path.replace(output_path)
    return output_path


def _zip_member_name(zip_path: Path, pattern: re.Pattern[str]) -> str:
    with zipfile.ZipFile(zip_path) as archive:
        matches = sorted(name for name in archive.namelist() if pattern.search(Path(name).name))
    if len(matches) == 0:
        raise FileNotFoundError(f"No ZIP member in {zip_path} matched {pattern.pattern}")
    return matches[0]


def _write_vector_output(gdf: gpd.GeoDataFrame, output_path: Path, layer: str = "water") -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    if temp_path.exists():
        temp_path.unlink()
    if output_path.exists():
        output_path.unlink()
    gdf.to_file(temp_path, layer=layer, driver="GPKG")
    temp_path.replace(output_path)
    return output_path


def _filter_water_layer(gdf: gpd.GeoDataFrame, layer_name: str) -> gpd.GeoDataFrame:
    if "FType" not in gdf.columns:
        return gdf

    if layer_name == "NHDArea":
        filtered = gdf[gdf["FType"].isin(_AREA_FTYPE_CODES)].copy()
        return filtered if not filtered.empty else gdf
    if layer_name == "NHDFlowline":
        filtered = gdf[gdf["FType"].isin(_FLOWLINE_FTYPE_CODES)].copy()
        return filtered if not filtered.empty else gdf
    return gdf


def collect_nhdplus_water_features(package_path: Path, study_area_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Load and clip the NHDPlus HR water layers needed by downstream distance-to-water logic."""
    import pyogrio

    if study_area_gdf.empty:
        raise ValueError("study_area_gdf must not be empty")
    if study_area_gdf.crs is None:
        raise ValueError("study_area_gdf must have a CRS")

    study_geometry = _union_geometry(study_area_gdf.geometry)
    available_layers: dict[str, str] = {}
    for layer_info in pyogrio.list_layers(package_path):
        layer_name = str(layer_info[0])
        available_layers[layer_name.lower()] = layer_name
    frames: list[gpd.GeoDataFrame] = []

    for candidate in _WATER_LAYER_CANDIDATES:
        layer_name = available_layers.get(candidate.lower())
        if layer_name is None:
            continue

        water = gpd.read_file(package_path, layer=layer_name)
        if water.empty or water.crs is None:
            continue

        water = water[water.geometry.notna() & ~water.geometry.is_empty].copy()
        if water.empty:
            continue

        water = _filter_water_layer(water, candidate)
        study_in_layer_crs = study_area_gdf.to_crs(water.crs)
        layer_geometry = _union_geometry(study_in_layer_crs.geometry)
        water = water[water.geometry.intersects(layer_geometry)].copy()
        if water.empty:
            continue

        water.geometry = water.geometry.intersection(layer_geometry)
        water = water[water.geometry.notna() & ~water.geometry.is_empty].copy()
        if water.empty:
            continue

        water = water[["geometry"]].copy()
        water["source_layer"] = candidate
        frames.append(water.to_crs(study_area_gdf.crs))

    if not frames:
        return gpd.GeoDataFrame({"source_layer": pd.Series(dtype=str)}, geometry=[], crs=study_area_gdf.crs)

    merged = pd.concat(frames, ignore_index=True)
    water = gpd.GeoDataFrame(merged, geometry="geometry", crs=study_area_gdf.crs)
    water = water[water.geometry.notna() & ~water.geometry.is_empty].copy()
    water.geometry = water.geometry.intersection(study_geometry)
    water = water[water.geometry.notna() & ~water.geometry.is_empty].copy()
    if water.empty:
        return gpd.GeoDataFrame({"source_layer": pd.Series(dtype=str)}, geometry=[], crs=study_area_gdf.crs)

    water["geometry_wkb"] = water.geometry.to_wkb(hex=True)
    water = water.drop_duplicates(subset=["source_layer", "geometry_wkb"]).drop(columns=["geometry_wkb"])
    return water.reset_index(drop=True)


def _acquire_dem_for_city(
    city: pd.Series,
    study_area_path: Path,
    output_path: Path,
    session: requests.Session,
    cache_dir: Path,
) -> dict[str, Any]:
    bbox_wgs84 = _study_area_bbox_wgs84(study_area_path)
    items = _tnm_products(
        session=session,
        dataset_name=TNM_3DEP_1ARCSEC_DATASET,
        bbox_wgs84=bbox_wgs84,
        prod_formats="GeoTIFF",
    )
    selected_items = _select_latest_products_by_key(items, key_parser=_dem_tile_key)
    if len(selected_items) == 0:
        raise RuntimeError("dem_tiles_not_found")

    tile_paths: list[Path] = []
    for item in selected_items:
        download_url = str(item.get("downloadURL", "") or "")
        if not download_url:
            continue
        tile_key = _dem_tile_key(item) or "unknown_tile"
        destination = cache_dir / "tiles" / tile_key / Path(download_url).name
        tile_paths.append(_download_file(session=session, url=download_url, destination=destination))

    if len(tile_paths) == 0:
        raise RuntimeError("dem_tile_downloads_missing")

    _mosaic_and_clip_rasters(tile_paths, study_area_path=study_area_path, output_path=output_path)
    return {
        "source_urls": [str(item.get("downloadURL", "")) for item in selected_items],
        "cache_paths": [str(path) for path in tile_paths],
        "n_source_files": len(tile_paths),
    }


def _ensure_nlcd_sources(session: requests.Session, cache_dir: Path) -> tuple[Path, Path]:
    land_bundle = _download_file(
        session=session,
        url=MRLC_ANNUAL_NLCD_LAND_COVER_BUNDLE_URL,
        destination=cache_dir / "bundles" / Path(MRLC_ANNUAL_NLCD_LAND_COVER_BUNDLE_URL).name,
    )
    impervious_bundle = _download_file(
        session=session,
        url=MRLC_ANNUAL_NLCD_IMPERVIOUS_BUNDLE_URL,
        destination=cache_dir / "bundles" / Path(MRLC_ANNUAL_NLCD_IMPERVIOUS_BUNDLE_URL).name,
    )

    land_member = _zip_member_name(land_bundle, NLCD_LAND_MEMBER_PATTERN)
    impervious_member = _zip_member_name(impervious_bundle, NLCD_IMPERVIOUS_MEMBER_PATTERN)

    land_raster = _extract_zip_member(
        zip_path=land_bundle,
        member_name=land_member,
        destination=cache_dir / "extracted" / Path(land_member).name,
    )
    impervious_raster = _extract_zip_member(
        zip_path=impervious_bundle,
        member_name=impervious_member,
        destination=cache_dir / "extracted" / Path(impervious_member).name,
    )
    return land_raster, impervious_raster


def _acquire_nlcd_for_city(
    study_area_path: Path,
    land_cover_output_path: Path,
    impervious_output_path: Path,
    session: requests.Session,
    cache_dir: Path,
) -> dict[str, Any]:
    land_source, impervious_source = _ensure_nlcd_sources(session=session, cache_dir=cache_dir)
    _clip_raster_to_study_area(land_source, study_area_path=study_area_path, output_path=land_cover_output_path)
    _clip_raster_to_study_area(impervious_source, study_area_path=study_area_path, output_path=impervious_output_path)
    return {
        "source_urls": [MRLC_ANNUAL_NLCD_LAND_COVER_BUNDLE_URL, MRLC_ANNUAL_NLCD_IMPERVIOUS_BUNDLE_URL],
        "cache_paths": [str(land_source), str(impervious_source)],
        "n_source_files": 2,
    }


def _hydro_geopackage_zip_member(zip_path: Path) -> str:
    with zipfile.ZipFile(zip_path) as archive:
        matches = sorted(name for name in archive.namelist() if name.lower().endswith(".gpkg"))
    if len(matches) == 0:
        raise FileNotFoundError(f"No GeoPackage found in {zip_path}")
    return matches[0]


def _acquire_hydro_for_city(
    study_area_path: Path,
    output_path: Path,
    session: requests.Session,
    cache_dir: Path,
) -> dict[str, Any]:
    bbox_wgs84 = _study_area_bbox_wgs84(study_area_path)
    items = _tnm_products(
        session=session,
        dataset_name=TNM_NHDPLUS_HR_DATASET,
        bbox_wgs84=bbox_wgs84,
    )
    geopackage_items = [item for item in items if "geopackage" in str(item.get("format", "")).lower()]
    selected_items = _select_latest_products_by_key(geopackage_items, key_parser=_hu4_key)
    if len(selected_items) == 0:
        raise RuntimeError("hydro_packages_not_found")

    study_area, _ = _study_area_geometry(study_area_path)
    all_water_frames: list[gpd.GeoDataFrame] = []
    cache_paths: list[str] = []

    for item in selected_items:
        download_url = str(item.get("downloadURL", "") or "")
        if not download_url:
            continue
        hu4_key = _hu4_key(item) or "unknown_hu4"
        zip_path = _download_file(
            session=session,
            url=download_url,
            destination=cache_dir / "packages" / hu4_key / Path(download_url).name,
        )
        member_name = _hydro_geopackage_zip_member(zip_path)
        package_path = _extract_zip_member(
            zip_path=zip_path,
            member_name=member_name,
            destination=cache_dir / "extracted" / Path(member_name).name,
        )
        cache_paths.append(str(package_path))
        water = collect_nhdplus_water_features(package_path=package_path, study_area_gdf=study_area)
        if not water.empty:
            all_water_frames.append(water)

    if all_water_frames:
        combined = pd.concat(all_water_frames, ignore_index=True)
        water_gdf = gpd.GeoDataFrame(combined, geometry="geometry", crs=study_area.crs)
        water_gdf["geometry_wkb"] = water_gdf.geometry.to_wkb(hex=True)
        water_gdf = water_gdf.drop_duplicates(subset=["source_layer", "geometry_wkb"]).drop(columns=["geometry_wkb"])
    else:
        water_gdf = gpd.GeoDataFrame({"source_layer": pd.Series(dtype=str)}, geometry=[], crs=study_area.crs)

    _write_vector_output(water_gdf, output_path=output_path)
    return {
        "source_urls": [str(item.get("downloadURL", "")) for item in selected_items],
        "cache_paths": cache_paths,
        "n_source_files": len(cache_paths),
    }


def _selected_datasets(dataset: str) -> tuple[str, ...]:
    normalized = dataset.strip().lower()
    if normalized == DATASET_ALL:
        return (DATASET_DEM, DATASET_NLCD, DATASET_HYDRO)
    if normalized in {DATASET_DEM, DATASET_NLCD, DATASET_HYDRO}:
        return (normalized,)
    raise ValueError("dataset must be one of: all, dem, nlcd, hydro")


def _dataset_missing(preflight_row: dict[str, Any], dataset: str) -> bool:
    if dataset == DATASET_DEM:
        return not bool(preflight_row.get("dem_source_available", False))
    if dataset == DATASET_NLCD:
        return not (
            bool(preflight_row.get("nlcd_land_cover_source_available", False))
            and bool(preflight_row.get("nlcd_impervious_source_available", False))
        )
    if dataset == DATASET_HYDRO:
        return not bool(preflight_row.get("hydro_source_available", False))
    raise ValueError(f"Unsupported dataset: {dataset}")


def _dataset_outputs_exist(expected_paths: Any, dataset: str) -> bool:
    if dataset == DATASET_DEM:
        return bool(expected_paths.dem_raster and expected_paths.dem_raster.exists())
    if dataset == DATASET_NLCD:
        return bool(
            expected_paths.nlcd_land_cover_raster
            and expected_paths.nlcd_land_cover_raster.exists()
            and expected_paths.nlcd_impervious_raster
            and expected_paths.nlcd_impervious_raster.exists()
        )
    if dataset == DATASET_HYDRO:
        return bool(expected_paths.hydro_vector and expected_paths.hydro_vector.exists())
    raise ValueError(f"Unsupported dataset: {dataset}")


def _dataset_output_fields(expected_paths: Any, dataset: str) -> tuple[Path, Path | None]:
    if dataset == DATASET_DEM:
        return expected_paths.dem_raster, None
    if dataset == DATASET_NLCD:
        return expected_paths.nlcd_land_cover_raster, expected_paths.nlcd_impervious_raster
    if dataset == DATASET_HYDRO:
        return expected_paths.hydro_vector, None
    raise ValueError(f"Unsupported dataset: {dataset}")


def run_raw_data_acquisition(
    dataset: str = DATASET_ALL,
    city_ids: list[int] | None = None,
    resolution: float = 30,
    all_missing: bool = False,
    force: bool = False,
    study_areas_dir: Path = STUDY_AREAS,
    city_grids_dir: Path = CITY_GRIDS,
    raw_dem_dir: Path = RAW_DEM,
    raw_nlcd_dir: Path = RAW_NLCD,
    raw_hydro_dir: Path = RAW_HYDRO,
    dem_cache_dir: Path = RAW_CACHE_DEM,
    nlcd_cache_dir: Path = RAW_CACHE_NLCD,
    hydro_cache_dir: Path = RAW_CACHE_HYDRO,
    support_layers_dir: Path = SUPPORT_LAYERS,
) -> RawAcquisitionResult:
    """Populate deterministic city raw DEM, NLCD, and hydro paths with restartable caching and summaries."""
    datasets = _selected_datasets(dataset)
    only_missing = all_missing or city_ids is None

    cities = load_cities()
    if city_ids:
        cities = cities[cities["city_id"].isin(city_ids)].copy()

    preflight = audit_support_layer_readiness(
        city_ids=city_ids,
        resolution=resolution,
        study_areas_dir=study_areas_dir,
        city_grids_dir=city_grids_dir,
        raw_dem_dir=raw_dem_dir,
        raw_nlcd_dir=raw_nlcd_dir,
        raw_hydro_dir=raw_hydro_dir,
        support_layers_dir=support_layers_dir,
        write_outputs=False,
    )
    preflight_by_city = {int(row["city_id"]): row for row in preflight.summary.to_dict(orient="records")}

    if only_missing:
        target_city_ids = []
        for _, city in cities.iterrows():
            row = preflight_by_city[int(city["city_id"])]
            if any(_dataset_missing(row, item) for item in datasets):
                target_city_ids.append(int(city["city_id"]))
        cities = cities[cities["city_id"].isin(target_city_ids)].copy()

    generated_at_utc = datetime.now(timezone.utc).isoformat()
    summary_json_path, summary_csv_path = _summary_paths(support_layers_dir=support_layers_dir)
    records: list[dict[str, Any]] = []

    with requests.Session() as session:
        session.headers.update({"User-Agent": "urban-heat-raw-acquisition/1.0"})

        for _, city in cities.iterrows():
            city_id = int(city["city_id"])
            city_name = str(city["city_name"])
            slug = city_slug(city_name)
            study_area_path, _ = city_output_paths(
                city=city,
                resolution=resolution,
                study_areas_dir=study_areas_dir,
                city_grids_dir=city_grids_dir,
            )
            expected_paths = expected_support_layer_raw_paths(
                city=city,
                raw_dem_dir=raw_dem_dir,
                raw_nlcd_dir=raw_nlcd_dir,
                raw_hydro_dir=raw_hydro_dir,
            )
            preflight_row = preflight_by_city.get(city_id, {})

            for item in datasets:
                if only_missing and not force and not _dataset_missing(preflight_row, item):
                    continue

                primary_output_path, secondary_output_path = _dataset_output_fields(expected_paths, item)
                record = {
                    "city_id": city_id,
                    "city_name": city_name,
                    "state": str(city["state"]),
                    "city_slug": slug,
                    "dataset": item,
                    "study_area_path": str(study_area_path),
                    "expected_output_path": str(primary_output_path),
                    "expected_secondary_output_path": str(secondary_output_path) if secondary_output_path else "",
                    "status": "",
                    "error": "",
                    "source_urls": "",
                    "cache_paths": "",
                    "n_source_files": 0,
                    "updated_at_utc": generated_at_utc,
                }

                if not study_area_path.exists():
                    record["status"] = STATUS_BLOCKED
                    record["error"] = "study_area_missing"
                    records.append(record)
                    continue

                if not force and _dataset_outputs_exist(expected_paths, item):
                    record["status"] = STATUS_SKIPPED_EXISTING
                    records.append(record)
                    continue

                try:
                    logger.info("Acquiring %s for city_id=%s city=%s", item, city_id, city_name)
                    if item == DATASET_DEM:
                        result = _acquire_dem_for_city(
                            city=city,
                            study_area_path=study_area_path,
                            output_path=primary_output_path,
                            session=session,
                            cache_dir=dem_cache_dir,
                        )
                    elif item == DATASET_NLCD:
                        result = _acquire_nlcd_for_city(
                            study_area_path=study_area_path,
                            land_cover_output_path=primary_output_path,
                            impervious_output_path=secondary_output_path,
                            session=session,
                            cache_dir=nlcd_cache_dir,
                        )
                    else:
                        result = _acquire_hydro_for_city(
                            study_area_path=study_area_path,
                            output_path=primary_output_path,
                            session=session,
                            cache_dir=hydro_cache_dir,
                        )

                    record["status"] = STATUS_COMPLETED
                    record["source_urls"] = ";".join(result.get("source_urls", []))
                    record["cache_paths"] = ";".join(result.get("cache_paths", []))
                    record["n_source_files"] = int(result.get("n_source_files", 0) or 0)
                except Exception as exc:  # pragma: no cover - exercised in integration/manual runs
                    logger.exception("Raw acquisition failed for city_id=%s dataset=%s", city_id, item)
                    record["status"] = STATUS_FAILED
                    record["error"] = str(exc)

                records.append(record)

    payload = {
        "generated_at_utc": generated_at_utc,
        "dataset": dataset,
        "city_ids": city_ids or [],
        "only_missing": only_missing,
        "force": force,
        "records": records,
    }
    summary = _write_summary_outputs(records, payload, summary_json_path, summary_csv_path)
    return RawAcquisitionResult(
        summary=summary,
        summary_json_path=summary_json_path,
        summary_csv_path=summary_csv_path,
    )

