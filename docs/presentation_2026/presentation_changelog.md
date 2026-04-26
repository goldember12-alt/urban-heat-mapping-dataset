# Presentation Changelog

## 2026-04-19 Detailed Speaker Notes Accuracy Pass

- Documentation refresh:
  - Rewrote `presentation_speaker_notes.md` as a detailed slide-by-slide companion document rather than presenter-prompt notes.
  - Removed the introductory note under the `Speaker Notes` heading so the document starts directly with Slide 1.
  - Expanded each slide section to explain the project mechanisms, figure elements, validation designs, metric definitions, conclusions, and limitations.
  - Added detailed Slide 4 notes explaining thresholded within-city precision / recall / F1 versus city-held-out PR AUC, mean city PR AUC, and recall at top 10%.
  - Added explicit notes that the retained city-held-out runs shown in the deck use a `5,000` rows-per-city sample cap for computational feasibility.
  - Removed the obsolete likely question about whether the partner 70/30 split is verified and expanded the remaining likely-questions section.
  - Updated the presentation README, outline, and asset manifest so the partner split is described as verified rather than tentative.
- Verification:
  - Scanned the current presentation documentation for stale presenter-prompt language and outdated partner-split hedging after the edits.

## 2026-04-19 Title-Case Label Pass

- Capitalization pass:
  - Updated slide headings, panel titles, chart titles, axis labels, map titles, and visible legends on Slides 2 through 6 to use title-case styling.
  - Updated the focused presentation tests to expect the revised title-case slide headings.
  - Aligned documentation headings for Slide 4 with the current deck title, `Results Side by Side`.
- Verification:
  - Regenerated `docs/presentation_2026/urban_heat_transfer_presentation.pptx`.
  - Rendered all 7 slides to PNG previews through the non-interactive deck render path and visually inspected Slides 2 through 6.
  - `C:\Users\golde\.venvs\STAT5630_FinalProject_DataProcessing\Scripts\python.exe -m pytest tests\test_presentation_deck_builder.py` passed with `3 passed`.

## 2026-04-19 Documentation Alignment Refresh

- Documentation refresh:
  - Updated the presentation README active-file list and current deck notes.
  - Updated the outline so Slide 3 is described as a two-panel visual logistic-versus-random-forest model diagram rather than a rendered mathematical model section.
  - Updated the speaker notes so Slide 3's talking points match the final feature-to-weighted-sum and feature-to-tree-vote visuals.
  - Updated the Slide 6 speaker note to describe the current three equal map panels.
  - Updated the asset manifest's Slide 3 figure description to match the final model-logic visual.
  - Replaced the stale legacy Quarto file content with an explicit inactive-stub note and the current seven-slide structure.
- Verification:
  - Scanned the presentation documentation for stale old-deck phrases and confirmed the current README, outline, speaker notes, asset manifest, rendering notes, and Quarto stub now match the active seven-slide PowerPoint narrative.

## 2026-04-19 RF Tree Gap Micro-Pass

- Slide 3 random-forest revision:
  - Moved the two random-forest trees slightly farther apart and reduced their branch spread.
  - Confirmed the `elev.` and `cover` split boxes no longer overlap and the leaf circles have visible separation.
- Verification:
  - Regenerated `docs/presentation_2026/urban_heat_transfer_presentation.pptx`.
  - Rendered all 7 slides to PNG previews through the non-interactive deck render path and visually inspected Slide 3.
  - `C:\Users\golde\.venvs\STAT5630_FinalProject_DataProcessing\Scripts\python.exe -m pytest tests\test_presentation_deck_builder.py` passed with `3 passed`.

## 2026-04-19 NDVI Color And RF Tree Spacing Pass

- Slide 3 / feature-color revision:
  - Added a distinct NDVI green so NDVI no longer uses the same chip color as land cover.
  - Applied the NDVI color consistently in the predictor chips on Slide 2 and the model-feature chips / contribution bar on Slide 3.
