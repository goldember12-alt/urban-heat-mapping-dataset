# Final Report Planning Handoff

This file is the continuity map for writing the STAT 5630 final report from `docs/report/`. A new chat should be able to read this file and the existing retained artifacts, then continue the writing pass without rediscovering the project. The older outline scaffold has been archived at `docs/report/archive/final_report_outline.md`.

## Current Report State

Existing report-facing files:

- `docs/report/cross_city_urban_heat_report.md`
  - A mature technical report draft created from retained repository artifacts.
  - Useful source material, but too comprehensive and technical for the course final report as-is.
  - Best used as content inventory and phrasing source.
- `docs/report/projectproposal.pdf`
  - Original proposal.
  - Contains useful background/source descriptions.
  - Drifts from completed project because it emphasizes Phoenix preliminary summaries and future-tense 30-city work.
- `docs/report/STAT5630 Slides-and-presentation--requirement-2026 (1).pdf`
  - Assignment instructions.
  - Requires title page, main text, tables/figures section, and appendix.
  - Main text limit: 15 pages for two-person project.
  - Tables and figures should be organized separately from main text.
- `docs/report/archive/final_report_outline.md`
  - Archived course-format outline and writing scaffold.

Important context:

- The final paper should not simply paste the existing technical report.
- The clean first writing pass should start with Background Information and Dataset Construction.
- The completed project is broader than the original proposal: it now includes a final 30-city dataset, within-city held-out results, city-held-out folds, retained logistic/RF benchmarks, signal-shift diagnostics, held-out maps, and transfer packaging.
- The active report narrative should follow the authoritative presentation PDFs in `docs/presentation_2026/`: `Urban Heat Transfer Prediction Presentation.pdf` and `Notes Readoff for Presentation.pdf`.
- Latest rendered PDF check:
  - `docs/report/stat5630_final_report_draft.pdf` renders successfully with title page, embedded figures, Tables and Figures section, and Appendix.
  - The latest rendered draft reflects the 2026-05-03 critique-guided revision pass: the all-city medium-scale spatial-alignment summary is now main Figure 7, and the selected Nashville/San Francisco spatial-alignment contrast is a single appendix figure.
  - The assignment's 15-page limit applies to **Main Text** only.
  - Current Main Text spans roughly pages 2-11, and Tables/Figures begin on page 12 after references, so the Main Text remains under the 15-page cap.
  - Render command currently uses 12 pt font and 1 inch margins; the PDF appears single-spaced under the Pandoc/XeLaTeX render path.
  - Do not treat the full-PDF page count as a violation unless the Main Text itself exceeds 15 pages.

## Presentation Narrative Anchor

Use the presentation PDFs as the report's narrative spine. The report should be a fuller written version of that story, not a city-held-out-only paper.

Slide-by-slide claims to preserve:

1. Slide 1 frames the project as cross-city urban heat hotspot prediction and explicitly signals two ways to evaluate hotspot prediction.
2. Slide 2 defines the research question, the 30-city 30 m dataset, the six first-pass predictors, the `hotspot_10pct` target, and the two validation designs: within-city held-out cells and city-held-out transfer.
3. Slide 3 compares logistic regression and random forest as two model forms using the same predictor contract: logistic is a global additive risk score, while random forest can capture nonlinear thresholds and interactions.
4. Slide 4 places within-city held-out and city-held-out transfer results side by side. Random forest clearly wins within-city hotspot precision, recall, and F1; city-held-out transfer is weaker and closer, with RF modestly ahead on pooled PR AUC and recall@top10 and logistic slightly ahead on mean city PR AUC.
5. Slide 5 is a core diagnostic, not an appendix afterthought. City-level within-city RF F1 correlates only about 0.08 with city-held-out RF PR AUC, and within-city RF recall correlates only about 0.03 with city-held-out RF recall@top10. Same-city learnability does not reliably predict transfer success.
6. Slide 6 uses Denver as a representative hot-arid held-out example. It shows predicted top-decile risk, true hotspot cells, and categorical errors; false positives and false negatives are spatially structured, indicating partial built-environment signal and missed city-specific detail.
7. Slide 7's takeaway is that basic environmental and built-environment factors contain real hotspot signal, but signal strength and model advantage depend on validation design.

## Report Narrative To Preserve

Main story:

1. Urban heat varies locally and matters for planning/public health.
2. The project asks whether basic environmental and built-environment features can identify hotspot cells, and how the answer changes across validation designs.
3. This project builds a standardized 30 m dataset for 30 U.S. cities.
4. The target is `hotspot_10pct`, a within-city top-decile ECOSTRESS LST label.
5. The report compares within-city held-out evaluation with whole-city holdout transfer.
6. Within-city held-out evaluation shows random forest clearly outperforming logistic regression on hotspot precision, recall, and F1.
7. City-held-out transfer is weaker, closer between models, and more heterogeneous; random forest modestly improves pooled PR AUC and recall@top10 while logistic remains slightly stronger on mean city PR AUC.
8. The defensible conclusion is that the project separates learnable same-city hotspot structure from cross-city transferability.

