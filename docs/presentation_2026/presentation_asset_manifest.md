# Presentation Asset Manifest

## Active Source Artifacts

| Path | Role | Slide(s) | Why used |
| --- | --- | --- | --- |
| `data_processed/final/final_dataset_artifact_summary.json` | canonical dataset size and schema summary | 2 | supplies the row and column context for the modeling handoff |
| `data_processed/modeling/final_dataset_audit_summary.json` | modeling-input audit summary | 2 | confirms `30` cities and the `hotspot_10pct` target |
| `data_processed/modeling/city_outer_folds.csv` | held-out-city split contract | 3, 5 | confirms `5` outer folds and `6` held-out cities per fold |
| `outputs/modeling/partner_data/per_city_logistic_rf_results/partner_results_metadata.json` | partner result metadata | 4 | records the inferred support fraction used for careful 70/30 split language |
| `outputs/modeling/partner_data/per_city_logistic_rf_results/tables/partner_model_summary.csv` | partner model summary | 4, 6 | supplies mean hotspot precision, recall, and F1 for logistic and random forest |
| `outputs/modeling/reporting/tables/cross_city_benchmark_report_benchmark_table.csv` | retained city-held-out benchmark metrics | 5, 6 | supplies logistic 5k and RF frontier transfer metrics |

## Active Figures

| Path | Slide | Why used |
| --- | --- | --- |
| `figures/presentation/research_question_predictors.(png|svg)` | 2 | presentation-native schematic linking basic predictors to `hotspot_10pct` |
| `figures/presentation/two_evaluation_questions.(png|svg)` | 3 | side-by-side conceptual anchor for within-city held-out versus city-held-out transfer |
| `figures/presentation/within_city_hotspot_results.(png|svg)` | 4 | clean hotspot precision/recall/F1 summary from partner results |
| `figures/presentation/city_heldout_transfer_results.(png|svg)` | 5 | retained repo benchmark comparison for pooled PR AUC, mean city PR AUC, and recall at top 10% |
| `figures/presentation/evaluation_contrast_takeaway.(png|svg)` | 6 | synthesis graphic showing that the two methodologies answer different use cases |

## Retired From The Active Story

The previous 7-slide version emphasized an end-to-end workflow, model math, a Denver map, and climate heterogeneity. Those artifacts remain useful for the broader project, but the active presentation no longer uses them because the narrative has shifted to comparing two evaluation methodologies.

## Metric Checks Used In Deck

- City count: `30`
- Final dataset rows: `71,394,894`
- Target: `hotspot_10pct`
- Partner support fraction: approximately `30%` of canonical city rows
- Partner mean hotspot precision:
  - logistic: `0.3887`
  - random forest: `0.7310`
- Partner mean hotspot recall:
  - logistic: `0.0727`
  - random forest: `0.3433`
- Partner mean hotspot F1:
  - logistic: `0.1083`
  - random forest: `0.4480`
- Repo city-held-out logistic 5k:
  - pooled PR AUC: `0.1421`
  - mean city PR AUC: `0.1803`
  - recall at top `10%`: `0.1647`
- Repo city-held-out RF frontier:
  - pooled PR AUC: `0.1486`
  - mean city PR AUC: `0.1781`
  - recall at top `10%`: `0.1961`

All values above come from the retained artifacts listed in this manifest.
