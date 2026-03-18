import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

from src.appeears_acquisition import (
    AcquisitionPreflightResult,
    audit_appeears_acquisition_readiness,
    build_product_spec,
    expected_aoi_path,
    expected_study_area_path,
    filter_cities_for_retry,
    resolve_city_download_dir,
    run_appeears_acquisition,
)
from src.appeears_client import build_area_task_payload
from src.load_cities import load_cities


def _write_valid_aoi(aoi_path: Path) -> None:
    aoi = gpd.GeoDataFrame(
        {"city_id": [1], "city_name": ["Phoenix"], "state": ["AZ"]},
        geometry=[Polygon([(-112.1, 33.4), (-112.0, 33.4), (-112.0, 33.5), (-112.1, 33.5)])],
        crs="EPSG:4326",
    )
    aoi_path.parent.mkdir(parents=True, exist_ok=True)
    aoi.to_file(aoi_path, driver="GeoJSON")


def test_resolve_city_download_dir_routes_ndvi_and_ecostress(tmp_path: Path):
    ndvi_root = tmp_path / "raw" / "ndvi"
    ecostress_root = tmp_path / "raw" / "ecostress"

    ndvi_path = resolve_city_download_dir(
        product_type="ndvi",
        city_name="Salt Lake City",
        raw_ndvi_dir=ndvi_root,
        raw_ecostress_dir=ecostress_root,
    )
    ecostress_path = resolve_city_download_dir(
        product_type="ecostress",
        city_name="Salt Lake City",
        raw_ndvi_dir=ndvi_root,
        raw_ecostress_dir=ecostress_root,
    )

    assert ndvi_path == ndvi_root / "salt_lake_city"
    assert ecostress_path == ecostress_root / "salt_lake_city"


def test_filter_cities_for_retry_keeps_only_incomplete_when_requested():
    cities = pd.DataFrame(
        {
            "city_id": [1, 2, 3],
            "city_name": ["CityA", "CityB", "CityC"],
            "state": ["AA", "BB", "CC"],
            "climate_group": ["hot_arid", "mild_cool", "mixed_humid"],
            "lat": [0.0, 1.0, 2.0],
            "lon": [0.0, 1.0, 2.0],
        }
    )
    existing = {
        1: {"status": "completed"},
        2: {"status": "failed"},
    }

    retry_subset = filter_cities_for_retry(cities=cities, existing_records=existing, retry_incomplete=True)
    assert retry_subset["city_id"].tolist() == [2, 3]

    all_subset = filter_cities_for_retry(cities=cities, existing_records=existing, retry_incomplete=False)
    assert all_subset["city_id"].tolist() == [1, 2, 3]


def test_default_ndvi_payload_uses_selectable_layer_name():
    spec = build_product_spec(product_type="ndvi")

    payload = build_area_task_payload(
        task_name="ndvi_phoenix_2023",
        product=spec.product_candidates[0],
        layer=spec.layer,
        start_date="2023-05-01",
        end_date="2023-08-31",
        aoi_feature_collection={
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"city_id": 1},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-112.1, 33.4], [-112.0, 33.4], [-112.0, 33.5], [-112.1, 33.5], [-112.1, 33.4]]],
                    },
                }
            ],
        },
    )

    assert payload["params"]["layers"][0]["product"] == "MOD13A1.061"
    assert payload["params"]["layers"][0]["layer"] == "_500m_16_days_NDVI"


def test_default_ecostress_payload_uses_live_selectable_product_and_layer():
    spec = build_product_spec(product_type="ecostress")

    payload = build_area_task_payload(
        task_name="ecostress_phoenix_2023",
        product=spec.product_candidates[0],
        layer=spec.layer,
        start_date="2023-05-01",
        end_date="2023-08-31",
        aoi_feature_collection={
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"city_id": 1},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-112.1, 33.4], [-112.0, 33.4], [-112.0, 33.5], [-112.1, 33.5], [-112.1, 33.4]]],
                    },
                }
            ],
        },
    )

    assert spec.product_candidates == ("ECO_L2T_LSTE.002", "ECO_L2_LSTE.002")
    assert spec.layer == "LST"
    assert payload["params"]["layers"][0]["product"] == "ECO_L2T_LSTE.002"
    assert payload["params"]["layers"][0]["layer"] == "LST"


