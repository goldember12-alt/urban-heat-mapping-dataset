# STAT 5630 Final Project - Urban Heat Dataset Construction

## Project Overview

This repository builds a reproducible Python geospatial workflow for constructing a cross-city urban heat dataset for 30 U.S. cities.

Target analytic unit: one row per 30 m grid cell per city.

## Implemented Pipeline Stages

Implemented:

1. City boundary and 2 km buffered study area construction from Census urban-area lookup.
2. Master 30 m city grid generation.
3. Batch city boundary/grid runner.
4. Generic raster alignment framework to city grid template.
5. DEM extraction (aligned).
6. NLCD land-cover and impervious extraction (aligned).
7. Hydrography distance-to-water raster generation and extraction.
8. Per-city feature assembly outputs (`.gpkg` + `.parquet`) with intermediate saves.
9. Final merged dataset assembly (`.parquet` + `.csv`) with row rules and `hotspot_10pct`.

Wired but data-blocked in this workspace:

- NDVI median May-Aug stage (requires source rasters in `data_raw/ndvi/`).
- ECOSTRESS/AppEEARS LST median + valid-pass stage (requires source rasters in `data_raw/ecostress/`).

## Required Final Columns

- `city_id`
- `city_name`
- `climate_group`
- `cell_id`
- `centroid_lon`
- `centroid_lat`
- `impervious_pct`
- `land_cover_class`
- `elevation_m`
- `dist_to_water_m`
- `ndvi_median_may_aug`
- `lst_median_may_aug`
- `n_valid_ecostress_passes`
- `hotspot_10pct`

## Data Rules Implemented

- Drop open-water cells when NLCD land-cover class is available.
- If LST is available, drop cells with `n_valid_ecostress_passes < 3`.
- Compute `hotspot_10pct` within each city from city-level LST distribution (90th percentile threshold).

## CLI Entrypoints

Initial city points + figure:

```powershell
.venv\Scripts\python.exe -m src.run_initial_outputs
```

One city boundary/grid:

```powershell
.venv\Scripts\python.exe -m src.run_city_processing --city-name Phoenix
```

Batch boundary/grid:

```powershell
.venv\Scripts\python.exe -m src.run_city_batch_processing --city-ids 1,2,3
```

One city feature extraction:

```powershell
.venv\Scripts\python.exe -m src.run_city_features --city-id 1 --max-cells 5000
```

Batch feature extraction:

```powershell
.venv\Scripts\python.exe -m src.run_city_features_batch --existing-grids-only --city-ids 1 --max-cells 5000
```

Final merge only:

```powershell
.venv\Scripts\python.exe -m src.run_final_dataset_assembly
```

End-to-end pipeline orchestrator:

```powershell
.venv\Scripts\python.exe -m src.run_full_pipeline --skip-city-processing --existing-grids-only --city-ids 1 --max-cells 5000
```

## Data Layout

- `data_raw/` immutable source data (DEM, NLCD, hydro, NDVI, ECOSTRESS folders)
- `data_processed/study_areas/` city buffered study areas
- `data_processed/city_grids/` city master grids
- `data_processed/intermediate/` aligned rasters + unfiltered/filtered city feature tables
- `data_processed/city_features/` per-city feature outputs + batch summary
- `data_processed/final/` merged dataset outputs
- `docs/` workflow and data dictionary
- `tests/` automated tests
