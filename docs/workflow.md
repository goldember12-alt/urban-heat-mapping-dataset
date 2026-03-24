# End-to-End Workflow

This project is best understood as an end-to-end urban heat study, not only as a geospatial preprocessing pipeline. The workflow below separates what is already implemented in code from what is documented as the next modeling and deliverable stages.

## Workflow At A Glance

1. Define the study design and target
2. Build study areas and 30 m grids
3. Acquire remote-sensing and support-layer inputs
4. Prepare support layers and assemble per-city features
5. Merge the final modeling dataset
6. Audit the final dataset and create city-held-out folds
7. Run baseline models
8. Expand to main models, evaluation, and map deliverables

## 1. Study Design And Target Definition

Project intent:

- Build a cross-city spatial ML framework for urban heat risk across 30 U.S. cities
- Use one 30 m grid cell as the analytic unit
- Predict urban heat hotspots in a way that generalizes to held-out cities

Core label definition:

- `lst_median_may_aug` is built from valid daytime ECOSTRESS observations
- `hotspot_10pct` is defined within each city from the upper 10% of valid cell-level LST values

Modeling contract:

- Split by `city_id`, not by individual cells
- Keep all preprocessing and tuning inside the training cities for each outer split
- Evaluate on held-out cities only

Status:

- Design is documented and reflected in the final dataset schema
- The grouped-city modeling plan is documented
- Only the baseline-modeling stage is currently implemented in code

## 2. City Selection, Study Areas, And Grid Generation

Implemented now:

- Load the 30-city configuration from `cities.csv`
- Identify the Census urban area containing the city center
- Preserve the core urban geometry and buffer it by 2 km by default
- Build the master 30 m grid in local UTM coordinates

Key outputs:

- `data_processed/study_areas/*_study_area.gpkg`
- `data_processed/city_grids/*_grid_30m.gpkg`

Main entrypoints:

- `src.run_city_processing`
- `src.run_city_batch_processing`

## 3. Data Acquisition

### AppEEARS NDVI And ECOSTRESS

Implemented now:

- Export one AppEEARS AOI GeoJSON per city in EPSG:4326
- Run AppEEARS preflight checks
- Submit, poll, and download NDVI or ECOSTRESS requests with resumable status tracking

Key outputs:

- `data_processed/appeears_aoi/`
- `data_processed/appeears_status/`
- `data_raw/ndvi/<city_slug>/`
- `data_raw/ecostress/<city_slug>/`

Main entrypoint:

- `src.run_appeears_acquisition`

### Raw Support Layers

Implemented now:

- Acquire official DEM, NLCD land-cover, NLCD impervious, and NHDPlus water inputs
- Preserve reusable downloads under `data_raw/cache/`
- Materialize deterministic city-specific raw files

Key outputs:

- `data_raw/dem/<city_slug>/`
- `data_raw/nlcd/<city_slug>/`
- `data_raw/hydro/<city_slug>/`
- `data_processed/support_layers/raw_data_acquisition_summary.json`
- `data_processed/support_layers/raw_data_acquisition_summary.csv`

Main entrypoint:

- `src.run_raw_data_acquisition`

## 4. Support-Layer Prep, Feature Assembly, And Data-Processing Reporting

Implemented now:

- Clip deterministic raw support inputs into prepared support artifacts
- Align source rasters to the city grid
- Compute cell-level elevation, land cover, imperviousness, distance to water, NDVI, and ECOSTRESS-derived LST
- Support `study_area` and `core_city` cell filtering modes
- Generate report-style per-city data-processing summaries, tables, and figures using the same pattern previously used only for Phoenix

Key outputs:

- `data_processed/support_layers/<city_stem>/`
- `data_processed/intermediate/aligned_rasters/`
- `data_processed/intermediate/city_features/`
- `data_processed/city_features/*.gpkg`
- `data_processed/city_features/*.parquet`
- `outputs/data_processing/<city_stem>/<city_slug>_data_summary.md`
- `outputs/data_processing/<city_stem>/tables/*.csv`
- `figures/data_processing/<city_stem>/*.png`
- `outputs/data_processing/data_processing_report_summary.csv`

Main entrypoints:

- `src.run_support_layers`
- `src.run_city_features`
- `src.run_city_features_batch`
- `src.run_data_processing_reports`
- `src.summarize_phoenix_dataset` as a Phoenix compatibility wrapper over the shared reporting path

Operational status:

- Full-stack orchestration has been manually verified for Phoenix, Tucson, Las Vegas, and Albuquerque
- Full 30-city completion is still limited by acquisition/runtime rather than missing code paths
- Report-style city summaries now use split roots by stage: data-processing artifacts under `outputs/data_processing/` and `figures/data_processing/`, with `outputs/modeling/` and `figures/modeling/` reserved for later ML/evaluation deliverables

## 5. Final Dataset Assembly

Implemented now:

- Merge per-city parquet outputs
- Drop open-water cells
- Drop rows with fewer than 3 valid ECOSTRESS passes
- Recompute `hotspot_10pct` within each city

Canonical outputs:

- `data_processed/final/final_dataset.parquet`
- `data_processed/final/final_dataset.csv`

Main entrypoint:

- `src.run_final_dataset_assembly`

## 6. Modeling-Ready Handoff

Implemented now:

- Audit the canonical final parquet without loading unnecessary columns
- Generate deterministic city-level outer folds for held-out-city modeling
- Save summary artifacts for collaborators under `data_processed/modeling/`

Key outputs:

- `data_processed/modeling/final_dataset_audit_summary.json`
- `data_processed/modeling/final_dataset_audit.md`
- `data_processed/modeling/final_dataset_city_summary.csv`
- `data_processed/modeling/final_dataset_feature_missingness.csv`
- `data_processed/modeling/final_dataset_feature_missingness_by_city.csv`
- `data_processed/modeling/city_outer_folds.parquet`
- `data_processed/modeling/city_outer_folds.csv`

Main entrypoints:

- `src.audit_final_dataset`
- `src.make_model_folds`

Verification status:

- The canonical modeling-prep stage has been manually verified on the real `final_dataset.parquet`
- Fold generation has been rerun to confirm deterministic output

## 7. Baseline Modeling

Implemented now:

- Train a city-held-out baseline stage from the canonical final dataset plus `city_outer_folds`
- Use leakage-safe preprocessing fitted only on training cities
- Write fold metrics, overall metrics, saved validation predictions, and model artifacts

Current implemented baseline models:

- Logistic regression baseline
- Lightweight decision-stump comparison

Key outputs:

- `data_processed/modeling/baselines/baseline_metrics_by_fold.csv`
- `data_processed/modeling/baselines/baseline_metrics_overall.csv`
- `data_processed/modeling/baselines/baseline_leakage_checks.csv`
- `data_processed/modeling/baselines/baseline_assumptions.md`
- `data_processed/modeling/baselines/baseline_run_summary.json`
- `data_processed/modeling/baselines/validation_predictions/`
- `data_processed/modeling/baselines/model_artifacts/`

Main entrypoint:

- `src.run_model_baselines`

Honest status line:

- The baseline-modeling code and tests exist, but a full canonical run on the real 30-city dataset has not yet been recorded in `docs/chat_handoff.md`

## 8. Main Modeling Roadmap

Planned next, not yet implemented as full production code:

- Logistic regression with `solver="saga"` inside an sklearn `Pipeline`
- Random forest inside an sklearn `Pipeline`
- `GroupKFold` or equivalent grouped city CV for training-city-only model selection
- `GridSearchCV` or equivalent tuning restricted to the training cities in each outer split

Design rules for those stages:

- Group by `city_id`
- Never tune on held-out cities
- Start with baselines before richer models
- Treat `final_dataset.parquet` as the canonical modeling input

The detailed modeling contract lives in [`docs/modeling_plan.md`](modeling_plan.md).

## 9. Evaluation And Deliverables

Planned next:

- Primary metric: PR AUC
- Additional evaluation: recall at top 10% predicted risk, calibration review, and held-out-city comparison tables
- Deliverables: predicted hotspot maps, true hotspot maps, residual/error maps, and eventually transfer to new cities

Current status:

- Evaluation artifacts currently exist only for the baseline-modeling stage
- The map-deliverable stage for held-out predictions is planned but not yet implemented

## 10. Orchestration

Implemented now:

- Thin acquisition orchestration for raw/support/AppEEARS stages
- Full-stack city orchestration through feature assembly
- End-to-end full pipeline entrypoint that can chain the main implemented stages

Relevant entrypoints:

- `src.run_acquisition_orchestration`
- `src.run_full_stack_orchestration`
- `src.run_full_pipeline`

Use [`docs/chat_handoff.md`](chat_handoff.md) for the latest verified checkpoint, current blockers, and the next recommended manual step.
