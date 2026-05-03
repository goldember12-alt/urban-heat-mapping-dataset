# Blind Reading Critique of `stat5630_final_report_draft(7).pdf`

**Reader stance:** I am reading this as a grader who knows nothing about the project except the submitted report and the loose STAT 5630 final-project requirements. I am intentionally being picky. I am not treating the Nicholas insertion placeholders as problems by themselves, because you said those are intentional and must remain structurally available for within-city validation material. I do, however, flag places where the surrounding prose needs to make those insertions land cleanly.

**Assignment frame used for critique:** the report must include a title page, main text, tables/figures, and appendix; the main text should motivate the topic, describe dataset/study background, present research questions and target population, explain variables and methods, summarize analysis and conclusions, discuss validity, and ensure tables/figures are properly labeled, clearly explained, and supportive of the main argument.

---

## 1. High-level blind-reader verdict

This draft is substantially stronger than a typical class report in scope, validation awareness, and statistical maturity. The central intellectual contribution is clear: **within-city learning looks strong, but city-held-out transfer is much weaker and more heterogeneous.** That is a good machine-learning story, and it aligns well with the assignment’s emphasis on research questions, methods, interpretation, validity, and possible improvements.

The biggest remaining weakness is not technical seriousness. It is **reader management**. The draft often assumes the reader already understands why certain choices matter, then gives dense project-internal details before fully orienting the reader. As a blind reader, I can eventually infer the structure, but I repeatedly have to work too hard to answer basic questions:

- What exactly is the target population?
- What is the final modeling sample versus the full constructed dataset?
- What is being evaluated in within-city validation versus city-held-out transfer?
- Why do within-city and transfer results use different metrics?
- How should I interpret PR AUC values like 0.1486 as “good,” “bad,” or “useful”?
- Which figures are essential to the argument versus supplemental evidence?
- What exactly did the partner contribute, and where will that contribution attach?

The report is currently strong but still slightly “artifact-shaped”: it reads like a well-compressed synthesis of a large codebase and modeling workflow. The next revision should make it feel more like a self-contained statistical report written for someone who has never seen the project.

The most important edits are:

1. **Add a short, plain-English roadmap at the end of the introduction.** Tell the reader: “We build the dataset, define a within-city top-decile hotspot label, compare models under two validation designs, and show that within-city performance does not imply city-held-out transfer.”
2. **Clarify target population and sample hierarchy earlier.** The target is not “all U.S. cities” and not exactly “urban heat exposure.” It is 30 purposively selected U.S. urban areas, analyzed as 30 m grid cells with a surface-temperature top-decile label.
3. **Defend the city-relative top-10% label more explicitly.** It is a smart design, but a blind reader may wonder whether a “hotspot” in Seattle is comparable to a “hotspot” in Phoenix. Explain that the project is about *within-city screening transfer*, not national absolute heat risk.
4. **Make the transition from full 71 million rows to sampled 5k-per-city modeling much clearer.** A blind reader may feel whiplash: the dataset is huge, but the headline transfer benchmark uses 150,000 sampled rows across folds. This is legitimate, but it must be framed as a computationally controlled benchmark rather than quietly introduced later.
5. **Make Figure 4 less visually misleading.** It says not to compare metric magnitudes across panels, but the visual side-by-side invites exactly that comparison. It is useful, but it needs a stronger caption, visual separator, or redesign.
6. **Improve figure readability for the Denver map and small multi-panel plots.** Several figures are conceptually excellent but small or visually crowded in the PDF.
7. **Resolve awkward phrasing, hyphenation artifacts, and overly compressed sentences.** The PDF has line-break artifacts like “tempera- ture,” “distinc- tion,” “validity is limited by the LST- versus-exposure distinction,” etc. These may be rendering artifacts, but they visually degrade professionalism.

---

## 2. Compliance with assignment requirements

### 2.1 Format and required sections

**Status:** Mostly compliant.

The assignment asks for a title page, main text, tables/figures section, and appendix. The draft has all of these. The title page includes title, collaborators, class, and date. The main text appears to be about 8 pages before references, which is within the 15-page limit for a two-person project. Tables and figures are placed after the main text, not interleaved, which matches the requirement.

**Potential issue:** The “References” section appears inside the main text before the “Tables and Figures” section. This is probably acceptable, but the assignment specifically names three parts: Main Text, Tables and Figures, Appendix. A strict grader may not care, but visually the references make the “Main Text” section feel longer and blur where the required three-part structure begins and ends.

**Suggestion:** Consider renaming the section sequence as:

- Main Text
  - Background Information
  - Research Questions
  - Dataset Construction
  - Model and Method
  - Analysis, Conclusion, and Discussion
  - References
- Tables and Figures
- Appendix

This is already effectively what you have, but make sure the PDF formatting makes it obvious that References are part of the main text or a separate unnumbered section.

### 2.2 Assignment asks for “Who, When, Where, What; How data was collected; Link to study and dataset”

The report partially satisfies this, but a blind grader may mark it as incomplete because these elements are embedded rather than explicitly signposted.

Current coverage:
- **Who/Where:** 30 U.S. cities across three broad climate groups.
- **When:** May-August 2023 for MODIS NDVI and ECOSTRESS LST; Census 2020 urban areas; NLCD 2021; 3DEP and NHDPlus HR.
- **What:** 30 m grid-cell dataset with environmental/built-environment predictors and city-relative top-decile LST hotspot target.
- **How collected:** AppEEARS for MODIS/ECOSTRESS, public geospatial sources, aligned to a grid.
- **Link to study/dataset:** Public source links are in references, but there is no clean “dataset availability” or “project repository / generated dataset” statement.

**Problem as a blind reader:** I do not know whether the final constructed dataset is publicly available, privately generated, too large to share, or just reproducible from the listed artifacts. The assignment explicitly asks to “Link to the study and dataset.” If this is a class-generated dataset, say so.

**Suggested addition near the end of Dataset Construction or in Reproducibility Notes:**

> The final modeling dataset was constructed by the authors from public source layers rather than downloaded as a single preexisting study dataset. The source products are listed in Table 1 and cited in the References. The generated project artifacts are retained in the project repository/output folders listed in the reproducibility notes.

If there is a GitHub link or shared archive, include it. If not, explicitly say the dataset is generated locally from the listed public sources and too large for direct inclusion.

### 2.3 Statistical method explanation

**Status:** Strong overall, but still somewhat abstract in places.

The method section explains logistic regression, random forest, baselines, grouped cross-validation, training-only preprocessing, and metrics. That is good. The biggest weakness is the **thresholding procedure for within-city metrics**, which is currently delegated to a placeholder. Since within-city results are central to the report’s contrast, the reader needs this detail before trusting Figure 4.

Even if Nicholas will fill the within-city section, the surrounding report needs to reserve space for:
- Whether threshold was 0.5, top 10%, tuned threshold, or some class-weighted decision rule.
- Whether the 70/30 split was within each city, across all pooled cells, stratified by city, or something else.
- Whether preprocessing was fit only on training cells.
- Whether city-specific thresholding occurred.
- Whether metrics were averaged by city or pooled.

This is not optional. Without it, the within-city numbers are impressive but not fully interpretable.

### 2.4 Validity discussion

**Status:** Good and above average. Needs one more validity issue.

The validity paragraph is strong. It covers leakage control, sampling validity, spatial dependence, LST-versus-exposure construct validity, external validity, and model-comparison validity.

The missing validity issue is **city-relative labeling and comparability**. Because every city has exactly 10% positives, the outcome erases absolute heat differences across cities. That is a reasonable and probably necessary choice for within-city screening, but it should be explicitly named as a construct-validity tradeoff.

Suggested addition:

> Because the hotspot label is defined within each city, the model is evaluated on local ranking rather than absolute heat severity. A positive cell in a cooler city and a positive cell in a hotter city are both “top-decile” cells, but they may correspond to very different physical LST values and public-health implications.

This would make the interpretation more intellectually honest and would likely impress a grader.

---

## 3. Global writing and structure comments

### 3.1 The title is accurate but dense

Current title:

> Cross-City Urban Heat Hotspot Screening: Within-City Learning and City-Held-Out Transfer

This is technically excellent, but for a blind class reader it is a lot. “City-Held-Out Transfer” is clear once I read the report, but slightly jargon-heavy on the title page.

Possible alternatives:
- **Urban Heat Hotspot Screening Across U.S. Cities: Within-City Learning Versus City-Held-Out Transfer**
- **Can Urban Heat Hotspot Models Transfer Across Cities? A 30-City Machine Learning Benchmark**
- **Cross-City Urban Heat Hotspot Screening Using Public Geospatial Predictors**

The current title is acceptable. The second alternative is more readable and more memorable.

### 3.2 Add a one-paragraph executive summary after the title page or at the start of main text

The assignment does not require an abstract, but this report would benefit from one. The project is complex enough that a blind reader needs a summary before the technical details.

Suggested abstract-style paragraph:

> This project asks whether public, non-thermal geospatial predictors can identify the hottest local surface-temperature cells within U.S. cities, and whether models trained on some cities transfer to unseen cities. We built a 30-city grid-cell dataset from Census urban areas, NLCD, 3DEP, NHDPlus HR, MODIS NDVI, and ECOSTRESS LST, defining hotspots as the top 10% of valid May-August 2023 LST cells within each city. Random forest strongly outperformed logistic regression under within-city held-out validation, but city-held-out transfer was weaker and only modestly better than simple imperviousness and land-cover baselines. The main conclusion is that same-city hotspot learnability does not guarantee cross-city transferability.

This would solve a lot of blind-reader orientation problems.

### 3.3 The introduction is good but too evenly weighted

The Background Information section spends a lot of time on remote sensing, LST, and literature, which is appropriate. But the project’s actual “hook” is validation design. That hook appears, but it needs to be more forceful earlier.

