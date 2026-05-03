# Spatial Alignment Diagnostic Summary

This supplemental diagnostic uses the retained random-forest frontier contract for selected representative cities, with full eligible held-out rows scored for spatial analysis. Existing full-city prediction files can be reused for table and map generation without refitting. It is not a new full 30-city benchmark.

- Model: `random_forest`
- Reference run: `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\outputs\modeling\random_forest\frontier_allfolds_s5000_frontier-check_2026-04-11_173430`
- Training sample cap: `5000` rows per training city
- Prediction scope: `full_city` for selected held-out cities
- Smoothing radii: `150, 300, 600 m`
- Top-region threshold fraction: `0.10`
- Selected cities: Denver (city_id=6, fold=1), New Orleans (city_id=14, fold=3), Detroit (city_id=29, fold=4)

## Outputs

- `tables/representative_city_selection.csv`
- `tables/spatial_alignment_metrics_representative_cities.csv`
- `full_city_predictions/*.parquet`

## Metric Snapshot

| city_name | scale_label | spearman_surface_corr | top_region_overlap_fraction | observed_mass_captured | centroid_distance_m | median_nearest_region_distance_m | grid_reconstruction_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Denver | fine | 0.2336 | 0.1176 | 0.2053 | 8659.3787 | 305.9412 | ok |
| Denver | medium | 0.2540 | 0.1168 | 0.1996 | 9060.9421 | 536.6563 | ok |
| Denver | broad | 0.2781 | 0.1176 | 0.1921 | 9920.2181 | 844.8077 | ok |
| New Orleans | fine | 0.3355 | 0.1123 | 0.1959 | 4155.3625 | 276.5863 | ok |
| New Orleans | medium | 0.3590 | 0.1164 | 0.1954 | 4396.2673 | 400.2499 | ok |
| New Orleans | broad | 0.3932 | 0.1277 | 0.1896 | 4810.5015 | 697.7822 | ok |
| Detroit | fine | 0.3047 | 0.1142 | 0.1975 | 14215.4818 | 807.7747 | ok |
| Detroit | medium | 0.3331 | 0.1115 | 0.1875 | 14995.3263 | 1337.9462 | ok |
| Detroit | broad | 0.3391 | 0.1018 | 0.1681 | 16410.6610 | 2320.1078 | ok |

## Full-City Prediction Files

- `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\outputs\modeling\supplemental\spatial_alignment\full_city_predictions\denver_city06_random_forest_full_city_predictions.parquet`
- `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\outputs\modeling\supplemental\spatial_alignment\full_city_predictions\new_orleans_city14_random_forest_full_city_predictions.parquet`
- `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\outputs\modeling\supplemental\spatial_alignment\full_city_predictions\detroit_city29_random_forest_full_city_predictions.parquet`

## Map Files

- `tables/spatial_alignment_map_manifest.csv`
- `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\figures\modeling\supplemental\spatial_alignment\denver_city06_random_forest_medium_surface_alignment.png`
- `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\figures\modeling\supplemental\spatial_alignment\new_orleans_city14_random_forest_medium_surface_alignment.png`
- `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\figures\modeling\supplemental\spatial_alignment\detroit_city29_random_forest_medium_surface_alignment.png`
