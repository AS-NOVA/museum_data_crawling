import json
import os
import requests
from tqdm import tqdm
from urllib.parse import urlparse

# ================= 配置区 =================
# 你爬下来的 JSON 文件所在的目录
SOURCE_DATA_DIR = "./dpm_data"

# 最终构建好的数据集要存放在哪里
OUTPUT_DIR = "./dpm_dataset"

# User-Agent，下载图片时模拟浏览器
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0"

# ================= 核心函数 =================

def download_image(url, save_path):
    """根据 URL 下载单张图片并保存"""
    if os.path.exists(save_path):
        # print(f"图片已存在，跳过: {save_path}")
        return
        
    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, stream=True, timeout=15)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        else:
            print(f"下载失败 (状态码 {response.status_code}): {url}")
    except Exception as e:
        print(f"下载时发生错误 ({url}): {e}")

def get_file_extension_from_url(url):
    """从URL中提取文件扩展名，例如 .png"""
    path = urlparse(url).path
    return os.path.splitext(path)[1]

# ================= 主程序 =================

def main():
    # 1. 创建输出目录
    images_dir = os.path.join(OUTPUT_DIR, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    # 2. 读取所有爬取到的 JSON 文件
    all_items = []
    for filename in os.listdir(SOURCE_DATA_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(SOURCE_DATA_DIR, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                all_items.extend(json.load(f))
    
    print(f"共找到 {len(all_items)} 件文物数据。")

    # 3. 循环处理每件文物，构建 metadata.jsonl
    metadata_file_path = os.path.join(OUTPUT_DIR, "metadata.jsonl")
    
    with open(metadata_file_path, 'w', encoding='utf-8') as f_meta:
        # 使用 tqdm 显示进度条
        for item in tqdm(all_items, desc="处理文物数据"):
            uuid = item.get("uuid")
            if not uuid:
                continue

            # --- 图片处理 ---
            # 你的注意点1：不使用 centerImage
            # 你的注意点2：对 images 列表中的 URL 去重
            unique_image_urls = sorted(list(set(item.get("images", []))))
            
            downloaded_image_paths = []
            for i, url in enumerate(unique_image_urls):
                extension = get_file_extension_from_url(url)
                # 使用 uuid 和图片索引作为文件名，确保唯一性
                image_filename = f"{uuid}_{i}{extension}"
                image_save_path = os.path.join(images_dir, image_filename)
                
                # 下载图片
                download_image(url, image_save_path)
                
                # 记录相对路径
                downloaded_image_paths.append(os.path.join("images", image_filename))

            # --- 元数据整理 ---
            metadata = {
                "uuid": uuid,
                "name": item.get("name"),
                "base_info": item.get("detail_info", {}), # 将所有标签和基础信息整合
                "image_paths": downloaded_image_paths
            }
            
            # 写入一行到 metadata.jsonl
            f_meta.write(json.dumps(metadata, ensure_ascii=False) + "\n")
            
    print(f"\n🎉 数据集构建完成！")
    print(f"图片保存在: {images_dir}")
    print(f"元数据保存在: {metadata_file_path}")


if __name__ == "__main__":
    main()