# Cross-City Modeling Report

Purpose:

- summarize the retained logistic and random-forest benchmark checkpoints most relevant for reporting
- compare city-level performance between the matched logistic `5000` slice and the current RF `frontier` checkpoint
- capture the current stop / escalate interpretation without requiring any new model runs

## Benchmark Comparison

| run_label | model_family | preset | rows_per_city | param_candidate_count | estimated_total_inner_fits | pooled_pr_auc | mean_city_pr_auc | pooled_recall_at_top_10pct | runtime_minutes | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| impervious_only_baseline | baseline | n/a | all available | n/a | n/a | 0.1351 | 0.1519 | 0.1858 | n/a | Strongest simple baseline on recall |
| land_cover_only_baseline | baseline | n/a | all available | n/a | n/a | 0.1353 | 0.1479 | 0.1672 | n/a | Strongest simple baseline on pooled PR AUC |
| full_allfolds_s5000_sampled-full-allfolds_2026-04-07_235825 | logistic_saga | full | 5000 | 20 | 400 | 0.1421 | 0.1803 | 0.1647 | 35.6 | Retained 5k linear baseline rung |
| full_allfolds_s10000_samplecurve-10k_2026-04-08_004723 | logistic_saga | full | 10000 | 20 | 400 | 0.1441 | 0.1792 | 0.1675 | 84.4 | Retained 10k linear baseline rung |
| full_allfolds_s20000_samplecurve-20k_2026-04-08_021152 | logistic_saga | full | 20000 | 20 | 400 | 0.1457 | 0.1796 | 0.1709 | 156.6 | Highest-capacity retained linear rung on this workstation |
| smoke_allfolds_s5000_nonlinear-check_2026-04-11_163814 | random_forest | smoke | 5000 | 4 | 60 | 0.1485 | 0.1782 | 0.1945 | 47.2 | Cheap nonlinear comparison checkpoint |
| frontier_allfolds_s5000_frontier-check_2026-04-11_173430 | random_forest | frontier | 5000 | 8 | 120 | 0.1486 | 0.1781 | 0.1961 | 97.2 | Targeted follow-up search around the smoke-winning RF region |
| phase1_smoke_allfolds | hist_gradient_boosting | smoke | 5000 | 4 | 60 | 0.1408 | 0.1761 | 0.1751 | 7.1 | Bounded Phase 1 better-learner checkpoint on the fixed six-feature contract |
| phase2_smoke_allfolds | logistic_saga_climate_interactions | smoke | 5000 | 4 | 60 | 0.1480 | 0.1814 | 0.1801 | 25.8 | Phase 2 climate-conditioned logistic benchmark on the fixed six-feature contract with training-only climate-by-numeric interactions |
| full_allfolds_s5000_phase3a-nlcd-context_2026-04-13_142451 | logistic_saga | full | 5000 | 20 | 400 | 0.1450 | 0.1807 | 0.1699 | 32.3 | Phase 3A richer-predictor logistic checkpoint with bounded NLCD neighborhood-context features added to the retained six-feature contract |

## City-Level Error Analysis

- RF frontier beats logistic 5k on PR AUC in `9` cities and trails in `21`.
- RF frontier beats logistic 5k on recall at top 10% in `9` cities and trails in `21`.
- Mean PR AUC delta (RF minus logistic) is `-0.0023`.
- Mean recall-at-top-10% delta (RF minus logistic) is `0.0106`.

### Climate Summary

| climate_group | city_count | rf_pr_auc_wins | logistic_pr_auc_wins | rf_recall_wins | logistic_recall_wins | mean_pr_auc_delta | median_pr_auc_delta | mean_recall_delta | median_recall_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hot_arid | 10 | 5 | 5 | 6 | 4 | 0.0336 | -0.0031 | 0.0762 | 0.0160 |
| hot_humid | 10 | 2 | 8 | 2 | 8 | -0.0123 | -0.0081 | -0.0164 | -0.0160 |
| mild_cool | 10 | 2 | 8 | 1 | 9 | -0.0281 | -0.0180 | -0.0280 | -0.0250 |

### Top RF Gains By City

