from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Main folders
DATA_RAW = PROJECT_ROOT / "data_raw"
DATA_PROCESSED = PROJECT_ROOT / "data_processed"
DOCS = PROJECT_ROOT / "docs"
FIGURES = PROJECT_ROOT / "figures"
NOTEBOOKS = PROJECT_ROOT / "notebooks"
SRC = PROJECT_ROOT / "src"
TESTS = PROJECT_ROOT / "tests"

# Common processed subfolders
CITY_FEATURES = DATA_PROCESSED / "city_features"
FINAL = DATA_PROCESSED / "final"
STUDY_AREAS = DATA_PROCESSED / "study_areas"
CITY_GRIDS = DATA_PROCESSED / "city_grids"

# Input files
CITIES_CSV = PROJECT_ROOT / "cities.csv"
