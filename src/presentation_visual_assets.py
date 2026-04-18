from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle

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
SAND = "#f0e4d4"
COOL = "#dfe8e8"


@dataclass(frozen=True)
class PresentationVisualAssets:
    problem_schematic_png: Path
    problem_schematic_svg: Path
    design_schematic_png: Path
    design_schematic_svg: Path


def build_presentation_visual_assets(
    repo_root: Path, data: PresentationData
) -> PresentationVisualAssets:
    output_dir = repo_root / "figures" / "presentation"
    output_dir.mkdir(parents=True, exist_ok=True)

    problem_png = output_dir / "transfer_problem_schematic.png"
    problem_svg = output_dir / "transfer_problem_schematic.svg"
    design_png = output_dir / "heldout_city_cv_schematic.png"
    design_svg = output_dir / "heldout_city_cv_schematic.svg"

    _build_problem_schematic(problem_png, problem_svg)
    _build_design_schematic(design_png, design_svg, data)

    return PresentationVisualAssets(
        problem_schematic_png=problem_png,
        problem_schematic_svg=problem_svg,
        design_schematic_png=design_png,
        design_schematic_svg=design_svg,
    )


def _build_problem_schematic(png_path: Path, svg_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11.5, 4.2), dpi=220)
    fig.patch.set_alpha(0)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    panel_x = [0.02, 0.35, 0.68]
    panel_w = 0.28
    for x in panel_x:
        ax.add_patch(
            FancyBboxPatch(
                (x, 0.08),
                panel_w,
                0.84,
                boxstyle="round,pad=0.016,rounding_size=0.04",
                facecolor=PANEL,
                edgecolor=OUTLINE,
                linewidth=1.8,
            )
        )

    ax.text(0.06, 0.83, "Heat risk", fontsize=16, fontweight="bold", color=INK)
    ax.add_patch(Circle((0.11, 0.62), 0.06, facecolor="#f2b65a", edgecolor="none", alpha=0.95))
    ax.add_patch(Rectangle((0.17, 0.38), 0.022, 0.18, facecolor=ACCENT_DARK, edgecolor="none"))
    ax.add_patch(Circle((0.181, 0.34), 0.032, facecolor=ACCENT, edgecolor="none"))
    ax.add_patch(Rectangle((0.07, 0.20), 0.035, 0.17, facecolor=TEAL, edgecolor="none"))
    ax.add_patch(Rectangle((0.11, 0.20), 0.04, 0.24, facecolor=TEAL_DARK, edgecolor="none"))
    ax.add_patch(Rectangle((0.16, 0.20), 0.038, 0.12, facecolor=GREEN, edgecolor="none"))
    ax.text(0.06, 0.12, "public health\nand planning", fontsize=11.5, color=MUTED, va="bottom")

    ax.text(0.39, 0.83, "Cities differ", fontsize=16, fontweight="bold", color=INK)
    city_x = [0.43, 0.50, 0.57]
    fills = [ACCENT, TEAL, GREEN]
    heights = [0.19, 0.25, 0.16]
    for x, fill, height in zip(city_x, fills, heights):
        ax.add_patch(Rectangle((x, 0.24), 0.022, height, facecolor=fill, edgecolor="none"))
        ax.add_patch(Rectangle((x + 0.028, 0.24), 0.026, height + 0.06, facecolor=TEAL_DARK, edgecolor="none"))
        ax.add_patch(Rectangle((x + 0.060, 0.24), 0.020, max(height - 0.02, 0.08), facecolor=SAND, edgecolor="none"))
        ax.add_patch(Circle((x + 0.036, 0.58), 0.065, facecolor=fill, edgecolor="none", alpha=0.16))
    ax.text(0.39, 0.12, "climate, land cover,\nwater, vegetation", fontsize=11.5, color=MUTED, va="bottom")

    ax.text(0.72, 0.83, "The real test", fontsize=16, fontweight="bold", color=INK)
    ax.text(0.72, 0.72, "same-city row split", fontsize=10.5, color=MUTED)
    same_city = FancyBboxPatch(
        (0.72, 0.48),
        0.10,
        0.18,
        boxstyle="round,pad=0.01,rounding_size=0.02",
        facecolor=WHITE,
        edgecolor=OUTLINE,
        linewidth=1.4,
        linestyle="--",
    )
    ax.add_patch(same_city)
    same_points = [
        (0.742, 0.54, TEAL),
        (0.766, 0.58, ACCENT),
        (0.788, 0.52, TEAL),
        (0.808, 0.60, ACCENT),
        (0.776, 0.63, TEAL_DARK),
    ]
    for x, y, fill in same_points:
        ax.add_patch(Circle((x, y), 0.010, facecolor=fill, edgecolor="none"))
    ax.text(0.85, 0.56, "vs.", fontsize=14, fontweight="bold", color=MUTED, va="center")

    ax.text(0.88, 0.72, "held-out city", fontsize=10.5, color=MUTED)
    seen_city = FancyBboxPatch(
        (0.88, 0.47),
        0.08,
        0.18,
        boxstyle="round,pad=0.01,rounding_size=0.02",
        facecolor=WHITE,
        edgecolor=TEAL,
        linewidth=1.6,
    )
    unseen_city = FancyBboxPatch(
        (0.90, 0.22),
        0.08,
        0.18,
        boxstyle="round,pad=0.01,rounding_size=0.02",
        facecolor=WHITE,
        edgecolor=ACCENT_DARK,
        linewidth=1.6,
    )
    ax.add_patch(seen_city)
    ax.add_patch(unseen_city)
    for x, y in [(0.905, 0.55), (0.926, 0.60), (0.948, 0.53), (0.937, 0.63)]:
        ax.add_patch(Circle((x, y), 0.010, facecolor=TEAL, edgecolor="none"))
    for x, y in [(0.924, 0.31), (0.945, 0.28), (0.966, 0.35)]:
        ax.add_patch(Circle((x, y), 0.010, facecolor=ACCENT, edgecolor="none"))
    ax.add_patch(
        FancyArrowPatch(
            (0.92, 0.45),
            (0.94, 0.40),
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=1.5,
            color=MUTED,
        )
    )
    ax.text(0.72, 0.12, "shared context looks easier;\nunseen context is the benchmark", fontsize=11.5, color=MUTED, va="bottom")

    fig.savefig(svg_path, bbox_inches="tight", transparent=True)
    fig.savefig(png_path, bbox_inches="tight", transparent=True)
    plt.close(fig)


