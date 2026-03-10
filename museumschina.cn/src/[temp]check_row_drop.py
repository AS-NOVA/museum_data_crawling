import pandas as pd
from pathlib import Path

# ================= 1. 路径配置 =================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

LIST_CSV = DATA_DIR / "pottery_list_20260305_153650.csv"
DETAIL_CSV = DATA_DIR / "pottery_details_local_image_20260310_155657.csv"

def find_missing():
    if not LIST_CSV.exists() or not DETAIL_CSV.exists():
        print("❌ 错误：输入文件缺失。")
        return

    # 2. 读取数据并去重（确保对比的是唯一 URL）
    # 列表页因为网站抖动可能有重复，我们取其唯一值
    df_list = pd.read_csv(LIST_CSV)
    df_detail = pd.read_csv(DETAIL_CSV)

    list_urls = set(df_list['detail_url'].unique())
    detail_urls = set(df_detail['detail_url'].unique())

    # 3. 统计基本情况
    print(f"📊 数据统计：")
    print(f"   - 列表页唯一 URL 数: {len(list_urls)}")
    print(f"   - 详情页唯一 URL 数: {len(detail_urls)}")

    # 4. 计算差集 (在列表页中但不在详情页中)
    missing_urls = list_urls - detail_urls

    # 5. 输出结果
    if not missing_urls:
        if len(df_list) > len(df_detail):
            print("\n✅ 逻辑闭环：唯一 URL 数量完全一致。")
            print("   列表页行数多是因为存在重复 URL，去重后两者其实是完全对应的。")
        else:
            print("\n🤔 奇怪：唯一 URL 完全一致，但行数对不上，请检查是否有完全重复的行。")
    else:
        print(f"\n🚩 发现缺失！共有 {len(missing_urls)} 条详情数据未被爬取。")
        print("-" * 50)
        for i, url in enumerate(missing_urls, 1):
            # 从列表页中找出这一行的详细信息，方便排查
            row_info = df_list[df_list['detail_url'] == url].iloc[0]
            print(f"缺失项 {i}:")
            print(f"  - 名称: {row_info.get('title')}")
            print(f"  - 博物馆: {row_info.get('museum')}")
            print(f"  - URL: {url}")
        print("-" * 50)
        print("💡 建议：直接手动访问上述 URL。如果是 404，就不用管了；如果是正常页面，手动补爬这一行即可。")

if __name__ == "__main__":
    find_missing()