from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

from src.presentation_deck_builder import PresentationData


BACKGROUND = "#f6f1e7"
INK = "#1e2a2f"
MUTED = "#5c696d"
ACCENT = "#d26b34"
ACCENT_DARK = "#9a402d"
TEAL = "#3a7182"
TEAL_DARK = "#254d5a"
WHITE = "#fffdfa"
PANEL = "#fffaf2"
OUTLINE = "#dbc7aa"
GREEN = "#8aa07a"
COOL = "#dfe8e8"

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans"],
        "axes.unicode_minus": False,
    }
)


@dataclass(frozen=True)
class PresentationVisualAssets:
    predictors_schematic_png: Path
    predictors_schematic_svg: Path
    evaluation_questions_png: Path
    evaluation_questions_svg: Path
    within_city_results_png: Path
    within_city_results_svg: Path
    transfer_results_png: Path
    transfer_results_svg: Path
    contrast_takeaway_png: Path
    contrast_takeaway_svg: Path


def build_presentation_visual_assets(
    repo_root: Path, data: PresentationData
) -> PresentationVisualAssets:
    output_dir = repo_root / "figures" / "presentation"
    output_dir.mkdir(parents=True, exist_ok=True)

    predictors_png = output_dir / "research_question_predictors.png"
    predictors_svg = output_dir / "research_question_predictors.svg"
    evaluation_png = output_dir / "two_evaluation_questions.png"
    evaluation_svg = output_dir / "two_evaluation_questions.svg"
    within_png = output_dir / "within_city_hotspot_results.png"
    within_svg = output_dir / "within_city_hotspot_results.svg"
    transfer_png = output_dir / "city_heldout_transfer_results.png"
    transfer_svg = output_dir / "city_heldout_transfer_results.svg"
    contrast_png = output_dir / "evaluation_contrast_takeaway.png"
    contrast_svg = output_dir / "evaluation_contrast_takeaway.svg"

    _build_predictors_schematic(predictors_png, predictors_svg, data)
    _build_evaluation_questions(evaluation_png, evaluation_svg, data)
    _build_within_city_results(within_png, within_svg, data)
    _build_transfer_results(transfer_png, transfer_svg, data)
    _build_contrast_takeaway(contrast_png, contrast_svg, data)

    return PresentationVisualAssets(
        predictors_schematic_png=predictors_png,
        predictors_schematic_svg=predictors_svg,
        evaluation_questions_png=evaluation_png,
        evaluation_questions_svg=evaluation_svg,
        within_city_results_png=within_png,
        within_city_results_svg=within_svg,
        transfer_results_png=transfer_png,
        transfer_results_svg=transfer_svg,
        contrast_takeaway_png=contrast_png,
        contrast_takeaway_svg=contrast_svg,
    )


def _save_figure(fig, png_path: Path, svg_path: Path) -> None:
    fig.savefig(svg_path, bbox_inches="tight", transparent=True)
    fig.savefig(png_path, bbox_inches="tight", transparent=True, dpi=240)
    plt.close(fig)


def _panel(
    ax,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    fill: str = WHITE,
    edge: str = OUTLINE,
    radius: float = 0.035,
) -> FancyBboxPatch:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.018,rounding_size={radius}",
        facecolor=fill,
        edgecolor=edge,
        linewidth=1.6,
    )
    ax.add_patch(patch)
    return patch


def _chip(ax, x: float, y: float, w: float, h: float, label: str, color: str) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.014,rounding_size=0.025",
            facecolor=color,
            edgecolor="none",
        )
    )
    ax.text(
        x + w / 2,
        y + h / 2,
        label,
        fontsize=12.0,
        fontweight="bold",
        color=WHITE,
        ha="center",
        va="center",
    )


def _city_grid(ax, x: float, y: float, w: float, h: float, *, train_color: str, test_color: str) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.012,rounding_size=0.022",
            facecolor=PANEL,
            edgecolor=OUTLINE,
            linewidth=1.0,
        )
    )
    columns = 5
    rows = 4
    for row in range(rows):
        for col in range(columns):
            color = test_color if (row + col) % 4 == 0 else train_color
            ax.add_patch(
                Circle(
                    (x + 0.035 + col * (w - 0.07) / (columns - 1), y + 0.035 + row * (h - 0.07) / (rows - 1)),
                    0.008,
                    facecolor=color,
                    edgecolor="none",
                    alpha=0.92,
                )
            )


