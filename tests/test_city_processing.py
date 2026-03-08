from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Polygon

from src.boundaries import UrbanAreaQueryResult
from src.city_processing import (
    build_city_grid,
    build_city_study_area,
    city_output_paths,
    fetch_city_urban_area,
    load_city_record,
    process_city,
)


def _fake_urban_area_result(lon: float, lat: float) -> UrbanAreaQueryResult:
    poly = Polygon(
        [
            (lon - 0.01, lat - 0.01),
            (lon + 0.01, lat - 0.01),
            (lon + 0.01, lat + 0.01),
            (lon - 0.01, lat + 0.01),
        ]
    )
    gdf = gpd.GeoDataFrame({"NAME": ["Mock Urban Area"]}, geometry=[poly], crs="EPSG:4326")
    return UrbanAreaQueryResult(geoid="99999", name="Mock Urban Area", geodataframe=gdf)


def test_load_city_record_by_id_and_name_match_same_city():
    by_id = load_city_record(city_id=1)
    by_name = load_city_record(city_name="Phoenix")

    assert int(by_id["city_id"]) == 1
    assert by_id["city_name"] == "Phoenix"
    assert by_name["city_name"] == "Phoenix"


def test_load_city_record_requires_exactly_one_selector():
    with pytest.raises(ValueError, match="exactly one"):
        load_city_record()

    with pytest.raises(ValueError, match="exactly one"):
        load_city_record(city_name="Phoenix", city_id=1)


def test_fetch_city_urban_area_adds_city_metadata(monkeypatch):
    def fake_fetch_urban_area_for_point(lon: float, lat: float, timeout: int = 60):
        return _fake_urban_area_result(lon=lon, lat=lat)

    monkeypatch.setattr("src.city_processing.fetch_urban_area_for_point", fake_fetch_urban_area_for_point)

    city = load_city_record(city_name="Phoenix")
    urban = fetch_city_urban_area(city)

    assert urban.crs.to_string() == "EPSG:4326"
    assert int(urban.iloc[0]["city_id"]) == 1
    assert urban.iloc[0]["city_name"] == "Phoenix"
    assert urban.iloc[0]["urban_geoid"] == "99999"


def test_build_city_study_area_is_projected(monkeypatch):
    city = load_city_record(city_name="Phoenix")

    def fake_fetch_city_urban_area(city: pd.Series, timeout: int = 60) -> gpd.GeoDataFrame:
        return _fake_urban_area_result(float(city["lon"]), float(city["lat"])).geodataframe

    monkeypatch.setattr("src.city_processing.fetch_city_urban_area", fake_fetch_city_urban_area)

    study = build_city_study_area(city=city, buffer_m=2000)
    assert study.crs.is_projected
    assert float(study.iloc[0]["buffer_m"]) == 2000.0


def test_build_city_grid_preserves_projected_crs():
    poly = Polygon([(0, 0), (120, 0), (120, 120), (0, 120)])
    gdf = gpd.GeoDataFrame({"name": ["study"]}, geometry=[poly], crs="EPSG:32612")

    grid = build_city_grid(gdf, resolution=30)
    assert len(grid) == 16
    assert list(grid.columns) == ["cell_id", "geometry"]
    assert grid.crs == gdf.crs


def test_process_city_saves_outputs(monkeypatch, tmp_path: Path):
    def fake_fetch_urban_area_for_point(lon: float, lat: float, timeout: int = 60):
        return _fake_urban_area_result(lon=lon, lat=lat)

    monkeypatch.setattr("src.city_processing.fetch_urban_area_for_point", fake_fetch_urban_area_for_point)

    study_dir = tmp_path / "study_areas"
    grid_dir = tmp_path / "city_grids"

    result = process_city(
        city_name="Phoenix",
        buffer_m=500,
        resolution=250,
        save_outputs=True,
        study_areas_dir=study_dir,
        city_grids_dir=grid_dir,
    )

    assert result.study_area_path is not None and result.study_area_path.exists()
    assert result.grid_path is not None and result.grid_path.exists()
    assert result.study_area.crs.is_projected
    assert result.grid.crs == result.study_area.crs
    assert len(result.grid) > 0


def test_city_output_paths_include_expected_folders(tmp_path: Path):
    city = load_city_record(city_name="Salt Lake City")
    study_dir = tmp_path / "study_areas"
    grid_dir = tmp_path / "city_grids"

    study_path, grid_path = city_output_paths(
        city=city,
        resolution=30,
        study_areas_dir=study_dir,
        city_grids_dir=grid_dir,
    )

    assert "study_areas" in str(study_path)
    assert "city_grids" in str(grid_path)
    assert grid_path.name.endswith("_grid_30m.gpkg")
