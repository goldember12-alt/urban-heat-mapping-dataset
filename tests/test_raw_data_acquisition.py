import re
import zipfile
from pathlib import Path

import geopandas as gpd
from shapely.geometry import LineString, box

from src.city_processing import city_output_paths
from src.load_cities import load_cities
from src.raw_data_acquisition import (
    _dem_tile_key,
    _select_latest_products_by_key,
    _zip_member_name,
    collect_nhdplus_water_features,
    run_raw_data_acquisition,
)
from src.support_layers import expected_support_layer_raw_paths


def test_select_latest_products_by_key_prefers_newest_dem_tile_version():
    items = [
        {
            "title": "USGS 1 Arc Second n34w112 20210301",
            "downloadURL": "https://example.com/historical/n34w112/USGS_1_n34w112_20210301.tif",
            "publicationDate": "2021-03-01",
            "lastUpdated": "2021-03-02T00:00:00",
        },
        {
            "title": "USGS 1 Arc Second n34w112 20240402",
            "downloadURL": "https://example.com/historical/n34w112/USGS_1_n34w112_20240402.tif",
            "publicationDate": "2024-04-02",
            "lastUpdated": "2024-04-03T00:00:00",
        },
        {
            "title": "USGS 1 Arc Second n34w113 20241016",
            "downloadURL": "https://example.com/historical/n34w113/USGS_1_n34w113_20241016.tif",
            "publicationDate": "2024-10-16",
            "lastUpdated": "2024-10-17T00:00:00",
        },
    ]

    selected = _select_latest_products_by_key(items, key_parser=_dem_tile_key)

    assert len(selected) == 2
    assert selected[0]["downloadURL"].endswith("USGS_1_n34w112_20240402.tif")
    assert selected[1]["downloadURL"].endswith("USGS_1_n34w113_20241016.tif")


def test_zip_member_name_finds_target_2021_nlcd_asset(tmp_path: Path):
    zip_path = tmp_path / "bundle.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("nested/Annual_NLCD_LndCov_2020_CU_C1V1.tif", b"2020")
        archive.writestr("nested/Annual_NLCD_LndCov_2021_CU_C1V1.tif", b"2021")

    member = _zip_member_name(zip_path, pattern=re.compile(r"Annual_NLCD_LndCov_2021_.*\.tif$", re.IGNORECASE))

    assert member == "nested/Annual_NLCD_LndCov_2021_CU_C1V1.tif"


def test_collect_nhdplus_water_features_reads_expected_layers(tmp_path: Path):
    package_path = tmp_path / "nhdplus_sample.gpkg"
    waterbody = gpd.GeoDataFrame({"FType": [390]}, geometry=[box(0, 0, 5, 5)], crs="EPSG:3857")
    flowline = gpd.GeoDataFrame({"FType": [460]}, geometry=[LineString([(0, 10), (10, 10)])], crs="EPSG:3857")
    ignored = gpd.GeoDataFrame({"name": ["ignore"]}, geometry=[box(20, 20, 30, 30)], crs="EPSG:3857")

    waterbody.to_file(package_path, layer="NHDWaterbody", driver="GPKG")
    flowline.to_file(package_path, layer="NHDFlowline", driver="GPKG")
    ignored.to_file(package_path, layer="WBDHU4", driver="GPKG")

    study_area = gpd.GeoDataFrame({"city_id": [1]}, geometry=[box(-1, -1, 12, 12)], crs="EPSG:3857")
    water = collect_nhdplus_water_features(package_path=package_path, study_area_gdf=study_area)

    assert sorted(water["source_layer"].unique().tolist()) == ["NHDFlowline", "NHDWaterbody"]
    assert len(water) == 2


def test_run_raw_data_acquisition_skips_existing_outputs_without_force(tmp_path: Path):
    city = load_cities().iloc[0]
    study_area_path, _ = city_output_paths(
        city,
        resolution=30,
        study_areas_dir=tmp_path / "study_areas",
        city_grids_dir=tmp_path / "city_grids",
    )
    study_area_path.parent.mkdir(parents=True, exist_ok=True)
    study_area_path.write_text("placeholder")

    expected_raw = expected_support_layer_raw_paths(
        city,
        raw_dem_dir=tmp_path / "raw" / "dem",
        raw_nlcd_dir=tmp_path / "raw" / "nlcd",
        raw_hydro_dir=tmp_path / "raw" / "hydro",
    )
    for path in [
        expected_raw.dem_raster,
        expected_raw.nlcd_land_cover_raster,
        expected_raw.nlcd_impervious_raster,
        expected_raw.hydro_vector,
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ready")

    result = run_raw_data_acquisition(
        dataset="all",
        city_ids=[1],
        study_areas_dir=tmp_path / "study_areas",
        city_grids_dir=tmp_path / "city_grids",
        raw_dem_dir=tmp_path / "raw" / "dem",
        raw_nlcd_dir=tmp_path / "raw" / "nlcd",
        raw_hydro_dir=tmp_path / "raw" / "hydro",
        dem_cache_dir=tmp_path / "cache" / "dem",
        nlcd_cache_dir=tmp_path / "cache" / "nlcd",
        hydro_cache_dir=tmp_path / "cache" / "hydro",
        support_layers_dir=tmp_path / "support_layers",
    )

    assert len(result.summary) == 3
    assert set(result.summary["dataset"].tolist()) == {"dem", "nlcd", "hydro"}
    assert set(result.summary["status"].tolist()) == {"skipped_existing"}
    assert result.summary_json_path.exists()
    assert result.summary_csv_path.exists()
