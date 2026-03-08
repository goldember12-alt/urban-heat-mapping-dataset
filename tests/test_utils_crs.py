import geopandas as gpd
from shapely.geometry import Point

from src.utils_crs import (
    get_utm_crs_for_lon_lat,
    reproject_to_local_utm,
    utm_epsg_from_lon_lat,
)



def test_utm_epsg_from_lon_lat_northern_hemisphere():
    assert utm_epsg_from_lon_lat(-112.0740, 33.4484) == 32612



def test_utm_epsg_from_lon_lat_southern_hemisphere():
    assert utm_epsg_from_lon_lat(151.2093, -33.8688) == 32756



def test_get_utm_crs_for_lon_lat_returns_expected_epsg():
    crs = get_utm_crs_for_lon_lat(-80.1918, 25.7617)
    assert crs.to_epsg() == 32617



def test_reproject_to_local_utm_changes_to_projected_crs():
    gdf = gpd.GeoDataFrame(
        {"city": ["Phoenix"]},
        geometry=[Point(-112.0740, 33.4484)],
        crs="EPSG:4326",
    )

    out = reproject_to_local_utm(gdf)
    assert out.crs.to_epsg() == 32612
    assert out.crs.is_projected
