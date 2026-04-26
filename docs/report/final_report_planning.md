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

## Report Narrative To Preserve

Main story:

1. Urban heat varies locally and matters for planning/public health.
2. Many easier modeling setups do not test whether predictions transfer to unseen cities.
3. This project builds a standardized 30 m dataset for 30 U.S. cities.
4. The target is `hotspot_10pct`, a within-city top-decile ECOSTRESS LST label.
5. The benchmark holds out entire cities, with all preprocessing and tuning fit only on training cities.
6. Learned models outperform simple baselines, but transfer performance is moderate and uneven.
7. Random forest improves pooled PR AUC and recall at top 10% relative to matched logistic regression, while logistic regression is slightly stronger on mean city PR AUC.
8. The defensible conclusion is "credible transfer-screening framework with limitations," not "deployment-ready heat-risk classifier."

Avoid these narrative traps:

- Do not describe sampled benchmark runs as full exhaustive 71.4M-row benchmark results.
- Do not present Phoenix proposal figures as final project evidence.
- Do not imply `hotspot_10pct` is an absolute national heat-risk threshold.
- Do not use partner-provided easier-split results as the headline benchmark.
- Do not let supplemental HGB, climate-interaction, richer-feature, or within-city results replace the retained logistic/RF comparison.

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
- Status: Need to generate.

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
- Status: Need to generate.
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
- Status: Need to generate.
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
- Status: Need to generate or write manually.

## Existing Tables To Reuse

Retained benchmark table:

- Source: `outputs/modeling/reporting/tables/cross_city_benchmark_report_benchmark_table.csv`
- Use as main Table 3, possibly simplified to the five rows listed in `final_report_outline.md`.

Climate delta table:

- Source: `outputs/modeling/reporting/tables/cross_city_benchmark_report_city_error_by_climate.csv`
- Use as main Table 4 or in appendix.

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
