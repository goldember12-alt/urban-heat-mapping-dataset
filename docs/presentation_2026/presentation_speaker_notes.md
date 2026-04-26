# Speaker Notes

## Slide 1 - Cross-City Urban Heat Hotspot Prediction

We open with introductions and our title.

## Slide 2 - Research Question + Validation Design

Our central research question is: Can a model, given basic environmental and built-environment features, predict urban heat hotspot risk across U.S. cities? 

Before training any models, we first begin with construction of the dataset. We first define a comparable study area for each of 30 U.S. cities. For each city, we identified the Census urban area containing the configured city center, preserved that core urban geometry, and then buffered it by 2 km to create the study area. Within each study area, we project a 30 m grid in the city’s local UTM coordinate system.

For each grid cell, we assembled aligned geospatial predictors from multiple sources. NLCD supplied land-cover class and impervious surface percentage. A 3DEP DEM supplied elevation. NHDPlus hydrography was clipped to the study area and converted into distance-to-water features. AppEEARS AOIs were exported for each city in EPSG:4326, then used to acquire remote-sensing inputs for May-August vegetation and heat summaries: Landsat/AppEEARS NDVI and ECOSTRESS/AppEEARS daytime land surface temperature. These rasters and vector-derived layers were aligned back to the city’s 30 m master grid, producing cell-level values for imperviousness, land cover, elevation, distance to water, NDVI, LST, and the number of valid ECOSTRESS observations.

The final dataset was then assembled by merging the per-city feature tables. Open-water cells were dropped where land_cover_class == 11 (Open Water), and cells with fewer than 3 valid ECOSTRESS observations were removed when LST was available. After those filters, the hotspot label was recomputed within each city: hotspot_10pct = 1 if the cell fell in the top 10% of valid lst_median_may_aug values for that city, and 0 otherwise. Therefore we define a hotspot as one of the hottest (top 10%) retained cells within a given city, relative to that city's land surface temperature distribution.

The final parquet contains 71,394,894 rows across 30 cities.

After construction of the dataset, we separate two evaluation settings that answer different questions:

- Within-city held-out cells: the city is represented during model development, and the model is evaluated on held-out cells from those same cities.
- City-held-out transfer: whole cities are withheld, and the model is evaluated on cities that were not seen during training.

Our goal is to observe differences in model performance between these evaluation methods. Can a model successfully predict hotspot % when trained on local city cells and tested on held-out cells in that same city? Can a model generalize patterns across cities to accurately predict hotspots in cities it hasn't seen before?

The top-left "Predictor Set" block lists the six first-pass predictors used for hotspot modeling:

- imperviousness, representing built surface intensity
- land cover, representing categorical surface type
- elevation, representing topographic context
- distance to water, representing proximity to cooling water bodies
- NDVI, representing vegetation greenness during May through August
- climate group, representing broad city climate context

These predictors are deliberately basic and leakage-safe (test set does not influence training). The first-pass hotspot models do not use the target itself, LST, ECOSTRESS pass count, cell ID, city ID, city name, or cell coordinates as predictive features. LST is used to define the target, not to predict it.

The top flow maps the predictor set into "Hotspot Risk." The risk score is a model output: a higher value means the model ranks a cell as more likely to be in the city-specific hottest decile. 

The bottom-left "Within-City Held-Out Cells" panel shows train and held-out cells mixed within cities. These colored dots are a simplified cell/city schematic, not a literal map of our design. Here, each city contributes training cells and held-out cells. The model can therefore learn from local city conditions while being tested on different cells from those same cities. This is useful for same-city screening or infill use cases, where the city of interest is already represented in the training data.

The bottom-right "City-Held-Out Transfer" panel shows whole cities withheld in outer folds. We use 5 outer folds and 6 unseen cities per fold, as represented in the dot diagram. In this design, preprocessing, tuning, and fitting are restricted to training-city rows for each fold, and the held-out cities remain unseen until evaluation. This design is the relevant one if the deployment question is: can a model trained on some cities transfer to a city that was not included during training?

Within-city results and city-held-out transfer results are both informative, but should not be interpreted as interchangeable evidence of model success; they're answering different questions. A model can look strong when it has seen examples from every city and still struggle when asked to transfer to a new city.

## Slide 3 - Modeling Section: Logistic vs Random Forest

This slide compares the two model families visually. Both panels use the same six input features from Slide 2. We show that the models differ in how they convert the same feature contract into a hotspot-risk score.

