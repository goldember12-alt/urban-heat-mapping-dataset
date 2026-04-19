# Presentation Changelog

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
