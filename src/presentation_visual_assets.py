from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle

from src.presentation_deck_builder import PresentationData


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
NDVI_GREEN = "#6f985f"
COOL = "#dfe8e8"

CLIMATE_COLORS = {
    "hot_arid": ACCENT_DARK,
    "hot_humid": TEAL,
    "mild_cool": GREEN,
}
CLIMATE_LABELS = {
    "hot_arid": "Hot-arid",
    "hot_humid": "Hot-humid",
    "mild_cool": "Mild-cool",
}

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans"],
        "axes.unicode_minus": False,
    }
)


@dataclass(frozen=True)
class PresentationVisualAssets:
    setup_schematic_png: Path
    setup_schematic_svg: Path
    model_math_png: Path
    model_math_svg: Path
    side_by_side_results_png: Path
    side_by_side_results_svg: Path
    city_signal_transfer_png: Path
    city_signal_transfer_svg: Path
    comparison_table_png: Path
    comparison_table_svg: Path
    heldout_map_png: Path
    heldout_map_svg: Path


def build_presentation_visual_assets(
    repo_root: Path, data: PresentationData
) -> PresentationVisualAssets:
    output_dir = repo_root / "figures" / "presentation"
    output_dir.mkdir(parents=True, exist_ok=True)

    setup_png = output_dir / "setup_predictors_evaluation_questions.png"
    setup_svg = output_dir / "setup_predictors_evaluation_questions.svg"
    math_png = output_dir / "logistic_rf_model_math.png"
    math_svg = output_dir / "logistic_rf_model_math.svg"
    side_png = output_dir / "within_city_vs_transfer_results.png"
    side_svg = output_dir / "within_city_vs_transfer_results.svg"
    city_png = output_dir / "city_signal_transfer_relationship.png"
    city_svg = output_dir / "city_signal_transfer_relationship.svg"
    table_png = output_dir / "evaluation_metric_comparison_table.png"
    table_svg = output_dir / "evaluation_metric_comparison_table.svg"
    map_png = output_dir / "heldout_denver_map_focus.png"
    map_svg = output_dir / "heldout_denver_map_focus.svg"

    comparison_df = pd.read_csv(
        repo_root
        / "outputs"
        / "modeling"
        / "partner_data"
        / "per_city_logistic_rf_results"
        / "tables"
        / "partner_vs_repo_city_comparison.csv"
    )

    _build_setup_schematic(setup_png, setup_svg, data)
    _build_model_math(math_png, math_svg)
    _build_side_by_side_results(side_png, side_svg, data)
    _build_city_signal_transfer(city_png, city_svg, comparison_df)
    _build_comparison_table(table_png, table_svg, data)
    _build_heldout_map_focus(map_png, map_svg, repo_root)

    return PresentationVisualAssets(
        setup_schematic_png=setup_png,
        setup_schematic_svg=setup_svg,
        model_math_png=math_png,
        model_math_svg=math_svg,
        side_by_side_results_png=side_png,
        side_by_side_results_svg=side_svg,
        city_signal_transfer_png=city_png,
        city_signal_transfer_svg=city_svg,
        comparison_table_png=table_png,
        comparison_table_svg=table_svg,
        heldout_map_png=map_png,
        heldout_map_svg=map_svg,
    )


def _save_figure(fig, png_path: Path, svg_path: Path) -> None:
    fig.savefig(svg_path, bbox_inches="tight", pad_inches=0.04, transparent=True)
    fig.savefig(png_path, bbox_inches="tight", pad_inches=0.04, transparent=True, dpi=240)
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
    radius: float = 0.030,
    linewidth: float = 1.4,
) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle=f"round,pad=0.014,rounding_size={radius}",
            facecolor=fill,
            edgecolor=edge,
            linewidth=linewidth,
        )
    )


def _chip(ax, x: float, y: float, w: float, h: float, label: str, color: str) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.010,rounding_size=0.020",
            facecolor=color,
            edgecolor="none",
        )
    )
    ax.text(
        x + w / 2,
        y + h / 2,
        label,
        fontsize=10.8,
        fontweight="bold",
        color=WHITE,
        ha="center",
        va="center",
    )