As a blind reader, I want the introduction to reach this sentence faster:

> The main question is not just whether a model can identify hotspots inside cities it has already seen, but whether it can transfer to entirely unseen cities.

That sentence or a variant should appear in the first page.

### 3.4 The report sometimes sounds like documentation rather than argument

Examples:
- “The modeling feature contract excludes thermal variables…”
- “The final assembly step merges the per-city feature tables…”
- “The matched 5k comparison is the headline logistic-versus-random-forest comparison…”
- “The grouped city-held-out contract is unchanged.”

These are precise, but “contract,” “artifact,” “benchmark scope,” and “delivery” sound internal/codebase-oriented. A grader will understand, but the tone sometimes feels like a technical handoff rather than a polished report.

Suggested replacements:
- “feature contract” → “feature set” or “modeling specification”
- “audit and split contract” in Figure 2 → “Quality checks and validation splits”
- “modeling and delivery” in Figure 2 → “Model training and evaluation”
- “city-held-out contract” → “city-held-out validation design”
- “benchmark source artifacts” → “Benchmark source outputs”

Keep “benchmark” and “validation design”; those are useful. Use “contract” less often.

### 3.5 There is some repetition around the six-feature specification

The six predictors are named in the introduction, dataset section, and method section. That is not inherently bad, but the repetition could be tightened. The method section is the best place for the exact variable list. Earlier sections can say “six non-thermal geospatial predictors described in Section 4.”

However, since the assignment asks for variables and data background, some repetition is acceptable. Just make sure it does not feel like filler.

### 3.6 The report needs clearer ownership around partner insertions

You told me not to critique the placeholder messages themselves, and I won’t. But as a blind reader, I need the final report to avoid a seam where one author’s work suddenly appears.

The three insertion areas are:
1. Related-work context connecting urban heat, spatial validation, and transfer learning.
2. Within-city held-out methods detail.
3. Signal-shift analysis connecting within-city and transfer metrics.

These are all high-leverage insertions. The surrounding prose already points to them well. The only issue is that the current draft’s argument depends heavily on them. If Nicholas’s insertions are late, the report remains structurally incomplete.

The most important of the three is the **within-city methods detail**, because Figure 4 and the main conclusion rely on it. The second most important is the **signal-shift analysis**, because Figure 5 is one of the strongest pieces of evidence in the report.

---

## 4. Page-by-page and paragraph-level critique

## Page 1: Title page

### Title

The title is accurate and impressive, but it is also dense. A blind reader understands “Urban Heat Hotspot Screening” but may not immediately understand “City-Held-Out Transfer.” That term is later explained well, so this is not fatal.

**Possible edit:** Add “Across U.S. Cities” to make the geography obvious:

> Cross-City Urban Heat Hotspot Screening Across U.S. Cities: Within-City Learning and City-Held-Out Transfer

Or make it more question-driven:

> Can Urban Heat Hotspot Models Transfer Across Cities?

The current title is safe and technically strong. A more question-driven title would be more engaging.

### Collaborator line

Fine. Make sure both names match exactly the email/PDF naming requirement.

### Date

Fine.

---

## Page 2: Background Information, opening paragraphs

### Paragraph 1

Current opening is solid:

> Extreme urban heat is a public-health, infrastructure, and planning problem because thermal exposure is not distributed evenly across a city.

This is a good first sentence. It is concrete and motivates the problem.

**Issue:** The paragraph says “thermal exposure,” but the project uses land surface temperature, not human heat exposure. Later you clarify this, but the opening could be slightly more careful.

**Suggested edit:**

> Extreme urban heat is a public-health, infrastructure, and planning problem because heat-related surface and exposure conditions are not distributed evenly across a city.

Or:

> Extreme urban heat is a public-health, infrastructure, and planning problem because surface heat and related exposure risks are not distributed evenly across a city.

This avoids implying that your target directly measures exposure.

### Paragraph 1, final sentence

Current:

> For a statistical learning project, the practical question is not only whether a city contains hot areas, but whether publicly available spatial variables can help rank local cells for screening when direct thermal labels are limited.

This is good, but “when direct thermal labels are limited” is a little odd because your project actually uses ECOSTRESS LST labels for all included cells. The limitation is about generalizing labels to new places or reducing reliance on thermal measurement, not necessarily label scarcity in this dataset.

**Suggested edit:**

> For a statistical learning project, the practical question is not only whether a city contains hot areas, but whether publicly available spatial variables can rank local grid cells for hotspot screening when direct thermal measurement is unavailable, incomplete, or held out.

### Paragraph 2

Current:

> Much urban heat mapping is local and descriptive…

This paragraph is excellent conceptually. It names the gap: local descriptive mapping versus multi-city validation and transfer.

**Issue:** “in familiar places” sounds informal. Replace with “within a single study area” or “within the same city.”

**Suggested edit:**

> Much urban heat mapping is local and descriptive: it shows where hotter surfaces occur within one city or estimates associations between LST and surface descriptors within the same study area.

### Paragraph 2, final sentence

Current:

> That framing makes both the standardized multi-city dataset and the validation design contrast central to the contribution rather than just pipeline details.

This is strong, but “pipeline details” sounds internal. Better:

> That framing makes the standardized multi-city dataset and the contrast between validation designs central to the contribution, not merely implementation details.

### Paragraph 3: LST explanation

This paragraph is important and mostly strong. It correctly explains that LST is not air temperature.

**Issue:** The phrase “how warm the observed surface would feel to the touch” is intuitive but maybe slightly imprecise scientifically. LST is radiometric/surface skin temperature; “feel to the touch” is okay for lay explanation but may invite oversimplification.

**Suggested edit:**

> it describes the temperature of the observed land surface itself, so a roof, road, tree canopy, irrigated field, or bare soil patch may all behave differently.

### Paragraph 3: NASA/ECOSTRESS sentence

Current:

> NASA’s land-surface-temperature documentation emphasizes that land heats and cools differently from the air, and ECOSTRESS documentation describes a thermal mission that measures surface temperature at fine spatial detail from the International Space Station.

This sentence reads like citation coverage rather than argument. It is fine, but a blind reader might wonder why this matters.

**Suggested edit:**

> This matters because the model is trained against a remote-sensing surface-temperature target, not against ground-station air temperature or human heat exposure.

You already say that next. Consider compressing the NASA sentence and emphasizing the interpretive consequence.

### Paragraph 3, last sentence

Current:

> The target is based on surface temperature, so the results should be interpreted as surface hotspot screening rather than direct human heat-exposure measurement.

This is excellent. Keep.

---

## Page 2-3: Literature review and contribution framing

### Literature paragraph

The paragraph citing Voogt and Oke, Weng et al., Yuan and Bauer, Stewart and Oke, and Harlan et al. is good but dense. It establishes a plausible feature set and the need for validation.

**Issue:** It reads a little like a citation list. The project-specific argument could be clearer.

**Suggested restructuring:**

1. First sentence: older literature shows urban thermal patterns are spatially heterogeneous and associated with surface form.
2. Second sentence: specific studies motivate vegetation and impervious surface predictors.
3. Third sentence: urban form/local climate zones motivate land cover and structure.
4. Fourth sentence: vulnerability literature reminds us LST is not equivalent to human exposure.
5. Final sentence: therefore the six-feature model is interpretable but intentionally limited.

Current final sentence:

> The six-feature specification keeps the model comparison interpretable.

Good, but too abrupt after the Harlan exposure/vulnerability citation. Expand slightly:

> The six-feature specification therefore keeps the model comparison interpretable while focusing on physically plausible, publicly available surface descriptors.

### AppEEARS paragraph

Current:

> AppEEARS supports the reproducible remote-sensing part of the workflow…

This is clear. But as a blind reader, I still do not know what AppEEARS is. You cite it later, but a short appositive helps.

**Suggested edit:**

> AppEEARS, NASA’s application for requesting and subsetting Earth observation products, supports the reproducible remote-sensing part of the workflow…

### Validation design paragraph

This is one of the strongest conceptual paragraphs. Keep the Roberts/Meyer citations. The paragraph clearly motivates grouped/city-held-out validation.

**Issue:** “This project applies the same principle at the city scale while retaining the easier same-city screening question” is good but slightly abstract. Add the concrete version:

> In other words, the report asks both “Can the model find held-out hotspots in cities it has already seen?” and “Can the model transfer to a city it has never seen?”

This exact sentence would help a blind reader a lot.

### Related-work insertion placeholder

Structurally this is a good location. The eventual insertion should not become a literature dump. It should serve the report’s two-design contrast.

**Advice for final insertion:** Nicholas or you should write this as a bridge, not as a separate lit review:
- Urban heat work motivates predictors.
- Spatial validation work motivates grouped holdouts.
- Transfer/generalization work motivates whole-city holdout.
- Therefore, the report’s two-design evaluation is not an arbitrary modeling choice.

### Contribution paragraph

Current:

> This project therefore contributes a standardized multi-city benchmark with three linked pieces…

This is clear and important.

**Issue:** “benchmark” is slightly ambiguous. Is it a dataset benchmark, a model benchmark, or an evaluation benchmark? It is all three, but define it.

**Suggested edit:**

> This project therefore contributes a standardized multi-city evaluation benchmark with three linked pieces…

### Dataset size sentence

Current:

> The completed dataset contains 71,394,894 rows and 17 columns, with one row representing one analytic 30 m grid cell in one of the selected U.S. cities.

Excellent. Keep. This is concrete and impressive.

**Issue:** The report later uses sampled 5,000 rows per city for transfer modeling. Consider foreshadowing that the full dataset is constructed, while the reported transfer benchmark uses controlled per-city samples for computationally matched model comparison.

