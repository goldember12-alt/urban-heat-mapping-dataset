from __future__ import annotations

from pathlib import Path

from src.pptx_vendor import ensure_pptx_vendor
from src.presentation_deck_builder import PresentationData, load_presentation_data

ensure_pptx_vendor()

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
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


def build_editable_presentation(repo_root: Path, output_path: Path) -> Path:
    data = load_presentation_data(repo_root)
    prs = Presentation()
    prs.slide_width = Inches(SLIDE_WIDTH_IN)
    prs.slide_height = Inches(SLIDE_HEIGHT_IN)

    blank = prs.slide_layouts[6]

    _slide_title(prs.slides.add_slide(blank), data)
    _slide_problem(prs.slides.add_slide(blank))
    _slide_design(prs.slides.add_slide(blank), data)
    _slide_models(prs.slides.add_slide(blank), data)
    _slide_denver(prs.slides.add_slide(blank), data)
    _slide_takeaway(prs.slides.add_slide(blank), data)

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
    margin_pt: float = 2.0,
    valign: MSO_ANCHOR = MSO_ANCHOR.TOP,
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


def _slide_title(slide, data: PresentationData) -> None:
    del data
    _set_background(slide)
    _add_oval(slide, 770, -120, 620, 780, ACCENT, 0.78)
    _add_oval(slide, 1160, -40, 420, 500, TEAL, 0.86)
    _add_oval(slide, -20, 640, 520, 380, LIGHT, 0.74)

    _add_round_rect(slide, 62, 58, 388, 64, ACCENT)
    _add_textbox(slide, 92, 66, 330, 48, "Held-out-city transfer", 22, WHITE, True)

    _add_textbox(
        slide,
        58,
        138,
        900,
        250,
        "30 cities | 71.4M cells\n| hotspot screening on\nunseen cities",
        40,
        INK,
        True,
    )
    _add_textbox(
        slide,
        66,
        500,
        860,
        86,
        "A presentation-first view of the urban heat\ntransfer benchmark.",
        25,
        MUTED,
    )

    _add_round_rect(slide, 1010, 110, 520, 600, PALE)
    _add_round_rect(slide, 1048, 156, 444, 78, TEAL)
    _add_textbox(slide, 1068, 172, 412, 42, "What the talk shows", 23, WHITE, True, PP_ALIGN.CENTER)

    bullets = [
        "why cross-city\ntransfer is the real\ntest",
        "how 30-city\nevaluation stays\nleakage-safe",
        "where RF helps\nand where\nuncertainty\nremains",
    ]
    y = 280
    for bullet in bullets:
        dot = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.OVAL, _x(1070), _y(y + 14), _w(18), _h(18))
        dot.fill.solid()
        dot.fill.fore_color.rgb = _rgb(ACCENT)
        dot.line.fill.background()
        _add_textbox(slide, 1120, y, 310, 110, bullet, 24, INK, True)
        y += 114

    _add_round_rect(slide, 62, 794, 1468, 70, LIGHT)
    _add_textbox(
        slide,
        92,
        812,
        1280,
        32,
        "Max Clements   |   STAT 5630 Final Project   |   April 2026",
        20,
        TEAL_DARK,
    )


def _slide_problem(slide) -> None:
    _set_background(slide)
    _add_oval(slide, 1040, -40, 500, 320, ACCENT, 0.86)
    _add_oval(slide, -40, 660, 420, 300, TEAL, 0.92)

    card_specs = [
        ("Heat risk matters", "public health + planning"),
        ("Cities differ", "climate, land cover, water,\nvegetation"),
        ("Random row splits mislead", "same-city leakage looks\neasier than transfer"),
    ]
    for x, (headline, subline) in zip((54, 548, 1042), card_specs):
        _add_round_rect(slide, x, 54, 446, 152, PANEL, OUTLINE)
        _add_textbox(slide, x + 28, 80, 392, 34, headline, 24, INK, True)
        _add_textbox(slide, x + 28, 126, 388, 60, subline, 19, MUTED)

    _add_round_rect(slide, 60, 248, 1480, 370, WHITE, OUTLINE, 1.5)
    _add_round_rect(slide, 108, 292, 314, 64, ACCENT_DARK)
    _add_textbox(slide, 136, 308, 258, 30, "Core question", 23, WHITE, True)
    _add_textbox(
        slide,
        114,
        396,
        1300,
        170,
        "Can a model trained on some cities find\nheat hotspots in a city it has never\nseen?",
        33,
        INK,
        True,
    )
    _add_round_rect(slide, 186, 716, 1228, 88, COOL)
    _add_textbox(
        slide,
        214,
        738,
        1180,
        38,
        "This is a transfer benchmark, not same-city interpolation.",
        23,
        TEAL_DARK,
        True,
        PP_ALIGN.CENTER,
    )


