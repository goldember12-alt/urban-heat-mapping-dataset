from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
import tempfile
from typing import Iterable
import warnings

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.transform import Affine, from_origin
from rasterio.warp import reproject

logger = logging.getLogger(__name__)
MEDIAN_STACK_CHUNK_SIZE = 100_000


@dataclass(frozen=True)
class GridAlignmentSpec:
    """Template raster specification that matches a city master grid."""

    crs: CRS
    transform: Affine
    width: int
    height: int
    resolution: float
    minx: float
    maxy: float

@dataclass(frozen=True)
class RasterNormalizationSpec:
    """Normalization rules applied to sampled raster values before aggregation."""

    scale_factor: float = 1.0
    add_offset: float = 0.0
    valid_min: float | None = None
    valid_max: float | None = None

def discover_rasters(directory: Path, patterns: Iterable[str] | None = None) -> list[Path]:
    """Return sorted raster paths in a directory matching one or more glob patterns."""
    if not directory.exists():
        return []

    patterns = list(patterns) if patterns is not None else ["*.tif", "*.tiff"]
    seen: set[Path] = set()
    results: list[Path] = []
    for pattern in patterns:
        for path in sorted(directory.glob(pattern)):
            if path.is_file() and path not in seen:
                seen.add(path)
                results.append(path)
    return results


def _validate_raster_path(path: Path) -> str | None:
    """Return an error string when a raster cannot be safely sampled."""
    if not path.exists():
        return "file_missing"
    if not path.is_file():
        return "not_a_file"

    try:
        with rasterio.open(path) as src:
            if src.count < 1:
                return "no_bands"
            if src.width <= 0 or src.height <= 0:
                return "empty_dimensions"
            if src.crs is None:
                return "crs_missing"
    except Exception as exc:  # pragma: no cover - exercised via callers/tests using invalid files
        return f"{type(exc).__name__}: {exc}"

    return None


def filter_valid_raster_paths(
    raster_paths: Iterable[Path],
    *,
    stack_label: str = "raster stack",
) -> list[Path]:
    """Keep only readable raster files, warning on missing or invalid inputs."""
    valid_paths: list[Path] = []
    seen: set[Path] = set()

    for raw_path in raster_paths:
        path = Path(raw_path)
        if path in seen:
            continue
        seen.add(path)

        error = _validate_raster_path(path)
        if error is not None:
            logger.warning("Skipping invalid %s raster: %s (%s)", stack_label, path, error)
            continue

        valid_paths.append(path)

    return valid_paths


def choose_city_or_global_files(
    files: list[Path],
    city_name: str,
    city_id: int,
) -> list[Path]:
    """Prefer files that appear city-specific; fallback to full file list."""
    if not files:
        return []

    city_slug = city_name.strip().lower().replace(" ", "_")
    id_token = f"{city_id:02d}_"

    city_specific = [
        p
        for p in files
        if city_slug in p.name.lower()
        or f"_{city_id}_" in p.name.lower()
        or id_token in p.name.lower()
    ]
    return city_specific if city_specific else files


def infer_grid_resolution(grid_gdf: gpd.GeoDataFrame) -> float:
    """Infer square-cell resolution from polygon bounds in a grid layer."""
    if grid_gdf.empty:
        raise ValueError("grid_gdf is empty")

    geom = next((g for g in grid_gdf.geometry if g is not None and not g.is_empty), None)
    if geom is None:
        raise ValueError("grid_gdf has no non-empty geometry")

    minx, miny, maxx, maxy = geom.bounds
    res_x = float(maxx - minx)
    res_y = float(maxy - miny)
    if res_x <= 0 or res_y <= 0:
        raise ValueError("Unable to infer positive grid resolution from geometry bounds")
    if not np.isclose(res_x, res_y):
        raise ValueError("Grid cells must be square for alignment")
    return res_x


def build_grid_alignment_spec(
    grid_gdf: gpd.GeoDataFrame,
    resolution: float | None = None,
) -> GridAlignmentSpec:
    """Build a raster template spec aligned to the master grid extent and cell size."""
    if grid_gdf.empty:
        raise ValueError("grid_gdf is empty")
    if grid_gdf.crs is None:
        raise ValueError("grid_gdf must have a CRS")

    res = float(resolution) if resolution is not None else infer_grid_resolution(grid_gdf)
    if res <= 0:
        raise ValueError("resolution must be positive")

    minx, miny, maxx, maxy = map(float, grid_gdf.total_bounds)
    width = int(round((maxx - minx) / res))
    height = int(round((maxy - miny) / res))
    if width <= 0 or height <= 0:
        raise ValueError("Invalid grid extent for template raster construction")

    transform = from_origin(minx, maxy, res, res)
    return GridAlignmentSpec(
        crs=CRS.from_user_input(grid_gdf.crs),
        transform=transform,
        width=width,
        height=height,
        resolution=res,
        minx=minx,
        maxy=maxy,
    )


