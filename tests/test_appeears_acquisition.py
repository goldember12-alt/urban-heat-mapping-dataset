from pathlib import Path

import pandas as pd

from src.appeears_acquisition import build_product_spec, filter_cities_for_retry, resolve_city_download_dir
from src.appeears_client import build_area_task_payload


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
