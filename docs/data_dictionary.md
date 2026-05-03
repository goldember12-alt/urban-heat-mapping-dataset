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
| `tree_cover_proxy_pct_270m` | Phase 3A local tree-cover proxy: share of nearby 30 m cells within an approximately 270 m neighborhood that fall in NLCD forest classes 41/42/43. |
| `vegetated_cover_proxy_pct_270m` | Phase 3A local vegetated-cover proxy: share of nearby 30 m cells within an approximately 270 m neighborhood that fall in the selected NLCD vegetated classes. |
| `impervious_pct_mean_270m` | Phase 3A local impervious-context feature: neighborhood mean NLCD impervious percentage within an approximately 270 m window. |

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

The parquet feature artifacts are the canonical Phase 3A backfill targets. `src.run_phase3a_nlcd_bundle` updates the per-city parquet artifacts and the intermediate filtered/unfiltered parquet tables by default, and only rewrites the GeoPackage copies when `--update-gpkg` is requested explicitly.

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
- `tree_cover_proxy_pct_270m_aligned.tif`
- `vegetated_cover_proxy_pct_270m_aligned.tif`
- `impervious_pct_mean_270m_aligned.tif`

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
- `outputs/modeling/logistic_saga_climate_interactions/`
- `outputs/modeling/random_forest/`
- `outputs/modeling/hist_gradient_boosting/`

Shared artifact pattern:

- `metrics_by_fold.csv`
- `metrics_by_city.csv`
- `metrics_summary.csv`
- `heldout_predictions.parquet`
- `calibration_curve.csv`
- `run_metadata.json`
- `feature_contract.json`

Bounded richer-feature checkpoint example:

- `outputs/modeling/logistic_saga/full_allfolds_s5000_phase3a-nlcd-context_2026-04-13_142451/`
- this Phase 3A run keeps the same grouped-city evaluation contract and sample cap as retained logistic `5000`, but adds the three NLCD neighborhood-context predictors above as a separate richer-feature variant

Cross-run history artifacts:

- `outputs/modeling/run_registry.jsonl`
- `outputs/modeling/tuning_history.csv`
- `outputs/modeling/tuning_history_annotations.csv`

Tuned-model CLI output-path behavior:

- `src.run_logistic_saga`, `src.run_logistic_saga_climate_interactions`, `src.run_random_forest`, and `src.run_hist_gradient_boosting` accept an optional `--output-dir`
- when `--output-dir` is omitted, those CLIs now create a unique, readable run directory under the model-family root
- generated names encode the preset, fold scope, sample scope, and timestamp so later filesystem review is easier
- `--run-label` can append a short manual tag to the generated name without replacing the shared naming contract

Model-specific extras:

- `outputs/modeling/logistic_saga/best_params_by_fold.csv`
- `outputs/modeling/logistic_saga_climate_interactions/best_params_by_fold.csv`
- `outputs/modeling/random_forest/best_params_by_fold.csv`
- `outputs/modeling/hist_gradient_boosting/best_params_by_fold.csv`

Current baseline runner:

- `src.run_modeling_baselines`

Current baseline models:

- `global_mean_baseline`
- `land_cover_only_baseline`
- `impervious_only_baseline`
- `climate_only_baseline`

Current main-model runners:

- `src.run_logistic_saga`
- `src.run_logistic_saga_climate_interactions` for the bounded Phase 2 climate-conditioned checkpoint on the fixed six-feature contract
- `src.run_random_forest`
- `src.run_hist_gradient_boosting` for the bounded Phase 1 better-learner checkpoint on the fixed six-feature contract
- `src.run_modeling_reporting`
- `src.run_modeling_supplemental`

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
- on this workstation, the intended convention is:
  - `validation` for smoke or one-fold workflow checks
  - `exploratory` for partial-scope, legacy-contract, or abandoned search paths
  - `benchmark` for retained decision checkpoints, including the logistic sampled-full baseline ladder and any retained random-forest stage outputs

Honest status note:

- These outputs are produced by implemented code and test-verified on synthetic grouped-city fixtures; a full canonical run on the real 30-city dataset is still pending

## Figures And Report Outputs

### Figures

