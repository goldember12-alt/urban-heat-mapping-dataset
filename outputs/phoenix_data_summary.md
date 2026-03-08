# Phoenix Summary of Data

The Phoenix summary uses `data_processed\city_features\01_phoenix_az_features.parquet`, the canonical Phoenix-only analysis-ready feature table. Each observation represents one filtered 30 m grid cell inside the buffered Phoenix study area, with built-form, vegetation, elevation, hydrologic proximity, and warm-season surface-temperature attributes aligned to the same cell geometry. The table is intended for downstream urban heat modeling in a hot_arid city, including both continuous LST analysis and binary hotspot prediction.

## Overview

| metric | value |
| --- | --- |
| Primary Phoenix analysis file | data_processed\city_features\01_phoenix_az_features.parquet |
| Dataset choice rationale | Canonical Phoenix-only filtered output intended for downstream modeling. |
| Observations | 4735561 |
| Variables | 14 |
| Unit of analysis | One filtered 30 m grid cell in the buffered Phoenix study area |
| Geometry / CRS | Cell polygons stored in EPSG:32612; centroids stored as WGS84 lon/lat |
| Projected spatial extent | [362550, 3662520, 458400, 3752910] |
| Study-area buffer | 2,000 m around the Census urban area |

## Key Variables

| variable_name | meaning | type_unit | why_it_matters |
| --- | --- | --- | --- |
| lst_median_may_aug | Median daytime land surface temperature across May-Aug ECOSTRESS observations. | continuous; ECOSTRESS LST units from source raster | Primary heat outcome for regression, classification, and hotspot analysis. |
| hotspot_10pct | Indicator for cells at or above the Phoenix-specific 90th percentile of LST. | binary flag | Natural target for hotspot classification and spatial risk mapping. |
| impervious_pct | NLCD impervious surface share for the 30 m cell. | continuous; percent | Core urban form exposure tied to heat retention and built intensity. |
| ndvi_median_may_aug | Median warm-season greenness index from Landsat/AppEEARS NDVI layers. | continuous; NDVI index | Vegetation is a likely protective predictor against elevated surface temperatures. |
| dist_to_water_m | Distance from the cell to the nearest mapped hydro feature. | continuous; meters | Captures proximity to possible local cooling influences and riparian structure. |
| land_cover_class | NLCD land cover class code for the cell. | categorical; NLCD class | Summarizes surface type and helps separate developed, barren, and vegetated cells. |
| n_valid_ecostress_passes | Count of valid ECOSTRESS observations contributing to the LST median. | count | Important quality-control covariate because low temporal coverage can weaken inference. |

## Targeted Descriptive Results

### Preprocessing audit

| stage | n_rows | share_of_unfiltered_pct |
| --- | --- | --- |
| unfiltered_input_rows | 4,743,629 | 100.00 |
| dropped_open_water_rows | 7,286 | 0.15 |
| dropped_lt3_ecostress_pass_rows | 763 | 0.02 |
| final_filtered_rows | 4,735,561 | 99.83 |

### Key numeric summary

| variable | n_non_missing | missing_pct | mean | median | std | p10 | p90 | skew |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| impervious_pct | 4,735,561 | 0.00 | 30.51 | 27.79 | 27.61 | 0.00 | 67.03 | 0.29 |
| ndvi_median_may_aug | 4,735,537 | 0.00 | 0.21 | 0.20 | 0.07 | 0.14 | 0.29 | 1.76 |
| lst_median_may_aug | 4,735,561 | 0.00 | 315.09 | 315.26 | 2.49 | 312.02 | 317.77 | -0.23 |
| dist_to_water_m | 4,735,561 | 0.00 | 550.68 | 390.00 | 555.63 | 60.00 | 1,236.93 | 2.05 |
| elevation_m | 4,735,561 | 0.00 | 450.07 | 412.06 | 125.66 | 341.42 | 610.23 | 1.97 |
| n_valid_ecostress_passes | 4,735,561 | 0.00 | 28.43 | 28.00 | 3.36 | 24.00 | 33.00 | -0.32 |

