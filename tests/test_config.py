from src.config import PROJECT_ROOT, DATA_RAW, DATA_PROCESSED, CITIES_CSV


def test_project_root_exists():
    assert PROJECT_ROOT.exists()


def test_data_directories_exist():
    assert DATA_RAW.exists()
    assert DATA_PROCESSED.exists()


def test_cities_csv_exists():
    assert CITIES_CSV.exists()