# STAT 5630 Final Project - Urban Heat Dataset Construction

## Project Overview

This repository builds a reproducible Python geospatial workflow for constructing a cross-city urban heat dataset for 30 U.S. cities.

Target analytic unit: one row per 30 m grid cell per city.

## Implemented Pipeline Stages

1. City boundary and 2 km buffered study area construction from Census urban-area lookup, with persisted core-urban geometry metadata.
2. Master 30 m city grid generation.
3. Batch city boundary/grid runner.
4. AppEEARS prerequisite preflight audit for all expected cities.
5. AppEEARS AOI export from city study areas (`data_processed/appeears_aoi/*.geojson`, EPSG:4326).
6. AppEEARS acquisition runner (submit, poll, download, resumable state) for NDVI and ECOSTRESS.
7. Support-layer preflight audit for DEM, NLCD land cover, NLCD impervious, and hydro inputs.
8. Raw support-layer acquisition runner for official USGS 3DEP, MRLC Annual NLCD, and USGS NHDPlus HR sources.
9. Support-layer prep runner that clips deterministic per-city support files into `data_processed/support_layers/<city_stem>/`.
10. Cache audit/cleanup utility for `data_raw/cache/` with dry-run metadata reporting and safe targeted prune modes.
11. Thin acquisition orchestrator that sequences raw support acquisition, support prep, NDVI AppEEARS, ECOSTRESS AppEEARS, and writes a restart-safe status summary.
12. Full-stack city orchestrator that extends the acquisition flow through feature assembly with per-city stage statuses and restart-safe skip/fail reasons.
13. Generic raster alignment framework to city grid template.
14. DEM extraction (aligned).
15. NLCD land-cover and impervious extraction (aligned).
16. Hydrography distance-to-water raster generation and extraction.
17. Per-city feature assembly outputs (`.gpkg` + `.parquet`) with intermediate saves.
18. Final merged dataset assembly (`.parquet` + `.csv`) with row rules and `hotspot_10pct`.
19. Final-dataset audit and deterministic city-level fold generation for modeling handoff.
20. Leak-safe city-held-out baseline modeling with streaming logistic regression, decision-stump comparison, fold metrics, and saved validation predictions.

Latest verified workspace checkpoint on 2026-03-19:

- Full-stack orchestration has completed end to end for Phoenix, Tucson, Las Vegas, and Albuquerque.
- Feature assembly now keeps the AppEEARS handoff strict: native NDVI/LST rasters are preferred, generic legacy names like `ndvi_1.tif` are not treated as native AppEEARS values, and unreadable TIFFs are skipped with warnings when enough valid rasters remain.

## Required Final Columns

- `city_id`
- `city_name`
- `climate_group`
- `cell_id`
- `centroid_lon`
- `centroid_lat`
- `impervious_pct`
- `land_cover_class`
- `elevation_m`
- `dist_to_water_m`
- `ndvi_median_may_aug`
- `lst_median_may_aug`
- `n_valid_ecostress_passes`
- `hotspot_10pct`

## AppEEARS Environment Variables

The acquisition CLI reads credentials from environment variables only:

- `APPEEARS_API_TOKEN` (preferred bearer token), or
- `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD`

Optional:

- `APPEEARS_BASE_URL` is not required for normal runs (default is baked into config).

Secrets are not printed in logs.

Recommended local operator pattern:

- Store local secrets in a gitignored `.env.local` file.
- Load it into the current PowerShell session before running AppEEARS-dependent commands:

```powershell
Get-Content .env.local | Where-Object { $_ -match '^\s*[^#].+=' } | ForEach-Object {
    $name, $value = $_ -split '=', 2
    Set-Item -Path "Env:$name" -Value $value
}
```

- If credentials are absent, AppEEARS-dependent stages now fail fast with `blocked_missing_credentials` and list the exact missing environment variables, while raw/support stages continue when possible.

## Support-Layer Standardization

The repo now treats support layers as a deterministic per-city raw-input contract, matching the existing Phoenix layout and feature-discovery assumptions:

- `data_raw/dem/<city_slug>/<city_slug>_dem_3dep_30m.tif`
- `data_raw/nlcd/<city_slug>/<city_slug>_nlcd_2021_land_cover_30m.tif`
- `data_raw/nlcd/<city_slug>/<city_slug>_nlcd_2021_impervious_30m.tif`
- `data_raw/hydro/<city_slug>/<city_slug>_nhdplus_water.gpkg`