The left panel shows logistic regression. The feature chips feed into a weighted-sum diagram. Each feature receives a learned contribution after preprocessing. Numeric features such as imperviousness, elevation, distance to water, and NDVI are imputed and scaled inside the modeling pipeline. Categorical features such as land cover and climate group are encoded inside the pipeline. Under leakage-safe city-held-out evaluation, those preprocessing steps must be fit using training-city rows only, then applied to held-out-city rows.

The weighted bars here are not meant to show the final fitted coefficient values. They are a simplified schematic representing how logistic regression combines feature contributions into one global additive score. The "Risk Score" pill is the model output used to rank cells. In plain terms, the logistic model asks whether one relatively smooth, global relationship between the six predictors and hotspot probability is enough to identify high-risk cells.

The right panel shows random forest. The same feature chips feed into split trees, which represent threshold-type decisions. A random forest builds many trees, each of which partitions the predictor space into regions. The small vote dots represent the fact that individual trees produce predictions that are averaged into the final risk score.

The random-forest diagram is more branching than the logistic diagram because random forests can represent nonlinear thresholds and feature interactions. For example, vegetation may matter differently in high-impervious cells than in lower-impervious cells, or distance to water may have different implications by land cover or climate group.

The key comparison is model form, not input contract. Logistic regression tests a global additive relationship, while random forest tests whether thresholded, nonlinear, and interaction-like structure improves hotspot ranking. Both are evaluated against the same conceptual target and the same first-pass predictor set.

## Slide 4 - Results Side by Side

Here, we contrast the within-city held-out question on the left and the city-held-out transfer question on the right.

The left chart, "Within-City Held-Out Cells," summarizes verified 70/30 within-city held-out results across the 30 cities. Metrics are thresholded class-1 metrics for the hotspot class. "Class 1" means cells labeled as hotspots under `hotspot_10pct`. Because the hotspot class is ~10% of cells, these class-specific metrics are more informative than raw accuracy.

The left chart's x-axis is "Mean Hotspot-Class Metric." It averages each metric across cities:

- Precision measures, among cells the model predicts as hotspots, what fraction are actually hotspots. Higher precision means fewer false positives among predicted hotspot cells.
- Recall measures, among actual hotspot cells, what fraction the model recovers. Higher recall means fewer missed hotspot cells.
- F1 is the harmonic mean of precision and recall, so it rewards a model only when both are reasonably strong.

The within-city results show a large random-forest advantage. Mean hotspot precision is about 0.731 for random forest versus 0.389 for logistic. Mean hotspot recall is about 0.343 for random forest versus 0.073 for logistic. Mean hotspot F1 is about 0.448 for random forest versus 0.108 for logistic. Under this within-city held-out design, the random forest is much better at recovering hotspot cells while maintaining stronger precision.

The right chart, "City-Held-Out Transfer," summarizes retained repo city-held-out benchmark runs. The split is 5 outer folds with 6 held-out cities per fold. The chart uses retained sampled benchmark runs rather than all 71,394,894 rows. Sampling is needed for computational reasons: full nested or repeated city-held-out model tuning on the complete cell-level dataset is too expensive on the available workstation. The retained comparison uses a 5,000 rows-per-city cap for the shown logistic and random-forest runs. The logistic retained rung used the full preset with 20 parameter candidates and about 400 estimated inner fits; the random-forest frontier used a targeted follow-up search with 8 candidates and about 120 estimated inner fits.

The right chart uses ranking and screening metrics rather than thresholded classification metrics:

- Pooled PR AUC is the area under the precision-recall curve after pooling held-out-city predictions across the outer folds. It evaluates how well the model ranks hotspot cells above non-hotspot cells over all possible thresholds. Because it is pooled, it is influenced by the distribution of held-out cells in aggregate.
- Mean City PR AUC computes PR AUC separately by city and averages the city scores. This gives each held-out city equal weight, so it is a city-level transfer summary rather than a pooled cell-level summary.
- Recall @ Top 10% asks: if we select only the top 10% of cells by predicted risk in each held-out setting, what fraction of true hotspot cells are captured? This matches the operational screening idea of prioritizing a limited top-risk set.

In city-held-out transfer, the differences are much smaller and more mixed than in the within-city panel. Random forest is slightly higher on pooled PR AUC, about 0.1486 versus 0.1421. Random forest is also higher on recall @ top 10%, about 0.1961 versus 0.1647. Logistic is slightly higher on mean city PR AUC, about 0.1803 versus 0.1781. Random forest has a clear edge in top-decile screening, but the other two results are so close, particularly mean city PR AUC, that there isn't strong evidence to suggest an advantage for either model.