def grid_row_col_indices(
    grid_gdf: gpd.GeoDataFrame,
    spec: GridAlignmentSpec,
) -> tuple[np.ndarray, np.ndarray]:
    """Map each grid cell centroid to row/col indices in the aligned raster template."""
    centroids = grid_gdf.geometry.centroid
    xs = centroids.x.to_numpy(dtype=np.float64)
    ys = centroids.y.to_numpy(dtype=np.float64)

    cols = np.floor((xs - spec.minx) / spec.resolution).astype(np.int64)
    rows = np.floor((spec.maxy - ys) / spec.resolution).astype(np.int64)

    if (rows < 0).any() or (rows >= spec.height).any() or (cols < 0).any() or (cols >= spec.width).any():
        raise ValueError("Computed row/col indices fall outside aligned raster bounds")
    return rows, cols


def align_raster_to_grid(
    raster_path: Path,
    spec: GridAlignmentSpec,
    resampling: Resampling = Resampling.nearest,
) -> np.ndarray:
    """Reproject a source raster to the master-grid-aligned template."""
    with rasterio.open(raster_path) as src:
        if src.crs is None:
            raise ValueError(f"Raster has no CRS: {raster_path}")

        dst = np.full((spec.height, spec.width), np.nan, dtype=np.float32)
        reproject(
            source=rasterio.band(src, 1),
            destination=dst,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=src.nodata,
            dst_transform=spec.transform,
            dst_crs=spec.crs,
            dst_nodata=np.nan,
            resampling=resampling,
        )
        return dst


def extract_grid_values_from_aligned_array(
    grid_gdf: gpd.GeoDataFrame,
    aligned_array: np.ndarray,
    spec: GridAlignmentSpec,
) -> np.ndarray:
    """Extract per-cell values from an aligned raster array using grid centroid indexing."""
    rows, cols = grid_row_col_indices(grid_gdf=grid_gdf, spec=spec)
    values = aligned_array[rows, cols].astype(np.float64, copy=False)
    return values


def save_aligned_raster(
    aligned_array: np.ndarray,
    output_path: Path,
    spec: GridAlignmentSpec,
    nodata_value: float = np.nan,
) -> Path:
    """Write an aligned single-band raster to GeoTIFF."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff",
        "height": spec.height,
        "width": spec.width,
        "count": 1,
        "dtype": str(aligned_array.dtype),
        "crs": spec.crs,
        "transform": spec.transform,
        "nodata": nodata_value,
        "compress": "LZW",
    }
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(aligned_array, 1)
    return output_path


def align_and_extract_raster_values(
    grid_gdf: gpd.GeoDataFrame,
    raster_path: Path,
    resolution: float | None = None,
    resampling: Resampling = Resampling.nearest,
    aligned_output_path: Path | None = None,
) -> np.ndarray:
    """Align a raster to the master grid and extract one value per grid cell."""
    spec = build_grid_alignment_spec(grid_gdf=grid_gdf, resolution=resolution)
    aligned = align_raster_to_grid(raster_path=raster_path, spec=spec, resampling=resampling)
    if aligned_output_path is not None:
        save_aligned_raster(aligned_array=aligned, output_path=aligned_output_path, spec=spec)
    return extract_grid_values_from_aligned_array(grid_gdf=grid_gdf, aligned_array=aligned, spec=spec)


def _centroid_points(grid_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if grid_gdf.empty:
        return gpd.GeoDataFrame({"geometry": []}, crs=grid_gdf.crs)

    centroids = gpd.GeoDataFrame(geometry=grid_gdf.geometry.centroid, crs=grid_gdf.crs)
    return centroids


def sample_raster_at_points(points_gdf: gpd.GeoDataFrame, raster_path: Path) -> np.ndarray:
    """Sample a raster at point locations and return float values with nodata mapped to NaN."""
    if points_gdf.crs is None:
        raise ValueError("points_gdf must have a CRS")

    with rasterio.open(raster_path) as src:
        if src.crs is None:
            raise ValueError(f"Raster has no CRS: {raster_path}")

        points = points_gdf.to_crs(src.crs)
        coords = [(geom.x, geom.y) for geom in points.geometry]
        values = np.array([x[0] for x in src.sample(coords)], dtype=np.float64)

        if src.nodata is not None:
            nodata = float(src.nodata)
            values[np.isclose(values, nodata)] = np.nan

        return values


def sample_raster_to_grid_centroids(grid_gdf: gpd.GeoDataFrame, raster_path: Path) -> np.ndarray:
    """Sample a raster at grid-cell centroid locations."""
    points = _centroid_points(grid_gdf)
    if points.empty:
        return np.array([], dtype=np.float64)
    return sample_raster_at_points(points, raster_path)


def _apply_normalization(
    values: np.ndarray,
    normalization: RasterNormalizationSpec | None,
) -> np.ndarray:
    """Apply optional scale/offset and valid-range masking to sampled values."""
    if normalization is None:
        return values

    if normalization.scale_factor != 1.0 or normalization.add_offset != 0.0:
        values = (values * float(normalization.scale_factor)) + float(normalization.add_offset)
    if normalization.valid_min is not None:
        values = np.where(values < float(normalization.valid_min), np.nan, values)
    if normalization.valid_max is not None:
        values = np.where(values > float(normalization.valid_max), np.nan, values)
    return values


def _reduce_stack_median_in_chunks(
    stack: np.memmap,
    chunk_size: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute per-cell nanmedian and valid-counts without loading the full stack into memory."""
    n_cells = int(stack.shape[1])
    median = np.full(n_cells, np.nan, dtype=np.float64)
    n_valid = np.zeros(n_cells, dtype=np.int64)

    for start in range(0, n_cells, chunk_size):
        end = min(start + chunk_size, n_cells)
        chunk = np.asarray(stack[:, start:end], dtype=np.float64)
        with np.errstate(invalid="ignore"):
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="All-NaN slice encountered", category=RuntimeWarning)
                median[start:end] = np.nanmedian(chunk, axis=0)
        n_valid[start:end] = np.sum(~np.isnan(chunk), axis=0).astype(np.int64)

    return median, n_valid


