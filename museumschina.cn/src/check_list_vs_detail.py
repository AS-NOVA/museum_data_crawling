import pandas as pd
from pathlib import Path

# ================= 1. 路径配置 =================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

LIST_CSV = DATA_DIR / "pottery_list_20260305_153650.csv"
DETAIL_CSV = DATA_DIR / "pottery_details_local_image_20260310_175310.csv"

# ================= 2. 映射关系定义 =================
# 列表页列名 : 详情页列名
COLUMN_MAP = {
    "title": "title_full",
    "museum": "museum_detail",
    "year": "era_detail",
    "category": "category_detail",
    "detail_url": "detail_url",
    "img_url": "main_image_url"
}

def check_consistency():
    if not LIST_CSV.exists() or not DETAIL_CSV.exists():
        print("❌ 错误：输入文件缺失。")
        return

    # 读取数据，转为字符串并去除空格
    # fillna('') 保证空值也能正常比对
    df_list = pd.read_csv(LIST_CSV).fillna('').astype(str).apply(lambda x: x.str.strip())
    df_detail = pd.read_csv(DETAIL_CSV).fillna('').astype(str).apply(lambda x: x.str.strip())

    # --- 1. 长度校验 ---
    len_list = len(df_list)
    len_detail = len(df_detail)
    
    print(f"📊 正在按行比对数据... (列表行数: {len_list}, 详情行数: {len_detail})")

    if len_list != len_detail:
        print(f"❌ 不完全相符：行数不一致！")
        print(f"列表页有 {len_list} 行，但详情页有 {len_detail} 行。这说明爬取过程中可能存在遗漏或重复写入。")
        return

    # --- 2. 逐行比对 ---
    is_all_match = True
    
    # 使用 itertuples() 遍历效率更高且逻辑清晰
    for idx in range(len_list):
        row_list = df_list.iloc[idx]
        row_detail = df_detail.iloc[idx]
        
        mismatch_found = False
        mismatch_field = ""

        for list_col, detail_col in COLUMN_MAP.items():
            if row_list[list_col] != row_detail[detail_col]:
                mismatch_found = True
                mismatch_field = list_col
                break
        
        if mismatch_found:
            print("-" * 50)
            print(f"❌ 不完全相符：在第 {idx + 2} 行发现差异 (CSV行号)")
            print(f"冲突字段: [{mismatch_field}]")
            print(f"列表页值: '{row_list[mismatch_field]}'")
            print(f"详情页值: '{row_detail[detail_col]}'")
            print("-" * 50)
            is_all_match = False
            break

    # --- 3. 最终结论 ---
    if is_all_match:
        print("✅ 完全相符")
        print("所有对应行数据在关键字段上均完全一致。")

if __name__ == "__main__":
    check_consistency()