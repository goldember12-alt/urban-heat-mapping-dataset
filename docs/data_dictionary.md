# Data Dictionary

## Stage-1 Outputs

### Study areas (`data_processed/study_areas/*.gpkg`)

- `geometry`: buffered study area polygon in local projected CRS
- `city_id`: integer city identifier
- `city_name`: city name
- `state`: state abbreviation
- `climate_group`: climate group label
- `buffer_m`: applied buffer distance in meters
- `core_geometry_wkt`: original unbuffered Census urban-area geometry serialized as WKT in the same projected CRS
- `core_geometry_crs`: CRS string for `core_geometry_wkt`

### City grids (`data_processed/city_grids/*.gpkg`)

- `cell_id`: integer grid-cell identifier within city
- `geometry`: 30 m grid-cell polygon

## AppEEARS Acquisition Outputs

### AppEEARS AOI exports (`data_processed/appeears_aoi/*.geojson`)

- `city_id`: integer city identifier
- `city_name`: city name
- `state`: state abbreviation
- `geometry`: one city AOI polygon (or multipart polygon) in EPSG:4326

### AppEEARS preflight summaries (`data_processed/appeears_status/appeears_<product_type>_preflight_summary.json|csv`)

Per-city preflight fields:

- `city_id`: integer city identifier
- `city_slug`: lowercase slug used for deterministic path construction
- `expected_study_area_path`: expected study-area GeoPackage path
- `study_area_exists`: whether the expected study-area file exists on disk
- `expected_aoi_path`: expected AppEEARS AOI GeoJSON path
- `aoi_exists`: whether the expected AOI file exists on disk
- `aoi_crs_valid`: whether the AOI resolves to EPSG:4326
- `expected_ndvi_raw_dir`: expected immutable NDVI raw-download folder for the city
- `expected_ecostress_raw_dir`: expected immutable ECOSTRESS raw-download folder for the city
- `expected_status_output_path`: expected acquisition summary JSON path for the selected product type
- `acquisition_ready`: `True` when study area exists, AOI exists, and AOI CRS validates as EPSG:4326
- `blocking_reason`: blank when ready, otherwise the first blocking reason (`study_area_missing`, `aoi_missing`, `aoi_crs_invalid:*`, `aoi_crs_missing`, `aoi_empty`, or `aoi_read_error:*`)
- `updated_at_utc`: preflight generation timestamp

### AppEEARS acquisition summaries (`data_processed/appeears_status/appeears_<product_type>_acquisition_summary.json|csv`)

Per-city status fields:

- `city_id`: integer city identifier
- `city_name`: city name
- `state`: state abbreviation
- `city_slug`: lowercase slug used for folder routing
- `product_type`: `ndvi` or `ecostress`
- `product`: AppEEARS product identifier actually used for submission
- `layer`: AppEEARS layer identifier used in payload
- `start_date`: requested date-range start (`YYYY-MM-DD`)
- `end_date`: requested date-range end (`YYYY-MM-DD`)
- `study_area_path`: current expected or exported study-area GeoPackage path
- `aoi_path`: current expected or exported AOI GeoJSON path
- `download_dir`: target raw download directory
- `task_id`: AppEEARS task identifier (if submitted)
- `remote_task_status`: latest polled remote task status string
- `status`: local pipeline status (`blocked`, `pending`, `submitted`, `completed`, `failed`)
- `n_bundle_files`: count of files listed in completed bundle
- `n_files_downloaded`: number of new files downloaded in this run
- `n_files_existing`: number of already-present files kept unchanged
- `error`: last error message (blank when successful)
- `updated_at_utc`: last update timestamp for that city record

### Raw acquisition folders

- `data_raw/ndvi/<city_slug>/`: immutable raw NDVI downloads
- `data_raw/ecostress/<city_slug>/`: immutable raw ECOSTRESS downloads

### Acquisition orchestration summary (`data_processed/orchestration/acquisition_orchestration_summary.json|csv`)

Per-stage orchestration fields:

- `stage`: orchestration stage name (`raw_support_acquisition`, `support_layer_prep`, `appeears_ndvi`, `appeears_ecostress`)
- `selection_mode`: requested orchestration scope (`all`, `city_subset`, or `all_missing`)
- `requested_city_ids`: comma-delimited requested city subset, blank when all configured cities were targeted
- `effective_city_ids`: comma-delimited city IDs present in the stage summary
- `n_effective_cities`: number of distinct cities represented in the stage summary
- `n_records`: number of raw rows in the underlying stage summary
- `status_counts_json`: JSON object of stage status counts
- `summary_json_path`: underlying stage JSON summary path
- `summary_csv_path`: underlying stage CSV summary path
- `notes`: lightweight stage-specific execution note

## Support-Layer Outputs

### Support-layer raw input contract

Canonical per-city raw support paths expected by the standardized support-layer audit and prep stage:

- `data_raw/dem/<city_slug>/<city_slug>_dem_3dep_30m.tif`
- `data_raw/nlcd/<city_slug>/<city_slug>_nlcd_2021_land_cover_30m.tif`
- `data_raw/nlcd/<city_slug>/<city_slug>_nlcd_2021_impervious_30m.tif`
- `data_raw/hydro/<city_slug>/<city_slug>_nhdplus_water.gpkg`

### Support-layer preflight summaries (`data_processed/support_layers/support_layers_preflight_summary.json|csv`)

Per-city readiness fields:

- `city_id`: integer city identifier
- `city_slug`: lowercase slug used for deterministic support-layer paths
- `expected_study_area_path`: expected study-area GeoPackage path
- `expected_grid_path`: expected city-grid GeoPackage path
- `expected_dem_raw_path`: canonical expected DEM raw path for the city
- `expected_nlcd_land_cover_raw_path`: canonical expected NLCD land-cover raw path for the city
- `expected_nlcd_impervious_raw_path`: canonical expected NLCD impervious raw path for the city
- `expected_hydro_raw_path`: canonical expected hydro raw path for the city
- `dem_source_path`: actual recursively discovered DEM raw source path in the city folder, if any
- `nlcd_land_cover_source_path`: actual recursively discovered NLCD land-cover source path in the city folder, if any
- `nlcd_impervious_source_path`: actual recursively discovered NLCD impervious source path in the city folder, if any
- `hydro_source_path`: actual recursively discovered hydro source path in the city folder, if any
- `expected_dem_prepared_path`: deterministic prepared DEM output path
- `expected_nlcd_land_cover_prepared_path`: deterministic prepared NLCD land-cover output path
- `expected_nlcd_impervious_prepared_path`: deterministic prepared NLCD impervious output path
- `expected_hydro_prepared_path`: deterministic prepared hydro output path
- `study_area_exists`: whether the study-area GeoPackage exists
- `grid_exists`: whether the city grid exists
- `dem_source_available`: whether a city raw DEM source was discovered
- `nlcd_land_cover_source_available`: whether a city raw NLCD land-cover source was discovered
- `nlcd_impervious_source_available`: whether a city raw NLCD impervious source was discovered
- `hydro_source_available`: whether a city raw hydro source was discovered
- `required_inputs_exist`: `True` when all four raw support sources were discovered
- `dem_prepared_exists`: whether the deterministic prepared DEM output already exists
- `nlcd_land_cover_prepared_exists`: whether the deterministic prepared NLCD land-cover output already exists
- `nlcd_impervious_prepared_exists`: whether the deterministic prepared NLCD impervious output already exists
- `hydro_prepared_exists`: whether the deterministic prepared hydro output already exists
- `support_prep_ready`: `True` when study area exists and all four raw support sources are available
- `feature_extraction_ready`: `True` when grid exists and all four support layers are available via prepared outputs or raw fallback
- `prep_blocking_reasons`: semicolon-delimited blockers for support-layer prep
- `feature_blocking_reasons`: semicolon-delimited blockers for feature extraction readiness
- `blocking_reasons`: union of prep and feature blockers
- `updated_at_utc`: preflight generation timestamp

