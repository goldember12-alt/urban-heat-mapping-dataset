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

## Stage 2: Generic Raster Alignment Framework

For each city grid:

1. Build grid-aligned raster template from grid CRS, extent, and resolution.
2. Reproject source rasters to this template.
3. Extract one value per grid cell from aligned arrays.
4. Optionally save aligned raster artifacts in `data_processed/intermediate/aligned_rasters/`.

Core module: `src/raster_features.py`

## Stage 3: DEM Feature Extraction

- Align DEM raster to city template.
- Extract `elevation_m` for each grid cell centroid index.

## Stage 4: NLCD Extraction

- Align NLCD land-cover raster and extract `land_cover_class` (nearest-neighbor).
- Align NLCD impervious raster and extract `impervious_pct`.

## Stage 5: Hydrography Distance-To-Water

- Rasterize hydro geometries to city template.
- Compute Euclidean distance transform (meters).
- Extract `dist_to_water_m` per grid cell.

Core module: `src/water_features.py`

## Stage 6: Per-City Feature Assembly

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

## Stage 7: Final Dataset Merge

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

## Stage 8: NDVI + ECOSTRESS

- NDVI and LST stages are implemented as raster-stack interfaces in feature assembly.
- They run only when source rasters exist in:
  - `data_raw/ndvi/`
  - `data_raw/ecostress/`
- If absent, columns remain missing (`NaN`) and stages are reported as blocked.

## Full Pipeline CLI

```powershell
.venv\Scripts\python.exe -m src.run_full_pipeline --skip-city-processing --existing-grids-only --city-ids 1 --max-cells 5000
```

Use `--max-cells` for partial/debug runs on very large city grids.