def _build_predictors_schematic(png_path: Path, svg_path: Path, data: PresentationData) -> None:
    fig, ax = plt.subplots(figsize=(11.8, 4.8), dpi=240)
    fig.patch.set_alpha(0)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    _panel(ax, 0.02, 0.08, 0.96, 0.84)
    ax.text(0.055, 0.84, "Research question", fontsize=18, fontweight="bold", color=INK)
    ax.text(
        0.055,
        0.74,
        "Can models predict urban heat hotspot cells from basic environmental and built-environment factors?",
        fontsize=15.0,
        color=INK,
        wrap=True,
    )

    predictors = [
        ("Imperviousness", TEAL),
        ("Land cover", GREEN),
        ("Elevation", ACCENT),
        ("Distance to water", TEAL_DARK),
        ("NDVI", GREEN),
        ("Climate group", ACCENT_DARK),
    ]
    chip_positions = [(0.06, 0.50), (0.25, 0.50), (0.44, 0.50), (0.06, 0.35), (0.25, 0.35), (0.44, 0.35)]
    for (label, color), (x, y) in zip(predictors, chip_positions):
        _chip(ax, x, y, 0.15, 0.09, label, color)

    ax.add_patch(
        FancyArrowPatch(
            (0.62, 0.45),
            (0.73, 0.45),
            arrowstyle="-|>",
            mutation_scale=22,
            linewidth=2.2,
            color=MUTED,
        )
    )
    _panel(ax, 0.75, 0.29, 0.18, 0.30, fill=COOL, edge=TEAL)
    ax.text(0.84, 0.49, data.target_column, fontsize=17.0, fontweight="bold", color=TEAL_DARK, ha="center")
    ax.text(0.84, 0.40, "hottest 10% of cells\nwithin each city", fontsize=11.2, color=MUTED, ha="center")

    ax.text(
        0.50,
        0.15,
        f"One row is one 30 m cell. The current modeling handoff covers {data.city_count} cities and {data.row_count / 1_000_000:.1f}M filtered cells.",
        fontsize=11.6,
        color=MUTED,
        ha="center",
    )

    _save_figure(fig, png_path, svg_path)


def _build_evaluation_questions(png_path: Path, svg_path: Path, data: PresentationData) -> None:
    fig, ax = plt.subplots(figsize=(11.8, 4.9), dpi=240)
    fig.patch.set_alpha(0)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    _panel(ax, 0.03, 0.08, 0.44, 0.84, fill=WHITE, edge=TEAL)
    _panel(ax, 0.53, 0.08, 0.44, 0.84, fill=WHITE, edge=ACCENT_DARK)

    ax.text(0.07, 0.84, "Within-city held-out cells", fontsize=17.0, fontweight="bold", color=TEAL_DARK)
    ax.text(0.07, 0.77, "Cities are represented during training.", fontsize=11.8, color=MUTED)
    for idx, (x, y) in enumerate([(0.08, 0.56), (0.25, 0.56), (0.08, 0.39), (0.25, 0.39)]):
        _city_grid(ax, x, y, 0.13, 0.12, train_color=TEAL, test_color=ACCENT)
        ax.text(x + 0.065, y - 0.035, f"city {idx + 1}", fontsize=9.5, color=MUTED, ha="center")
    ax.add_patch(Circle((0.09, 0.25), 0.010, facecolor=TEAL, edgecolor="none"))
    ax.text(0.11, 0.25, "training cells", fontsize=10.5, color=TEAL_DARK, va="center")
    ax.add_patch(Circle((0.25, 0.25), 0.010, facecolor=ACCENT, edgecolor="none"))
    ax.text(0.27, 0.25, "held-out cells", fontsize=10.5, color=ACCENT_DARK, va="center")
    ax.text(
        0.25,
        0.15,
        "Question: can the model identify hotspot structure where local city patterns are already represented?",
        fontsize=11.0,
        color=INK,
        ha="center",
        wrap=True,
    )

    ax.text(0.57, 0.84, "City-held-out transfer", fontsize=17.0, fontweight="bold", color=ACCENT_DARK)
    ax.text(
        0.57,
        0.77,
        f"{data.outer_fold_count} folds; {data.held_out_cities_per_fold} cities held out per fold.",
        fontsize=11.8,
        color=MUTED,
    )
    for idx, (x, y) in enumerate([(0.58, 0.56), (0.72, 0.56), (0.58, 0.39)]):
        _city_grid(ax, x, y, 0.11, 0.12, train_color=TEAL, test_color=TEAL)
        ax.text(x + 0.055, y - 0.035, f"seen {idx + 1}", fontsize=9.5, color=MUTED, ha="center")
    ax.add_patch(
        FancyArrowPatch(
            (0.76, 0.44),
            (0.84, 0.44),
            arrowstyle="-|>",
            mutation_scale=18,
            linewidth=1.8,
            color=MUTED,
        )
    )
    _city_grid(ax, 0.84, 0.40, 0.10, 0.16, train_color=ACCENT, test_color=ACCENT)
    ax.text(0.89, 0.36, "new city", fontsize=9.8, color=ACCENT_DARK, ha="center")
    ax.text(
        0.75,
        0.15,
        "Question: can the model generalize to places it has not seen?",
        fontsize=11.0,
        color=INK,
        ha="center",
        wrap=True,
    )

    _save_figure(fig, png_path, svg_path)


