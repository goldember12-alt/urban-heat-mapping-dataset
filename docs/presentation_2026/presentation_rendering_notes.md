# Rendering Notes

## Active Workflow

- Run `render_presentation.ps1` to build `urban_heat_transfer_presentation.pptx`.
- The script uses the Python native PowerPoint builder.
- The active workflow does not render HTML.

## If The Script Says Python Was Not Found

- Prefer the project environment at `C:\Users\golde\.venvs\STAT5630_FinalProject_DataProcessing\Scripts\python.exe`.
- Reopen PowerShell and rerun the script.

## If PowerShell Blocks The Script

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\render_presentation.ps1
```

## If The PowerPoint File Is Open

Close `urban_heat_transfer_presentation.pptx` in PowerPoint before rerunning the render script. If the file is locked and you need a review copy, run:

```powershell
C:\Users\golde\.venvs\STAT5630_FinalProject_DataProcessing\Scripts\python.exe -m src.run_editable_presentation --output-path docs\presentation_2026\urban_heat_transfer_presentation_content_revision.pptx
```

## Output Files

- `docs/presentation_2026/urban_heat_transfer_presentation.pptx`
- If the canonical `.pptx` is open/locked, use the review-copy command above to create `docs/presentation_2026/urban_heat_transfer_presentation_content_revision.pptx`.

## Notes

- The deck is intentionally optimized for projected presentation, so the notes file carries the detailed narrative.
- The active deck is editable in PowerPoint: text boxes, cards, and callout panels are native objects.
- Slides 2 through 6 place reusable presentation figures generated under `figures/presentation/`.
- The current seven-slide structure and presenter script are documented in `presentation_outline.md` and `presentation_speaker_notes.md`.
- Legacy Reveal / HTML outputs are not part of the active workflow anymore.
