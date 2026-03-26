# Chat Handoff - Urban Heat Mapping Dataset Project

## Project Goal

Maintain a reproducible cross-city urban heat project that covers study design, geospatial data assembly, modeling-ready handoff, and city-held-out machine-learning evaluation for 30 U.S. cities.

## What Is Completed

Implemented in code:

- Boundary, study-area, and 30 m grid processing for the 30-city city list.
- Study-area outputs now persist the original urban-core geometry alongside the buffered acquisition geometry.
- Batch city-processing runner for one city or all configured cities.
- Raster alignment, DEM, NLCD, hydro distance, city feature assembly, and final dataset assembly.
- Final-dataset audit CLI plus deterministic city-level fold generation for modeling handoff.
- Baseline modeling CLI for city-held-out logistic regression plus decision-stump comparison, with fold metrics, saved validation predictions, leakage checks, and assumptions reporting.
- Shared first-pass modeling contract plus reusable sklearn-based ML layer:
  - `src.modeling_config`
  - `src.modeling_data`
  - `src.modeling_metrics`
  - `src.modeling_baselines`
  - `src.modeling_runner`
  - `src.run_modeling_baselines`
  - `src.run_logistic_saga`
  - `src.run_random_forest`
- First-pass held-out-city baseline suite with:
  - global mean baseline
  - land-cover-only baseline
  - impervious-only baseline
  - climate-only baseline
- First-pass held-out-city main models with:
  - logistic regression using `solver="saga"` in an sklearn `Pipeline`
  - random forest in an sklearn `Pipeline`
- The tuned sklearn runners now share an explicit feature-type contract and coerce categorical columns before categorical imputation/encoding, which fixes the mixed `land_cover_class` / `climate_group` preprocessing failure that previously surfaced as `could not convert string to float: 'hot_arid'`.
- The tuned sklearn runners now also expose explicit `smoke` and `full` tuning presets, preload sampled city rows once per run, enable safe per-fold sklearn pipeline caching, and emit concise timing/search-space diagnostics in logs plus `run_metadata.json`.
- The modeling import path is now decoupled from `src.feature_assembly` / `geopandas` by a lightweight `src.final_dataset_contract` module, so focused modeling tests and CLIs can import without pulling the full geospatial stack.
- The modeling data loader is now parquet-first by default, while still supporting explicit CSV compatibility inputs including deterministic chunked per-city sampling when that fallback path is intentionally used.
- The rebuilt repo-local `.venv` is now the standard interpreter for this repo, reads the canonical `final_dataset.parquet` and `city_outer_folds.parquet` cleanly through both `pandas` and low-level `pyarrow`, and both smoke modeling CLIs have been manually verified end to end against those parquet artifacts.
- The tuned modeling runner now creates its per-fold cache directories with plain `Path.mkdir()` instead of `tempfile.TemporaryDirectory`, which avoids Windows temp-directory permission failures seen in this Codex session.
- First-pass modeling outputs now write to `outputs/modeling/{baselines,logistic_saga,random_forest}/` with metrics tables, held-out predictions, calibration tables, best-parameter summaries for tuned models, run metadata, and feature-contract manifests.
- AppEEARS AOI export from buffered study areas.
- AppEEARS API client with environment-only authentication.
- Resumable AppEEARS acquisition runner for NDVI and ECOSTRESS (`submit`, `poll`, `download`, `retry-incomplete`).
- AppEEARS submit handling now preserves deterministic `task_name` state, retries transient GET/status JSON failures, and records recoverable submit failures instead of flattening all timeouts into generic hard failures.
- AppEEARS-related CLIs now load `PROJECT_ROOT/.env.local` before credential lookup, without overriding already-exported environment variables.
- Thin acquisition orchestration runner that sequences raw support acquisition, support-layer prep, NDVI AppEEARS, ECOSTRESS AppEEARS, and writes a restart-safe status summary.
- Full-stack city orchestration runner that extends raw/support/AppEEARS stages through feature assembly and writes one per-city stage summary row.
- Full-stack orchestration summaries now carry explicit per-stage exception metadata (`exception_type`, `exception_message`, `traceback`) plus a city-level `stage` pointer to the primary failed or incomplete stage.
- Full-stack CLI exit behavior is now explicit: `0` when all requested cities complete, `1` when any city fails, and `2` when cities remain incomplete or credential-blocked.
- Deterministic AppEEARS preflight/audit path that computes expected per-city study area, AOI, raw download, and status-summary paths; validates AOI CRS; and writes machine-readable preflight outputs.
- Deterministic support-layer preflight/audit path for DEM, NLCD land cover, NLCD impervious, and hydro inputs.
- Restartable raw support-layer acquisition runner for official USGS 3DEP 1 arc-second DEM, MRLC Annual NLCD 2021 land cover + impervious, and USGS NHDPlus HR hydro packages.
- Raw support downloads now preserve `.part` files, resume interrupted large hydro ZIP transfers when the host supports byte ranges, and record structured `failure_reason` / `failure_category` / `recoverable` metadata plus hydro warning details.
- AppEEARS bundle downloads now retry transient connection and retryable HTTP failures instead of failing a city on the first dropped connection, and those failures now serialize as recoverable download-specific reasons.
- TNM malformed pseudo-JSON wrappers that embed ScienceBase/TNM upstream failures, including `RemoteDisconnected`, `Connection aborted`, `Remote end closed connection`, `Response ended prematurely`, and `get_products.py`, now classify as recoverable `sciencebase_upstream_error` events with a 6-attempt retry/backoff policy; retry-exhausted TNM `/products` `502/503/504` errors now classify as recoverable `tnm_upstream_http_error`, `dem_tiles_not_found` is now a recoverable `data_unavailable` failure, and raw-acquisition TLS classification now imports `requests.exceptions.SSLError` correctly.
- Deterministic support-layer prep runner that clips standardized city-specific raw support files into `data_processed/support_layers/<city_stem>/`.
- GeoPackage writers now use `.tmp.gpkg` temp targets plus atomic replace, and hydro vectors are normalized to 2D before write so measured/M-or-Z geometries do not rely on silent pyogrio conversion.
- Cache audit/cleanup utility now inventories `data_raw/cache/`, classifies artifacts by retention tier, writes JSON metadata outside the cache tree, and supports dry-run targeted prune plans for safe regenerable artifacts.
- Feature-source discovery now prefers prepared support-layer outputs and otherwise preserves the prior raw-folder fallback behavior.
- AppEEARS feature-source discovery now recognizes native value-layer filenames and excludes QA/cloud/error sidecars with explicit logging.
- Full-stack orchestration has completed end to end for Phoenix (`city_id=1`), Tucson (`2`), Las Vegas (`3`), and Albuquerque (`4`), with per-city feature outputs on disk.
- The NDVI/LST handoff now requires AppEEARS-like native filename markers, so stale generic files such as `ndvi_1.tif`, `ndvi_2.tif`, or `lst_1.tif` are not treated as native value rasters.
- Raster-stack sampling now validates TIFF readability before use and skips unreadable stale files with warnings as long as enough valid rasters remain for the city.
- Feature assembly now supports `cell_filter_mode=study_area` (current behavior) and `cell_filter_mode=core_city` (buffered acquisition, core-city-only training cells).
- Documentation now makes the workflow from an empty city to a support-layer-ready city explicit, including the automated raw acquisition stage.
- Data-processing reporting is now generalized for all configured cities: the former Phoenix-only summary logic was refactored into a shared per-city reporting module plus a batch CLI, with Phoenix retained as a compatibility wrapper.
- Data-processing report outputs now write to `outputs/data_processing/<city_stem>/` and `figures/data_processing/<city_stem>/`, while first-pass ML tables and prediction artifacts now write under `outputs/modeling/` and later figures will live under `figures/modeling/`.
- Documentation architecture was redesigned on 2026-03-23 so the repo now reads as the full urban-heat ML project, not only as a preprocessing pipeline. `README.md` is now the landing page, `docs/workflow.md` is lifecycle-oriented, `docs/data_dictionary.md` is artifact-focused, and `docs/modeling_plan.md` was added as the concise grouped-city modeling-methods reference.
- The obsolete exploratory `notebooks/` workspace was removed on 2026-03-23, and the unused `NOTEBOOKS` path constant plus README mention were deleted so the documented repo layout matches the actual production tree.

Standardization status:

- Study-area and 30 m grid generation are standardized for one-city and all-city execution.
- AppEEARS acquisition is standardized in code for all 30 cities.
- Support-layer acquisition/prep is standardized in code around deterministic per-city raw-input paths plus deterministic prepared outputs.
- Data-processing reporting is standardized in code for all configured cities and no longer treats Phoenix as a special one-off output path.
- Reusable upstream caches for support-layer acquisition now live under `data_raw/cache/`.
- The current remaining blocker for broader scaling is data volume, long wall-clock runtime, and remaining city-specific source variability across the unfinished cities, not missing orchestration code paths.

## Testing Status

As of 2026-03-25:

- Rebuilt repo-local `.venv` verification checkpoint:
  - `.venv\Scripts\python.exe --version` returned `Python 3.13.5`
  - `.venv\Scripts\python.exe -c "import sys; print(sys.executable); print(sys.prefix); print(sys.base_prefix)"` returned:
    - `sys.executable=C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\.venv\Scripts\python.exe`
    - `sys.prefix=C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\.venv`
    - `sys.base_prefix=C:\Users\golde\anaconda3`
  - `.venv\pyvenv.cfg` now records `home = C:\Users\golde\anaconda3` and `executable = C:\Users\golde\anaconda3\python.exe`
  - `.venv\Scripts\python.exe -m pip --version` succeeded from the repo-local site-packages path
  - Key imports succeeded directly through `.venv`:
    - `import pandas, sklearn, pyarrow`
    - `import geopandas`
  - `requirements.txt` now includes `pytest` so future rebuilt environments can run tests directly; this session's rebuilt `.venv` initially lacked `pytest`, so the current environment was seeded from the accessible base interpreter's pytest packages after `pip install pytest` hit sandbox temp-path permission errors
- Focused modeling verification now passes through the rebuilt `.venv`:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_modeling_contract.py tests/test_modeling_runner.py -q`
  - Result: `18 passed` in `4.52s`
  - Caveat: the run emitted the same non-fatal Windows `joblib` cache warnings seen in earlier checkpoints
- Canonical-path CLI guidance verification now passes through the rebuilt `.venv`:
  - `.\.venv\Scripts\python.exe -m src.run_logistic_saga --help` succeeded
  - `.\.venv\Scripts\python.exe -m src.run_random_forest --help` succeeded
  - The live help text now explicitly documents parquet-first dataset defaults, parquet-preferred fold resolution, CSV compatibility fallback status, and the bounded default `smoke` preset wording
- Parquet environment diagnosis through the rebuilt `.venv`:
  - `.\.venv\Scripts\python.exe -c "import sys, platform, pandas as pd, pyarrow, geopandas as gpd; print(sys.version); print(platform.platform()); print('pandas', pd.__version__); print('pyarrow', pyarrow.__version__); print('geopandas', gpd.__version__)"` returned:
    - `Python 3.13.5`
    - `Windows-11-10.0.26200-SP0`
    - `pandas 3.0.1`
    - `pyarrow 23.0.1`
    - `geopandas 1.1.3`
  - `pd.read_parquet(...)`, `pyarrow.parquet.ParquetFile(...)`, `pyarrow.parquet.read_metadata(...)`, and subset row-group reads all succeeded for:
    - `data_processed/final/final_dataset.parquet`
    - `data_processed/modeling/city_outer_folds.parquet`
  - Metadata confirmed both files are flat parquet tables written by `parquet-cpp-arrow version 23.0.1`; no `Repetition level histogram size mismatch` repro remained in this environment
- Real logistic smoke verification completed through the rebuilt `.venv` using canonical parquet artifacts and serial grid search:
  - `.\.venv\Scripts\python.exe -m src.run_logistic_saga --dataset-path data_processed\final\final_dataset.parquet --folds-path data_processed\modeling\city_outer_folds.parquet --sample-rows-per-city 5000 --outer-folds 0 --tuning-preset smoke --grid-search-n-jobs 1 --output-dir outputs\modeling\logistic_saga\parquet_verify`
  - Wall clock: `351.79s`
  - Metadata:
    - `sampled_city_preload=19.21s`
    - `grid_search_seconds=332.03s`
    - `train_row_count=120,000`
    - `test_row_count=30,000`
    - `param_candidate_count=4`
  - Fold metric:
    - `pooled_pr_auc=0.1729`
    - `pooled_recall_at_top_10pct=0.2171`
  - Caveats:
    - `joblib` emitted non-fatal cache-write warnings
    - `sklearn` emitted `ConvergenceWarning` for some logistic fits at `max_iter=2000`
- Real random-forest smoke verification completed through the rebuilt `.venv` using canonical parquet artifacts and serial settings:
  - `.\.venv\Scripts\python.exe -m src.run_random_forest --dataset-path data_processed\final\final_dataset.parquet --folds-path data_processed\modeling\city_outer_folds.parquet --sample-rows-per-city 5000 --outer-folds 0 --tuning-preset smoke --grid-search-n-jobs 1 --model-n-jobs 1 --output-dir outputs\modeling\random_forest\parquet_verify`
  - Wall clock: `291.03s`
  - Metadata:
    - `sampled_city_preload=19.25s`
    - `grid_search_seconds=270.92s`
    - `train_row_count=120,000`
    - `test_row_count=30,000`
    - `param_candidate_count=4`
  - Fold metric:
    - `pooled_pr_auc=0.1865`
    - `pooled_recall_at_top_10pct=0.2499`
  - Caveat: `joblib` emitted the same non-fatal cache-write warnings during pipeline caching
- Real logistic smoke verification completed through the rebuilt `.venv` using CSV artifacts and serial grid search:
  - `.\.venv\Scripts\python.exe -m src.run_logistic_saga --dataset-path data_processed\final\final_dataset.csv --folds-path data_processed\modeling\city_outer_folds.csv --sample-rows-per-city 5000 --outer-folds 0 --tuning-preset smoke --grid-search-n-jobs 1 --output-dir outputs\modeling\logistic_saga\venv_verify`
  - Wall clock: `382.43s`
  - Metadata:
    - `sampled_city_preload=95.08s`
    - `grid_search_seconds=284.13s`
    - `fold_wall_clock_seconds=284.36s`
    - `train_row_count=95,000`
    - `test_row_count=30,000`
    - `param_candidate_count=4`
  - Fold metric:
    - `pooled_pr_auc=0.1739`
    - `pooled_recall_at_top_10pct=0.2199`
  - Caveats:
    - This remains a compatibility fallback check, not the preferred verified path now that parquet smoke verification succeeds in the same `.venv`
    - `data_processed/final/final_dataset.csv` is not currently row-equivalent to `data_processed/final/final_dataset.parquet` (`48,522,748` vs `71,394,894` rows)
    - `joblib` emitted non-fatal cache-write warnings
    - `sklearn` emitted `ConvergenceWarning` for some logistic fits at `max_iter=2000`
- Real random-forest smoke verification completed through the rebuilt `.venv` using CSV artifacts and serial settings:
  - `.\.venv\Scripts\python.exe -m src.run_random_forest --dataset-path data_processed\final\final_dataset.csv --folds-path data_processed\modeling\city_outer_folds.csv --sample-rows-per-city 5000 --outer-folds 0 --tuning-preset smoke --grid-search-n-jobs 1 --model-n-jobs 1 --output-dir outputs\modeling\random_forest\venv_verify`
  - Wall clock: `279.34s`
  - Metadata:
    - `sampled_city_preload=96.43s`
    - `grid_search_seconds=178.19s`
    - `fold_wall_clock_seconds=178.45s`
    - `train_row_count=95,000`
    - `test_row_count=30,000`
    - `param_candidate_count=4`
  - Fold metric:
    - `pooled_pr_auc=0.1807`
    - `pooled_recall_at_top_10pct=0.1995`
  - Caveat: `joblib` emitted the same non-fatal cache-write warnings during pipeline caching
- CLI entrypoint health through the rebuilt `.venv`:
  - `.\.venv\Scripts\python.exe -m src.run_logistic_saga --help` succeeded
  - `.\.venv\Scripts\python.exe -m src.run_random_forest --help` succeeded
- Tuned-runtime checkpoint:
  - Syntax compilation passed via:
    - `cmd /c call "C:\Users\golde\anaconda3\python.exe" -m py_compile src\modeling_config.py src\modeling_runner.py src\run_logistic_saga.py src\run_random_forest.py tests\test_modeling_runner.py`
  - Search-space probe confirmed the new preset sizes via:
    - `cmd /c call "C:\Users\golde\anaconda3\python.exe" -c "from sklearn.model_selection import ParameterGrid; from src.modeling_config import get_model_tuning_spec; ..."`
    - Observed counts:
      - `logistic_smoke=4`
      - `logistic_full=20`
      - `rf_smoke=4`
      - `rf_full=81`
  - Focused modeling pytest collection did not complete in the accessible interpreter:
    - `cmd /c call "C:\Users\golde\anaconda3\python.exe" -m pytest tests/test_modeling_contract.py tests/test_modeling_runner.py -q"`
    - Result: collection blocked with `ModuleNotFoundError: No module named 'geopandas'`
  - Direct repo-venv execution was blocked in this Codex session:
    - `.venv\Scripts\python.exe -m src.run_logistic_saga --sample-rows-per-city 5000 --outer-folds 0 --tuning-preset smoke`
    - `.venv\Scripts\python.exe -m src.run_random_forest --sample-rows-per-city 5000 --outer-folds 0 --tuning-preset smoke`
    - Result for both: `Access is denied`

