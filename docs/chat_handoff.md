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
  - Feature source discovery scans `data_raw/ndvi/<city_slug>/` and `data_raw/ecostress/<city_slug>/` recursively and selects science layers only (`_NDVI_` for NDVI, `_LST_` for ECOSTRESS) with legacy top-level fallback (`src/feature_assembly.py`).
- Phoenix support-layer discovery crash recovery update:
  - Feature source discovery now checks city-specific recursive folders for DEM, NLCD, and hydro sources (`data_raw/dem/<city_slug>/`, `data_raw/nlcd/<city_slug>/`, `data_raw/hydro/<city_slug>/`) before top-level fallback (`src/feature_assembly.py`).
  - Focused regression test added for recursive city-folder DEM/NLCD/hydro discovery (`tests/test_feature_assembly.py`).
- NDVI/LST normalization update:
  - Sampling pipeline now supports per-layer normalization rules (scale factor, offset, valid-range masking).
  - Phoenix run uses NDVI normalization (`scale_factor=0.0001`, valid range `[-0.2, 1.0]`) and LST normalization (`scale_factor=1`, units Kelvin).

## Testing Status

As of 2026-03-08:

- `49 passed` via:
  - `.venv\Scripts\python.exe -m pytest -q`

- `5 passed` via:
  - `.venv\Scripts\python.exe -m pytest tests/test_feature_assembly.py -q`

Focused tests relevant to AppEEARS ingestion and normalization:

- `tests/test_feature_assembly.py::test_discover_default_feature_sources_uses_city_appeears_layer_files`
- `tests/test_feature_assembly.py::test_discover_default_feature_sources_falls_back_to_top_level_when_city_folder_missing`
- `tests/test_feature_assembly.py::test_discover_default_feature_sources_uses_city_recursive_dem_nlcd_hydro`
- `tests/test_raster_features.py::test_sample_median_from_raster_stack_applies_normalization_and_valid_range`

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

New manual verification in this session (normalization + uncapped Phoenix run):

- Verified NDVI and LST scaling metadata from real Phoenix source files:
  - NDVI TIFF (`MOD13A1...NDVI...tif`): `dtype=int16`, `nodata=-3000`, dataset tags include `scale_factor=0.0001`, `add_offset=0.0`.
  - LST TIFF (`ECO_L2T_LSTE...LST...tif`): `dtype=float32`, `nodata=NaN`, dataset tags include `scale_factor=1`, `add_offset=0`, `units=Kelvin`.
- Verified authoritative AppEEARS product metadata (`/api/product/<product>`):
  - `MOD13A1.061` `_500m_16_days_NDVI`: `ScaleFactor=0.0001`, `ValidMin=-0.2`, `ValidMax=1.0`, `FillValue=-3000`.
  - `ECO_L2T_LSTE.002` `LST`: `ScaleFactor=1`, `Units=Kelvin`, `FillValue=NaN`.
- Ran uncapped one-city extraction with existing CLI and real AppEEARS files:
  - `.venv\Scripts\python.exe -m src.run_city_features --city-id 1`
  - CLI result: `rows=4742866`; `blocked_stages=dem;hydro_distance;nlcd_impervious;nlcd_land_cover`; dropped `763` rows with `<3` ECOSTRESS passes.
- Verified Phoenix per-city normalized output in `data_processed/city_features/01_phoenix_az_features.parquet`:
  - NDVI min/median/max: `0.0254 / 0.1960 / 0.7368`
  - LST min/median/max (Kelvin): `302.49 / 315.25 / 330.35`
  - Non-null counts:
    - `ndvi_median_may_aug`: `4,742,842`
    - `lst_median_may_aug`: `4,742,866`
    - `n_valid_ecostress_passes`: `4,742,866`


New manual verification in this recovery session (Phoenix support-layer unblock):

