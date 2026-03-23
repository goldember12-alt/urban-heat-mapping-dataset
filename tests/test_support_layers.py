import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import LineString, box

import src.feature_assembly as feature_assembly
from src.city_processing import city_output_paths
from src.load_cities import load_cities
from src.support_layers import (
    audit_support_layer_readiness,
    discover_city_raw_support_sources,
    discover_prepared_support_sources,
    expected_support_layer_prepared_paths,
    expected_support_layer_raw_paths,
    prepare_support_layers,
)


def _write_city_study_area(city: pd.Series, study_area_path: Path) -> None:
    study_area = gpd.GeoDataFrame(
        {
            "city_id": [int(city["city_id"])],
            "city_name": [str(city["city_name"])],
            "state": [str(city["state"])],
            "climate_group": [str(city["climate_group"])],
            "buffer_m": [2000.0],
        },
        geometry=[box(30, 30, 180, 180)],
        crs="EPSG:3857",
    )
    study_area_path.parent.mkdir(parents=True, exist_ok=True)
    study_area.to_file(study_area_path, driver="GPKG")


def _write_city_grid(city: pd.Series, grid_path: Path) -> None:
    grid = gpd.GeoDataFrame(
        {"cell_id": [1]},
        geometry=[box(30, 150, 60, 180)],
        crs="EPSG:3857",
    )
    grid_path.parent.mkdir(parents=True, exist_ok=True)
    grid.to_file(grid_path, driver="GPKG")


def _write_raster(path: Path, values: np.ndarray, dtype: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=values.shape[0],
        width=values.shape[1],
        count=1,
        dtype=dtype,
        crs="EPSG:3857",
        transform=from_origin(0, 300, 30, 30),
        nodata=0,
    ) as dst:
        dst.write(values, 1)


