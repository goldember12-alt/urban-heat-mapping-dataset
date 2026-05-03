# Critical Review of `stat5630_final_report_draft(11).pdf`

This review is intentionally severe. The draft has a real contribution and a defensible technical story, but its current presentation often hides that contribution under overqualification, repeated methodological framing, dense internal language, and figure/table choices that do not always serve the reader. The most important revision goal is not adding more information. It is sharpening the argument so a reader can quickly understand: **what was built, what was tested, what worked, what failed to transfer, and what the spatial diagnostic adds without overstating it.**

---

## Section 1 - Writing Critique

### 1. Overall diagnosis

The paper is substantively strong but rhetorically overloaded. It repeatedly tries to protect itself from overclaiming, which is good scientifically, but the accumulation of caveats makes the prose feel defensive and sometimes exhausting. The strongest version of this report would be more direct: it would state the contribution, define the evaluation designs once, use consistent terminology, and then let the results demonstrate the core contrast between within-city learning and city-held-out transfer.

Right now, the central argument is clear after careful reading, but not immediately clear on a first pass. The reader has to work through many repeated phrases: “city-held-out transfer,” “exact-cell retrieval,” “broader spatial placement,” “supplemental diagnostic,” “sampled benchmark,” “primary six-predictor benchmark,” “not a replacement,” “not operational evidence,” and “not causal.” These are mostly accurate, but they appear so often that they become verbal clutter.

The draft’s best writing appears when it explains the scientific motivation plainly: urban heat is spatially uneven; city averages hide local hotspots; LST is surface temperature rather than air temperature; same-city validation can be too easy; city-held-out transfer is harder. The weakest writing appears when the draft describes repo artifacts, diagnostic status, inferred splits, sanity checks, and appendix material in language that feels like internal project documentation rather than a final statistical learning report.

### 2. Is the writing repetitive?

Yes. The repetition is the largest writing problem.

The paper repeats the same conceptual contrast too many times: within-city performance is strong, city-held-out transfer is weaker, and spatial alignment partially complicates exact-cell retrieval. That contrast is the paper’s core, but it appears in the Background, Research Questions, Methods, Analysis, Conclusion, Limitations, and Future Work with only slight wording changes. Repetition is not inherently bad in a technical paper, but here the repeated framing often arrives before new evidence is introduced, so it feels like the paper is telling the reader how to interpret results before showing enough results.

Several phrases recur with near-identical function:

- “within-city held-out” versus “city-held-out transfer”
- “exact-cell retrieval” versus “broader spatial placement”
- “sampled benchmark” versus “full-city spatial diagnostic”
- “not a replacement for the sampled benchmark”
- “not operational evidence of intervention-ready hotspot boundaries”
- “hypothesis-generating rather than causal/explanatory”
- “primary six-predictor benchmark”
- “retained random-forest transfer model”

These phrases are conceptually useful, but their frequency makes the prose feel more like an audit memo than an article. A reader does not need to be reminded in every paragraph that the spatial diagnostic is supplemental. Define the hierarchy once, then use shorter terms afterward.

Recommended compression strategy:

- Define the three evaluation targets once near the end of the introduction:
  1. same-city interpolation,
  2. exact-cell transfer to unseen cities,
  3. broad spatial placement in unseen cities.
- After that, use those names consistently.
- Move repetitive caveats into one clearly labeled “Interpretation limits” paragraph or subsection.
- Delete redundant reminders unless they prevent a likely misreading at that exact point.

The “not X, but Y” construction is especially overused. It appears in many forms: LST is not air temperature; 30 m is analytic grid not native resolution; within-city is not transfer; spatial diagnostic is not replacement; spatial diagnostic is not operational evidence; climate groups are not formal climatology; feature importance is not causal. Each distinction is valid. Together, they create a paper that often sounds like it is apologizing for itself. The revision should preserve the distinctions but convert them into confident scope statements.

For example:

> Current pattern: “This is X, not Y, and should not be interpreted as Z.”

Better pattern:

> “This analysis estimates X. It is designed for Y-level screening, so Z remains outside the scope of this benchmark.”

That phrasing is still objective but less defensive.

### 3. Is everything well-explained?

Mostly, but not consistently. The draft explains the broad scientific context well and explains the validation logic well. However, several locally defined or internally meaningful terms are either introduced too late, used too often, or defined in a way that assumes the reader already knows the project history.

#### Terms that need clearer first-use definitions

**“Exact-cell retrieval.”** This is an important phrase, but it is not intuitive enough to carry the argument without a crisp definition. The paper eventually makes clear that it means recovering the specific grid cells labeled as top-decile LST hotspots in held-out cities. Define it explicitly the first time it appears.

Suggested definition:

> “I use exact-cell retrieval to mean whether the model ranks the same 30 m cells as hotspots that the observed LST label identifies as hotspots.”

**“Broader spatial placement.”** This phrase is understandable but vague. Does it mean the right neighborhood? The right side of the city? The right smoothed hotspot region? The spatial-alignment section later defines metrics, but the phrase appears before the measurement concept is concrete.

Suggested definition:

> “Broader spatial placement asks whether high predicted risk falls in the same smoothed parts of a city as observed hotspot concentration, even when the exact 30 m cells do not match.”

**“Support-checked 70/30 within-city diagnostic.”** This phrase is not intuitive and sounds like a project-internal artifact. It also raises a methodological trust issue: the draft says the 70/30 structure was “inferred and checked from the partner result support counts” and that the repo does not contain the original split script or random seed. That is important, but the current wording risks making the within-city comparison feel improvised. If those results are retained, the paper should clearly downgrade them as noncanonical and explain why they are still useful.

Suggested framing:

> “Because the original within-city split script was unavailable, we treat the within-city results as a diagnostic contrast rather than as a fully reproducible benchmark. Their purpose is to show the scale of the same-city/cross-city gap, not to establish a final within-city leaderboard.”

Then avoid repeatedly calling them “support-checked.” That phrase does not help an outside reader.

**“Target-rate-stratified samples.”** The sampling scheme matters. The draft says each city contributes 500 positives and 4,500 negatives, but the implication for metrics could be clearer. If the sampled data are exactly 10% positive by construction, then PR AUC and recall@top10 are interpretable relative to a 0.10 baseline, but the reader may ask how this affects full-city calibration and whether row weighting changes the story. The draft gestures at this; it should be more explicit.

