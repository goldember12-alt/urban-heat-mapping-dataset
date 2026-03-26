from pathlib import Path
import json
import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import Polygon

import src.feature_assembly as feature_assembly
from src.city_processing import CORE_GEOMETRY_CRS_COLUMN, CORE_GEOMETRY_WKT_COLUMN, city_output_paths
from src.feature_assembly import (
    CELL_FILTER_CORE_CITY,
    CityFeatureResult,
    FeatureSourceConfig,
    assemble_final_dataset,
    extract_features_for_all_cities,
)
from src.grid import create_grid_from_polygon


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


def test_assemble_final_dataset_applies_drop_rules_and_hotspot(tmp_path: Path, monkeypatch):
    city_features_dir = tmp_path / "city_features"
    final_dir = tmp_path / "final"
    city_features_dir.mkdir(parents=True, exist_ok=True)

    city1 = pd.DataFrame(
        {
            "city_id": [1, 1, 1],
            "city_name": ["CityA", "CityA", "CityA"],
            "climate_group": ["hot_arid", "hot_arid", "hot_arid"],
            "cell_id": [1, 2, 3],
            "centroid_lon": [0.0, 0.1, 0.2],
            "centroid_lat": [0.0, 0.1, 0.2],
            "impervious_pct": [20.0, 30.0, 40.0],
            "land_cover_class": [11, 21, 22],
            "elevation_m": [100.0, 101.0, 102.0],
            "dist_to_water_m": [5.0, 10.0, 15.0],
            "ndvi_median_may_aug": [0.2, 0.3, 0.4],
            "lst_median_may_aug": [30.0, 40.0, 50.0],
            "n_valid_ecostress_passes": [5, 2, 5],
            "hotspot_10pct": [pd.NA, pd.NA, pd.NA],
        }
    )

    city2 = pd.DataFrame(
        {
            "city_id": [2],
            "city_name": ["CityB"],
            "climate_group": ["mild_cool"],
            "cell_id": [1],
            "centroid_lon": [1.0],
            "centroid_lat": [1.0],
            "impervious_pct": [10.0],
            "land_cover_class": [23],
            "elevation_m": [110.0],
            "dist_to_water_m": [20.0],
            "ndvi_median_may_aug": [0.5],
            "lst_median_may_aug": [pd.NA],
            "n_valid_ecostress_passes": [pd.NA],
            "hotspot_10pct": [pd.NA],
        }
    )

    parquet_1 = city_features_dir / "01_citya_features.parquet"
    parquet_2 = city_features_dir / "02_cityb_features.parquet"
    parquet_1.write_text("mock")
    parquet_2.write_text("mock")

    source_frames = {
        str(parquet_1): city1,
        str(parquet_2): city2,
    }

    def fake_read_parquet(path):
        return source_frames[str(path)].copy()

    def fake_to_parquet(self, path, index=False):
        Path(path).write_text("mock parquet output")

    monkeypatch.setattr(feature_assembly.pd, "read_parquet", fake_read_parquet)
    monkeypatch.setattr(pd.DataFrame, "to_parquet", fake_to_parquet, raising=False)

    result = assemble_final_dataset(city_features_dir=city_features_dir, final_dir=final_dir)

    assert len(result.final_df) == 2
    assert (result.final_df["land_cover_class"] == 11).sum() == 0
    assert ((result.final_df["city_id"] == 1) & (result.final_df["cell_id"] == 2)).sum() == 0

    city1_row = result.final_df[result.final_df["city_id"] == 1].iloc[0]
    assert bool(city1_row["hotspot_10pct"]) is True

    city2_row = result.final_df[result.final_df["city_id"] == 2].iloc[0]
    assert pd.isna(city2_row["hotspot_10pct"])

    assert result.parquet_path.exists()
    assert result.csv_path.exists()
    assert result.artifact_summary_path.exists()

    artifact_summary = json.loads(result.artifact_summary_path.read_text(encoding="utf-8"))
    assert artifact_summary["row_count"] == 2
    assert artifact_summary["input_city_feature_row_count"] == 4
    assert artifact_summary["dropped_row_count"] == 2
    assert artifact_summary["canonical_modeling_input"].endswith("final_dataset.parquet")
    assert artifact_summary["csv_status"] == "compatibility_fallback_serialization"
    assert len(artifact_summary["source_city_feature_files"]) == 2