def _city_strip(
    ax,
    x: float,
    y: float,
    *,
    n_cities: int,
    held_out: set[int] | None,
    width: float,
    dot_size: float = 0.0065,
) -> None:
    held_out = held_out or set()
    step = width / max(n_cities - 1, 1)
    for city_idx in range(n_cities):
        color = ACCENT if city_idx in held_out else TEAL
        ax.add_patch(
            Circle(
                (x + city_idx * step, y),
                dot_size,
                facecolor=color,
                edgecolor=WHITE,
                linewidth=0.25,
                alpha=0.95,
            )
        )


def _build_setup_schematic(png_path: Path, svg_path: Path, data: PresentationData) -> None:
    fig, ax = plt.subplots(figsize=(12.0, 5.9), dpi=240)
    fig.patch.set_alpha(0)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.07, 0.905, "Predictor Set", fontsize=16.0, fontweight="bold", color=INK)
    predictors = [
        ("impervious", TEAL),
        ("land cover", GREEN),
        ("elevation", ACCENT),
        ("water dist.", TEAL_DARK),
        ("NDVI", NDVI_GREEN),
        ("climate", ACCENT_DARK),
    ]
    for idx, (label, color) in enumerate(predictors):
        col = idx % 3
        row = idx // 3
        _chip(ax, 0.07 + col * 0.145, 0.800 - row * 0.092, 0.125, 0.066, label, color)

    ax.add_patch(
        FancyArrowPatch(
            (0.535, 0.760),
            (0.675, 0.760),
            arrowstyle="-|>",
            mutation_scale=24,
            linewidth=2.4,
            color=MUTED,
        )
    )
    _panel(ax, 0.705, 0.690, 0.235, 0.140, fill=PANEL, edge=ACCENT_DARK, linewidth=1.7)
    ax.text(0.822, 0.774, "Hotspot Risk", fontsize=16.0, fontweight="bold", color=ACCENT_DARK, ha="center")
    ax.text(0.822, 0.718, "top-decile model score", fontsize=11.4, color=MUTED, ha="center")

    _panel(ax, 0.035, 0.110, 0.435, 0.445, fill=WHITE, edge=TEAL, linewidth=1.8)
    ax.text(0.065, 0.485, "Within-City Held-Out Cells", fontsize=16.4, fontweight="bold", color=TEAL_DARK)
    ax.text(0.065, 0.433, "Train and test cells come from every city.", fontsize=11.5, color=MUTED)
    for i in range(5):
        y = 0.345 - i * 0.052
        _city_strip(ax, 0.090, y, n_cities=16, held_out=set(range(2, 16, 4)), width=0.235, dot_size=0.0068)
    ax.add_patch(Circle((0.350, 0.333), 0.009, facecolor=TEAL, edgecolor="none"))
    ax.text(0.372, 0.333, "Train", fontsize=11.0, color=TEAL_DARK, va="center")
    ax.add_patch(Circle((0.350, 0.280), 0.009, facecolor=ACCENT, edgecolor="none"))
    ax.text(0.372, 0.280, "Held Out", fontsize=11.0, color=ACCENT_DARK, va="center")

    _panel(ax, 0.530, 0.110, 0.435, 0.445, fill=WHITE, edge=ACCENT_DARK, linewidth=1.8)
    ax.text(0.560, 0.485, "City-Held-Out Transfer", fontsize=16.4, fontweight="bold", color=ACCENT_DARK)
    ax.text(0.560, 0.433, f"{data.outer_fold_count} outer folds; {data.held_out_cities_per_fold} unseen cities per fold.", fontsize=11.5, color=MUTED)
    for fold_idx in range(data.outer_fold_count):
        held = set(range(fold_idx * data.held_out_cities_per_fold, (fold_idx + 1) * data.held_out_cities_per_fold))
        _city_strip(ax, 0.570, 0.350 - fold_idx * 0.041, n_cities=data.city_count, held_out=held, width=0.260, dot_size=0.0058)
    ax.add_patch(Circle((0.855, 0.333), 0.009, facecolor=TEAL, edgecolor="none"))
    ax.text(0.878, 0.333, "Seen", fontsize=11.0, color=TEAL_DARK, va="center")
    ax.add_patch(Circle((0.855, 0.280), 0.009, facecolor=ACCENT, edgecolor="none"))
    ax.text(0.878, 0.280, "Unseen", fontsize=11.0, color=ACCENT_DARK, va="center")

    _save_figure(fig, png_path, svg_path)


