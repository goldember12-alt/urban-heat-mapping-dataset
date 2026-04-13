# All-City Within-City Supplemental Pass

This summary is supplemental and easier than the canonical benchmark because each evaluation uses repeated random splits inside the same city.
The project benchmark remains the cross-city city-held-out evaluation, and these within-city random-split results must not be treated as benchmark-equivalent.
The all-city pass keeps the same six-feature contract, caps each city at up to 20,000 rows, and uses 3 repeated stratified 80/20 splits with smoke-sized within-city tuning only.

Interpretation guardrail:
- Cities with relatively strong within-city random-split performance but weak retained cross-city performance are more suggestive of transfer difficulty under the six-feature contract.
- Cities that remain weak even under within-city random splits are more suggestive of intrinsic difficulty under the same limited feature contract.
- These patterns are diagnostic support for the benchmark story, not a replacement for held-out-city evaluation.

## Climate-Group Within-City Summary

| climate_group | model_name | city_count | mean_city_within_city_pr_auc | mean_city_within_city_recall_at_top_10pct |
| --- | --- | --- | --- | --- |
| hot_arid | city_prevalence_baseline | 10 | 0.1000 | 0.1050 |
| hot_arid | logistic_saga | 10 | 0.3042 | 0.3259 |
| hot_arid | random_forest | 10 | 0.5150 | 0.5047 |
| hot_humid | city_prevalence_baseline | 10 | 0.1000 | 0.1040 |
| hot_humid | logistic_saga | 10 | 0.2723 | 0.3002 |
| hot_humid | random_forest | 10 | 0.3242 | 0.3471 |
| mild_cool | city_prevalence_baseline | 10 | 0.1000 | 0.1050 |
| mild_cool | logistic_saga | 10 | 0.2694 | 0.3075 |
| mild_cool | random_forest | 10 | 0.4246 | 0.4236 |

## Climate-Group Within-vs-Cross Gap Summary

| climate_group | model_name | city_count | mean_city_within_city_pr_auc | mean_city_cross_city_pr_auc | mean_city_pr_auc_gap | mean_city_within_city_recall_at_top_10pct | mean_city_cross_city_recall_at_top_10pct | mean_city_recall_gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hot_arid | city_prevalence_baseline | 10 | 0.1000 | n/a | n/a | 0.1050 | n/a | n/a |
| hot_arid | logistic_saga | 10 | 0.3042 | 0.1339 | 0.1703 | 0.3259 | 0.1246 | 0.2013 |
| hot_arid | random_forest | 10 | 0.5150 | 0.1675 | 0.3475 | 0.5047 | 0.2008 | 0.3039 |
| hot_humid | city_prevalence_baseline | 10 | 0.1000 | n/a | n/a | 0.1040 | n/a | n/a |
| hot_humid | logistic_saga | 10 | 0.2723 | 0.2143 | 0.0580 | 0.3002 | 0.2454 | 0.0548 |
| hot_humid | random_forest | 10 | 0.3242 | 0.2020 | 0.1222 | 0.3471 | 0.2290 | 0.1181 |
| mild_cool | city_prevalence_baseline | 10 | 0.1000 | n/a | n/a | 0.1050 | n/a | n/a |
| mild_cool | logistic_saga | 10 | 0.2694 | 0.1929 | 0.0765 | 0.3075 | 0.2130 | 0.0945 |
| mild_cool | random_forest | 10 | 0.4246 | 0.1647 | 0.2599 | 0.4236 | 0.1850 | 0.2386 |

## Largest Positive Within-vs-Cross PR AUC Gaps

| city_name | climate_group | model_name | within_city_pr_auc_mean | cross_city_pr_auc | pr_auc_gap | within_city_recall_at_top_10pct_mean | cross_city_recall_at_top_10pct | recall_gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Reno | hot_arid | random_forest | 0.7513 | 0.1143 | 0.6370 | 0.6950 | 0.1060 | 0.5890 |
| San Jose | mild_cool | random_forest | 0.5928 | 0.0972 | 0.4956 | 0.5533 | 0.0800 | 0.4733 |
| El Paso | hot_arid | random_forest | 0.5937 | 0.0997 | 0.4940 | 0.5758 | 0.0440 | 0.5318 |
| Los Angeles | mild_cool | random_forest | 0.6046 | 0.1382 | 0.4663 | 0.5742 | 0.1320 | 0.4422 |
| Las Vegas | hot_arid | logistic_saga | 0.5439 | 0.0850 | 0.4589 | 0.5450 | 0.0480 | 0.4970 |
| Las Vegas | hot_arid | random_forest | 0.6619 | 0.2795 | 0.3824 | 0.6067 | 0.3900 | 0.2167 |

## Hardest Cities Even Under Within-City Random Splits

| city_name | climate_group | model_name | within_city_pr_auc_mean | within_city_recall_at_top_10pct_mean |
| --- | --- | --- | --- | --- |
| Columbia | hot_humid | city_prevalence_baseline | 0.1000 | 0.0950 |
| Albuquerque | hot_arid | city_prevalence_baseline | 0.1000 | 0.1050 |
| Atlanta | hot_humid | city_prevalence_baseline | 0.1000 | 0.1050 |
| Bakersfield | hot_arid | city_prevalence_baseline | 0.1000 | 0.1050 |
| Boston | mild_cool | city_prevalence_baseline | 0.1000 | 0.1050 |
| Charlotte | hot_humid | city_prevalence_baseline | 0.1000 | 0.1050 |

Figure: `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\figures\modeling\supplemental\within_city_all_cities\within_city_all_cities_pr_auc_by_climate.png`
Figure: `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\figures\modeling\supplemental\within_city_all_cities\within_city_all_cities_recall_by_climate.png`
Figure: `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\figures\modeling\supplemental\within_city_all_cities\within_city_all_cities_within_vs_cross_gap.png`
