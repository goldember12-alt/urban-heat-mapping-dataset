# Data Dictionary

## Study area outputs (`data_processed/study_areas/*.gpkg`)

- `geometry`: buffered city study area polygon in local projected CRS
- `city_id`: integer city identifier from `cities.csv`
- `city_name`: city name from `cities.csv`
- `state`: state abbreviation from `cities.csv`
- `climate_group`: climate group label from `cities.csv`
- `buffer_m`: buffer distance in meters used to create study area

## City grid outputs (`data_processed/city_grids/*.gpkg`)

- `cell_id`: sequential integer cell identifier within city grid
- `geometry`: grid cell polygon geometry at requested resolution (default 30 m)

Notes:
- Grid CRS matches the corresponding projected study area CRS.
- Grid contains only cells intersecting the study area polygon.
