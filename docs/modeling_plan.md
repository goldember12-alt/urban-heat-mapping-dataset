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
- `src.run_logistic_saga_climate_interactions`
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

Current benchmark-strengthening candidates:

- histogram gradient boosting in an sklearn `Pipeline`, bounded to a Phase 1 smoke-only checkpoint on the same six-feature contract
- logistic SAGA with explicit training-only climate-by-numeric interactions, bounded to a Phase 2 smoke-only checkpoint on the same six-feature contract

Current implemented evaluation outputs:

- fold-level PR AUC
- per-city PR AUC
- recall at top 10% predicted risk
- calibration-curve tables
- held-out prediction tables
- per-fold best-parameter summaries for tuned models
- city-level RF-vs-logistic error comparison tables by city and climate group
- benchmark comparison markdown and benchmark figures under the modeling reporting layer
- optional Phase 1 HGB-vs-RF comparison tables under the shared modeling reporting layer when an HGB checkpoint is supplied
- optional Phase 2 logistic-climate-interaction comparison and climate-disparity tables under the shared modeling reporting layer when a climate-interaction checkpoint is supplied
- optional Phase 3 richer-predictor comparison tables under the shared modeling reporting layer when a richer-feature checkpoint is supplied
- representative held-out-city predicted-hotspot, true-hotspot, and categorical error maps under `outputs/modeling/reporting/heldout_city_maps/` and `figures/modeling/heldout_city_maps/`
- a bounded final-train transfer package under `outputs/modeling/final_train/` that reuses the retained six-feature benchmark selection without changing the canonical evaluation methodology
- an application-only transfer inference path under `outputs/modeling/transfer_inference/` and `figures/modeling/transfer_inference/` that applies the retained transfer package to one new-city feature parquet without computing new held-out-city benchmark metrics
- supplemental within-city contrast markdown/tables/figures under `outputs/modeling/supplemental/within_city/` and `figures/modeling/supplemental/within_city/`
- supplemental retained-run interpretation tables/figures under `outputs/modeling/supplemental/feature_importance/` and `figures/modeling/supplemental/feature_importance/`

Honest implementation status:

- The modeling-prep stage has been manually verified on the real 30-city final dataset
- The new sklearn-based modeling layer is test-verified on synthetic grouped-city fixtures
- A full canonical modeling run on the real final dataset is not currently the practical benchmark path on this workstation; sampled all-fold runs, typically up to `20,000` rows per city, are the meaningful comparison path to record in `docs/chat_handoff.md`
- `README.md` is now the canonical definition of `smoke` versus `full`, including how those presets should and should not be described in methodology/results language
- The tuned sklearn runners now persist mid-run progress plus fold-level state so interrupted runs can be resumed at the outer-fold boundary

## Candidate Feature Contract

Retained first-pass feature contract for the headline benchmark:

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

Current bounded richer-feature expansion contract:

- keep the retained six-feature benchmark contract frozen
- add the Phase 3A NLCD neighborhood-context bundle only in explicitly richer-feature runs:
  - `tree_cover_proxy_pct_270m`
  - `vegetated_cover_proxy_pct_270m`
  - `impervious_pct_mean_270m`

## Evaluation Plan

Primary metric:

- PR AUC

Implemented supporting evaluation:

- recall at top 10% predicted risk
- calibration-curve tables
- held-out-city comparison tables

Implemented post-benchmark deliverables:

- representative held-out-city predicted hotspot maps
- representative held-out-city true hotspot maps
- representative held-out-city categorical residual or error maps
- a bounded final-train transfer package based on the retained benchmark-selected model
- a separate transfer inference CLI for scoring one new-city feature parquet from that retained package

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

## Next Benchmark-Strengthening Roadmap

Purpose:

- improve the benchmark in deliberate stages without rewriting the project narrative
- separate gains from model class, climate conditioning, and richer predictors
- keep each step small enough that future agents can implement, test, and document it cleanly

Global guardrails for all phases:

- keep the canonical benchmark as cross-city city-held-out evaluation by `city_id`
- do not replace the retained logistic / RF checkpoints as the historical first-pass benchmark record
- do not report supplemental within-city results as benchmark-equivalent evidence
- keep parquet-first behavior, deterministic output paths, and raw-data immutability
- fit all preprocessing, encoding, interactions, imputation, selection, and tuning on training-city rows only
- update `README.md`, `docs/workflow.md`, `docs/data_dictionary.md`, `docs/modeling_plan.md`, and `docs/chat_handoff.md` whenever a phase lands

