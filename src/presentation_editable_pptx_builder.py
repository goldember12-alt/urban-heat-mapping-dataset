from __future__ import annotations

from pathlib import Path

from src.pptx_vendor import ensure_pptx_vendor
from src.presentation_deck_builder import PresentationData, load_presentation_data
from src.presentation_visual_assets import build_presentation_visual_assets

ensure_pptx_vendor()

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Inches, Pt


SLIDE_WIDTH_IN = 13.333
SLIDE_HEIGHT_IN = 7.5
SLIDE_ASSET_WIDTH = 1600
SLIDE_ASSET_HEIGHT = 900

BACKGROUND = "F6F1E7"
INK = "1E2A2F"
MUTED = "5C696D"
ACCENT = "D26B34"
ACCENT_DARK = "9A402D"
TEAL = "3A7182"
TEAL_DARK = "254D5A"
WHITE = "FFFDFA"
PALE = "FFF8EF"
LIGHT = "EBE0CF"
PANEL = "FFFAF2"
OUTLINE = "DBC7AA"
COOL = "DFE8E8"
SAND = "F0E4D4"
TAKEAWAY = "E8DCC7"
GREEN = "8AA07A"


def build_editable_presentation(repo_root: Path, output_path: Path) -> Path:
    data = load_presentation_data(repo_root)
    visual_assets = build_presentation_visual_assets(repo_root, data)

    prs = Presentation()
    prs.slide_width = Inches(SLIDE_WIDTH_IN)
    prs.slide_height = Inches(SLIDE_HEIGHT_IN)

    blank = prs.slide_layouts[6]

    _slide_title(prs.slides.add_slide(blank))
    _slide_problem(prs.slides.add_slide(blank), visual_assets.problem_schematic_png)
    _slide_design(prs.slides.add_slide(blank), data, visual_assets.design_schematic_png)
    _slide_models(prs.slides.add_slide(blank), data)
    _slide_denver(prs.slides.add_slide(blank), data)
    _slide_takeaway(prs.slides.add_slide(blank), data)
    _slide_qa(prs.slides.add_slide(blank))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(output_path)
    return output_path


def _rgb(hex_color: str) -> RGBColor:
    return RGBColor.from_string(hex_color)


def _x(px: float) -> Inches:
    return Inches(px / SLIDE_ASSET_WIDTH * SLIDE_WIDTH_IN)


def _y(py: float) -> Inches:
    return Inches(py / SLIDE_ASSET_HEIGHT * SLIDE_HEIGHT_IN)


def _w(px: float) -> Inches:
    return Inches(px / SLIDE_ASSET_WIDTH * SLIDE_WIDTH_IN)


def _h(py: float) -> Inches:
    return Inches(py / SLIDE_ASSET_HEIGHT * SLIDE_HEIGHT_IN)


def _set_background(slide, color: str = BACKGROUND) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = _rgb(color)


def _add_oval(slide, x, y, w, h, color: str, transparency: float) -> None:
    shape = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.OVAL, _x(x), _y(y), _w(w), _h(h))
    fill = shape.fill
    fill.solid()
    fill.fore_color.rgb = _rgb(color)
    fill.transparency = transparency
    shape.line.fill.background()


def _add_round_rect(
    slide,
    x,
    y,
    w,
    h,
    fill_color: str,
    line_color: str | None = None,
    line_width_pt: float = 1.0,
) -> object:
    shape = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, _x(x), _y(y), _w(w), _h(h))
    fill = shape.fill
    fill.solid()
    fill.fore_color.rgb = _rgb(fill_color)
    if line_color is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = _rgb(line_color)
        shape.line.width = Pt(line_width_pt)
    return shape


def _add_chevron(slide, x, y, w, h, fill_color: str) -> object:
    shape = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.CHEVRON, _x(x), _y(y), _w(w), _h(h))
    fill = shape.fill
    fill.solid()
    fill.fore_color.rgb = _rgb(fill_color)
    shape.line.fill.background()
    return shape


