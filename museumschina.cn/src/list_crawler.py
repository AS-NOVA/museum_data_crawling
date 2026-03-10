"""
本脚本用于爬取中国博物馆网（https://www.museumschina.cn/）陶瓷类藏品的信息。
爬取内容包括：藏品名称、所属博物馆、年代、类别、详情页链接、缩略图链接等。
爬取结果将保存为CSV文件，并记录日志以便后续分析和调试。
使用前，请务必确认各路径配置：
- BASE_DIR: 子项目根目录（当前是脚本所在目录的上一级）
- LOG_DIR: 根目录下的日志文件夹
- OUT_DIR: 根目录下的输出文件夹
此脚本有Gemini参与编写
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import time
import logging

# ================= 配置区 =================
BASE_DIR = Path(__file__).resolve().parent.parent
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_DIR = BASE_DIR / "log"
LOG_FILE = LOG_DIR / f"crawl_log_{TIMESTAMP}.log"
OUT_DIR = BASE_DIR / "data"
OUTPUT_FILE = OUT_DIR / "" f"pottery_list_{TIMESTAMP}.csv"

# 初始化日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
    ]
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.museumschina.cn/Collection"
}

def fetch_page(page_num):
    url = f"https://www.museumschina.cn/Collection?category=2&yearType=45&pages={page_num}&size=20"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logging.error(f"Page {page_num} failed to load: {str(e)}")
        return None

def parse_html(html_content, page_num):
    soup = BeautifulSoup(html_content, 'html.parser')
    items = soup.select("div.exhibit_li")
    
    page_data = []
    for idx, item in enumerate(items):
        try:
            # 提取详情页链接
            detail_path = item.select_one("div.coll_img > a")['href']
            detail_url = f"https://www.museumschina.cn{detail_path}"
            
            # 提取缩略图
            img_src = item.select_one("div.coll_img > a > img")['src']
            
            # 提取文本信息
            title = item.select_one("div.ex_info_tit > a").get_text(strip=True)
            museum = item.select_one("div.ex_info_address > a").get_text(strip=True)
            category = item.select_one("div.ex_info_type").get_text(strip=True).replace("类别：", "")
            year = item.select_one("div.ex_info_year").get_text(strip=True).replace("年代：", "")
            
            page_data.append({
                "title": title,
                "museum": museum,
                "year": year,
                "category": category,
                "detail_url": detail_url,
                "img_url": img_src
            })
        except Exception as e:
            logging.warning(f"Page {page_num}, Item {idx+1} parsing error: {str(e)}")
            
    return page_data

def main():
    total_pages = 55
    all_results = []
    
    logging.info("Starting crawl mission: China Museums Network - Pottery")
    
    for p in tqdm(range(1, total_pages + 1), desc="Crawling Pages"):
        content = fetch_page(p)
        if content:
            data = parse_html(content, p)
            if data:
                all_results.extend(data)
                logging.info(f"Page {p} success: Scraped {len(data)} items.")
            else:
                logging.error(f"Page {p} failed: No items found in DOM.")
        
        # 强制休眠，防止被封IP
        time.sleep(1.5)

    # 保存结果
    if all_results:
        df = pd.DataFrame(all_results)
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        logging.info(f"Mission Accomplished. Data saved to {OUTPUT_FILE}")
    else:
        logging.critical("No data collected. Check network or DOM selectors.")

if __name__ == "__main__":
    main()