- Tuned-modeling preprocessing regression checkpoint:
  - `10 passed` via:
    - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m pytest tests/test_modeling_contract.py tests/test_modeling_runner.py -q"`
  - Added regression coverage for:
    - explicit feature-type contract enforcement
    - categorical string values like `hot_arid` plus missing values
    - tuned logistic / random-forest pipeline fit on tiny mixed-type data
    - categorical contract columns staying out of the numeric transformer
- First-pass sklearn modeling layer checkpoint:
  - `9 passed` via:
    - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m pytest tests/test_modeling_prep.py tests/test_modeling_contract.py tests/test_modeling_runner.py -q"`
  - `scikit-learn`, `joblib`, and `threadpoolctl` were installed into `.venv` during this checkpoint because the repo already required sklearn-style modeling code but the dependency was missing from the environment and `requirements.txt`.
- Data-processing reporting generalization checkpoint:
  - `4 passed` via:
    - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m pytest tests/test_summarize_phoenix_dataset.py tests/test_data_processing_reporting.py -q"`
  - `16 passed` via:
    - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m pytest tests/test_city_processing.py tests/test_feature_assembly.py -q"`
- Repository housekeeping checkpoint: no tests were run because this change only removed obsolete exploratory notebooks and cleaned stale references.
- Documentation redesign checkpoint: no tests were run because this change updated docs only and did not modify pipeline code.
- Baseline-modeling + modeling-prep subset: `8 passed` via:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m pytest tests/test_model_baselines.py tests/test_modeling_prep.py -q"`
- Modeling-prep subset: `4 passed` via:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m pytest tests/test_modeling_prep.py -q"`
- Orchestration/AppEEARS/vector hardening subset: `36 passed` via:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m pytest tests/test_appeears_client.py tests/test_appeears_acquisition.py tests/test_full_stack_orchestration.py tests/test_support_layers.py -q"`

Previously recorded:

- Focused raw/AppEEARS/full-stack hardening subset: `35 passed` via:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m pytest tests/test_raw_data_acquisition.py tests/test_appeears_client.py tests/test_appeears_acquisition.py tests/test_full_stack_orchestration.py -q"`
- Focused ScienceBase/TNM retry subset: `22 passed` via:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m pytest tests/test_raw_data_acquisition.py tests/test_full_stack_orchestration.py -q"`
- Focused `.env.local` bootstrap/AppEEARS/full-stack subset: `27 passed` via:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m pytest tests/test_env_bootstrap.py tests/test_appeears_client.py tests/test_appeears_acquisition.py tests/test_full_stack_orchestration.py -q"`
- Acquisition orchestration compatibility subset: `2 passed` via:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m pytest tests/test_acquisition_orchestration.py -q"`

- Focused regression subset: `23 passed` via:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m pytest tests/test_feature_assembly.py tests/test_full_stack_orchestration.py tests/test_raw_data_acquisition.py tests/test_raster_features.py -q"`
- Additional focused buffer-policy subset: `21 passed` via:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m pytest tests/test_batch_city_processing.py tests/test_city_processing.py tests/test_feature_assembly.py tests/test_full_stack_orchestration.py -q"`
- Latest previously recorded full-suite result:
  - `69 passed` via `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m pytest -q"`

Test-verified in the latest checkpoint:

- New cache cleanup coverage passed: `4 passed` via:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m pytest tests/test_cache_cleanup.py -q"`
- Mixed-folder AppEEARS discovery now ignores generic stale filenames like `ndvi_1.tif` and keeps only native AppEEARS value rasters when both are present.
- Raster-stack sampling now skips invalid TIFFs with a warning instead of crashing the city when valid rasters remain.
- Focused AppEEARS rerun-state regressions passed: `18 passed` via:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m pytest tests/test_appeears_client.py tests/test_appeears_acquisition.py -q"`
- Focused AppEEARS client, AppEEARS acquisition, and raw-acquisition resilience subsets passed: `22 passed` via:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m pytest tests/test_appeears_client.py tests/test_raw_data_acquisition.py tests/test_appeears_acquisition.py -q"`
- Raw acquisition logging and hydro read-path regression subset passed: `5 passed` via `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m pytest tests/test_raw_data_acquisition.py -q"`.
- DEM TNM Access product deduplication keeps the newest tile version per 1x1 degree tile.
- Annual NLCD bundle member selection resolves the 2021 land-cover raster deterministically.
- NHDPlus HR water export reads the expected water layers and ignores unrelated layers.
- NHDPlus HR water-layer reads now pass a spatial `bbox` into `geopandas.read_file`, preventing full-layer reads for each city-sized clip.
- AppEEARS auth selection now prefers Earthdata credentials over a simultaneously configured static `APPEEARS_API_TOKEN`, ensuring task submission mints a fresh bearer token instead of reusing a stale one.
- AppEEARS task-submission errors now classify `401` as auth failure, `400/422` as bad payload, and `403` as either stale token or likely permission/EULA issue depending on auth mode.
- AppEEARS reruns now reuse persisted `task_id` values by polling existing tasks first, downloading completed bundles for those same tasks, and only submitting new tasks when no reusable saved task exists or the old remote task is terminal-invalid.
- AppEEARS acquisition summaries no longer label in-progress remote work as `not_started`; reruns now keep active tasks in AppEEARS-specific in-progress statuses and mark `done + files already present` as `skipped_existing`.
- TNM product queries and downloads now retry transient `408/429/5xx` failures with exponential backoff, and hydro package `404` URLs trigger one metadata refresh/retry before the package is skipped or the dataset fails cleanly.
- TNM product-query parsing now retries transient invalid/non-JSON bodies instead of crashing in `response.json()`.
- TNM malformed pseudo-JSON wrappers that mention ScienceBase/`HTTPSConnectionPool`/`Max retries exceeded` or surface `RemoteDisconnected` / `Connection aborted` / `Response ended prematurely` / `get_products.py` are now classified as `sciencebase_upstream_error` and retried with a longer backoff window.
- Retry-exhausted TNM `/products` `502/503/504` responses now classify as recoverable `tnm_upstream_http_error` rows under `upstream_dependency` instead of falling through to `unexpected_error`.
- DEM cities with no returned TNM tiles now fail as structured recoverable `dem_tiles_not_found` / `data_unavailable` rows instead of bubbling a raw runtime exception into the full pipeline.
- Raw-acquisition TLS classification now correctly handles `requests.exceptions.SSLError` without crashing the failure-classification path.
- Large hydro ZIP downloads now keep partial files and resume after interrupted chunked transfers instead of restarting from byte `0`.
- Raw support and AppEEARS summaries now expose structured failure metadata (`failure_reason`, `recoverable`, plus raw-stage `failure_category` / warning fields), and full-stack orchestration now carries those fields into its per-city stage summary.
- TNM retry logging now emits an explicit final-attempt error line, so the old `attempt 1/4`, `2/4`, `3/4`, then fail pattern is now clearly understood as four total attempts rather than three effective attempts.
- `.env.local` is now loaded automatically at CLI startup for full-stack, acquisition-orchestration, and AppEEARS acquisition entrypoints before any AppEEARS credential lookup runs.
- The raw acquisition runner skips already materialized deterministic outputs unless `--force` is passed.
- Prior coverage for city processing, AppEEARS acquisition, support-layer preflight/prep, and feature assembly still passes.
- Native AppEEARS filename discovery is covered for both underscore-delimited and native dotted layer names.
- Thin orchestration sequencing and all-missing stage targeting are covered in `tests/test_acquisition_orchestration.py`.
- Full-stack city orchestration stage mapping, feature-stage deferral, and `all-missing` targeting are covered in `tests/test_full_stack_orchestration.py`.
- AppEEARS missing-credential handling is covered in `tests/test_appeears_acquisition.py`.
- Phoenix summary dataset selection prefers the canonical per-city feature parquet over intermediate and merged alternatives.
- Phoenix preprocessing-audit logic counts open-water and low-ECOSTRESS-pass drops deterministically.

## Manual Verification Status

Implemented:

- `src.run_city_processing` and `src.run_city_batch_processing` generate study areas and 30 m grids.
- `src.run_support_layers --preflight-only` serves as the deterministic prerequisite audit for support-layer readiness.
- `src.run_raw_data_acquisition` performs deterministic raw DEM/NLCD/hydro acquisition and clipping into the standardized raw folders, with reusable caches and summary outputs.
- `src.run_cache_cleanup` audits cache growth, records a JSON manifest outside `data_raw/cache/`, and supports safe dry-run prune plans for regenerable extracted artifacts and partial downloads.
- `src.run_support_layers` performs deterministic support-layer prep once raw support inputs exist.
- `src.run_acquisition_orchestration` sequences raw support acquisition, support-layer prep, NDVI AppEEARS, and ECOSTRESS AppEEARS into one restart-safe CLI.
- `src.run_full_stack_orchestration` extends the same flow through feature assembly and writes one per-city stage-status summary row.
- `src.audit_final_dataset` validates the canonical final parquet and writes modeling handoff summaries under `data_processed/modeling/`.
- `src.make_model_folds` writes deterministic city-level outer folds under `data_processed/modeling/`.
- `src.run_model_baselines` trains city-held-out baseline models from the canonical final parquet plus `city_outer_folds.*` and writes metrics, predictions, leakage checks, and model artifacts under `data_processed/modeling/baselines/`.
- `src.run_modeling_baselines` trains the first-pass held-out-city baseline suite and writes outputs under `outputs/modeling/baselines/`.
- `src.run_logistic_saga` trains the grouped logistic SAGA model with training-city-only preprocessing/tuning and writes outputs under `outputs/modeling/logistic_saga/`.
- `src.run_random_forest` trains the grouped random-forest model with the same held-out-city discipline and writes outputs under `outputs/modeling/random_forest/`.
- `src.run_logistic_saga` and `src.run_random_forest` now use the same explicit shared feature-type contract for tuned preprocessing, with categorical columns coerced safely ahead of `SimpleImputer` / encoder steps.
- `src.run_logistic_saga` and `src.run_random_forest` now default to `--tuning-preset smoke`, preserve `--tuning-preset full`, record per-fold timing/search-space metadata, and reuse sampled city rows across folds instead of reloading them fold by fold.
- `src.run_data_processing_reports` generates per-city data-processing markdown summaries, supporting CSV tables, and PNG figures for all configured cities or a selected subset.
- `src.summarize_phoenix_dataset` remains available as a Phoenix compatibility wrapper over the shared data-processing reporting logic.

Test-verified:

- Batch city-processing coverage is included in `tests/test_batch_city_processing.py`.
- AppEEARS acquisition coverage is included in `tests/test_appeears_acquisition.py`.
- Support-layer audit, raw acquisition helpers, prep, and prepared-output discovery are covered by `tests/test_support_layers.py` and `tests/test_raw_data_acquisition.py`.
- Thin acquisition orchestration coverage is included in `tests/test_acquisition_orchestration.py`.
- Full-stack city orchestration coverage is included in `tests/test_full_stack_orchestration.py`.
- Raster stack validation and stale-legacy AppEEARS handoff coverage are included in `tests/test_feature_assembly.py` and `tests/test_raster_features.py`.
- Buffered-vs-core study-area metadata and feature filtering coverage are included in `tests/test_city_processing.py` and `tests/test_feature_assembly.py`.
- Baseline-modeling coverage is included in `tests/test_model_baselines.py`.
- First-pass grouped sklearn modeling coverage is included in `tests/test_modeling_contract.py` and `tests/test_modeling_runner.py`.
- Modeling-path regression coverage now also locks in parquet-preferred fold resolution plus CLI parquet-first help/default guidance.
- Data-processing report path generation and batch city iteration coverage are included in `tests/test_data_processing_reporting.py`.
- The latest targeted regression result is `36 passed` for AppEEARS client/acquisition, full-stack orchestration, and support-layer vector normalization hardening.

