from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.final_dataset_contract import PHASE3A_ADDITIONAL_FINAL_COLUMNS
from src.raster_features import (
    compute_local_class_share_from_aligned_array,
    compute_local_mean_from_aligned_array,
)

PHASE3A_WINDOW_METERS = 270
PHASE3A_WINDOW_RADIUS_CELLS = 4

TREE_COVER_PROXY_CLASSES = (41, 42, 43)
VEGETATED_COVER_PROXY_CLASSES = (41, 42, 43, 52, 71, 81, 82, 90, 95)

TREE_COVER_PROXY_COLUMN = "tree_cover_proxy_pct_270m"
VEGETATED_COVER_PROXY_COLUMN = "vegetated_cover_proxy_pct_270m"
IMPERVIOUS_MEAN_270M_COLUMN = "impervious_pct_mean_270m"


@dataclass(frozen=True)
class Phase3aAlignedBundle:
    tree_cover_proxy_pct_270m: np.ndarray
    vegetated_cover_proxy_pct_270m: np.ndarray
    impervious_pct_mean_270m: np.ndarray

    def as_dict(self) -> dict[str, np.ndarray]:
        return {
            TREE_COVER_PROXY_COLUMN: self.tree_cover_proxy_pct_270m,
            VEGETATED_COVER_PROXY_COLUMN: self.vegetated_cover_proxy_pct_270m,
            IMPERVIOUS_MEAN_270M_COLUMN: self.impervious_pct_mean_270m,
        }


def get_phase3a_final_columns() -> list[str]:
    """Return the bounded richer-predictor Phase 3A output columns."""
    return list(PHASE3A_ADDITIONAL_FINAL_COLUMNS)


def get_phase3a_window_radius_cells(resolution_m: float) -> int:
    """Return the centered square-window radius in cells for the configured nominal window width."""
    if resolution_m <= 0:
        raise ValueError("resolution_m must be positive")
    window_cells = max(int(round(PHASE3A_WINDOW_METERS / float(resolution_m))), 1)
    if window_cells % 2 == 0:
        window_cells += 1
    return window_cells // 2


def compute_phase3a_nlcd_bundle(
    *,
    land_cover_aligned: np.ndarray,
    impervious_aligned: np.ndarray,
    radius_cells: int = PHASE3A_WINDOW_RADIUS_CELLS,
) -> Phase3aAlignedBundle:
    """Compute the bounded Phase 3A NLCD neighborhood-context bundle."""
    tree_cover_proxy = compute_local_class_share_from_aligned_array(
        land_cover_aligned,
        target_values=TREE_COVER_PROXY_CLASSES,
        radius_cells=radius_cells,
    )
    vegetated_cover_proxy = compute_local_class_share_from_aligned_array(
        land_cover_aligned,
        target_values=VEGETATED_COVER_PROXY_CLASSES,
        radius_cells=radius_cells,
    )
    impervious_mean = compute_local_mean_from_aligned_array(
        impervious_aligned,
        radius_cells=radius_cells,
    )
    return Phase3aAlignedBundle(
        tree_cover_proxy_pct_270m=tree_cover_proxy,
        vegetated_cover_proxy_pct_270m=vegetated_cover_proxy,
        impervious_pct_mean_270m=impervious_mean,
    )
