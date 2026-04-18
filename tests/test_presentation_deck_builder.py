from __future__ import annotations

from pathlib import Path

from src.pptx_vendor import ensure_pptx_vendor
from src.presentation_deck_builder import build_slide_specs, load_presentation_data
from src.presentation_editable_pptx_builder import build_editable_presentation

ensure_pptx_vendor()

from pptx import Presentation


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


def test_editable_pptx_has_multiple_objects_and_editable_text(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output = tmp_path / "editable_deck.pptx"
    build_editable_presentation(repo_root=repo_root, output_path=output)

    prs = Presentation(output)
    assert len(prs.slides) == 6

    # Title slide: many editable shape/text objects, no full-slide figure.
    assert len(prs.slides[0].shapes) >= 8
    assert all(shape.shape_type != 13 for shape in prs.slides[0].shapes)

    # Results slide: separate chart image plus text/shape objects.
    results_slide = prs.slides[3]
    assert len(results_slide.shapes) >= 8
    picture_count = sum(1 for shape in results_slide.shapes if shape.shape_type == 13)
    assert picture_count >= 1
    text_blobs = [shape.text for shape in results_slide.shapes if hasattr(shape, "text")]
    assert any("Logistic regression" in text for text in text_blobs)
    assert any("RF pooled PR" in text for text in text_blobs)

    # Denver slide: map image plus editable caption/tag shapes, not a single background image.
    denver_slide = prs.slides[4]
    assert len(denver_slide.shapes) >= 4
    assert sum(1 for shape in denver_slide.shapes if shape.shape_type == 13) >= 1
    assert any(
        "Prediction errors remain spatially structured rather than random." in shape.text
        for shape in denver_slide.shapes
        if hasattr(shape, "text")
    )