Avoid these narrative traps:

- Do not describe sampled benchmark runs as full exhaustive 71.4M-row benchmark results.
- Do not present Phoenix proposal figures as final project evidence.
- Do not imply `hotspot_10pct` is an absolute national heat-risk threshold.
- Do not let within-city held-out results replace the stricter city-held-out transfer benchmark.
- Do not collapse within-city precision/recall/F1 and city-held-out PR AUC/recall@top10 into one direct metric leaderboard.
- Do not let supplemental HGB, climate-interaction, or richer-feature results replace the two-design logistic/RF comparison.

## Assignment Formatting Interpretation

The assignment states:

- Title Page: project title and names of all collaborators.
- Three parts: Main Text; Tables and Figures; Appendix.
- For Main Text only: single-spaced, 12 pt, 1 inch margins, limited to 10 pages for a one-person project and 15 pages for a two-person project.
- Tables and figures should be organized in their corresponding parts and not mixed with main text.

Working interpretation:

- The title page, Tables and Figures section, and Appendix are outside the 15-page Main Text limit.
- It is acceptable for the complete PDF to exceed 15 pages if the Main Text stays under 15 pages.
- The current report can afford a substantial main-text expansion, especially in Background, Dataset Construction, Methodology, and Analysis.

Current render command:

```powershell
C:\Users\golde\AppData\Local\Programs\Quarto\bin\tools\pandoc.exe stat5630_final_report_draft.md --from markdown+pipe_tables+raw_tex+link_attributes-implicit_figures --to pdf --standalone --pdf-engine=xelatex -V geometry:margin=1in -V fontsize=12pt -V papersize=letter -o stat5630_final_report_draft.pdf
```

## High-Value Expansion Plan

The next writing pass should use the available Main Text space deliberately. The goal is not more words everywhere; it is a more rigorous paper with a clearer research gap and stronger methods/results interpretation.

### Highest Priority: Background And Research Gap

Target length:

- Expand Background Information by at least 1-2 pages of Main Text.

Purpose:

- Establish why urban heat mapping matters.
- Explain what thermal remote sensing and land-surface-temperature studies have already shown.
- Explain why land cover, imperviousness, vegetation, elevation, and water proximity are plausible predictors.
- Establish the research gap: many studies are single-city, descriptive, correlation-focused, or within-city; fewer separate same-city hotspot screening from fully unseen-city transfer under a leakage-safe evaluation design.

Recommended structure:

1. Urban heat as a local exposure and planning problem.
2. Thermal remote sensing and LST as a practical way to observe fine-scale surface heat.
3. Existing evidence that impervious surfaces, vegetation/NDVI, water, terrain, and land cover shape LST.
4. Limitations of common study designs:
   - single-city focus.
   - descriptive maps or simple correlations.
   - random row/cell splits that can overstate performance under spatial autocorrelation.
5. This project's gap:
   - standardized cross-city dataset.
   - city-relative hotspot target.
   - within-city held-out validation.
   - entire-city held-out validation.
   - explicit contrast between the two validation designs.

Candidate reference directions:

- Voogt and Oke (2003), *Thermal remote sensing of urban climates*, for the foundation of urban thermal remote sensing and the critique that urban thermal studies often remain descriptive or correlation-focused.
- Weng, Lu, and Schubring (2004) or Yuan and Bauer (2007), for classic Landsat/LST work linking LST with vegetation and impervious surface indicators.
- NASA Earthdata / ECOSTRESS documentation for the role of ECOSTRESS LST and the distinction between LST and air temperature.
- AppEEARS / LP DAAC documentation for data acquisition and spatial/temporal subsetting.
- Spatial validation literature, such as Roberts et al. (2017) or Meyer et al. (2018), for why random cross-validation can be overoptimistic when spatial structure is present.

The next chat should verify exact citation details before writing final reference text. Use primary/official sources where possible.

### Second Priority: Dataset Construction Detail

Target expansion:

- Add about 1-2 pages beyond the current dataset-construction prose if space permits.

Add detail on:

- City selection logic and climate grouping:
  - why 30 cities.
  - why hot-arid, hot-humid, and mild-cool groups are useful for transfer interpretation.
- Study-area definition:
  - Census urban area containing the city center.
  - 2 km buffer.
  - preserved core urban geometry.
  - why this creates consistent but city-specific study regions.
- Grid construction:
  - local UTM CRS.
  - 30 m analytic unit.
  - why alignment to a master grid matters.
- Source processing:
  - raster predictors aligned/resampled to grid.
  - vector hydrography converted to distance-to-water.
  - NDVI and ECOSTRESS summarized over May-August.
  - valid ECOSTRESS pass count and row filtering.
- Target construction:
  - city-specific 90th percentile after filtering.
  - why recomputing after filtering matters.
  - why this supports cross-climate comparison without implying equal absolute thermal severity.
