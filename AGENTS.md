# AGENTS.md

## Project

Build a reproducible Python geospatial workflow for constructing a cross-city urban heat dataset for 30 U.S. cities.

## Goal

Create a final cell-level dataset at 30 m resolution with one row per grid cell per city.

## Required outputs

- `data_processed/final/final_dataset.parquet`
- `data_processed/final/final_dataset.csv`
- one per-city GeoPackage in `data_processed/city_features/`
- figures in `figures/`
- reproducible CLI entrypoint
- tests in `tests/`
- documentation in `docs/`

## Final columns

- `city_id`
- `city_name`
- `climate_group`
- `cell_id`
- `centroid_lon`
- `centroid_lat`
- `impervious_pct`
- `land_cover_class`
- `elevation_m`
- `dist_to_water_m`
- `ndvi_median_may_aug`
- `lst_median_may_aug`
- `n_valid_ecostress_passes`
- `hotspot_10pct`

## Data logic

- Study area = Census urban area polygon containing city center, buffered by 2 km
- Build master 30 m grid in local UTM CRS
- Align all rasters to the master grid
- Compute distance-to-water raster from hydrography
- NDVI = median May–Aug composite from Landsat surface reflectance
- LST = median valid daytime May–Aug ECOSTRESS/AppEEARS observations
- Drop open-water cells
- Drop cells with fewer than 3 valid ECOSTRESS passes
- Define `hotspot_10pct` within each city

## Engineering rules

- Use Python only
- Prefer `geopandas`, `rasterio`, `rioxarray`, `xarray`, `pandas`, `numpy`, `shapely`
- Use functions, not notebook-only logic
- Keep raw data immutable
- Save intermediate artifacts
- Add logging
- Add type hints where practical
- Add tests for core geometry/alignment functions
- Do not hardcode credentials
- Read secrets from environment variables

## Documentation rules

- Update `README` when architecture changes
- Maintain `docs/workflow.md` with pipeline steps
- Maintain `docs/data_dictionary.md` with column definitions
- Add docstrings to public functions

## State and handoff maintenance

- Treat `docs/chat_handoff.md` as the canonical rolling project-state document for handoff to future chats/sessions.
- Prefer updating existing docs over creating redundant new status files.
- Do not create additional tracking documents if `docs/chat_handoff.md` can be updated instead.
- After any meaningful change to code, pipeline behavior, tests, outputs, or docs, and before ending the task, update `docs/chat_handoff.md`.
- At the end of every substantive task, update `docs/chat_handoff.md` before finishing.
- If a prompt asks for code changes, tests, or docs changes, assume `docs/chat_handoff.md` must also be updated unless the prompt explicitly says not to.
- Keep `docs/chat_handoff.md` concise, factual, and current.
- Do not invent verification status; only mark something verified if it was actually checked.

## Required handoff contents

When relevant, refresh these sections in `docs/chat_handoff.md`:

- What Is Completed
- Testing Status
- Manual Verification Status
- Immediate Next Step
- Current Output Structure
- Not Started Yet / Open Issues

When adding a new module, CLI entrypoint, output artifact, or pipeline stage, record:

- what was added
- where it lives
- how to run it
- what was verified manually
- what was verified only by tests

When tests are run, record the latest high-level result in `docs/chat_handoff.md`.

## Verification logging

- For each completed stage, note the next recommended manual verification step in `docs/chat_handoff.md`.
- Distinguish clearly between:
  - implemented
  - test-verified
  - manually verified

## Handoff update template

Each update to `docs/chat_handoff.md` should include, when relevant:

- Date / checkpoint
- Change made
- Files touched
- How to run
- Test status
- Manual verification status
- Next recommended step
- Keep handoff entries short but effective

## Task completion rule

- A task is not complete until relevant code, tests, docs, and `docs/chat_handoff.md` updates are finished.