def test_audit_appeears_acquisition_readiness_uses_all_cities_when_city_ids_omitted(tmp_path: Path):
    cities = load_cities()
    result = audit_appeears_acquisition_readiness(
        product_type="ndvi",
        study_areas_dir=tmp_path / "study_areas",
        aoi_dir=tmp_path / "appeears_aoi",
        status_dir=tmp_path / "appeears_status",
        raw_ndvi_dir=tmp_path / "raw" / "ndvi",
        raw_ecostress_dir=tmp_path / "raw" / "ecostress",
    )

    assert len(result.summary) == len(cities) == 30
    assert result.summary["city_id"].tolist() == cities["city_id"].tolist()
    assert set(result.summary["blocking_reason"]) == {"study_area_missing"}
    assert not result.summary["acquisition_ready"].any()
    assert result.summary_json_path.exists()
    assert result.summary_csv_path.exists()


def test_audit_appeears_acquisition_readiness_marks_missing_prerequisites(tmp_path: Path):
    result = audit_appeears_acquisition_readiness(
        product_type="ndvi",
        city_ids=[1],
        study_areas_dir=tmp_path / "study_areas",
        aoi_dir=tmp_path / "appeears_aoi",
        status_dir=tmp_path / "appeears_status",
        raw_ndvi_dir=tmp_path / "raw" / "ndvi",
        raw_ecostress_dir=tmp_path / "raw" / "ecostress",
    )

    row = result.summary.iloc[0]
    assert row["city_id"] == 1
    assert bool(row["study_area_exists"]) is False
    assert bool(row["aoi_exists"]) is False
    assert bool(row["aoi_crs_valid"]) is False
    assert bool(row["acquisition_ready"]) is False
    assert row["blocking_reason"] == "study_area_missing"


