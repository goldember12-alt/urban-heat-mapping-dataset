import geopandas as gpd
import pytest
from shapely.geometry import Polygon

from src.grid import create_grid_from_polygon


def test_create_grid_from_polygon_returns_cells():
    poly = Polygon([(0, 0), (90, 0), (90, 90), (0, 90)])
    gdf = gpd.GeoDataFrame({"name": ["study"]}, geometry=[poly], crs="EPSG:32612")

    grid = create_grid_from_polygon(gdf, resolution=30)
    assert len(grid) == 9
    assert list(grid.columns) == ["cell_id", "geometry"]
    assert grid.crs == gdf.crs


def test_create_grid_from_polygon_only_returns_intersections():
    poly = Polygon([(0, 0), (90, 0), (0, 90)])
    gdf = gpd.GeoDataFrame({"name": ["study"]}, geometry=[poly], crs="EPSG:32612")

    grid = create_grid_from_polygon(gdf, resolution=30)
    study_geom = gdf.geometry.union_all()

    assert len(grid) > 0
    assert len(grid) < 9
    assert grid.geometry.intersects(study_geom).all()


def test_create_grid_from_polygon_requires_projected_crs():
    poly = Polygon([(-112.08, 33.44), (-112.07, 33.44), (-112.07, 33.45), (-112.08, 33.45)])
    gdf = gpd.GeoDataFrame({"name": ["study"]}, geometry=[poly], crs="EPSG:4326")

    with pytest.raises(ValueError, match="projected CRS"):
        create_grid_from_polygon(gdf, resolution=30)


def test_create_grid_from_polygon_supports_centroid_debug_mode():
    poly = Polygon([(0, 0), (90, 0), (90, 90), (0, 90)])
    gdf = gpd.GeoDataFrame({"name": ["study"]}, geometry=[poly], crs="EPSG:32612")

    poly_grid = create_grid_from_polygon(gdf, resolution=30)
    centroid_grid = create_grid_from_polygon(gdf, resolution=30, return_geometry="centroid")

    assert len(centroid_grid) == len(poly_grid)
    assert centroid_grid.geometry.geom_type.eq("Point").all()


def test_create_grid_from_polygon_rejects_invalid_geometry_mode():
    poly = Polygon([(0, 0), (90, 0), (90, 90), (0, 90)])
    gdf = gpd.GeoDataFrame({"name": ["study"]}, geometry=[poly], crs="EPSG:32612")

    with pytest.raises(ValueError, match="return_geometry"):
        create_grid_from_polygon(gdf, resolution=30, return_geometry="invalid")


def test_create_grid_from_polygon_avoids_geopandas_overlay(monkeypatch):
    def fail_overlay(*args, **kwargs):
        raise AssertionError("geopandas.overlay should not be used for grid creation")

    monkeypatch.setattr(gpd, "overlay", fail_overlay)

    poly = Polygon([(0, 0), (90, 0), (90, 90), (0, 90)])
    gdf = gpd.GeoDataFrame({"name": ["study"]}, geometry=[poly], crs="EPSG:32612")

    grid = create_grid_from_polygon(gdf, resolution=30)
    assert len(grid) == 9
