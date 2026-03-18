# STAT 5630 Final Project - Urban Heat Dataset Construction

## Project Overview

This repository builds a reproducible Python geospatial workflow for constructing a cross-city urban heat dataset for 30 U.S. cities.

Target analytic unit: one row per 30 m grid cell per city.

## Implemented Pipeline Stages

1. City boundary and 2 km buffered study area construction from Census urban-area lookup.
2. Master 30 m city grid generation.
3. Batch city boundary/grid runner.
4. AppEEARS prerequisite preflight audit for all expected cities.
5. AppEEARS AOI export from city study areas (`data_processed/appeears_aoi/*.geojson`, EPSG:4326).
6. AppEEARS acquisition runner (submit, poll, download, resumable state) for NDVI and ECOSTRESS.
7. Support-layer preflight audit for DEM, NLCD land cover, NLCD impervious, and hydro inputs.
8. Raw support-layer acquisition runner for official USGS 3DEP, MRLC Annual NLCD, and USGS NHDPlus HR sources.
9. Support-layer prep runner that clips deterministic per-city support files into `data_processed/support_layers/<city_stem>/`.
10. Thin acquisition orchestrator that sequences raw support acquisition, support prep, NDVI AppEEARS, ECOSTRESS AppEEARS, and writes a restart-safe status summary.
11. Full-stack city orchestrator that extends the acquisition flow through feature assembly with per-city stage statuses and restart-safe skip/fail reasons.
12. Generic raster alignment framework to city grid template.
13. DEM extraction (aligned).
14. NLCD land-cover and impervious extraction (aligned).
15. Hydrography distance-to-water raster generation and extraction.
16. Per-city feature assembly outputs (`.gpkg` + `.parquet`) with intermediate saves.
17. Final merged dataset assembly (`.parquet` + `.csv`) with row rules and `hotspot_10pct`.

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

Recommended local operator pattern:

- Store local secrets in a gitignored `.env.local` file.
- Load it into the current PowerShell session before running AppEEARS-dependent commands:

```powershell
Get-Content .env.local | Where-Object { $_ -match '^\s*[^#].+=' } | ForEach-Object {
    $name, $value = $_ -split '=', 2
    Set-Item -Path "Env:$name" -Value $value
}
```

- If credentials are absent, AppEEARS-dependent stages now fail fast with `blocked_missing_credentials` and list the exact missing environment variables, while raw/support stages continue when possible.

## Support-Layer Standardization

The repo now treats support layers as a deterministic per-city raw-input contract, matching the existing Phoenix layout and feature-discovery assumptions:

- `data_raw/dem/<city_slug>/<city_slug>_dem_3dep_30m.tif`
- `data_raw/nlcd/<city_slug>/<city_slug>_nlcd_2021_land_cover_30m.tif`
- `data_raw/nlcd/<city_slug>/<city_slug>_nlcd_2021_impervious_30m.tif`
- `data_raw/hydro/<city_slug>/<city_slug>_nhdplus_water.gpkg`

The raw acquisition stage caches reusable upstream downloads under `data_raw/cache/` and then clips deterministic city-specific outputs into the raw contract above.

The standardized prep stage keeps those raw files immutable and writes deterministic prepared outputs to:

- `data_processed/support_layers/<city_stem>/dem_prepared.tif`
- `data_processed/support_layers/<city_stem>/nlcd_land_cover_prepared.tif`
- `data_processed/support_layers/<city_stem>/nlcd_impervious_prepared.tif`
- `data_processed/support_layers/<city_stem>/hydro_water_prepared.gpkg`

`src.feature_assembly` now prefers prepared support outputs when they exist and otherwise falls back to the existing raw-folder discovery behavior.
AppEEARS raster discovery is product-aware: native filenames such as `MOD13A1...NDVI...tif` and `ECO_L2T_LSTE...LST...tif` are treated as value rasters, while obvious QA/cloud/error sidecars are excluded.

## Empty City To Support-Layer-Ready City

Automated:

- Study areas and 30 m grids are already automated for one city via `src.run_city_processing` and for all 30 cities via `src.run_city_batch_processing`.
- The prerequisite audit is automated via `src.run_support_layers --preflight-only`.
- Raw support-layer acquisition is automated via `src.run_raw_data_acquisition`.
- Support-layer clipping/prep is automated via `src.run_support_layers`.

Operational notes:

- The MRLC Annual NLCD cache downloads are large and are intentionally reused across cities.
- The raw acquisition runner is restartable: it skips completed deterministic outputs unless `--force` is passed and reuses cached DEM tiles, NLCD bundles, and NHDPlus HR packages.
- Use `data_processed/support_layers/raw_data_acquisition_summary.csv` as the canonical machine-readable status summary for the new acquisition stage.
- After raw acquisition completes, rerun `src.run_support_layers --preflight-only` and then run `src.run_support_layers` for the same city set.

## CLI Entrypoints

Initial city points + figure:

```powershell
.venv\Scripts\python.exe -m src.run_initial_outputs
```

