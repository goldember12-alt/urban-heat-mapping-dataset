import os
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
INTERMEDIATE = DATA_PROCESSED / "intermediate"
APPEEARS_AOI = DATA_PROCESSED / "appeears_aoi"
APPEEARS_STATUS = DATA_PROCESSED / "appeears_status"
SUPPORT_LAYERS = DATA_PROCESSED / "support_layers"

# Common raw-data subfolders (optional; used when source files are available)
RAW_DEM = DATA_RAW / "dem"
RAW_NLCD = DATA_RAW / "nlcd"
RAW_HYDRO = DATA_RAW / "hydro"
RAW_NDVI = DATA_RAW / "ndvi"
RAW_ECOSTRESS = DATA_RAW / "ecostress"

# Input files
CITIES_CSV = PROJECT_ROOT / "cities.csv"

# AppEEARS defaults and environment-variable names
APPEEARS_BASE_URL = os.getenv("APPEEARS_BASE_URL", "https://appeears.earthdatacloud.nasa.gov/api")
APPEEARS_TOKEN_ENV = "APPEEARS_API_TOKEN"
EARTHDATA_USERNAME_ENV = "EARTHDATA_USERNAME"
EARTHDATA_PASSWORD_ENV = "EARTHDATA_PASSWORD"

NDVI_DEFAULT_PRODUCT = "MOD13A1.061"
NDVI_DEFAULT_LAYER = "_500m_16_days_NDVI"

ECOSTRESS_PRODUCT_CANDIDATES = ("ECO_L2T_LSTE.002", "ECO_L2_LSTE.002")
ECOSTRESS_DEFAULT_LAYER = "LST"
