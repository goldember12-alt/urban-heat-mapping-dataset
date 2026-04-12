# Transfer Inference Summary

Purpose:

- apply the retained final-train transfer package to one new-city feature parquet
- keep this scoring path separate from held-out-city benchmark evaluation
- write deterministic prediction tables, a compact summary, and one map-style or fallback figure

Benchmark framing note:

This inference output is an application artifact derived from the retained transfer package. It is not a new held-out-city benchmark result and should be read underneath the canonical `outputs/modeling/reporting/cross_city_benchmark_report.md` benchmark narrative.

Inputs:

- package dir: `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\outputs\modeling\final_train\random_forest_frontier_s5000_all_cities_transfer_package`
- input parquet: `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\data_processed\city_features\05_el_paso_tx_features.parquet`
- selected feature columns: `impervious_pct, elevation_m, dist_to_water_m, ndvi_median_may_aug, land_cover_class, climate_group`
- figure kind: `centroid_map`

Prediction summary:

| row_count | predicted_hotspot_count | predicted_hotspot_fraction | predicted_probability_min | predicted_probability_mean | predicted_probability_median | predicted_probability_max | top_decile_probability_threshold | rows_with_any_missing_features | city_id | city_name | centroid_lon | centroid_lat |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 738527 | 73853 | 0.1000 | 0.0211 | 0.0949 | 0.0806 | 0.3272 | 0.1625 | 0 | 5 | El Paso | -106.1758 | 31.6968 |

Prediction deciles:

| prediction_decile | row_count | predicted_probability_min | predicted_probability_mean | predicted_probability_max | predicted_hotspot_count |
| --- | --- | --- | --- | --- | --- |
| 1.0000 | 73852.0000 | 0.1625 | 0.1980 | 0.3272 | 73852.0000 |
| 2.0000 | 73853.0000 | 0.1313 | 0.1486 | 0.1625 | 1.0000 |
| 3.0000 | 73853.0000 | 0.1071 | 0.1168 | 0.1313 | 0.0000 |
| 4.0000 | 73852.0000 | 0.0918 | 0.0991 | 0.1071 | 0.0000 |
| 5.0000 | 73853.0000 | 0.0806 | 0.0857 | 0.0918 | 0.0000 |
| 6.0000 | 73853.0000 | 0.0721 | 0.0762 | 0.0806 | 0.0000 |
| 7.0000 | 73852.0000 | 0.0643 | 0.0680 | 0.0721 | 0.0000 |
| 8.0000 | 73853.0000 | 0.0571 | 0.0607 | 0.0643 | 0.0000 |
| 9.0000 | 73853.0000 | 0.0494 | 0.0534 | 0.0571 | 0.0000 |
| 10.0000 | 73853.0000 | 0.0211 | 0.0423 | 0.0494 | 0.0000 |

Artifacts:

- predictions parquet: `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\outputs\modeling\transfer_inference\05_el_paso_tx\predictions.parquet`
- predictions csv: `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\outputs\modeling\transfer_inference\05_el_paso_tx\predictions.csv`
- summary csv: `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\outputs\modeling\transfer_inference\05_el_paso_tx\prediction_summary.csv`
- deciles csv: `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\outputs\modeling\transfer_inference\05_el_paso_tx\prediction_deciles.csv`
- feature missingness csv: `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\outputs\modeling\transfer_inference\05_el_paso_tx\feature_missingness.csv`
- figure: `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\figures\modeling\transfer_inference\05_el_paso_tx\predicted_risk_map.png`
- metadata: `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\outputs\modeling\transfer_inference\05_el_paso_tx\transfer_inference_metadata.json`