Note: It is valid to compare logistic versus random forest within the left panel because the models are evaluated under the same within-city metrics. It is valid to compare logistic versus random forest within the right panel because the models are evaluated under the same city-held-out metrics. It is not valid to compare a left-panel precision or F1 value directly to a right-panel PR AUC value, because those metrics measure different things on different scales under different validation designs.

The defensible conclusion is: within-city held-out screening shows strong learnable hotspot signal, especially for random forest, but whole-city transfer is harder and more mixed. The deployment use case determines which evaluation should be trusted. Same-city screening can lean on within-city evidence; applying to unseen cities requires city-held-out validation.

## Slide 5 - City-Level Signal Shifts Across Evaluation Designs

This slide asks whether city-level success under within-city evaluation predicts city-level success under city-held-out transfer. Each point is one city. The colors show climate group: hot-arid, hot-humid, or mild-cool.

The left panel, "RF City Ranking Shifts," compares within-city RF hotspot F1 on the x-axis with city-held-out RF PR AUC on the y-axis. A strong positive relationship would mean that cities where random forest performs well under the within-city split also tend to be cities where random forest transfers well under whole-city holdout. The plotted Pearson correlation is about 0.08, which is very, very weak. That means within-city RF F1 is not a strong guide to city-held-out RF PR AUC.

The right panel, "Retrieval Signal Shifts," compares within-city hotspot recall on the x-axis with city-held-out RF recall @ top 10% on the y-axis. A strong positive relationship would mean that cities where random forest recovers many hotspots under within-city testing are also cities where the transferred model recovers many hotspots in the top-risk decile. The plotted Pearson correlation is about 0.03, even weaker.

The scatterplots help explain why the Slide 4 results should not be collapsed into one model ranking. A city can look comparatively easy under within-city held-out testing because the model has access to examples from that city during training. That does not guarantee that the same city's hotspot structure is portable from other cities. Whole-city transfer depends on whether relationships among imperviousness, land cover, vegetation, elevation, water proximity, and climate align with the relationships learned from the training cities.

The slide also separates "model can learn signal" from "signal transfers cleanly." The weak correlations do not mean the predictors are useless; they simply mean that the apparent strength of the signal changes when the evaluation design changes. This supports the practical guidance from Slide 4: choose validation based on the intended use case.

## Slide 6 - Held-Out Denver Map Example

This slide examines a spatial example for city-held-out evaluation. The maps use retained held-out prediction points for Denver from the random-forest frontier checkpoint. Denver is a representative hot-arid example in the retained held-out-city map outputs. Denver is placed in this group not because it is desert-like but because it is much closer to Albuquerque, Salt Lake City, Reno, and other dry western metros than the other climate groups. It provides valuable variation within the dry group due to its high elevation.

The left map, "Predicted Top-Decile Risk," marks the cells selected by the model as the top-decile risk set. This is the spatial version of a top-risk screening output: if a user can only inspect or prioritize a limited share of cells, these are the cells the model places highest. 

The middle map, "Observed Hotspot Cells," marks the true `hotspot_10pct` cells from the observed LST-derived target. This is the benchmark reference for the held-out city. The city was not part of training for that outer fold, so agreement between the predicted and observed maps is evidence of transfer.

The right map, "Error Pattern," overlays the prediction and observation categories:

- True Positive: predicted top-decile risk and observed hotspot
- False Positive: predicted top-decile risk but not observed hotspot
- False Negative: observed hotspot but not predicted top-decile risk
- Other Cells: neither predicted top-decile risk nor observed hotspot

This slide shows both signal and error. The model captures some spatial hotspot structure, but false positives and false negatives remain spatially organized. False positives are clustered closer to the city center, while false negatives are structured further towards the edges. This is a reasonable result; features such as land cover correlate heavily with that exact pattern. The model may predict higher risk in higher density areas without considering more nuanced elements of the specific city, a direct result of it not having trained on that held-out city.

This map should be read as a spatial diagnostic for the transfer task. Because Denver was held out from training, agreement with the observed hotspot map shows what the model can recover from cross-city signal alone. The value of the figure is not that it produces a final Denver heat-risk layer, but that it reveals the geography of transfer: which high-risk cells are recovered, which hotspots are missed, and where the model overpredicts. In practical terms, this kind of output is useful for screening or prioritizing areas for follow-up, but it would still need local validation or calibration before being treated as a planning-grade heat-risk product.

## Slide 7 - Q&A

Our core takeaway is that basic environmental and built-environment factors contain real hotspot signal, but the strength and meaning of that signal depend on the evaluation design.