**“Average precision” versus “PR AUC.”** The paper uses PR AUC and AP interchangeably in some places. The Figure 4 caption says “precision-recall AUC / average precision,” which is helpful, but this should appear in Methods before the results. A statistically sophisticated reader may ask whether the reported PR AUC is trapezoidal PR AUC or average precision. Pick one term as primary. If it is average precision from sklearn, call it “average precision (AP)” and then say it is used as the PR-ranking summary.

**“Climate group.”** The paper is careful that climate group is coarse and not formal climatology. Good. But it should also explain why “hot arid,” “hot humid,” and “mild cool” are enough for the modeling question. Are they hand-assigned? Based on a classification? Selected manually? The draft treats them as preassigned, but the reader may want one sentence on how the labels were determined.

#### Places where the reader is left with design questions

**The city selection process is underexplained.** The draft says the 30 cities were selected for geographic and climate variation while remaining feasible. That is acceptable, but still vague. A skeptical reader may ask: why these cities and not others? Why 10 per group? Why include both San Francisco and San Jose? Why is Denver “hot arid”? The paper does not need a full sampling theory, but it should include a concise selection rule or acknowledge that selection was purposive and workflow-driven.

**The 2 km buffer is plausible but not justified enough.** The draft says the buffer captures near-urban land-cover and water-adjacency transitions. That is reasonable, but a reader may ask why 2 km instead of 1 km, 5 km, or no buffer. If the choice is pragmatic, say so. If sensitivity was not tested, say that as a limitation or future work.

**The open-water filter is mentioned but not fully explained.** Table 1 notes open-water filtering where NLCD class 11 is present, and the methods mention open-water and ECOSTRESS quality filters. The reader needs one clean sentence explaining whether open-water cells were removed before labeling, why, and whether the filter affects coastal cities disproportionately.

**The target construction needs one more concrete example.** The draft defines `hotspot_10pct` accurately, but a non-expert reader would benefit from an example: in each city, after filtering, cells are ranked by median May-August LST; the hottest decile is labeled 1; all other eligible cells are labeled 0. This would make the outcome immediately intuitive.

**The spatial diagnostic is introduced before it is fully motivated.** The report says exact-cell retrieval may be too strict and planning may care about broad zones. That is a good motivation. But the paper should more clearly explain why smoothing at 150 m, 300 m, and 600 m is appropriate. These scales appear suddenly. Are they neighborhood scales? Robustness scales? Computational choices? The main text reports 300 m results but does not justify 300 m as the medium scale beyond naming it.

**The relationship between sampled model training and full-city spatial scoring needs stronger explanation.** The paper says models are trained/tuned on sampled training-city rows and then used to score all eligible held-out rows for spatial analysis. That is important. But the reader may wonder whether the random forest trained on 5,000 rows per city can meaningfully score tens of millions of full-grid cells, and whether the full-city scoring distribution differs from the sampled test distribution. This is not fatal, but it should be discussed more directly.

### 4. Is language intuitive, needlessly dense, and accurate?

The language is accurate but often needlessly dense. It frequently uses compound technical nouns where simpler language would be more readable.

Examples of dense or internal phrasing:

- “The final held-out prediction table is therefore a transfer test at the city level, not a same-city interpolation exercise.”
- “The matched 5k comparison is the primary logistic-versus-random-forest comparison.”
- “The broader spatial-placement diagnostic gives a cautious answer to that follow-up question.”
- “The report contributes a standardized multi-city evaluation benchmark with four linked pieces.”
- “retained-prediction sanity check”
- “target-rate-stratified per-city sample”
- “support-checked within-city 70/30 held-out diagnostic”
- “primary six-predictor benchmark”

None of these are wrong. The problem is accumulation. The prose often asks the reader to hold too many technical qualifiers in a single sentence.

Suggested style principle: use technical precision for the object of analysis, not for every surrounding modifier.

For example:

> Current: “The matched 5,000 rows-per-city comparison is the primary logistic-versus-random-forest comparison because both models share the same sample cap and fold design.”

Better:

> “The 5,000-row runs are the fair model comparison: logistic regression and random forest use the same cities, same sample size, and same fold design.”

That is clearer and stronger.

Another example:

> Current: “Weak PR AUC and recall-at-top-10% mean the model is limited at exact-cell hotspot retrieval, while the spatial diagnostic suggests that in some cities the transferred random forest still places elevated risk in broadly plausible zones.”

This is good, but it could be even more direct:

> “The model often misses the exact hotspot cells. In some cities, however, its high-risk surface still falls in roughly the right parts of the city.”

The second version is less formal but much more memorable. The paper can then define the metrics around that idea.

### 5. Does the text have a coherent voice?

Yes, but the voice is uneven. The dominant voice is cautious, technical, and methodologically responsible. That is appropriate for the project. However, the voice sometimes shifts into repo-handoff language: “partner result support counts,” “repo does not contain,” “retained model,” “canonical transfer benchmark,” “report-facing artifacts,” and long reproducibility artifact lists. Those details are useful, but they read as internal project state rather than polished final-report prose.

The paper should distinguish between three voices:

1. **Main paper voice:** explains research motivation, methods, results, and interpretation.
2. **Reproducibility voice:** gives file paths, scripts, artifacts, and exact regeneration commands.
3. **Audit voice:** explains limitations of inherited artifacts and noncanonical diagnostics.

Right now, all three voices appear in the main narrative. That weakens the paper’s professional tone. Move more of the audit/repo language to the Reproducibility Notes or a short appendix note. The main text can say the within-city diagnostic is less reproducible without mentioning “partner result support counts” unless necessary.

### 6. Is the paper logically structured?

Broadly, yes. The section order is sensible: background, research questions, dataset, methods, analysis, figures/tables, appendix. The biggest structural issue is that the results and discussion are combined into one very long section. “Analysis, Conclusion, and Discussion” is doing too much. It contains within-city results, transfer results, city-level shifts, heterogeneity, Denver maps, spatial alignment, feature importance, conclusion, limitations, and future work. This section would be stronger if separated.

Recommended structure:

1. **Background and Contribution**
2. **Research Questions**
3. **Dataset Construction**
4. **Modeling and Validation Design**
5. **Results**
   - 5.1 Within-city diagnostic
   - 5.2 City-held-out transfer benchmark
   - 5.3 City heterogeneity
   - 5.4 Spatial-alignment diagnostic
6. **Discussion**
   - What the results mean
   - Why within-city performance does not imply transfer
   - What the spatial diagnostic does and does not change
7. **Limitations and Future Work**
8. **Conclusion**