- Slide 3 random-forest revision:
  - Reduced the random-forest diagram from three small trees to two larger trees.
  - Increased horizontal breathing room for the tree split labels while preserving the multiple-path / averaged-vote visual logic.
- Verification:
  - Regenerated `docs/presentation_2026/urban_heat_transfer_presentation.pptx`.
  - Rendered all 7 slides to PNG previews through the non-interactive deck render path and visually inspected Slides 2 and 3.
  - `C:\Users\golde\.venvs\STAT5630_FinalProject_DataProcessing\Scripts\python.exe -m pytest tests\test_presentation_deck_builder.py` passed with `3 passed`.

## 2026-04-19 Slide 3 Spacing And Logistic Flow Clarification

- Slide 3 revision:
  - Increased vertical spacing inside both model panels and widened the gutter between the logistic-regression and random-forest cards.
  - Recentered the logistic diagram inside its panel.
  - Replaced the unclear curve-and-marker endpoint with a direct vertical flow from feature chips to weighted sum to a risk-score output pill.
  - Preserved the random-forest panel structure while aligning its vertical rhythm with the revised logistic panel.
- Verification:
  - Regenerated `docs/presentation_2026/urban_heat_transfer_presentation.pptx`.
  - Rendered all 7 slides to PNG previews through the non-interactive deck render path and visually inspected Slide 3.
  - `C:\Users\golde\.venvs\STAT5630_FinalProject_DataProcessing\Scripts\python.exe -m pytest tests\test_presentation_deck_builder.py` passed with `3 passed`.

## 2026-04-19 Slide 3 Two-Panel Model Redesign

- Slide 3 revision:
  - Removed the internal "same inputs" title/subtitle and the separate shared-feature-contract band.
  - Rebuilt the Slide 3 figure as two equal side-by-side panels: logistic regression on the left and random forest on the right.
  - Repeated the same six feature chips inside both model diagrams so the common input contract is visible without a separate explanatory container.
  - Added more interpretable model visuals: feature weights feeding a risk output for logistic regression, and labeled feature split trees feeding averaged votes for random forest.
  - Fixed the prior curve-label collision by replacing the overlapping label with a separate risk output chip.
- Verification:
  - Regenerated `docs/presentation_2026/urban_heat_transfer_presentation.pptx`.
  - Rendered all 7 slides to PNG previews through the non-interactive deck render path and visually inspected the final Slide 3 preview from the canonical deck.
  - `C:\Users\golde\.venvs\STAT5630_FinalProject_DataProcessing\Scripts\python.exe -m pytest tests\test_presentation_deck_builder.py` passed with `3 passed`.

## 2026-04-19 Slide-Specific Polish Follow-Up

- Slide 2 spacing fix:
  - Slightly separated the two bottom validation panels while preserving their parallel sizing.
  - Shifted the within-city legend away from the training/held-out dot pattern so the key no longer competes with the diagram.
  - Kept the larger predictor-to-hotspot-risk flow as the top visual anchor.
- Slide 3 redesign:
  - Replaced the equation-heavy model panel with a more diagrammatic comparison: shared feature chips, a weighted-signal-to-risk-curve visual for logistic regression, and a tree-vote ensemble visual for random forest.
  - Removed the cramped rendered math from the model body while preserving the same narrative: same inputs, different model forms.
- Slide 4 polish:
  - Moved the small method notes up near each chart title so they read as chart context rather than plotted content.
- Slide 6 map layout:
  - Reworked the Denver held-out map figure into three equally spaced side-by-side maps: predicted top-decile risk, observed hotspot cells, and error pattern.
  - Enlarged the map footprints and retained the bottom legend.
- Verification:
  - Built `docs/presentation_2026/urban_heat_transfer_presentation_content_revision.pptx`.
  - Rendered all 7 slides to PNG previews through the non-interactive deck render path and visually inspected Slides 2, 3, 4, and 6 after the final pass.
  - The canonical deck path could not be overwritten because `docs/presentation_2026/urban_heat_transfer_presentation.pptx` was locked: `PermissionError: [Errno 13] Permission denied`.
  - `C:\Users\golde\.venvs\STAT5630_FinalProject_DataProcessing\Scripts\python.exe -m pytest tests\test_presentation_deck_builder.py` passed with `3 passed`.