**Suggested addition after dataset size sentence:**

> The full table defines the constructed study population, while the main city-held-out model comparison uses balanced per-city samples described in Section 4.

That prevents later surprise.

### “Figure 1 shows…” sentence

Fine.

### Final paragraph before Research Questions

Current:

> The resulting dataset combines public geospatial and remote-sensing sources summarized in Table 1. The modeling feature contract excludes thermal variables, using ECOSTRESS LST to define the outcome rather than to predict it.

Good content, but “feature contract” is internal.

**Suggested edit:**

> The resulting dataset combines the public geospatial and remote-sensing sources summarized in Table 1. The headline model specification excludes thermal variables: ECOSTRESS LST defines the outcome but is not used as a predictor.

This is clearer and more polished.

---

## Page 3: Research Questions

### Primary research question

Strong. The research question is clear and aligned with the project.

**Issue:** The primary question has two clauses and is a little long. It is okay, but for readability:

> Can basic environmental and built-environment features identify urban heat hotspots across a multi-city dataset? How does performance change when evaluation moves from within-city held-out cells to whole-city holdout transfer?

This two-sentence version is easier to digest.

### Explanation of two parts

Current:

> The within-city held-out design asks whether a model can identify held-out hotspot cells from cities represented during model development. The city-held-out transfer design asks whether a model can rank cells in a whole unseen city by hotspot risk.

Excellent. Keep. This is one of the clearest passages in the report.

### Unit of analysis sentence

Current:

> The unit of analysis is a 30 m grid cell, but the stricter transfer evaluation uses city_id as the grouping variable.

Good but slightly technical. A blind reader may understand, but you can make it smoother:

> The unit of analysis is a 30 m grid cell, while the strict transfer evaluation treats the city as the grouping unit: all cells from a held-out city are excluded from training.

This explains the implication.

### Secondary questions

These are good and well aligned with results.

**Issue:** The fourth question, “does success under within-city evaluation predict success under city-held-out transfer?” is arguably one of the most interesting findings. Consider elevating it as a major question, not the fourth secondary question.

Maybe present as:
- Main transfer question.
- Model comparison question.
- Heterogeneity/signal-shift question.

This would align better with Figures 4 and 5.

### Outcome definition

Current:

> The outcome is hotspot_10pct, a city-relative binary label…

This is essential and well written.

**Issue:** This is the first time the target is defined in detail. It may be slightly late, because the introduction already uses “hotspot” often. Consider giving a parenthetical earlier in Background:

> Here, a “hotspot” means a grid cell in the hottest 10% of valid May-August ECOSTRESS LST values within its city.

Then repeat the formal definition here.

### “valid eligible cells” phrase

This phrase appears several times. It is technically useful but slightly opaque.

**Problem:** A blind reader asks: eligible how? open-water removed? ECOSTRESS pass threshold? core/buffer? valid LST? You explain later, but the phrase should be unpacked once.

**Suggested edit:**

> A positive cell is one of the hottest 10% of cells remaining after open-water and ECOSTRESS quality filters within its own city…

If there are additional eligibility rules, name them.

---

## Pages 3-5: Dataset Construction

### Opening paragraph

Good. It clearly states 30 cities, climate groups, purposive benchmark panel.

**Strong sentence:**

> …the set should be treated as a purposive benchmark panel rather than a statistically representative sample of U.S. urban areas.

Keep this. It is an important validity caveat and reads professionally.

**Potential issue:** “climate groups make the transfer question more interpretable without replacing formal climatology or local meteorology” is good but abstract. Fine as-is.

### Study region paragraph

Clear. The 2020 Census urban area and 2 km buffer are understandable.

**Question as blind reader:** Why 2 km? Is this conventional, arbitrary, or practical? You give a plausible reason, but not why 2 km specifically.

**Suggested addition:**

> The 2 km distance is a pragmatic buffer chosen to include near-urban transitions without expanding the study area far beyond the selected urban area.

If 2 km was chosen for a specific reason, state that. If it was pragmatic, say so.

### Local UTM grid paragraph

Good. It explains why local projected CRS matters.

**Minor edit:** “master 30 m grid” may sound internal. Use “city-specific 30 m grid.”

### “30 m dataset” caveat paragraph

This is excellent and important. Keep it. It anticipates a major blind-reader concern.

**Potential improvement:** The paragraph should say whether values are assigned by centroid, zonal summary, nearest pixel, or raster resampling. You partially mention centroid/geometry for vector quantities, but raster handling remains broad.

For a report, this may be enough. But because “30 m” can be misleading, one more sentence helps:

> Thus, the 30 m cell is the common reporting unit, not a claim that every predictor was originally measured at 30 m resolution.

You already say this conceptually. Consider making it the first or last sentence.

### Source layers paragraph

This paragraph is good but long. It lists all sources and transformations.

**Potential issue:** “selected hydro feature” is vague. What water features were selected? Rivers/lakes? All NHDPlus HR flowlines and waterbodies? If not important, fine. But “selected” makes me wonder what was excluded.

**Suggested edit:**

> …converted to a distance from each grid cell to the nearest included hydrographic feature.

Or define selected water features in Table 1.

### May-August paragraph

Very good. It explains why a seasonal summary is used and why ECOSTRESS pass count matters.

**Issue:** “Cells with fewer than three valid ECOSTRESS observations are removed when LST is available” is confusing. “When LST is available” seems contradictory: if they have fewer than three observations, is LST available or not? Are cells with missing LST removed? Are cells with 1-2 passes removed? What about cells with zero passes?

**Suggested edit:**

> Cells are retained for labeling only if they have at least three valid ECOSTRESS observations contributing to the May-August LST summary.

If that is correct, use it. If not, clarify exactly.

### Final assembly paragraph

Current:

> The final assembly step merges the per-city feature tables into a single modeling-ready dataset, with CSV also written as a compatibility output.

This sounds internal. A grader does not need “CSV compatibility output” in the main text.

**Suggested edit:**

> The final assembly step merges the per-city feature tables into one modeling-ready table. After open-water and ECOSTRESS quality filters, hotspot_10pct is recomputed within each city…

Move CSV compatibility to Reproducibility Notes only.

### Dataset contents paragraph

Good. It clearly separates headline predictors from supplemental neighborhood variables.

**Issue:** “headline predictors” is somewhat presentation-like. “Primary predictors” or “main predictors” may be smoother.

### Audit paragraph

This is useful and concrete.

**Issue:** This paragraph is dense with numbers. It may be too much for main text, especially because Table 2 and Appendix A1 also present summaries.

Potential revision:
- Keep 30 cities, 71.4M rows, 7.14M positives.
- Keep missingness summary if assignment rewards dataset clarity.
- Move exact missing-cell counts to appendix if main text is tight.

**Important blind-reader issue:** The missingness statement says headline predictors have favorable missingness, but you later mention preprocessing imputation. It would be useful to explicitly say missing values were imputed within training folds for modeling. You do that later. Good.

### Row-count distribution sentence

Current:

> The row-count distribution is uneven across cities because study-area extents differ substantially; Appendix Figure A1 is included as support for that point.

This is fine, but “included as support” sounds like a memo. Better:

> Appendix Figure A1 shows the uneven city row-count distribution produced by differences in study-area extent.

### Large row count caveat

Excellent. Keep.

### Figure 2 sentence

Current:

> The key modeling implication is that the final table is not an ad hoc spreadsheet…

This is good but “ad hoc spreadsheet” is a little informal/defensive. It might be okay, but for polished report:

> The key modeling implication is that the final table is a standardized, reproducible grid-cell dataset rather than a manually assembled collection of city-specific summaries.

This says the same thing more academically.

---

## Pages 5-7: Model and Method

### Opening task statement

Good. It states the response and predictors.

**Issue:** You use “probability that the cell belongs to the hottest 10% of valid eligible cells in its own city.” Since the target is city-relative, this is accurate. But remember that the model is trained on sampled rows with exactly 10% positives per city in the transfer benchmark. If the training sample is stratified, predicted probabilities may not be calibrated to the full population. You mostly interpret as ranking, which is good.

**Suggested addition later in metrics paragraph:**

> Because the sampled benchmark preserves a fixed 10% positive rate, predicted scores are interpreted primarily as rankings rather than calibrated probabilities.

### Excluded variables paragraph

This is important and mostly excellent.

**Issue:** Excluding centroid coordinates is good for portability, but a blind reader may wonder whether excluding coordinates weakens within-city maps. Say that this is deliberate.

**Suggested edit:**

> This exclusion is deliberate: coordinates could improve apparent predictive performance by acting as location identifiers, but would make the learned relationship less portable.

### Validation design paragraph: within-city

This section currently depends on a placeholder. The surrounding prose is good, but the missing details are critical.

**Specific questions that must be answered in final text:**
- Is the 70/30 split performed separately within each city?
- Is it random over grid cells?
- Is it stratified by hotspot label?
- Are neighboring cells allowed in both train and test? If yes, explicitly acknowledge this is why it is “easier.”
- Are logistic/RF hyperparameters tuned? If yes, how? If not, say fixed.
- Are the metrics pooled over all held-out cells or averaged by city?
- What threshold converts probabilities to class labels? 0.5? Top 10%? Tuned? Default sklearn? This is crucial.

**Suggested bridge sentence before placeholder:**

> Because this design allows other cells from the same city into training, it should be interpreted as same-city interpolation rather than evidence of cross-city generalization.

This would make the contrast much sharper.

### City-held-out transfer paragraph

This is very strong. It clearly explains folds, training-only preprocessing, and city-level holdout.

**Minor issue:** “inner cross-validation for tuning also occurs only within the training cities” is good, but say “grouped by city” if true. You do later in appendix, but main text should say it:

> Inner cross-validation for tuning also uses grouped city splits within the training cities.