def sample_median_from_raster_stack(
    grid_gdf: gpd.GeoDataFrame,
    raster_paths: list[Path],
    resolution: float | None = None,
    resampling: Resampling = Resampling.nearest,
    normalization: RasterNormalizationSpec | None = None,
    stack_label: str = "raster stack",
) -> tuple[np.ndarray, np.ndarray]:
    """Align/sample raster stack to grid cells and return median and valid-count arrays."""
    n = len(grid_gdf)
    if n == 0:
        return np.array([], dtype=np.float64), np.array([], dtype=np.int64)

    valid_paths = filter_valid_raster_paths(raster_paths, stack_label=stack_label)
    if len(valid_paths) == 0:
        return np.full(n, np.nan, dtype=np.float64), np.zeros(n, dtype=np.int64)

    spec = build_grid_alignment_spec(grid_gdf=grid_gdf, resolution=resolution)
    rows, cols = grid_row_col_indices(grid_gdf=grid_gdf, spec=spec)

    with tempfile.TemporaryDirectory(prefix="median_stack_") as temp_dir:
        stack_path = Path(temp_dir) / "stack.dat"
        stack = np.memmap(
            stack_path,
            mode="w+",
            dtype=np.float64,
            shape=(len(valid_paths), n),
        )
        try:
            used_count = 0
            for path in valid_paths:
                try:
                    aligned = align_raster_to_grid(path, spec=spec, resampling=resampling)
                except Exception as exc:  # pragma: no cover - defensive fallback
                    logger.warning("Skipping unreadable %s raster during sampling: %s (%s)", stack_label, path, exc)
                    continue

                values = aligned[rows, cols].astype(np.float64, copy=False)
                stack[used_count, :] = _apply_normalization(values, normalization)
                used_count += 1

            if used_count == 0:
                return np.full(n, np.nan, dtype=np.float64), np.zeros(n, dtype=np.int64)

            stack.flush()
            median, n_valid = _reduce_stack_median_in_chunks(
                stack=stack[:used_count, :],
                chunk_size=MEDIAN_STACK_CHUNK_SIZE,
            )
        finally:
            del stack

    return median, n_valid


def raster_exists(path: Path | None) -> bool:
    return path is not None and path.exists() and path.is_file()


def first_existing(paths: Iterable[Path | None]) -> Path | None:
    """Return first existing file path from a candidate list."""
    for path in paths:
        if raster_exists(path):
            return path
    return None


