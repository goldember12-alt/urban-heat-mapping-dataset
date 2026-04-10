# Denver Summary of Data

The Denver summary uses `data_processed\city_features\06_denver_co_features.parquet`, the canonical Denver-only analysis-ready feature table. Each observation represents one filtered 30 m grid cell inside the buffered Denver study area, with built-form, vegetation, elevation, hydrologic proximity, and warm-season surface-temperature attributes aligned to the same cell geometry. The table is intended for downstream urban heat modeling in a hot_arid city, including both continuous LST analysis and binary hotspot prediction.

## Overview

| metric | value |
| --- | --- |
| Primary Denver analysis file | data_processed\city_features\06_denver_co_features.parquet |
| Dataset choice rationale | Canonical per-city filtered output intended for downstream modeling. |
| Observations | 1859393 |
| Variables | 16 |
| Unit of analysis | One filtered 30 m grid cell in the buffered Denver study area |
| Geometry / CRS | Cell polygons stored in EPSG:32613; centroids stored as WGS84 lon/lat |
| Projected spatial extent | [478770, 4369890, 529140, 4431450] |
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
| unfiltered_input_rows | 2,830,218 | 100.00 |
| dropped_open_water_rows | 64,091 | 2.26 |
| dropped_lt3_ecostress_pass_rows | 420 | 0.01 |
| final_filtered_rows | 1,859,393 | 65.70 |

### Key numeric summary

| variable | n_non_missing | missing_pct | mean | median | std | p10 | p90 | skew |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| impervious_pct | 1,859,393 | 0.00 | 42.97 | 43.93 | 22.64 | 8.31 | 70.86 | -0.21 |
| ndvi_median_may_aug | 1,859,393 | 0.00 | 0.43 | 0.44 | 0.10 | 0.30 | 0.55 | -0.46 |
| lst_median_may_aug | 1,859,393 | 0.00 | 293.13 | 293.23 | 1.36 | 291.34 | 294.75 | -0.36 |
| dist_to_water_m | 1,859,393 | 0.00 | 294.24 | 192.09 | 311.75 | 30.00 | 690.00 | 2.08 |
| elevation_m | 1,859,393 | 0.00 | 1,677.20 | 1,664.26 | 80.87 | 1,579.07 | 1,793.28 | 0.53 |
| n_valid_ecostress_passes | 1,859,393 | 0.00 | 30.33 | 30.00 | 2.03 | 28.00 | 33.00 | 0.24 |

### Land-cover composition

| land_cover_class | land_cover_label | n_rows | share_pct |
| --- | --- | --- | --- |
| 22 | Developed, Low Intensity | 740,301 | 39.81 |
| 23 | Developed, Medium Intensity | 676,255 | 36.37 |
| 21 | Developed, Open Space | 154,521 | 8.31 |
| 24 | Developed, High Intensity | 110,328 | 5.93 |
| 71 | Grassland/Herbaceous | 105,237 | 5.66 |
| 95 | Emergent Herbaceous Wetlands | 30,049 | 1.62 |
| 52 | Shrub/Scrub | 19,660 | 1.06 |
| 82 | Cultivated Crops | 17,383 | 0.93 |

### Missingness for key variables

| variable | missing_n | missing_pct | non_missing_n |
| --- | --- | --- | --- |
| dist_to_water_m | 0 | 0.0000 | 1,859,393 |
| elevation_m | 0 | 0.0000 | 1,859,393 |
| hotspot_10pct | 0 | 0.0000 | 1,859,393 |
| impervious_pct | 0 | 0.0000 | 1,859,393 |
| land_cover_class | 0 | 0.0000 | 1,859,393 |
| lst_median_may_aug | 0 | 0.0000 | 1,859,393 |
| n_valid_ecostress_passes | 0 | 0.0000 | 1,859,393 |
| ndvi_median_may_aug | 0 | 0.0000 | 1,859,393 |

### Correlation matrix

| variable | lst_median_may_aug | impervious_pct | ndvi_median_may_aug | dist_to_water_m | elevation_m | n_valid_ecostress_passes |
| --- | --- | --- | --- | --- | --- | --- |
| lst_median_may_aug | 1.00 | 0.32 | -0.34 | 0.21 | -0.40 | -0.06 |
| impervious_pct | 0.32 | 1.00 | -0.39 | 0.15 | -0.13 | 0.07 |
| ndvi_median_may_aug | -0.34 | -0.39 | 1.00 | -0.17 | 0.27 | -0.08 |
| dist_to_water_m | 0.21 | 0.15 | -0.17 | 1.00 | -0.25 | 0.08 |
| elevation_m | -0.40 | -0.13 | 0.27 | -0.25 | 1.00 | 0.28 |
| n_valid_ecostress_passes | -0.06 | 0.07 | -0.08 | 0.08 | 0.28 | 1.00 |

## Figures

![Denver key distributions](../../../../figures/data_processing/city_summaries/06_denver_co/denver_key_distributions.png)

![Denver land-cover composition](../../../../figures/data_processing/city_summaries/06_denver_co/denver_land_cover_composition.png)

![Denver key correlations](../../../../figures/data_processing/city_summaries/06_denver_co/denver_key_correlations.png)

![Denver hotspot map](../../../../figures/data_processing/city_summaries/06_denver_co/denver_hotspot_map.png)

## Notable Patterns

- None of the key modeling variables have missing values in the filtered Denver table.
- `hotspot_10pct` is intentionally imbalanced at 10.00% positives because it marks the Denver-specific top decile of LST.
- Land cover is concentrated in Developed, Low Intensity cells, which make up 39.8% of the filtered Denver dataset.
- The strongest linear relationship with LST among the key numeric variables is negative for `elevation_m` (r = -0.40).
- Hotspot prevalence varies by Denver quadrant from 1.8% to 23.8%, which is consistent with non-random spatial concentration.
- `dist_to_water_m` is strongly skewed (skew = 2.08), so transformations or robust summaries may be useful in later modeling.

## Output Notes

- The Denver-only per-city feature parquet was chosen over the merged final dataset when it was available because it is the direct analysis-ready output for this city and already reflects the row-drop rules used by the pipeline.
- Supporting CSV tables and PNG figures for this summary were generated deterministically by the companion CLI.
- City markdown and tables live under `outputs/data_processing/city_summaries/`, batch summary tables live under `outputs/data_processing/batch_reports/`, and figures live under `figures/data_processing/city_summaries/`.
- `outputs/modeling/` and `figures/modeling/` remain reserved for ML/evaluation artifacts.
