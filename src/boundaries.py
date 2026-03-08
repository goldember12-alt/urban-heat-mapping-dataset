from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode

import geopandas as gpd
import requests
from shapely.geometry import shape

from src.utils_crs import reproject_to_local_utm

TIGERWEB_URBAN_LAYER_URL = (
    "https://tigerweb.geo.census.gov/arcgis/rest/services/Census2020/Urban/MapServer/1/query"
)


@dataclass(frozen=True)
class UrbanAreaQueryResult:
    geoid: str
    name: str
    geodataframe: gpd.GeoDataFrame


def build_urban_area_query_url(lon: float, lat: float) -> str:
    """Build the Census TIGERweb query URL for the urban area containing a point."""
    params = {
        "f": "geojson",
        "where": "1=1",
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "returnGeometry": "true",
        "outFields": "GEOID,UA,BASENAME,NAME,OBJECTID",
        "resultRecordCount": 1,
    }
    return f"{TIGERWEB_URBAN_LAYER_URL}?{urlencode(params)}"


def fetch_urban_area_for_point(
    lon: float,
    lat: float,
    timeout: int = 60,
) -> UrbanAreaQueryResult:
    """Fetch the Census 2020 urban area polygon containing a point."""
    url = build_urban_area_query_url(lon, lat)
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    payload = response.json()

    features = payload.get("features", [])
    if not features:
        raise ValueError(f"No urban area found for point ({lat}, {lon}).")

    feature = features[0]
    props = feature.get("properties", {})
    geom = shape(feature["geometry"])

    gdf = gpd.GeoDataFrame([props], geometry=[geom], crs="EPSG:4326")
    geoid = str(props.get("GEOID") or props.get("UA") or "")
    name = props.get("NAME") or props.get("BASENAME") or "Unknown Urban Area"

    return UrbanAreaQueryResult(geoid=geoid, name=name, geodataframe=gdf)


def fetch_urban_area_by_point(
    lon: float,
    lat: float,
    timeout: int = 60,
) -> gpd.GeoDataFrame:
    result = fetch_urban_area_for_point(lon=lon, lat=lat, timeout=timeout)
    return result.geodataframe


def make_buffered_study_area(
    urban_area_gdf: gpd.GeoDataFrame,
    buffer_m: float = 2000,
) -> gpd.GeoDataFrame:
    if urban_area_gdf.empty:
        raise ValueError("urban_area_gdf is empty")

    projected = reproject_to_local_utm(urban_area_gdf)
    buffered = projected.copy()
    buffered["geometry"] = projected.buffer(buffer_m)
    return buffered