- Data quality:
  - final audit row count.
  - city/climate summary.
  - low missingness if a concise missingness statement is added.

Do not turn this into a code walkthrough. Keep it methodological and reproducible.

### Third Priority: Two-Design Methodology

The report should distinguish two validation concepts:

- **Within-city held-out cells:** same-city screening/interpolation.
  - Cities are represented during model development.
  - Models are evaluated on held-out cells from those same cities.
  - The verified 70/30 result reports hotspot precision, recall, and F1.
- **City-held-out transfer:** stricter unseen-city transfer.
  - This remains the canonical benchmark for transfer to unseen cities.
  - Emphasize grouped city folds and train-city-only preprocessing/tuning.

Suggested placement:

- Main Method section:
  - Introduce both validation designs as first-class methods.
  - Keep city-held-out validation as the stricter transfer benchmark with the most leakage-control detail.
  - Add an outward-facing insertion bracket for fuller within-city split details if the current source lacks them.
- Results/Discussion:
  - Present within-city results first, then city-held-out transfer, then the signal-shift comparison.
  - Emphasize that within-city success does not establish cross-city transfer.

### Fourth Priority: Analysis And Results Rigor

Potential additions:

- Interpret PR AUC against the 10% prevalence context.
- Explain why pooled PR AUC and mean city PR AUC differ.
- Give the matched 5k logistic/RF comparison priority over unmatched 20k logistic vs RF.
- Add a clearer paragraph on climate heterogeneity:
  - hot-arid RF gains.
  - hot-humid/mild-cool logistic steadiness.
  - implications for one-size-fits-all transfer models.
- Add a concise "what the model appears to use" paragraph:
  - feature-importance artifacts suggest vegetation, imperviousness, climate group, land cover, and elevation matter.
  - keep this explicitly non-causal.
- Add a stronger limitations/validity paragraph:
  - sampled benchmark.
  - surface temperature rather than air temperature/human exposure.
  - city-relative label.
  - spatial dependence.
  - selected 30-city sample.

### Lower Priority Unless Space Remains

- More details on supplemental HGB, climate-interaction, and richer-feature checkpoints.
- Full transfer-package/inference workflow.
- Long appendix commentary.

These are useful but not central to the course report's clearest argument.

## Key Completed Dataset Facts

Canonical final dataset:

- `data_processed/final/final_dataset.parquet`
- `data_processed/final/final_dataset.csv`

Audit artifacts:

- `data_processed/modeling/final_dataset_audit.md`
- `data_processed/modeling/final_dataset_audit_summary.json`
- `data_processed/modeling/final_dataset_city_summary.csv`
- `data_processed/modeling/final_dataset_feature_missingness.csv`
- `data_processed/modeling/final_dataset_feature_missingness_by_city.csv`

Important audited facts:

- 30 cities.
- 71,394,894 rows.
- 17 final dataset columns.
- One row per 30 m grid cell per city.
- Binary target validation for `hotspot_10pct` passed.
- Positive cells: 7,139,588.
- Negative cells: 64,255,306.
- Target prevalence is approximately 10% by construction.

Climate groups:

- hot-arid: 10 cities.
- hot-humid: 10 cities.
- mild-cool: 10 cities.

Final assembly rules:

- Drop open-water cells where `land_cover_class == 11` when land cover is available.
- Drop rows with `n_valid_ecostress_passes < 3` when LST is available.
- Recompute `hotspot_10pct` within each city after filtering.

Headline model features:

- `impervious_pct`
- `land_cover_class`
- `elevation_m`
- `dist_to_water_m`
- `ndvi_median_may_aug`
- `climate_group`

Excluded from first-pass predictive features:

- `hotspot_10pct`
- `lst_median_may_aug`
- `n_valid_ecostress_passes`
- `cell_id`
- `city_id`
- `city_name`
- `centroid_lon`
- `centroid_lat`

## Key Benchmark Facts

Primary benchmark reference:

- `outputs/modeling/reporting/cross_city_benchmark_report.md`
- `outputs/modeling/reporting/tables/cross_city_benchmark_report_benchmark_table.csv`
- `outputs/modeling/reporting/tables/cross_city_benchmark_report_city_error_comparison.csv`
- `outputs/modeling/reporting/tables/cross_city_benchmark_report_city_error_by_climate.csv`

Evaluation design:

- Five deterministic outer folds.
- Six held-out cities per fold.
- Split by `city_id`, not row/cell.
- All preprocessing, imputation, encoding, scaling, feature engineering inside the model pipeline, and hyperparameter tuning are fit only on training-city rows.

Metrics:

- Primary: PR AUC.
- Supporting:
  - mean city PR AUC.
  - recall at top 10% predicted risk.
  - calibration tables, currently secondary.

Retained main comparison:

| Model checkpoint | Rows per city | Pooled PR AUC | Mean city PR AUC | Recall at top 10% | Runtime |
| --- | ---: | ---: | ---: | ---: | ---: |
| Impervious-only baseline | all available | 0.1351 | 0.1519 | 0.1858 | n/a |
| Land-cover-only baseline | all available | 0.1353 | 0.1479 | 0.1672 | n/a |
| Logistic SAGA retained 5k | 5,000 | 0.1421 | 0.1803 | 0.1647 | 35.6 min |
| Logistic SAGA retained 20k | 20,000 | 0.1457 | 0.1796 | 0.1709 | 156.6 min |
| Random forest frontier | 5,000 | 0.1486 | 0.1781 | 0.1961 | 97.2 min |

Interpretation:

- Learned models beat simple baselines on pooled PR AUC.
- RF frontier beats logistic 5k on pooled PR AUC and recall at top 10%.
- Logistic 5k slightly beats RF frontier on mean city PR AUC.
- RF gains are concentrated, especially in hot-arid cities.
- The retained benchmark is sampled all-fold, not exhaustive all-row scoring.

Climate-group deltas for RF frontier minus logistic 5k:

| Climate group | Mean PR AUC delta | Mean recall-at-top-10% delta |
| --- | ---: | ---: |
| hot-arid | +0.0336 | +0.0762 |
| hot-humid | -0.0123 | -0.0164 |
| mild-cool | -0.0281 | -0.0280 |

## Existing Report Figures

These files already exist under `docs/report/figures/` and can be referenced from report markdown with paths like `figures/study_city_points.png`.

### Figure: Study City Locations

- File: `docs/report/figures/study_city_points.png`
- Source/provenance: copied from `figures/data_processing/reference/study_city_points.png`.
- Use in report: Background or Dataset Construction.
- Message: Shows the 30 benchmark cities across the U.S. and supports the climate-group/cross-city framing.
- Status: Ready.
- Caption direction: Emphasize broad U.S. coverage and three climate groups, not exact cartographic precision.

### Figure: Workflow Overview

- File: `docs/report/figures/workflow_overview.svg`
- Source/provenance: report-specific schematic created for `cross_city_urban_heat_report.md`.
- Use in report: Dataset Construction or Methods.
- Message: Study-area construction, 30 m grids, aligned feature assembly, final dataset, audit/folds, modeling.
- Status: Ready.
- Caption direction: This is an end-to-end data and modeling lifecycle figure.

### Figure: City-Held-Out Evaluation Design

- File: `docs/report/figures/evaluation_design.svg`
- Source/provenance: report-specific schematic created for `cross_city_urban_heat_report.md`.
- Use in report: Model and Method.
- Message: Each fold holds out six entire cities and trains on the remaining 24; preprocessing and tuning are training-city only.
- Status: Ready.
- Caption direction: This is the central leakage-safe benchmark design.

### Figure: Within-City and City-Held-Out Results Side by Side

- File: `docs/report/figures/within_city_vs_transfer_results.png`
- Source/provenance: copied from `figures/presentation/within_city_vs_transfer_results.png`.
- Use in report: Analysis and Results.
- Message: Slide 4 comparison: RF dominates within-city precision/recall/F1, while city-held-out transfer is weaker and closer.
- Status: Ready.
- Caption direction: Compare validation-design patterns, not raw metric magnitudes across panels. State that the right-panel AUC values are PR AUC / average precision, not ROC AUC; the no-skill reference is the `0.10` hotspot prevalence, not `0.50`.
- Label/score sanity check: `docs/report/tables/label_score_sanity_check.csv` recomputes original-score and inverted-score metrics from retained held-out predictions. Original RF AP is `0.1486` versus `0.0752` with inverted scores, and original RF ROC AUC is `0.6214` versus `0.3786` inverted, so the saved transfer scores are not behaving like flipped labels or flipped predicted probabilities.

### Figure: City-Level Signal Shifts Across Evaluation Designs

- File: `docs/report/figures/city_signal_transfer_relationship_labeled.png`
- Source/provenance: labeled report copy derived from the city signal transfer relationship figure.
- Use in report: Analysis and Results.
- Message: Slide 5 diagnostic: within-city RF F1 has about 0.08 correlation with transfer RF PR AUC, and within-city RF recall has about 0.03 correlation with transfer RF recall@top10.
- Status: Ready.
- Caption direction: Same-city learnability does not reliably rank transfer success.

### Figure: Benchmark Metrics

- File: `docs/report/figures/benchmark_metrics.png`
- Source/provenance: copied from `figures/modeling/reporting/cross_city_benchmark_report_benchmark_metrics.png`.
- Use in report: Analysis and Results.
- Message: Compares retained city-held-out transfer metrics across simple baselines, logistic checkpoints, and RF.
- Status: Ready.
- Caption direction: State the sampled rows-per-city caveat and identify the matched 5k logistic/RF comparison.

### Figure: City Metric Deltas

- File: `docs/report/figures/city_metric_deltas.png`
- Source/provenance: copied from `figures/modeling/reporting/cross_city_benchmark_report_city_metric_deltas.png`.
- Use in report: Analysis and Results.
- Message: RF minus logistic performance is uneven by city and climate group.
- Status: Ready.
- Caption direction: Use this to explain why pooled and mean-city results differ.

