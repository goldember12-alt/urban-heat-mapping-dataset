# Spatial Alignment Diagnostic Summary

This supplemental diagnostic uses the retained random-forest frontier contract, with full eligible held-out rows scored for spatial analysis across all selected held-out cities. Existing full-city prediction files can be reused for table and map generation without refitting. It is supplemental full-city spatial placement diagnostics, not a new canonical benchmark, and not a replacement for the retained sampled held-out-city PR AUC / recall benchmark.

- Model: `random_forest`
- Reference run: `C:\Users\golde\OneDrive - University of Virginia\STAT5630_FinalProject_DataProcessing\outputs\modeling\random_forest\frontier_allfolds_s5000_frontier-check_2026-04-11_173430`
- Training sample cap: `5000` rows per training city
- City selection: `all`
- Prediction scope: `full_city` for all selected held-out cities
- Smoothing radii: `150, 300, 600 m`
- Top-region threshold fraction: `0.10`
- Selected cities: Tucson (city_id=2, fold=0), Bakersfield (city_id=9, fold=0), Richmond (city_id=13, fold=0), Tampa (city_id=15, fold=0), Atlanta (city_id=18, fold=0), San Jose (city_id=24, fold=0), Denver (city_id=6, fold=1), Salt Lake City (city_id=7, fold=1), Fresno (city_id=8, fold=1), Portland (city_id=22, fold=1), Chicago (city_id=27, fold=1), Minneapolis (city_id=28, fold=1), Phoenix (city_id=1, fold=2), Reno (city_id=10, fold=2), Houston (city_id=11, fold=2), Columbia (city_id=12, fold=2), Jacksonville (city_id=17, fold=2), Seattle (city_id=21, fold=2), Las Vegas (city_id=3, fold=3), New Orleans (city_id=14, fold=3), Miami (city_id=16, fold=3), Charlotte (city_id=19, fold=3), San Francisco (city_id=23, fold=3), Boston (city_id=30, fold=3), Albuquerque (city_id=4, fold=4), El Paso (city_id=5, fold=4), Nashville (city_id=20, fold=4), Los Angeles (city_id=25, fold=4), San Diego (city_id=26, fold=4), Detroit (city_id=29, fold=4)

## Outputs

- `tables/all_city_selection.csv`
- `tables/spatial_alignment_metrics_all_cities.csv`
- `full_city_predictions/*.parquet`

## Metric Snapshot

