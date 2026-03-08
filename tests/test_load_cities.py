from src.load_cities import load_cities


def test_load_cities_returns_dataframe():
    df = load_cities()
    assert len(df) == 30
    assert "city_name" in df.columns
    assert "lat" in df.columns
    assert "lon" in df.columns


def test_city_ids_are_unique():
    df = load_cities()
    assert df["city_id"].is_unique


def test_no_missing_coordinates():
    df = load_cities()
    assert df["lat"].notna().all()
    assert df["lon"].notna().all()