If inner CV is GroupKFold by city, say that explicitly.

### Baselines paragraph

Good. Baselines are important and increase credibility.

**Issue:** “no-skill prevalence reference” and “global-mean baseline” sound similar. The report later explains tie handling, but a blind reader may not immediately understand the difference.

Suggested clarification:

> The no-skill reference is the expected PR AUC and top-decile recall under a 10% positive rate. The global-mean baseline assigns all held-out cells the same training prevalence score, serving as an implemented constant-score check.

This may be more detail than needed, but it avoids confusion when Table 3 shows 0.0982 instead of exactly 0.1000.

### Logistic regression paragraph

Good.

**Issue:** “saga solver” may be too implementation-specific for a main report unless you say why it matters. You do: it supports regularized logistic regression. Good.

**Potential missing detail:** Did logistic regression use class weights? Did it optimize average precision? The appendix says tuning scoring average precision. Main text should include that:

> Hyperparameters are selected by inner cross-validation using average precision.

This matters because PR AUC is central.

### Random forest paragraph

Good and accessible.

**Issue:** “same training-only preprocessing rule” is slightly vague. You define it, fine.

**Potential concern:** One-hot encoding categorical variables for random forest can be less natural than native categorical handling, but sklearn requires it. Not worth discussing unless asked.

### Metrics paragraph

This is a crucial section and mostly strong.

**Issue:** “The two validation settings use related but not identical metrics, so the report compares patterns rather than treating all numbers as one leaderboard” is very important. But because Figure 4 puts them side-by-side, the figure should visually reinforce this.

**Suggested main-text addition:**

> The left and right panels of Figure 4 should therefore be read as separate summaries of two validation questions, not as a direct comparison of precision/F1 against PR AUC.

You already say similar in caption. Put it in main text too.

### PR AUC explanation

You explain PR AUC indirectly but not explicitly. A blind grader in a statistical ML class will know it, but a short explanation helps:

> PR AUC summarizes how well the model ranks true hotspot cells ahead of non-hotspot cells across thresholds and is more informative than accuracy for a 10% positive class.

This belongs in the metrics paragraph.

### Recall at top 10% explanation

Excellent. This is one of the clearest metric explanations.

**Potential issue:** Since the sampled test sets have exactly 10% positives, recall at top 10% is equivalent to the fraction of true hotspots recovered when selecting as many cells as the number of true hotspots. That is intuitive. You already say this.

### Sampling paragraph

This paragraph is essential but arrives late. It is well written, but the full dataset versus sampled benchmark distinction should be introduced earlier.

**Issue:** “5,000 rows sampled per city with target-rate stratification: 500 positives and 4,500 negatives per city” is clear. However, because your final dataset has 71 million rows, a blind reader will want to know whether sampling changes the substantive conclusions.

You partly address this by calling it a controlled sampled benchmark, not exhaustive full-city operational scoring. Good.

**Suggested addition:**

> This sampling design gives each city equal sample size in the benchmark, preventing the largest urban areas from dominating model fitting, but it also means that reported transfer metrics should be interpreted as sampled benchmark performance rather than full-population city maps.

This is very important and persuasive.

---

## Pages 7-9: Analysis, Conclusion, and Discussion

### Section title

Current:

> Analysis, Conclusion and Discussion

Add Oxford comma:

> Analysis, Conclusion, and Discussion

### Within-city results paragraph

The result is compelling.

**Issue:** The paragraph gives exact means but does not say whether these are city-averaged or pooled. It says “Across the 30 cities,” which implies city means, but be explicit.

**Suggested edit:**

> Averaged across the 30 cities, random forest reaches…

If these are pooled, say pooled. This matters.

### “six-feature contract” again

Replace with “six-feature specification” or “six-predictor specification.”

### Interpretation of within-city RF result

Current:

> This result suggests that the six-feature contract contains useful local hotspot-screening signal and that nonlinear or interaction-like structure helps when local city examples are available during model development.

This is excellent. Keep with wording adjustment.

Suggested:

> This result suggests that the six-predictor specification contains useful local hotspot-screening signal and that nonlinear or interaction-like structure helps when examples from the same city are available during model development.

### City-held-out paragraph

Good. It immediately contrasts weaker transfer.

**Issue:** “gains over imperviousness and land-cover baselines are small and concentrate mainly in selected hot-arid cities” is important but not fully supported until later. Fine, but maybe cite Table 4 immediately:

> …as Table 4 later shows…

No actual citation needed in report, just refer to the table.

### Table 3 interpretation paragraph

Good.

**Issue:** PR AUC 0.1486 vs 0.1000 needs a reader-friendly interpretation. Is that meaningful? modest? You call it weaker and small; good. But you might add:

> In absolute terms, this remains a low-to-moderate ranking signal.

This prevents overclaiming.

### Matched 5k comparison paragraph

Excellent. This is one of the best result paragraphs because it is nuanced: RF wins pooled PR AUC and recall@top10; logistic slightly wins mean city PR AUC; 20k logistic is context, not headline.

**Potential issue:** Too many numbers in one paragraph. It is still readable. If space allows, keep.

**Suggested edit:** “At the same time” can become “However” for sharper contrast.

### Ranking result paragraph

Very strong. The sentence:

> In practical screening terms, much of the transferable retrieval signal in this six-feature contract is already captured by simple built-intensity information.

This is one of the best conclusions in the report.

Replace “contract” with “feature set.”

### Validation-design comparison paragraph

Excellent. This is the core argument.

**Issue:** “Figure 4 should therefore be interpreted as a validation-design comparison rather than a single leaderboard…” is exactly right, but again, the figure design must support that. See figure critique below.

### Figure 5 paragraph

This is strong. The correlations are clear and substantively meaningful.

**Issue:** “weak relationships mean that cities that look comparatively learnable…” Good, but “learnable” could be explained:

> cities where held-out cells are easy to classify using same-city training data…

Suggested rewrite:

> These weak relationships mean that cities where held-out cells are easy to classify using same-city training examples are not necessarily the cities where a model trained on other cities transfers well.

This is more accessible.

### Signal-shift insertion

This is a high-value placeholder. The eventual insertion should answer:
- Which cities are outliers?
- Are hot-arid cities driving RF gains?
- Does within-city RF performance mostly reflect local spatial regularities that do not transfer?
- Are transfer successes associated with climate group, urban form, sample composition, or label comparability?
- Is the failure due to model class, feature set, or target definition?

Do not let this insertion become too long. It should directly interpret Figure 5 and connect to Tables 4-6.

### Transfer heterogeneity paragraph

Good.

**Issue:** “RF improves several folds” is vague. Which folds? Table 5 shows folds 0, 3, 4 for PR AUC and 0, 3, 4 for recall; folds 1 and 2 worse. Say that.

Suggested:

> At the fold level, RF improves over logistic in folds 0, 3, and 4 but underperforms in folds 1 and 2.

This is more concrete.

### Climate pattern caveat

Excellent. Keep:

> The climate pattern should be read as a benchmark-generated hypothesis rather than an established causal explanation.

This is exactly the right tone.

### Denver paragraph

Conceptually strong. The Denver map is a good diagnostic.

**Issue:** The phrase “captures some spatial structure” is vague. What structure? Does it capture corridors, clusters, urban core, edge patterns? If the figure is too small to see, the text should say more.

Suggested:

> The predicted high-risk cells are not randomly scattered, but the false positive and false negative maps show spatially clustered misses rather than independent noise.

If you can name a visible pattern, do so.

### Feature-importance paragraph

Good, but very short. Since Appendix Figure A2 is visually dense, the main text should tell me the headline finding:

> Appendix Figure A2 suggests that NDVI and imperviousness are among the most important random-forest predictors, while logistic coefficients are harder to interpret because land-cover categories depend on the omitted reference level.

Only say this if accurate from the figure. The figure appears to show RF permutation importance highest for NDVI, then imperviousness, then climate group, then land cover, elevation, distance to water. That is worth mentioning.

### Conclusion paragraph

Strong and bounded. The phrase “main contribution is separating same-city learnability from cross-city transferability” is excellent. Keep.

### Validity paragraph

Very good. See earlier suggestion to add city-relative target caveat.

**Issue:** The sentence is long:

> Construct validity is limited by the LST-versus-exposure distinction and the 30 m analytic-grid caveat described earlier.

Good content, but maybe split construct validity into two pieces:
- LST is not air temperature or exposure.
- 30 m grid is a common analytic unit, not native resolution for every variable.

### Future work paragraph

This is good and appropriately specific.

**Opportunity:** This section is a “great find,” as you said in prior context. It could be even stronger by grouping future work into model/data/evaluation directions.

Current:

> Future work should extend both sides of the evaluation contrast by scoring larger held-out samples or full held-out cities, adding uncertainty summaries over cities, testing neighborhood-context predictors, and comparing the LST-based target with air-temperature, exposure, or vulnerability measures where such data are available.

This is excellent. Keep it, but consider adding one sentence:

> The most direct next step is full held-out-city scoring, because it would test whether the sampled benchmark conclusions hold across each city’s complete spatial distribution.

That gives priority.

---

## 5. Tables critique

## Table 1: Data Sources and Constructed Variables

### Overall

This table is useful and assignment-relevant. It supports “How data was collected” and “variables.” It is a strong inclusion.

### Problems

1. **It is visually cramped in the PDF.** The narrow columns cause awkward line breaks and make it harder to scan.
2. **Some entries are too verbose.** For example, Census urban areas row contains a lot of text.
3. **“Used in headline model?” is useful but “headline” may sound informal.** Use “Used in primary model?” or “Used as predictor?”
4. **The ECOSTRESS row has multiple variables with semicolons in a narrow cell.** This is hard to read.
5. **MODIS/Terra NDVI row appears to have `ndvi_median_may_augSummertime` without spacing in the parsed text and possibly in visual layout.** Check the PDF table. If the spacing is actually broken, fix it.

