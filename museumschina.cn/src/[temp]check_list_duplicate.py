import pandas as pd
from pathlib import Path

# ================= 1. 路径配置 =================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
INPUT_CSV = DATA_DIR / "pottery_list_20260305_153650.csv"

def check_duplicates():
    if not INPUT_CSV.exists():
        print(f"❌ 错误：找不到文件 {INPUT_CSV}")
        return

    # 读取并统一转为字符串并去首尾空格
    df = pd.read_csv(INPUT_CSV).astype(str).apply(lambda x: x.str.strip())
    
    # 找出所有重复的 URL
    # keep=False 表示标记所有重复出现过的行
    duplicate_mask = df.duplicated(subset=['detail_url'], keep=False)
    df_duplicates = df[duplicate_mask]

    if df_duplicates.empty:
        print("✅ 列表页中不存在重复的 detail_url。")
        return

    # 按 detail_url 分组
    grouped = df_duplicates.groupby('detail_url')
    
    conflicts = []

    for url, group in grouped:
        # 检查该组内去重后的行数
        # 如果去重后行数 > 1，说明存在内容不一致
        if len(group.drop_duplicates()) > 1:
            conflicts.append(group)

    # ================= 2. 输出结果 =================
    if not conflicts:
        print("-" * 50)
        print("✅ 结论：所有重复行内容完全相同。")
        print(f"统计：共有 {len(df_duplicates)} 条重复记录，涉及 {len(grouped)} 个唯一 URL。")
        print("建议：你可以直接执行 drop_duplicates(subset=['detail_url']) 进行清理。")
        print("-" * 50)
    else:
        print("-" * 50)
        print("❌ 警告：存在内容不一致的重复项！")
        print(f"共发现 {len(conflicts)} 组 detail_url 对应的其他字段内容不同。")
        print("\n以下是第一组不符的详细数据：")
        print("-" * 50)
        # 打印第一组冲突数据
        first_conflict = conflicts[0]
        print(first_conflict)
        print("-" * 50)

if __name__ == "__main__":
    check_duplicates();