def _apply_plot_style(ax) -> None:
    ax.set_facecolor(WHITE)
    ax.grid(axis="x", color=OUTLINE, linewidth=0.8, alpha=0.7)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(OUTLINE)
    ax.tick_params(axis="x", labelsize=12, colors=MUTED)
    ax.tick_params(axis="y", labelsize=14, colors=INK, length=0)


def _build_within_city_results(png_path: Path, svg_path: Path, data: PresentationData) -> None:
    metrics = [
        ("Hotspot precision", data.partner_logistic.class_1_precision_mean, data.partner_rf.class_1_precision_mean),
        ("Hotspot recall", data.partner_logistic.class_1_recall_mean, data.partner_rf.class_1_recall_mean),
        ("Hotspot F1", data.partner_logistic.class_1_f1_mean, data.partner_rf.class_1_f1_mean),
    ]

    fig, ax = plt.subplots(figsize=(10.5, 4.9), dpi=240)
    fig.patch.set_alpha(0)
    _apply_plot_style(ax)

    y_positions = [2.0, 1.0, 0.0]
    bar_h = 0.28
    for y, (_label, logistic, rf) in zip(y_positions, metrics):
        ax.barh(y + bar_h / 2, logistic, height=bar_h, color=TEAL, alpha=0.92)
        ax.barh(y - bar_h / 2, rf, height=bar_h, color=ACCENT_DARK, alpha=0.92)
        ax.text(logistic + 0.018, y + bar_h / 2, f"{logistic:.3f}", fontsize=11.5, color=TEAL_DARK, va="center")
        ax.text(rf + 0.018, y - bar_h / 2, f"{rf:.3f}", fontsize=11.5, color=ACCENT_DARK, va="center")

    ax.set_xlim(0, 0.82)
    ax.set_ylim(-0.75, 2.75)
    ax.set_yticks(y_positions, [row[0] for row in metrics])
    ax.set_xlabel("Mean thresholded hotspot-class metric across 30 cities", fontsize=12.4, color=MUTED)
    ax.set_title("Within-city held-out evaluation", loc="left", fontsize=18, fontweight="bold", color=INK, pad=12)
    ax.text(
        0.0,
        2.58,
        f"Support counts appear consistent with about {data.partner_support_fraction_mean:.0%} of cells held out per city.",
        fontsize=11.4,
        color=MUTED,
    )
    ax.legend(
        handles=[
            Line2D([0], [0], marker="s", color="none", markerfacecolor=TEAL, markersize=10, label="logistic"),
            Line2D([0], [0], marker="s", color="none", markerfacecolor=ACCENT_DARK, markersize=10, label="random forest"),
        ],
        loc="lower right",
        frameon=False,
        fontsize=12.0,
        ncol=2,
    )

    _save_figure(fig, png_path, svg_path)


def _build_transfer_results(png_path: Path, svg_path: Path, data: PresentationData) -> None:
    metrics = [
        ("Pooled PR AUC", data.logistic_5k.pooled_pr_auc, data.rf_frontier.pooled_pr_auc),
        ("Mean city PR AUC", data.logistic_5k.mean_city_pr_auc, data.rf_frontier.mean_city_pr_auc),
        ("Recall @ top 10%", data.logistic_5k.pooled_recall_at_top_10pct, data.rf_frontier.pooled_recall_at_top_10pct),
    ]

    fig, ax = plt.subplots(figsize=(10.5, 4.9), dpi=240)
    fig.patch.set_alpha(0)
    _apply_plot_style(ax)

    y_positions = [2.2, 1.1, 0.0]
    x_min = 0.138
    x_max = 0.202

    for y, (_label, logistic, rf) in zip(y_positions, metrics):
        low = min(logistic, rf)
        high = max(logistic, rf)
        ax.hlines(y, low, high, color=OUTLINE, linewidth=3.0, zorder=1)
        ax.scatter(logistic, y, s=150, color=TEAL, edgecolors=WHITE, linewidths=1.0, zorder=3)
        ax.scatter(rf, y, s=150, color=ACCENT_DARK, edgecolors=WHITE, linewidths=1.0, zorder=3)
        ax.text(logistic, y + 0.22, f"{logistic:.4f}", fontsize=11.4, color=TEAL_DARK, ha="center")
        ax.text(rf, y - 0.27, f"{rf:.4f}", fontsize=11.4, color=ACCENT_DARK, ha="center")

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(-0.9, 2.8)
    ax.set_yticks(y_positions, [row[0] for row in metrics])
    ax.set_xticks([0.14, 0.16, 0.18, 0.20])
    ax.set_xlabel("Held-out-city benchmark score", fontsize=12.4, color=MUTED)
    ax.set_title("City-held-out transfer evaluation", loc="left", fontsize=18, fontweight="bold", color=INK, pad=12)
    ax.text(
        0.138,
        2.62,
        "RF improves pooled retrieval; logistic remains competitive on mean city PR AUC.",
        fontsize=11.4,
        color=MUTED,
    )
    ax.legend(
        handles=[
            Line2D([0], [0], marker="o", color="none", markerfacecolor=TEAL, markeredgecolor=WHITE, markersize=10, label="logistic 5k"),
            Line2D([0], [0], marker="o", color="none", markerfacecolor=ACCENT_DARK, markeredgecolor=WHITE, markersize=10, label="RF frontier"),
        ],
        loc="lower left",
        frameon=False,
        fontsize=12.0,
        ncol=2,
    )

    _save_figure(fig, png_path, svg_path)