### Specific suggestions

- Consider landscape orientation for Table 1, or reduce column count.
- Replace “Spatial role” with “Role in dataset.”
- Replace “Used in headline model?” with “Primary predictor?”
- Use shorter entries:
  - “Defines city footprint and grid.”
  - “Categorical surface-cover predictor; open-water filter.”
  - “Continuous built-intensity predictor.”
  - “Terrain predictor.”
  - “Distance-to-water predictor.”
  - “Vegetation predictor.”
  - “Outcome source and LST quality support.”

### Blind-reader question

For ECOSTRESS, the table says the raw product is “daytime land-surface-temperature observations.” Is it always daytime? ECOSTRESS has varied overpass times. If the product selection is daytime-only because you filtered it, say so. If not, avoid “daytime” unless correct.

---

## Table 2: Final Dataset Summary by Climate Group

### Overall

Useful. It demonstrates balance by city count, imbalance by row count, and 10% prevalence.

### Problems

1. **Column wrapping makes it visually ugly.** “Hot-arid,” “Hot-humid,” and “Hotspot prevalence” break awkwardly.
2. **Median valid ECOSTRESS passes is useful but not interpreted in main text.** You mention pass count in methods, but not this table’s values.

### Suggested caption improvement

Current title is fine, but caption could say:

> Each climate group contains 10 cities, but row counts differ because urban-area extents differ. Hotspot prevalence is approximately 10% by construction after city-level recomputation.

This would make the table more self-explanatory.

### Potential issue

The table rounds prevalence to 0.1000. Since positives are exactly nearest top 10%, that is okay. But if exact counts do not equal exactly 10% due to ties/rounding, no problem.

---

## Table 3: Main City-Held-Out Benchmark Metrics

### Overall

This is one of the most important tables. It supports the main transfer conclusion.

### Strengths

- Includes baselines.
- Separates 5k matched comparison from 20k logistic context.
- Includes pooled PR AUC, mean city PR AUC, recall@top10, runtime.

### Problems

1. **The table is visually fragmented by line wrapping.** Model names wrap awkwardly, making it harder to compare rows.
2. **Runtime is not central to the argument.** It is interesting, but if the table is cramped, runtime could move to appendix.
3. **Global-mean and climate-only baselines showing below 0.1000 may confuse readers.** The note explains tie handling, which is good, but the table still invites “why is no-skill better than global mean?” confusion.
4. **“Rows labeled 5,000 sampled…” caption is awkward.**

### Suggested caption

> Metrics are from the city-held-out benchmark. Rows marked “5,000 sampled” use the same target-rate-stratified per-city sample and are directly comparable. The 20,000-row logistic run is included only as higher-sample linear context.

### Suggested table edit

Rename “Rows per city” values:
- `5,000 sampled`
- `20,000 sampled`

Fine.

Rename model checkpoint:
- No-skill reference
- Global mean
- Climate only
- Impervious only
- Land cover only
- Logistic SAGA, 5k
- Logistic SAGA, 20k context
- Random forest, 5k

### Interpretation issue

The table should visually highlight that RF has best pooled PR AUC and recall@top10 but logistic has best mean city PR AUC. If you can bold maxima in each column, do it. If not, the text already states it.

---

## Table 4: RF Minus Logistic Performance by Climate Group

### Overall

Useful for heterogeneity. It supports the claim that RF gains concentrate in hot-arid cities.

### Problems

1. The table is hard to read because columns are numerous and wrapped.
2. It reports wins and mean deltas, but not medians. With only 10 cities per group, means may be driven by one outlier.
3. The text says climate pattern is hypothesis-generating, which is good.

### Suggested improvement

Add or mention median deltas by climate group if available. If not, keep as is.

### Possible caption enhancement

> Positive deltas mean RF outperformed matched 5k logistic within the same held-out cities. The hot-arid advantage is hypothesis-generating because cities were purposively selected and climate group is confounded with geography and urban form.

That caption would prevent overinterpretation.

---

## Table 5: Fold-Level RF Minus Logistic Comparison

### Overall

Useful but possibly too detailed for main tables. It may belong in appendix unless you need it to support heterogeneity.

### Problems

1. It is visually very cramped and ugly in the PDF.
2. The broken negative signs and wrapped labels make it hard to read.
3. It contains many columns that duplicate information.
4. A blind reader may not care about train rows/test rows/test positives/test prevalence after this has already been explained.

### Recommendation

Move Table 5 to the appendix unless main table count is not a concern. In the main text, summarize fold-level result in one sentence.

If kept in main tables, simplify:
- Outer fold
- Logistic PR AUC
- RF PR AUC
- Delta PR AUC
- Logistic recall@top10
- RF recall@top10
- Delta recall@top10

Remove train rows/test rows/test positives/test prevalence because they are constant and already described.

---

## Table 6: City-Level Paired RF Minus Logistic Summary

### Overall

Good compact heterogeneity summary. This is more useful in main tables than Table 5.

### Problems

1. The row labels wrap badly (`City PR AUC`, `City recall@top10`).
2. The table clearly shows RF wins only 9 of 30 city comparisons for both metrics, which is important. The main text should emphasize this more.

### Suggested interpretation sentence

> Although RF has the best pooled recall@top10, logistic wins 21 of 30 city-level PR AUC and recall@top10 comparisons, showing that RF’s aggregate gains are not broadly uniform.

This is a strong nuance and should be in the main analysis.

---

## Appendix Table A1: Final Dataset Columns

### Overall

Very useful. Supports reproducibility and variable clarity.

### Problems

1. It is long and visually dense.
2. It uses “headline model” again.
3. Some definitions could be shorter.

### Specific edit

Change “Used in headline model?” to “Used as primary predictor?” or “Used in primary benchmark?”

### Potential issue

The table says `climate_group` is “Predictor / stratifier.” Since climate group is used as a predictor in the model and city selection balance, this is okay. But make clear that outer folds are by city, not by climate only.

---

## Appendix Table A2: Model Run Metadata

### Overall

Good. It documents tuning settings and makes the modeling work look serious.

### Problems

1. “Estimated inner fits” may be too internal unless explained.
2. The random forest row says “targeted RF search,” while logistic says “full.” This could invite the question: was RF tuned less thoroughly than logistic? You should acknowledge or justify that if relevant.

### Suggested note

> RF tuning used a smaller targeted grid because each fit was substantially more expensive; the 5k sample cap was held fixed for the matched model comparison.

Only include if true.

---

## Appendix Table A3: Model and Baseline Specifications

### Overall

Very good appendix table. It answers many method questions.

### Problems

1. It is too wide and line-wrapped. Consider landscape orientation or smaller font.
2. It might duplicate method text, but in appendix that is fine.

### Specific concern

The no-skill reference says “PR AUC and top-decile recall equal to the 10% target rate.” That is conceptually right for a prevalence reference, but actual constant-score implementation can differ due to tie handling. Your Table 3 note handles this. Good.

---

## Appendix Table A4: City and Fold Composition

### Overall

Useful and important. It lets the reader verify city composition.

### Problems

1. Very long, but appropriate for appendix.
2. Climate-group names wrap awkwardly.
3. Some city names wrap awkwardly.

### Suggested improvement

If possible, make this table landscape or use smaller font. It is appendix, so visual ugliness is less damaging.

---

## 6. Figure critique

## Figure 1: Study City Locations

### Overall

This is a good figure. It immediately communicates the 30-city benchmark and broad geographic/climate spread. It is meaningful and belongs in the report.

### Strengths

- Clear color grouping.
- City labels make the panel interpretable.
- It supports the claim that the benchmark spans western, southern, and northern U.S. regions.

### Problems

1. **It is not a map, but it looks like a scatterplot in longitude/latitude.** That is acceptable, but a blind reader may expect state outlines. Without a basemap, city locations are interpretable but visually sparse.
2. **Some labels are small.** In the PDF, labels are readable but not comfortable.
3. **The legend is small and sits inside the plot.** It is okay but could be cleaner.
4. **The colors are reused throughout the report, which is good.** Make sure the same hot-arid/hot-humid/mild-cool palette is consistent everywhere.

### Suggested improvements

- Add a light U.S. outline if easy. This would make it more map-like and easier for a blind reader.
- Increase point size and label font slightly.
- Consider moving legend outside plot or enlarging it.
- Use title: “Thirty Study Cities by Climate Group” instead of “Study City Locations by Climate Group.”

### Caption critique

Current caption is good. It says Appendix Table A4 lists full details. Keep.

---

## Figure 2: Dataset Construction Workflow

### Overall

This is conceptually very useful. It helps explain a complex workflow without overwhelming the reader. It belongs in the report.

### Strengths

- Clean left-to-right/top-to-bottom flow.
- Makes clear that inputs feed per-city features, final dataset, audit/splits, and modeling.
- Visually supports the claim that this is a reproducible pipeline.

### Problems

1. **The small text inside boxes may be difficult to read in PDF.**
2. **Some labels sound internal:** “Audit and Split Contract,” “Modeling And Delivery,” “Canonical benchmark story.”
3. **The workflow has arrows that may be visually confusing because final dataset points to audit/split then modeling, while per-city features points down to final dataset. This is okay, but the layout could be cleaner.**
4. **“Modeling And Delivery” should use title case consistently: “Modeling and Delivery.” Better yet, “Model Training and Evaluation.”**

### Suggested box text edits

- “Study Design” box:
  - `30 cities`
  - `Census urban area + 2 km buffer`
- “City Grids”:
  - `Local UTM 30 m grid`
  - `Core and buffered extents`
