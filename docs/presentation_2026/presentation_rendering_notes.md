# Rendering Notes

## Active Workflow

- Run `render_presentation.ps1` to build the slide visuals and render `urban_heat_transfer_presentation.pptx`.
- The script uses the Python slide-asset builder plus Pandoc.
- The active workflow does not render HTML.

## If The Script Says Pandoc Was Not Found

- Install Quarto for your user account, because the script can reuse the bundled `pandoc.exe`.
- Reopen PowerShell and rerun `render_presentation.ps1`.

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
- `docs/presentation_2026/build/slide_manifest.json`
- `docs/presentation_2026/build/*.png`

## Notes

- The deck is intentionally optimized for projected presentation, so the notes file carries the detailed narrative.
- Legacy Reveal / HTML outputs are not part of the active workflow anymore.
