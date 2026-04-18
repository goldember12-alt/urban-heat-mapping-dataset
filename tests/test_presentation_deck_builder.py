from __future__ import annotations

from pathlib import Path

from src.presentation_deck_builder import build_slide_specs, load_presentation_data


def test_slide_specs_respect_slide_cap() -> None:
    specs = build_slide_specs()
    assert len(specs) == 6
    assert len(specs) - 1 <= 5


def test_presentation_data_matches_city_held_out_contract() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    data = load_presentation_data(repo_root)

    assert data.city_count == 30
    assert data.outer_fold_count == 5
    assert data.held_out_cities_per_fold == 6
    assert data.row_count == 71_394_894
    assert data.target_column == "hotspot_10pct"
    assert data.rf_frontier.pooled_pr_auc > data.logistic_5k.pooled_pr_auc
