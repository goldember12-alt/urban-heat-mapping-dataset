# Supplemental Smoothed Spatial-Alignment Method Note

## Purpose

This document describes the supplemental spatial-placement diagnostic used in the STAT 5630 urban heat hotspot workflow. The main city-held-out benchmark evaluates whether models recover exact 30 m hotspot cells in held-out cities using ranking metrics such as PR AUC and recall at the top 10% predicted risk. The spatial-alignment diagnostic asks a related but different question:

> When a city-held-out model is imperfect at exact-cell retrieval, does it still place elevated hotspot risk in the correct broad parts of the city?

The diagnostic compares smoothed observed-hotspot surfaces with smoothed predicted-risk surfaces. It is supplemental. It is not a replacement for the leakage-safe exact-cell city-held-out transfer benchmark, and it should not be described as operational hotspot mapping evidence by itself.

## Relationship To The Main Benchmark

The retained city-held-out benchmark uses sampled held-out prediction rows for ranking metrics. That is adequate for PR AUC and recall-at-top-decile summaries, but sampled predictions are too sparse for report-grade smoothed spatial surfaces.

The spatial-alignment diagnostic therefore uses the same leakage-safe city-held-out training contract but changes the prediction/export scope for the diagnostic step:

1. keep sampled training and tuning rows so model fitting remains feasible;
2. fit each selected outer-fold model using training cities only;
3. score every eligible row in the held-out city or cities for that fold;
4. build smoothed observed and predicted surfaces from those full-city held-out predictions.

This keeps the benchmark logic intact: held-out cities remain fully unseen during training and tuning. The only change is that prediction/export for selected cities uses full-city scoring rather than sampled held-out scoring.

## Diagnostic Scope

The diagnostic produces:

- full eligible held-out city scoring for the diagnostic model;
- smoothed observed and predicted surfaces at multiple smoothing scales;
- cell/raster-based alignment metrics before any optional polygonization;
- optional maps for selected cities and scales.

Core metrics:

- Spearman correlation between smoothed observed-hotspot surface and smoothed predicted-risk surface;
- top 10% smoothed-region overlap;
- observed hotspot mass captured by the predicted top 10% smoothed region;
- centroid distance between observed and predicted top-region hotspot mass;
- median nearest-region distance from observed top-region cells to predicted top-region cells.

## Representative Cities

The first validation pass evaluated a small, interpretable set of held-out cities before expanding the metric table to all 30 cities.

The representative-city rule was:

1. include Denver because it already appears in the report as the qualitative spatial diagnostic;
2. include one representative city per climate group, selected from retained city-level RF metrics as the city closest to the climate-group median PR AUC;
3. if Denver is already selected by the climate-group rule, do not duplicate it;
4. record the selection rule and selected city IDs in an output table.

This yields roughly three to four cities and provides a bounded visual review set before all-city expansion.

After the method is validated, the diagnostic can be expanded to all 30 cities and summarized by model, scale, and climate group.

## All-City Expansion

The representative-city mode validated the random-forest spatial-alignment method. The all-city diagnostic then applies the same process to every held-out city in the five outer folds.

This all-city pass is not a new canonical benchmark. It uses the existing leakage-safe outer-fold structure:

1. use the five outer folds from `data_processed/modeling/city_outer_folds.csv` or `.parquet`;
2. each fold holds out six cities;
3. train and tune the RF pipeline once per fold on sampled training-city rows only;
4. score every eligible row for all six held-out cities in that fold;
5. compute the `150 m`, `300 m`, and `600 m` spatial-alignment metrics for all 30 cities.

This expands the spatial-placement diagnostic table from representative cities to the full city panel while preserving the grouped-city leakage-safe contract. It should still be described as a supplemental full-city spatial-placement diagnostic, not as a new canonical benchmark or replacement for the sampled held-out-city evaluation.

All-city outputs are kept separate from the representative-city validation outputs:

```text
outputs/modeling/supplemental/spatial_alignment_all_cities/
figures/modeling/supplemental/spatial_alignment_all_cities/
```

