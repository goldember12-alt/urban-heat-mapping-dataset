from pathlib import Path

import pandas as pd

import src.full_stack_orchestration as orchestration
from src.appeears_acquisition import AcquisitionRunResult
from src.feature_assembly import CityFeatureOutputPaths
from src.raw_data_acquisition import RawAcquisitionResult
from src.support_layers import SupportLayerPrepResult


def test_run_full_stack_orchestration_skips_existing_feature_outputs(monkeypatch, tmp_path: Path):
    cities = pd.DataFrame(
        {
            "city_id": [1],
            "city_name": ["Phoenix"],
            "state": ["AZ"],
            "climate_group": ["hot_arid"],
            "lat": [33.45],
            "lon": [-112.07],
        }
    )
    feature_paths = CityFeatureOutputPaths(
        city_features_gpkg_path=tmp_path / "city_features" / "phoenix.gpkg",
        city_features_parquet_path=tmp_path / "city_features" / "phoenix.parquet",
        intermediate_unfiltered_path=tmp_path / "intermediate" / "phoenix_unfiltered.parquet",
        intermediate_filtered_path=tmp_path / "intermediate" / "phoenix_filtered.parquet",
    )
    feature_paths.city_features_gpkg_path.parent.mkdir(parents=True, exist_ok=True)
    feature_paths.city_features_gpkg_path.write_text("existing")
    feature_paths.city_features_parquet_path.write_text("existing")

    monkeypatch.setattr(orchestration, "load_cities", lambda: cities)
    monkeypatch.setattr(
        orchestration,
        "expected_city_feature_output_paths",
        lambda **kwargs: feature_paths,
    )
    monkeypatch.setattr(
        orchestration,
        "run_raw_data_acquisition",
        lambda **kwargs: RawAcquisitionResult(
            summary=pd.DataFrame(
                {
                    "city_id": [1, 1, 1],
                    "dataset": ["dem", "nlcd", "hydro"],
                    "status": ["completed", "skipped_existing", "completed"],
                    "error": ["", "", ""],
                }
            ),
            summary_json_path=tmp_path / "raw.json",
            summary_csv_path=tmp_path / "raw.csv",
        ),
    )
    monkeypatch.setattr(
        orchestration,
        "prepare_support_layers",
        lambda **kwargs: SupportLayerPrepResult(
            summary=pd.DataFrame({"city_id": [1], "status": ["completed"], "error": [""], "message": [""]}),
            summary_json_path=tmp_path / "support.json",
            summary_csv_path=tmp_path / "support.csv",
        ),
    )

    def fake_appeears(**kwargs):
        return AcquisitionRunResult(
            summary=pd.DataFrame(
                {"city_id": [1], "status": ["skipped_existing"], "error": [""], "message": ["existing retained"]}
            ),
            summary_json_path=tmp_path / f"{kwargs['product_type']}.json",
            summary_csv_path=tmp_path / f"{kwargs['product_type']}.csv",
        )

    monkeypatch.setattr(orchestration, "run_appeears_acquisition", fake_appeears)
    monkeypatch.setattr(
        orchestration,
        "assemble_city_features",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("feature assembly should not run")),
    )

    result = orchestration.run_full_stack_orchestration(
        start_date="2023-05-01",
        end_date="2023-08-31",
        city_ids=[1],
        orchestration_dir=tmp_path / "orchestration",
        city_features_dir=tmp_path / "city_features",
        intermediate_dir=tmp_path / "intermediate",
    )

    row = result.summary.iloc[0]
    assert row["raw_support_acquisition_status"] == "completed"
    assert row["support_layer_prep_status"] == "completed"
    assert row["appeears_ndvi_status"] == "skipped_existing"
    assert row["appeears_ecostress_status"] == "skipped_existing"
    assert row["feature_assembly_status"] == "skipped_existing"
    assert row["overall_status"] == "completed"
    assert result.summary_json_path.exists()
    assert result.summary_csv_path.exists()


