# Urban Heat Mapping Dataset and Cross-City Modeling Framework

This repository supports a cross-city urban heat project that combines geospatial data engineering with city-held-out machine learning. The current codebase builds a reproducible 30 m cell-level dataset for 30 U.S. cities, prepares modeling handoff artifacts, and now includes the first reusable sklearn-based modeling layer.

The project is broader than a preprocessing pipeline. It is organized around the full lifecycle:

1. Study design and city selection
2. Data acquisition and preprocessing
3. Feature assembly and final dataset generation
4. Modeling-ready handoff
5. Baseline modeling
6. Main-model training, evaluation, and map deliverables

## What This Repo Produces

Canonical outputs:

- `data_processed/final/final_dataset.parquet`
- `data_processed/final/final_dataset.csv`
- one per-city feature GeoPackage and parquet in `data_processed/city_features/`
- modeling handoff artifacts in `data_processed/modeling/`
- data-processing report outputs in `outputs/data_processing/<city_stem>/`
- data-processing figures in `figures/data_processing/<city_stem>/`
- first-pass ML outputs in `outputs/modeling/`
- reserved modeling figures in `figures/modeling/`

Final dataset columns:

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

## Current Status

Implemented now:

- City study-area generation from Census urban areas, including buffered study areas and 30 m master grids
- AppEEARS AOI export plus resumable NDVI and ECOSTRESS acquisition
- Raw support-layer acquisition for DEM, NLCD land cover, NLCD impervious, and hydrography
- Deterministic support-layer prep outputs
- Per-city feature assembly and merged final dataset generation
- Per-city data-processing summaries and figures using the Phoenix reporting pattern generalized to all configured cities
- Final-dataset audit and deterministic city-level outer-fold creation
- First-pass held-out-city ML layer with explicit feature contract, simple baselines, logistic SAGA, and random forest runners

Verified status:

- Full-stack orchestration has been manually verified for Phoenix, Tucson, Las Vegas, and Albuquerque
- The canonical modeling-prep stage has been manually verified on the real `final_dataset.parquet`
- The new sklearn-based modeling layer is test-verified on synthetic grouped-city fixtures
- A full end-to-end canonical modeling run on the real `71,394,894`-row dataset has not yet been recorded in the handoff log

Planned next, not yet implemented as full production code:

- Held-out-city spatial sanity figures and residual/error maps under `figures/modeling/`
- Final train-on-all-cities packaging for apply-to-new-cities workflows
- Scaling strategy for full canonical runs if workstation memory/runtime becomes the bottleneck

## Project Lifecycle

### 1. Study Design

- Cross-city spatial ML framework for urban heat risk
- Analytic unit: one row per 30 m grid cell per city
- Label: `hotspot_10pct`, defined within city from ECOSTRESS LST
- Evaluation principle: hold out entire cities, not random cells

### 2. Acquisition And Preprocessing

- Build buffered study areas and 30 m grids
- Export AppEEARS-ready AOIs
- Acquire NDVI and ECOSTRESS through AppEEARS
- Acquire and prepare DEM, NLCD, and hydro support layers

### 3. Feature Assembly

- Align source rasters to the master city grid
- Assemble imperviousness, land cover, elevation, distance to water, NDVI, and ECOSTRESS-derived LST
- Write one per-city feature table per city
- Merge per-city tables into the final dataset

### 4. Modeling-Ready Handoff

- Audit the canonical merged parquet
- Generate deterministic city-level outer folds
- Save machine-readable summaries under `data_processed/modeling/`

### 5. Modeling And Evaluation

- Implemented now: first-pass baselines plus grouped logistic SAGA and random forest runners
- Next stage: richer evaluation figures, map deliverables, and final-train packaging

## Repo Layout

- `src/`: Python modules and CLI entrypoints for acquisition, preprocessing, feature assembly, orchestration, modeling prep, baselines, and grouped sklearn modeling
- `tests/`: regression and unit tests for geometry, acquisition, orchestration, feature assembly, and modeling-prep logic
- `docs/`: project-facing documentation
- `data_raw/`: immutable downloaded source data
- `data_processed/`: processed artifacts organized by project phase
- `figures/`: figure outputs split into `figures/data_processing/` for preprocessing-era reports and `figures/modeling/` for ML/evaluation deliverables, plus a small number of legacy/global inspection plots
- `outputs/`: report-style deliverables split into `outputs/data_processing/` for preprocessing-era city summaries, `outputs/modeling/` for ML/evaluation tables and prediction artifacts, plus storage-management outputs

