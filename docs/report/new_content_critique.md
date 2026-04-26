# Harsh Content Critique of New Final Report Draft

**File reviewed:** `stat5630_final_report_draft(1).pdf`  
**Review stance:** harsh blind-reader review. I am not granting credit for unstated project history, repository knowledge, prior conversations, or what the authors intended. I am evaluating what the submitted report itself communicates.

## Bottom-line grade under harsh reading

**Current content grade: B / B- range.**

This version is meaningfully stronger than the prior draft. The central framing has improved from “prediction” to “screening/ranking,” the results are more honestly interpreted, the no-skill reference is now present, the model comparison is less overclaimed, and the validity paragraph is much more submission-ready. However, the report still has several content-level weaknesses that would prevent it from feeling fully polished to a blind statistical-machine-learning reader:

1. **The narrative is now cautious, but sometimes so compressed that the core scientific contribution feels under-defended.** The report repeatedly says “limited but real transferable ranking signal,” which is fair, but it does not always explain why this is still a worthwhile result.
2. **The partner-expansion space is not visibly structured.** The report no longer has obvious placeholders, but it also does not clearly set up a substantial second-author contribution. If partner material is coming later, the current draft should make it easier to insert that material without feeling bolted on.
3. **The figures are improved in concept but still uneven in evidentiary value.** Figure 1 is useful, Figure 3 is useful, Figure 4 is acceptable, but Figure 5 is currently a major missed opportunity because the city labels appear unreadable or absent. Figure 2 also appears to contain an outdated/inconsistent NDVI source label.
4. **The 30 m dataset claim needs more careful handling.** The report acknowledges MODIS NDVI is 500 m, but the title and repeated “30 m grid cell” language can still overstate the effective resolution of the predictors and target.
5. **The statistical-methods section is clear at a conceptual level but not fully satisfying as a machine-learning report.** It describes the evaluation design well, but does not sufficiently justify the sampling scheme, the target-rate stratification, the hyperparameter choices, or the absence of uncertainty intervals.
6. **The results section is honest but could be sharper about what exactly was learned.** It gives the numbers, but the interpretation of why the model succeeds/fails across climate groups is still too speculative and too lightly supported.

The report is no longer in “draft with obvious holes” territory, but it is also not yet in “this reads like a mature final submission” territory. It is close, but the remaining work is substantive.

---

## What works well

### 1. The title and research framing are much better

Changing the title from “Prediction” to **“Screening”** is the right move. The current results do not support a strong claim of high-accuracy prediction, but they do support a more modest screening/ranking benchmark. The title now matches the actual performance level and avoids overselling.

The primary research question is also much better:

> Can a model trained on a multi-city urban heat dataset rank 30 m grid cells by their likelihood of being among the locally hottest cells in cities that were entirely excluded from training?

This is specific, measurable, and aligned with PR AUC / recall@top10. It fixes one of the most important conceptual problems: the task is not “classify urban heat risk perfectly,” but “rank cells for local hotspot screening under city-held-out transfer.”

### 2. The report now owns the modesty of the results

The new results section is far more credible because it explicitly says the signal is **limited**, **heterogeneous**, and **only modestly stronger than simple surface-intensity baselines**. That is exactly the right level of humility. The report now says, in effect:

- random forest beats the no-skill and simple baselines on pooled PR AUC;
- the gain over impervious-only recall is small;
- logistic regression wins more city-level comparisons;
- random forest’s advantage is concentrated in hot-arid cities;
- this is not a deployment-ready model.

That is a mature interpretation. The previous danger was overclaiming a small PR AUC improvement; this version mostly avoids that.

### 3. The no-skill / prevalence reference materially improves the benchmark table

Table 3 is much stronger now that it includes a no-skill prevalence reference at 0.1000. Without that, readers had to infer the baseline PR AUC context. Now the reader can immediately see:

- no-skill PR AUC: 0.1000;
- impervious-only PR AUC: 0.1351;
- land-cover-only PR AUC: 0.1353;
- logistic 5k PR AUC: 0.1421;
- random forest 5k PR AUC: 0.1486.

This makes the “limited but real” interpretation much easier to believe. It also makes the smallness of the gain unavoidable, which is good. A strong report should not hide the scale of its improvement.

### 4. The new fold-level and city-level comparison tables are valuable

Tables 5 and 6 add important evidence that the RF improvement is not uniform. Table 5 shows random forest gains in some folds but losses in others. Table 6 shows that random forest wins only 9 of 30 city-level PR AUC comparisons and only 9 of 30 recall@top10 comparisons, despite its pooled PR AUC and pooled recall advantage.

That is a strong addition because it prevents the report from relying only on aggregate metrics. It also makes the climate-group heterogeneity claim more credible.

### 5. The validity paragraph is now one of the strongest parts of the report

The paragraph beginning “Validity can be organized into six parts” is very good. It is clear, direct, and appropriately skeptical. It addresses:

- leakage/internal validity;
- sampling validity;
- spatial validity;
- construct validity;
- external validity;
- model-comparison validity.

This directly responds to the assignment criterion asking for “sufficient discussions on the validity of the statistical methods.” It is one of the most submission-ready paragraphs in the draft.

### 6. The dataset construction narrative is coherent and mostly self-contained

