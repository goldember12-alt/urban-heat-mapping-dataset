# Final Report Outline

Working title:

**Cross-City Urban Heat Hotspot Screening: Within-City Learning and City-Held-Out Transfer**

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

Working interpretation after reading the assignment:

- The 15-page cap applies to Main Text only, not to the title page, Tables and Figures section, or Appendix.
- The current rendered draft leaves substantial Main Text space available, so the report should be expanded for rigor rather than kept artificially short.
- Preserve single spacing, 12 pt font, and 1 inch margins in the Pandoc/XeLaTeX render command.

## Core Narrative

Urban heat varies at fine spatial scales, but the meaning of model performance depends on the validation design. This project builds a standardized 30 m cell-level dataset for 30 U.S. cities and evaluates whether basic environmental and built-environment predictors can identify the hottest within-city cells under two settings: within-city held-out evaluation and whole-city holdout transfer. The main contribution is therefore threefold: a reproducible cross-city urban heat dataset, an explicit comparison of same-city hotspot screening against unseen-city transfer, and a leakage-safe city-held-out benchmark.

The conclusion should be deliberately bounded but not apologetic. The retained predictors contain real hotspot signal. Within-city held-out evaluation makes random forest look clearly stronger than logistic regression on hotspot precision, recall, and F1. City-held-out transfer is weaker, closer between models, and more heterogeneous: random forest modestly improves pooled PR AUC and top-decile recall relative to the matched logistic checkpoint, while logistic remains competitive and slightly stronger on mean city PR AUC. The project supports a validation-design comparison and transfer-screening benchmark with clear limits, not deployment-ready heat-risk classification.

## Main Text

### 1. Background Information

Purpose:

- Motivate urban heat as a public-health, infrastructure, and planning problem.
- Explain why fine-scale land-surface characteristics matter.
- Introduce the transfer gap: within-city prediction is easier than predicting hotspots in cities not seen during training.
- Identify the public data sources used to construct the dataset.
- Establish a clear research gap from existing work:
  - many remote-sensing urban heat studies map one city or summarize correlations.
  - LST studies commonly link heat with impervious surface, vegetation/NDVI, water, and land cover.
  - spatial prediction can look stronger under random row/cell splits than under spatial or city-level validation.
  - this project separates the easier same-city screening question from the harder transfer question by also holding out entire cities.

Target expansion:

- Add at least 1-2 pages of background/literature context before the research questions.
- Include formal references and a References section later in the document.

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

Insertion note:

`[Insert related-work extension here: add 1-2 paragraphs of related-work context and citations on urban heat mapping, remotely sensed LST, or transfer/generalization in spatial ML. Keep this aligned with the two-design validation narrative rather than a broad climate-change essay.]`

Suggested references to verify and use:

- Voogt and Oke (2003) on thermal remote sensing of urban climates.
- Weng, Lu, and Schubring (2004) and/or Yuan and Bauer (2007) on LST, impervious surface, and NDVI.
- NASA Earthdata / ECOSTRESS documentation on LST and ECOSTRESS spatial/temporal data properties.
- NASA Earthdata / AppEEARS documentation for data access/subsetting.
- Spatial cross-validation literature such as Roberts et al. (2017) or Meyer et al. (2018) for transfer/validation concerns.

### 2. Research Questions

Primary question:

- Can basic environmental and built-environment features identify urban heat hotspots across a multi-city dataset, and how does performance change when evaluation moves from within-city held-out cells to whole-city held-out transfer?

Explicit subquestions:

- Within-city screening: when a city is represented during model development, can the model identify held-out hotspot cells from that same city?
- City-held-out transfer: when a whole city is excluded from training, can the model rank that unseen city's cells by hotspot risk?

Secondary questions:

- Do non-thermal geospatial predictors contain useful signal for hotspot screening?
- Does random forest improve over logistic regression and simple baselines, and does that model ranking change by validation design?
- Does performance vary systematically by climate group or city?
- Does within-city success predict city-held-out transfer success?