Recommended execution order:

1. Phase 1: better learner with the same six features
2. Phase 2: climate-conditioned structure with the same six features
3. Phase 3: richer predictor bundles, introduced one theme at a time

### Phase 1: Better Learner With The Same Six Features

Goal:

- test whether a stronger tabular learner improves held-out-city transfer without changing the feature contract

Primary candidate:

- histogram gradient boosting as the first new benchmark model family

Why this phase comes first:

- current retained logistic and RF tuning has largely plateaued
- the fastest remaining question is whether model class still matters under the exact same six-feature contract
- this phase preserves the cleanest apples-to-apples comparison with the retained benchmark

Feature contract for this phase:

- `impervious_pct`
- `elevation_m`
- `dist_to_water_m`
- `ndvi_median_may_aug`
- `land_cover_class`
- `climate_group`

Modeling and tuning scope:

- add one new runner, likely `src.run_hist_gradient_boosting`
- add one shared pipeline builder in `src.modeling_runner`
- start with a bounded `smoke` preset only
- use the same grouped outer folds and training-city-only preprocessing contract as logistic / RF
- if the model cannot natively handle categorical columns in the desired sklearn version, keep preprocessing explicit and training-only
- do not add a frontier/full expansion in the same task unless the smoke result clearly beats the retained RF frontier checkpoint

Likely code touchpoints:

- `src/modeling_config.py`
- `src/modeling_runner.py`
- `src/modeling_reporting.py`
- `src/modeling_run_registry.py`
- `src/run_modeling_reporting.py`
- new CLI entrypoint such as `src/run_hist_gradient_boosting.py`
- optional new helper module only if shared code would otherwise become messy

Expected outputs:

- a new run root under `outputs/modeling/hist_gradient_boosting/`
- standard run outputs matching current tuned-runner conventions:
  - metrics summary
  - fold metrics
  - city metrics
  - held-out predictions
  - calibration table
  - best-parameter summary
  - run metadata
- refreshed reporting comparisons through `src.run_modeling_reporting`, not through ad hoc tables

Tests required before calling the phase complete:

- feature-contract and leakage-safe grouped-fold parity with existing tuned runners
- deterministic default output-path generation if auto-naming is used
- preprocessing compatibility for mixed numeric/categorical six-feature inputs
- run-metadata and reporting-table integration
- at least one focused CLI-level test analogous to the current logistic / RF runner tests

Manual verification target:

- one bounded real smoke run on the canonical parquet with serial worker settings
- one reporting refresh after the retained result is available

Decision rule after Phase 1:

- if the better learner does not meaningfully beat the retained RF frontier result on pooled PR AUC and does not improve the city-level story, stop and keep it as a negative-result checkpoint
- if it improves pooled PR AUC only in a narrow subset of cities, note that honestly and continue to Phase 2 before considering any larger tuning expansion
- only consider a broader search for this learner if the smoke result changes the benchmark story enough to justify more runtime

Current Phase 1 status after the implemented smoke checkpoint:

- `src.run_hist_gradient_boosting` now exists and reuses the shared grouped-city runner, six-feature contract, parquet-first data path, deterministic output structure, run registry, tuning history, and `src.run_modeling_reporting` integration
- the current retained Phase 1 checkpoint is `outputs/modeling/hist_gradient_boosting/phase1_smoke_allfolds/`
- sampled all-fold smoke metrics on the canonical parquet at `5000` rows per city are:
  - pooled PR AUC `0.1408`
  - mean city PR AUC `0.1761`
  - pooled recall at top 10% `0.1751`
- retained RF frontier at the same sampled slice remains stronger:
  - pooled PR AUC `0.1486`
  - mean city PR AUC `0.1781`
  - pooled recall at top 10% `0.1961`
- the optional reporting comparison under `cross_city_benchmark_report_phase1_smoke_phase1_hgb_vs_rf.csv` shows HGB wins `17` city-fold PR AUC rows and loses `13`, but the overall mean PR AUC delta is still negative at `-0.0020`, with mild-cool cities especially weaker on average
- treat Phase 1 as implemented and currently closed as a negative-result checkpoint; do not widen HGB tuning unless a later explicit decision reopens it

### Phase 2: Climate-Conditioned Structure With The Same Six Features

Goal:

- test whether climate heterogeneity is a major source of transfer failure under the current six-feature contract

