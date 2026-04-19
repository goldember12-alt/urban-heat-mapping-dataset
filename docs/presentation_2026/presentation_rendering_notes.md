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

## Output Files

- `docs/presentation_2026/urban_heat_transfer_presentation.pptx`

## Notes

- The deck is intentionally optimized for projected presentation, so the notes file carries the detailed narrative.
- The active deck is editable in PowerPoint: text boxes, cards, and callout panels are native objects.
- Slides 2 through 6 place reusable presentation figures generated under `figures/presentation/`.
- Legacy Reveal / HTML outputs are not part of the active workflow anymore.
