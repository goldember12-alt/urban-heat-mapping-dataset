# Bakersfield Summary of Data

The Bakersfield summary uses `data_processed\city_features\09_bakersfield_ca_features.parquet`, the canonical Bakersfield-only analysis-ready feature table. Each observation represents one filtered 30 m grid cell inside the buffered Bakersfield study area, with built-form, vegetation, elevation, hydrologic proximity, and warm-season surface-temperature attributes aligned to the same cell geometry. The table is intended for downstream urban heat modeling in a hot_arid city, including both continuous LST analysis and binary hotspot prediction.

## Overview

| metric | value |
| --- | --- |
| Primary Bakersfield analysis file | data_processed\city_features\09_bakersfield_ca_features.parquet |
| Dataset choice rationale | Canonical per-city filtered output intended for downstream modeling. |
| Observations | 382964 |
| Variables | 16 |
| Unit of analysis | One filtered 30 m grid cell in the buffered Bakersfield study area |
| Geometry / CRS | Cell polygons stored in EPSG:32611; centroids stored as WGS84 lon/lat |
| Projected spatial extent | [299430, 3903840, 330900, 3925920] |
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
| unfiltered_input_rows | 684,592 | 100.00 |
| dropped_open_water_rows | 2,181 | 0.32 |
| dropped_lt3_ecostress_pass_rows | 140 | 0.02 |
| final_filtered_rows | 382,964 | 55.94 |

### Key numeric summary

| variable | n_non_missing | missing_pct | mean | median | std | p10 | p90 | skew |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| impervious_pct | 382,964 | 0.00 | 44.17 | 49.26 | 23.25 | 8.26 | 71.25 | -0.36 |
| ndvi_median_may_aug | 382,964 | 0.00 | 0.26 | 0.26 | 0.07 | 0.18 | 0.34 | 0.88 |
| lst_median_may_aug | 382,964 | 0.00 | 313.47 | 313.57 | 1.59 | 311.72 | 315.12 | -0.95 |
| dist_to_water_m | 382,964 | 0.00 | 501.07 | 375.90 | 446.70 | 60.00 | 1,148.26 | 1.34 |
| elevation_m | 382,964 | 0.00 | 127.36 | 117.39 | 28.52 | 107.89 | 165.03 | 2.44 |
| n_valid_ecostress_passes | 382,964 | 0.00 | 34.52 | 35.00 | 1.45 | 33.00 | 36.00 | -1.34 |

### Land-cover composition

| land_cover_class | land_cover_label | n_rows | share_pct |
| --- | --- | --- | --- |
| 23 | Developed, Medium Intensity | 168,341 | 43.96 |
| 22 | Developed, Low Intensity | 108,359 | 28.29 |
| 21 | Developed, Open Space | 51,199 | 13.37 |
| 24 | Developed, High Intensity | 23,812 | 6.22 |
| 82 | Cultivated Crops | 18,694 | 4.88 |
| 71 | Grassland/Herbaceous | 10,585 | 2.76 |
| 52 | Shrub/Scrub | 951 | 0.25 |
| 95 | Emergent Herbaceous Wetlands | 638 | 0.17 |

### Missingness for key variables

| variable | missing_n | missing_pct | non_missing_n |
| --- | --- | --- | --- |
| dist_to_water_m | 0 | 0.0000 | 382,964 |
| elevation_m | 0 | 0.0000 | 382,964 |
| hotspot_10pct | 0 | 0.0000 | 382,964 |
| impervious_pct | 0 | 0.0000 | 382,964 |
| land_cover_class | 0 | 0.0000 | 382,964 |
| lst_median_may_aug | 0 | 0.0000 | 382,964 |
| n_valid_ecostress_passes | 0 | 0.0000 | 382,964 |
| ndvi_median_may_aug | 0 | 0.0000 | 382,964 |

### Correlation matrix

| variable | lst_median_may_aug | impervious_pct | ndvi_median_may_aug | dist_to_water_m | elevation_m | n_valid_ecostress_passes |
| --- | --- | --- | --- | --- | --- | --- |
| lst_median_may_aug | 1.00 | 0.02 | -0.51 | 0.02 | -0.08 | -0.08 |
| impervious_pct | 0.02 | 1.00 | -0.17 | 0.10 | -0.01 | 0.28 |
| ndvi_median_may_aug | -0.51 | -0.17 | 1.00 | 0.06 | -0.03 | -0.10 |
| dist_to_water_m | 0.02 | 0.10 | 0.06 | 1.00 | 0.29 | 0.06 |
| elevation_m | -0.08 | -0.01 | -0.03 | 0.29 | 1.00 | 0.01 |
| n_valid_ecostress_passes | -0.08 | 0.28 | -0.10 | 0.06 | 0.01 | 1.00 |

## Figures

![Bakersfield key distributions](../../../../figures/data_processing/city_summaries/09_bakersfield_ca/bakersfield_key_distributions.png)

![Bakersfield land-cover composition](../../../../figures/data_processing/city_summaries/09_bakersfield_ca/bakersfield_land_cover_composition.png)

![Bakersfield key correlations](../../../../figures/data_processing/city_summaries/09_bakersfield_ca/bakersfield_key_correlations.png)

![Bakersfield hotspot map](../../../../figures/data_processing/city_summaries/09_bakersfield_ca/bakersfield_hotspot_map.png)

## Notable Patterns

- None of the key modeling variables have missing values in the filtered Bakersfield table.
- `hotspot_10pct` is intentionally imbalanced at 10.00% positives because it marks the Bakersfield-specific top decile of LST.
- Land cover is concentrated in Developed, Medium Intensity cells, which make up 44.0% of the filtered Bakersfield dataset.
- The strongest linear relationship with LST among the key numeric variables is negative for `ndvi_median_may_aug` (r = -0.51).
- Hotspot prevalence varies by Bakersfield quadrant from 5.4% to 17.0%, which is consistent with non-random spatial concentration.
- `elevation_m` is strongly skewed (skew = 2.44), so transformations or robust summaries may be useful in later modeling.

## Output Notes

- The Bakersfield-only per-city feature parquet was chosen over the merged final dataset when it was available because it is the direct analysis-ready output for this city and already reflects the row-drop rules used by the pipeline.
- Supporting CSV tables and PNG figures for this summary were generated deterministically by the companion CLI.
- City markdown and tables live under `outputs/data_processing/city_summaries/`, batch summary tables live under `outputs/data_processing/batch_reports/`, and figures live under `figures/data_processing/city_summaries/`.
- `outputs/modeling/` and `figures/modeling/` remain reserved for ML/evaluation artifacts.
