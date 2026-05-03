# Repository Forward-Facing Polish Plan

This is an internal plan for making `https://github.com/goldember12-alt/urban-heat-mapping-dataset` presentable to readers of the STAT 5630 final report. It is intentionally an audit and work plan, not a broad restructuring pass.

## Current Snapshot

- The repository already contains the core Python workflow, report source, report figures/tables, tests, and project documentation for the 30-city urban heat hotspot dataset and modeling framework.
- The public-facing story should match the report: same-city screening is easier, exact-cell city-held-out transfer is the main benchmark, and broad spatial placement is a supplemental spatial-alignment diagnostic.
- Several tracked documents and artifacts still read like internal development state: `README.md`, `AGENTS.md`, `docs/chat_handoff.md`, `docs/report/final_report_planning.md`, report revision notes, presentation notes, and many generated `outputs/` files.
- Local Windows paths appear in public-visible documents and report metadata tables. These should be removed, rewritten as generic examples, or moved to clearly internal notes before sharing the repo link confidently.
- No top-level `LICENSE` file was found in the working tree snapshot inspected for this plan. Do not add a license until the intended license is confirmed.

## 1. README Alignment

Goal: make `README.md` read like a public project document, not a rolling Codex handoff.

Findings:

- `README.md` has the right high-level project frame, but it is too long and operationally internal for a first-time reader.
- It includes user-specific paths such as `C:\Users\golde\.venvs\STAT5630_FinalProject_DataProcessing\Scripts\python.exe`, `C:\Users\golde\.tmp\...`, and `C:\Users\golde\.pip-cache`.
- It mixes public claims, verification history, benchmark run details, expansion-phase notes, transfer packaging, and local workstation caveats.
- It references `docs/chat_handoff.md` as a recommended navigation target, which is useful for Codex continuity but confusing for outside readers.

Recommended rewrite:

- Lead with a concise project summary: 30-city 30 m urban heat hotspot dataset, public geospatial/remote-sensing inputs, within-city screening, city-held-out transfer, and supplemental spatial-alignment diagnostics.
- Add a plain `What is included` section:
  - Python source under `src/`
  - tests under `tests/`
  - report source under `docs/report/`
  - lightweight report tables/figures needed to render the final report, if intentionally tracked
  - configuration/reference files such as `cities.csv`, `requirements.txt`, and fold metadata if kept lightweight
- Add a `What is not included` section:
  - raw AppEEARS, DEM, NLCD, hydrography downloads
  - large processed parquet/GeoPackage outputs
  - most generated modeling prediction tables and run directories unless deliberately curated
  - local credentials, local virtual environments, and machine-specific caches
- Replace absolute interpreter commands with generic examples:
  - `python -m src.run_final_dataset_assembly`
  - `python -m src.make_model_folds --n-splits 5`
  - `python -m src.run_logistic_saga --sample-rows-per-city 5000`
- Explain that full regeneration requires external data acquisition and local compute, while report tables/figures depend on generated artifacts that may not all be committed.
- Move detailed phase histories and workstation-specific verification notes out of README into internal documentation or an archive.

Specific files to inspect or edit:

- `README.md`
- `docs/workflow.md`
- `docs/modeling_plan.md`
- `docs/data_dictionary.md`
- `docs/report/stat5630_final_report_draft.md`

## 2. Repository Navigation

Goal: make the top-level tree understandable without requiring Codex conversation history.

Findings:

- Current top-level folders are mostly understandable: `src/`, `tests/`, `docs/`, `outputs/`, `figures/`, and ignored `data_processed/`.
- `outputs/` currently has many tracked generated files. A `git ls-files` spot check found hundreds of tracked files under `outputs/`.
- `docs/report/` contains final report source and support files, but also critique, planning, visual QA, revision, archive, proposal, and assignment PDFs.
- `docs/presentation_2026/` is tracked and may be useful, but should be clearly labeled as presentation material rather than core reproducibility material.
- `src/_vendor_pptx/` appears to contain vendored package material. Confirm whether this is necessary, and if so document why.

Recommended navigation changes:

- Add short README files where outside readers will land:
  - `docs/README.md`: public documentation map, with internal/dev notes labeled separately
  - `docs/report/README.md`: how the report source, tables, figures, and rendered PDF relate
  - optionally `outputs/README.md`: explain which generated outputs are curated and which are normally untracked
