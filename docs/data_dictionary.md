# Data Dictionary

## Stage-1 Outputs

### Study areas (`data_processed/study_areas/*.gpkg`)

- `geometry`: buffered study area polygon in local projected CRS
- `city_id`: integer city identifier
- `city_name`: city name
- `state`: state abbreviation
- `climate_group`: climate group label
- `buffer_m`: applied buffer distance in meters

### City grids (`data_processed/city_grids/*.gpkg`)

- `cell_id`: integer grid-cell identifier within city
- `geometry`: 30 m grid-cell polygon

## Intermediate Outputs

### Aligned rasters (`data_processed/intermediate/aligned_rasters/<city_stem>/`)

When source data is available, aligned rasters may include:

- `dem_aligned.tif`
- `nlcd_land_cover_aligned.tif`
- `nlcd_impervious_aligned.tif`
- `dist_to_water_m_aligned.tif`

### Per-city intermediate tables (`data_processed/intermediate/city_features/`)

- `*_features_unfiltered.parquet`: before open-water / ECOSTRESS pass-count row drops
- `*_features_filtered.parquet`: after row-drop rules

## Per-City Feature Outputs (`data_processed/city_features/*.gpkg|*.parquet`)

Final per-city feature columns:

- `city_id`: integer city identifier
- `city_name`: city name
- `climate_group`: climate-group category
- `cell_id`: cell identifier within city grid
- `centroid_lon`: centroid longitude (WGS84)
- `centroid_lat`: centroid latitude (WGS84)
- `impervious_pct`: NLCD impervious percentage (if available)
- `land_cover_class`: NLCD land-cover class code (if available)
- `elevation_m`: DEM-derived elevation in meters (if available)
- `dist_to_water_m`: distance to nearest hydro feature in meters (if available)
- `ndvi_median_may_aug`: median NDVI from May-Aug raster stack (if available)
- `lst_median_may_aug`: median LST from May-Aug ECOSTRESS/AppEEARS stack (if available)
- `n_valid_ecostress_passes`: number of valid LST observations used in the median (if available)
- `hotspot_10pct`: boolean indicator for top 10% LST cells within city

## Final Dataset Outputs (`data_processed/final/final_dataset.*`)

Schema matches per-city feature columns listed above.

## Row Rules

- Drop open-water rows where `land_cover_class == 11` when land-cover exists.
- If LST is available, drop rows with `n_valid_ecostress_passes < 3`.
- Compute `hotspot_10pct` within each city using city-specific LST 90th percentile threshold.