A separate conclusion should be short. The current conclusion is embedded in a long discussion and loses force.

The background is also somewhat long for the amount of literature it covers. It does a good job establishing remote sensing and spatial validation, but it could be tightened. The introduction should get to the paper’s actual contribution sooner. The strongest intro path is:

1. Urban heat hotspots matter because city averages hide local risk.
2. LST remote sensing can define fine-scale surface-temperature hotspots, but LST is not air temperature.
3. Many models may work within a city because nearby cells share structure.
4. The harder question is whether models transfer to cities never seen during training.
5. This paper builds a 30-city grid dataset and compares within-city screening, city-held-out exact-cell retrieval, and broader spatial placement.

That is the paper. The current introduction contains those pieces, but in a more diffuse order.

### 7. Is the reader engaged from start to end?

The opening is engaging enough because the problem is concrete and policy-relevant. The middle becomes less engaging because the paper spends many paragraphs on methodological safeguards before the reader sees the payoff. The results section recovers interest because the findings are genuinely interesting: random forest works well within city, transfer is much weaker, simple baselines are competitive, and spatial maps look partially coherent even when exact-cell metrics are modest.

The most engaging part of the paper is the tension between metric failure and visual/spatial plausibility. That tension should be foregrounded more. The current draft treats the spatial diagnostic cautiously, which is appropriate, but it buries the most interesting interpretive question: **what does it mean for a model to fail exact hotspot retrieval but still produce coherent high-risk surfaces?** That question is scientifically rich and should be made more explicit in the discussion.

A stronger discussion paragraph might say:

> “The transfer model is not reliable enough for exact 30 m hotspot selection. Yet the maps and smoothed-surface diagnostics suggest that, in some cities, it captures broad spatial gradients. This distinction matters because model evaluation can be too strict or too lenient depending on the intended use. If the use case is selecting exact cells for intervention, the transfer results are weak. If the use case is exploratory screening of broad candidate areas, the spatial diagnostic suggests partial value, but only in some cities and not yet at an operational standard.”

That paragraph is essentially already present in fragments. It needs to become the interpretive center.

### 8. Background, limitations, future work, and objectivity

The background is adequate and scientifically appropriate. It connects the feature set to prior LST/urban heat literature and connects the validation design to spatial cross-validation literature. The biggest issue is not missing background but excess framing. The paper could be shorter and stronger without losing scholarly grounding.

The limitations are unusually thorough. That is good, but the limitation section is so expansive that it risks overwhelming the contribution. The paper correctly notes limits involving LST versus air temperature, city selection, sampled benchmark rows, spatial dependence, smoothing scale, and validation-design comparability. However, the limitations are presented in a dense block that reads like a legal disclaimer.

Recommended limitation structure:

- **Construct validity:** LST is surface temperature, not air temperature or direct human exposure.
- **Sampling/external validity:** 30 purposively selected cities; sampled transfer benchmark; 30 m analytic grid not native resolution for every source.
- **Validation validity:** within-city diagnostic is noncanonical; city-held-out benchmark is stronger; spatial alignment answers a different question.
- **Model scope:** simple non-thermal predictors; no location coordinates; no spatial/hierarchical model; no vulnerability features.

That structure would let the paper highlight limitations without sounding dominated by them.

The future work section is solid but could be more ambitious and better organized. Right now it lists appropriate next steps: full-row held-out-city benchmark, spatial-alignment comparisons across model families, neighborhood-context predictors, flexible spatial/hierarchical models, uncertainty summaries, and comparison with air-temperature/exposure/vulnerability measures. This is good. It should be framed as an agenda that follows directly from the results:

- If exact-cell transfer is weak, test whether full-city training/scoring and richer features help.
- If broad spatial placement is partially present, evaluate it systematically across models and scales.
- If LST is not exposure, connect the target to air temperature and vulnerability.

The writing is objective overall. It does not overclaim. The larger risk is underclaiming: the paper’s contribution is real, but the prose repeatedly diminishes it before the reader can appreciate it. The conclusion should be more confident while still bounded.

### 9. Specific writing issues by section

#### Title page

The title is accurate but long and slightly clunky. “Cross-City Urban Heat Hotspot Screening: Within-City Learning and City-Held-Out Transfer” is good, but “Screening” and “Learning” may be a little abstract. Consider:

> “Urban Heat Hotspot Screening Across Cities: Same-City Learning, City-Held-Out Transfer, and Spatial Alignment”

This would include the spatial diagnostic, which has become important to the paper.

#### Background Information

The first paragraph is strong. It explains the problem in intuitive terms. The second paragraph starts to move into the research question, but the phrase “exact-cell hotspot retrieval is the strictest version of that transfer question” arrives before the reader fully understands the modeling setup. Define later or explain immediately.

The literature review is credible but compressed. The citations are used to justify feature selection and validation design. That works. However, the paragraph listing Voogt and Oke, Weng et al., Yuan and Bauer, Stewart and Oke, and Harlan et al. is dense. It could be split into two paragraphs: one on surface predictors and one on heat vulnerability/exposure scope.

The AppEEARS paragraph is too short and technical to stand alone. Either integrate it into Dataset Construction or expand it slightly in Methods. In the Background, it feels like a workflow detail interrupting the conceptual flow.

The final contribution paragraph is good but overloaded: “standardized multi-city evaluation benchmark with four linked pieces...” Then it immediately gives dataset size and climate groups. This is important, but the paragraph may be trying to be both a contribution statement and a dataset summary. Split it.

#### Research Questions

The primary research question is clear. The two-part question works.

The five secondary questions are useful, but five is a lot. Some overlap with the results narrative. Consider reducing them to three grouped questions:

1. Do non-thermal predictors rank local LST hotspots?
2. How much does performance degrade under city-held-out transfer, and do nonlinear models help?
3. Are failures purely exact-cell failures, or do predictions retain broader spatial alignment?

That would make the paper easier to follow.

The target population paragraph is strong and should stay. It is one of the clearest pieces of the paper. Add a simple example of the top-decile label.

#### Dataset Construction

This section is generally clear and well ordered. The distinction between the 30 m analytic grid and native source resolution is excellent and necessary.

The biggest weakness is that it contains many procedural details but does not always distinguish between design choices and constraints. For example, the May-August summary is framed as a compromise, which is good. The 2 km buffer is framed as substantive but lacks justification. City selection is framed as purposive but could be more explicit.