The all-city diagnostic tables use generic names under that separate output root:

```text
outputs/modeling/supplemental/spatial_alignment_all_cities/tables/all_city_selection.csv
outputs/modeling/supplemental/spatial_alignment_all_cities/tables/spatial_alignment_metrics_all_cities.csv
outputs/modeling/supplemental/spatial_alignment_all_cities/spatial_alignment_summary.md
```

Maps remain optional. The all-city metric table should be reviewed before selecting report cities and smoothing scales for map generation.

## Model Scope

The report-facing diagnostic focuses on random forest because it is the bounded nonlinear reference model in the report and the most relevant model for the spatial-placement question.

The feature contract is the same as the first-pass transfer benchmark. The model uses the six safe non-thermal predictors:

- `impervious_pct`
- `land_cover_class`
- `elevation_m`
- `dist_to_water_m`
- `ndvi_median_may_aug`
- `climate_group`

A matched logistic SAGA spatial-alignment diagnostic could be added later using the same full-city held-out scoring contract, but the current public method note describes the random-forest diagnostic used for the report-facing spatial-alignment results.

## Leakage-Safe Full-City Scoring Contract

For each selected model and selected held-out city:

1. Determine the city outer fold from `data_processed/modeling/city_outer_folds.parquet`.
2. Load training cities for that outer fold.
3. Sample training rows using the benchmark sample cap, e.g. `sample_rows_per_city=5000`.
4. Fit/tune preprocessing and model steps on training-city rows only.
5. Load all eligible rows for the selected held-out city from `data_processed/final/final_dataset.parquet`.
6. Apply the fitted pipeline to full held-out city rows.
7. Save full-city predictions with enough metadata to distinguish them from sampled benchmark predictions.

Required prediction columns:

- `city_id`
- `city_name`
- `climate_group`
- `outer_fold`
- `cell_id`
- `centroid_lon`
- `centroid_lat`
- `hotspot_10pct`
- `model_name`
- `predicted_probability`
- `prediction_scope`, with value `full_city`
- `training_sample_rows_per_city`
- `source_reference_run_dir`

The full-city prediction outputs are evaluation artifacts for spatial diagnostics. They should not replace the sampled benchmark metrics or be described as a new full benchmark unless the corresponding run is explicitly recorded and documented.

## Multi-Scale Design

Evaluate several smoothing scales. The point is not to find one perfect radius; the point is to test whether model alignment improves as the question moves from exact cells to broader hotspot zones.

Suggested scales:

| Scale label | Smoothing radius | Interpretation |
|---|---:|---|
| Fine | 150 m | small local clusters, roughly immediate blocks |
| Medium | 300 m | neighborhood-scale hotspot zones |
| Broad | 600 m | larger corridors or district-scale thermal zones |

On a 30 m grid these correspond approximately to 5, 10, and 20 cells. The metric table records the actual smoothing radius used for each row.

## Coordinate And Grid Handling

Full-city prediction rows have longitude and latitude but do not include city-local projected coordinates. The diagnostic reconstructs projected coordinates per city.

Coordinate handling:

1. Determine an appropriate local UTM CRS from the city centroid.
2. Reproject `centroid_lon` and `centroid_lat` to projected `x_m` and `y_m`.
3. Infer grid spacing from nearest unique projected coordinate differences.
4. Build a sparse raster-like cell index using rounded projected coordinates.
5. Validate that inferred spacing is compatible with the 30 m grid.
6. Record CRS, inferred spacing, row count, and any grid reconstruction warnings in diagnostics.

If robust raster reconstruction is not possible for a city, fall back to cell/point-based nearest-neighbor distance calculations for that city and flag the row as `grid_reconstruction_status != "ok"`.

## Smoothing Method

The diagnostic uses gridded full-city predictions when grid reconstruction succeeds.

For each city, model, and scale:

1. Build an observed binary raster from `hotspot_10pct`.
2. Build a predicted score raster from `predicted_probability`.
3. Build a valid-cell mask.
4. Apply Gaussian or circular moving-window smoothing to numerator arrays.
5. Apply the same smoothing to the valid-cell mask.
6. Divide smoothed numerators by smoothed valid-cell weights so edges and holes are normalized.
7. Mask invalid cells after smoothing.

This avoids treating cells outside the valid study area as zeros.

The smoothing method should be recorded in the output table. The report-facing implementation uses the table fields:

- `smoothing_method`
- `smoothing_radius_m`
- `smoothing_sigma_m`, if applicable
- `grid_cell_size_m`

## Top-Region Definition

High-intensity regions are defined as the top 10% of valid cells within each smoothed surface.

Selection rule:

- use rank-based selection by cell count rather than raw quantile comparison, because ties can otherwise create inconsistent selected areas;
- select `ceil(valid_cell_count * 0.10)` cells for observed and predicted surfaces separately;
- record `threshold_fraction=0.10`;
- sensitivity checks at other thresholds can be added later, but the report-facing diagnostic uses `threshold_fraction=0.10`.

## Metrics Table

One row per city, model, scale, and threshold.

Required columns:

- `city_id`
- `city_name`
- `climate_group`
- `outer_fold`
- `model_name`
- `source_reference_run_dir`
- `training_sample_rows_per_city`
- `prediction_scope`
- `row_count`
- `valid_cell_count`
- `scale_label`
- `smoothing_radius_m`
- `smoothing_method`
- `threshold_fraction`
- `spearman_surface_corr`
- `top_region_overlap_fraction`
- `observed_mass_captured`
- `centroid_distance_m`
- `median_nearest_region_distance_m`
- `observed_top_cell_count`
- `predicted_top_cell_count`
- `overlap_cell_count`
- `grid_cell_size_m`
- `projected_crs`
- `grid_reconstruction_status`

Metric definitions:

### Spearman Surface Correlation

Compute Spearman correlation between the smoothed observed-hotspot surface and smoothed predicted-risk surface over valid cells.

Interpretation:

- high values mean the model's broad risk gradients align with observed hotspot concentration gradients.

### Top 10% Overlap

```text
top_region_overlap_fraction = overlap_cell_count / union_cell_count
```

This is a cell/raster analogue of region IoU using the observed and predicted top smoothed regions.

### Observed Mass Captured

```text
observed_mass_captured =
    sum(observed_smoothed_surface over predicted_top_region)
    / sum(observed_smoothed_surface over all valid cells)
```

Interpretation:

- how much observed smoothed hotspot mass is captured by the model's predicted high-risk region.

### Centroid Distance

Compute weighted centroids for the observed top smoothed region and predicted top smoothed region, using the smoothed surface values as weights. Report projected distance in meters.

### Median Nearest-Region Distance

Compute the distance from each observed top-region cell to the nearest predicted top-region cell, then report the median distance in meters.

This captures near misses when top regions are spatially adjacent but do not overlap exactly.

## Maps

After the metric table is created and reviewed, maps can be generated for selected cities, models, and smoothing scales. Medium scale (`300 m`) is the primary report-facing map scale.

Recommended panels:

1. observed smoothed hotspot surface;
2. predicted smoothed risk surface;
3. observed top 10% smoothed region;
4. predicted top 10% smoothed region;
5. overlap, observed-only misses, and predicted-only areas.

Maps should use full-city predictions only. If a city has grid reconstruction warnings, the map title or metadata should expose that status.

## Polygonization Later

Polygonization is a possible later extension after the cell/raster metric path is stable.

Later polygonization steps:

1. Convert observed and predicted top-region rasters to vector polygons.
2. Dissolve contiguous cells.
3. Drop very small patches below a configurable area threshold.
4. Compute polygon IoU, coverage, purity, patch count, largest-patch share, and area-weighted nearest-patch distance.
5. Compare polygon metrics to the initial cell/raster metrics before using them in report prose.

Do not overinterpret polygon boundaries. They are diagnostic summaries of smoothed surfaces, not literal neighborhood or policy-zone boundaries.
