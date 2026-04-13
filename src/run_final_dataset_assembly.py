from __future__ import annotations

import json
import logging

from src.feature_assembly import assemble_final_dataset


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    result = assemble_final_dataset()
    print(result.parquet_path)
    print(result.csv_path)
    artifact_summary = json.loads(result.artifact_summary_path.read_text(encoding="utf-8"))
    print(f"rows={artifact_summary['row_count']}")


if __name__ == "__main__":
    main()
