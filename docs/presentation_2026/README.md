# Presentation Deck (2026)

This folder uses a PowerPoint-first workflow for the cross-city urban heat talk. The active deck is a native editable `.pptx` with separate speaker notes.

## Active Files

- `render_presentation.ps1`: builds the native editable `.pptx`
- `presentation_outline.md`: current slide-by-slide deck structure
- `presentation_speaker_notes.md`: presenter notes with the detailed narrative
- `presentation_asset_manifest.md`: data artifacts, generated figures, and checked metric values used by the deck
- `presentation_rendering_notes.md`: render commands and troubleshooting notes
- `presentation_changelog.md`: chronological record of presentation revisions
- `urban_heat_transfer_presentation.pptx`: active editable deck

## Current Deck Structure

- `7` slides total
- `1` title slide
- `5` content slides comparing two evaluation methodologies
- `1` Q&A slide
- no appendix slides
- no HTML output in the active workflow

## Render From Repo Root

```powershell
powershell -ExecutionPolicy Bypass -File .\docs\presentation_2026\render_presentation.ps1
```

The script will build a native editable PowerPoint and write:

- `docs/presentation_2026/urban_heat_transfer_presentation.pptx`

## Notes

- The deck is intentionally sparse. Explanatory detail belongs in `presentation_speaker_notes.md`, not on the slides.
- Benchmark values are pulled from retained repo artifacts rather than retyped by hand.
- The active narrative contrasts within-city held-out evaluation from the isolated partner logistic/RF table with this repo's city-held-out transfer benchmark.
- The deck phrases the partner split carefully as appearing consistent with a within-city or row-level 70/30 holdout based on support counts, unless partner code later verifies the exact split.
- The active render path produces only PowerPoint because the deck is optimized for live presentation, not dual-format parity.
- The active deck is rebuilt from editable PowerPoint objects plus reusable presentation figures.
- Reusable presentation figures now live under `figures/presentation/` for Slides 2 through 6.
- Slide 2 now foregrounds the predictor-to-risk flow and the two validation questions.
- Slide 3 compares logistic regression and random forest with a visual two-panel model diagram using the same six input features in both panels.
- Slide 4 places within-city and city-held-out results side by side.
- Slide 5 adds a city-level partner-vs-repo scatter comparison.
- Slide 6 is now a Denver held-out map example from retained benchmark map points.
