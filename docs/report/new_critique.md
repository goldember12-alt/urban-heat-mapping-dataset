# STAT 5630 Final Report Draft — Short Critique of New Version

## Overall judgment

This edition is substantially stronger. As a blind-reader, I would now read it as a coherent, defensible final-report draft rather than a report that is still structurally underdeveloped. The biggest improvements are that the narrative is now clearly about **screening / transfer ranking**, not generic “prediction”; the “30 m dataset” caveat is much better handled; sampling is explained as an inferential design choice rather than only a computational shortcut; and the conclusion is appropriately restrained.

My harsh read: this is close to submission-ready on content, but not yet maximally strong.

The central story now works:

> Public non-thermal geospatial predictors contain limited but real cross-city hotspot-ranking signal; simple surface-intensity baselines are hard to beat; nonlinear random forest helps mainly in selected hot-arid cities; therefore the project contributes a transfer-screening benchmark, not a deployment-ready heat-risk model.

That is a clean, honest, statistically mature argument.

## Highest-priority content fixes

### 1. The partner-expansion space is now invisible

Earlier, the report had obvious partner TODOs. Now it reads as a finished solo-style report. That is not automatically bad, but given the intended partner expansion, the draft no longer makes clear where Nick’s contribution will enter or why it is substantively nontrivial.

You do **not** need to add the partner material now, but the current draft no longer visibly reserves conceptual space for it. A blind reader would not think “this report is designed for a partner expansion”; they would think “this report is complete and maybe a little compact.”

Best fix: add one short transition sentence near the end of the methods or beginning of the discussion, something like:

> The results reported here establish the retained city-held-out benchmark; the partner extension will add complementary diagnostic analyses that help interpret why transfer performance differs across cities without replacing the headline benchmark.

That keeps the report whole while making the future contribution nontrivial.

### 2. The background is still slightly too source/pipeline-heavy before the research question

The background is much better than before, but it still spends a lot of space justifying data sources and geospatial construction before the reader fully understands the statistical stakes. The transfer gap paragraph is strong, but I would sharpen the contrast earlier.

Current implicit logic:

> urban heat matters → LST matters → predictors are plausible → AppEEARS → transfer gap

Better blind-reader logic:

> urban heat matters → many studies map/correlate heat locally → the statistical question is whether relationships transfer to unseen cities → therefore the dataset and validation design matter

The AppEEARS paragraph is useful, but it feels slightly operational for main-text background. It is not wrong; it just reads more like “we did a careful data pipeline” than “this is the scientific/statistical motivation.”

### 3. The city-selection rationale is improved but still under-justified

The new language that the 30 cities are a “purposive benchmark set rather than a probability sample” is excellent. But a harsh reader may still ask: **why these 30 cities specifically?**

You explain why 10/10/10 climate balance is useful, but not whether cities were selected because of data availability, size, regional representation, computational feasibility, recognizability, or coverage of urban forms. This matters because the external-validity caveat depends on the selection rule.

Add 2–3 sentences in Dataset Construction:

> Cities were selected to provide broad geographic and climate variation while remaining feasible for a standardized data-acquisition and modeling pipeline. The set should therefore be treated as a benchmark panel rather than a statistically representative sample of U.S. urban areas. This affects external validity: performance differences across the selected cities are informative, but they do not estimate national average performance.

You already say pieces of this; the missing part is the actual selection rationale.

### 4. The sampling explanation is now good, but it reveals a deeper weakness

The sampling paragraph is honest and useful. But now that you say the sample preserves prevalence and city balance but not full spatial density, all within-city clustering, or exact full-population feature distributions, the reader may wonder whether the model is being evaluated on an artificially balanced, spatially thinned benchmark that differs from deployment.

That is okay, but you should explicitly say why this still answers the research question. One sentence would help:

> Because every city contributes the same number of positives and negatives, the retained benchmark is best interpreted as a controlled comparison of model ranking behavior across cities, not as an estimate of full-map operational performance.

This would make the sampling design feel intentional instead of apologetic.