One city boundary/grid:

```powershell
.venv\Scripts\python.exe -m src.run_city_processing --city-name Phoenix
```

All-city boundary/grid:

```powershell
.venv\Scripts\python.exe -m src.run_city_batch_processing --resolution 30
```

AppEEARS preflight only:

```powershell
.venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ndvi --preflight-only
```

AppEEARS acquisition:

```powershell
.venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ndvi --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31
```

```powershell
.venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ecostress --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31
```

```powershell
.venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ndvi --start-date 2023-05-01 --end-date 2023-08-31 --retry-incomplete
```

Support-layer preflight only:

```powershell
.venv\Scripts\python.exe -m src.run_support_layers --preflight-only
```

Acquire raw support layers for all currently missing cities:

```powershell
.venv\Scripts\python.exe -m src.run_raw_data_acquisition --all-missing
```

Acquire one dataset group for selected cities:

```powershell
.venv\Scripts\python.exe -m src.run_raw_data_acquisition --city-ids 1 2 3 --dataset dem
```

```powershell
.venv\Scripts\python.exe -m src.run_raw_data_acquisition --dataset nlcd --all-missing
```

```powershell
.venv\Scripts\python.exe -m src.run_raw_data_acquisition --dataset hydro --all-missing
```

Force rebuilding requested deterministic raw outputs:

```powershell
.venv\Scripts\python.exe -m src.run_raw_data_acquisition --city-ids 1 --force
```

Prepare support layers for one city:

```powershell
.venv\Scripts\python.exe -m src.run_support_layers --city-ids 1
```

Prepare support layers for all cities:

```powershell
.venv\Scripts\python.exe -m src.run_support_layers
```

Supported support-layer mode flag:

- `--preflight-only`
- `--overwrite`

Supported raw acquisition mode flags:

- `--all-missing`
- `--dataset {all,dem,nlcd,hydro}`
- `--force`

Supported AppEEARS acquisition modes:

- `--preflight-only`
- `--submit-only`
- `--poll-only`
- `--download-only`
- `--retry-incomplete`

Thin acquisition orchestrator:

```powershell
.venv\Scripts\python.exe -m src.run_acquisition_orchestration --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31
```

```powershell
.venv\Scripts\python.exe -m src.run_acquisition_orchestration --all-missing --start-date 2023-05-01 --end-date 2023-08-31
```

Optional orchestrator mode flags:

- `--all-missing`
- `--force-raw`
- `--overwrite-support`

Verification note from the moved Windows workspace on 2026-03-18: the Phoenix orchestration command completed and rewrote the orchestration/AppEEARS summary files with the new OneDrive-backed paths, but the Phoenix raw NDVI and ECOSTRESS `.tif` timestamps remained at 2026-03-08. Treat that as restart/resume validation of the moved workspace, not as proof of a fresh AppEEARS submit/download on 2026-03-18.

Full-stack city orchestration:

```powershell
.venv\Scripts\python.exe -m src.run_full_stack_orchestration --city-ids 2,3,4 --start-date 2023-05-01 --end-date 2023-08-31
```

```powershell
.venv\Scripts\python.exe -m src.run_full_stack_orchestration --all-missing --start-date 2023-05-01 --end-date 2023-08-31
```

Full-stack status output:

- `data_processed/orchestration/full_stack_city_orchestration_summary.json`
- `data_processed/orchestration/full_stack_city_orchestration_summary.csv`

Per-city stage columns include raw support, support prep, NDVI, ECOSTRESS, and feature assembly statuses plus `error` and `message` fields. The feature stage only runs when upstream support and AppEEARS stages are complete or safely reusable.

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
- `data_raw/cache/` reusable upstream download/extraction cache for DEM, NLCD, and hydro packages
- `data_raw/dem/<city_slug>/` city-specific DEM source files
- `data_raw/nlcd/<city_slug>/` city-specific NLCD land-cover and impervious source files
- `data_raw/hydro/<city_slug>/` city-specific hydro source files
- `data_raw/ndvi/<city_slug>/` downloaded AppEEARS NDVI files
- `data_raw/ecostress/<city_slug>/` downloaded AppEEARS ECOSTRESS files
- `data_processed/study_areas/` city buffered study areas
- `data_processed/appeears_aoi/` AppEEARS AOI GeoJSON exports
- `data_processed/appeears_status/` preflight JSON/CSV plus acquisition summary JSON/CSV per product type
- `data_processed/orchestration/` thin acquisition orchestration summary JSON/CSV
- `data_processed/orchestration/` full-stack city orchestration summary JSON/CSV
- `data_processed/support_layers/` support-layer preflight summary, raw acquisition summary, prep summary, and per-city prepared support artifacts
- `data_processed/city_grids/` city master grids
- `data_processed/intermediate/` aligned rasters + unfiltered/filtered city feature tables
- `data_processed/city_features/` per-city feature outputs + batch summary
- `data_processed/final/` merged dataset outputs
- `docs/` workflow and data dictionary
- `tests/` automated tests
