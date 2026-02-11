import pandas as pd
from collections import Counter

def verify_pottery_names(csv_path, output_path):
    # 1. 读取数据
    df = pd.read_csv(csv_path)
    
    # 2. 定义参与拼接的列（严格排除 condition）
    # 注意：这里的顺序是拼接的默认顺序，但我们后续会进行“字符集”比对，所以顺序不影响由于乱序导致的误报
    part_columns = ['era', 'culture', 'decoration', 'shape_feature', 'texture', 'root_shape']
    
    results = []
    
    print(f"正在检查 {len(df)} 条数据...")
    
    for idx, row in df.iterrows():
        original_name = str(row['name']).strip()
        
        # 提取各部分内容，去除空值
        parts = []
        for col in part_columns:
            val = row.get(col, '')
            if pd.notna(val) and str(val).strip() != '':
                parts.append(str(val).strip())
        
        # 拼接字符串
        reconstructed_name = "".join(parts)
        
        # 核心逻辑：使用多重集 (Multiset) 进行字符级比对
        # 这种方法忽略顺序，只检查“该有的字有没有”以及“是不是多出了字”
        name_chars = Counter(original_name)
        parts_chars = Counter(reconstructed_name)
        
        # 计算差异
        missing_in_parts = name_chars - parts_chars  # 原名有，但拆分后没了（漏词）
        extra_in_parts = parts_chars - name_chars    # 拆分后多出来的（幻觉或重复）
        
        missing_str = "".join(sorted(missing_in_parts.elements()))
        extra_str = "".join(sorted(extra_in_parts.elements()))
        
        # 如果有任何字符不匹配，记录下来
        if missing_str or extra_str:
            results.append({
                'row_index': row.get('row_index_0_based', idx),
                'original_name': original_name,
                'reconstructed': reconstructed_name,
                'missing_chars': missing_str, # 重点关注：漏掉的信息
                'hallucinated_chars': extra_str # 重点关注：多出的重复或符号
            })
    
    # 3. 输出报告
    if results:
        result_df = pd.DataFrame(results)
        result_df.to_csv(output_path, index=False)
        print(f"检测完成！发现 {len(result_df)} 处不匹配。")
        print(f"详细报告已保存至: {output_path}")
        # 打印前几条供预览
        print("\n--- 典型错误预览 ---")
        print(result_df[['original_name', 'missing_chars', 'hallucinated_chars']].head().to_markdown(index=False))
    else:
        print("完美！所有名字均可由各部分精确重组。")

# 使用示例
if __name__ == "__main__":
    # 请确保 CSV 文件在当前目录下
    verify_pottery_names('extracted_metadata.csv', 'name_split_check_report.csv')