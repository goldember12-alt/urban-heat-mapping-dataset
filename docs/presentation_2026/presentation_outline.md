# Presentation Outline

This deck is `7` slides total: `1` title slide, `5` content slides, and `1` Q&A slide.

The current content pass is intentionally denser and more data-forward. It keeps the central contrast between:

- within-city held-out evaluation, using the isolated partner logistic/RF results
- city-held-out transfer evaluation, using the repo's retained canonical logistic/RF benchmark

## Slide 1 - Cross-City Urban Heat Hotspot Prediction

- sparse title opener
- frames the talk as a comparison of two ways to evaluate hotspot prediction

## Slide 2 - Research Question + Validation Design

- combines the former research-question and two-evaluation-question content into one schematic
- foregrounds the six first-pass predictors, the hotspot-risk score, the within-city held-out question, and the city-held-out transfer question
- goal: establish the modeling target and validation contrast in a single scientific setup slide

## Slide 3 - Modeling Section: Logistic vs Random Forest

- uses a two-panel visual model comparison rather than rendered equations
- left panel: logistic regression maps the six feature inputs into a weighted sum and then a risk score
- right panel: random forest reuses the same feature inputs in multiple split trees and averages the tree votes into a risk score
- goal: clarify that the two models use the same predictor set but differ in how they convert those inputs into hotspot-risk scores

## Slide 4 - Results Side by Side

- compresses the prior within-city and city-held-out result slides into a single two-panel comparison
- left panel: partner within-city-style hotspot precision, recall, and F1
- right panel: repo city-held-out pooled PR AUC, mean city PR AUC, and recall at top 10%
- goal: make the contrast visible without asking the audience to remember numbers across slides

## Slide 5 - City-Level Signal Shifts Across Evaluation Designs

- adds a city-level scatter figure using `partner_vs_repo_city_comparison.csv`
- compares within-city RF hotspot F1/recall against city-held-out RF PR AUC/recall at top 10%
- goal: show that cities that look easy under one evaluation design are not automatically easy under whole-city transfer

## Slide 6 - Held-Out Denver Map Example

- replaces the duplicate metric-table slide with a retained held-out-city map example
- uses Denver as the documented representative hot-arid held-out benchmark map
- goal: make the city-held-out task spatially concrete after the metric and city-level comparison slides

## Slide 7 - Q&A

- simple closing slide
- verbal takeaway: basic factors contain real hotspot signal, but transfer to unseen cities is the hard part