def _build_model_math(png_path: Path, svg_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12.0, 5.9), dpi=240)
    fig.patch.set_alpha(0)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    feature_chips = [
        ("impervious", TEAL),
        ("land cover", GREEN),
        ("elevation", ACCENT),
        ("water dist.", TEAL_DARK),
        ("NDVI", NDVI_GREEN),
        ("climate", ACCENT_DARK),
    ]

    def add_feature_grid(x0: float, y0: float) -> None:
        for idx, (label, color) in enumerate(feature_chips):
            col = idx % 3
            row = idx // 3
            _chip(ax, x0 + col * 0.126, y0 - row * 0.062, 0.108, 0.043, label, color)

    _panel(ax, 0.045, 0.075, 0.420, 0.840, fill=WHITE, edge=TEAL, linewidth=1.8)
    ax.text(0.075, 0.855, "Logistic Regression", fontsize=18.0, fontweight="bold", color=TEAL_DARK)
    ax.text(0.075, 0.808, "Each feature gets one learned weight.", fontsize=12.1, color=MUTED)
    add_feature_grid(0.075, 0.720)

    ax.add_patch(
        FancyArrowPatch((0.255, 0.620), (0.255, 0.570), arrowstyle="-|>", mutation_scale=18, linewidth=1.8, color=MUTED)
    )

    baseline_y = 0.485
    ax.plot([0.110, 0.400], [baseline_y, baseline_y], color=OUTLINE, linewidth=2.0)
    bar_x = [0.125, 0.168, 0.211, 0.254, 0.297, 0.340]
    bar_h = [0.085, -0.048, 0.110, -0.065, 0.052, 0.075]
    for x, h, (_label, color) in zip(bar_x, bar_h, feature_chips):
        y = baseline_y if h >= 0 else baseline_y + h
        ax.add_patch(Rectangle((x, y), 0.026, abs(h), facecolor=color, edgecolor="none", alpha=0.92))
    ax.text(0.255, 0.390, "Weighted Sum", fontsize=11.2, color=MUTED, ha="center")

    ax.add_patch(
        FancyArrowPatch((0.255, 0.365), (0.255, 0.322), arrowstyle="-|>", mutation_scale=18, linewidth=1.8, color=MUTED)
    )
    ax.add_patch(
        FancyBboxPatch(
            (0.165, 0.258),
            0.200,
            0.054,
            boxstyle="round,pad=0.010,rounding_size=0.025",
            facecolor=ACCENT_DARK,
            edgecolor="none",
        )
    )
    ax.text(0.265, 0.285, "Risk Score", fontsize=11.8, fontweight="bold", color=WHITE, ha="center", va="center")
    ax.text(0.255, 0.165, "One global relationship maps the feature mix to risk.", fontsize=11.6, color=INK, ha="center")

    _panel(ax, 0.535, 0.075, 0.420, 0.840, fill=WHITE, edge=ACCENT_DARK, linewidth=1.8)
    ax.text(0.565, 0.855, "Random Forest", fontsize=18.0, fontweight="bold", color=ACCENT_DARK)
    ax.text(0.565, 0.808, "Features are reused in many split rules.", fontsize=12.1, color=MUTED)
    add_feature_grid(0.565, 0.720)

    ax.add_patch(
        FancyArrowPatch((0.745, 0.620), (0.745, 0.570), arrowstyle="-|>", mutation_scale=18, linewidth=1.8, color=MUTED)
    )

    def draw_tree(cx: float, cy: float, scale: float, root_label: str, left_label: str, right_label: str) -> None:
        nodes = [
            (cx, cy + 0.090),
            (cx - 0.045 * scale, cy + 0.020),
            (cx + 0.045 * scale, cy + 0.020),
            (cx - 0.070 * scale, cy - 0.045),
            (cx - 0.020 * scale, cy - 0.045),
            (cx + 0.020 * scale, cy - 0.045),
            (cx + 0.070 * scale, cy - 0.045),
        ]
        for parent, child in [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (2, 6)]:
            x0, y0 = nodes[parent]
            x1, y1 = nodes[child]
            ax.plot([x0, x1], [y0, y1], color=MUTED, linewidth=1.4)
        for idx, (x, y) in enumerate(nodes):
            color = ACCENT_DARK if idx in {0, 1, 2} else (ACCENT if idx % 2 else TEAL)
            if idx in {0, 1, 2}:
                ax.add_patch(
                    FancyBboxPatch(
                        (x - 0.037, y - 0.017),
                        0.074,
                        0.034,
                        boxstyle="round,pad=0.004,rounding_size=0.010",
                        facecolor=color,
                        edgecolor=WHITE,
                        linewidth=0.8,
                    )
                )
            else:
                ax.add_patch(Circle((x, y), 0.012, facecolor=color, edgecolor=WHITE, linewidth=0.8))
        ax.text(nodes[0][0], nodes[0][1], root_label, fontsize=8.0, fontweight="bold", color=WHITE, ha="center", va="center")
        ax.text(nodes[1][0], nodes[1][1], left_label, fontsize=7.8, fontweight="bold", color=WHITE, ha="center", va="center")
        ax.text(nodes[2][0], nodes[2][1], right_label, fontsize=7.8, fontweight="bold", color=WHITE, ha="center", va="center")

    draw_tree(0.635, 0.460, 1.05, "NDVI", "water", "elev.")
    draw_tree(0.855, 0.460, 1.05, "imperv.", "cover", "clim.")
    ax.text(0.745, 0.343, "Many Shallow Decision Paths", fontsize=11.0, color=MUTED, ha="center")

    ax.add_patch(
        FancyArrowPatch((0.745, 0.318), (0.745, 0.272), arrowstyle="-|>", mutation_scale=18, linewidth=1.8, color=MUTED)
    )
    vote_x = [0.670, 0.705, 0.740, 0.775, 0.810]
    vote_colors = [ACCENT_DARK, TEAL, ACCENT_DARK, ACCENT_DARK, TEAL]
    for x, color in zip(vote_x, vote_colors):
        ax.add_patch(Circle((x, 0.240), 0.014, facecolor=color, edgecolor=WHITE, linewidth=0.9))
    ax.text(0.745, 0.165, "Average tree votes become the risk score.", fontsize=11.6, color=INK, ha="center")

    _save_figure(fig, png_path, svg_path)