### Figure: Held-Out Denver Map Example

- File: `docs/report/figures/heldout_denver_map_focus.png`
- Source/provenance: copied from `figures/presentation/heldout_denver_map_focus.png`.
- Use in report: Analysis and Results or Appendix.
- Message: Representative hot-arid held-out-city prediction/true/error spatial example.
- Status: Ready.
- Caption direction: State that false positives and false negatives are spatially organized, suggesting partial built-environment signal and missed city-specific detail.

### Figure: Feature Importance Ranked Summary

- File: `docs/report/figures/feature_importance_ranked_summary.png`
- Source/provenance: copied from `figures/modeling/supplemental/feature_importance/feature_importance_ranked_summary.png`.
- Use in report: Appendix or brief Results support.
- Message: Vegetation, imperviousness, climate group, land cover, and elevation are important transferable signals.
- Status: Ready.
- Caption direction: Label as supplemental interpretation and non-causal.

### Figure: Within-City Versus Cross-City Gap

- File: `docs/report/figures/within_vs_cross_gap.png`
- Source/provenance: copied from `figures/modeling/supplemental/within_city_all_cities/within_city_all_cities_within_vs_cross_gap.png`.
- Use in report: Appendix or Limitations.
- Message: Within-city splits are much easier and would overstate transfer performance.
- Status: Ready.
- Caption direction: Label as supplemental/easier diagnostic, not canonical benchmark.

## Visual, Table, And Appendix Improvement Audit

2026-05-03 audit scope:

- Current draft uses 6 main figures, 6 main tables, 4 appendix tables, and 5 appendix figures.
- The available visual inventory is much larger than the report currently uses: `figures/` contains 168 PNGs and 18 SVGs.
- The strongest underused visual families are:
  - all-city spatial-alignment maps and metrics under `figures/modeling/supplemental/spatial_alignment_all_cities/` and `outputs/modeling/supplemental/spatial_alignment_all_cities/`;
  - all-city within-city versus cross-city diagnostics under `figures/modeling/supplemental/within_city_all_cities/`;
  - 29 completed city-level data-processing map/summary figure sets under `figures/data_processing/city_summaries/` plus one empty/error Boston report folder noted in the batch summary;
  - presentation-grade result schematics under `figures/presentation/`.
- Current main Tables 4-6 are useful for exact values, but they visually slow down the Results section. Prefer moving detailed heterogeneity tables to the appendix and using one clearer figure in the main tables/figures section.

2026-05-03 first-pass implementation decisions:

- Generated `docs/report/figures/spatial_alignment_medium_summary.png` from the all-city spatial-alignment metrics table using medium-scale (`300 m`) rows only.
- Kept Tables 1-3 as the core tables in the Tables and Figures section.
- Moved the former main Tables 4-6 to Appendix Tables A5-A7 so detailed heterogeneity values remain available without slowing the main figure/table flow.
- Integrated the existing within-city versus cross-city gap figure as Appendix Figure A6, with language that it is supplemental and easier than the canonical city-held-out transfer benchmark.
- Integrated the all-city medium-scale spatial-alignment summary as Appendix Figure A7 and kept interpretation cautious: partial broad spatial alignment, wide city-level variation, and no climate-group pattern claim.
- Copied the Nashville and San Francisco medium-scale spatial-alignment maps into `docs/report/figures/` and used them as Appendix Figure A8, a selected high/low contrast rather than a main narrative replacement.
- Updated `src.report_artifacts` so `C:\Users\golde\.venvs\STAT5630_FinalProject_DataProcessing\Scripts\python.exe -m src.run_report_artifacts` regenerates the new summary figure and report-facing copied map/diagnostic figures.

2026-05-03 critique-guided revision decisions:

- Tightened the active report draft using `docs/internal/report_development/stat5630_draft_critical_review.md` as an actionable checklist rather than a broad rewrite request.
- Defined same-city screening, exact-cell transfer, and broad spatial placement earlier in the Background.
- Clarified AP/PR AUC wording in Methods and moved the defensive flipped-score sanity-check language out of the Figure 4 caption.
- Promoted former Appendix Figure A7 to main Figure 7 because it is central to the spatial-alignment result.
- Replaced the former split Appendix Figure A8 with `docs/report/figures/selected_spatial_alignment_map_contrast.png`, generated reproducibly by `src.run_report_artifacts`.
- Added `docs/internal/report_development/stat5630_revision_pass_notes.md` as the focused revision-pass record.

### Highest-Value Visual Additions

1. Add an all-city spatial-alignment summary figure.