def _slide_design(slide, data: PresentationData) -> None:
    _set_background(slide)
    _add_oval(slide, 1240, 700, 380, 260, TEAL, 0.9)

    stat_cards = [
        (f"{data.city_count}", "cities"),
        (f"{data.row_count:,}", "rows"),
        ("30 m", "grid cell"),
        (data.target_column, "target"),
    ]
    x_positions = [50, 364, 678, 992]
    for x, (value, label) in zip(x_positions, stat_cards):
        _add_round_rect(slide, x, 42, 300, 180, PANEL, OUTLINE)
        size = 36 if len(value) >= 11 else 44 if len(value) >= 8 else 50
        _add_textbox(slide, x + 26, 74, 248, 54, value, size, INK, True)
        _add_textbox(slide, x + 26, 150, 200, 30, label, 20, MUTED)

    _add_round_rect(slide, 1308, 42, 240, 180, ACCENT)
    _add_textbox(slide, 1382, 76, 90, 52, f"{data.outer_fold_count}", 50, WHITE, True, PP_ALIGN.CENTER)
    _add_textbox(slide, 1340, 150, 180, 32, "outer folds", 22, WHITE, False, PP_ALIGN.CENTER)

    _add_round_rect(slide, 50, 274, 942, 538, WHITE, OUTLINE)
    _add_round_rect(slide, 84, 308, 302, 68, TEAL)
    _add_textbox(slide, 116, 324, 230, 32, "Analytic unit", 24, WHITE, True, PP_ALIGN.CENTER)
    _add_textbox(
        slide,
        88,
        418,
        840,
        112,
        "One row = one 30 m cell in one city. Predictors\nsummarize built form, terrain, water, vegetation,\nand climate context.",
        22,
        INK,
    )

    _add_round_rect(slide, 1020, 274, 528, 538, PANEL, OUTLINE)
    _add_round_rect(slide, 1044, 308, 480, 68, ACCENT_DARK)
    _add_textbox(slide, 1070, 324, 430, 32, "Leakage-safe benchmark", 22, WHITE, True, PP_ALIGN.CENTER)
    _add_textbox(
        slide,
        1050,
        420,
        432,
        130,
        "6 held-out cities per fold.\nPreprocessing, tuning,\nand model fitting use\ntraining-city rows only.",
        21,
        INK,
    )

    pipeline = [
        (90, 648, 212, "Assemble\nfeatures", TEAL),
        (384, 648, 228, "Train on 24\ncities", "8AA07A"),
        (694, 648, 228, "Tune on\ntrain only", ACCENT),
        (1004, 648, 246, "Score 6\nunseen cities", ACCENT_DARK),
    ]
    for idx, (x, y, w, text, fill) in enumerate(pipeline):
        _add_round_rect(slide, x, y, w, 106, fill)
        _add_textbox(slide, x + 18, y + 18, w - 36, 70, text, 18, WHITE, True, PP_ALIGN.CENTER)
        if idx < len(pipeline) - 1:
            _add_chevron(slide, x + w + 18, y + 34, 40, 40, MUTED)