- “Input Layers”:
  - `NLCD, 3DEP, NHDPlus HR`
  - `MODIS NDVI and ECOSTRESS LST`
  - `May-August 2023`
- “Per-City Features”:
  - `Aligned to city grid`
  - `One feature table per city`
- “Final Dataset”:
  - `71.4M grid cells`
  - `17 columns`
  - `One row per 30 m cell`
- “Quality Checks and Splits”:
  - `Missingness and row-count audits`
  - `Binary target validation`
  - `City-held-out folds`
- “Model Training and Evaluation”:
  - `Training-only preprocessing`
  - `Held-out city predictions`
  - `Transfer metrics and diagnostics`

### Caption critique

Current caption is long but useful. It could be simpler:

> Figure 2 shows the construction pipeline from city study regions and public source layers to aligned per-city features, final dataset audits, city-held-out folds, and model evaluation.

The current caption repeats details already in the figure. Shorten if space is tight.

---

## Figure 3: City-Held-Out Evaluation Design

### Overall

This is one of the best figures. It directly supports the report’s central validation argument.

### Strengths

- Clearly shows 30 cities, 5 folds, 6 held-out cities per fold.
- The leakage guardrail box is valuable.
- The bottom explanation helps a blind reader understand fold k.

### Problems

1. **Text is slightly small.**
2. **The colored city blocks are cute but may not add much unless the colors map to climate group.** They appear to be small blocks but not fully explained. If they represent held-out cities, say so.
3. **“No city appears in both training and testing” is very important. Make it larger or bolder.**
4. **“Primary metric: PR AUC…” appears in tiny text at the bottom. This is important but hard to read.**

### Suggested improvement

Make the bottom rule the visual centerpiece:

> For fold k: train on 24 cities, tune within training cities, test on 6 unseen cities. No city appears in both train and test.

That is the whole point.

### Caption critique

Current caption is concise and good. Keep.

---

## Figure 4: Within-City and City-Held-Out Results Side by Side

### Overall

This figure is important, but it is also the figure most likely to mislead a blind reader. It tries to compare validation designs while using different metrics. The caption warns against comparing magnitudes, but the visual layout still invites comparison.

### Strengths

- It communicates the headline story quickly: RF dominates within-city; transfer is closer.
- The two-panel structure is intuitive.
- Values are labeled.

### Major problems

1. **Different metrics are placed side by side on similar visual scales.** A reader may compare within-city F1/precision/recall directly to transfer PR AUC/recall even though the caption says not to.
2. **The right panel uses dot/line markers while left uses bars.** This helps distinguish designs, but the relationship between designs still feels too direct.
3. **The within-city panel visually dominates because the bars are much larger.** This could make transfer look “bad” simply because different metrics have different scales.
4. **Caption is doing too much work.** A good figure should not depend on a warning to avoid misreading.

### Suggested redesign options

**Option A: Keep figure, add stronger separation.**
- Put a vertical divider between panels.
- Add subtitles:
  - `Within-city held-out cells (thresholded classification metrics)`
  - `City-held-out transfer (ranking/screening metrics)`
- Add a text note under the panels:
  - `Metrics differ by design; compare model ranking patterns, not absolute heights across panels.`
- Use separate x-axis ranges appropriate to each panel.

**Option B: Split into two figures.**
- Figure 4A: Within-city results.
- Figure 4B: City-held-out transfer results.
This avoids the misleading side-by-side comparison but weakens the “contrast” story.

**Option C: Make it a model-rank figure rather than raw metric figure.**
- Show RF-minus-logistic deltas within each design.
- This would directly show that RF gains are large within-city and modest/mixed in transfer.
- But it may be less intuitive.

### Specific visual comments

- The left panel labels are readable.
- The right panel values are small; increase annotation size.
- The metric labels on the right are a little awkward: “Recall @ Top 10%” should be consistent with text “recall at top 10% predicted risk.”
- The right x-axis starts around 0.14, which visually expands small differences. That is okay if intentional, but it can exaggerate gaps. Consider starting at 0.10 reference or clearly showing the prevalence line.

### Caption critique

The current caption is good and responsible. Keep the warning. But if you keep the figure as-is, make the warning even stronger:

> The panels use different metric families and should not be compared by absolute magnitude; the figure is intended to compare model-ranking patterns within each validation design.

---

## Figure 5: City-Level Signal Shifts Across Evaluation Designs

### Overall

This is one of the most intellectually interesting figures. It directly supports the claim that within-city performance does not predict transfer performance.

### Strengths

- Each point as a city is intuitive.
- Climate-group colors allow heterogeneity exploration.
- Correlation values are directly shown.
- The figure supports a non-obvious conclusion.

### Problems

1. **The points are small and some overlap.**
2. **City names are not labeled, so outliers cannot be identified.** As a blind reader, I want to know which cities are driving the high/low values.
3. **The correlation labels are very small and easy to miss.**
4. **The titles “RF City Ranking Shifts” and “Retrieval Signal Shifts” are a bit vague.**
5. **Axes are technical but okay.**

### Suggested improvements

- Label 3-5 notable outlier cities, especially:
  - high within-city but low transfer,
  - low within-city but high transfer,
  - highest transfer PR AUC,
  - highest transfer recall@top10.
- Increase correlation label font and write:
  - `Pearson r = 0.08`
  - `Pearson r = 0.03`
- Rename panel titles:
  - `Within-city F1 vs. held-out-city PR AUC`
  - `Within-city recall vs. held-out-city recall@top10`
- Add a faint trend line only if it does not imply meaningful slope. With r ≈ 0, no line may be better.

### Caption critique

Current caption is good. It explains both panels. Keep, but add the interpretive consequence:

> The lack of association suggests that same-city learnability and cross-city transferability are distinct model behaviors.

---

## Figure 6: Held-Out Denver Map Example

### Overall

This is visually and conceptually valuable. It gives the report a spatial diagnostic, which is important for a geospatial ML project. It makes the results feel real.

### Strengths

- Three panels tell a complete diagnostic story:
  - predicted high risk,
  - observed hotspots,
  - error pattern.
- The map supports the claim that errors are spatially structured.
- Denver as a held-out city is a concrete example.

### Major problems

1. **The maps are too small in the PDF.** The spatial patterns are hard to inspect.
2. **The legend is low and small.**
3. **It is unclear what gray points represent in the first two panels.** The legend says “Other Cells,” but in the first panel are red points predicted top-decile and gray others? In the second, dark red true positives? Clarify.
4. **The first panel title “Predicted Top-Decile Risk” could mean continuous risk or selected top-decile predicted cells. It appears to show selected predicted top-decile cells.**
5. **The third panel “Error Pattern” is excellent, but the colors for false positives/false negatives need to be maximally distinguishable in print.**
6. **No geographic context is provided.** A blind reader does not know where downtown Denver, mountains, highways, or water are. That may be okay, but the map is abstract.

### Suggested improvements

- Make Figure 6 full-page width or move it to appendix with larger dimensions.
- Rename first panel:
  - `Predicted top 10% cells`
  rather than `Predicted Top-Decile Risk` if it shows a binary top-decile selection.
- Rename second panel:
  - `Observed hotspot cells`
- Rename third panel:
  - `Prediction error categories`
- Add a sentence in caption:
  - `Gray cells are sampled non-selected/other cells in the held-out Denver test set.`
- Consider adding city boundary outline or light basemap if possible.
- Consider increasing point size or alpha so patterns are visible.

### Caption critique

Current caption is good but split across pages in the PDF. The figure appears on page 15 and the caption continues on page 16. That is visually awkward.

**Recommendation:** Resize or move the figure/caption so they stay together. A caption split across pages makes the report look less polished.

---

## Appendix Figure A1: Final Dataset Row Counts by City and Climate Group

### Overall

Useful and clear. It supports the row-count imbalance caveat.

### Strengths

- Horizontal bars are appropriate.
- Group coloring helps.
- Sorting makes comparison easy.

### Problems

1. **The figure is a bit too large vertically relative to its informational value.** It takes almost a full page.
2. **The x-axis label says “Final dataset rows (millions),” good.**
3. **Legend is readable.**

### Suggested improvement

Keep as appendix. It is fine.

---

## Appendix Figure A2: Supplemental Feature-Importance Summary

### Overall

Conceptually useful but visually weak. It is too dense and hard to read.

### Strengths

- Includes both logistic coefficient summary and RF permutation importance.
- Caption correctly says predictive, not causal.
- It supports interpretability.

### Problems

1. **The logistic coefficient panel has many tiny category labels.** It is difficult to read.
2. **The two panels have very different interpretive meanings but are placed side by side.** Coefficients and permutation importance are not directly comparable.
3. **The logistic panel uses land-cover code labels that a blind reader cannot interpret.** `land_cover_class_90` etc. require a legend or mapping.
4. **The title “Supplemental Feature-Importance Summary” may overstate logistic coefficients as feature importance.**
5. **The RF panel is readable and more useful than the logistic panel.**

### Suggested improvements

- Split into two appendix figures:
  - A2a Logistic coefficient summary
  - A2b RF permutation importance
- For logistic coefficients, show only top 10 absolute coefficients and include land-cover descriptions if possible:
  - e.g., `Woody wetlands (90)`, `Developed high intensity (24)`, etc.
- Rename:
  - `Supplemental Model Interpretation Diagnostics`
- Add note:
  - `Coefficient magnitudes depend on scaling and encoding; land-cover levels are relative to the omitted category.`

The current caption says some of this. Good, but the visual itself is still hard.

---

## Appendix Figure A3: City-Held-Out Benchmark Metric Comparison

### Overall

This is useful but visually cramped. It duplicates Table 3 in graphical form.

### Strengths

- Shows baseline/model comparison across all metrics.
- Dashed 10% reference is helpful.
- Makes it visually clear that RF is only modestly above simpler baselines.

