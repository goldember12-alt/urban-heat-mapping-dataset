from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.city_processing import city_output_paths, city_slug, city_stem, load_city_record
from src.config import (
    DATA_PROCESSING_FIGURES,
    DATA_PROCESSING_OUTPUTS,
    MODELING_FIGURES,
    MODELING_OUTPUTS,
    PROJECT_ROOT,
)
from src.feature_assembly import expected_city_feature_output_paths
from src.load_cities import load_cities

logger = logging.getLogger(__name__)

LAND_COVER_LABELS = {
    11: "Open Water",
    12: "Perennial Ice/Snow",
    21: "Developed, Open Space",
    22: "Developed, Low Intensity",
    23: "Developed, Medium Intensity",
    24: "Developed, High Intensity",
    31: "Barren Land",
    41: "Deciduous Forest",
    42: "Evergreen Forest",
    43: "Mixed Forest",
    52: "Shrub/Scrub",
    71: "Grassland/Herbaceous",
    81: "Pasture/Hay",
    82: "Cultivated Crops",
    90: "Woody Wetlands",
    95: "Emergent Herbaceous Wetlands",
}

KEY_VARIABLE_METADATA = [
    {
        "variable_name": "lst_median_may_aug",
        "meaning": "Median daytime land surface temperature across May-Aug ECOSTRESS observations.",
        "type_unit": "continuous; ECOSTRESS LST units from source raster",
        "why_it_matters": "Primary heat outcome for regression, classification, and hotspot analysis.",
    },
    {
        "variable_name": "hotspot_10pct",
        "meaning": "Indicator for cells at or above the city-specific 90th percentile of LST.",
        "type_unit": "binary flag",
        "why_it_matters": "Natural target for hotspot classification and spatial risk mapping.",
    },
    {
        "variable_name": "impervious_pct",
        "meaning": "NLCD impervious surface share for the 30 m cell.",
        "type_unit": "continuous; percent",
        "why_it_matters": "Core urban form exposure tied to heat retention and built intensity.",
    },
    {
        "variable_name": "ndvi_median_may_aug",
        "meaning": "Median warm-season greenness index from Landsat/AppEEARS NDVI layers.",
        "type_unit": "continuous; NDVI index",
        "why_it_matters": "Vegetation is a likely protective predictor against elevated surface temperatures.",
    },
    {
        "variable_name": "dist_to_water_m",
        "meaning": "Distance from the cell to the nearest mapped hydro feature.",
        "type_unit": "continuous; meters",
        "why_it_matters": "Captures proximity to possible local cooling influences and riparian structure.",
    },
    {
        "variable_name": "land_cover_class",
        "meaning": "NLCD land cover class code for the cell.",
        "type_unit": "categorical; NLCD class",
        "why_it_matters": "Summarizes surface type and helps separate developed, barren, and vegetated cells.",
    },
    {
        "variable_name": "n_valid_ecostress_passes",
        "meaning": "Count of valid ECOSTRESS observations contributing to the LST median.",
        "type_unit": "count",
        "why_it_matters": "Important quality-control covariate because low temporal coverage can weaken inference.",
    },
]

NUMERIC_SUMMARY_COLUMNS = [
    "impervious_pct",
    "ndvi_median_may_aug",
    "lst_median_may_aug",
    "dist_to_water_m",
    "elevation_m",
    "n_valid_ecostress_passes",
]
CORRELATION_COLUMNS = [
    "lst_median_may_aug",
    "impervious_pct",
    "ndvi_median_may_aug",
    "dist_to_water_m",
    "elevation_m",
    "n_valid_ecostress_passes",
]
MISSINGNESS_COLUMNS = [
    "impervious_pct",
    "land_cover_class",
    "elevation_m",
    "dist_to_water_m",
    "ndvi_median_may_aug",
    "lst_median_may_aug",
    "n_valid_ecostress_passes",
    "hotspot_10pct",
]


@dataclass(frozen=True)
class DatasetChoice:
    dataset_path: Path
    dataset_label: str
    dataset_reason: str
    candidate_status: pd.DataFrame


@dataclass(frozen=True)
class SummaryPaths:
    markdown_path: Path
    output_dir: Path
    tables_dir: Path
    figures_dir: Path


@dataclass(frozen=True)
class CityReportResult:
    city: pd.Series
    paths: SummaryPaths
    dataset_choice: DatasetChoice
    row_count: int


@dataclass(frozen=True)
class BatchReportResult:
    summary: pd.DataFrame
    summary_path: Path


def _default_markdown_path(city: pd.Series, outputs_root: Path = DATA_PROCESSING_OUTPUTS) -> Path:
    stem = city_stem(city)
    slug = city_slug(str(city["city_name"]))
    return outputs_root / stem / f"{slug}_data_summary.md"