def test_assemble_final_dataset_keeps_existing_csv_when_rewrite_fails(tmp_path: Path, monkeypatch):
    city_features_dir = tmp_path / "city_features"
    final_dir = tmp_path / "final"
    city_features_dir.mkdir(parents=True, exist_ok=True)
    final_dir.mkdir(parents=True, exist_ok=True)

    city_df = pd.DataFrame(
        {
            "city_id": [1],
            "city_name": ["CityA"],
            "climate_group": ["hot_arid"],
            "cell_id": [1],
            "centroid_lon": [0.0],
            "centroid_lat": [0.0],
            "impervious_pct": [20.0],
            "land_cover_class": [21],
            "elevation_m": [100.0],
            "dist_to_water_m": [5.0],
            "ndvi_median_may_aug": [0.2],
            "lst_median_may_aug": [30.0],
            "n_valid_ecostress_passes": [5],
            "hotspot_10pct": [pd.NA],
        }
    )

    parquet_path = city_features_dir / "01_citya_features.parquet"
    parquet_path.write_text("mock")
    (final_dir / "final_dataset.csv").write_text("previous csv output", encoding="utf-8")

    monkeypatch.setattr(feature_assembly.pd, "read_parquet", lambda path: city_df.copy())
    monkeypatch.setattr(
        pd.DataFrame,
        "to_parquet",
        lambda self, path, index=False: Path(path).write_text("mock parquet output"),
        raising=False,
    )

    def failing_to_csv(self, path, index=False):
        raise RuntimeError("csv write failed")

    monkeypatch.setattr(pd.DataFrame, "to_csv", failing_to_csv, raising=False)

    with pytest.raises(RuntimeError, match="csv write failed"):
        assemble_final_dataset(city_features_dir=city_features_dir, final_dir=final_dir)

    assert (final_dir / "final_dataset.csv").read_text(encoding="utf-8") == "previous csv output"
    assert not (final_dir / "final_dataset.csv.tmp").exists()


def test_extract_features_for_all_cities_can_skip_missing_grids(monkeypatch, tmp_path: Path):
    cities = pd.DataFrame(
        {
            "city_id": [1, 2],
            "city_name": ["CityA", "CityB"],
            "state": ["AA", "BB"],
            "climate_group": ["hot_arid", "mild_cool"],
            "lat": [0.0, 1.0],
            "lon": [0.0, 1.0],
        }
    )
    monkeypatch.setattr(feature_assembly, "load_cities", lambda: cities)

    existing_grid = tmp_path / "grid.gpkg"
    existing_grid.write_text("placeholder")

    def fake_resolve(city: pd.Series, resolution: float = 30, city_grids_dir: Path = Path(".")) -> Path:
        return existing_grid if int(city["city_id"]) == 1 else tmp_path / "missing.gpkg"

    monkeypatch.setattr(feature_assembly, "_resolve_city_grid_path", fake_resolve)

    def fake_assemble_city_features(*args, **kwargs):
        return CityFeatureResult(
            city=cities.iloc[0],
            n_rows=4,
            city_features_gpkg_path=None,
            city_features_parquet_path=None,
            intermediate_unfiltered_path=None,
            intermediate_filtered_path=None,
            blocked_stages=[],
        )

    monkeypatch.setattr(feature_assembly, "assemble_city_features", fake_assemble_city_features)

    result = extract_features_for_all_cities(
        resolution=30,
        save_outputs=False,
        continue_on_error=True,
        existing_grids_only=True,
    )

    statuses = sorted(result.summary["status"].tolist())
    assert statuses == ["ok", "skipped_missing_grid"]