### Problems

1. **X-axis labels are too small and angled.**
2. **The three-panel layout is cramped.**
3. **Colors are not immediately explained in the figure itself.**
4. **It may be redundant with Table 3.**

### Recommendation

Keep in appendix. It is not strong enough for main text. If you keep it, increase width or make each metric a separate horizontal bar chart.

---

## Appendix Figure A4: City-Level RF Minus Logistic Deltas

### Overall

This is a strong diagnostic figure. It supports transfer heterogeneity and reveals city-level variation.

### Strengths

- RF-minus-logistic deltas are directly tied to the model comparison.
- Sorting makes winners/losers visible.
- Climate colors add interpretive context.
- Shows that RF gains are driven by a minority of cities.

### Problems

1. **Text is small.**
2. **Two panels are cramped.**
3. **The x-axis label for the right panel says `Delta in recall at top 10%`, good.**
4. **The legend is inside and may cover data or take space.**
5. **If this figure is important to the main argument, it may deserve main-text placement more than Table 5.**

### Suggested improvement

Consider moving this to the main figures if space allows, because it is more visually informative than fold-level Table 5.

Caption should say:

> RF gains are concentrated in a small number of cities rather than uniformly distributed across the benchmark.

This is the key interpretation.

---

## Appendix Figure A5: Absolute Random-Forest City PR AUC

### Overall

This is useful and readable. It shows heterogeneity in absolute transfer performance.

### Strengths

- Horizontal sorted bars are effective.
- Dashed 0.10 reference is helpful.
- City labels are readable.
- It reveals Nashville as a major high-performing outlier.

### Problems

1. **Nashville is a huge outlier.** The report should mention or contextualize this somewhere if the figure is included. A blind reader will wonder: why is Nashville so high?
2. **The dashed 10% reference label is small and overlaps near the line.**
3. **The caption is clear but minimal.**

### Suggested main-text addition

If you keep A5, mention:

> Absolute RF PR AUC varies widely across held-out cities, with a few high-performing cities driving much of the apparent transfer signal.

This prevents the pooled metric from being overread.

---

## 7. Specific wording edits and sentence-level fixes

Below are highly specific edits by location. These are not all mandatory, but they are the kinds of changes that would make the report feel more polished and less internal.

### Page 2, paragraph 1

Current:
> thermal exposure is not distributed evenly across a city

Suggested:
> surface heat and related exposure risks are not distributed evenly across a city

Reason: avoids implying LST directly measures human exposure.

### Page 2, paragraph 1

Current:
> whether publicly available spatial variables can help rank local cells for screening when direct thermal labels are limited

Suggested:
> whether publicly available spatial variables can rank local grid cells for screening when direct thermal measurements are unavailable, incomplete, or held out

Reason: “direct thermal labels are limited” is slightly awkward.

### Page 2, paragraph 2

Current:
> familiar places

Suggested:
> the same city or study area

Reason: more formal and precise.

### Page 2, paragraph 2

Current:
> rather than just pipeline details

Suggested:
> rather than merely implementation details

Reason: less internal.

### Page 2, LST paragraph

Current:
> how warm the observed surface would feel to the touch

Suggested:
> the temperature of the observed land surface itself

Reason: more scientifically precise.

### Page 2, literature paragraph

Current:
> Together, this work motivates the feature set used here

Suggested:
> Together, this work motivates an interpretable feature set based on vegetation, imperviousness, land cover, terrain, water proximity, and broad climate context

Reason: makes the feature set explicit.

### Page 3, AppEEARS paragraph

Current:
> AppEEARS supports the reproducible remote-sensing part of the workflow

Suggested:
> AppEEARS, NASA’s tool for requesting and subsetting Earth observation products, supports the reproducible remote-sensing part of the workflow

Reason: defines AppEEARS for blind readers.

### Page 3, contribution paragraph

Current:
> standardized multi-city benchmark

Suggested:
> standardized multi-city evaluation benchmark

Reason: clarifies benchmark type.

### Page 3, contribution paragraph

Current:
> feature contract

Suggested:
> feature set or model specification

Reason: less internal.

### Page 3, research question

Current:
> Can basic environmental and built-environment features identify urban heat hotspots across a multi-city dataset, and how does performance change when evaluation moves from within-city held-out cells to whole-city held-out transfer?

Suggested:
> Can basic environmental and built-environment features identify urban heat hotspots across a multi-city dataset? How does performance change when evaluation moves from within-city held-out cells to whole-city holdout transfer?

Reason: easier to read as two questions.

### Page 3, unit of analysis

Current:
> The unit of analysis is a 30 m grid cell, but the stricter transfer evaluation uses city_id as the grouping variable.

Suggested:
> The unit of analysis is a 30 m grid cell, while the strict transfer evaluation treats the city as the grouping unit: all cells from a held-out city are excluded from training.

Reason: explains implication.

### Page 4, Dataset Construction

Current:
> The coarse climate groups make the transfer question more interpretable without replacing formal climatology or local meteorology.

Suggested:
> The coarse climate groups help structure the transfer comparison, but they should not be interpreted as a substitute for formal climatology or local meteorological analysis.

Reason: clearer caveat.

### Page 4, study region paragraph

Current:
> The buffer captures nearby land-cover and water-adjacency transitions that can affect urban thermal patterns

Suggested:
> The buffer captures near-urban land-cover and water-adjacency transitions that may affect urban thermal patterns

Reason: “nearby” could refer to nearby what.

### Page 4, grid paragraph

Current:
> master 30 m grid

Suggested:
> city-specific 30 m analytic grid

Reason: clearer and less internal.

### Page 4, 30 m caveat

Current:
> The phrase “30 m dataset” refers to the analytic grid and row unit, not the native resolution of every source variable.

Keep. This is excellent.

### Page 5, ECOSTRESS observations sentence

Current:
> Cells with fewer than three valid ECOSTRESS observations are removed when LST is available.

Suggested:
> Cells are retained for labeling only when at least three valid ECOSTRESS observations contribute to the May-August LST summary.

Reason: current wording is confusing.

### Page 5, assembly paragraph

Current:
> with CSV also written as a compatibility output

Suggested:
Remove from main text.

Reason: reproducibility detail, not main argument.

### Page 5, audit paragraph

Current:
> The feature-missingness summary is favorable for the headline predictors

Suggested:
> Missingness is low for the primary predictors

Reason: simpler.

### Page 5, Figure 2 lead-in

Current:
> not an ad hoc spreadsheet

Suggested:
> a standardized, reproducible grid-cell dataset rather than a manually assembled collection of city-specific summaries

Reason: more polished.

### Page 5, Model and Method opening

Current:
> Given that construction

Suggested:
> Using this constructed dataset

Reason: smoother section transition.

### Page 6, excluded variables

Current:
> because they could let a model memorize location-specific patterns

Suggested:
> because they could allow the model to exploit location identity rather than portable surface-characteristic relationships

Reason: more precise.

### Page 6, within-city paragraph

Add:
> Because cells from the same city can appear in both training and testing, this design measures same-city interpolation rather than cross-city generalization.

Reason: sharpens validation contrast.

### Page 6, city-held-out paragraph

Current:
> Every city is held out exactly once.

Keep. This is clear.

### Page 6, city-held-out paragraph

Current:
> inner cross-validation for tuning also occurs only within the training cities

Suggested:
> inner cross-validation for tuning is also grouped within the training cities

Reason: if true, clarifies grouping.

### Page 6, baselines paragraph

Current:
> very limited rules

Suggested:
> simple ranking rules

Reason: more precise.

### Page 6, logistic paragraph

Current:
> The classifier uses the saga solver

Suggested:
> The classifier uses the saga solver to support regularized L1, L2, and elastic-net logistic models

Reason: connects implementation to model class.

### Page 7, metrics paragraph

Add:
> PR AUC is emphasized because hotspot cells make up only about 10% of the benchmark sample, making accuracy less informative.

Reason: helps blind readers.

### Page 7, sampling paragraph

Current:
> This is a controlled sampled benchmark, not exhaustive full-city operational scoring

Keep. This is excellent.

Add:
> The sampling design gives each city equal sample size in the benchmark, but it does not preserve every detail of each city’s full spatial distribution.

Reason: balanced validity.

### Page 7, section title

Current:
> Analysis, Conclusion and Discussion

Suggested:
> Analysis, Conclusion, and Discussion

Reason: grammar/style.

### Page 7, within-city result

Current:
> Across the 30 cities

Suggested:
> Averaged across the 30 cities

Reason: clarifies aggregation, if true.

### Page 7, within-city result

Current:
> six-feature contract

Suggested:
> six-predictor specification

Reason: less internal.

### Page 7, transfer result

Current:
> weaker and closer result

Suggested:
> weaker and much closer model comparison

Reason: clearer.

### Page 8, ranking interpretation

Current:
> much of the transferable retrieval signal in this six-feature contract is already captured by simple built-intensity information

Suggested:
> much of the transferable retrieval signal in this six-feature set is already captured by simple built-intensity information

Reason: less internal.

### Page 8, Figure 5 interpretation

Current:
> cities that look comparatively learnable under within-city testing

Suggested:
> cities where held-out cells are comparatively easy to classify using same-city training data

Reason: clearer.

### Page 8, transfer heterogeneity

Current:
> improves several folds

Suggested:
> improves folds 0, 3, and 4 but underperforms in folds 1 and 2

Reason: more specific.

### Page 8, Denver paragraph

Current:
> captures some spatial structure

Suggested:
> identifies some geographically organized high-risk areas, but the false-positive and false-negative cells are also spatially clustered

Reason: more concrete.

### Page 8, feature importance

Current:
> Appendix Figure A2 provides feature-importance diagnostics.

