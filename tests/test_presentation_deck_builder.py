from __future__ import annotations

from pathlib import Path

from src.pptx_vendor import ensure_pptx_vendor
from src.presentation_deck_builder import load_presentation_data
from src.presentation_editable_pptx_builder import build_editable_presentation
from src.presentation_visual_assets import build_presentation_visual_assets

ensure_pptx_vendor()

from pptx import Presentation


def test_presentation_data_matches_city_held_out_contract() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    data = load_presentation_data(repo_root)

    assert data.city_count == 30
    assert data.outer_fold_count == 5
    assert data.held_out_cities_per_fold == 6
    assert data.row_count == 71_394_894
    assert data.target_column == "hotspot_10pct"
    assert data.rf_frontier.pooled_pr_auc > data.logistic_5k.pooled_pr_auc


def test_reusable_presentation_figures_are_written() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    data = load_presentation_data(repo_root)
    assets = build_presentation_visual_assets(repo_root, data)

    assert assets.problem_schematic_png.exists()
    assert assets.problem_schematic_svg.exists()
    assert assets.design_schematic_png.exists()
    assert assets.design_schematic_svg.exists()


def test_editable_pptx_has_multiple_objects_and_editable_text(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output = tmp_path / "editable_deck.pptx"
    build_editable_presentation(repo_root=repo_root, output_path=output)

    prs = Presentation(output)
    assert len(prs.slides) == 7

    for slide in prs.slides:
        assert all(not shape.is_placeholder for shape in slide.shapes)
        assert any(getattr(shape, "has_text_frame", False) for shape in slide.shapes)

    title_text = [shape.text for shape in prs.slides[0].shapes if hasattr(shape, "text")]
    assert any("Nicholas Machado" in text for text in title_text)

    problem_slide = prs.slides[1]
    assert sum(1 for shape in problem_slide.shapes if shape.shape_type == 13) >= 1

    design_slide = prs.slides[2]
    assert sum(1 for shape in design_slide.shapes if shape.shape_type == 13) >= 1

    results_slide = prs.slides[3]
    assert sum(1 for shape in results_slide.shapes if shape.shape_type == 13) == 1
    assert any(
        "Logistic regression" in shape.text for shape in results_slide.shapes if hasattr(shape, "text")
    )
    assert any("RF pooled PR AUC" in shape.text for shape in results_slide.shapes if hasattr(shape, "text"))

    denver_slide = prs.slides[4]
    assert sum(1 for shape in denver_slide.shapes if shape.shape_type == 13) == 1

    qa_slide = prs.slides[6]
    assert sum(1 for shape in qa_slide.shapes if shape.shape_type == 13) == 0
    assert any("Questions?" in shape.text for shape in qa_slide.shapes if hasattr(shape, "text"))
