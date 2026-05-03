# AGENTS.md

## Project

Build and maintain a reproducible end-to-end urban heat workflow for 30 U.S. cities that covers:

1. study design
2. geospatial data acquisition and preprocessing
3. per-city feature assembly
4. final dataset generation
5. modeling-ready handoff
6. city-held-out machine learning evaluation
7. later modeling figures and transfer-oriented deliverables

This repo is not only a preprocessing pipeline. It is a cross-city urban heat dataset and modeling framework.

## Core Objective

Produce a canonical 30 m cell-level dataset and use it to predict urban heat hotspots in cities that were not seen during training.

Analytic unit:

- one row per 30 m grid cell per city

Canonical label:

- `hotspot_10pct`

Grouping variable for evaluation:

- `city_id`

## Canonical Outputs

Primary dataset artifacts:

- `data_processed/final/final_dataset.parquet`
- `data_processed/final/final_dataset.csv`

Per-city feature artifacts:

- `data_processed/city_features/*.parquet`
- `data_processed/city_features/*.gpkg`

Modeling handoff artifacts:

- `data_processed/modeling/final_dataset_audit_summary.json`
- `data_processed/modeling/final_dataset_audit.md`
- `data_processed/modeling/final_dataset_city_summary.csv`
- `data_processed/modeling/final_dataset_feature_missingness.csv`
- `data_processed/modeling/final_dataset_feature_missingness_by_city.csv`
- `data_processed/modeling/city_outer_folds.parquet`
- `data_processed/modeling/city_outer_folds.csv`

Data-processing report outputs:

- `outputs/data_processing/<city_stem>/`
- `figures/data_processing/<city_stem>/`

First-pass modeling outputs:

- `outputs/modeling/baselines/`
- `outputs/modeling/logistic_saga/`
- `outputs/modeling/random_forest/`

Reserved later-stage modeling figures:

- `figures/modeling/`

## Canonical Final Dataset Columns

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

## Workflow Contract

The repo should be treated as an end-to-end lifecycle with these stages:

1. define study design and target
2. build study areas and 30 m grids
3. acquire AppEEARS and support-layer inputs
4. prepare support layers and assemble per-city features
5. merge the final dataset
6. audit the final dataset and create held-out-city folds
7. run first-pass held-out-city models
8. expand to figures, map deliverables, and final-train packaging

## Data Logic

Study design and feature logic:

- Study area = Census urban area polygon containing the city center, buffered by 2 km by default
- Preserve both buffered study-area geometry and the original core urban geometry
- Build the master 30 m grid in a local UTM CRS
- Align raster and vector-derived features to the master grid
- Compute cell-level elevation, land cover, imperviousness, distance to water, NDVI, and ECOSTRESS-derived LST
- Support both `study_area` and `core_city` cell filtering modes where implemented

Final assembly rules:

- Drop open-water cells where `land_cover_class == 11` when land cover is available
- Drop rows with `n_valid_ecostress_passes < 3` when LST is available
- Recompute `hotspot_10pct` within each city after row filtering

## Modeling Contract

Treat modeling as a first-class pipeline stage.

Canonical modeling inputs:

- `data_processed/final/final_dataset.parquet`
- `data_processed/modeling/city_outer_folds.parquet`
- `data_processed/modeling/city_outer_folds.csv`

Leakage-safe evaluation rules:

- split by `city_id`, not by individual cells
- held-out cities must remain fully unseen during training
- all preprocessing, imputation, scaling, encoding, feature selection, and tuning must be fit using training-city rows only
- tuning must happen only inside the training cities for each outer split

Implemented first-pass model runners:

- `src.run_modeling_baselines`
- `src.run_logistic_saga`
- `src.run_random_forest`

Implemented baseline models:

- `global_mean_baseline`
- `land_cover_only_baseline`
- `impervious_only_baseline`
- `climate_only_baseline`

Implemented main models:

- logistic regression with `solver="saga"` in an sklearn `Pipeline`
- random forest in an sklearn `Pipeline`

