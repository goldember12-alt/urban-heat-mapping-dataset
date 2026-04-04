from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Sequence

from src.modeling_config import get_default_output_dir

_NON_ALNUM_PATTERN = re.compile(r"[^a-z0-9-]+")
_DUPLICATE_HYPHEN_PATTERN = re.compile(r"-{2,}")


def resolve_model_output_dir(
    *,
    model_name: str,
    output_dir: Path | None,
    tuning_preset: str | None,
    selected_outer_folds: Sequence[int] | None,
    sample_rows_per_city: int | None,
    run_label: str | None = None,
    now: datetime | None = None,
    base_output_root: Path | None = None,
) -> tuple[Path, bool]:
    """Return the explicit output dir or a generated model-scoped run directory."""
    if output_dir is not None:
        return output_dir, False

    root_dir = base_output_root or get_default_output_dir(model_name)
    folder_name = build_generated_model_run_dirname(
        tuning_preset=tuning_preset,
        selected_outer_folds=selected_outer_folds,
        sample_rows_per_city=sample_rows_per_city,
        run_label=run_label,
        now=now,
    )
    candidate_path = root_dir / folder_name
    suffix_index = 1
    while candidate_path.exists():
        candidate_path = root_dir / f"{folder_name}_{suffix_index:02d}"
        suffix_index += 1
    return candidate_path, True


def build_generated_model_run_dirname(
    *,
    tuning_preset: str | None,
    selected_outer_folds: Sequence[int] | None,
    sample_rows_per_city: int | None,
    run_label: str | None = None,
    now: datetime | None = None,
) -> str:
    """Build a compact, human-readable run directory name for one modeling CLI invocation."""
    effective_now = datetime.now() if now is None else now
    preset_slug = _slugify_token(tuning_preset or "custom")
    fold_scope = format_model_run_fold_scope(selected_outer_folds)
    sample_scope = format_model_run_sample_scope(sample_rows_per_city)
    timestamp_text = effective_now.strftime("%Y-%m-%d_%H%M%S")
    label_slug = sanitize_model_run_label(run_label)

    parts = [preset_slug, fold_scope, sample_scope]
    if label_slug is not None:
        parts.append(label_slug)
    parts.append(timestamp_text)
    return "_".join(parts)


def format_model_run_fold_scope(selected_outer_folds: Sequence[int] | None) -> str:
    """Return a compact fold-scope token such as f0, f0-2_4, or allfolds."""
    if selected_outer_folds is None:
        return "allfolds"
    normalized = sorted({int(value) for value in selected_outer_folds})
    if not normalized:
        return "allfolds"

    ranges: list[str] = []
    start = normalized[0]
    end = normalized[0]
    for value in normalized[1:]:
        if value == end + 1:
            end = value
            continue
        ranges.append(f"{start}" if start == end else f"{start}-{end}")
        start = value
        end = value
    ranges.append(f"{start}" if start == end else f"{start}-{end}")
    if len(ranges) == 1:
        return "f" + ranges[0]
    return "_".join(f"f{range_text}" for range_text in ranges)


def format_model_run_sample_scope(sample_rows_per_city: int | None) -> str:
    """Return a compact sample-scope token such as s5000 or fullrows."""
    if sample_rows_per_city is None:
        return "fullrows"
    return f"s{int(sample_rows_per_city)}"


def sanitize_model_run_label(run_label: str | None) -> str | None:
    """Return a compact ASCII token suitable for generated output-dir names."""
    if run_label is None:
        return None
    normalized = _slugify_token(run_label)
    if not normalized:
        return None
    return normalized[:24]


def _slugify_token(raw_value: str) -> str:
    lowered = str(raw_value).strip().lower()
    replaced = _NON_ALNUM_PATTERN.sub("-", lowered)
    collapsed = _DUPLICATE_HYPHEN_PATTERN.sub("-", replaced).strip("-")
    return collapsed