Suggested:
> Appendix Figure A2 provides predictive interpretation diagnostics: RF permutation importance emphasizes NDVI and imperviousness, while logistic coefficients are more sensitive to categorical encoding and the omitted land-cover reference level.

Reason: makes the appendix figure meaningful in text.

### Page 9, validity paragraph

Add:
> The city-relative top-decile target also limits interpretation: a hotspot in each city means locally hot relative to that city, not equally hot in absolute LST or equally severe for human exposure.

Reason: important construct-validity caveat.

### Page 9, future work

Add:
> The most direct next step is full held-out-city scoring, which would test whether the sampled benchmark patterns hold across each city’s complete spatial distribution.

Reason: prioritizes future work.

---

## 8. Missing or underdeveloped explanations

### 8.1 Why choose top 10%?

The report defines `hotspot_10pct` but does not fully justify why 10% was chosen. A blind reader may ask: why not top 5%, top 20%, or absolute threshold?

Suggested explanation:

> A top-10% label creates a common within-city screening task across cities with different absolute temperature distributions. It also matches a practical prioritization frame: if planners could inspect or target only the highest-risk decile of cells, how many true local hotspots would be recovered?

This would connect the label to recall@top10.

### 8.2 What is the target population?

The assignment asks to clarify target population. The report implies it, but make it explicit.

Suggested sentence in Research Questions:

> The target population for inference is the set of eligible 30 m grid cells in the 30 selected U.S. urban-area study regions, not all U.S. cities or all forms of human heat exposure.

This is blunt and useful.

### 8.3 What exactly is “transfer”?

You explain it, but consider giving a one-sentence definition:

> In this report, transfer means training on one set of cities and evaluating on complete cities withheld from all model fitting and preprocessing.

This would be a good early definition.

### 8.4 How should PR AUC values be interpreted?

You compare to 0.10 prevalence reference, which is good. But state the interpretation:

> Since the sampled benchmark has 10% positives, a PR AUC near 0.10 corresponds to little useful ranking beyond prevalence; values above 0.10 indicate that true hotspots tend to receive higher scores than non-hotspots.

This should appear before Table 3 or in the Table 3 caption.

### 8.5 Are results calibrated probabilities or rankings?

You mostly interpret rankings, but the method says “estimate probability.” If the benchmark sample is stratified, calibration may be artificial.

Suggested:

> Because the benchmark uses target-rate-stratified samples, the reported scores are interpreted primarily as rankings for screening rather than calibrated probabilities of hotspot status in the full city population.

This is important.

### 8.6 Why include climate group as a predictor?

A blind reader may wonder whether including broad climate group in a city-held-out transfer model leaks city identity. It does not leak exact city identity, but it gives broad category.

Suggested clarification:

> Climate group is included as a broad, preassigned city-level descriptor rather than a city identifier; it does not identify individual held-out cities but may capture coarse regional thermal context.

If climate group is known for a new city at prediction time, this is reasonable.

### 8.7 Why exclude coordinates?

You explain this well. Keep.

### 8.8 Why are there neighborhood-context variables but not in headline model?

You mention they are reserved for supplemental modeling. A blind reader may ask why not use them if they might improve performance.

Suggested explanation:

> They are excluded from the primary benchmark to keep the first model comparison simple and to separate the value of basic cell-level public predictors from more engineered spatial-context features.

This is good future-work setup.

---

## 9. Tone and presentation issues

### 9.1 Avoid sounding defensive

Phrases like “not an ad hoc spreadsheet,” “not just pipeline details,” and “contract” can sound defensive or internal. Replace with positive descriptions:
- standardized
- reproducible
- leakage-controlled
- interpretable
- benchmarked
- city-held-out

### 9.2 Avoid overclaiming “public-health” when measuring LST

The report is careful overall, but the opening and motivation mention public health. That is valid as motivation, but always return to the caveat: LST is surface temperature, not direct human exposure.

### 9.3 Use “city-held-out” consistently

The report alternates:
- city-held-out transfer
- whole-city holdout
- held-out city
- cross-city transfer
- grouped city-held-out contract

These are all understandable, but choose a primary term:
- **city-held-out transfer** for the design,
- **held-out city** for units,
- **cross-city transfer** for conceptual interpretation.

Avoid “contract.”

### 9.4 Use “same-city” consistently

For within-city validation, “within-city held-out” is good. But also use “same-city interpolation” when contrasting with transfer.

### 9.5 Watch PDF hyphenation and extraction artifacts

The PDF contains many visible hyphenation breaks in the parsed text:
- `tempera- ture`
- `distinc- tion`
- `surface descriptors`
- `reproducible`
- `city-held-out`
- etc.

Some may be normal LaTeX line breaks. But if the PDF visually shows awkward discretionary hyphens, consider using fewer narrow text blocks or LaTeX settings to avoid them. This is not a content issue but affects polish.

---

## 10. Prioritized revision checklist

### Must fix before submission

1. **Fill or finalize the within-city methods insertion.** The thresholding/split/aggregation details are required for Figure 4 to be credible.
2. **Add explicit target population sentence.**
3. **Add explicit justification/caveat for city-relative top-10% hotspot label.**
4. **Clarify full dataset versus sampled modeling benchmark earlier.**
5. **Fix Figure 4 or strengthen its visual/caption warning.**
6. **Make Figure 6 caption stay with the figure and clarify what each color/category means.**
7. **Replace internal-sounding “contract” language in main text.**
8. **Add a plain-English abstract or opening roadmap.**
9. **Mention that transfer scores are ranking/screening scores, not calibrated full-city probabilities.**
10. **Add the city-relative target limitation to validity discussion.**

### Should fix if time allows

1. Simplify Table 5 or move it to appendix.
2. Improve Table 1 formatting.
3. Label outliers in Figure 5.
4. Make Figure 6 larger or more legible.
5. Add one-sentence interpretation of Appendix Figure A2 in main text.
6. Bold best values in Table 3.
7. Add a note explaining why climate group is allowed as a predictor.
8. Replace “headline model” with “primary benchmark” or “primary model.”
9. Add exact city names for notable transfer successes/failures if discussed.
10. Prioritize future work by naming full held-out-city scoring as the next most direct extension.

### Nice-to-have polish

1. Add a U.S. outline to Figure 1.
2. Split Appendix Figure A2 into two cleaner panels.
3. Make Appendix Figure A3 horizontal bars or separate charts.
4. Use landscape orientation for wide tables.
5. Standardize capitalization in figure box labels.
6. Use consistent terminology for model names: “Logistic SAGA” and “Random forest.”
7. Add a short “Data availability / reproducibility” sentence before the appendix notes.
8. Confirm all URLs/DOIs render correctly and are not broken by line hyphenation.
9. Make sure title and filename match the assignment’s naming requirement.
10. Ensure Nicholas’s inserted text matches tone, tense, and terminology of the rest of the report.

---

## 11. Suggested revised mini-roadmap for the introduction

If you add only one paragraph, I would add something like this near the end of Background Information:

> The report proceeds in four steps. First, it constructs a standardized 30-city grid-cell dataset from public geospatial and remote-sensing sources. Second, it defines a city-relative hotspot label based on the hottest 10% of valid May-August ECOSTRESS LST cells within each city. Third, it compares logistic regression and random forest under two validation designs: within-city held-out cells and city-held-out transfer. Finally, it uses city-level diagnostics to show that strong same-city performance does not necessarily imply strong transfer to unseen cities.

This paragraph would dramatically improve blind-reader orientation.

---

## 12. Suggested revised validity paragraph

Current validity paragraph is already good. A slightly strengthened version:

> Several validity limits shape the interpretation. Leakage control is strongest for the city-held-out transfer benchmark because complete cities are held out and preprocessing and tuning are fit using training cities only. Sampling validity is bounded by the 5,000-row-per-city benchmark rather than exhaustive all-row scoring; the sample preserves target prevalence and city balance, but not every detail of each city’s full spatial distribution. Spatial dependence and clustered errors can remain within held-out cities. Construct validity is limited because LST measures surface temperature rather than air temperature or direct human exposure, and because the 30 m grid is a common analytic unit rather than the native resolution of every source variable. The city-relative hotspot label also means that a positive cell is locally hot within its city, not necessarily equally hot in absolute LST or equally severe for public-health exposure across cities. External validity is limited because the 30 selected cities form a purposive benchmark set rather than a representative sample of all U.S. urban forms, climates, coastal settings, and topographies. Model-comparison validity is also bounded because within-city and transfer results use different metrics and should be interpreted as complementary validation questions rather than one combined leaderboard.

This preserves your content but adds the missing target caveat and improves flow.

---

## 13. Suggested revised future-work paragraph

Current paragraph is good. A stronger version:

> Future work should extend both sides of the evaluation contrast. The most direct next step is full held-out-city scoring, which would test whether the sampled benchmark patterns hold across each city’s complete spatial distribution. Additional work should add uncertainty summaries over cities, test whether neighborhood-context predictors improve transfer, evaluate more flexible spatial or hierarchical models, and compare the LST-based target with air-temperature, exposure, or vulnerability measures where such data are available.

This is more prioritized and shows a path forward.

---

## 14. Bottom-line assessment

This is a strong project and a strong draft. The statistical story is good: the report does not just chase the highest metric; it makes a serious validation argument. The strongest sentence-level idea is that **same-city learnability and cross-city transferability are different things**. Everything should be revised to make that idea impossible to miss.

The report will be submission-ready after the within-city placeholder is filled and the main blind-reader gaps are closed. The main risk is not that the project looks weak. The main risk is that the reader sees a very sophisticated workflow but has to infer too much about the target, sampling benchmark, metric interpretation, and validation contrast. Tightening those explanations will make the report feel much more self-contained and much more gradeable.
