# Modeling Plan

This document describes the city-held-out modeling methodology for the urban heat project. It distinguishes clearly between what is already implemented and what still remains for later expansion.

## Modeling Objective

Use the canonical cell-level dataset to predict `hotspot_10pct` for cities that were not seen during training.

Canonical inputs:

- `data_processed/final/final_dataset.parquet`
- `data_processed/modeling/city_outer_folds.parquet`
- `data_processed/modeling/city_outer_folds.csv`

Analytic unit:

- One row per 30 m grid cell per city

Grouping variable:

- `city_id`

## Leakage-Safe Split Strategy

The project uses grouped cross-validation by city.

Outer evaluation rule:

- Held-out cities must remain fully unseen during training

Tuning rule:

- Hyperparameter tuning must happen only inside the training cities for each outer split

Implication:

- Any preprocessing, imputation, scaling, encoding, feature selection, or model tuning must be fit using training-city rows only

## Implemented Now

Modeling-prep stage:

- `src.audit_final_dataset`
- `src.make_model_folds`

These stages:

- audit the canonical final parquet
- summarize missingness and class balance
- generate deterministic city-level outer folds

First-pass modeling stage:

- `src.run_modeling_baselines`
- `src.run_logistic_saga`
- `src.run_random_forest`

Current implemented baseline models:

- `global_mean_baseline`
- `land_cover_only_baseline`
- `impervious_only_baseline`
- `climate_only_baseline`

Current implemented main models:

- logistic regression with `solver="saga"` in an sklearn `Pipeline`
- random forest in an sklearn `Pipeline`

Current implemented evaluation outputs:

- fold-level PR AUC
- per-city PR AUC
- recall at top 10% predicted risk
- calibration-curve tables
- held-out prediction tables
- per-fold best-parameter summaries for tuned models

Honest implementation status:

- The modeling-prep stage has been manually verified on the real 30-city final dataset
- The new sklearn-based modeling layer is test-verified on synthetic grouped-city fixtures
- A full canonical modeling run on the real final dataset is still recorded as pending in `docs/chat_handoff.md`
- `README.md` is now the canonical definition of `smoke` versus `full`, including how those presets should and should not be described in methodology/results language
- The tuned sklearn runners now persist mid-run progress plus fold-level state so interrupted runs can be resumed at the outer-fold boundary

## Candidate Feature Contract

Safe initial feature candidates for the first hotspot models:

- `impervious_pct`
- `land_cover_class`
- `elevation_m`
- `dist_to_water_m`
- `ndvi_median_may_aug`
- `climate_group`

Columns to exclude from the first predictive feature set:

- `hotspot_10pct`
- `lst_median_may_aug`
- `n_valid_ecostress_passes`
- `cell_id`
- `city_id`
- `city_name`
- `centroid_lon`
- `centroid_lat`

Reason:

- These excluded columns are either the target, direct target ingredients, identifiers, or location fields that are not part of the intended portable baseline feature contract
- `lst_median_may_aug` is excluded explicitly because `hotspot_10pct` is derived from ECOSTRESS LST

## Evaluation Plan

Primary metric:

- PR AUC

Implemented supporting evaluation:

- recall at top 10% predicted risk
- calibration-curve tables
- held-out-city comparison tables

Planned next evaluation additions:

- error analysis by city and climate group
- predicted hotspot maps
- true hotspot maps
- residual or error maps

## Relationship To Future Scripts

Future modeling scripts should treat:

- `final_dataset.parquet` as the canonical row-level input
- `city_outer_folds.*` as the grouped outer-split contract

Scratch-script guidance:

- Read `final_dataset.parquet` with `pd.read_parquet(...)` or the repo helper `src.modeling_data.load_modeling_rows(...)`, not `pd.read_csv(...)`
- Do not use row counts, `skiprows`, or `nrows` to isolate Phoenix, Tucson, or any other city from parquet; filter by `city_id`
- Select predictors from the explicit first-pass feature contract only:
  - `impervious_pct`
  - `land_cover_class`
  - `elevation_m`
  - `dist_to_water_m`
  - `ndvi_median_may_aug`
  - `climate_group`
- Use `hotspot_10pct` as the target
- Treat within-city random train/test splits as exploratory debugging only, not as the canonical project evaluation

Current training scripts already:

- join folds by `city_id`
- fit preprocessing only on training cities
- tune only within training cities
- save held-out-city predictions and evaluation summaries

## Practical Run Monitoring And Resume

Tuned runner output directories now include:

- `progress.json`
- `progress_log.csv`
- `fold_status.json`
- `fold_artifacts/outer_fold_XX/`
- `sample_diagnostics_by_city.csv` when `--sample-rows-per-city` is used

Operational guidance:

- monitor `progress.json` during a live run for the current phase, outer fold, completed inner fits, and rough remaining time
- use `fold_status.json` to see which outer folds already completed successfully
- rerunning the same model command against the same `--output-dir` skips completed outer folds when their per-fold artifacts are present
- resumability is intentionally limited to the outer-fold boundary; the code does not attempt to resume inside one unfinished sklearn fit

Recommended tuning workflow:

- use sampled runs first for search-space iteration and broader fold coverage
- inspect `sample_diagnostics_by_city.csv` to make sure sampled positive counts and rates still reflect the full city-level hotspot signal
- use full-row runs later for final confirmation once the sampled run looks methodologically stable

Recommended implementation order:

1. Run the new first-pass modeling CLIs on the canonical parquet and review the outputs under `outputs/modeling/`
2. Add held-out-city figure generation under `figures/modeling/`
3. Add richer calibration/reporting views and residual-map exports
4. Add final-train-on-all-cities packaging for transfer to new cities

Run logging note:

- meaningful modeling CLI runs now append structured records to `outputs/modeling/run_registry.jsonl`
- that registry now also supports `outputs/modeling/tuning_history.csv` as a cross-run chronology for later figure generation and model-selection rationale, with `outputs/modeling/tuning_history_annotations.csv` reserved for manual status and decision notes
