# Feature-Importance Summary

These artifacts refit only the saved outer-fold winners from retained benchmark runs.
They describe predictive reliance under the current six-feature contract and should not be read causally.

## Logistic Coefficient Summary

| feature_name | base_feature_name | median_coefficient | median_abs_coefficient | median_absolute_rank | majority_sign | sign_consistency |
| --- | --- | --- | --- | --- | --- | --- |
| climate_group_hot_arid | climate_group | -2.1885 | 2.1885 | 1.0000 | negative | 1.0000 |
| climate_group_mild_cool | climate_group | -1.5101 | 1.5101 | 2.0000 | negative | 1.0000 |
| climate_group_hot_humid | climate_group | -1.1911 | 1.1911 | 4.0000 | negative | 0.6000 |
| land_cover_class_90 | land_cover_class | -1.1036 | 1.1036 | 4.0000 | negative | 1.0000 |
| land_cover_class_31 | land_cover_class | 1.0783 | 1.0783 | 5.0000 | positive | 0.8000 |
| land_cover_class_43 | land_cover_class | -0.8465 | 0.8465 | 6.0000 | negative | 1.0000 |
| land_cover_class_82 | land_cover_class | 0.6290 | 0.6290 | 7.0000 | positive | 1.0000 |
| land_cover_class_41 | land_cover_class | -0.7941 | 0.7941 | 8.0000 | negative | 1.0000 |

## Random-Forest Held-Out Permutation Importance

| feature_name | mean_pr_auc_drop | std_pr_auc_drop_across_folds | median_rank | stability_positive_drop_fraction |
| --- | --- | --- | --- | --- |
| ndvi_median_may_aug | 0.0375 | 0.0160 | 1.0000 | 1.0000 |
| impervious_pct | 0.0300 | 0.0123 | 2.0000 | 1.0000 |
| climate_group | 0.0242 | 0.0173 | 3.0000 | 1.0000 |
| land_cover_class | 0.0062 | 0.0044 | 5.0000 | 0.8000 |
| elevation_m | 0.0048 | 0.0161 | 5.0000 | 0.6000 |
| dist_to_water_m | -0.0021 | 0.0044 | 6.0000 | 0.6000 |

Figure: `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\figures\modeling\supplemental\feature_importance\feature_importance_ranked_summary.png`
