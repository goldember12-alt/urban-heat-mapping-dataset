# STAT5630 Final Report Visual QA Notes

Date: 2026-05-03

## Scope

This pass focused on report-PDF presentation quality rather than new modeling results. The main deliverables were updated report Markdown, refreshed report-facing artifacts where needed, a rerendered PDF, and visual verification of the rendered pages.

## Rendering And Audit Method

- Rerendered `docs/report/stat5630_final_report_draft.pdf` from `docs/report/stat5630_final_report_draft.md` using the existing Pandoc/XeLaTeX workflow.
- Rendered every PDF page to PNG previews with the bundled Node/pdfjs stack.
- Visually inspected the final 30-page PDF using contact sheets in `C:\Users\golde\.tmp\STAT5630_FinalProject_DataProcessing\pdf_visual_audit\final\`.
- After the last reproducibility-note path cleanup, rechecked targeted rendered pages 13, 14, 20, 21, 29, and 30 under `C:\Users\golde\.tmp\STAT5630_FinalProject_DataProcessing\pdf_visual_audit\final_post_patch\pages\`.
- Confirmed the report source has 14 Markdown image references and zero missing local image files.

## Fixed Issues

- Table 1 was simplified to four columns: Source, Product/layer, Constructed variable(s), and Role. Long spatial-role prose was moved out of the table and into surrounding text.
- Table 2 spacing was tightened for large row counts using smaller table text and adjusted column spacing.
- Table 3 model labels were shortened, explanatory details were moved into notes, and the table was moved to its own page so it no longer splits awkwardly.
- Appendix Table A1 was replaced with grouped bullet lists for metadata, primary predictors, target/quality fields, and supplemental context features.
- Appendix Table A3 was compacted into a shorter specification table, with tuning-grid details moved into notes.
- Reproducibility notes were shortened and the long Windows Python command was manually wrapped with PowerShell line continuation logic.
- Figure/table captions and surrounding text were tightened where the old wording made comparison constraints or figure purpose less clear.
- The selected high/low spatial-alignment map contrast was regenerated as a clearer multi-panel figure focused on observed surface, predicted surface, and top-region overlap.
- Main results now include the cautious Appendix Figure A4 interpretation: random-forest gains concentrate in hot arid cities, while hot humid and mild cool cities more often favor logistic or show weaker RF gains; this is framed as hypothesis-generating rather than causal.
- Future work now explicitly addresses intentionally excluded raw latitude/longitude and proposes location-aware benchmarks to separate portable surface relationships from city-specific spatial effects.

## Visual QA Result

The final rendered PDF was visually checked page by page. No visible table-text overlap, clipped text, off-page command/path text, or awkward table splitting remained in the checked final PDF. Some appendix figures remain information-dense, but their labels and captions are readable enough for final submission and no remaining figure-panel clipping was visible.

## Intentionally Not Changed

- No reported performance metrics were changed unless regenerated from existing report artifacts.
- The city-held-out benchmark remains the core contribution.
- The spatial-alignment diagnostic remains supplemental and is not presented as proof of operational usefulness.
- Climate-group heterogeneity is described cautiously and not interpreted causally.
