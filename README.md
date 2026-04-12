# Urban Heat Mapping Dataset and Cross-City Modeling Framework

This repository supports a cross-city urban heat project that combines geospatial data engineering with city-held-out machine learning. The current codebase builds a reproducible 30 m cell-level dataset for 30 U.S. cities, prepares modeling handoff artifacts, and includes a reusable sklearn-based modeling layer whose canonical headline result remains the retained cross-city city-held-out benchmark.

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
- data-processing report outputs in `outputs/data_processing/city_summaries/<city_stem>/`
- data-processing figures in `figures/data_processing/city_summaries/<city_stem>/`
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
- Retained benchmark reporting with `outputs/modeling/reporting/cross_city_benchmark_report.md` as the headline modeling reference, plus representative held-out-city map exports under `outputs/modeling/reporting/heldout_city_maps/` and `figures/modeling/heldout_city_maps/` as support artifacts rather than replacement results
- Bounded final-train transfer packaging under `outputs/modeling/final_train/`, reusing the retained six-feature benchmark contract rather than creating a new benchmark path
- A separate new-city transfer inference path under `outputs/modeling/transfer_inference/` and `figures/modeling/transfer_inference/` that scores one city feature parquet with the retained RF transfer package and writes deterministic prediction/report artifacts without reopening benchmark evaluation
- Bounded supplemental modeling artifacts with a 3-city within-city exploratory contrast, a separate logistic-only spatial-block within-city sensitivity, and retained-run interpretation exports that keep logistic coefficients and RF held-out permutation importance primary while adding appendix-style cross-check tables

Verified status:

- Full-stack orchestration has been manually verified for Phoenix, Tucson, Las Vegas, and Albuquerque
- The canonical modeling-prep stage has been manually verified on the real `final_dataset.parquet`
- Parquet-backed logistic SAGA and random-forest smoke runs have been manually verified in the rebuilt repo-local `.venv` using the canonical parquet artifacts
- The new sklearn-based modeling layer is test-verified on synthetic grouped-city fixtures
- A full all-fold canonical modeling run on the real `71,394,894`-row dataset has not been recorded and is not the practical benchmark path on this workstation; the current benchmark-grade path is sampled all-fold evaluation, typically capped at `5,000-20,000` rows per city

Planned next, not yet implemented as full production code:

- Any further benchmark expansion only if a later doc-backed decision says the added runtime is worth it on this workstation

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
- Implemented now: retained benchmark reporting, representative held-out-city map exports, bounded final-train packaging, and a separate transfer-inference application path, while the supplemental within-city, spatial-sensitivity, and feature-importance layer remains appendix-style support for the canonical cross-city benchmark

## Benchmark Reference

Use these modeling artifacts in this order:

- `outputs/modeling/reporting/cross_city_benchmark_report.md` is the headline benchmark reference for the project narrative.
- `outputs/modeling/reporting/heldout_city_maps/heldout_city_maps.md` and `figures/modeling/heldout_city_maps/` are map-style support built from retained held-out predictions.
- `outputs/modeling/supplemental/` and `figures/modeling/supplemental/` are appendix/support layers only.
- `outputs/modeling/final_train/random_forest_frontier_s5000_all_cities_transfer_package/` is the retained post-benchmark transfer package.
- `outputs/modeling/transfer_inference/` and `figures/modeling/transfer_inference/` are application outputs from that retained package, not new evaluation-equivalent benchmark results.

## Repo Layout

- `src/`: Python modules and CLI entrypoints for acquisition, preprocessing, feature assembly, orchestration, modeling prep, baselines, and grouped sklearn modeling
- `tests/`: regression and unit tests for geometry, acquisition, orchestration, feature assembly, and modeling-prep logic
- `docs/`: project-facing documentation
- `data_raw/`: immutable downloaded source data
- `data_processed/`: processed artifacts organized by project phase
- `figures/`: figure outputs split into `figures/data_processing/city_summaries/` for preprocessing-era city reports, `figures/data_processing/reference/` for shared reference plots, and `figures/modeling/` for ML/evaluation deliverables including `reporting/`, `heldout_city_maps/`, `transfer_inference/`, and `supplemental/`
- `outputs/`: report-style deliverables split into `outputs/data_processing/city_summaries/` for per-city preprocessing summaries, `outputs/data_processing/batch_reports/` for batch status tables, `outputs/modeling/` for ML/evaluation tables and prediction artifacts including `reporting/`, `final_train/`, `transfer_inference/`, and `supplemental/`, and `outputs/storage/` for storage-management outputs

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

