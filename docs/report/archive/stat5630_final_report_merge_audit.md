# STAT5630 Final Report Merge Report And Structural Audit

Date: May 3, 2026

Canonical draft audited: `docs/report/stat5630_final_report_draft.md`

Reference draft compared: `docs/report/Report Draft Text Only.md`

Operating guide: `docs/report/codex_paper_writing_plan.md`

Spatial-alignment evidence checked: `outputs/modeling/supplemental/spatial_alignment_all_cities/`

## Task 1 Merge Report

### Sections Updated

| Section | Update |
| --- | --- |
| 1. Background Information | Added a compact model-comparison rationale from the text-only draft, scoped to logistic regression as the linear benchmark and random forest as the nonlinear benchmark. |
| 3. Dataset Construction | Added the text-only draft's prevalence nuance that the hotspot rate is approximately, not exactly, 10% because rare LST threshold ties can occur. |
| 4. Model and Method | Added the text-only draft's climate-group interpretation note, clarified pass count as a construction support variable, and added a restrained future-work note about location-aware/spatial-context features. |
| 4. Model and Method | Added the text-only draft's computational-limit sampling rationale, while keeping the current sampled-benchmark language. |
| 5. Analysis, Conclusion, and Discussion | Added the text-only draft's high-precision/low-recall interpretation for within-city random forest, phrased as selective hotspot retrieval rather than complete hotspot recovery. |
| 5. Analysis, Conclusion, and Discussion | Added a scope-controlled version of the partner-entered Figure 5 observation about relative city positions and Nashville, explicitly treating it as hypothesis-generating. |

### Text Incorporated From The Edited Draft

- Model comparison rationale: logistic regression is the linear benchmark; random forest is the nonlinear benchmark; PR-oriented metrics are more appropriate than accuracy for the city-held-out imbalanced hotspot task.
- Dataset prevalence nuance: 7,139,588 positives among 71,394,894 rows is approximately 10%, not exactly 10%, because rare ties can occur around city-specific LST thresholds.
- Feature-scope rationale: climate group supports later interpretation; LST and pass count are excluded because they define or support the label rather than portable surface-characteristic prediction.
- Future-work bridge: location-aware or spatial-context features are a logical next step, but outside the primary six-predictor benchmark.
- Sampling rationale: computational constraints motivated the 5,000-row-per-city sampled benchmark; the larger logistic run is useful context but does not make full-city scoring equivalent to the sampled benchmark.
- Within-city interpretation: random forest's higher precision and lower recall imply a selective retrieval pattern.
- Figure 5 interpretation: visible relative-city patterns and Nashville's strong position are useful diagnostics but should not be overread against the weak cross-design correlations.

### Remaining Placeholders

| Location | Placeholder | Status |
| --- | --- | --- |
| Background Information | `[Insert additional related-work context here: connect urban heat, spatial validation, and transfer learning literature to the report's two-design evaluation question.]` | Still real missing work. Fill before line editing. |
| Model and Method | `[Insert within-city held-out methods detail here: describe the verified 70/30 split, thresholding procedure, and class-1 precision, recall, and F1 interpretation for same-city hotspot screening.]` | Still real missing work. Needs exact method details and evidence source. |
| Analysis, Conclusion, and Discussion | `[Insert signal-shift analysis here: expand the Figure 5 interpretation by comparing city-level within-city random-forest F1/recall against city-held-out random-forest PR AUC/recall@top10 and explaining why same-city learnability does not imply cross-city transferability.]` | Still real missing work. Needs Figure 5 and metric-driven interpretation. |

### Ambiguous Conflicts

| Conflict | Resolution |
| --- | --- |
| Text-only draft says PR AUC was used because most data were not hotspots. | Merged as city-held-out precision-recall emphasis. The repo draft correctly notes that within-city results use precision, recall, and F1 rather than PR AUC as the main summary. |
| Text-only draft implies climate-group separation means a model fit in one group would not be suitable for another. | Not incorporated as a conclusion. Reframed as hypothesis-generating because the current evidence supports heterogeneity, not a definitive climate-transfer rule. |
| Text-only draft says Nashville appears better with "city held out data" in Figure 5. | Incorporated only as a visible diagnostic pattern, not as a standalone performance conclusion. |
| Text-only draft uses more first-person language. | Repo draft keeps the more canonical report voice. No broad prose rewrite was performed. |

