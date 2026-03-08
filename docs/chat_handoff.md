# Chat Handoff - Urban Heat Mapping Dataset Project

## Project Goal

Build a reproducible Python geospatial workflow to create a 30 m cell-level urban heat dataset for 30 U.S. cities across climate groups.

## What Is Completed

Implemented in code:

- Boundary, study-area, and 30 m grid processing for the 30-city city list.
- Batch city-processing runner for one city or all configured cities.
- Raster alignment, DEM, NLCD, hydro distance, city feature assembly, and final dataset assembly.
- AppEEARS AOI export from buffered study areas.
- AppEEARS API client with environment-only authentication.
- Resumable AppEEARS acquisition runner for NDVI and ECOSTRESS (`submit`, `poll`, `download`, `retry-incomplete`).
- Deterministic AppEEARS preflight/audit path that computes expected per-city study area, AOI, raw download, and status-summary paths; validates AOI CRS; and writes machine-readable preflight outputs.
- Deterministic support-layer preflight/audit path for DEM, NLCD land cover, NLCD impervious, and hydro inputs.
- Deterministic support-layer prep runner that clips standardized city-specific raw support files into `data_processed/support_layers/<city_stem>/`.
- Feature-source discovery now prefers prepared support-layer outputs and otherwise preserves the prior raw-folder fallback behavior.
- Documentation now makes the workflow from an empty city to a support-layer-ready city explicit, including what remains automated vs manual.

Standardization status:

- Study-area and 30 m grid generation are already standardized for one-city and all-city execution.
- AppEEARS acquisition is standardized in code for all 30 cities.
- Support-layer acquisition/prep is standardized in code around deterministic per-city raw-input paths plus deterministic prepared outputs.
- The current remaining blocker for all-city support-layer prep is now raw DEM/NLCD/hydro population for 29 cities, not missing study areas or grids.

## Testing Status

As of 2026-03-08:

- `63 passed` via:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m pytest -q"`

Test-verified in the latest checkpoint:

- `process_all_cities(...)` uses the full 30-city list when `city_ids` is omitted
- `process_all_cities(...)` honors explicit city subsets
- all-city support-layer preflight path uses the full 30-city list when `--city-ids` is omitted
- deterministic expected DEM/NLCD/hydro raw paths are emitted correctly
- missing-prerequisite handling reports blocked rows deterministically
- city-specific raw-folder recursive discovery assumptions are codified and tested
- support-layer prep writes deterministic prepared outputs from standardized raw inputs
- feature discovery prefers prepared support outputs without breaking raw fallback behavior

## Manual Verification Status

Implemented:

- `src.run_city_processing` and `src.run_city_batch_processing` generate study areas and 30 m grids.
- `src.run_support_layers --preflight-only` serves as the deterministic prerequisite audit for support-layer readiness.
- `src.run_support_layers` performs deterministic support-layer prep once raw support inputs exist.

Test-verified:

- Batch city-processing coverage is now included in `tests/test_batch_city_processing.py`.
- Support-layer audit, prep, and prepared-output discovery are covered by `tests/test_support_layers.py`.
- The latest full-suite result is `63 passed`.

Manually verified:

- Ran the real all-city boundary/grid batch:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_city_batch_processing --resolution 30"`
- Observed output:
  - `data_processed/batch_city_processing_summary_30m.csv`
  - status counts: `ok=30`
- Ran the real workspace support-layer preflight after all-city boundary/grid generation:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_support_layers --preflight-only"`
- Observed output:
  - `data_processed/support_layers/support_layers_preflight_summary.json`
  - `data_processed/support_layers/support_layers_preflight_summary.csv`
  - readiness counts: `True/True=1`, `False/False=29`
  - the 29 blocked rows now share `prep_blocking_reasons=dem_source_missing;nlcd_land_cover_source_missing;nlcd_impervious_source_missing;hydro_source_missing`
- Ran the real workspace support-layer prep CLI for Phoenix:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_support_layers --city-ids 1"`
- Observed output:
  - `data_processed/support_layers/support_layers_prep_summary.json`
  - `data_processed/support_layers/support_layers_prep_summary.csv`
  - Phoenix prep summary status: `completed`
- Reran the real workspace AppEEARS NDVI preflight after all-city boundary/grid generation:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_appeears_acquisition --product-type ndvi --preflight-only"`
- Observed output:
  - `data_processed/appeears_status/appeears_ndvi_preflight_summary.json`
  - `data_processed/appeears_status/appeears_ndvi_preflight_summary.csv`
  - readiness counts: `True=1`, `False=29`
  - the 29 blocked rows now share `blocking_reason=aoi_missing`

Currently materialized on disk:

- `data_processed/study_areas/`: all 30 cities
- `data_processed/city_grids/`: all 30 cities at 30 m
- `data_processed/batch_city_processing_summary_30m.csv`
- `data_processed/appeears_aoi/`: Phoenix only
- `data_raw/dem/`: Phoenix only
- `data_raw/nlcd/`: Phoenix only
- `data_raw/hydro/`: Phoenix only
- `data_raw/ndvi/`: Phoenix only
- `data_raw/ecostress/`: Phoenix only
- `data_processed/support_layers/`:
  - `support_layers_preflight_summary.json`
  - `support_layers_preflight_summary.csv`
  - `support_layers_prep_summary.json`
  - `support_layers_prep_summary.csv`
  - `01_phoenix_az/dem_prepared.tif`
  - `01_phoenix_az/nlcd_land_cover_prepared.tif`
  - `01_phoenix_az/nlcd_impervious_prepared.tif`
  - `01_phoenix_az/hydro_water_prepared.gpkg`
