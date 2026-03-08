from pathlib import Path

import pandas as pd

from src.summarize_phoenix_dataset import (
    PHOENIX_CITY_STEM,
    choose_phoenix_dataset,
    compute_preprocessing_audit,
)


def test_choose_phoenix_dataset_prefers_city_feature_output(tmp_path: Path) -> None:
    processed = tmp_path / "data_processed"
    city_features_path = processed / "city_features" / f"{PHOENIX_CITY_STEM}_features.parquet"
    filtered_path = processed / "intermediate" / "city_features" / f"{PHOENIX_CITY_STEM}_features_filtered.parquet"
    final_path = processed / "final" / "final_dataset.parquet"

    city_features_path.parent.mkdir(parents=True, exist_ok=True)
    filtered_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.parent.mkdir(parents=True, exist_ok=True)

    pd.DataFrame({"city_id": [1], "value": [1]}).to_parquet(city_features_path, index=False)
    pd.DataFrame({"city_id": [1], "value": [1]}).to_parquet(filtered_path, index=False)
    pd.DataFrame({"city_id": [1], "value": [1]}).to_parquet(final_path, index=False)

    result = choose_phoenix_dataset(project_root=tmp_path)

    assert result.dataset_path == city_features_path
    assert result.dataset_label == "per_city_feature_output"
    assert result.candidate_status["exists"].tolist() == [True, True, True]


def test_compute_preprocessing_audit_counts_open_water_and_low_pass_rows() -> None:
    unfiltered = pd.DataFrame(
        {
            "land_cover_class": pd.Series([11, 21, 22, 23], dtype="Int64"),
            "lst_median_may_aug": [10.0, 20.0, 30.0, 40.0],
            "n_valid_ecostress_passes": pd.Series([5, 2, 3, 1], dtype="Int64"),
        }
    )
    filtered = unfiltered.iloc[[2]].copy()

    result = compute_preprocessing_audit(unfiltered_df=unfiltered, filtered_df=filtered)

    assert result.loc[result["stage"] == "dropped_open_water_rows", "n_rows"].iloc[0] == 1
    assert result.loc[result["stage"] == "dropped_lt3_ecostress_pass_rows", "n_rows"].iloc[0] == 2
    assert result.loc[result["stage"] == "final_filtered_rows", "n_rows"].iloc[0] == 1