| city_name | scale_label | spearman_surface_corr | top_region_overlap_fraction | observed_mass_captured | centroid_distance_m | median_nearest_region_distance_m | grid_reconstruction_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Tucson | fine | 0.2686 | 0.2002 | 0.3216 | 4233.2095 | 228.4732 | ok |
| Tucson | medium | 0.2693 | 0.2072 | 0.3192 | 4317.5255 | 480.0000 | ok |
| Tucson | broad | 0.2517 | 0.2180 | 0.3079 | 4226.9317 | 1074.1508 | ok |
| Bakersfield | fine | 0.2944 | 0.2475 | 0.3695 | 1725.7899 | 90.0000 | ok |
| Bakersfield | medium | 0.3060 | 0.2778 | 0.3687 | 1828.7313 | 84.8528 | ok |
| Bakersfield | broad | 0.2858 | 0.3115 | 0.3523 | 2184.0101 | 60.0000 | ok |
| Richmond | fine | 0.4275 | 0.2026 | 0.3172 | 11031.1187 | 150.0000 | ok |
| Richmond | medium | 0.4813 | 0.2141 | 0.3175 | 12298.0423 | 240.0000 | ok |
| Richmond | broad | 0.5210 | 0.2188 | 0.3027 | 14462.5683 | 371.0795 | ok |
| Tampa | fine | 0.4257 | 0.1400 | 0.2346 | 9464.0576 | 234.3075 | ok |
| Tampa | medium | 0.4435 | 0.1420 | 0.2296 | 9856.5029 | 360.0000 | ok |
| Tampa | broad | 0.4551 | 0.1397 | 0.2177 | 10543.8772 | 600.0000 | ok |
| Atlanta | fine | 0.2273 | 0.1325 | 0.2313 | 31496.5450 | 510.8816 | ok |
| Atlanta | medium | 0.2392 | 0.1235 | 0.2170 | 32710.0999 | 1020.4411 | ok |
| Atlanta | broad | 0.2424 | 0.1117 | 0.1969 | 34452.1371 | 1590.0000 | ok |
| San Jose | fine | 0.0864 | 0.0420 | 0.0785 | 13050.4790 | 496.5884 | ok |
| San Jose | medium | 0.0750 | 0.0306 | 0.0557 | 14462.4841 | 1001.2992 | ok |
| San Jose | broad | 0.0269 | 0.0111 | 0.0210 | 16370.9620 | 1818.1584 | ok |
| Denver | fine | 0.2336 | 0.1176 | 0.2053 | 8659.3787 | 305.9412 | ok |
| Denver | medium | 0.2540 | 0.1168 | 0.1996 | 9060.9421 | 536.6563 | ok |
| Denver | broad | 0.2781 | 0.1176 | 0.1921 | 9920.2181 | 844.8077 | ok |
| Salt Lake City | fine | 0.1776 | 0.0839 | 0.1537 | 3017.0307 | 391.1521 | ok |
| Salt Lake City | medium | 0.2099 | 0.0901 | 0.1632 | 2858.8570 | 523.9275 | ok |
| Salt Lake City | broad | 0.2370 | 0.0945 | 0.1704 | 2425.2173 | 684.1053 | ok |
| Fresno | fine | 0.4283 | 0.1648 | 0.2693 | 2280.8715 | 150.0000 | ok |
| Fresno | medium | 0.5075 | 0.1540 | 0.2445 | 2427.6647 | 318.9044 | ok |
| Fresno | broad | 0.5702 | 0.1523 | 0.2180 | 2567.2247 | 1026.1579 | ok |
| Portland | fine | 0.4926 | 0.2067 | 0.3233 | 5033.8092 | 90.0000 | ok |
| Portland | medium | 0.5792 | 0.2267 | 0.3351 | 5541.6697 | 120.0000 | ok |
| Portland | broad | 0.6438 | 0.2314 | 0.3182 | 6566.4119 | 180.0000 | ok |
| Chicago | fine | 0.4549 | 0.1802 | 0.2961 | 4993.0316 | 192.0937 | ok |
| Chicago | medium | 0.4975 | 0.1947 | 0.3045 | 5007.9788 | 271.6616 | ok |
| Chicago | broad | 0.5345 | 0.2155 | 0.3112 | 4979.6452 | 362.4914 | ok |
| Minneapolis | fine | 0.0336 | 0.0609 | 0.1160 | 25781.4565 | 713.0919 | ok |
| Minneapolis | medium | 0.0192 | 0.0553 | 0.1069 | 26891.3450 | 1251.7588 | ok |
| Minneapolis | broad | -0.0065 | 0.0453 | 0.0911 | 28261.4764 | 2365.4386 | ok |
| Phoenix | fine | 0.0967 | 0.0992 | 0.1732 | 10490.0780 | 1001.2992 | ok |
| Phoenix | medium | 0.0872 | 0.1003 | 0.1692 | 10972.0561 | 1518.1897 | ok |
| Phoenix | broad | 0.0805 | 0.0965 | 0.1547 | 11910.2042 | 1945.3791 | ok |
| Reno | fine | 0.1201 | 0.0625 | 0.1191 | 2586.8252 | 1326.1222 | ok |
| Reno | medium | 0.1452 | 0.0670 | 0.1258 | 2476.8688 | 1781.9091 | ok |
| Reno | broad | 0.1727 | 0.0622 | 0.1300 | 2313.6307 | 2177.0163 | ok |
| Houston | fine | 0.0989 | 0.0615 | 0.1157 | 10301.4017 | 416.7733 | ok |
| Houston | medium | 0.0853 | 0.0561 | 0.1066 | 11447.0926 | 713.0919 | ok |
| Houston | broad | 0.0478 | 0.0447 | 0.0907 | 13268.2240 | 1434.0502 | ok |
| Columbia | fine | 0.0768 | 0.0790 | 0.1366 | 7172.0379 | 591.6925 | ok |
| Columbia | medium | 0.0604 | 0.0823 | 0.1346 | 7624.1636 | 751.7978 | ok |
| Columbia | broad | 0.0326 | 0.0772 | 0.1271 | 8331.1382 | 1082.0813 | ok |
| Jacksonville | fine | 0.3933 | 0.1645 | 0.2640 | 4351.7260 | 212.1320 | ok |
| Jacksonville | medium | 0.4358 | 0.1814 | 0.2776 | 5178.0179 | 301.4963 | ok |
| Jacksonville | broad | 0.4600 | 0.2003 | 0.2831 | 6096.2948 | 458.9118 | ok |
| Seattle | fine | 0.4277 | 0.1763 | 0.2884 | 7573.6650 | 152.9706 | ok |
| Seattle | medium | 0.4804 | 0.1937 | 0.2968 | 7112.4570 | 216.3331 | ok |
| Seattle | broad | 0.5150 | 0.2047 | 0.2863 | 6758.2560 | 318.9044 | ok |
| Las Vegas | fine | 0.2577 | 0.2936 | 0.4383 | 1853.5747 | 67.0820 | ok |
| Las Vegas | medium | 0.2421 | 0.3136 | 0.4472 | 1661.5088 | 60.0000 | ok |
| Las Vegas | broad | 0.2278 | 0.3406 | 0.4547 | 1568.9810 | 0.0000 | ok |
| New Orleans | fine | 0.3355 | 0.1123 | 0.1959 | 4155.3625 | 276.5863 | ok |
| New Orleans | medium | 0.3590 | 0.1164 | 0.1954 | 4396.2673 | 400.2499 | ok |
| New Orleans | broad | 0.3932 | 0.1277 | 0.1896 | 4810.5015 | 697.7822 | ok |
| Miami | fine | 0.3108 | 0.0899 | 0.1631 | 25970.1934 | 270.0000 | ok |
| Miami | medium | 0.3598 | 0.0968 | 0.1710 | 27822.0628 | 394.5884 | ok |
| Miami | broad | 0.3942 | 0.1040 | 0.1780 | 29852.7577 | 570.0000 | ok |
| Charlotte | fine | 0.2330 | 0.0956 | 0.1725 | 4548.9532 | 792.5907 | ok |
| Charlotte | medium | 0.2423 | 0.0904 | 0.1648 | 4909.2639 | 1207.4767 | ok |
| Charlotte | broad | 0.2290 | 0.0833 | 0.1530 | 5707.5989 | 1813.9460 | ok |
| San Francisco | fine | 0.0607 | 0.0282 | 0.0562 | 33150.3460 | 550.7268 | ok |
| San Francisco | medium | 0.0499 | 0.0213 | 0.0438 | 34510.2756 | 1039.6634 | ok |
| San Francisco | broad | 0.0075 | 0.0114 | 0.0237 | 35708.4686 | 1782.1616 | ok |
| Boston | fine | 0.3621 | 0.1609 | 0.2661 | 17556.6778 | 161.5549 | ok |
| Boston | medium | 0.3814 | 0.1616 | 0.2567 | 18388.8125 | 300.0000 | ok |
| Boston | broad | 0.3783 | 0.1544 | 0.2357 | 19234.4237 | 648.9992 | ok |
| Albuquerque | fine | -0.0179 | 0.0409 | 0.0824 | 7506.2681 | 1548.4185 | ok |
| Albuquerque | medium | 0.0154 | 0.0402 | 0.0842 | 8032.1065 | 2459.8171 | ok |
| Albuquerque | broad | 0.0440 | 0.0398 | 0.0905 | 8847.8728 | 4095.8516 | ok |
| El Paso | fine | -0.0411 | 0.0206 | 0.0413 | 11311.6388 | 617.7378 | ok |
| El Paso | medium | -0.0778 | 0.0210 | 0.0415 | 11260.9604 | 915.8603 | ok |
| El Paso | broad | -0.1433 | 0.0260 | 0.0442 | 11366.4253 | 1471.2240 | ok |
| Nashville | fine | 0.6844 | 0.3908 | 0.5262 | 3464.8873 | 0.0000 | ok |
| Nashville | medium | 0.7476 | 0.4202 | 0.5114 | 3841.0947 | 0.0000 | ok |
| Nashville | broad | 0.7808 | 0.4504 | 0.4594 | 4387.0526 | 0.0000 | ok |
| Los Angeles | fine | 0.1621 | 0.0518 | 0.0960 | 20770.2500 | 780.5767 | ok |
| Los Angeles | medium | 0.1299 | 0.0524 | 0.0955 | 21073.9199 | 1880.4521 | ok |
| Los Angeles | broad | 0.0752 | 0.0547 | 0.0968 | 21304.6377 | 5860.3754 | ok |
| San Diego | fine | 0.1939 | 0.0915 | 0.1662 | 12403.5377 | 349.8571 | ok |
| San Diego | medium | 0.1808 | 0.0984 | 0.1716 | 13022.6283 | 615.5485 | ok |
| San Diego | broad | 0.1549 | 0.1020 | 0.1757 | 14330.3243 | 1008.0179 | ok |
| Detroit | fine | 0.3047 | 0.1142 | 0.1975 | 14215.4818 | 807.7747 | ok |
| Detroit | medium | 0.3331 | 0.1115 | 0.1875 | 14995.3263 | 1337.9462 | ok |
| Detroit | broad | 0.3391 | 0.1018 | 0.1681 | 16410.6610 | 2320.1078 | ok |

