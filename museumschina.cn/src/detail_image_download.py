import pandas as pd
import requests
import hashlib
import time
import logging
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# ================= 1. 路径配置 (Pathlib) =================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "log"
IMAGE_DIR = DATA_DIR / "images"
# INPUT_CSV = DATA_DIR / "pottery_details_20260305_210613.csv"
INPUT_CSV = DATA_DIR / "data_cleaned_20260311_175712.csv"

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_CSV = DATA_DIR / f"data_local_image_{TIMESTAMP}.csv"
LOG_FILE = LOG_DIR / f"download_log_{TIMESTAMP}.log"

# ================= 2. 日志配置 =================
logging.basicConfig(
    level=logging.INFO,
    filename=LOG_FILE,
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_unique_filename(url):
    """通过URL的MD5值生成唯一文件名，保留原始后缀"""
    if not url or not isinstance(url, str):
        return None
    # 提取后缀，默认为 .jpg
    ext = Path(url).suffix if Path(url).suffix in ['.jpg', '.png', '.jpeg', '.webp'] else '.jpg'
    # 计算MD5
    hash_obj = hashlib.md5(url.encode('utf-8'))
    return f"{hash_obj.hexdigest()}{ext}"

def download_image(url, target_path, max_retries=3):
    """执行实际的下载操作，包含重试机制"""
    if target_path.exists():
        # 如果文件已存在，直接视为成功（MD5保证了内容一致性）
        return True
    
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for attempt in range(max_retries):
        try:
            r = requests.get(url, headers=headers, timeout=20)
            r.raise_for_status()
            with open(target_path, 'wb') as f:
                f.write(r.content)
            logging.info(f"DOWNLOAD SUCCESS: {url} -> {target_path.name}")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                logging.warning(f"RETRYING ({attempt+1}/{max_retries}): {url} | Reason: {str(e)}")
                time.sleep(1)
            else:
                logging.error(f"DOWNLOAD FAILED after {max_retries} attempts: {url} | Reason: {str(e)}")
                return False
    return False

def main():
    if not INPUT_CSV.exists():
        print(f"❌ 找不到输入文件: {INPUT_CSV}")
        return

    # 读取数据
    df = pd.read_csv(INPUT_CSV)
    
    # 准备存储本地路径的新列
    df['local_main_image'] = ""
    df['local_gallery_images'] = ""

    print(f"🚀 开始下载图片，共计 {len(df)} 个展品...")

    for index, row in tqdm(df.iterrows(), total=len(df), desc="Downloading"):
        # --- 处理高清主图 ---
        main_url = row.get('main_image_url')
        if pd.notna(main_url) and main_url.strip():
            filename = get_unique_filename(main_url)
            local_path = IMAGE_DIR / filename
            if download_image(main_url, local_path):
                # 存储相对路径，方便项目迁移
                df.at[index, 'local_main_image'] = f"images/{filename}"

        # --- 处理轮播图 (gallery_urls 之前用 '|' 分隔) ---
        gallery_urls_raw = row.get('gallery_urls')
        if pd.notna(gallery_urls_raw) and gallery_urls_raw.strip():
            urls = gallery_urls_raw.split('|')
            local_paths = []
            for g_url in urls:
                g_filename = get_unique_filename(g_url)
                g_local_path = IMAGE_DIR / g_filename
                if download_image(g_url, g_local_path):
                    local_paths.append(f"images/{g_filename}")
                time.sleep(0.05) # 短暂休眠避免请求过快
            df.at[index, 'local_gallery_images'] = "|".join(local_paths)

    # 保存新的 CSV
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"\n✅ 图片下载完成！")
    print(f"📊 更新后的表格已保存至: {OUTPUT_CSV}")
    print(f"🖼️ 图片存放目录: {IMAGE_DIR}")

if __name__ == "__main__":
    main()