def test_assemble_city_features_core_city_filter_marks_buffer_ring_cells(tmp_path: Path, monkeypatch):
    city = pd.Series(
        {
            "city_id": 9,
            "city_name": "Buffer City",
            "state": "BC",
            "climate_group": "hot_arid",
            "lat": [0.0][0],
            "lon": [0.0][0],
        }
    )
    study_polygon = Polygon([(0, 0), (120, 0), (120, 60), (0, 60)])
    core_polygon = Polygon([(30, 0), (90, 0), (90, 60), (30, 60)])
    study_area = gpd.GeoDataFrame(
        {
            "city_id": [9],
            "city_name": ["Buffer City"],
            "state": ["BC"],
            "climate_group": ["hot_arid"],
            "buffer_m": [2000.0],
            CORE_GEOMETRY_WKT_COLUMN: [core_polygon.wkt],
            CORE_GEOMETRY_CRS_COLUMN: ["EPSG:32612"],
        },
        geometry=[study_polygon],
        crs="EPSG:32612",
    )
    grid = create_grid_from_polygon(study_area[["geometry"]].copy(), resolution=30)

    study_areas_dir = tmp_path / "study_areas"
    city_grids_dir = tmp_path / "city_grids"
    city_features_dir = tmp_path / "city_features"
    intermediate_dir = tmp_path / "intermediate"
    study_path, grid_path = city_output_paths(
        city=city,
        resolution=30,
        study_areas_dir=study_areas_dir,
        city_grids_dir=city_grids_dir,
    )
    study_path.parent.mkdir(parents=True, exist_ok=True)
    grid_path.parent.mkdir(parents=True, exist_ok=True)
    study_area.to_file(study_path, driver="GPKG")
    grid.to_file(grid_path, driver="GPKG")

    monkeypatch.setattr(feature_assembly, "load_city_record", lambda **kwargs: city)

    result = feature_assembly.assemble_city_features(
        city_id=9,
        resolution=30,
        feature_sources=FeatureSourceConfig(),
        cell_filter_mode=CELL_FILTER_CORE_CITY,
        save_outputs=True,
        city_grids_dir=city_grids_dir,
        study_areas_dir=study_areas_dir,
        city_features_dir=city_features_dir,
        intermediate_dir=intermediate_dir,
    )

    unfiltered = pd.read_parquet(result.intermediate_unfiltered_path)
    filtered = pd.read_parquet(result.city_features_parquet_path)

    assert len(unfiltered) == 8
    assert int(unfiltered["is_core_city_cell"].fillna(False).sum()) == 4
    assert int(unfiltered["is_buffer_ring_cell"].fillna(False).sum()) == 4
    assert result.n_rows == 4
    assert len(filtered) == 4
    assert filtered["is_core_city_cell"].fillna(False).all()
    assert not filtered["is_buffer_ring_cell"].fillna(False).any()


def test_assemble_city_features_core_city_filter_requires_core_metadata(tmp_path: Path, monkeypatch):
    city = pd.Series(
        {
            "city_id": 10,
            "city_name": "Legacy City",
            "state": "LC",
            "climate_group": "hot_arid",
            "lat": [0.0][0],
            "lon": [0.0][0],
        }
    )
    study_polygon = Polygon([(0, 0), (120, 0), (120, 60), (0, 60)])
    study_area = gpd.GeoDataFrame(
        {
            "city_id": [10],
            "city_name": ["Legacy City"],
            "state": ["LC"],
            "climate_group": ["hot_arid"],
            "buffer_m": [2000.0],
        },
        geometry=[study_polygon],
        crs="EPSG:32612",
    )
    grid = create_grid_from_polygon(study_area[["geometry"]].copy(), resolution=30)

    study_areas_dir = tmp_path / "study_areas"
    city_grids_dir = tmp_path / "city_grids"
    study_path, grid_path = city_output_paths(
        city=city,
        resolution=30,
        study_areas_dir=study_areas_dir,
        city_grids_dir=city_grids_dir,
    )
    study_path.parent.mkdir(parents=True, exist_ok=True)
    grid_path.parent.mkdir(parents=True, exist_ok=True)
    study_area.to_file(study_path, driver="GPKG")
    grid.to_file(grid_path, driver="GPKG")

    monkeypatch.setattr(feature_assembly, "load_city_record", lambda **kwargs: city)

    with pytest.raises(ValueError, match="Rerun city processing"):
        feature_assembly.assemble_city_features(
            city_id=10,
            resolution=30,
            feature_sources=FeatureSourceConfig(),
            cell_filter_mode=CELL_FILTER_CORE_CITY,
            save_outputs=False,
            city_grids_dir=city_grids_dir,
            study_areas_dir=study_areas_dir,
            city_features_dir=tmp_path / "city_features",
            intermediate_dir=tmp_path / "intermediate",
        )