Not manually verified in the latest checkpoint:

- No full canonical all-fold modeling run has been recorded yet for `src.run_modeling_baselines`, `src.run_logistic_saga`, or `src.run_random_forest` on the full `71,394,894`-row dataset beyond the smoke presets.
- No pyarrow downgrade or alternate-version experiment was needed in this checkpoint because the current rebuilt `.venv` already reads both real parquet artifacts successfully.

Manually verified:

- The rebuilt repo-local `.venv` is now manually runnable in this Codex session and is the standard interpreter path going forward; use `.\.venv\Scripts\python.exe -m ...` from the repo root.
- Canonical parquet access is manually verified in this sandbox:
  - `data_processed/final/final_dataset.parquet` loads through `pandas.read_parquet(...)`, `pyarrow.parquet.ParquetFile(...)`, `pyarrow.parquet.read_metadata(...)`, schema reads, subset column reads, and row-group reads
  - `data_processed/modeling/city_outer_folds.parquet` loads through the same `pandas` and `pyarrow` read paths without reproducing `OSError: Repetition level histogram size mismatch`
- Canonical parquet smoke verification is manually complete for:
  - `outputs/modeling/logistic_saga/parquet_verify/`
  - `outputs/modeling/random_forest/parquet_verify/`
- The canonical modeling workflow now defaults to parquet-first guidance; CSV remains documented only as a compatibility fallback because `data_processed/final/final_dataset.csv` is not row-equivalent to the canonical parquet.

- 2026-03-23 repository housekeeping verification:
  - Confirmed the only live `notebooks` references were the README repo-layout bullet and the unused `src.config.NOTEBOOKS` constant.
  - Removed the exploratory notebook files and their `.ipynb_checkpoints` artifacts because they were not part of any runnable pipeline, test, or documented output.
  - Reran a repo-wide text search after cleanup and confirmed no remaining production/runtime `notebooks` references outside the historical notes recorded in this handoff file.
- 2026-03-23 data-processing reporting verification:
  - Ran `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_data_processing_reports --city-ids 1"` successfully.
  - Confirmed the new Phoenix report now writes to `outputs/data_processing/01_phoenix_az/phoenix_data_summary.md`, `outputs/data_processing/01_phoenix_az/tables/*.csv`, and `figures/data_processing/01_phoenix_az/*.png`.
  - Confirmed the batch CLI also writes `outputs/data_processing/data_processing_report_summary.csv` and creates the reserved stage roots `outputs/modeling/` and `figures/modeling/`.
  - Verified that the generated Phoenix markdown links to figures across the split `outputs/` and `figures/` roots instead of assuming a bundled single-folder asset layout.
  - Full all-city live report generation has not been run yet in this checkpoint; only Phoenix was manually smoke-tested on real data.
- 2026-03-23 documentation redesign verification:
  - Reviewed the top-level repo structure, existing `src/`, `tests/`, `data_processed/`, `outputs/`, and `figures/` layout before rewriting docs.
  - Verified that the redesigned docs match the implemented code boundaries: baseline modeling exists, grouped-city fold generation exists, and the planned `solver="saga"` logistic-regression and random-forest stages are documented as planned rather than implemented.
  - Verified that no code modules, import paths, or output directories were moved in this checkpoint; the repo-structure change is conceptual/documentary rather than a risky physical refactor.
- 2026-03-23 real canonical modeling-prep verification:
  - Ran `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m pytest tests/test_modeling_prep.py -q"` and confirmed `4 passed`.
  - The first live `src.audit_final_dataset` run on the canonical parquet failed with `MemoryError`, which exposed that the original implementation was trying to materialize the full final dataset.
  - Updated `src.modeling_prep` to validate required columns from parquet schema metadata and load only the columns needed for audit/fold generation.
  - Reran `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m src.audit_final_dataset"` successfully.
  - Reran `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m src.make_model_folds --n-splits 5"` successfully, then reran the same fold command a second time and confirmed the `data_processed/modeling/city_outer_folds.csv` SHA-256 hash stayed `4A5EE01AFC6D192A88509E62C80ED73E85B83E4913CEBEEF943CC1ACA1CE9467`.
  - Confirmed the canonical dataset path `data_processed/final/final_dataset.parquet` exists and the audit reported `71,394,894` rows across `30` cities with `hotspot_10pct` binary validation passing.
  - Confirmed modeling artifacts now exist under `data_processed/modeling/`: `final_dataset_audit_summary.json`, `final_dataset_audit.md`, `final_dataset_city_summary.csv`, `final_dataset_feature_missingness.csv`, `final_dataset_feature_missingness_by_city.csv`, `city_outer_folds.parquet`, and `city_outer_folds.csv`.
  - Confirmed the fold artifact is city-level and deterministic in the real workspace: `30` rows, `30` unique `city_id` values, `0` duplicate city assignments, `5` folds, and an even `6` cities per fold in the current greedy row-count balance.
- 2026-03-23 baseline-modeling implementation checkpoint:
  - Added `src.model_baselines` and `src.run_model_baselines` for memory-aware city-held-out baseline modeling that loads only required parquet columns, joins batches to city-level folds by `city_id`, fits train-fold-only preprocessing, trains a streaming logistic regression, and optionally fits a decision-stump comparison.
  - Added regression coverage in `tests/test_model_baselines.py` for leakage-column rejection, fold joins, fold-table validation, and end-to-end artifact writing on a synthetic parquet fixture.
  - Updated `README.md`, `docs/workflow.md`, and `docs/data_dictionary.md` to document the new baseline stage, outputs, and CLI usage.
  - No fresh end-to-end run of `src.run_model_baselines` has been executed yet on the canonical `71,394,894`-row parquet; this checkpoint is test-verified only.
- 2026-03-23 tuned-modeling preprocessing regression verification:
  - Ran `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m pytest tests/test_modeling_contract.py tests/test_modeling_runner.py -q"` and confirmed `10 passed`.
  - Reran `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_logistic_saga --sample-rows-per-city 5000"` twice on the canonical parquet; the command no longer failed immediately in sklearn preprocessing, but it exceeded both a `20` minute and a `60` minute interactive verification window before writing fold outputs.
  - Reran `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_random_forest --sample-rows-per-city 5000"` on the canonical parquet; it also exceeded a `20` minute interactive verification window without reproducing the old preprocessing error.
  - Reran `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_logistic_saga --sample-rows-per-city 5000 --outer-folds 0"` and `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_random_forest --sample-rows-per-city 5000 --outer-folds 0"`; both also exceeded a `30` minute verification window on the canonical parquet without reproducing the old `hot_arid` preprocessing error.
  - The tuned output roots currently show refreshed `feature_contract.json` manifests, but no completed fold-level artifacts were produced during these timed verification windows.
- 2026-03-19 real workspace cache/storage audit:
  - Ran `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m src.run_cache_cleanup --prune-modes regenerable --protect-recent-hours 24 --report-json outputs\storage\cache_cleanup_dry_run_20260319.json"` in dry-run mode.
  - Ran `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m src.run_cache_cleanup --prune-modes regenerable --protect-recent-hours 0 --report-json outputs\storage\cache_cleanup_dry_run_no_age_gate_20260319.json"` in dry-run mode.
  - Confirmed `data_raw/cache/` currently accounts for about `63.72 GB` across `80` files, dominated by `hydro_extracted=25.15 GB`, `nlcd_bundle=21.97 GB`, and `hydro_package=12.64 GB`.
  - Confirmed the conservative active-run dry-run plan with `--protect-recent-hours 24` proposed `0 GB` for deletion and blocked `27.80 GB` solely because the candidate files were newer than 24 hours.
  - Confirmed the no-age-gate dry-run plan proposed `27.83 GB` across `28` files for safe regenerable cleanup, consisting of hydro extracted GeoPackages, NLCD extracted rasters, and `.part` partial downloads.
  - Confirmed downstream support outputs remain small relative to cache: `data_raw/dem=0.126 GB`, `data_raw/nlcd=0.035 GB`, `data_raw/hydro=0.031 GB`, `data_processed/support_layers=0.055 GB`.
  - Confirmed by SHA-256 that Tucson, Las Vegas, and Albuquerque DEM/NLCD raw outputs are byte-identical to their prepared counterparts; hydro prepared outputs are not byte-identical but remain the same clipped downstream derivative stage.
- 2026-03-19 real-city Phoenix buffer-policy validation:
  - Regenerated `src.run_city_processing --city-id 1 --buffer-m 2000 --resolution 30`.
  - Confirmed `data_processed/study_areas/01_phoenix_az_study_area.gpkg` now contains non-empty `core_geometry_wkt` and `core_geometry_crs=EPSG:32612`.
  - Ran `src.run_city_features --city-id 1 --cell-filter-mode core_city` successfully with `blocked_stages=` blank.
  - Phoenix per-city feature rows changed from `4,735,561` buffered-study-area rows to `3,199,440` core-city rows.
  - Phoenix intermediate unfiltered table retained both `is_core_city_cell` and `is_buffer_ring_cell`; filtered/core-city outputs retained only core cells.
  - A temporary `assemble_final_dataset(...)` run succeeded, confirming the new per-city audit fields do not break downstream final-dataset assembly.
  - A temporary AppEEARS AOI export and support-layer geometry/bbox read against the refreshed Phoenix `study_area.gpkg` also succeeded, confirming the added metadata columns do not break those downstream readers.
- Confirmed current on-disk completion state for cities `1-4`:
  - `data_processed/city_features/01_phoenix_az_features.parquet`
  - `data_processed/city_features/02_tucson_az_features.parquet`
  - `data_processed/city_features/03_las_vegas_nv_features.parquet`
  - `data_processed/city_features/04_albuquerque_nm_features.parquet`
- Confirmed current AOI, raw support, and prepared-support directories exist for cities `1-4`:
  - `data_processed/appeears_aoi/01_phoenix_az_aoi.geojson`
  - `data_processed/appeears_aoi/02_tucson_az_aoi.geojson`
  - `data_processed/appeears_aoi/03_las_vegas_nv_aoi.geojson`
  - `data_processed/appeears_aoi/04_albuquerque_nm_aoi.geojson`
  - `data_raw/dem/{phoenix,tucson,las_vegas,albuquerque}/`
  - `data_processed/support_layers/{01_phoenix_az,02_tucson_az,03_las_vegas_nv,04_albuquerque_nm}/`
- Confirmed current AppEEARS status summaries for cities `2-4`:
  - NDVI summary rows show Tucson=`skipped_existing`, Las Vegas=`completed`, Albuquerque=`completed`, all with `remote_task_status=done`.
  - ECOSTRESS summary rows show Tucson=`skipped_existing`, Las Vegas=`completed`, Albuquerque=`completed`, all with `remote_task_status=done`.
- No fresh live orchestration rerun was executed in the 2026-03-19 checkpoint; readiness assessment is based on current on-disk outputs plus the new focused regression pass.
- No fresh live rerun of the affected cities (`5,6,7,21,27`) has been executed after the 2026-03-20 network-recovery hardening and follow-up TNM wrapper / DEM-tile / `SSLError` fixes; these checkpoints are test-verified only.
- No fresh live rerun of the 2026-03-22 ECOSTRESS-affected cities (`16,17,18,19,28`) has been executed after the 2026-03-23 AppEEARS download retry, summary-schema, and GeoPackage/vector hardening changes; this checkpoint is test-verified only.
- 2026-03-21 rerun log review from `rerun_affected.log`:
  - Confirmed the earlier `sciencebase_upstream_error` fix is now active in real orchestration output, with `6` retry attempts and no full-pipeline abort.
  - Confirmed the remaining gaps were a retry-exhausted TNM `/products` `504` that still summarized as `unexpected_error` and a malformed wrapper containing `Response ended prematurely` plus `get_products.py` that still summarized as `invalid_json_response`.
  - No second live rerun was executed after the 2026-03-21 follow-up code fix; this new checkpoint is log-verified plus test-verified.
- Phoenix is now manually verified in `core_city` mode; the remaining cities still need the same refresh if they will join an overnight `core_city` run.
- Verified the moved virtual environment resolves against the new OneDrive-backed workspace:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -c 'import sys, pathlib; print(sys.executable); print(pathlib.Path(sys.executable).exists())'"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -c 'from src.config import PROJECT_ROOT, DATA_RAW, DATA_PROCESSED; print(PROJECT_ROOT); print(DATA_RAW); print(DATA_PROCESSED)'"`
- Observed output:
  - `.venv\Scripts\python.exe` executed successfully outside the sandbox.
  - `PROJECT_ROOT`, `DATA_RAW`, and `DATA_PROCESSED` resolved to `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\...`
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
  - the 29 blocked rows share `prep_blocking_reasons=dem_source_missing;nlcd_land_cover_source_missing;nlcd_impervious_source_missing;hydro_source_missing`
- Ran the real workspace Phoenix support-layer prep CLI:
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
  - the 29 blocked rows share `blocking_reason=aoi_missing`
- Ran the real workspace raw acquisition CLI against the already-materialized Phoenix raw inputs:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command \".venv\Scripts\python.exe -m src.run_raw_data_acquisition --city-ids 1 --dataset all\""`
- Observed output:
  - `data_processed/support_layers/raw_data_acquisition_summary.json`
  - `data_processed/support_layers/raw_data_acquisition_summary.csv`
  - status counts: `dem/skipped_existing=1`, `nlcd/skipped_existing=1`, `hydro/skipped_existing=1`
- Ran the real workspace Phoenix summary CLI:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.summarize_phoenix_dataset"`
- Observed output:
  - `outputs/phoenix_data_summary.md`
  - `outputs/phoenix_data_summary/tables/*.csv`
  - `outputs/phoenix_data_summary/figures/*.png`
  - `dataset_consistency_check.csv` confirms the canonical per-city feature parquet matches the Phoenix filtered intermediate row count (`4,735,561`).
- Ran a real workspace Phoenix AppEEARS discovery probe:
  - `@'...discover_default_feature_sources...'@ | .venv\Scripts\python.exe -`