## 2026-04-19 Vertical Figure Expansion And Map Replacement

- Layout revision:
  - Removed the separate bottom takeaway text boxes from Slides 2 through 5.
  - Expanded Slides 2 through 5 figures vertically to use the freed space and reduce the horizontally stretched report-page feel.
  - Removed the separate target box from Slide 2 and folded the target idea into the predictor-to-hotspot-risk flow.
  - Kept Slide 3 per duplicate-table feedback and made the math section less cramped with larger panels and split equations.
  - Removed the extra top title/subtitle text inside the Slide 4 and Slide 5 figures.
  - Moved the Slide 5 climate legend below the scatterplots to match the Slide 4 legend placement.
- Slide replacement:
  - Treated the Slide 6 metric table as duplicative of Slide 4's metric content.
  - Replaced Slide 6 with a presentation-oriented Denver held-out map figure generated from `outputs/modeling/reporting/heldout_city_maps/heldout_city_map_points.parquet`.
- Verification:
  - Regenerated `docs/presentation_2026/urban_heat_transfer_presentation.pptx`.
  - Rendered all 7 slides to PNG previews through the non-interactive deck render path and visually inspected the final pass.
  - `C:\Users\golde\.venvs\STAT5630_FinalProject_DataProcessing\Scripts\python.exe -m pytest tests\test_presentation_deck_builder.py` passed with `3 passed`.

## 2026-04-19 Polish And Readability Pass

- Visual polish:
  - Tightened Slide 1 title spacing and added a subtle accent rule so the opener feels more deliberate while staying minimal.
  - Rebuilt Slide 2's setup schematic with larger validation panels, larger predictor chips, clearer train/held-out cell patterns, and fewer nested frames.
  - Rebalanced Slide 3 around a split feature vector and parallel logistic/random-forest panels with less micro-text.
  - Increased chart label, legend, axis, and annotation readability on Slides 4 and 5.
  - Kept Slide 6 as a spreadsheet-style metric table per feedback, but removed the audience-facing readout column so the data table itself is the slide focus.
  - Repositioned the Q&A slide text for a more intentional close.
- Verification:
  - Regenerated `docs/presentation_2026/urban_heat_transfer_presentation.pptx`.
  - Rendered all 7 slides to PNG previews using the non-interactive deck render path and visually inspected the final pass.
  - `C:\Users\golde\.venvs\STAT5630_FinalProject_DataProcessing\Scripts\python.exe -m pytest tests\test_presentation_deck_builder.py` passed with `3 passed`.

## 2026-04-19 Content-Density Revision Pass

- Narrative/content revision:
  - Combined the former research-question and evaluation-design setup into one denser Slide 2.
  - Added back the mathematical modeling section as Slide 3, with shared feature vector, logistic SAGA probability model, and random-forest ensemble score.
  - Combined the within-city and city-held-out result views into one side-by-side Slide 4.
  - Added a new data-rich Slide 5 showing city-level relationships between within-city RF metrics and city-held-out RF metrics.
  - Replaced the prior broad synthesis graphic with a tabular Slide 6 comparing logistic and random forest within each evaluation block.
- New reusable figures:
  - `figures/presentation/setup_predictors_evaluation_questions.(png|svg)`.
  - `figures/presentation/logistic_rf_model_math.(png|svg)`.
  - `figures/presentation/within_city_vs_transfer_results.(png|svg)`.
  - `figures/presentation/city_signal_transfer_relationship.(png|svg)`.
  - `figures/presentation/evaluation_metric_comparison_table.(png|svg)`.
- Verification:
  - Focused presentation tests passed after the content restructure.
  - The canonical PowerPoint file was open in PowerPoint and could not be overwritten; a review copy was generated at `docs/presentation_2026/urban_heat_transfer_presentation_content_revision.pptx`.

## 2026-04-19 Evaluation-Methodology Narrative Rebuild

