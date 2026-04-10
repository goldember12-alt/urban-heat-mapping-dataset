# Portland Summary of Data

The Portland summary uses `data_processed\city_features\22_portland_or_features.parquet`, the canonical Portland-only analysis-ready feature table. Each observation represents one filtered 30 m grid cell inside the buffered Portland study area, with built-form, vegetation, elevation, hydrologic proximity, and warm-season surface-temperature attributes aligned to the same cell geometry. The table is intended for downstream urban heat modeling in a mild_cool city, including both continuous LST analysis and binary hotspot prediction.

## Overview

| metric | value |
| --- | --- |
| Primary Portland analysis file | data_processed\city_features\22_portland_or_features.parquet |
| Dataset choice rationale | Canonical per-city filtered output intended for downstream modeling. |
| Observations | 1496116 |
| Variables | 16 |
| Unit of analysis | One filtered 30 m grid cell in the buffered Portland study area |
| Geometry / CRS | Cell polygons stored in EPSG:32610; centroids stored as WGS84 lon/lat |
| Projected spatial extent | [488010, 5001900, 554130, 5072250] |
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
| unfiltered_input_rows | 2,563,107 | 100.00 |
| dropped_open_water_rows | 101,510 | 3.96 |
| dropped_lt3_ecostress_pass_rows | 377 | 0.01 |
| final_filtered_rows | 1,496,116 | 58.37 |

### Key numeric summary

| variable | n_non_missing | missing_pct | mean | median | std | p10 | p90 | skew |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| impervious_pct | 1,496,116 | 0.00 | 41.83 | 45.30 | 26.76 | 0.10 | 77.61 | -0.09 |
| ndvi_median_may_aug | 1,496,116 | 0.00 | 0.55 | 0.55 | 0.12 | 0.40 | 0.69 | -0.19 |
| lst_median_may_aug | 1,496,116 | 0.00 | 295.01 | 295.10 | 1.18 | 293.44 | 296.43 | -0.24 |
| dist_to_water_m | 1,496,116 | 0.00 | 392.67 | 234.31 | 450.44 | 30.00 | 999.05 | 2.02 |
| elevation_m | 1,496,116 | 0.00 | 80.76 | 70.45 | 50.91 | 21.45 | 152.37 | 1.29 |
| n_valid_ecostress_passes | 1,496,116 | 0.00 | 37.22 | 37.00 | 2.19 | 35.00 | 40.00 | 0.32 |

### Land-cover composition

| land_cover_class | land_cover_label | n_rows | share_pct |
| --- | --- | --- | --- |
| 23 | Developed, Medium Intensity | 538,215 | 35.97 |
| 22 | Developed, Low Intensity | 394,212 | 26.35 |
| 21 | Developed, Open Space | 214,514 | 14.34 |
| 24 | Developed, High Intensity | 147,185 | 9.84 |
| 81 | Pasture/Hay | 93,401 | 6.24 |
| 43 | Mixed Forest | 40,440 | 2.70 |
| 42 | Evergreen Forest | 28,460 | 1.90 |
| 90 | Woody Wetlands | 13,219 | 0.88 |

### Missingness for key variables

| variable | missing_n | missing_pct | non_missing_n |
| --- | --- | --- | --- |
| dist_to_water_m | 0 | 0.0000 | 1,496,116 |
| elevation_m | 0 | 0.0000 | 1,496,116 |
| hotspot_10pct | 0 | 0.0000 | 1,496,116 |
| impervious_pct | 0 | 0.0000 | 1,496,116 |
| land_cover_class | 0 | 0.0000 | 1,496,116 |
| lst_median_may_aug | 0 | 0.0000 | 1,496,116 |
| n_valid_ecostress_passes | 0 | 0.0000 | 1,496,116 |
| ndvi_median_may_aug | 0 | 0.0000 | 1,496,116 |

### Correlation matrix

| variable | lst_median_may_aug | impervious_pct | ndvi_median_may_aug | dist_to_water_m | elevation_m | n_valid_ecostress_passes |
| --- | --- | --- | --- | --- | --- | --- |
| lst_median_may_aug | 1.00 | 0.50 | -0.50 | 0.18 | -0.32 | -0.03 |
| impervious_pct | 0.50 | 1.00 | -0.63 | 0.26 | -0.34 | 0.18 |
| ndvi_median_may_aug | -0.50 | -0.63 | 1.00 | -0.34 | 0.50 | -0.20 |
| dist_to_water_m | 0.18 | 0.26 | -0.34 | 1.00 | -0.08 | 0.09 |
| elevation_m | -0.32 | -0.34 | 0.50 | -0.08 | 1.00 | -0.15 |
| n_valid_ecostress_passes | -0.03 | 0.18 | -0.20 | 0.09 | -0.15 | 1.00 |

## Figures

![Portland key distributions](../../../../figures/data_processing/city_summaries/22_portland_or/portland_key_distributions.png)

![Portland land-cover composition](../../../../figures/data_processing/city_summaries/22_portland_or/portland_land_cover_composition.png)

![Portland key correlations](../../../../figures/data_processing/city_summaries/22_portland_or/portland_key_correlations.png)

![Portland hotspot map](../../../../figures/data_processing/city_summaries/22_portland_or/portland_hotspot_map.png)

## Notable Patterns

- None of the key modeling variables have missing values in the filtered Portland table.
- `hotspot_10pct` is intentionally imbalanced at 10.00% positives because it marks the Portland-specific top decile of LST.
- Land cover is concentrated in Developed, Medium Intensity cells, which make up 36.0% of the filtered Portland dataset.
- The strongest linear relationship with LST among the key numeric variables is negative for `ndvi_median_may_aug` (r = -0.50).
- Hotspot prevalence varies by Portland quadrant from 5.4% to 14.3%, which is consistent with non-random spatial concentration.
- `dist_to_water_m` is strongly skewed (skew = 2.02), so transformations or robust summaries may be useful in later modeling.

## Output Notes

- The Portland-only per-city feature parquet was chosen over the merged final dataset when it was available because it is the direct analysis-ready output for this city and already reflects the row-drop rules used by the pipeline.
- Supporting CSV tables and PNG figures for this summary were generated deterministically by the companion CLI.
- City markdown and tables live under `outputs/data_processing/city_summaries/`, batch summary tables live under `outputs/data_processing/batch_reports/`, and figures live under `figures/data_processing/city_summaries/`.
- `outputs/modeling/` and `figures/modeling/` remain reserved for ML/evaluation artifacts.
