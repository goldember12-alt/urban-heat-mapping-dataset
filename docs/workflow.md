# Workflow

## Stage 1: Boundary + Grid

1. Select city (`city_id` or `city_name`).
2. Query Census TIGERweb urban area containing city center.
3. Reproject to local UTM, preserve the original urban-core geometry as study-area metadata, and buffer by 2 km unless `--buffer-m 0` is requested.
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
3. If a submit attempt times out or drops the connection, reuse a matching server task by deterministic `task_name` when the API task list exposes it; otherwise record a recoverable failure for rerun rather than silently creating blind duplicate submissions.
4. Poll task status with retry/backoff for transient network, HTTP `408/429/5xx`, and invalid-JSON responses.
5. Download completed bundle files to immutable raw folders:
   - `data_raw/ndvi/<city_slug>/`
   - `data_raw/ecostress/<city_slug>/`
6. Persist resumable status summaries with structured `failure_reason`, `recoverable`, and `submit_decision_reason` fields:
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

## Stage 4B: Thin Acquisition Orchestration

1. Run raw support acquisition with restart-safe skipping of existing outputs.
2. Run support-layer prep, targeting either the requested city set or only cities still missing prepared support outputs.
3. Run AppEEARS NDVI acquisition with resumable retry behavior.
4. Run AppEEARS ECOSTRESS acquisition with resumable retry behavior.
5. Write a thin orchestration status summary:
   - `data_processed/orchestration/acquisition_orchestration_summary.json|csv`

CLI:

```powershell
.venv\Scripts\python.exe -m src.run_acquisition_orchestration --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31
```

```powershell
.venv\Scripts\python.exe -m src.run_acquisition_orchestration --all-missing --start-date 2023-05-01 --end-date 2023-08-31
```

Optional mode flags:

- `--all-missing`
- `--force-raw`
- `--overwrite-support`

Latest manual verification in the moved Windows workspace on 2026-03-18:

- `--city-ids 1` completed and wrote `data_processed/orchestration/acquisition_orchestration_summary.json|csv`.
- Raw support acquisition and support-layer prep reported `skipped_existing` for Phoenix.
- The NDVI and ECOSTRESS acquisition summaries were rewritten with the new workspace root, but Phoenix raw AppEEARS `.tif` timestamps stayed at 2026-03-08, so this checkpoint validates resume behavior after the move rather than a fresh live download.

Credential handling:

- AppEEARS-dependent work now performs an explicit environment preflight before client creation when the stage truly needs auth.
- Missing credentials produce `blocked_missing_credentials` with a message listing the exact missing env vars.
- Non-auth stages are not blocked by that preflight.

Recommended local operator pattern:

```powershell
Get-Content .env.local | Where-Object { $_ -match '^\s*[^#].+=' } | ForEach-Object {
    $name, $value = $_ -split '=', 2
    Set-Item -Path "Env:$name" -Value $value
}
```

## Stage 4C: Full-Stack City Orchestration

1. Select one city, many cities, or the computed `all_missing` subset.
2. Run raw support acquisition with restart-safe skip behavior.
3. Run support-layer prep with restart-safe skip behavior.
4. Run AppEEARS NDVI with resumable state and explicit missing-credential blocking.
5. Run AppEEARS ECOSTRESS with resumable state and explicit missing-credential blocking.
6. Run feature assembly only when upstream support and AppEEARS stages are complete or safely reusable.
7. Write one per-city status row with stage-level `status`, `error`, `failure_reason`, `recoverable`, and `message` fields to:
   - `data_processed/orchestration/full_stack_city_orchestration_summary.json|csv`

CLI:

```powershell
.venv\Scripts\python.exe -m src.run_full_stack_orchestration --city-ids 2,3,4 --start-date 2023-05-01 --end-date 2023-08-31
```

```powershell
.venv\Scripts\python.exe -m src.run_full_stack_orchestration --all-missing --start-date 2023-05-01 --end-date 2023-08-31
```

Optional mode flags:

- `--all-missing`
- `--force-raw`
- `--overwrite-support`
- `--overwrite-features`
- `--max-cells`
- `--cell-filter-mode {study_area,core_city}`

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

## Stage 6: Raw Support-Layer Acquisition

1. Load the city list from `cities.csv` and the already materialized study areas from `data_processed/study_areas/`.
2. By default, select only city/dataset combinations that are still missing from support-layer readiness.
3. Acquire official raw sources with reusable caching:
   - DEM via TNM Access API queries against USGS 3DEP 1 arc-second products
   - NLCD via MRLC Annual NLCD CONUS bundles cached once under `data_raw/cache/nlcd/`
   - Hydro via TNM Access API queries against NHDPlus HR GeoPackage HU4 packages
4. Download source archives/tiles into `data_raw/cache/` and reuse them across reruns.
5. Preserve `.part` files for interrupted large downloads and resume hydro package ZIP transfers with HTTP range requests when the remote host supports them.
6. Validate TNM product-query responses before calling `response.json()`; retry transient invalid/non-JSON TNM bodies instead of crashing with `JSONDecodeError`.
7. Treat dead HU4 package URLs as warnings only when at least one intersecting HU4 package succeeded for the city; otherwise fail the hydro dataset cleanly.
8. Mosaic and clip DEM tiles to the city study area, then write:
   - `data_raw/dem/<city_slug>/<city_slug>_dem_3dep_30m.tif`
