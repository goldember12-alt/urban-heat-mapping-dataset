# End-to-End Workflow

This project is best understood as an end-to-end urban heat study, not only as a geospatial preprocessing pipeline. The workflow below separates what is already implemented in code from what remains the next modeling and deliverable stage.

## Workflow At A Glance

1. Define the study design and target
2. Build study areas and 30 m grids
3. Acquire remote-sensing and support-layer inputs
4. Prepare support layers and assemble per-city features
5. Merge the final modeling dataset
6. Audit the final dataset and create city-held-out folds
7. Run first-pass held-out-city models
8. Expand to benchmark reporting, support figures, bounded supplemental analyses, final-train packaging, and transfer inference

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
- The first-pass grouped modeling layer is now implemented in code

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
- Backfill the bounded Phase 3A NLCD neighborhood-context bundle into existing per-city feature artifacts with `src.run_phase3a_nlcd_bundle`
- Support `study_area` and `core_city` cell filtering modes
- Generate report-style per-city data-processing summaries, tables, and figures using the same pattern previously used only for Phoenix

Key outputs:

- `data_processed/support_layers/<city_stem>/`
- `data_processed/intermediate/aligned_rasters/`
- `data_processed/intermediate/city_features/`
- `data_processed/city_features/*.gpkg`
- `data_processed/city_features/*.parquet`
- `outputs/data_processing/city_summaries/<city_stem>/<city_slug>_data_summary.md`
- `outputs/data_processing/city_summaries/<city_stem>/tables/*.csv`
- `figures/data_processing/city_summaries/<city_stem>/*.png`
- `outputs/data_processing/batch_reports/data_processing_report_summary.csv`

Main entrypoints:

- `src.run_support_layers`
- `src.run_city_features`
- `src.run_city_features_batch`
- `src.run_phase3a_nlcd_bundle`
- `src.run_data_processing_reports`
- `src.summarize_phoenix_dataset` as a Phoenix compatibility wrapper over the shared reporting path

Operational status:

- Full-stack orchestration has been manually verified for Phoenix, Tucson, Las Vegas, and Albuquerque
- Full 30-city completion is still limited by acquisition/runtime rather than missing code paths
- Report-style city summaries now use dedicated sub-roots: per-city artifacts under `outputs/data_processing/city_summaries/` and `figures/data_processing/city_summaries/`, batch status tables under `outputs/data_processing/batch_reports/`, and separate modeling roots under `outputs/modeling/` and `figures/modeling/`

## 5. Final Dataset Assembly

Implemented now:

- Merge per-city parquet outputs
- Drop open-water cells
- Drop rows with fewer than 3 valid ECOSTRESS passes
- Recompute `hotspot_10pct` within each city
- Preserve the retained row-level contract while carrying the bounded Phase 3A columns into the canonical final dataset schema

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

## 7. First-Pass Modeling

Implemented now:

- Train city-held-out baseline models from the canonical final dataset plus `city_outer_folds`
- Train grouped logistic regression with `solver="saga"` using training-city-only preprocessing and tuning
- Train grouped random forest with the same held-out-city discipline
- Run a bounded histogram-gradient-boosting Phase 1 candidate benchmark on the same six-feature city-held-out contract without rewriting the retained logistic/RF benchmark story
- Run a bounded logistic SAGA Phase 2 climate-interaction benchmark on the same six-feature city-held-out contract, with training-only climate-by-numeric interactions and without rewriting the retained logistic/RF benchmark story
- Run a bounded Phase 3A richer-predictor logistic benchmark on the retained `5000` rows-per-city slice, with the NLCD neighborhood-context bundle kept separate from the frozen six-feature benchmark story
- Save held-out prediction tables, fold metrics, per-city metrics, best-parameter summaries, calibration tables, and run metadata under `outputs/modeling/`
- Refresh a lightweight cross-run tuning-history table plus manual-annotation template under `outputs/modeling/`
- Auto-generate unique tuned-model output directories when `--output-dir` is omitted so important runs are easier to preserve and compare without accidental overwrites

Current implemented baseline models:

- Global mean baseline
- Land-cover-only baseline
- Impervious-only baseline
- Climate-only baseline

Current implemented main models:

- Logistic regression with `solver="saga"` in an sklearn `Pipeline`
- Random forest in an sklearn `Pipeline`

