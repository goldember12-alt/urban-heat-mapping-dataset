from __future__ import annotations

import logging
from pathlib import Path

import geopandas as gpd
from shapely import wkb as shapely_wkb

logger = logging.getLogger(__name__)


def _force_geometry_2d(geometry):
    if geometry is None or geometry.is_empty:
        return geometry
    try:
        return shapely_wkb.loads(shapely_wkb.dumps(geometry, output_dimension=2))
    except Exception:
        return geometry


def normalize_vector_geometry_dimensions(
    gdf: gpd.GeoDataFrame,
    *,
    context: str,
) -> gpd.GeoDataFrame:
    if gdf.empty:
        return gdf

    normalized = gdf.copy()
    changed = 0
    geometries = []
    for geometry in normalized.geometry:
        updated = _force_geometry_2d(geometry)
        if geometry is not None and updated is not None:
            try:
                if geometry.wkb != updated.wkb:
                    changed += 1
            except Exception:
                pass
        geometries.append(updated)

    normalized = normalized.set_geometry(gpd.GeoSeries(geometries, index=normalized.index, crs=normalized.crs))
    if changed:
        logger.info("Normalized %s geometries to 2D for %s", changed, context)
    return normalized


def gpkg_temp_path(output_path: Path) -> Path:
    return output_path.with_name(f"{output_path.stem}.tmp{output_path.suffix}")


def write_gpkg_atomic(
    gdf: gpd.GeoDataFrame,
    output_path: Path,
    *,
    layer: str | None = None,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = gpkg_temp_path(output_path)
    if temp_path.exists():
        temp_path.unlink()

    write_kwargs: dict[str, object] = {"driver": "GPKG"}
    if layer:
        write_kwargs["layer"] = layer
    gdf.to_file(temp_path, **write_kwargs)
    temp_path.replace(output_path)
    return output_path