- Proposed file: `docs/report/figures/spatial_alignment_medium_summary.png`.
- Source data: `outputs/modeling/supplemental/spatial_alignment_all_cities/tables/spatial_alignment_metrics_all_cities.csv`.
- Suggested design: medium-scale (`300 m`) scatter or lollipop figure with `spearman_surface_corr` on one axis and `observed_mass_captured` or `top_region_overlap_fraction` on the other, colored by climate group and labeled only for the strongest/weakest cities.
- Why it helps: the current text discusses all-city spatial alignment, but the report only visualizes Denver. This figure would make the supplemental spatial-placement claim concrete while keeping the sampled PR AUC / recall benchmark primary.
- Values to preserve: medium-scale means are Spearman `0.2713`, top-region overlap `0.1353`, and observed hotspot mass captured `0.2114`; all reconstruction statuses are `ok`.
- Interpretation guardrail: show variation and partial alignment, not "strong transfer." Do not claim climate-group transfer patterns from this figure.
- Priority: Very high.

2. Add a high-versus-low spatial-alignment map contrast.

- Existing candidate files:
  - `figures/modeling/supplemental/spatial_alignment_all_cities/nashville_city20_random_forest_medium_surface_alignment.png`
  - `figures/modeling/supplemental/spatial_alignment_all_cities/san_francisco_city23_random_forest_medium_surface_alignment.png`
  - optional additional contrasts: `portland_city22...` and `las_vegas_city03...`.
- Suggested use: appendix figure, or main Figure 7 only if the Results section adds one short paragraph on spatial-placement heterogeneity.
- Why it helps: this is visually compelling and supports the new distinction between exact-cell retrieval and broader spatial placement.
- Interpretation guardrail: describe as supplemental full-city spatial diagnostic maps generated from retained RF held-out folds, not a new benchmark and not operational deployment evidence.
- Priority: High.

3. Use the existing within-city versus cross-city gap figure.

- Existing file: `docs/report/figures/within_vs_cross_gap.png`.
- Source data: `outputs/modeling/supplemental/within_city_all_cities/tables/within_city_all_cities_cross_city_gap_by_city.csv`.
- Suggested use: replace or augment one current heterogeneity table in the main tables/figures section, or add as Appendix Figure A6.
- Why it helps: this single figure visualizes the project thesis directly: within-city evaluation is much easier than city-held-out transfer. It is a stronger visual than another table of metric deltas.
- Values to preserve: for random forest, mean within-city PR AUC is `0.4213`, mean cross-city PR AUC is `0.1781`, and mean PR AUC gap is `0.2432`; mean recall gap is `0.2202`.
- Interpretation guardrail: these within-city random-split results are supplemental and easier than the canonical city-held-out benchmark.
- Priority: High.

4. Build a city hotspot-map montage.

- Candidate source files: `figures/data_processing/city_summaries/*/*_hotspot_map.png`.
- Suggested design: 2 x 3 or 3 x 3 montage of representative city hotspot maps, for example Denver, Nashville, San Francisco, Las Vegas, Portland, and El Paso.
- Why it helps: it shows that the target is spatially structured and city-specific before any model is introduced. This would make the dataset contribution more vivid than row-count tables alone.
- Suggested placement: appendix, or a compact Figure 2 companion if the Dataset Construction section needs visual lift.
- Caveat: Boston's city data-processing report failed in the batch summary, so use known completed city maps and avoid implying all 30 city-summary maps rendered successfully.
- Priority: Medium high.

5. Replace result table density with one compact heterogeneity figure.

- Existing candidate: `docs/report/figures/city_metric_deltas.png`.
- Possible new figure: a cleaner "RF-minus-logistic by city and metric" dot/lollipop chart that combines climate grouping with PR AUC and recall deltas, then move Tables 4-6 to appendix.
- Why it helps: the paper currently repeats the heterogeneity story across Tables 4-6 plus Appendix Figures A4-A5. A polished figure can carry the story while tables retain exact audit values.
- Priority: Medium.

### Lower-Priority Or Appendix-Only Visuals

- `figures/modeling/reporting/cross_city_benchmark_report_runtime_vs_pr_auc.png`: useful for computational tradeoff, but not central to the final course-report story. Keep appendix-only if used.
- `figures/presentation/evaluation_metric_comparison_table.png`: visually attractive, but the current Figure 4 already carries the validation-design contrast and the draft now has exact metric tables.
- `figures/modeling/heldout_city_maps/atlanta_heldout_map_triptych.png` and `detroit_heldout_map_triptych.png`: useful as additional appendix examples, but Denver is enough for the main narrative unless a multi-city map comparison replaces the single Denver figure.
- City-level `key_correlations`, `key_distributions`, and `land_cover_composition` figures: useful for QA and appendix exploration, but too city-specific for the main report unless turned into a synthesized multi-city figure.

### Recommended Table And Appendix Rebalance

- Keep Table 1 and Table 2 in the main tables/figures section because they define data sources and dataset scale.
- Keep Table 3 as the main benchmark table because exact metric values matter.
- Move Tables 4-6 to appendix if adding the spatial-alignment summary figure and within-vs-cross gap figure. Their claims can be summarized in prose and supported visually.
- Keep Appendix Table A1 and A2 for reproducibility.
- Consider compressing Appendix Table A3 into prose if the appendix gets visually crowded; the model specification is useful but less visually important than spatial diagnostics.
- Add new appendix entries only if they have a direct narrative job:
  - A6: within-city versus cross-city gap;
  - A7: spatial-alignment medium-scale summary;
  - A8: selected high/low spatial-alignment maps or hotspot-map montage.