def test_discover_default_feature_sources_uses_city_appeears_layer_files(tmp_path: Path, monkeypatch):
    raw_ndvi = tmp_path / "raw" / "ndvi"
    raw_ecostress = tmp_path / "raw" / "ecostress"
    city_ndvi_dir = raw_ndvi / "phoenix" / "MOD13A1.061_2023106_to_2023243"
    city_lst_dir = raw_ecostress / "phoenix" / "ECO_L2T_LSTE.002_2023121_to_2023243"
    city_ndvi_dir.mkdir(parents=True, exist_ok=True)
    city_lst_dir.mkdir(parents=True, exist_ok=True)

    ndvi_layer = city_ndvi_dir / "MOD13A1.061__500m_16_days_NDVI_doy2023113000000_aid0001.tif"
    ndvi_quality = city_ndvi_dir / "MOD13A1.061__500m_16_days_VI_Quality_doy2023113000000_aid0001.tif"
    lst_layer = city_lst_dir / "ECO_L2T_LSTE.002_LST_doy2023123074744_aid0001_12N.tif"
    lst_cloud = city_lst_dir / "ECO_L2T_LSTE.002_cloud_doy2023123074744_aid0001_12N.tif"
    lst_qc = city_lst_dir / "ECO_L2T_LSTE.002_QC_doy2023123074744_aid0001_12N.tif"
    stale_ndvi_1 = raw_ndvi / "phoenix" / "ndvi_1.tif"
    stale_ndvi_2 = raw_ndvi / "phoenix" / "ndvi_2.tif"
    stale_lst_1 = raw_ecostress / "phoenix" / "lst_1.tif"

    for path in [ndvi_quality, lst_cloud, lst_qc, stale_ndvi_1, stale_ndvi_2, stale_lst_1]:
        path.write_bytes(b"x")
    _write_raster(ndvi_layer, np.array([[1, 2], [3, 4]], dtype=np.int16))
    _write_raster(lst_layer, np.array([[10, 11], [12, 13]], dtype=np.int16))

    monkeypatch.setattr(feature_assembly, "RAW_NDVI", raw_ndvi)
    monkeypatch.setattr(feature_assembly, "RAW_ECOSTRESS", raw_ecostress)
    monkeypatch.setattr(feature_assembly, "RAW_DEM", tmp_path / "raw" / "dem")
    monkeypatch.setattr(feature_assembly, "RAW_NLCD", tmp_path / "raw" / "nlcd")
    monkeypatch.setattr(feature_assembly, "RAW_HYDRO", tmp_path / "raw" / "hydro")
    monkeypatch.setattr(feature_assembly, "SUPPORT_LAYERS", tmp_path / "support_layers")

    city = pd.Series({"city_id": 1, "city_name": "Phoenix", "state": "AZ"})
    sources = feature_assembly.discover_default_feature_sources(city)

    assert sources.ndvi_rasters == [ndvi_layer]
    assert sources.lst_rasters == [lst_layer]


