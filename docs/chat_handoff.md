# Chat Handoff - Urban Heat Mapping Dataset Project

## Project Goal

Build a reproducible Python geospatial workflow to create a 30 m cell-level urban heat dataset for 30 U.S. cities across three climate groups (hot_arid, hot_humid, mild_cool).

The intended final analytic unit is one row per 30 m grid cell per city.

## What Is Completed

The boundary + grid foundation is now modular and working.

- Repository structure, config, and testing scaffold are in place.
- `cities.csv` is present and loads correctly.
- City center point workflow is implemented and saved to GeoPackage.
- Study city point figure generation works.
- Census TIGERweb urban area lookup works.
- Buffered study area creation (local projected CRS, meter-based buffer) works.
- 30 m grid generation was optimized and is working for large-city cases (including Phoenix workflow use).
- Reusable single-city processing pipeline was implemented.
- CLI entrypoint for processing one city was added.
- Documentation pages (`README.md`, `docs/workflow.md`, `docs/data_dictionary.md`) were updated for this stage.
- Test suite currently passes.

## Implemented Reusable Pipeline

Core module:

- `src/city_processing.py`

Key reusable functions:

- `load_city_record(city_name=None, city_id=None)`
- `fetch_city_urban_area(city, timeout=60)`
- `build_city_study_area(city, buffer_m=2000, timeout=60)`
- `build_city_grid(study_area_gdf, resolution=30)`
- `city_output_paths(...)`
- `save_city_processing_outputs(...)`
- `process_city(...)`

Grid creation uses the optimized method in `src/grid.py` (rasterized mask + vectorized geometry construction; no full-grid geopandas overlay).

## CLI Entrypoint

- `python -m src.run_city_processing --city-name Phoenix`
- `python -m src.run_city_processing --city-id 1`

Optional flags:

- `--buffer-m`
- `--resolution`
- `--timeout`
- `--no-save`

## Current Output Structure

Implemented output folders:

- `data_processed/study_areas/`
- `data_processed/city_grids/`

Also present from earlier stage:

- `data_processed/city_points/city_points.gpkg`
- `figures/study_city_points.png`

Current workspace also contains Phoenix stage-1 artifacts (study area + grid) and a Phoenix debug figure.

## Testing Status (Verified)

As of March 8, 2026:

- `30 passed, 4 warnings` via `pytest -q`

Warnings are deprecation notices from `src/utils_crs.py` (`unary_union` -> `union_all`) and do not currently break functionality.

## Not Started Yet (Intentionally)

These stages are not implemented yet:

- NLCD ingestion/alignment
- DEM ingestion/alignment
- Hydrography distance-to-water raster
- NDVI processing
- ECOSTRESS/AppEEARS LST processing
- Per-city feature assembly in `data_processed/city_features/`
- Final merged outputs:
  - `data_processed/final/final_dataset.parquet`
  - `data_processed/final/final_dataset.csv`

## Immediate Next Step

Scale `process_city(...)` from one-city CLI runs to a batch runner over all 30 cities, then begin raster alignment/extraction stages using the saved per-city study areas and master grids.