### Implementation Notes For A Future Visual Pass

- Copy any reused existing figure into `docs/report/figures/` before referencing it from the draft.
- Generate new report-specific figures from source tables rather than editing existing PNGs by hand.
- Use the standard interpreter:
  - `C:\Users\golde\.venvs\STAT5630_FinalProject_DataProcessing\Scripts\python.exe -m ...`
- Good targets for generation code:
  - add report-only plot helpers to `src/report_artifacts.py` if the figure should be reproducible with `src.run_report_artifacts`;
  - add a separate small report-visual CLI only if the spatial-alignment figure depends on supplemental outputs outside the existing report-artifact path.
- After adding figures, rerender `docs/report/stat5630_final_report_draft.pdf` and inspect the figure pages for label readability.

## New Tables/Figures To Generate

These should be generated before or during the first writing pass so the dataset-construction section can present completed-project evidence instead of proposal-era Phoenix evidence.

### New Table 1: Data Sources and Constructed Variables

- Proposed file: `docs/report/tables/data_sources_variables.csv` or directly written as markdown in the Tables/Figures section.
- Inputs:
  - `docs/data_dictionary.md`
  - `docs/workflow.md`
  - proposal source descriptions.
- Columns:
  - Source
  - Raw product / layer
  - Constructed final variable(s)
  - Spatial role
  - Used in headline model? yes/no
- Rows:
  - Census urban areas: study area/core geometry.
  - NLCD land cover: `land_cover_class`.
  - NLCD impervious: `impervious_pct`.
  - USGS 3DEP DEM: `elevation_m`.
  - NHDPlus HR: `dist_to_water_m`.
  - Landsat/AppEEARS NDVI: `ndvi_median_may_aug`.
  - ECOSTRESS/AppEEARS LST: `lst_median_may_aug`, `n_valid_ecostress_passes`, `hotspot_10pct`.
- Priority: High.
- Status: Generated at `docs/report/tables/data_sources_variables.csv` by `src.run_report_artifacts`.

### New Table 2: Final Dataset Summary By Climate Group

- Proposed file: `docs/report/tables/final_dataset_by_climate_group.csv`.
- Inputs:
  - `data_processed/modeling/final_dataset_city_summary.csv`.
- Metrics:
  - city count.
  - total rows.
  - total hotspot positives.
  - hotspot prevalence.
  - minimum city row count.
  - median city row count.
  - maximum city row count.
  - median `n_valid_ecostress_passes` if useful.
- Priority: High.
- Status: Generated at `docs/report/tables/final_dataset_by_climate_group.csv` by `src.run_report_artifacts`.
- Notes:
  - This is likely the most useful new dataset-construction table.

### New Figure: City Row Counts By Climate Group

- Proposed file: `docs/report/figures/final_dataset_city_row_counts.png`.
- Inputs:
  - `data_processed/modeling/final_dataset_city_summary.csv`.
- Design:
  - Horizontal bar chart.
  - City names on y-axis.
  - Row count on x-axis, possibly in millions.
  - Color by climate group.
  - Sort by climate group then row count or by row count descending.
- Message:
  - Study-area extents differ substantially; the dataset is not uniformly sampled by city.
- Priority: Medium.
- Status: Generated at `docs/report/figures/final_dataset_city_row_counts.png` by `src.run_report_artifacts`.
- Caution:
  - Use as appendix if main report gets crowded.

### New Figure: Dataset Construction / Variable Flow

- Proposed file: `docs/report/figures/dataset_variable_flow.svg` or `.png`.
- Inputs:
  - `docs/workflow.md`
  - `docs/data_dictionary.md`.
- Design:
  - Similar to workflow overview but more data-source specific.
  - Public source layers on left, 30 m grid alignment in center, final model features and target on right.
- Message:
  - Makes data construction legible for readers who do not care about pipeline entrypoints.
- Priority: Medium.
- Status: Optional; existing `workflow_overview.svg` may be enough.

### New Table/Figure: Missingness Summary

- Proposed file:
  - `docs/report/tables/final_dataset_feature_missingness.csv`
  - optional `docs/report/figures/final_dataset_missingness.png`
- Inputs:
  - `data_processed/modeling/final_dataset_feature_missingness.csv`.
- Message:
  - Modeling features are mostly complete; residual missingness is small.
- Priority: Low to Medium.
- Status: Need to decide.
- Suggested use:
  - Appendix unless the dataset section needs extra evidence of data quality.

### New Table: Final Dataset Columns

- Proposed file: appendix table copied/summarized from `docs/data_dictionary.md`.
- Inputs:
  - `docs/data_dictionary.md`.
- Message:
  - Reproducible schema definition.