def _plot_partner_bars(ax, data: PresentationData) -> None:
    metrics = [
        ("Precision", data.partner_logistic.class_1_precision_mean, data.partner_rf.class_1_precision_mean),
        ("Recall", data.partner_logistic.class_1_recall_mean, data.partner_rf.class_1_recall_mean),
        ("F1", data.partner_logistic.class_1_f1_mean, data.partner_rf.class_1_f1_mean),
    ]
    y_positions = [2, 1, 0]
    for y, (_label, logistic, rf) in zip(y_positions, metrics):
        ax.barh(y + 0.16, logistic, height=0.28, color=TEAL)
        ax.barh(y - 0.16, rf, height=0.28, color=ACCENT_DARK)
        ax.text(logistic + 0.018, y + 0.16, f"{logistic:.3f}", fontsize=10.4, color=TEAL_DARK, va="center")
        ax.text(rf + 0.018, y - 0.16, f"{rf:.3f}", fontsize=10.4, color=ACCENT_DARK, va="center")
    ax.set_xlim(0, 0.82)
    ax.set_ylim(-0.65, 2.6)
    ax.set_yticks(y_positions, [row[0] for row in metrics])
    ax.set_xlabel("Mean Hotspot-Class Metric", fontsize=11.4, color=MUTED, labelpad=8)
    ax.set_title("Within-City Held-Out Cells", loc="left", fontsize=15.0, fontweight="bold", color=TEAL_DARK, pad=26)
    ax.text(
        0.0,
        1.030,
        "Thresholded class-1 metrics; support ~= 30% per city",
        transform=ax.transAxes,
        fontsize=10.0,
        color=MUTED,
        clip_on=False,
    )


