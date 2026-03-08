from math import floor

import geopandas as gpd
from pyproj import CRS

WGS84_EPSG = 4326


def utm_epsg_from_lon_lat(lon: float, lat: float) -> int:
    """Return the EPSG code for the UTM zone containing a lon/lat point."""
    zone = int(floor((lon + 180) / 6) + 1)
    if lat >= 0:
        return 32600 + zone
    return 32700 + zone



def get_utm_crs_for_lon_lat(lon: float, lat: float) -> CRS:
    """Return a pyproj CRS object for the local UTM zone of a lon/lat point."""
    return CRS.from_epsg(utm_epsg_from_lon_lat(lon, lat))



def reproject_to_local_utm(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Reproject a GeoDataFrame to the local UTM CRS based on its centroid.

    The input GeoDataFrame must have a geographic CRS.
    """
    if gdf.empty:
        raise ValueError("Input GeoDataFrame is empty.")
    if gdf.crs is None:
        raise ValueError("Input GeoDataFrame has no CRS.")
    if not CRS.from_user_input(gdf.crs).is_geographic:
        raise ValueError("Input GeoDataFrame must have a geographic CRS before UTM reprojection.")

    centroid = gdf.to_crs(epsg=WGS84_EPSG).unary_union.centroid
    utm_crs = get_utm_crs_for_lon_lat(centroid.x, centroid.y)
    return gdf.to_crs(utm_crs)
