# Final Report Outline

Working title:

**Cross-City Urban Heat Hotspot Prediction: A 30 m Dataset and City-Held-Out Transfer Benchmark**

Collaborators:

- Max Clements
- Nicholas Machado

Course:

- STAT 5630 Statistical Machine Learning

## Assignment Constraints

- Submit final report as PDF by 2026-05-04 at 11:59pm.
- Required report parts:
  - Main Text
  - Tables and Figures
  - Appendix
- Main text limit for two-person project: 15 pages, single-spaced, 12 pt, 1 inch margins.
- Tables and figures should be organized in their own section, not interleaved with the main text.
- Recommended content sections from assignment:
  - Background Information
  - Research Questions
  - Model and Method
  - Analysis, Conclusion and Discussion
  - Appendix

## Core Narrative

Urban heat varies at fine spatial scales, but models evaluated with ordinary row-level splits can overstate how well they would generalize to cities that did not contribute training labels. This project builds a standardized 30 m cell-level dataset for 30 U.S. cities and evaluates whether non-thermal geospatial predictors can identify the hottest within-city cells in fully held-out cities. The main contribution is therefore twofold: a reproducible cross-city urban heat dataset and a leakage-safe city-held-out modeling benchmark.

The conclusion should be deliberately bounded. Cross-city hotspot prediction is feasible because learned models outperform simple transfer baselines, but performance is moderate and uneven across cities and climate groups. The strongest current random-forest checkpoint improves pooled PR AUC and top-decile recall relative to the matched logistic regression checkpoint, while logistic regression remains slightly stronger on mean city PR AUC. The project supports transferable screening, not deployment-ready heat-risk classification.

## Main Text

### 1. Background Information

Purpose:

- Motivate urban heat as a public-health, infrastructure, and planning problem.
- Explain why fine-scale land-surface characteristics matter.
- Introduce the transfer gap: within-city prediction is easier than predicting hotspots in cities not seen during training.
- Identify the public data sources used to construct the dataset.

Use from proposal:

- General urban heat motivation.
- NLCD land cover and imperviousness background.
- USGS 3DEP elevation background.
- NHDPlus hydrography background.
- Landsat/AppEEARS NDVI background.
- ECOSTRESS LST background.

Update from proposal:

- Replace future tense and Phoenix-only preliminary framing with completed 30-city dataset framing.
- Avoid presenting Phoenix exploratory summaries as the project result.
- Cite the completed final dataset size and city coverage.

Partner gap:

`[PARTNER TODO: Add 1-2 paragraphs of related-work context and citations on urban heat mapping, remotely sensed LST, or transfer/generalization in spatial ML. Keep this aligned with the dataset and transfer benchmark rather than a broad climate-change essay.]`

### 2. Research Questions

Primary question:

- Can a model trained on a multi-city urban heat dataset identify hotspot cells in cities that were entirely excluded from training?

Secondary questions:

- Do non-thermal geospatial predictors contain transferable signal for hotspot screening?
- Does random forest improve cross-city ranking or retrieval relative to logistic regression and simple baselines?
- Does performance vary systematically by climate group or city?

Target population:

- 30 m grid cells inside buffered Census urban-area study regions for the 30 selected U.S. cities.
- Inference is about relative within-city hotspot screening for similar U.S. urban areas, not absolute national heat exposure thresholds.

### 3. Dataset Construction

Purpose:

- This should be the first major writing pass.
- Explain the completed dataset clearly enough that the modeling setup feels inevitable.

Key facts:

- 30 U.S. cities.
- Climate groups: 10 hot-arid, 10 hot-humid, 10 mild-cool.
- Study area: Census urban area containing city center, buffered by 2 km by default.
- Analytic unit: one 30 m grid cell per city.
- Final canonical dataset: `data_processed/final/final_dataset.parquet`.
- Final audited size: 71,394,894 rows and 17 columns.
- Canonical target: `hotspot_10pct`.

Construction steps:

1. Select study cities and assign broad climate groups.
2. Build buffered study areas from Census urban-area geometry.
3. Build local UTM 30 m grids.
4. Acquire and prepare source layers:
   - NLCD land cover
   - NLCD impervious percentage
   - USGS 3DEP elevation
   - NHDPlus water features
   - Landsat/AppEEARS NDVI
   - ECOSTRESS/AppEEARS LST
5. Align raster and vector-derived features to each city grid.
6. Assemble per-city feature tables.
7. Merge final dataset.
8. Apply final row filters:
   - drop open-water cells where `land_cover_class == 11`
   - drop rows with fewer than 3 valid ECOSTRESS passes
   - recompute `hotspot_10pct` within each city after filtering

Variables to describe:

- Predictors used in headline models:
  - `impervious_pct`
  - `land_cover_class`
  - `elevation_m`
  - `dist_to_water_m`
  - `ndvi_median_may_aug`
  - `climate_group`
- Outcome ingredient:
  - `lst_median_may_aug`
- Target:
  - `hotspot_10pct`, defined from each city-specific 90th percentile of valid LST.
- Metadata:
  - city, cell, centroid fields.
- Extra dataset columns:
  - neighborhood-context Phase 3A features, kept for expansion but not part of the frozen headline benchmark.

Partner gap:

`[PARTNER TODO: Review this section for domain-language clarity. Add one sentence on why city-relative top-decile hotspots are more appropriate than one national absolute LST cutoff for a cross-climate city set.]`

### 4. Model and Method

Purpose:

- Translate the dataset into a statistical learning problem.
- Emphasize leakage-safe city-held-out evaluation.

Prediction task:

- Predict probability that a cell is in the hottest 10% of valid cells in its own city, using only non-thermal predictors.

Excluded first-pass predictive fields:

- `hotspot_10pct`
- `lst_median_may_aug`
- `n_valid_ecostress_passes`
- `cell_id`
- `city_id`
- `city_name`
- `centroid_lon`
- `centroid_lat`

Evaluation design:

- Five deterministic outer folds.
- Six held-out cities per fold.
- Every city held out exactly once.
- All preprocessing, imputation, scaling, encoding, feature selection, and tuning fit only on training-city rows.

Metrics:

- PR AUC as primary metric because target prevalence is about 10%.
- Mean city PR AUC to avoid letting larger cities dominate interpretation.
- Recall at top 10% predicted risk as a screening-oriented retrieval metric.
- Calibration tables exist but are secondary in the report narrative.

Models:

- Simple baselines:
  - global mean baseline
  - land-cover-only baseline
  - impervious-only baseline
  - climate-only baseline
- Logistic regression:
  - sklearn pipeline
  - training-only imputation, scaling, one-hot encoding
  - `solver="saga"`
  - tuned regularization
- Random forest:
  - sklearn pipeline
  - training-only imputation and categorical encoding
  - tuned tree count, depth, feature subsampling, and leaf size

Computational caveat:

- Retained benchmark results use sampled all-fold runs, especially 5,000 to 20,000 rows per city, because exhaustive all-row tuning over 71.4 million rows was not the practical benchmark path on the available workstation.

Partner gap:

`[PARTNER TODO: Add or refine statistical-method explanations in course language, especially PR AUC, grouped cross-validation, logistic regression, and random forest. Keep formulas short and interpretable.]`

### 5. Analysis and Results

Purpose:

- Present the benchmark as evidence for bounded transfer, not as a claim of high accuracy.

Required result claims:

- Learned models beat strongest simple baselines on pooled PR AUC.
- Matched 5,000 rows-per-city comparison:
  - Logistic SAGA pooled PR AUC: 0.1421.
  - Random forest frontier pooled PR AUC: 0.1486.
  - Logistic recall at top 10%: 0.1647.
  - Random forest recall at top 10%: 0.1961.
  - Logistic mean city PR AUC: 0.1803.
  - Random forest mean city PR AUC: 0.1781.
- Interpretation:
  - RF improves aggregate ranking and retrieval.
  - Logistic remains slightly stronger on average city PR AUC.
  - RF gains are concentrated in hot-arid cities and selected cities, not uniform.

