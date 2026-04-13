from pathlib import Path

import pandas as pd
import pytest

from src.modeling_prep import (
    audit_final_dataset,
    build_city_fold_table,
    load_final_dataset,
    validate_required_final_columns,
)


def _build_final_dataset_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "city_id": [1, 1, 2, 2, 3, 3],
            "city_name": ["Phoenix", "Phoenix", "Tucson", "Tucson", "Miami", "Miami"],
            "climate_group": ["hot_arid", "hot_arid", "hot_arid", "hot_arid", "humid_subtropical", "humid_subtropical"],
            "cell_id": [1, 2, 1, 2, 1, 2],
            "centroid_lon": [-112.1, -112.0, -110.9, -110.8, -80.2, -80.1],
            "centroid_lat": [33.4, 33.5, 32.2, 32.3, 25.7, 25.8],
            "impervious_pct": [25.0, 40.0, 15.0, 18.0, 55.0, 60.0],
            "land_cover_class": [21, 22, 23, 24, 22, 21],
            "elevation_m": [350.0, 355.0, 720.0, 725.0, 4.0, 5.0],
            "dist_to_water_m": [100.0, 200.0, 300.0, 400.0, 25.0, 20.0],
            "ndvi_median_may_aug": [0.20, 0.25, 0.28, 0.30, 0.45, 0.47],
            "tree_cover_proxy_pct_270m": [0.10, 0.12, 0.05, 0.06, 0.18, 0.20],
            "vegetated_cover_proxy_pct_270m": [0.25, 0.28, 0.20, 0.22, 0.35, 0.37],
            "impervious_pct_mean_270m": [30.0, 35.0, 18.0, 20.0, 58.0, 62.0],
            "lst_median_may_aug": [38.0, 41.0, 35.0, 37.0, 32.0, 33.0],
            "n_valid_ecostress_passes": [5, 6, 4, 4, 8, 9],
            "hotspot_10pct": [False, True, False, True, False, True],
        }
    )


def test_validate_required_final_columns_raises_for_missing_columns():
    df = _build_final_dataset_fixture().drop(columns=["hotspot_10pct", "ndvi_median_may_aug"])

    with pytest.raises(ValueError, match="hotspot_10pct, ndvi_median_may_aug"):
        validate_required_final_columns(df)


def test_load_final_dataset_can_select_column_subset(tmp_path: Path):
    dataset_path = tmp_path / "final_dataset.parquet"
    _build_final_dataset_fixture().to_parquet(dataset_path, index=False)

    loaded = load_final_dataset(dataset_path=dataset_path, columns=["city_id", "hotspot_10pct", "city_id"])

    assert loaded.columns.tolist() == ["city_id", "hotspot_10pct"]
    assert loaded.shape == (6, 2)


def test_build_city_fold_table_keeps_each_city_in_one_fold_and_is_deterministic():
    df = _build_final_dataset_fixture()

    first = build_city_fold_table(df, n_splits=2)
    second = build_city_fold_table(df, n_splits=2)

    pd.testing.assert_frame_equal(first, second)
    assert first["city_id"].is_unique
    assert set(first["outer_fold"]) == {0, 1}

    merged = df.merge(first[["city_id", "outer_fold"]], on="city_id", how="left")
    assert merged["outer_fold"].notna().all()
    assert merged.groupby("city_id")["outer_fold"].nunique().eq(1).all()


def test_audit_final_dataset_writes_expected_artifacts(tmp_path: Path):
    dataset_path = tmp_path / "final_dataset.parquet"
    output_dir = tmp_path / "modeling"
    df = _build_final_dataset_fixture()
    df.to_parquet(dataset_path, index=False)

    result = audit_final_dataset(dataset_path=dataset_path, output_dir=output_dir)

    assert result.row_count == len(df)
    assert result.city_count == 3
    assert result.summary_json_path.exists()
    assert result.summary_markdown_path.exists()
    assert result.city_summary_csv_path.exists()
    assert result.missingness_csv_path.exists()
    assert result.missingness_by_city_csv_path.exists()

    city_summary = pd.read_csv(result.city_summary_csv_path)
    assert city_summary["city_id"].tolist() == [1, 2, 3]
    assert city_summary["row_count"].tolist() == [2, 2, 2]

    missingness = pd.read_csv(result.missingness_csv_path)
    assert "impervious_pct" in missingness["column"].tolist()
    assert (missingness["missing_count"] == 0).all()