### Repetitive Or Structurally Weak Areas

- Section 5 currently combines analysis, conclusion, discussion, limitations, and future work. It is doing too many jobs and should probably be split before final polishing.
- The related-work bridge is visibly missing, which weakens the introduction's transition from urban heat mapping to transfer validation.
- The within-city methods placeholder leaves the Figure 4 results under-specified.
- The signal-shift placeholder creates repetition around Figure 5 because the draft already interprets the low correlations before the placeholder.
- Tables and figures are clear, but the main text sometimes references them as evidence before giving the exact takeaway the reader should retain.

## Task 2 Structural Audit

### Current Center Of Gravity

The paper's current center of gravity is still the original benchmark framing: a reproducible 30-city urban heat hotspot dataset and a validation-design comparison showing that same-city hotspot screening is much easier than city-held-out transfer. The spatial-alignment all-city diagnostic is complete and useful, but its metrics are heterogeneous and modest enough that it should qualify the transfer story rather than reframe it.

### Section-By-Section Audit

| Section | Current purpose | Evidence supporting it | What is missing | Action |
| --- | --- | --- | --- | --- |
| Introduction / motivation | Establish urban heat as a fine-scale screening problem and introduce surface-temperature prediction. | LST definition, ECOSTRESS role, 30-city benchmark contribution. | Stronger bridge from local heat mapping to transfer learning. | Revise after placeholder fill. |
| Literature / validation framing | Justify spatial/city-group validation rather than row splits. | Voogt and Oke, Weng et al., Yuan and Bauer, Stewart and Oke, Roberts et al., Meyer et al. | More explicit synthesis connecting these literatures to the two-design evaluation. | Expand. |
| Dataset construction | Explain city selection, study areas, 30 m grid, source layers, and final assembly. | Table 1, Figure 2, final dataset audit counts, missingness values. | None fatal; the "30 m analytic grid" caveat is already present. | Keep, light tighten later. |
| Target definition | Define `hotspot_10pct` as city-relative top-decile May-August ECOSTRESS LST. | Dataset construction text, Table A1, final audit counts. | Could more explicitly state tie handling if known from code. | Keep, verify tie logic if final wording gets more precise. |
| Feature specification | State safe six-predictor benchmark and excluded leakage/location variables. | Model and Method section, Table 1, Table A3, feature contract metadata. | Clarify status of neighborhood-context variables if they appear in final dataset but not benchmark. | Keep, minor clarification later. |
| Validation design | Separate within-city held-out evaluation from city-held-out transfer. | Figure 3, fold structure, grouped preprocessing/tuning language. | Within-city 70/30 methods detail remains placeholder. | Expand before prose edit. |
| Models / baselines | Define baselines, logistic SAGA, random forest, and why nonlinear comparison matters. | Table 3, Table A2, Table A3, run metadata. | More concise model hyperparameter search details may be needed if not fully covered in appendix. | Keep, verify appendix completeness. |
| Metrics | Explain PR AUC, mean city PR AUC, recall@top10, and within-city precision/recall/F1. | Table 3, Figure 4, benchmark metrics. | Need avoid mixing within-city and transfer metrics as a single leaderboard. | Keep, sharpen in final edit. |
| Sampling design | Explain 5k-per-city benchmark and 20k logistic context. | Table 3, Table A2, run metadata, sample diagnostics. | More explicit limitation that sampled benchmark is not full-city operational scoring. | Keep, already improved. |
| Within-city results | Show RF strongly outperforms logistic when cities are represented in training. | Figure 4, mean precision/recall/F1 values. | Methods detail for split and thresholding. | Expand methods first, then polish results. |
| City-held-out results | Show transfer is weaker, models are close, and simple built-intensity baseline captures much signal. | Table 3, recall@top10, pooled and mean city PR AUC. | Ensure all values match retained run tables. | Keep, verify numeric consistency. |
| City heterogeneity / signal shift | Show same-city learnability does not reliably predict transfer. | Figure 5, correlations 0.08 and 0.03, Tables 4-6, Appendix Figures A4-A5. | Placeholder asks for fuller Figure 5 interpretation. | Expand. |
| Spatial diagnostics / spatial alignment | Current draft has Denver map only; new all-city spatial alignment is not yet integrated. | Figure 6, spatial-alignment all-city output: 30 cities, 3 smoothing scales, all grid statuses ok. | Decide placement and whether to add a compact supplemental subsection or appendix table/figure. | Add compact supplemental diagnostic if time permits. |
| Limitations | Bound leakage, sampling, construct, external-validity, and metric-comparison claims. | Existing limitations paragraph and run scope. | Add spatial-alignment scope if integrated. | Revise after spatial decision. |
| Future work | Extend full-city scoring, uncertainty, neighborhood context, spatial/hierarchical models, exposure outcomes. | Existing future-work paragraph. | If spatial alignment remains supplemental, mention as diagnostic extension only if not already integrated. | Revise after spatial decision. |
| Conclusion | Restate dataset contribution and validation-design contrast. | Main results in Figures 4-5 and Table 3. | Needs to reflect any spatial-alignment diagnostic without changing main benchmark claim. | Revise last. |