Recommended top-level navigation:

1. Start with `README.md` for the project overview and runnable entrypoints.
2. Use `data_processed/` for canonical machine-readable artifacts by workflow stage.
3. Use `outputs/` for report-style tables and markdown deliverables.
4. Use `figures/` for visual deliverables only.
5. Use `docs/` for workflow, schema, modeling, and handoff guidance.

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
.\.venv\Scripts\python.exe -m src.run_modeling_reporting
.\.venv\Scripts\python.exe -m src.run_modeling_spatial_reporting
.\.venv\Scripts\python.exe -m src.run_modeling_supplemental
.\.venv\Scripts\python.exe -m src.run_modeling_transfer_package
.\.venv\Scripts\python.exe -m src.run_transfer_inference --input-parquet data_processed\city_features\05_el_paso_tx_features.parquet
```

AppEEARS-dependent commands read credentials from environment variables only. See the workflow doc for the acquisition contract and expected raw-output locations.

Recommended first ML smoke run on the canonical dataset:

```powershell
.\.venv\Scripts\python.exe -m src.run_modeling_baselines --sample-rows-per-city 5000
.\.venv\Scripts\python.exe -m src.run_logistic_saga --sample-rows-per-city 5000
.\.venv\Scripts\python.exe -m src.run_random_forest --sample-rows-per-city 5000
```

These runners default to `data_processed/final/final_dataset.parquet` as the canonical row-level input and prefer `data_processed/modeling/city_outer_folds.parquet` as the held-out-city split contract. They write prediction tables, fold metrics, per-city metrics, best-parameter summaries, calibration tables, and run metadata under `outputs/modeling/`.

`src.run_modeling_reporting` builds report-ready comparison artifacts from retained modeling runs, writing markdown and derived CSV tables under `outputs/modeling/reporting/` plus benchmark figures under `figures/modeling/reporting/`.

`src.run_modeling_spatial_reporting` builds representative held-out-city predicted-hotspot, true-hotspot, and categorical error map triptychs from retained held-out predictions, writing selection tables and point-level parquet exports under `outputs/modeling/reporting/heldout_city_maps/` plus map figures under `figures/modeling/heldout_city_maps/`.

`src.run_modeling_supplemental` builds the bounded supplemental layer under `outputs/modeling/supplemental/` and `figures/modeling/supplemental/`. It keeps the city-held-out cross-city benchmark as the canonical story while adding:

- a `Reno` / `Charlotte` / `Detroit` within-city exploratory contrast with repeated stratified `80/20` splits
- an opt-in `--run-within-city-all-cities` appendix pass under `outputs/modeling/supplemental/within_city_all_cities/` and `figures/modeling/supplemental/within_city_all_cities/`, using the same six-feature contract, up to `20,000` rows per city, and `3` repeated stratified `80/20` splits with smoke-sized within-city tuning only
- an opt-in `--run-within-city-spatial` logistic-only spatial-block within-city sensitivity under `outputs/modeling/supplemental/within_city_spatial/` and `figures/modeling/supplemental/within_city_spatial/`, using deterministic centroid quadrants as a harder supplemental contrast rather than a replacement for held-out-city transfer
- retained-run logistic coefficient exports from the sampled `20,000`-row linear reference, with held-out permutation importance added only as a cross-check
- retained-run random-forest held-out permutation importance from the retained `frontier` reference, with impurity importance exported only as secondary/debug appendix output

The all-city within-city pass remains explicitly diagnostic rather than benchmark-equivalent. It is meant to help distinguish transfer-hard cities from cities that are hard even under easier within-city random splits, and to compare those patterns across climate groups without reopening the canonical held-out-city benchmark ladder.

`src.run_modeling_transfer_package` fits the retained benchmark-selected model on all 30 cities at the retained sample cap and writes a bounded transfer-oriented package under `outputs/modeling/final_train/`, including `model.joblib`, a preprocessing manifest, the six-feature contract, selected hyperparameters, and training metadata. This package supports later transfer workflows but does not replace the canonical city-held-out benchmark framing.

`src.run_transfer_inference` is the thin application CLI for the retained transfer package. It loads `model.joblib`, validates the explicit six-feature schema from `feature_contract.json`, reads one new-city feature parquet, scores it, and writes deterministic outputs under `outputs/modeling/transfer_inference/<inference_id>/` plus `figures/modeling/transfer_inference/<inference_id>/`.

## Apply To A New City

Use `src.run_transfer_inference` only after the canonical benchmark has already been selected and frozen.

Required input parquet columns:

- `cell_id`
- `impervious_pct`
- `elevation_m`
- `dist_to_water_m`
- `ndvi_median_may_aug`
- `land_cover_class`
- `climate_group`

Optional but recommended columns:

- `city_id`
- `city_name`
- `centroid_lon`
- `centroid_lat`

What the CLI writes:

- `outputs/modeling/transfer_inference/<inference_id>/predictions.parquet`
- `outputs/modeling/transfer_inference/<inference_id>/predictions.csv`
- `outputs/modeling/transfer_inference/<inference_id>/prediction_summary.csv`
- `outputs/modeling/transfer_inference/<inference_id>/prediction_deciles.csv`
- `outputs/modeling/transfer_inference/<inference_id>/feature_missingness.csv`
- `outputs/modeling/transfer_inference/<inference_id>/transfer_inference_summary.md`
- `outputs/modeling/transfer_inference/<inference_id>/transfer_inference_metadata.json`
- `figures/modeling/transfer_inference/<inference_id>/predicted_risk_map.png`

If `centroid_lon` and `centroid_lat` are present, the figure is a simple predicted-risk map plus predicted top-decile hotspot panel. If centroid columns are absent, the CLI still writes a fallback score-distribution figure so the transfer pass always emits at least one deterministic figure artifact.

Example command:

```powershell
.\.venv\Scripts\python.exe -m src.run_transfer_inference --input-parquet data_processed\city_features\05_el_paso_tx_features.parquet
```

`--output-dir` is now optional for the tuned modeling CLIs. If you omit it, the CLI auto-generates a unique, readable run directory under the correct model-family root using the preset, fold scope, sample scope, and a timestamp. You can still pass `--output-dir` explicitly to override that behavior, and `--run-label` can add a short human tag to an auto-generated name without building the full path yourself.

Long tuned runs now also write durable mid-run state inside the run output directory:

- `progress.json` = current phase, outer fold, completed inner fits, ETA-style estimates, and the latest tuned params seen
- `progress_log.csv` = append-only progress history for phase changes and fit completion
- `fold_status.json` = machine-readable per-fold completion state for restart-safe skipping
- `fold_artifacts/outer_fold_XX/` = per-fold predictions, metrics, calibration, and runtime payloads written as each fold completes
- `sample_diagnostics_by_city.csv` = per-city sampled-vs-full hotspot-rate diagnostics when `--sample-rows-per-city` is used

How to monitor a live tuned run:

- watch `progress.json` to confirm the run is still alive and see the current phase plus completed-fit counts
- inspect `progress_log.csv` if you want a durable timeline of fold starts, tuning updates, and completion boundaries
- read `fold_status.json` to see which outer folds are already safe to skip on rerun

Current resumability is deliberately coarse-grained and robust:

- rerunning the same command against the same `--output-dir` safely skips outer folds that already finished and have complete per-fold artifacts
- the code does not try to resume inside a single sklearn fit or halfway through one unfinished outer fold
- if a run fails, `progress.json`, `progress_log.csv`, and `fold_status.json` preserve the last observed phase and completed folds

Recommended tuning workflow on this workstation:

- use `--sample-rows-per-city` for iteration and broader preset exploration
- review `sample_diagnostics_by_city.csv` before trusting a sampled run, especially the sampled vs full positive counts and rates
- treat sampled all-fold runs as the standard benchmark path on this workstation; only consider fuller-row confirmation later if hardware, scope, or runtime constraints change

CSV inputs remain supported for compatibility or recovery workflows, but they are secondary paths. The regenerated `data_processed/final/final_dataset.csv` was re-audited on 2026-03-26 and now matches the canonical parquet on row count, column names, per-city row counts, hotspot counts, and key null-count checks.

## Manual Parquet Inspection Pattern

If you need a scratch script for quick inspection or a small local experiment, keep it aligned with the repo's modeling contract:

- use `pd.read_parquet(...)` or `src.modeling_data.load_modeling_rows(...)`, not `pd.read_csv(...)`, for `final_dataset.parquet`
- do not use `skiprows` or `nrows` to carve out cities from parquet; filter by `city_id` instead
- use the first-pass feature contract:
  - `impervious_pct`
  - `land_cover_class`
  - `elevation_m`
  - `dist_to_water_m`
  - `ndvi_median_may_aug`
  - `climate_group`
- use `hotspot_10pct` as the target
- do not use `lst_median_may_aug` or `n_valid_ecostress_passes` as predictors in the first-pass hotspot models because they leak target information
- do not treat a random cell-level `train_test_split(...)` as the project benchmark; the canonical evaluation is city-held-out using `city_outer_folds.*`

Example for loading one city's rows with the approved feature set:

```python
from src.modeling_config import DEFAULT_FEATURE_COLUMNS, TARGET_COLUMN
from src.modeling_data import drop_missing_target_rows, load_modeling_rows