def test_audit_appeears_acquisition_readiness_validates_aoi_crs(tmp_path: Path, monkeypatch):
    city = load_cities().iloc[0]
    study_path = expected_study_area_path(city, tmp_path / "study_areas")
    aoi_path = expected_aoi_path(city, tmp_path / "appeears_aoi")
    study_path.parent.mkdir(parents=True, exist_ok=True)
    aoi_path.parent.mkdir(parents=True, exist_ok=True)
    study_path.touch()
    aoi_path.touch()

    invalid_aoi = gpd.GeoDataFrame(
        {"city_id": [1]},
        geometry=[Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
        crs="EPSG:3857",
    )
    original_read_file = gpd.read_file

    def fake_read_file(path: Path):
        if Path(path) == aoi_path:
            return invalid_aoi
        return original_read_file(path)

    monkeypatch.setattr("src.appeears_acquisition.gpd.read_file", fake_read_file)

    result = audit_appeears_acquisition_readiness(
        product_type="ecostress",
        city_ids=[1],
        study_areas_dir=tmp_path / "study_areas",
        aoi_dir=tmp_path / "appeears_aoi",
        status_dir=tmp_path / "appeears_status",
    )

    row = result.summary.iloc[0]
    assert bool(row["study_area_exists"]) is True
    assert bool(row["aoi_exists"]) is True
    assert bool(row["aoi_crs_valid"]) is False
    assert bool(row["acquisition_ready"]) is False
    assert str(row["blocking_reason"]).startswith("aoi_crs_invalid:")


def test_audit_outputs_include_expected_paths_and_ready_status(tmp_path: Path):
    city = load_cities().iloc[0]
    study_path = expected_study_area_path(city, tmp_path / "study_areas")
    aoi_path = expected_aoi_path(city, tmp_path / "appeears_aoi")
    study_path.parent.mkdir(parents=True, exist_ok=True)
    study_path.touch()
    _write_valid_aoi(aoi_path)

    result = audit_appeears_acquisition_readiness(
        product_type="ndvi",
        city_ids=[1],
        study_areas_dir=tmp_path / "study_areas",
        aoi_dir=tmp_path / "appeears_aoi",
        status_dir=tmp_path / "appeears_status",
        raw_ndvi_dir=tmp_path / "raw" / "ndvi",
        raw_ecostress_dir=tmp_path / "raw" / "ecostress",
    )

    row = result.summary.iloc[0]
    assert row["city_slug"] == "phoenix"
    assert bool(row["study_area_exists"]) is True
    assert bool(row["aoi_exists"]) is True
    assert bool(row["aoi_crs_valid"]) is True
    assert bool(row["acquisition_ready"]) is True
    assert row["blocking_reason"] == ""
    assert row["expected_status_output_path"] == str(tmp_path / "appeears_status" / "appeears_ndvi_acquisition_summary.json")
    assert row["expected_ndvi_raw_dir"] == str(tmp_path / "raw" / "ndvi" / "phoenix")
    assert row["expected_ecostress_raw_dir"] == str(tmp_path / "raw" / "ecostress" / "phoenix")

    with result.summary_json_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    assert payload["product_type"] == "ndvi"
    assert payload["records"][0]["acquisition_ready"] is True
    assert payload["records"][0]["expected_aoi_path"] == str(aoi_path)

    csv = pd.read_csv(result.summary_csv_path)
    assert csv.loc[0, "expected_study_area_path"] == str(study_path)
    assert bool(csv.loc[0, "acquisition_ready"]) is True


def test_run_appeears_acquisition_preflight_only_returns_audit_summary(tmp_path: Path):
    result = run_appeears_acquisition(
        product_type="ndvi",
        start_date="",
        end_date="",
        city_ids=[1],
        preflight_only=True,
        study_areas_dir=tmp_path / "study_areas",
        aoi_dir=tmp_path / "appeears_aoi",
        status_dir=tmp_path / "appeears_status",
    )

    assert "acquisition_ready" in result.summary.columns
    assert result.summary_json_path.name == "appeears_ndvi_preflight_summary.json"
    assert result.summary_csv_path.name == "appeears_ndvi_preflight_summary.csv"


def test_run_appeears_acquisition_marks_missing_credentials_with_explicit_env_vars(tmp_path: Path, monkeypatch):
    cities = pd.DataFrame(
        {
            "city_id": [1],
            "city_name": ["Phoenix"],
            "state": ["AZ"],
            "climate_group": ["hot_arid"],
            "lat": [33.45],
            "lon": [-112.07],
        }
    )
    preflight_summary = pd.DataFrame(
        {
            "city_id": [1],
            "expected_study_area_path": [str(tmp_path / "study_areas" / "phoenix.gpkg")],
            "expected_aoi_path": [str(tmp_path / "appeears_aoi" / "phoenix.geojson")],
        }
    )
    aoi_summary = pd.DataFrame(
        {
            "city_id": [1],
            "status": ["completed"],
            "study_area_path": [str(tmp_path / "study_areas" / "phoenix.gpkg")],
            "aoi_path": [str(tmp_path / "appeears_aoi" / "phoenix.geojson")],
        }
    )

    monkeypatch.setattr("src.appeears_acquisition.load_cities", lambda: cities)
    monkeypatch.setattr(
        "src.appeears_acquisition.audit_appeears_acquisition_readiness",
        lambda **kwargs: AcquisitionPreflightResult(
            summary=preflight_summary,
            summary_json_path=tmp_path / "appeears_status" / "preflight.json",
            summary_csv_path=tmp_path / "appeears_status" / "preflight.csv",
        ),
    )
    monkeypatch.setattr("src.appeears_acquisition.export_appeears_aois", lambda **kwargs: aoi_summary)

    def fail_if_client_requested():
        raise AssertionError("AppEEARS client should not be created when credentials are missing")

    monkeypatch.setattr("src.appeears_acquisition.AppEEARSClient.from_environment", fail_if_client_requested)
    monkeypatch.delenv("APPEEARS_API_TOKEN", raising=False)
    monkeypatch.delenv("EARTHDATA_USERNAME", raising=False)
    monkeypatch.delenv("EARTHDATA_PASSWORD", raising=False)

    result = run_appeears_acquisition(
        product_type="ndvi",
        start_date="2023-05-01",
        end_date="2023-08-31",
        city_ids=[1],
        status_dir=tmp_path / "appeears_status",
    )

    row = result.summary.iloc[0]
    assert row["status"] == "blocked_missing_credentials"
    assert row["error"] == "missing_credentials"
    assert "APPEEARS_API_TOKEN" in row["message"]
    assert "EARTHDATA_USERNAME" in row["message"]
    assert "EARTHDATA_PASSWORD" in row["message"]