Climate/city heterogeneity:

- RF minus logistic mean PR AUC delta by climate:
  - hot-arid: +0.0336
  - hot-humid: -0.0123
  - mild-cool: -0.0281
- RF minus logistic recall-at-top-10% delta by climate:
  - hot-arid: +0.0762
  - hot-humid: -0.0164
  - mild-cool: -0.0280

Spatial example:

- Denver held-out map triptych is a representative benchmark snapshot, not an exhaustive citywide inference surface.
- Use it to show that transfer errors are spatially structured and the model captures partial but imperfect hotspot geography.

Feature interpretation:

- Retained RF permutation importance and logistic coefficients suggest vegetation, imperviousness, land cover, elevation, and climate group carry most of the transferable signal.
- State clearly that feature importance is not causal evidence.

Partner gap:

`[PARTNER TODO: Decide whether to add the partner-provided per-city logistic/RF classification results. If included, label them supplemental/easier-split diagnostics and do not let them replace the retained city-held-out benchmark.]`

### 6. Discussion and Limitations

Main limitations:

- Sampled all-fold benchmark rather than exhaustive full-row scoring.
- City-relative hotspot target is useful for within-city screening but not an absolute heat-exposure threshold.
- Transfer performance is uneven across cities and climate groups.
- Feature contract is intentionally narrow; richer context features are only supplemental.
- Remote-sensing LST captures surface temperature, not direct human heat exposure.
- Spatial autocorrelation and city-specific land-form patterns remain challenges for generalization.

Validity discussion:

- City-held-out evaluation is the main validity strength.
- Train-only preprocessing and tuning reduce leakage.
- PR AUC and recall-at-top-10% are appropriate for a 10% hotspot-screening target.
- Remaining validity concern is external generalization beyond the selected 30-city sample.

Future directions:

- Confirm larger or full-population benchmark on stronger hardware.
- Expand climate-conditioned modeling carefully.
- Add richer spatial-context predictors.
- Improve calibration and threshold selection.
- Connect predictions to demographic vulnerability or planning outcomes in a later-stage analysis.

### 7. Conclusion

Core conclusion:

- The project successfully built a reproducible 30-city, 30 m urban heat dataset and a leakage-safe transfer benchmark.
- Cross-city hotspot prediction is feasible but difficult.
- Random forest provides a modest aggregate gain in pooled PR AUC and top-decile recall, especially in hot-arid cities, while logistic regression remains competitive and steadier by mean city PR AUC.
- The best framing is a transferable screening framework with documented limits.

## Tables and Figures Section

Tables and figures should be placed after the main text to satisfy the assignment instruction not to mix them with prose.

See `docs/report/final_report_planning.md` for full figure provenance and generation status.

Recommended main tables:

- Table 1. Data sources and constructed variables.
- Table 2. Final dataset summary by climate group.
- Table 3. Main city-held-out benchmark results.
- Table 4. RF minus logistic performance by climate group.

Recommended main figures:

- Figure 1. Study city locations.
- Figure 2. Dataset construction workflow.
- Figure 3. City-held-out evaluation design.
- Figure 4. Benchmark metric comparison.
- Figure 5. City-level RF minus logistic deltas.
- Figure 6. Denver held-out map triptych.

Recommended appendix figures:

- Supplemental feature-importance summary.
- Within-city versus cross-city performance gap.
- Full city row-count distribution if generated.
- Missingness summary if generated.

## Appendix

Include:

- Extra tables or figures not central enough for the main Tables/Figures section.
- Model hyperparameter grids or selected parameters.
- Data dictionary excerpt for final dataset columns.
- Reproducibility notes with key repo artifacts and commands.
- Code/output excerpts only as needed for the course requirement.

Possible appendix placeholders:

`[APPENDIX TODO: Add final dataset column table from docs/data_dictionary.md.]`

`[APPENDIX TODO: Add hyperparameter grid / retained run metadata for logistic and RF.]`

`[APPENDIX TODO: Add brief reproducibility note listing canonical repo entrypoints and retained artifact paths.]`
