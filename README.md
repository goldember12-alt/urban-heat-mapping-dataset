# STAT 5630 Final Project - Urban Heat Dataset Construction

## Project Overview

This repository builds a reproducible Python geospatial workflow for constructing a cross-city urban heat dataset for 30 U.S. cities.

Target analytic unit: one row per 30 m grid cell per city.

## Implemented Pipeline Stages

1. City boundary and 2 km buffered study area construction from Census urban-area lookup.
2. Master 30 m city grid generation.
3. Batch city boundary/grid runner.
4. AppEEARS AOI export from city study areas (`data_processed/appeears_aoi/*.geojson`, EPSG:4326).
5. AppEEARS acquisition runner (submit, poll, download, resumable state) for NDVI and ECOSTRESS.
6. Generic raster alignment framework to city grid template.
7. DEM extraction (aligned).
8. NLCD land-cover and impervious extraction (aligned).
9. Hydrography distance-to-water raster generation and extraction.
10. Per-city feature assembly outputs (`.gpkg` + `.parquet`) with intermediate saves.
11. Final merged dataset assembly (`.parquet` + `.csv`) with row rules and `hotspot_10pct`.

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

## AppEEARS Environment Variables

The acquisition CLI reads credentials from environment variables only:

- `APPEEARS_API_TOKEN` (preferred bearer token), or
- `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD`

Optional:

- `APPEEARS_BASE_URL` is not required for normal runs (default is baked into config).

Secrets are not printed in logs.

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

AppEEARS acquisition (new):

```powershell
.venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ndvi --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31
```

```powershell
.venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ecostress --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31
```

```powershell
.venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ndvi --start-date 2023-05-01 --end-date 2023-08-31 --retry-incomplete
```

Supported run modes:

- `--submit-only`
- `--poll-only`
- `--download-only`
- `--retry-incomplete`

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

- `data_raw/` immutable source data
- `data_raw/ndvi/<city_slug>/` downloaded AppEEARS NDVI files
- `data_raw/ecostress/<city_slug>/` downloaded AppEEARS ECOSTRESS files
- `data_processed/study_areas/` city buffered study areas
- `data_processed/appeears_aoi/` AppEEARS AOI GeoJSON exports
- `data_processed/appeears_status/` acquisition summary JSON/CSV per product type
- `data_processed/city_grids/` city master grids
- `data_processed/intermediate/` aligned rasters + unfiltered/filtered city feature tables
- `data_processed/city_features/` per-city feature outputs + batch summary
- `data_processed/final/` merged dataset outputs
- `docs/` workflow and data dictionary
- `tests/` automated tests
