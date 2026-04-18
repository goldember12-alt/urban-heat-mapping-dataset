# Presentation Changelog

## Architecture Reset

- Retired the dual-output render path as the active workflow. The current build now targets `pptx` only.
- Added a Python slide-asset builder that pulls dataset counts and retained benchmark metrics directly from repo artifacts.
- Bypassed the old Quarto render path. The active workflow now builds the `.pptx` directly from Python with native PowerPoint objects.
- Kept detailed explanation in a separate notes file so the deck can stay lean.

## Slide Decisions

- Slide 1 now works as a sparse coauthored title card with transfer framing and dataset scale instead of opening with document-style setup text.
- Slide 2 now uses a reusable problem-framing schematic plus one prominent research question.
- Slide 3 now uses stat chips plus a reusable held-out-city evaluation schematic so methods do not consume multiple slides.
- Slide 4 combines the required model equations with the single benchmark figure and only the three metrics worth saying out loud.
- Slide 5 gives the Denver triptych nearly the whole slide and keeps the message to one caption.
- Slide 6 closes with one answer sentence plus a visual signal / caveat / next-step summary, and Slide 7 now handles Q&A as a separate minimal closing card.

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
