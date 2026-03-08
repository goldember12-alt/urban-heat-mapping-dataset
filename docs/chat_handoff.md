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
- AppEEARS-to-feature ingestion update:
  - Feature source discovery now scans `data_raw/ndvi/<city_slug>/` and `data_raw/ecostress/<city_slug>/` recursively and selects science layers only (`_NDVI_` for NDVI, `_LST_` for ECOSTRESS) with legacy top-level fallback (`src/feature_assembly.py`).

## Testing Status

As of 2026-03-08:

- `48 passed` via:
  - `.venv\Scripts\python.exe -m pytest -q`

Focused ingestion/file-selection tests now include:

- `tests/test_feature_assembly.py::test_discover_default_feature_sources_uses_city_appeears_layer_files`
- `tests/test_feature_assembly.py::test_discover_default_feature_sources_falls_back_to_top_level_when_city_folder_missing`

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

New manual verification in this session (real Phoenix AppEEARS raw downloads wired into feature extraction):

- Confirmed discovered feature inputs for Phoenix (`city_id=1`) from raw AppEEARS directories:
  - `ndvi_count=9` files from `data_raw/ndvi/phoenix/...*_NDVI_*.tif`
  - `lst_count=61` files from `data_raw/ecostress/phoenix/...*_LST_*.tif`
- Ran one-city extraction with existing CLI and real AppEEARS files:
  - `.venv\Scripts\python.exe -m src.run_city_features --city-id 1 --max-cells 1000`
  - CLI result: `rows=998`; `blocked_stages=dem;hydro_distance;nlcd_impervious;nlcd_land_cover`
- Verified Phoenix per-city output columns are populated in `data_processed/city_features/01_phoenix_az_features.parquet`:
  - `ndvi_median_may_aug`: 998 non-null
  - `lst_median_may_aug`: 998 non-null
  - `n_valid_ecostress_passes`: 998 non-null
  - `n_valid_ecostress_passes` range: 34 to 37

## Immediate Next Step

Validate and apply scale-factor/units normalization for AppEEARS NDVI and ECOSTRESS LST values before broader multi-city runs, then rerun Phoenix without `--max-cells`.

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

- NDVI values in Phoenix output currently appear unscaled raw integer-like magnitudes (example range observed: ~1823 to ~2385), so NDVI scaling/normalization still needs explicit handling verification.
- DEM/NLCD/hydro feature stages remain blocked for this run due missing corresponding raw inputs in local folders.
- Real NDVI and ECOSTRESS acquisition completeness for all 30 cities remains pending.
- Full 30-city end-to-end run at 30 m remains pending data availability and runtime.

## Checkpoint Log

### 2026-03-08 - Milestone: Phoenix Real AppEEARS Downloads Wired Into Feature Extraction

- Change made:
  - Updated feature-source discovery to use city-specific recursive AppEEARS folders for NDVI and ECOSTRESS and select only science layers (`_NDVI_`, `_LST_`).
  - Kept fallback to legacy top-level raster discovery if city-specific folders are absent.
  - Added focused tests for ingestion/file-selection behavior.
- Files touched:
  - `src/feature_assembly.py`
  - `tests/test_feature_assembly.py`
  - `docs/chat_handoff.md`
- How to run:
  - `.venv\Scripts\python.exe -m src.run_city_features --city-id 1 --max-cells 1000`
- Test status:
  - `48 passed` (`pytest -q`).
- Manual verification status:
  - Real Phoenix AppEEARS NDVI and ECOSTRESS files were discovered and consumed in one-city extraction.
  - Output columns `ndvi_median_may_aug`, `lst_median_may_aug`, and `n_valid_ecostress_passes` were confirmed non-null for all 998 retained rows in the capped run.
- Next recommended step:
  - Confirm and implement NDVI/LST unit scaling rules, then run uncapped Phoenix extraction and check summary distribution sanity.
### 2026-03-08 - Milestone: ECOSTRESS Product/Layer Defaults Corrected via Live AppEEARS Metadata

- Live issue observed:
  - Real AppEEARS submit rejected prior defaults with:
  - `Product ECO_L2G_LSTE.002 is not available`
  - `Product ECO_L2G_LSTE.001 is not available`
- Metadata query result (live AppEEARS API):
  - Product catalog endpoint (`/api/product`) shows available ECOSTRESS LST products include:
  - `ECO_L2T_LSTE.002` (Available=true)
  - `ECO_L2_LSTE.002` (Available=true)
  - Product-layer endpoint (`/api/product/<product_id>`) shows selectable `LST` layer is available for both products.
- Change made:
  - Updated ECOSTRESS fallback/default product candidates in config from unavailable `ECO_L2G_*` ids to:
  - `("ECO_L2T_LSTE.002", "ECO_L2_LSTE.002")`
  - Kept ECOSTRESS default layer as `LST` (validated selectable in live metadata).
  - Added/updated tests to ensure default ECOSTRESS payload uses verified selectable product/layer.
- Files touched:
  - `src/config.py`
  - `tests/test_appeears_acquisition.py`
  - `docs/chat_handoff.md`
- How to rerun Phoenix ECOSTRESS submit-only:
  - `.venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ecostress --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31 --submit-only`
- Test status:
  - `46 passed` (`pytest -q`).
- Manual verification status:
  - ECOSTRESS product/layer availability verified via live metadata endpoints; rerun submission pending in this session.
- Next recommended step:
  - Execute the Phoenix ECOSTRESS submit-only command above and confirm task submission succeeds.
### 2026-03-08 - Milestone: NDVI Layer Selection Corrected for AppEEARS

- Change made:
  - Queried live AppEEARS product metadata for `MOD13A1.061` and confirmed selectable NDVI layer name is `_500m_16_days_NDVI`.
  - Updated NDVI default layer config to `_500m_16_days_NDVI`.
  - Added test coverage to verify default NDVI spec/payload uses the corrected layer.
- Files touched:
  - `src/config.py`
  - `tests/test_appeears_acquisition.py`
  - `docs/chat_handoff.md`
- How to run:
  - `.venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ndvi --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31 --submit-only`
- Test status:
  - `45 passed` (`pytest -q`).
- Manual verification status:
  - Layer availability verified by live metadata query; live submit response not manually verified in this session.
- Next recommended step:
  - Re-run Phoenix NDVI submit-only and confirm task submission succeeds with updated default layer.
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





