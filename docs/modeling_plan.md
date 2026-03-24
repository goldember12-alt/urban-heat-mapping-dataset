# Modeling Plan

This document describes the city-held-out modeling methodology for the urban heat project. It distinguishes clearly between what is already implemented and what is still planned.

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

Initial baseline-modeling stage:

- `src.run_model_baselines`

Current implemented baseline models:

- logistic regression baseline
- lightweight decision-stump comparison

Current baseline outputs:

- fold-level metrics
- overall metrics
- leakage checks
- saved validation predictions
- model-artifact tables

Honest implementation status:

- The modeling-prep stage has been manually verified on the real 30-city final dataset
- The baseline-modeling code is implemented and test-verified
- A full canonical baseline run on the real final dataset is still recorded as pending in `docs/chat_handoff.md`

## Planned First Main Models

These are documented design targets, not completed production stages yet.

### Logistic Regression

Planned setup:

- sklearn `Pipeline`
- logistic regression with `solver="saga"`
- grouped CV with `GroupKFold`
- hyperparameter tuning with `GridSearchCV`
- primary selection metric: PR AUC

### Random Forest

Planned setup:

- sklearn `Pipeline`
- grouped CV with `GroupKFold`
- hyperparameter tuning with `GridSearchCV`
- primary selection metric: PR AUC

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

## Evaluation Plan

Primary metric:

- PR AUC

Planned supporting evaluation:

- recall at top 10% predicted risk
- calibration review
- held-out-city comparison tables
- error analysis by city and climate group

Planned map deliverables:

- predicted hotspot maps
- true hotspot maps
- residual or error maps

## Relationship To Future Scripts

Future modeling scripts should treat:

- `final_dataset.parquet` as the canonical row-level input
- `city_outer_folds.*` as the grouped outer-split contract

Future training scripts should:

- join folds by `city_id`
- fit preprocessing only on training cities
- tune only within training cities
- save held-out-city predictions and evaluation summaries

Recommended implementation order:

1. Run the canonical baseline-modeling pass and review the outputs
2. Add the planned logistic `saga` pipeline
3. Add the planned random-forest pipeline
4. Add held-out-city map generation and richer evaluation reporting
