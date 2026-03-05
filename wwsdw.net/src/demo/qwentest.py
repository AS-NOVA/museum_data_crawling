import base64
import csv
import json
import os
from pathlib import Path
from typing import Dict, Iterable

from openai import OpenAI
from tqdm import tqdm

# ================= 配置区域 (Config) =================
API_KEY = os.getenv("DASHSCOPE_API_KEY", "sk-dd18b9d0f8b3431d8a9187638bd045bd")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "qwen3-vl-plus"

BASE_DIR = Path(__file__).resolve().parents[2]  # wwsdw.net
DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = BASE_DIR / "images"
INPUT_CSV = DATA_DIR / "extracted" / "extracted_metadata.csv"
PROMPT_FILE = DATA_DIR / "name_prompt.txt"
OUTPUT_DIR = BASE_DIR / "output" / "qwen"
OUTPUT_JSONL = OUTPUT_DIR / "qwen_name_results.jsonl"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


def image_to_data_url(path: Path) -> str:
    """Read local image and return data URL for OpenAI-compatible image input."""
    mime = "image/jpeg"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def load_prompt() -> str:
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(f"Prompt file missing: {PROMPT_FILE}")
    return PROMPT_FILE.read_text(encoding="utf-8").strip()


def iter_rows() -> Iterable[Dict[str, str]]:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Input CSV missing: {INPUT_CSV}")
    with INPUT_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row:
                continue
            yield row


def call_qwen(image_path: Path, prompt_text: str) -> str:
    content = [
        {"type": "image_url", "image_url": {"url": image_to_data_url(image_path)}},
        {"type": "text", "text": prompt_text},
    ]
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": content}],
    )
    return response.choices[0].message.content


def clean_json_string(text: str):
    """Extract JSON object substring from a model reply."""
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end <= 0:
            return None
        return json.loads(text[start:end])
    except Exception:
        return None


def main() -> None:
    prompt_template = load_prompt()
    rows = list(iter_rows())
    total = len(rows)
    processed = 0

    print(f"检测到 {total} 条记录，开始处理...")

    with OUTPUT_JSONL.open("a", encoding="utf-8") as out_f:
        for row in tqdm(rows, desc="Processing", unit="item"):
            artifact_name = (row.get("name") or "").strip()
            artifact_id = (row.get("id") or "").strip()
            if not artifact_name or not artifact_id:
                continue

            image_name = f"{artifact_id}_0.jpg"
            image_path = IMAGES_DIR / image_name
            if not image_path.exists():
                print(f"[跳过] 未找到图片: {image_name}")
                continue

            prompt_text = f"{prompt_template}\n\n原表格名称：{artifact_name}"
            try:
                response_text = call_qwen(image_path, prompt_text)
            except Exception as exc:  # catch to continue batch
                print(f"[失败] {artifact_id}: {exc}")
                continue

            structured = clean_json_string(response_text)
            if not structured:
                print(f"[跳过] 无法解析 JSON: {artifact_id}")
                continue

            structured["source_id"] = artifact_id
            structured["original_name"] = artifact_name
            structured["image_file"] = image_name

            out_f.write(json.dumps(structured, ensure_ascii=False) + "\n")
            processed += 1
            if processed % 10 == 0:
                print(f"已完成 {processed} 条 / {total} 条")

    print(f"完成。成功写入 {processed} 条记录，遍历总数 {total}。输出: {OUTPUT_JSONL}")


if __name__ == "__main__":
    main()