Target population:

- 30 m grid cells inside buffered Census urban-area study regions for the 30 selected U.S. cities.
- Inference is about relative within-city hotspot screening for similar U.S. urban areas, not absolute national heat exposure thresholds.

### 3. Dataset Construction

Purpose:

- This should be the first major writing pass.
- Explain the completed dataset clearly enough that the modeling setup feels inevitable.
- Use additional Main Text space to make this section a methodological contribution, not just a schema summary.

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

Expansion priorities:

- Explain why city selection and climate grouping matter for transfer.
- Explain why the Census urban area plus 2 km buffer is used.
- Explain why the core urban geometry is preserved.
- Explain why local UTM and a master 30 m grid are important for distances and alignment.
- Explain how raster and vector layers are converted to cell-level features.
- Explain May-August summaries for NDVI and ECOSTRESS LST.
- Explain pass-count filtering and city-specific hotspot recomputation.
- Add a short data-quality paragraph using audit totals and missingness if space allows.

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

Insertion note:

`[Insert city-relative target language here: add one concise sentence on why city-relative top-decile hotspots are more appropriate than one national absolute LST cutoff for a cross-climate city set.]`

### 4. Model and Method

Purpose:

- Translate the dataset into a statistical learning problem.
- Separate within-city held-out evaluation from city-held-out transfer.
- Emphasize that city-held-out evaluation is the stricter transfer result.
- Use the within-city result as the necessary contrast for interpreting how validation design changes apparent model performance.

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

Evaluation designs:

- Within-city held-out cells:
  - verified 70/30 within-city evaluation.
  - cities are represented during model development.
  - evaluates held-out cells from those same cities.
  - reports hotspot precision, recall, and F1.
  - answers same-city screening/interpolation, not unseen-city transfer.
- City-held-out transfer:
  - five deterministic outer folds.
  - six held-out cities per fold.
  - every city held out exactly once.
  - all preprocessing, imputation, scaling, encoding, feature selection, and tuning fit only on training-city rows.

Interpretive boundary:

- City-held-out validation remains the headline benchmark for transfer.
- Within-city validation is not replacing it; it shows what happens when local examples from the same cities are available.
- The two settings may use different metrics, so compare directional patterns and implications rather than raw magnitudes across designs.

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

Insertion note:

`[Insert within-city held-out design details and results here: describe the verified 70/30 within-city evaluation, report logistic-versus-random-forest precision, recall, and F1, and explain that this setting measures same-city hotspot screening rather than unseen-city transfer.]`

### 5. Analysis and Results

Purpose:

- Present the benchmark as evidence for bounded transfer, not as a claim of high accuracy.
- Use available Main Text space to interpret not only which model is higher, but why the metrics disagree and what that implies for transfer reliability.

Required result claims:

- Within-city held-out evaluation:
  - random forest clearly outperforms logistic regression on hotspot precision, recall, and F1.
  - presentation metric checks: logistic precision 0.3887, recall 0.0727, F1 0.1083; random forest precision 0.7310, recall 0.3433, F1 0.4480.
  - interpret as evidence that nonlinear structure helps when local city examples are available.
- City-held-out transfer:
  - learned models beat strongest simple baselines on pooled PR AUC.
  - matched 5,000 rows-per-city comparison:
  - Logistic SAGA pooled PR AUC: 0.1421.
  - Random forest frontier pooled PR AUC: 0.1486.
  - Logistic recall at top 10%: 0.1647.
  - Random forest recall at top 10%: 0.1961.
  - Logistic mean city PR AUC: 0.1803.
  - Random forest mean city PR AUC: 0.1781.
- Interpretation:
  - RF modestly improves aggregate ranking and retrieval.
  - Logistic remains slightly stronger on average city PR AUC.
  - RF gains are concentrated in hot-arid cities and selected cities, not uniform.
- Evaluation-design comparison:
  - the main result is not one universal model ranking.
  - performance and model advantage change when moving from within-city held-out evaluation to whole-city transfer.
  - within-city success should not be treated as evidence of cross-city transfer.

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

