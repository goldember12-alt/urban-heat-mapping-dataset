# Nashville Summary of Data

The Nashville summary uses `data_processed\city_features\20_nashville_tn_features.parquet`, the canonical Nashville-only analysis-ready feature table. Each observation represents one filtered 30 m grid cell inside the buffered Nashville study area, with built-form, vegetation, elevation, hydrologic proximity, and warm-season surface-temperature attributes aligned to the same cell geometry. The table is intended for downstream urban heat modeling in a hot_humid city, including both continuous LST analysis and binary hotspot prediction.

## Overview

| metric | value |
| --- | --- |
| Primary Nashville analysis file | data_processed\city_features\20_nashville_tn_features.parquet |
| Dataset choice rationale | Canonical per-city filtered output intended for downstream modeling. |
| Observations | 1680248 |
| Variables | 16 |
| Unit of analysis | One filtered 30 m grid cell in the buffered Nashville study area |
| Geometry / CRS | Cell polygons stored in EPSG:32616; centroids stored as WGS84 lon/lat |
| Projected spatial extent | [497670, 3963300, 555840, 4033860] |
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
| unfiltered_input_rows | 2,876,724 | 100.00 |
| dropped_open_water_rows | 121,373 | 4.22 |
| dropped_lt3_ecostress_pass_rows | 354 | 0.01 |
| final_filtered_rows | 1,680,248 | 58.41 |

### Key numeric summary

| variable | n_non_missing | missing_pct | mean | median | std | p10 | p90 | skew |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| impervious_pct | 1,680,248 | 0.00 | 26.83 | 20.58 | 25.21 | 0.00 | 66.12 | 0.81 |
| ndvi_median_may_aug | 1,680,248 | 0.00 | 0.67 | 0.69 | 0.11 | 0.52 | 0.78 | -1.00 |
| lst_median_may_aug | 1,680,248 | 0.00 | 307.13 | 307.09 | 2.66 | 303.68 | 310.58 | 0.11 |
| dist_to_water_m | 1,680,248 | 0.00 | 234.69 | 189.74 | 204.64 | 30.00 | 484.66 | 1.89 |
| elevation_m | 1,680,248 | 0.00 | 177.88 | 171.91 | 32.60 | 141.36 | 223.01 | 0.92 |
| n_valid_ecostress_passes | 1,680,248 | 0.00 | 19.01 | 19.00 | 2.09 | 16.00 | 22.00 | -0.07 |

### Land-cover composition

| land_cover_class | land_cover_label | n_rows | share_pct |
| --- | --- | --- | --- |
| 22 | Developed, Low Intensity | 478,038 | 28.45 |
| 21 | Developed, Open Space | 429,521 | 25.56 |
| 23 | Developed, Medium Intensity | 271,326 | 16.15 |
| 41 | Deciduous Forest | 160,006 | 9.52 |
| 81 | Pasture/Hay | 146,683 | 8.73 |
| 24 | Developed, High Intensity | 94,191 | 5.61 |
| 43 | Mixed Forest | 61,827 | 3.68 |
| 42 | Evergreen Forest | 21,212 | 1.26 |

### Missingness for key variables

| variable | missing_n | missing_pct | non_missing_n |
| --- | --- | --- | --- |
| dist_to_water_m | 0 | 0.0000 | 1,680,248 |
| elevation_m | 0 | 0.0000 | 1,680,248 |
| hotspot_10pct | 0 | 0.0000 | 1,680,248 |
| impervious_pct | 0 | 0.0000 | 1,680,248 |
| land_cover_class | 0 | 0.0000 | 1,680,248 |
| lst_median_may_aug | 0 | 0.0000 | 1,680,248 |
| n_valid_ecostress_passes | 0 | 0.0000 | 1,680,248 |
| ndvi_median_may_aug | 0 | 0.0000 | 1,680,248 |

### Correlation matrix

| variable | lst_median_may_aug | impervious_pct | ndvi_median_may_aug | dist_to_water_m | elevation_m | n_valid_ecostress_passes |
| --- | --- | --- | --- | --- | --- | --- |
| lst_median_may_aug | 1.00 | 0.62 | -0.71 | 0.22 | -0.34 | 0.09 |
| impervious_pct | 0.62 | 1.00 | -0.64 | 0.20 | -0.16 | 0.29 |
| ndvi_median_may_aug | -0.71 | -0.64 | 1.00 | -0.27 | 0.33 | -0.29 |
| dist_to_water_m | 0.22 | 0.20 | -0.27 | 1.00 | 0.01 | 0.20 |
| elevation_m | -0.34 | -0.16 | 0.33 | 0.01 | 1.00 | 0.21 |
| n_valid_ecostress_passes | 0.09 | 0.29 | -0.29 | 0.20 | 0.21 | 1.00 |

## Figures

![Nashville key distributions](../../../../figures/data_processing/city_summaries/20_nashville_tn/nashville_key_distributions.png)

![Nashville land-cover composition](../../../../figures/data_processing/city_summaries/20_nashville_tn/nashville_land_cover_composition.png)

![Nashville key correlations](../../../../figures/data_processing/city_summaries/20_nashville_tn/nashville_key_correlations.png)

![Nashville hotspot map](../../../../figures/data_processing/city_summaries/20_nashville_tn/nashville_hotspot_map.png)

## Notable Patterns

- None of the key modeling variables have missing values in the filtered Nashville table.
- `hotspot_10pct` is intentionally imbalanced at 10.00% positives because it marks the Nashville-specific top decile of LST.
- Land cover is concentrated in Developed, Low Intensity cells, which make up 28.5% of the filtered Nashville dataset.
- The strongest linear relationship with LST among the key numeric variables is negative for `ndvi_median_may_aug` (r = -0.71).
- Hotspot prevalence varies by Nashville quadrant from 5.7% to 16.3%, which is consistent with non-random spatial concentration.
- `dist_to_water_m` is strongly skewed (skew = 1.89), so transformations or robust summaries may be useful in later modeling.

## Output Notes

- The Nashville-only per-city feature parquet was chosen over the merged final dataset when it was available because it is the direct analysis-ready output for this city and already reflects the row-drop rules used by the pipeline.
- Supporting CSV tables and PNG figures for this summary were generated deterministically by the companion CLI.
- City markdown and tables live under `outputs/data_processing/city_summaries/`, batch summary tables live under `outputs/data_processing/batch_reports/`, and figures live under `figures/data_processing/city_summaries/`.
- `outputs/modeling/` and `figures/modeling/` remain reserved for ML/evaluation artifacts.