def resolve_city_report_paths(
    city: pd.Series,
    markdown_path: Path | None = None,
    tables_dir: Path | None = None,
    figures_dir: Path | None = None,
    outputs_root: Path = DATA_PROCESSING_OUTPUTS,
    figures_root: Path = DATA_PROCESSING_FIGURES,
) -> SummaryPaths:
    """Return the canonical markdown, table, and figure paths for one city report."""
    resolved_markdown = (markdown_path or _default_markdown_path(city, outputs_root=outputs_root)).resolve()
    stem = city_stem(city)
    resolved_tables = (tables_dir or resolved_markdown.parent / "tables").resolve()
    resolved_figures = (figures_dir or (figures_root / stem)).resolve()
    return SummaryPaths(
        markdown_path=resolved_markdown,
        output_dir=resolved_markdown.parent,
        tables_dir=resolved_tables,
        figures_dir=resolved_figures,
    )


def _candidate_dataset_paths(city: pd.Series, project_root: Path) -> list[tuple[str, Path, str]]:
    processed_dir = project_root / "data_processed"
    feature_paths = expected_city_feature_output_paths(
        city=city,
        city_features_dir=processed_dir / "city_features",
        intermediate_dir=processed_dir / "intermediate",
    )
    return [
        (
            "per_city_feature_output",
            feature_paths.city_features_parquet_path,
            "Canonical per-city filtered output intended for downstream modeling.",
        ),
        (
            "intermediate_filtered_output",
            feature_paths.intermediate_filtered_path,
            "Filtered intermediate table with the same post-rule rows but not the primary published output.",
        ),
        (
            "merged_final_dataset",
            project_root / "data_processed" / "final" / "final_dataset.parquet",
            "Merged cross-city dataset that may contain this city's rows but is broader than the city-only deliverable.",
        ),
    ]


def choose_city_dataset(city: pd.Series, project_root: Path = PROJECT_ROOT) -> DatasetChoice:
    """Choose the most relevant city-specific analysis dataset from materialized outputs."""
    city_id = int(city["city_id"])
    records: list[dict[str, object]] = []
    chosen: tuple[str, Path, str] | None = None

    for label, path, reason in _candidate_dataset_paths(city=city, project_root=project_root):
        exists = path.exists()
        records.append(
            {
                "candidate": label,
                "path": str(path),
                "exists": exists,
                "reason": reason,
            }
        )
        if chosen is None and exists:
            if label == "merged_final_dataset":
                try:
                    final_df = pd.read_parquet(path, columns=["city_id"])
                    if not (final_df["city_id"] == city_id).any():
                        continue
                except Exception:
                    continue
            chosen = (label, path, reason)

    if chosen is None:
        candidate_table = pd.DataFrame(records)
        raise FileNotFoundError(
            f"No analysis dataset was found for city_id={city_id} city_name={city['city_name']}. Checked:\n"
            f"{candidate_table[['candidate', 'path']].to_string(index=False)}"
        )

    label, path, reason = chosen
    return DatasetChoice(
        dataset_path=path,
        dataset_label=label,
        dataset_reason=reason,
        candidate_status=pd.DataFrame(records),
    )


def _load_analysis_table(choice: DatasetChoice, city: pd.Series) -> pd.DataFrame:
    df = pd.read_parquet(choice.dataset_path)
    if choice.dataset_label == "merged_final_dataset":
        df = df[df["city_id"] == int(city["city_id"])].copy()
    if df.empty:
        raise ValueError(f"Chosen analysis dataset is empty: {choice.dataset_path}")
    return df


def _load_feature_geometry(city: pd.Series, project_root: Path = PROJECT_ROOT) -> gpd.GeoDataFrame:
    processed_dir = project_root / "data_processed"
    geometry_path = expected_city_feature_output_paths(
        city=city,
        city_features_dir=processed_dir / "city_features",
        intermediate_dir=processed_dir / "intermediate",
    ).city_features_gpkg_path
    if not geometry_path.exists():
        raise FileNotFoundError(f"City geometry file not found: {geometry_path}")
    gdf = gpd.read_file(geometry_path)
    if gdf.empty:
        raise ValueError(f"City geometry file is empty: {geometry_path}")
    return gdf


def _load_study_area(city: pd.Series, project_root: Path = PROJECT_ROOT) -> gpd.GeoDataFrame:
    processed_dir = project_root / "data_processed"
    study_area_path, _ = city_output_paths(
        city=city,
        study_areas_dir=processed_dir / "study_areas",
        city_grids_dir=processed_dir / "city_grids",
    )
    if not study_area_path.exists():
        raise FileNotFoundError(f"Study-area file not found: {study_area_path}")
    return gpd.read_file(study_area_path)