def _build_design_schematic(png_path: Path, svg_path: Path, data: PresentationData) -> None:
    fig, ax = plt.subplots(figsize=(11.6, 4.4), dpi=220)
    fig.patch.set_alpha(0)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.add_patch(
        FancyBboxPatch(
            (0.02, 0.08),
            0.96,
            0.84,
            boxstyle="round,pad=0.02,rounding_size=0.04",
            facecolor=WHITE,
            edgecolor=OUTLINE,
            linewidth=1.8,
        )
    )

    ax.text(0.05, 0.84, f"{data.city_count} cities", fontsize=17, fontweight="bold", color=INK)
    ax.text(0.20, 0.84, f"{data.outer_fold_count} outer folds", fontsize=13.5, color=MUTED)
    ax.text(0.37, 0.84, f"{data.held_out_cities_per_fold} held out each fold", fontsize=13.5, color=MUTED)

    start_x = 0.08
    dx = 0.026
    heldout_idx = set(range(data.held_out_cities_per_fold))
    for i in range(data.city_count):
        x = start_x + dx * i
        if i >= 15:
            x += 0.02
        if i >= 25:
            x += 0.02
        fill = ACCENT if i in heldout_idx else TEAL
        alpha = 0.95 if i in heldout_idx else 0.78
        ax.add_patch(Circle((x, 0.68), 0.0105, facecolor=fill, edgecolor="none", alpha=alpha))

    ax.text(0.08, 0.73, "one fold snapshot", fontsize=10.5, color=MUTED)
    ax.text(0.07, 0.61, "24 seen", fontsize=11, color=TEAL_DARK)
    ax.text(0.82, 0.61, "6 unseen", fontsize=11, color=ACCENT_DARK)

    ax.add_patch(
        FancyArrowPatch((0.22, 0.54), (0.46, 0.54), arrowstyle="-|>", mutation_scale=16, linewidth=2.4, color=MUTED)
    )
    ax.add_patch(
        FancyArrowPatch((0.54, 0.54), (0.78, 0.54), arrowstyle="-|>", mutation_scale=16, linewidth=2.4, color=MUTED)
    )

    boxes = [
        (0.08, 0.39, 0.18, 0.12, TEAL, "seen cities"),
        (0.30, 0.39, 0.18, 0.12, GREEN, "fit preprocess"),
        (0.52, 0.39, 0.18, 0.12, ACCENT, "tune on seen"),
        (0.74, 0.39, 0.18, 0.12, ACCENT_DARK, "score unseen"),
    ]
    for x, y, w, h, fill, label in boxes:
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.012,rounding_size=0.03",
                facecolor=fill,
                edgecolor="none",
            )
        )
        ax.text(x + w / 2, y + h / 2, label, fontsize=12.5, fontweight="bold", color=WHITE, ha="center", va="center")

    ax.add_patch(
        FancyBboxPatch(
            (0.08, 0.16),
            0.84,
            0.12,
            boxstyle="round,pad=0.01,rounding_size=0.03",
            facecolor=COOL,
            edgecolor="none",
        )
    )
    ax.text(
        0.50,
        0.22,
        "one row = one 30 m city cell | target = hotspot_10pct | no preprocessing leakage across held-out cities",
        fontsize=12,
        color=TEAL_DARK,
        ha="center",
        va="center",
    )

    fig.savefig(svg_path, bbox_inches="tight", transparent=True)
    fig.savefig(png_path, bbox_inches="tight", transparent=True)
    plt.close(fig)