- `data_processed/appeears_status/`:
  - `appeears_ndvi_preflight_summary.json`
  - `appeears_ndvi_preflight_summary.csv`
  - Phoenix acquisition summaries for NDVI and ECOSTRESS

Explicit blocker statement:

- Yes: the current real blocker for all-30-city support-layer prep is missing standardized raw DEM/NLCD/hydro inputs for 29 cities.
- Yes: the current real blocker for all-30-city AppEEARS acquisition is now missing AOIs for 29 cities, not missing study areas.

## Immediate Next Step

Populate the standardized per-city raw DEM, NLCD land-cover, NLCD impervious, and hydro files for the remaining 29 cities, rerun `src.run_support_layers --preflight-only`, and then run all-city support-layer prep.

## Current Output Structure

- `data_processed/study_areas/`
- `data_processed/city_grids/`
- `data_processed/appeears_aoi/`
- `data_processed/appeears_status/`
- `data_processed/support_layers/`
- `data_processed/intermediate/aligned_rasters/`
- `data_processed/intermediate/city_features/`
- `data_processed/city_features/`
- `data_processed/final/`
- `data_raw/dem/<city_slug>/`
- `data_raw/nlcd/<city_slug>/`
- `data_raw/hydro/<city_slug>/`
- `data_raw/ndvi/<city_slug>/`
- `data_raw/ecostress/<city_slug>/`

## Not Started Yet / Open Issues

- Standardized DEM raw folders are not yet populated for 29 cities.
- Standardized NLCD raw folders are not yet populated for 29 cities.
- Standardized hydro raw folders are not yet populated for 29 cities.
- Full support-layer prep has not yet been materialized beyond Phoenix.
- AOIs are still only materialized for Phoenix.
- Full all-city AppEEARS acquisition has not started beyond Phoenix-ready assets.
- Additional uncapped city-by-city feature validation beyond Phoenix is still pending.
- Full 30-city end-to-end dataset generation at 30 m remains pending data availability and runtime.

## Checkpoint Log

### 2026-03-08 - Checkpoint: All-City Study Areas And 30 m Grids Materialized

- Date / checkpoint:
  - 2026-03-08 prerequisite materialization and blocker refresh.
- Change made:
  - Verified that the existing batch city-processing workflow already supports all 30 cities when `--city-ids` is omitted.
  - Materialized all 30 study areas and all 30 city grids at 30 m using the existing batch runner.
  - Added tests that lock in all-city default behavior and subset behavior for batch city processing.
  - Updated docs to make the empty-city-to-support-layer-ready workflow explicit and to distinguish automated vs manual support-input population.
  - Refreshed support-layer preflight and AppEEARS preflight to update the real current blockers.
- Files touched:
  - `README.md`
  - `docs/workflow.md`
  - `docs/chat_handoff.md`
  - `tests/test_batch_city_processing.py`
  - `tests/test_feature_assembly.py`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_city_processing --city-id 1 --resolution 30"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_city_batch_processing --resolution 30"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_support_layers --preflight-only"`
- Test status:
  - `63 passed` (`pytest -q`).
- Manual verification status:
  - Real workspace all-city city-processing batch completed with `ok=30`.
  - Real workspace support-layer preflight now blocks only on missing raw DEM/NLCD/hydro inputs for 29 cities.
  - Real workspace AppEEARS preflight now blocks only on `aoi_missing` for 29 cities.
- Next recommended step:
  - Populate the remaining 29 city-specific DEM/NLCD/hydro raw folders and rerun support-layer preflight.

### 2026-03-08 - Checkpoint: Support-Layer Standardization Added

- Date / checkpoint:
  - 2026-03-08 support-layer readiness standardization and Phoenix prep verification.
- Change made:
  - Added deterministic support-layer preflight/audit logic and CLI support for `--preflight-only`.
  - Added deterministic support-layer prep logic and CLI for one-city and all-city prep runs.
  - Added deterministic prepared support outputs under `data_processed/support_layers/<city_stem>/`.
  - Updated feature discovery to prefer prepared support outputs before the existing raw-folder fallback.
  - Added tests for all-city support-layer preflight coverage, missing-prerequisite handling, recursive city raw discovery, prep outputs, and prepared-output feature discovery.
- Files touched:
  - `src/config.py`
  - `src/support_layers.py`
  - `src/run_support_layers.py`
  - `src/feature_assembly.py`
  - `tests/test_support_layers.py`
  - `README.md`
  - `docs/workflow.md`
  - `docs/data_dictionary.md`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_support_layers --preflight-only"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_support_layers --city-ids 1"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_support_layers"`
- Test status:
  - `61 passed` (`pytest -q`) at that checkpoint.
- Manual verification status:
  - Real workspace support-layer preflight produced `1 ready / 29 blocked`.
  - Real workspace Phoenix support-layer prep completed and wrote deterministic prepared DEM, NLCD, and hydro outputs.
- Next recommended step:
  - Materialize the remaining study areas, grids, and city-specific DEM/NLCD/hydro raw folders, then rerun support-layer preflight and all-city prep.

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
  - `56 passed` (`pytest -q`) at that checkpoint.
- Manual verification status:
  - Real workspace preflight produced `1 ready / 29 blocked`.
  - Phoenix was the only currently materialized ready city for AppEEARS prerequisites at that time.
- Next recommended step:
  - Materialize study areas for all cities, rerun preflight, and proceed to all-city AOI export and AppEEARS submit-only acquisition.