def test_run_full_stack_orchestration_blocks_features_when_credentials_missing(monkeypatch, tmp_path: Path):
    cities = pd.DataFrame(
        {
            "city_id": [1],
            "city_name": ["Phoenix"],
            "state": ["AZ"],
            "climate_group": ["hot_arid"],
            "lat": [33.45],
            "lon": [-112.07],
        }
    )
    feature_paths = CityFeatureOutputPaths(
        city_features_gpkg_path=tmp_path / "city_features" / "phoenix.gpkg",
        city_features_parquet_path=tmp_path / "city_features" / "phoenix.parquet",
        intermediate_unfiltered_path=tmp_path / "intermediate" / "phoenix_unfiltered.parquet",
        intermediate_filtered_path=tmp_path / "intermediate" / "phoenix_filtered.parquet",
    )

    monkeypatch.setattr(orchestration, "load_cities", lambda: cities)
    monkeypatch.setattr(
        orchestration,
        "expected_city_feature_output_paths",
        lambda **kwargs: feature_paths,
    )
    monkeypatch.setattr(
        orchestration,
        "run_raw_data_acquisition",
        lambda **kwargs: RawAcquisitionResult(
            summary=pd.DataFrame(
                {
                    "city_id": [1, 1, 1],
                    "dataset": ["dem", "nlcd", "hydro"],
                    "status": ["completed", "completed", "completed"],
                    "error": ["", "", ""],
                }
            ),
            summary_json_path=tmp_path / "raw.json",
            summary_csv_path=tmp_path / "raw.csv",
        ),
    )
    monkeypatch.setattr(
        orchestration,
        "prepare_support_layers",
        lambda **kwargs: SupportLayerPrepResult(
            summary=pd.DataFrame({"city_id": [1], "status": ["completed"], "error": [""], "message": [""]}),
            summary_json_path=tmp_path / "support.json",
            summary_csv_path=tmp_path / "support.csv",
        ),
    )

    def fake_appeears(**kwargs):
        return AcquisitionRunResult(
            summary=pd.DataFrame(
                {
                    "city_id": [1],
                    "status": ["blocked_missing_credentials"],
                    "error": ["missing_credentials"],
                    "message": ["Missing env vars: APPEEARS_API_TOKEN, EARTHDATA_USERNAME, EARTHDATA_PASSWORD."],
                }
            ),
            summary_json_path=tmp_path / f"{kwargs['product_type']}.json",
            summary_csv_path=tmp_path / f"{kwargs['product_type']}.csv",
        )

    monkeypatch.setattr(orchestration, "run_appeears_acquisition", fake_appeears)
    monkeypatch.setattr(
        orchestration,
        "assemble_city_features",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("feature assembly should not run")),
    )

    result = orchestration.run_full_stack_orchestration(
        start_date="2023-05-01",
        end_date="2023-08-31",
        city_ids=[1],
        orchestration_dir=tmp_path / "orchestration",
        city_features_dir=tmp_path / "city_features",
        intermediate_dir=tmp_path / "intermediate",
    )

    row = result.summary.iloc[0]
    assert row["appeears_ndvi_status"] == "blocked_missing_credentials"
    assert row["appeears_ecostress_status"] == "blocked_missing_credentials"
    assert row["feature_assembly_status"] == "not_started"
    assert "waiting on prerequisites" in row["feature_assembly_message"]
    assert row["overall_status"] == "blocked_missing_credentials"


