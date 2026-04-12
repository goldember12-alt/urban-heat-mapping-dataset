# Logistic And Random-Forest Comparison Summary

Date: 2026-04-11

Purpose:

- Summarize the retained cross-city modeling checkpoints most relevant for reporting
- Compare tuned logistic SAGA against staged random forest on the canonical held-out-city task
- Record the current stop / escalate conclusion for the RF search

Scope notes:

- The strongest directly comparable slice is the all-fold sampled `5000` rows-per-city comparison between logistic `full`, RF `smoke`, and RF `frontier`
- Logistic `10000` and `20000` rows-per-city runs are retained linear baseline ladder rungs, but they are not sample-size-matched to the RF `5000` runs
- Baseline rows below use the all-fold baseline summary in `outputs/modeling/baselines/metrics_summary.csv`

## Comparison Table

| Run | Model family | Preset | Rows per city | Param candidates | Est. inner fits | Pooled PR AUC | Mean city PR AUC | Recall at top 10% | Runtime (min) | Notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `impervious_only_baseline` | baseline | n/a | all available | n/a | n/a | 0.1351 | 0.1519 | 0.1858 | n/a | Strongest simple baseline on recall |
| `land_cover_only_baseline` | baseline | n/a | all available | n/a | n/a | 0.1353 | 0.1479 | 0.1672 | n/a | Strongest simple baseline on pooled PR AUC |
| `full_allfolds_s5000_sampled-full-allfolds_2026-04-07_235825` | logistic SAGA | `full` | 5000 | 20 | 400 | 0.1421 | 0.1803 | 0.1647 | 35.6 | Retained 5k linear baseline rung |
| `full_allfolds_s10000_samplecurve-10k_2026-04-08_004723` | logistic SAGA | `full` | 10000 | 20 | 400 | 0.1441 | 0.1792 | 0.1675 | 84.4 | Retained 10k linear baseline rung |
| `full_allfolds_s20000_samplecurve-20k_2026-04-08_021152` | logistic SAGA | `full` | 20000 | 20 | 400 | 0.1457 | 0.1796 | 0.1709 | 156.6 | Highest-capacity retained linear rung on this workstation |
| `smoke_allfolds_s5000_nonlinear-check_2026-04-11_163814` | random forest | `smoke` | 5000 | 4 | 60 | 0.1485 | 0.1782 | 0.1945 | 47.2 | Cheap nonlinear comparison checkpoint |
| `frontier_allfolds_s5000_frontier-check_2026-04-11_173430` | random forest | `frontier` | 5000 | 8 | 120 | 0.1486 | 0.1781 | 0.1961 | 97.2 | Targeted follow-up search around the smoke-winning region |

## Main Takeaways

- All tuned logistic and RF runs beat the strongest simple transfer baselines on pooled PR AUC.
- At the directly comparable `5000` rows-per-city slice, both RF checkpoints beat logistic on pooled PR AUC and recall at top 10%.
- Logistic remains slightly better on mean city PR AUC, which suggests somewhat steadier city-to-city ranking performance even when RF improves pooled metrics.
- The retained logistic ladder shows gradual gains from `5000` to `20000` rows per city, but those gains are modest relative to the runtime increase.

## RF Stage Decision

- RF `smoke` already established that a nonlinear model can improve pooled ranking and top-decile hotspot capture relative to the retained logistic `5000` benchmark.
- RF `frontier` only marginally improved on RF `smoke`:
  - pooled PR AUC: `0.14852 -> 0.14859`
  - recall at top 10%: `0.19447 -> 0.19607`
  - mean city PR AUC: `0.17823 -> 0.17809`
  - runtime: `47.2 -> 97.2` minutes
- This is a weak return on the extra search cost. The frontier run mostly confirmed the smoke-winning RF region rather than opening a meaningfully better one.

## Current Reporting Conclusion

The current evidence supports a moderate but real cross-city transfer signal. Both logistic SAGA and random forest outperform the simple baselines, but neither model family reaches a level that would justify claiming strong universal hotspot transfer across unseen cities. Random forest improves pooled PR AUC and recall at top 10%, while logistic is slightly stronger on mean city PR AUC and remains the cleaner retained linear baseline. Given the tiny frontier-over-smoke lift and the observed day-scale projected cost of RF `full`, the present reporting recommendation is to stop the routine RF search at `frontier` unless an explicit high-cost confirmation run is needed for the final report.
