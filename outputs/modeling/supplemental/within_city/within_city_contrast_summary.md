# Within-City Exploratory Contrast

This supplement is exploratory and easier than the canonical project benchmark because training and testing both occur inside the same city.
The main project narrative remains the cross-city city-held-out benchmark.

## Selected Cities

| city_name | climate_group | pr_auc_logistic | climate_group_logistic_pr_auc_median | abs_diff_to_group_median |
| --- | --- | --- | --- | --- |
| Reno | hot_arid | 0.1412 | 0.1350 | 0.0062 |
| Charlotte | hot_humid | 0.1491 | 0.1861 | 0.0370 |
| Detroit | mild_cool | 0.1856 | 0.1786 | 0.0071 |

## Within-City vs Cross-City Contrast

| city_name | climate_group | model_name | within_city_pr_auc_mean | cross_city_pr_auc | pr_auc_gap | within_city_recall_at_top_10pct_mean | cross_city_recall_at_top_10pct | recall_gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Reno | hot_arid | logistic_saga | 0.5037 | 0.2144 | 0.2893 | 0.4908 | 0.2650 | 0.2258 |
| Reno | hot_arid | random_forest | 0.7513 | 0.1142 | 0.6371 | 0.6950 | 0.1060 | 0.5890 |
| Charlotte | hot_humid | logistic_saga | 0.1542 | 0.1438 | 0.0103 | 0.1600 | 0.1695 | -0.0095 |
| Charlotte | hot_humid | random_forest | 0.1984 | 0.1464 | 0.0520 | 0.2342 | 0.1760 | 0.0582 |
| Detroit | mild_cool | logistic_saga | 0.1735 | 0.1744 | -0.0009 | 0.2000 | 0.2130 | -0.0130 |
| Detroit | mild_cool | random_forest | 0.2881 | 0.1663 | 0.1218 | 0.3117 | 0.1960 | 0.1157 |

## Average Gap By Model

| model_name | mean_pr_auc_gap | mean_recall_gap |
| --- | --- | --- |
| logistic_saga | 0.0996 | 0.0678 |
| random_forest | 0.2703 | 0.2543 |

Figure: `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\figures\modeling\supplemental\within_city\within_city_pr_auc_contrast.png`
