# Salt Lake City Summary of Data

The Salt Lake City summary uses `data_processed\city_features\07_salt_lake_city_ut_features.parquet`, the canonical Salt Lake City-only analysis-ready feature table. Each observation represents one filtered 30 m grid cell inside the buffered Salt Lake City study area, with built-form, vegetation, elevation, hydrologic proximity, and warm-season surface-temperature attributes aligned to the same cell geometry. The table is intended for downstream urban heat modeling in a hot_arid city, including both continuous LST analysis and binary hotspot prediction.

## Overview

| metric | value |
| --- | --- |
| Primary Salt Lake City analysis file | data_processed\city_features\07_salt_lake_city_ut_features.parquet |
| Dataset choice rationale | Canonical per-city filtered output intended for downstream modeling. |
| Observations | 863557 |
| Variables | 16 |
| Unit of analysis | One filtered 30 m grid cell in the buffered Salt Lake City study area |
| Geometry / CRS | Cell polygons stored in EPSG:32612; centroids stored as WGS84 lon/lat |
| Projected spatial extent | [406140, 4479540, 434370, 4520790] |
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
| unfiltered_input_rows | 1,243,292 | 100.00 |
| dropped_open_water_rows | 8,954 | 0.72 |
| dropped_lt3_ecostress_pass_rows | 218 | 0.02 |
| final_filtered_rows | 863,557 | 69.46 |

### Key numeric summary

| variable | n_non_missing | missing_pct | mean | median | std | p10 | p90 | skew |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| impervious_pct | 863,557 | 0.00 | 46.89 | 49.36 | 24.00 | 6.11 | 78.25 | -0.37 |
| ndvi_median_may_aug | 863,557 | 0.00 | 0.38 | 0.39 | 0.11 | 0.20 | 0.50 | -0.29 |
| lst_median_may_aug | 863,557 | 0.00 | 299.40 | 299.37 | 2.18 | 296.67 | 302.14 | -0.01 |
| dist_to_water_m | 863,557 | 0.00 | 349.38 | 254.56 | 330.09 | 30.00 | 810.00 | 1.56 |
| elevation_m | 863,557 | 0.00 | 1,376.88 | 1,353.45 | 92.22 | 1,288.67 | 1,500.22 | 1.60 |
| n_valid_ecostress_passes | 863,557 | 0.00 | 30.12 | 30.00 | 3.13 | 26.00 | 34.00 | -0.24 |

### Land-cover composition

| land_cover_class | land_cover_label | n_rows | share_pct |
| --- | --- | --- | --- |
| 23 | Developed, Medium Intensity | 347,741 | 40.27 |
| 22 | Developed, Low Intensity | 287,149 | 33.25 |
| 24 | Developed, High Intensity | 87,559 | 10.14 |
| 21 | Developed, Open Space | 52,927 | 6.13 |
| 52 | Shrub/Scrub | 36,426 | 4.22 |
| 95 | Emergent Herbaceous Wetlands | 13,135 | 1.52 |
| 81 | Pasture/Hay | 12,391 | 1.43 |
| 82 | Cultivated Crops | 11,273 | 1.31 |

### Missingness for key variables

| variable | missing_n | missing_pct | non_missing_n |
| --- | --- | --- | --- |
| dist_to_water_m | 0 | 0.0000 | 863,557 |
| elevation_m | 0 | 0.0000 | 863,557 |
| hotspot_10pct | 0 | 0.0000 | 863,557 |
| impervious_pct | 0 | 0.0000 | 863,557 |
| land_cover_class | 0 | 0.0000 | 863,557 |
| lst_median_may_aug | 0 | 0.0000 | 863,557 |
| n_valid_ecostress_passes | 0 | 0.0000 | 863,557 |
| ndvi_median_may_aug | 0 | 0.0000 | 863,557 |

### Correlation matrix

| variable | lst_median_may_aug | impervious_pct | ndvi_median_may_aug | dist_to_water_m | elevation_m | n_valid_ecostress_passes |
| --- | --- | --- | --- | --- | --- | --- |
| lst_median_may_aug | 1.00 | 0.26 | -0.58 | 0.15 | -0.29 | 0.11 |
| impervious_pct | 0.26 | 1.00 | -0.39 | 0.23 | -0.26 | 0.30 |
| ndvi_median_may_aug | -0.58 | -0.39 | 1.00 | -0.18 | 0.44 | -0.40 |
| dist_to_water_m | 0.15 | 0.23 | -0.18 | 1.00 | -0.06 | 0.24 |
| elevation_m | -0.29 | -0.26 | 0.44 | -0.06 | 1.00 | -0.36 |
| n_valid_ecostress_passes | 0.11 | 0.30 | -0.40 | 0.24 | -0.36 | 1.00 |

## Figures

![Salt Lake City key distributions](../../../../figures/data_processing/city_summaries/07_salt_lake_city_ut/salt_lake_city_key_distributions.png)

![Salt Lake City land-cover composition](../../../../figures/data_processing/city_summaries/07_salt_lake_city_ut/salt_lake_city_land_cover_composition.png)

![Salt Lake City key correlations](../../../../figures/data_processing/city_summaries/07_salt_lake_city_ut/salt_lake_city_key_correlations.png)

![Salt Lake City hotspot map](../../../../figures/data_processing/city_summaries/07_salt_lake_city_ut/salt_lake_city_hotspot_map.png)

## Notable Patterns

- None of the key modeling variables have missing values in the filtered Salt Lake City table.
- `hotspot_10pct` is intentionally imbalanced at 10.00% positives because it marks the Salt Lake City-specific top decile of LST.
- Land cover is concentrated in Developed, Medium Intensity cells, which make up 40.3% of the filtered Salt Lake City dataset.
- The strongest linear relationship with LST among the key numeric variables is negative for `ndvi_median_may_aug` (r = -0.58).
- Hotspot prevalence varies by Salt Lake City quadrant from 3.7% to 18.6%, which is consistent with non-random spatial concentration.
- `elevation_m` is strongly skewed (skew = 1.60), so transformations or robust summaries may be useful in later modeling.

## Output Notes

- The Salt Lake City-only per-city feature parquet was chosen over the merged final dataset when it was available because it is the direct analysis-ready output for this city and already reflects the row-drop rules used by the pipeline.
- Supporting CSV tables and PNG figures for this summary were generated deterministically by the companion CLI.
- City markdown and tables live under `outputs/data_processing/city_summaries/`, batch summary tables live under `outputs/data_processing/batch_reports/`, and figures live under `figures/data_processing/city_summaries/`.
- `outputs/modeling/` and `figures/modeling/` remain reserved for ML/evaluation artifacts.
