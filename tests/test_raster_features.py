from pathlib import Path
import logging

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_origin

import src.raster_features as raster_features
from shapely.geometry import Polygon

from src.grid import create_grid_from_polygon
from src.raster_features import (
    RasterNormalizationSpec,
    align_and_extract_raster_values,
    build_grid_alignment_spec,
    sample_median_from_raster_stack,
)

def _build_test_grid() -> gpd.GeoDataFrame:
    polygon = Polygon([(0, 0), (60, 0), (60, 60), (0, 60)])
    study_area = gpd.GeoDataFrame({"name": ["study"]}, geometry=[polygon], crs="EPSG:32612")
    return create_grid_from_polygon(study_area, resolution=30)


def _write_raster(path: Path, values: np.ndarray, nodata: float | None = None) -> Path:
    transform = from_origin(0, 60, 30, 30)
    profile = {
        "driver": "GTiff",
        "height": values.shape[0],
        "width": values.shape[1],
        "count": 1,
        "dtype": str(values.dtype),
        "crs": "EPSG:32612",
        "transform": transform,
        "nodata": nodata,
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(values, 1)
    return path


def test_build_grid_alignment_spec_matches_grid_extent():
    grid = _build_test_grid()

    spec = build_grid_alignment_spec(grid)

    assert spec.width == 2
    assert spec.height == 2
    assert spec.resolution == 30


def test_align_and_extract_raster_values_returns_cell_order_values(tmp_path: Path):
    grid = _build_test_grid()
    raster_path = _write_raster(tmp_path / "values.tif", np.array([[1, 2], [3, 4]], dtype=np.float32))

    values = align_and_extract_raster_values(grid_gdf=grid, raster_path=raster_path, resolution=30)

    assert np.allclose(values, np.array([1, 2, 3, 4], dtype=np.float64), equal_nan=True)


def test_sample_median_from_raster_stack_returns_median_and_valid_count(tmp_path: Path):
    grid = _build_test_grid()
    r1 = _write_raster(tmp_path / "r1.tif", np.array([[1, 2], [3, 4]], dtype=np.float32))
    r2 = _write_raster(tmp_path / "r2.tif", np.array([[1, -9999], [5, 7]], dtype=np.float32), nodata=-9999)

    median, n_valid = sample_median_from_raster_stack(
        grid_gdf=grid,
        raster_paths=[r1, r2],
        resolution=30,
    )

    assert np.allclose(median, np.array([1.0, 2.0, 4.0, 5.5]), equal_nan=True)
    assert np.array_equal(n_valid, np.array([2, 1, 2, 2]))


def test_sample_median_from_raster_stack_applies_normalization_and_valid_range(tmp_path: Path):
    grid = _build_test_grid()
    r1 = _write_raster(tmp_path / "r1.tif", np.array([[10000, -3000], [5000, 12000]], dtype=np.int16), nodata=-3000)
    r2 = _write_raster(tmp_path / "r2.tif", np.array([[8000, 0], [7000, 11000]], dtype=np.int16), nodata=-3000)

    normalization = RasterNormalizationSpec(
        scale_factor=0.0001,
        add_offset=0.0,
        valid_min=-0.2,
        valid_max=1.0,
    )

    median, n_valid = sample_median_from_raster_stack(
        grid_gdf=grid,
        raster_paths=[r1, r2],
        resolution=30,
        normalization=normalization,
    )

    # Cell order is top-left, top-right, bottom-left, bottom-right.
    assert np.allclose(median, np.array([0.9, 0.0, 0.6, np.nan]), equal_nan=True)
    assert np.array_equal(n_valid, np.array([2, 1, 2, 0]))


def test_sample_median_from_raster_stack_uses_chunked_reduction(tmp_path: Path, monkeypatch):
    grid = _build_test_grid()
    r1 = _write_raster(tmp_path / "r1.tif", np.array([[1, 4], [7, 10]], dtype=np.float32))
    r2 = _write_raster(tmp_path / "r2.tif", np.array([[2, 5], [8, 11]], dtype=np.float32))
    r3 = _write_raster(tmp_path / "r3.tif", np.array([[3, -9999], [9, 12]], dtype=np.float32), nodata=-9999)

    monkeypatch.setattr(raster_features, "MEDIAN_STACK_CHUNK_SIZE", 2)

    median, n_valid = sample_median_from_raster_stack(
        grid_gdf=grid,
        raster_paths=[r1, r2, r3],
        resolution=30,
    )

    assert np.allclose(median, np.array([2.0, 4.5, 8.0, 11.0]), equal_nan=True)
    assert np.array_equal(n_valid, np.array([3, 2, 3, 3]))


def test_sample_median_from_raster_stack_skips_invalid_tiffs_when_valid_rasters_remain(tmp_path: Path, caplog):
    grid = _build_test_grid()
    r1 = _write_raster(tmp_path / "valid_1.tif", np.array([[1, 2], [3, 4]], dtype=np.float32))
    r2 = _write_raster(tmp_path / "valid_2.tif", np.array([[5, 6], [7, 8]], dtype=np.float32))
    invalid = tmp_path / "ndvi_1.tif"
    invalid.write_bytes(b"x")

    with caplog.at_level(logging.WARNING):
        median, n_valid = sample_median_from_raster_stack(
            grid_gdf=grid,
            raster_paths=[invalid, r1, r2],
            resolution=30,
            stack_label="NDVI city_id=2 city_name=Tucson",
        )

    assert np.allclose(median, np.array([3.0, 4.0, 5.0, 6.0]), equal_nan=True)
    assert np.array_equal(n_valid, np.array([2, 2, 2, 2]))
    assert "Skipping invalid NDVI city_id=2 city_name=Tucson raster" in caplog.text

