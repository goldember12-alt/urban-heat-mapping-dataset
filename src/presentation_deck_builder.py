from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from matplotlib import font_manager


SLIDE_ASSET_WIDTH = 1600
SLIDE_ASSET_HEIGHT = 760
BACKGROUND = "#f6f1e7"
INK = "#1e2a2f"
MUTED = "#5c696d"
ACCENT = "#d26b34"
ACCENT_DARK = "#9a402d"
TEAL = "#3a7182"
TEAL_DARK = "#254d5a"
SAND = "#e6d3ae"
WHITE = "#fffdfa"
LIGHT = "#ede4d4"
COOL_LIGHT = "#dfe9e8"


@dataclass(frozen=True)
class BenchmarkRun:
    model_family: str
    preset: str
    rows_per_city: str
    pooled_pr_auc: float
    mean_city_pr_auc: float
    pooled_recall_at_top_10pct: float


@dataclass(frozen=True)
class PresentationData:
    city_count: int
    row_count: int
    column_count: int
    target_column: str
    outer_fold_count: int
    held_out_cities_per_fold: int
    logistic_5k: BenchmarkRun
    rf_frontier: BenchmarkRun
    benchmark_figure_path: Path
    denver_figure_path: Path


@dataclass(frozen=True)
class SlideSpec:
    title: str
    image_filename: str


def _repo_path(repo_root: Path, relative_path: str) -> Path:
    return repo_root / Path(relative_path)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_presentation_data(repo_root: Path) -> PresentationData:
    artifact_summary = _load_json(
        _repo_path(repo_root, "data_processed/final/final_dataset_artifact_summary.json")
    )
    audit_summary = _load_json(
        _repo_path(repo_root, "data_processed/modeling/final_dataset_audit_summary.json")
    )
    folds_rows = _load_csv(_repo_path(repo_root, "data_processed/modeling/city_outer_folds.csv"))
    benchmark_rows = _load_csv(
        _repo_path(repo_root, "outputs/modeling/reporting/tables/cross_city_benchmark_report_benchmark_table.csv")
    )

    fold_ids = sorted({int(row["outer_fold"]) for row in folds_rows})
    fold_sizes = {fold_id: 0 for fold_id in fold_ids}
    for row in folds_rows:
        fold_sizes[int(row["outer_fold"])] += 1

    logistic_row = next(
        row
        for row in benchmark_rows
        if row["model_family"] == "logistic_saga" and row["rows_per_city"] == "5000"
    )
    rf_row = next(
        row
        for row in benchmark_rows
        if row["model_family"] == "random_forest" and row["preset"] == "frontier"
    )

    return PresentationData(
        city_count=int(audit_summary["city_count"]),
        row_count=int(artifact_summary["row_count"]),
        column_count=int(artifact_summary["column_count"]),
        target_column=str(audit_summary["target_column"]),
        outer_fold_count=len(fold_ids),
        held_out_cities_per_fold=max(fold_sizes.values()),
        logistic_5k=BenchmarkRun(
            model_family="logistic_saga",
            preset=str(logistic_row["preset"]),
            rows_per_city=str(logistic_row["rows_per_city"]),
            pooled_pr_auc=float(logistic_row["pooled_pr_auc"]),
            mean_city_pr_auc=float(logistic_row["mean_city_pr_auc"]),
            pooled_recall_at_top_10pct=float(logistic_row["pooled_recall_at_top_10pct"]),
        ),
        rf_frontier=BenchmarkRun(
            model_family="random_forest",
            preset=str(rf_row["preset"]),
            rows_per_city=str(rf_row["rows_per_city"]),
            pooled_pr_auc=float(rf_row["pooled_pr_auc"]),
            mean_city_pr_auc=float(rf_row["mean_city_pr_auc"]),
            pooled_recall_at_top_10pct=float(rf_row["pooled_recall_at_top_10pct"]),
        ),
        benchmark_figure_path=_repo_path(
            repo_root, "figures/modeling/reporting/cross_city_benchmark_report_benchmark_metrics.png"
        ),
        denver_figure_path=_repo_path(
            repo_root, "figures/modeling/heldout_city_maps/denver_heldout_map_triptych.png"
        ),
    )