### Support-layer prep summaries (`data_processed/support_layers/support_layers_prep_summary.json|csv`)

Per-city prep fields:

- `city_id`: integer city identifier
- `city_name`: city name
- `city_slug`: lowercase slug used for deterministic support-layer paths
- `study_area_path`: study-area GeoPackage used for clipping
- `grid_path`: expected city-grid GeoPackage for downstream feature extraction
- `dem_source_path`: DEM raw source used for prep
- `nlcd_land_cover_source_path`: NLCD land-cover raw source used for prep
- `nlcd_impervious_source_path`: NLCD impervious raw source used for prep
- `hydro_source_path`: hydro raw source used for prep
- `dem_prepared_path`: prepared DEM output path
- `nlcd_land_cover_prepared_path`: prepared NLCD land-cover output path
- `nlcd_impervious_prepared_path`: prepared NLCD impervious output path
- `hydro_prepared_path`: prepared hydro output path
- `status`: prep status (`blocked`, `completed`, `failed`, `skipped_existing`)
- `error`: blank on success, otherwise the blocking reason or exception string
- `updated_at_utc`: prep summary timestamp

### Prepared support-layer outputs (`data_processed/support_layers/<city_stem>/`)

- `dem_prepared.tif`: study-area-clipped DEM raster
- `nlcd_land_cover_prepared.tif`: study-area-clipped NLCD land-cover raster
- `nlcd_impervious_prepared.tif`: study-area-clipped NLCD impervious raster
- `hydro_water_prepared.gpkg`: study-area-clipped hydro vector layer

## Intermediate Outputs

### Aligned rasters (`data_processed/intermediate/aligned_rasters/<city_stem>/`)

When source data is available, aligned rasters may include:

- `dem_aligned.tif`
- `nlcd_land_cover_aligned.tif`
- `nlcd_impervious_aligned.tif`
- `dist_to_water_m_aligned.tif`

### Per-city intermediate tables (`data_processed/intermediate/city_features/`)

- `*_features_unfiltered.parquet`: before spatial core-city filtering, open-water drops, and ECOSTRESS pass-count row drops
- `*_features_filtered.parquet`: after any requested spatial filter plus the row-drop rules

## Per-City Feature Outputs (`data_processed/city_features/*.gpkg|*.parquet`)

Final per-city feature columns:

- `city_id`: integer city identifier
- `city_name`: city name
- `climate_group`: climate-group category
- `cell_id`: cell identifier within city grid
- `centroid_lon`: centroid longitude (WGS84)
- `centroid_lat`: centroid latitude (WGS84)
- `impervious_pct`: NLCD impervious percentage (if available)
- `land_cover_class`: NLCD land-cover class code (if available)
- `elevation_m`: DEM-derived elevation in meters (if available)
- `dist_to_water_m`: distance to nearest hydro feature in meters (if available)
- `ndvi_median_may_aug`: median NDVI from May-Aug raster stack (if available)
- `lst_median_may_aug`: median LST from May-Aug ECOSTRESS/AppEEARS stack (if available)
- `n_valid_ecostress_passes`: number of valid LST observations used in the median (if available)
- `hotspot_10pct`: boolean indicator for top 10% LST cells within city

Additional per-city output audit fields:

- `is_core_city_cell`: boolean flag marking cells retained by `--cell-filter-mode core_city`
- `is_buffer_ring_cell`: boolean flag marking cells outside the saved core urban footprint but inside the buffered study area

## Final Dataset Outputs (`data_processed/final/final_dataset.*`)

Schema matches the required per-city feature columns listed above and does not include the per-city-only audit fields.

## Modeling Prep Outputs (`data_processed/modeling/`)

### Final-dataset audit artifacts

