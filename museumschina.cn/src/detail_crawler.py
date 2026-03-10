"""
此脚本读入INPUT_FILE中的detail_url列，访问每个url并爬取每个详情页的高清主图、文本信息（如标题、收藏单位、类别、年代、级别、入藏年度、质地等）以及轮播多图，并将结果保存到OUTPUT_FILE中。日志记录爬取过程中的成功与失败情况。
"""


import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import time
import logging

# ================= 1. 环境定义 =================
BASE_DIR = Path(__file__).resolve().parent.parent
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
INPUT_DIR = BASE_DIR / "data"
INPUT_FILE = INPUT_DIR / "pottery_list_20260305_153650.csv"
OUTPUT_DIR = BASE_DIR / "data"
OUTPUT_FILE = OUTPUT_DIR / f"pottery_details_{TIMESTAMP}.csv"
LOG_DIR = BASE_DIR / "log"
LOG_FILE = LOG_DIR / f"detail_crawl_log_{TIMESTAMP}.log"

# 配置日志（仅文件记录，终端留给 tqdm）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8')]
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# ================= 2. 核心提取逻辑 =================
def parse_detail_page(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        data = {"detail_url": url}

        # 1. 提取高清主图
        main_img = soup.select_one("div.details_img > img")
        data["main_image_url"] = main_img['src'] if main_img else ""

        # 2. 提取文本信息 (details_info)
        info_div = soup.select_one("div.details_info")
        if info_div:
            # 标题
            title_node = info_div.select_one(".info_tit")
            data["title_full"] = title_node.get_text(strip=True) if title_node else ""
            
            # 使用“标签对照法”提取动态字段
            p_tags = info_div.find_all("p")
            # 预设我们关心的字段映射
            field_map = {
                "收藏单位": "museum_detail",
                "类别": "category_detail",
                "年代": "era_detail",
                "级别": "level",
                "入藏年度": "entry_year",
                "质地": "material"
            }
            
            for p in p_tags:
                span = p.find("span")
                if span:
                    label = span.get_text(strip=True)
                    if label in field_map:
                        # 移除span后的文字内容，有些在a标签里，有些是纯文本
                        # 直接拿整个p的text，然后去掉label部分
                        value = p.get_text(strip=True).replace(label, "").strip()
                        data[field_map[label]] = value

        # 3. 提取轮播多图 (#pic)
        gallery_images = []
        pic_items = soup.select("#pic div.pic_li img")
        for img in pic_items:
            gallery_images.append(img['src'])
        data["gallery_urls"] = "|".join(gallery_images) # 用竖线分隔，方便后续拆分

        return data

    except Exception as e:
        logging.error(f"Failed to crawl {url}: {str(e)}")
        return None

# ================= 3. 执行流程 =================
def main():
    # 检查输入
    if not INPUT_FILE.exists():
        print(f"错误：找不到输入文件 {INPUT_FILE}")
        return

    # 读取原始数据
    df_list = pd.read_csv(INPUT_FILE)
    if 'detail_url' not in df_list.columns:
        print("错误：CSV中不包含 detail_url 列")
        return

    urls = df_list['detail_url'].tolist()
    results = []

    print(f"开始爬取详情页，共 {len(urls)} 条数据...")
    
    # 强制进度条
    for url in tqdm(urls, desc="Detail Scraping"):
        # 针对每个详情页进行抓取
        detail_data = parse_detail_page(url)
        if detail_data:
            results.append(detail_data)
            logging.info(f"SUCCESS: {url}")
        else:
            logging.warning(f"FAILED: {url}")
        
        # 礼貌性延时，避免被封
        time.sleep(0.5)

    # 保存新数据
    if results:
        new_df = pd.DataFrame(results)
        new_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print(f"\n任务完成！详情数据已保存至: {OUTPUT_FILE}")
        print(f"日志记录请查看: {LOG_FILE}")
    else:
        print("\n未成功爬取到任何数据，请检查日志。")

if __name__ == "__main__":
    main()