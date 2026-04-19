# Partner Logistic/RF Per-City Results

## Artifact Scope

This folder intentionally stores partner-provided modeling results separately from the repository's canonical model-run directories. The copied source file is:

- `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\outputs\modeling\partner_data\per_city_logistic_rf_results\partner_per_city_logistic_rf_results.csv`

Derived tables live in `tables/`, and figures live in `figures/`.

## What The File Contains

- `60` rows: `30` cities by `2` model labels (`logistic` and `rf`).
- The columns are sklearn-style classification-report metrics for class `0` and class `1`, plus accuracy, macro averages, weighted averages, and support counts.
- Class `1` aligns with the hotspot class: each city has approximately `10%` class-1 support.
- The file does not contain predicted probabilities, PR AUC, recall-at-top-10%, fold IDs, hyperparameters, feature lists, random seeds, run metadata, or paths back to training artifacts.

## Inferred Creation Logic

The strongest reproducible clue is the support count. Partner `total_support` is almost exactly `30%` of the canonical city row count in `data_processed/modeling/final_dataset_city_summary.csv`.

- Mean support fraction of canonical rows: `0.300000`
- Min support fraction: `0.300000`
- Max support fraction: `0.300002`

Because all `30` cities appear in the evaluation table and each city contributes about `30%` of its canonical cells, this most likely came from a row-level or within-city holdout split, plausibly a `70/30` train-test split with stratification by the hotspot label. That is an inference from the support counts, not a verified statement about the partner's code.

The metrics also appear to be hard-class predictions, likely at a default classification threshold, because they are precision/recall/F1 values from a classification report rather than ranking metrics from probability scores.

## Alignment With This Repo

The partner file aligns with the repo in several useful ways:

- It uses the same `30` city set.
- Its class balance matches the canonical `hotspot_10pct` target, with roughly `10%` positives per city.
- Its city support counts align closely with the canonical final filtered dataset, which suggests it was derived after the same or similar final row filtering.
- It compares the same broad model families as the headline repo narrative: logistic regression and random forest.

## Key Contrast With The Canonical Repo Results

The partner file should not be treated as a replacement for the repo's city-held-out benchmark. The repo's canonical evaluation withholds entire cities, fits preprocessing and tuning on training cities only, and reports PR AUC plus recall among the top `10%` predicted-risk cells. The partner file appears to report thresholded classification metrics on a per-city `30%` holdout from every city.

That difference matters. A row-level or within-city split is much easier because the model can train on other cells from the same city before being evaluated on that city. It is useful as supporting diagnostic evidence, but it does not answer the transfer question on its own.

## Partner Metric Summary

| Model | Mean hotspot precision | Mean hotspot recall | Mean hotspot F1 | Mean macro F1 | Mean accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| Logistic | 0.3887 | 0.0727 | 0.1083 | 0.5263 | 0.9013 |
| Random forest | 0.7310 | 0.3433 | 0.4480 | 0.7037 | 0.9243 |

Random forest beats logistic on hotspot recall in `30` cities and trails in `0`. It beats logistic on hotspot F1 in `30` cities and trails in `0`.

Accuracy is high for both models because class `0` is about `90%` of each city. The hotspot-class metrics are more informative than accuracy or weighted averages.

## Largest RF Gains By Hotspot F1

| city | class_1_f1_logistic | class_1_f1_rf | class_1_f1_delta_rf_minus_logistic | class_1_recall_logistic | class_1_recall_rf |
| --- | --- | --- | --- | --- | --- |
| El Paso | 0.0000 | 0.6800 | 0.6800 | 0.0000 | 0.5900 |
| Albuquerque | 0.0000 | 0.6000 | 0.6000 | 0.0000 | 0.4900 |
| San Jose | 0.0400 | 0.6300 | 0.5900 | 0.0200 | 0.5200 |
| Fresno | 0.0000 | 0.5300 | 0.5300 | 0.0000 | 0.3900 |
| Salt Lake City | 0.0000 | 0.5100 | 0.5100 | 0.0000 | 0.3800 |
| Phoenix | 0.0200 | 0.5000 | 0.4800 | 0.0100 | 0.3600 |
| Denver | 0.0200 | 0.4800 | 0.4600 | 0.0100 | 0.3500 |

## Largest RF Losses By Hotspot F1

| city | class_1_f1_logistic | class_1_f1_rf | class_1_f1_delta_rf_minus_logistic | class_1_recall_logistic | class_1_recall_rf |
| --- | --- | --- | --- | --- | --- |
| Miami | 0.0000 | 0.1200 | 0.1200 | 0.0000 | 0.0700 |
| Atlanta | 0.1500 | 0.2700 | 0.1200 | 0.0900 | 0.1800 |
| Charlotte | 0.0000 | 0.1300 | 0.1300 | 0.0000 | 0.0700 |
| Nashville | 0.4100 | 0.5500 | 0.1400 | 0.3100 | 0.4500 |
| Jacksonville | 0.1200 | 0.2700 | 0.1500 | 0.0700 | 0.1700 |
| Houston | 0.0000 | 0.2100 | 0.2100 | 0.0000 | 0.1200 |
| Tampa | 0.0100 | 0.2300 | 0.2200 | 0.0000 | 0.1400 |

## Relationship To Repo City-Held-Out Results

Correlations against the repo's retained city-held-out comparison are weak to moderate and should be interpreted cautiously because the metrics and likely split designs differ.

| comparison | n_cities | pearson_correlation |
| --- | --- | --- |
| logistic_class1_recall_vs_repo_recall_top10 | 30 | 0.1284 |
| rf_class1_recall_vs_repo_recall_top10 | 30 | 0.0332 |
| rf_minus_logistic_class1_recall_delta_vs_repo_recall_delta | 30 | 0.2036 |
| rf_minus_logistic_class1_f1_delta_vs_repo_pr_auc_delta | 30 | 0.0257 |

The main interpretive value is directional: the partner file supports the idea that random forest can recover more hotspot positives under an easier split, but it also emphasizes why the repo's harder city-held-out benchmark is necessary. Within-city-looking performance can be much stronger than cross-city transfer performance.

## Figure Outputs

- `figures/partner_metric_summary.png`
- `figures/partner_city_class1_metrics.png`
- `figures/partner_rf_minus_logistic_class1_deltas.png`
- `figures/partner_support_alignment.png`
- `figures/partner_vs_repo_delta_contrast.png`
