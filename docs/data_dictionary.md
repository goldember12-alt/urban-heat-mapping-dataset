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

## First-Pass Modeling Outputs

Location:

- `outputs/modeling/baselines/`
- `outputs/modeling/logistic_saga/`
- `outputs/modeling/random_forest/`

Shared artifact pattern:

- `metrics_by_fold.csv`
- `metrics_by_city.csv`
- `metrics_summary.csv`
- `heldout_predictions.parquet`
- `calibration_curve.csv`
- `run_metadata.json`
- `feature_contract.json`

Cross-run history artifacts:

- `outputs/modeling/run_registry.jsonl`
- `outputs/modeling/tuning_history.csv`
- `outputs/modeling/tuning_history_annotations.csv`

Tuned-model CLI output-path behavior:

- `src.run_logistic_saga` and `src.run_random_forest` accept an optional `--output-dir`
- when `--output-dir` is omitted, those CLIs now create a unique, readable run directory under the model-family root
- generated names encode the preset, fold scope, sample scope, and timestamp so later filesystem review is easier
- `--run-label` can append a short manual tag to the generated name without replacing the shared naming contract

Model-specific extras:

- `outputs/modeling/logistic_saga/best_params_by_fold.csv`
- `outputs/modeling/random_forest/best_params_by_fold.csv`

Current baseline runner:

- `src.run_modeling_baselines`

Current baseline models:

- `global_mean_baseline`
- `land_cover_only_baseline`
- `impervious_only_baseline`
- `climate_only_baseline`

Current main-model runners:

- `src.run_logistic_saga`
- `src.run_random_forest`

Held-out prediction table columns:

- `model_name`
- `outer_fold`
- `city_id`
- `city_name`
- `climate_group`
- `cell_id`
- `centroid_lon`
- `centroid_lat`
- `hotspot_10pct`
- `predicted_probability`

`metrics_by_fold.csv` contains:

- held-out fold id
- train/test city counts
- train/test row counts
- held-out PR AUC
- held-out recall at top 10%
- for tuned models, the best inner-CV PR AUC

`metrics_by_city.csv` contains:

- one row per held-out city per model
- held-out PR AUC
- held-out recall at top 10%
- held-out row count and positive count

`best_params_by_fold.csv` contains:

- `model_name`
- `outer_fold`
- `best_inner_cv_average_precision`
- `best_params_json`

`tuning_history.csv` contains:

- one row per logged modeling run in chronological order
- factual run metadata reused from `run_registry.jsonl` and per-run `run_metadata.json`
- search-contract descriptors and signatures for contract-drift tracking
- comparison signatures for identifying directly comparable runs
- key held-out summary metrics and runtime
- frontier fields such as prior-best pooled PR AUC within the same comparison group
- merged manual annotation fields for status labels, decision notes, and comparability notes

`tuning_history_annotations.csv` contains:

- one row per logged modeling run
- lightweight manual fields only
- a durable place to label runs as validation, exploratory, benchmark, superseded, or similar without editing generated metadata

Honest status note:

- These outputs are produced by implemented code and test-verified on synthetic grouped-city fixtures; a full canonical run on the real 30-city dataset is still pending

## Figures And Report Outputs

### Figures

- `figures/data_processing/<city_stem>/` contains per-city data-processing report figures
- Current per-city data-processing figure set includes:
  - `<city_slug>_key_distributions.png`
  - `<city_slug>_land_cover_composition.png`
  - `<city_slug>_key_correlations.png`
  - `<city_slug>_hotspot_map.png`
- `figures/modeling/` is the intended root for held-out prediction, calibration, and map-oriented modeling figures as that stage expands
- A small number of legacy/global inspection figures may still exist directly under `figures/` from earlier checkpoints

### Report-style outputs

- `outputs/data_processing/<city_stem>/<city_slug>_data_summary.md` stores the markdown summary for one city
- `outputs/data_processing/<city_stem>/tables/` stores supporting CSV tables for that city summary
- `outputs/data_processing/data_processing_report_summary.csv` stores the latest batch run status across requested cities
- `outputs/modeling/` stores the current first-pass modeling metrics tables, held-out predictions, calibration tables, and run metadata
- `outputs/storage/` continues to hold storage-management and cache-audit artifacts
- Legacy Phoenix-only root-level outputs may still exist from pre-refactor runs, but the reporting code now writes new data-processing summaries only to the split stage-specific structure above
