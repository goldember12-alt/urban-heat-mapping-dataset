import pandas as pd

from src.config import CITIES_CSV


REQUIRED_COLUMNS = ["city_id", "city_name", "state", "climate_group", "lat", "lon"]


def load_cities() -> pd.DataFrame:
    df = pd.read_csv(CITIES_CSV)

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"cities.csv is missing required columns: {missing}")

    return df[REQUIRED_COLUMNS].copy()