- Keep top-level README focused and link to deeper docs instead of embedding every command and status note.
- Mark internal-only material clearly with names such as `docs/internal/` or `docs/archive/`.
- Consider moving report planning and QA notes into `docs/internal/report_development/` after final submission.

## 3. Internal Documentation Cleanup

Goal: separate public documentation from development continuity notes.

Recommended classification:

| Path | Current role | Recommendation |
| --- | --- | --- |
| `AGENTS.md` | Codex operating instructions | Keep if useful for agents, but mention in README only if necessary; otherwise treat as internal. |
| `docs/chat_handoff.md` | rolling Codex/project handoff | Move to `docs/internal/chat_handoff.md` or keep but remove from public README navigation. |
| `docs/report/final_report_planning.md` | report-development continuity | Move to `docs/internal/report_development/` after final report is submitted. |
| `docs/report/stat5630_revision_pass_notes.md` | report-development QA note | Move to internal/archive or delete after final submission if superseded. |
| `docs/report/stat5630_visual_qa_notes.md` | report-development QA note | Move to internal/archive or keep only if clearly labeled. |
| `docs/report/stat5630_draft_critical_review.md` | critique/development note | Move to internal/archive. |
| `docs/report/archive/` | report history | Keep only if useful, but label as archive and exclude from main README navigation. |
| `docs/presentation_2026/presentation_changelog.md` | presentation development log | Move to internal/archive or shorten if presentation source remains public. |
| `docs/spatial_alignment_design.md` | method design plus implementation prompt remnants | Rewrite as public method note or move prompt-like sections to internal notes. |

Do not delete these in the first polish pass unless they are clearly superseded and confirmed unnecessary.

## 4. `.gitignore` And Data Policy

Goal: make tracked versus untracked artifacts deliberate.

Current `.gitignore` strengths:

- Ignores Python caches, local virtual environments, repo-local scratch/cache folders, `.env`, `.env.local`, `data_raw/`, `data_processed/`, and top-level `figures/`.
- Keeps `docs/report/figures/` available for tracked report-ready images.
- Ignores selected generated presentation build outputs and oversized transfer-inference predictions.

Gaps and risks to audit:

- Many generated `outputs/` files are already tracked, so adding `outputs/` to `.gitignore` later will not remove existing tracked files.
- `docs/report/stat5630_final_report_draft.pdf` is tracked. Decide whether the rendered report PDF should remain tracked as a convenience artifact.
- `docs/report/tables/retained_model_run_metadata.csv` contains absolute local run paths. Either sanitize those fields or regenerate them as relative paths.
- `docs/report/` includes assignment/proposal PDFs and QA notes that may not belong in a public project repo.
- `src/_vendor_pptx/` is tracked and large/noisy. Confirm whether vendoring is intentional; if not, remove in a dedicated cleanup with dependency documentation.

Recommended policy:

- Track lightweight, source-like reproducibility files:
  - `cities.csv`
  - `requirements.txt`
  - source code and tests
  - report markdown
  - curated report tables and figures if needed to render the final report without full regeneration
  - small fold definitions or metadata only if lightweight and non-sensitive
- Do not track:
  - raw downloads
  - large processed parquet/GeoPackage outputs
  - full prediction tables
  - full modeling run directories
  - caches, local temp folders, virtual environments, local configs, and credentials
  - rendered drafts that are not final public deliverables
- Add a public `Data Availability` section explaining that source products are public but raw/processed bulk data are not necessarily included in GitHub.

## 5. Reproducibility Scope

Goal: state honestly what an outside reader can do from the repo as-is.

As-is likely reproducible:

- Inspect the workflow and modeling code.
- Run unit tests that use synthetic or small fixtures.
- Render the final report only if all referenced report figures/tables are tracked and the local Pandoc/XeLaTeX toolchain is installed.
- Recreate some report figures/tables only if the needed generated modeling/data artifacts are already present locally.

Requires external data downloads:

- Rebuilding city study-area inputs from public geospatial sources if cached files are absent.
- AppEEARS NDVI and ECOSTRESS acquisition.
- DEM, NLCD, imperviousness, and hydrography support-layer acquisition.

Requires generated artifacts not necessarily committed:

- `data_processed/final/final_dataset.parquet`
- per-city feature parquet/GeoPackage files
- modeling run directories with held-out predictions and calibration tables
- full-city spatial-alignment prediction tables
- most `outputs/modeling/` and `figures/modeling/` products

Recommended future command structure:

- Add a simple `Makefile`, `noxfile.py`, or `scripts/run_workflow.py` wrapper with high-level targets:
  - `make test`
  - `make report`
  - `make audit-final-dataset`
  - `make folds`
  - `make benchmark-smoke`
  - `make report-artifacts`
- Keep detailed CLI modules available, but make the README path much shorter.
- Use environment variables only for credentials. Document required AppEEARS variables without showing values.

## 6. Report/Repo Consistency

Goal: align terminology and artifact names across README, docs, scripts, and report.

Terms to standardize:

- `same-city screening`: within-city held-out/random split evaluation, easier and diagnostic
- `exact-cell city-held-out transfer`: the main benchmark, split by `city_id`
- `broad spatial placement`: spatial interpretation question
- `supplemental spatial-alignment diagnostic`: full eligible held-out city scoring for smoothed spatial analysis, not a replacement benchmark

Known consistency checks to run:

- Search for older phrases such as `cross-city benchmark`, `retained benchmark`, `transfer package`, and `within-city` and make sure each occurrence fits the report's current framing.
- Confirm model names match across README, report tables, and code:
  - logistic regression with SAGA
  - random forest
  - simple baselines
  - supplemental exploratory variants only when explicitly labeled
- Confirm report-facing figures/tables match generated filenames:
  - `docs/report/figures/benchmark_metrics.png`
  - `docs/report/figures/within_city_vs_transfer_results.png`
  - `docs/report/figures/city_signal_transfer_relationship_labeled.png`
  - `docs/report/figures/spatial_alignment_medium_summary.png`
  - `docs/report/figures/selected_spatial_alignment_map_contrast.png`
  - `docs/report/tables/*.csv`
- Flag any mismatch where the report says tables/figures are generated from the workflow but the repo lacks the command, artifact, or tracked support file needed to reproduce them.

## 7. Licensing And Citation

Goal: make reuse expectations clear without guessing.

Findings:

- No top-level `LICENSE` file was found in the inspected working tree.
- Dependency license files exist inside vendored package material under `src/_vendor_pptx/`, but these are not a project license.

Recommendations:

- Ask the project owner to choose a license before adding one. Common choices might include MIT/BSD-3-Clause for code, but the correct license depends on intended reuse and institutional/course constraints.
- Add a `Citation` section to `README.md` with:
  - the GitHub repository URL
  - report title and authors once final
  - a note that public source products should be cited separately
- Add high-level source-data citations or links aligned with report Table 1 and References:
  - U.S. Census urban areas
  - USGS 3DEP or DEM source used
  - NLCD land cover and impervious products
  - NHD or hydrography source used
  - MODIS/Terra MOD13A1.061 NDVI via AppEEARS
  - ECOSTRESS ECO_L2T_LSTE.002 LST via AppEEARS

## 8. Security, Privacy, And Local Path Cleanup

Goal: remove machine-specific assumptions and verify no secrets are tracked.

Findings from targeted search:

- Local path references appear in `README.md`, `AGENTS.md`, `docs/spatial_alignment_design.md`, `docs/presentation_2026/*`, `docs/report/final_report_planning.md`, `docs/report/stat5630_revision_pass_notes.md`, `docs/report/stat5630_visual_qa_notes.md`, and `docs/report/tables/retained_model_run_metadata.csv`.
- The current report draft no longer contains the local virtual environment path in the reproducibility note.
- `.env.local` exists in the working tree but is ignored by `.gitignore`. Confirm it is not tracked before sharing.
- Code appears to use environment-based AppEEARS credentials, but do a final secret scan before publication.

Recommended cleanup:

- Remove absolute local paths from public README and report-facing metadata.
- Keep local path guidance only in internal agent notes if needed.
- Replace absolute paths with generic `python -m ...` examples or `<repo-root>/...` placeholders.
- Run a final scan before publishing:
  - `rg -n "C:\\\\Users|OneDrive|\\.venvs|\\.tmp|\\.pip-cache|password|token|secret|api_key|apikey" README.md docs src tests`
  - `git ls-files .env .env.local`
  - inspect any matches manually rather than assuming they are harmless.

## 9. Prioritized Action List

