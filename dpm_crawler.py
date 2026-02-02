import requests
import json
import time
import random
import os
from bs4 import BeautifulSoup
import re

# ================= 配置区 =================
# 之前抓到的 User-Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0"

# 基础 URL
URL_LIST = "https://digicol.dpm.org.cn/cultural/queryList"
URL_DETAIL = "https://digicol.dpm.org.cn/cultural/detail"
URL_IMAGES = "https://digicol.dpm.org.cn/cultural/listCulturalImage"

# 请求头模板
HEADERS_BASE = {
    "User-Agent": USER_AGENT,
    "Origin": "https://digicol.dpm.org.cn",
    # 中文爬取！
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# ================= 核心函数 =================

def get_cultural_list(page_num, category="6", dynasty="1276"):
    """
    获取第 page_num 页的文物列表（JSON API）
    """
    print(f"📥 正在获取第 {page_num} 页列表...")
    
    payload = {
        "page": str(page_num),
        "categoryList": [category],
        "dynastyList": [dynasty]
    }
    
    # 注意：列表页还需要 Referer 才能不报错
    headers = HEADERS_BASE.copy()
    headers["Referer"] = f"https://digicol.dpm.org.cn/?page={page_num}&category={category}&dynasty={dynasty}"
    headers["Content-Type"] = "application/json;charset=UTF-8"

    try:
        resp = requests.post(URL_LIST, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if "rows" in data:
                return data["rows"]
        print(f"❌ 获取列表失败: {resp.text[:100]}")
    except Exception as e:
        print(f"💥 网络错误: {e}")
    return []



def get_cultural_detail(uuid, page_num):
    """
    获取文物的详情信息（解析 HTML）
    将基本信息和标签信息分离开，并特殊处理颜色代码。
    """
    params = {
        "id": uuid,
        "source": "0",
        "page": str(page_num)
    }
    
    try:
        resp = requests.get(URL_DETAIL, headers=HEADERS_BASE, params=params, timeout=10)
        if resp.status_code != 200:
            return None
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # 最终返回的字典，包含两个子字典
        result = {
            "base_info": {},
            "tags": {}
        }
        base_info_dict = result["base_info"]
        tags_dict = result["tags"]

        # 1. 解析基本信息 (文物号, 分类, 年代, 颜色)
        ul_box = soup.find("div", class_="ul_box")
        if ul_box:
            for li in ul_box.find_all("li"):
                span = li.find("span")
                if not span:
                    continue
                
                key = span.get_text(strip=True)
                
                if key == "颜色":
                    # --- 特殊处理颜色代码 ---
                    color_codes = []
                    # 查找包含颜色信息的 font 标签
                    color_font = li.find("font", class_="detail_color")
                    if color_font:
                        # 遍历所有 biankuang 里的 font
                        for inner_font in color_font.select("div.biankuang font"):
                            style_attr = inner_font.get("style", "")
                            # 使用正则表达式从 "color:#000000" 中提取颜色代码
                            match = re.search(r"color:\s*(#[0-9a-fA-F]{6})", str(style_attr))
                            if match:
                                color_codes.append(match.group(1))
                    base_info_dict[key] = color_codes
                else:
                    # --- 常规处理其他基本信息 ---
                    font = li.find("font")
                    if font:
                        value = font.get_text(strip=True)
                        if key and value: # 确保 key 和 value 都不为空
                            base_info_dict[key] = value

        # 2. 解析标签 (图案与纹样, 过程与技术...)
        tags_container = soup.find("div", id="recommend_relevance_tags")
        if tags_container:
            for kg in tags_container.find_all("div", class_="kg-container"):
                title_div = kg.find("div", class_="swiper-tag-title")
                if title_div:
                    tag_category = title_div.get_text(strip=True)
                    tags = [a.get_text(strip=True) for a in kg.find_all("a", class_="caption")]
                    tags_dict[tag_category] = tags
        
        return result

    except Exception as e:
        print(f"💥 解析详情出错 ({uuid}): {e}")
        return None

def get_cultural_images(uuid):
    """
    获取文物的多张图片链接（解析 HTML）
    """
    params = {"id": uuid}
    image_list = []
    
    try:
        resp = requests.get(URL_IMAGES, headers=HEADERS_BASE, params=params, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # .swiper-slide -> img['src']
        slides = soup.find_all("div", class_="swiper-slide")
        for slide in slides:
            img = slide.find("img")
            if img and img.get("src"):
                image_list.append(img["src"])
                
    except Exception as e:
        print(f"💥 解析图片出错 ({uuid}): {e}")
    
    return image_list

# ================= 主程序 =================

def main():
    # 创建保存结果的文件夹
    if not os.path.exists("dpm_data"):
        os.makedirs("dpm_data")

    # 只爬第 5 页作为测试
    page = 5
    items = get_cultural_list(page)
    
    if not items:
        print("没有获取到文物列表，程序结束。")
        return

    print(f"💪 本页共有 {len(items)} 个文物，开始逐个爬取详情...")

    results = []

    # 遍历列表中的每一个文物
    for index, item in enumerate(items):
        name = item.get("name", "未知")
        uuid = item.get("uuid")
        
        print(f"[{index+1}/{len(items)}] 正在处理: {name} ...")
        
        # 1. 获取详情（基本信息+标签）
        detail_info = get_cultural_detail(uuid, page)
        
        # 2. 获取多图链接
        image_urls = get_cultural_images(uuid)
        
        # 3. 整合数据
        final_data = {
            "name": name,
            "uuid": uuid,
            "list_page_data": item, # 保留列表页原始数据
            "detail_info": detail_info,
            "images": image_urls
        }
        
        results.append(final_data)
        
        # 礼貌爬虫：每爬一个，休息一小会儿，防止被封 IP
        time.sleep(random.uniform(0.5, 1.5))

    # 保存结果到 JSON 文件
    with open(f"dpm_data/page_{page}.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎉 完成！数据已保存到 dpm_data/page_{page}.json")

if __name__ == "__main__":
    main()