The report does a good job explaining the 30-city design, buffered Census urban areas, local UTM grids, layer alignment, open-water removal, ECOSTRESS pass filtering, and within-city recomputation of `hotspot_10pct`.

A blind reader can understand the pipeline at a high level. That is a major strength.

---

## Highest-priority content problems

## 1. The report still needs a clearer “why this result matters despite modest performance” argument

The report is now appropriately cautious, but it sometimes risks sounding like the project failed softly. The main result is basically:

> We built a very large, carefully validated transfer benchmark; simple predictors contain some cross-city signal; random forest improves pooled performance modestly; performance is heterogeneous and strongest in hot-arid cities.

That is defensible. But the report needs to make the intellectual contribution more explicit. Right now, the reader can ask:

> If the best model only gets PR AUC 0.1486 and beats impervious-only recall by about one percentage point, why is this interesting?

The report gives pieces of the answer, but not a crisp synthesis. It should say more clearly that the contribution is not just “the model is good.” The contribution is something like:

- a reproducible 30-city transfer benchmark was created;
- city-held-out validation reveals that naive optimism would be inappropriate;
- non-thermal features do transfer, but weakly;
- simple built-intensity baselines are surprisingly competitive;
- nonlinear improvements are climate-dependent rather than universal;
- this suggests future urban heat ML work should report transfer validation and climate-stratified performance, not only random splits or single-city maps.

That is a real contribution. But the current draft does not state it forcefully enough. It spends many paragraphs saying what the model is not. It needs a stronger paragraph saying what the project **does establish**.

### Specific fix

Add a short synthesis paragraph near the end of the results section:

> The main contribution is therefore not a high-performing operational classifier, but a transfer benchmark showing that cross-city hotspot screening is possible yet fragile. The benchmark demonstrates that non-thermal public geospatial predictors carry some transferable signal, that simple imperviousness and land-cover baselines are hard to beat, and that nonlinear gains concentrate in hot-arid cities rather than generalizing uniformly. This makes the project useful as a methodological warning and baseline for future urban heat ML work: city-held-out validation changes the interpretation of model performance.

This would make the report feel more like a finished argument and less like a cautious list of caveats.

---

## 2. The partner-expansion space is not yet narratively shaped

You specifically said there should be room for partner expansion, and that it should be clear why missing content belongs to the partner and is not trivial. The current version no longer has visible `[PARTNER TODO]` placeholders, which is good for polish, but it also does not clearly reserve a nontrivial intellectual role for partner material.

A blind reader would not know that meaningful partner expansion is expected. They would simply see a report that is mostly complete but somewhat thin in certain areas.

The problem is not that the partner content is missing. The problem is that the draft does not yet create obvious “docking points” for partner content.

### Where partner expansion should logically fit

The most natural nontrivial partner expansions are not minor citation paragraphs. They are substantial modules:

#### A. Literature / domain grounding expansion

The background currently cites urban thermal remote sensing and validation literature, but it remains skeletal. A partner contribution could deepen:

- urban heat mapping literature;
- LST versus air-temperature interpretation;
- equity/planning motivation for hotspot screening;
- limitations of LST as exposure proxy;
- why vegetation, imperviousness, and land cover are physically meaningful predictors.

This would not be trivial if it adds a real conceptual bridge from urban heat science to the ML benchmark.

#### B. Dataset validity / remote-sensing construction expansion

This is probably the strongest partner-expansion target. The report has a huge dataset-construction effort, but still leaves several blind-reader questions unresolved:

- Why these 30 cities?
- How exactly were the climate groups assigned?
- How were the Census urban areas selected when city names and urban-area polygons do not perfectly align?
- What happens when the 2 km buffer includes non-urban land?
- What are the implications of aligning 500 m MODIS NDVI and ECOSTRESS LST to a 30 m grid?
- Why was May-August 2023 selected specifically?
- How robust is the ECOSTRESS pass-count threshold of 3?

A partner section could add serious credibility here.

#### C. Supplemental validation / diagnostic expansion

Another strong partner role would be supplemental diagnostics:

- within-city versus city-held-out comparison;
- per-city error patterns;
- feature-importance interpretation;
- held-out map interpretation;
- calibration or score-distribution diagnostics;
- spatial clustering of false positives/false negatives.

This would give the partner a nontrivial analytical role rather than “add a few citations.”

### Specific fix

Even if you do not add partner content yet, shape the narrative by adding transition sentences like:

> The benchmark results below focus on the retained six-feature city-held-out comparison. Additional diagnostic material, including richer spatial error interpretation and supplemental model diagnostics, is treated as an extension because it answers a different question from the headline transfer benchmark.

Or, near the end of Dataset Construction:

> Several construction choices—city selection, climate grouping, temporal window, sensor resolution, and ECOSTRESS pass-count filtering—are substantive validity decisions rather than mechanical preprocessing details. The main benchmark treats them as fixed design choices, while supplemental discussion can examine their implications for interpretation and future model extensions.

These sentences create space for partner expansion without leaving obvious holes.

---

## 3. The “30 m dataset” claim still needs more qualification

The title says **“A 30 m Dataset”**, and the report repeatedly says each row is a 30 m grid cell. That is technically true for the analytic grid, but the data sources are not all 30 m:

- MODIS/Terra NDVI is 500 m 16-day NDVI.
- ECOSTRESS LST is not 30 m native resolution.
- 3DEP 1 arc-second is roughly 30 m but not perfectly equivalent everywhere.
- Some vector-derived variables are summarized to cells.

The report adds a good note under Table 1 saying MODIS NDVI should be interpreted as an aligned warm-season vegetation summary rather than an independent 30 m optical observation. That is good, but not enough. This issue affects the title, the unit-of-analysis language, and the interpretation of 71.4 million rows.

A harsh reader could say:

> You do not have 71.4 million independent 30 m observations. You have 71.4 million analytic grid cells, many of which share coarse predictor values and spatially autocorrelated thermal labels.

The report does acknowledge spatial dependence, but the “30 m dataset” branding remains a little too confident.

### Specific fix

Use language like:

> The dataset is a 30 m analytic grid, not a claim that every source variable has independent 30 m native resolution. Coarser satellite products are aligned or summarized to this grid, so the 30 m cell is the modeling unit rather than the native resolution of every predictor.

This should appear in the main text, not only under Table 1. It is a construct-validity issue, not just a table footnote.

---

## 4. The sampling design is described, but not sufficiently justified

The methods section now states that the main comparison uses 5,000 rows sampled per city with target-rate stratification: 500 positives and 4,500 negatives per city, random state 42, with 120,000 training rows and 30,000 test rows per fold. This is a major improvement.

But a harsh reader still has questions:

1. Why 5,000 per city?
2. Why target-rate stratification rather than spatially stratified sampling?
3. Does target-rate stratified sampling preserve the land-cover, imperviousness, and spatial distributions of each city?
4. Does using the same sampled city preload for all folds introduce any limitation or variance issue?
5. Would the results be stable under a different random seed?
6. Since cities differ enormously in size, does equal sampled row count per city intentionally equalize cities, or does it distort the pooled metric relative to the full population?

The report currently treats sampling as a computational caveat. That is true, but incomplete. Sampling is also an inferential design choice. It changes what the benchmark estimates.

### Specific fix

Add a paragraph like:

> The sampled benchmark intentionally gives each city the same sampled row count, so the retained metrics should be interpreted as performance on a balanced city sample rather than as full-population scoring over every eligible grid cell. Target-rate stratification preserves the 10% positive prevalence in each sampled city, but it does not guarantee that spatial clusters, land-cover distributions, or neighborhood structure are represented exactly as in the full city. This makes the benchmark useful for model comparison under controlled computation, but full-city scoring or repeated samples would be needed to quantify sampling variability.

This would make the sampling caveat much sharper.

---

## 5. The methods section explains models, but not enough about model selection uncertainty

The report says logistic regression and random forest were tuned using grouped inner CV and reports candidate settings in Appendix Table A3. That is good. But the model-selection story is still thin.

Questions a blind reader may have:

- Were hyperparameter grids chosen before seeing results?
- Why these specific RF values: `n_estimators = 200, 300`, `max_depth = 10, 20`, `min_samples_leaf = 1, 5`?
- What does “targeted RF search” mean? Targeted based on what? A previous smoke run? If so, was that exploratory and could it bias the comparison?
- Did the random forest get more human tuning attention than logistic regression?
- Were both models given comparable search effort?
- Why is HGB mentioned only as future/supplemental but not in the main comparison?

The report does not need to become a hyperparameter diary, but it should say enough that the model comparison feels fair.

### Specific fix

Add a short fairness statement:

> Both headline models were selected using training-city-only inner cross-validation within each outer fold. The random-forest grid was a targeted follow-up around feasible settings identified during exploratory runs, so the RF result should be interpreted as a retained practical frontier rather than an exhaustive search over all nonlinear models. Logistic regression and random forest are compared as representative linear and nonlinear benchmarks under the same six-feature contract, not as proof that no other model class could perform better.

This would avoid overclaiming the RF comparison while explaining “targeted RF search.”

---

## 6. The climate-group interpretation is plausible but under-supported

The report says:

> One interpretation is that dry urban landscapes may have sharper nonlinear contrasts among vegetation, imperviousness, land cover, and LST, while humid and mild-cool cities may contain thermal patterns that are less well captured by the current six-feature benchmark.

This is plausible, but the report does not show enough evidence to support it beyond performance differences. It needs to be framed more carefully or supported with more diagnostics.

Right now, the reader could ask:

- Are hot-arid cities easier because their physical relationships are sharper?
- Or because the selected hot-arid cities are smaller, more homogeneous, or have different sampling distributions?
- Or because MODIS NDVI works differently in arid regions?
- Or because ECOSTRESS pass counts differ?
- Or because folds with certain cities happened to favor RF?
- Or because the six-feature contract omits key predictors for humid/mild-cool cities?

The report calls the explanation “a modeling interpretation, not a causal claim,” which is good, but still too hand-wavy.

### Specific fix

Add one sentence limiting the claim:

> The report does not test this mechanism directly, so the climate interpretation should be read as a hypothesis generated by the benchmark rather than an established explanation.

Even better, add a future-work item:

> Testing this hypothesis would require comparing feature distributions, LST distributions, and error maps by climate group, rather than relying only on performance deltas.

This would make the interpretation more rigorous.

---

## 7. The report needs a clearer distinction between “screening” and “planning action”