The short version is:

- Within-city held-out evaluation shows that the feature set can identify hotspot structure when cities are represented in training.
- City-held-out transfer shows that applying the same feature set to unseen cities is harder, more mixed, and computationally expensive to evaluate carefully.
- A model result should always be reported with the validation design, sample cap, model family, and metric definition.

## Likely Questions

### Why put the results side by side if the metrics differ?

The slide is comparing evaluation questions, not building one combined leaderboard. The left panel uses thresholded class-1 metrics from a verified 70/30 within-city held-out design. Precision, recall, and F1 are calculated after the model makes a hotspot/non-hotspot classification for held-out cells inside cities represented in the data. The right panel uses ranking and screening metrics from city-held-out transfer. PR AUC evaluates ranking quality across thresholds, and recall @ top 10% evaluates how many true hotspots are captured in a limited high-risk screening set.

The correct comparison is directional and methodological. Within each panel, logistic and random forest can be compared directly because they share the same metric definitions and validation design. Across panels, the magnitude of a precision value cannot be compared directly to the magnitude of a PR AUC value. What can be compared across panels is the pattern: random forest dominates under within-city held-out metrics, while city-held-out transfer is much closer and more mixed.

### Why is `hotspot_10pct` city-relative instead of an absolute temperature threshold?

The goal is to identify the hottest cells within each city's own surface-temperature distribution. Cities differ in climate, elevation, vegetation, urban form, and absolute seasonal temperatures. A single absolute temperature cutoff would mix local hotspot structure with regional climate differences. A city-relative top-decile target keeps the task focused on intra-city heat inequality: which cells are unusually hot for that city?

### Why not use LST, ECOSTRESS pass count, city ID, or coordinates as predictors?

LST is used to define the target, so using it as a predictor would leak the answer. ECOSTRESS pass count is a data-quality/support variable rather than a stable urban-form predictor. City ID and city name can let a model memorize city-specific prevalence or artifacts rather than learn transferable relationships. Coordinates can also act as a spatial shortcut, especially in within-city settings. The first-pass feature contract is intentionally restricted to safer predictors that are more plausible for transfer.

### Which model is better?

It depends on the evaluation question. Under the verified within-city 70/30 held-out summary, random forest is clearly stronger on hotspot precision, recall, and F1. Under the retained city-held-out transfer benchmark, random forest is slightly stronger on pooled PR AUC and recall @ top 10%, while logistic is slightly stronger on mean city PR AUC. The most accurate statement is that random forest is stronger for same-city hotspot screening in these results, while new-city transfer remains close enough that metric choice and city weighting matter.

### Why does city-held-out evaluation require sampling?

The canonical final dataset has 71,394,894 cell rows across 30 cities. City-held-out tuning is not a single model fit: each outer fold holds out six cities, and model selection must happen inside the training cities for that fold. For the retained runs shown in the deck, the logistic 5k benchmark used 20 candidates and about 400 estimated inner fits; the random-forest frontier used 8 candidates and about 120 estimated inner fits. Running that nested process over the full row set would be much more expensive in time and memory. The sampled retained benchmark preserves the grouped-city evaluation structure while keeping the computation feasible.

### What does the weak correlation on Slide 5 mean?

It means that city-level performance under within-city testing does not reliably rank cities by city-held-out transfer performance. A city that is easy when local examples are present in training is not necessarily easy when the model is trained only on other cities. This is evidence that the evaluation design changes what "good performance" means.

### Why use Denver for the map example?

Denver is a representative hot-arid held-out city from the retained map outputs. The purpose is to show the spatial meaning of the city-held-out task, not to claim that Denver is uniquely important or that the model is optimized for Denver. The map example gives a concrete view of predicted top-decile risk, observed hotspots, and spatial error categories.

### What is the practical use of this modeling workflow?

For cities represented in training, within-city evaluation supports same-city screening and prioritization. For cities not represented in training, the city-held-out workflow is the relevant evidence. A transfer model can provide a first-pass risk ranking, but the map should be treated as a screening product that needs local validation and careful interpretation before planning or policy use.

### What are the main limitations?

The first-pass feature set is intentionally simple. It does not include every possible urban heat driver, such as detailed morphology, building materials, anthropogenic heat, tree canopy at all relevant scales, or local meteorology. The retained city-held-out comparison is sampled for computational feasibility. The partner within-city results and repo city-held-out results answer different evaluation questions and use different metrics. The maps are point-based model outputs, not independently validated intervention recommendations.
