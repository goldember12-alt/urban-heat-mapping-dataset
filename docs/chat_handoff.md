# Chat Handoff - Urban Heat Mapping Dataset Project

## Project Goal

Build a reproducible Python geospatial workflow to create a 30 m cell-level urban heat dataset for 30 U.S. cities across climate groups.

## What Is Completed

Implemented in code:

- Boundary, study-area, and 30 m grid processing for the 30-city city list.
- Raster alignment, DEM, NLCD, hydro distance, city feature assembly, and final dataset assembly.
- AppEEARS AOI export from buffered study areas.
- AppEEARS API client with environment-only authentication.
- Resumable AppEEARS acquisition runner for NDVI and ECOSTRESS (`submit`, `poll`, `download`, `retry-incomplete`).
- Deterministic AppEEARS preflight/audit path that computes expected per-city study area, AOI, raw download, and status-summary paths; validates AOI CRS; and writes machine-readable preflight outputs.
- CLI support for `--preflight-only` without breaking existing acquisition modes.

Standardization status:

- AppEEARS acquisition code is standardized for all 30 cities in code.
- The current blocker is not missing acquisition logic.
- The current blocker is missing materialized prerequisites on disk for 29 cities.

## Testing Status

As of 2026-03-08:

- `56 passed` via:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m pytest -q"`

Test-verified in this checkpoint:

- all-city batch preflight path uses the full 30-city list when `--city-ids` is omitted
- missing-prerequisite handling reports blocked rows deterministically
- AOI CRS validation marks non-EPSG:4326 AOIs as not ready
- preflight JSON/CSV outputs contain the expected fields and paths
- `run_appeears_acquisition(..., preflight_only=True)` returns preflight artifacts cleanly

## Manual Verification Status

Implemented:

- Preflight/audit logic exists in `src/appeears_acquisition.py` and is wired into `src/run_appeears_acquisition.py`.

Test-verified:

- The new preflight logic and CLI path are covered by `tests/test_appeears_acquisition.py` and included in the `56 passed` full-suite result.

Manually verified:

- Ran the real workspace CLI preflight for NDVI:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ndvi --preflight-only"`
- Observed output:
  - `data_processed/appeears_status/appeears_ndvi_preflight_summary.json`
  - `data_processed/appeears_status/appeears_ndvi_preflight_summary.csv`
  - readiness counts: `False=29`, `True=1`
- Inspected the written preflight CSV and confirmed:
  - Phoenix (`city_id=1`) is the only ready city
  - the other 29 cities are blocked with `blocking_reason=study_area_missing`

Currently materialized on disk:

- `data_processed/study_areas/`: Phoenix only
- `data_processed/appeears_aoi/`: Phoenix only
- `data_raw/ndvi/`: Phoenix only
- `data_raw/ecostress/`: Phoenix only
- `data_processed/appeears_status/`: Phoenix acquisition summaries plus the new NDVI preflight summary

Explicit blocker statement:

- Yes: the current real blocker for all-30-city AppEEARS acquisition is missing study areas, and therefore missing AOIs, for 29 cities.

## Immediate Next Step

Materialize the missing 29 study areas with the existing city-processing workflow, rerun AppEEARS preflight, then export the newly ready AOIs and begin all-city AppEEARS submit-only runs.

## Current Output Structure

- `data_processed/study_areas/`
- `data_processed/city_grids/`
- `data_processed/appeears_aoi/`
- `data_processed/appeears_status/`
- `data_processed/intermediate/aligned_rasters/`
- `data_processed/intermediate/city_features/`
- `data_processed/city_features/`
- `data_processed/final/`
- `data_raw/ndvi/<city_slug>/`
- `data_raw/ecostress/<city_slug>/`

Current materialized AppEEARS-related outputs:

- `data_processed/appeears_status/appeears_ndvi_preflight_summary.json`
- `data_processed/appeears_status/appeears_ndvi_preflight_summary.csv`
- `data_processed/appeears_status/appeears_ndvi_acquisition_summary.json`
- `data_processed/appeears_status/appeears_ndvi_acquisition_summary.csv`
- `data_processed/appeears_status/appeears_ecostress_acquisition_summary.json`
- `data_processed/appeears_status/appeears_ecostress_acquisition_summary.csv`
- Phoenix study area, AOI, NDVI raw folder, and ECOSTRESS raw folder

## Not Started Yet / Open Issues

- Study areas are not yet materialized for 29 cities.
- Because study areas are missing for 29 cities, AOIs are also not yet materialized for those cities.
- Full all-city AppEEARS acquisition has not started beyond Phoenix-ready assets.
- Real NDVI and ECOSTRESS acquisition completeness for all 30 cities remains pending.
- Additional uncapped city-by-city feature validation beyond Phoenix is still pending.
- Full 30-city end-to-end dataset generation at 30 m remains pending data availability and runtime.

## Checkpoint Log

### 2026-03-08 - Checkpoint: AppEEARS Preflight Standardization Added

- Date / checkpoint:
  - 2026-03-08 AppEEARS readiness standardization and disk-state audit.
- Change made:
  - Added deterministic AppEEARS preflight/audit logic and CLI support for `--preflight-only`.
  - Added tests for all-city preflight coverage, missing-prerequisite handling, AOI CRS validation, and audit artifact correctness.
  - Updated acquisition summaries to use deterministic current workspace paths instead of carrying forward stale prior-run path values.
- Files touched:
  - `src/appeears_acquisition.py`
  - `src/run_appeears_acquisition.py`
  - `tests/test_appeears_acquisition.py`
  - `README.md`
  - `docs/workflow.md`
  - `docs/data_dictionary.md`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ndvi --preflight-only"`
- Test status:
  - `56 passed` (`pytest -q`).
- Manual verification status:
  - Real workspace preflight produced `1 ready / 29 blocked`.
  - All 29 blocked rows were `study_area_missing`.
  - Phoenix is the only currently materialized ready city for AppEEARS prerequisites in this workspace.
- Next recommended step:
  - Run the existing city-processing batch to generate the remaining 29 study areas, then rerun preflight and proceed to all-city AppEEARS submit-only acquisition.
