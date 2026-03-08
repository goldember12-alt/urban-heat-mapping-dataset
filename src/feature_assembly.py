from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from rasterio.enums import Resampling

from src.city_processing import city_output_paths, load_city_record
from src.config import (
    CITY_FEATURES,
    CITY_GRIDS,
    FINAL,
    INTERMEDIATE,
    RAW_DEM,
    RAW_ECOSTRESS,
    RAW_HYDRO,
    RAW_NDVI,
    RAW_NLCD,
)
from src.load_cities import load_cities
from src.raster_features import (
    align_and_extract_raster_values,
    choose_city_or_global_files,
    discover_rasters,
    first_existing,
    raster_exists,
    sample_median_from_raster_stack,
)
from src.water_features import compute_dist_to_water_m

logger = logging.getLogger(__name__)

FINAL_COLUMNS = [
    "city_id",
    "city_name",
    "climate_group",
    "cell_id",
    "centroid_lon",
    "centroid_lat",
    "impervious_pct",
    "land_cover_class",
    "elevation_m",
    "dist_to_water_m",
    "ndvi_median_may_aug",
    "lst_median_may_aug",
    "n_valid_ecostress_passes",
    "hotspot_10pct",
]

OPEN_WATER_CLASS = 11


@dataclass(frozen=True)
class FeatureSourceConfig:
    dem_raster: Path | None = None
    nlcd_land_cover_raster: Path | None = None
    nlcd_impervious_raster: Path | None = None
    hydro_vector: Path | None = None
    ndvi_rasters: list[Path] = field(default_factory=list)
    lst_rasters: list[Path] = field(default_factory=list)


@dataclass(frozen=True)
class CityFeatureResult:
    city: pd.Series
    n_rows: int
    city_features_gpkg_path: Path | None
    city_features_parquet_path: Path | None
    intermediate_unfiltered_path: Path | None
    intermediate_filtered_path: Path | None
    blocked_stages: list[str]


@dataclass(frozen=True)
class BatchFeatureResult:
    summary: pd.DataFrame
    summary_path: Path


@dataclass(frozen=True)
class FinalDatasetResult:
    final_df: pd.DataFrame
    parquet_path: Path
    csv_path: Path