The final dataset summary paragraph is useful but dense. Consider moving some missingness details to Table 2 or an appendix table. In the main text, focus on the most interpretable dataset facts: 30 cities, 71.4M cells, 10% positives by city, uneven city sizes, low missingness.

#### Model and Method

This section is technically careful but too long. It should be reorganized around the two validation designs first, then models, then metrics, then sampling, then spatial diagnostic.

The feature exclusion paragraph is strong. It explains why coordinates, city IDs, and thermal variables are excluded. This is important because a reader might otherwise ask why location is omitted from a spatial problem.

The within-city paragraph is the weakest method paragraph because it introduces uncertainty about the split artifact. The repo/script issue should be stated cleanly and then contained. Avoid letting that uncertainty contaminate the whole method section.

The metric explanation is good and should probably appear before results. The PR AUC/no-skill baseline explanation is especially important.

#### Analysis, Conclusion, and Discussion

This section contains the paper’s strongest findings but is too compressed and too structurally broad.

The first paragraph on within-city results is clear. It gives numbers and interprets high precision/low recall appropriately.

The transfer benchmark paragraphs are also clear, but the comparison among baselines, logistic 5k, logistic 20k, and random forest 5k could be more visually and narratively direct. The key point is: random forest improves over logistic on pooled PR AUC and recall@top10, but not mean city PR AUC; simple impervious/land-cover baselines remain competitive. That should be stated in one clean topic sentence before the detailed numbers.

The Figure 5 paragraph is good but cautious. It should explain why the correlations matter in more intuitive language: cities that are easy when the model has seen that city are not necessarily easy when the model has never seen that city.

The spatial diagnostic paragraphs are important but should be elevated into a separate subsection. The Denver map and all-city spatial-alignment metric are too important to feel like add-ons.

The feature-importance paragraph is brief and probably underused. If feature importance remains only in the appendix, that is fine. But if the paper wants to argue that NDVI and imperviousness drive predictions, then Figure A2 should either be moved into the main figures or discussed more substantively.

The conclusion is accurate but buried. End with a short, memorable conclusion after the limitations and future work.

### 10. Highest-priority writing fixes

1. **Split “Analysis, Conclusion, and Discussion” into Results, Discussion, Limitations/Future Work, and Conclusion.** This is the single biggest structural improvement.
2. **Reduce repeated caveats.** Define scope once, then stop restating every limitation after every figure.
3. **Replace internal project language with reader-facing language.** Especially “support-checked,” “partner result support counts,” “retained model,” and “canonical” unless explicitly necessary.
4. **Define exact-cell retrieval, broader spatial placement, AP/PR AUC, and target-rate-stratified sampling earlier and more plainly.**
5. **Make the spatial diagnostic a coherent subsection, not an appendage.** It is now part of the intellectual contribution.
6. **Condense the research questions.** Five secondary questions are too many for a final report unless each maps directly to a subsection.
7. **Make the conclusion more confident.** The report should not oversell, but it should clearly claim its contribution.

---

## Section 2 - Figures and Tables Critique

### 1. Overall diagnosis

The figures and tables contain the right information, but the visual hierarchy is not yet aligned with the paper’s argument. Some of the most important evidence is in the appendix, while some main figures are either too small, too caption-heavy, or too visually underpowered. The paper’s visual story should be:

1. What cities and data are included?
2. How was the dataset built and evaluated?
3. What is the main performance contrast between within-city and city-held-out validation?
4. How heterogeneous is transfer across cities?
5. Does spatial alignment reveal broader structure despite weak exact-cell retrieval?

The current figure set contains all five pieces, but not in the best order or emphasis. In particular, the spatial-alignment figure and at least one city-level heterogeneity figure probably deserve main-text status.

### 2. Are figures and tables properly cited in the text?

Mostly, but not fully. Main figures are cited in the text, but appendix figures are sometimes doing important interpretive work without enough main-text integration.

Main text references are generally present:

- Figure 1 is cited when selected city locations are introduced.
- Table 2 is cited when final dataset summary by climate group is introduced.
- Table 1 is mentioned as the data source summary.
- Figure 2 is discussed after dataset construction.
- Figure 3 is cited in the city-held-out method paragraph.
- Figure 4 is used for within-city versus transfer results.
- Figure 5 is used for city-level signal shifts.
- Figure 6 is used for the Denver spatial diagnostic.

Appendix references are more uneven:

- Appendix Figure A1 is referenced to support row-count imbalance. Good.
- Appendix Figure A2 is mentioned for predictive interpretation diagnostics. Good, but the discussion is thin.
- Appendix Tables A5-A7 and Figures A4-A5 are referenced for heterogeneity. Good, but their importance may warrant moving one to the main text.
- Appendix Figure A7 is cited in the spatial-alignment discussion. Given that spatial alignment is now a major result, A7 should likely be a main figure.
- Appendix Figure A8 is cited as a selected high/low map contrast. It is visually important but currently awkwardly placed and split across pages.

The largest issue is not missing citations but mismatched importance. The reader hears a lot about heterogeneity and spatial alignment, but the strongest visual summaries of those claims are in the appendix. If page/space limits allow, promote selected appendix visuals.

### 3. Should any appendix figures or tables be moved to the main text?

Yes.

#### Promote Appendix Figure A7 to the main text

Appendix Figure A7 is central to the added spatial-placement diagnostic. The main text reports mean Spearman correlation, top-region overlap, and observed mass captured. A7 is the only figure that lets the reader see the city-level spread behind those numbers. Since the spatial diagnostic now changes the scope of the paper, A7 should not be hidden in the appendix.

Recommended change:

- Make A7 the new Figure 7 in the main text.
- Keep the Denver map as Figure 6 if you want a concrete example.
- Then use new Figure 7 to show the all-city generalization of that idea.

This would make the spatial diagnostic feel legitimate rather than tacked on.

#### Consider promoting Appendix Figure A5 or A4

The paper repeatedly argues that transfer performance is heterogeneous. Table 3 gives aggregate metrics, but aggregate metrics hide the city-to-city variation. Appendix Figure A5, absolute random-forest city PR AUC, communicates that heterogeneity more clearly than the text alone. Appendix Figure A4 shows RF-minus-logistic deltas and is useful for model comparison. Of these, A5 is probably more generally useful; A4 is more diagnostic.

Recommended option:

- Promote A5 as a main figure if the main claim is “transfer success varies sharply by city.”
- Keep A4 in the appendix if the main model-comparison story can be told through Table 3.

#### Keep Appendix Figure A1 in the appendix

