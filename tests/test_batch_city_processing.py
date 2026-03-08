from pathlib import Path
from types import SimpleNamespace

import pandas as pd

import src.batch_city_processing as batch_city_processing


def test_process_all_cities_uses_full_city_list_when_city_ids_omitted(tmp_path: Path, monkeypatch):
    calls: list[int] = []

    def fake_process_city(
        city_id: int | None = None,
        buffer_m: float = 2000,
        resolution: float = 30,
        timeout: int = 60,
        save_outputs: bool = True,
    ):
        calls.append(int(city_id))
        return SimpleNamespace(
            grid=[1, 2, 3],
            study_area_path=tmp_path / f"{city_id}_study_area.gpkg",
            grid_path=tmp_path / f"{city_id}_grid.gpkg",
        )

    monkeypatch.setattr(batch_city_processing, "process_city", fake_process_city)

    result = batch_city_processing.process_all_cities(save_outputs=False)

    assert len(result.summary) == 30
    assert len(calls) == 30
    assert result.summary["status"].tolist() == ["ok"] * 30


def test_process_all_cities_honors_city_id_subset(tmp_path: Path, monkeypatch):
    calls: list[int] = []

    def fake_process_city(
        city_id: int | None = None,
        buffer_m: float = 2000,
        resolution: float = 30,
        timeout: int = 60,
        save_outputs: bool = True,
    ):
        calls.append(int(city_id))
        return SimpleNamespace(
            grid=[1],
            study_area_path=tmp_path / f"{city_id}_study_area.gpkg",
            grid_path=tmp_path / f"{city_id}_grid.gpkg",
        )

    monkeypatch.setattr(batch_city_processing, "process_city", fake_process_city)

    result = batch_city_processing.process_all_cities(save_outputs=False, city_ids=[1, 3, 5])

    assert calls == [1, 3, 5]
    assert result.summary["city_id"].tolist() == [1, 3, 5]