Priority implementation order inside this phase:

1. logistic climate-interaction benchmark
2. climate-aware version of the better Phase 1 learner if still warranted
3. same-climate transfer appendix as a supplemental diagnostic only

Phase 2A: logistic climate interactions

- keep the canonical six features unchanged
- add explicit interactions between `climate_group` and the numeric predictors inside the training-only preprocessing pipeline
- preserve the same grouped held-out-city evaluation
- keep this as a separate benchmark runner or explicit model variant, not a silent change to the retained logistic path

Phase 2B: climate-aware nonlinear structure

- if the better learner from Phase 1 remains promising, allow it to exploit climate-conditioned structure explicitly while still training only on training cities
- do not let this become a feature-expansion task; the only change here is how the same six features are modeled

Phase 2C: same-climate supplemental appendix

- optional and explicitly supplemental
- for each held-out city, train only on training cities in the same `climate_group`
- write results under a separate supplemental root if implemented
- never present this appendix as a replacement for the all-city held-out benchmark

Likely code touchpoints:

- `src/modeling_runner.py`
- `src/modeling_config.py`
- `src/modeling_reporting.py`
- `src/run_modeling_reporting.py`
- `src.run_logistic_saga_climate_interactions`
- supplemental reporting code only if Phase 2C is implemented

Expected outputs:

- one new benchmark run family or variant with normal tuned-runner outputs
- refreshed reporting tables showing whether climate-conditioned structure reduces climate-group disparity
- if Phase 2C is implemented, a separate supplemental appendix root rather than new canonical benchmark paths

Tests required before calling the phase complete:

- training-only interaction construction with no leakage from held-out cities
- parity of grouped fold behavior and feature-contract enforcement
- reporting-table integration for the new benchmark family or variant
- explicit tests that any same-climate appendix remains separate from the canonical benchmark reporting layer

Manual verification target:

- one bounded real benchmark run for the interaction model or climate-aware learner
- inspection of reporting tables by climate group before deciding whether this phase materially improves the story

Decision rule after Phase 2:

- if climate-conditioned structure narrows the hot-arid / hot-humid / mild-cool performance spread meaningfully, keep it as a serious candidate for the next benchmark rung
- if it only improves within one climate group and complicates interpretation heavily, document that and move to richer predictors instead of widening modeling complexity further

Current Phase 2 status after the implemented smoke checkpoint:

- `src.run_logistic_saga_climate_interactions` now exists and reuses the shared grouped-city runner, six-feature contract, parquet-first data path, deterministic output structure, run registry, tuning history, and `src.run_modeling_reporting` integration while keeping the retained logistic path untouched
- the current retained Phase 2 checkpoint is `outputs/modeling/logistic_saga_climate_interactions/phase2_smoke_allfolds/`
- sampled all-fold smoke metrics on the canonical parquet at `5000` rows per city are:
  - pooled PR AUC `0.1480`
  - mean city PR AUC `0.1814`
  - pooled recall at top 10% `0.1801`
- versus retained logistic `5000`, that smoke checkpoint improves pooled PR AUC from `0.1421` to `0.1480`, mean city PR AUC from `0.1803` to `0.1814`, and pooled recall at top 10% from `0.1647` to `0.1801`
- the optional reporting comparison under `cross_city_benchmark_report_phase2_smoke_phase2_logistic_ci_vs_logistic_by_climate.csv` shows the gains are concentrated mainly in `hot_arid`, `hot_humid` is nearly flat, and `mild_cool` degrades on both PR AUC and recall
- the new disparity table under `cross_city_benchmark_report_phase2_smoke_phase2_logistic_ci_vs_logistic_disparity.csv` shows narrower climate-group spread, with PR AUC range reduced by `0.0193` and recall range reduced by `0.0172`
- treat Phase 2 as implemented and currently closed as a mixed-result checkpoint: it suggests climate heterogeneity matters, but not cleanly enough to replace the retained benchmark or to justify widening Phase 2B/2C before moving to richer predictors

### Phase 3: Richer Predictor Bundles

Goal:

- raise the benchmark meaningfully once model-class-only and climate-structure-only gains are exhausted

Principle:

- add predictors in small themed bundles so we can attribute gains and keep the data pipeline maintainable

Recommended bundle order:

1. tree canopy / vegetation structure
2. urban form / density / morphology
3. surface reflectance or albedo proxies
4. building intensity / height proxies
5. finer water / coastal exposure detail if justified

