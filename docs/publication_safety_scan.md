# Publication Safety Scan

Date: 2026-05-03

## Scan Commands

Targeted scan run:

```bash
rg -n "C:\\\\Users|OneDrive|\\.venvs|\\.tmp|\\.pip-cache|password|token|secret|api_key|apikey" README.md docs src tests .gitignore
git ls-files .env .env.local
```

Additional summary checks were run with `rg -l` for local-path patterns and credential-related words, plus quick checks of tracked `outputs/` files and tracked report PDFs.

## Fixed In This Pass

- Rewrote `README.md` so it no longer contains local Windows paths, OneDrive paths, user-level virtual-environment commands, Codex handoff navigation, or phase-history clutter.
- Added `docs/README.md` as public documentation navigation without local paths or handoff-first guidance.
- Sanitized `docs/report/tables/retained_model_run_metadata.csv` so report-facing run directories are repository-relative rather than absolute local paths.
- Moved report-development planning and QA notes from `docs/report/` to `docs/internal/report_development/` so public report navigation is no longer mixed with internal revision history.
- Rewrote `docs/spatial_alignment_design.md` as a public supplemental smoothed spatial-alignment method note with local interpreter paths and implementation-prompt text removed.

## Remaining Local-Path Matches

Remaining local-path matches are concentrated in internal/development notes, test/code credential handling, and vendored dependency code:

- `docs/chat_handoff.md`: rolling internal handoff with historical local commands and temporary render paths.
- `docs/repo_forward_facing_polish_plan.md`: internal cleanup plan that intentionally records local-path findings.
- `docs/internal/report_development/final_report_planning.md`, `docs/internal/report_development/stat5630_revision_pass_notes.md`, and `docs/internal/report_development/stat5630_visual_qa_notes.md`: moved report-development and QA notes with historical local commands.
- `docs/presentation_2026/render_presentation.ps1`, `docs/presentation_2026/presentation_rendering_notes.md`, and `docs/presentation_2026/presentation_changelog.md`: presentation-build notes and scripts.
- `tests/` and `src/`: some matches refer to temporary-path handling or path-length safeguards in code/tests.
- `src/_vendor_pptx/`: vendored package code contains generic `tmpdir`, `token`, or `password` terminology.

These were not all edited because the current scope is the next public documentation layer. A focused public-doc subset scan of `README.md`, `docs/README.md`, `docs/spatial_alignment_design.md`, `docs/workflow.md`, `docs/data_dictionary.md`, `docs/modeling_plan.md`, and `docs/report/stat5630_final_report_draft.md` found no remaining local-path or credential-like matches, aside from benign `.gitignore` scratch-directory patterns when `.gitignore` is included.

## Credential And Secret Findings

- `git ls-files .env .env.local` returned no tracked files.
- Credential-related matches in `src/appeears_client.py` and related tests refer to environment-variable handling, mocked test tokens, stale-token classification, or generic authentication code.
- Credential-related matches in `src/_vendor_pptx/` are vendored library terminology such as filter tokens, worksheet passwords, or temporary-directory options, not project credentials.
- No real secret or credential value was identified in the reviewed scan output. If a future scan finds an actual token, password, or key value, it should be removed from the working tree, rotated, and checked for Git history exposure before publication.

## `.gitignore` And Artifact Policy Notes

- `data_raw/` is ignored, which matches the policy that raw downloads should not be committed.
- `data_processed/` is ignored, which matches the policy that large processed artifacts should not be committed by default.
- Local virtual environments, scratch/cache folders, `.env`, and `.env.local` are ignored.
- Top-level `figures/` is ignored, while `docs/report/figures/` is unignored for curated report figures.
- `outputs/` is not broadly ignored; `git ls-files outputs` found 816 tracked files. Do not remove these in this pass, but decide later which generated outputs should remain public.
- Tracked report PDFs currently include the rendered draft report, the original project proposal, and a course assignment PDF. The rendered final report PDF may be useful to keep; the proposal and assignment PDFs need an explicit public-repo decision.
