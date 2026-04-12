import os
import json
import logging
from datetime import datetime
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from openai import OpenAI
from dotenv import load_dotenv

# ================= 1. 路径与配置设定 (Config) =================
# 项目根目录与核心数据目录
BASE_DIR = Path(__file__).parent.parent.parent.resolve()
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "extracted"
LOG_DIR = BASE_DIR / "log"
ENV_PATH = BASE_DIR / ".env"

# 初始化基础目录
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 动态时间戳，避免覆盖历史文件
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# 输入输出路径
INPUT_CSV = DATA_DIR / "data_cleaned.csv"
PROMPT_FILE = DATA_DIR / "prompt.txt"
OUTPUT_JSONL = OUTPUT_DIR / f"extracted_metadata_{TIMESTAMP}.jsonl"
LOG_FILE = LOG_DIR / f"llm_process_{TIMESTAMP}.log"

# 模型配置
MODEL_NAME = "deepseek-chat"

# ================= 2. 环境初始化 (Setup) =================
# 配置日志记录 (明确记录请求结果，便于溯源)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# 环境变量与客户端初始化
load_dotenv(dotenv_path=ENV_PATH)
API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not API_KEY:
    raise ValueError(f"严重错误：未在 {ENV_PATH} 或环境中找到 DEEPSEEK_API_KEY。")

client = OpenAI(
    api_key=API_KEY,
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
)

# ================= 3. 核心工具函数 =================
def get_processed_ids(output_dir: Path) -> set:
    """
    扫描输出目录下所有的 jsonl 文件，提取已处理的 source_id。
    完美兼容带时间戳的输出文件，实现跨文件的断点续传。
    """
    processed = set()
    for file_path in output_dir.glob("*.jsonl"):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if 'source_id' in data:
                        processed.add(str(data['source_id']))
                except json.JSONDecodeError:
                    continue
    return processed

def extract_json(text: str) -> dict:
    """提取大模型返回文本中的 JSON 内容"""
    start = text.find('{')
    end = text.rfind('}') + 1
    if start == -1 or end == 0:
        return {}
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        return {}

# ================= 4. 主流程 (Main) =================
def main():
    if not INPUT_CSV.exists() or not PROMPT_FILE.exists():
        raise FileNotFoundError(f"输入文件缺失，请检查：\n{INPUT_CSV}\n{PROMPT_FILE}")

    prompt_template = PROMPT_FILE.read_text(encoding='utf-8')
    df = pd.read_csv(INPUT_CSV)
    
    # 鲁棒性处理：确保有可用的唯一 ID 列
    if 'id' not in df.columns:
        df['id'] = df.index 

    # 收集历史进度，过滤待处理数据
    processed_ids = get_processed_ids(OUTPUT_DIR)
    df_to_process = df[~df['id'].astype(str).isin(processed_ids)]
    
    print(f"🚀 任务启动 | 总量: {len(df)} | 已完成: {len(processed_ids)} | 本次待处理: {len(df_to_process)}")

    # 循环控制与进度追踪
    for _, row in tqdm(df_to_process.iterrows(), total=len(df_to_process), desc="LLM Extraction"):
        artifact_name = str(row['name'])
        source_id = str(row['id'])
        current_prompt = prompt_template.replace("{input_name}", artifact_name)
        
        try:
            # 发起网络请求
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": current_prompt}
                ],
                temperature=0.1
            )
            raw_content = response.choices[0].message.content
            structured_data = extract_json(raw_content)

            if structured_data:
                # 数据组装与落盘
                structured_data['source_id'] = source_id
                structured_data['original_name'] = artifact_name
                
                with open(OUTPUT_JSONL, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(structured_data, ensure_ascii=False) + "\n")
                
                logging.info(f"[SUCCESS] {artifact_name} (ID: {source_id})")
            else:
                # 模型返回了非 JSON 格式
                logging.warning(f"[PARSE_ERROR] {artifact_name} (ID: {source_id}) | 原始返回: {raw_content}")

        except Exception as e:
            # 捕获网络、API Key 或限流等全部异常
            logging.error(f"[REQUEST_FAILED] {artifact_name} (ID: {source_id}) | Error: {e}")

    print(f"\n✅ 任务结束！\n📁 结果已存至: {OUTPUT_JSONL}\n📝 日志已存至: {LOG_FILE}")

if __name__ == "__main__":
    main()