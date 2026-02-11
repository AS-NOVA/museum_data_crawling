import csv
import os
import random
from typing import List, Dict

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
INPUT_CSV = os.path.join(BASE_DIR, "data", "list_with_detail.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "data", "sample_100_with_image_count.csv")
SAMPLE_SIZE = 100
INDEX_BASE = 0

REQUIRED_COLS = {"name", "id", "image_count"}


def is_non_empty(value: str) -> bool:
    return value is not None and str(value).strip() != ""


def main() -> None:
    with open(INPUT_CSV, "r", encoding="utf-8", newline="") as in_file:
        reader = csv.DictReader(in_file)
        if reader.fieldnames is None:
            raise ValueError("CSV has no header row.")

        missing = REQUIRED_COLS - set(reader.fieldnames)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        candidates: List[Dict[str, str]] = []
        for idx, row in enumerate(reader, start=INDEX_BASE):
            if not is_non_empty(row.get("image_count", "")):
                continue
            candidates.append(
                {
                    "row_index": str(idx),
                    "name": row.get("name", ""),
                    "id": row.get("id", ""),
                    "image_count": row.get("image_count", ""),
                }
            )

    if len(candidates) < SAMPLE_SIZE:
        raise ValueError(
            f"Not enough rows with non-empty image_count: {len(candidates)}"
        )

    sample = random.sample(candidates, SAMPLE_SIZE)

    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as out_file:
        fieldnames = [
            f"row_index_{INDEX_BASE}_based",
            "name",
            "id",
            "image_count",
        ]
        writer = csv.DictWriter(out_file, fieldnames=fieldnames)
        writer.writeheader()
        for item in sample:
            writer.writerow(
                {
                    f"row_index_{INDEX_BASE}_based": item["row_index"],
                    "name": item["name"],
                    "id": item["id"],
                    "image_count": item["image_count"],
                }
            )

    print(
        f"Wrote {SAMPLE_SIZE} rows to {OUTPUT_CSV} with {INDEX_BASE}-based row index."
    )


if __name__ == "__main__":
    main()