def test_run_full_stack_orchestration_all_missing_uses_missing_city_subset(monkeypatch, tmp_path: Path):
    cities = pd.DataFrame(
        {
            "city_id": [1, 2],
            "city_name": ["Phoenix", "Tucson"],
            "state": ["AZ", "AZ"],
            "climate_group": ["hot_arid", "hot_arid"],
            "lat": [33.45, 32.22],
            "lon": [-112.07, -110.97],
        }
    )
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(orchestration, "load_cities", lambda: cities)
    monkeypatch.setattr(orchestration, "city_ids_missing_full_stack_outputs", lambda **kwargs: [2])
    monkeypatch.setattr(
        orchestration,
        "expected_city_feature_output_paths",
        lambda **kwargs: CityFeatureOutputPaths(
            city_features_gpkg_path=tmp_path / "city_features" / "city.gpkg",
            city_features_parquet_path=tmp_path / "city_features" / "city.parquet",
            intermediate_unfiltered_path=tmp_path / "intermediate" / "city_unfiltered.parquet",
            intermediate_filtered_path=tmp_path / "intermediate" / "city_filtered.parquet",
        ),
    )

    def fake_raw(**kwargs):
        calls.append(("raw", kwargs))
        return RawAcquisitionResult(
            summary=pd.DataFrame(
                {
                    "city_id": [2, 2, 2],
                    "dataset": ["dem", "nlcd", "hydro"],
                    "status": ["skipped_existing", "skipped_existing", "skipped_existing"],
                    "error": ["", "", ""],
                }
            ),
            summary_json_path=tmp_path / "raw.json",
            summary_csv_path=tmp_path / "raw.csv",
        )

    def fake_support(**kwargs):
        calls.append(("support", kwargs))
        return SupportLayerPrepResult(
            summary=pd.DataFrame({"city_id": [2], "status": ["skipped_existing"], "error": [""], "message": [""]}),
            summary_json_path=tmp_path / "support.json",
            summary_csv_path=tmp_path / "support.csv",
        )

    def fake_appeears(**kwargs):
        calls.append((str(kwargs["product_type"]), kwargs))
        return AcquisitionRunResult(
            summary=pd.DataFrame({"city_id": [2], "status": ["skipped_existing"], "error": [""], "message": [""]}),
            summary_json_path=tmp_path / f"{kwargs['product_type']}.json",
            summary_csv_path=tmp_path / f"{kwargs['product_type']}.csv",
        )

    monkeypatch.setattr(orchestration, "run_raw_data_acquisition", fake_raw)
    monkeypatch.setattr(orchestration, "prepare_support_layers", fake_support)
    monkeypatch.setattr(orchestration, "run_appeears_acquisition", fake_appeears)
    monkeypatch.setattr(
        orchestration,
        "assemble_city_features",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("feature assembly should not run")),
    )

    result = orchestration.run_full_stack_orchestration(
        start_date="2023-05-01",
        end_date="2023-08-31",
        all_missing=True,
        orchestration_dir=tmp_path / "orchestration",
        city_features_dir=tmp_path / "city_features",
        intermediate_dir=tmp_path / "intermediate",
    )

    assert [name for name, _ in calls] == ["raw", "support", "ndvi", "ecostress"]
    assert calls[0][1]["city_ids"] == [2]
    assert calls[1][1]["city_ids"] == [2]
    assert calls[2][1]["city_ids"] == [2]
    assert calls[3][1]["city_ids"] == [2]
    assert result.summary["city_id"].tolist() == [2]


def test_run_full_stack_orchestration_carries_stage_failure_metadata(monkeypatch, tmp_path: Path):
    cities = pd.DataFrame(
        {
            "city_id": [1],
            "city_name": ["Phoenix"],
            "state": ["AZ"],
            "climate_group": ["hot_arid"],
            "lat": [33.45],
            "lon": [-112.07],
        }
    )

    monkeypatch.setattr(orchestration, "load_cities", lambda: cities)
    monkeypatch.setattr(
        orchestration,
        "expected_city_feature_output_paths",
        lambda **kwargs: CityFeatureOutputPaths(
            city_features_gpkg_path=tmp_path / "city_features" / "phoenix.gpkg",
            city_features_parquet_path=tmp_path / "city_features" / "phoenix.parquet",
            intermediate_unfiltered_path=tmp_path / "intermediate" / "phoenix_unfiltered.parquet",
            intermediate_filtered_path=tmp_path / "intermediate" / "phoenix_filtered.parquet",
        ),
    )
    monkeypatch.setattr(
        orchestration,
        "run_raw_data_acquisition",
        lambda **kwargs: RawAcquisitionResult(
            summary=pd.DataFrame(
                {
                    "city_id": [1, 1, 1],
                    "dataset": ["dem", "nlcd", "hydro"],
                    "status": ["failed", "completed", "completed"],
                    "error": ["stream interrupted", "", ""],
                    "failure_reason": ["download_stream_interrupted", "", ""],
                    "recoverable": [True, False, False],
                }
            ),
            summary_json_path=tmp_path / "raw.json",
            summary_csv_path=tmp_path / "raw.csv",
        ),
    )
    monkeypatch.setattr(
        orchestration,
        "prepare_support_layers",
        lambda **kwargs: SupportLayerPrepResult(
            summary=pd.DataFrame({"city_id": [1], "status": ["not_started"], "error": [""], "message": [""]}),
            summary_json_path=tmp_path / "support.json",
            summary_csv_path=tmp_path / "support.csv",
        ),
    )
    monkeypatch.setattr(
        orchestration,
        "run_appeears_acquisition",
        lambda **kwargs: AcquisitionRunResult(
            summary=pd.DataFrame({"city_id": [1], "status": ["not_started"], "error": [""], "message": [""]}),
            summary_json_path=tmp_path / f"{kwargs['product_type']}.json",
            summary_csv_path=tmp_path / f"{kwargs['product_type']}.csv",
        ),
    )
    monkeypatch.setattr(
        orchestration,
        "assemble_city_features",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("feature assembly should not run")),
    )

    result = orchestration.run_full_stack_orchestration(
        start_date="2023-05-01",
        end_date="2023-08-31",
        city_ids=[1],
        orchestration_dir=tmp_path / "orchestration",
        city_features_dir=tmp_path / "city_features",
        intermediate_dir=tmp_path / "intermediate",
    )

    row = result.summary.iloc[0]
    assert row["raw_support_acquisition_failure_reason"] == "download_stream_interrupted"
    assert bool(row["raw_support_acquisition_recoverable"]) is True
    assert row["stage"] == "raw_support_acquisition"