Important `data_processed/` subdirectories:

- `study_areas/`
- `city_grids/`
- `appeears_aoi/`
- `appeears_status/`
- `support_layers/`
- `intermediate/`
- `city_features/`
- `final/`
- `modeling/`
- `orchestration/`

## Python Environment

Run project commands from the repo root with the repo-local virtualenv:

```powershell
.venv\Scripts\python.exe -m ...
```

Current verified environment notes:

- `.venv` is expected to be built from the accessible base interpreter at `C:\Users\golde\anaconda3\python.exe`
- `sys.executable` and `sys.prefix` should point into the repo `.venv`, while `sys.base_prefix` should point to `C:\Users\golde\anaconda3`
- virtual environments are disposable; if `.venv\pyvenv.cfg` points to the wrong or inaccessible base interpreter, delete and recreate `.venv` from the correct base instead of copying or repairing an old broken environment
- `requirements.txt` now includes `pytest` so rebuilt environments can run the focused test suite directly

## Main Runnable Entrypoints

These are the most important current entrypoints. The workflow doc lists how they fit together.

```powershell
.venv\Scripts\python.exe -m src.run_city_batch_processing --resolution 30
.venv\Scripts\python.exe -m src.run_full_stack_orchestration --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31
.venv\Scripts\python.exe -m src.run_final_dataset_assembly
.venv\Scripts\python.exe -m src.run_data_processing_reports
.venv\Scripts\python.exe -m src.audit_final_dataset
.venv\Scripts\python.exe -m src.make_model_folds --n-splits 5
.venv\Scripts\python.exe -m src.run_modeling_baselines
.venv\Scripts\python.exe -m src.run_logistic_saga
.venv\Scripts\python.exe -m src.run_random_forest
```

AppEEARS-dependent commands read credentials from environment variables only. See the workflow doc for the acquisition contract and expected raw-output locations.

Recommended first ML smoke run on the canonical dataset:

```powershell
.venv\Scripts\python.exe -m src.run_modeling_baselines --sample-rows-per-city 5000
.venv\Scripts\python.exe -m src.run_logistic_saga --sample-rows-per-city 5000
.venv\Scripts\python.exe -m src.run_random_forest --sample-rows-per-city 5000
```

These runners treat `data_processed/final/final_dataset.parquet` as the canonical row-level input and `data_processed/modeling/city_outer_folds.parquet` as the held-out-city split contract. They write prediction tables, fold metrics, per-city metrics, best-parameter summaries, calibration tables, and run metadata under `outputs/modeling/`.

Current sandbox-verified modeling commands:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_modeling_contract.py tests/test_modeling_runner.py -q
.venv\Scripts\python.exe -m src.run_logistic_saga --dataset-path data_processed\final\final_dataset.csv --folds-path data_processed\modeling\city_outer_folds.csv --sample-rows-per-city 5000 --outer-folds 0 --tuning-preset smoke --grid-search-n-jobs 1 --output-dir outputs\modeling\logistic_saga\venv_verify
.venv\Scripts\python.exe -m src.run_random_forest --dataset-path data_processed\final\final_dataset.csv --folds-path data_processed\modeling\city_outer_folds.csv --sample-rows-per-city 5000 --outer-folds 0 --tuning-preset smoke --grid-search-n-jobs 1 --model-n-jobs 1 --output-dir outputs\modeling\random_forest\venv_verify
```

In this sandbox, the CSV dataset and fold files are still the verified smoke path because the canonical parquet artifacts remain unreadable in the current environment, and serial grid-search flags are still required for stable execution.

## How To Navigate The Docs

Start here, then use:

- [`docs/workflow.md`](docs/workflow.md) for the end-to-end project lifecycle
- [`docs/data_dictionary.md`](docs/data_dictionary.md) for data columns and artifact definitions
- [`docs/modeling_plan.md`](docs/modeling_plan.md) for the city-held-out modeling methodology and what is implemented versus planned
- [`docs/chat_handoff.md`](docs/chat_handoff.md) for the latest project-state checkpoint and next recommended step
