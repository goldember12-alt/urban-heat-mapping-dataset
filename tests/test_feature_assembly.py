from pathlib import Path

import pandas as pd

import src.feature_assembly as feature_assembly
from src.feature_assembly import CityFeatureResult, assemble_final_dataset, extract_features_for_all_cities


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

    for path in [ndvi_layer, ndvi_quality, lst_layer, lst_cloud, lst_qc]:
        path.write_text("x")

    monkeypatch.setattr(feature_assembly, "RAW_NDVI", raw_ndvi)
    monkeypatch.setattr(feature_assembly, "RAW_ECOSTRESS", raw_ecostress)
    monkeypatch.setattr(feature_assembly, "RAW_DEM", tmp_path / "raw" / "dem")
    monkeypatch.setattr(feature_assembly, "RAW_NLCD", tmp_path / "raw" / "nlcd")
    monkeypatch.setattr(feature_assembly, "RAW_HYDRO", tmp_path / "raw" / "hydro")

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

    city = pd.Series({"city_id": 1, "city_name": "Phoenix", "state": "AZ"})
    sources = feature_assembly.discover_default_feature_sources(city)

    assert sources.ndvi_rasters == [ndvi_top]
    assert sources.lst_rasters == [lst_top]
