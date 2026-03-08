from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config import DATA_PROCESSED, PROJECT_ROOT

logger = logging.getLogger(__name__)

PHOENIX_CITY_ID = 1
PHOENIX_CITY_STEM = "01_phoenix_az"
DEFAULT_MARKDOWN_PATH = PROJECT_ROOT / "outputs" / "phoenix_data_summary.md"
DEFAULT_ASSET_DIR = PROJECT_ROOT / "outputs" / "phoenix_data_summary"

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
        "meaning": "Indicator for cells at or above the Phoenix-specific 90th percentile of LST.",
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
    asset_dir: Path
    tables_dir: Path
    figures_dir: Path


def _candidate_dataset_paths(project_root: Path) -> list[tuple[str, Path, str]]:
    processed_dir = project_root / DATA_PROCESSED.name
    return [
        (
            "per_city_feature_output",
            processed_dir / "city_features" / f"{PHOENIX_CITY_STEM}_features.parquet",
            "Canonical Phoenix-only filtered output intended for downstream modeling.",
        ),
        (
            "intermediate_filtered_output",
            processed_dir / "intermediate" / "city_features" / f"{PHOENIX_CITY_STEM}_features_filtered.parquet",
            "Filtered intermediate table with the same post-rule rows but not the primary published output.",
        ),
        (
            "merged_final_dataset",
            processed_dir / "final" / "final_dataset.parquet",
            "Merged cross-city dataset that may contain Phoenix rows but is broader than the Phoenix-only deliverable.",
        ),
    ]


def choose_phoenix_dataset(project_root: Path = PROJECT_ROOT) -> DatasetChoice:
    """Choose the most relevant Phoenix analysis dataset from the materialized outputs."""
    records: list[dict[str, object]] = []
    chosen: tuple[str, Path, str] | None = None

    for label, path, reason in _candidate_dataset_paths(project_root):
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
                    if not (final_df["city_id"] == PHOENIX_CITY_ID).any():
                        continue
                except Exception:
                    continue
            chosen = (label, path, reason)

    if chosen is None:
        candidate_table = pd.DataFrame(records)
        raise FileNotFoundError(
            "No Phoenix analysis dataset was found. Checked:\n"
            f"{candidate_table[['candidate', 'path']].to_string(index=False)}"
        )

    label, path, reason = chosen
    return DatasetChoice(
        dataset_path=path,
        dataset_label=label,
        dataset_reason=reason,
        candidate_status=pd.DataFrame(records),
    )


def _paths(markdown_path: Path, asset_dir: Path | None = None) -> SummaryPaths:
    resolved_markdown = markdown_path.resolve()
    resolved_asset_dir = (asset_dir or DEFAULT_ASSET_DIR).resolve()
    return SummaryPaths(
        markdown_path=resolved_markdown,
        asset_dir=resolved_asset_dir,
        tables_dir=resolved_asset_dir / "tables",
        figures_dir=resolved_asset_dir / "figures",
    )


def _load_analysis_table(choice: DatasetChoice) -> pd.DataFrame:
    df = pd.read_parquet(choice.dataset_path)
    if choice.dataset_label == "merged_final_dataset":
        df = df[df["city_id"] == PHOENIX_CITY_ID].copy()
    if df.empty:
        raise ValueError(f"Chosen Phoenix dataset is empty: {choice.dataset_path}")
    return df


def _load_feature_geometry(project_root: Path = PROJECT_ROOT) -> gpd.GeoDataFrame:
    geometry_path = project_root / "data_processed" / "city_features" / f"{PHOENIX_CITY_STEM}_features.gpkg"
    if not geometry_path.exists():
        raise FileNotFoundError(f"Phoenix geometry file not found: {geometry_path}")
    gdf = gpd.read_file(geometry_path)
    if gdf.empty:
        raise ValueError(f"Phoenix geometry file is empty: {geometry_path}")
    return gdf


def _load_study_area(project_root: Path = PROJECT_ROOT) -> gpd.GeoDataFrame:
    study_area_path = project_root / "data_processed" / "study_areas" / f"{PHOENIX_CITY_STEM}_study_area.gpkg"
    if not study_area_path.exists():
        raise FileNotFoundError(f"Phoenix study-area file not found: {study_area_path}")
    return gpd.read_file(study_area_path)


def _load_preprocessing_inputs(project_root: Path = PROJECT_ROOT) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    base = project_root / "data_processed" / "intermediate" / "city_features"
    unfiltered_path = base / f"{PHOENIX_CITY_STEM}_features_unfiltered.parquet"
    filtered_path = base / f"{PHOENIX_CITY_STEM}_features_filtered.parquet"
    unfiltered = pd.read_parquet(unfiltered_path) if unfiltered_path.exists() else None
    filtered = pd.read_parquet(filtered_path) if filtered_path.exists() else None
    return unfiltered, filtered


