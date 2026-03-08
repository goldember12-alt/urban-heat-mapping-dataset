from pathlib import Path

from src.config import DATA_PROCESSED
from src.make_city_points import make_city_points


def save_city_points(output_path: Path | None = None) -> Path:
    """Save city center points as a GeoPackage and return the written path."""
    out_dir = DATA_PROCESSED / "city_points"
    out_dir.mkdir(parents=True, exist_ok=True)

    if output_path is None:
        output_path = out_dir / "city_points.gpkg"

    gdf = make_city_points()
    gdf.to_file(output_path, driver="GPKG")
    return output_path


if __name__ == "__main__":
    saved = save_city_points()
    print(f"Saved city points to: {saved}")