| city_name | climate_group | pr_auc_logistic | pr_auc_rf | pr_auc_delta_rf_minus_logistic | recall_at_top_10pct_logistic | recall_at_top_10pct_rf | recall_delta_rf_minus_logistic |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Las Vegas | hot_arid | 0.0850 | 0.2795 | 0.1945 | 0.0480 | 0.3900 | 0.3420 |
| Bakersfield | hot_arid | 0.1041 | 0.2693 | 0.1652 | 0.1300 | 0.3480 | 0.2180 |
| Tucson | hot_arid | 0.1121 | 0.1941 | 0.0819 | 0.0640 | 0.2500 | 0.1860 |
| Fresno | hot_arid | 0.1618 | 0.2182 | 0.0563 | 0.1920 | 0.2840 | 0.0920 |
| New Orleans | hot_humid | 0.1443 | 0.1781 | 0.0337 | 0.1440 | 0.1840 | 0.0400 |

### Top RF Losses By City

| city_name | climate_group | pr_auc_logistic | pr_auc_rf | pr_auc_delta_rf_minus_logistic | recall_at_top_10pct_logistic | recall_at_top_10pct_rf | recall_delta_rf_minus_logistic |
| --- | --- | --- | --- | --- | --- | --- | --- |
| San Jose | mild_cool | 0.1715 | 0.0972 | -0.0743 | 0.1360 | 0.0800 | -0.0560 |
| Chicago | mild_cool | 0.2844 | 0.2162 | -0.0682 | 0.3080 | 0.2460 | -0.0620 |
| Portland | mild_cool | 0.3172 | 0.2505 | -0.0667 | 0.3820 | 0.3120 | -0.0700 |
| Atlanta | hot_humid | 0.2425 | 0.1817 | -0.0608 | 0.3040 | 0.2380 | -0.0660 |
| Salt Lake City | hot_arid | 0.1663 | 0.1221 | -0.0442 | 0.1760 | 0.1200 | -0.0560 |

## Figure Outputs

- benchmark metric comparison: `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\figures\modeling\reporting\cross_city_benchmark_report_phase3a_nlcd_context_benchmark_metrics.png`
- runtime versus pooled PR AUC: `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\figures\modeling\reporting\cross_city_benchmark_report_phase3a_nlcd_context_runtime_vs_pr_auc.png`
- city-level RF-minus-logistic deltas: `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\figures\modeling\reporting\cross_city_benchmark_report_phase3a_nlcd_context_city_metric_deltas.png`

## Current Interpretation

The retained logistic and RF checkpoints all outperform the strongest simple transfer baselines on pooled PR AUC. At the matched `5000` rows-per-city slice, RF still improves pooled PR AUC and top-decile recall relative to logistic, but logistic remains slightly stronger on mean city PR AUC. The city-level deltas show that RF's gains are concentrated mainly in hot-arid cities, while logistic remains steadier across hot-humid and mild-cool cities. That supports the current project conclusion: RF adds a real but uneven nonlinear benefit, and the current frontier checkpoint is informative enough for reporting without automatically justifying a broader RF search.

## Phase 1 Candidate Checkpoint

This section is optional and does not replace the retained logistic/RF benchmark story. It records how the bounded histogram-gradient-boosting smoke run compares with the retained RF frontier checkpoint on the same six-feature contract.

- HGB smoke beats RF frontier on PR AUC in `17` city-fold rows and trails in `13`.
- HGB smoke beats RF frontier on recall at top 10% in `14` city-fold rows and trails in `14`.
- Mean PR AUC delta (HGB minus RF frontier) is `-0.0020`.
- Mean recall-at-top-10% delta (HGB minus RF frontier) is `-0.0039`.

### HGB vs RF Frontier Climate Summary

| climate_group | city_count | hgb_pr_auc_wins | rf_pr_auc_wins | hgb_recall_wins | rf_recall_wins | mean_pr_auc_delta | median_pr_auc_delta | mean_recall_delta | median_recall_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hot_arid | 10 | 7 | 3 | 5 | 5 | -0.0027 | 0.0057 | -0.0022 | 0.0020 |
| hot_humid | 10 | 6 | 4 | 5 | 3 | 0.0002 | 0.0021 | 0.0068 | 0.0030 |
| mild_cool | 10 | 4 | 6 | 4 | 6 | -0.0036 | -0.0087 | -0.0164 | -0.0240 |

