import csv
import os
from typing import List

BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, "list_with_detail.csv")
LOG_PATH = os.path.join(BASE_DIR, "image_count_mismatch.log")
NEW_COL = "image_count"
REQUIRED_COLS = {"pictureIds", "local_image_paths"}
PICTURE_IDS_DELIM = ","
LOCAL_PATHS_DELIM = "|"



def split_and_count(raw: str, delimiter: str) -> int:
    if raw is None:
        return 0
    text = raw.strip()
    if not text:
        return 0
    parts = [part.strip() for part in text.split(delimiter)]
    return len([part for part in parts if part])


def main() -> None:
    temp_path = CSV_PATH + ".tmp"

    with open(CSV_PATH, "r", encoding="utf-8", newline="") as in_file:
        reader = csv.DictReader(in_file)
        if reader.fieldnames is None:
            raise ValueError("CSV has no header row.")
        missing = REQUIRED_COLS - set(reader.fieldnames)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        fieldnames: List[str] = list(reader.fieldnames)
        if NEW_COL not in fieldnames:
            fieldnames.append(NEW_COL)

        with open(temp_path, "w", encoding="utf-8", newline="") as out_file, open(
            LOG_PATH, "w", encoding="utf-8", newline=""
        ) as log_file:
            writer = csv.DictWriter(out_file, fieldnames=fieldnames)
            writer.writeheader()

            log_file.write("row_number,id,name,pictureIds_count,local_paths_count\n")

            for row_number, row in enumerate(reader, start=2):
                picture_ids_count = split_and_count(
                    row.get("pictureIds", ""), PICTURE_IDS_DELIM
                )
                local_paths_count = split_and_count(
                    row.get("local_image_paths", ""), LOCAL_PATHS_DELIM
                )

                if picture_ids_count == local_paths_count:
                    row[NEW_COL] = str(picture_ids_count)
                else:
                    row[NEW_COL] = ""
                    log_file.write(
                        f"{row_number},{row.get('id','')},{row.get('name','')},"
                        f"{picture_ids_count},{local_paths_count}\n"
                    )

                writer.writerow(row)

    os.replace(temp_path, CSV_PATH)


if __name__ == "__main__":
    main()
