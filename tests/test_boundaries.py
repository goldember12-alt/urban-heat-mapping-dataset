from urllib.parse import parse_qs, urlparse

import geopandas as gpd
from shapely.geometry import Polygon

from src.boundaries import build_urban_area_query_url, make_buffered_study_area



def test_build_urban_area_query_url_contains_expected_params():
    url = build_urban_area_query_url(-112.0740, 33.4484)
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    assert "Census2020/Urban/MapServer/1/query" in parsed.path
    assert query["f"] == ["geojson"]
    assert query["geometry"] == ["-112.074,33.4484"]
    assert query["geometryType"] == ["esriGeometryPoint"]



def test_make_buffered_study_area_returns_projected_polygon():
    gdf = gpd.GeoDataFrame(
        {"name": ["sample"]},
        geometry=[Polygon([(-112.08, 33.44), (-112.07, 33.44), (-112.07, 33.45), (-112.08, 33.45)])],
        crs="EPSG:4326",
    )

    buffered = make_buffered_study_area(gdf, buffer_m=2000)
    assert buffered.crs.is_projected
    assert buffered.geometry.iloc[0].geom_type == "Polygon"
