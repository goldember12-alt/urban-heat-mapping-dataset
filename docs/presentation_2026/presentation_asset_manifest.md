# Presentation Asset Manifest

## Active Source Artifacts

| Path | Role | Slide(s) | Why used |
| --- | --- | --- | --- |
| `data_processed/final/final_dataset_artifact_summary.json` | canonical dataset size and schema summary | 2 | supplies the row context for the modeling handoff |
| `data_processed/modeling/final_dataset_audit_summary.json` | modeling-input audit summary | 2 | confirms `30` cities and the `hotspot_10pct` target |
| `data_processed/modeling/city_outer_folds.csv` | held-out-city split contract | 2, 4 | confirms `5` outer folds and `6` held-out cities per fold |
| `outputs/modeling/partner_data/per_city_logistic_rf_results/partner_results_metadata.json` | partner result metadata | 4 | records the support fraction for the verified within-city 70/30 split used in the presentation |
| `outputs/modeling/partner_data/per_city_logistic_rf_results/tables/partner_model_summary.csv` | partner model summary | 4 | supplies mean hotspot precision, recall, and F1 for logistic and random forest |
| `outputs/modeling/partner_data/per_city_logistic_rf_results/tables/partner_vs_repo_city_comparison.csv` | city-level partner/repo comparison | 5 | supplies the 30-city scatter comparison between within-city RF metrics and city-held-out RF metrics |
| `outputs/modeling/reporting/tables/cross_city_benchmark_report_benchmark_table.csv` | retained city-held-out benchmark metrics | 4 | supplies logistic 5k and RF frontier transfer metrics |
| `outputs/modeling/reporting/heldout_city_maps/heldout_city_map_points.parquet` | retained held-out map points | 6 | supplies the Denver predicted, observed, and error-map panels |

## Active Figures

| Path | Slide | Why used |
| --- | --- | --- |
| `figures/presentation/setup_predictors_evaluation_questions.(png|svg)` | 2 | combines target, predictors, and two evaluation questions into one setup graphic |
| `figures/presentation/logistic_rf_model_math.(png|svg)` | 3 | shows the logistic-versus-random-forest model logic as two visual panels using the same six input features |
| `figures/presentation/within_city_vs_transfer_results.(png|svg)` | 4 | places partner within-city metrics and repo city-held-out metrics side by side |
| `figures/presentation/city_signal_transfer_relationship.(png|svg)` | 5 | data-rich city-level scatter view showing that within-city strength and transfer strength differ |
| `figures/presentation/heldout_denver_map_focus.(png|svg)` | 6 | presentation-oriented Denver held-out benchmark map showing predicted top-decile risk, observed hotspots, and categorical errors |

## Metric Checks Used In Deck

- City count: `30`
- Final dataset rows: `71,394,894`
- Target: `hotspot_10pct`
- Partner support fraction: approximately `30%` of canonical city rows under the verified within-city 70/30 split
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
