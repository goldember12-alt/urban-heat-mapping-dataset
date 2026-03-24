# Urban Heat Mapping Dataset and Cross-City Modeling Framework

This repository supports a cross-city urban heat project that combines geospatial data engineering with city-held-out machine learning. The current codebase builds a reproducible 30 m cell-level dataset for 30 U.S. cities, prepares modeling handoff artifacts, and includes an initial baseline-modeling stage.

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
- reserved modeling/evaluation report roots in `outputs/modeling/` and `figures/modeling/`

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
- Initial baseline modeling with city-held-out evaluation artifacts

Verified status:

- Full-stack orchestration has been manually verified for Phoenix, Tucson, Las Vegas, and Albuquerque
- The canonical modeling-prep stage has been manually verified on the real `final_dataset.parquet`
- Baseline-modeling code is implemented and test-verified, but a full end-to-end canonical baseline run has not yet been recorded in the handoff log

Planned next, not yet implemented as full production code:

- Main city-held-out model training with logistic regression using `solver="saga"` in a `Pipeline` plus grouped CV
- Main city-held-out random forest training in a `Pipeline` plus grouped CV
- Nested tuning that stays fully inside the training cities
- Evaluation extensions such as recall at top 10%, calibration review, and held-out-city prediction/error maps
- Application workflow for scoring new cities after the first modeling stack is stable

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

- Current implemented stage: baseline modeling
- Documented next stage: grouped city CV, training-city-only tuning, held-out-city evaluation, and map deliverables

## Repo Layout

- `src/`: Python modules and CLI entrypoints for acquisition, preprocessing, feature assembly, orchestration, modeling prep, and baseline modeling
- `tests/`: regression and unit tests for geometry, acquisition, orchestration, feature assembly, and modeling-prep logic
- `docs/`: project-facing documentation
- `data_raw/`: immutable downloaded source data
- `data_processed/`: processed artifacts organized by project phase
- `figures/`: figure outputs split into `figures/data_processing/` for preprocessing-era reports, `figures/modeling/` for future ML/evaluation deliverables, plus a small number of legacy/global inspection plots
- `outputs/`: report-style deliverables split into `outputs/data_processing/` for preprocessing-era city summaries, `outputs/modeling/` for future ML/evaluation reports, plus storage-management outputs

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

## Main Runnable Entrypoints

These are the most important current entrypoints. The workflow doc lists how they fit together.

```powershell
.venv\Scripts\python.exe -m src.run_city_batch_processing --resolution 30
.venv\Scripts\python.exe -m src.run_full_stack_orchestration --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31
.venv\Scripts\python.exe -m src.run_final_dataset_assembly
.venv\Scripts\python.exe -m src.run_data_processing_reports
.venv\Scripts\python.exe -m src.audit_final_dataset
.venv\Scripts\python.exe -m src.make_model_folds --n-splits 5
.venv\Scripts\python.exe -m src.run_model_baselines
```

AppEEARS-dependent commands read credentials from environment variables only. See the workflow doc for the acquisition contract and expected raw-output locations.

## How To Navigate The Docs

Start here, then use:

- [`docs/workflow.md`](docs/workflow.md) for the end-to-end project lifecycle
- [`docs/data_dictionary.md`](docs/data_dictionary.md) for data columns and artifact definitions
- [`docs/modeling_plan.md`](docs/modeling_plan.md) for the city-held-out modeling methodology and what is implemented versus planned
- [`docs/chat_handoff.md`](docs/chat_handoff.md) for the latest project-state checkpoint and next recommended step