def compute_preprocessing_audit(
    unfiltered_df: pd.DataFrame | None,
    filtered_df: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize row filtering between unfiltered and filtered Phoenix tables."""
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


def _save_distribution_figure(df: pd.DataFrame, output_path: Path) -> None:
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
    fig.suptitle("Phoenix key predictor and outcome distributions", fontsize=14)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def _save_land_cover_figure(land_cover_df: pd.DataFrame, output_path: Path) -> None:
    top = land_cover_df.head(8).sort_values("share_pct")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(top["land_cover_label"], top["share_pct"], color="#C56E3E")
    ax.set_xlabel("Share of Phoenix cells (%)")
    ax.set_title("Dominant Phoenix land-cover classes")
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def _save_correlation_figure(corr_df: pd.DataFrame, output_path: Path) -> None:
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
    ax.set_title("Correlation among key Phoenix variables")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def _save_hotspot_map(gdf: gpd.GeoDataFrame, study_area: gpd.GeoDataFrame, output_path: Path) -> None:
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
    ax.set_title("Phoenix hotspot cells (top 10% LST)")
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
            notes.append("None of the key modeling variables have missing values in the filtered Phoenix table.")
        else:
            worst = missingness_df.iloc[0]
            if max_missing < 0.01:
                notes.append(
                    f"Missingness is negligible: only {int(worst['missing_n']):,} `{worst['variable']}` values are missing ({worst['missing_pct']:.4f}%)."
                )
            else:
                notes.append(
                    f"Missingness is limited overall; the highest missing share is {worst['variable']} at {worst['missing_pct']:.2f}%."
                )

    hotspot_share = float((df["hotspot_10pct"].astype("boolean") == True).mean()) * 100.0
    notes.append(
        f"`hotspot_10pct` is intentionally imbalanced at {hotspot_share:.2f}% positives because it marks the Phoenix-specific top decile of LST."
    )

    if not land_cover_df.empty:
        top_land = land_cover_df.iloc[0]
        notes.append(
            f"Land cover is concentrated in {top_land['land_cover_label']} cells, which make up {top_land['share_pct']:.1f}% of the filtered Phoenix dataset."
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
                f"Hotspot prevalence varies by Phoenix quadrant from {quadrant_df['hotspot_share_pct'].min():.1f}% to {quadrant_df['hotspot_share_pct'].max():.1f}%, which is consistent with non-random spatial concentration."
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
                f"The published Phoenix table retains {int(final_n):,} of {int(unfiltered_n):,} initially assembled cells after rule-based filtering."
            )

    return notes[:6]


def _overview_table(
    df: pd.DataFrame,
    gdf: gpd.GeoDataFrame,
    study_area: gpd.GeoDataFrame,
    choice: DatasetChoice,
) -> pd.DataFrame:
    bounds = gdf.total_bounds
    extent_text = f"[{bounds[0]:.0f}, {bounds[1]:.0f}, {bounds[2]:.0f}, {bounds[3]:.0f}]"
    return pd.DataFrame(
        [
            {"metric": "Primary Phoenix analysis file", "value": str(choice.dataset_path.relative_to(PROJECT_ROOT))},
            {"metric": "Dataset choice rationale", "value": choice.dataset_reason},
            {"metric": "Observations", "value": len(df)},
            {"metric": "Variables", "value": df.shape[1]},
            {"metric": "Unit of analysis", "value": "One filtered 30 m grid cell in the buffered Phoenix study area"},
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


def _overview_paragraph(choice: DatasetChoice, df: pd.DataFrame) -> str:
    city_name = str(df["city_name"].iloc[0])
    climate_group = str(df["climate_group"].iloc[0])
    return (
        f"The Phoenix summary uses `{choice.dataset_path.relative_to(PROJECT_ROOT)}`, the canonical Phoenix-only "
        f"analysis-ready feature table. Each observation represents one filtered 30 m grid cell inside the buffered "
        f"{city_name} study area, with built-form, vegetation, elevation, hydrologic proximity, and warm-season "
        f"surface-temperature attributes aligned to the same cell geometry. The table is intended for downstream urban "
        f"heat modeling in a {climate_group} city, including both continuous LST analysis and binary hotspot prediction."
    )


def _section_image(markdown_path: Path, image_path: Path, alt_text: str) -> str:
    relative = image_path.relative_to(markdown_path.parent)
    return f"![{alt_text}]({relative.as_posix()})"


def _write_markdown(
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
    content = [
        "# Phoenix Summary of Data",
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
        _section_image(paths.markdown_path, paths.figures_dir / "phoenix_key_distributions.png", "Phoenix key distributions"),
        "",
        _section_image(paths.markdown_path, paths.figures_dir / "phoenix_land_cover_composition.png", "Phoenix land-cover composition"),
        "",
        _section_image(paths.markdown_path, paths.figures_dir / "phoenix_key_correlations.png", "Phoenix key correlations"),
        "",
        _section_image(paths.markdown_path, paths.figures_dir / "phoenix_hotspot_map.png", "Phoenix hotspot map"),
        "",
        "## Notable Patterns",
        "",
        *[f"- {note}" for note in notes],
        "",
        "## Output Notes",
        "",
        "- The Phoenix-only per-city feature parquet was chosen over the merged final dataset because it is the direct analysis-ready output for this city and already reflects the row-drop rules used by the pipeline.",
        "- Supporting CSV tables and PNG figures for this summary were generated deterministically by the companion CLI.",
    ]
    paths.markdown_path.parent.mkdir(parents=True, exist_ok=True)
    paths.markdown_path.write_text("\n".join(content) + "\n", encoding="utf-8")

def generate_phoenix_summary(
    markdown_path: Path = DEFAULT_MARKDOWN_PATH,
    asset_dir: Path = DEFAULT_ASSET_DIR,
    project_root: Path = PROJECT_ROOT,
) -> SummaryPaths:
    """Build the Phoenix summary markdown, tables, and figures."""
    paths = _paths(markdown_path=markdown_path, asset_dir=asset_dir)
    paths.tables_dir.mkdir(parents=True, exist_ok=True)
    paths.figures_dir.mkdir(parents=True, exist_ok=True)

    choice = choose_phoenix_dataset(project_root=project_root)
    df = _load_analysis_table(choice)
    gdf = _load_feature_geometry(project_root=project_root)
    study_area = _load_study_area(project_root=project_root)
    unfiltered_df, intermediate_filtered_df = _load_preprocessing_inputs(project_root=project_root)

    preprocessing_df = compute_preprocessing_audit(unfiltered_df=unfiltered_df, filtered_df=df)
    numeric_summary_df = compute_numeric_summary(df=df, columns=NUMERIC_SUMMARY_COLUMNS)
    missingness_df = compute_missingness_summary(df=df, columns=MISSINGNESS_COLUMNS)
    land_cover_df = compute_land_cover_summary(df=df)
    hotspot_df = compute_hotspot_summary(df=df)
    corr_df = compute_correlation_matrix(df=df, columns=CORRELATION_COLUMNS)
    quadrant_df = compute_quadrant_hotspot_summary(df=df)
    overview_df = _overview_table(df=df, gdf=gdf, study_area=study_area, choice=choice)
    key_variable_df = _key_variable_table()

    notes = build_notable_patterns(
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

    _save_distribution_figure(df=df, output_path=paths.figures_dir / "phoenix_key_distributions.png")
    _save_land_cover_figure(land_cover_df=land_cover_df, output_path=paths.figures_dir / "phoenix_land_cover_composition.png")
    _save_correlation_figure(corr_df=corr_df, output_path=paths.figures_dir / "phoenix_key_correlations.png")
    _save_hotspot_map(gdf=gdf, study_area=study_area, output_path=paths.figures_dir / "phoenix_hotspot_map.png")

    _write_markdown(
        paths=paths,
        overview_paragraph=_overview_paragraph(choice=choice, df=df),
        overview_df=overview_df,
        key_variable_df=key_variable_df,
        preprocessing_df=preprocessing_df,
        numeric_summary_df=numeric_summary_df,
        land_cover_df=land_cover_df,
        missingness_df=missingness_df,
        corr_df=corr_df,
        notes=notes,
    )

    logger.info("Wrote Phoenix markdown summary to %s", paths.markdown_path)
    logger.info("Wrote Phoenix summary assets to %s", paths.asset_dir)
    return paths


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a concise Phoenix data summary deliverable.")
    parser.add_argument(
        "--markdown-path",
        type=Path,
        default=DEFAULT_MARKDOWN_PATH,
        help="Output markdown path for the Phoenix summary.",
    )
    parser.add_argument(
        "--asset-dir",
        type=Path,
        default=DEFAULT_ASSET_DIR,
        help="Directory for supporting Phoenix summary tables and figures.",
    )
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()
    result = generate_phoenix_summary(markdown_path=args.markdown_path, asset_dir=args.asset_dir)
    print(result.markdown_path)
    print(result.asset_dir)


if __name__ == "__main__":
    main()

