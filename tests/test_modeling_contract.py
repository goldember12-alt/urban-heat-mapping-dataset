from pathlib import Path

import pandas as pd
import pytest

from src.modeling_config import (
    DEFAULT_FEATURE_COLUMNS,
    FEATURE_TYPE_CATEGORICAL,
    FEATURE_TYPE_NUMERIC,
    get_feature_type_map,
)
from src.modeling_data import (
    get_requested_outer_folds,
    load_city_outer_folds,
    load_outer_fold_data,
    validate_model_feature_columns,
)
from src.modeling_metrics import recall_at_top_fraction


def _build_modeling_fixture() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    city_specs = [
        (1, "Phoenix", "hot_arid", 0),
        (2, "Tucson", "hot_arid", 0),
        (3, "Miami", "humid_subtropical", 1),
        (4, "Atlanta", "humid_subtropical", 1),
    ]
    for city_id, city_name, climate_group, fold_id in city_specs:
        for idx in range(8):
            impervious = 10 + (idx * 12) + (city_id * 2)
            rows.append(
                {
                    "city_id": city_id,
                    "city_name": city_name,
                    "climate_group": climate_group,
                    "cell_id": (city_id * 1000) + idx,
                    "centroid_lon": -100.0 - city_id - (idx * 0.01),
                    "centroid_lat": 30.0 + city_id + (idx * 0.01),
                    "impervious_pct": float(impervious),
                    "land_cover_class": 21 if idx < 4 else 24,
                    "elevation_m": float((city_id * 100) + idx),
                    "dist_to_water_m": float(500 - (idx * 40) + (city_id * 5)),
                    "ndvi_median_may_aug": float(0.2 + (idx * 0.03)),
                    "lst_median_may_aug": float(30 + city_id + idx),
                    "n_valid_ecostress_passes": 5,
                    "hotspot_10pct": idx >= 4,
                }
            )
    return pd.DataFrame(rows)


def _build_fold_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "city_id": [1, 2, 3, 4],
            "city_name": ["Phoenix", "Tucson", "Miami", "Atlanta"],
            "climate_group": ["hot_arid", "hot_arid", "humid_subtropical", "humid_subtropical"],
            "row_count": [8, 8, 8, 8],
            "hotspot_positive_count": [4, 4, 4, 4],
            "hotspot_non_missing_count": [8, 8, 8, 8],
            "hotspot_prevalence": [0.5, 0.5, 0.5, 0.5],
            "outer_fold": [0, 0, 1, 1],
        }
    )


def test_validate_model_feature_columns_rejects_leakage_columns():
    available_columns = _build_modeling_fixture().columns.tolist()

    with pytest.raises(ValueError, match="lst_median_may_aug"):
        validate_model_feature_columns(
            feature_columns=["impervious_pct", "lst_median_may_aug"],
            available_columns=available_columns,
        )

    selected = validate_model_feature_columns(
        feature_columns=DEFAULT_FEATURE_COLUMNS,
        available_columns=available_columns,
    )
    assert selected == DEFAULT_FEATURE_COLUMNS


def test_validate_model_feature_columns_requires_explicit_type_contract():
    available_columns = [*_build_modeling_fixture().columns.tolist(), "custom_feature"]

    with pytest.raises(ValueError, match="explicit modeling type contract"):
        validate_model_feature_columns(
            feature_columns=["impervious_pct", "custom_feature"],
            available_columns=available_columns,
        )


def test_feature_type_contract_keeps_climate_group_categorical():
    feature_type_map = get_feature_type_map(DEFAULT_FEATURE_COLUMNS)

    assert feature_type_map["impervious_pct"] == FEATURE_TYPE_NUMERIC
    assert feature_type_map["climate_group"] == FEATURE_TYPE_CATEGORICAL
    assert feature_type_map["land_cover_class"] == FEATURE_TYPE_CATEGORICAL


def test_recall_at_top_fraction_matches_expected_example():
    recall = recall_at_top_fraction(
        y_true=[1, 0, 1, 0, 1],
        y_score=[0.9, 0.2, 0.8, 0.1, 0.7],
        fraction=0.4,
    )

    assert recall == pytest.approx(2 / 3)


def test_load_outer_fold_data_keeps_train_and_test_cities_disjoint(tmp_path: Path):
    dataset_path = tmp_path / "final_dataset.parquet"
    folds_path = tmp_path / "city_outer_folds.parquet"
    _build_modeling_fixture().to_parquet(dataset_path, index=False)
    _build_fold_fixture().to_parquet(folds_path, index=False)

    fold_table = load_city_outer_folds(folds_path)
    requested = get_requested_outer_folds(fold_table)
    assert requested == [0, 1]

    fold_data = load_outer_fold_data(
        outer_fold=0,
        dataset_path=dataset_path,
        folds_path=folds_path,
        feature_columns=DEFAULT_FEATURE_COLUMNS,
    )

    assert set(fold_data.train_city_ids) == {3, 4}
    assert set(fold_data.test_city_ids) == {1, 2}
    assert set(fold_data.train_df["city_id"].unique()) == {3, 4}
    assert set(fold_data.test_df["city_id"].unique()) == {1, 2}
