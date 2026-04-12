# Within-City Spatial-Block Sensitivity

This layer is a harder within-city sensitivity than the default random-split supplement because each evaluation holds out one deterministic centroid-based spatial block.
It remains supplemental and exploratory, and it is not equivalent to the canonical cross-city city-held-out benchmark or to transfer into unseen cities.
The main project narrative remains the canonical cross-city city-held-out benchmark.
This pass intentionally keeps model scope logistic SAGA only so the spatial sensitivity stays bounded and workstation-friendly.

Deterministic blocking rule:
- deterministic centroid quadrants using city-specific median centroid_lon and centroid_lat, with ties assigned to the north/east side via >= median comparisons

## Selected Cities

| city_name | climate_group | pr_auc_logistic | climate_group_logistic_pr_auc_median | abs_diff_to_group_median |
| --- | --- | --- | --- | --- |
| Reno | hot_arid | 0.1412 | 0.1350 | 0.0062 |
| Charlotte | hot_humid | 0.1491 | 0.1861 | 0.0370 |
| Detroit | mild_cool | 0.1856 | 0.1786 | 0.0071 |

## Default vs Spatial vs Cross-City Contrast

| city_name | climate_group | default_within_city_pr_auc_mean | spatial_within_city_pr_auc_mean | cross_city_pr_auc | spatial_minus_default_pr_auc_gap | spatial_minus_cross_city_pr_auc_gap | default_within_city_recall_at_top_10pct_mean | spatial_within_city_recall_at_top_10pct_mean | cross_city_recall_at_top_10pct | spatial_minus_default_recall_gap | spatial_minus_cross_city_recall_gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Reno | hot_arid | 0.5037 | 0.4438 | 0.2144 | -0.0599 | 0.2295 | 0.4908 | 0.6651 | 0.2650 | 0.1743 | 0.4001 |
| Charlotte | hot_humid | 0.1542 | 0.1385 | 0.1438 | -0.0156 | -0.0053 | 0.1600 | 0.1637 | 0.1695 | 0.0037 | -0.0058 |
| Detroit | mild_cool | 0.1735 | 0.1759 | 0.1744 | 0.0024 | 0.0015 | 0.2000 | 0.2494 | 0.2130 | 0.0494 | 0.0364 |

## Average Gap Across Cities

| mean_spatial_minus_default_pr_auc_gap | mean_spatial_minus_cross_city_pr_auc_gap | mean_spatial_minus_default_recall_gap | mean_spatial_minus_cross_city_recall_gap |
| --- | --- | --- | --- |
| -0.0244 | 0.0752 | 0.0758 | 0.1436 |

Figure: `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\figures\modeling\supplemental\within_city_spatial\within_city_spatial_pr_auc_contrast.png`
