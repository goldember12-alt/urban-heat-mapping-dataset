from __future__ import annotations

from math import ceil, floor
from typing import Literal

import geopandas as gpd
import numpy as np
from rasterio.features import rasterize
from rasterio.transform import from_origin

try:
    from shapely import box as vectorized_box
    from shapely import points as vectorized_points
except ImportError:  # pragma: no cover - fallback for older shapely
    from shapely.geometry import Point, box

    def vectorized_box(x0: np.ndarray, y0: np.ndarray, x1: np.ndarray, y1: np.ndarray):
        return [box(a, b, c, d) for a, b, c, d in zip(x0, y0, x1, y1)]

    def vectorized_points(x: np.ndarray, y: np.ndarray):
        return [Point(a, b) for a, b in zip(x, y)]


GridGeometryMode = Literal["polygon", "bbox", "centroid"]


def _snap_bounds_to_resolution(
    bounds: tuple[float, float, float, float],
    resolution: float,
) -> tuple[float, float, float, float]:
    """Snap bounds outward so cells align exactly to the target resolution."""
    minx, miny, maxx, maxy = bounds
    snapped_minx = floor(minx / resolution) * resolution
    snapped_miny = floor(miny / resolution) * resolution
    snapped_maxx = ceil(maxx / resolution) * resolution
    snapped_maxy = ceil(maxy / resolution) * resolution
    return snapped_minx, snapped_miny, snapped_maxx, snapped_maxy


def create_grid_from_polygon(
    study_area_gdf: gpd.GeoDataFrame,
    resolution: float = 30,
    return_geometry: GridGeometryMode = "polygon",
) -> gpd.GeoDataFrame:
    """Create a square grid of cells intersecting the study area.

    The input must already be in a projected CRS with meter units.
    This implementation avoids expensive full-grid geopandas overlay by:
    1) rasterizing the study polygon to the target grid, then
    2) building geometries only for touched cells.

    Notes
    -----
    Plotting full 30 m grids for large cities (for example Phoenix) can be
    expensive. Use ``return_geometry=\"centroid\"`` for faster visual debugging.
    """
    if study_area_gdf.empty:
        raise ValueError("study_area_gdf is empty")
    if study_area_gdf.crs is None or not study_area_gdf.crs.is_projected:
        raise ValueError("study_area_gdf must have a projected CRS")
    if resolution <= 0:
        raise ValueError("resolution must be positive")
    if return_geometry not in {"polygon", "bbox", "centroid"}:
        raise ValueError("return_geometry must be one of: 'polygon', 'bbox', 'centroid'")

    study_geom = study_area_gdf.geometry.union_all()
    if study_geom.is_empty:
        raise ValueError("study_area_gdf has empty geometry")

    minx, miny, maxx, maxy = _snap_bounds_to_resolution(study_geom.bounds, resolution)
    width = int(round((maxx - minx) / resolution))
    height = int(round((maxy - miny) / resolution))

    if width <= 0 or height <= 0:
        raise ValueError("study_area_gdf geometry bounds are invalid for grid creation")

    transform = from_origin(minx, maxy, resolution, resolution)
    mask = rasterize(
        [(study_geom, 1)],
        out_shape=(height, width),
        transform=transform,
        fill=0,
        all_touched=True,
        dtype=np.uint8,
    )

    rows, cols = np.nonzero(mask)
    if len(rows) == 0:
        return gpd.GeoDataFrame({"cell_id": [], "geometry": []}, crs=study_area_gdf.crs)

    x0 = minx + (cols.astype(np.float64) * resolution)
    y1 = maxy - (rows.astype(np.float64) * resolution)
    x1 = x0 + resolution
    y0 = y1 - resolution

    if return_geometry == "centroid":
        geometry = vectorized_points(x0 + (resolution / 2.0), y0 + (resolution / 2.0))
    else:
        geometry = vectorized_box(x0, y0, x1, y1)

    grid = gpd.GeoDataFrame(
        {
            "cell_id": np.arange(1, len(rows) + 1, dtype=np.int64),
            "geometry": geometry,
        },
        crs=study_area_gdf.crs,
    )
    return grid