def test_assemble_city_features_uses_only_valid_discovered_appeears_rasters(tmp_path: Path, monkeypatch):
    raw_ndvi = tmp_path / "raw" / "ndvi"
    raw_ecostress = tmp_path / "raw" / "ecostress"
    city_ndvi_dir = raw_ndvi / "tucson" / "MOD13A1.061_2023106_to_2023243"
    city_lst_dir = raw_ecostress / "tucson" / "ECO_L2T_LSTE.002_2023121_to_2023243"
    city_ndvi_dir.mkdir(parents=True, exist_ok=True)
    city_lst_dir.mkdir(parents=True, exist_ok=True)

    ndvi_a = _write_raster(city_ndvi_dir / "MOD13A1.061__500m_16_days_NDVI_doy2023113000000_aid0001.tif", np.array([[1, 2], [3, 4]], dtype=np.int16))
    ndvi_b = _write_raster(city_ndvi_dir / "MOD13A1.061__500m_16_days_NDVI_doy2023129000000_aid0001.tif", np.array([[2, 3], [4, 5]], dtype=np.int16))
    lst_a = _write_raster(city_lst_dir / "ECO_L2T_LSTE.002_LST_doy2023123074744_aid0001_12N.tif", np.array([[10, 11], [12, 13]], dtype=np.int16))
    lst_b = _write_raster(city_lst_dir / "ECO_L2T_LSTE.002_LST_doy2023135074744_aid0001_12N.tif", np.array([[12, 13], [14, 15]], dtype=np.int16))

    for path in [
        raw_ndvi / "tucson" / "ndvi_1.tif",
        raw_ndvi / "tucson" / "ndvi_2.tif",
        raw_ecostress / "tucson" / "lst_1.tif",
    ]:
        path.write_bytes(b"x")

    monkeypatch.setattr(feature_assembly, "RAW_NDVI", raw_ndvi)
    monkeypatch.setattr(feature_assembly, "RAW_ECOSTRESS", raw_ecostress)
    monkeypatch.setattr(feature_assembly, "RAW_DEM", tmp_path / "raw" / "dem")
    monkeypatch.setattr(feature_assembly, "RAW_NLCD", tmp_path / "raw" / "nlcd")
    monkeypatch.setattr(feature_assembly, "RAW_HYDRO", tmp_path / "raw" / "hydro")
    monkeypatch.setattr(feature_assembly, "SUPPORT_LAYERS", tmp_path / "support_layers")

    city = pd.Series({"city_id": 2, "city_name": "Tucson", "state": "AZ", "climate_group": "hot_arid"})
    grid = _build_test_grid()
    fake_grid_path = tmp_path / "grid.gpkg"
    fake_grid_path.write_text("placeholder")

    monkeypatch.setattr(feature_assembly, "load_city_record", lambda **kwargs: city)
    monkeypatch.setattr(feature_assembly, "_resolve_city_grid_path", lambda **kwargs: fake_grid_path)
    monkeypatch.setattr(feature_assembly, "_read_city_grid", lambda **kwargs: grid.copy())

    captured_paths: dict[str, list[Path]] = {}

    def fake_sample_median_from_raster_stack(*, grid_gdf, raster_paths, stack_label="raster stack", **kwargs):
        captured_paths[stack_label] = list(raster_paths)
        n = len(grid_gdf)
        if stack_label.startswith("LST"):
            return np.full(n, 35.0, dtype=np.float64), np.full(n, 3, dtype=np.int64)
        return np.full(n, 0.5, dtype=np.float64), np.full(n, 2, dtype=np.int64)

    monkeypatch.setattr(feature_assembly, "sample_median_from_raster_stack", fake_sample_median_from_raster_stack)

    result = feature_assembly.assemble_city_features(city_id=2, save_outputs=False)

    ndvi_label = "NDVI city_id=2 city_name=Tucson"
    lst_label = "LST city_id=2 city_name=Tucson"

    assert captured_paths[ndvi_label] == [ndvi_a, ndvi_b]
    assert captured_paths[lst_label] == [lst_a, lst_b]
    assert "ndvi" not in result.blocked_stages
    assert "ecostress_lst" not in result.blocked_stages


def test_discover_default_feature_sources_accepts_native_appeears_layer_names_without_legacy_tokens(
    tmp_path: Path,
    monkeypatch,
):
    raw_ndvi = tmp_path / "raw" / "ndvi"
    raw_ecostress = tmp_path / "raw" / "ecostress"
    city_ndvi_dir = raw_ndvi / "phoenix" / "MOD13A1.061_2023106_to_2023243"
    city_lst_dir = raw_ecostress / "phoenix" / "ECO_L2T_LSTE.002_2023121_to_2023243"
    city_ndvi_dir.mkdir(parents=True, exist_ok=True)
    city_lst_dir.mkdir(parents=True, exist_ok=True)

    ndvi_layer = city_ndvi_dir / "MOD13A1.061.500m.16.days.NDVI.doy2023113000000.aid0001.tif"
    ndvi_quality = city_ndvi_dir / "MOD13A1.061.500m.16.days.VI.Quality.doy2023113000000.aid0001.tif"
    lst_layer = city_lst_dir / "ECO_L2T_LSTE.002.LST.doy2023123074744.aid0001.12N.tif"
    lst_error = city_lst_dir / "ECO_L2T_LSTE.002.LST_ERR.doy2023123074744.aid0001.12N.tif"

    for path in [ndvi_layer, ndvi_quality, lst_layer, lst_error]:
        path.write_text("x")

    monkeypatch.setattr(feature_assembly, "RAW_NDVI", raw_ndvi)
    monkeypatch.setattr(feature_assembly, "RAW_ECOSTRESS", raw_ecostress)
    monkeypatch.setattr(feature_assembly, "RAW_DEM", tmp_path / "raw" / "dem")
    monkeypatch.setattr(feature_assembly, "RAW_NLCD", tmp_path / "raw" / "nlcd")
    monkeypatch.setattr(feature_assembly, "RAW_HYDRO", tmp_path / "raw" / "hydro")
    monkeypatch.setattr(feature_assembly, "SUPPORT_LAYERS", tmp_path / "support_layers")

    city = pd.Series({"city_id": 1, "city_name": "Phoenix", "state": "AZ"})
    sources = feature_assembly.discover_default_feature_sources(city)

    assert sources.ndvi_rasters == [ndvi_layer]
    assert sources.lst_rasters == [lst_layer]