- `figures/data_processing/city_summaries/<city_stem>/` contains per-city data-processing report figures
- Current per-city data-processing figure set includes:
  - `<city_slug>_key_distributions.png`
  - `<city_slug>_land_cover_composition.png`
  - `<city_slug>_key_correlations.png`
  - `<city_slug>_hotspot_map.png`
- `figures/modeling/` is the root for held-out prediction, calibration, and map-oriented modeling figures
- A small number of legacy/global inspection figures may still exist directly under `figures/` from earlier checkpoints

### Report-style outputs

- `outputs/data_processing/city_summaries/<city_stem>/<city_slug>_data_summary.md` stores the markdown summary for one city
- `outputs/data_processing/city_summaries/<city_stem>/tables/` stores supporting CSV tables for that city summary
- `outputs/data_processing/batch_reports/data_processing_report_summary.csv` stores the latest batch run status across requested cities
- `outputs/modeling/` stores the current first-pass modeling metrics tables, held-out predictions, calibration tables, and run metadata
- `outputs/modeling/reporting/` stores broader markdown comparison summaries and decision-ready reporting notes derived from retained modeling runs
- `outputs/modeling/reporting/cross_city_benchmark_report.md` is the headline modeling benchmark reference for the project narrative
- `outputs/modeling/reporting/tables/` stores derived reporting tables such as cross-run benchmark comparisons, city-level RF-vs-logistic error summaries, optional Phase 1 HGB-vs-RF comparison tables when an HGB run is passed to `src.run_modeling_reporting`, and optional Phase 2 logistic-climate-interaction comparison plus climate-disparity tables when a climate-interaction run is passed
- `outputs/modeling/reporting/cross_city_benchmark_report_phase3a_nlcd_context.md` records the bounded richer-feature checkpoint without replacing the retained headline benchmark report
- `outputs/modeling/reporting/tables/cross_city_benchmark_report_phase3a_nlcd_context_phase3_richer_vs_logistic.csv` compares the Phase 3A richer-feature logistic run against retained logistic `5000` by city-fold row
- `outputs/modeling/reporting/tables/cross_city_benchmark_report_phase3a_nlcd_context_phase3_richer_vs_logistic_by_climate.csv` summarizes that same Phase 3A comparison by climate group
- `figures/modeling/reporting/` stores benchmark comparison figures and city-level metric-delta plots derived from retained modeling runs
- `outputs/modeling/reporting/heldout_city_maps/` stores retained-run held-out map reporting artifacts such as:
  - `heldout_city_maps.md`
  - `heldout_city_map_selection.csv`
  - `heldout_city_map_points.parquet`
  - `heldout_city_map_city_summary.csv`
- `figures/modeling/heldout_city_maps/` stores representative held-out-city map triptychs with predicted-hotspot, true-hotspot, and categorical error panels such as:
  - `denver_heldout_map_triptych.png`
  - `atlanta_heldout_map_triptych.png`
  - `detroit_heldout_map_triptych.png`
  - these are support artifacts derived from retained benchmark predictions, not replacement benchmark results
- `outputs/modeling/final_train/` stores bounded final-train transfer packages derived from retained benchmark selections, currently including:
  - `random_forest_frontier_s5000_all_cities_transfer_package/model.joblib`
  - `random_forest_frontier_s5000_all_cities_transfer_package/feature_contract.json`
  - `random_forest_frontier_s5000_all_cities_transfer_package/preprocessing_manifest.json`
  - `random_forest_frontier_s5000_all_cities_transfer_package/selected_hyperparameters.json`
  - `random_forest_frontier_s5000_all_cities_transfer_package/hyperparameter_selection_summary.csv`
  - `random_forest_frontier_s5000_all_cities_transfer_package/training_city_summary.csv`
  - `random_forest_frontier_s5000_all_cities_transfer_package/training_sample_diagnostics.csv`
  - `random_forest_frontier_s5000_all_cities_transfer_package/transfer_package_metadata.json`
- `outputs/modeling/transfer_inference/` stores deterministic application outputs written from the retained transfer package, such as:
  - `<inference_id>/predictions.parquet`
  - `<inference_id>/predictions.csv`
  - `<inference_id>/prediction_summary.csv`
  - `<inference_id>/prediction_deciles.csv`
  - `<inference_id>/feature_missingness.csv`
  - `<inference_id>/transfer_inference_summary.md`
  - `<inference_id>/transfer_inference_metadata.json`
