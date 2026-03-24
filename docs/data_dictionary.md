# Data Dictionary

This document focuses on the main datasets, output artifacts, and canonical column definitions. For workflow sequencing, see [`docs/workflow.md`](workflow.md). For grouped-city modeling methodology, see [`docs/modeling_plan.md`](modeling_plan.md).

## Canonical Final Dataset

Primary files:

- `data_processed/final/final_dataset.parquet`
- `data_processed/final/final_dataset.csv`

One row represents one 30 m grid cell in one city.

| Column | Definition |
| --- | --- |
| `city_id` | Integer city identifier used for joins and grouped CV. |
| `city_name` | Human-readable city name. |
| `climate_group` | Climate grouping label for the city. |
| `cell_id` | Cell identifier within the city grid. |
| `centroid_lon` | Cell centroid longitude in WGS84. |
| `centroid_lat` | Cell centroid latitude in WGS84. |
| `impervious_pct` | NLCD impervious percentage for the cell. |
| `land_cover_class` | NLCD land-cover class code for the cell. |
| `elevation_m` | DEM-derived elevation in meters. |
| `dist_to_water_m` | Distance from the cell to the nearest hydro feature in meters. |
| `ndvi_median_may_aug` | Median May-Aug NDVI derived from AppEEARS/Landsat inputs. |
| `lst_median_may_aug` | Median May-Aug daytime land surface temperature derived from ECOSTRESS/AppEEARS inputs. |
| `n_valid_ecostress_passes` | Number of valid ECOSTRESS observations contributing to the cell-level LST summary. |
| `hotspot_10pct` | Binary indicator for whether the cell falls in the within-city top 10% of valid LST values. |

Row rules applied during final assembly:

- Drop open-water cells where `land_cover_class == 11` when land cover is available
- Drop rows with `n_valid_ecostress_passes < 3` when LST is available
- Recompute `hotspot_10pct` within each city after row filtering

## Per-City Feature Outputs

Primary files:

- `data_processed/city_features/*.parquet`
- `data_processed/city_features/*.gpkg`

These files contain the same core feature columns as the final dataset, but the GeoPackage version also preserves geometry. Per-city feature outputs may also include audit fields used before the final merge:

- `is_core_city_cell`: `True` when the cell is inside the saved core urban footprint
- `is_buffer_ring_cell`: `True` when the cell lies in the buffered area outside the core urban footprint

## Study Area And Grid Artifacts

### Study areas

Location:

- `data_processed/study_areas/*.gpkg`

Key fields:

- `geometry`: buffered study-area polygon in projected CRS
- `city_id`
- `city_name`
- `state`
- `climate_group`
- `buffer_m`
- `core_geometry_wkt`: original unbuffered urban-area geometry serialized as WKT
- `core_geometry_crs`: CRS string for `core_geometry_wkt`

### City grids

Location:

- `data_processed/city_grids/*.gpkg`

Key fields:

- `cell_id`
- `geometry`: 30 m grid-cell polygon

## Acquisition Artifacts

### AppEEARS AOIs

Location:

- `data_processed/appeears_aoi/*.geojson`

Purpose:

- One EPSG:4326 AOI polygon per city for AppEEARS submission

### AppEEARS status summaries

Location:

- `data_processed/appeears_status/`

Purpose:

- Per-city preflight and acquisition summaries for NDVI and ECOSTRESS

Typical fields:

- city identifiers and slugs
- expected paths
- readiness or acquisition status
- task metadata
- file counts
- error or blocking-reason fields
- update timestamps

### Raw remote-sensing downloads

Locations:

- `data_raw/ndvi/<city_slug>/`
- `data_raw/ecostress/<city_slug>/`

Purpose:

- Immutable raw AppEEARS downloads used for NDVI and LST feature assembly

## Support-Layer Artifacts

### Canonical raw support-input contract

- `data_raw/dem/<city_slug>/<city_slug>_dem_3dep_30m.tif`
- `data_raw/nlcd/<city_slug>/<city_slug>_nlcd_2021_land_cover_30m.tif`
- `data_raw/nlcd/<city_slug>/<city_slug>_nlcd_2021_impervious_30m.tif`
- `data_raw/hydro/<city_slug>/<city_slug>_nhdplus_water.gpkg`

### Prepared support outputs

Location:

- `data_processed/support_layers/<city_stem>/`

Files:

- `dem_prepared.tif`
- `nlcd_land_cover_prepared.tif`
- `nlcd_impervious_prepared.tif`
- `hydro_water_prepared.gpkg`

### Support-layer summaries

Location:

- `data_processed/support_layers/`

Primary summary files:

- `support_layers_preflight_summary.json`
- `support_layers_preflight_summary.csv`
- `raw_data_acquisition_summary.json`
- `raw_data_acquisition_summary.csv`
- `support_layers_prep_summary.json`
- `support_layers_prep_summary.csv`

Purpose:

- Record per-city readiness, deterministic paths, stage status, and error or warning fields

## Intermediate Artifacts

### Aligned rasters

Location:

- `data_processed/intermediate/aligned_rasters/<city_stem>/`

Typical files:

- `dem_aligned.tif`
- `nlcd_land_cover_aligned.tif`
- `nlcd_impervious_aligned.tif`
- `dist_to_water_m_aligned.tif`

### Per-city intermediate tables

Location:

- `data_processed/intermediate/city_features/`

Files:

- `*_features_unfiltered.parquet`
- `*_features_filtered.parquet`

Purpose:

- Preserve the pre-drop and post-drop feature tables around spatial filtering and final row rules

## Modeling Handoff Artifacts

Location:

- `data_processed/modeling/`

### Final-dataset audit outputs

- `final_dataset_audit_summary.json`
- `final_dataset_audit.md`
- `final_dataset_city_summary.csv`
- `final_dataset_feature_missingness.csv`
- `final_dataset_feature_missingness_by_city.csv`

Purpose:

- Summarize the canonical merged dataset before modeling

### City outer folds

- `city_outer_folds.parquet`
- `city_outer_folds.csv`

Key fields:

- `city_id`
- `city_name`
- `climate_group`
- `row_count`
- `hotspot_positive_count`
- `hotspot_non_missing_count`
- `hotspot_prevalence`
- `outer_fold`

Purpose:

- Define city-held-out outer splits without duplicating the full cell-level dataset

## Baseline Modeling Outputs

Location:

- `data_processed/modeling/baselines/`

Primary artifacts:

- `baseline_metrics_by_fold.csv`
- `baseline_metrics_overall.csv`
- `baseline_leakage_checks.csv`
- `baseline_assumptions.md`
- `baseline_run_summary.json`
- `validation_predictions/`
- `model_artifacts/`

Validation prediction files contain:

- `model_name`
- `outer_fold`
- `city_id`
- `city_name`
- `cell_id`
- `hotspot_10pct`
- `predicted_probability`

Model artifact examples:

- `model_artifacts/logistic_regression_coefficients.csv`
- `model_artifacts/decision_stump_rules.csv`

Honest status note:

- These baseline outputs are produced by implemented code, but the project handoff still records the full canonical baseline run as pending

## Figures And Report Outputs

### Figures

- `figures/` contains project figures such as city-point and grid-sample plots

### Report-style outputs

- `outputs/` contains generated summaries and storage-management artifacts
- Current examples include `outputs/phoenix_data_summary.md`, `outputs/phoenix_data_summary/`, and `outputs/storage/`
