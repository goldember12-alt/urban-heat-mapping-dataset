# Speaker Notes

These notes are written as live speaking guidance for a short technical talk. The slides stay intentionally sparse; the explanation belongs here.

## Slide 1 - Cross-City Urban Heat Hotspot Prediction

Open by framing this as a transfer problem, not just an urban heat mapping project. The dataset is large, but the reason it matters is simple: if a model only works inside cities it has already seen, it is not very useful for screening new cities. Tell the audience that the talk will move quickly from the question, to the evaluation design, to the main result, to one held-out map example.

Use the subtitle panel to orient the room. Mention that the benchmark covers `30` U.S. cities, about `71.4` million 30 m cells, and a hotspot screening target defined within each city. Do not spend time on data engineering details yet. The goal on this slide is to set the scale and make the audience curious about whether transfer is possible at all.

Transition: “So before we get into models, the first thing to ask is why transfer is actually the hard part.”

## Slide 2 - Why Transfer Matters

Start with the applied motivation in one sentence: urban heat matters for health, infrastructure, and planning. Then pivot immediately to the harder statistical point. Cities differ in climate regime, vegetation, land cover mix, water access, and built form. A model can look good if it borrows city-specific structure from the same place it was trained on, but that is not the deployment problem we care about.

Read the research question out loud exactly once. Then add the interpretation that the benchmark asks whether a model trained on some cities can identify hotspots in a city it has never seen. Use the bottom banner to make the contrast explicit: this is a transfer benchmark, not same-city interpolation.

Transition: “That question only means something if the data layout and the validation design actually enforce it.”

## Slide 3 - Data + Evaluation Design

Walk the audience across the cards from left to right. There are `30` cities, `71,394,894` rows, and each row is one `30 m` grid cell. The target is `hotspot_10pct`, meaning the cell falls in the hottest within-city decile after the project’s row filtering rules. Keep that definition short on the slide, but explain here that the label is intentionally city-relative because absolute temperature levels differ a lot across climates.

Then move to the two larger boxes. The analytic unit box tells the audience what the predictors represent: built form, terrain, water access, vegetation, and climate context aligned to a shared city grid. The benchmark box is the validity check: `5` outer folds, `6` held-out cities per fold, and preprocessing, tuning, and model fitting happen on training-city rows only. Make the audience hear that last part, because it is what stops leakage.

If you want one extra sentence, say that the final dataset was already audited before modeling, so the benchmark sits on top of a reproducible pipeline rather than slide-only summaries. That helps reassure the room without dragging them into pipeline mechanics.

Transition: “Once the split is fixed, the comparison becomes a clean question about model class.”

## Slide 4 - Models + Main Result

Point to the left panel first. The logistic regression equation is the linear probabilistic baseline: every predictor shifts hotspot log-odds additively. The random forest equation is the nonlinear alternative: an average across many trees that can pick up interactions and threshold behavior. Mention that both models use the same transfer-safe predictor set and that LST itself is excluded from the inputs, because it is part of the target construction.

Then shift to the benchmark figure and read the three callouts rather than every bar. The main pooled ranking result favors random forest: pooled PR AUC is `0.1486` for RF frontier versus `0.1421` for the retained logistic `5k` rung. The operational retrieval result also favors RF: recall in the top predicted decile is `0.1961` versus `0.1647`. But the mean city PR AUC still slightly favors logistic at `0.1803` versus RF `0.1781`, which is why the story is “RF helps, but not uniformly,” not “RF wins everywhere.”

Explain the metrics in plain language. PR AUC matters because the hotspot label is imbalanced at roughly `10%` positives. Recall at the top `10%` matters because, if this became a screening tool, we care about whether the highest-risk cells actually contain true hotspots. Keep the caveat visible but secondary: these are retained sampled all-fold checkpoints, not exhaustive scoring across all `71` million rows.

Transition: “The chart tells us the aggregate story. The map shows what success and failure look like inside one held-out city.”

## Slide 5 - Held-Out Denver

Orient the audience left to right. The first panel is predicted hotspot cells, the second is the true hotspot pattern, and the third is the categorical error map. Tell them not to judge this as a perfect reconstruction. That is not the standard. The more important question is whether errors look spatially meaningful or whether they look like noise.

The main message is that misses remain spatially structured rather than random. There are coherent corridors and clusters where the model is concentrating risk, and the error map is not just isolated salt-and-pepper mistakes. That is encouraging because it suggests the model is learning transferable urban heat structure even when it misses individual cells. If useful, add that Denver was selected as a representative hot-arid held-out city from the retained RF frontier run.

Transition: “So the answer is not ‘problem solved,’ but it is stronger than ‘nothing transfers.’”

## Slide 6 - Takeaway

Deliver the conclusion in one sentence: cross-city hotspot transfer looks feasible, but performance is still uneven across climates. Then use the three panels to close the loop. The best current signal is that RF improves pooled hotspot retrieval and recall at the top-risk decile. The key caveat is that the headline comparison is still the retained sampled all-fold benchmark path. The next step is to run broader scoring and diagnose why transfer behavior changes across climate groups rather than assuming one model will dominate everywhere.

End with the practical implication. The project now supports the idea of a transferable screening model, but the unresolved statistical question is consistency. That gives the audience a clear answer to the research question and a believable reason the work is not finished.

## Likely Questions

### Why not use a random train/test split over all cells?

Because that would place rows from the same city in both training and testing and would overstate how well the model transfers to a truly unseen city.

### Why emphasize PR AUC and recall at top 10%?

The label is intentionally imbalanced, so retrieval-oriented metrics are more informative than accuracy. Recall at the top predicted decile also matches the screening use case more closely.

### Did the benchmark use all `71.4` million rows?

No. The retained headline comparison is sampled all-fold evaluation, with matched row caps such as `5,000` rows per city in the slide’s logistic versus RF comparison.

### Does the Denver map prove the model is ready for deployment?

No. It is evidence that the model learns spatial structure in a held-out city, but it does not remove the need for broader benchmarking or climate-specific diagnosis.