- `figures/modeling/transfer_inference/` stores transfer-inference figures, typically:
  - `<inference_id>/predicted_risk_map.png`
  - when centroid columns are absent, the same filename stores a fallback score-distribution figure instead of a centroid map
- `outputs/modeling/supplemental/within_city/` stores exploratory within-city markdown summaries plus bounded contrast artifacts such as:
  - `within_city_contrast_summary.md`
  - `tables/within_city_selected_cities.csv`
  - `tables/within_city_repeat_metrics.csv`
  - `tables/within_city_summary.csv`
  - `tables/within_city_city_model_contrast.csv`
  - `tables/within_city_best_params.csv`
  - `tables/within_city_calibration_curve.csv`
  - `within_city_predictions.parquet`
- within-city supplemental tables may include the exploratory-only `city_prevalence_baseline`, which is not part of the canonical cross-city baseline suite
- `figures/modeling/supplemental/within_city/` stores bounded within-city contrast figures such as:
  - `within_city_pr_auc_contrast.png`
  - `within_city_recall_contrast.png`
- `outputs/modeling/supplemental/within_city_all_cities/` stores the bounded all-city within-city appendix, including:
  - `within_city_all_cities_summary.md`
  - `within_city_all_cities_predictions.parquet`
  - `tables/within_city_all_cities_repeat_metrics.csv`
  - `tables/within_city_all_cities_city_summary.csv`
  - `tables/within_city_all_cities_climate_summary.csv`
  - `tables/within_city_all_cities_cross_city_gap_by_city.csv`
  - `tables/within_city_all_cities_cross_city_gap_by_climate.csv`
- the all-city within-city appendix keeps the same six-feature contract and uses retained cross-city reporting tables only as comparison references; it remains explicitly easier than and subordinate to the canonical held-out-city benchmark
- `figures/modeling/supplemental/within_city_all_cities/` stores the all-city appendix figures:
  - `within_city_all_cities_pr_auc_by_climate.png`
  - `within_city_all_cities_recall_by_climate.png`
  - `within_city_all_cities_within_vs_cross_gap.png`
- `outputs/modeling/supplemental/within_city_spatial/` stores the harder logistic-only within-city spatial sensitivity artifacts such as:
  - `within_city_spatial_sensitivity_summary.md`
  - `tables/within_city_spatial_selected_cities.csv`
  - `tables/within_city_spatial_sampling_diagnostics.csv`
  - `tables/within_city_spatial_metrics.csv`
  - `tables/within_city_spatial_summary.csv`
  - `tables/within_city_spatial_contrast.csv`
  - `tables/within_city_spatial_best_params.csv`
  - `tables/within_city_spatial_calibration_curve.csv`
  - `within_city_spatial_predictions.parquet`
- the spatial sensitivity keeps the same six-feature contract and the same `Reno` / `Charlotte` / `Detroit` city trio, but uses deterministic centroid quadrants and remains explicitly supplemental rather than equivalent to the canonical cross-city city-held-out benchmark
- `figures/modeling/supplemental/within_city_spatial/` stores the bounded spatial-sensitivity figure set, currently including `within_city_spatial_pr_auc_contrast.png`
- `outputs/modeling/supplemental/spatial_alignment/` is the output root produced by `src.run_modeling_spatial_alignment` for the RF-first representative-city full-city held-out spatial-alignment diagnostic. The CLI starts from the retained random-forest frontier run, keeps training and tuning on sampled training-city rows, scores full eligible rows in selected held-out cities, and remains a supplemental diagnostic rather than a full 30-city benchmark. Representative-city expected artifacts include:
  - `spatial_alignment_summary.md`
  - `spatial_alignment_metadata.json`
  - `tables/representative_city_selection.csv`
  - `tables/spatial_alignment_metrics_representative_cities.csv`
  - `tables/spatial_alignment_map_manifest.csv` when optional maps are generated
  - `full_city_predictions/*_random_forest_full_city_predictions.parquet`