def build_slide_specs() -> list[SlideSpec]:
    return [
        SlideSpec("Cross-City Urban Heat Hotspot Prediction", "slide_01_title_card.png"),
        SlideSpec("Why Transfer Matters", "slide_02_problem_framing.png"),
        SlideSpec("Data + Evaluation Design", "slide_03_design.png"),
        SlideSpec("Models + Main Result", "slide_04_models_results.png"),
        SlideSpec("Held-Out Denver", "slide_05_denver_example.png"),
        SlideSpec("Takeaway", "slide_06_takeaway.png"),
    ]


def build_presentation_assets(repo_root: Path, output_dir: Path) -> list[Path]:
    data = load_presentation_data(repo_root)
    output_dir.mkdir(parents=True, exist_ok=True)

    slide_builders = [
        ("slide_01_title_card.png", lambda: _build_title_slide(data)),
        ("slide_02_problem_framing.png", lambda: _build_problem_slide(data)),
        ("slide_03_design.png", lambda: _build_design_slide(data)),
        ("slide_04_models_results.png", lambda: _build_models_results_slide(data)),
        ("slide_05_denver_example.png", lambda: _build_denver_slide(data)),
        ("slide_06_takeaway.png", lambda: _build_takeaway_slide(data)),
    ]

    written_paths: list[Path] = []
    for filename, builder in slide_builders:
        image = builder().convert("RGB")
        output_path = output_dir / filename
        image.save(output_path, format="PNG")
        written_paths.append(output_path)

    manifest_path = output_dir / "slide_manifest.json"
    manifest = {
        "slide_count": len(slide_builders),
        "slides": [
            {"title": slide.title, "image_filename": slide.image_filename}
            for slide in build_slide_specs()
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    written_paths.append(manifest_path)
    return written_paths


def _build_title_slide(data: PresentationData) -> Image.Image:
    image = _base_canvas()
    draw = ImageDraw.Draw(image)

    _draw_vertical_glow(image, (1080, -40), 520, "#e9976d33")
    _draw_vertical_glow(image, (1330, 240), 340, "#4e879433")
    _draw_vertical_glow(image, (310, 540), 260, "#efd9b033")

    kicker_font = _font(34, bold=True)
    hero_font = _font(70, bold=True)
    sub_font = _font(36)
    footer_font = _font(26)
    stat_font = _font(28, bold=True)

    draw.rounded_rectangle((72, 78, 420, 132), radius=18, fill=ACCENT)
    draw.text((102, 92), "Held-out-city transfer", font=kicker_font, fill=WHITE)

    hero_text = "30 cities | 71.4M cells | hotspot screening on unseen cities"
    _draw_wrapped(draw, hero_text, (80, 184), 900, hero_font, INK, line_spacing=18)
    _draw_wrapped(
        draw,
        "A presentation-first view of the urban heat transfer benchmark.",
        (86, 390),
        760,
        sub_font,
        MUTED,
        line_spacing=10,
    )

    draw.rounded_rectangle((980, 140, 1490, 600), radius=28, fill="#fff8ef")
    draw.rounded_rectangle((1020, 184, 1450, 258), radius=20, fill=TEAL)
    draw.text((1060, 204), "What the talk shows", font=_font(32, bold=True), fill=WHITE)

    bullets = [
        "why cross-city transfer is the real test",
        "how 30-city evaluation stays leakage-safe",
        "where RF helps and where uncertainty remains",
    ]
    y = 302
    for bullet in bullets:
        draw.ellipse((1040, y + 8, 1058, y + 26), fill=ACCENT)
        _draw_wrapped(draw, bullet, (1082, y), 320, stat_font, INK, line_spacing=8)
        y += 92

    draw.rounded_rectangle((80, 630, 1490, 694), radius=22, fill="#ebe0cf")
    footer = "Max Clements   |   STAT 5630 Final Project   |   April 2026"
    draw.text((110, 648), footer, font=footer_font, fill=TEAL_DARK)
    return image


def _build_problem_slide(data: PresentationData) -> Image.Image:
    del data
    image = _base_canvas()
    draw = ImageDraw.Draw(image)
    _draw_vertical_glow(image, (1270, 96), 280, "#d26b3422")
    _draw_vertical_glow(image, (170, 580), 220, "#3a718222")

    card_specs = [
        ("Heat risk matters", "public health + planning"),
        ("Cities differ", "climate, land cover, water, vegetation"),
        ("Random row splits mislead", "same-city leakage looks easier than transfer"),
    ]
    x_positions = [80, 555, 1030]
    for x, (headline, subline) in zip(x_positions, card_specs):
        draw.rounded_rectangle((x, 66, x + 410, 186), radius=24, fill="#fffaf2", outline="#dfc7a4", width=2)
        draw.text((x + 26, 90), headline, font=_font(32, bold=True), fill=INK)
        _draw_wrapped(draw, subline, (x + 26, 130), 355, _font(24), MUTED)

    draw.rounded_rectangle((110, 248, 1490, 520), radius=38, fill=WHITE, outline="#d7c2a0", width=3)
    draw.rounded_rectangle((158, 292, 438, 346), radius=18, fill=ACCENT_DARK)
    draw.text((190, 304), "Core question", font=_font(30, bold=True), fill=WHITE)
    question = "Can a model trained on some cities find heat hotspots in a city it has never seen?"
    _draw_wrapped(draw, question, (170, 380), 1250, _font(54, bold=True), INK, line_spacing=16)

    draw.rounded_rectangle((240, 582, 1360, 676), radius=28, fill="#dfe8e8")
    caption = "This is a transfer benchmark, not same-city interpolation."
    w = _text_bbox(draw, caption, _font(34, bold=True))[2]
    draw.text(((1600 - w) / 2, 612), caption, font=_font(34, bold=True), fill=TEAL_DARK)
    return image


def _build_design_slide(data: PresentationData) -> Image.Image:
    image = _base_canvas()
    draw = ImageDraw.Draw(image)
    _draw_vertical_glow(image, (1340, 638), 210, "#3a71821e")

    stat_cards = [
        (f"{data.city_count}", "cities"),
        (f"{data.row_count:,}", "rows"),
        ("30 m", "grid cell"),
        (data.target_column, "target"),
    ]
    x = 76
    for value, label in stat_cards:
        draw.rounded_rectangle((x, 60, x + 290, 220), radius=26, fill="#fffaf2", outline="#dbc7aa", width=2)
        draw.text((x + 28, 92), value, font=_font(48, bold=True), fill=INK)
        draw.text((x + 28, 156), label, font=_font(28), fill=MUTED)
        x += 312

    draw.rounded_rectangle((1330, 60, 1524, 220), radius=26, fill=ACCENT)
    draw.text((1370, 92), f"{data.outer_fold_count}", font=_font(48, bold=True), fill=WHITE)
    draw.text((1360, 156), "outer folds", font=_font(28), fill=WHITE)

    draw.rounded_rectangle((76, 278, 940, 682), radius=30, fill=WHITE, outline="#d8c6ab", width=2)
    draw.rounded_rectangle((106, 312, 360, 370), radius=20, fill=TEAL)
    draw.text((136, 326), "Analytic unit", font=_font(30, bold=True), fill=WHITE)
    _draw_wrapped(
        draw,
        "One row = one 30 m cell in one city. Predictors summarize built form, terrain, water, vegetation, and climate context.",
        (110, 406),
        786,
        _font(31),
        INK,
        line_spacing=12,
    )

    draw.rounded_rectangle((1000, 278, 1524, 682), radius=30, fill="#fffaf2", outline="#d8c6ab", width=2)
    draw.rounded_rectangle((1040, 312, 1484, 370), radius=20, fill=ACCENT_DARK)
    draw.text((1080, 326), "Leakage-safe benchmark", font=_font(30, bold=True), fill=WHITE)
    _draw_wrapped(
        draw,
        f"{data.held_out_cities_per_fold} held-out cities per fold. Preprocessing, tuning, and model fitting use training-city rows only.",
        (1040, 408),
        404,
        _font(29),
        INK,
        line_spacing=12,
    )

    pipeline_y = 548
    pipeline_boxes = [
        ("Assemble features", TEAL),
        ("Train on 24 cities", "#7f9776"),
        ("Tune on train only", ACCENT),
        ("Score 6 unseen cities", ACCENT_DARK),
    ]
    x = 116
    for index, (label, fill) in enumerate(pipeline_boxes):
        box_w = 190 if index == 0 else 220 if index == 3 else 210
        draw.rounded_rectangle((x, pipeline_y, x + box_w, pipeline_y + 94), radius=22, fill=fill)
        _draw_wrapped(draw, label, (x + 18, pipeline_y + 14), box_w - 36, _font(22, bold=True), WHITE)
        if index < len(pipeline_boxes) - 1:
            _draw_arrow(draw, (x + box_w + 18, pipeline_y + 47), (x + box_w + 64, pipeline_y + 47), fill=MUTED, width=10)
        x += box_w + 82

    return image


def _build_models_results_slide(data: PresentationData) -> Image.Image:
    image = _base_canvas()
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((44, 46, 496, 710), radius=30, fill="#fffaf2", outline="#d8c5a7", width=2)
    draw.rounded_rectangle((78, 84, 464, 132), radius=18, fill=TEAL)
    draw.text((114, 94), "Same predictor contract", font=_font(24, bold=True), fill=WHITE)
    _draw_wrapped(
        draw,
        "Inputs exclude LST itself. The comparison isolates linear vs nonlinear transfer behavior.",
        (78, 160),
        372,
        _font(24),
        INK,
        line_spacing=10,
    )

    model_cards = [
        ("Logistic regression", "Pr(Y=1|x) = σ(β₀ + xᵀβ)", "Linear additive baseline"),
        ("Random forest", "p̂(x) = (1/B) Σ T_b(x)", "Tree ensemble for nonlinear effects"),
    ]
    y = 284
    for title, equation, interpretation in model_cards:
        draw.rounded_rectangle((78, y, 462, y + 168), radius=24, fill=WHITE, outline="#d9d9d1", width=2)
        draw.text((102, y + 22), title, font=_font(27, bold=True), fill=INK)
        draw.text((102, y + 70), equation, font=_font(25, bold=True), fill=ACCENT_DARK)
        _draw_wrapped(draw, interpretation, (102, y + 112), 326, _font(22), MUTED)
        y += 186

    benchmark = Image.open(data.benchmark_figure_path).convert("RGB")
    benchmark = ImageOps.contain(benchmark, (1008, 430))
    image.paste(benchmark, (536, 48))

    metrics = [
        (f"RF pooled PR AUC\n{data.rf_frontier.pooled_pr_auc:.4f}", ACCENT_DARK, WHITE),
        (f"RF recall@10%\n{data.rf_frontier.pooled_recall_at_top_10pct:.4f}", TEAL, WHITE),
        (f"Logistic mean city PR AUC\n{data.logistic_5k.mean_city_pr_auc:.4f}", "#efe5d2", INK),
    ]
    x_positions = [560, 888, 1216]
    for (text, fill, text_fill), x in zip(metrics, x_positions):
        draw.rounded_rectangle((x, 510, x + 272, 636), radius=24, fill=fill)
        _draw_wrapped(draw, text, (x + 24, 540), 224, _font(27, bold=True), text_fill, line_spacing=8)

    caveat = "Matched sampled all-fold checkpoints; not exhaustive 71M-cell scoring."
    draw.rounded_rectangle((556, 670, 1478, 720), radius=18, fill="#ebe2d5")
    draw.text((590, 686), caveat, font=_font(22), fill=MUTED)
    return image


def _build_denver_slide(data: PresentationData) -> Image.Image:
    image = _base_canvas()
    draw = ImageDraw.Draw(image)

    frame = (58, 48, 1542, 630)
    draw.rounded_rectangle(frame, radius=30, fill=WHITE, outline="#d8c6ab", width=2)
    denver = Image.open(data.denver_figure_path).convert("RGB")
    denver = ImageOps.contain(denver, (1460, 548))
    image.paste(denver, (70, 64))

    draw.rounded_rectangle((1180, 648, 1514, 704), radius=18, fill=TEAL)
    draw.text((1214, 664), "RF frontier | hot-arid", font=_font(24, bold=True), fill=WHITE)

    draw.rounded_rectangle((82, 648, 1120, 714), radius=22, fill="#f0e4d4")
    caption = "Prediction errors remain spatially structured rather than random."
    _draw_wrapped(draw, caption, (112, 664), 950, _font(30, bold=True), INK)
    return image


def _build_takeaway_slide(data: PresentationData) -> Image.Image:
    image = _base_canvas()
    draw = ImageDraw.Draw(image)
    _draw_vertical_glow(image, (1340, 120), 260, "#d26b3433")
    _draw_vertical_glow(image, (260, 620), 220, "#3a718222")

    draw.rounded_rectangle((76, 76, 1524, 290), radius=36, fill=WHITE, outline="#d8c6ab", width=2)
    takeaway = "Yes: cross-city hotspot transfer is feasible, but performance is not yet uniform across climates."
    _draw_wrapped(draw, takeaway, (116, 128), 1310, _font(54, bold=True), INK, line_spacing=16)

    items = [
        (
            "Best current signal",
            f"RF improves pooled PR AUC ({data.rf_frontier.pooled_pr_auc:.4f}) and recall@10% ({data.rf_frontier.pooled_recall_at_top_10pct:.4f}).",
            ACCENT_DARK,
        ),
        (
            "Key caveat",
            "The headline comparison is the retained sampled all-fold benchmark path.",
            TEAL,
        ),
        (
            "Next step",
            "Run broader full scoring and diagnose why transfer shifts by climate group.",
            "#e8dcc7",
        ),
    ]

    x = 76
    for heading, body, fill in items:
        text_fill = WHITE if fill in {ACCENT_DARK, TEAL} else INK
        body_fill = "#f8f4ec" if text_fill == WHITE else WHITE
        draw.rounded_rectangle((x, 360, x + 444, 632), radius=28, fill=fill)
        draw.text((x + 28, 392), heading, font=_font(30, bold=True), fill=text_fill)
        draw.rounded_rectangle((x + 22, 448, x + 422, 602), radius=22, fill=body_fill)
        _draw_wrapped(draw, body, (x + 44, 476), 352, _font(27), INK, line_spacing=10)
        x += 474

    draw.text((1310, 684), "Questions?", font=_font(28, bold=True), fill=MUTED)
    return image


def _base_canvas() -> Image.Image:
    image = Image.new("RGBA", (SLIDE_ASSET_WIDTH, SLIDE_ASSET_HEIGHT), BACKGROUND)
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    for y in range(SLIDE_ASSET_HEIGHT):
        alpha = int(28 * (1 - y / SLIDE_ASSET_HEIGHT))
        overlay_draw.line((0, y, SLIDE_ASSET_WIDTH, y), fill=(255, 255, 255, alpha), width=1)
    image = Image.alpha_composite(image, overlay)
    return image


def _draw_vertical_glow(image: Image.Image, center: tuple[int, int], radius: int, fill: str) -> None:
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    x, y = center
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill)
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=42))
    image.alpha_composite(overlay)


