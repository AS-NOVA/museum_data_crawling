import requests
import json

# 1. 目标接口 (我们刚才在 Network 里找到的)
url = "https://digicol.dpm.org.cn/cultural/queryList"

# 2. 请求头 (Headers)
# 我把你提供的 User-Agent 放进去了，同时加了 Referer 和 Origin，
# 这两个字段是告诉服务器“我是从故宫官网内部发起的请求”，防止防盗链拦截。
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://digicol.dpm.org.cn",
    "Referer": "https://digicol.dpm.org.cn/?page=5&category=6&dynasty=1276"
}

# 3. 载荷 (Payload)
# 这里直接照抄你截图里的 JSON 结构
payload = {
    "page": "5",
    "categoryList": ["6"],   # 6 代表陶瓷
    "dynastyList": ["1276"]  # 1276 代表唐代
}

# 4. 发送请求
print("正在向故宫发送请求...")

try:
    # 核心知识点：因为载荷是 JSON 格式，requests 库要用 json= 参数，它会自动处理格式转换
    response = requests.post(url, headers=headers, json=payload)
    
    # 5. 验证结果
    if response.status_code == 200:
        print("✅ 请求成功！状态码 200")
        
        # 将返回的文本解析为 JSON 对象
        result_json = response.json()
        
        # 检查是否拿到了数据
        if "rows" in result_json:
            rows = result_json["rows"]
            print(f"🎉 成功获取到 {len(rows)} 件文物信息！\n")
            
            # 打印前 3 个看看对不对
            print("--- 数据预览 ---")
            for item in rows[:3]:
                name = item.get("name", "未知名称")
                img_url = item.get("centerImage", "无图")
                uuid = item.get("uuid", "")
                print(f"文物名: {name}")
                print(f"ID (uuid): {uuid}")
                print(f"图片链接: {img_url}")
                print("-" * 30)
        else:
            print("⚠️ 警告：返回了 200，但 JSON 里没有 'rows' 字段。")
            print("服务器返回内容：", result_json)
    else:
        print(f"❌ 请求失败，状态码：{response.status_code}")
        print("返回内容：", response.text)

except Exception as e:
    print(f"💥 程序出错: {e}")