import requests
import csv
import time
import random
import os

# --- 配置部分 ---
# 目标 API URL
url = "http://www.wwsdw.net/admin/collection/getCollectionList.do"

# 请求头 (模拟浏览器，防止被简单的反爬拦截)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "http://www.wwsdw.net/",
    "Origin": "http://www.wwsdw.net"
}

# 基础查询参数 (根据你的筛选条件：新石器时代+陶器)
params = {
    "year": "45",              # 新石器时代
    "collectionsCategory": "2", # 陶器
    "orgId": "",
    "name": "",
    "isThree": "",
    "size": "6",               # 每页数量
    # currentPage 将在循环中动态修改
    # _t (时间戳) 将在循环中动态生成
}

# 保存的文件名
filename = "shandong_neolithic_pottery.csv"

# --- 核心逻辑 ---

def get_current_timestamp():
    """生成毫秒级时间戳，对应 URL 中的 _t 参数"""
    return int(time.time() * 1000)

def fetch_page(page_num):
    """抓取指定页码的数据"""
    current_params = params.copy()
    current_params["currentPage"] = page_num
    current_params["_t"] = get_current_timestamp()

    try:
        response = requests.get(url, headers=headers, params=current_params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"请求失败 (状态码 {response.status_code}): 第 {page_num} 页")
            return None
    except Exception as e:
        print(f"请求发生异常: {e}")
        return None

def main():
    # 1. 先请求第一页，获取总页数和表头字段
    print("正在初始化并获取总页数...")
    first_page_data = fetch_page(1)
    
    if not first_page_data or "data" not in first_page_data:
        print("无法获取第一页数据，程序终止。")
        return

    # 解析分页信息
    page_info = first_page_data.get("page", {})
    total_pages = page_info.get("totalPage", 0)
    total_rows = page_info.get("allRow", 0)
    
    print(f"成功连接！共发现 {total_rows} 件藏品，共 {total_pages} 页。")

    # 准备 CSV 文件
    # 从第一条数据中提取所有字段名作为 CSV 表头
    if len(first_page_data["data"]) > 0:
        csv_headers = list(first_page_data["data"][0].keys())
    else:
        print("第一页没有数据？")
        return

    # 如果文件不存在，则创建并写入表头；如果存在则追加（方便断点续传，但这里简化为每次覆盖）
    file_exists = os.path.exists(filename)
    mode = 'w' # 'w' 表示覆盖写入，如果你想断点续传可以用 'a'
    
    with open(filename, mode, encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        if mode == 'w':
            writer.writeheader()
        
        # 写入第一页的数据
        writer.writerows(first_page_data["data"])
        print(f"第 1/{total_pages} 页已保存。")

        # 2. 循环抓取剩余页面
        for page in range(2, total_pages + 1):
            # 随机休眠 0.5 到 1.5 秒，对服务器保持礼貌
            time.sleep(random.uniform(0.5, 1.5))
            
            data_json = fetch_page(page)
            
            if data_json and "data" in data_json:
                items = data_json["data"]
                writer.writerows(items)
                print(f"第 {page}/{total_pages} 页已保存 ({len(items)} 条数据)。")
            else:
                print(f"警告：第 {page} 页数据为空或获取失败。")
                # 可以在这里添加重试逻辑，或者记录失败的页码

    print(f"\n全部爬取完成！数据已保存至 {filename}")

if __name__ == "__main__":
    main()