def _city_slug(city_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", city_name.strip().lower()).strip("_")


def _city_stem(city: pd.Series) -> str:
    return f"{int(city['city_id']):02d}_{_city_slug(str(city['city_name']))}_{str(city['state']).lower()}"

def _discover_city_product_rasters(
    product_root: Path,
    city_name: str,
    include_name_tokens: tuple[str, ...],
) -> list[Path]:
    """Discover AppEEARS rasters for one city/product by scanning the city slug subfolder recursively."""
    city_dir = product_root / _city_slug(city_name)
    if not city_dir.exists():
        return []

    candidates: list[Path] = []
    for pattern in ("*.tif", "*.tiff"):
        candidates.extend(sorted(path for path in city_dir.rglob(pattern) if path.is_file()))

    if not candidates:
        return []

    tokens = tuple(token.lower() for token in include_name_tokens if token)
    if not tokens:
        return candidates

    return [path for path in candidates if any(token in path.name.lower() for token in tokens)]

def discover_default_feature_sources(city: pd.Series) -> FeatureSourceConfig:
    """Discover optional feature source files from default raw-data folders."""
    city_name = str(city["city_name"])
    city_id = int(city["city_id"])

    dem = first_existing(discover_rasters(RAW_DEM))

    nlcd_rasters = discover_rasters(RAW_NLCD)
    nlcd_city = choose_city_or_global_files(nlcd_rasters, city_name=city_name, city_id=city_id)
    nlcd_land = first_existing([p for p in nlcd_city if "impervious" not in p.name.lower() and "imp" not in p.name.lower()])
    nlcd_impervious = first_existing([p for p in nlcd_city if "impervious" in p.name.lower() or "imp" in p.name.lower()])

    hydro_candidates: list[Path] = []
    if RAW_HYDRO.exists():
        for pattern in ["*.gpkg", "*.shp", "*.geojson", "*.json"]:
            hydro_candidates.extend(sorted(RAW_HYDRO.glob(pattern)))
    hydro = first_existing(hydro_candidates)
    ndvi_city = _discover_city_product_rasters(
        product_root=RAW_NDVI,
        city_name=city_name,
        include_name_tokens=("_ndvi_",),
    )
    if not ndvi_city:
        ndvi_candidates = discover_rasters(RAW_NDVI)
        ndvi_city = choose_city_or_global_files(ndvi_candidates, city_name=city_name, city_id=city_id)

    lst_city = _discover_city_product_rasters(
        product_root=RAW_ECOSTRESS,
        city_name=city_name,
        include_name_tokens=("_lst_",),
    )
    if not lst_city:
        lst_candidates = discover_rasters(RAW_ECOSTRESS)
        lst_city = choose_city_or_global_files(lst_candidates, city_name=city_name, city_id=city_id)

    return FeatureSourceConfig(
        dem_raster=dem,
        nlcd_land_cover_raster=nlcd_land,
        nlcd_impervious_raster=nlcd_impervious,
        hydro_vector=hydro,
        ndvi_rasters=ndvi_city,
        lst_rasters=lst_city,
    )


def _resolve_city_grid_path(city: pd.Series, resolution: float = 30, city_grids_dir: Path = CITY_GRIDS) -> Path:
    _, grid_path = city_output_paths(city=city, resolution=resolution, city_grids_dir=city_grids_dir)
    return grid_path


def _read_city_grid(grid_path: Path, max_cells: int | None = None) -> gpd.GeoDataFrame:
    """Read a city grid GeoPackage, optionally limiting feature count for partial runs."""
    if max_cells is None:
        return gpd.read_file(grid_path)
    if max_cells <= 0:
        raise ValueError("max_cells must be positive when provided")

    try:
        return gpd.read_file(grid_path, rows=slice(0, max_cells))
    except TypeError:
        grid = gpd.read_file(grid_path)
        return grid.head(max_cells).copy()


def _aligned_stage_dir(intermediate_dir: Path, city_stem: str) -> Path:
    return intermediate_dir / "aligned_rasters" / city_stem


def _base_city_features(grid_gdf: gpd.GeoDataFrame, city: pd.Series) -> gpd.GeoDataFrame:
    base = grid_gdf[["cell_id", "geometry"]].copy()
    base["city_id"] = int(city["city_id"])
    base["city_name"] = str(city["city_name"])
    base["climate_group"] = str(city["climate_group"])

    centroid_proj = gpd.GeoSeries(base.geometry.centroid, crs=base.crs)
    centroid_wgs84 = centroid_proj.to_crs(epsg=4326)
    base["centroid_lon"] = centroid_wgs84.x.astype(float)
    base["centroid_lat"] = centroid_wgs84.y.astype(float)
    return base


def _apply_rule_filters(df: gpd.GeoDataFrame, lst_stage_available: bool) -> gpd.GeoDataFrame:
    filtered = df.copy()

    if "land_cover_class" in filtered.columns and filtered["land_cover_class"].notna().any():
        before = len(filtered)
        filtered = filtered[filtered["land_cover_class"] != OPEN_WATER_CLASS].copy()
        logger.info("Dropped %s open-water cells", before - len(filtered))

    if lst_stage_available:
        before = len(filtered)
        passes = filtered["n_valid_ecostress_passes"].fillna(0).astype("Int64")
        filtered = filtered[passes >= 3].copy()
        logger.info("Dropped %s cells with <3 ECOSTRESS passes", before - len(filtered))

    return filtered


def _assign_hotspot(df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    out = df.copy()
    out["hotspot_10pct"] = pd.Series(pd.array([pd.NA] * len(out), dtype="boolean"), index=out.index)

    has_lst = out["lst_median_may_aug"].notna().any()
    if not has_lst:
        return out

    for city_id, city_rows in out.groupby("city_id"):
        valid = city_rows["lst_median_may_aug"].dropna()
        if valid.empty:
            continue
        threshold = float(valid.quantile(0.9))
        mask = (out["city_id"] == city_id) & out["lst_median_may_aug"].notna()
        out.loc[mask, "hotspot_10pct"] = (out.loc[mask, "lst_median_may_aug"] >= threshold).astype("boolean")

    return out


def _finalize_city_feature_columns(city_features: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    for column in FINAL_COLUMNS:
        if column not in city_features.columns:
            city_features[column] = np.nan
    city_features = city_features[[*FINAL_COLUMNS, "geometry"]]
    return city_features


def assemble_city_features(
    city_name: str | None = None,
    city_id: int | None = None,
    resolution: float = 30,
    feature_sources: FeatureSourceConfig | None = None,
    save_outputs: bool = True,
    max_cells: int | None = None,
    city_grids_dir: Path = CITY_GRIDS,
    city_features_dir: Path = CITY_FEATURES,
    intermediate_dir: Path = INTERMEDIATE,
) -> CityFeatureResult:
    """Assemble one city's cell-level feature table from available source layers."""
    city = load_city_record(city_name=city_name, city_id=city_id)
    stem = _city_stem(city)

    grid_path = _resolve_city_grid_path(city=city, resolution=resolution, city_grids_dir=city_grids_dir)
    if not grid_path.exists():
        raise FileNotFoundError(f"City grid not found: {grid_path}. Run city/grid pipeline first.")

    grid = _read_city_grid(grid_path=grid_path, max_cells=max_cells)
    if grid.empty:
        raise ValueError(f"Grid file is empty: {grid_path}")
    if max_cells is not None and len(grid) == max_cells:
        logger.info("Feature extraction for city_id=%s limited to first %s grid cells", int(city["city_id"]), max_cells)

    if feature_sources is None:
        feature_sources = discover_default_feature_sources(city)

    blocked_stages: list[str] = []
    city_features = _base_city_features(grid, city)

    aligned_dir = _aligned_stage_dir(intermediate_dir, stem)
    if save_outputs:
        aligned_dir.mkdir(parents=True, exist_ok=True)

    # DEM
    if raster_exists(feature_sources.dem_raster):
        dem_aligned = aligned_dir / "dem_aligned.tif" if save_outputs else None
        city_features["elevation_m"] = align_and_extract_raster_values(
            grid_gdf=city_features,
            raster_path=feature_sources.dem_raster,
            resolution=resolution,
            resampling=Resampling.bilinear,
            aligned_output_path=dem_aligned,
        )
    else:
        blocked_stages.append("dem")
        city_features["elevation_m"] = np.nan

    # NLCD
    if raster_exists(feature_sources.nlcd_land_cover_raster):
        land_cover_aligned = aligned_dir / "nlcd_land_cover_aligned.tif" if save_outputs else None
        land_cover = align_and_extract_raster_values(
            grid_gdf=city_features,
            raster_path=feature_sources.nlcd_land_cover_raster,
            resolution=resolution,
            resampling=Resampling.nearest,
            aligned_output_path=land_cover_aligned,
        )
        city_features["land_cover_class"] = pd.Series(land_cover).round().astype("Int64")
    else:
        blocked_stages.append("nlcd_land_cover")
        city_features["land_cover_class"] = pd.Series(pd.array([pd.NA] * len(city_features), dtype="Int64"))

    if raster_exists(feature_sources.nlcd_impervious_raster):
        impervious_aligned = aligned_dir / "nlcd_impervious_aligned.tif" if save_outputs else None
        city_features["impervious_pct"] = align_and_extract_raster_values(
            grid_gdf=city_features,
            raster_path=feature_sources.nlcd_impervious_raster,
            resolution=resolution,
            resampling=Resampling.bilinear,
            aligned_output_path=impervious_aligned,
        )
    else:
        blocked_stages.append("nlcd_impervious")
        city_features["impervious_pct"] = np.nan

    # Hydro distance-to-water
    if feature_sources.hydro_vector is not None and feature_sources.hydro_vector.exists():
        dist_raster_path = aligned_dir / "dist_to_water_m_aligned.tif" if save_outputs else None
        city_features["dist_to_water_m"] = compute_dist_to_water_m(
            grid_gdf=city_features,
            hydro_path=feature_sources.hydro_vector,
            resolution=resolution,
            distance_raster_output_path=dist_raster_path,
        )
    else:
        blocked_stages.append("hydro_distance")
        city_features["dist_to_water_m"] = np.nan

    # NDVI
    ndvi_paths = [p for p in feature_sources.ndvi_rasters if p.exists()]
    if ndvi_paths:
        ndvi_median, _ = sample_median_from_raster_stack(
            grid_gdf=city_features,
            raster_paths=ndvi_paths,
            resolution=resolution,
            resampling=Resampling.bilinear,
        )
        city_features["ndvi_median_may_aug"] = ndvi_median
    else:
        blocked_stages.append("ndvi")
        city_features["ndvi_median_may_aug"] = np.nan

    # ECOSTRESS / LST
    lst_paths = [p for p in feature_sources.lst_rasters if p.exists()]
    if lst_paths:
        lst_median, n_valid = sample_median_from_raster_stack(
            grid_gdf=city_features,
            raster_paths=lst_paths,
            resolution=resolution,
            resampling=Resampling.bilinear,
        )
        city_features["lst_median_may_aug"] = lst_median
        city_features["n_valid_ecostress_passes"] = pd.Series(n_valid, dtype="Int64")
        lst_stage_available = city_features["lst_median_may_aug"].notna().any()
    else:
        blocked_stages.append("ecostress_lst")
        city_features["lst_median_may_aug"] = np.nan
        city_features["n_valid_ecostress_passes"] = pd.Series(pd.array([pd.NA] * len(city_features), dtype="Int64"))
        lst_stage_available = False

    city_features = _finalize_city_feature_columns(city_features)

    city_features_unfiltered = city_features.copy()
    city_features_filtered = _apply_rule_filters(city_features, lst_stage_available=lst_stage_available)
    city_features_filtered = _assign_hotspot(city_features_filtered)
    city_features_filtered = _finalize_city_feature_columns(city_features_filtered)

    city_features_gpkg_path: Path | None = None
    city_features_parquet_path: Path | None = None
    intermediate_unfiltered_path: Path | None = None
    intermediate_filtered_path: Path | None = None

    if save_outputs:
        city_features_dir.mkdir(parents=True, exist_ok=True)
        (intermediate_dir / "city_features").mkdir(parents=True, exist_ok=True)

        intermediate_unfiltered_path = intermediate_dir / "city_features" / f"{stem}_features_unfiltered.parquet"
        intermediate_filtered_path = intermediate_dir / "city_features" / f"{stem}_features_filtered.parquet"
        city_features_gpkg_path = city_features_dir / f"{stem}_features.gpkg"
        city_features_parquet_path = city_features_dir / f"{stem}_features.parquet"

        city_features_unfiltered.drop(columns=["geometry"]).to_parquet(intermediate_unfiltered_path, index=False)
        city_features_filtered.drop(columns=["geometry"]).to_parquet(intermediate_filtered_path, index=False)
        city_features_filtered.to_file(city_features_gpkg_path, driver="GPKG")
        city_features_filtered.drop(columns=["geometry"]).to_parquet(city_features_parquet_path, index=False)

        logger.info("Saved city features GPKG: %s", city_features_gpkg_path)
        logger.info("Saved city features table: %s", city_features_parquet_path)

    return CityFeatureResult(
        city=city,
        n_rows=len(city_features_filtered),
        city_features_gpkg_path=city_features_gpkg_path,
        city_features_parquet_path=city_features_parquet_path,
        intermediate_unfiltered_path=intermediate_unfiltered_path,
        intermediate_filtered_path=intermediate_filtered_path,
        blocked_stages=sorted(set(blocked_stages)),
    )


def extract_features_for_all_cities(
    resolution: float = 30,
    save_outputs: bool = True,
    continue_on_error: bool = True,
    city_ids: list[int] | None = None,
    existing_grids_only: bool = False,
    max_cells: int | None = None,
    city_grids_dir: Path = CITY_GRIDS,
    city_features_dir: Path = CITY_FEATURES,
    intermediate_dir: Path = INTERMEDIATE,
) -> BatchFeatureResult:
    """Run feature assembly for all cities, optionally skipping cities missing grids."""
    cities = load_cities()
    if city_ids:
        cities = cities[cities["city_id"].isin(city_ids)].copy()

    rows: list[dict[str, object]] = []

    for _, city in cities.iterrows():
        cid = int(city["city_id"])
        cname = str(city["city_name"])
        logger.info("Extracting features for city_id=%s city=%s", cid, cname)

        if existing_grids_only:
            grid_path = _resolve_city_grid_path(city=city, resolution=resolution, city_grids_dir=city_grids_dir)
            if not grid_path.exists():
                rows.append(
                    {
                        "city_id": cid,
                        "city_name": cname,
                        "status": "skipped_missing_grid",
                        "n_rows": 0,
                        "city_features_parquet_path": "",
                        "blocked_stages": "grid_missing",
                        "error": "",
                    }
                )
                continue

        try:
            result = assemble_city_features(
                city_id=cid,
                resolution=resolution,
                save_outputs=save_outputs,
                max_cells=max_cells,
                city_grids_dir=city_grids_dir,
                city_features_dir=city_features_dir,
                intermediate_dir=intermediate_dir,
            )
            rows.append(
                {
                    "city_id": cid,
                    "city_name": cname,
                    "status": "ok",
                    "n_rows": result.n_rows,
                    "city_features_parquet_path": str(result.city_features_parquet_path) if result.city_features_parquet_path else "",
                    "blocked_stages": ";".join(result.blocked_stages),
                    "error": "",
                }
            )
        except Exception as exc:  # pragma: no cover - exercised via integration/manual runs
            logger.exception("Feature extraction failed for city_id=%s", cid)
            rows.append(
                {
                    "city_id": cid,
                    "city_name": cname,
                    "status": "error",
                    "n_rows": 0,
                    "city_features_parquet_path": "",
                    "blocked_stages": "",
                    "error": str(exc),
                }
            )
            if not continue_on_error:
                raise

    summary = pd.DataFrame(rows)
    summary_path = city_features_dir / f"feature_extraction_summary_{int(resolution)}m.csv"
    if save_outputs:
        city_features_dir.mkdir(parents=True, exist_ok=True)
        summary.to_csv(summary_path, index=False)

    return BatchFeatureResult(summary=summary, summary_path=summary_path)


def _enforce_final_drop_rules(final_df: pd.DataFrame) -> pd.DataFrame:
    """Apply final row-drop rules to keep the merged output consistent."""
    out = final_df.copy()

    if "land_cover_class" in out.columns and out["land_cover_class"].notna().any():
        out = out[out["land_cover_class"] != OPEN_WATER_CLASS].copy()

    if "lst_median_may_aug" in out.columns and "n_valid_ecostress_passes" in out.columns:
        pass_count = out["n_valid_ecostress_passes"].fillna(0)
        keep = out["lst_median_may_aug"].isna() | (pass_count >= 3)
        out = out[keep].copy()

    return out


def assemble_final_dataset(
    city_features_dir: Path = CITY_FEATURES,
    final_dir: Path = FINAL,
) -> FinalDatasetResult:
    """Merge per-city feature tables and write final parquet/csv outputs."""
    tables = sorted(city_features_dir.glob("*_features.parquet"))
    if len(tables) == 0:
        raise FileNotFoundError(f"No per-city feature parquet files found in {city_features_dir}")

    frames = [pd.read_parquet(path) for path in tables]
    final_df = pd.concat(frames, ignore_index=True)

    for column in FINAL_COLUMNS:
        if column not in final_df.columns:
            final_df[column] = np.nan

    final_df = _enforce_final_drop_rules(final_df)

    final_df["hotspot_10pct"] = pd.Series(pd.array([pd.NA] * len(final_df), dtype="boolean"))
    for city_id, city_rows in final_df.groupby("city_id"):
        valid = city_rows["lst_median_may_aug"].dropna()
        if valid.empty:
            continue
        threshold = float(valid.quantile(0.9))
        mask = (final_df["city_id"] == city_id) & final_df["lst_median_may_aug"].notna()
        final_df.loc[mask, "hotspot_10pct"] = (final_df.loc[mask, "lst_median_may_aug"] >= threshold).astype("boolean")

    if "land_cover_class" in final_df.columns:
        final_df["land_cover_class"] = pd.Series(final_df["land_cover_class"]).astype("Int64")
    if "n_valid_ecostress_passes" in final_df.columns:
        final_df["n_valid_ecostress_passes"] = pd.Series(final_df["n_valid_ecostress_passes"]).astype("Int64")

    final_df = final_df[FINAL_COLUMNS]

    final_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = final_dir / "final_dataset.parquet"
    csv_path = final_dir / "final_dataset.csv"
    final_df.to_parquet(parquet_path, index=False)
    final_df.to_csv(csv_path, index=False)

    logger.info("Saved final parquet: %s", parquet_path)
    logger.info("Saved final csv: %s", csv_path)
    return FinalDatasetResult(final_df=final_df, parquet_path=parquet_path, csv_path=csv_path)