### Visible Placeholders And Structural Gaps Before Wording Edits

| Gap | Why it matters | Fix before line editing? |
| --- | --- | --- |
| Related-work placeholder | A reader can see the literature bridge is unfinished. | Yes |
| Within-city methods placeholder | Figure 4 results need enough methods detail to be defensible. | Yes |
| Signal-shift placeholder | Figure 5 interpretation is partly duplicated and partly incomplete. | Yes |
| Combined Section 5 | Results, discussion, limitations, future work, and conclusion are compressed into one section. | Yes, at least add internal structure. |
| Spatial alignment not yet located | The all-city diagnostic exists but has not been assigned a paper role. | Yes, decide role before final revision. |

### Claims Ledger

| Major claim | Support | Current strength |
| --- | --- | --- |
| The project builds a reproducible 30-city, 30 m analytic-grid dataset. | Final dataset audit, Table 1, Table 2, Figure 2, Table A1. | Strong. |
| The target is surface hotspot screening, not direct human heat exposure. | ECOSTRESS LST target definition and literature/remote-sensing discussion. | Strong. |
| The 30 m label refers to the analytic grid, not native resolution of every source. | Dataset construction caveat, Table 1 source resolution roles. | Strong. |
| City-held-out evaluation is more leakage-safe than row/cell splits for transfer. | Figure 3, grouped fold method, Roberts et al. and Meyer et al. | Strong if methods text remains explicit. |
| Within-city RF outperforms logistic on hotspot precision, recall, and F1. | Figure 4, means: RF precision 0.7310, recall 0.3433, F1 0.4480; logistic precision 0.3887, recall 0.0727, F1 0.1083. | Strong, pending within-city methods fill. |
| City-held-out transfer is weaker and models are closer. | Table 3: RF 5k pooled PR AUC 0.1486, logistic 5k 0.1421, prevalence 0.1000. | Strong for sampled benchmark. |
| RF improves recall@top10 over logistic in the matched 5k benchmark. | Table 3: RF 0.1961 vs logistic 0.1647. | Strong for sampled benchmark. |
| Simple built-intensity information captures much of the transferable signal. | Table 3: impervious-only recall@top10 0.1860, close to RF 0.1961; land-cover PR AUC 0.1353. | Moderate to strong. |
| Same-city learnability does not imply cross-city transferability. | Figure 5 correlations: F1 vs PR AUC 0.08; recall vs recall@top10 0.03. | Strong as diagnostic association. |
| Transfer heterogeneity differs by fold and climate group. | Tables 4-6, Appendix Figures A4-A5. | Moderate; should remain hypothesis-generating. |
| Denver map suggests clustered transfer errors. | Figure 6. | Illustrative only, not all-city proof. |
| Spatial alignment shows some broad placement signal but is heterogeneous. | All-city spatial-alignment metrics: 30 cities, all statuses ok, medium mean Spearman 0.2713, range -0.0778 to 0.7476; medium mean top-region overlap 0.1353, range 0.0210 to 0.4202. | Moderate supplemental diagnostic. |

### Figure And Table Audit

