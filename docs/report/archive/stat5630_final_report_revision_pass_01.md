# STAT5630 Final Report Revision Pass 01

Date: May 3, 2026

Purpose: integrate the supplemental all-city random-forest spatial-alignment diagnostic into the canonical report as a controlled thread, while keeping the sampled city-held-out PR AUC / recall benchmark primary.

## Pre-Edit Integration Map

| Paper location | Current issue | Spatial-alignment integration needed | Edit type |
| --- | --- | --- | --- |
| Abstract, if present | No abstract is present in the current draft. | No edit needed unless an abstract is added later. | Defer |
| Introduction / motivation | Transfer is framed mainly as exact-cell hotspot screening. | Add one light sentence distinguishing exact-cell retrieval from broader spatial placement. | Add sentence |
| Research questions | Spatial alignment is absent from the question set. | Add it as the final secondary question for the RF transfer model. | Revise sentence |
| Contribution paragraph | Contributions list dataset, validation comparison, and model comparison only. | Add a fourth, explicitly supplemental contribution: full-city spatial-placement diagnostic. | Revise paragraph |
| Validation design / metrics | Methods define within-city and city-held-out transfer, but not the spatial-placement diagnostic. | Add compact method paragraph after sampled benchmark scope and before results. | Add paragraph |
| Sampling design | Sampled benchmark and full-city scoring distinction is present but not connected to spatial alignment. | Clarify that full-city held-out rows are scored for diagnostics only, not benchmark replacement. | Revise paragraph |
| Results transition after city-held-out benchmark | Transfer results end at exact-cell ranking and heterogeneity. | Add natural follow-up: weak exact-cell retrieval does not answer broad placement. | Add transition |
| Figure 6 / spatial diagnostic discussion | Denver map is framed as a standalone diagnostic example. | Reframe Denver as a bridge that motivates all-city spatial alignment. | Revise paragraph/caption |
| Limitations | Spatial-alignment limitations absent. | Add scale-sensitivity, broad-placement-only, RF-only, heterogeneous-city cautions. | Revise paragraph |
| Future work | Mentions full held-out-city scoring as next step, which is now partly done for RF diagnostics. | Update to say future work should compare models, add richer predictors, and extend spatial validation beyond this diagnostic. | Revise paragraph |
| Conclusion | Does not include the spatial-placement nuance. | Add cautious conclusion that weak exact-cell transfer does not always imply spatially meaningless predictions, but signal is inconsistent. | Revise paragraph |

## Files Changed

- `docs/report/stat5630_final_report_draft.md`
- `docs/report/stat5630_final_report_revision_pass_01.md`
- `docs/chat_handoff.md`

## Summary Of Edits

- Replaced the related-work placeholder with a concise bridge connecting urban heat feature evidence to spatial validation and transfer.
- Replaced the within-city methods placeholder with support-checked 70/30 diagnostic language and an explicit caveat that the repo does not contain the original split script or random seed.
- Replaced the Figure 5 signal-shift placeholder with a concise interpretation of the weak city-level correlations and Nashville/relative-position visual pattern.
- Integrated exact-cell retrieval versus broader spatial placement as a recurring distinction.
- Added a compact spatial-alignment methods paragraph, not a standalone methods section.
- Added cautious all-city spatial-alignment results after the city-held-out and Figure 5 transfer story.
- Revised the Denver Figure 6 discussion so it motivates the all-city diagnostic rather than serving as proof by example.
- Updated limitations, future work, conclusion, Figure 6 caption, and reproducibility artifacts to preserve scope control.

## Where Spatial Alignment Was Integrated

| Paper location | Integration |
| --- | --- |
| Introduction / motivation | Added exact-cell retrieval versus broader spatial placement framing. |
| Research questions | Added a final secondary RF spatial-alignment question. |
| Contribution paragraph | Added supplemental full-city spatial-placement diagnostic as the fourth contribution. |
| Methods / metrics | Added compact diagnostic description: retained RF city-held-out contract, full eligible held-out scoring for diagnostics, 150 m / 300 m / 600 m smoothing, and five metric families. |
| Sampling design | Clarified that full-city scores are diagnostic and do not replace sampled PR AUC / recall. |
| Results | Added the 300 m all-city metric summary and cautious heterogeneous interpretation after the Figure 5 transfer/heterogeneity sequence. |
| Figure 6 | Reframed Denver as a motivation bridge to all-city spatial alignment. |
| Limitations | Added RF-only, scale-sensitive, broad-placement-only, and non-benchmark cautions. |
| Future work | Split future work into exact-cell full-row benchmarking and broader spatial-validation extensions. |
| Conclusion | Added the qualified point that weak exact-cell retrieval is not always spatially meaningless, but broad placement is inconsistent. |

## Remaining Placeholders

No bracketed `[Insert ...]` placeholders remain in the canonical draft after this pass.

## Claims That Still Need Verification

- The within-city diagnostic is support-checked from partner result artifacts, but the original split script, random seed, and thresholding code are not in the repo. The draft now states this limitation directly.
- The spatial-alignment metric values were manually checked from `outputs/modeling/supplemental/spatial_alignment_all_cities/tables/spatial_alignment_metrics_all_cities.csv`; no new PDF render was performed in this pass.
- If the paper later adds a spatial-alignment table or figure, the selected rows should be regenerated or copied from the canonical CSV rather than typed by hand.

## Recommended Next Codex Prompt

Render the revised report PDF, inspect the pages around Sections 1, 4, 5, Figure 6, and the reproducibility notes, then do a second targeted edit for structure and flow. Keep the exact-cell benchmark primary, keep spatial alignment supplemental, and do not add new figures unless the rendered layout clearly needs a compact spatial-alignment table.
