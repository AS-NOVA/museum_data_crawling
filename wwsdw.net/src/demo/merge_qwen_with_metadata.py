import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]  # wwsdw.net
META_CSV = BASE_DIR / "data" / "extracted" / "extracted_metadata.csv"
QWEN_CSV = BASE_DIR / "output" / "qwen" / "qwen_name_results.csv"
OUTPUT_CSV = BASE_DIR / "output" / "qwen" / "qwen_merged.csv"

# qwen 表中需要丢弃的字段
QWEN_DROP_FIELDS = {"original_name", "image_file"}


def load_csv(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"缺少输入文件: {path}")
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]
        return reader.fieldnames or [], rows


def build_qwen_map(qwen_rows):
    qwen_map = {}
    for row in qwen_rows:
        row_id = row.get("id", "").strip()
        if not row_id:
            continue
        filtered = {k: v for k, v in row.items() if k not in QWEN_DROP_FIELDS}
        qwen_map[row_id] = filtered
    return qwen_map


def merge_rows(meta_rows, qwen_map):
    merged_rows = []
    for row in meta_rows:
        row_id = row.get("id", "").strip()
        if not row_id:
            continue
        if row_id not in qwen_map:
            continue  # 仅合并匹配到的
        merged = {**row, **qwen_map[row_id]}
        merged_rows.append(merged)
    return merged_rows


def main():
    meta_fields, meta_rows = load_csv(META_CSV)
    qwen_fields, qwen_rows = load_csv(QWEN_CSV)

    qwen_map = build_qwen_map(qwen_rows)
    merged_rows = merge_rows(meta_rows, qwen_map)

    # 输出字段顺序：元数据全部 + qwen 字段（去掉重复字段）
    qwen_fields_filtered = [f for f in qwen_fields if f not in QWEN_DROP_FIELDS]
    fieldnames = meta_fields + [f for f in qwen_fields_filtered if f not in meta_fields]

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in merged_rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    print(f"合并完成，共写入 {len(merged_rows)} 条，输出: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