def _draw_arrow(
    draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], fill: str, width: int
) -> None:
    draw.line((start, end), fill=fill, width=width)
    head = 14
    draw.polygon(
        [
            (end[0], end[1]),
            (end[0] - head * 2, end[1] - head),
            (end[0] - head * 2, end[1] + head),
        ],
        fill=fill,
    )


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    if bold:
        prop = font_manager.FontProperties(family="DejaVu Sans", weight="bold")
    else:
        prop = font_manager.FontProperties(family="DejaVu Sans")
    return ImageFont.truetype(font_manager.findfont(prop), size)


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
    lines: list[str] = []
    for paragraph in text.splitlines():
        if not paragraph:
            lines.append("")
            continue
        words = paragraph.split()
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if _text_bbox(draw, candidate, font)[2] <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return "\n".join(lines)


def _draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    position: tuple[int, int],
    max_width: int,
    font: ImageFont.FreeTypeFont,
    fill: str,
    line_spacing: int = 6,
) -> None:
    wrapped = _wrap_text(draw, text, font, max_width)
    draw.multiline_text(position, wrapped, font=font, fill=fill, spacing=line_spacing)


def _text_bbox(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont
) -> tuple[int, int, int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return (box[0], box[1], box[2] - box[0], box[3] - box[1])
