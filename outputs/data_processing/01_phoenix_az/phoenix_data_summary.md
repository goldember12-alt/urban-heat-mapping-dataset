# Phoenix Summary of Data

The Phoenix summary uses `data_processed\city_features\01_phoenix_az_features.parquet`, the canonical Phoenix-only analysis-ready feature table. Each observation represents one filtered 30 m grid cell inside the buffered Phoenix study area, with built-form, vegetation, elevation, hydrologic proximity, and warm-season surface-temperature attributes aligned to the same cell geometry. The table is intended for downstream urban heat modeling in a hot_arid city, including both continuous LST analysis and binary hotspot prediction.

## Overview

| metric | value |
| --- | --- |
| Primary Phoenix analysis file | data_processed\city_features\01_phoenix_az_features.parquet |
| Dataset choice rationale | Canonical per-city filtered output intended for downstream modeling. |
| Observations | 3199440 |
| Variables | 16 |
| Unit of analysis | One filtered 30 m grid cell in the buffered Phoenix study area |
| Geometry / CRS | Cell polygons stored in EPSG:32612; centroids stored as WGS84 lon/lat |
| Projected spatial extent | [364560, 3664530, 456390, 3750870] |
| Study-area buffer | 2,000 m around the Census urban area |

## Key Variables

| variable_name | meaning | type_unit | why_it_matters |
| --- | --- | --- | --- |
| lst_median_may_aug | Median daytime land surface temperature across May-Aug ECOSTRESS observations. | continuous; ECOSTRESS LST units from source raster | Primary heat outcome for regression, classification, and hotspot analysis. |
| hotspot_10pct | Indicator for cells at or above the city-specific 90th percentile of LST. | binary flag | Natural target for hotspot classification and spatial risk mapping. |
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
| dropped_open_water_rows | 7,283 | 0.15 |
| dropped_lt3_ecostress_pass_rows | 763 | 0.02 |
| final_filtered_rows | 3,199,440 | 67.45 |

### Key numeric summary

| variable | n_non_missing | missing_pct | mean | median | std | p10 | p90 | skew |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| impervious_pct | 3,199,440 | 0.00 | 42.75 | 47.27 | 23.98 | 6.31 | 71.52 | -0.23 |
| ndvi_median_may_aug | 3,199,440 | 0.00 | 0.21 | 0.20 | 0.06 | 0.14 | 0.29 | 0.98 |
| lst_median_may_aug | 3,199,440 | 0.00 | 315.00 | 315.13 | 1.92 | 312.66 | 317.22 | -0.59 |
| dist_to_water_m | 3,199,440 | 0.00 | 590.84 | 420.00 | 586.25 | 60.00 | 1,344.66 | 1.95 |
| elevation_m | 3,199,440 | 0.00 | 421.22 | 391.76 | 95.25 | 340.18 | 545.14 | 2.21 |
| n_valid_ecostress_passes | 3,199,440 | 0.00 | 28.62 | 28.00 | 2.92 | 25.00 | 33.00 | 0.02 |

### Land-cover composition

| land_cover_class | land_cover_label | n_rows | share_pct |
| --- | --- | --- | --- |
| 23 | Developed, Medium Intensity | 1,328,050 | 41.51 |
| 22 | Developed, Low Intensity | 895,269 | 27.98 |
| 21 | Developed, Open Space | 411,874 | 12.87 |
| 52 | Shrub/Scrub | 305,504 | 9.55 |
| 24 | Developed, High Intensity | 205,396 | 6.42 |
| 82 | Cultivated Crops | 49,979 | 1.56 |
| 90 | Woody Wetlands | 1,919 | 0.06 |
| 81 | Pasture/Hay | 772 | 0.02 |

### Missingness for key variables

| variable | missing_n | missing_pct | non_missing_n |
| --- | --- | --- | --- |
| dist_to_water_m | 0 | 0.0000 | 3,199,440 |
| elevation_m | 0 | 0.0000 | 3,199,440 |
| hotspot_10pct | 0 | 0.0000 | 3,199,440 |
| impervious_pct | 0 | 0.0000 | 3,199,440 |
| land_cover_class | 0 | 0.0000 | 3,199,440 |
| lst_median_may_aug | 0 | 0.0000 | 3,199,440 |
| n_valid_ecostress_passes | 0 | 0.0000 | 3,199,440 |
| ndvi_median_may_aug | 0 | 0.0000 | 3,199,440 |

### Correlation matrix

| variable | lst_median_may_aug | impervious_pct | ndvi_median_may_aug | dist_to_water_m | elevation_m | n_valid_ecostress_passes |
| --- | --- | --- | --- | --- | --- | --- |
| lst_median_may_aug | 1.00 | 0.16 | -0.25 | 0.03 | -0.46 | -0.28 |
| impervious_pct | 0.16 | 1.00 | -0.26 | 0.13 | -0.36 | 0.01 |
| ndvi_median_may_aug | -0.25 | -0.26 | 1.00 | -0.01 | 0.15 | -0.30 |
| dist_to_water_m | 0.03 | 0.13 | -0.01 | 1.00 | -0.13 | 0.13 |
| elevation_m | -0.46 | -0.36 | 0.15 | -0.13 | 1.00 | 0.24 |
| n_valid_ecostress_passes | -0.28 | 0.01 | -0.30 | 0.13 | 0.24 | 1.00 |

## Figures

![Phoenix key distributions](../../../figures/data_processing/01_phoenix_az/phoenix_key_distributions.png)

![Phoenix land-cover composition](../../../figures/data_processing/01_phoenix_az/phoenix_land_cover_composition.png)

![Phoenix key correlations](../../../figures/data_processing/01_phoenix_az/phoenix_key_correlations.png)

![Phoenix hotspot map](../../../figures/data_processing/01_phoenix_az/phoenix_hotspot_map.png)

## Notable Patterns

- None of the key modeling variables have missing values in the filtered Phoenix table.
- `hotspot_10pct` is intentionally imbalanced at 10.00% positives because it marks the Phoenix-specific top decile of LST.
- Land cover is concentrated in Developed, Medium Intensity cells, which make up 41.5% of the filtered Phoenix dataset.
- The strongest linear relationship with LST among the key numeric variables is negative for `elevation_m` (r = -0.46).
- Hotspot prevalence varies by Phoenix quadrant from 1.9% to 17.2%, which is consistent with non-random spatial concentration.
- `elevation_m` is strongly skewed (skew = 2.21), so transformations or robust summaries may be useful in later modeling.

## Output Notes

- The Phoenix-only per-city feature parquet was chosen over the merged final dataset when it was available because it is the direct analysis-ready output for this city and already reflects the row-drop rules used by the pipeline.
- Supporting CSV tables and PNG figures for this summary were generated deterministically by the companion CLI.
- Markdown and tables live under `outputs/data_processing/`, while figures live under `figures/data_processing/`; `outputs/modeling/` and `figures/modeling/` are reserved for later ML/evaluation artifacts.
