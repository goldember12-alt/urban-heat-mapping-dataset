from pathlib import Path

import pandas as pd

from src.appeears_acquisition import filter_cities_for_retry, resolve_city_download_dir


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
