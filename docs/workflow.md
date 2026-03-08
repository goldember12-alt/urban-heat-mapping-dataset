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

One city:

```powershell
.venv\Scripts\python.exe -m src.run_city_processing --city-id 1 --resolution 30
```

All 30 cities:

```powershell
.venv\Scripts\python.exe -m src.run_city_batch_processing --resolution 30
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

## Stage 5: Support-Layer Preflight Audit

1. Load the expected city list from `cities.csv`.
2. Compute deterministic expected study-area, grid, raw support-input, and prepared support-output paths for each city.
3. Audit city-specific raw support folders:
   - `data_raw/dem/<city_slug>/<city_slug>_dem_3dep_30m.tif`
   - `data_raw/nlcd/<city_slug>/<city_slug>_nlcd_2021_land_cover_30m.tif`
   - `data_raw/nlcd/<city_slug>/<city_slug>_nlcd_2021_impervious_30m.tif`
   - `data_raw/hydro/<city_slug>/<city_slug>_nhdplus_water.gpkg`
4. Report whether each city is ready for support-layer prep and whether it is already ready for feature extraction.
5. Write machine-readable preflight outputs:
   - `data_processed/support_layers/support_layers_preflight_summary.json|csv`

CLI:

```powershell
.venv\Scripts\python.exe -m src.run_support_layers --preflight-only
```

Raw-input population status:

- Automated today: prerequisite auditing and downstream prep once files exist.
- Manual today: obtaining and placing DEM, NLCD land-cover, NLCD impervious, and hydro source files into the deterministic per-city raw paths audited above.
- Reproducible procedure: populate the audited raw paths, rerun `src.run_support_layers --preflight-only`, then run `src.run_support_layers` for the same city set.

## Stage 6: Support-Layer Prep

1. Read deterministic city-specific raw support files.
2. Clip DEM, NLCD land cover, NLCD impervious, and hydro inputs to the city study area.
3. Save deterministic prepared outputs under `data_processed/support_layers/<city_stem>/`:
   - `dem_prepared.tif`
   - `nlcd_land_cover_prepared.tif`
   - `nlcd_impervious_prepared.tif`
   - `hydro_water_prepared.gpkg`
4. Write machine-readable prep outputs:
   - `data_processed/support_layers/support_layers_prep_summary.json|csv`

CLI:

```powershell
.venv\Scripts\python.exe -m src.run_support_layers --city-ids 1
```

```powershell
.venv\Scripts\python.exe -m src.run_support_layers
```

Optional mode:

- `--overwrite`

## Stage 7: Generic Raster Alignment Framework

For each city grid:

1. Build grid-aligned raster template from grid CRS, extent, and resolution.
2. Reproject source rasters to this template.
3. Extract one value per grid cell from aligned arrays.
4. Optionally save aligned raster artifacts in `data_processed/intermediate/aligned_rasters/`.

Core module: `src/raster_features.py`

## Stage 8: DEM Feature Extraction

- Prefer prepared DEM support output when present.
- Otherwise fall back to the existing city raw DEM discovery path.
- Align DEM raster to city template.
- Extract `elevation_m` for each grid cell centroid index.

## Stage 9: NLCD Extraction

- Prefer prepared NLCD support outputs when present.
- Otherwise fall back to the existing city raw NLCD discovery path.
- Align NLCD land-cover raster and extract `land_cover_class` (nearest-neighbor).
- Align NLCD impervious raster and extract `impervious_pct`.

## Stage 10: Hydrography Distance-To-Water

- Prefer prepared hydro support output when present.
- Otherwise fall back to the existing city raw hydro discovery path.
- Rasterize hydro geometries to city template.
- Compute Euclidean distance transform (meters).
- Extract `dist_to_water_m` per grid cell.

Core module: `src/water_features.py`

## Stage 11: Per-City Feature Assembly

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

## Stage 12: Final Dataset Merge

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