The raw acquisition stage caches reusable upstream downloads under `data_raw/cache/` and then clips deterministic city-specific outputs into the raw contract above.

The standardized prep stage keeps those raw files immutable and writes deterministic prepared outputs to:

- `data_processed/support_layers/<city_stem>/dem_prepared.tif`
- `data_processed/support_layers/<city_stem>/nlcd_land_cover_prepared.tif`
- `data_processed/support_layers/<city_stem>/nlcd_impervious_prepared.tif`
- `data_processed/support_layers/<city_stem>/hydro_water_prepared.gpkg`

`src.feature_assembly` now prefers prepared support outputs when they exist and otherwise falls back to the existing raw-folder discovery behavior.
AppEEARS raster discovery is product-aware: native filenames such as `MOD13A1...NDVI...tif` and `ECO_L2T_LSTE...LST...tif` are treated as value rasters, while obvious QA/cloud/error sidecars and generic legacy files such as `ndvi_1.tif` are excluded.
Raster-stack sampling also validates TIFF readability before use so stale/corrupt files are warned and skipped instead of aborting a city when valid rasters remain.
Feature assembly now also separates acquisition footprint from training footprint:

- Current behavior: `--buffer-m 2000` with `--cell-filter-mode study_area`
- Buffered acquisition + core-city-only training cells: `--buffer-m 2000` with `--cell-filter-mode core_city`
- No buffer: `--buffer-m 0` with `--cell-filter-mode study_area`

Switching from `study_area` to `core_city` after buffered study areas already exist only requires refreshed study-area metadata plus feature/final-output regeneration. Switching to `--buffer-m 0` changes the acquisition footprint itself, so AOIs, raw support, prepared support, features, and final outputs should all be regenerated for the affected cities.

## Empty City To Support-Layer-Ready City

Automated:

- Study areas and 30 m grids are already automated for one city via `src.run_city_processing` and for all 30 cities via `src.run_city_batch_processing`.
- The prerequisite audit is automated via `src.run_support_layers --preflight-only`.
- Raw support-layer acquisition is automated via `src.run_raw_data_acquisition`.
- Support-layer clipping/prep is automated via `src.run_support_layers`.

Operational notes:

- The MRLC Annual NLCD cache downloads are large and are intentionally reused across cities.
- The raw acquisition runner is restartable: it skips completed deterministic outputs unless `--force` is passed and reuses cached DEM tiles, NLCD bundles, and NHDPlus HR packages.
- The largest safely regenerable cache artifacts are the extracted NLCD rasters and extracted hydro GeoPackages. Use the cache cleanup CLI in dry-run mode first and keep its JSON report outside `data_raw/cache/`.
- Use `data_processed/support_layers/raw_data_acquisition_summary.csv` as the canonical machine-readable status summary for the new acquisition stage.
- After raw acquisition completes, rerun `src.run_support_layers --preflight-only` and then run `src.run_support_layers` for the same city set.

## CLI Entrypoints

Initial city points + figure:

```powershell
.venv\Scripts\python.exe -m src.run_initial_outputs
```

One city boundary/grid:

```powershell
.venv\Scripts\python.exe -m src.run_city_processing --city-name Phoenix
```

All-city boundary/grid:

```powershell
.venv\Scripts\python.exe -m src.run_city_batch_processing --resolution 30
```

AppEEARS preflight only:

```powershell
.venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ndvi --preflight-only
```

AppEEARS acquisition:

```powershell
.venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ndvi --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31
```

```powershell
.venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ecostress --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31
```

```powershell
.venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ndvi --start-date 2023-05-01 --end-date 2023-08-31 --retry-incomplete
```

Support-layer preflight only:

```powershell
.venv\Scripts\python.exe -m src.run_support_layers --preflight-only
```

Acquire raw support layers for all currently missing cities:

```powershell
.venv\Scripts\python.exe -m src.run_raw_data_acquisition --all-missing
```

Acquire one dataset group for selected cities:

```powershell
.venv\Scripts\python.exe -m src.run_raw_data_acquisition --city-ids 1 2 3 --dataset dem
```

```powershell
.venv\Scripts\python.exe -m src.run_raw_data_acquisition --dataset nlcd --all-missing
```

```powershell
.venv\Scripts\python.exe -m src.run_raw_data_acquisition --dataset hydro --all-missing
```

Force rebuilding requested deterministic raw outputs:

```powershell
.venv\Scripts\python.exe -m src.run_raw_data_acquisition --city-ids 1 --force
```

Audit cache usage and produce a dry-run cleanup plan:

```powershell
.venv\Scripts\python.exe -m src.run_cache_cleanup --prune-modes regenerable --protect-recent-hours 24 --report-json outputs\storage\cache_cleanup_dry_run.json
```

Recompute the same plan without the recent-file protection gate:

```powershell
.venv\Scripts\python.exe -m src.run_cache_cleanup --prune-modes regenerable --protect-recent-hours 0 --report-json outputs\storage\cache_cleanup_dry_run_no_age_gate.json
```

Prepare support layers for one city:

```powershell
.venv\Scripts\python.exe -m src.run_support_layers --city-ids 1
```

Prepare support layers for all cities:

```powershell
.venv\Scripts\python.exe -m src.run_support_layers
```

Supported support-layer mode flag:

- `--preflight-only`
- `--overwrite`

Supported raw acquisition mode flags:

- `--all-missing`
- `--dataset {all,dem,nlcd,hydro}`
- `--force`

Supported cache cleanup modes:

- `--prune-modes {partials,nlcd-extracted,hydro-extracted,extracted,regenerable}`
- `--protect-recent-hours`
- `--execute`
- `--report-json`

Supported AppEEARS acquisition modes:

- `--preflight-only`
- `--submit-only`
- `--poll-only`
- `--download-only`
- `--retry-incomplete`

Thin acquisition orchestrator:

```powershell
.venv\Scripts\python.exe -m src.run_acquisition_orchestration --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31
```

```powershell
.venv\Scripts\python.exe -m src.run_acquisition_orchestration --all-missing --start-date 2023-05-01 --end-date 2023-08-31
```

Optional orchestrator mode flags:

- `--all-missing`
- `--force-raw`
- `--overwrite-support`

Verification note from the moved Windows workspace on 2026-03-18: the Phoenix orchestration command completed and rewrote the orchestration/AppEEARS summary files with the new OneDrive-backed paths, but the Phoenix raw NDVI and ECOSTRESS `.tif` timestamps remained at 2026-03-08. Treat that as restart/resume validation of the moved workspace, not as proof of a fresh AppEEARS submit/download on 2026-03-18.

Full-stack city orchestration:

```powershell
.venv\Scripts\python.exe -m src.run_full_stack_orchestration --city-ids 2,3,4 --start-date 2023-05-01 --end-date 2023-08-31
```

```powershell
.venv\Scripts\python.exe -m src.run_full_stack_orchestration --all-missing --start-date 2023-05-01 --end-date 2023-08-31
```

Full-stack status output:

- `data_processed/orchestration/full_stack_city_orchestration_summary.json`
- `data_processed/orchestration/full_stack_city_orchestration_summary.csv`

Per-city stage columns include raw support, support prep, NDVI, ECOSTRESS, and feature assembly statuses plus `error` and `message` fields. The feature stage only runs when upstream support and AppEEARS stages are complete or safely reusable.
Add `--cell-filter-mode core_city` when you want buffered upstream acquisition but only core-city cells in the final per-city training outputs.

One city feature extraction:

```powershell
.venv\Scripts\python.exe -m src.run_city_features --city-id 1 --max-cells 5000
```

```powershell
.venv\Scripts\python.exe -m src.run_city_features --city-id 1 --cell-filter-mode core_city
```

Batch feature extraction:

```powershell
.venv\Scripts\python.exe -m src.run_city_features_batch --existing-grids-only --city-ids 1 --max-cells 5000
```

Final merge only:

```powershell
.venv\Scripts\python.exe -m src.run_final_dataset_assembly
```

Final-dataset audit:

```powershell
.venv\Scripts\python.exe -m src.audit_final_dataset
```

Deterministic city-level folds:

```powershell
.venv\Scripts\python.exe -m src.make_model_folds --n-splits 5
```

Baseline modeling:

```powershell
.venv\Scripts\python.exe -m src.run_model_baselines
```

Run a subset of folds or models during smoke checks:

```powershell
.venv\Scripts\python.exe -m src.run_model_baselines --outer-folds 0 --models logistic_regression
```

End-to-end pipeline orchestrator:

```powershell
.venv\Scripts\python.exe -m src.run_full_pipeline --skip-city-processing --existing-grids-only --city-ids 1 --max-cells 5000
```

For stage-1 regeneration with no buffer:

```powershell
.venv\Scripts\python.exe -m src.run_city_batch_processing --buffer-m 0 --resolution 30
```

## Data Layout

- `data_raw/` immutable source data
- `data_raw/cache/` reusable upstream download/extraction cache for DEM, NLCD, and hydro packages
- `data_raw/dem/<city_slug>/` city-specific DEM source files
- `data_raw/nlcd/<city_slug>/` city-specific NLCD land-cover and impervious source files
- `data_raw/hydro/<city_slug>/` city-specific hydro source files
- `data_raw/ndvi/<city_slug>/` downloaded AppEEARS NDVI files
- `data_raw/ecostress/<city_slug>/` downloaded AppEEARS ECOSTRESS files
- `data_processed/study_areas/` city study areas with buffered geometry plus persisted core-urban metadata
- `data_processed/appeears_aoi/` AppEEARS AOI GeoJSON exports
- `data_processed/appeears_status/` preflight JSON/CSV plus acquisition summary JSON/CSV per product type
- `data_processed/orchestration/` thin acquisition orchestration summary JSON/CSV
- `data_processed/orchestration/` full-stack city orchestration summary JSON/CSV
- `data_processed/support_layers/` support-layer preflight summary, raw acquisition summary, prep summary, and per-city prepared support artifacts
- `data_processed/city_grids/` city master grids
- `data_processed/intermediate/` aligned rasters + unfiltered/filtered city feature tables
- `data_processed/city_features/` per-city feature outputs + batch summary
- `data_processed/final/` merged dataset outputs
- `data_processed/modeling/` final-dataset audit artifacts, deterministic city-level folds, and baseline-model outputs
- `docs/` workflow and data dictionary
- `tests/` automated tests

## Modeling Handoff

Canonical training dataset:

- `data_processed/final/final_dataset.parquet`

Initial modeling contract:

- Target column: `hotspot_10pct`
- Grouping column: `city_id`
- Use city-held-out evaluation only: no cells from a held-out city may appear in training or training-only preprocessing.
- Start with baseline models before main models.

Initial safe feature candidates for the first hotspot models:

- `impervious_pct`
- `land_cover_class`
- `elevation_m`
- `dist_to_water_m`
- `ndvi_median_may_aug`
- `climate_group`

Exclude from the first predictive feature set to avoid leakage or non-portable identifiers:

- `hotspot_10pct`
- `lst_median_may_aug`
- `n_valid_ecostress_passes`
- `cell_id`
- `city_id`
- `city_name`
- `centroid_lon`
- `centroid_lat`

Fold artifact for collaboration:

- `data_processed/modeling/city_outer_folds.parquet`
- `data_processed/modeling/city_outer_folds.csv`

Implemented baseline modeling outputs:

- `data_processed/modeling/baselines/baseline_metrics_by_fold.csv`
- `data_processed/modeling/baselines/baseline_metrics_overall.csv`
- `data_processed/modeling/baselines/baseline_leakage_checks.csv`
- `data_processed/modeling/baselines/baseline_assumptions.md`
- `data_processed/modeling/baselines/baseline_run_summary.json`
- `data_processed/modeling/baselines/validation_predictions/`
- `data_processed/modeling/baselines/model_artifacts/logistic_regression_coefficients.csv`
- `data_processed/modeling/baselines/model_artifacts/decision_stump_rules.csv`

Current baseline stage assumptions:

- The baseline runner loads only the required parquet columns for training or validation passes.
- Rows are assigned to folds by joining the city-level fold table back on `city_id`.
- Numeric features use train-fold-only mean imputation plus z-scoring and missing indicators.
- Categorical features use train-fold-only vocabularies plus explicit missing/unseen buckets.
- Overall metrics are fold aggregates; exact pooled out-of-fold ROC-AUC / PR-AUC is not computed in this first memory-safe baseline stage.

Recommended next modeling steps:

- Run `src.run_model_baselines` from the verified canonical `final_dataset.parquet` plus `city_outer_folds.*`.
- Inspect `data_processed/modeling/baselines/baseline_metrics_by_fold.csv`, `baseline_metrics_overall.csv`, and `baseline_leakage_checks.csv`.
- Review the saved validation predictions and the logistic coefficients / stump rules before moving to heavier tree ensembles or more flexible models.
- If the merged final dataset changes upstream, rerun `src.run_final_dataset_assembly`, `src.audit_final_dataset`, `src.make_model_folds --n-splits 5`, and then rerun `src.run_model_baselines`.