A1 supports row-count imbalance but is not central enough for the main text. It is fine as an appendix figure.

#### Keep Appendix Figure A2 in the appendix unless interpretation becomes a larger claim

Feature importance is useful but not central unless the paper wants to argue about which predictors matter most. If moved to the main text, the paper needs a stronger interpretation paragraph. Otherwise it can remain supplemental.

#### Keep Appendix Tables A5-A7 in the appendix

These are useful audit tables, but they are not reader-friendly enough to be main tables. The main text can cite them for support.

### 4. Is there a clear missed opportunity for a figure?

Yes. The paper needs one cleaner “main result story” visual.

Figure 4 tries to compare within-city and city-held-out results side by side, but the two panels use different metrics and scales. The caption correctly warns against direct magnitude comparison, but that warning reveals the limitation of the figure. The figure is useful, but it is not an ideal main-result visualization because readers may still compare bar lengths and dot positions too literally.

A stronger main-result figure could be a conceptual + metric summary organized by validation question:

| Validation question | Data split | Metric | Best result | Interpretation |
|---|---|---|---|---|
| Same-city screening | held-out cells within represented cities | class-1 F1 | RF 0.448 | strong selective local signal |
| Exact-cell transfer | whole held-out cities, sampled rows | AP / R@10 | RF AP 0.149, R@10 0.196 | weak/modest transfer |
| Broad spatial placement | whole held-out cities, full rows, smoothed surfaces | Spearman / mass captured | mean 0.271 / 0.211 | partial and heterogeneous |

This could be a table or a schematic figure. It would prevent the reader from confusing the validation designs while making the paper’s contribution easier to understand.

Other missed visual opportunities:

- A simple flowchart of the three evaluation questions would be more useful than repeating the distinction in prose.
- A city-level heatmap with rows as cities and columns as within-city F1, transfer PR AUC, recall@top10, spatial Spearman, and mass captured could unify the heterogeneity story.
- A small calibration/distribution plot of predicted scores for hotspots versus non-hotspots could help explain why PR AUC is only modest even when maps look coherent.
- A visual of the top-decile label construction would help non-specialist readers understand `hotspot_10pct`.

### 5. Table-by-table critique

#### Table 1 - Data Sources and Constructed Variables

Table 1 is substantively useful but visually weak. It suffers from heavy text wrapping, narrow columns, and dense descriptions. It looks like a spreadsheet forced into a portrait page. Several cells contain long phrases broken across many lines, which makes the table tiring to read.

Problems:

- Column widths are poorly matched to content.
- Product names and constructed variables wrap awkwardly.
- The “Spatial role” column contains prose that may belong in notes rather than cells.
- The “Primary predictor?” column is useful, but the distinction between “No” because metadata, “No” because target ingredient, and “No” because support field is not visually clear.
- The table occupies multiple cognitive roles: source citation, variable dictionary, modeling feature flag, and preprocessing explanation.

Recommended fix:

- Split into two tables or simplify.
- Main text table should include: Source, Product, Constructed variable, Modeling role.
- Move detailed spatial role descriptions to the dataset construction prose or Appendix Table A1.
- Use shorter modeling-role labels: “Predictor,” “Target source,” “Quality filter,” “Metadata,” “Geometry/grid.”

Example row style:

| Source | Product | Variable(s) | Role |
|---|---|---|---|
| NLCD | 2021 land cover | `land_cover_class` | predictor; open-water filter |
| ECOSTRESS | ECO_L2T_LSTE, May-Aug 2023 | `lst_median_may_aug`, `hotspot_10pct` | target source |

This would be much easier to read.

#### Table 2 - Final Dataset Summary by Climate Group

Table 2 is useful and belongs in the main text. It cleanly supports the dataset description and climate-group balance. However, the table could be improved visually.

Problems:

- “Hotspot prev.” is identical across groups and may not need four decimals unless tied to the top-decile construction.
- “Median valid passes” is useful but not explained enough in the table note.
- The row-count columns are valuable but could be labeled more explicitly as cells/rows in final analytic dataset.

Recommended fix:

- Add a note: “Rows are eligible 30 m analytic grid cells after open-water and ECOSTRESS quality filters.”
- Consider adding total row count across all groups in a final row.
- Keep this as a main table.

#### Table 3 - Main City-Held-Out Benchmark Metrics

Table 3 is one of the most important tables and should remain in the main text. It is clear enough, but it would benefit from stronger visual hierarchy.

Problems:

- The model names wrap awkwardly.
- The table mixes baselines, matched models, and higher-sample context. That is acceptable but could be visually grouped.
- Runtime is useful but may distract from performance metrics unless runtime is part of the paper’s argument.
- The note is too long and does some interpretation that should also appear in the results prose.

Recommended fix:

- Add grouping rows: “References,” “Simple baselines,” “Learned models.”
- Bold or otherwise mark the primary matched comparison rows: Logistic SAGA 5k and Random forest 5k.
- Rename “Rows/city” to “Sample used for benchmark.”
- Consider moving runtime to Appendix Table A2 unless computational cost is part of the main story.
- Keep the note about 0.1000 no-skill reference; it is essential.

#### Appendix Table A1 - Final Dataset Columns

This table is useful but visually cumbersome. It spans multiple pages and contains many wrapped cells. It is acceptable in the appendix, but it should not be expected to carry important main-text explanation. The main text should define the six predictors and target clearly enough that the reader does not need A1.

Recommended fix:

- Use landscape orientation or reduce prose in cells.
- Group variables by role: metadata, primary predictors, target/quality fields, supplemental features.
- Use code formatting consistently for variable names.

#### Appendix Table A2 - Model Run Metadata

This table is useful but underformatted. It should remain in the appendix. The explanatory text below it is good but could be converted into table notes.

Potential issue: The logistic run has 400 inner fits and RF has 120 inner fits, but the relationship between candidates, folds, and outer folds may not be obvious. A short note explaining the multiplication would help.

#### Appendix Table A3 - Model and Baseline Specifications

This is important for reproducibility but too dense. It should remain appendix material. The table is hard to read because cells contain paragraph-like text. A landscape layout would help significantly.

Recommended fix:

- Use shorter entries.
- Put detailed tuning grids in separate rows or footnotes.
- Make “Grouped CV?” clearer: for baselines, “outer folds only” is not the same kind of grouped CV as model tuning.

#### Appendix Table A4 - City and Fold Composition

This table is useful and probably necessary. It is acceptable as appendix material. It gives city IDs, rows, hotspot counts, prevalence, and fold assignment. The table is dense but readable enough.

