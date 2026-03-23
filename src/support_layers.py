from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.mask import mask
from shapely.geometry import mapping

from src.appeears_aoi import city_slug
from src.city_processing import city_output_paths
from src.config import CITY_GRIDS, RAW_DEM, RAW_HYDRO, RAW_NLCD, STUDY_AREAS, SUPPORT_LAYERS
from src.error_utils import blank_exception_details, exception_details
from src.load_cities import load_cities
from src.vector_io import normalize_vector_geometry_dimensions, write_gpkg_atomic

logger = logging.getLogger(__name__)

STATUS_BLOCKED = "blocked"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_SKIPPED_EXISTING = "skipped_existing"


@dataclass(frozen=True)
class SupportLayerSourcePaths:
    dem_raster: Path | None = None
    nlcd_land_cover_raster: Path | None = None
    nlcd_impervious_raster: Path | None = None
    hydro_vector: Path | None = None


@dataclass(frozen=True)
class SupportLayerPreparedPaths:
    prepared_dir: Path
    dem_raster: Path
    nlcd_land_cover_raster: Path
    nlcd_impervious_raster: Path
    hydro_vector: Path


@dataclass(frozen=True)
class SupportLayerPreflightResult:
    summary: pd.DataFrame
    summary_json_path: Path
    summary_csv_path: Path


@dataclass(frozen=True)
class SupportLayerPrepResult:
    summary: pd.DataFrame
    summary_json_path: Path
    summary_csv_path: Path


def _city_stem(city: pd.Series) -> str:
    return f"{int(city['city_id']):02d}_{city_slug(str(city['city_name']))}_{str(city['state']).lower()}"


def expected_support_layer_raw_paths(
    city: pd.Series,
    raw_dem_dir: Path = RAW_DEM,
    raw_nlcd_dir: Path = RAW_NLCD,
    raw_hydro_dir: Path = RAW_HYDRO,
) -> SupportLayerSourcePaths:
    slug = city_slug(str(city["city_name"]))
    return SupportLayerSourcePaths(
        dem_raster=raw_dem_dir / slug / f"{slug}_dem_3dep_30m.tif",
        nlcd_land_cover_raster=raw_nlcd_dir / slug / f"{slug}_nlcd_2021_land_cover_30m.tif",
        nlcd_impervious_raster=raw_nlcd_dir / slug / f"{slug}_nlcd_2021_impervious_30m.tif",
        hydro_vector=raw_hydro_dir / slug / f"{slug}_nhdplus_water.gpkg",
    )


def expected_support_layer_prepared_paths(
    city: pd.Series,
    support_layers_dir: Path = SUPPORT_LAYERS,
) -> SupportLayerPreparedPaths:
    prepared_dir = support_layers_dir / _city_stem(city)
    return SupportLayerPreparedPaths(
        prepared_dir=prepared_dir,
        dem_raster=prepared_dir / "dem_prepared.tif",
        nlcd_land_cover_raster=prepared_dir / "nlcd_land_cover_prepared.tif",
        nlcd_impervious_raster=prepared_dir / "nlcd_impervious_prepared.tif",
        hydro_vector=prepared_dir / "hydro_water_prepared.gpkg",
    )


def _discover_city_rasters(
    product_root: Path,
    city_name: str,
) -> list[Path]:
    city_dir = product_root / city_slug(city_name)
    if not city_dir.exists():
        return []

    candidates: list[Path] = []
    for pattern in ("*.tif", "*.tiff"):
        candidates.extend(sorted(path for path in city_dir.rglob(pattern) if path.is_file()))
    return candidates


def _discover_city_vectors(vector_root: Path, city_name: str) -> list[Path]:
    city_dir = vector_root / city_slug(city_name)
    if not city_dir.exists():
        return []

    candidates: list[Path] = []
    for pattern in ("*.gpkg", "*.shp", "*.geojson", "*.json"):
        candidates.extend(sorted(path for path in city_dir.rglob(pattern) if path.is_file()))
    return candidates


def discover_city_raw_support_sources(
    city: pd.Series,
    raw_dem_dir: Path = RAW_DEM,
    raw_nlcd_dir: Path = RAW_NLCD,
    raw_hydro_dir: Path = RAW_HYDRO,
) -> SupportLayerSourcePaths:
    city_name = str(city["city_name"])

    dem_candidates = _discover_city_rasters(raw_dem_dir, city_name=city_name)
    nlcd_candidates = _discover_city_rasters(raw_nlcd_dir, city_name=city_name)
    hydro_candidates = _discover_city_vectors(raw_hydro_dir, city_name=city_name)

    nlcd_land_cover = next(
        (path for path in nlcd_candidates if "impervious" not in path.name.lower() and "imp" not in path.name.lower()),
        None,
    )
    nlcd_impervious = next(
        (path for path in nlcd_candidates if "impervious" in path.name.lower() or "imp" in path.name.lower()),
        None,
    )

    return SupportLayerSourcePaths(
        dem_raster=dem_candidates[0] if dem_candidates else None,
        nlcd_land_cover_raster=nlcd_land_cover,
        nlcd_impervious_raster=nlcd_impervious,
        hydro_vector=hydro_candidates[0] if hydro_candidates else None,
    )