Recommended first bundle:

- canopy cover
- one additional vegetation or moisture proxy beyond NDVI
- one urban morphology bundle such as road density, intersection density, building coverage, or local built-form summary at one or more radii

Implemented Phase 3A first bundle:

- the landed first bundle uses the lowest-risk existing-source path rather than adding a new national acquisition dependency
- the current bundle is an NLCD neighborhood-context bundle built from the prepared/aligned land-cover and impervious rasters already in the repo workflow
- the three landed columns are:
  - `tree_cover_proxy_pct_270m`
  - `vegetated_cover_proxy_pct_270m`
  - `impervious_pct_mean_270m`
- these should be described as bounded local context proxies, not as a replacement for a dedicated national canopy product or a full morphology stack

Implementation requirements:

- each bundle must have a documented raw-to-processed acquisition and feature-assembly path
- raw data remain immutable and cached under the established raw/support-layer contracts
- new per-city features must integrate into `data_processed/city_features/*.parquet` and the final assembly contract deliberately
- do not add a large kitchen-sink feature set in one pass
- after each bundle lands, rerun the dataset audit and fold-compatible modeling path before claiming benchmark improvement

Likely code touchpoints:

- acquisition or support-layer modules for the new data source
- per-city feature assembly modules
- final dataset assembly and audit modules
- `src.run_phase3a_nlcd_bundle` for deterministic parquet-first backfill of the Phase 3A bundle into existing per-city feature artifacts
- `docs/data_dictionary.md` for schema additions
- modeling runners only after the new features are fully integrated and audited

Expected outputs:

- new deterministic raw/support/intermediate artifacts for the bundle
- updated final dataset schema and audit outputs
- one new benchmark comparison against the frozen six-feature benchmark

Tests required before calling the phase complete:

- raw or support-layer acquisition helper tests as needed
- feature-assembly tests for the new columns
- final-dataset audit coverage for the expanded schema
- modeling feature-contract tests if a new feature bundle becomes an approved benchmark contract

Manual verification target:

- one bounded city-level preprocessing verification for the new feature bundle
- one full-dataset audit refresh
- one benchmark run at a bounded sampled slice before any broader expansion

Decision rule after each Phase 3 bundle:

- if the bundle does not move the held-out-city benchmark materially, stop and record it as non-essential
- if the bundle improves the benchmark but adds large operational cost, keep both the frozen six-feature benchmark and the expanded-feature benchmark clearly separated in reporting

Current Phase 3A status after the implemented first bundle:

- `src.run_phase3a_nlcd_bundle` now backfills the bounded Phase 3A NLCD neighborhood-context bundle into existing per-city feature parquets and intermediate feature tables without rerunning NDVI or ECOSTRESS acquisition
- the canonical final dataset has been refreshed and now carries `17` columns, with the three new Phase 3A columns added alongside the retained historical schema
- `src.audit_final_dataset` now audits the richer nine-feature candidate contract by default, while `src.modeling_prep.validate_required_final_columns(...)` still keeps the legacy core final columns as the minimum compatibility requirement
- the current bounded richer-feature benchmark is `outputs/modeling/logistic_saga/full_allfolds_s5000_phase3a-nlcd-context_2026-04-13_142451/`
- relative to retained logistic `5000`, that Phase 3A run improves pooled PR AUC from `0.1421` to `0.1450`, mean city PR AUC from `0.1803` to `0.1807`, and pooled recall at top `10%` from `0.1647` to `0.1699`
- the optional reporting comparison under `outputs/modeling/reporting/cross_city_benchmark_report_phase3a_nlcd_context.md` shows the gains are modest overall, stronger in `hot_arid` and `mild_cool`, and weaker in `hot_humid`
- treat Phase 3A as implemented and currently closed as a modest-gain richer-feature checkpoint: keep the frozen six-feature benchmark as the headline story, keep Phase 3A separate in reporting, and only add another richer bundle after an explicit follow-on decision

## Phase 1 Handoff Checklist

When a future agent starts Phase 1, the implementation target is:

- add one better learner under the same six-feature contract
- keep the retained benchmark story frozen
- avoid expanding routine logistic / RF search
- add focused tests, one bounded real smoke run if feasible, and full doc / handoff updates

Minimum completion bar for Phase 1:

- code landed
- targeted tests passed
- at least one bounded real run command recorded or an honest blocker documented
- reporting integration completed or explicitly deferred with rationale
- `docs/chat_handoff.md` updated with exact verification status and next step

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
- `outputs/modeling/supplemental/within_city_all_cities/within_city_all_cities_summary.md`
- `outputs/modeling/supplemental/within_city_all_cities/tables/*.csv`
- `figures/modeling/supplemental/within_city_all_cities/*.png`
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

### All-City Within-City Supplemental Methodology

Scope guardrails:

- keep this pass explicitly subordinate to the canonical cross-city city-held-out benchmark
- do not present repeated within-city random splits as evaluation-equivalent to held-out-city transfer
- keep the same six-feature first-pass contract
- do not reopen broader within-city RF frontier/full search in this pass
- keep the existing `Reno` / `Charlotte` / `Detroit` exploratory slice intact rather than replacing it

Current bounded implementation:

- iterate over all benchmark cities using the retained reporting roster from `outputs/modeling/reporting/tables/cross_city_benchmark_report_city_error_comparison.csv`
- sample up to `20,000` rows per city with the existing stratified city-sampling helper
- use all available rows when a city has fewer than `20,000`
- run `3` repeated stratified within-city `80/20` train/test splits with fixed seeds
- fit only `city_prevalence_baseline`, logistic SAGA, and random forest
- keep tuning bounded to the same `smoke`-sized within-city grids used by the smaller exploratory supplement
- use the retained city-error comparison table only as a comparison reference for within-city-vs-cross-city gap summaries; do not rerun or redefine the benchmark

Current bounded outputs:

- `outputs/modeling/supplemental/within_city_all_cities/within_city_all_cities_summary.md`
- `outputs/modeling/supplemental/within_city_all_cities/within_city_all_cities_predictions.parquet`
- `outputs/modeling/supplemental/within_city_all_cities/tables/within_city_all_cities_repeat_metrics.csv`
- `outputs/modeling/supplemental/within_city_all_cities/tables/within_city_all_cities_city_summary.csv`
- `outputs/modeling/supplemental/within_city_all_cities/tables/within_city_all_cities_climate_summary.csv`
- `outputs/modeling/supplemental/within_city_all_cities/tables/within_city_all_cities_cross_city_gap_by_city.csv`
- `outputs/modeling/supplemental/within_city_all_cities/tables/within_city_all_cities_cross_city_gap_by_climate.csv`
- `figures/modeling/supplemental/within_city_all_cities/within_city_all_cities_pr_auc_by_climate.png`
- `figures/modeling/supplemental/within_city_all_cities/within_city_all_cities_recall_by_climate.png`
- `figures/modeling/supplemental/within_city_all_cities/within_city_all_cities_within_vs_cross_gap.png`

Current presentation:

- restate in the markdown summary that the benchmark remains canonical and the all-city within-city pass is easier
- use climate-group summaries to compare within-city performance patterns across `hot_arid`, `hot_humid`, and `mild_cool`
- use city-level within-city-versus-cross-city gaps to diagnose whether some cities look mainly transfer-hard versus hard even under the six-feature within-city setting
- keep any such interpretation careful and explicitly non-benchmark-equivalent

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
6. The opt-in all-city within-city appendix now materializes under `outputs/modeling/supplemental/within_city_all_cities/` and `figures/modeling/supplemental/within_city_all_cities/`, using the same six-feature contract, `3` repeated stratified `80/20` splits, smoke-sized within-city tuning only, and retained reporting tables strictly as comparison references.
7. The separate within-city spatial sensitivity runner now materializes the same `3` cities under `outputs/modeling/supplemental/within_city_spatial/` and `figures/modeling/supplemental/within_city_spatial/`, using deterministic centroid quadrants and logistic SAGA only so the pass stays bounded.
8. The retained-run interpretation-export path now refits saved outer-fold winners from `best_params_by_fold.csv` and writes primary logistic coefficient tables, logistic held-out permutation cross-check tables, primary RF held-out permutation tables, and secondary/debug RF impurity appendix tables under `outputs/modeling/supplemental/feature_importance/`.
9. The repo docs and handoff notes now document the supplemental outputs explicitly while keeping the cross-city benchmark narrative canonical.

Run logging note:

- meaningful modeling CLI runs now append structured records to `outputs/modeling/run_registry.jsonl`
- that registry now also supports `outputs/modeling/tuning_history.csv` as a cross-run chronology for later figure generation and model-selection rationale, with `outputs/modeling/tuning_history_annotations.csv` reserved for manual status and decision notes