### A. Must Fix Before Sharing Repo Link Confidently

1. Rewrite `README.md` for public readers.
   - Remove local Windows paths and long run-history sections.
   - Add `What is included`, `What is not included`, `Reproducibility scope`, and `Data availability` sections.
   - Proposed prompt: "Rewrite README.md as a concise public-facing project README aligned with docs/report/stat5630_final_report_draft.md. Remove local paths and Codex handoff language. Keep only honest reproducibility claims."

2. Sanitize local paths in report-facing artifacts.
   - Inspect `docs/report/tables/retained_model_run_metadata.csv` and regenerate or edit local run path fields into relative identifiers.
   - Proposed prompt: "Sanitize report-facing metadata tables so they contain no absolute local paths, then rerender docs/report/stat5630_final_report_draft.pdf and verify no path overflow."

3. Decide what to do with internal docs.
   - Remove `docs/chat_handoff.md` from public navigation immediately.
   - Move or clearly label `docs/report/*planning*`, `*notes*`, and critique files as internal/archive.
   - Proposed prompt: "Create docs/internal/ and move or relabel development-only documentation without deleting source report files. Update README and docs/README.md navigation accordingly."

4. Audit tracked generated outputs.
   - Inventory tracked `outputs/`, `figures/`, PDFs, and vendored package files.
   - Decide which small curated report artifacts should remain tracked.
   - Proposed prompt: "Audit tracked generated artifacts and propose a minimal keep/remove list for public GitHub. Do not delete yet; produce a file-level action table."

5. Run a secret/local path scan.
   - Confirm `.env.local` is ignored and untracked.
   - Search for tokens, credentials, usernames, OneDrive paths, and absolute Windows paths.
   - Proposed prompt: "Run a publication safety scan for local paths and credentials; fix public-facing occurrences and report any internal-only occurrences left intentionally."

### B. Should Fix For A Polished Public Repo

1. Add documentation landing pages.
   - Add `docs/README.md` and `docs/report/README.md`.
   - Proposed prompt: "Add short README files under docs/ and docs/report/ that explain public navigation and distinguish report artifacts from internal development notes."

2. Tighten `.gitignore` and data policy.
   - Add ignore patterns for future generated modeling outputs if the curated-artifact policy says they should not be tracked.
   - Remember that existing tracked files require `git rm --cached` in a deliberate cleanup pass.
   - Proposed prompt: "Update .gitignore and document the data/artifact tracking policy without removing tracked outputs yet."

3. Rewrite `docs/spatial_alignment_design.md` as either public methods documentation or an internal design memo.
   - Remove prompt-like instructions from public-facing sections.
   - Proposed prompt: "Split docs/spatial_alignment_design.md into a public method note and internal implementation notes, preserving the validated spatial-alignment contract."

4. Align terminology across docs.
   - Run terminology search and update old names that conflict with report language.
   - Proposed prompt: "Make README.md, docs/workflow.md, docs/modeling_plan.md, and docs/data_dictionary.md use the report's terms: same-city screening, exact-cell city-held-out transfer, broad spatial placement, supplemental spatial-alignment diagnostic."

5. Add citation guidance.
   - Add README citation section once final report author/title/license decisions are known.
   - Proposed prompt: "Add a README citation/data-source section aligned with Table 1 and the report references, without adding a project license."

### C. Nice To Have After Final Report Submission

1. Add a Makefile-style workflow.
   - Provide simple targets for tests, report render, report artifact generation, and smoke benchmark checks.
   - Proposed prompt: "Add a lightweight Makefile or Python workflow wrapper for test, report, audit, folds, and benchmark-smoke targets."

2. Reduce vendored dependency noise.
   - Confirm why `src/_vendor_pptx/` is tracked. Replace with normal dependency management if feasible.
   - Proposed prompt: "Audit src/_vendor_pptx and recommend whether it should remain vendored, move to a plugin/runtime dependency, or be removed from the public repo."

3. Create a compact public artifact manifest.
   - List which report figures/tables are tracked and which require regeneration.
   - Proposed prompt: "Create docs/artifact_manifest.md describing tracked lightweight report artifacts and untracked generated data/model artifacts."

4. Add continuous integration.
   - Run fast tests and markdown/link checks on push.
   - Proposed prompt: "Add a minimal GitHub Actions workflow for Python setup, focused pytest, and README/report link checks."
