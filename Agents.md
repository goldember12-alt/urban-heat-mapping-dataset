\# AGENTS.md



\## Project

Build a reproducible Python geospatial workflow for constructing a cross-city urban heat dataset for 30 U.S. cities.



\## Goal

Create a final cell-level dataset at 30 m resolution with one row per grid cell per city.



\## Required outputs

\- `data\_processed/final/final\_dataset.parquet`

\- `data\_processed/final/final\_dataset.csv`

\- one per-city GeoPackage in `data\_processed/city\_features/`

\- figures in `figures/`

\- reproducible CLI entrypoint

\- tests in `tests/`

\- documentation in `docs/`



\## Final columns

\- city\_id

\- city\_name

\- climate\_group

\- cell\_id

\- centroid\_lon

\- centroid\_lat

\- impervious\_pct

\- land\_cover\_class

\- elevation\_m

\- dist\_to\_water\_m

\- ndvi\_median\_may\_aug

\- lst\_median\_may\_aug

\- n\_valid\_ecostress\_passes

\- hotspot\_10pct



\## Data logic

\- Study area = Census urban area polygon containing city center, buffered by 2 km

\- Build master 30 m grid in local UTM CRS

\- Align all rasters to the master grid

\- Compute distance-to-water raster from hydrography

\- NDVI = median May–Aug composite from Landsat surface reflectance

\- LST = median valid daytime May–Aug ECOSTRESS/AppEEARS observations

\- Drop open-water cells

\- Drop cells with fewer than 3 valid ECOSTRESS passes

\- Define hotspot\_10pct within each city



\## Engineering rules

\- Use Python only

\- Prefer geopandas, rasterio, rioxarray, xarray, pandas, numpy, shapely

\- Use functions, not notebook-only logic

\- Keep raw data immutable

\- Save intermediate artifacts

\- Add logging

\- Add type hints where practical

\- Add tests for core geometry/alignment functions

\- Do not hardcode credentials

\- Read secrets from environment variables



\## Documentation rules

\- Update README when architecture changes

\- Maintain docs/workflow.md with pipeline steps

\- Maintain docs/data\_dictionary.md with column definitions

\- Add docstrings to public functions