Potential improvement:

- Sort by climate group then city, as currently done, is fine.
- Consider adding a fold-balance note: each fold has six cities.

#### Appendix Tables A5-A7 - RF Minus Logistic Performance

These tables support the heterogeneity claim. They are appropriate as appendices. A5 is interpretable; A6 and A7 are more audit-like.

Problems:

- A5 is useful but the “wins” framing can overemphasize counts over magnitude.
- A6 has many columns and is hard to scan.
- A7 is compact and useful but abstract.

Recommended fix:

- Keep them, but use one visual in the main text to communicate heterogeneity.
- In the table captions, explicitly state that these are paired comparisons under the matched 5k benchmark.

### 6. Figure-by-figure critique

#### Figure 1 - Study City Locations

The figure is useful but visually underwhelming. It establishes geographic coverage, but the city labels are too small and some are difficult to read. The map has a lot of empty space, and the points do not strongly communicate the climate-group balance.

Problems:

- Labels are tiny.
- Some labels are hard to distinguish from the grid/background.
- The legend is small.
- The color palette is acceptable but not especially strong.
- It is not obvious that there are exactly 10 cities per climate group unless the caption/text says so.

Recommended fix:

- Increase figure size or label font.
- Use direct labels only for cities if they remain legible; otherwise number cities and refer to a table.
- Consider using a simple U.S. basemap or state outlines. A longitude-latitude scatterplot is functional but looks less polished.
- Add a subtitle or note: “10 cities per climate group.”

Caption critique: The caption is concise and mostly good. It could be more informative by saying what the colors encode and that the set is purposive, not representative.

#### Figure 2 - Dataset Construction Workflow

This figure is conceptually helpful and belongs in the main text. It shows the pipeline from study design to modeling/delivery. However, the text inside boxes is too small in the rendered PDF, and the workflow is too compressed horizontally.

Problems:

- Box text is difficult to read.
- The figure contains many small labels that duplicate the caption.
- The visual design is clean but low-impact.
- The reader may not understand which steps are per-city and which steps are combined across cities.

Recommended fix:

- Make the figure larger or use a vertical workflow.
- Increase font size substantially.
- Reduce each box to a short label and move details to caption or methods.
- Use one visual cue to distinguish source data, processing steps, and outputs.

Caption critique: The caption is too long and packed with product names. It should explain the workflow in conceptual terms, not repeat every source. Product details already appear in Table 1.

#### Figure 3 - City-Held-Out Evaluation Design

This is one of the better conceptual figures. It makes the city-held-out fold design concrete. However, like Figure 2, the text is small and some internal labels are hard to read.

Problems:

- Font size is too small.
- The visual hierarchy could better emphasize “held-out cities never enter preprocessing/tuning.”
- The diagram uses red squares to represent held-out cities, but the legend/meaning could be clearer.
- The bottom text is small.

Recommended fix:

- Enlarge the fold strip and label “held out” clearly.
- Use fewer words in boxes.
- Add a single bold note: “No city appears in both training and testing.”

Caption critique: The caption is clear and appropriately short. It could mention that inner CV is also grouped by city if that is central to leakage control.

#### Figure 4 - Within-City and City-Held-Out Results Side by Side

Figure 4 is important but risky. It is visually clear in the sense that the bars/dots are readable, but conceptually it invites comparison across panels that the caption then tells the reader not to make. The left panel uses precision/recall/F1; the right panel uses PR AUC, mean city PR AUC, and recall@top10. These are related but not directly comparable.

Problems:

- The two-panel layout implies a direct comparison of magnitudes even though the metrics differ.
- The caption is very long because it has to prevent misinterpretation.
- The right-panel x-axis range is narrow, which visually exaggerates small differences.
- The no-skill 0.10 reference is not shown directly in the right panel, even though the caption discusses it.
- The sanity-check paragraph about flipped labels/probabilities is too internal for a figure caption.

Recommended fix:

- Keep the figure but retitle it more explicitly: “Validation Design Changes the Apparent Model Advantage.”
- Add a vertical reference line at 0.10 in the right panel.
- Avoid placing within-city thresholded metrics and transfer ranking metrics as if they are one metric family. Consider two separate figures or a table-like panel.
- Move the flipped-score sanity check to a footnote, appendix, or reproducibility note. It clutters the caption.

Caption critique: The first paragraph is helpful. The second paragraph is too long and too defensive. Most readers do not need inverted-score AP and ROC AUC in the main caption unless there was a known concern about flipped predictions.

#### Figure 5 - City-Level Signal Shifts Across Evaluation Designs

Figure 5 is conceptually important but visually crowded. It tries to show that within-city success does not predict transfer success. That is a strong point. However, every city is labeled, labels are small, and some overlap or crowding reduces readability.

Problems:

- City labels are too small.
- Some labels are hard to read or close to points.
- The two panels are useful but visually dense.
- The meaning of “signal shifts” is not immediately intuitive.
- Pearson correlations are shown, but the figure would benefit from a faint trend line or visual annotation explaining “near zero relationship.”

Recommended fix:

- Label only selected cities: strongest, weakest, and notable outliers. Put full labels in appendix or interactive source.
- Use larger points and larger axis labels.
- Add a regression line or smooth line only if it helps; otherwise annotate “near-zero correlation.”
- Rename panels with plainer language:
  - “Same-city F1 vs transfer AP”
  - “Same-city recall vs transfer recall@10%”
- Consider moving this figure after Table 3 and before the spatial diagnostic.

Caption critique: The caption is good but could be more direct. “Signal shifts” is abstract. Say: “Cities that are easy under same-city validation are not necessarily easy under city-held-out transfer.”

#### Figure 6 - Held-Out Denver Map Example

This figure is important because it visually motivates spatial alignment. The idea is strong. The execution is only partly successful.

Problems:

- The maps are small, so spatial patterns are difficult to inspect.
- The color legend is small.
- The title “Error Pattern” is useful, but the meaning of colors requires careful reading.
- The gray background/other cells are faint; that may be intentional, but it reduces interpretability.
- Denver is only one city, and the caption correctly warns not to generalize. However, the map may feel anecdotal unless immediately followed by the all-city spatial summary.

Recommended fix:

- Make Figure 6 larger, perhaps full-width with fewer panels or one larger error map.
- Add a small note explaining red/blue/green categories directly in the panel or legend.
- If space is limited, use only observed hotspots and error pattern; predicted top-decile cells may be redundant.
- Follow immediately with the all-city spatial summary as the next main figure.

