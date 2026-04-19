# Presentation Outline

This deck is `7` slides total: `1` title slide, `5` content slides, and `1` Q&A slide.

The central story is the contrast between two useful evaluation questions:

- within-city held-out evaluation, using the isolated partner logistic/RF results
- city-held-out transfer evaluation, using the repo's retained canonical logistic/RF benchmark

## Slide 1 - Cross-City Urban Heat Hotspot Prediction

- sparse title opener
- frames the talk as a comparison of two evaluation approaches

## Slide 2 - Research Question + Predictors

- states the research question plainly: can basic environmental and built-environment factors predict hotspot cells?
- shows the target and first-pass predictors: imperviousness, land cover, elevation, distance to water, NDVI, and climate group
- goal: make the modeling problem legible before discussing validation design

## Slide 3 - Two Evaluation Questions

- side-by-side schematic contrasting within-city held-out cells and city-held-out transfer
- left side asks whether models can identify hotspot structure when cities are represented in training
- right side asks whether models can generalize to cities not seen during training
- goal: make the evaluation design the conceptual anchor of the talk

## Slide 4 - Within-City Held-Out Evaluation

- uses partner results from `outputs/modeling/partner_data/per_city_logistic_rf_results/`
- emphasizes hotspot precision, recall, and F1 rather than accuracy
- states carefully that support counts appear consistent with about a 30% held-out sample per city
- goal: show strong learnable hotspot signal, especially for random forest, under a within-city question

## Slide 5 - City-Held-Out Transfer Evaluation

- uses retained repo benchmark values for logistic 5k versus RF frontier
- shows pooled PR AUC, mean city PR AUC, and recall at top 10% predicted risk
- goal: show that transfer is harder, with RF improving pooled retrieval while logistic remains competitive on mean city performance

## Slide 6 - What The Contrast Shows

- synthesizes the two evaluation methodologies without ranking one as inherently better
- message: models learn within-city hotspot structure more readily than they transfer across cities
- implication: evaluation must match the intended use case

## Slide 7 - Q&A

- simple closing slide
- one-line verbal takeaway: basic factors contain real hotspot signal, but transfer to unseen cities is the hard part
