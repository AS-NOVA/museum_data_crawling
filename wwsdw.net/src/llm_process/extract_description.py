import os
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm

# ==========================================
# 1. 路径与基础配置
# ==========================================
# 解析项目根目录: wwsdw.net
# 假设当前脚本位于 wwsdw.net/src/llm_process/extract_attributes.py
BASE_DIR = Path(__file__).resolve().parent.parent.parent
INPUT_FILE = BASE_DIR / "data" / "processed_df.jsonl"
ENV_FILE = BASE_DIR / ".env"
# 输出与日志目录配置
OUTPUT_DIR = BASE_DIR / "data" / "extracted"
LOG_DIR = BASE_DIR / "log"
# 生成带时间戳的文件名，避免覆盖
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_FILE = OUTPUT_DIR / f"extracted_desc_{timestamp}.jsonl"
LOG_FILE = LOG_DIR / f"api_extract_{timestamp}.log"

# ==========================================
# 2. 日志配置
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler() # 同时输出到控制台看严重报错
    ]
)
# 屏蔽第三方库的底层日志，保持日志文件清爽
logging.getLogger("httpx").setLevel(logging.WARNING)

# ==========================================
# 3. 提示词与大模型配置
# ==========================================
# 加载环境变量
load_dotenv(ENV_FILE)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
SYSTEM_PROMPT = """你是一个专业的考古与文物数据提取助手。
请阅读用户提供的彩陶文物的描述文本，并且结合名称和器型信息，从这些信息中尽可能完整地提取以下 9 个维度的信息，并严格按照 JSON 格式输出。

提取维度与要求：
1. "material": 对文物材质的描述，如夹砂红陶、泥质灰陶等
2. "pattern": 对彩陶文物上面所绘制纹样的细致描述
3. "shape": 在基础器型之上，对器型的辅助描述，如高柄、双耳等；或进一步详细描述器型的语句
4. "state": 文物当前的保存状态，如残、修复等
5. "color": 与文物颜色相关的信息，可能如彩绘、黑陶衣等
6. "craft": 对文物制作时采用的工艺的详细描述，可能如镂空、磨光、轮制等
7. "raw_excavation_info": 描述文物出土的时间、地点的语句，原样摘录
8. "raw_size_in_desc": 描述文物的长宽高、口径等各方面尺寸的语句，原样摘录
9. "other_info": 所有完全无法归为前8类的冗余或额外描述

如果暂无描述，则尝试仅基于名称和器型提取信息。
提取时，如果某属性有完整的相应语句，应尽可能提取完整的语句或分句。如果没有完整语句或分句，则尽量提取相关的关键词或短语。如果该属性确实没有任何相关信息，则填写空值null。请严格输出且仅输出包含这 9 个键的 JSON 对象，不要输出任何额外的解释文本或 markdown 代码块标记。"""

# ==========================================
# 4. 核心异步处理逻辑
# ==========================================
async def process_single_item(item: dict, sem: asyncio.Semaphore, client: AsyncOpenAI, file_lock: asyncio.Lock):
    """处理单条文物数据"""
    item_id = item.get("id", "UNKNOWN_ID")
    full_desc = item.get("fullDesc", "")
    name = item.get("name", "")
    shape_type = item.get("shape_type","")
    
    # 如果描述为空，直接返回空字段占位，不浪费 API
    # if not full_desc:
    #     result_data = {
    #         "id": item_id,
    #         "extracted": {k: None for k in ["color", "craft", "material", "pattern", "shape", "state", "other_info", "raw_excavation_info", "raw_size_in_desc"]},
    #         "status": "skipped_empty_desc"
    #     }
    #     await save_result(result_data, file_lock)
    #     logging.info(f"Skipped {item_id}: fullDesc is empty.")
    #     return
    
    # 如果描述为空，用“暂无描述”填充，继续传给大模型，让大模型从名称里尽量提取信息
    if not full_desc:
        full_desc = "暂无描述"

    async with sem:
        try:
            # 组装用户 prompt
            user_prompt = f"文物名称: {name}\n文物器型：{shape_type}\n文物描述: {full_desc}"
            
            response = await client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1, # 低温度保证信息提取的稳定性
                timeout=60 # 设置超时，防止请求挂死
            )
            
            # 解析大模型返回的 JSON 字符串
            raw_content = response.choices[0].message.content
            extracted_json = json.loads(raw_content)

            result_data = {
                "id": item_id,
                "name": name,
                "fullDesc": full_desc,
                "extracted": extracted_json,
                "status": "success"
            }
            await save_result(result_data, file_lock)
            logging.info(f"Success {item_id}")
            
        except Exception as e:
            # 捕获所有异常，确保崩溃不传染，记录日志便于后续排查
            error_msg = str(e)
            result_data = {
                "id": item_id,
                "extracted": None,
                "status": "error",
                "error_msg": error_msg
            }
            await save_result(result_data, file_lock)
            logging.error(f"Failed {item_id}: {error_msg}")

async def save_result(result_data: dict, file_lock: asyncio.Lock):
    """带锁写入本地文件，确保异步并发下文件写入的安全"""
    async with file_lock:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(result_data, ensure_ascii=False) + "\n")

async def main():
    logging.info(f"开始任务。输入: {INPUT_FILE}")
    logging.info(f"输出将实时写入: {OUTPUT_FILE}")
    
    # 初始化客户端
    client = AsyncOpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL
    )
    
    # 限制并发量，20 相对保守且安全
    sem = asyncio.Semaphore(20)
    file_lock = asyncio.Lock()
    
    # 加载所有数据
    items = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
                
    logging.info(f"共加载 {len(items)} 条数据。开始并发请求...")
    
    # 创建所有异步任务
    tasks = [process_single_item(item, sem, client, file_lock) for item in items]
    
    # 带进度条运行
    await tqdm.gather(*tasks, desc="API Extraction Progress")
    
    logging.info("所有请求处理完毕！")

if __name__ == "__main__":
    asyncio.run(main())