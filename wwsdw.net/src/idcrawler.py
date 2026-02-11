import pandas as pd
import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- 全局配置 ---
INPUT_CSV = 'list.csv'
OUTPUT_CSV = 'list_with_detail.csv'
IMAGE_DIR = 'images'
MAX_WORKERS = 16 # 开启16个线程并发，拒绝两小时的低效等待

os.makedirs(IMAGE_DIR, exist_ok=True)

def process_item(row):
    item_id = row['id']
    # 构造请求，加入时间戳防止缓存
    api_url = f"http://www.wwsdw.net/admin/collection/getCollectionById.do?_t={int(time.time()*1000)}&userId=&token=&id={item_id}"
    
    result = {
        'id': item_id,
        'size': '',
        'collectionTexture': '',
        'local_image_paths': ''
    }
    
    try:
        resp = requests.get(api_url, timeout=10)
        data = resp.json().get('data', {}).get('collectionInfo', {})
        if not data:
            return result
            
        # 1. 提取新增文本信息
        result['size'] = data.get('size', '')
        result['collectionTexture'] = data.get('collectionTexture', '')
        
        # 2. 提取并下载图片
        local_paths = []
        pics = data.get('pics', [])
        
        for i, pic in enumerate(pics):
            # 详情页的 url 字段通常是原始清晰度，thumb系列是缩略图
            img_url = pic.get('url', '')
            if not img_url:
                continue
                
            img_ext = img_url.split('.')[-1]
            local_filename = f"{item_id}_{i}.{img_ext}"
            local_filepath = os.path.join(IMAGE_DIR, local_filename)
            
            # 如果本地已有该图，则跳过下载（支持断点续传的粗略逻辑）
            if not os.path.exists(local_filepath):
                img_resp = requests.get(img_url, timeout=15)
                if img_resp.status_code == 200:
                    with open(local_filepath, 'wb') as f:
                        f.write(img_resp.content)
            
            local_paths.append(local_filepath)
            
        result['local_image_paths'] = "|".join(local_paths) # 用管道符连接多张图路径
        print(f"[成功] 提取并下载完成: {item_id} (图片数: {len(local_paths)})")
        
    except Exception as e:
        print(f"[失败] 处理 {item_id} 时出错: {e}")
        
    return result

def main():
    print("开始读取列表数据...")
    df = pd.read_csv(INPUT_CSV)
    
    # 将 DataFrame 转换为字典列表以便多线程处理
    rows = df.to_dict('records')
    results_list = []
    
    print(f"启动高并发下载，线程数: {MAX_WORKERS}...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有任务
        futures = {executor.submit(process_item, row): row for row in rows}
        
        for future in as_completed(futures):
            results_list.append(future.result())
            
    # 将详情页结果合并回原始 DataFrame
    print("下载完成，开始合并数据...")
    details_df = pd.DataFrame(results_list)
    # 按照 ID 进行合并
    final_df = pd.merge(df, details_df, on='id', how='left')
    
    final_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"工程结束！完整数据已保存至 {OUTPUT_CSV}")

if __name__ == "__main__":
    main()