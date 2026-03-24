from pathlib import Path

import pandas as pd

from src.data_processing_reporting import (
    BatchReportResult,
    CityReportResult,
    DatasetChoice,
    SummaryPaths,
    generate_all_city_data_reports,
    resolve_city_report_paths,
)


def test_resolve_city_report_paths_uses_split_data_processing_roots(tmp_path: Path) -> None:
    city = pd.Series({"city_id": 1, "city_name": "Phoenix", "state": "AZ"})
    outputs_root = tmp_path / "outputs" / "data_processing"
    figures_root = tmp_path / "figures" / "data_processing"

    paths = resolve_city_report_paths(city=city, outputs_root=outputs_root, figures_root=figures_root)

    assert paths.markdown_path == outputs_root / "01_phoenix_az" / "phoenix_data_summary.md"
    assert paths.tables_dir == outputs_root / "01_phoenix_az" / "tables"
    assert paths.figures_dir == figures_root / "01_phoenix_az"


def test_generate_all_city_data_reports_writes_batch_summary(monkeypatch, tmp_path: Path) -> None:
    cities = pd.DataFrame(
        [
            {"city_id": 1, "city_name": "Phoenix", "state": "AZ", "climate_group": "hot_arid", "lat": 0.0, "lon": 0.0},
            {"city_id": 2, "city_name": "Tucson", "state": "AZ", "climate_group": "hot_arid", "lat": 0.0, "lon": 0.0},
        ]
    )
    calls: list[int] = []

    def fake_generate_city_data_report(city_id: int, outputs_root: Path, figures_root: Path) -> CityReportResult:
        calls.append(city_id)
        city = cities.loc[cities["city_id"] == city_id].iloc[0].copy()
        stem = f"{city_id:02d}_{city['city_name'].lower()}_{city['state'].lower()}"
        paths = SummaryPaths(
            markdown_path=outputs_root / stem / f"{city['city_name'].lower()}_data_summary.md",
            output_dir=outputs_root / stem,
            tables_dir=outputs_root / stem / "tables",
            figures_dir=figures_root / stem,
        )
        return CityReportResult(
            city=city,
            paths=paths,
            dataset_choice=DatasetChoice(
                dataset_path=tmp_path / f"{city['city_name'].lower()}.parquet",
                dataset_label="per_city_feature_output",
                dataset_reason="test",
                candidate_status=pd.DataFrame(),
            ),
            row_count=123,
        )

    monkeypatch.setattr("src.data_processing_reporting.load_cities", lambda: cities)
    monkeypatch.setattr("src.data_processing_reporting.generate_city_data_report", fake_generate_city_data_report)

    result = generate_all_city_data_reports(
        city_ids=[2],
        outputs_root=tmp_path / "outputs" / "data_processing",
        figures_root=tmp_path / "figures" / "data_processing",
    )

    assert isinstance(result, BatchReportResult)
    assert calls == [2]
    assert result.summary["city_id"].tolist() == [2]
    assert result.summary["status"].tolist() == ["ok"]
    assert result.summary_path.exists()
