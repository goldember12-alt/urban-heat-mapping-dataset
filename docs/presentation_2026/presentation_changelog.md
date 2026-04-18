# Presentation Changelog

## Architecture Reset

- Retired the dual-output render path as the active workflow. The current build now targets `pptx` only.
- Added a Python slide-asset builder that pulls dataset counts and retained benchmark metrics directly from repo artifacts.
- Bypassed the old Quarto render path. The active workflow now uses a minimal markdown slide source rendered straight to `.pptx` with Pandoc.
- Kept detailed explanation in a separate notes file so the deck can stay lean.

## Slide Decisions

- Slide 1 now works as a clean title card with subtitle and talk framing instead of opening with document-style setup text.
- Slide 2 compresses motivation into three short framing cards plus one prominent research question.
- Slide 3 merges dataset scale and evaluation design into one scannable visual so methods do not consume multiple slides.
- Slide 4 combines the required model equations with the single benchmark figure and only the three metrics worth saying out loud.
- Slide 5 gives the Denver triptych nearly the whole slide and keeps the message to one caption.
- Slide 6 closes with one answer sentence, one caveat, one next step, and a small questions prompt instead of a generic outro slide.