## Full-City Prediction Files

- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\tucson_city02_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\bakersfield_city09_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\richmond_city13_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\tampa_city15_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\atlanta_city18_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\san_jose_city24_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\denver_city06_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\salt_lake_city_city07_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\fresno_city08_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\portland_city22_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\chicago_city27_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\minneapolis_city28_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\phoenix_city01_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\reno_city10_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\houston_city11_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\columbia_city12_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\jacksonville_city17_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\seattle_city21_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\las_vegas_city03_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\new_orleans_city14_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\miami_city16_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\charlotte_city19_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\san_francisco_city23_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\boston_city30_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\albuquerque_city04_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\el_paso_city05_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\nashville_city20_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\los_angeles_city25_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\san_diego_city26_random_forest_full_city_predictions.parquet`
- `outputs\modeling\supplemental\spatial_alignment_all_cities\full_city_predictions\detroit_city29_random_forest_full_city_predictions.parquet`

## Map Files

Optional maps are supplemental full-city spatial placement diagnostics only; they do not replace the retained sampled held-out-city PR AUC / recall benchmark.

- `tables/spatial_alignment_map_manifest.csv`
- `figures\modeling\supplemental\spatial_alignment_all_cities\portland_city22_random_forest_medium_surface_alignment.png`
- `figures\modeling\supplemental\spatial_alignment_all_cities\las_vegas_city03_random_forest_medium_surface_alignment.png`
- `figures\modeling\supplemental\spatial_alignment_all_cities\san_francisco_city23_random_forest_medium_surface_alignment.png`
- `figures\modeling\supplemental\spatial_alignment_all_cities\nashville_city20_random_forest_medium_surface_alignment.png`
