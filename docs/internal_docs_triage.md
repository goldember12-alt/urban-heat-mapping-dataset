# Internal Documentation Triage

This table records public-risk triage for obvious internal or development-oriented documents. No files were deleted in these cleanup passes.

| Path | Current public risk | Recommendation | Move now? |
| --- | --- | --- | --- |
| `AGENTS.md` | Contains agent operating rules, local environment conventions, and workflow-maintenance instructions that are useful internally but confusing for public readers. | Keep for agent use, but do not link from public README navigation. Consider moving to an internal docs area only after confirming agent discovery behavior. | No |
| `docs/chat_handoff.md` | Rolling Codex/project handoff with local paths, verification history, and internal next-step language. High confusion risk as a public entry point. | Keep for continuity, remove from public navigation, and later move to `docs/internal/` if links and agent conventions are updated. | No |
| `docs/repo_forward_facing_polish_plan.md` | Internal audit and work plan with local-path findings and cleanup prompts. | Keep as internal planning context; do not link as public project documentation except from internal triage/safety notes. | No |
| `docs/internal/report_development/final_report_planning.md` | Report-development handoff with assignment details, render commands, planning language, and local paths. | Moved from `docs/report/` to keep public report navigation focused on source, figures, tables, and rendered draft. | Done |
| `docs/internal/report_development/stat5630_draft_critical_review.md` | Critical review memo for revision work, not a polished project document. Some encoding artifacts and internal critique language. | Moved from `docs/report/` as internal report QA history. | Done |
| `docs/internal/report_development/stat5630_revision_pass_notes.md` | Revision-pass QA record with local commands and internal verification details. | Moved from `docs/report/` as internal report QA history. | Done |
| `docs/internal/report_development/stat5630_visual_qa_notes.md` | Visual QA record with local temporary paths and verification details. | Moved from `docs/report/` as internal report QA history. | Done |
| `docs/report/archive/` | Historical report outlines, critiques, and merge notes; not harmful but not current public guidance. | Label as archive and keep out of main public navigation. | No |
| `docs/report/projectproposal.pdf` | Earlier proposal may drift from completed project and should not be mistaken for final methods/results. | Keep only as historical/project context or move to archive later. Public readers should use the final report first. | No |
| `docs/report/STAT5630 Slides-and-presentation--requirement-2026 (1).pdf` | Course assignment material; not part of the research artifact. | Move to internal/course materials later if public cleanup continues. | No |
| `docs/report/tables/retained_model_run_metadata.csv` | Report-facing table previously contained absolute local run directories. | Replace absolute local run directories with repository-relative output paths and keep as curated report metadata. | No |
| `docs/spatial_alignment_design.md` | Previously useful method/design content with implementation prompt remnants and local command examples. | Rewritten as a public supplemental smoothed spatial-alignment method note. | Done |
| `docs/presentation_2026/presentation_changelog.md` | Presentation development log, not core reproducibility material. | Keep out of public navigation; move to internal/archive in a later pass if presentation materials remain public. | No |

## `.gitignore` Quick Audit

- Raw data folders: `data_raw/` is ignored.
- Processed data folders: `data_processed/` is ignored.
- Virtual environments, cache, scratch, and env files: `.venv/`, `env/`, `venv/`, repo-local scratch/cache folders, `.env`, and `.env.local` are ignored.
- Figures: top-level `figures/` is ignored, with `docs/report/figures/` explicitly unignored for curated report figures.
- Outputs: `outputs/` is not broadly ignored, and a quick `git ls-files outputs` check found 816 tracked output files. A later pass should decide which tracked generated outputs are intentional public artifacts.
- Rendered report PDFs: tracked PDFs include `docs/report/stat5630_final_report_draft.pdf`, `docs/report/projectproposal.pdf`, and the course assignment PDF. The final rendered report PDF may be intentional as a convenience artifact; the proposal and assignment PDFs need a later public-repo decision.
