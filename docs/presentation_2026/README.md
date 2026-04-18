# Presentation Deck (2026)

This folder now uses a PowerPoint-first workflow for the cross-city urban heat talk. The active deck is designed around one target only: a lean `.pptx` with separate speaker notes.

## Active Files

- `slides_powerpoint.qmd`: minimal slide source
- `render_presentation.ps1`: builds slide art, then renders the `.pptx` with Pandoc
- `presentation_speaker_notes.md`: presenter notes with the detailed narrative
- `presentation_changelog.md`: short summary of the reset and slide decisions
- `build/`: generated slide images and manifest

## Current Deck Structure

- `6` slides total
- `1` title slide
- `5` non-title slides
- no appendix slides
- no HTML output in the active workflow

## Render From Repo Root

```powershell
powershell -ExecutionPolicy Bypass -File .\docs\presentation_2026\render_presentation.ps1
```

The script will:

1. build slide visuals from repo artifacts
2. render `slides_powerpoint.qmd` to PowerPoint only
3. write `docs/presentation_2026/urban_heat_transfer_presentation.pptx`

## Notes

- The deck is intentionally sparse. Explanatory detail belongs in `presentation_speaker_notes.md`, not on the slides.
- Benchmark values are pulled from retained repo artifacts rather than retyped by hand.
- The active render path produces only PowerPoint because the deck is optimized for live presentation, not dual-format parity.
- The slide source is now simple markdown-plus-images. Quarto is no longer the active renderer for this deck.