Implemented evaluation outputs:

- fold-level PR AUC
- per-city PR AUC
- recall at top 10% predicted risk
- calibration-curve tables
- held-out prediction tables
- best-parameter summaries for tuned models

Feature-contract guidance for the first hotspot models:

Safe predictive features:

- `impervious_pct`
- `land_cover_class`
- `elevation_m`
- `dist_to_water_m`
- `ndvi_median_may_aug`
- `climate_group`

Do not use these as first-pass predictive features:

- `hotspot_10pct`
- `lst_median_may_aug`
- `n_valid_ecostress_passes`
- `cell_id`
- `city_id`
- `city_name`
- `centroid_lon`
- `centroid_lat`

## Preset And Benchmarking Rules

`README.md` is the canonical definition of `smoke` versus `full`.

Use that document as the source of truth for:

- what `smoke` means
- what `full` means
- how those presets should be described in methods/results language
- the current search-space sizes in code

Do not describe `smoke` runs as final benchmark-quality results.
Always report the preset used, plus any sample cap, fold subset, and job-count constraints.

Meaningful modeling runs should append to:

- `outputs/modeling/run_registry.jsonl`

Do not claim a full canonical benchmark has been completed unless it is actually recorded in `docs/chat_handoff.md`.

## Python Environment Rules

Use the user-level virtual environment as the standard interpreter:

```powershell
C:\Users\golde\.venvs\STAT5630_FinalProject_DataProcessing\Scripts\python.exe -m ...
```

Environment rules:

- prefer `C:\Users\golde\.venvs\STAT5630_FinalProject_DataProcessing\` for normal repo work
- do not create or recreate `.venv` inside the repository
- keep temporary files under `C:\Users\golde\.tmp\STAT5630_FinalProject_DataProcessing\`, not under repo-local `.tmp`, `.codex_tmp`, or other scratch folders
- keep pip/cache material under `C:\Users\golde\.pip-cache\` or another user-level cache root, not under the repository
- for temp-heavy or install commands, set `TEMP`, `TMP`, and `PIP_CACHE_DIR` to those user-level roots before running the command
- treat parquet as the canonical modeling path
- keep CSV support as a compatibility path, not the primary modeling reference
- do not hardcode credentials
- read secrets from environment variables only
- AppEEARS-dependent commands must use environment-provided credentials or tokens only

## Engineering Rules

- Use Python only
- Prefer production modules and CLI entrypoints over notebook-only logic
- Keep raw data immutable
- Preserve deterministic output paths
- Save intermediate artifacts where the pipeline expects them
- Add logging
- Add type hints where practical
- Add or update tests for modified logic
- Prefer memory-aware, column-selective, parquet-first implementations when working with large artifacts
- Keep preprocessing/modeling logic separate from geospatial-heavy imports when possible
- Do not silently change canonical output schemas or directory contracts
- When changing modeling behavior, preserve the grouped-city leakage-safe contract

Preferred libraries include:

- `geopandas`
- `rasterio`
- `rioxarray`
- `xarray`
- `pandas`
- `numpy`
- `shapely`
- `scikit-learn`
- `pyarrow`

## Main Entrypoints To Respect

Geospatial and orchestration:

- `src.run_city_processing`
- `src.run_city_batch_processing`
- `src.run_appeears_acquisition`
- `src.run_raw_data_acquisition`
- `src.run_support_layers`
- `src.run_city_features`
- `src.run_city_features_batch`
- `src.run_acquisition_orchestration`
- `src.run_full_stack_orchestration`
- `src.run_full_pipeline`

Reporting and final assembly:

- `src.run_data_processing_reports`
- `src.summarize_phoenix_dataset`
- `src.run_final_dataset_assembly`

Modeling-prep and modeling:

- `src.audit_final_dataset`
- `src.make_model_folds`
- `src.run_modeling_baselines`
- `src.run_logistic_saga`
- `src.run_random_forest`

## Documentation Rules

Keep these documents aligned:

- `README.md` = landing page and canonical high-level repo definition
- `docs/workflow.md` = lifecycle-oriented workflow and stage sequencing
- `docs/data_dictionary.md` = canonical artifacts, columns, and output contracts
- `docs/modeling_plan.md` = grouped-city modeling methodology and feature-contract guidance
- `docs/chat_handoff.md` = rolling state, verification history, and next-step handoff

Documentation expectations:

- update `README.md` when repo architecture or canonical usage changes
- update `docs/workflow.md` when lifecycle stages, entrypoints, or stage outputs change
- update `docs/data_dictionary.md` when schemas, artifact names, or output contracts change
- update `docs/modeling_plan.md` when modeling methodology, feature contract, or evaluation scope changes
- add docstrings to public functions and CLI entrypoints where practical

## State And Handoff Maintenance

Treat `docs/chat_handoff.md` as the canonical rolling handoff file.

Rules:

- prefer updating existing docs over creating redundant status files
- do not create extra tracking docs if `docs/chat_handoff.md` can carry the state
- after any meaningful code, test, documentation, output, or workflow change, update `docs/chat_handoff.md` before ending the task unless explicitly told not to
- keep handoff notes concise, factual, and honest
- distinguish clearly between:
  - implemented
  - test-verified
  - manually verified
- do not invent manual verification or benchmark status

When relevant, refresh these handoff sections:

- What Is Completed
- Testing Status
- Manual Verification Status
- Immediate Next Step
- Current Output Structure
- Not Started Yet / Open Issues

For any new module, CLI, artifact, or workflow stage, record:

- what was added
- where it lives
- how to run it
- what was verified manually
- what was verified only by tests

## Task Completion Rule

A task is not complete until the relevant combination of:

- code
- tests
- docs
- `docs/chat_handoff.md`

has been updated consistently.

## Git Operations

Before any push, run:

- `git remote -v`
- `git branch --show-current`
- `git status`

Git rules:

- default branch is `main`
- keep `origin` configured as:
  - `https://github.com/goldember12-alt/urban-heat-mapping-dataset.git`