The report says the practical planning question is which local cells should be prioritized for closer inspection. That is reasonable. But it still occasionally gestures toward heat-mitigation investments and planning attention. Given the modest performance, the report should be careful not to imply that model outputs are ready to guide investments.

The correct chain is:

1. Model can weakly rank local hotspots in held-out cities.
2. This ranking could support screening or prioritization for further measurement.
3. It should not directly allocate mitigation resources.
4. It does not measure human exposure or vulnerability.

The draft says pieces of this, but it should make the chain explicit.

### Specific fix

In the conclusion, say:

> The intended use is preliminary screening: identifying candidate areas for additional data collection, field validation, or more detailed local modeling. The benchmark should not be interpreted as sufficient for allocating heat-mitigation investments without local validation and exposure/vulnerability data.

This would protect the report from an overreach critique.

---

# Section-by-section critique

## Title page

### What works

“Cross-City Urban Heat Hotspot Screening” is the right title phrase. It is more accurate than “prediction” and sets expectations appropriately.

### Remaining issue

“A 30 m Dataset” is still slightly risky because not every underlying source is 30 m. It is acceptable if the report clearly defines 30 m as the analytic grid, but the title alone could be read as implying all source data are 30 m. Consider:

> “A 30 m Analytic Grid Dataset and City-Held-Out Transfer Benchmark”

This is less elegant, but more defensible.

## Background Information

### What works

The background does a good job motivating urban heat as a spatially uneven planning problem and explaining why remote sensing is relevant. It also distinguishes LST from air temperature, which is essential.

The literature sequence is logical:

- Voogt and Oke for urban thermal remote sensing;
- Weng et al. for NDVI/LST relationship;
- Yuan and Bauer for impervious surface and NDVI;
- Roberts and Meyer for spatial/target-oriented validation.

### Main weaknesses

#### A. The literature review is still thin for a two-person final report

The literature review is serviceable but not rich. It reads more like a justification for selected features than a full background section. For a two-person project, this is exactly where partner expansion could add value.

The current literature does not yet deeply address:

- urban heat vulnerability or planning use cases;
- prior ML-based urban heat prediction studies;
- cross-city transfer in environmental/spatial ML;
- LST versus air temperature limitations in applied planning;
- why top-decile local hotspots are a meaningful target.

This is not fatal, but it is one of the clearest areas where the report could be stronger.

#### B. The background does not fully set up the “screening” concept

The title says “screening,” and the research question says “rank,” but the background could more explicitly explain why screening is valuable even when performance is modest. Screening is not the same as classification. The report should introduce screening as a lower-stakes, triage-oriented use case.

#### C. The “research gap is transfer” paragraph is good but could be more precise

The transfer gap is the report’s central argument. It deserves more emphasis. The report should more sharply contrast:

- random cell-level validation;
- within-city interpolation;
- city-held-out transfer.

This contrast appears later in Methods, but the Background should preview why this distinction changes the meaning of performance.

## Research Questions

### What works

This is one of the strongest sections. The primary research question is clear and testable. The secondary questions align with the models and metrics.

### Remaining weaknesses

#### A. Target population is still vague

The target population is described as:

> 30 m grid cells inside buffered Census urban-area study regions for the selected U.S. cities, with cautious extension to similar urban areas.

This is okay, but “similar urban areas” is vague. Similar how? Similar by climate group? U.S. cities? Census urban areas? Availability of AppEEARS data? Urban form? The report should not leave this undefined.

#### B. “Selected U.S. cities” requires more justification

The report states the cities are balanced across three broad climate groups. But a blind reader still does not know why these specific cities were chosen. Were they chosen for size, data availability, geographic spread, known heat relevance, convenience, or computational feasibility? This matters because the external-validity claim depends on the selection logic.

#### C. The top-decile target is well explained, but could use a sharper planning rationale

The report says top-decile hotspots are useful for prioritizing closer inspection. That is good. But it could make the target choice more explicit:

- Why 10% rather than 5%, 20%, or an absolute threshold?
- Is top 10% chosen for interpretability and class balance?
- Does top 10% correspond to a screening budget assumption?

The target is not wrong, but the threshold feels more asserted than justified.

## Dataset Construction

### What works

This section is coherent and much improved. It gives enough pipeline detail for a blind reader to understand the construction logic.

The best additions are:

- specific 2020 Census / NLCD 2021 / MODIS / ECOSTRESS product names;
- explicit May-August 2023 window;
- open-water removal logic;
- ECOSTRESS pass-count filtering;
- recomputation of hotspot label after filtering;
- warning that 71.4 million rows are not independent observations.

### Main weaknesses

#### A. City selection remains under-explained

This is probably the biggest dataset-construction gap. The report says 30 cities, 10 per climate group. But it does not explain selection criteria.

A harsh blind reader may wonder:

- Why these exact cities?
- Were they chosen before modeling?
- Were any cities excluded because data acquisition failed?
- Were cities selected to balance region, size, climate, or computational feasibility?
- Are the climate groups standard categories or author-defined bins?
- Why is Los Angeles “mild-cool” in this grouping, and what does that label actually mean?

The report does not need a long defense, but it needs a transparent selection statement.

#### B. The climate-group construction is not adequately documented

The report says hot-arid, hot-humid, and mild-cool are intentionally coarse, but not how cities were assigned. This is a content issue because climate group is both a predictor and a stratifier.

