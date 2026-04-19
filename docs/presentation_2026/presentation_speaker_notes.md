# Speaker Notes

These notes are written as live speaking guidance. The slides are now more data-forward, but the explanation still belongs here.

## Slide 1 - Cross-City Urban Heat Hotspot Prediction

Open by saying the talk is about one research question and two evaluation designs. The research question is whether basic environmental and built-environment factors can predict urban heat hotspot cells.

Set an objective tone immediately: the two evaluation designs answer different applied questions. One asks about identifying hotspot structure in cities that are represented in training. The other asks about transferring to cities the model has not seen.

Transition: "The setup slide puts the target, predictors, and validation questions on the same page."

## Slide 2 - Research Question + Validation Design

Use this slide as the setup for the rest of the talk. Walk through the six first-pass predictors: imperviousness, land cover, elevation, distance to water, NDVI, and climate group. Mention that the model score is for the `hotspot_10pct` target, where a cell is in the hottest 10% within its city after filtering.

Close the slide by contrasting the two evaluation questions. Within-city held-out cells ask whether the model can recover hotspot structure where the city is already represented during training. City-held-out transfer asks whether the model can generalize to places it has not seen.

Transition: "Given that setup, the next question is what the models are actually doing."

## Slide 3 - Modeling Section: Logistic vs Random Forest

This slide explains the two model families visually.

Begin by pointing out that the same six predictors appear in both panels: imperviousness, land cover, elevation, distance to water, NDVI, and climate group. Both models exclude the label, LST, city identifiers, and coordinates as predictors.

For logistic regression, use the left panel's flow: the features receive learned weights, those contributions combine into a weighted sum, and that score becomes the model's hotspot-risk score. In plain language, logistic regression asks whether one global additive relationship across the predictors is enough.

For random forest, use the right panel's flow: the same features are reused in many split rules, each tree casts a vote, and the votes are averaged into a hotspot-risk score. In plain language, random forest asks whether nonlinear thresholds and interactions among imperviousness, vegetation, water proximity, land cover, elevation, and climate improve hotspot identification.

Transition: "Now we can compare the two evaluation questions with the same model families."

## Slide 4 - Results Side By Side

This is the main result contrast.

On the left, describe the partner results as a within-city or row-level held-out evaluation, based on support counts appearing consistent with about 30% of cells held out per city. The table reports thresholded hotspot-class metrics. Under that evaluation question, random forest is much stronger than logistic on mean hotspot precision, recall, and F1.

On the right, describe the repo benchmark as city-held-out transfer: 5 outer folds with 6 held-out cities per fold. Here the gains are smaller. Random forest improves pooled PR AUC and recall at the top 10% predicted risk, but logistic remains slightly higher on mean city PR AUC.

The point is not that one design should replace the other. The point is that the evaluation question changes what performance means.

Transition: "The city-level view shows why the two summaries should not be collapsed into one leaderboard."

## Slide 5 - City-Level Signal Shifts Across Evaluation Designs

Each point is one city. The left panel compares within-city RF hotspot F1 with city-held-out RF PR AUC. The right panel compares within-city RF hotspot recall with city-held-out RF recall at the top 10%.

The relationships are weak, which reinforces the central message. A city that looks easier when its local patterns are represented during training is not necessarily easy when the model has to transfer to it as a new city.

Use the climate colors as visual context rather than a definitive climate conclusion. The key statement is methodological: within-city strength and new-city transfer are related but not interchangeable.

Transition: "The final content slide makes that transfer task spatial rather than tabular."

## Slide 6 - Held-Out Denver Map Example

Use this as a visual example of what the held-out-city benchmark is evaluating. Denver was selected as a representative hot-arid held-out city from the retained random-forest frontier checkpoint.

The three maps show predicted top-decile hotspot risk, observed hotspot cells, and the categorical error pattern for a city that was not part of training in that outer fold.

Close with the implication: the model does recover some spatial hotspot structure, but the false positives and false negatives show why transfer should be evaluated city by city rather than assumed from within-city screening.

## Slide 7 - Q&A

Use this as a clean stop. A good final sentence is: "Basic factors contain real hotspot signal, but transfer to unseen cities is the hard part."

## Likely Questions

### Are the partner results definitely from a 70/30 within-city split?

Not directly verified from partner code. The support counts are almost exactly 30% of canonical city row counts, and all 30 cities appear in the evaluation table, so the results appear consistent with a within-city or row-level 70/30 held-out evaluation. The deck phrases this as an inference.

### Why put the results side by side if the metrics differ?

Because the slide is comparing evaluation questions, not constructing a single combined leaderboard. The labels and notes make clear that thresholded hotspot metrics and transfer ranking metrics should be read within their own blocks.

### Which model is better?

It depends on the evaluation question. Under the partner within-city held-out summary, random forest is much stronger on hotspot precision, recall, and F1. Under city-held-out transfer, random forest improves pooled retrieval and recall at top 10%, while logistic remains slightly higher on mean city PR AUC.

### What is the practical implication?

Match validation to deployment. Same-city screening can use within-city held-out evidence. Applying to cities not seen during training requires city-held-out validation.
