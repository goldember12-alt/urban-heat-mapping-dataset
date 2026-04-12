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
- `src.run_modeling_reporting`
- `src.run_modeling_supplemental`

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
- city-level RF-vs-logistic error comparison tables by city and climate group
- benchmark comparison markdown and benchmark figures under the modeling reporting layer
- supplemental within-city contrast markdown/tables/figures under `outputs/modeling/supplemental/within_city/` and `figures/modeling/supplemental/within_city/`
- supplemental retained-run interpretation tables/figures under `outputs/modeling/supplemental/feature_importance/` and `figures/modeling/supplemental/feature_importance/`

Honest implementation status:

- The modeling-prep stage has been manually verified on the real 30-city final dataset
- The new sklearn-based modeling layer is test-verified on synthetic grouped-city fixtures
- A full canonical modeling run on the real final dataset is not currently the practical benchmark path on this workstation; sampled all-fold runs, typically up to `20,000` rows per city, are the meaningful comparison path to record in `docs/chat_handoff.md`
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

- treat logistic sampled `full` runs as the retained linear baseline path
- use random-forest sampled `smoke` first for the cheap nonlinear comparison against logistic
- inspect `sample_diagnostics_by_city.csv` to make sure sampled positive counts and rates still reflect the full city-level hotspot signal
- treat sampled all-fold runs as the standard benchmark path on this workstation; reserve any fuller-row confirmation for narrower scopes or future hardware

Practical staged random-forest workflow on this workstation:

- Stage A: RF `smoke` at `5000` rows per city on all folds for the first nonlinear comparison
- Stage B: RF `frontier` only if Stage A looks materially better than logistic
- Stage C: RF `full` only if Stage B still looks promising enough to justify expensive confirmation
- keep `--grid-search-n-jobs 1` and `--model-n-jobs 1` for RF on this hardware
- do not broaden both search space and sample size at the same time unless there is already a retained RF result that justifies it

Retained logistic sampled baseline ladder:

- logistic SAGA still uses the sampled `full` ladder at `5000`, `10000`, and `20000` rows per city
- use `--run-label samplecurve-5k`, `samplecurve-10k`, and `samplecurve-20k` for that retained baseline ladder

Run-history conventions for the ladder:

- `validation` = smoke or one-fold workflow checks
- `exploratory` = partial-scope, legacy-contract, or abandoned runs that are useful context but not retained checkpoints
- `benchmark` = retained decision checkpoints used for cross-model comparison and later figures

Stopping guidance:

- stop expanding RF search if RF `smoke` does not materially beat logistic on the same sampled evaluation slice
- stop at RF `frontier` if the best region looks stable and the broader search does not add meaningful gain
- stop increasing RF sample size if runtime grows faster than practical performance gains
- use `tuning_history.csv` plus `tuning_history_annotations.csv` to record those stop / escalate decisions explicitly for later writeup

Reporting-oriented status after the current retained runs:

- the main cross-city story is now established from retained outputs: both tuned models beat simple baselines, RF improves pooled metrics somewhat, performance remains moderate and uneven across cities, and cross-city transfer is still difficult
- keep the city-held-out evaluation as the canonical project methodology and comparison frame for all later supplements
- keep the retained logistic sampled `full` ladder at `5000`, `10000`, and `20000` rows per city as the linear reference path already used in reporting
- keep RF `smoke` and RF `frontier` at `5000` rows per city as the retained nonlinear checkpoints already used in reporting
- do not schedule more routine logistic or RF benchmark expansion now; RF `full` remains a reserved confirmation path only if a later decision explicitly reopens it

## Bounded Supplemental Analysis Layer

Guardrails:

- cross-city city-held-out evaluation remains the canonical methodology, headline benchmark, and main project narrative
- within-city results must be labeled explicitly as exploratory, easier, and supplemental because training and testing occur inside the same city
- interpretation outputs must be framed as predictive associations or model reliance under the current feature contract, not as causal effects
- reuse retained reporting artifacts and retained benchmark configurations wherever possible

Recommended output locations:

- `outputs/modeling/supplemental/within_city/within_city_contrast_summary.md`
- `outputs/modeling/supplemental/within_city/tables/*.csv`
- `figures/modeling/supplemental/within_city/*.png`
- `outputs/modeling/supplemental/within_city_spatial/within_city_spatial_sensitivity_summary.md`
- `outputs/modeling/supplemental/within_city_spatial/tables/*.csv`
- `figures/modeling/supplemental/within_city_spatial/*.png`
- `outputs/modeling/supplemental/feature_importance/feature_importance_summary.md`
- `outputs/modeling/supplemental/feature_importance/tables/*.csv`
- `figures/modeling/supplemental/feature_importance/*.png`

### Within-City Exploratory Methodology

Recommended city count:

- `3` cities total, which is large enough to show contrast across climate settings but still small enough for a bounded workstation-friendly supplement

Recommended default city set:

- `Reno` for `hot_arid`
- `Charlotte` for `hot_humid`
- `Detroit` for `mild_cool`

Selection rule:

- choose one city per climate group using the existing retained comparison table `outputs/modeling/reporting/tables/cross_city_benchmark_report_city_error_comparison.csv`
- default to the city closest to the current climate-group median logistic PR AUC so the supplemental set is representative rather than cherry-picked toward either easy or extreme-error cities
- if retained reporting tables are refreshed later, reapply the same nearest-median-per-climate rule instead of hardcoding a new ad hoc trio
- the current retained table resolves to `Reno`, `Charlotte`, and `Detroit`, which is the default trio used by `src.run_modeling_supplemental`

Data scope:

- use the same first-pass feature contract as the canonical cross-city models
- sample up to `20,000` rows per selected city with stratification on `hotspot_10pct`
- if a selected city has fewer than `20,000` valid rows after filtering, use all available rows
- keep the sample cap explicit in the final summary so the supplement is not misread as a full-city benchmark

Split strategy:

- use `3` repeated within-city `80/20` stratified train/test splits with fixed random seeds
- tune only inside each training split
- keep this intentionally simple and clearly label it as optimistic relative to the held-out-city benchmark because it does not test transfer to unseen cities
- keep this as the default within-city supplement even after adding any harder spatial-block sensitivity; do not silently replace it

Models to compare:

- logistic SAGA with the same preprocessing pattern and six-feature contract used in the main pipeline
- random forest with the same six-feature contract and a bounded `smoke`-sized search only
- `city_prevalence_baseline` as a within-city-only contextual baseline that predicts the training-split hotspot prevalence for every test row
- do not run RF `frontier` or RF `full` for the within-city supplement unless a later implementation note finds a concrete reason they are needed
- do not treat that contextual baseline as part of the canonical cross-city baseline suite

Metrics to report:

- primary metric: PR AUC
- supporting metric: recall at top 10% predicted risk
- optional if already easy to export from the shared helpers: calibration curve tables
- report mean and standard deviation across the `3` repeats for each city-model pair
- join the within-city summary back to retained cross-city city-level metrics so the main presentation is the performance gap between within-city and held-out-city settings
- the current implementation uses retained logistic `20,000` sampled `full` city metrics plus retained RF `smoke` city metrics for that cross-city contrast join

Recommended presentation:

- one markdown summary that starts by restating that cross-city transfer remains canonical and within-city is a contrast case only
- one city-model contrast table with columns for `city_name`, `climate_group`, `model_family`, `within_city_pr_auc_mean`, `cross_city_pr_auc`, `pr_auc_gap`, `within_city_recall_at_top_10pct_mean`, `cross_city_recall_at_top_10pct`, and `recall_gap`
- one simple figure such as a dumbbell or slope plot showing within-city versus cross-city PR AUC for each selected city-model pair
- one companion figure showing within-city versus retained cross-city recall at top 10% predicted risk for the same comparable city-model pairs
- allow the exploratory `city_prevalence_baseline` rows to carry `n/a` retained cross-city comparison cells because that baseline is intentionally not part of the canonical transfer benchmark suite

### Within-City Spatial-Block Sensitivity Methodology

Scope guardrails:

- keep this path separate from the default within-city random-split contrast
- keep the same `Reno` / `Charlotte` / `Detroit` selected-city set
- keep the same six-feature first-pass contract
- keep the canonical cross-city city-held-out benchmark as the headline methodology
- do not describe within-city spatial blocks as equivalent to transfer into unseen cities

Current bounded implementation:

- model scope is logistic SAGA only for this pass
- reuse the same per-city sample cap of up to `20,000` rows
- assign deterministic within-city spatial blocks from cell centroids using city-specific median `centroid_lon` and median `centroid_lat`
- assign one of four centroid quadrants per sampled row: `southwest`, `southeast`, `northwest`, `northeast`
- break ties onto the north/east side using `>=` median comparisons
- evaluate one bounded holdout per non-empty block by training on the other blocks and testing on the held-out block

Current bounded outputs:

- `outputs/modeling/supplemental/within_city_spatial/within_city_spatial_sensitivity_summary.md`
- `outputs/modeling/supplemental/within_city_spatial/tables/within_city_spatial_metrics.csv`
- `outputs/modeling/supplemental/within_city_spatial/tables/within_city_spatial_contrast.csv`
- `figures/modeling/supplemental/within_city_spatial/within_city_spatial_pr_auc_contrast.png`

Current presentation:

- compare the default within-city random-split logistic summary to the harder spatial-block logistic summary for the same cities
- retain the city-level cross-city logistic benchmark columns in the same contrast table so the appendix view keeps the canonical benchmark visible
- report PR AUC plus recall at top 10% predicted risk in the spatial contrast table

### Feature-Importance / Interpretation Methodology

Retained reference runs to use:

- logistic reference run: `outputs/modeling/logistic_saga/full_allfolds_s20000_samplecurve-20k_2026-04-08_021152/`
- random-forest reference run: `outputs/modeling/random_forest/frontier_allfolds_s5000_frontier-check_2026-04-11_173430/`
- if future reporting refreshes rename those run directories, use the corresponding retained benchmark rows from `outputs/modeling/reporting/tables/cross_city_benchmark_report_benchmark_table.csv`

Current artifact constraint:

- the retained run directories save metrics, predictions, calibration tables, and `best_params_by_fold.csv`, but they do not currently save fitted estimator objects or exported feature-importance tables
- because of that, the current implementation uses a bounded refit/export path instead of trying to serialize large fitted estimator objects from the retained benchmark runs

Current bounded implementation path:

- do not rerun inner search grids for interpretation
- instead, add an interpretation-export mode that reads the retained `best_params_by_fold.csv`, refits only the final outer-fold estimator for each fold, and writes interpretation artifacts
- that keeps the interpretation work to `5` final-model refits for logistic plus `5` final-model refits for RF, rather than repeating the original benchmark tuning ladders

Logistic recommendation:

- use fold-level post-preprocessing coefficients as the primary logistic interpretation artifact
- export the resolved feature names after preprocessing so numeric features and one-hot categorical levels are visible explicitly
- summarize each feature with median coefficient, median absolute coefficient rank, and sign consistency across outer folds
- for categorical levels, report the encoded one-hot level names explicitly and interpret them as regularized model weights within the encoded design rather than as standalone causal effects
- add held-out-fold permutation importance for logistic only as a cross-check on the coefficient story, scored by held-out PR AUC / average-precision drop on the same retained outer-fold test rows
- keep logistic coefficients as the primary logistic interpretation artifact in the markdown summary and main figure

Random-forest recommendation:

- use permutation importance on the held-out-city rows from each outer fold as the primary RF importance method
- score permutation importance with PR AUC / average precision drop so the interpretation metric matches the main evaluation story
- aggregate importance across folds using mean drop, median rank, and fold-to-fold stability
- do not use impurity-based importance as the main reported result because it is more vulnerable to split-selection bias and can overstate importance under correlated predictors
- export impurity importance only in a separate appendix/debug table clearly marked as secondary

Interpretation guardrails:

- describe both coefficient summaries and permutation-importance summaries as first-pass model interpretation, not explanation of physical heat causation
- remind readers that correlated predictors can trade off with one another, especially `impervious_pct`, land-cover encodings, NDVI, and distance-to-water features
- do not claim that the model importance ranking estimates the effect of changing one urban feature in the real world
- keep the interpretation section tied to the current six-feature first-pass contract and say explicitly that richer feature sets could change the ranking

Most worth doing first:

- the `3`-city within-city contrast using representative cities and repeated stratified splits
- the exploratory `city_prevalence_baseline` as a bounded within-city context row only
- logistic coefficient summaries from the retained `20,000`-row sampled `full` benchmark configuration
- RF held-out-fold permutation importance from the retained `frontier` benchmark configuration
- one concise markdown summary plus PR AUC and recall contrast figures for within-city versus cross-city and one ranked-importance figure

Implemented after the original optional list:

- spatial-block within-city sensitivity runs for the same `3` cities, kept as a separate logistic-only appendix path rather than changing the default within-city workflow

Implementation status:

1. The retained reference runs and reporting-table snapshot are now frozen in code through `src.run_modeling_supplemental`.
2. The within-city city-selection helper now defaults to the nearest-median city in each climate group from `cross_city_benchmark_report_city_error_comparison.csv`.
3. The within-city runner now materializes the `3`-city repeated-stratified exploratory contrast under `outputs/modeling/supplemental/within_city/`.
4. The within-city supplemental tables and markdown now also include the exploratory `city_prevalence_baseline` as a within-city-only context row without changing the canonical cross-city baseline suite.
5. The within-city supplemental figure set now includes both PR AUC and recall-at-top-10%-risk contrast figures under `figures/modeling/supplemental/within_city/`.
6. The separate within-city spatial sensitivity runner now materializes the same `3` cities under `outputs/modeling/supplemental/within_city_spatial/` and `figures/modeling/supplemental/within_city_spatial/`, using deterministic centroid quadrants and logistic SAGA only so the pass stays bounded.
7. The retained-run interpretation-export path now refits saved outer-fold winners from `best_params_by_fold.csv` and writes primary logistic coefficient tables, logistic held-out permutation cross-check tables, primary RF held-out permutation tables, and secondary/debug RF impurity appendix tables under `outputs/modeling/supplemental/feature_importance/`.
8. The repo docs and handoff notes now document the supplemental outputs explicitly while keeping the cross-city benchmark narrative canonical.

Run logging note:

- meaningful modeling CLI runs now append structured records to `outputs/modeling/run_registry.jsonl`
- that registry now also supports `outputs/modeling/tuning_history.csv` as a cross-run chronology for later figure generation and model-selection rationale, with `outputs/modeling/tuning_history_annotations.csv` reserved for manual status and decision notes