At minimum, the report should state whether climate groups were assigned using:

- Köppen climate classifications;
- NOAA climate normals;
- manual regional categorization;
- prior domain knowledge;
- simple project-defined grouping.

If climate group is manually assigned, say so and treat it as a coarse analysis label.

#### C. The 2 km buffer is plausible but not justified enough

The report says heat patterns and land-cover transitions do not stop at boundaries. That is true. But why 2 km specifically? Why not 1 km or 5 km? Does the buffer inflate some city areas more than others? Does it bring in rural/fringe land that changes the hotspot distribution?

This does not need a sensitivity analysis, but it needs a caveat.

#### D. Sensor-resolution alignment needs more main-text discussion

The MODIS NDVI note under Table 1 is good, but this issue belongs in Dataset Construction too. A 500 m NDVI value repeated across many 30 m cells changes the effective predictor resolution. This is not a small footnote.

#### E. ECOSTRESS temporal/sampling limitations are underdeveloped

The report says ECOSTRESS has irregular overpass timing and uses pass count. Good. But a blind reader might still ask:

- Are overpasses at comparable times of day across cities?
- Does daytime-only LST vary by acquisition time?
- Are some cities observed more often or under different seasonal/cloud conditions?
- Does median May-August LST reduce these issues enough?

The report does not need to solve all of this, but it should acknowledge that ECOSTRESS sampling is not just “number of passes”; timing and conditions matter.

## Model and Method

### What works

The city-held-out validation design is explained clearly. The leakage-control language is strong. The explanation of PR AUC and recall@top10 is accessible and aligned with the task.

The model descriptions are appropriate for a STAT 5630 final report: not too mathematically dense, but clear enough for logistic regression and random forest.

### Main weaknesses

#### A. Sampling is still the biggest methods issue

The report states the sample design, but does not justify it enough. Because the full dataset has 71.4 million rows, sampling is understandable. But the sampled benchmark is central to the results, so it deserves more methodological defense.

The phrase “target-rate stratification” is especially important. The reader needs to know whether this preserves only prevalence or also preserves meaningful spatial and feature distributions. Right now, the report does not say enough.

#### B. No uncertainty intervals or repeated-sample variability

The report appropriately says it gives descriptive variability evidence rather than formal confidence intervals. But that caveat should be more visible before the final validity paragraph.

Because the model differences are small, especially PR AUC differences of 0.0065 or recall differences near 0.01 over baseline, uncertainty matters. Without repeated seeds, bootstrap intervals by city, or fold-level uncertainty intervals, the reader should be warned not to overinterpret small differences.

#### C. Baseline definitions are mostly in the appendix, but the main text relies heavily on them

The main text says impervious-only and land-cover-only baselines are strong. Table A3 defines them. That is acceptable, but because the baseline comparison is central to the conclusion, the main text should briefly explain how the strongest baselines work.

For example:

> The impervious-only baseline bins training-city cells by imperviousness decile and transfers the training-bin hotspot rate to held-out cells.

That one sentence would make the baseline result more interpretable.

#### D. Calibration is mentioned in Figure 3 but not actually reported

Figure 3’s diagram text says “Supporting metrics: recall among the top 10% highest-risk held-out cells and calibration tables.” But the report does not appear to include calibration tables or a calibration discussion.

This is a content inconsistency, not just formatting. Either remove “calibration tables” from Figure 3 or include a calibration discussion/table. Otherwise, the figure promises content that the report does not deliver.

## Analysis, Conclusion and Discussion

### What works

This section is much stronger than before. It no longer oversells the RF result. It directly addresses:

- modest gains over baselines;
- pooled versus mean-city differences;
- fold-level heterogeneity;
- city-level paired comparison;
- climate-group differences;
- limitations and future work.

The paragraph saying “much of the transferable retrieval signal in this six-feature contract is already captured by simple built-intensity information” is excellent. That is honest and analytically useful.

### Main weaknesses

#### A. The conclusion needs a stronger positive contribution statement

The conclusion is appropriately cautious, but it needs to avoid sounding like “we built a huge dataset and found weak results.” The positive contribution is the benchmark and the transfer-validation lesson. State that more explicitly.

#### B. The hot-arid interpretation is too speculative relative to the evidence shown

The report should either support the hot-arid mechanism with feature-distribution evidence or frame it as a hypothesis generated by performance differences.

#### C. The future-work paragraph is good but too short

Future work should be more connected to the observed limitations:

- sampling limitation → full-city scoring and repeated sampling;
- spatial dependence → spatially blocked within-city diagnostics or cluster-level error summaries;
- weak feature contract → neighborhood/context features and possibly morphology features;
- construct validity → compare LST hotspots to air temperature or vulnerability indicators;
- climate heterogeneity → stratified model families or climate-specific calibration.

Right now, future work is accurate but compressed. It could be more satisfying without becoming long.

---

# Figure and table critique

## Table 1: Data Sources and Constructed Variables

### Effective?

Mostly yes. This table is useful and much improved because it includes specific product names and dates.

### Problems

- The table is dense and visually awkward, but you said formatting quirks are not the main issue.
- The MODIS NDVI resolution caveat is excellent, but it should also appear in main text.
- The table says all variables are summarized to the 30 m grid; this is true, but it risks hiding the effective-resolution issue.

