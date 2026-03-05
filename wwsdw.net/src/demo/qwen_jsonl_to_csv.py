import csv
import json
from pathlib import Path

# 输入/输出路径
BASE_DIR = Path(__file__).resolve().parents[2]  # wwsdw.net
INPUT_JSONL = BASE_DIR / "output" / "qwen" / "qwen_name_results.jsonl"
OUTPUT_CSV = BASE_DIR / "output" / "qwen" / "qwen_name_results.csv"

# 字段重命名映射
FIELD_MAP = {
    "reasoning": "qwen_reasoning",
    "era": "qwen_era",
    "culture": "qwen_culture",
    "decoration": "qwen_decoration",
    "shape_feature": "qwen_shape_feature",
    "material": "qwen_texture",
    "common_name": "qwen_root_shape",
    "full_name": "qwen_name",
    "source_id": "id",
}

# 目标字段的首选顺序
PREFERRED_ORDER = [
    "id",
    "original_name",
    "image_file",
    "qwen_reasoning",
    "qwen_era",
    "qwen_culture",
    "qwen_decoration",
    "qwen_shape_feature",
    "qwen_texture",
    "qwen_root_shape",
    "qwen_name",
]


def load_jsonl(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"缺少输入文件: {path}")
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def transform_rows(raw_rows):
    transformed = []
    extra_fields = set()

    for rec in raw_rows:
        row = {}
        for key, val in rec.items():
            if key in FIELD_MAP:
                row[FIELD_MAP[key]] = val
            else:
                row[key] = val
                if key not in PREFERRED_ORDER:
                    extra_fields.add(key)
        transformed.append(row)

    # 合并最终字段列表：优先顺序 + 额外字段（按字母排序）
    fieldnames = PREFERRED_ORDER + [k for k in sorted(extra_fields) if k not in PREFERRED_ORDER]
    return transformed, fieldnames


def write_csv(rows, fieldnames, path: Path):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            # 确保所有字段都有值
            full_row = {name: row.get(name, "") for name in fieldnames}
            writer.writerow(full_row)


def main():
    print(f"读取: {INPUT_JSONL}")
    raw_rows = load_jsonl(INPUT_JSONL)
    print(f"读取到 {len(raw_rows)} 条记录，开始转换...")

    transformed_rows, fieldnames = transform_rows(raw_rows)
    write_csv(transformed_rows, fieldnames, OUTPUT_CSV)

    print(f"完成，已输出 CSV: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
