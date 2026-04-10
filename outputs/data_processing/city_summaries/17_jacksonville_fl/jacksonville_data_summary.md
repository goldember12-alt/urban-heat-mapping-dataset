# Jacksonville Summary of Data

The Jacksonville summary uses `data_processed\city_features\17_jacksonville_fl_features.parquet`, the canonical Jacksonville-only analysis-ready feature table. Each observation represents one filtered 30 m grid cell inside the buffered Jacksonville study area, with built-form, vegetation, elevation, hydrologic proximity, and warm-season surface-temperature attributes aligned to the same cell geometry. The table is intended for downstream urban heat modeling in a hot_humid city, including both continuous LST analysis and binary hotspot prediction.

## Overview

| metric | value |
| --- | --- |
| Primary Jacksonville analysis file | data_processed\city_features\17_jacksonville_fl_features.parquet |
| Dataset choice rationale | Canonical per-city filtered output intended for downstream modeling. |
| Observations | 1664542 |
| Variables | 16 |
| Unit of analysis | One filtered 30 m grid cell in the buffered Jacksonville study area |
| Geometry / CRS | Cell polygons stored in EPSG:32617; centroids stored as WGS84 lon/lat |
| Projected spatial extent | [415050, 3314070, 468870, 3379560] |
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
| unfiltered_input_rows | 2,817,139 | 100.00 |
| dropped_open_water_rows | 411,878 | 14.62 |
| dropped_lt3_ecostress_pass_rows | 363 | 0.01 |
| final_filtered_rows | 1,664,542 | 59.09 |

### Key numeric summary

| variable | n_non_missing | missing_pct | mean | median | std | p10 | p90 | skew |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| impervious_pct | 1,664,542 | 0.00 | 29.15 | 25.98 | 25.70 | 0.00 | 65.77 | 0.53 |
| ndvi_median_may_aug | 1,664,542 | 0.00 | 0.61 | 0.62 | 0.10 | 0.48 | 0.73 | -0.81 |
| lst_median_may_aug | 1,664,542 | 0.00 | 300.01 | 299.97 | 1.01 | 298.76 | 301.25 | 0.52 |
| dist_to_water_m | 1,664,542 | 0.00 | 110.50 | 67.08 | 125.03 | 0.00 | 276.59 | 1.74 |
| elevation_m | 1,664,542 | 0.00 | 8.06 | 6.62 | 6.19 | 1.68 | 18.60 | 1.32 |
| n_valid_ecostress_passes | 1,664,542 | 0.00 | 20.64 | 21.00 | 2.37 | 18.00 | 24.00 | 0.20 |

### Land-cover composition

| land_cover_class | land_cover_label | n_rows | share_pct |
| --- | --- | --- | --- |
| 22 | Developed, Low Intensity | 514,888 | 30.93 |
| 23 | Developed, Medium Intensity | 322,302 | 19.36 |
| 90 | Woody Wetlands | 273,689 | 16.44 |
| 21 | Developed, Open Space | 253,125 | 15.21 |
| 42 | Evergreen Forest | 140,733 | 8.45 |
| 24 | Developed, High Intensity | 89,451 | 5.37 |
| 95 | Emergent Herbaceous Wetlands | 45,363 | 2.73 |
| 81 | Pasture/Hay | 13,699 | 0.82 |

### Missingness for key variables

| variable | missing_n | missing_pct | non_missing_n |
| --- | --- | --- | --- |
| dist_to_water_m | 0 | 0.0000 | 1,664,542 |
| elevation_m | 0 | 0.0000 | 1,664,542 |
| hotspot_10pct | 0 | 0.0000 | 1,664,542 |
| impervious_pct | 0 | 0.0000 | 1,664,542 |
| land_cover_class | 0 | 0.0000 | 1,664,542 |
| lst_median_may_aug | 0 | 0.0000 | 1,664,542 |
| n_valid_ecostress_passes | 0 | 0.0000 | 1,664,542 |
| ndvi_median_may_aug | 0 | 0.0000 | 1,664,542 |

### Correlation matrix

| variable | lst_median_may_aug | impervious_pct | ndvi_median_may_aug | dist_to_water_m | elevation_m | n_valid_ecostress_passes |
| --- | --- | --- | --- | --- | --- | --- |
| lst_median_may_aug | 1.00 | 0.35 | -0.52 | 0.21 | -0.09 | 0.20 |
| impervious_pct | 0.35 | 1.00 | -0.55 | 0.29 | 0.05 | 0.19 |
| ndvi_median_may_aug | -0.52 | -0.55 | 1.00 | -0.24 | 0.11 | -0.23 |
| dist_to_water_m | 0.21 | 0.29 | -0.24 | 1.00 | 0.14 | 0.20 |
| elevation_m | -0.09 | 0.05 | 0.11 | 0.14 | 1.00 | 0.06 |
| n_valid_ecostress_passes | 0.20 | 0.19 | -0.23 | 0.20 | 0.06 | 1.00 |

## Figures

![Jacksonville key distributions](../../../../figures/data_processing/city_summaries/17_jacksonville_fl/jacksonville_key_distributions.png)

![Jacksonville land-cover composition](../../../../figures/data_processing/city_summaries/17_jacksonville_fl/jacksonville_land_cover_composition.png)

![Jacksonville key correlations](../../../../figures/data_processing/city_summaries/17_jacksonville_fl/jacksonville_key_correlations.png)

![Jacksonville hotspot map](../../../../figures/data_processing/city_summaries/17_jacksonville_fl/jacksonville_hotspot_map.png)

## Notable Patterns

- None of the key modeling variables have missing values in the filtered Jacksonville table.
- `hotspot_10pct` is intentionally imbalanced at 10.00% positives because it marks the Jacksonville-specific top decile of LST.
- Land cover is concentrated in Developed, Low Intensity cells, which make up 30.9% of the filtered Jacksonville dataset.
- The strongest linear relationship with LST among the key numeric variables is negative for `ndvi_median_may_aug` (r = -0.52).
- Hotspot prevalence varies by Jacksonville quadrant from 3.7% to 14.4%, which is consistent with non-random spatial concentration.
- `dist_to_water_m` is strongly skewed (skew = 1.74), so transformations or robust summaries may be useful in later modeling.

## Output Notes

- The Jacksonville-only per-city feature parquet was chosen over the merged final dataset when it was available because it is the direct analysis-ready output for this city and already reflects the row-drop rules used by the pipeline.
- Supporting CSV tables and PNG figures for this summary were generated deterministically by the companion CLI.
- City markdown and tables live under `outputs/data_processing/city_summaries/`, batch summary tables live under `outputs/data_processing/batch_reports/`, and figures live under `figures/data_processing/city_summaries/`.
- `outputs/modeling/` and `figures/modeling/` remain reserved for ML/evaluation artifacts.