def test_discover_default_feature_sources_falls_back_to_top_level_when_city_folder_missing(tmp_path: Path, monkeypatch):
    raw_ndvi = tmp_path / "raw" / "ndvi"
    raw_ecostress = tmp_path / "raw" / "ecostress"
    raw_ndvi.mkdir(parents=True, exist_ok=True)
    raw_ecostress.mkdir(parents=True, exist_ok=True)

    ndvi_top = raw_ndvi / "phoenix_ndvi_stack.tif"
    lst_top = raw_ecostress / "phoenix_lst_stack.tif"
    ndvi_top.write_text("x")
    lst_top.write_text("x")

    monkeypatch.setattr(feature_assembly, "RAW_NDVI", raw_ndvi)
    monkeypatch.setattr(feature_assembly, "RAW_ECOSTRESS", raw_ecostress)
    monkeypatch.setattr(feature_assembly, "RAW_DEM", tmp_path / "raw" / "dem")
    monkeypatch.setattr(feature_assembly, "RAW_NLCD", tmp_path / "raw" / "nlcd")
    monkeypatch.setattr(feature_assembly, "RAW_HYDRO", tmp_path / "raw" / "hydro")
    monkeypatch.setattr(feature_assembly, "SUPPORT_LAYERS", tmp_path / "support_layers")

    city = pd.Series({"city_id": 1, "city_name": "Phoenix", "state": "AZ"})
    sources = feature_assembly.discover_default_feature_sources(city)

    assert sources.ndvi_rasters == [ndvi_top]
    assert sources.lst_rasters == [lst_top]


def test_discover_default_feature_sources_uses_city_recursive_dem_nlcd_hydro(tmp_path: Path, monkeypatch):
    raw_dem = tmp_path / "raw" / "dem"
    raw_nlcd = tmp_path / "raw" / "nlcd"
    raw_hydro = tmp_path / "raw" / "hydro"
    raw_ndvi = tmp_path / "raw" / "ndvi"
    raw_ecostress = tmp_path / "raw" / "ecostress"

    city_dem_dir = raw_dem / "phoenix" / "subset"
    city_nlcd_dir = raw_nlcd / "phoenix" / "subset"
    city_hydro_dir = raw_hydro / "phoenix" / "subset"
    city_dem_dir.mkdir(parents=True, exist_ok=True)
    city_nlcd_dir.mkdir(parents=True, exist_ok=True)
    city_hydro_dir.mkdir(parents=True, exist_ok=True)
    raw_ndvi.mkdir(parents=True, exist_ok=True)
    raw_ecostress.mkdir(parents=True, exist_ok=True)

    dem_city = city_dem_dir / "phoenix_dem.tif"
    land_city = city_nlcd_dir / "phoenix_land_cover.tif"
    imp_city = city_nlcd_dir / "phoenix_impervious.tif"
    hydro_city = city_hydro_dir / "phoenix_hydro.gpkg"

    dem_city.write_text("x")
    land_city.write_text("x")
    imp_city.write_text("x")
    hydro_city.write_text("x")

    monkeypatch.setattr(feature_assembly, "RAW_DEM", raw_dem)
    monkeypatch.setattr(feature_assembly, "RAW_NLCD", raw_nlcd)
    monkeypatch.setattr(feature_assembly, "RAW_HYDRO", raw_hydro)
    monkeypatch.setattr(feature_assembly, "SUPPORT_LAYERS", tmp_path / "support_layers")
    monkeypatch.setattr(feature_assembly, "RAW_NDVI", raw_ndvi)
    monkeypatch.setattr(feature_assembly, "RAW_ECOSTRESS", raw_ecostress)

    city = pd.Series({"city_id": 1, "city_name": "Phoenix", "state": "AZ"})
    sources = feature_assembly.discover_default_feature_sources(city)

    assert sources.dem_raster == dem_city
    assert sources.nlcd_land_cover_raster == land_city
    assert sources.nlcd_impervious_raster == imp_city
    assert sources.hydro_vector == hydro_city
