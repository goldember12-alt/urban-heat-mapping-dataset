# Chat Handoff - Urban Heat Mapping Dataset Project

## Project Goal

Build a reproducible Python geospatial workflow to create a 30 m cell-level urban heat dataset for 30 U.S. cities across climate groups.

## What Is Completed

Implemented end-to-end pipeline components now include:

- Batch city boundary + study-area + grid runner (`src/batch_city_processing.py`, `src/run_city_batch_processing.py`).
- Generic raster alignment/extraction framework aligned to city master grids (`src/raster_features.py`).
- DEM extraction (aligned) in city feature assembly.
- NLCD extraction for `land_cover_class` + `impervious_pct` (aligned).
- Hydrography distance-to-water generation via rasterized water mask + distance transform (`src/water_features.py`).
- Per-city feature assembly outputs (`.gpkg` + `.parquet`) with intermediate unfiltered/filtered artifacts (`src/feature_assembly.py`).
- Final merged dataset assembly (`.parquet` + `.csv`) with enforced row rules and city-level `hotspot_10pct`.
- Full pipeline CLI orchestrator (`src/full_pipeline.py`, `src/run_full_pipeline.py`).
- Optional partial/debug mode for very large grids via `--max-cells`.
- AppEEARS acquisition stage:
  - AOI discovery/export from `data_processed/study_areas/*.gpkg` to `data_processed/appeears_aoi/*.geojson` in EPSG:4326 (`src/appeears_aoi.py`).
  - AppEEARS API client with env-only auth (`src/appeears_client.py`).
  - Resumable submit/poll/download orchestration with machine-readable per-city status summaries (`src/appeears_acquisition.py`).
  - Acquisition CLI entrypoint (`src/run_appeears_acquisition.py`).

## Testing Status

As of 2026-03-08:

- `44 passed` via:
  - `.venv\Scripts\python.exe -m pytest -q`

New tests added for acquisition stage:

- `tests/test_appeears_aoi.py`
- `tests/test_appeears_client.py`
- `tests/test_appeears_acquisition.py`

## Manual Verification Status

As of 2026-03-08:

Implemented and manually executed previously:

- Installed parquet engine dependency:
  - `.venv\Scripts\pip.exe install pyarrow`
- Validated stage-1 batch runner (single-city, coarse resolution, no-save):
  - `.venv\Scripts\python.exe -m src.run_city_batch_processing --city-ids 1 --no-save --stop-on-error --resolution 500 --timeout 60`
  - Output: `data_processed/batch_city_processing_summary_500m.csv` with `status=ok` for city 1.
- Ran partial end-to-end pipeline (existing grid only, capped cells):
  - `.venv\Scripts\python.exe -m src.run_full_pipeline --skip-city-processing --existing-grids-only --city-ids 1 --max-cells 5000`
- Verified produced artifacts:
  - `data_processed/city_features/01_phoenix_az_features.gpkg`
  - `data_processed/city_features/01_phoenix_az_features.parquet`
  - `data_processed/city_features/feature_extraction_summary_30m.csv`
  - `data_processed/intermediate/city_features/01_phoenix_az_features_unfiltered.parquet`
  - `data_processed/intermediate/city_features/01_phoenix_az_features_filtered.parquet`
  - `data_processed/final/final_dataset.parquet`
  - `data_processed/final/final_dataset.csv`

New acquisition stage manual verification in this session:

- Test-verified only (no live AppEEARS API run performed in this sandboxed session).
- Not manually verified against real AppEEARS task submission/download yet.

## Immediate Next Step

Set AppEEARS credentials in environment variables and run one live city acquisition per product to verify real API submission/poll/download and raw file placement.

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

Current verified final output files exist:

- `data_processed/final/final_dataset.parquet` (partial run; 5000 Phoenix cells)
- `data_processed/final/final_dataset.csv` (partial run; 5000 Phoenix cells)

## Not Started Yet / Open Issues

- Live AppEEARS API interaction (auth + submit + poll + download) has not been manually run in this session.
- Real NDVI and ECOSTRESS acquisition completeness for all 30 cities remains pending.
- Full 30-city end-to-end run at 30 m remains pending data availability and runtime.

## Checkpoint Log

### 2026-03-08 - Milestone: AppEEARS Date Format Fix

- Change made:
  - Kept CLI date input contract as `YYYY-MM-DD`.
  - Updated AppEEARS payload date formatting to submit `MM-DD-YYYY` in `build_area_task_payload`.
  - Added tests confirming conversion behavior and rejection of `MM-DD-YYYY` CLI input.
- Files touched:
  - `src/appeears_client.py`
  - `tests/test_appeears_client.py`
  - `docs/chat_handoff.md`
- How to run:
  - `.venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ndvi --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31 --submit-only`
- Test status:
  - `44 passed` (`pytest -q`).
- Manual verification status:
  - Date-format behavior verified by tests; live AppEEARS submission response not manually verified in this session.
- Next recommended step:
  - Re-run Phoenix NDVI `--submit-only` request and confirm AppEEARS accepts payload date format.
