from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.cache_cleanup import PRUNE_MODES, prune_cache


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit data_raw/cache usage and optionally prune safe regenerable artifacts."
    )
    parser.add_argument(
        "--prune-modes",
        nargs="+",
        choices=sorted(PRUNE_MODES),
        help="Optional prune plan to build. Omit for inventory-only mode.",
    )
    parser.add_argument(
        "--protect-recent-hours",
        type=float,
        default=24.0,
        help="Protect files newer than this many hours from pruning.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete the planned prune candidates. Default is dry-run.",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        help="Optional JSON path for the inventory and prune plan metadata.",
    )
    return parser


def _print_table(title: str, rows: list[dict[str, object]], key_field: str) -> None:
    if not rows:
        return
    print(title)
    for row in rows:
        key = str(row[key_field])
        size_gb = float(row.get("size_gb", 0.0))
        file_count = int(row.get("file_count", 0))
        suffix = ""
        retention = str(row.get("retention_class", "")).strip()
        if retention:
            suffix = f" | retention={retention}"
        print(f"- {key}: {size_gb:.3f} GB across {file_count} files{suffix}")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _build_arg_parser().parse_args()

    report = prune_cache(
        prune_modes=args.prune_modes,
        protect_recent_hours=args.protect_recent_hours,
        execute=args.execute,
        report_json_path=args.report_json,
    )

    print(report["cache_root"])
    print(
        f"inventory: {report['inventory_summary']['size_gb']:.3f} GB "
        f"across {report['inventory_summary']['file_count']} files"
    )
    _print_table("subfolders:", report["subfolder_summary"], "subfolder")
    _print_table("categories:", report["category_summary"], "category")

    if args.prune_modes:
        print(f"prune_modes: {', '.join(args.prune_modes)}")
        print(
            f"candidate_prune: {report['prune_summary']['candidate_gb']:.3f} GB "
            f"across {report['prune_summary']['candidate_files']} files"
        )
        print(
            f"blocked_by_safety_checks: {report['prune_summary']['blocked_gb']:.3f} GB "
            f"across {report['prune_summary']['blocked_files']} files"
        )
        if not args.execute:
            print("dry_run=true")

    report_json_path = report.get("report_json_path")
    if report_json_path:
        print(report_json_path)


if __name__ == "__main__":
    main()
