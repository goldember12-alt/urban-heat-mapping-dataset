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
- Parquet-backed logistic SAGA and random-forest smoke runs have been manually verified in the rebuilt repo-local `.venv` using the canonical parquet artifacts
- The new sklearn-based modeling layer is test-verified on synthetic grouped-city fixtures
- A full all-fold canonical modeling run on the real `71,394,894`-row dataset has not yet been recorded in the handoff log

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

Run project commands from the repo root with the repo-local virtualenv. This repo-local `.venv` is the standard interpreter for normal use:

```powershell
.\.venv\Scripts\python.exe -m ...
```

Current verified environment notes:

- The canonical modeling path is the rebuilt repo-local `.venv` plus parquet-backed artifacts
- `.venv` is expected to be built from the accessible base interpreter at `C:\Users\golde\anaconda3\python.exe`
- `sys.executable` and `sys.prefix` should point into the repo `.venv`, while `sys.base_prefix` should point to `C:\Users\golde\anaconda3`
- virtual environments are disposable; if `.venv\pyvenv.cfg` points to the wrong or inaccessible base interpreter, delete and recreate `.venv` from the correct base instead of copying or repairing an old broken environment
- `requirements.txt` now includes `pytest` so rebuilt environments can run the focused test suite directly

## Main Runnable Entrypoints

These are the most important current entrypoints. The workflow doc lists how they fit together.

```powershell
.\.venv\Scripts\python.exe -m src.run_city_batch_processing --resolution 30
.\.venv\Scripts\python.exe -m src.run_full_stack_orchestration --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31
.\.venv\Scripts\python.exe -m src.run_final_dataset_assembly
.\.venv\Scripts\python.exe -m src.run_data_processing_reports
.\.venv\Scripts\python.exe -m src.audit_final_dataset
.\.venv\Scripts\python.exe -m src.make_model_folds --n-splits 5
.\.venv\Scripts\python.exe -m src.run_modeling_baselines
.\.venv\Scripts\python.exe -m src.run_logistic_saga
.\.venv\Scripts\python.exe -m src.run_random_forest
```

AppEEARS-dependent commands read credentials from environment variables only. See the workflow doc for the acquisition contract and expected raw-output locations.

Recommended first ML smoke run on the canonical dataset:

```powershell
.\.venv\Scripts\python.exe -m src.run_modeling_baselines --sample-rows-per-city 5000
.\.venv\Scripts\python.exe -m src.run_logistic_saga --sample-rows-per-city 5000
.\.venv\Scripts\python.exe -m src.run_random_forest --sample-rows-per-city 5000
```

These runners default to `data_processed/final/final_dataset.parquet` as the canonical row-level input and prefer `data_processed/modeling/city_outer_folds.parquet` as the held-out-city split contract. They write prediction tables, fold metrics, per-city metrics, best-parameter summaries, calibration tables, and run metadata under `outputs/modeling/`.

CSV inputs remain supported for compatibility or recovery workflows, but they are secondary paths. The regenerated `data_processed/final/final_dataset.csv` was re-audited on 2026-03-26 and now matches the canonical parquet on row count, column names, per-city row counts, hotspot counts, and key null-count checks.

Current artifact-provenance note:

- `src.feature_assembly.assemble_final_dataset()` writes parquet and CSV from the same in-memory final table, so they are intended to be equivalent serializations when generated successfully
- final-dataset assembly now writes both artifacts with atomic temp-file replacement and emits `data_processed/final/final_dataset_artifact_summary.json` so future runs leave a provenance summary next to the artifacts
- the artifact summary now records row count, column count, per-city row counts, artifact paths/sizes, and an explicit `artifacts_written_from_same_final_dataframe=true` flag

## Modeling Presets

This README is the canonical definition of `smoke` versus `full`.

`smoke` means:

- the bounded default tuning preset used by the CLI runners
- smaller search spaces and fewer inner grouped-CV splits than `full`
- intended for environment verification, pipeline regression checks, artifact-path validation, and modest benchmarking increments
- appropriate when confirming that parquet inputs, folds, preprocessing, and metric outputs behave correctly
- not appropriate to cite as a benchmark-quality final result or as the project's main tuned-model estimate