### 2026-03-08 - Milestone: AppEEARS Submission Error Reporting Hardened

- Change made:
  - Improved AppEEARS `POST /task` failure reporting in the client to include HTTP status code, parsed AppEEARS error message/body, and submission context (`city_id`, `product`).
  - Added explicit error logging for failed task submission without exposing secrets.
  - Added client test coverage for failed task submission error content.
- Files touched:
  - `src/appeears_client.py`
  - `tests/test_appeears_client.py`
  - `docs/chat_handoff.md`
- How to run:
  - `.venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ndvi --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31 --submit-only`
- Test status:
  - `43 passed` (`pytest -q`).
- Manual verification status:
  - Error reporting behavior verified by tests; live AppEEARS API failure response not manually exercised in this session.
- Next recommended step:
  - Re-run one-city NDVI submit with `--submit-only` and confirm surfaced CLI error includes status/body/city/product if AppEEARS rejects the request.
### 2026-03-08 - Milestone: AppEEARS Acquisition Stage (Implemented)

- Change made:
  - Added AOI export stage from study areas and AppEEARS acquisition automation with resumable status handling.
  - Added support for NDVI and ECOSTRESS product-type runs with defaults/fallback candidates.
  - Added submit-only, poll-only, download-only, and retry-incomplete run modes.
  - Added machine-readable per-city acquisition summary outputs (JSON + CSV).
- Files touched:
  - `src/config.py`
  - `src/appeears_aoi.py`
  - `src/appeears_client.py`
  - `src/appeears_acquisition.py`
  - `src/run_appeears_acquisition.py`
  - `tests/test_appeears_aoi.py`
  - `tests/test_appeears_client.py`
  - `tests/test_appeears_acquisition.py`
  - `README.md`
  - `docs/workflow.md`
  - `docs/data_dictionary.md`
  - `docs/chat_handoff.md`
- How to run:
  - `.venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ndvi --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31`
  - `.venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ecostress --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31`
  - `.venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ndvi --start-date 2023-05-01 --end-date 2023-08-31 --retry-incomplete`
- Test status:
  - `43 passed` (`pytest -q`).
- Manual verification status:
  - Implemented + test-verified; live AppEEARS API behavior not manually verified in this session.
- Next recommended step:
  - Run one-city live AppEEARS submit/poll/download for NDVI and ECOSTRESS with valid environment credentials, then verify summary statuses and raw download folders.

### 2026-03-08 - Milestone: Alignment + Core Feature Stages

- Change made:
  - Implemented generic raster alignment + integrated DEM/NLCD/hydro distance stages into city feature assembly.
- Files touched:
  - `src/raster_features.py`
  - `src/water_features.py`
  - `src/feature_assembly.py`
  - `src/run_city_features_batch.py`
  - `tests/test_raster_features.py`
  - `tests/test_water_features.py`
  - `tests/test_feature_assembly.py`
  - `requirements.txt`
- How to run:
  - `.venv\Scripts\python.exe -m src.run_city_features_batch --existing-grids-only --city-ids 1 --max-cells 5000`
- Test status:
  - Initially 1 failing test, then fixed and passing in later checkpoint.
- Manual verification status:
  - Implementation verified by tests; real extraction pending due missing parquet engine at that time.
- Next recommended step:
  - Install parquet engine and execute pipeline.

### 2026-03-08 - Milestone: Full Pipeline CLI + Partial End-to-End Output

- Change made:
  - Added full pipeline orchestrator and partial-run support (`--max-cells`), installed `pyarrow`, and produced real per-city/final outputs.
- Files touched:
  - `src/full_pipeline.py`
  - `src/run_full_pipeline.py`
  - `src/run_city_features.py`
  - `src/run_city_features_batch.py`
  - `README.md`
  - `docs/workflow.md`
  - `docs/data_dictionary.md`
  - `docs/chat_handoff.md`
- How to run:
  - `.venv\Scripts\python.exe -m src.run_full_pipeline --skip-city-processing --existing-grids-only --city-ids 1 --max-cells 5000`
- Test status:
  - `37 passed` (`pytest -q`) at that checkpoint.
- Manual verification status:
  - Partial dataset artifacts produced and file existence verified.
- Next recommended step:
  - Run full 30-city extraction with real raw raster inputs and without `--max-cells`.

### 2026-03-08 - Milestone: Stage-1 Batch Runner Validation

- Change made:
  - Executed batch stage-1 runner manually for one city to verify operational status after integration.
- Files touched:
  - `docs/chat_handoff.md`
- How to run:
  - `.venv\Scripts\python.exe -m src.run_city_batch_processing --city-ids 1 --no-save --stop-on-error --resolution 500 --timeout 60`
- Test status:
  - No additional code tests required for this checkpoint.
- Manual verification status:
  - Command completed successfully with `status=ok` summary output.
- Next recommended step:
  - Execute stage-1 batch run for all cities at target settings when full compute/network run is intended.