def discover_prepared_support_sources(
    city: pd.Series,
    support_layers_dir: Path = SUPPORT_LAYERS,
) -> SupportLayerSourcePaths:
    prepared = expected_support_layer_prepared_paths(city=city, support_layers_dir=support_layers_dir)
    return SupportLayerSourcePaths(
        dem_raster=prepared.dem_raster if prepared.dem_raster.exists() else None,
        nlcd_land_cover_raster=prepared.nlcd_land_cover_raster if prepared.nlcd_land_cover_raster.exists() else None,
        nlcd_impervious_raster=prepared.nlcd_impervious_raster if prepared.nlcd_impervious_raster.exists() else None,
        hydro_vector=prepared.hydro_vector if prepared.hydro_vector.exists() else None,
    )


def _preflight_paths(support_layers_dir: Path = SUPPORT_LAYERS) -> tuple[Path, Path]:
    return (
        support_layers_dir / "support_layers_preflight_summary.json",
        support_layers_dir / "support_layers_preflight_summary.csv",
    )


def _prep_summary_paths(support_layers_dir: Path = SUPPORT_LAYERS) -> tuple[Path, Path]:
    return (
        support_layers_dir / "support_layers_prep_summary.json",
        support_layers_dir / "support_layers_prep_summary.csv",
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


def _study_area_geometry(study_area_path: Path) -> tuple[gpd.GeoDataFrame, object]:
    study_area = gpd.read_file(study_area_path)
    if study_area.empty:
        raise ValueError(f"Study area is empty: {study_area_path}")
    if study_area.crs is None:
        raise ValueError(f"Study area has no CRS: {study_area_path}")

    geometry_series = study_area.geometry
    if hasattr(geometry_series, "union_all"):
        geometry = geometry_series.union_all()
    else:  # pragma: no cover
        geometry = geometry_series.unary_union

    if geometry is None or geometry.is_empty:
        raise ValueError(f"Study area has empty geometry: {study_area_path}")
    return study_area, geometry


def _clip_raster_to_study_area(
    source_path: Path,
    study_area_path: Path,
    output_path: Path,
) -> Path:
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
                "compress": "LZW",
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(clipped)
    return output_path


def _clip_vector_to_study_area(
    source_path: Path,
    study_area_path: Path,
    output_path: Path,
) -> Path:
    study_area, geometry = _study_area_geometry(study_area_path)
    hydro = gpd.read_file(source_path)
    if hydro.crs is None:
        raise ValueError(f"Vector source has no CRS: {source_path}")

    hydro = hydro.to_crs(study_area.crs)
    hydro = hydro[hydro.geometry.notna() & ~hydro.geometry.is_empty].copy()

    if not hydro.empty:
        hydro = hydro[hydro.geometry.intersects(geometry)].copy()
        if not hydro.empty:
            hydro.geometry = hydro.geometry.intersection(geometry)
            hydro = hydro[hydro.geometry.notna() & ~hydro.geometry.is_empty].copy()

    hydro = normalize_vector_geometry_dimensions(hydro, context=f"support-layer hydro clip {output_path.name}")
    return write_gpkg_atomic(hydro, output_path)


def audit_support_layer_readiness(
    city_ids: list[int] | None = None,
    resolution: float = 30,
    study_areas_dir: Path = STUDY_AREAS,
    city_grids_dir: Path = CITY_GRIDS,
    raw_dem_dir: Path = RAW_DEM,
    raw_nlcd_dir: Path = RAW_NLCD,
    raw_hydro_dir: Path = RAW_HYDRO,
    support_layers_dir: Path = SUPPORT_LAYERS,
    write_outputs: bool = True,
) -> SupportLayerPreflightResult:
    """Audit deterministic support-layer raw and prepared paths for the selected cities."""
    cities = load_cities()
    if city_ids is not None:
        cities = cities[cities["city_id"].isin(city_ids)].copy()

    generated_at_utc = datetime.now(timezone.utc).isoformat()
    records: list[dict[str, Any]] = []
    summary_json_path, summary_csv_path = _preflight_paths(support_layers_dir=support_layers_dir)

    for _, city in cities.iterrows():
        study_area_path, grid_path = city_output_paths(
            city=city,
            resolution=resolution,
            study_areas_dir=study_areas_dir,
            city_grids_dir=city_grids_dir,
        )
        expected_raw = expected_support_layer_raw_paths(
            city=city,
            raw_dem_dir=raw_dem_dir,
            raw_nlcd_dir=raw_nlcd_dir,
            raw_hydro_dir=raw_hydro_dir,
        )
        prepared = expected_support_layer_prepared_paths(city=city, support_layers_dir=support_layers_dir)
        discovered_raw = discover_city_raw_support_sources(
            city=city,
            raw_dem_dir=raw_dem_dir,
            raw_nlcd_dir=raw_nlcd_dir,
            raw_hydro_dir=raw_hydro_dir,
        )

        study_area_exists = study_area_path.exists()
        grid_exists = grid_path.exists()
        dem_source_available = discovered_raw.dem_raster is not None
        nlcd_land_cover_source_available = discovered_raw.nlcd_land_cover_raster is not None
        nlcd_impervious_source_available = discovered_raw.nlcd_impervious_raster is not None
        hydro_source_available = discovered_raw.hydro_vector is not None

        dem_prepared_exists = prepared.dem_raster.exists()
        nlcd_land_cover_prepared_exists = prepared.nlcd_land_cover_raster.exists()
        nlcd_impervious_prepared_exists = prepared.nlcd_impervious_raster.exists()
        hydro_prepared_exists = prepared.hydro_vector.exists()

        prep_blockers: list[str] = []
        feature_blockers: list[str] = []

        if not study_area_exists:
            prep_blockers.append("study_area_missing")
        if not dem_source_available:
            prep_blockers.append("dem_source_missing")
        if not nlcd_land_cover_source_available:
            prep_blockers.append("nlcd_land_cover_source_missing")
        if not nlcd_impervious_source_available:
            prep_blockers.append("nlcd_impervious_source_missing")
        if not hydro_source_available:
            prep_blockers.append("hydro_source_missing")

        if not grid_exists:
            feature_blockers.append("grid_missing")
        if not (dem_prepared_exists or dem_source_available):
            feature_blockers.append("dem_feature_input_missing")
        if not (nlcd_land_cover_prepared_exists or nlcd_land_cover_source_available):
            feature_blockers.append("nlcd_land_cover_feature_input_missing")
        if not (nlcd_impervious_prepared_exists or nlcd_impervious_source_available):
            feature_blockers.append("nlcd_impervious_feature_input_missing")
        if not (hydro_prepared_exists or hydro_source_available):
            feature_blockers.append("hydro_feature_input_missing")

        records.append(
            {
                "city_id": int(city["city_id"]),
                "city_slug": city_slug(str(city["city_name"])),
                "expected_study_area_path": str(study_area_path),
                "expected_grid_path": str(grid_path),
                "expected_dem_raw_path": str(expected_raw.dem_raster),
                "expected_nlcd_land_cover_raw_path": str(expected_raw.nlcd_land_cover_raster),
                "expected_nlcd_impervious_raw_path": str(expected_raw.nlcd_impervious_raster),
                "expected_hydro_raw_path": str(expected_raw.hydro_vector),
                "dem_source_path": str(discovered_raw.dem_raster) if discovered_raw.dem_raster else "",
                "nlcd_land_cover_source_path": str(discovered_raw.nlcd_land_cover_raster)
                if discovered_raw.nlcd_land_cover_raster
                else "",
                "nlcd_impervious_source_path": str(discovered_raw.nlcd_impervious_raster)
                if discovered_raw.nlcd_impervious_raster
                else "",
                "hydro_source_path": str(discovered_raw.hydro_vector) if discovered_raw.hydro_vector else "",
                "expected_dem_prepared_path": str(prepared.dem_raster),
                "expected_nlcd_land_cover_prepared_path": str(prepared.nlcd_land_cover_raster),
                "expected_nlcd_impervious_prepared_path": str(prepared.nlcd_impervious_raster),
                "expected_hydro_prepared_path": str(prepared.hydro_vector),
                "study_area_exists": study_area_exists,
                "grid_exists": grid_exists,
                "dem_source_available": dem_source_available,
                "nlcd_land_cover_source_available": nlcd_land_cover_source_available,
                "nlcd_impervious_source_available": nlcd_impervious_source_available,
                "hydro_source_available": hydro_source_available,
                "required_inputs_exist": (
                    dem_source_available
                    and nlcd_land_cover_source_available
                    and nlcd_impervious_source_available
                    and hydro_source_available
                ),
                "dem_prepared_exists": dem_prepared_exists,
                "nlcd_land_cover_prepared_exists": nlcd_land_cover_prepared_exists,
                "nlcd_impervious_prepared_exists": nlcd_impervious_prepared_exists,
                "hydro_prepared_exists": hydro_prepared_exists,
                "support_prep_ready": len(prep_blockers) == 0,
                "feature_extraction_ready": len(feature_blockers) == 0,
                "prep_blocking_reasons": ";".join(prep_blockers),
                "feature_blocking_reasons": ";".join(feature_blockers),
                "blocking_reasons": ";".join(sorted(set(prep_blockers + feature_blockers))),
                "updated_at_utc": generated_at_utc,
            }
        )

    payload = {
        "generated_at_utc": generated_at_utc,
        "records": records,
    }
    summary = (
        _write_summary_outputs(records, payload, summary_json_path, summary_csv_path)
        if write_outputs
        else pd.DataFrame(records)
    )
    return SupportLayerPreflightResult(
        summary=summary,
        summary_json_path=summary_json_path,
        summary_csv_path=summary_csv_path,
    )


def prepare_support_layers(
    city_ids: list[int] | None = None,
    resolution: float = 30,
    overwrite: bool = False,
    study_areas_dir: Path = STUDY_AREAS,
    city_grids_dir: Path = CITY_GRIDS,
    raw_dem_dir: Path = RAW_DEM,
    raw_nlcd_dir: Path = RAW_NLCD,
    raw_hydro_dir: Path = RAW_HYDRO,
    support_layers_dir: Path = SUPPORT_LAYERS,
) -> SupportLayerPrepResult:
    """Prepare deterministic per-city support-layer artifacts from standardized raw folders."""
    cities = load_cities()
    if city_ids is not None:
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
    preflight_by_city = {
        int(row["city_id"]): row
        for row in preflight.summary.to_dict(orient="records")
    }

    generated_at_utc = datetime.now(timezone.utc).isoformat()
    records: list[dict[str, Any]] = []
    summary_json_path, summary_csv_path = _prep_summary_paths(support_layers_dir=support_layers_dir)

    for _, city in cities.iterrows():
        city_id = int(city["city_id"])
        row = preflight_by_city[city_id]
        prepared = expected_support_layer_prepared_paths(city=city, support_layers_dir=support_layers_dir)

        record: dict[str, Any] = {
            "city_id": city_id,
            "city_name": str(city["city_name"]),
            "city_slug": city_slug(str(city["city_name"])),
            "study_area_path": str(row["expected_study_area_path"]),
            "grid_path": str(row["expected_grid_path"]),
            "dem_source_path": str(row["dem_source_path"]),
            "nlcd_land_cover_source_path": str(row["nlcd_land_cover_source_path"]),
            "nlcd_impervious_source_path": str(row["nlcd_impervious_source_path"]),
            "hydro_source_path": str(row["hydro_source_path"]),
            "dem_prepared_path": str(prepared.dem_raster),
            "nlcd_land_cover_prepared_path": str(prepared.nlcd_land_cover_raster),
            "nlcd_impervious_prepared_path": str(prepared.nlcd_impervious_raster),
            "hydro_prepared_path": str(prepared.hydro_vector),
            "status": "",
            "error": "",
            "updated_at_utc": generated_at_utc,
            **blank_exception_details(),
        }

        if not bool(row["support_prep_ready"]):
            record["status"] = STATUS_BLOCKED
            record["error"] = str(row["prep_blocking_reasons"])
            records.append(record)
            continue

        if (
            not overwrite
            and prepared.dem_raster.exists()
            and prepared.nlcd_land_cover_raster.exists()
            and prepared.nlcd_impervious_raster.exists()
            and prepared.hydro_vector.exists()
        ):
            record["status"] = STATUS_SKIPPED_EXISTING
            records.append(record)
            continue

        try:
            _clip_raster_to_study_area(Path(row["dem_source_path"]), Path(row["expected_study_area_path"]), prepared.dem_raster)
            _clip_raster_to_study_area(
                Path(row["nlcd_land_cover_source_path"]),
                Path(row["expected_study_area_path"]),
                prepared.nlcd_land_cover_raster,
            )
            _clip_raster_to_study_area(
                Path(row["nlcd_impervious_source_path"]),
                Path(row["expected_study_area_path"]),
                prepared.nlcd_impervious_raster,
            )
            _clip_vector_to_study_area(
                Path(row["hydro_source_path"]),
                Path(row["expected_study_area_path"]),
                prepared.hydro_vector,
            )
            record["status"] = STATUS_COMPLETED
            record["error"] = ""
        except Exception as exc:  # pragma: no cover - exercised in integration/manual runs
            logger.exception("Support-layer prep failed for city_id=%s", city_id)
            record["status"] = STATUS_FAILED
            record["error"] = str(exc)
            record.update(exception_details(exc))

        records.append(record)

    payload = {
        "generated_at_utc": generated_at_utc,
        "records": records,
    }
    summary = _write_summary_outputs(records, payload, summary_json_path, summary_csv_path)
    return SupportLayerPrepResult(
        summary=summary,
        summary_json_path=summary_json_path,
        summary_csv_path=summary_csv_path,
    )