- Narrative reset:
  - Rebuilt the active 7-slide deck around two audience-facing evaluation questions rather than the prior workflow / Denver / climate-heterogeneity arc.
  - Kept Slide 1 as the title opener and Slide 7 as the Q&A close.
  - Reframed Slides 2 through 6 around research question, predictor set, within-city held-out evaluation, city-held-out transfer evaluation, and the interpretation of the contrast.
- Partner-results integration:
  - Added partner model-summary loading to the presentation data contract.
  - Used `outputs/modeling/partner_data/per_city_logistic_rf_results/tables/partner_model_summary.csv` for hotspot precision, recall, and F1.
  - Used `partner_results_metadata.json` to phrase the split carefully as appearing consistent with about a `30%` held-out sample per city.
- New reusable figures:
  - Added `figures/presentation/research_question_predictors.(png|svg)`.
  - Added `figures/presentation/two_evaluation_questions.(png|svg)`.
  - Added `figures/presentation/within_city_hotspot_results.(png|svg)`.
  - Added `figures/presentation/city_heldout_transfer_results.(png|svg)`.
  - Added `figures/presentation/evaluation_contrast_takeaway.(png|svg)`.
- Retired from the active deck:
  - The previous workflow figure, project-math panel, Denver triptych slide, and climate heterogeneity figure are no longer used by the active presentation narrative.
- Verification:
  - Regenerated `docs/presentation_2026/urban_heat_transfer_presentation.pptx`.
  - Updated focused presentation tests for the new asset contract and slide text spine.

## 2026-04-18 Slide 4 Rescue And Slide 6 Caption Pass

- Slide 4:
  - Replaced the overlapping left-side editable text stack with a rendered `figures/presentation/project_model_math.(png|svg)` panel.
  - Removed the subtitle from the crowded top band so it no longer sits behind the project-math panel or the results figure.
  - Kept the logistic-versus-random-forest result diagram on the right, with the sampled-checkpoint caveat in a separate right-aligned caption box.
  - Gave the random-forest summation its own vertical lane in the project-math panel so the sigma notation no longer collides with the row title or explanatory note.
- Slide 6:
  - Split the climate figure and interpretation note into separate boxes.
  - Right-aligned the bottom caption text while keeping the figure panel uncluttered.
- Verification:
  - Updated presentation tests so Slide 4 expects two figure objects and generated editable text remains at least `18 pt`.

## 2026-04-18 Audience-Facing Polish And Math Pass

- Slide 2 workflow wording:
  - Replaced internal phrases with audience-facing language: urban areas and 30 m grids, satellite/support layers, city feature assembly, hotspot labels and audit, and unseen-city models.
  - Preserved the colored stage blocks and numeric scale row because those were working visually.
- Slide 4 model explanation:
  - Rebuilt the left side as readable project math: the within-city hottest-decile target, the six safe predictors, train-city-only preprocessing, and tuned logistic / random-forest parameters.
  - Kept the logistic-versus-random-forest result diagram on the right side and retained the sampled-checkpoint caveat.
- Slide 6 climate heterogeneity:
  - Reworked the climate-delta figure to show per-city points, climate means, standard deviations, and middle-50% spread bars.
  - Added a concise caption explaining why hot-arid spread can favor RF while hot-humid and mild-cool groups more consistently favor logistic.
- Generator and verification:
  - Updated the generator so future renders preserve the manually simplified Slide 7 and do not reintroduce undersized editable text.
  - Added a presentation test guard requiring generated editable text runs to be at least `18 pt`.

## 2026-04-18 Report Alignment And Climate-Figure Pass

- Report alignment:
  - Replaced the previous Slide 2 transfer-problem schematic with a workflow figure, `figures/presentation/data_to_transfer_workflow.(png|svg)`.
  - The new Slide 2 makes the deck show the repo lifecycle first: study areas, AppEEARS/support layers, per-city features, final dataset and audit, and held-out models.
  - Kept Slide 3 as the validation-design slide, avoiding duplicate transfer-explanation content across Slides 2 and 3.
