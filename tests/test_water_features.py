from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import LineString, Polygon

from src.grid import create_grid_from_polygon
from src.water_features import compute_dist_to_water_m, compute_distance_to_water_array, rasterize_water_mask


def _build_test_grid() -> gpd.GeoDataFrame:
    polygon = Polygon([(0, 0), (60, 0), (60, 60), (0, 60)])
    study_area = gpd.GeoDataFrame({"name": ["study"]}, geometry=[polygon], crs="EPSG:32612")
    return create_grid_from_polygon(study_area, resolution=30)


def test_compute_distance_to_water_array_returns_nan_when_no_water():
    mask = np.zeros((2, 2), dtype=np.uint8)

    distances = compute_distance_to_water_array(mask, resolution=30)

    assert np.isnan(distances).all()


def test_rasterize_and_extract_distance_to_water(tmp_path: Path):
    grid = _build_test_grid()

    hydro = gpd.GeoDataFrame(
        {"name": ["channel"]},
        geometry=[LineString([(15, 0), (15, 60)])],
        crs="EPSG:32612",
    )
    hydro_path = tmp_path / "hydro.gpkg"
    hydro.to_file(hydro_path, driver="GPKG")

    water_mask, spec = rasterize_water_mask(grid_gdf=grid, hydro_path=hydro_path, resolution=30)
    dist_values = compute_dist_to_water_m(grid_gdf=grid, hydro_path=hydro_path, resolution=30)

    assert water_mask.shape == (spec.height, spec.width)
    assert np.array_equal(water_mask, np.array([[1, 0], [1, 0]], dtype=np.uint8))
    assert np.allclose(dist_values, np.array([0.0, 30.0, 0.0, 30.0]), equal_nan=True)
