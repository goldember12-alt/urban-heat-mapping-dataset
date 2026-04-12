# Held-Out City Maps

Purpose:

- export deterministic held-out-city map deliverables from retained benchmark predictions without rerunning the benchmark ladder
- keep the city-held-out cross-city benchmark as the canonical narrative while adding map-ready appendix/reporting figures

Reference run:

- model: `random_forest`
- tuning preset: `frontier`
- retained sample rows per city: `5000`
- source run dir: `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\outputs\modeling\random_forest\frontier_allfolds_s5000_frontier-check_2026-04-11_173430`

Selected representative cities:

| model_name | outer_fold | city_id | city_name | climate_group | row_count | positive_count | prevalence | pr_auc | recall_at_top_10pct | climate_group_pr_auc_median | pr_auc_distance_from_climate_median | source_run_dir |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_forest | 1 | 6 | Denver | hot_arid | 5000 | 500 | 0.1000 | 0.1508 | 0.2000 | 0.1459 | 0.0049 | C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\outputs\modeling\random_forest\frontier_allfolds_s5000_frontier-check_2026-04-11_173430 |
| random_forest | 0 | 18 | Atlanta | hot_humid | 5000 | 500 | 0.1000 | 0.1817 | 0.2380 | 0.1799 | 0.0018 | C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\outputs\modeling\random_forest\frontier_allfolds_s5000_frontier-check_2026-04-11_173430 |
| random_forest | 4 | 29 | Detroit | mild_cool | 5000 | 500 | 0.1000 | 0.1668 | 0.1900 | 0.1598 | 0.0070 | C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\outputs\modeling\random_forest\frontier_allfolds_s5000_frontier-check_2026-04-11_173430 |

Selected city error summary:

| city_id | city_name | climate_group | outer_fold | row_count | predicted_hotspot_count | true_hotspot_count | true_positive_count | false_positive_count | false_negative_count | true_negative_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | Denver | hot_arid | 1 | 5000 | 500 | 500 | 100 | 400 | 400 | 4100 |
| 18 | Atlanta | hot_humid | 0 | 5000 | 500 | 500 | 119 | 381 | 381 | 4119 |
| 29 | Detroit | mild_cool | 4 | 5000 | 500 | 500 | 95 | 405 | 405 | 4095 |

Figure files:

- `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\figures\modeling\heldout_city_maps\atlanta_heldout_map_triptych.png`
- `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\figures\modeling\heldout_city_maps\denver_heldout_map_triptych.png`
- `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\figures\modeling\heldout_city_maps\detroit_heldout_map_triptych.png`

Interpretation note:

These figures use saved held-out prediction artifacts from the retained benchmark checkpoint. They support the existing cross-city benchmark story and do not replace the city-held-out evaluation methodology.