- `final_dataset_audit_summary.json`: high-level row count, city count, target validation, and output-path metadata
- `final_dataset_audit.md`: short human-readable audit summary for collaborators
- `final_dataset_city_summary.csv`: one row per city with:
  - `city_id`
  - `city_name`
  - `climate_group`
  - `row_count`
  - `hotspot_positive_count`
  - `hotspot_non_missing_count`
  - `hotspot_prevalence`
  - `n_valid_ecostress_passes_non_missing_count`
  - `n_valid_ecostress_passes_min`
  - `n_valid_ecostress_passes_median`
  - `n_valid_ecostress_passes_mean`
  - `n_valid_ecostress_passes_max`
- `final_dataset_feature_missingness.csv`: dataset-wide missingness for candidate modeling features
- `final_dataset_feature_missingness_by_city.csv`: per-city missingness for candidate modeling features

### Deterministic fold artifacts

- `city_outer_folds.parquet`
- `city_outer_folds.csv`

Fold-file columns:

- `city_id`: grouping key to join back to the cell-level dataset
- `city_name`: city label for quick inspection
- `climate_group`: climate-group label copied from the final dataset
- `row_count`: number of rows contributed by that city in the audited final dataset
- `hotspot_positive_count`: number of hotspot-positive rows in that city
- `hotspot_non_missing_count`: number of non-missing target rows in that city
- `hotspot_prevalence`: hotspot share among non-missing target rows
- `n_valid_ecostress_passes_non_missing_count`: non-missing ECOSTRESS pass-count rows
- `n_valid_ecostress_passes_min`: city-level minimum ECOSTRESS pass count
- `n_valid_ecostress_passes_median`: city-level median ECOSTRESS pass count
- `n_valid_ecostress_passes_mean`: city-level mean ECOSTRESS pass count
- `n_valid_ecostress_passes_max`: city-level maximum ECOSTRESS pass count
- `outer_fold`: deterministic held-out-city fold identifier

### Baseline modeling outputs (`data_processed/modeling/baselines/`)

- `baseline_metrics_by_fold.csv`: one row per model per outer fold with:
  - `model_name`
  - `outer_fold`
  - `n_training_rows`
  - `training_positive_count`
  - `training_prevalence`
  - `n_validation_rows`
  - `validation_positive_count`
  - `validation_prevalence`
  - `n_training_cities`
  - `n_validation_cities`
  - `validation_city_ids`
  - `validation_city_names`
  - `roc_auc`
  - `pr_auc`
  - `missing_target_rows_dropped`
  - `prediction_path`
- `baseline_metrics_overall.csv`: one row per model with fold-aggregated metrics:
  - `model_name`
  - `n_folds`
  - `total_validation_rows`
  - `total_validation_positive_count`
  - `mean_fold_roc_auc`
  - `weighted_mean_fold_roc_auc`
  - `mean_fold_pr_auc`
  - `weighted_mean_fold_pr_auc`
  - `mean_fold_validation_prevalence`
  - `weighted_mean_validation_prevalence`
- `baseline_leakage_checks.csv`: fold-level leakage guard summary with train/validation city counts, overlap count, and excluded-column record
- `baseline_assumptions.md`: human-readable description of the feature set, leakage exclusions, filtering, and aggregation assumptions
- `baseline_run_summary.json`: machine-readable run configuration and output-path metadata

Validation prediction files under `validation_predictions/<model_name>/outer_fold=<k>.parquet` include:

- `model_name`: baseline model identifier
- `outer_fold`: held-out fold id
- `city_id`: city join key
- `city_name`: city label
- `cell_id`: cell identifier within city
- `hotspot_10pct`: observed binary target used for validation metrics
- `predicted_probability`: model-estimated hotspot probability

Model artifact files:

- `model_artifacts/logistic_regression_coefficients.csv`: one row per fold-feature coefficient with convergence metadata
- `model_artifacts/decision_stump_rules.csv`: one row per fold with the selected split feature, threshold, and leaf probabilities

## Row Rules

- Drop open-water rows where `land_cover_class == 11` when land-cover exists.
- If LST is available, drop rows with `n_valid_ecostress_passes < 3`.
- Compute `hotspot_10pct` within each city using city-specific LST 90th percentile threshold.