### Land-cover composition

| land_cover_class | land_cover_label | n_rows | share_pct |
| --- | --- | --- | --- |
| 52 | Shrub/Scrub | 1,441,117 | 30.43 |
| 23 | Developed, Medium Intensity | 1,384,313 | 29.23 |
| 22 | Developed, Low Intensity | 972,106 | 20.53 |
| 21 | Developed, Open Space | 499,963 | 10.56 |
| 24 | Developed, High Intensity | 213,895 | 4.52 |
| 82 | Cultivated Crops | 209,095 | 4.42 |
| 90 | Woody Wetlands | 6,585 | 0.14 |
| 71 | Grassland/Herbaceous | 4,269 | 0.09 |

### Missingness for key variables

| variable | missing_n | missing_pct | non_missing_n |
| --- | --- | --- | --- |
| ndvi_median_may_aug | 24 | 0.0005 | 4,735,537 |
| dist_to_water_m | 0 | 0.0000 | 4,735,561 |
| elevation_m | 0 | 0.0000 | 4,735,561 |
| hotspot_10pct | 0 | 0.0000 | 4,735,561 |
| impervious_pct | 0 | 0.0000 | 4,735,561 |
| land_cover_class | 0 | 0.0000 | 4,735,561 |
| lst_median_may_aug | 0 | 0.0000 | 4,735,561 |
| n_valid_ecostress_passes | 0 | 0.0000 | 4,735,561 |

### Correlation matrix

| variable | lst_median_may_aug | impervious_pct | ndvi_median_may_aug | dist_to_water_m | elevation_m | n_valid_ecostress_passes |
| --- | --- | --- | --- | --- | --- | --- |
| lst_median_may_aug | 1.00 | 0.05 | -0.21 | 0.03 | -0.52 | -0.37 |
| impervious_pct | 0.05 | 1.00 | -0.17 | 0.15 | -0.41 | 0.06 |
| ndvi_median_may_aug | -0.21 | -0.17 | 1.00 | 0.07 | 0.12 | -0.36 |
| dist_to_water_m | 0.03 | 0.15 | 0.07 | 1.00 | -0.16 | 0.00 |
| elevation_m | -0.52 | -0.41 | 0.12 | -0.16 | 1.00 | 0.28 |
| n_valid_ecostress_passes | -0.37 | 0.06 | -0.36 | 0.00 | 0.28 | 1.00 |

## Figures

![Phoenix key distributions](phoenix_data_summary/figures/phoenix_key_distributions.png)

![Phoenix land-cover composition](phoenix_data_summary/figures/phoenix_land_cover_composition.png)

![Phoenix key correlations](phoenix_data_summary/figures/phoenix_key_correlations.png)

![Phoenix hotspot map](phoenix_data_summary/figures/phoenix_hotspot_map.png)

## Notable Patterns

- Missingness is negligible: only 24 `ndvi_median_may_aug` values are missing (0.0005%).
- `hotspot_10pct` is intentionally imbalanced at 10.00% positives because it marks the Phoenix-specific top decile of LST.
- Land cover is concentrated in Shrub/Scrub cells, which make up 30.4% of the filtered Phoenix dataset.
- The strongest linear relationship with LST among the key numeric variables is negative for `elevation_m` (r = -0.52).
- Hotspot prevalence varies by Phoenix quadrant from 6.9% to 14.6%, which is consistent with non-random spatial concentration.
- `dist_to_water_m` is strongly skewed (skew = 2.05), so transformations or robust summaries may be useful in later modeling.

## Output Notes

- The Phoenix-only per-city feature parquet was chosen over the merged final dataset because it is the direct analysis-ready output for this city and already reflects the row-drop rules used by the pipeline.
- Supporting CSV tables and PNG figures for this summary were generated deterministically by the companion CLI.