Caption critique: The caption is accurate but long. It states the interpretive point clearly: errors are clustered, and the single city motivates the all-city diagnostic. Good. It could be tightened.

#### Appendix Figure A1 - Final Dataset Row Counts by City and Climate Group

This figure is clear and useful. The horizontal bar chart is appropriate. It effectively shows that city row counts vary substantially.

Problems:

- The legend is small but readable.
- The caption is too minimal; it should remind the reader that row counts differ because buffered urban-area extents differ.
- It might be helpful to mark climate groups more directly with grouping separators.

Recommended fix:

- Keep in appendix.
- Consider adding group labels or facets by climate group.

#### Appendix Figure A2 - Supplemental Feature-Importance Summary

This figure contains useful model interpretation diagnostics, but it is visually crowded. The logistic coefficient panel in particular is hard to interpret because encoded land-cover categories are not self-explanatory.

Problems:

- Logistic coefficient labels are small and internal.
- Land-cover encoded levels are difficult for readers to interpret unless they know NLCD codes.
- The two panels use very different interpretive units: coefficients versus permutation importance. Side-by-side placement may imply comparability that is not valid.
- The caption correctly says predictive, not causal, but does not explain what the reader should take away.

Recommended fix:

- If kept, add a short interpretive title: “RF importance emphasizes NDVI and imperviousness.”
- Translate land-cover codes into plain labels where possible.
- Avoid overemphasizing logistic coefficients unless the reference category is clearly stated.
- Keep appendix unless the paper adds a stronger feature-interpretation discussion.

Caption critique: Good caution, but too thin. It says what not to infer but not what to infer.

#### Appendix Figure A3 - City-Held-Out Benchmark Metric Comparison

This figure is redundant with Table 3 and Figure 4. It may be useful as a visual companion, but it is not essential.

Problems:

- X-axis labels are angled and small.
- Bars are difficult to compare precisely.
- The figure duplicates Table 3 without adding much new insight.
- If retained, it should have a clearer purpose: showing baselines versus models visually.

Recommended fix:

- Either improve and promote as the main benchmark visual, or remove from appendix if Table 3 and Figure 4 already carry the story.
- If improved, group bars by model family and use a consistent 0.10 reference line.

Caption critique: Adequate but generic. It should state the main takeaway: learned models only modestly exceed simple baselines under transfer.

#### Appendix Figure A4 - City-Level RF Minus Logistic Deltas

This figure is useful and potentially main-text worthy if the model-comparison heterogeneity matters. It clearly shows that RF does not dominate uniformly.

Problems:

- City labels are small.
- Two side-by-side horizontal bar charts are a good choice, but the figure is cramped.
- The x-axis label “RF - Logistic” could be more explicit about positive values favoring RF.
- Climate colors are useful but may distract from positive/negative direction.

Recommended fix:

- Increase width or split into two separate figures.
- Add a vertical zero line, if not already visually obvious.
- Consider sorting cities consistently across both panels to show whether PR AUC and recall gains align.

Caption critique: The caption is clear but minimal. It should say positive values favor RF.

#### Appendix Figure A5 - Absolute Random-Forest City PR AUC

This is one of the clearest and most useful appendix figures. It directly shows heterogeneity in transfer performance across cities. It should be considered for the main text.

Problems:

- Legend is a bit small.
- The dashed 0.10 reference is useful.
- It only shows random forest, so it does not convey model comparison. But it conveys city heterogeneity very well.

Recommended fix:

- Promote to main text if space allows.
- Add a note that all values are held-out city AP/PR AUC under the matched 5k RF run.
- Consider grouping or coloring by climate but sorting by PR AUC as currently done is effective.

Caption critique: Good. It clearly explains the dashed reference.

#### Appendix Figure A6 - Supplemental Within-City Versus Cross-City Gap

This figure makes an important point: within-city performance is much easier. However, it is cognitively less immediate than Figure 4 or Figure 5.

Problems:

- The y-axis “Within-city F1 minus transfer city PR AUC” mixes unlike metrics, which is hard to interpret.
- The caption warns that it is not an alternative benchmark, but the metric construction still invites confusion.
- It may be better as an exploratory appendix figure than a core result.

Recommended fix:

- Keep appendix only.
- Consider replacing with a simpler conceptual statement or standardized-rank comparison if the goal is to show a gap.

Caption critique: The caution is necessary but again signals that the figure may be conceptually risky.

#### Appendix Figure A7 - Medium-Scale All-City Spatial-Alignment Summary

This figure is important and should likely be promoted. It communicates the all-city spatial diagnostic far better than the text alone.

Problems:

- The main title is strong.
- The axes are clear.
- The mean reference lines are useful.
- Marker-size legend is conceptually useful but visually subtle.
- Only three cities are labeled; that is okay, but the caption mentions several high/low cities in the text, not all visible in the figure.
- The figure is placed in the appendix even though the spatial diagnostic is central.

Recommended fix:

- Promote to main text as Figure 7.
- Label the top few and bottom few cities or use a cleaner labeling strategy.
- Clarify top-region overlap in the caption. A reader may not know what “top-region” means without going back to methods.
- Consider adding a short panel note: “Higher right/up = stronger broad spatial alignment.”

Caption critique: Mostly good. It explains that color should not be interpreted as stable climate-group evidence. However, the phrase “observed hotspot mass captured” needs a plainer parenthetical explanation.

#### Appendix Figure A8 - Selected High/Low Spatial-Alignment Map Contrast

This figure has major layout problems. It is split across pages, with the Nashville row on one page and the San Francisco row on the next. The title appears before the Nashville row, but the explanatory caption appears after the San Francisco row. This makes the figure difficult to read and visually unprofessional.

Problems:

- The figure is split across pages.
- Individual map panels are too small.
- Some panels are nearly blank or extremely faint, which may be meaningful but looks like missing data unless explained.
- The color legend is tiny.
- The reader has to infer that Nashville is the high-alignment example and San Francisco is the low-alignment example.
- The caption says high/low contrast but does not explicitly state which is high and which is low.

Recommended fix:

- Do not split this figure across pages.
- Either make it a full-page landscape figure or reduce to two or three panels per city.
- Add city-level metric values directly in the figure title: “Nashville: Spearman = X, mass captured = Y” and “San Francisco: Spearman = X, mass captured = Y.”
- Use stronger color scaling or explain blank/faint panels.
- If the full 5-panel map set is too large, show only observed smoothed surface, predicted smoothed surface, and top-region overlap.