def _plot_transfer_dots(ax, data: PresentationData) -> None:
    metrics = [
        ("Pooled\nPR AUC", data.logistic_5k.pooled_pr_auc, data.rf_frontier.pooled_pr_auc),
        ("Mean City\nPR AUC", data.logistic_5k.mean_city_pr_auc, data.rf_frontier.mean_city_pr_auc),
        ("Recall\n@ Top 10%", data.logistic_5k.pooled_recall_at_top_10pct, data.rf_frontier.pooled_recall_at_top_10pct),
    ]
    y_positions = [2.1, 1.05, 0.0]
    for y, (_label, logistic, rf) in zip(y_positions, metrics):
        ax.hlines(y, min(logistic, rf), max(logistic, rf), color=OUTLINE, linewidth=2.5)
        ax.scatter([logistic], [y], s=90, color=TEAL, edgecolors=WHITE, linewidths=0.8, zorder=3)
        ax.scatter([rf], [y], s=90, color=ACCENT_DARK, edgecolors=WHITE, linewidths=0.8, zorder=3)
        ax.text(logistic, y + 0.20, f"{logistic:.4f}", fontsize=9.6, color=TEAL_DARK, ha="center")
        ax.text(rf, y - 0.24, f"{rf:.4f}", fontsize=9.6, color=ACCENT_DARK, ha="center")
    ax.set_xlim(0.138, 0.202)
    ax.set_ylim(-0.65, 2.62)
    ax.set_yticks(y_positions, [row[0] for row in metrics])
    ax.set_xticks([0.14, 0.16, 0.18, 0.20])
    ax.set_xlabel("Held-Out City Score", fontsize=11.4, color=MUTED, labelpad=8)
    ax.set_title("City-Held-Out Transfer", loc="left", fontsize=15.0, fontweight="bold", color=ACCENT_DARK, pad=26)
    ax.text(
        0.0,
        1.030,
        "5 outer folds; 6 held-out cities per fold",
        transform=ax.transAxes,
        fontsize=10.0,
        color=MUTED,
        clip_on=False,
    )


def _apply_small_plot_style(ax) -> None:
    ax.set_facecolor(WHITE)
    ax.grid(axis="x", color=OUTLINE, linewidth=0.7, alpha=0.7)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(OUTLINE)
    ax.tick_params(axis="x", labelsize=10.5, colors=MUTED)
    ax.tick_params(axis="y", labelsize=11.4, colors=INK, length=0)


def _build_side_by_side_results(png_path: Path, svg_path: Path, data: PresentationData) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.9), dpi=240)
    fig.patch.set_alpha(0)
    for ax in axes:
        _apply_small_plot_style(ax)
    _plot_partner_bars(axes[0], data)
    _plot_transfer_dots(axes[1], data)
    handles = [
        Line2D([0], [0], marker="s", color="none", markerfacecolor=TEAL, markersize=8, label="Logistic"),
        Line2D([0], [0], marker="s", color="none", markerfacecolor=ACCENT_DARK, markersize=8, label="Random Forest"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False, fontsize=11.2)
    fig.subplots_adjust(left=0.10, right=0.985, top=0.90, bottom=0.17, wspace=0.32)

    _save_figure(fig, png_path, svg_path)


def _scatter_with_fit(ax, df: pd.DataFrame, x_col: str, y_col: str, title: str, x_label: str, y_label: str) -> None:
    for climate, subset in df.groupby("climate_group"):
        ax.scatter(
            subset[x_col],
            subset[y_col],
            s=58,
            color=CLIMATE_COLORS.get(climate, MUTED),
            edgecolors=WHITE,
            linewidths=0.6,
            alpha=0.86,
            label=CLIMATE_LABELS.get(climate, climate),
        )
    r_value = float(df[[x_col, y_col]].corr(method="pearson").iloc[0, 1])
    ax.set_title(title, loc="left", fontsize=15.0, fontweight="bold", color=INK, pad=12)
    ax.text(0.02, 0.94, f"Pearson r = {r_value:.2f}", transform=ax.transAxes, fontsize=10.5, color=MUTED)
    ax.set_xlabel(x_label, fontsize=11.2, color=MUTED, labelpad=8)
    ax.set_ylabel(y_label, fontsize=11.2, color=MUTED, labelpad=8)
    ax.grid(True, color=OUTLINE, linewidth=0.7, alpha=0.65)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(OUTLINE)
    ax.spines["bottom"].set_color(OUTLINE)
    ax.tick_params(axis="both", labelsize=10.4, colors=MUTED)


def _build_city_signal_transfer(png_path: Path, svg_path: Path, df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.9), dpi=240)
    fig.patch.set_alpha(0)

    _scatter_with_fit(
        axes[0],
        df,
        "class_1_f1_rf",
        "pr_auc_rf",
        "RF City Ranking Shifts",
        "Within-City RF Hotspot F1",
        "City-Held-Out RF PR AUC",
    )
    _scatter_with_fit(
        axes[1],
        df,
        "class_1_recall_rf",
        "recall_at_top_10pct_rf",
        "Retrieval Signal Shifts",
        "Within-City Hotspot Recall",
        "City-Held-Out RF Recall @ Top 10%",
    )

    for ax in axes:
        ax.set_facecolor(WHITE)
    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=color, markeredgecolor=WHITE, markersize=8, label=label)
        for label, color in [("Hot-arid", ACCENT_DARK), ("Hot-humid", TEAL), ("Mild-cool", GREEN)]
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, fontsize=11.0)
    fig.subplots_adjust(left=0.095, right=0.985, top=0.90, bottom=0.17, wspace=0.25)

    _save_figure(fig, png_path, svg_path)


