import pandas as pd
from pathlib import Path

# ================= 1. 路径配置 =================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
INPUT_CSV = DATA_DIR / "pottery_details_local_image_20260310_155657.csv"

def check_download_status():
    if not INPUT_CSV.exists():
        print(f"❌ 错误：找不到文件 {INPUT_CSV}")
        return

    # 读取数据，将空值填充为空字符串以便处理
    df = pd.read_csv(INPUT_CSV).fillna("")
    
    error_list = []

    print(f"🔍 正在核对数据完整性 (总计 {len(df)} 行)...\n")
    print(f"{'行号':<6} | {'文物名称':<25} | {'主图':<6} | {'轮播图(总/失)'}")
    print("-" * 70)

    for index, row in df.iterrows():
        # --- 1. 检查主图 ---
        main_url = str(row['main_image_url']).strip()
        local_main = str(row['local_main_image']).strip()
        
        main_failed = False
        if main_url and not local_main:
            main_failed = True

        # --- 2. 检查轮播图 ---
        gallery_urls_str = str(row['gallery_urls']).strip()
        local_gallery_str = str(row['local_gallery_images']).strip()
        
        # 统计原始URL数量
        url_list = [u for u in gallery_urls_str.split('|') if u]
        # 统计本地路径数量
        local_list = [l for l in local_gallery_str.split('|') if l]
        
        total_gallery = len(url_list)
        failed_gallery = total_gallery - len(local_list)
        
        # --- 3. 判定是否为“异常行” ---
        if main_failed or failed_gallery > 0:
            artifact_name = row['title_full'][:20] # 截断过长名称
            main_status = "失败" if main_failed else "成功"
            
            # 记录结果
            error_info = {
                "row": index + 2, # CSV行号 = 索引 + 标题行(1) + 1
                "name": artifact_name,
                "main": main_status,
                "gallery": f"{total_gallery} / {failed_gallery}"
            }
            error_list.append(error_info)
            
            # 实时输出
            print(f"{error_info['row']:<8} | {error_info['name']:<27} | {error_info['main']:<8} | {error_info['gallery']}")

    # --- 4. 汇总报告 ---
    print("-" * 70)
    if error_list:
        print(f"🚩 统计完成：共发现 {len(error_list)} 件文物存在图片下载缺失。")
        print(f"💡 建议：记录上述行号，如有必要可针对性重跑下载逻辑。")
    else:
        print("🎉 恭喜！所有文物图片均已完整下载，未发现缺失。")

if __name__ == "__main__":
    check_download_status()