- Verified local raw support-layer presence for Phoenix:
  - `data_raw/dem/phoenix/phoenix_dem_3dep_30m.tif`
  - `data_raw/nlcd/phoenix/phoenix_nlcd_2021_impervious_30m.tif`
  - `data_raw/nlcd/phoenix/phoenix_nlcd_2021_land_cover_30m.tif`
  - `data_raw/hydro/phoenix/phoenix_nhdplus_water.gpkg`
- Re-ran uncapped Phoenix extraction:
  - `.venv\Scripts\python.exe -m src.run_city_features --city-id 1`
  - Run failed before final summary with NumPy memory error in `sample_median_from_raster_stack` during LST median (`Unable to allocate 2.16 GiB`).
- Re-ran capped Phoenix extraction for stage verification:
  - `.venv\Scripts\python.exe -m src.run_city_features --city-id 1 --max-cells 1000`
  - CLI result: `rows=993`; `blocked_stages=` (empty), confirming `dem`, `hydro_distance`, `nlcd_impervious`, and `nlcd_land_cover` are no longer blocked.
## Immediate Next Step

Address uncapped Phoenix memory pressure in LST median stack processing (chunking/streaming or other minimal memory fix), then rerun uncapped city extraction and confirm full-run stage summary remains unblocked.

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

- Phoenix support-layer block is resolved in capped live run (`blocked_stages` empty), but uncapped Phoenix extraction currently fails with NumPy memory allocation during LST median calculation.
- ECOSTRESS LST currently uses product-provided LST layer without additional cloud/QC masking in feature assembly; if stricter quality filtering is required, that policy is still open.
- Real NDVI and ECOSTRESS acquisition completeness for all 30 cities remains pending.
- Full 30-city end-to-end run at 30 m remains pending data availability and runtime.

## Checkpoint Log

### 2026-03-08 - Checkpoint: Crash-Recovery Commit Validated for Phoenix Support-Layer Discovery

- Date / checkpoint:
  - 2026-03-08 commit `97b3007` recovery verification.
- Change made:
  - Recovered commit includes city-recursive DEM/NLCD/hydro source discovery plus focused test coverage.
  - No additional code changes were required to resolve the previously blocked support-layer stages.
- Files touched:
  - `docs/chat_handoff.md`
- How to run:
  - `.venv\Scripts\python.exe -m pytest tests/test_feature_assembly.py -q`
  - `.venv\Scripts\python.exe -m src.run_city_features --city-id 1 --max-cells 1000`
- Test status:
  - `5 passed` in `tests/test_feature_assembly.py`.
- Manual verification status:
  - Phoenix capped extraction completed with `blocked_stages=` (empty), confirming support-layer unblock for `dem`, `hydro_distance`, `nlcd_impervious`, and `nlcd_land_cover`.
  - Uncapped extraction still fails due memory allocation in LST median computation.
- Next recommended step:
  - Implement minimal memory-safe median strategy for uncapped LST stack processing and verify with uncapped Phoenix rerun.

### 2026-03-08 - Milestone: NDVI/LST Normalization Verified and Uncapped Phoenix Run Completed

- Date / checkpoint:
  - 2026-03-08 normalization verification + uncapped Phoenix extraction.
- Change made:
  - Added normalization support in raster stack sampling (scale factor, offset, valid-range masking).
  - Applied NDVI normalization rules (`0.0001`, valid `[-0.2, 1.0]`) and LST normalization rules (`1.0`, Kelvin) in city feature assembly.
  - Added focused normalization test coverage.
- Files touched:
  - `src/raster_features.py`
  - `src/feature_assembly.py`
  - `tests/test_raster_features.py`
  - `docs/chat_handoff.md`
- How to run:
  - `.venv\Scripts\python.exe -m src.run_city_features --city-id 1`
- Test status:
  - `49 passed` (`pytest -q`).
- Manual verification status:
  - Scale/unit/fill rules verified from source TIFF metadata and AppEEARS product metadata endpoints.
  - Uncapped Phoenix extraction completed and output sanity checked (NDVI/LST ranges and ECOSTRESS pass counts).
- Next recommended step:
  - Decide and implement ECOSTRESS cloud/QC masking policy before multi-city production runs.
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