Caption critique: The caption is directionally good but too cautious and not specific enough. It says the maps are not operational evidence, but it does not clearly tell the reader what visual contrast to notice.

### 7. Caption and small-description critique

The captions are generally accurate but too often function as defensive mini-method sections. Captions should help the reader interpret the visual quickly. Several captions instead spend much of their space preventing overinterpretation.

Common caption issues:

- Too much internal language: “support-checked,” “retained-prediction sanity check,” “retained random-forest full-city prediction surfaces.”
- Too many caveats in the caption rather than in the main text.
- Not enough “what to notice” language.
- Some captions define what a figure is not, but not what it shows.

Recommended caption pattern:

1. First sentence: what the figure shows.
2. Second sentence: what the reader should notice.
3. Optional third sentence: one key limitation or scope condition.

For example, Figure 4 could become:

> “Figure 4 compares model performance under same-city held-out evaluation and city-held-out transfer. Random forest has a large advantage over logistic regression in the same-city diagnostic, but the transfer benchmark is much closer and only modestly above simple baselines. Because the panels use different metrics, the figure should be read as a validation-design contrast rather than a direct scale comparison.”

That is shorter, clearer, and still cautious.

Figure A7 could become:

> “Figure 7 summarizes broad spatial alignment for the full-city random-forest predictions at 300 m smoothing. Cities in the upper-right have stronger agreement between predicted high-risk surfaces and observed hotspot concentration, while lower-left cities show weak alignment. Point size represents overlap between the predicted and observed top smoothed regions.”

This tells the reader how to read the figure.

### 8. Visual design and layout issues across the document

The paper has several layout problems beyond individual figures.

#### Figures and tables are separated from the main text

All figures and tables are placed after the references rather than interleaved. That is sometimes required by formatting rules, but it weakens readability. The reader has to flip back and forth between text and visuals. If allowed, place key figures and tables near first mention. At minimum, ensure the results text names the exact table/figure and summarizes its takeaway.

#### Some figures are too small for the page

Figures 1, 2, 3, 5, 6, A2, A3, A4, and A8 all suffer from small labels or cramped visual elements. The issue is not just aesthetics; it prevents the reader from extracting the intended message.

#### Multi-panel figures need larger labels and simpler captions

Several multi-panel figures try to do too much. Figure 4, Figure 5, Figure 6, A2, A3, A4, and A8 all rely on small text and caption explanation. The revision should either enlarge them or reduce panel complexity.

#### Color use is mostly functional but not always communicative

The color palette consistently distinguishes climate groups in many figures. That is good. However, climate color appears even when climate group is not the main point. This can lead readers to search for climate-group conclusions that the paper explicitly says are not stable. Use climate colors only when climate group matters. For model comparisons, use model colors. For error maps, use error-category colors. For spatial alignment, climate color is acceptable but should be visually secondary.

#### Some captions and notes are too close to body prose

The rendered PDF often shows large blocks of caption text below figures. Figure 4 especially has a caption that feels like a paragraph of results. This hurts visual rhythm. Captions should be shorter, and detailed caveats should move to the main text or appendix notes.

#### Reproducibility notes overflow visually

On the reproducibility page, the command path is too long and appears to run across the page. This is a layout issue. Use a smaller monospace font, line breaks, or a code block environment that wraps cleanly. The reproducibility section is valuable, but the current layout looks unpolished.

### 9. Recommended final figure/table set

If the paper can include a limited number of main visuals, I recommend this main set:

1. **Table 1:** Simplified data sources and variable roles.
2. **Table 2:** Final dataset summary by climate group.
3. **Figure 1:** Study city map, improved labels or basemap.
4. **Figure 2:** Dataset workflow, enlarged and simplified.
5. **Figure 3:** City-held-out validation design, enlarged and simplified.
6. **Table 3:** Main city-held-out benchmark metrics, visually grouped.
7. **Figure 4:** Main validation contrast, revised to reduce metric confusion.
8. **Figure 5:** City-level within-city versus transfer relationship, with fewer labels or clearer annotation.
9. **Figure 6:** Denver spatial error map, enlarged.
10. **Figure 7:** Promoted spatial-alignment all-city summary, formerly Appendix Figure A7.

Optional main figure if space allows:

- **Absolute RF city PR AUC**, formerly Appendix Figure A5, because it communicates heterogeneity more clearly than several paragraphs.

Appendix should contain:

- Final dataset columns.
- Model metadata.
- Model/baseline specifications.
- City/fold composition.
- RF-minus-logistic detailed tables.
- Feature importance.
- Full heterogeneity diagnostics.
- High/low spatial map contrast, but only if fixed so it does not split across pages.

### 10. Highest-priority figure/table fixes

1. **Promote Appendix Figure A7 to the main text.** It is central to the spatial-alignment addition.
2. **Fix Appendix Figure A8 or remove it.** A split high/low map contrast is not acceptable in final form.
3. **Simplify Table 1.** It currently reads like a compressed spreadsheet, not a polished report table.
4. **Revise Figure 4 to reduce metric confusion.** Add the 0.10 reference and shorten the caption.
5. **Increase font sizes across figures.** Many visuals are technically readable only with effort.
6. **Use captions to say what to notice, not just what not to overinterpret.**
7. **Consider promoting Appendix Figure A5.** The heterogeneity story needs a stronger main-text visual.
8. **Move flipped-label/probability sanity-check details out of the Figure 4 caption.** It is too internal for the main visual narrative.
9. **Clean up reproducibility-note wrapping.** Long paths should not overflow the page.
10. **Make climate-group color meaningful rather than default.** Use it only where climate-group interpretation is actually relevant.

---

## Bottom-line revision advice

The draft is strongest when it argues that validation design changes the apparent success of urban heat hotspot models. It is weakest when it sounds like a cautious project audit instead of a confident final report. The technical story does not need to be softened; it needs to be clarified.

The final paper should make three claims with discipline:

1. **Same-city hotspot screening works reasonably well with simple public geospatial predictors, especially for random forest.**
2. **City-held-out exact-cell transfer is much harder, only modestly above simple baselines, and highly heterogeneous across cities.**
3. **Full-city spatial diagnostics suggest partial broad-scale alignment in some cities, but this does not yet establish reliable operational hotspot mapping.**

Everything in the writing, tables, figures, captions, limitations, and future work should serve those three claims. Anything that does not serve them should be shortened, moved to the appendix, or deleted.