- Slide 4 methods and spacing:
  - Reworked the left-side method block into math-style logistic and random-forest formulas with the actual pipeline/tuning context.
  - Made the sampling caveat explicit as `5,000 rows/city` sampled all-fold checkpoints rather than exhaustive `71.4M`-cell scoring.
  - Added vertical room in the benchmark comparison figure so the logistic/random-forest legend no longer collides with recall labels.
- Slide 6 scientific figure replacement:
  - Replaced the signal / caveat / next-step card with `figures/presentation/transfer_climate_heterogeneity.(png|svg)`.
  - The new figure plots RF frontier minus logistic 5k deltas by climate group for PR AUC and recall at top 10%, using per-city points and climate means from the retained report tables.
- Preserved:
  - Left Slide 1 and Slide 7 unchanged.
  - Kept Slide 5 as the large Denver spatial example.

## 2026-04-18 Focused Scientific Redesign Pass

- Slide 1 simplification:
  - Reduced the title slide to a dominant title, one coauthor line, and the bottom banner only.
  - Removed the extra floating support text so the opener reads as a minimal typographic slide rather than a small-card layout.
- New reusable figures created and refreshed:
  - Refreshed `figures/presentation/transfer_problem_schematic.(png|svg)` for Slide 2 as the same-city versus held-out-city transfer comparison.
  - Refreshed `figures/presentation/heldout_city_cv_schematic.(png|svg)` for Slide 3 as the benchmark-design / outer-fold workflow figure.
  - Added `figures/presentation/transfer_benchmark_result_comparison.(png|svg)` for Slide 4 as the main result comparison figure.
  - Added `figures/presentation/transfer_takeaway_summary.(png|svg)` for Slide 6 as the compact signal / caveat / next-step summary figure.
- Slide 5 text improvements:
  - Rewrote the title to a shorter, cleaner claim line.
  - Tightened the caption so it reads as one precise takeaway instead of panel-by-panel explanatory prose.
- Visual consistency enforcement:
  - Rebuilt Slides 2, 3, 4, and 6 around one dominant scientific-style figure per slide with shared palette logic, similar annotation density, and matching rounded white figure frames.
  - Kept Slide 5 as the anchor reference and aligned the rebuilt slides to its cleaner figure-first presentation style rather than adding more PowerPoint cards or decorative boxes.
- Text-fitting and spacing corrections:
  - Enlarged slide titles and widened title boxes so the main claims read cleanly at projector scale.
  - Removed awkward forced wraps in the Slide 4 method labels and Slide 5 title.
  - Tightened subtitle, caption, and caveat placement so text sits close to the figure it describes instead of floating in oversized containers.
  - Rebalanced figure frames and gutters so Slides 2, 3, 4, 5, and 6 use the horizontal canvas more efficiently.

## 2026-04-18 Cleanup + Visual Strengthening Pass

- Text-box fitting and layout fixes:
  - Slide 1: simplified the title composition, rebalanced the title/subtitle/author blocks, and tightened the footer so the opening card uses space more intentionally.
  - Slide 2: resized the figure panel, question banner, and label treatment so the slide reads through the schematic first and no longer depends on multiple top-row text cards.
  - Slide 3: resized the stat chips, enlarged the benchmark schematic panel, and tightened the footer callout so the benchmark logic reads in one scan.
  - Slide 4: rebuilt the left-side method stack with cleaner equation-card proportions and better spacing around the chart, metric boxes, and caveat strip.
  - Slide 5: enlarged the figure frame and rebalanced the caption/tag row for cleaner bottom-of-slide spacing.
  - Slide 6: replaced the old text-heavy takeaway cards with a more graphical signal / caveat / next-step summary and cleaned up the closing hierarchy.
  - Slide 7: simplified the Q&A card so the question and author line fill the slide more naturally.