def _table_cell(
    ax,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    *,
    fill: str,
    color: str = INK,
    weight: str = "normal",
    fontsize: float = 10.5,
    ha: str = "center",
) -> None:
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fill, edgecolor=OUTLINE, linewidth=0.75))
    ax.text(
        x + w / 2 if ha == "center" else x + 0.018,
        y + h / 2,
        text,
        fontsize=fontsize,
        color=color,
        fontweight=weight,
        ha=ha,
        va="center",
        wrap=True,
    )


def _build_comparison_table(png_path: Path, svg_path: Path, data: PresentationData) -> None:
    fig, ax = plt.subplots(figsize=(12.0, 5.0), dpi=240)
    fig.patch.set_alpha(0)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.03, 0.94, "Evaluation Metrics by Model Type", fontsize=18, fontweight="bold", color=INK)
    ax.text(
        0.03,
        0.885,
        "Within-city rows and held-out-city rows answer different validation questions.",
        fontsize=11.0,
        color=MUTED,
    )

    x0 = 0.03
    widths = [0.52, 0.205, 0.205]
    headers = ["Evaluation Metric", "Logistic", "Random Forest"]
    y = 0.760
    h = 0.080
    x = x0
    for width, header in zip(widths, headers):
        _table_cell(ax, x, y, width, h, header, fill=TEAL_DARK, color=WHITE, weight="bold", fontsize=12.0)
        x += width

    rows = [
        ("Within-City Hotspot Precision", f"{data.partner_logistic.class_1_precision_mean:.3f}", f"{data.partner_rf.class_1_precision_mean:.3f}"),
        ("Within-City Hotspot Recall", f"{data.partner_logistic.class_1_recall_mean:.3f}", f"{data.partner_rf.class_1_recall_mean:.3f}"),
        ("Within-City Hotspot F1", f"{data.partner_logistic.class_1_f1_mean:.3f}", f"{data.partner_rf.class_1_f1_mean:.3f}"),
        ("City-Held-Out Pooled PR AUC", f"{data.logistic_5k.pooled_pr_auc:.4f}", f"{data.rf_frontier.pooled_pr_auc:.4f}"),
        ("City-Held-Out Mean City PR AUC", f"{data.logistic_5k.mean_city_pr_auc:.4f}", f"{data.rf_frontier.mean_city_pr_auc:.4f}"),
        ("City-Held-Out Recall @ Top 10%", f"{data.logistic_5k.pooled_recall_at_top_10pct:.4f}", f"{data.rf_frontier.pooled_recall_at_top_10pct:.4f}"),
    ]
    y = 0.675
    row_h = 0.100
    for idx, row in enumerate(rows):
        fill = WHITE if idx % 2 == 0 else PANEL
        if idx == 3:
            ax.add_patch(Rectangle((x0, y + row_h - 0.013), sum(widths), 0.013, facecolor=OUTLINE, edgecolor="none"))
        x = x0
        for col_idx, (width, text) in enumerate(zip(widths, row)):
            color = ACCENT_DARK if col_idx == 2 and idx in {0, 1, 2, 3, 5} else INK
            if col_idx == 1 and idx == 4:
                color = TEAL_DARK
            _table_cell(
                ax,
                x,
                y,
                width,
                row_h,
                text,
                fill=fill,
                color=color,
                weight="bold" if col_idx in {1, 2} else "normal",
                fontsize=12.0 if col_idx == 0 else 12.4,
                ha="left" if col_idx == 0 else "center",
            )
            x += width
        y -= row_h

    _save_figure(fig, png_path, svg_path)