def test_run_full_stack_orchestration_carries_exception_metadata(monkeypatch, tmp_path: Path):
    cities = pd.DataFrame(
        {
            "city_id": [1],
            "city_name": ["Phoenix"],
            "state": ["AZ"],
            "climate_group": ["hot_arid"],
            "lat": [33.45],
            "lon": [-112.07],
        }
    )

    monkeypatch.setattr(orchestration, "load_cities", lambda: cities)
    monkeypatch.setattr(
        orchestration,
        "expected_city_feature_output_paths",
        lambda **kwargs: CityFeatureOutputPaths(
            city_features_gpkg_path=tmp_path / "city_features" / "phoenix.gpkg",
            city_features_parquet_path=tmp_path / "city_features" / "phoenix.parquet",
            intermediate_unfiltered_path=tmp_path / "intermediate" / "phoenix_unfiltered.parquet",
            intermediate_filtered_path=tmp_path / "intermediate" / "phoenix_filtered.parquet",
        ),
    )
    monkeypatch.setattr(
        orchestration,
        "run_raw_data_acquisition",
        lambda **kwargs: RawAcquisitionResult(
            summary=pd.DataFrame(
                {
                    "city_id": [1, 1, 1],
                    "dataset": ["dem", "nlcd", "hydro"],
                    "status": ["completed", "completed", "completed"],
                    "error": ["", "", ""],
                }
            ),
            summary_json_path=tmp_path / "raw.json",
            summary_csv_path=tmp_path / "raw.csv",
        ),
    )
    monkeypatch.setattr(
        orchestration,
        "prepare_support_layers",
        lambda **kwargs: SupportLayerPrepResult(
            summary=pd.DataFrame({"city_id": [1], "status": ["completed"], "error": [""], "message": [""]}),
            summary_json_path=tmp_path / "support.json",
            summary_csv_path=tmp_path / "support.csv",
        ),
    )
    monkeypatch.setattr(
        orchestration,
        "run_appeears_acquisition",
        lambda **kwargs: AcquisitionRunResult(
            summary=pd.DataFrame(
                {
                    "city_id": [1],
                    "status": ["failed"],
                    "error": ["download_error:connection reset"],
                    "failure_reason": ["download_connection_error"],
                    "recoverable": [True],
                    "message": ["download failed"],
                    "exception_type": ["AppEEARSRequestError"],
                    "exception_message": ["connection reset"],
                    "traceback": ["Traceback..."],
                }
            ),
            summary_json_path=tmp_path / f"{kwargs['product_type']}.json",
            summary_csv_path=tmp_path / f"{kwargs['product_type']}.csv",
        ),
    )
    monkeypatch.setattr(
        orchestration,
        "assemble_city_features",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("feature assembly should not run")),
    )

    result = orchestration.run_full_stack_orchestration(
        start_date="2023-05-01",
        end_date="2023-08-31",
        city_ids=[1],
        orchestration_dir=tmp_path / "orchestration",
        city_features_dir=tmp_path / "city_features",
        intermediate_dir=tmp_path / "intermediate",
    )

    row = result.summary.iloc[0]
    assert row["stage"] == "appeears_ndvi"
    assert row["exception_type"] == "AppEEARSRequestError"
    assert row["exception_message"] == "connection reset"
    assert row["traceback"] == "Traceback..."
    assert row["appeears_ndvi_exception_type"] == "AppEEARSRequestError"
    assert row["appeears_ndvi_traceback"] == "Traceback..."


def test_orchestration_exit_code_is_explicit():
    assert orchestration.orchestration_exit_code(pd.DataFrame()) == 0
    assert orchestration.orchestration_exit_code(pd.DataFrame({"overall_status": ["completed"]})) == 0
    assert orchestration.orchestration_exit_code(pd.DataFrame({"overall_status": ["not_started"]})) == 2
    assert orchestration.orchestration_exit_code(pd.DataFrame({"overall_status": ["failed", "completed"]})) == 1
