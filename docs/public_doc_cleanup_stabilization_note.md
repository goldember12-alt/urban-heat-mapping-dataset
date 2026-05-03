# Public Documentation Cleanup Stabilization Note

Date: 2026-05-03

## Scope

This stabilization pass was limited to documenting and classifying the current dirty worktree after the public-documentation cleanup work. No files were staged or committed, no license was added, and no broad repository cleanup was performed.

## Files Intentionally Changed

- `docs/README.md`: public documentation navigation plus an internal/development notes section.
- `docs/internal_docs_triage.md`: internal-doc triage checklist updated to reflect completed moves and the spatial-alignment rewrite.
- `docs/publication_safety_scan.md`: safety-scan record updated with current remaining internal-only and false-positive match categories.
- `docs/spatial_alignment_design.md`: rewritten as a public supplemental smoothed spatial-alignment method note.
- `docs/chat_handoff.md`: rolling handoff updated with the public-doc cleanup status.
- `docs/report/archive/final_report_outline.md`: internal pointer updated to the moved report-planning path.
- `docs/internal/report_development/final_report_planning.md`: internal references updated after the move.

## Files Intentionally Moved

- `docs/report/final_report_planning.md` -> `docs/internal/report_development/final_report_planning.md`
- `docs/report/stat5630_draft_critical_review.md` -> `docs/internal/report_development/stat5630_draft_critical_review.md`
- `docs/report/stat5630_revision_pass_notes.md` -> `docs/internal/report_development/stat5630_revision_pass_notes.md`
- `docs/report/stat5630_visual_qa_notes.md` -> `docs/internal/report_development/stat5630_visual_qa_notes.md`

## Files Restored Or Recommended For Restoration

- `docs/report/critique.md`: recommended for restoration or an explicit user-approved move. A replacement copy exists at `docs/report/archive/critique.md`, but it is not an exact no-change move relative to `HEAD`, so the deletion should not be accepted silently.
- `docs/report/final_report_outline.md`: recommended for restoration or an explicit user-approved move. A replacement copy exists at `docs/report/archive/final_report_outline.md`, but it is not an exact no-change move relative to `HEAD`, so the deletion should not be accepted silently.

Attempted command:

```bash
git restore -- docs/report/critique.md docs/report/final_report_outline.md
```

Result: failed with `fatal: Unable to create ... .git/index.lock: Permission denied`. No forced recovery was attempted.

## Unresolved User Decisions

- Decide whether `docs/report/critique.md` should be restored to its original location, moved to `docs/internal/report_development/`, or intentionally archived.
- Decide whether `docs/report/final_report_outline.md` should be restored to its original location, moved to `docs/internal/report_development/`, or intentionally archived.
- Decide whether untracked generated spatial-alignment outputs under `outputs/modeling/supplemental/spatial_alignment_all_cities/` belong in the public patch. Current recommendation: leave them untracked for review and do not include them in the public-doc cleanup commit.
- Decide whether report figure/table/code changes from earlier modeling/report work belong in the same commit as the public-doc cleanup. Current recommendation: keep the public-doc cleanup commit narrow.

## Remaining Public-Facing Local Path Issues

Focused checks of `README.md`, `docs/README.md`, and `docs/spatial_alignment_design.md` found no local Windows path or user-virtual-environment references. The full scan still reports `.gitignore` scratch-directory patterns such as `.tmp/`, which are benign.

## Remaining Internal-Only Local Path Issues

- `docs/chat_handoff.md` contains historical local commands and temporary render paths.
- `docs/repo_forward_facing_polish_plan.md` records earlier local-path findings as part of an internal cleanup plan.
- `docs/internal/report_development/` contains report-development history with local commands and QA notes.
- `docs/presentation_2026/` still contains presentation-build notes/scripts with local build details.
- `src/appeears_client.py` and `tests/test_appeears_client.py` contain credential-handling terminology and mocked token/password strings, not real secrets.
- `src/_vendor_pptx/` contains vendored-library uses of words such as `token`, `password`, and `tmpdir`.

## Recommended Next Commit Contents

For a narrow public-documentation cleanup commit, include:

- `docs/README.md`
- `docs/internal_docs_triage.md`
- `docs/publication_safety_scan.md`
- `docs/public_doc_cleanup_stabilization_note.md`
- `docs/spatial_alignment_design.md`
- `docs/chat_handoff.md`
- the four intentional report-development moves under `docs/internal/report_development/`
- only the minimal broken-link update in `docs/report/archive/final_report_outline.md` if that archive move is approved

Do not include large generated outputs, report figure/table regeneration, or unrelated modeling/source-code changes in this narrow documentation commit unless the user explicitly chooses a broader commit.

## Recommended Next Repo-Polish Prompt

"Review the stabilization note and decide the fate of `docs/report/critique.md` and `docs/report/final_report_outline.md`: restore to original locations, move to `docs/internal/report_development/`, or keep archived. Then prepare a narrow public-documentation cleanup commit plan that excludes generated spatial-alignment outputs, report-render artifacts, and unrelated modeling code changes."