def _add_textbox(
    slide,
    x,
    y,
    w,
    h,
    text: str,
    font_size: float,
    color: str = INK,
    bold: bool = False,
    align: PP_ALIGN = PP_ALIGN.LEFT,
    font_name: str = "Arial",
    margin_pt: float = 5.0,
    valign: MSO_ANCHOR = MSO_ANCHOR.TOP,
    auto_fit: bool = False,
) -> object:
    box = slide.shapes.add_textbox(_x(x), _y(y), _w(w), _h(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Pt(margin_pt)
    tf.margin_right = Pt(margin_pt)
    tf.margin_top = Pt(margin_pt)
    tf.margin_bottom = Pt(margin_pt)
    tf.vertical_anchor = valign
    if auto_fit:
        tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    lines = text.split("\n")
    for idx, line in enumerate(lines):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.alignment = align
        run = p.add_run()
        run.text = line
        run.font.name = font_name
        run.font.size = Pt(font_size)
        run.font.bold = bold
        run.font.color.rgb = _rgb(color)
    return box


def _add_picture(slide, path: Path, x: float, y: float, w: float, h: float) -> None:
    slide.shapes.add_picture(str(path), _x(x), _y(y), _w(w), _h(h))


def _slide_title(slide) -> None:
    _set_background(slide)
    _add_oval(slide, 1190, -80, 320, 320, ACCENT, 0.88)
    _add_oval(slide, 1270, 560, 230, 230, TEAL, 0.92)

    _add_round_rect(slide, 72, 86, 292, 54, ACCENT)
    _add_textbox(slide, 96, 95, 240, 34, "Held-out-city transfer", 18, WHITE, True)

    _add_textbox(
        slide,
        74,
        188,
        780,
        170,
        "Cross-City Urban Heat\nHotspot Prediction",
        29,
        INK,
        True,
        auto_fit=True,
    )
    _add_textbox(
        slide,
        78,
        382,
        560,
        56,
        "30 cities | 71.4M cells | unseen-city hotspot screening",
        18,
        MUTED,
        False,
        auto_fit=True,
    )
    _add_textbox(
        slide,
        78,
        560,
        560,
        62,
        "Max Clements | Nicholas Machado",
        23,
        TEAL_DARK,
        True,
        auto_fit=True,
    )
    _add_textbox(
        slide,
        78,
        640,
        620,
        46,
        "STAT 5630 Final Project | April 2026",
        16,
        MUTED,
        False,
        auto_fit=True,
    )

    _add_round_rect(slide, 1042, 198, 328, 356, PALE, OUTLINE, 1.0)
    motif_specs = [
        (1110, 270, 86, TEAL),
        (1238, 220, 86, GREEN),
        (1238, 382, 86, ACCENT),
    ]
    for x, y, size, fill in motif_specs:
        shape = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.OVAL, _x(x), _y(y), _w(size), _h(size))
        shape.fill.solid()
        shape.fill.fore_color.rgb = _rgb(fill)
        shape.line.fill.background()
    _add_chevron(slide, 1188, 300, 44, 46, TEAL_DARK)
    _add_chevron(slide, 1280, 342, 44, 46, ACCENT_DARK)
    _add_textbox(
        slide,
        1090,
        470,
        236,
        44,
        "seen cities -> unseen city",
        15,
        MUTED,
        True,
        PP_ALIGN.CENTER,
        auto_fit=True,
    )


def _slide_problem(slide, figure_path: Path) -> None:
    _set_background(slide)
    _add_oval(slide, 1260, -60, 260, 240, ACCENT, 0.9)

    _add_textbox(slide, 60, 38, 330, 34, "Why transfer matters", 18, TEAL_DARK, True)
    _add_round_rect(slide, 52, 88, 1496, 492, WHITE, OUTLINE, 1.4)
    _add_picture(slide, figure_path, 84, 116, 1430, 438)

    _add_round_rect(slide, 98, 636, 286, 56, ACCENT_DARK)
    _add_textbox(slide, 122, 646, 234, 34, "Research question", 19, WHITE, True, auto_fit=True)
    _add_round_rect(slide, 52, 698, 1496, 130, COOL)
    _add_textbox(
        slide,
        100,
        726,
        1380,
        70,
        "Can a model trained on some cities find heat hotspots in a city it has never seen?",
        26,
        INK,
        True,
        PP_ALIGN.CENTER,
        auto_fit=True,
    )


def _slide_design(slide, data: PresentationData, figure_path: Path) -> None:
    _set_background(slide)
    _add_textbox(slide, 58, 36, 420, 34, "Data + evaluation design", 18, TEAL_DARK, True)

    stat_cards = [
        (f"{data.city_count}", "cities"),
        (f"{data.row_count:,}", "rows"),
        ("30 m", "grid cell"),
        (data.target_column, "target"),
    ]
    x_positions = [52, 370, 688, 1006]
    for x, (value, label) in zip(x_positions, stat_cards):
        _add_round_rect(slide, x, 86, 286, 118, PANEL, OUTLINE)
        value_size = 26 if len(value) >= 11 else 30 if len(value) >= 8 else 36
        _add_textbox(slide, x + 22, 106, 242, 42, value, value_size, INK, True, auto_fit=True)
        _add_textbox(slide, x + 22, 152, 180, 28, label, 16, MUTED, False, auto_fit=True)

    _add_round_rect(slide, 1324, 86, 224, 118, ACCENT)
    _add_textbox(
        slide,
        1370,
        104,
        128,
        36,
        f"{data.outer_fold_count}",
        34,
        WHITE,
        True,
        PP_ALIGN.CENTER,
        auto_fit=True,
    )
    _add_textbox(
        slide,
        1350,
        152,
        172,
        26,
        "outer folds",
        15,
        WHITE,
        False,
        PP_ALIGN.CENTER,
        auto_fit=True,
    )

    _add_round_rect(slide, 52, 238, 1496, 500, WHITE, OUTLINE, 1.4)
    _add_picture(slide, figure_path, 84, 272, 1430, 410)

    _add_round_rect(slide, 188, 768, 1222, 64, LIGHT)
    _add_textbox(
        slide,
        220,
        784,
        1160,
        28,
        "Train, tune, and preprocess only on seen cities before scoring unseen cities.",
        17,
        TEAL_DARK,
        True,
        PP_ALIGN.CENTER,
        auto_fit=True,
    )


def _slide_models(slide, data: PresentationData) -> None:
    _set_background(slide)

    _add_round_rect(slide, 36, 30, 456, 820, PANEL, OUTLINE)
    _add_round_rect(slide, 62, 62, 404, 56, TEAL)
    _add_textbox(slide, 90, 72, 346, 30, "Same predictor contract", 18, WHITE, True, auto_fit=True)
    _add_textbox(
        slide,
        62,
        138,
        382,
        92,
        "Inputs exclude LST itself.\nThe comparison isolates linear\nversus nonlinear transfer.",
        18,
        INK,
        False,
        auto_fit=True,
    )

    _add_round_rect(slide, 72, 246, 382, 192, WHITE, "D9D9D1")
    _add_textbox(slide, 96, 266, 260, 28, "Logistic regression", 21, INK, True, auto_fit=True)
    _add_textbox(
        slide,
        96,
        314,
        270,
        54,
        "Pr(Y=1|x) = sigma(beta_0 + x^T beta)",
        16,
        ACCENT_DARK,
        True,
        auto_fit=True,
    )
    _add_textbox(slide, 96, 382, 248, 26, "Linear additive baseline", 15, MUTED, False, auto_fit=True)

    _add_round_rect(slide, 72, 456, 382, 192, WHITE, "D9D9D1")
    _add_textbox(slide, 96, 476, 230, 28, "Random forest", 21, INK, True, auto_fit=True)
    _add_textbox(
        slide,
        96,
        524,
        254,
        54,
        "p_hat(x) = (1/B) sum T_b(x)",
        16,
        ACCENT_DARK,
        True,
        auto_fit=True,
    )
    _add_textbox(
        slide,
        96,
        592,
        250,
        34,
        "Tree ensemble for nonlinear effects",
        15,
        MUTED,
        False,
        auto_fit=True,
    )

    _add_picture(slide, data.benchmark_figure_path, 516, 24, 1032, 468)

    metric_specs = [
        (526, "RF pooled PR AUC", f"{data.rf_frontier.pooled_pr_auc:.4f}", ACCENT_DARK, WHITE),
        (876, "RF recall@10%", f"{data.rf_frontier.pooled_recall_at_top_10pct:.4f}", TEAL, WHITE),
        (1226, "Logistic mean city PR AUC", f"{data.logistic_5k.mean_city_pr_auc:.4f}", "EFE5D2", INK),
    ]
    for x, label, value, fill, text_color in metric_specs:
        _add_round_rect(slide, x, 530, 312, 164, fill)
        _add_textbox(slide, x + 24, 554, 264, 40, label, 16, text_color, True, auto_fit=True)
        _add_textbox(
            slide,
            x + 24,
            602,
            264,
            42,
            value,
            28,
            text_color,
            True,
            auto_fit=True,
        )

    _add_round_rect(slide, 526, 744, 1008, 70, "EBE2D5")
    _add_textbox(
        slide,
        554,
        762,
        948,
        34,
        "Matched sampled all-fold checkpoints; not exhaustive 71M-cell scoring.",
        15,
        MUTED,
        False,
        auto_fit=True,
    )


def _slide_denver(slide, data: PresentationData) -> None:
    _set_background(slide)
    _add_round_rect(slide, 24, 20, 1552, 724, WHITE, OUTLINE)
    _add_picture(slide, data.denver_figure_path, 38, 38, 1524, 688)

    _add_round_rect(slide, 40, 772, 1066, 84, SAND)
    _add_textbox(
        slide,
        68,
        792,
        1010,
        42,
        "Prediction errors remain spatially structured rather than random.",
        25,
        INK,
        True,
        auto_fit=True,
    )
    _add_round_rect(slide, 1130, 780, 414, 68, TEAL)
    _add_textbox(
        slide,
        1162,
        796,
        348,
        30,
        "RF frontier | hot-arid",
        18,
        WHITE,
        True,
        PP_ALIGN.CENTER,
        auto_fit=True,
    )


def _slide_takeaway(slide, data: PresentationData) -> None:
    _set_background(slide)
    _add_oval(slide, 1270, -80, 300, 260, ACCENT, 0.9)

    _add_round_rect(slide, 52, 54, 1490, 178, WHITE, OUTLINE)
    _add_textbox(
        slide,
        92,
        92,
        1360,
        100,
        "Yes: cross-city hotspot transfer is feasible, but performance is not yet uniform across climates.",
        28,
        INK,
        True,
        auto_fit=True,
    )

    cards = [
        ("Signal", f"RF > logistic\nPR AUC {data.rf_frontier.pooled_pr_auc:.4f}", ACCENT_DARK, WHITE, "best current benchmark"),
        ("Caveat", "sampled all-fold\nbenchmark path", TEAL, WHITE, "not exhaustive 71M-cell scoring"),
        ("Next", "full scoring +\nclimate-shift diagnosis", TAKEAWAY, INK, "next analytic priority"),
    ]
    x_positions = [72, 560, 1048]
    for x, (heading, body, fill, head_color, footer) in zip(x_positions, cards):
        _add_round_rect(slide, x, 314, 420, 372, fill)
        glyph = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.OVAL, _x(x + 28), _y(340), _w(54), _h(54))
        glyph.fill.solid()
        glyph.fill.fore_color.rgb = _rgb(WHITE if fill != TAKEAWAY else PANEL)
        glyph.line.fill.background()
        _add_textbox(slide, x + 98, 344, 208, 28, heading, 21, head_color, True, auto_fit=True)
        _add_round_rect(slide, x + 24, 418, 372, 176, WHITE if fill == TAKEAWAY else "F8F4EC")
        _add_textbox(
            slide,
            x + 44,
            448,
            332,
            84,
            body,
            22,
            INK,
            True,
            auto_fit=True,
        )
        _add_textbox(
            slide,
            x + 44,
            614,
            332,
            30,
            footer,
            15,
            MUTED,
            False,
            auto_fit=True,
        )


def _slide_qa(slide) -> None:
    _set_background(slide)
    _add_oval(slide, 1220, 40, 320, 320, ACCENT, 0.9)
    _add_oval(slide, 1280, 560, 220, 220, TEAL, 0.93)

    _add_round_rect(slide, 74, 110, 230, 50, ACCENT_DARK)
    _add_textbox(slide, 98, 118, 182, 30, "Cross-city urban heat", 17, WHITE, True, auto_fit=True)

    _add_textbox(slide, 78, 268, 520, 82, "Questions?", 38, INK, True, auto_fit=True)
    _add_textbox(
        slide,
        80,
        380,
        620,
        42,
        "Max Clements | Nicholas Machado",
        18,
        MUTED,
        True,
        auto_fit=True,
    )
