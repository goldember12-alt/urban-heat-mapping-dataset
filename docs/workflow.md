# Workflow

## Stage 1: Boundary + Grid

1. Select city (`city_id` or `city_name`).
2. Query Census TIGERweb urban area containing city center.
3. Reproject to local UTM and buffer by 2 km.
4. Build 30 m master grid intersecting study area.
5. Save:
   - `data_processed/study_areas/*_study_area.gpkg`
   - `data_processed/city_grids/*_grid_30m.gpkg`

CLI:

```powershell
.venv\Scripts\python.exe -m src.run_city_batch_processing --city-ids 1,2,3
```

## Stage 2: AppEEARS Preflight Audit

1. Load the expected city list from `cities.csv`.
2. Compute deterministic expected paths for study areas, AOIs, raw NDVI folders, raw ECOSTRESS folders, and product-specific acquisition status output.
3. Check whether each expected study area exists.
4. Check whether each expected AOI exists and resolves to EPSG:4326.
5. Write machine-readable preflight outputs:
   - `data_processed/appeears_status/appeears_ndvi_preflight_summary.json|csv`
   - `data_processed/appeears_status/appeears_ecostress_preflight_summary.json|csv`

CLI:

```powershell
.venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ndvi --preflight-only
```

## Stage 3: AppEEARS AOI Export

1. Discover city study-area GeoPackages in `data_processed/study_areas/`.
2. Convert each study area polygon to EPSG:4326.
3. Export one AOI GeoJSON per city to `data_processed/appeears_aoi/`.

AOI export is executed automatically by the acquisition runner.

## Stage 4: AppEEARS Acquisition (NDVI + ECOSTRESS)

1. Authenticate with AppEEARS from environment variables only.
2. Submit area tasks per city and product/date range.
3. Poll task status.
4. Download completed bundle files to immutable raw folders:
   - `data_raw/ndvi/<city_slug>/`
   - `data_raw/ecostress/<city_slug>/`
5. Persist resumable status summaries:
   - `data_processed/appeears_status/appeears_ndvi_acquisition_summary.json|csv`
   - `data_processed/appeears_status/appeears_ecostress_acquisition_summary.json|csv`

CLI:

```powershell
.venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ndvi --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31
```

```powershell
.venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ecostress --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31
```

Modes:

- `--preflight-only`
- `--submit-only`
- `--poll-only`
- `--download-only`
- `--retry-incomplete`

## Stage 5: Generic Raster Alignment Framework

For each city grid:

1. Build grid-aligned raster template from grid CRS, extent, and resolution.
2. Reproject source rasters to this template.
3. Extract one value per grid cell from aligned arrays.
4. Optionally save aligned raster artifacts in `data_processed/intermediate/aligned_rasters/`.

Core module: `src/raster_features.py`

## Stage 6: DEM Feature Extraction

- Align DEM raster to city template.
- Extract `elevation_m` for each grid cell centroid index.

## Stage 7: NLCD Extraction

- Align NLCD land-cover raster and extract `land_cover_class` (nearest-neighbor).
- Align NLCD impervious raster and extract `impervious_pct`.

## Stage 8: Hydrography Distance-To-Water

- Rasterize hydro geometries to city template.
- Compute Euclidean distance transform (meters).
- Extract `dist_to_water_m` per grid cell.

Core module: `src/water_features.py`

## Stage 9: Per-City Feature Assembly

- Assemble city feature table from available sources.
- Save intermediate unfiltered + filtered tables:
  - `data_processed/intermediate/city_features/*_features_unfiltered.parquet`
  - `data_processed/intermediate/city_features/*_features_filtered.parquet`
- Save per-city outputs:
  - `data_processed/city_features/*_features.gpkg`
  - `data_processed/city_features/*_features.parquet`

CLI:

```powershell
.venv\Scripts\python.exe -m src.run_city_features_batch --existing-grids-only --city-ids 1 --max-cells 5000
```

## Stage 10: Final Dataset Merge

- Concatenate per-city parquet tables.
- Apply row rules:
  - drop open-water cells (if land-cover available)
  - if LST is available, drop rows with `n_valid_ecostress_passes < 3`
- Recompute `hotspot_10pct` within city.
- Save:
  - `data_processed/final/final_dataset.parquet`
  - `data_processed/final/final_dataset.csv`

CLI:

```powershell
.venv\Scripts\python.exe -m src.run_final_dataset_assembly
```

## Full Pipeline CLI

```powershell
.venv\Scripts\python.exe -m src.run_full_pipeline --skip-city-processing --existing-grids-only --city-ids 1 --max-cells 5000
```

Use `--max-cells` for partial/debug runs on very large city grids.
