from __future__ import annotations

CORE_FINAL_COLUMNS = [
    "city_id",
    "city_name",
    "climate_group",
    "cell_id",
    "centroid_lon",
    "centroid_lat",
    "impervious_pct",
    "land_cover_class",
    "elevation_m",
    "dist_to_water_m",
    "ndvi_median_may_aug",
    "lst_median_may_aug",
    "n_valid_ecostress_passes",
    "hotspot_10pct",
]

PHASE3A_ADDITIONAL_FINAL_COLUMNS = [
    "tree_cover_proxy_pct_270m",
    "vegetated_cover_proxy_pct_270m",
    "impervious_pct_mean_270m",
]

FINAL_COLUMNS = [*CORE_FINAL_COLUMNS, *PHASE3A_ADDITIONAL_FINAL_COLUMNS]