- Wording reduced:
  - Slide 1 removes the old roadmap-style support card and keeps only the core framing line, dataset scale, and author/course information.
  - Slide 2 replaces most explanatory text with the transfer-comparison schematic and a single large research question.
  - Slide 3 keeps only the essential numbers and evaluation labels on-slide while pushing the logic into the schematic.
  - Slide 4 trims the predictor-contract copy and keeps the caveat short.
  - Slide 6 shortens the signal, caveat, and next-step text into brief scan-friendly statements.
- Reusable figures:
  - No additional figure filenames were added in this pass.
  - Refreshed the existing reusable schematics in `figures/presentation/`:
    - `transfer_problem_schematic.(png|svg)` for Slide 2
    - `heldout_city_cv_schematic.(png|svg)` for Slide 3
- Slide-space improvements:
  - Slides 2 and 3 now dedicate substantially more area to figure-led explanation.
  - Slide 4 removes a large low-value left-side empty zone and gives the result figure/metrics more breathing room.
  - Slide 6 converts the close from three dense blocks into a wider visual summary that uses the horizontal canvas.
- Remaining constraints:
  - The benchmark chart on Slide 4 and Denver triptych on Slide 5 remain external raster figures, so this pass improves their framing and readability but does not change the internal whitespace or typography baked into those source figures.

## Architecture Reset

- Retired the dual-output render path as the active workflow. The current build now targets `pptx` only.
- Added a Python slide-asset builder that pulls dataset counts and retained benchmark metrics directly from repo artifacts.
- Bypassed the old Quarto render path. The active workflow now builds the `.pptx` directly from Python with native PowerPoint objects.
- Kept detailed explanation in a separate notes file so the deck can stay lean.

## Slide Decisions

- Slide 1 now works as a sparse coauthored title card with transfer framing and dataset scale instead of opening with document-style setup text.
- Slide 2 now uses a reusable audience-facing workflow figure that shows the path from urban grids to unseen-city hotspot models.
- Slide 3 now uses stat chips plus a reusable held-out-city evaluation schematic so methods do not consume multiple slides.
- Slide 4 combines project-specific model math with the single benchmark figure and only the metrics worth saying out loud.
- Slide 5 gives the Denver triptych nearly the whole slide and keeps the message to one caption.
- Slide 6 closes with a climate-delta figure showing per-city spread, climate means, and where RF versus logistic tends to transfer better; Slide 7 handles Q&A as a separate minimal closing card.

## 2026-04-18 Layout Cleanup

- Removed the default PowerPoint title-and-picture placeholder effect from the rendered deck by postprocessing the `.pptx` into one full-slide image per slide.
- Increased slide-art height to full `16:9` and tightened internal placement so the slide canvas is used more aggressively without changing the slide sequence.
- Enlarged the title slide headline/support text, the models/results figure and metric callouts, the Denver map frame/caption, and the takeaway cards.
- Tightened the data/evaluation spacing and reduced conservative outer margins while preserving the existing visual language.

## 2026-04-18 Native PowerPoint Rebuild

- Replaced the flattened full-slide-image deck with a fully editable native PowerPoint built from text boxes, rounded-rectangle cards, callout panels, decorative shapes, and separately placed figure images.
- Reconstructed all six slides from the flattened version while preserving the same slide count, wording, order, and overall composition as closely as practical.
- Kept only the benchmark chart and Denver map as raster images because those are true figure assets.
- Switched the active render path from Pandoc/image-based export to a Python native PowerPoint builder.

## 2026-04-18 Figure-Led Readability Pass

- Resized and rebalanced text boxes, cards, and callouts so the editable deck uses cleaner wrapping and more natural padding rather than forcing short phrases into awkward line breaks.
- Simplified the title slide, added Nicholas Machado as coauthor, and removed the busy roadmap treatment in favor of a calmer opening card.
- Added a final Q&A slide in the same visual language as the title slide.
- Created two reusable schematic figures under `figures/presentation/`:
  - `transfer_problem_schematic.(png|svg)` for Slide 2
  - `heldout_city_cv_schematic.(png|svg)` for Slide 3
- Shifted Slides 2, 3, and 6 toward more figure-led communication with fewer words while preserving the existing result claims and caveats.
