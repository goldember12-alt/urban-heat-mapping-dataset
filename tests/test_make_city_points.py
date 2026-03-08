from src.make_city_points import make_city_points


def test_make_city_points_returns_geodataframe():
    gdf = make_city_points()
    assert len(gdf) == 30
    assert gdf.geometry is not None


def test_make_city_points_has_wgs84_crs():
    gdf = make_city_points()
    assert gdf.crs.to_string() == "EPSG:4326"


def test_all_geometries_are_points():
    gdf = make_city_points()
    assert (gdf.geometry.geom_type == "Point").all()