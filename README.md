# Urban Heat Hotspot Screening Across Cities

This repository supports a STAT 5630 final project on urban heat hotspot screening. The project constructs and documents a 30-city analytic grid dataset from public geospatial and remote-sensing inputs, then uses that dataset to study whether non-thermal surface and environmental variables can identify local urban heat hotspots.

The report evaluates three related questions: same-city screening, exact-cell city-held-out transfer, and supplemental broad spatial-placement diagnostics. The main finding is cautious: same-city performance is stronger than city-held-out transfer, while broad spatial alignment is partial, heterogeneous, and not yet evidence of reliable operational hotspot mapping.

## What Is Included

- Python source code under `src/` for geospatial processing, feature assembly, dataset audit, fold creation, modeling, reporting, and supplemental diagnostics.
- Tests under `tests/`, including synthetic and focused regression tests for key workflow pieces.
- Report source, report-ready figures, report-ready tables, and the rendered draft PDF under `docs/report/`.
- Project documentation under `docs/`, including workflow, data dictionary, modeling methodology, and public documentation navigation.
- Lightweight configuration and metadata files such as `cities.csv`, `requirements.txt`, and tracked report artifacts where present.

## What Is Not Included

- Raw AppEEARS, NLCD, DEM, Census, and hydrography downloads may not be included in the Git repository.
- Large processed parquet, GeoPackage, raster, and full prediction artifacts may be untracked or available only in a local working copy.
- Full modeling run directories and prediction tables may be omitted unless they were intentionally curated as lightweight report artifacts.
- Local virtual environments, caches, credentials, `.env` files, and machine-specific paths are not part of the public repository.

## Reproducibility Scope

From the repository as shared, a reader can inspect the workflow code, tests, report source, and curated report artifacts. Fast tests or smoke checks can be run when the Python dependencies are installed and any required fixture or local data paths are available:

```bash
python -m pytest
```

Selected workflow stages are exposed as Python module entrypoints, for example:

```bash
python -m src.run_final_dataset_assembly
python -m src.make_model_folds --n-splits 5
python -m src.run_logistic_saga --sample-rows-per-city 5000
```

These examples are entrypoint examples, not a promise of one-command full reproduction. Full regeneration requires external data acquisition, AppEEARS access, local storage, and substantial compute. The report's benchmark results also depend on generated modeling artifacts that may not all be committed to GitHub.

## Data Sources

The workflow uses public source products summarized in the final report:

- U.S. Census urban-area polygons for study-area definition.
- National Land Cover Database (NLCD) land cover and imperviousness.
- USGS 3DEP elevation data.
- NHDPlus HR hydrography.
- MODIS/Terra NDVI via AppEEARS.
- ECOSTRESS land surface temperature via AppEEARS.

Public source products should be cited separately from this project repository when reused.

## Repository Map

- `src/`: project Python modules and CLI entrypoints.
- `tests/`: focused tests for data processing, acquisition helpers, modeling contracts, and reporting helpers.
- `docs/`: project documentation and documentation navigation.
- `docs/report/`: final report source, rendered draft PDF, report-ready figures, and report-ready tables.
- `outputs/`: generated report/modeling outputs where tracked; large or run-specific outputs may be absent.
- `figures/`: generated figures where tracked; report-ready figures are curated under `docs/report/figures/`.

For documentation navigation, start with [`docs/README.md`](docs/README.md).

## Citation And Report

The main report source is [`docs/report/stat5630_final_report_draft.md`](docs/report/stat5630_final_report_draft.md), with a rendered draft at [`docs/report/stat5630_final_report_draft.pdf`](docs/report/stat5630_final_report_draft.pdf) when tracked.

Repository URL: <https://github.com/goldember12-alt/urban-heat-mapping-dataset>

No project license is declared here; reuse permissions should not be assumed until a license is selected.
