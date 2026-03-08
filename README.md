\# STAT 5630 Final Project – Urban Heat Dataset Construction



\## Project Overview

This project builds a reproducible Python workflow for constructing a 30 m cell-level urban heat dataset for 30 U.S. cities across three climate groups: hot/arid, hot/humid, and mild/cool. The goal is to create a consistent cross-city geospatial dataset that can be used to study how land-surface characteristics such as impervious cover, land cover, vegetation, elevation, and proximity to water are associated with urban heat risk.



\## Unit of Observation

The final analytic dataset is constructed at the 30 m × 30 m grid-cell level. Each row in the final dataset represents one grid cell within a city study area.



\## Study Cities



\### Hot / arid

\- Phoenix, AZ

\- Tucson, AZ

\- Las Vegas, NV

\- Albuquerque, NM

\- El Paso, TX

\- Denver, CO

\- Salt Lake City, UT

\- Fresno, CA

\- Bakersfield, CA

\- Reno, NV



\### Hot / humid

\- Houston, TX

\- Columbia, SC

\- Richmond, VA

\- New Orleans, LA

\- Tampa, FL

\- Miami, FL

\- Jacksonville, FL

\- Atlanta, GA

\- Charlotte, NC

\- Nashville, TN



\### Mild / cool

\- Seattle, WA

\- Portland, OR

\- San Francisco, CA

\- San Jose, CA

\- Los Angeles, CA

\- San Diego, CA

\- Chicago, IL

\- Minneapolis, MN

\- Detroit, MI

\- Boston, MA



\## Planned Final Dataset Columns

The final dataset is expected to include the following core fields:



\- `city\_id`

\- `city\_name`

\- `state`

\- `climate\_group`

\- `cell\_id`

\- `centroid\_lon`

\- `centroid\_lat`

\- `impervious\_pct`

\- `land\_cover\_class`

\- `elevation\_m`

\- `dist\_to\_water\_m`

\- `ndvi\_median\_may\_aug`

\- `lst\_median\_may\_aug`

\- `n\_valid\_ecostress\_passes`

\- `hotspot\_10pct`



Additional intermediate or diagnostic columns may be added as needed during processing.



\## Planned Workflow

The intended workflow is:



1\. Define each city study area from a city-center point and urban area boundary.

2\. Buffer the study area and project it to a local projected CRS.

3\. Build a master 30 m grid for each city.

4\. Align all predictor rasters and vector-derived layers to the master grid.

5\. Construct predictor variables:

&nbsp;  - NLCD land cover

&nbsp;  - NLCD impervious surface

&nbsp;  - elevation

&nbsp;  - distance to water

&nbsp;  - NDVI

6\. Construct the response variable from ECOSTRESS land surface temperature.

7\. Clean and assemble the final per-city datasets.

8\. Merge all cities into one final analytic dataset.

9\. Create summary figures and documentation.



\## Repository Structure



\- `data\_raw/`  

&nbsp; Raw downloaded source data. These files should remain unchanged after download.



\- `data\_processed/`  

&nbsp; Intermediate and final processed datasets, including city-level outputs and the final merged dataset.



\- `docs/`  

&nbsp; Project documentation, workflow notes, and data dictionary files.



\- `figures/`  

&nbsp; Maps, plots, and other exported visualizations.



\- `notebooks/`  

&nbsp; Jupyter notebooks for exploration, debugging, and figure development.



\- `src/`  

&nbsp; Python source code for the reproducible data-processing pipeline.



\- `tests/`  

&nbsp; Tests for core processing functions and dataset validation.



\## Notes

This repository is intended to support both dataset construction and documentation of the full geospatial workflow used in the project.


## Current City Processing Entrypoint

The repository now includes a reusable single-city pipeline entrypoint for boundary + study area + grid creation:

```bash
python -m src.run_city_processing --city-name Phoenix
```

Outputs are written to:

- `data_processed/study_areas/`
- `data_processed/city_grids/`

Use `--city-id` instead of `--city-name` if preferred.
