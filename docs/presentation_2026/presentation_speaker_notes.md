# Speaker Notes

These notes are written as live speaking guidance. The slides stay sparse; the explanation belongs here.

## Slide 1 - Cross-City Urban Heat Hotspot Prediction

Open by saying the talk is about one research question and two ways to evaluate it. The research question is whether basic environmental and built-environment factors can predict urban heat hotspot cells.

Set an objective tone immediately: the two evaluation designs are not competing claims about who did the better analysis. They answer different applied questions. One asks about identifying hotspot structure in cities that are represented in training. The other asks about transferring to cities the model has not seen.

Transition: "First, what are we trying to predict?"

## Slide 2 - Research Question + Predictors

Read the question plainly: can models predict urban heat hotspot cells from basic environmental and built-environment factors?

Define the target as `hotspot_10pct`: the hottest 10% of cells within each city after the project's filtering rules. Mention that it is city-relative because cities differ in climate and absolute temperature levels.

Walk through the predictors quickly: imperviousness, land cover, elevation, distance to water, NDVI, and climate group. Emphasize that these are relatively basic factors, not direct use of LST as a predictor.

Transition: "With the target and predictors fixed, the next question is how to evaluate the model."

## Slide 3 - Two Evaluation Questions

This is the conceptual anchor of the talk.

For the within-city held-out design, explain that training and test cells come from cities that are represented in the modeling data. The question is: can the model identify hotspot structure when local city patterns are already represented?

For the city-held-out transfer design, explain that whole cities are withheld. The question is: can the model generalize to places it has not seen?

Present the within-city design as informative for same-city screening, infill, or settings where the city is represented in training. The transfer design is necessary when the intended use case is applying to new cities.

Transition: "Under the within-city question, the signal is quite strong."

## Slide 4 - Within-City Held-Out Evaluation

State the data caveat carefully: the partner table contains 30 cities by 2 model families, with sklearn-style thresholded classification metrics. The support counts appear consistent with about 30% of canonical cells held out per city, so this deck treats the table as a within-city or row-level held-out evaluation unless the original partner code says otherwise.

Focus on hotspot-class metrics rather than accuracy. Accuracy is high partly because the non-hotspot class is about 90% of cells. Precision, recall, and F1 for the hotspot class are more informative.

Main message: under this evaluation question, the models show a clear learnable hotspot signal, especially random forest. Random forest has much higher mean hotspot precision, recall, and F1 than logistic regression across the partner summary.

Transition: "Now compare that with the harder question: what happens when the city is not represented during training?"

## Slide 5 - City-Held-Out Transfer Evaluation

Explain that the repo benchmark holds out whole cities across 5 outer folds, with 6 held-out cities per fold. All preprocessing, tuning, and fitting occur inside the training cities for each outer split.

Read the result as a balanced contrast. Random forest improves pooled retrieval: pooled PR AUC is `0.1486` versus `0.1421`, and recall at the top 10% predicted risk is `0.1961` versus `0.1647`. Logistic remains competitive by mean city PR AUC: `0.1803` versus `0.1781`.

Main message: transfer remains possible, but the gains are smaller and less uniform than in the within-city setting.

Transition: "The takeaway is not that one evaluation is better in all contexts. It is that they answer different questions."

## Slide 6 - What The Contrast Shows

Synthesize the two designs. Within-city evaluation shows that the predictors contain real hotspot signal. City-held-out evaluation shows that the same signal is not fully portable across cities.

Phrase the limitation objectively: models learn within-city hotspot structure more readily than they transfer across cities. The limitation is not that the models fail. It is that spatial, climate, vegetation, water, and urban-form relationships shift from city to city.

Close the slide with the practical implication. If the use case is filling in or screening within cities represented in training, within-city splits are informative. If the use case is applying to new cities, city-held-out validation is necessary.

## Slide 7 - Q&A

Use this as a clean stop. A good final sentence is: "Basic factors contain real hotspot signal, but transfer to unseen cities is the hard part."

## Likely Questions

### Are the partner results definitely from a 70/30 within-city split?

Not directly verified from partner code. The support counts are almost exactly 30% of canonical city row counts, and all 30 cities appear in the evaluation table, so the results appear consistent with a within-city or row-level 70/30 held-out evaluation. The deck phrases this as an inference.

### Why not compare the partner and repo scores directly as one leaderboard?

The metrics and evaluation questions differ. The partner table reports thresholded classification metrics, while the repo benchmark reports ranking and screening metrics under whole-city holdout. The point is the methodological contrast, not a single interchangeable score.

### Which model is better?

It depends on the evaluation question. Under the partner within-city held-out summary, random forest is much stronger on hotspot precision, recall, and F1. Under city-held-out transfer, random forest improves pooled retrieval and recall at top 10%, while logistic remains slightly higher on mean city PR AUC.

### What is the practical implication?

Match validation to deployment. Same-city screening can use within-city held-out evidence. Applying to cities not seen during training requires city-held-out validation.
