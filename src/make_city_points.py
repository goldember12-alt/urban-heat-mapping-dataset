import geopandas as gpd
from shapely.geometry import Point

from src.load_cities import load_cities


def make_city_points() -> gpd.GeoDataFrame:
    df = load_cities()

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["lon"], df["lat"]),
        crs="EPSG:4326",
    )

    return gdf