- if `origin` is missing, add it:
  - `git remote add origin https://github.com/goldember12-alt/urban-heat-mapping-dataset.git`
- push with:
  - `git push -u origin main`
- if push fails, capture and report the exact error text
- do not guess auth or permission causes; verify by rerunning and reporting the actual message
- do not force-push `main` unless explicitly requested

## AppEEARS And Remote-Sensing Rules

AppEEARS is a required pipeline stage for NDVI and ECOSTRESS acquisition.

Rules:

- export one AOI GeoJSON per city from the buffered study area
- AOI CRS must be EPSG:4326
- store AOIs under `data_processed/appeears_aoi/`
- keep acquisition resumable
- support submit-only, poll-only, download-only, and retry-incomplete workflows where the CLI already exposes them
- store raw NDVI downloads under `data_raw/ndvi/<city_slug>/`
- store raw ECOSTRESS downloads under `data_raw/ecostress/<city_slug>/`
- keep raw downloads immutable
- record per-city acquisition or blocking status in the appropriate status summaries

Support-layer acquisition rules:

- preserve reusable downloads under `data_raw/cache/`
- materialize deterministic city-specific raw files for DEM, NLCD, and hydro inputs
- do not bypass the documented raw/prepared support-layer contract without updating docs and handoff notes

## Output-Structure Rules

Respect the split output structure:

- `data_processed/` = canonical machine-readable processed artifacts by stage
- `outputs/data_processing/` = report-style preprocessing/data summaries
- `figures/data_processing/` = preprocessing/data-report figures
- `outputs/modeling/` = modeling metrics, predictions, calibration, metadata, registry
- `figures/modeling/` = modeling/evaluation maps and figures as that stage expands

Do not collapse these stage-specific roots back into a single mixed output directory without a deliberate repo-wide documentation update.