def _style_focus_map_axis(axis: plt.Axes, city_df: pd.DataFrame, title: str) -> None:
    x_col = "map_x" if "map_x" in city_df.columns else "centroid_lon"
    y_col = "map_y" if "map_y" in city_df.columns else "centroid_lat"
    x_min = float(city_df[x_col].min())
    x_max = float(city_df[x_col].max())
    y_min = float(city_df[y_col].min())
    y_max = float(city_df[y_col].max())
    x_pad = max(0.0025, (x_max - x_min) * 0.030)
    y_pad = max(0.0025, (y_max - y_min) * 0.030)
    axis.set_xlim(x_min - x_pad, x_max + x_pad)
    axis.set_ylim(y_min - y_pad, y_max + y_pad)
    axis.set_aspect("equal", adjustable="box")
    axis.set_xticks([])
    axis.set_yticks([])
    axis.set_title(title, fontsize=14.5, fontweight="bold", color=INK, pad=10)
    axis.set_facecolor(WHITE)
    for spine in axis.spines.values():
        spine.set_visible(False)


def _draw_map_points(
    axis: plt.Axes,
    city_df: pd.DataFrame,
    colors: pd.Series,
    *,
    size: float,
    alpha: float = 0.92,
) -> None:
    axis.scatter(
        city_df["map_x"] if "map_x" in city_df.columns else city_df["centroid_lon"],
        city_df["map_y"] if "map_y" in city_df.columns else city_df["centroid_lat"],
        c=colors,
        s=size,
        linewidths=0,
        alpha=alpha,
    )


def _build_heldout_map_focus(png_path: Path, svg_path: Path, repo_root: Path) -> None:
    points_path = (
        repo_root
        / "outputs"
        / "modeling"
        / "reporting"
        / "heldout_city_maps"
        / "heldout_city_map_points.parquet"
    )
    map_points = pd.read_parquet(points_path)
    city_df = map_points.loc[map_points["city_name"].astype(str).str.lower() == "denver"].copy()
    if city_df.empty:
        city_df = map_points.sort_values(["climate_group", "city_name", "cell_id"]).head(5000).copy()
    lat_scale = float(np.cos(np.deg2rad(city_df["centroid_lat"].mean())))
    city_df["map_x"] = city_df["centroid_lon"] * lat_scale
    city_df["map_y"] = city_df["centroid_lat"]

    marker_size = float(min(10.0, max(2.5, 28000.0 / max(1, len(city_df)))))

    fig, axes = plt.subplots(1, 3, figsize=(12.0, 5.9), dpi=240)
    fig.patch.set_alpha(0)
    predicted_ax, observed_ax, error_ax = axes

    neutral = "#d9d9d9"
    predicted_colors = city_df["predicted_hotspot_10pct"].astype(bool).map({True: "#c64a32", False: neutral})
    observed_colors = city_df["hotspot_10pct"].astype(bool).map({True: "#6f1d1b", False: neutral})
    error_palette = {
        "true_positive": "#7f0000",
        "false_positive": "#ef8a62",
        "false_negative": "#67a9cf",
        "true_negative": neutral,
    }
    error_colors = city_df["error_type"].map(error_palette)

    _draw_map_points(predicted_ax, city_df, predicted_colors, size=marker_size)
    _style_focus_map_axis(predicted_ax, city_df, "Predicted Top-Decile Risk")

    _draw_map_points(observed_ax, city_df, observed_colors, size=marker_size)
    _style_focus_map_axis(observed_ax, city_df, "Observed Hotspot Cells")

    _draw_map_points(error_ax, city_df, error_colors, size=marker_size)
    _style_focus_map_axis(error_ax, city_df, "Error Pattern")

    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#7f0000", markersize=8, label="True Positive"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#ef8a62", markersize=8, label="False Positive"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#67a9cf", markersize=8, label="False Negative"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=neutral, markersize=8, label="Other Cells"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=11.2)
    fig.subplots_adjust(left=0.015, right=0.992, top=0.88, bottom=0.15, wspace=0.045)

    _save_figure(fig, png_path, svg_path)