- `outputs/modeling/supplemental/spatial_alignment_all_cities/` is the separate output root for the all-city expansion of the same RF-first spatial-alignment diagnostic. It uses `--city-selection all`, the existing five city-held-out outer folds, six held-out cities per fold, one train/tune pass per fold on sampled training-city rows, and full eligible scoring for all held-out cities in the fold. It is supplemental full-city spatial placement diagnostics, not a new canonical benchmark, and not a replacement for the retained sampled held-out-city PR AUC / recall benchmark. All-city expected artifacts include:
  - `spatial_alignment_summary.md`
  - `spatial_alignment_metadata.json`
  - `tables/all_city_selection.csv`
  - `tables/spatial_alignment_metrics_all_cities.csv`
  - `tables/spatial_alignment_map_manifest.csv` only when optional maps are generated after metric review
  - `full_city_predictions/*_random_forest_full_city_predictions.parquet`
- produced full-city spatial-alignment prediction tables include:
  - `city_id`
  - `city_name`
  - `climate_group`
  - `outer_fold`
  - `cell_id`
  - `centroid_lon`
  - `centroid_lat`
  - `hotspot_10pct`
  - `model_name`
  - `predicted_probability`
  - `prediction_scope`
  - `training_sample_rows_per_city`
  - `source_reference_run_dir`
- produced full-city spatial-alignment metric tables include one row per selected city, model, smoothing scale, and threshold, with Spearman surface correlation, top-region overlap, observed mass captured, centroid distance, median nearest-region distance, grid-cell-size diagnostics, projected CRS, and grid reconstruction status
- `figures/modeling/supplemental/spatial_alignment/` stores optional representative-city five-panel spatial-alignment maps generated from the full-city prediction files, starting with medium-scale (`300 m`) maps named like `<city_slug>_city<id>_random_forest_medium_surface_alignment.png`
- `figures/modeling/supplemental/spatial_alignment_all_cities/` stores optional selected all-city expansion maps generated after reviewing `tables/spatial_alignment_metrics_all_cities.csv`; the current medium-scale (`300 m`) supplemental set covers Nashville, San Francisco, Portland, and Las Vegas
- `outputs/modeling/supplemental/feature_importance/` stores retained-run interpretation markdown plus tables such as:
  - `feature_importance_summary.md`
  - `tables/logistic_post_preprocessing_feature_names.csv`
  - `tables/logistic_coefficients_by_fold.csv`
  - `tables/logistic_coefficients_summary.csv`
  - `tables/logistic_permutation_importance_by_fold.csv`
  - `tables/logistic_permutation_importance_summary.csv`
  - `tables/logistic_refit_fold_metrics.csv`
  - `tables/rf_permutation_importance_by_fold.csv`
  - `tables/rf_permutation_importance_summary.csv`
  - `tables/rf_impurity_importance_by_fold.csv`
  - `tables/rf_impurity_importance_summary.csv`
  - `tables/rf_refit_fold_metrics.csv`
- `figures/modeling/supplemental/feature_importance/` stores ranked-importance and coefficient-summary figures such as `feature_importance_ranked_summary.png`; the figure keeps logistic coefficients and RF held-out permutation importance as the primary displayed summaries rather than promoting the appendix-only RF impurity export
- `outputs/storage/` continues to hold storage-management and cache-audit artifacts
- `figures/data_processing/reference/` stores shared inspection figures such as the city-point map that are not tied to one city summary

## Transfer Inference Input Contract

Primary input:

- one new-city feature parquet already aligned to the retained six-feature first-pass contract

Required columns:

- `cell_id`
- `impervious_pct`
- `elevation_m`
- `dist_to_water_m`
- `ndvi_median_may_aug`
- `land_cover_class`
- `climate_group`

Optional reporting/map columns:

- `city_id`
- `city_name`
- `centroid_lon`
- `centroid_lat`

Behavior notes:

- the CLI validates required columns against the retained package `feature_contract.json`
- `cell_id` must be present and unique
- the parquet is expected to represent one city per run
- if centroid columns are present, the transfer figure is a simple predicted-risk map plus predicted top-decile hotspot panel
- if centroid columns are absent, the CLI still writes a fallback figure so the transfer artifact set is deterministic
- transfer inference outputs are application artifacts derived from the retained package and are not evaluation-equivalent replacements for the canonical city-held-out benchmark