- Denver held-out map example is a representative benchmark snapshot, not an exhaustive citywide inference surface.
- Use it to show that transfer errors are spatially structured and the model captures partial but imperfect hotspot geography.
- Mention the presentation lesson: false positives and false negatives are spatially organized, suggesting partial built-environment signal but missed city-specific detail.

Feature interpretation:

- Retained RF permutation importance and logistic coefficients suggest vegetation, imperviousness, land cover, elevation, and climate group carry most of the transferable signal.
- State clearly that feature importance is not causal evidence.

Analysis expansion priorities:

- Interpret PR AUC relative to the 10% hotspot prevalence.
- Explain pooled PR AUC versus mean city PR AUC.
- Emphasize matched 5k logistic/RF comparison as the cleanest model contrast.
- Discuss climate-group heterogeneity as a main result, not a side note.
- Mention feature-importance evidence only as supplemental/non-causal.
- Strengthen validity/limitations language around sampled benchmark, LST versus human exposure, city-relative target, and spatial dependence.

Signal-shift diagnostic:

- Within-city RF hotspot F1 versus city-held-out RF PR AUC correlation is about 0.08.
- Within-city RF hotspot recall versus city-held-out RF recall@top10 correlation is about 0.03.
- Same-city learnability does not imply cross-city transferability.

Insertion note:

`[Insert evaluation-design signal-shift analysis here: compare city-level within-city random-forest F1/recall against city-held-out random-forest PR AUC/recall@top10, report the weak correlations from the presentation, and explain that same-city learnability does not imply cross-city transferability.]`

### 6. Discussion and Limitations

Main limitations:

- Sampled all-fold benchmark rather than exhaustive full-row scoring.
- City-relative hotspot target is useful for within-city screening but not an absolute heat-exposure threshold.
- Transfer performance is uneven across cities and climate groups.
- Feature contract is intentionally narrow; richer context features are only supplemental.
- Remote-sensing LST captures surface temperature, not direct human heat exposure.
- Spatial autocorrelation and city-specific land-form patterns remain challenges for generalization.

Validity discussion:

- City-held-out evaluation is the main transfer-validity strength.
- Within-city evaluation should be interpreted as same-city screening evidence.
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

- The project successfully built a reproducible 30-city, 30 m urban heat dataset and compared same-city hotspot screening with leakage-safe city-held-out transfer.
- Cross-city hotspot prediction is feasible but difficult.
- Random forest provides a modest aggregate gain in pooled PR AUC and top-decile recall, especially in hot-arid cities, while logistic regression remains competitive and steadier by mean city PR AUC.
- The best framing is a transferable screening framework with documented limits.

## Tables and Figures Section

Tables and figures should be placed after the main text to satisfy the assignment instruction not to mix them with prose.

See `docs/internal/report_development/final_report_planning.md` for full figure provenance and generation status.

Recommended main tables:

- Table 1. Data sources and constructed variables.
- Table 2. Final dataset summary by climate group.
- Table 3. Main city-held-out benchmark results.
- Table 4. RF minus logistic performance by climate group.

Recommended main figures:

- Figure 1. Study city locations.
- Figure 2. Dataset construction workflow.
- Figure 3. City-held-out evaluation design.
- Figure 4. Within-city and city-held-out results side by side.
- Figure 5. City-level signal shifts across evaluation designs.
- Figure 6. City-held-out benchmark metric comparison.
- Figure 7. City-level RF minus logistic transfer deltas.
- Figure 8. Absolute RF city PR AUC.
- Figure 9. Held-out Denver map example.

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

`[Insert appendix table here: add final dataset column table from docs/data_dictionary.md.]`

`[Insert appendix table here: add hyperparameter grid / retained run metadata for logistic and RF.]`

`[Insert reproducibility appendix here: add brief reproducibility note listing canonical repo entrypoints and retained artifact paths.]`