### 5. The results section is strong, but the conclusion could be even more memorable

The conclusion paragraph is good. The line “city-held-out validation therefore changes how urban heat model performance should be interpreted” is especially strong.

But the report still lacks a single compact final answer to the primary research question. The reader gets it, but you can make it sharper:

> Answer: yes, but only weakly and unevenly. The models can rank local hotspots above chance in held-out cities, but the improvement over simple imperviousness and land-cover baselines is modest and concentrated mainly in hot-arid cities.

That exact sentence, or something close, should appear near the start or end of Section 5.

## Figure critique

### Figure 1: Study City Locations

Much improved. City labels and climate colors make it actually useful now. It supports the design claim.

Remaining issue: it shows geography, but not fold composition. Since Appendix Table A4 handles folds, this is acceptable. Main figure is effective.

### Figure 2: Dataset Construction Workflow

Also improved. The input layers now correctly mention MODIS/Terra NDVI and ECOSTRESS LST. The figure supports the pipeline narrative well.

Remaining issue: it still slightly oversells “30 m cells” visually because the figure does not visually distinguish native source resolution from aligned grid resolution. But the text now handles this, so I would not spend more effort unless you want perfection.

### Figure 3: City-Held-Out Evaluation Design

This is one of the most important figures and it works. It directly supports the statistical-methods argument. The “no city appears in both training and testing” line is excellent.

No major content issue.

### Figure 4: Benchmark Metric Comparison

This is now much better because the prevalence reference line is visible and explained. It supports the main argument that improvements are modest.

Remaining issue: the x-axis labels are small and hard to read, but that is more formatting than content. Content-wise, the figure is effective.

### Figure 5: City-Level RF Minus Logistic Deltas

This is substantially improved. Sorting by PR AUC delta and labeling cities makes the heterogeneity argument visible. It now earns its place in the main report.

Remaining issue: because the recall panel uses the same city order as PR AUC, some recall-specific patterns are harder to see. That is fine because the point is paired city comparison, not separately optimized recall ranking.

### Appendix Figure A2: Feature Importance

This is useful but still potentially risky. The cautionary caption is good. However, the logistic coefficient panel may be hard for a blind reader to interpret because land-cover codes are not translated into land-cover names. If you keep it, consider adding a note somewhere that land-cover classes are encoded NLCD categories and coefficient signs depend on the reference category.

### Appendix Figure A3: Denver Map

Still the weakest figure. Moving it to the appendix was the right decision. It is illustrative but not central. The problem is that it is visually interesting but analytically underexplained: why Denver? why this sample? what should I learn from the map beyond “errors cluster spatially”?

It is acceptable as an appendix figure. I would not move it back to the main text unless you add a more pointed interpretation.

## Is any obvious figure still missing?

The most useful missing figure would be a **per-city PR AUC plot for the best model**, not just RF-minus-logistic deltas.

Figure 5 shows model comparison, but not absolute performance by city. A blind reader still cannot easily see whether the hot-arid gains happen in cities where performance is actually good, or merely where logistic was worse. A simple bar/dot plot of random-forest city PR AUC, colored by climate group, with a 0.10 reference line, would be highly illustrative.

Second-best missing figure: **full LST or hotspot map for one city with predictor context**, but that may become too geospatial and distract from the statistical report.

Given space, the per-city absolute performance plot is the one I would add if adding only one.

## Submission-readiness judgment

Content-wise: **yes, this is now close to submission-ready.**

Harsh grade estimate on content only: **A-/B+ range currently**, with a plausible **A-level** if the partner expansion adds real diagnostic value and does not dilute the clean benchmark story.

The report’s main remaining vulnerability is not that anything is obviously wrong. It is that the current version is very careful and defensible, but slightly conservative. The partner addition needs to feel like it deepens the interpretation rather than just appending extra results.

The cleanest role for that expansion is:

> diagnose why performance varies across cities, especially why hot-arid cities show stronger RF gains while humid/mild-cool cities do not.

That would directly serve the narrative rather than becoming an unrelated add-on.