### Content verdict

Strong table, but the report should not rely on the table footnote alone to defend the “30 m” claim.

## Table 2: Final Dataset Summary by Climate Group

### Effective?

Yes. It supports the dataset-size and climate-balance claims.

### Problems

- It summarizes by climate group but not by city. Appendix Table A4 solves that.
- It does not explain why hot-humid and mild-cool have many more rows than hot-arid. Appendix Figure A1 helps, but the main text should note city-size/study-area imbalance.

### Content verdict

Useful and appropriate.

## Table 3: Main City-Held-Out Benchmark Metrics

### Effective?

Yes. This is probably the most important table in the report.

### Problems

- It mixes 5k and 20k rows, though the note explains that 20k is context. This is okay but still invites casual misreading.
- Runtime is interesting but not central. In a content-focused final report, runtime is less important than uncertainty or fold variability. If space gets tight, runtime could move to appendix.
- The global-mean and climate-only baselines having PR AUC below 0.1000 may confuse readers. It is probably due to ranking/tie behavior, but the report should briefly explain why a constant-ish baseline can be slightly below the prevalence reference.

### Content verdict

Strong, but could use a footnote explaining baseline/tie behavior and why 20k is not the headline comparison.

## Table 4: RF Minus Logistic by Climate Group

### Effective?

Yes. This supports the climate-heterogeneity argument.

### Problems

- It does not show uncertainty or city identities.
- “Hot-arid RF wins 5, logistic wins 5, mean PR AUC delta +0.0336” suggests a few large wins drive the mean. That should be explicitly noted.

### Content verdict

Good table, but needs interpretation that means are sensitive to large city-level gains.

## Table 5: Fold-Level RF Minus Logistic Comparison

### Effective?

Yes. It helps prevent overreading aggregate metrics.

### Problems

- The fold IDs are not interpretable unless the reader jumps to Appendix Table A4.
- The report should briefly mention which cities are in the folds where RF loses badly. Otherwise the fold table is abstract.

### Content verdict

Useful, but a sentence connecting folds to city composition would improve it.

## Table 6: City-Level Paired RF Minus Logistic Summary

### Effective?

Very useful. This is one of the best additions.

### Problems

- It gives min/max but not which cities produced them. Figure 5 should provide that, but currently Figure 5 is hard to read.
- Median deltas are negative while mean recall delta is positive. The report explains this somewhat, but could more explicitly say the aggregate RF advantage is driven by a minority of large wins.

### Content verdict

Strong table; it would become much stronger paired with a readable Figure 5.

## Figure 1: Study City Locations

### Effective?

Yes, much better than before. City labels and climate colors make it actually informative.

### Problems

- Some labels are small, but this is not a fatal content issue.
- The figure supports geographic spread, but not the city-selection rationale.

### Content verdict

Effective enough for main report.

## Figure 2: Dataset Construction Workflow

### Effective?

Conceptually yes. It helps readers understand the pipeline.

### Serious problem

The figure appears to still say **“AppEEARS / Landsat NDVI”** inside the Input Layers box, while the text now says **MODIS/Terra MOD13A1.061 NDVI**. This is a substantive content inconsistency. It makes the figure look stale and undermines confidence in the data-source description.

This must be fixed. This is not a minor formatting quirk.

### Additional problems

- “One parquet and GeoPackage per city” may be implementation detail that does not matter to a blind statistical reader.
- The workflow shows high-level steps but does not surface the most important validity decisions: sensor resolution, pass-count filtering, open-water removal, city-relative target recomputation, and sampling.

### Content verdict

Keep it, but update the NDVI source and consider making the boxes more validity-focused rather than repository-artifact-focused.

## Figure 3: City-Held-Out Evaluation Design

### Effective?

Yes. This is one of the most important figures. It visually communicates the leakage guardrail well.

### Problem

The figure mentions calibration tables, but calibration does not appear to be reported. Remove that phrase or add calibration results.

### Content verdict

Good, but fix the calibration inconsistency.

## Figure 4: Benchmark Metric Comparison

### Effective?

Mostly yes. It visually supports the main benchmark comparison and the dashed 10% reference is a good addition.

### Problems

- The x-axis labels are difficult to read, though this is partly formatting.
- The figure somewhat duplicates Table 3. Its added value is visual comparison, especially the small incremental gains.
- Because differences are small, the figure should maybe use direct delta annotations or a companion plot showing improvement over no-skill / land-cover baseline.

### Content verdict

Acceptable main-text figure. Not spectacular, but useful.

## Figure 5: City-Level RF Minus Logistic Deltas

### Effective?

Currently, **no**. This figure should be one of the most important figures in the report, but as rendered it is not effective enough.

### Major content problem

The city labels appear missing or unreadable. The caption says RF gains are concentrated in selected hot-arid cities and several hot-humid/mild-cool cities favor logistic regression, but the reader cannot easily identify which cities those are from the figure. That makes the figure much less useful.

The prior version, while less elegant, at least had city names visible. This new grouped/climate-colored version sacrifices interpretability.

### Why this matters

The report’s key substantive claim is heterogeneity by city/climate group. Figure 5 is supposed to show that. If the reader cannot identify cities, the figure becomes a decorative grouped bar plot rather than evidence.

