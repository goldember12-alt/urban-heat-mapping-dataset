from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
from rasterio.features import rasterize
from scipy.ndimage import distance_transform_edt

from src.raster_features import (
    GridAlignmentSpec,
    build_grid_alignment_spec,
    extract_grid_values_from_aligned_array,
    save_aligned_raster,
)


def rasterize_water_mask(
    grid_gdf: gpd.GeoDataFrame,
    hydro_path: Path,
    resolution: float | None = None,
) -> tuple[np.ndarray, GridAlignmentSpec]:
    """Rasterize hydrography geometries to the city master-grid template."""
    if grid_gdf.crs is None or not grid_gdf.crs.is_projected:
        raise ValueError("grid_gdf must have a projected CRS")
    if not hydro_path.exists():
        raise FileNotFoundError(f"Hydro source file not found: {hydro_path}")

    spec = build_grid_alignment_spec(grid_gdf=grid_gdf, resolution=resolution)

    hydro = gpd.read_file(hydro_path)
    if hydro.empty:
        return np.zeros((spec.height, spec.width), dtype=np.uint8), spec

    hydro = hydro.to_crs(grid_gdf.crs)
    hydro = hydro[hydro.geometry.notna() & ~hydro.geometry.is_empty].copy()
    if hydro.empty:
        return np.zeros((spec.height, spec.width), dtype=np.uint8), spec

    water_mask = rasterize(
        [(geom, 1) for geom in hydro.geometry],
        out_shape=(spec.height, spec.width),
        transform=spec.transform,
        fill=0,
        all_touched=True,
        dtype=np.uint8,
    )
    return water_mask, spec


def compute_distance_to_water_array(
    water_mask: np.ndarray,
    resolution: float,
) -> np.ndarray:
    """Compute Euclidean distance-to-water raster (meters) from a binary water mask."""
    if water_mask.ndim != 2:
        raise ValueError("water_mask must be a 2D array")
    if resolution <= 0:
        raise ValueError("resolution must be positive")

    if not np.any(water_mask):
        return np.full(water_mask.shape, np.nan, dtype=np.float32)

    distance_cells = distance_transform_edt(water_mask == 0)
    distance_m = (distance_cells * float(resolution)).astype(np.float32)
    return distance_m


def compute_dist_to_water_m(
    grid_gdf: gpd.GeoDataFrame,
    hydro_path: Path,
    resolution: float | None = None,
    distance_raster_output_path: Path | None = None,
) -> np.ndarray:
    """Compute per-cell distance to nearest water geometry in meters."""
    water_mask, spec = rasterize_water_mask(
        grid_gdf=grid_gdf,
        hydro_path=hydro_path,
        resolution=resolution,
    )

    distance_raster = compute_distance_to_water_array(
        water_mask=water_mask,
        resolution=spec.resolution,
    )
    if distance_raster_output_path is not None:
        save_aligned_raster(
            aligned_array=distance_raster,
            output_path=distance_raster_output_path,
            spec=spec,
            nodata_value=np.nan,
        )

    values = extract_grid_values_from_aligned_array(
        grid_gdf=grid_gdf,
        aligned_array=distance_raster,
        spec=spec,
    )
    return values