def _metric_box(ax, x: float, y: float, w: float, h: float, value: str, label: str, color: str) -> None:
    _panel(ax, x, y, w, h, fill=PANEL, edge=color, radius=0.025)
    ax.text(x + w / 2, y + h * 0.58, value, fontsize=22.0, fontweight="bold", color=color, ha="center")
    ax.text(x + w / 2, y + h * 0.25, label, fontsize=10.2, color=MUTED, ha="center")


def _build_contrast_takeaway(png_path: Path, svg_path: Path, data: PresentationData) -> None:
    fig, ax = plt.subplots(figsize=(11.8, 4.85), dpi=240)
    fig.patch.set_alpha(0)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    _panel(ax, 0.03, 0.17, 0.43, 0.70, fill=WHITE, edge=TEAL)
    _panel(ax, 0.54, 0.17, 0.43, 0.70, fill=WHITE, edge=ACCENT_DARK)

    ax.text(0.07, 0.78, "Within cities represented in training", fontsize=15.8, fontweight="bold", color=TEAL_DARK)
    ax.text(0.07, 0.70, "Local spatial structure is available to learn from.", fontsize=11.5, color=MUTED)
    _metric_box(ax, 0.08, 0.48, 0.15, 0.14, f"{data.partner_rf.class_1_recall_mean:.3f}", "RF hotspot recall", ACCENT_DARK)
    _metric_box(ax, 0.27, 0.48, 0.15, 0.14, f"{data.partner_rf.class_1_f1_mean:.3f}", "RF hotspot F1", ACCENT_DARK)
    ax.text(
        0.245,
        0.31,
        "Interpretation: strong learnable hotspot signal under a within-city held-out question.",
        fontsize=12.4,
        color=INK,
        ha="center",
        wrap=True,
    )

    ax.text(0.58, 0.78, "Entire cities held out", fontsize=15.8, fontweight="bold", color=ACCENT_DARK)
    ax.text(0.58, 0.70, "The model must transfer across climate and urban form.", fontsize=11.5, color=MUTED)
    _metric_box(ax, 0.59, 0.48, 0.15, 0.14, f"{data.rf_frontier.pooled_pr_auc:.3f}", "RF pooled PR AUC", ACCENT_DARK)
    _metric_box(ax, 0.78, 0.48, 0.15, 0.14, f"{data.rf_frontier.pooled_recall_at_top_10pct:.3f}", "RF recall @ top 10%", ACCENT_DARK)
    ax.text(
        0.755,
        0.31,
        "Interpretation: transfer remains possible, but gains are smaller and more uneven.",
        fontsize=12.4,
        color=INK,
        ha="center",
        wrap=True,
    )

    ax.add_patch(
        FancyArrowPatch(
            (0.47, 0.52),
            (0.53, 0.52),
            arrowstyle="-|>",
            mutation_scale=20,
            linewidth=2.0,
            color=MUTED,
        )
    )
    ax.text(0.50, 0.59, "harder question", fontsize=10.8, color=MUTED, ha="center")
    _panel(ax, 0.10, 0.03, 0.80, 0.08, fill=COOL, edge=TEAL)
    ax.text(
        0.50,
        0.07,
        "Evaluation must match the intended use case: same-city screening and new-city transfer are both useful, but they answer different questions.",
        fontsize=11.4,
        color=TEAL_DARK,
        ha="center",
        va="center",
    )

    _save_figure(fig, png_path, svg_path)
