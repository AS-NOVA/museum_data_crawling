import pandas as pd
import json
import logging
from pathlib import Path

# ================= 配置区域 =================
BASE_DIR = Path(__file__).parent.parent.parent.resolve() # wwsdw.net
OUTPUT_DIR = BASE_DIR / "data" / "extracted"
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "log"

# 输入文件
RAW_CSV_PATH = DATA_DIR / "sample_100_with_image_count.csv"
JSONL_PATH = OUTPUT_DIR / "extracted_metadata.jsonl"

# 输出文件
FINAL_CSV_PATH = OUTPUT_DIR / "extracted_metadata.csv"
ERROR_LOG_PATH = LOG_DIR / "jsonl_to_csv.log"

# ================= 核心逻辑 =================
def main():
    print("🧹 开始执行数据清洗与合并...")

    # 1. 读取原始 CSV（作为主骨架）
    if not RAW_CSV_PATH.exists():
        print(f"❌ 致命错误：找不到原始文件 {RAW_CSV_PATH}")
        return
    
    df_raw = pd.read_csv(RAW_CSV_PATH)
    # 强制将 id 转为字符串，防止与 jsonl 中的 id 类型不匹配
    if 'id' in df_raw.columns:
        df_raw['id'] = df_raw['id'].astype(str)
    print(f"📄 原始数据加载完成，共 {len(df_raw)} 条记录")

    # 2. 读取并校验 JSONL 数据
    if not JSONL_PATH.exists():
        print(f"❌ 致命错误：找不到提取结果 {JSONL_PATH}")
        return

    valid_records = []
    parse_errors = 0

    with open(JSONL_PATH, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line: continue
            
            try:
                data = json.loads(line)
                # 简单校验：必须包含 source_id 才能对账
                if 'source_id' not in data:
                    raise ValueError("缺失 source_id 字段")
                valid_records.append(data)
            except Exception as e:
                parse_errors += 1
                # 记录具体哪一行坏了，方便手动检查（虽然一般直接丢弃）
                with open(ERROR_LOG_PATH, 'a', encoding='utf-8') as err_f:
                    err_f.write(f"Line {line_num}: {str(e)} | Content: {line[:50]}...\n")

    print(f"🔍 JSONL 校验报告：")
    print(f"   - 成功解析: {len(valid_records)} 条")
    print(f"   - 格式错误: {parse_errors} 条 (已记录至 {ERROR_LOG_PATH.name})")

    # 3. 转换为 DataFrame
    if not valid_records:
        print("⚠️ 警告：没有有效数据，终止合并。")
        return

    df_extracted = pd.DataFrame(valid_records)
    if 'original_name' in df_extracted.columns:
        df_extracted.drop(columns=['original_name'], inplace=True)
    
    # 确保 source_id 也是字符串
    df_extracted['source_id'] = df_extracted['source_id'].astype(str)

    # 4. 数据合并 (Left Join)
    # 以原始 CSV 为主，把提取的信息贴上去。
    # 这样即使大模型漏了几条，原始数据也不会丢。
    if 'id' in df_raw.columns:
        # 使用 id 进行精确匹配
        df_final = pd.merge(
            df_raw, 
            df_extracted, 
            left_on='id', 
            right_on='source_id', 
            how='left'
        )
        # 清理掉多余的 source_id 列
        if 'source_id' in df_final.columns:
            df_final.drop(columns=['source_id'], inplace=True)
            
    else:
        # 如果原始csv没有id，只能按顺序强行合并（风险较高，但在你的脚本里我们用了id）
        print("⚠️ 原始CSV无'id'列，尝试索引合并（仅当数据完全对应时有效）")
        df_final = pd.concat([df_raw, df_extracted], axis=1)

    # 5. 最终检查与导出
    # 检查完成度：看看有多少行的 'era' 是空的
    missing_count = df_final['era'].isnull().sum()
    print(f"📊 合并报告：")
    print(f"   - 总行数: {len(df_final)}")
    print(f"   - 成功匹配到时代: {len(df_final) - missing_count}")
    print(f"   - 未匹配到时代: {missing_count}")

    # 保存
    df_final.to_csv(FINAL_CSV_PATH, index=False, encoding='utf-8-sig') # sig 解决 Excel 中文乱码
    print(f"\n✅ 最终文件已生成: {FINAL_CSV_PATH}")

if __name__ == "__main__":
    main()