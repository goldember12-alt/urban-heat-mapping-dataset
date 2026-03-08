from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

from src.appeears_aoi import export_appeears_aois


def test_export_appeears_aois_writes_wgs84_geojson(tmp_path: Path):
    study_areas_dir = tmp_path / "study_areas"
    aoi_dir = tmp_path / "appeears_aoi"
    study_areas_dir.mkdir(parents=True, exist_ok=True)

    study_area = gpd.GeoDataFrame(
        {
            "city_id": [1],
            "city_name": ["Phoenix"],
            "state": ["AZ"],
        },
        geometry=[Polygon([(400000, 3700000), (401000, 3700000), (401000, 3701000), (400000, 3701000)])],
        crs="EPSG:32612",
    )
    study_path = study_areas_dir / "01_phoenix_az_study_area.gpkg"
    study_area.to_file(study_path, driver="GPKG")

    cities = pd.DataFrame(
        {
            "city_id": [1],
            "city_name": ["Phoenix"],
            "state": ["AZ"],
            "climate_group": ["hot_arid"],
            "lat": [33.4484],
            "lon": [-112.074],
        }
    )

    summary = export_appeears_aois(cities=cities, study_areas_dir=study_areas_dir, aoi_dir=aoi_dir)

    assert summary.iloc[0]["status"] == "exported"
    aoi_path = Path(summary.iloc[0]["aoi_path"])
    assert aoi_path.exists()

    exported = gpd.read_file(aoi_path)
    assert exported.crs is not None
    assert exported.crs.to_epsg() == 4326
    assert len(exported) == 1


def test_export_appeears_aois_marks_missing_study_area_blocked(tmp_path: Path):
    cities = pd.DataFrame(
        {
            "city_id": [99],
            "city_name": ["Missing City"],
            "state": ["ZZ"],
            "climate_group": ["mild_cool"],
            "lat": [0.0],
            "lon": [0.0],
        }
    )

    summary = export_appeears_aois(cities=cities, study_areas_dir=tmp_path / "none", aoi_dir=tmp_path / "aois")
    assert summary.iloc[0]["status"] == "blocked"
    assert summary.iloc[0]["error"] == "study_area_missing"