- Observed output:
  - `ndvi_count=9`
  - `lst_count=61`
  - first discovered NDVI raster: `MOD13A1.061__500m_16_days_NDVI_doy2023113000000_aid0001.tif`
  - first discovered LST raster: `ECO_L2T_LSTE.002_LST_doy2023123074836_aid0001_12N.tif`
- Ran a real workspace Phoenix feature-extraction smoke test:
  - `cmd /d /c ".venv\Scripts\python.exe -m src.run_city_features --city-id 1 --max-cells 100 --no-save"`
- Observed output:
  - `rows=94`
  - `blocked_stages=` (empty)
  - discovery logs reported `ndvi=9` and `lst=61`, confirming Phoenix is no longer blocked at NDVI/LST discovery.
- Ran the moved-workspace Phoenix orchestration CLI:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_acquisition_orchestration --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31"`
- Observed output:
  - `data_processed/orchestration/acquisition_orchestration_summary.json`
  - `data_processed/orchestration/acquisition_orchestration_summary.csv`
  - orchestration stage counts: `raw_support_acquisition=1`, `support_layer_prep=1`, `appeears_ndvi=1`, `appeears_ecostress=1`
  - `data_processed/support_layers/raw_data_acquisition_summary.csv` rewrote Phoenix rows with `skipped_existing` for `dem`, `nlcd`, and `hydro`
  - `data_processed/support_layers/support_layers_prep_summary.csv` rewrote Phoenix with `status=skipped_existing`
  - `data_processed/appeears_status/appeears_ndvi_acquisition_summary.csv` rewrote Phoenix as `status=completed`, `remote_task_status=done`, `n_bundle_files=25`
  - `data_processed/appeears_status/appeears_ecostress_acquisition_summary.csv` rewrote Phoenix as `status=completed`, `remote_task_status=done`, `n_bundle_files=284`
  - Phoenix raw NDVI and ECOSTRESS `.tif` timestamps remained on `2026-03-08`, so this was resumptive validation after the move, not proof of a fresh AppEEARS re-download on `2026-03-18`
- Ran the real workspace full-stack city orchestration CLI on Phoenix:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_full_stack_orchestration --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31 --max-cells 100"`
- Observed output:
  - `data_processed/orchestration/full_stack_city_orchestration_summary.json`
  - `data_processed/orchestration/full_stack_city_orchestration_summary.csv`
  - Phoenix summary row reported `raw_support_acquisition_status=skipped_existing`, `support_layer_prep_status=skipped_existing`, `appeears_ndvi_status=skipped_existing`, `appeears_ecostress_status=skipped_existing`, `feature_assembly_status=skipped_existing`, `overall_status=completed`
  - The new full-stack runner successfully reused already-materialized Phoenix artifacts end to end without unnecessary reruns
- Investigated the 2026-03-18 Tucson raw-acquisition pause for `src.run_full_stack_orchestration --city-ids 2,3,4 ...`:
  - `data_raw/cache/nlcd/bundles/Annual_NLCD_LndCov_2015-2024_CU_C1V1.zip` is `13.12 GB`
  - `data_raw/cache/nlcd/bundles/Annual_NLCD_FctImp_2015-2024_CU_C1V1.zip` is `8.85 GB`
  - Cached hydro ZIPs for Tucson HU4 packages `1504` and `1505` were `515.01 MB` and `574.62 MB`, with extracted GeoPackages of `1038.59 MB` and `1145.52 MB`
  - The apparent "stall" was consistent with silent heavyweight I/O plus opaque post-download work, not an infinite loop in the clipping logic
- Ran a real-data Tucson hydro smoke timing after adding spatially filtered hydro reads:
  - `@'...collect_nhdplus_water_features...'@ | & '.\.venv\Scripts\python.exe' -`
- Observed output:
  - `NHDPLUS_H_1504_HU4_20220901_GPKG.gpkg rows=0 elapsed_s=0.28`
  - `NHDPLUS_H_1505_HU4_20220901_GPKG.gpkg rows=4307 elapsed_s=2.98`
  - This checkpoint manually verified that local hydro package reads are now fast once the `.gpkg` is on disk; the remaining long pole is the size of the official downloads plus any incomplete transfer such as Tucson HU4 `1508`
- Investigated the 2026-03-18 full-stack failures for cities `2,3,4`:
  - `appeears_ndvi_acquisition_summary.csv` shows Tucson, Las Vegas, and Albuquerque NDVI submissions all failed with `status=403` and the same permission-style response body for `MOD13A1.061`
  - `raw_data_acquisition_summary.csv` shows Las Vegas hydro failed on `NHDPLUS_H_1606_HU4_20220418_GPKG.zip` with `404`, while Albuquerque DEM and hydro failed on TNM Access product queries with `504 Gateway Timeout`
  - Official AppEEARS materials were checked and still document `POST /login` with Earthdata credentials followed by `Authorization: Bearer <token>` on `/task`, so the likely local defect was stale-token precedence rather than obsolete header formatting
- Investigated the AppEEARS rerun bug after task-completion emails arrived:
  - The persisted NDVI and ECOSTRESS summary rows already contained real `task_id` values for Tucson, Las Vegas, and Albuquerque
  - The old acquisition state machine still stored those active rows as `status=not_started`, so orchestration with `retry_incomplete=True` treated them as candidates for a fresh submission
  - The rerun logic now treats an existing nonterminal `task_id` as reusable work: poll first, download if done, and submit only when no usable saved task exists

### 2026-03-23 - Checkpoint: First-Pass Grouped Sklearn Modeling Layer Added

- Date / checkpoint:
  - 2026-03-23 first-pass ML layer built on top of the canonical final dataset and modeling-prep stage.
- Change made:
  - Added a shared modeling contract in `src/modeling_config.py` so the target column, grouping column, leakage exclusions, and first-pass safe feature set have one source of truth.
  - Added reusable data-loading/fold helpers in `src/modeling_data.py`, including fold-table validation, held-out-city split loading, deterministic optional per-city sampling, and explicit feature-contract export.
  - Added evaluation utilities in `src/modeling_metrics.py` for PR AUC, recall at top 10%, grouped metric tables, and calibration-curve tables.
  - Added `src/modeling_baselines.py` plus `src/run_modeling_baselines.py` for the first baseline suite: global mean, land-cover-only, impervious-only, and climate-only.
  - Added `src/modeling_runner.py`, `src/run_logistic_saga.py`, and `src/run_random_forest.py` for grouped held-out-city tuning/evaluation with sklearn `Pipeline`, `GroupKFold`, and `GridSearchCV`.
  - Added regression tests in `tests/test_modeling_contract.py` and `tests/test_modeling_runner.py`.
  - Updated `requirements.txt` to include `scikit-learn` and installed it into `.venv` so the new modeling layer can import and run.
  - Updated `README.md`, `docs/workflow.md`, `docs/data_dictionary.md`, and `docs/modeling_plan.md` to document the new ML stage and output structure.