9. Extract the cached 2021 Annual NLCD land-cover and impervious rasters, clip per city, then write:
   - `data_raw/nlcd/<city_slug>/<city_slug>_nlcd_2021_land_cover_30m.tif`
   - `data_raw/nlcd/<city_slug>/<city_slug>_nlcd_2021_impervious_30m.tif`
10. Extract intersecting NHDPlus HR water layers from cached HU4 GeoPackages, clip to the study area, then write:
   - `data_raw/hydro/<city_slug>/<city_slug>_nhdplus_water.gpkg`
11. Persist resumable run status with structured `failure_reason`, `failure_category`, `recoverable`, `warnings`, and `warning_count` fields:
   - `data_processed/support_layers/raw_data_acquisition_summary.json|csv`

CLI:

```powershell
.venv\Scripts\python.exe -m src.run_raw_data_acquisition --all-missing
```

```powershell
.venv\Scripts\python.exe -m src.run_raw_data_acquisition --city-ids 1 2 3 --dataset dem
```

```powershell
.venv\Scripts\python.exe -m src.run_raw_data_acquisition --dataset nlcd --all-missing
```

```powershell
.venv\Scripts\python.exe -m src.run_raw_data_acquisition --dataset hydro --all-missing
```

```powershell
.venv\Scripts\python.exe -m src.run_raw_data_acquisition --city-ids 1 --force
```

## Stage 6B: Cache Audit + Cleanup Planning

1. Inventory every file under `data_raw/cache/`.
2. Classify cache artifacts into:
   - must keep
   - useful to keep temporarily
   - safe to delete/regenerate
3. Preserve cleanup metadata outside the cache tree as JSON before any deletion.
4. In dry-run mode, compute targeted prune candidates for:
   - `partials`
   - `nlcd-extracted`
   - `hydro-extracted`
   - `extracted`
   - `regenerable`
5. Protect recently modified files during active runs unless the operator intentionally sets `--protect-recent-hours 0`.

CLI:

```powershell
.venv\Scripts\python.exe -m src.run_cache_cleanup --prune-modes regenerable --protect-recent-hours 24 --report-json outputs\storage\cache_cleanup_dry_run.json
```

```powershell
.venv\Scripts\python.exe -m src.run_cache_cleanup --prune-modes regenerable --protect-recent-hours 0 --report-json outputs\storage\cache_cleanup_dry_run_no_age_gate.json
```

## Stage 7: Support-Layer Prep

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

## Stage 8: Generic Raster Alignment Framework

For each city grid:

1. Build grid-aligned raster template from grid CRS, extent, and resolution.
2. Reproject source rasters to this template.
3. Extract one value per grid cell from aligned arrays.
4. Optionally save aligned raster artifacts in `data_processed/intermediate/aligned_rasters/`.

Core module: `src/raster_features.py`

## Stage 9: DEM Feature Extraction

- Prefer prepared DEM support output when present.
- Otherwise fall back to the existing city raw DEM discovery path.
- Align DEM raster to city template.
- Extract `elevation_m` for each grid cell centroid index.

## Stage 10: NLCD Extraction

- Prefer prepared NLCD support outputs when present.
- Otherwise fall back to the existing city raw NLCD discovery path.
- Align NLCD land-cover raster and extract `land_cover_class` (nearest-neighbor).
- Align NLCD impervious raster and extract `impervious_pct`.

## Stage 11: Hydrography Distance-To-Water

- Prefer prepared hydro support output when present.
- Otherwise fall back to the existing city raw hydro discovery path.
- Rasterize hydro geometries to city template.
- Compute Euclidean distance transform (meters).
- Extract `dist_to_water_m` per grid cell.

Core module: `src/water_features.py`

## Stage 12: Per-City Feature Assembly

- Assemble city feature table from available sources.
- Study-area files now carry both the buffered acquisition geometry and the original core-urban geometry metadata.
- AppEEARS raster discovery accepts native value-layer names like `MOD13A1...NDVI...tif` and `ECO_L2T_LSTE...LST...tif`, while skipping QA/cloud/error sidecars and generic legacy names like `ndvi_1.tif` / `lst_1.tif`.
- Before stack sampling, NDVI/LST rasters are validated for readability and CRS; unreadable stale TIFFs are warned and skipped as long as enough valid rasters remain.
- `--cell-filter-mode study_area` keeps the current behavior; `--cell-filter-mode core_city` keeps buffered upstream acquisition but drops buffer-ring cells before hotspot labeling and final per-city outputs.
- The full-stack city orchestrator only enters this stage after raw support, support prep, NDVI, and ECOSTRESS are complete or reusable for that city.
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

```powershell
.venv\Scripts\python.exe -m src.run_city_features --city-id 1 --cell-filter-mode core_city
```

Latest manual verification on 2026-03-19:

- Full-stack runs have completed successfully for Phoenix, Tucson, Las Vegas, and Albuquerque.
- Tucson's earlier stale-file failure mode is now covered by regression tests that mix valid native AppEEARS rasters with invalid legacy TIFFs in the same city folder.

## Stage 13: Final Dataset Merge

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