`full` means:

- the broader tuning preset for more serious benchmark runs after inputs, provenance, and logging are stable
- larger search spaces and more inner grouped-CV splits than `smoke`
- intended for better-faith model comparison and methodology/results tables, subject to compute limits and explicit run logging

Why `smoke` is the default CLI preset:

- the canonical dataset is large enough that an unrestricted default search is too expensive for routine verification
- most day-to-day work in this repo needs to validate the grouped modeling contract, not immediately launch the heaviest search
- using `smoke` by default makes accidental broad runs less likely while preserving a documented path to `full`

How to describe them in methods/results writing:

- `smoke` results are verification runs or bounded benchmark checkpoints
- `full` results are the ones to prefer for substantive model-performance discussion once they are actually executed and logged
- always report the preset used, plus any sample cap, outer-fold subset, and job-count constraints

The current preset sizes in code are:

- logistic SAGA: `smoke=4` parameter candidates with `3` inner grouped-CV splits; `full=20` candidates with `4` inner grouped-CV splits
- random forest: `smoke=4` parameter candidates with `3` inner grouped-CV splits; `full=81` candidates with `4` inner grouped-CV splits

## Run Registry

Meaningful modeling CLI runs now append a structured record to `outputs/modeling/run_registry.jsonl`.

The modeling registry now also refreshes a lightweight cross-run tuning-history layer under `outputs/modeling/`:

- `tuning_history.csv` = machine-readable chronology built from the registry plus per-run metadata
- `tuning_history_annotations.csv` = durable manual annotation sidecar for status labels, comparability notes, and decision rationale

This layer is intended for later figures and writeups such as tuning chronology, smoke-versus-full comparisons, contract-drift notes, and stopping-rationale tables without re-parsing every individual run directory by hand.

Each registry record captures:

- model type and preset
- exact CLI command and interpreter path
- dataset path and format
- fold selection and sample cap
- job settings
- output directory
- summary metrics when available
- wall-clock time when available
- success or failure status
- notes such as CSV fallback caveats

You can rebuild the tuning-history artifacts from the registry at any time with:

```powershell
.\.venv\Scripts\python.exe -m src.run_modeling_tuning_history
```

Current sandbox-verified modeling commands:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_modeling_contract.py tests/test_modeling_runner.py -q
.\.venv\Scripts\python.exe -m src.run_logistic_saga --dataset-path data_processed\final\final_dataset.parquet --folds-path data_processed\modeling\city_outer_folds.parquet --sample-rows-per-city 5000 --outer-folds 0 --tuning-preset smoke --grid-search-n-jobs 1 --output-dir outputs\modeling\logistic_saga\parquet_verify
.\.venv\Scripts\python.exe -m src.run_random_forest --dataset-path data_processed\final\final_dataset.parquet --folds-path data_processed\modeling\city_outer_folds.parquet --sample-rows-per-city 5000 --outer-folds 0 --tuning-preset smoke --grid-search-n-jobs 1 --model-n-jobs 1 --output-dir outputs\modeling\random_forest\parquet_verify
```

In this sandbox, the canonical parquet dataset and fold artifacts are verified through the rebuilt `.venv`, and the serial grid-search flags above remain the stable smoke settings for constrained verification here. Those serial flags are sandbox-specific guidance, not a requirement to force serial mode or CSV in normal use.

## How To Navigate The Docs

Start here, then use:

- [`docs/workflow.md`](docs/workflow.md) for the end-to-end project lifecycle
- [`docs/data_dictionary.md`](docs/data_dictionary.md) for data columns and artifact definitions
- [`docs/modeling_plan.md`](docs/modeling_plan.md) for the city-held-out modeling methodology and what is implemented versus planned
- [`docs/chat_handoff.md`](docs/chat_handoff.md) for the latest project-state checkpoint and next recommended step