## Phase 2 Climate-Conditioned Checkpoint

This section is optional and does not replace the retained logistic/RF benchmark story. It records how a separate logistic SAGA variant with training-only climate-by-numeric interactions compares against the retained logistic benchmark slice on the same six-feature contract.

- The climate-interaction logistic variant beats retained logistic on PR AUC in `12` city-fold rows and trails in `18`.
- The climate-interaction logistic variant beats retained logistic on recall at top 10% in `12` city-fold rows and trails in `18`.
- Mean PR AUC delta (interaction logistic minus retained logistic) is `0.0011`.
- Mean recall-at-top-10% delta (interaction logistic minus retained logistic) is `-0.0003`.

### Climate Summary

| climate_group | city_count | mean_pr_auc_logistic | mean_pr_auc_logistic_climate_interactions | interaction_pr_auc_wins | logistic_pr_auc_wins | mean_pr_auc_delta | median_pr_auc_delta | mean_recall_at_top_10pct_logistic | mean_recall_at_top_10pct_logistic_climate_interactions | interaction_recall_wins | logistic_recall_wins | mean_recall_delta | median_recall_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hot_arid | 10 | 0.1339 | 0.1545 | 6 | 4 | 0.0207 | 0.0134 | 0.1246 | 0.1454 | 5 | 5 | 0.0208 | 0.0120 |
| hot_humid | 10 | 0.2143 | 0.2157 | 5 | 5 | 0.0014 | 0.0016 | 0.2454 | 0.2490 | 5 | 5 | 0.0036 | 0.0040 |
| mild_cool | 10 | 0.1929 | 0.1741 | 1 | 9 | -0.0188 | -0.0190 | 0.2130 | 0.1878 | 2 | 8 | -0.0252 | -0.0280 |

### Climate-Group Disparity Summary

| metric | baseline_climate_group_range | interaction_climate_group_range | range_delta_interaction_minus_baseline |
| --- | --- | --- | --- |
| pr_auc | 0.0805 | 0.0612 | -0.0193 |
| recall_at_top_10pct | 0.1208 | 0.1036 | -0.0172 |

## Phase 3 Richer-Predictor Checkpoint

This section is optional and does not replace the retained six-feature benchmark story. It records one bounded Phase 3A expansion: a logistic SAGA run on the retained `5000` rows-per-city slice with an NLCD neighborhood-context bundle added to the frozen six-feature contract. The added predictors are a `270 m` tree-cover proxy, a `270 m` vegetated-cover proxy, and a `270 m` local impervious mean.

- The richer-feature logistic variant beats retained logistic on PR AUC in `17` city-fold rows and trails in `13`.
- The richer-feature logistic variant beats retained logistic on recall at top 10% in `18` city-fold rows and trails in `9`.
- Mean PR AUC delta (Phase 3A richer logistic minus retained logistic) is `0.0003`.
- Mean recall-at-top-10% delta (Phase 3A richer logistic minus retained logistic) is `0.0022`.

### Climate Summary

| climate_group | city_count | mean_pr_auc_logistic | mean_pr_auc_phase3a | phase3a_pr_auc_wins | logistic_pr_auc_wins | mean_pr_auc_delta | median_pr_auc_delta | mean_recall_at_top_10pct_logistic | mean_recall_at_top_10pct_phase3a | phase3a_recall_wins | logistic_recall_wins | mean_recall_delta | median_recall_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hot_arid | 10 | 0.1339 | 0.1374 | 5 | 5 | 0.0035 | 0.0004 | 0.1246 | 0.1372 | 7 | 3 | 0.0126 | 0.0080 |
| hot_humid | 10 | 0.2143 | 0.2110 | 6 | 4 | -0.0033 | 0.0007 | 0.2454 | 0.2372 | 3 | 4 | -0.0082 | 0.0000 |
| mild_cool | 10 | 0.1929 | 0.1937 | 6 | 4 | 0.0009 | 0.0028 | 0.2130 | 0.2152 | 8 | 2 | 0.0022 | 0.0040 |