def _slide_models(slide, data: PresentationData) -> None:
    _set_background(slide)

    _add_round_rect(slide, 34, 34, 452, 810, PANEL, OUTLINE)
    _add_round_rect(slide, 58, 68, 404, 58, TEAL)
    _add_textbox(slide, 82, 82, 356, 26, "Same predictor contract", 18, WHITE, True)
    _add_textbox(
        slide,
        58,
        146,
        374,
        110,
        "Inputs exclude LST itself.\nThe comparison isolates\nlinear vs nonlinear\ntransfer behavior.",
        20,
        INK,
    )

    # Logistic card
    _add_round_rect(slide, 66, 254, 388, 210, WHITE, "D9D9D1")
    _add_textbox(slide, 92, 274, 300, 28, "Logistic regression", 22, INK, True)
    _add_textbox(slide, 92, 322, 300, 70, "Pr(Y=1|x) = σ(β₀ + xᵀβ)", 19, ACCENT_DARK, True)
    _add_textbox(slide, 92, 398, 290, 30, "Linear additive baseline", 17, MUTED)

    # RF card
    _add_round_rect(slide, 66, 476, 388, 210, WHITE, "D9D9D1")
    _add_textbox(slide, 92, 496, 300, 28, "Random forest", 22, INK, True)
    _add_textbox(slide, 92, 544, 300, 70, "p̂(x) = (1/B) Σ T_b(x)", 19, ACCENT_DARK, True)
    _add_textbox(slide, 92, 622, 304, 40, "Tree ensemble for nonlinear\neffects", 17, MUTED)

    slide.shapes.add_picture(str(data.benchmark_figure_path), _x(510), _y(24), _w(1040), _h(472))

    metrics = [
        (530, "RF pooled PR\nAUC\n0.1486", ACCENT_DARK, WHITE),
        (878, "RF\nrecall@10%\n0.1961", TEAL, WHITE),
        (1226, "Logistic mean\ncity PR AUC\n0.1803", "EFE5D2", INK),
    ]
    for x, text, fill, text_color in metrics:
        _add_round_rect(slide, x, 538, 312, 168, fill)
        _add_textbox(slide, x + 28, 570, 254, 100, text, 23, text_color, True)

    _add_round_rect(slide, 526, 748, 1008, 66, "EBE2D5")
    _add_textbox(
        slide,
        562,
        768,
        930,
        26,
        "Matched sampled all-fold checkpoints; not exhaustive 71M-cell scoring.",
        17,
        MUTED,
    )


def _slide_denver(slide, data: PresentationData) -> None:
    _set_background(slide)
    _add_round_rect(slide, 22, 20, 1556, 724, WHITE, OUTLINE)
    slide.shapes.add_picture(str(data.denver_figure_path), _x(36), _y(40), _w(1528), _h(686))

    _add_round_rect(slide, 38, 772, 1050, 84, SAND)
    _add_textbox(
        slide,
        68,
        794,
        980,
        42,
        "Prediction errors remain spatially structured rather than random.",
        28,
        INK,
        True,
    )
    _add_round_rect(slide, 1130, 780, 414, 70, TEAL)
    _add_textbox(slide, 1160, 802, 350, 28, "RF frontier | hot-arid", 22, WHITE, True, PP_ALIGN.CENTER)


def _slide_takeaway(slide, data: PresentationData) -> None:
    _set_background(slide)
    _add_oval(slide, 1220, -50, 420, 320, ACCENT, 0.88)
    _add_oval(slide, -20, 700, 480, 280, TEAL, 0.94)

    _add_round_rect(slide, 48, 48, 1504, 256, WHITE, OUTLINE)
    _add_textbox(
        slide,
        86,
        92,
        1388,
        170,
        "Yes: cross-city hotspot transfer is\nfeasible, but performance is not yet\nuniform across climates.",
        34,
        INK,
        True,
    )

    cards = [
        (
            48,
            "Best current signal",
            f"RF improves pooled PR\nAUC ({data.rf_frontier.pooled_pr_auc:.4f}) and\nrecall@10% ({data.rf_frontier.pooled_recall_at_top_10pct:.4f}).",
            ACCENT_DARK,
            WHITE,
        ),
        (
            560,
            "Key caveat",
            "The headline\ncomparison is the\nretained sampled\nall-fold benchmark path.",
            TEAL,
            WHITE,
        ),
        (
            1072,
            "Next step",
            "Run broader full scoring\nand diagnose why\ntransfer shifts by\nclimate group.",
            TAKEAWAY,
            INK,
        ),
    ]
    for x, heading, body, fill, heading_color in cards:
        _add_round_rect(slide, x, 382, 480, 350, fill)
        _add_textbox(slide, x + 30, 424, 300, 30, heading, 24, heading_color, True)
        _add_round_rect(slide, x + 24, 502, 432, 184, WHITE if fill == TAKEAWAY else "F8F4EC")
        _add_textbox(slide, x + 44, 528, 384, 130, body, 21, INK)

    _add_textbox(slide, 1290, 820, 220, 34, "Questions?", 23, MUTED, True, PP_ALIGN.CENTER)
