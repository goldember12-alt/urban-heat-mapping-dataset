from __future__ import annotations

import logging

from src.feature_assembly import assemble_final_dataset


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    result = assemble_final_dataset()
    print(result.parquet_path)
    print(result.csv_path)
    print(f"rows={len(result.final_df)}")


if __name__ == "__main__":
    main()
