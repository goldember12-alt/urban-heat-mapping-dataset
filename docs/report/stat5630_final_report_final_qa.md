# Final Report Revision QA

Date: 2026-05-03

## Prose Edits Made

- Retitled the report to include the final scope: same-city learning, city-held-out transfer, and spatial alignment.
- Tightened the opening so page 1 now states what was built, what was tested, the main validation-design finding, and what the spatial-alignment diagnostic adds.
- Reduced defensive framing by converting repeated "not X" caveats into positive scope statements.
- Clarified that same-city screening and city-held-out transfer are both central validation designs, while the spatial-alignment layer is a supplemental diagnostic.
- Added Section 5 subheadings for same-city screening, exact-cell transfer, heterogeneity/signal shift, broad spatial placement, and predictive interpretation.
- Added a short discussion bridge explaining why exact-cell retrieval and broad spatial screening answer different planning questions.
- Strengthened the conclusion around the main "so what": same-city learning overstates unseen-city performance, simple public predictors transfer modestly, random forest helps selectively, and validation design changes the scientific conclusion.
- Made the Data and Code Availability note more modest about the GitHub repository: the workflow is maintained there, but raw downloads and generated artifacts may require external acquisition, storage, and recomputation.

## Figure/Table/Layout Edits Made

- Rebuilt Figure 3 as a cleaner visual schematic with an explicit 24 training city / 6 held-out city split and a separate leakage-control box.
- Increased Figure 7's report-facing size and label readability, and clarified its axis/point-size explanation in the caption.
- Increased the Denver diagnostic point size slightly and strengthened the Figure 6 caption so it supports the spatial-alignment argument without overclaiming.
- Shortened Table 3 row labels from "5,000 sampled" / "20,000 sampled" to "5k sampled" / "20k sampled" for easier scanning.
- Re-rendered `docs/report/stat5630_final_report_draft.pdf`.

## Blind-Reader Check

- Research question after page 1: yes. The introduction now states the 30-city dataset, the same-city versus unseen-city validation contrast, and the spatial-alignment add-on before the literature discussion ends.
- Same-city screening, exact-cell transfer, and broad spatial placement: yes. They are defined early and revisited in Methods, Results, and Conclusion.
- Coordinate exclusion: yes. Methods explain that coordinates were excluded to focus on portable surface-characteristic relationships; Future Work explains how location-aware models should be tested.
- RF interpretation: yes. The report says RF helps strongly within cities and selectively under transfer, especially in some hot arid cities, but is not a universal transfer solution.
- Figure 7 contribution: yes. The caption and text explain that Figure 7 shows broad 300 m spatial placement, not exact-cell retrieval.
- Internal/Codex language: no remaining obvious internal workflow language was found in the report text.

## Remaining Imperfections

- Figure 2 is still somewhat word-forward, but it is readable and no longer the main explanatory burden.
- Figure 5 remains label-dense because all city labels are useful for the heterogeneity story.
- Figure 6 is still a compact point-map diagnostic; the map is readable, but the caption carries part of the interpretation.
- Table 1 remains dense, especially the ECOSTRESS row, but the rendered PDF is readable without visible clipping.

## PDF QA Result

- Rendered PDF page count: 29.
- Markdown image references checked: 14 image references, 0 missing local image files.
- Rendered-PDF visual QA found no visible clipping, off-page text, figure-panel overlap, or awkward table splitting in the checked final PDF.
- Targeted rendered-page checks included Tables 1 and 3, Figures 3, 6, and 7, Appendix Figure A4, Appendix Figure A7, and the Data and Code Availability note.
- The GitHub reproducibility note is appropriately modest: it identifies the repository as the maintained workflow and does not imply that all raw data or generated artifacts are bundled or trivially reproducible.