Current benchmark-strengthening candidate:

- Histogram gradient boosting in an sklearn `Pipeline`, limited to a smoke-sized Phase 1 checkpoint on the fixed six-feature contract
- Logistic SAGA with explicit training-only climate-by-numeric interactions, currently landed as a bounded Phase 2 checkpoint on the fixed six-feature contract
- Logistic SAGA with the bounded Phase 3A richer-feature NLCD neighborhood-context bundle, currently landed as a separate all-fold sampled comparison against retained logistic `5000`

Key outputs:

- `outputs/modeling/baselines/metrics_by_fold.csv`
- `outputs/modeling/baselines/metrics_by_city.csv`
- `outputs/modeling/baselines/metrics_summary.csv`
- `outputs/modeling/baselines/heldout_predictions.parquet`
- `outputs/modeling/logistic_saga/metrics_by_fold.csv`
- `outputs/modeling/logistic_saga/metrics_by_city.csv`
- `outputs/modeling/logistic_saga/metrics_summary.csv`
- `outputs/modeling/logistic_saga/best_params_by_fold.csv`
- `outputs/modeling/logistic_saga/heldout_predictions.parquet`
- `outputs/modeling/logistic_saga_climate_interactions/metrics_by_fold.csv`
- `outputs/modeling/logistic_saga_climate_interactions/metrics_by_city.csv`
- `outputs/modeling/logistic_saga_climate_interactions/metrics_summary.csv`
- `outputs/modeling/logistic_saga_climate_interactions/best_params_by_fold.csv`
- `outputs/modeling/logistic_saga_climate_interactions/heldout_predictions.parquet`
- `outputs/modeling/random_forest/metrics_by_fold.csv`
- `outputs/modeling/random_forest/metrics_by_city.csv`
- `outputs/modeling/random_forest/metrics_summary.csv`
- `outputs/modeling/random_forest/best_params_by_fold.csv`
- `outputs/modeling/random_forest/heldout_predictions.parquet`
- `outputs/modeling/hist_gradient_boosting/metrics_by_fold.csv`
- `outputs/modeling/hist_gradient_boosting/metrics_by_city.csv`
- `outputs/modeling/hist_gradient_boosting/metrics_summary.csv`
- `outputs/modeling/hist_gradient_boosting/best_params_by_fold.csv`
- `outputs/modeling/hist_gradient_boosting/heldout_predictions.parquet`
- `outputs/modeling/run_registry.jsonl`
- `outputs/modeling/tuning_history.csv`
- `outputs/modeling/tuning_history_annotations.csv`
- `outputs/modeling/reporting/*.md`
- `outputs/modeling/reporting/tables/*.csv`
- `figures/modeling/reporting/*.png`

Main entrypoints:

- `src.run_modeling_baselines`
- `src.run_logistic_saga`
- `src.run_random_forest`
- `src.run_logistic_saga_climate_interactions`
- `src.run_hist_gradient_boosting`
- `src.run_modeling_reporting`
- `src.run_modeling_supplemental`

Honest status line:

- The new first-pass modeling layer is test-verified on synthetic grouped-city fixtures, but a full canonical run on the real 30-city dataset has not yet been recorded in `docs/chat_handoff.md`

## 8. Evaluation, Reporting, Transfer, And Supplemental Deliverables

Implemented now:

- Primary metric: PR AUC
- Supporting evaluation: recall at top 10% predicted risk, per-city PR AUC tables, calibration-curve tables, city-level RF-vs-logistic error summaries, and benchmark comparison figures
- The reporting layer can now also materialize optional Phase 1 HGB-vs-RF comparison tables when a bounded HGB checkpoint is supplied to `src.run_modeling_reporting`
- The reporting layer can now also materialize optional Phase 2 logistic-climate-interaction comparison and climate-disparity tables when a bounded climate-interaction checkpoint is supplied to `src.run_modeling_reporting`
- `outputs/modeling/reporting/cross_city_benchmark_report.md` is the headline benchmark reference for the modeling story
- Held-out prediction tables include `city_id`, `city_name`, `climate_group`, `cell_id`, `centroid_lon`, and `centroid_lat` so later map export code can build on the saved outputs directly
- A retained-run held-out map reporting layer under `outputs/modeling/reporting/heldout_city_maps/` and `figures/modeling/heldout_city_maps/` that exports representative predicted-hotspot, true-hotspot, and categorical error triptychs without rerunning the benchmark ladder; these remain support artifacts under the retained benchmark rather than replacement evaluation results
- A bounded final-train transfer package under `outputs/modeling/final_train/` that refits the retained benchmark-selected model on all cities at the retained sample cap and saves the fitted model plus transfer metadata
- A separate transfer-inference application path under `outputs/modeling/transfer_inference/` and `figures/modeling/transfer_inference/` that applies the retained transfer package to one new-city feature parquet, validates the six-feature schema, and writes deterministic prediction/summary/map artifacts without computing new held-out benchmark metrics
- A bounded supplemental within-city layer under `outputs/modeling/supplemental/within_city/` and `figures/modeling/supplemental/within_city/` that is explicitly labeled exploratory/easier and presented only as a contrast to the canonical held-out-city benchmark
- A separate bounded all-city within-city layer under `outputs/modeling/supplemental/within_city_all_cities/` and `figures/modeling/supplemental/within_city_all_cities/` that keeps the same six-feature contract, uses up to `20,000` rows per city with `3` repeated stratified `80/20` splits, and summarizes climate-group patterns plus within-city-versus-retained-cross-city gaps without replacing the canonical benchmark
- A separate supplemental within-city spatial sensitivity layer under `outputs/modeling/supplemental/within_city_spatial/` and `figures/modeling/supplemental/within_city_spatial/` that keeps the same `Reno` / `Charlotte` / `Detroit` trio but uses deterministic centroid quadrants as a harder logistic-only within-city sensitivity rather than as a replacement for the canonical held-out-city benchmark
- A bounded retained-run interpretation layer under `outputs/modeling/supplemental/feature_importance/` and `figures/modeling/supplemental/feature_importance/` that refits saved outer-fold winners to export primary logistic coefficients, logistic held-out permutation cross-check tables, primary random-forest held-out permutation importance, and secondary/debug RF impurity appendix tables
- A supplemental full-city held-out spatial-alignment diagnostic under `outputs/modeling/supplemental/spatial_alignment/` and `figures/modeling/supplemental/spatial_alignment/` that starts from the retained random-forest frontier checkpoint, selects representative cities by climate-group median city PR AUC plus Denver if needed, refits each selected held-out fold on sampled training-city rows only, scores every eligible row in the selected held-out cities, and writes smoothed-surface alignment metrics at `150 m`, `300 m`, and `600 m`; this validated representative-city diagnostic is separate from all-city expansion outputs and is not a full 30-city benchmark
- A separate all-city spatial-alignment expansion root under `outputs/modeling/supplemental/spatial_alignment_all_cities/` and `figures/modeling/supplemental/spatial_alignment_all_cities/` that uses `--city-selection all`, the existing five outer folds, six held-out cities per fold, one train/tune pass per fold on sampled training-city rows, and full eligible scoring for every held-out city before computing `150 m`, `300 m`, and `600 m` metrics for all 30 cities; this remains supplemental full-city spatial placement diagnostics rather than a new canonical benchmark or replacement for the retained sampled held-out-city PR AUC / recall benchmark, with optional selected `300 m` maps generated after metric review
- `src.run_modeling_supplemental` to regenerate the supplemental roots from retained artifacts plus the canonical parquet dataset, with `--run-within-city-all-cities` available for the heavier all-city within-city appendix and `--run-within-city-spatial` reserved for the separate spatial-block sensitivity path
- `src.run_modeling_spatial_alignment` to regenerate the RF-first representative-city full-city spatial-alignment diagnostic from the retained frontier run or the separate all-city metric expansion when passed `--city-selection all` and the all-city output roots
- `src.run_modeling_spatial_reporting` to regenerate the held-out map reporting root from retained prediction artifacts
- `src.run_modeling_transfer_package` to regenerate the bounded final-train package from the retained benchmark-selected run metadata and best-parameter summaries
- `src.run_transfer_inference` to score one new-city feature parquet with the retained package and materialize deterministic transfer-inference outputs

Still later, if explicitly reopened:

- Scaling strategy for full-canonical runs if workstation memory/runtime becomes the main blocker

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