def _write_hydro(path: Path, *, with_z: bool = False) -> None:
    geometry = LineString([(45, 45, 5), (165, 165, 9)]) if with_z else LineString([(45, 45), (165, 165)])
    hydro = gpd.GeoDataFrame(
        {"name": ["canal"]},
        geometry=[geometry],
        crs="EPSG:3857",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    hydro.to_file(path, driver="GPKG")


def test_audit_support_layer_readiness_uses_all_cities_when_city_ids_omitted(tmp_path: Path):
    cities = load_cities()
    result = audit_support_layer_readiness(
        study_areas_dir=tmp_path / "study_areas",
        city_grids_dir=tmp_path / "city_grids",
        raw_dem_dir=tmp_path / "raw" / "dem",
        raw_nlcd_dir=tmp_path / "raw" / "nlcd",
        raw_hydro_dir=tmp_path / "raw" / "hydro",
        support_layers_dir=tmp_path / "support_layers",
    )

    assert len(result.summary) == len(cities) == 30
    first = result.summary.iloc[0]
    assert first["city_slug"] == "phoenix"
    assert bool(first["support_prep_ready"]) is False
    assert bool(first["feature_extraction_ready"]) is False
    assert "study_area_missing" in str(first["blocking_reasons"])
    assert result.summary_json_path.exists()
    assert result.summary_csv_path.exists()


def test_audit_support_layer_readiness_reports_expected_paths_and_missing_inputs(tmp_path: Path):
    result = audit_support_layer_readiness(
        city_ids=[1],
        study_areas_dir=tmp_path / "study_areas",
        city_grids_dir=tmp_path / "city_grids",
        raw_dem_dir=tmp_path / "raw" / "dem",
        raw_nlcd_dir=tmp_path / "raw" / "nlcd",
        raw_hydro_dir=tmp_path / "raw" / "hydro",
        support_layers_dir=tmp_path / "support_layers",
    )

    row = result.summary.iloc[0]
    assert row["expected_dem_raw_path"] == str(tmp_path / "raw" / "dem" / "phoenix" / "phoenix_dem_3dep_30m.tif")
    assert row["expected_nlcd_land_cover_raw_path"] == str(
        tmp_path / "raw" / "nlcd" / "phoenix" / "phoenix_nlcd_2021_land_cover_30m.tif"
    )
    assert row["expected_nlcd_impervious_raw_path"] == str(
        tmp_path / "raw" / "nlcd" / "phoenix" / "phoenix_nlcd_2021_impervious_30m.tif"
    )
    assert row["expected_hydro_raw_path"] == str(tmp_path / "raw" / "hydro" / "phoenix" / "phoenix_nhdplus_water.gpkg")
    assert bool(row["required_inputs_exist"]) is False
    assert bool(row["support_prep_ready"]) is False
    assert bool(row["feature_extraction_ready"]) is False
    assert row["prep_blocking_reasons"] == (
        "study_area_missing;dem_source_missing;nlcd_land_cover_source_missing;"
        "nlcd_impervious_source_missing;hydro_source_missing"
    )

    with result.summary_json_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    assert payload["records"][0]["city_id"] == 1


def test_discover_city_raw_support_sources_uses_recursive_city_folders(tmp_path: Path):
    city = load_cities().iloc[0]
    expected_raw = expected_support_layer_raw_paths(
        city,
        raw_dem_dir=tmp_path / "raw" / "dem",
        raw_nlcd_dir=tmp_path / "raw" / "nlcd",
        raw_hydro_dir=tmp_path / "raw" / "hydro",
    )

    dem_path = expected_raw.dem_raster.parent / "nested" / "phoenix_dem_3dep_30m.tif"
    land_cover_path = expected_raw.nlcd_land_cover_raster.parent / "nested" / "phoenix_nlcd_2021_land_cover_30m.tif"
    impervious_path = expected_raw.nlcd_impervious_raster.parent / "nested" / "phoenix_nlcd_2021_impervious_30m.tif"
    hydro_path = expected_raw.hydro_vector.parent / "nested" / "phoenix_nhdplus_water.gpkg"

    for path in [dem_path, land_cover_path, impervious_path]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x")
    hydro_path.parent.mkdir(parents=True, exist_ok=True)
    hydro_path.write_text("x")

    discovered = discover_city_raw_support_sources(
        city,
        raw_dem_dir=tmp_path / "raw" / "dem",
        raw_nlcd_dir=tmp_path / "raw" / "nlcd",
        raw_hydro_dir=tmp_path / "raw" / "hydro",
    )

    assert discovered.dem_raster == dem_path
    assert discovered.nlcd_land_cover_raster == land_cover_path
    assert discovered.nlcd_impervious_raster == impervious_path
    assert discovered.hydro_vector == hydro_path


def test_prepare_support_layers_writes_prepared_outputs_and_updates_readiness(tmp_path: Path):
    city = load_cities().iloc[0]
    study_area_path, grid_path = city_output_paths(
        city,
        resolution=30,
        study_areas_dir=tmp_path / "study_areas",
        city_grids_dir=tmp_path / "city_grids",
    )
    _write_city_study_area(city, study_area_path)
    _write_city_grid(city, grid_path)

    expected_raw = expected_support_layer_raw_paths(
        city,
        raw_dem_dir=tmp_path / "raw" / "dem",
        raw_nlcd_dir=tmp_path / "raw" / "nlcd",
        raw_hydro_dir=tmp_path / "raw" / "hydro",
    )
    _write_raster(expected_raw.dem_raster, np.arange(100, dtype=np.float32).reshape(10, 10), "float32")
    _write_raster(expected_raw.nlcd_land_cover_raster, np.full((10, 10), 21, dtype=np.uint8), "uint8")
    _write_raster(expected_raw.nlcd_impervious_raster, np.full((10, 10), 35, dtype=np.uint8), "uint8")
    _write_hydro(expected_raw.hydro_vector)

    result = prepare_support_layers(
        city_ids=[1],
        study_areas_dir=tmp_path / "study_areas",
        city_grids_dir=tmp_path / "city_grids",
        raw_dem_dir=tmp_path / "raw" / "dem",
        raw_nlcd_dir=tmp_path / "raw" / "nlcd",
        raw_hydro_dir=tmp_path / "raw" / "hydro",
        support_layers_dir=tmp_path / "support_layers",
    )

    row = result.summary.iloc[0]
    assert row["status"] == "completed"

    prepared = expected_support_layer_prepared_paths(city, support_layers_dir=tmp_path / "support_layers")
    assert prepared.dem_raster.exists()
    assert prepared.nlcd_land_cover_raster.exists()
    assert prepared.nlcd_impervious_raster.exists()
    assert prepared.hydro_vector.exists()

    with rasterio.open(expected_raw.dem_raster) as src:
        source_shape = (src.height, src.width)
    with rasterio.open(prepared.dem_raster) as src:
        prepared_shape = (src.height, src.width)
    assert prepared_shape[0] <= source_shape[0]
    assert prepared_shape[1] <= source_shape[1]

    audit = audit_support_layer_readiness(
        city_ids=[1],
        study_areas_dir=tmp_path / "study_areas",
        city_grids_dir=tmp_path / "city_grids",
        raw_dem_dir=tmp_path / "raw" / "dem",
        raw_nlcd_dir=tmp_path / "raw" / "nlcd",
        raw_hydro_dir=tmp_path / "raw" / "hydro",
        support_layers_dir=tmp_path / "support_layers",
        write_outputs=False,
    )
    audit_row = audit.summary.iloc[0]
    assert bool(audit_row["support_prep_ready"]) is True
    assert bool(audit_row["feature_extraction_ready"]) is True
    assert bool(audit_row["dem_prepared_exists"]) is True
    assert bool(audit_row["hydro_prepared_exists"]) is True


def test_discover_prepared_support_sources_and_feature_assembly_prefer_prepared_outputs(tmp_path: Path, monkeypatch):
    city = load_cities().iloc[0]
    prepared = expected_support_layer_prepared_paths(city, support_layers_dir=tmp_path / "support_layers")
    for path in [prepared.dem_raster, prepared.nlcd_land_cover_raster, prepared.nlcd_impervious_raster, prepared.hydro_vector]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x")

    discovered = discover_prepared_support_sources(city, support_layers_dir=tmp_path / "support_layers")
    assert discovered.dem_raster == prepared.dem_raster
    assert discovered.nlcd_land_cover_raster == prepared.nlcd_land_cover_raster
    assert discovered.nlcd_impervious_raster == prepared.nlcd_impervious_raster
    assert discovered.hydro_vector == prepared.hydro_vector

    monkeypatch.setattr(feature_assembly, "SUPPORT_LAYERS", tmp_path / "support_layers")
    monkeypatch.setattr(feature_assembly, "RAW_DEM", tmp_path / "raw" / "dem")
    monkeypatch.setattr(feature_assembly, "RAW_NLCD", tmp_path / "raw" / "nlcd")
    monkeypatch.setattr(feature_assembly, "RAW_HYDRO", tmp_path / "raw" / "hydro")
    monkeypatch.setattr(feature_assembly, "RAW_NDVI", tmp_path / "raw" / "ndvi")
    monkeypatch.setattr(feature_assembly, "RAW_ECOSTRESS", tmp_path / "raw" / "ecostress")

    sources = feature_assembly.discover_default_feature_sources(city)
    assert sources.dem_raster == prepared.dem_raster
    assert sources.nlcd_land_cover_raster == prepared.nlcd_land_cover_raster
    assert sources.nlcd_impervious_raster == prepared.nlcd_impervious_raster
    assert sources.hydro_vector == prepared.hydro_vector


def test_prepare_support_layers_normalizes_hydro_to_2d(tmp_path: Path):
    city = load_cities().iloc[0]
    study_area_path, grid_path = city_output_paths(
        city,
        resolution=30,
        study_areas_dir=tmp_path / "study_areas",
        city_grids_dir=tmp_path / "city_grids",
    )
    _write_city_study_area(city, study_area_path)
    _write_city_grid(city, grid_path)

    expected_raw = expected_support_layer_raw_paths(
        city,
        raw_dem_dir=tmp_path / "raw" / "dem",
        raw_nlcd_dir=tmp_path / "raw" / "nlcd",
        raw_hydro_dir=tmp_path / "raw" / "hydro",
    )
    _write_raster(expected_raw.dem_raster, np.arange(100, dtype=np.float32).reshape(10, 10), "float32")
    _write_raster(expected_raw.nlcd_land_cover_raster, np.full((10, 10), 21, dtype=np.uint8), "uint8")
    _write_raster(expected_raw.nlcd_impervious_raster, np.full((10, 10), 35, dtype=np.uint8), "uint8")
    _write_hydro(expected_raw.hydro_vector, with_z=True)

    prepare_support_layers(
        city_ids=[1],
        study_areas_dir=tmp_path / "study_areas",
        city_grids_dir=tmp_path / "city_grids",
        raw_dem_dir=tmp_path / "raw" / "dem",
        raw_nlcd_dir=tmp_path / "raw" / "nlcd",
        raw_hydro_dir=tmp_path / "raw" / "hydro",
        support_layers_dir=tmp_path / "support_layers",
    )

    prepared = expected_support_layer_prepared_paths(city, support_layers_dir=tmp_path / "support_layers")
    hydro = gpd.read_file(prepared.hydro_vector)
    assert bool(hydro.geometry.iloc[0].has_z) is False
