# Presentation Deck (2026)

This folder now uses a PowerPoint-first workflow for the cross-city urban heat talk. The active deck is a native editable `.pptx` with separate speaker notes.

## Active Files

- `render_presentation.ps1`: builds the native editable `.pptx`
- `presentation_speaker_notes.md`: presenter notes with the detailed narrative
- `presentation_changelog.md`: short summary of the reset and slide decisions
- `urban_heat_transfer_presentation.pptx`: active editable deck

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

The script will build a native editable PowerPoint and write:

- `docs/presentation_2026/urban_heat_transfer_presentation.pptx`

## Notes

- The deck is intentionally sparse. Explanatory detail belongs in `presentation_speaker_notes.md`, not on the slides.
- Benchmark values are pulled from retained repo artifacts rather than retyped by hand.
- The active render path produces only PowerPoint because the deck is optimized for live presentation, not dual-format parity.
- The active deck is rebuilt from editable PowerPoint objects. Only the benchmark chart and Denver map remain raster figures.
