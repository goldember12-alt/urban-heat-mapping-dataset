# Workflow

## Stage 1: City boundary and 30 m grid generation

This stage processes one city from `cities.csv` into two reusable geospatial artifacts:

- `data_processed/study_areas/*_study_area.gpkg`
- `data_processed/city_grids/*_grid_30m.gpkg`

Pipeline steps for a single city:

1. Select one city using `city_id` or `city_name`.
2. Query Census TIGERweb Urban Area polygon containing the city center point.
3. Reproject to local UTM and buffer by `buffer_m` (default: 2000 m).
4. Build a 30 m intersecting-cell grid from the buffered projected polygon.
5. Save study area and grid outputs.

## CLI usage

Run from project root:

```bash
python -m src.run_city_processing --city-name Phoenix
```

Alternate selector by ID:

```bash
python -m src.run_city_processing --city-id 1
```

Useful options:

- `--buffer-m 2000`
- `--resolution 30`
- `--timeout 60`
- `--no-save` (dry run)

## Notes

- Grid generation uses a rasterized mask + vectorized geometry construction to avoid slow full-grid overlays.
- Plotting full 30 m grids for large metro areas can still be expensive in notebooks.