phoenix = drop_missing_target_rows(
    load_modeling_rows(
        city_ids=[1],
        feature_columns=DEFAULT_FEATURE_COLUMNS,
    )
)

X = phoenix[DEFAULT_FEATURE_COLUMNS].copy()
y = phoenix[TARGET_COLUMN].copy()
```

Example for a leakage-safe fold from the canonical grouped split contract:

```python
from src.modeling_config import DEFAULT_FEATURE_COLUMNS, TARGET_COLUMN
from src.modeling_data import load_outer_fold_data

fold_data = load_outer_fold_data(
    outer_fold=0,
    feature_columns=DEFAULT_FEATURE_COLUMNS,
    sample_rows_per_city=5000,
)

X_train = fold_data.train_df[DEFAULT_FEATURE_COLUMNS].copy()
y_train = fold_data.train_df[TARGET_COLUMN].copy()
X_test = fold_data.test_df[DEFAULT_FEATURE_COLUMNS].copy()
y_test = fold_data.test_df[TARGET_COLUMN].copy()
```

For actual repo-consistent runs, prefer the existing CLI entrypoints instead of ad hoc scripts:

```powershell
.\.venv\Scripts\python.exe -m src.run_logistic_saga --sample-rows-per-city 5000
.\.venv\Scripts\python.exe -m src.run_random_forest --sample-rows-per-city 5000
```

Current artifact-provenance note:

- `src.feature_assembly.assemble_final_dataset()` writes parquet and CSV from the same in-memory final table, so they are intended to be equivalent serializations when generated successfully
- final-dataset assembly now writes both artifacts with atomic temp-file replacement and emits `data_processed/final/final_dataset_artifact_summary.json` so future runs leave a provenance summary next to the artifacts
- the artifact summary now records row count, column count, per-city row counts, artifact paths/sizes, and an explicit `artifacts_written_from_same_final_dataframe=true` flag

## Modeling Presets

This README is the canonical definition of the staged tuned-model workflow on this workstation.

`smoke` means:

- the bounded default tuning preset used by the CLI runners
- smaller search spaces and fewer inner grouped-CV splits than `full`
- intended for environment verification, pipeline regression checks, artifact-path validation, and modest benchmarking increments
- appropriate when confirming that parquet inputs, folds, preprocessing, and metric outputs behave correctly
- for random forest, the default first-pass nonlinear comparison against the retained logistic baseline
- not appropriate to cite as a final tuned-model estimate on its own

`frontier` means:

- a random-forest-only targeted preset between `smoke` and `full`
- a bounded follow-up search around the plausible smoke-winning RF region
- intended only after RF `smoke` shows enough promise to justify another pass
- designed to answer whether a modestly broader RF search changes the practical comparison against logistic

`full` means:

- the broadest explicit tuned search still kept in code
- larger search spaces and more inner grouped-CV splits than `smoke`
- for logistic SAGA, the practical sampled benchmark path on this workstation
- for random forest, an expensive confirmation step that should only be used after `smoke` or `frontier` already suggests RF may materially outperform logistic

Why `smoke` is the default CLI preset:

- the canonical dataset is large enough that an unrestricted default search is too expensive for routine verification
- most day-to-day work in this repo needs to validate the grouped modeling contract, not immediately launch the heaviest search
- using `smoke` by default makes accidental broad runs less likely while preserving documented escalation paths when the early evidence justifies them

How to describe them in methods/results writing:

- logistic `full` sampled runs are the retained linear baseline path
- random-forest `smoke` runs are the first nonlinear comparison checkpoint
- random-forest `frontier` runs are targeted follow-up searches, not automatic second defaults
- random-forest `full` runs are high-cost confirmation checks, not the normal iteration path
- always report the preset used, plus any sample cap, outer-fold subset, and job-count constraints

The current preset sizes in code are:

- logistic SAGA: `smoke=4` parameter candidates with `3` inner grouped-CV splits; `full=20` candidates with `4` inner grouped-CV splits
- random forest: `smoke=4` parameter candidates with `3` inner grouped-CV splits; `frontier=8` candidates with `3` inner grouped-CV splits; `full=81` candidates with `4` inner grouped-CV splits

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

## Practical Benchmark Workflow

Use logistic SAGA and random forest differently on this workstation.

Retained logistic baseline ladder:

- use `--tuning-preset full`
- use all outer folds
- keep `--grid-search-n-jobs 1`
- use sample caps at `5000`, `10000`, and `20000` rows per city
- use `--run-label samplecurve-5k`, `samplecurve-10k`, and `samplecurve-20k`

Recommended logistic baseline commands:

```powershell
.\.venv\Scripts\python.exe -m src.run_logistic_saga --dataset-path data_processed\final\final_dataset.parquet --folds-path data_processed\modeling\city_outer_folds.parquet --sample-rows-per-city 5000 --tuning-preset full --grid-search-n-jobs 1 --run-label samplecurve-5k
.\.venv\Scripts\python.exe -m src.run_logistic_saga --dataset-path data_processed\final\final_dataset.parquet --folds-path data_processed\modeling\city_outer_folds.parquet --sample-rows-per-city 10000 --tuning-preset full --grid-search-n-jobs 1 --run-label samplecurve-10k
.\.venv\Scripts\python.exe -m src.run_logistic_saga --dataset-path data_processed\final\final_dataset.parquet --folds-path data_processed\modeling\city_outer_folds.parquet --sample-rows-per-city 20000 --tuning-preset full --grid-search-n-jobs 1 --run-label samplecurve-20k
```

Staged random-forest workflow:

Stage A:

- run RF `smoke` on all folds at `5000` rows per city as the cheap nonlinear comparison against logistic
- recommended first command:

```powershell
.\.venv\Scripts\python.exe -m src.run_random_forest --dataset-path data_processed\final\final_dataset.parquet --folds-path data_processed\modeling\city_outer_folds.parquet --sample-rows-per-city 5000 --tuning-preset smoke --grid-search-n-jobs 1 --model-n-jobs 1 --run-label nonlinear-check
```

Stage B:

- only if RF `smoke` looks materially better than logistic, run RF `frontier`
- keep the same sampled `5000` rows-per-city slice first so the wider RF search is still interpretable

```powershell
.\.venv\Scripts\python.exe -m src.run_random_forest --dataset-path data_processed\final\final_dataset.parquet --folds-path data_processed\modeling\city_outer_folds.parquet --sample-rows-per-city 5000 --tuning-preset frontier --grid-search-n-jobs 1 --model-n-jobs 1 --run-label frontier-check
```

Stage C:

- only if RF `frontier` still looks meaningfully better and the winning region is stable, run RF `full`
- treat this as expensive confirmation, not the routine next click

```powershell
.\.venv\Scripts\python.exe -m src.run_random_forest --dataset-path data_processed\final\final_dataset.parquet --folds-path data_processed\modeling\city_outer_folds.parquet --sample-rows-per-city 5000 --tuning-preset full --grid-search-n-jobs 1 --model-n-jobs 1 --run-label confirm-check
```

Stopping guidance:

- stop expanding RF search if RF `smoke` does not materially beat the retained logistic baseline
- stop at RF `frontier` if the broader search does not produce a meaningful gain or the winning region looks stable already
- stop increasing RF sample size if runtime grows much faster than PR AUC or top-10% recall improves
- when RF does justify more work, prefer changing one dimension at a time: preset first, then sample size

Run-history conventions for `tuning_history_annotations.csv`:

- `validation` = setup checks, one-fold checks, or artifact verification runs
- `exploratory` = partial-scope runs, legacy contracts, and abandoned search paths
- `benchmark` = retained comparison checkpoints used to justify go / no-go decisions, including logistic sampled-full rungs and any retained RF stage outputs

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
