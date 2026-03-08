from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.feature_assembly import FeatureSourceConfig, assemble_city_features


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract features for one city from available source layers.")
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--city-name", type=str, help="City name from cities.csv")
    selector.add_argument("--city-id", type=int, help="City ID from cities.csv")

    parser.add_argument("--resolution", type=float, default=30, help="Grid resolution in meters")
    parser.add_argument("--no-save", action="store_true", help="Run extraction without writing outputs")
    parser.add_argument(
        "--max-cells",
        type=int,
        default=0,
        help="Optional limit on number of grid cells to process (for partial/debug runs)",
    )

    parser.add_argument("--dem-raster", type=str, default="", help="Optional DEM raster path")
    parser.add_argument("--nlcd-land-cover-raster", type=str, default="", help="Optional NLCD land-cover raster path")
    parser.add_argument("--nlcd-impervious-raster", type=str, default="", help="Optional NLCD impervious raster path")
    parser.add_argument("--hydro-vector", type=str, default="", help="Optional hydro vector path")
    parser.add_argument("--ndvi-rasters", type=str, default="", help="Optional comma-separated NDVI raster paths")
    parser.add_argument("--lst-rasters", type=str, default="", help="Optional comma-separated ECOSTRESS/LST raster paths")
    return parser


def _optional_path(value: str) -> Path | None:
    value = value.strip()
    return Path(value) if value else None


def _optional_path_list(value: str) -> list[Path]:
    if not value.strip():
        return []
    return [Path(x.strip()) for x in value.split(",") if x.strip()]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()

    use_manual_sources = any(
        [
            args.dem_raster,
            args.nlcd_land_cover_raster,
            args.nlcd_impervious_raster,
            args.hydro_vector,
            args.ndvi_rasters,
            args.lst_rasters,
        ]
    )

    sources = None
    if use_manual_sources:
        sources = FeatureSourceConfig(
            dem_raster=_optional_path(args.dem_raster),
            nlcd_land_cover_raster=_optional_path(args.nlcd_land_cover_raster),
            nlcd_impervious_raster=_optional_path(args.nlcd_impervious_raster),
            hydro_vector=_optional_path(args.hydro_vector),
            ndvi_rasters=_optional_path_list(args.ndvi_rasters),
            lst_rasters=_optional_path_list(args.lst_rasters),
        )

    max_cells = args.max_cells if args.max_cells > 0 else None
    result = assemble_city_features(
        city_name=args.city_name,
        city_id=args.city_id,
        resolution=args.resolution,
        feature_sources=sources,
        save_outputs=not args.no_save,
        max_cells=max_cells,
    )

    print(f"city_id={int(result.city['city_id'])} city_name={result.city['city_name']}")
    print(f"rows={result.n_rows}")
    print(f"blocked_stages={';'.join(result.blocked_stages)}")
    if result.city_features_gpkg_path:
        print(result.city_features_gpkg_path)
    if result.city_features_parquet_path:
        print(result.city_features_parquet_path)


if __name__ == "__main__":
    main()