def _load_preprocessing_inputs(
    city: pd.Series,
    project_root: Path = PROJECT_ROOT,
) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    processed_dir = project_root / "data_processed"
    feature_paths = expected_city_feature_output_paths(
        city=city,
        city_features_dir=processed_dir / "city_features",
        intermediate_dir=processed_dir / "intermediate",
    )
    unfiltered = pd.read_parquet(feature_paths.intermediate_unfiltered_path) if feature_paths.intermediate_unfiltered_path.exists() else None
    filtered = pd.read_parquet(feature_paths.intermediate_filtered_path) if feature_paths.intermediate_filtered_path.exists() else None
    return unfiltered, filtered


def compute_preprocessing_audit(
    unfiltered_df: pd.DataFrame | None,
    filtered_df: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize row filtering between unfiltered and filtered city tables."""
    filtered_rows = len(filtered_df)
    if unfiltered_df is None or unfiltered_df.empty:
        return pd.DataFrame(
            [
                {"stage": "unfiltered_input_rows", "n_rows": np.nan, "share_of_unfiltered_pct": np.nan},
                {"stage": "final_filtered_rows", "n_rows": filtered_rows, "share_of_unfiltered_pct": np.nan},
            ]
        )

    water_dropped = int((unfiltered_df.get("land_cover_class") == 11).fillna(False).sum())
    if "lst_median_may_aug" in unfiltered_df.columns and unfiltered_df["lst_median_may_aug"].notna().any():
        low_pass_mask = unfiltered_df["n_valid_ecostress_passes"].fillna(0).astype("Int64") < 3
        low_pass_mask &= unfiltered_df["land_cover_class"].ne(11).fillna(True)
        low_pass_dropped = int(low_pass_mask.sum())
    else:
        low_pass_dropped = 0

    return pd.DataFrame(
        [
            {"stage": "unfiltered_input_rows", "n_rows": len(unfiltered_df), "share_of_unfiltered_pct": 100.0},
            {
                "stage": "dropped_open_water_rows",
                "n_rows": water_dropped,
                "share_of_unfiltered_pct": 100.0 * water_dropped / len(unfiltered_df),
            },
            {
                "stage": "dropped_lt3_ecostress_pass_rows",
                "n_rows": low_pass_dropped,
                "share_of_unfiltered_pct": 100.0 * low_pass_dropped / len(unfiltered_df),
            },
            {
                "stage": "final_filtered_rows",
                "n_rows": filtered_rows,
                "share_of_unfiltered_pct": 100.0 * filtered_rows / len(unfiltered_df),
            },
        ]
    )


def _label_land_cover(value: object) -> str:
    if pd.isna(value):
        return "Missing"
    code = int(value)
    return LAND_COVER_LABELS.get(code, f"Class {code}")


def compute_numeric_summary(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for column in columns:
        if column not in df.columns:
            continue
        series = pd.to_numeric(df[column], errors="coerce")
        valid = series.dropna()
        if valid.empty:
            continue
        rows.append(
            {
                "variable": column,
                "n_non_missing": int(valid.shape[0]),
                "missing_pct": 100.0 * (1.0 - valid.shape[0] / len(df)),
                "mean": float(valid.mean()),
                "median": float(valid.median()),
                "std": float(valid.std(ddof=1)) if len(valid) > 1 else 0.0,
                "min": float(valid.min()),
                "p10": float(valid.quantile(0.10)),
                "p90": float(valid.quantile(0.90)),
                "max": float(valid.max()),
                "skew": float(valid.skew()) if len(valid) > 2 else 0.0,
            }
        )
    return pd.DataFrame(rows)


def compute_missingness_summary(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for column in columns:
        if column not in df.columns:
            continue
        missing_n = int(df[column].isna().sum())
        rows.append(
            {
                "variable": column,
                "missing_n": missing_n,
                "missing_pct": 100.0 * missing_n / len(df),
                "non_missing_n": int(len(df) - missing_n),
            }
        )
    return pd.DataFrame(rows).sort_values(["missing_pct", "variable"], ascending=[False, True]).reset_index(drop=True)


def compute_land_cover_summary(df: pd.DataFrame) -> pd.DataFrame:
    counts = (
        df["land_cover_class"]
        .dropna()
        .astype("Int64")
        .value_counts(dropna=False)
        .rename_axis("land_cover_class")
        .reset_index(name="n_rows")
    )
    counts["land_cover_label"] = counts["land_cover_class"].map(_label_land_cover)
    counts["share_pct"] = 100.0 * counts["n_rows"] / counts["n_rows"].sum()
    return counts


def compute_hotspot_summary(df: pd.DataFrame) -> pd.DataFrame:
    hotspot = df["hotspot_10pct"].astype("boolean")
    return pd.DataFrame(
        [
            {"category": "hotspot", "n_rows": int((hotspot == True).sum()), "share_pct": 100.0 * float((hotspot == True).mean())},
            {
                "category": "non_hotspot",
                "n_rows": int((hotspot == False).sum()),
                "share_pct": 100.0 * float((hotspot == False).mean()),
            },
            {"category": "missing", "n_rows": int(hotspot.isna().sum()), "share_pct": 100.0 * hotspot.isna().mean()},
        ]
    )


def compute_correlation_matrix(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    available = [column for column in columns if column in df.columns]
    numeric = df[available].apply(pd.to_numeric, errors="coerce")
    usable = [column for column in numeric.columns if numeric[column].notna().sum() > 1]
    return numeric[usable].corr()


def compute_quadrant_hotspot_summary(df: pd.DataFrame) -> pd.DataFrame:
    if not {"centroid_lon", "centroid_lat", "hotspot_10pct"}.issubset(df.columns):
        return pd.DataFrame()
    lon_mid = float(df["centroid_lon"].median())
    lat_mid = float(df["centroid_lat"].median())
    lon_side = np.where(df["centroid_lon"] <= lon_mid, "west", "east")
    lat_side = np.where(df["centroid_lat"] <= lat_mid, "south", "north")
    quadrant = pd.Series(lat_side, index=df.index) + "_" + pd.Series(lon_side, index=df.index)
    hotspot = df["hotspot_10pct"].astype("boolean")
    summary = (
        pd.DataFrame({"quadrant": quadrant, "hotspot_10pct": hotspot})
        .groupby("quadrant", dropna=False)["hotspot_10pct"]
        .agg(
            n_cells="size",
            hotspot_n=lambda x: int((x == True).sum()),
            hotspot_share_pct=lambda x: 100.0 * float((x == True).mean()),
        )
        .reset_index()
        .sort_values("quadrant")
        .reset_index(drop=True)
    )
    return summary


def _format_number(value: object, decimals: int = 2) -> str:
    if pd.isna(value):
        return "NA"
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}"
    if isinstance(value, (float, np.floating)):
        return f"{float(value):,.{decimals}f}"
    return str(value)


def _markdown_table(df: pd.DataFrame, decimals: int = 2) -> str:
    display = df.copy()
    for column in display.columns:
        if pd.api.types.is_numeric_dtype(display[column]):
            if pd.api.types.is_integer_dtype(display[column].dtype):
                display[column] = display[column].map(lambda value: _format_number(value, decimals=0))
            else:
                display[column] = display[column].map(lambda value: _format_number(value, decimals=decimals))
        else:
            display[column] = display[column].astype(str)
    header = "| " + " | ".join(display.columns) + " |"
    divider = "| " + " | ".join(["---"] * len(display.columns)) + " |"
    rows = ["| " + " | ".join(row) + " |" for row in display.astype(str).values.tolist()]
    return "\n".join([header, divider, *rows])


def _write_table_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def _figure_path(paths: SummaryPaths, city: pd.Series, suffix: str) -> Path:
    return paths.figures_dir / f"{city_slug(str(city['city_name']))}_{suffix}.png"


def _save_distribution_figure(df: pd.DataFrame, output_path: Path, city_name: str) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    plot_specs = [
        ("lst_median_may_aug", "LST", axes[0, 0], None),
        ("impervious_pct", "Impervious (%)", axes[0, 1], None),
        ("ndvi_median_may_aug", "NDVI", axes[1, 0], None),
        ("dist_to_water_m", "Distance to water (m, log1p)", axes[1, 1], np.log1p),
    ]
    for column, title, ax, transform in plot_specs:
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        values = transform(series) if transform is not None else series
        ax.hist(values, bins=40, color="#4C6A92", edgecolor="white")
        ax.set_title(title)
        ax.set_ylabel("Cells")
        ax.grid(alpha=0.2)
    axes[0, 0].set_xlabel("Median LST")
    axes[0, 1].set_xlabel("Impervious surface share")
    axes[1, 0].set_xlabel("Median NDVI")
    axes[1, 1].set_xlabel("log(1 + meters)")
    fig.suptitle(f"{city_name} key predictor and outcome distributions", fontsize=14)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def _save_land_cover_figure(land_cover_df: pd.DataFrame, output_path: Path, city_name: str) -> None:
    top = land_cover_df.head(8).sort_values("share_pct")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(top["land_cover_label"], top["share_pct"], color="#C56E3E")
    ax.set_xlabel(f"Share of {city_name} cells (%)")
    ax.set_title(f"Dominant {city_name} land-cover classes")
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def _save_correlation_figure(corr_df: pd.DataFrame, output_path: Path, city_name: str) -> None:
    fig, ax = plt.subplots(figsize=(7, 6))
    image = ax.imshow(corr_df.values, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr_df.columns)))
    ax.set_yticks(range(len(corr_df.index)))
    ax.set_xticklabels(corr_df.columns, rotation=45, ha="right")
    ax.set_yticklabels(corr_df.index)
    for i in range(len(corr_df.index)):
        for j in range(len(corr_df.columns)):
            value = corr_df.iloc[i, j]
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=8, color="black")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Pearson correlation")
    ax.set_title(f"Correlation among key {city_name} variables")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def _save_hotspot_map(gdf: gpd.GeoDataFrame, study_area: gpd.GeoDataFrame, output_path: Path, city_name: str) -> None:
    plot_gdf = gdf.copy()
    plot_gdf["hotspot_10pct"] = plot_gdf["hotspot_10pct"].astype("boolean")
    centroids = plot_gdf.geometry.centroid
    background = gpd.GeoDataFrame(
        plot_gdf.loc[plot_gdf["hotspot_10pct"] != True, ["hotspot_10pct"]].copy(),
        geometry=centroids[plot_gdf["hotspot_10pct"] != True],
        crs=plot_gdf.crs,
    )
    hotspots = gpd.GeoDataFrame(
        plot_gdf.loc[plot_gdf["hotspot_10pct"] == True, ["hotspot_10pct"]].copy(),
        geometry=centroids[plot_gdf["hotspot_10pct"] == True],
        crs=plot_gdf.crs,
    )
    if len(background) > 80000:
        background = background.sample(n=80000, random_state=0)
    if len(hotspots) > 80000:
        hotspots = hotspots.sample(n=80000, random_state=0)

    fig, ax = plt.subplots(figsize=(8, 8))
    study_area.boundary.plot(ax=ax, color="black", linewidth=0.8)
    background.plot(ax=ax, color="#CFCFCF", markersize=1, alpha=0.35)
    hotspots.plot(ax=ax, color="#D64541", markersize=1.8, alpha=0.7)
    ax.set_title(f"{city_name} hotspot cells (top 10% LST)")
    ax.set_axis_off()
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def _strongest_outcome_correlation(corr_df: pd.DataFrame) -> tuple[str, float] | None:
    if "lst_median_may_aug" not in corr_df.columns:
        return None
    series = corr_df["lst_median_may_aug"].drop(labels=["lst_median_may_aug"], errors="ignore").dropna()
    if series.empty:
        return None
    variable = series.abs().idxmax()
    return variable, float(series.loc[variable])


def _largest_skew(numeric_summary_df: pd.DataFrame) -> tuple[str, float] | None:
    if numeric_summary_df.empty:
        return None
    idx = numeric_summary_df["skew"].abs().idxmax()
    row = numeric_summary_df.loc[idx]
    return str(row["variable"]), float(row["skew"])


def build_notable_patterns(
    city_name: str,
    df: pd.DataFrame,
    preprocessing_df: pd.DataFrame,
    missingness_df: pd.DataFrame,
    numeric_summary_df: pd.DataFrame,
    land_cover_df: pd.DataFrame,
    corr_df: pd.DataFrame,
    quadrant_df: pd.DataFrame,
) -> list[str]:
    notes: list[str] = []

    max_missing = float(missingness_df["missing_pct"].max()) if not missingness_df.empty else np.nan
    if pd.notna(max_missing):
        if max_missing == 0:
            notes.append(f"None of the key modeling variables have missing values in the filtered {city_name} table.")
        else:
            worst = missingness_df.iloc[0]
            if max_missing < 0.01:
                notes.append(
                    f"Missingness is negligible: only {int(worst['missing_n']):,} `{worst['variable']}` values are missing ({worst['missing_pct']:.4f}%)."
                )
            else:
                notes.append(
                    f"Missingness is limited overall; the highest missing share is `{worst['variable']}` at {worst['missing_pct']:.2f}%."
                )

    hotspot_share = float((df["hotspot_10pct"].astype("boolean") == True).mean()) * 100.0
    notes.append(
        f"`hotspot_10pct` is intentionally imbalanced at {hotspot_share:.2f}% positives because it marks the {city_name}-specific top decile of LST."
    )

    if not land_cover_df.empty:
        top_land = land_cover_df.iloc[0]
        notes.append(
            f"Land cover is concentrated in {top_land['land_cover_label']} cells, which make up {top_land['share_pct']:.1f}% of the filtered {city_name} dataset."
        )

    strongest_corr = _strongest_outcome_correlation(corr_df)
    if strongest_corr is not None:
        variable, corr_value = strongest_corr
        direction = "positive" if corr_value >= 0 else "negative"
        notes.append(
            f"The strongest linear relationship with LST among the key numeric variables is {direction} for `{variable}` (r = {corr_value:.2f})."
        )

    if not quadrant_df.empty:
        spread = quadrant_df["hotspot_share_pct"].max() - quadrant_df["hotspot_share_pct"].min()
        if spread >= 2.0:
            notes.append(
                f"Hotspot prevalence varies by {city_name} quadrant from {quadrant_df['hotspot_share_pct'].min():.1f}% to {quadrant_df['hotspot_share_pct'].max():.1f}%, which is consistent with non-random spatial concentration."
            )

    skew_info = _largest_skew(numeric_summary_df)
    if skew_info is not None:
        variable, skew_value = skew_info
        if abs(skew_value) >= 1.0:
            notes.append(
                f"`{variable}` is strongly skewed (skew = {skew_value:.2f}), so transformations or robust summaries may be useful in later modeling."
            )

    if not preprocessing_df.empty and preprocessing_df["stage"].eq("unfiltered_input_rows").any() and len(notes) < 6:
        unfiltered_n = preprocessing_df.loc[preprocessing_df["stage"] == "unfiltered_input_rows", "n_rows"].iloc[0]
        final_n = preprocessing_df.loc[preprocessing_df["stage"] == "final_filtered_rows", "n_rows"].iloc[0]
        if pd.notna(unfiltered_n) and pd.notna(final_n):
            notes.append(
                f"The published {city_name} table retains {int(final_n):,} of {int(unfiltered_n):,} initially assembled cells after rule-based filtering."
            )

    return notes[:6]


def _overview_table(
    city_name: str,
    df: pd.DataFrame,
    gdf: gpd.GeoDataFrame,
    study_area: gpd.GeoDataFrame,
    choice: DatasetChoice,
) -> pd.DataFrame:
    bounds = gdf.total_bounds
    extent_text = f"[{bounds[0]:.0f}, {bounds[1]:.0f}, {bounds[2]:.0f}, {bounds[3]:.0f}]"
    return pd.DataFrame(
        [
            {"metric": f"Primary {city_name} analysis file", "value": str(choice.dataset_path.relative_to(PROJECT_ROOT))},
            {"metric": "Dataset choice rationale", "value": choice.dataset_reason},
            {"metric": "Observations", "value": len(df)},
            {"metric": "Variables", "value": df.shape[1]},
            {"metric": "Unit of analysis", "value": f"One filtered 30 m grid cell in the buffered {city_name} study area"},
            {"metric": "Geometry / CRS", "value": f"Cell polygons stored in {gdf.crs}; centroids stored as WGS84 lon/lat"},
            {"metric": "Projected spatial extent", "value": extent_text},
            {
                "metric": "Study-area buffer",
                "value": f"{float(study_area['buffer_m'].iloc[0]):,.0f} m around the Census urban area",
            },
        ]
    )


def _key_variable_table() -> pd.DataFrame:
    return pd.DataFrame(KEY_VARIABLE_METADATA)


def _overview_paragraph(city_name: str, choice: DatasetChoice, df: pd.DataFrame) -> str:
    climate_group = str(df["climate_group"].iloc[0])
    return (
        f"The {city_name} summary uses `{choice.dataset_path.relative_to(PROJECT_ROOT)}`, the canonical {city_name}-only "
        f"analysis-ready feature table. Each observation represents one filtered 30 m grid cell inside the buffered "
        f"{city_name} study area, with built-form, vegetation, elevation, hydrologic proximity, and warm-season "
        f"surface-temperature attributes aligned to the same cell geometry. The table is intended for downstream urban "
        f"heat modeling in a {climate_group} city, including both continuous LST analysis and binary hotspot prediction."
    )


def _section_image(markdown_path: Path, image_path: Path, alt_text: str) -> str:
    relative = Path(os.path.relpath(image_path, start=markdown_path.parent))
    return f"![{alt_text}]({relative.as_posix()})"


def _write_markdown(
    city: pd.Series,
    paths: SummaryPaths,
    overview_paragraph: str,
    overview_df: pd.DataFrame,
    key_variable_df: pd.DataFrame,
    preprocessing_df: pd.DataFrame,
    numeric_summary_df: pd.DataFrame,
    land_cover_df: pd.DataFrame,
    missingness_df: pd.DataFrame,
    corr_df: pd.DataFrame,
    notes: list[str],
) -> None:
    city_name = str(city["city_name"])
    distribution_path = _figure_path(paths, city, "key_distributions")
    land_cover_path = _figure_path(paths, city, "land_cover_composition")
    correlation_path = _figure_path(paths, city, "key_correlations")
    hotspot_map_path = _figure_path(paths, city, "hotspot_map")
    content = [
        f"# {city_name} Summary of Data",
        "",
        overview_paragraph,
        "",
        "## Overview",
        "",
        _markdown_table(overview_df, decimals=2),
        "",
        "## Key Variables",
        "",
        _markdown_table(key_variable_df, decimals=2),
        "",
        "## Targeted Descriptive Results",
        "",
        "### Preprocessing audit",
        "",
        _markdown_table(preprocessing_df, decimals=2),
        "",
        "### Key numeric summary",
        "",
        _markdown_table(
            numeric_summary_df[
                ["variable", "n_non_missing", "missing_pct", "mean", "median", "std", "p10", "p90", "skew"]
            ],
            decimals=2,
        ),
        "",
        "### Land-cover composition",
        "",
        _markdown_table(land_cover_df.head(8)[["land_cover_class", "land_cover_label", "n_rows", "share_pct"]], decimals=2),
        "",
        "### Missingness for key variables",
        "",
        _markdown_table(missingness_df, decimals=4),
        "",
        "### Correlation matrix",
        "",
        _markdown_table(corr_df.reset_index().rename(columns={"index": "variable"}), decimals=2),
        "",
        "## Figures",
        "",
        _section_image(paths.markdown_path, distribution_path, f"{city_name} key distributions"),
        "",
        _section_image(paths.markdown_path, land_cover_path, f"{city_name} land-cover composition"),
        "",
        _section_image(paths.markdown_path, correlation_path, f"{city_name} key correlations"),
        "",
        _section_image(paths.markdown_path, hotspot_map_path, f"{city_name} hotspot map"),
        "",
        "## Notable Patterns",
        "",
        *[f"- {note}" for note in notes],
        "",
        "## Output Notes",
        "",
        f"- The {city_name}-only per-city feature parquet was chosen over the merged final dataset when it was available because it is the direct analysis-ready output for this city and already reflects the row-drop rules used by the pipeline.",
        "- Supporting CSV tables and PNG figures for this summary were generated deterministically by the companion CLI.",
        "- Markdown and tables live under `outputs/data_processing/`, while figures live under `figures/data_processing/`; `outputs/modeling/` and `figures/modeling/` are reserved for later ML/evaluation artifacts.",
    ]
    paths.markdown_path.parent.mkdir(parents=True, exist_ok=True)
    paths.markdown_path.write_text("\n".join(content) + "\n", encoding="utf-8")


def generate_city_data_report(
    city_name: str | None = None,
    city_id: int | None = None,
    markdown_path: Path | None = None,
    tables_dir: Path | None = None,
    figures_dir: Path | None = None,
    project_root: Path = PROJECT_ROOT,
    outputs_root: Path = DATA_PROCESSING_OUTPUTS,
    figures_root: Path = DATA_PROCESSING_FIGURES,
) -> CityReportResult:
    """Build one city's markdown summary, supporting tables, and figures."""
    city = load_city_record(city_name=city_name, city_id=city_id)
    city_name_value = str(city["city_name"])
    paths = resolve_city_report_paths(
        city=city,
        markdown_path=markdown_path,
        tables_dir=tables_dir,
        figures_dir=figures_dir,
        outputs_root=outputs_root,
        figures_root=figures_root,
    )

    paths.output_dir.mkdir(parents=True, exist_ok=True)
    paths.tables_dir.mkdir(parents=True, exist_ok=True)
    paths.figures_dir.mkdir(parents=True, exist_ok=True)
    MODELING_OUTPUTS.mkdir(parents=True, exist_ok=True)
    MODELING_FIGURES.mkdir(parents=True, exist_ok=True)

    choice = choose_city_dataset(city=city, project_root=project_root)
    df = _load_analysis_table(choice, city=city)
    gdf = _load_feature_geometry(city=city, project_root=project_root)
    study_area = _load_study_area(city=city, project_root=project_root)
    unfiltered_df, intermediate_filtered_df = _load_preprocessing_inputs(city=city, project_root=project_root)

    preprocessing_df = compute_preprocessing_audit(unfiltered_df=unfiltered_df, filtered_df=df)
    numeric_summary_df = compute_numeric_summary(df=df, columns=NUMERIC_SUMMARY_COLUMNS)
    missingness_df = compute_missingness_summary(df=df, columns=MISSINGNESS_COLUMNS)
    land_cover_df = compute_land_cover_summary(df=df)
    hotspot_df = compute_hotspot_summary(df=df)
    corr_df = compute_correlation_matrix(df=df, columns=CORRELATION_COLUMNS)
    quadrant_df = compute_quadrant_hotspot_summary(df=df)
    overview_df = _overview_table(city_name=city_name_value, df=df, gdf=gdf, study_area=study_area, choice=choice)
    key_variable_df = _key_variable_table()

    notes = build_notable_patterns(
        city_name=city_name_value,
        df=df,
        preprocessing_df=preprocessing_df,
        missingness_df=missingness_df,
        numeric_summary_df=numeric_summary_df,
        land_cover_df=land_cover_df,
        corr_df=corr_df,
        quadrant_df=quadrant_df,
    )

    _write_table_csv(choice.candidate_status, paths.tables_dir / "dataset_candidates.csv")
    _write_table_csv(overview_df, paths.tables_dir / "overview.csv")
    _write_table_csv(key_variable_df, paths.tables_dir / "key_variables.csv")
    _write_table_csv(preprocessing_df, paths.tables_dir / "preprocessing_audit.csv")
    _write_table_csv(numeric_summary_df, paths.tables_dir / "key_numeric_summary.csv")
    _write_table_csv(land_cover_df, paths.tables_dir / "land_cover_composition.csv")
    _write_table_csv(missingness_df, paths.tables_dir / "missingness_summary.csv")
    _write_table_csv(hotspot_df, paths.tables_dir / "hotspot_summary.csv")
    _write_table_csv(corr_df.reset_index(), paths.tables_dir / "correlation_matrix.csv")
    _write_table_csv(quadrant_df, paths.tables_dir / "hotspot_quadrants.csv")
    if intermediate_filtered_df is not None:
        consistency_df = pd.DataFrame(
            [
                {
                    "comparison": "city_features_vs_intermediate_filtered_rows",
                    "matches": len(df) == len(intermediate_filtered_df),
                    "city_features_rows": len(df),
                    "intermediate_filtered_rows": len(intermediate_filtered_df),
                }
            ]
        )
        _write_table_csv(consistency_df, paths.tables_dir / "dataset_consistency_check.csv")

    _save_distribution_figure(df=df, output_path=_figure_path(paths, city, "key_distributions"), city_name=city_name_value)
    _save_land_cover_figure(
        land_cover_df=land_cover_df,
        output_path=_figure_path(paths, city, "land_cover_composition"),
        city_name=city_name_value,
    )
    _save_correlation_figure(
        corr_df=corr_df,
        output_path=_figure_path(paths, city, "key_correlations"),
        city_name=city_name_value,
    )
    _save_hotspot_map(
        gdf=gdf,
        study_area=study_area,
        output_path=_figure_path(paths, city, "hotspot_map"),
        city_name=city_name_value,
    )

    _write_markdown(
        city=city,
        paths=paths,
        overview_paragraph=_overview_paragraph(city_name=city_name_value, choice=choice, df=df),
        overview_df=overview_df,
        key_variable_df=key_variable_df,
        preprocessing_df=preprocessing_df,
        numeric_summary_df=numeric_summary_df,
        land_cover_df=land_cover_df,
        missingness_df=missingness_df,
        corr_df=corr_df,
        notes=notes,
    )

    logger.info("Wrote %s markdown summary to %s", city_name_value, paths.markdown_path)
    logger.info("Wrote %s summary tables to %s", city_name_value, paths.tables_dir)
    logger.info("Wrote %s summary figures to %s", city_name_value, paths.figures_dir)
    return CityReportResult(city=city, paths=paths, dataset_choice=choice, row_count=int(len(df)))


def generate_all_city_data_reports(
    city_ids: list[int] | None = None,
    continue_on_error: bool = True,
    outputs_root: Path = DATA_PROCESSING_OUTPUTS,
    figures_root: Path = DATA_PROCESSING_FIGURES,
) -> BatchReportResult:
    """Generate data-processing reports for all configured cities or a selected subset."""
    outputs_root.mkdir(parents=True, exist_ok=True)
    figures_root.mkdir(parents=True, exist_ok=True)
    MODELING_OUTPUTS.mkdir(parents=True, exist_ok=True)
    MODELING_FIGURES.mkdir(parents=True, exist_ok=True)

    cities = load_cities()
    if city_ids:
        cities = cities[cities["city_id"].isin(city_ids)].copy()

    rows: list[dict[str, object]] = []
    for _, city in cities.iterrows():
        city_id_value = int(city["city_id"])
        city_name_value = str(city["city_name"])
        logger.info("Generating data-processing report for city_id=%s city_name=%s", city_id_value, city_name_value)
        try:
            result = generate_city_data_report(
                city_id=city_id_value,
                outputs_root=outputs_root,
                figures_root=figures_root,
            )
            rows.append(
                {
                    "city_id": city_id_value,
                    "city_name": city_name_value,
                    "status": "ok",
                    "row_count": result.row_count,
                    "dataset_path": str(result.dataset_choice.dataset_path),
                    "markdown_path": str(result.paths.markdown_path),
                    "tables_dir": str(result.paths.tables_dir),
                    "figures_dir": str(result.paths.figures_dir),
                    "error": "",
                }
            )
        except Exception as exc:  # pragma: no cover - exercised via CLI/manual runs
            logger.exception("Data-processing report generation failed for city_id=%s", city_id_value)
            rows.append(
                {
                    "city_id": city_id_value,
                    "city_name": city_name_value,
                    "status": "error",
                    "row_count": 0,
                    "dataset_path": "",
                    "markdown_path": "",
                    "tables_dir": "",
                    "figures_dir": "",
                    "error": str(exc),
                }
            )
            if not continue_on_error:
                raise

    summary = pd.DataFrame(rows)
    summary_path = outputs_root / "data_processing_report_summary.csv"
    summary.to_csv(summary_path, index=False)
    logger.info("Wrote data-processing report batch summary to %s", summary_path)
    return BatchReportResult(summary=summary, summary_path=summary_path)
