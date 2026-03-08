from src.save_city_points import save_city_points


def test_save_city_points_writes_file(tmp_path):
    out_path = tmp_path / "city_points.gpkg"
    written = save_city_points(output_path=out_path)

    assert written == out_path
    assert out_path.exists()