### Specific fix

Use a horizontal bar chart sorted by PR AUC delta with city labels clearly visible. Color bars by climate group. If two metrics are needed, either:

- use two separate full-width figures; or
- use one figure for PR AUC city deltas and put recall deltas in appendix; or
- create a lollipop plot / paired dot plot with readable city labels.

Do not prioritize having both metrics side by side if it makes city names unreadable.

### Content verdict

Needs revision before final submission.

## Appendix Figure A1: Row Counts by City and Climate Group

### Effective?

Yes. This is a good appendix figure. It explains why row counts differ and helps contextualize pooled metrics.

### Problems

None major. This is properly placed in appendix.

## Appendix Figure A2: Feature-Importance Summary

### Effective?

Moderately. It is useful as a diagnostic, and the caption correctly says it is not causal.

### Problems

- Logistic coefficients with one-hot land-cover categories need reference-category context; otherwise the coefficient signs are hard to interpret.
- Random-forest permutation importance is shown as mean held-out PR AUC drop, which is good, but no variability is shown.
- The figure may be too compressed to interpret fully.

### Content verdict

Appropriate as appendix. If partner expansion includes feature interpretation, this figure could become more important.

## Appendix Figure A3: Denver Held-Out Map Triptych

### Effective?

Partially. The map is visually interesting and helps show spatial structure.

### Problems

- It is hard to interpret without city context, roads, water, or neighborhood landmarks.
- The title says hot_arid for Denver, which matches the project grouping but may surprise readers.
- The map remains more illustrative than analytical. It does not quantify error clustering or show how this map relates to Denver’s city-level metric.

### Content verdict

Appendix is the right place unless the report adds real spatial interpretation. If partner expansion includes spatial diagnostics, this could be upgraded.

---

# Obvious missing figure/table candidates

These are content-level additions that would make the report stronger. They are not all necessary, but at least one or two would improve the report substantially.

## 1. A readable per-city performance figure

The report needs a better figure than current Figure 5. This is the most obvious missing/effective visual.

Recommended version:

- y-axis: city names;
- x-axis: RF minus logistic PR AUC;
- color: climate group;
- sorted by delta;
- maybe annotate top positive and negative cities.

This would directly support the heterogeneity argument.

## 2. A full per-city PR AUC / recall table or appendix figure

Table 6 summarizes city deltas, but does not show the actual city-level values. A blind reader may want to know whether RF gains occur in cities where both models are good or where logistic fails badly.

A city-level table could include:

- city;
- climate group;
- fold;
- logistic PR AUC;
- RF PR AUC;
- delta;
- logistic recall@top10;
- RF recall@top10;
- delta.

This may be too large for main text, but would be useful in appendix.

## 3. A target / LST distribution figure by city or climate group

The report defines `hotspot_10pct` as within-city top decile, but never visually shows what that means. A figure showing LST distributions or top-decile thresholds by city/climate would help readers understand:

- why a Boston hotspot and Phoenix hotspot are not equivalent absolute temperatures;
- how city-relative labels standardize the task;
- whether some cities have much wider/narrower LST distributions.

This would strongly support construct validity.

## 4. A sampling design figure or table

Because the sampling caveat is important, a small table/figure could show:

- full city rows;
- sampled rows;
- sampled positives/negatives;
- train/test rows per fold;
- why 5k is a controlled benchmark rather than full scoring.

This might be overkill, but the current sampling explanation is text-heavy.

## 5. PR curves for the main models

Since PR AUC is the primary metric, at least one PR curve would be illustrative. A pooled PR curve comparing no-skill, impervious-only, logistic, and RF would make the PR AUC metric more concrete.

This is not strictly necessary, but it would be a strong machine-learning figure.

## 6. Score distribution or calibration plot

If the report keeps any mention of calibration, it needs an actual calibration plot/table. Otherwise remove calibration from Figure 3.

## 7. Feature distribution by climate group

This would support the climate interpretation. For example:

- NDVI distribution by climate group;
- imperviousness distribution by climate group;
- land-cover composition by climate group.

This would make the hot-arid explanation less speculative.

---

# Content issues that could cost points under the assignment rubric

The assignment asks whether questions and conclusions are well-defined and properly interpreted, methods are clearly explained and properly applied, validity is sufficiently discussed, and tables/figures are properly labeled and support the main argument.

## Questions and conclusions

Mostly strong. The research question is well-defined, and conclusions are appropriately cautious.

Potential deduction: the report should more forcefully state its positive contribution, not only its limitations.

## Statistical methods

Clear but not complete. Grouped CV is well explained. Logistic/RF descriptions are adequate. But sampling, hyperparameter-search fairness, and uncertainty remain underdeveloped.

Potential deduction: small metric differences are interpreted descriptively without intervals or repeated-sample stability.

## Validity discussion

Strong, especially in the final section. But construct validity around 30 m analytic grid versus coarser source resolution needs more main-text emphasis.

Potential deduction: the report may still appear to overstate the effective resolution of the data.

## Tables and figures

Tables are generally useful. Figures are mixed.

Potential deduction: Figure 2 appears inconsistent with text on NDVI source; Figure 5 is not effective enough as evidence because city labels are unreadable or absent; Figure 3 mentions calibration without calibration results.

## Possible directions for improvement

