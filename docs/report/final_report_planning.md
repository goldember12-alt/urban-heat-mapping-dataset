# Final Report Planning Handoff

This file is the continuity map for writing the STAT 5630 final report from `docs/report/`. A new chat should be able to read this file, `final_report_outline.md`, and the existing retained artifacts, then continue the writing pass without rediscovering the project.

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
- `docs/report/final_report_outline.md`
  - New course-format outline and writing scaffold.

Important context:

- The final paper should not simply paste the existing technical report.
- The clean first writing pass should start with Background Information and Dataset Construction.
- The completed project is broader than the original proposal: it now includes a final 30-city dataset, city-held-out folds, retained logistic/RF benchmarks, supplemental modeling checks, held-out maps, and transfer packaging.
- Latest rendered PDF check:
  - `docs/report/stat5630_final_report_draft.pdf` renders successfully with title page, embedded figures, Tables and Figures section, and Appendix.
  - The latest rendered draft is 26 pages after adding stricter results framing, variability tables, and appendix support.
  - The assignment's 15-page limit applies to **Main Text** only.
  - Current Main Text spans roughly pages 2-10, and Tables/Figures begin after references, so the Main Text remains under the 15-page cap.
  - Render command currently uses 12 pt font and 1 inch margins; the PDF appears single-spaced under the Pandoc/XeLaTeX render path.
  - Do not treat the 18-page total PDF as a violation unless the Main Text itself exceeds 15 pages.

## Report Narrative To Preserve

Main story:

1. Urban heat varies locally and matters for planning/public health.
2. Many easier modeling setups do not test whether predictions transfer to unseen cities.
3. This project builds a standardized 30 m dataset for 30 U.S. cities.
4. The target is `hotspot_10pct`, a within-city top-decile ECOSTRESS LST label.
5. The benchmark holds out entire cities, with all preprocessing and tuning fit only on training cities.
6. The retained predictors show limited but real transferable ranking signal, strongest in hot-arid cities.
7. Random forest improves pooled PR AUC and recall at top 10% relative to matched logistic regression, but gains over simple baselines are modest and city-level wins are heterogeneous.
8. The defensible conclusion is "transfer-screening benchmark with clear limits," not "robust all-city hotspot identifier" or "deployment-ready heat-risk classifier."

Avoid these narrative traps:

- Do not describe sampled benchmark runs as full exhaustive 71.4M-row benchmark results.
- Do not present Phoenix proposal figures as final project evidence.
- Do not imply `hotspot_10pct` is an absolute national heat-risk threshold.
- Do not use partner-provided easier-split results as the headline benchmark.
- Do not let supplemental HGB, climate-interaction, richer-feature, or within-city results replace the retained logistic/RF comparison.

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
- Establish the research gap: many studies are single-city, descriptive, correlation-focused, or within-city; fewer ask whether hotspot prediction transfers to fully unseen cities under a leakage-safe evaluation design.

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
   - entire-city held-out validation.
   - explicit contrast with easier within-city held-out validation that partner will describe.

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

### Third Priority: Methodology Split Between Authors

The report should distinguish two validation concepts:

- **Our side / headline method:** whole-city held-out validation.
  - This remains the canonical benchmark for transfer to unseen cities.
  - Emphasize grouped city folds and train-city-only preprocessing/tuning.
- **Partner side:** within-city held-out validation.
  - Partner should describe this as a complementary/easier diagnostic, not the headline transfer benchmark.
  - It can help show how performance changes when train/test data come from the same city.
  - It should be clearly labeled as not equivalent to unseen-city transfer.

Suggested placement:

- Main Method section:
  - Put whole-city held-out validation first and in greatest detail.
  - Add a subsection or paragraph: "Complementary within-city validation" reserved for partner language.
- Results/Discussion:
  - Use within-city results only as context for how much harder transfer is, if partner elects to include them.

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

### Figure: Benchmark Metrics

- File: `docs/report/figures/benchmark_metrics.png`
- Source/provenance: copied from `figures/modeling/reporting/cross_city_benchmark_report_benchmark_metrics.png`.
- Use in report: Analysis and Results.
- Message: Compares retained benchmark metrics across simple baselines, logistic checkpoints, and RF.
- Status: Ready.
- Caption direction: State the sampled rows-per-city caveat and identify the matched 5k logistic/RF comparison.

### Figure: City Metric Deltas

- File: `docs/report/figures/city_metric_deltas.png`
- Source/provenance: copied from `figures/modeling/reporting/cross_city_benchmark_report_city_metric_deltas.png`.
- Use in report: Analysis and Results.
- Message: RF minus logistic performance is uneven by city and climate group.
- Status: Ready.
- Caption direction: Use this to explain why pooled and mean-city results differ.

### Figure: Denver Held-Out Map Triptych

- File: `docs/report/figures/denver_heldout_map_triptych.png`
- Source/provenance: copied from `figures/modeling/heldout_city_maps/denver_heldout_map_triptych.png`.
- Use in report: Analysis and Results or Appendix.
- Message: Representative held-out-city prediction/true/error spatial example.
- Status: Ready.
- Caption direction: Explicitly state it is a sampled held-out benchmark snapshot, not a full citywide deployment map.

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
- Use as main Table 3, simplified to the five rows listed in `final_report_outline.md`.
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

## Partner-Owned Gaps

Use visible placeholders in the draft so gaps are intentional and easy to fill.

Recommended placeholders:

- `[PARTNER TODO: Add 1-2 paragraphs of related-work context and citations on urban heat mapping, remotely sensed LST, or transfer/generalization in spatial ML.]`
- `[PARTNER TODO: Review city-relative target wording and add one sentence on why top-decile hotspots are useful across climate groups.]`
- `[PARTNER TODO: Add or refine statistical-method explanations in course language, especially PR AUC, grouped cross-validation, logistic regression, and random forest.]`
- `[PARTNER TODO: Decide whether to add the partner-provided per-city logistic/RF classification results. If included, label them supplemental/easier-split diagnostics.]`
- `[PARTNER TODO: Review discussion/future-work section and add any project-management or domain caveats from your part of the work.]`

Suggested partner responsibilities:

- Related work and citations.
- Course-language statistical explanation.
- Partner-supplied supplemental analysis, if included.
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

- `docs/report/final_report_outline.md`
- `docs/report/final_report_planning.md`
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