| Item | Status | Main takeaway | Action |
| --- | --- | --- | --- |
| Table 1. Data Sources and Constructed Variables | Present. | Defines sources and predictor/target roles. | Keep. |
| Table 2. Final Dataset Summary by Climate Group | Present. | Shows balanced climate groups and near-10% prevalence. | Keep. |
| Table 3. Main City-Held-Out Benchmark Metrics | Present. | RF 5k modestly leads pooled PR AUC and recall@top10, but gains are small. | Keep as main results table. |
| Table 4. RF Minus Logistic Performance by Climate Group | Present. | RF gains concentrate in hot arid group. | Keep, maybe appendix if space is tight. |
| Table 5. Fold-Level RF Minus Logistic Comparison | Present. | RF gains are fold-dependent. | Keep or move to appendix if main text tightens. |
| Table 6. City-Level Paired RF Minus Logistic Summary | Present. | Logistic wins most city-level PR AUC comparisons despite RF pooled gains. | Keep or move to appendix with text reference. |
| Figure 1. Study City Locations | Present and referenced. | Shows geographic and climate-group spread. | Keep. |
| Figure 2. Dataset Construction Workflow | Present and referenced. | Establishes reproducible pipeline. | Keep. |
| Figure 3. City-Held-Out Evaluation Design | Present and referenced. | Visualizes leakage-safe held-out-city design. | Keep. |
| Figure 4. Within-City and City-Held-Out Results Side by Side | Present and referenced. | Shows validation-design gap and RF within-city advantage. | Keep as central figure. |
| Figure 5. City-Level Signal Shifts Across Evaluation Designs | Present and referenced. | Shows weak cross-design association. | Keep, but fill placeholder and consider using labeled version if readability is better. |
| Figure 6. Held-Out Denver Map Example | Present and referenced. | Illustrates clustered spatial errors in one held-out city. | Keep as diagnostic example, not proof of all-city placement. |
| Appendix Figure A1. Row Counts | Present. | Supports uneven city sizes. | Keep appendix. |
| Appendix Figure A2. Feature Importance | Present. | Predictive interpretation only. | Keep appendix with causal caveat. |
| Appendix Figure A3. Benchmark Metric Comparison | Present. | Visual support for Table 3. | Keep appendix unless redundancy becomes an issue. |
| Appendix Figure A4. RF Minus Logistic Deltas | Present. | City heterogeneity. | Keep appendix. |
| Appendix Figure A5. Absolute RF City PR AUC | Present. | City-level spread in RF transfer. | Keep appendix. |
| Spatial-alignment maps | Generated for Portland, Las Vegas, San Francisco, and Nashville only. | Supplemental placement examples. | Do not add as main figure unless a compact supplemental diagnostic is added. |
| Spatial-alignment metrics table | Generated for all 30 cities and three scales. | Heterogeneous broad placement signal. | Use only as supplemental evidence or appendix table. |

### Spatial Alignment Recommendation

Recommended role: **supplemental diagnostic**.

Reasoning:

- Completeness is good: 90 metric rows cover 30 cities and three smoothing scales, and all grid reconstruction statuses are `ok`.
- Signal is not consistently strong enough to reframe the paper. At the medium 300 m scale, mean Spearman surface correlation is 0.2713 and median is 0.2481, with a wide range from -0.0778 to 0.7476. Mean top-region overlap is 0.1353, only modestly above the 0.10 threshold fraction in aggregate, with a range from 0.0210 to 0.4202. Mean observed mass captured is 0.2114, with a range from 0.0415 to 0.5114.
- The strongest medium-scale cities include Nashville, Portland, Fresno, Chicago, and Richmond; the weakest include El Paso, Albuquerque, Minneapolis, San Francisco, and Columbia. This heterogeneity supports a cautious diagnostic story, not a report-changing conclusion.
- PR AUC and recall@top10 should remain the main sampled city-held-out benchmark because they evaluate exact-cell hotspot retrieval. Spatial alignment answers a different question: whether full-city prediction surfaces place elevated risk in broadly correct neighborhoods, corridors, or zones.

Suggested eventual placement: one compact supplemental subsection after the Denver spatial diagnostic or before limitations, with one small table summarizing scale-level averages and a sentence explicitly stating that spatial alignment does not replace the sampled city-held-out PR AUC / recall benchmark.
