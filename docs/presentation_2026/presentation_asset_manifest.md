# Presentation Asset Manifest

## Active Source Artifacts

| Path | Role | Slide(s) | Why used |
| --- | --- | --- | --- |
| `data_processed/final/final_dataset_artifact_summary.json` | canonical dataset size and schema summary | 1, 3 | supplies the `71,394,894` row count, `17` columns, and the city-feature file count context |
| `data_processed/modeling/final_dataset_audit_summary.json` | modeling-input audit summary | 3 | confirms `30` cities, the binary target column, and the audited final dataset state |
| `data_processed/modeling/city_outer_folds.csv` | held-out-city split contract | 3 | confirms `5` outer folds and `6` held-out cities per fold |
| `outputs/modeling/reporting/tables/cross_city_benchmark_report_benchmark_table.csv` | retained benchmark metrics | 4, 6 | provides the logistic `5k` and RF frontier values used in the result callouts |
| `outputs/modeling/reporting/heldout_city_maps/heldout_city_maps.md` | representative held-out city summary | 5 | supports the Denver selection as a representative hot-arid held-out city |

## Active Figures

| Path | Slide | Why used |
| --- | --- | --- |
| `figures/modeling/reporting/cross_city_benchmark_report_benchmark_metrics.png` | 4 | single most compact benchmark figure for pooled PR AUC, mean city PR AUC, and recall at top 10% |
| `figures/modeling/heldout_city_maps/denver_heldout_map_triptych.png` | 5 | best large-format spatial example for a held-out city with readable panel labels |

## Slide-Only Generated Assets

The active workflow builds these presentation-specific images under `docs/presentation_2026/build/`:

- `slide_01_title_card.png`
- `slide_02_problem_framing.png`
- `slide_03_design.png`
- `slide_04_models_results.png`
- `slide_05_denver_example.png`
- `slide_06_takeaway.png`

These are derived from the repo artifacts above and are intended only for the PowerPoint deck.

## Metric Checks Used In Deck

- Final dataset rows: `71,394,894`
- Final dataset columns: `17`
- City count: `30`
- Outer folds: `5`
- Held-out cities per fold: `6`
- Logistic `5k` pooled PR AUC: `0.1421`
- Logistic `5k` mean city PR AUC: `0.1803`
- RF frontier pooled PR AUC: `0.1486`
- RF frontier recall at top `10%`: `0.1961`

All values above come from the retained artifacts listed in this manifest.
