from __future__ import annotations

import argparse
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import pandas as pd

from src.boundaries import fetch_urban_area_for_point, make_buffered_study_area
from src.config import CITY_GRIDS, STUDY_AREAS
from src.grid import create_grid_from_polygon
from src.load_cities import load_cities

logger = logging.getLogger(__name__)

CORE_GEOMETRY_WKT_COLUMN = "core_geometry_wkt"
CORE_GEOMETRY_CRS_COLUMN = "core_geometry_crs"


@dataclass(frozen=True)
class CityProcessingResult:
    city: pd.Series
    urban_area: gpd.GeoDataFrame
    study_area: gpd.GeoDataFrame
    grid: gpd.GeoDataFrame
    study_area_path: Path | None
    grid_path: Path | None


def _city_slug(city_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", city_name.strip().lower()).strip("_")


def load_city_record(
    city_name: str | None = None,
    city_id: int | None = None,
) -> pd.Series:
    """Load one city row from cities.csv by city name or city_id."""
    if (city_name is None) == (city_id is None):
        raise ValueError("Provide exactly one of city_name or city_id")

    cities = load_cities()

    if city_id is not None:
        matches = cities[cities["city_id"] == city_id]
    else:
        name_norm = city_name.strip().lower() if city_name is not None else ""
        matches = cities[cities["city_name"].str.lower() == name_norm]

    if matches.empty:
        raise ValueError(f"City not found for city_name={city_name!r}, city_id={city_id!r}")

    if len(matches) > 1:
        raise ValueError(f"Expected one city match but found {len(matches)}")

    return matches.iloc[0].copy()


def fetch_city_urban_area(city: pd.Series, timeout: int = 60) -> gpd.GeoDataFrame:
    """Fetch the Census urban area polygon containing the selected city center."""
    result = fetch_urban_area_for_point(lon=float(city["lon"]), lat=float(city["lat"]), timeout=timeout)
    urban_area = result.geodataframe.copy()
    urban_area["city_id"] = int(city["city_id"])
    urban_area["city_name"] = str(city["city_name"])
    urban_area["state"] = str(city["state"])
    urban_area["climate_group"] = str(city["climate_group"])
    urban_area["urban_geoid"] = result.geoid
    urban_area["urban_name"] = result.name
    return urban_area


def _study_area_from_urban_area(
    city: pd.Series,
    urban_area: gpd.GeoDataFrame,
    buffer_m: float,
) -> gpd.GeoDataFrame:
    """Attach city metadata and persisted core geometry to the buffered study area."""
    study_area = make_buffered_study_area(urban_area, buffer_m=buffer_m)
    core_geometry = urban_area.to_crs(study_area.crs).geometry.union_all()

    study_area["city_id"] = int(city["city_id"])
    study_area["city_name"] = str(city["city_name"])
    study_area["state"] = str(city["state"])
    study_area["climate_group"] = str(city["climate_group"])
    study_area["buffer_m"] = float(buffer_m)
    study_area[CORE_GEOMETRY_WKT_COLUMN] = core_geometry.wkt
    study_area[CORE_GEOMETRY_CRS_COLUMN] = study_area.crs.to_string()
    return study_area


def build_city_study_area(
    city: pd.Series,
    buffer_m: float = 2000,
    timeout: int = 60,
) -> gpd.GeoDataFrame:
    """Build a buffered study area in local projected CRS for one city."""
    urban_area = fetch_city_urban_area(city=city, timeout=timeout)
    return _study_area_from_urban_area(city=city, urban_area=urban_area, buffer_m=buffer_m)


def build_city_grid(study_area_gdf: gpd.GeoDataFrame, resolution: float = 30) -> gpd.GeoDataFrame:
    """Build the city grid from a projected study area polygon."""
    return create_grid_from_polygon(study_area_gdf, resolution=resolution)


def city_output_paths(
    city: pd.Series,
    resolution: float = 30,
    study_areas_dir: Path = STUDY_AREAS,
    city_grids_dir: Path = CITY_GRIDS,
) -> tuple[Path, Path]:
    """Return output paths for one city study area and grid files."""
    stem = f"{int(city['city_id']):02d}_{_city_slug(str(city['city_name']))}_{str(city['state']).lower()}"
    study_path = study_areas_dir / f"{stem}_study_area.gpkg"
    grid_path = city_grids_dir / f"{stem}_grid_{int(resolution)}m.gpkg"
    return study_path, grid_path


def save_city_processing_outputs(
    city: pd.Series,
    study_area_gdf: gpd.GeoDataFrame,
    grid_gdf: gpd.GeoDataFrame,
    resolution: float = 30,
    study_areas_dir: Path = STUDY_AREAS,
    city_grids_dir: Path = CITY_GRIDS,
) -> tuple[Path, Path]:
    """Save one city's study area and grid to GeoPackage files."""
    study_areas_dir.mkdir(parents=True, exist_ok=True)
    city_grids_dir.mkdir(parents=True, exist_ok=True)

    study_path, grid_path = city_output_paths(
        city=city,
        resolution=resolution,
        study_areas_dir=study_areas_dir,
        city_grids_dir=city_grids_dir,
    )

    study_area_gdf.to_file(study_path, driver="GPKG")
    grid_gdf.to_file(grid_path, driver="GPKG")

    logger.info("Saved study area to %s", study_path)
    logger.info("Saved city grid to %s", grid_path)
    return study_path, grid_path


def process_city(
    city_name: str | None = None,
    city_id: int | None = None,
    buffer_m: float = 2000,
    resolution: float = 30,
    timeout: int = 60,
    save_outputs: bool = True,
    study_areas_dir: Path = STUDY_AREAS,
    city_grids_dir: Path = CITY_GRIDS,
) -> CityProcessingResult:
    """Run boundary + buffered study area + grid processing for one city."""
    city = load_city_record(city_name=city_name, city_id=city_id)
    logger.info("Processing city %s (%s)", city["city_name"], city["state"])

    urban_area = fetch_city_urban_area(city=city, timeout=timeout)
    study_area = _study_area_from_urban_area(city=city, urban_area=urban_area, buffer_m=buffer_m)

    grid = build_city_grid(study_area, resolution=resolution)

    study_path: Path | None = None
    grid_path: Path | None = None
    if save_outputs:
        study_path, grid_path = save_city_processing_outputs(
            city=city,
            study_area_gdf=study_area,
            grid_gdf=grid,
            resolution=resolution,
            study_areas_dir=study_areas_dir,
            city_grids_dir=city_grids_dir,
        )

    return CityProcessingResult(
        city=city,
        urban_area=urban_area,
        study_area=study_area,
        grid=grid,
        study_area_path=study_path,
        grid_path=grid_path,
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Process one city study area and 30 m grid.")
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--city-name", type=str, help="City name from cities.csv (exact match)")
    selector.add_argument("--city-id", type=int, help="City ID from cities.csv")

    parser.add_argument("--buffer-m", type=float, default=2000, help="Study area buffer in meters")
    parser.add_argument("--resolution", type=float, default=30, help="Grid resolution in meters")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout for Census query in seconds")
    parser.add_argument("--no-save", action="store_true", help="Run processing without writing files")
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = _build_arg_parser()
    args = parser.parse_args()

    result = process_city(
        city_name=args.city_name,
        city_id=args.city_id,
        buffer_m=args.buffer_m,
        resolution=args.resolution,
        timeout=args.timeout,
        save_outputs=not args.no_save,
    )

    print(f"city_id={int(result.city['city_id'])} city_name={result.city['city_name']}")
    print(f"study_area_crs={result.study_area.crs}")
    print(f"grid_cells={len(result.grid)}")
    if result.study_area_path is not None:
        print(result.study_area_path)
    if result.grid_path is not None:
        print(result.grid_path)


if __name__ == "__main__":
    main()