- Priority: Medium for appendix.
- Status: Generated at `docs/report/tables/final_dataset_columns.csv` by `src.run_report_artifacts` and included as Appendix Table A1.

### New Appendix Table: Retained Model Run Metadata

- File: `docs/report/tables/retained_model_run_metadata.csv`.
- Inputs:
  - retained logistic SAGA 5k `run_metadata.json` and `best_params_by_fold.csv`.
  - retained random-forest frontier `run_metadata.json` and `best_params_by_fold.csv`.
  - `outputs/modeling/reporting/tables/cross_city_benchmark_report_benchmark_table.csv`.
- Message:
  - Compact reproducibility metadata for the retained headline model runs, including preset, sample cap, folds, inner-CV setup, search size, scoring metric, retained metrics, and selected-parameter summary.
- Priority: Medium for appendix.
- Status: Generated by `src.run_report_artifacts` and included as Appendix Table A2.

## Existing Tables To Reuse

Retained benchmark table:

- Source: `outputs/modeling/reporting/tables/cross_city_benchmark_report_benchmark_table.csv`
- Use as main Table 3, simplified to the five rows listed in `docs/report/archive/final_report_outline.md`.
- Report-facing generated file: `docs/report/tables/benchmark_metrics.csv`.

Climate delta table:

- Source: `outputs/modeling/reporting/tables/cross_city_benchmark_report_city_error_by_climate.csv`
- Use as main Table 4 or in appendix.
- Report-facing generated file: `docs/report/tables/rf_vs_logistic_by_climate.csv`.

City-level comparison table:

- Source: `outputs/modeling/reporting/tables/cross_city_benchmark_report_city_error_comparison.csv`
- Use in appendix, not main text unless space allows.

Final dataset city summary:

- Source: `data_processed/modeling/final_dataset_city_summary.csv`
- Use for new dataset summary table and row-count figure.

Feature missingness:

- Source: `data_processed/modeling/final_dataset_feature_missingness.csv`
- Use for appendix data-quality table if needed.

## Outward-Facing Insertion Notes

Use visible placeholders in the draft so gaps are intentional and easy to fill.

Recommended placeholders:

- `[Insert related-work extension here: add 1-2 paragraphs of related-work context and citations on urban heat mapping, remotely sensed LST, or transfer/generalization in spatial ML.]`
- `[Insert within-city held-out design details and results here: describe the verified 70/30 within-city evaluation, report logistic-versus-random-forest precision, recall, and F1, and explain that this setting measures same-city hotspot screening rather than unseen-city transfer.]`
- `[Insert evaluation-design signal-shift analysis here: compare city-level within-city random-forest F1/recall against city-held-out random-forest PR AUC/recall@top10, report the weak correlations from the presentation, and explain that same-city learnability does not imply cross-city transferability.]`
- `[Insert final discussion polish here: add any project-management, domain, or validity caveats that clarify the two-design interpretation without changing retained model results.]`

Suggested partner responsibilities:

- Related work and citations.
- Course-language statistical explanation.
- Any supplemental analysis needed to complete the two-design interpretation.
- Final discussion polish.
- Appendix/code-output curation.

## First Writing Pass Plan

Recommended next step:

1. Generate the high-priority new table(s):
   - data sources / constructed variables.
   - final dataset summary by climate group.
2. Optionally generate city row-count figure.
3. Draft the first main-text sections:
   - Background Information.
   - Research Questions.
   - Dataset Construction.
   - First-pass draft now lives at `docs/report/stat5630_final_report_draft.md`.
4. Keep placeholders for partner-owned literature/statistical explanation.
5. Do not yet over-polish Results; the existing technical report already contains results prose that can be adapted later.

Tone target:

- Clear course report, not a repo audit.
- Concrete and quantitative, but not overloaded with implementation details.
- Honest about sampled benchmark limits.

## Source Files To Read For Next Writing Pass

Minimum read set:

- `docs/report/archive/final_report_outline.md`
- `docs/internal/report_development/final_report_planning.md`
- `docs/report/cross_city_urban_heat_report.md`
- `docs/data_dictionary.md`
- `docs/workflow.md`
- `data_processed/modeling/final_dataset_audit.md`
- `data_processed/modeling/final_dataset_city_summary.csv`

Optional read set:

- `docs/modeling_plan.md`
- `outputs/modeling/reporting/cross_city_benchmark_report.md`
- `outputs/modeling/reporting/tables/cross_city_benchmark_report_benchmark_table.csv`
- `outputs/modeling/supplemental/feature_importance/feature_importance_summary.md`
- `outputs/modeling/reporting/heldout_city_maps/heldout_city_maps.md`

Proposal source:

- `docs/report/projectproposal.pdf`
- Use for background/source descriptions only; do not carry forward Phoenix preliminary results as headline final evidence.

Assignment source:

- `docs/report/STAT5630 Slides-and-presentation--requirement-2026 (1).pdf`
- Use for report structure and page/format constraints.