- Files touched:
  - `src/modeling_config.py`
  - `src/modeling_data.py`
  - `src/modeling_metrics.py`
  - `src/modeling_baselines.py`
  - `src/modeling_runner.py`
  - `src/run_modeling_baselines.py`
  - `src/run_logistic_saga.py`
  - `src/run_random_forest.py`
  - `src/modeling_prep.py`
  - `tests/test_modeling_contract.py`
  - `tests/test_modeling_runner.py`
  - `requirements.txt`
  - `README.md`
  - `docs/workflow.md`
  - `docs/data_dictionary.md`
  - `docs/modeling_plan.md`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_modeling_baselines --sample-rows-per-city 5000"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_logistic_saga --sample-rows-per-city 5000"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_random_forest --sample-rows-per-city 5000"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m pytest tests/test_modeling_prep.py tests/test_modeling_contract.py tests/test_modeling_runner.py -q"`
- Test status:
  - `9 passed` for the targeted modeling subset above.
  - The run emitted sklearn 1.8 `FutureWarning` messages about the explicit `penalty` hyperparameter names in the logistic grid, but the tests passed.
- Manual verification status:
  - No fresh full canonical modeling run was executed in this checkpoint.
  - Manual verification remains limited to repo inspection, artifact-path checks, and the successful targeted test run after installing `scikit-learn`.
- Next recommended step:
  - Run the three new CLIs on the canonical dataset with a bounded `--sample-rows-per-city` smoke configuration, review the outputs under `outputs/modeling/`, then decide whether to scale up directly or introduce a dedicated sampled modeling dataset artifact.

Currently materialized on disk:

- `data_processed/study_areas/`: all 30 cities
- `data_processed/city_grids/`: all 30 cities at 30 m
- `data_processed/batch_city_processing_summary_30m.csv`
- `data_processed/appeears_aoi/`: Phoenix, Tucson, Las Vegas, Albuquerque
- `data_raw/cache/`: ready for reusable DEM/NLCD/hydro downloads but not yet populated by a full all-city acquisition run
- `data_raw/dem/`: Phoenix, Tucson, Las Vegas, Albuquerque
- `data_raw/nlcd/`: Phoenix, Tucson, Las Vegas, Albuquerque
- `data_raw/hydro/`: Phoenix, Tucson, Las Vegas, Albuquerque
- `data_raw/ndvi/`: Phoenix, Tucson, Las Vegas, Albuquerque
- `data_raw/ecostress/`: Phoenix, Tucson, Las Vegas, Albuquerque
- `data_processed/support_layers/`:
  - `support_layers_preflight_summary.json`
  - `support_layers_preflight_summary.csv`
  - `raw_data_acquisition_summary.json`
  - `raw_data_acquisition_summary.csv`
  - `support_layers_prep_summary.json`
  - `support_layers_prep_summary.csv`
  - `01_phoenix_az/dem_prepared.tif`
  - `01_phoenix_az/nlcd_land_cover_prepared.tif`
  - `01_phoenix_az/nlcd_impervious_prepared.tif`
  - `01_phoenix_az/hydro_water_prepared.gpkg`
  - `02_tucson_az/*`
  - `03_las_vegas_nv/*`
  - `04_albuquerque_nm/*`
- `data_processed/appeears_status/`:
  - `appeears_ndvi_preflight_summary.json`
  - `appeears_ndvi_preflight_summary.csv`
  - acquisition summaries for Phoenix, Tucson, Las Vegas, and Albuquerque for NDVI and ECOSTRESS
- `data_processed/orchestration/`:
  - `acquisition_orchestration_summary.json`
  - `acquisition_orchestration_summary.csv`
  - `full_stack_city_orchestration_summary.json`
  - `full_stack_city_orchestration_summary.csv`
- `data_processed/city_features/`:
  - per-city feature outputs for Phoenix, Tucson, Las Vegas, and Albuquerque
  - Phoenix was regenerated on 2026-03-19 in `cell_filter_mode=core_city`; Tucson, Las Vegas, and Albuquerque remain in buffered `study_area` mode

Explicit blocker statement:

- The prior manual blocker for standardized DEM/NLCD/hydro population is resolved in code.
- The current practical blocker for broader scaling is running the same pipeline for the remaining 26 unfinished cities and waiting for large official downloads and AppEEARS bundles to complete.
- The current operational risks are heavy NLCD/NHDPlus I/O, OneDrive-backed workspace churn on large files, and city-specific source quirks that have not yet been observed outside the first four completed cities.
- Overnight `core_city` runs now have one real-city proof point in Phoenix, but the study-area metadata refresh has not yet been applied across the other completed cities.

## Immediate Next Step

Superseding the older parquet-triage note, the current recommended next step is to standardize future modeling verification in this Codex session on the rebuilt repo-local `.venv` plus the canonical parquet artifacts, while keeping explicit `.\.venv\Scripts\python.exe -m ...` commands from the repo root:

- Keep the command prefix explicit:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_modeling_contract.py tests/test_modeling_runner.py -q`
  - `.\.venv\Scripts\python.exe -m src.run_logistic_saga --dataset-path data_processed\final\final_dataset.parquet --folds-path data_processed\modeling\city_outer_folds.parquet --sample-rows-per-city 5000 --outer-folds 0 --tuning-preset smoke --grid-search-n-jobs 1 --output-dir outputs\modeling\logistic_saga\parquet_verify`
  - `.\.venv\Scripts\python.exe -m src.run_random_forest --dataset-path data_processed\final\final_dataset.parquet --folds-path data_processed\modeling\city_outer_folds.parquet --sample-rows-per-city 5000 --outer-folds 0 --tuning-preset smoke --grid-search-n-jobs 1 --model-n-jobs 1 --output-dir outputs\modeling\random_forest\parquet_verify`
- Keep repo defaults distinct from sandbox smoke guidance:
  - the CLIs now document canonical parquet defaults directly
  - retain `smoke` as the default preset for bounded routine verification
  - treat `--grid-search-n-jobs 1` and `--model-n-jobs 1` as sandbox-specific stability settings, not universal requirements
- Treat CSV inputs as compatibility fallback only:
  - keep `data_processed/final/final_dataset.csv` and `data_processed/modeling/city_outer_folds.csv` for recovery/debugging paths
  - prefer parquet for canonical modeling because the current final CSV is not row-equivalent to the canonical parquet
- Treat virtual environments as disposable:
  - if `.venv\pyvenv.cfg` points to the wrong or inaccessible base interpreter, delete and recreate `.venv` from the correct accessible base instead of copying or trying to repair the old environment
- Continue using serial modeling flags in this sandbox because that remains the stable execution path here, and investigate the non-fatal Windows `joblib` cache-write warnings separately if cache reuse becomes important.
- After that baseline stays stable, the next broader modeling verification step should be a multi-fold parquet-backed smoke pass or a controlled all-fold smoke run before attempting any heavier `full` tuning run.



## Current Output Structure

- `data_processed/study_areas/`
- `data_processed/city_grids/`
- `data_processed/appeears_aoi/`
- `data_processed/appeears_status/`
- `data_processed/orchestration/`
- `data_processed/support_layers/`
- `data_processed/intermediate/aligned_rasters/`
- `data_processed/intermediate/city_features/`
- `data_processed/city_features/`
- `data_processed/final/`
- `data_processed/modeling/`
- `data_processed/modeling/baselines/`
- `outputs/data_processing/<city_stem>/`
- `outputs/data_processing/data_processing_report_summary.csv`
- `outputs/modeling/`
- `outputs/modeling/baselines/`
- `outputs/modeling/logistic_saga/`
- `outputs/modeling/logistic_saga/parquet_verify/`
- `outputs/modeling/random_forest/`
- `outputs/modeling/random_forest/parquet_verify/`
- `outputs/storage/`
- `figures/data_processing/<city_stem>/`
- `figures/modeling/`
- `data_raw/cache/`
- `data_raw/dem/<city_slug>/`
- `data_raw/nlcd/<city_slug>/`
- `data_raw/hydro/<city_slug>/`
- `data_raw/ndvi/<city_slug>/`
- `data_raw/ecostress/<city_slug>/`

## Not Started Yet / Open Issues

- Full all-city raw DEM acquisition has not been executed yet.
- Full all-city raw NLCD acquisition/clipping has not been executed yet.
- Full all-city raw hydro acquisition/clipping has not been executed yet.
- Full support-layer prep has not yet been materialized beyond the first four completed cities.
- Full all-city AppEEARS acquisition has not been executed yet; current completed coverage is Phoenix, Tucson, Las Vegas, and Albuquerque.
- No full canonical run of `src.run_modeling_baselines`, `src.run_logistic_saga`, or `src.run_random_forest` has been recorded yet on the real `71,394,894`-row final dataset.
- The old parquet failure signatures are not reproducible in the rebuilt `.venv`; canonical parquet reads and parquet-backed smoke runs are now verified on `pandas 3.0.1` plus `pyarrow 23.0.1`.
- `data_processed/final/final_dataset.csv` is not currently row-equivalent to the canonical parquet (`48,522,748` vs `71,394,894` rows across the same 14 columns), so the CSV path should remain fallback-only unless the CSV artifact is deliberately regenerated.
- The rebuilt `.venv` smoke runs still required `--grid-search-n-jobs 1` and, for random forest, `--model-n-jobs 1` because the Windows sandbox still makes serial execution the stable path here.
- The smoke runs completed, but `joblib` pipeline-cache writes still emitted non-fatal warnings under the current Windows workspace paths, so cache effectiveness is not yet fully verified.
- Held-out-city map exports and figure generation under `figures/modeling/` are still not implemented.
- The current sklearn-based first-pass runners may still need a scaling strategy or dedicated sampled dataset if full-canonical runtime or memory is too heavy on a workstation.
- Preflight summary CSVs should be regenerated before using them as authoritative global readiness counts, because the current disk state now extends beyond the older Phoenix-only checkpoint.
- Broader cross-climate validation beyond the first four Southwestern cities is still pending.
- The new cache cleanup utility has not yet been run in live delete mode; only dry-run audit/plan manifests were generated on 2026-03-19.
- The new full-stack city orchestration starts at raw support acquisition, not city boundary/grid generation; city-processing remains a separate prerequisite for cities missing study areas or grids.
- Additional uncapped city-by-city feature validation beyond the first four completed cities is still pending.
- Full 30-city end-to-end dataset generation at 30 m remains pending data acquisition/runtime.
- Raw support acquisition still depends on very large official NLCD and NHDPlus source downloads; long wall-clock times are expected even when the code is behaving correctly.
- `data_processed/city_grids/` is now a separate major storage hotspot at about `25.09 GB` and will need its own retention/compression review after cache cleanup.
- Minneapolis still depends on the fresh AppEEARS ECOSTRESS task submitted on 2026-03-23 finishing remotely before city-level feature assembly can complete.
- The current `city_outer_folds` logic balances cities by row count and city count, not by hotspot prevalence; revisit if stricter target-stratified folds are needed for later modeling experiments.
- The new baseline-modeling stage has not yet been run end to end on the canonical `final_dataset.parquet`; current verification is synthetic-fixture testing plus the already-completed canonical modeling-prep verification.
- Legacy Phoenix-only root-level report artifacts under `outputs/phoenix_data_summary*` still exist from pre-refactor runs; the new code writes only to the split stage-specific structure, but the old generated files were not deleted automatically in this checkpoint.
- Held-out-city map deliverables, residual/error maps, and the application-to-new-cities workflow are still planned rather than implemented.

## Checkpoint Log

### 2026-03-25 - Checkpoint: Modeling Workflow Docs And Defaults Hardened Around Parquet-First .venv

- Date / checkpoint:
  - 2026-03-25 parquet-first modeling workflow cleanup after canonical `.venv` smoke verification.
- Change made:
  - Tightened the logistic and random-forest CLI help text so the documented defaults now explicitly match reality: repo-local `.venv` usage, canonical parquet input, parquet-preferred fold resolution, CSV compatibility fallback, and bounded `smoke` preset wording.
  - Added focused regression coverage for parquet-preferred fold resolution plus CLI help/default text that locks in the canonical parquet-first path without removing CSV support.
  - Refreshed `README.md` and the current-state sections of this handoff so command examples consistently use `.\.venv\Scripts\python.exe -m ...`, parquet is called out as the canonical modeling source, CSV is called out as non-interchangeable fallback, and the verified parquet smoke commands remain the normal reference point.
- Files touched:
  - `README.md`
  - `docs/chat_handoff.md`
  - `src/modeling_data.py`
  - `src/run_logistic_saga.py`
  - `src/run_random_forest.py`
  - `tests/test_modeling_contract.py`
  - `tests/test_modeling_runner.py`
- How to run:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_modeling_contract.py tests/test_modeling_runner.py -q`
  - `.\.venv\Scripts\python.exe -m src.run_logistic_saga --help`
  - `.\.venv\Scripts\python.exe -m src.run_random_forest --help`
- Test status:
  - Focused modeling subset passed: `18 passed`.
  - Both tuned-model CLI help commands completed successfully.
- Manual verification status:
  - No new long-running parquet smoke model fit was needed because runtime behavior did not change.
  - Verified directly from the live CLI help output that the user-facing defaults now describe parquet-first guidance instead of the older fallback/debug framing.
- Next recommended step:
  - Run a broader parquet-backed smoke verification pass, for example more outer folds or all smoke folds, before attempting any heavier full-tuning run.

### 2026-03-25 - Checkpoint: Canonical Parquet Path Re-Verified In Rebuilt .venv

- Date / checkpoint:
  - 2026-03-25
- Change made:
  - Reproduced parquet reads directly in the rebuilt repo-local `.venv` using both `pandas` and low-level `pyarrow`.
  - Verified that `data_processed/final/final_dataset.parquet` and `data_processed/modeling/city_outer_folds.parquet` both read successfully, including schema/metadata inspection and subset row-group reads.
  - Confirmed the old `OSError: Repetition level histogram size mismatch` signature does not reproduce in the current environment.
  - Manually reran the smoke logistic and random-forest CLIs against the canonical parquet artifacts and recorded successful outputs under `outputs/modeling/logistic_saga/parquet_verify/` and `outputs/modeling/random_forest/parquet_verify/`.
  - Updated repo docs so parquet is again the primary verified modeling path in this sandbox and CSV is documented as a compatibility fallback only.
- Files touched:
  - `README.md`
  - `docs/chat_handoff.md`
- How to run:
  - `.\.venv\Scripts\python.exe -c "import sys, platform, pandas as pd, pyarrow, geopandas as gpd; print(sys.version); print(platform.platform()); print('pandas', pd.__version__); print('pyarrow', pyarrow.__version__); print('geopandas', gpd.__version__)"`
  - `.\.venv\Scripts\python.exe -m src.run_logistic_saga --dataset-path data_processed\final\final_dataset.parquet --folds-path data_processed\modeling\city_outer_folds.parquet --sample-rows-per-city 5000 --outer-folds 0 --tuning-preset smoke --grid-search-n-jobs 1 --output-dir outputs\modeling\logistic_saga\parquet_verify`
  - `.\.venv\Scripts\python.exe -m src.run_random_forest --dataset-path data_processed\final\final_dataset.parquet --folds-path data_processed\modeling\city_outer_folds.parquet --sample-rows-per-city 5000 --outer-folds 0 --tuning-preset smoke --grid-search-n-jobs 1 --model-n-jobs 1 --output-dir outputs\modeling\random_forest\parquet_verify`
- Test status:
  - No new pytest suite was needed in this checkpoint; the earlier rebuilt-`.venv` focused modeling subset still stands at `15 passed`.
- Manual verification status:
  - `pandas.read_parquet(...)` and `pyarrow.parquet.ParquetFile(...)` both succeeded for the real canonical dataset and fold parquet files.
  - `pyarrow.parquet.read_metadata(...)` succeeded for both files; metadata reports `created_by=parquet-cpp-arrow version 23.0.1`.
  - Logistic parquet smoke completed in `351.79s` with `pooled_pr_auc=0.1729` and `pooled_recall_at_top_10pct=0.2171`.
  - Random-forest parquet smoke completed in `291.03s` with `pooled_pr_auc=0.1865` and `pooled_recall_at_top_10pct=0.2499`.
  - The remaining modeling caveats are non-fatal Windows `joblib` cache-write warnings, serial-only stable execution flags, and the stale non-equivalent final CSV artifact.
- Next recommended step:
  - Keep future smoke checks on parquet in the rebuilt `.venv`, then choose between a broader all-fold canonical modeling run or deliberate regeneration of `data_processed/final/final_dataset.csv` if CSV parity is still needed.

### 2026-03-24 - Checkpoint: Modeling Environment Unblocked Via CSV Fallback And Real Smoke Verification

- Date / checkpoint:
  - 2026-03-24 modeling execution unblock and honest smoke verification after the earlier runtime-instrumentation pass.
- Change made:
  - Confirmed the repo `.venv` already contains the geospatial/modeling packages on disk, so the latest blocker in this Codex session is the venv launcher returning `Access is denied`, not a missing dependency set.
  - Moved the final-dataset column contract into `src.final_dataset_contract` so the modeling import path no longer pulls `src.feature_assembly` / `geopandas` at import time.
  - Added CSV support to the modeling data loader, including deterministic chunked per-city sampling, so the smoke runners can execute against `final_dataset.csv` when the parquet artifact is unreadable in the active interpreter.
  - Replaced `tempfile.TemporaryDirectory` cache-dir creation in `src.modeling_runner` with a plain managed `Path.mkdir()` directory to avoid Windows temp-directory permission failures in this session.
  - Updated the focused modeling tests to use workspace-backed temp paths and serial grid-search settings so the modeled behavior, not the host temp/multiprocessing implementation, is what gets verified.
  - Completed one real sampled smoke run for tuned logistic SAGA and one for tuned random forest using the accessible interpreter, CSV dataset fallback, CSV folds artifact, and serial grid-search settings.
- Files touched:
  - `src/final_dataset_contract.py`
  - `src/feature_assembly.py`
  - `src/modeling_prep.py`
  - `src/modeling_data.py`
  - `src/modeling_runner.py`
  - `tests/conftest.py`
  - `tests/test_modeling_contract.py`
  - `tests/test_modeling_runner.py`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\Users\golde\anaconda3\python.exe -m pytest tests/test_modeling_contract.py tests/test_modeling_runner.py -q`
  - `C:\Users\golde\anaconda3\python.exe -m src.run_logistic_saga --dataset-path data_processed\final\final_dataset.csv --folds-path data_processed\modeling\city_outer_folds.csv --sample-rows-per-city 5000 --outer-folds 0 --tuning-preset smoke --grid-search-n-jobs 1 --output-dir outputs\modeling\logistic_saga\vcsv`
  - `C:\Users\golde\anaconda3\python.exe -m src.run_random_forest --dataset-path data_processed\final\final_dataset.csv --folds-path data_processed\modeling\city_outer_folds.csv --sample-rows-per-city 5000 --outer-folds 0 --tuning-preset smoke --grid-search-n-jobs 1 --model-n-jobs 1 --output-dir outputs\modeling\random_forest\vcsv`
- Test status:
  - Focused modeling subset passed: `15 passed` via `C:\Users\golde\anaconda3\python.exe -m pytest tests/test_modeling_contract.py tests/test_modeling_runner.py -q`.
- Manual verification status:
  - Direct `.venv` execution still failed immediately with `Access is denied`.
  - `final_dataset.parquet` still aborted inside `pyarrow` reads in the accessible interpreter, and `city_outer_folds.parquet` still failed with `Repetition level histogram size mismatch`.
  - Logistic smoke completed in `824.36s` wall clock with `sampled_city_preload=270.32s`, `grid_search_seconds=532.12s`, `pr_auc=0.1739`, and `recall_at_top_10pct=0.2199`.
  - Random-forest smoke completed in `313.08s` wall clock with `sampled_city_preload=86.10s`, `grid_search_seconds=223.17s`, `pr_auc=0.1808`, and `recall_at_top_10pct=0.1998`.
  - Both real smoke runs completed despite non-fatal `joblib` cache warnings under the current Windows workspace paths.
- Next recommended step:
  - Repair or regenerate the canonical parquet artifacts and rerun the same smoke commands against parquet in a Python environment where the repo `.venv` launcher is actually executable.

### 2026-03-24 - Checkpoint: Tuned Runtime Smoke Preset And Timing Instrumentation

- Date / checkpoint:
  - 2026-03-24 tuned modeling runtime reduction and observability pass after the categorical preprocessing fix.
- Change made:
  - Traced the remaining tuned workload from the existing config and fold artifact: `5` outer folds with `6` cities per fold, so the old defaults implied `20 x up to 4 = 80` inner fits per outer fold for logistic (`400` total) and `81 x up to 4 = 324` per outer fold for random forest (`1620` total).
  - Added explicit `smoke` and `full` tuning presets in `src.modeling_config`; the new smoke defaults are `4` candidate combinations for logistic, `4` for random forest, and `3` requested inner CV splits.
  - Updated `src.modeling_runner` to preload sampled city rows once per run, split folds in memory for sampled runs, enable safe per-fold sklearn pipeline caching, and log/write concise timing diagnostics for contract enforcement, data loading, preprocessing build/probe, grid search, and total wall-clock.
  - Updated `src.run_logistic_saga` and `src.run_random_forest` to default to `--tuning-preset smoke` while preserving `--tuning-preset full` for the heavier historical search.
  - Added tests for tuning-preset size differences, runtime metadata fields, sampled preload behavior, and the new CLI default preset.
- Files touched:
  - `src/modeling_config.py`
  - `src/modeling_runner.py`
  - `src/run_logistic_saga.py`
  - `src/run_random_forest.py`
  - `tests/test_modeling_runner.py`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_logistic_saga --sample-rows-per-city 5000 --outer-folds 0 --tuning-preset smoke"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_random_forest --sample-rows-per-city 5000 --outer-folds 0 --tuning-preset smoke"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_logistic_saga --sample-rows-per-city 5000 --tuning-preset full"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_random_forest --sample-rows-per-city 5000 --tuning-preset full"`
- Test status:
  - Syntax compilation passed for the edited files via `cmd /c call "C:\Users\golde\anaconda3\python.exe" -m py_compile ...`.
  - Grid-size probe passed and confirmed `logistic_smoke=4`, `logistic_full=20`, `rf_smoke=4`, `rf_full=81`.
  - Focused pytest collection under the accessible fallback interpreter failed with `ModuleNotFoundError: No module named 'geopandas'`.
- Manual verification status:
  - Not manually verified on the canonical parquet in this checkpoint.
  - Direct `.venv\Scripts\python.exe` execution returned `Access is denied` in this Codex session, and the accessible Anaconda interpreter could not import the full geospatial dependency stack.
- Next recommended step:
  - Re-run the new smoke commands inside a working full-dependency venv, then record the resulting `run_metadata.json` wall-clock timings before deciding whether additional scaling changes are still needed.

### 2026-03-23 - Checkpoint: Tuned Modeling Preprocessing Contract Fixed

- Date / checkpoint:
  - 2026-03-23 tuned modeling preprocessing regression fix on top of the canonical modeling handoff.
- Change made:
  - Replaced the loose split-by-membership logic with a single shared feature-type contract in `src.modeling_config`.
  - Updated `src.modeling_data` to reject requested features that are missing an explicit modeling type contract and to write the resolved type map into `feature_contract.json`.
  - Updated `src.modeling_runner` so numeric columns are coerced with `pd.to_numeric(...)` before numeric imputation, while categorical columns are coerced to plain object/string values with `np.nan` missing markers before categorical imputation and encoding.
  - Set tuned `GridSearchCV` defaults to use `n_jobs=-1` so the exact CLI smoke-test commands no longer default to single-core grid search.
  - Added targeted regression tests for `hot_arid`-style categorical values with missing data and for accidental routing of categorical features into the numeric transformer.
- Files touched:
  - `src/modeling_config.py`
  - `src/modeling_data.py`
  - `src/modeling_runner.py`
  - `src/run_logistic_saga.py`
  - `src/run_random_forest.py`
  - `tests/test_modeling_contract.py`
  - `tests/test_modeling_runner.py`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m pytest tests/test_modeling_contract.py tests/test_modeling_runner.py -q"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_logistic_saga --sample-rows-per-city 5000"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_random_forest --sample-rows-per-city 5000"`
- Test status:
  - Focused tuned-modeling regression subset passed: `10 passed`.
- Manual verification status:
  - The exact tuned smoke commands now progress past the previous sklearn preprocessing failure and refresh `feature_contract.json`, but they did not finish within the available 20-60 minute verification windows on the canonical parquet.
  - Full tuned artifact generation on the real canonical parquet is therefore not yet manually verified complete in this checkpoint.
- Next recommended step:
  - Choose an explicit smoke-mode runtime strategy for tuned modeling so canonical verification can finish in a bounded unattended run.

### 2026-03-23 - Checkpoint: All-City Data-Processing Reporting Generalized

- Date / checkpoint:
  - 2026-03-23 generalized Phoenix-only reporting into a shared all-city data-processing reporting stage.
- Change made:
  - Added `src.data_processing_reporting` to generate the existing Phoenix-style markdown summary, supporting tables, and four figures for any city with materialized feature outputs.
  - Added `src.run_data_processing_reports` so the same reporting stage can be run explicitly for all configured cities or a selected subset.
  - Converted `src.summarize_phoenix_dataset` into a Phoenix compatibility wrapper over the shared reporting implementation.
  - Added stage-specific output roots in `src.config` so data-processing reports now write under `outputs/data_processing/<city_stem>/` and `figures/data_processing/<city_stem>/`, with parallel `outputs/modeling/` and `figures/modeling/` roots reserved for future ML/evaluation artifacts.
  - Reused the existing Phoenix report artifact pattern rather than inventing new metrics or figure classes, and updated docs to explain the split output structure.
- Files touched:
  - `src/config.py`
  - `src/city_processing.py`
  - `src/feature_assembly.py`
  - `src/data_processing_reporting.py`
  - `src/summarize_phoenix_dataset.py`
  - `src/run_data_processing_reports.py`
  - `tests/test_data_processing_reporting.py`
  - `README.md`
  - `docs/workflow.md`
  - `docs/data_dictionary.md`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_data_processing_reports"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_data_processing_reports --city-ids 1,2,3,4"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.summarize_phoenix_dataset"`
- Test status:
  - Focused reporting subset passed: `4 passed`.
  - Focused city-processing/feature-assembly regression subset passed: `16 passed`.
- Manual verification status:
  - Phoenix smoke run completed successfully through `src.run_data_processing_reports --city-ids 1`.
  - Verified real outputs at `outputs/data_processing/01_phoenix_az/phoenix_data_summary.md`, `outputs/data_processing/01_phoenix_az/tables/*.csv`, `figures/data_processing/01_phoenix_az/*.png`, and `outputs/data_processing/data_processing_report_summary.csv`.
  - Full all-city live reporting was not run in this checkpoint.
- Next recommended step:
  - Run `src.run_data_processing_reports` against all currently completed cities, then rerun it after the remaining cities finish feature assembly so the full 30-city reporting set is materialized in the new staged layout.

### 2026-03-23 - Checkpoint: Remove Obsolete Exploratory Notebooks

- Date / checkpoint:
  - 2026-03-23 repository housekeeping for obsolete exploratory notebooks.
- Change made:
  - Removed the untracked production-irrelevant `notebooks/` workspace, including the old city-point and boundary-check inspection notebooks plus `.ipynb_checkpoints/`.
  - Deleted the unused `NOTEBOOKS` path constant from `src/config.py`.
  - Removed the stale `notebooks/` repo-layout reference from `README.md`.
- Files touched:
  - `src/config.py`
  - `README.md`
  - `docs/chat_handoff.md`
  - removed `notebooks/01_city_points_check.ipynb`
  - removed `notebooks/02_boundary_check.ipynb`
  - removed `notebooks/.ipynb_checkpoints/*`
- How to run:
  - No runtime entrypoint changed.
  - Verification command used: `rg -n "notebooks|/notebooks|\\notebooks|NOTEBOOKS" .`
- Test status:
  - No tests run; this was a docs/config/tree cleanup only.
- Manual verification status:
  - Verified before deletion that no production code imported or used `src.config.NOTEBOOKS`.
  - Verified after deletion that the repo-wide search returned only the historical notebook-removal notes in `docs/chat_handoff.md`, with no remaining production/runtime references.
- Next recommended step:
  - Continue with the existing next milestone: run the first real canonical baseline-modeling pass from the verified final dataset.

### 2026-03-23 - Checkpoint: Documentation Architecture Redesign

- Date / checkpoint:
  - 2026-03-23 documentation and repo-navigation redesign.
- Change made:
  - Rewrote `README.md` as the project landing page for the full urban-heat ML workflow instead of a long stage inventory.
  - Reworked `docs/workflow.md` into an end-to-end lifecycle document covering study design, acquisition, feature assembly, modeling prep, baselines, planned main models, evaluation, and deliverables.
  - Refocused `docs/data_dictionary.md` on canonical columns, artifact families, and dataset locations rather than repeating pipeline narration.
  - Added `docs/modeling_plan.md` to document the grouped-city modeling contract, baseline stage, planned `solver="saga"` logistic-regression and random-forest setups, and evaluation roadmap.
  - Kept the physical repo structure stable in this checkpoint to avoid breaking working code; the structure change is primarily a clearer documentation scheme.
- Files touched:
  - `README.md`
  - `docs/workflow.md`
  - `docs/data_dictionary.md`
  - `docs/modeling_plan.md`
  - `docs/chat_handoff.md`
- How to run:
  - Open `README.md`, then follow the links to `docs/workflow.md`, `docs/data_dictionary.md`, `docs/modeling_plan.md`, and `docs/chat_handoff.md`.
- Test status:
  - No tests run in this checkpoint because the change was documentation-only.
- Manual verification status:
  - Verified doc accuracy against the current top-level repo layout and existing implemented CLI stages.
  - Confirmed the docs now clearly separate implemented, test-verified, manually verified, and planned-next work.
- Next recommended step:
  - Run the first real canonical baseline-modeling pass, then use the new docs as the project-facing reference for the next modeling implementation stage.

### 2026-03-23 - Checkpoint: Baseline Modeling Stage Implemented

- Date / checkpoint:
  - 2026-03-23 first baseline-modeling stage added on top of the verified canonical modeling-prep artifacts.
- Change made:
  - Added `src.model_baselines` with streaming parquet batch readers, fold joins on `city_id`, train-fold-only preprocessing, a full-data logistic regression baseline, and a lightweight decision-stump comparison.
  - Added `src.run_model_baselines` as the reproducible CLI entrypoint for fold-by-fold city-held-out baseline training/evaluation.
  - Added artifact writing for fold metrics, overall metrics, leakage checks, assumptions, validation predictions, logistic coefficients, and stump rules under `data_processed/modeling/baselines/`.
  - Added focused regression tests and updated README/workflow/data-dictionary docs to document the new stage.
- Files touched:
  - `src/model_baselines.py`
  - `src/run_model_baselines.py`
  - `tests/test_model_baselines.py`
  - `README.md`
  - `docs/workflow.md`
  - `docs/data_dictionary.md`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m pytest tests/test_model_baselines.py tests/test_modeling_prep.py -q"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m src.run_model_baselines"`
- Test status:
  - `8 passed` for `tests/test_model_baselines.py` plus `tests/test_modeling_prep.py`.
- Manual verification status:
  - Synthetic-fixture end-to-end artifact writing is covered by tests.
  - No full canonical run of `src.run_model_baselines` has been executed yet in this checkpoint because the canonical dataset is very large and the new stage is expected to be a long-running job.
- Next recommended step:
  - Run `src.run_model_baselines` on the real canonical parquet/fold artifacts, then inspect the fold metrics, leakage checks, and saved validation predictions before expanding to richer model classes.

### 2026-03-23 - Checkpoint: Modeling Handoff Verified On Canonical Final Dataset

- Date / checkpoint:
  - 2026-03-23 continuation focused on finishing the modeling-prep verification and handoff.
- Change made:
  - Confirmed the new modeling-prep modules, tests, and docs were already present in the working tree and treated them as the source of truth.
  - Found a real-data `MemoryError` in the first canonical `src.audit_final_dataset` run because the implementation loaded the full final parquet into memory.
  - Tightened `src.modeling_prep` so required-column validation uses parquet schema metadata and both the audit and fold paths load only the columns they actually need.
  - Added a small regression test covering subset-column parquet loading.
  - Verified the docs already matched the implemented modeling CLI names and output paths, so no README/workflow/data-dictionary wording changes were needed in this continuation.
- Files touched:
  - `src/modeling_prep.py`
  - `tests/test_modeling_prep.py`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m pytest tests/test_modeling_prep.py -q"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m src.audit_final_dataset"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m src.make_model_folds --n-splits 5"`
- Test status:
  - `4 passed` for `tests/test_modeling_prep.py`.
- Manual verification status:
  - Verified on the real canonical dataset after the column-selective fix: audit completed for `71,394,894` rows across `30` cities and fold generation completed with `5` folds.
  - Verified deterministic output by rerunning `src.make_model_folds --n-splits 5` and confirming the CSV SHA-256 hash stayed unchanged.
- Next recommended step:
  - Start city-held-out baseline modeling from the verified current `final_dataset.parquet` plus `city_outer_folds.*`, and rerun assembly/audit/folds whenever upstream feature outputs materially change.

### 2026-03-23 - Checkpoint: ECOSTRESS Download Retry, Exception Summary, And GeoPackage Hardening

- Date / checkpoint:
  - 2026-03-23 follow-up after reviewing `full_run_v2.txt` and the saved full-stack/AppEEARS summaries.
- Change made:
  - Confirmed cities `16=Miami`, `17=Jacksonville`, `18=Atlanta`, and `19=Charlotte` failed at AppEEARS ECOSTRESS bundle download after `remote_task_status=done` because a single `ConnectionResetError(10054)` was treated as a terminal city failure.
  - Confirmed city `28=Minneapolis` was not truly unstarted; its saved ECOSTRESS task remained remote `processing`, so the city was still incomplete rather than crashed.
  - Added AppEEARS bundle-download retry handling for recoverable connection and retryable HTTP failures, preserving resumable/idempotent download behavior.
  - Expanded raw/support/AppEEARS/full-stack summary rows to serialize `exception_type`, `exception_message`, and `traceback`, and added a full-stack `stage` field pointing at the primary failed or incomplete stage.
  - Made the full-stack CLI route logs/warnings to stdout and return explicit exit codes instead of relying on PowerShell-native stderr behavior.
  - Normalized hydro vector geometries to 2D before write and switched GeoPackage temp writes to `.tmp.gpkg` atomic outputs.
- Files touched:
  - `src/appeears_client.py`
  - `src/appeears_acquisition.py`
  - `src/full_stack_orchestration.py`
  - `src/run_full_stack_orchestration.py`
  - `src/raw_data_acquisition.py`
  - `src/support_layers.py`
  - `src/feature_assembly.py`
  - `src/error_utils.py`
  - `src/vector_io.py`
  - `tests/test_appeears_client.py`
  - `tests/test_appeears_acquisition.py`
  - `tests/test_full_stack_orchestration.py`
  - `tests/test_support_layers.py`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_full_stack_orchestration --city-ids 16,17,18,19,28 --start-date 2023-05-01 --end-date 2023-08-31 --cell-filter-mode core_city"`
- Test status:
  - Verified by `36 passed` from the targeted pytest subset covering AppEEARS client/acquisition, full-stack orchestration, and support-layer vector normalization.
- Manual verification status:
  - No live rerun executed yet after the patch set; the saved 2026-03-22 summary/log artifacts remain the source for the root-cause diagnosis.
- Next recommended step:
  - Run the five-city rerun above, then confirm the full-stack summary counts move from `completed=25, failed=4, not_started=1` to either all completed or only Minneapolis remaining incomplete if its remote task is still processing.

### 2026-03-23 - Checkpoint: Fresh Minneapolis ECOSTRESS Submission Requested

- Date / checkpoint:
  - 2026-03-23 manual intervention after confirming the reused Minneapolis task continued to report `remote_task_status=processing`.
- Change made:
  - Backed up the prior ECOSTRESS acquisition summaries before intervention.
  - Reset only the saved Minneapolis ECOSTRESS task state so orchestration would stop reusing the old task id.
  - Submitted a fresh AppEEARS ECOSTRESS request for city `28`.
- Files touched:
  - `data_processed/appeears_status/appeears_ecostress_acquisition_summary.json`
  - `data_processed/appeears_status/appeears_ecostress_acquisition_summary.csv`
  - backup snapshots `data_processed/appeears_status/appeears_ecostress_acquisition_summary.20260323_151049.bak.json|csv`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_full_stack_orchestration --city-ids 28 --start-date 2023-05-01 --end-date 2023-08-31 --cell-filter-mode core_city"`
- Test status:
  - No code changes in this checkpoint; no additional pytest run was needed.
- Manual verification status:
  - Verified a fresh AppEEARS row for Minneapolis with `status=submitted`, `task_name=ecostress_minneapolis_2023-05-01_2023-08-31`, and new `task_id=31c8a14a-8869-44ef-a105-a6ec6688efeb`.
- Next recommended step:
  - Poll/download via the Minneapolis-only full-stack command above until the new task turns `done` and feature outputs materialize.

### 2026-03-21 - Checkpoint: TNM 504 Classification And Premature-Response Wrapper Fixed

- Date / checkpoint:
  - 2026-03-21 follow-up fixes after reviewing `rerun_affected.log`.
- Change made:
  - Added structured raw-acquisition classification for retry-exhausted TNM `/products` `502/503/504` `HTTPError` failures, mapping them to recoverable `tnm_upstream_http_error` under `upstream_dependency` instead of `unexpected_error`.
  - Expanded the malformed-wrapper detector to treat `Response ended prematurely` bodies with the TNM `get_products.py` stack trace as `sciencebase_upstream_error`.
  - Kept the existing 6-attempt retry behavior unchanged for wrapped upstream TNM failures.
  - Added regression tests for the `Response ended prematurely` wrapper and the retry-exhausted TNM `504` classification path.
- Files touched:
  - `src/raw_data_acquisition.py`
  - `tests/test_raw_data_acquisition.py`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m pytest tests/test_raw_data_acquisition.py tests/test_full_stack_orchestration.py -q"`
- Test status:
  - Focused ScienceBase/TNM retry subset passed: `22 passed`.
- Manual verification status:
  - The remaining failure signatures were confirmed from `rerun_affected.log`.
  - No fresh live rerun was executed after this code change.
- Next recommended step:
  - Rerun the affected full-stack batch once more and confirm city `14` hydro now records `tnm_upstream_http_error` and city `23` no longer emits `invalid_json_response` for the premature-response wrapper variant.

### 2026-03-20 - Checkpoint: TNM Wrapper Classification And DEM Missing-Tile Handling Fixed

- Date / checkpoint:
  - 2026-03-20 follow-up fixes from `full_run.log` crash analysis.
- Change made:
  - Expanded TNM malformed-body detection so wrapper payloads containing `RemoteDisconnected`, `Connection aborted`, `Remote end closed connection`, or `get_products.py` classify as `sciencebase_upstream_error` instead of generic `invalid_json_response`.
  - Preserved the extended retry behavior for those wrapped upstream failures at `6` attempts with exponential backoff.
  - Fixed raw-acquisition TLS classification to import `SSLError` from `requests.exceptions`, removing the `AttributeError: module 'requests' has no attribute 'SSLError'` crash path.
  - Changed empty TNM DEM tile selections to raise a structured recoverable `dem_tiles_not_found` / `data_unavailable` failure instead of a bare `RuntimeError`.
  - Added regression tests for the `RemoteDisconnected` TNM wrapper, structured DEM missing-tile handling, and the `SSLError` classifier path.
- Files touched:
  - `src/raw_data_acquisition.py`
  - `tests/test_raw_data_acquisition.py`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m pytest tests/test_raw_data_acquisition.py tests/test_full_stack_orchestration.py -q"`
- Test status:
  - Focused ScienceBase/TNM retry subset passed: `20 passed`.
- Manual verification status:
  - No fresh live rerun was executed in this checkpoint.
  - The failure signatures were confirmed directly from `full_run.log`, and the fix is currently test-verified rather than manually rerun against the affected cities.
- Next recommended step:
  - Rerun `src.run_full_stack_orchestration --city-ids 5,6,7,21,27 --start-date 2023-05-01 --end-date 2023-08-31` and confirm the new raw-acquisition summary rows show `sciencebase_upstream_error` or `dem_tiles_not_found` without aborting the full pipeline.

### 2026-03-20 - Checkpoint: Network Recovery Paths Hardened For Raw Acquisition And AppEEARS

- Date / checkpoint:
  - 2026-03-20 hardening based on the `cities5.30logfile.txt` orchestration failures for cities `5,6,7,21,27`.
- Change made:
  - Added resumable raw-download support that preserves `.part` files and resumes interrupted hydro ZIP transfers instead of restarting from scratch.
  - Hardened TNM product queries so transient invalid/non-JSON bodies are retried and reported as structured payload failures rather than crashing in `response.json()`.
  - Added a narrower TNM special case for malformed pseudo-JSON that wraps ScienceBase upstream failures, classifying it as `sciencebase_upstream_error` under `upstream_dependency` with a longer retry/backoff policy.
  - Kept dead HU4 package URLs as warnings only when at least one intersecting package succeeds; otherwise the hydro dataset still fails cleanly.
  - Hardened AppEEARS submit handling so ambiguous timeout/connection failures first try to recover by deterministic `task_name`, and otherwise persist a recoverable structured failure instead of a generic opaque error.
  - Propagated `failure_reason` / `recoverable` fields into AppEEARS summaries and full-stack orchestration stage rows.
  - Clarified TNM retry logging by emitting a final-attempt error line when no retries remain, removing ambiguity about whether `attempt 1/4`, `2/4`, `3/4`, then fail means three or four effective tries.
  - Added regression tests for interrupted hydro downloads, TNM invalid JSON, the ScienceBase malformed-body wrapper, recoverable AppEEARS submit failures, ambiguous submit recovery by task name, and full-stack failure-metadata propagation.
- Files touched:
  - `src/raw_data_acquisition.py`
  - `src/appeears_client.py`
  - `src/appeears_acquisition.py`
  - `src/full_stack_orchestration.py`
  - `tests/test_raw_data_acquisition.py`
  - `tests/test_appeears_client.py`
  - `tests/test_appeears_acquisition.py`
  - `tests/test_full_stack_orchestration.py`
  - `docs/workflow.md`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m pytest tests/test_raw_data_acquisition.py tests/test_appeears_client.py tests/test_appeears_acquisition.py tests/test_full_stack_orchestration.py -q"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m pytest tests/test_acquisition_orchestration.py -q"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_full_stack_orchestration --city-ids 5,6,7,21,27 --start-date 2023-05-01 --end-date 2023-08-31"`
- Test status:
  - Focused hardening subset passed: `35 passed`.
  - Focused ScienceBase/TNM retry subset passed: `16 passed`.
  - Acquisition orchestration compatibility subset passed: `2 passed`.
- Manual verification status:
  - No live rerun was executed in this checkpoint.
  - Verification is currently unit/integration-test based plus failure-path tracing from the attached orchestration log.
- Next recommended step:
  - Rerun cities `5,6,7,21,27` and inspect the raw/AppEEARS/full-stack summaries for the new `failure_reason`, `recoverable`, and raw hydro `warnings` fields.

### 2026-03-20 - Checkpoint: .env.local Bootstrap Added For AppEEARS CLIs

- Date / checkpoint:
  - 2026-03-20 local-development environment bootstrap for AppEEARS credentials.
- Change made:
  - Added `src.env_bootstrap` to load `PROJECT_ROOT/.env.local` without overriding existing exported environment variables.
  - Wired that bootstrap into `src.run_full_stack_orchestration`, `src.run_acquisition_orchestration`, and `src.run_appeears_acquisition` before any AppEEARS-related imports can read environment variables.
  - Added INFO logging that confirms `.env.local` was loaded, without logging secrets.
  - Added unit coverage for populating `APPEEARS_API_TOKEN` from `.env.local` and preserving an already-exported environment value.
  - Because `python-dotenv` is not installed in the current workspace, `src.env_bootstrap` includes a tiny non-overriding fallback parser so local CLI startup still works immediately.
- Files touched:
  - `src/env_bootstrap.py`
  - `src/run_full_stack_orchestration.py`
  - `src/run_acquisition_orchestration.py`
  - `src/run_appeears_acquisition.py`
  - `tests/test_env_bootstrap.py`
  - `docs/workflow.md`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m pytest tests/test_env_bootstrap.py tests/test_appeears_client.py tests/test_appeears_acquisition.py tests/test_full_stack_orchestration.py -q"`
- Test status:
  - Focused `.env.local` bootstrap/AppEEARS/full-stack subset passed: `27 passed`.
- Manual verification status:
  - No live CLI run was executed in this checkpoint.
  - Verification is test-based in the current workspace.
- Next recommended step:
  - Rerun the same full-stack command from the project root and confirm the startup log reports `.env.local` loading before AppEEARS credential preflight.

### 2026-03-19 - Checkpoint: Cache Storage Audit And Safe Cleanup Utility Added

- Date / checkpoint:
  - 2026-03-19 cache growth audit and cleanup tooling for `data_raw/cache/`.
- Change made:
  - Added `src.cache_cleanup` and `src.run_cache_cleanup` to inventory cache files, classify them by retention tier, preserve JSON metadata outside the cache tree, and support dry-run targeted prune plans for `partials`, `nlcd-extracted`, `hydro-extracted`, `extracted`, and `regenerable`.
  - Added tests covering category classification, source-archive safety checks, dry-run pruning logic, and non-cache path protection.
  - Updated README and workflow docs with the new storage-audit CLI and the recommended dry-run-first policy.
- Files touched:
  - `src/cache_cleanup.py`
  - `src/run_cache_cleanup.py`
  - `tests/test_cache_cleanup.py`
  - `README.md`
  - `docs/workflow.md`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m pytest tests/test_cache_cleanup.py -q"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m src.run_cache_cleanup --prune-modes regenerable --protect-recent-hours 24 --report-json outputs\storage\cache_cleanup_dry_run.json"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m src.run_cache_cleanup --prune-modes regenerable --protect-recent-hours 0 --report-json outputs\storage\cache_cleanup_dry_run_no_age_gate.json"`
- Test status:
  - Focused cache cleanup subset passed: `4 passed`.
- Manual verification status:
  - Real workspace dry-run storage audit measured `data_raw/cache/` at about `63.72 GB`.
  - The conservative active-run dry-run plan proposed `0 GB` for deletion with a 24-hour age gate.
  - The no-age-gate dry-run plan proposed `27.83 GB` for safe regenerable cleanup without touching NLCD bundles, DEM tiles, or hydro package ZIPs.
- Next recommended step:
  - Wait until the current city batch is no longer actively downloading, then rerun the dry-run with `--protect-recent-hours 0` and review the JSON manifest before any live `--execute` prune.

### 2026-03-19 - Checkpoint: Buffer Policy Parameterized For Feature Assembly

- Date / checkpoint:
  - 2026-03-19 study-area buffer propagation audit plus minimal policy split between acquisition footprint and training footprint.
- Change made:
  - Persisted the original unbuffered urban-core geometry inside each study-area GeoPackage.
  - Added `cell_filter_mode` support to feature assembly, batch feature extraction, full pipeline, and full-stack orchestration.
  - Added per-cell audit flags `is_core_city_cell` and `is_buffer_ring_cell` to per-city outputs and intermediate tables.
  - Kept AppEEARS AOI creation, raw support acquisition, and support-layer prep tied to the saved study-area geometry, so buffered acquisition can coexist with core-city-only training cells.
- Files touched:
  - `src/city_processing.py`
  - `src/feature_assembly.py`
  - `src/full_pipeline.py`
  - `src/full_stack_orchestration.py`
  - `src/run_city_features.py`
  - `src/run_city_features_batch.py`
  - `src/run_full_stack_orchestration.py`
  - `tests/test_city_processing.py`
  - `tests/test_feature_assembly.py`
  - `README.md`
  - `docs/workflow.md`
  - `docs/data_dictionary.md`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_city_features --city-id 1 --cell-filter-mode core_city"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_full_stack_orchestration --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31 --cell-filter-mode core_city"`
- Test status:
  - Focused buffer-policy subset passed: `21 passed`.
- Manual verification status:
  - Phoenix was manually rerun on refreshed real-city outputs and passed the end-to-end metadata + feature-filtering check.
- Next recommended step:
  - Refresh the remaining target cities' study-area files before launching an overnight `core_city` batch, so the workspace does not stay mixed between `study_area` and `core_city` outputs.

### 2026-03-19 - Checkpoint: Phoenix Core-City Manual Validation

- Date / checkpoint:
  - 2026-03-19 real-city validation of the new study-area metadata and feature filtering path.
- Change made:
  - Regenerated Phoenix city processing with `--buffer-m 2000` so the study-area GeoPackage carries `core_geometry_wkt`.
  - Rebuilt Phoenix features with `--cell-filter-mode core_city`.
  - Verified temp final-dataset assembly still succeeds with the new per-city audit fields present.
- Files touched:
  - `data_processed/study_areas/01_phoenix_az_study_area.gpkg`
  - `data_processed/city_grids/01_phoenix_az_grid_30m.gpkg`
  - `data_processed/intermediate/city_features/01_phoenix_az_features_unfiltered.parquet`
  - `data_processed/intermediate/city_features/01_phoenix_az_features_filtered.parquet`
  - `data_processed/city_features/01_phoenix_az_features.gpkg`
  - `data_processed/city_features/01_phoenix_az_features.parquet`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_city_processing --city-id 1 --buffer-m 2000 --resolution 30"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_city_features --city-id 1 --cell-filter-mode core_city"`
- Test status:
  - No new pytest suite was needed beyond the existing 21-pass buffer-policy subset; this checkpoint adds manual validation.
- Manual verification status:
  - `core_geometry_wkt` present and non-empty in the Phoenix study-area GeoPackage.
  - Phoenix feature outputs contain `is_core_city_cell` / `is_buffer_ring_cell`.
  - Phoenix filtered row count decreased from `4,735,561` buffered-study-area rows to `3,199,440` core-city rows.
  - Temporary final-dataset assembly succeeded without schema breakage.
  - Temporary AppEEARS AOI export plus support-layer geometry/bbox reads also succeeded on the refreshed Phoenix study-area file.
- Next recommended step:
  - Refresh study-area files for the next overnight target set, then launch the same run pattern with `--cell-filter-mode core_city`.

### 2026-03-19 - Checkpoint: Stale Legacy Raster Handoff Hardened

- Date / checkpoint:
  - 2026-03-19 targeted NDVI/LST feature-assembly hardening after the Tucson stale-file failure.
- Change made:
  - Tightened native AppEEARS raster matching so generic legacy filenames such as `ndvi_1.tif`, `ndvi_2.tif`, and `lst_1.tif` no longer count as native value rasters.
  - Added raster-path validation before NDVI/LST stack sampling so unreadable or corrupt TIFFs are warned and skipped instead of aborting the city when valid rasters remain.
  - Added regression coverage for a mixed directory containing valid native AppEEARS rasters plus invalid legacy TIFFs, and for stack sampling with mixed valid/invalid TIFF inputs.
- Files touched:
  - `src/feature_assembly.py`
  - `src/raster_features.py`
  - `tests/test_feature_assembly.py`
  - `tests/test_raster_features.py`
  - `README.md`
  - `docs/workflow.md`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m pytest tests/test_feature_assembly.py tests/test_full_stack_orchestration.py tests/test_raw_data_acquisition.py tests/test_raster_features.py -q"`
- Test status:
  - Focused regression subset passed: `23 passed`.
- Manual verification status:
  - Confirmed current on-disk full-stack outputs exist for Phoenix, Tucson, Las Vegas, and Albuquerque.
  - Confirmed the current AppEEARS status summaries for cities `2-4` report `remote_task_status=done`.
  - No fresh live city rerun was executed in this checkpoint.
- Next recommended step:
  - Run one more controlled full-stack batch, for example `--city-ids 5,6,7`, before promoting to `--all-missing`.

### 2026-03-18 - Checkpoint: AppEEARS Saved-Task Reruns Fixed

- Date / checkpoint:
  - 2026-03-18 AppEEARS rerun-state fix for persisted task reuse.
- Change made:
  - Updated the AppEEARS acquisition state machine to treat an existing saved `task_id` as reusable work unless the prior remote task is terminal-failed.
  - Added explicit logging for existing `task_id` discovery, polling, remote status returns, bundle listing/download start, bundle sync counts, and the reason a fresh submission is chosen.
  - Stopped mapping active remote tasks to `status=not_started`; in-progress rows now remain in AppEEARS-specific in-progress statuses while completed bundle reuse resolves to `skipped_existing`.
  - Added regression tests covering saved-task polling without resubmission, completed-task download reuse, and the `done + files already present -> skipped_existing` path.
- Files touched:
  - `src/appeears_acquisition.py`
  - `tests/test_appeears_acquisition.py`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m pytest tests/test_appeears_client.py tests/test_appeears_acquisition.py -q"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_full_stack_orchestration --city-ids 2,3,4 --start-date 2023-05-01 --end-date 2023-08-31"`
- Test status:
  - Focused AppEEARS rerun-state subset passed: `18 passed`.
- Manual verification status:
  - No fresh live AppEEARS rerun was executed in this checkpoint.
  - The failure mode was confirmed from persisted summary rows and fixed in unit tests that assert existing `task_id` values are polled instead of resubmitted.
- Next recommended step:
  - Rerun the same `2,3,4` full-stack batch and confirm no new AppEEARS request emails are triggered for already-submitted tasks.

### 2026-03-18 - Checkpoint: AppEEARS Auth Refresh And TNM Retry/Fallback Hardened

- Date / checkpoint:
  - 2026-03-18 targeted blocker fixes for AppEEARS submission failures and TNM raw-acquisition resilience.
- Change made:
  - Changed AppEEARS auth selection to prefer `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` over a simultaneously configured `APPEEARS_API_TOKEN`, so submission uses a fresh `/login` bearer token instead of silently preferring a stale static token.
  - Added clearer AppEEARS task-submission error classification for stale token/auth failure, permission or EULA issues, and bad payloads.
  - Added TNM request retry/backoff for transient query/download failures and a hydro-package 404 refresh path that requeries TNM metadata for the same HU4 before giving up.
  - Added focused regression tests for auth precedence, AppEEARS failure classification, TNM retry behavior, and hydro dead-URL fallback.
- Files touched:
  - `src/appeears_client.py`
  - `src/raw_data_acquisition.py`
  - `tests/test_appeears_client.py`
  - `tests/test_raw_data_acquisition.py`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m pytest tests/test_appeears_client.py tests/test_raw_data_acquisition.py tests/test_appeears_acquisition.py -q"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_full_stack_orchestration --city-ids 2,3,4 --start-date 2023-05-01 --end-date 2023-08-31"`
- Test status:
  - Focused AppEEARS/TNM regression subset passed: `22 passed`.
- Manual verification status:
  - Confirmed the failing AppEEARS summary rows all returned `403` during task submission for Tucson, Las Vegas, and Albuquerque.
  - Confirmed the failing TNM summary rows were a Las Vegas hydro `404` dead package URL and Albuquerque DEM/hydro `504` TNM query timeouts.
  - Verified against current official AppEEARS materials that the supported flow still uses `/login` plus a bearer token on `/task`; no evidence was found that the header format itself had changed.
- Next recommended step:
  - Load Earthdata credentials, unset any stale `APPEEARS_API_TOKEN`, and rerun the same `2,3,4` full-stack batch to confirm AppEEARS submission succeeds and TNM failures downgrade to retries or cleanly classified errors.

### 2026-03-18 - Checkpoint: Raw Acquisition Stall Diagnosis And Logging Tightened

- Date / checkpoint:
  - 2026-03-18 diagnosis of long raw-support acquisition pauses during Tucson full-stack orchestration.
- Change made:
  - Added byte-size and completion logging for raw support downloads so multi-GB NLCD and multi-hundred-MB hydro transfers no longer look idle.
  - Added extraction logging for cached ZIP members.
  - Updated NHDPlus water-layer loading to pass a study-area `bbox` into `geopandas.read_file`, reducing unnecessary full-package reads before hydro clipping.
  - Added a regression test that locks in the new spatially filtered hydro read behavior.
- Files touched:
  - `src/raw_data_acquisition.py`
  - `tests/test_raw_data_acquisition.py`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command "& '.\.venv\Scripts\python.exe' -m pytest tests/test_raw_data_acquisition.py -q"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_full_stack_orchestration --city-ids 2,3,4 --start-date 2023-05-01 --end-date 2023-08-31"`
- Test status:
  - Focused raw-acquisition regression subset passed: `5 passed`.
- Manual verification status:
  - Confirmed cached Tucson NLCD bundle sizes of `13.12 GB` and `8.85 GB`.
  - Confirmed cached Tucson hydro package sizes above `500 MB` each, with extracted GeoPackages above `1 GB`.
  - Real-data Tucson hydro smoke timing completed in `0.28s` and `2.98s` for the currently extracted packages after the `bbox` optimization.
  - The prior apparent stall is now understood as a combination of very large official downloads, previously sparse logging, and expensive hydro package reads before this checkpoint.
- Next recommended step:
  - Rerun the Tucson/Albuquerque/Las Vegas orchestration batch and watch the new progress logs to verify whether the remaining delay is simply the unfinished HU4 `1508` transfer.

### 2026-03-18 - Checkpoint: AppEEARS Discovery Fix And Thin Acquisition Orchestrator Added

- Date / checkpoint:
  - 2026-03-18 AppEEARS discovery handoff fix plus restart-safe orchestration CLI.
- Change made:
  - Replaced brittle AppEEARS value-raster discovery with native filename-aware matching for NDVI and ECOSTRESS LST while excluding QA/cloud/error sidecars.
  - Added explicit discovery logging so feature extraction reports candidate counts, matched rasters, and fallback behavior.
  - Added `src.run_acquisition_orchestration` to sequence raw support acquisition, support prep, NDVI AppEEARS, and ECOSTRESS AppEEARS into one thin status-reporting CLI.
  - Added tests for native AppEEARS filename discovery and orchestration sequencing.
- Files touched:
  - `src/feature_assembly.py`
  - `src/acquisition_orchestration.py`
  - `src/run_acquisition_orchestration.py`
  - `src/config.py`
  - `src/appeears_acquisition.py`
  - `src/raw_data_acquisition.py`
  - `src/support_layers.py`
  - `tests/test_feature_assembly.py`
  - `tests/test_acquisition_orchestration.py`
  - `README.md`
  - `docs/workflow.md`
  - `docs/data_dictionary.md`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_acquisition_orchestration --city-ids 1 --start-date 2023-05-01 --end-date 2023-08-31"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_acquisition_orchestration --all-missing --start-date 2023-05-01 --end-date 2023-08-31"`
- Test status:
  - Focused regression subset passed: `21 passed`.
  - Full suite not rerun in this checkpoint.
- Manual verification status:
  - Real Phoenix discovery probe found `9` NDVI rasters and `61` LST rasters in the current workspace.
  - Real Phoenix feature-extraction smoke test completed with `blocked_stages=` empty.
  - The moved `.venv` executed successfully and `src.config.PROJECT_ROOT` resolved to the new OneDrive-backed workspace root.
  - The Phoenix orchestration CLI was run in the moved workspace and rewrote orchestration, support-layer, and AppEEARS summary files with the new workspace root.
  - Phoenix raw AppEEARS `.tif` timestamps remained on `2026-03-08`, so the 2026-03-18 orchestration run validated resume behavior after the move, not a fresh AppEEARS submit/download.
- Next recommended step:
  - Verify AppEEARS credentials in the active session, then run the orchestration CLI for cities `2`, `3`, and `4` before scaling to `--all-missing`.

### 2026-03-18 - Checkpoint: Full-Stack City Orchestration Added

- Date / checkpoint:
  - 2026-03-18 full-stack per-city orchestration through feature assembly.
- Change made:
  - Added `src.run_full_stack_orchestration` to extend raw support acquisition, support prep, NDVI AppEEARS, and ECOSTRESS AppEEARS through feature assembly with one per-city summary row.
  - Added a strict AppEEARS credential preflight that lists the exact missing env vars and returns `blocked_missing_credentials` only for auth-dependent stages.
  - Added reusable city-feature output path helpers so the full-stack runner can skip existing feature outputs safely.
  - Documented the recommended gitignored `.env.local` pattern for local operators.
- Files touched:
  - `src/stage_status.py`
  - `src/full_stack_orchestration.py`
  - `src/run_full_stack_orchestration.py`
  - `src/appeears_client.py`
  - `src/appeears_acquisition.py`
  - `src/feature_assembly.py`
  - `.gitignore`
  - `tests/test_appeears_acquisition.py`
  - `tests/test_full_stack_orchestration.py`
  - `README.md`
  - `docs/workflow.md`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_full_stack_orchestration --city-ids 2,3,4 --start-date 2023-05-01 --end-date 2023-08-31"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_full_stack_orchestration --all-missing --start-date 2023-05-01 --end-date 2023-08-31"`
- Test status:
  - Focused orchestration/AppEEARS regression subset passed: `21 passed`.
- Manual verification status:
  - Real workspace run of `src.run_full_stack_orchestration --city-ids 1 ... --max-cells 100` completed and wrote the new full-stack orchestration summary files.
  - Phoenix reused existing raw support, prepared support, AppEEARS, and feature outputs without unnecessary reruns.
  - Missing-credential behavior is test-verified; it was not manually exercised in the real workspace because Phoenix already had reusable AppEEARS outputs.
- Next recommended step:
  - Load credentials from `.env.local` into the active shell, then run the new full-stack orchestrator for cities `2`, `3`, and `4`.

### 2026-03-08 - Checkpoint: Phoenix Data Summary Deliverable Added

- Date / checkpoint:
  - 2026-03-08 Phoenix-only summary deliverable generated from the materialized analysis dataset.
- Change made:
  - Added `src/summarize_phoenix_dataset.py` to select the canonical Phoenix-only analysis table, compute concise descriptive statistics, and write a polished markdown summary.
  - Added deterministic supporting CSV tables and PNG figures under `outputs/phoenix_data_summary/`.
  - Added tests for Phoenix dataset selection priority and preprocessing-audit logic.
- Files touched:
  - `src/summarize_phoenix_dataset.py`
  - `tests/test_summarize_phoenix_dataset.py`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.summarize_phoenix_dataset"`
- Test status:
  - `69 passed` (`pytest -q`).
- Manual verification status:
  - Real workspace run wrote `outputs/phoenix_data_summary.md` plus supporting tables and four figures under `outputs/phoenix_data_summary/`.
  - `dataset_consistency_check.csv` confirms the canonical per-city feature table matches the Phoenix filtered intermediate row count (`4,735,561`).
- Next recommended step:
  - Manually review the generated Phoenix figures and narrative for presentation preferences, then reuse the same CLI pattern for other cities if needed.
### 2026-03-08 - Checkpoint: Raw Support-Layer Acquisition Pipeline Added

- Date / checkpoint:
  - 2026-03-08 raw DEM/NLCD/hydro acquisition automation.
- Change made:
  - Added a restartable raw acquisition runner that fills deterministic city raw DEM, NLCD, and hydro paths from official USGS/MRLC sources.
  - Added reusable `data_raw/cache/` download/extraction caches for DEM tiles, Annual NLCD bundles, and NHDPlus HR HU4 packages.
  - Added machine-readable raw acquisition summary outputs under `data_processed/support_layers/`.
  - Added tests for TNM tile deduplication, Annual NLCD bundle member selection, NHDPlus HR water-layer extraction, and skip/idempotence behavior.
  - Updated README and workflow docs to document the new raw acquisition stage and CLI usage.
- Files touched:
  - `src/config.py`
  - `src/raw_data_acquisition.py`
  - `src/run_raw_data_acquisition.py`
  - `tests/test_raw_data_acquisition.py`
  - `README.md`
  - `docs/workflow.md`
  - `docs/chat_handoff.md`
- How to run:
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_raw_data_acquisition --all-missing"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_raw_data_acquisition --city-ids 1 2 3 --dataset dem"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_raw_data_acquisition --dataset nlcd --all-missing"`
  - `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -Command ".venv\Scripts\python.exe -m src.run_raw_data_acquisition --dataset hydro --all-missing"`
- Test status:
  - `67 passed` (`pytest -q`).
- Manual verification status:
  - Real workspace CLI run for Phoenix produced the new raw acquisition summary and correctly skipped all already-existing deterministic outputs.
  - Official endpoint assumptions were verified during implementation against TNM Access, MRLC Annual NLCD bundle URLs, and TNM NHDPlus HR product queries.
  - Full multi-city download execution has not been run yet.
- Next recommended step:
  - Execute `src.run_raw_data_acquisition --all-missing`, then rerun support-layer preflight and prep.

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








