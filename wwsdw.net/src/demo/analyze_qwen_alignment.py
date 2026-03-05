import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

BASE_DIR = Path(__file__).resolve().parents[2]  # wwsdw.net
MERGED_CSV = BASE_DIR / "output" / "qwen" / "qwen_merged.csv"
REPORT_TXT = BASE_DIR / "output" / "qwen" / "qwen_alignment_report.txt"
REPORT_SUMMARY_CSV = BASE_DIR / "output" / "qwen" / "qwen_alignment_summary.csv"

# 映射：原始字段 -> Qwen 字段
FIELD_PAIRS: List[Tuple[str, str]] = [
    ("era", "qwen_era"),
    ("culture", "qwen_culture"),
    ("decoration", "qwen_decoration"),
    ("shape_feature", "qwen_shape_feature"),
    ("texture", "qwen_texture"),
    ("root_shape", "qwen_root_shape"),
]


def normalize(text: str) -> str:
    if text is None:
        return ""
    return " ".join(text.strip().lower().split())


def load_rows(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"缺少输入文件: {path}")
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def analyze(rows: List[Dict[str, str]]):
    stats = {orig: {"total": 0, "match": 0, "mismatches": []} for orig, _ in FIELD_PAIRS}

    for row in rows:
        for orig, pred in FIELD_PAIRS:
            orig_val = normalize(row.get(orig, ""))
            pred_val = normalize(row.get(pred, ""))
            if not orig_val and not pred_val:
                # 都为空不计入统计
                continue
            stats[orig]["total"] += 1
            if orig_val == pred_val:
                stats[orig]["match"] += 1
            else:
                # 记录少量示例
                if len(stats[orig]["mismatches"]) < 5:
                    stats[orig]["mismatches"].append(
                        {
                            "id": row.get("id", ""),
                            "orig": row.get(orig, ""),
                            "pred": row.get(pred, ""),
                            "qwen_name": row.get("qwen_name", ""),
                            "name": row.get("name", ""),
                        }
                    )
    return stats


def write_summary_csv(stats: Dict[str, Dict]):
    REPORT_SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_SUMMARY_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["field", "total", "match", "accuracy"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for orig, _ in FIELD_PAIRS:
            total = stats[orig]["total"]
            match = stats[orig]["match"]
            acc = (match / total) if total else 0.0
            writer.writerow({
                "field": orig,
                "total": total,
                "match": match,
                "accuracy": f"{acc:.4f}",
            })


def write_text_report(stats: Dict[str, Dict]):
    lines = []
    lines.append("Qwen 对齐分析报告\n")
    lines.append(f"数据源: {MERGED_CSV}")
    lines.append("")

    for orig, _ in FIELD_PAIRS:
        total = stats[orig]["total"]
        match = stats[orig]["match"]
        acc = (match / total) if total else 0.0
        lines.append(f"字段 {orig}: 匹配 {match}/{total}, 准确率 {acc:.2%}")
        mismatches = stats[orig]["mismatches"]
        if mismatches:
            lines.append("  示例不匹配 (最多5条):")
            for m in mismatches:
                lines.append(
                    f"    id={m['id']} | 原: {m['orig']} | 预测: {m['pred']} | qwen_name: {m['qwen_name']} | 原名: {m['name']}"
                )
        lines.append("")

    REPORT_TXT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_TXT.write_text("\n".join(lines), encoding="utf-8")


def main():
    rows = load_rows(MERGED_CSV)
    stats = analyze(rows)
    write_summary_csv(stats)
    write_text_report(stats)
    print(f"完成。汇总写入: {REPORT_SUMMARY_CSV}\n详细写入: {REPORT_TXT}")


if __name__ == "__main__":
    main()
