from pathlib import Path

import pandas as pd

import src.acquisition_orchestration as orchestration
from src.appeears_acquisition import AcquisitionRunResult
from src.raw_data_acquisition import RawAcquisitionResult
from src.support_layers import SupportLayerPreflightResult, SupportLayerPrepResult


def test_run_acquisition_orchestration_sequences_requested_subset(monkeypatch, tmp_path: Path):
    calls: list[tuple[str, object]] = []

    def fake_raw_data_acquisition(**kwargs):
        calls.append(("raw", kwargs))
        summary = pd.DataFrame(
            {
                "city_id": [1, 2, 1, 2],
                "dataset": ["dem", "dem", "nlcd", "hydro"],
                "status": ["completed", "completed", "skipped_existing", "completed"],
            }
        )
        return RawAcquisitionResult(
            summary=summary,
            summary_json_path=tmp_path / "raw.json",
            summary_csv_path=tmp_path / "raw.csv",
        )

    def fake_prepare_support_layers(**kwargs):
        calls.append(("support", kwargs))
        summary = pd.DataFrame(
            {
                "city_id": [1, 2],
                "status": ["completed", "skipped_existing"],
            }
        )
        return SupportLayerPrepResult(
            summary=summary,
            summary_json_path=tmp_path / "support.json",
            summary_csv_path=tmp_path / "support.csv",
        )

    def fake_appeears(**kwargs):
        calls.append((str(kwargs["product_type"]), kwargs))
        summary = pd.DataFrame(
            {
                "city_id": [1, 2],
                "status": ["completed", "submitted"],
            }
        )
        return AcquisitionRunResult(
            summary=summary,
            summary_json_path=tmp_path / f"{kwargs['product_type']}.json",
            summary_csv_path=tmp_path / f"{kwargs['product_type']}.csv",
        )

    monkeypatch.setattr(orchestration, "run_raw_data_acquisition", fake_raw_data_acquisition)
    monkeypatch.setattr(orchestration, "prepare_support_layers", fake_prepare_support_layers)
    monkeypatch.setattr(orchestration, "run_appeears_acquisition", fake_appeears)

    result = orchestration.run_acquisition_orchestration(
        start_date="2023-05-01",
        end_date="2023-08-31",
        city_ids=[1, 2],
        orchestration_dir=tmp_path / "orchestration",
    )

    assert [name for name, _ in calls] == ["raw", "support", "ndvi", "ecostress"]
    assert calls[0][1]["city_ids"] == [1, 2]
    assert calls[0][1]["all_missing"] is False
    assert calls[1][1]["city_ids"] == [1, 2]
    assert calls[2][1]["retry_incomplete"] is True
    assert calls[3][1]["retry_incomplete"] is True
    assert result.summary["stage"].tolist() == [
        "raw_support_acquisition",
        "support_layer_prep",
        "appeears_ndvi",
        "appeears_ecostress",
    ]
    assert result.summary_json_path.exists()
    assert result.summary_csv_path.exists()


def test_run_acquisition_orchestration_all_missing_uses_stage_specific_support_targets(monkeypatch, tmp_path: Path):
    calls: list[tuple[str, object]] = []

    def fake_raw_data_acquisition(**kwargs):
        calls.append(("raw", kwargs))
        summary = pd.DataFrame(
            {
                "city_id": [1, 2, 3],
                "dataset": ["dem", "nlcd", "hydro"],
                "status": ["completed", "completed", "completed"],
            }
        )
        return RawAcquisitionResult(
            summary=summary,
            summary_json_path=tmp_path / "raw.json",
            summary_csv_path=tmp_path / "raw.csv",
        )

    def fake_audit_support_layer_readiness(**kwargs):
        calls.append(("support_preflight", kwargs))
        summary = pd.DataFrame(
            {
                "city_id": [1, 2, 3],
                "support_prep_ready": [True, True, False],
                "dem_prepared_exists": [False, True, False],
                "nlcd_land_cover_prepared_exists": [False, True, False],
                "nlcd_impervious_prepared_exists": [False, True, False],
                "hydro_prepared_exists": [False, True, False],
            }
        )
        return SupportLayerPreflightResult(
            summary=summary,
            summary_json_path=tmp_path / "support_preflight.json",
            summary_csv_path=tmp_path / "support_preflight.csv",
        )

    def fake_prepare_support_layers(**kwargs):
        calls.append(("support", kwargs))
        summary = pd.DataFrame({"city_id": kwargs["city_ids"], "status": ["completed"] * len(kwargs["city_ids"])})
        return SupportLayerPrepResult(
            summary=summary,
            summary_json_path=tmp_path / "support.json",
            summary_csv_path=tmp_path / "support.csv",
        )

    def fake_appeears(**kwargs):
        calls.append((str(kwargs["product_type"]), kwargs))
        summary = pd.DataFrame({"city_id": [1, 2, 3], "status": ["completed", "submitted", "blocked"]})
        return AcquisitionRunResult(
            summary=summary,
            summary_json_path=tmp_path / f"{kwargs['product_type']}.json",
            summary_csv_path=tmp_path / f"{kwargs['product_type']}.csv",
        )

    monkeypatch.setattr(orchestration, "run_raw_data_acquisition", fake_raw_data_acquisition)
    monkeypatch.setattr(orchestration, "audit_support_layer_readiness", fake_audit_support_layer_readiness)
    monkeypatch.setattr(orchestration, "prepare_support_layers", fake_prepare_support_layers)
    monkeypatch.setattr(orchestration, "run_appeears_acquisition", fake_appeears)

    orchestration.run_acquisition_orchestration(
        start_date="2023-05-01",
        end_date="2023-08-31",
        all_missing=True,
        orchestration_dir=tmp_path / "orchestration",
    )

    assert calls[0][0] == "raw"
    assert calls[0][1]["all_missing"] is True
    assert calls[0][1]["city_ids"] is None
    assert calls[1][0] == "support_preflight"
    assert calls[2][0] == "support"
    assert calls[2][1]["city_ids"] == [1]
    assert calls[3][0] == "ndvi"
    assert calls[3][1]["city_ids"] is None
    assert calls[4][0] == "ecostress"
    assert calls[4][1]["city_ids"] is None