Present but too short. Future work should be more directly tied to observed limitations.

Potential deduction: future-work paragraph is accurate but underdeveloped for such a large project.

---

# Specific revision checklist

## Must-fix before final submission

1. **Fix Figure 2 NDVI source label.** It appears to say Landsat NDVI despite the text/table saying MODIS/Terra MOD13A1.061 NDVI.
2. **Fix Figure 5.** City labels need to be readable. This is the most important figure problem.
3. **Remove or support the “calibration tables” phrase in Figure 3.** The report does not actually present calibration tables.
4. **Add a main-text clarification that 30 m is the analytic grid, not the native resolution of every source variable.**
5. **Add a short city-selection / climate-group assignment explanation.** Even two or three sentences would help.
6. **Expand the sampling caveat into a sampling-validity explanation.** Explain what the 5k target-rate-stratified sample does and does not preserve.
7. **Add a stronger positive contribution paragraph.** The report should not only say “limited model”; it should say “valuable benchmark revealing limited transfer.”

## Strongly recommended

1. Add a sentence explaining why top 10% was chosen.
2. Briefly define the impervious-only and land-cover-only baselines in the main text.
3. Add a caveat that the hot-arid mechanism is hypothesis-generating, not demonstrated.
4. Expand future work by mapping each limitation to a next step.
5. Add or appendix a per-city performance table.
6. Consider adding a PR curve or LST distribution figure if space allows.

## Partner-expansion shaping moves

These are especially relevant given your stated intent.

1. Create a clear narrative slot for partner expansion in **Dataset Validity**:
   - city selection;
   - climate grouping;
   - sensor resolution;
   - ECOSTRESS temporal sampling;
   - 2 km buffer implications.

2. Create a clear narrative slot for partner expansion in **Diagnostic Interpretation**:
   - spatial error patterns;
   - feature importance;
   - climate-specific feature distributions;
   - within-city versus city-held-out contrast.

3. Avoid making partner expansion sound like “add one citation.” It should be framed as substantive validation/diagnostic work.

4. Add transition language that distinguishes the current retained benchmark from supplemental diagnostics. This allows partner material to enter as a meaningful extension rather than an afterthought.

---

# Suggested paragraph insertions

## Insert after dataset row-count / spatial-dependence paragraph

> The 30 m cell is the analytic grid unit rather than the native resolution of every source layer. Some predictors, especially MODIS NDVI, are coarser products aligned or summarized to the grid. As a result, the dataset should be interpreted as a consistent 30 m modeling table, not as 71.4 million independent native-resolution measurements. This distinction matters for interpreting both spatial dependence and the effective detail available to the models.

## Insert in Methods after sampling description

> The sampled benchmark intentionally gives each city the same sampled row count, so the retained metrics describe performance on a balanced city sample rather than exhaustive full-population scoring over every eligible grid cell. Target-rate stratification preserves the 10% positive prevalence in each sampled city, but it does not guarantee exact preservation of spatial clusters, land-cover composition, or neighborhood structure. Full-city scoring or repeated sampled runs would be needed to quantify sampling variability.

## Insert in Results before final conclusion

> The main contribution is therefore not a deployment-ready classifier, but a transfer benchmark showing that cross-city hotspot screening is possible yet fragile. The benchmark demonstrates that public non-thermal geospatial predictors carry some transferable signal, that simple built-intensity baselines are difficult to beat, and that nonlinear gains concentrate in selected hot-arid cities rather than generalizing uniformly across all cities.

## Insert near climate interpretation

> The report does not directly test the physical mechanism behind the hot-arid advantage, so this interpretation should be read as a hypothesis generated by the benchmark rather than as a demonstrated causal explanation.

## Insert in Future Work

> Future extensions should map directly onto the current limitations: repeated samples or full-city scoring for sampling uncertainty, spatially explicit error summaries for clustered mistakes, richer neighborhood and morphology features for the narrow feature contract, and external heat-exposure or vulnerability data for construct validity beyond surface-temperature hotspots.

---

# Final harsh assessment

This is a substantially improved draft and much closer to submission-ready. The report now has a coherent central task, a defensible evaluation design, honest interpretation, and useful supporting tables. It no longer reads like a project trying to force a strong predictive conclusion from weak metrics.

But the draft still needs tightening before it should be considered polished. The biggest remaining content issue is not the prose; it is the evidentiary structure. The report needs to make its contribution more explicit, explain its sampling and resolution limitations more rigorously, and ensure the figures actually support the claims being made. Figure 5, in particular, currently fails to carry the city-heterogeneity argument because the reader cannot clearly identify cities. Figure 2 appears to preserve an outdated data-source label, which is exactly the kind of inconsistency that makes a grader distrust the pipeline.

The partner-expansion issue is also important. The current draft is not obviously missing partner notes anymore, but it also does not clearly stage a substantial partner contribution. If partner material will be added, the report should frame that material as substantive validation and diagnostic interpretation, not as decorative background. The best partner expansion would probably focus on dataset/design validity, remote-sensing limitations, climate-group interpretation, and spatial/feature diagnostics.

With the must-fix items addressed, this could become a strong final report. Without them, it is still good, but it remains vulnerable to harsh grading on figure effectiveness, sampling validity, source-resolution interpretation, and the clarity of the project’s positive contribution.
