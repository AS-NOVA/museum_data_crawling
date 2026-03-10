import pandas as pd
from ydata_profiling import ProfileReport
from pathlib import Path
from datetime import datetime
import sys
import os
import wordcloud
from ydata_profiling.visualisation import plot as yp_plot

# --- WordCloud 中文支持补丁 ---
FONT_PATH = (
    Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts" / "msyh.ttc"
)

_original_wc_init = wordcloud.WordCloud.__init__

def _patched_wc_init(self, *args, **kwargs):
    if not kwargs.get("font_path"):
        kwargs["font_path"] = str(FONT_PATH)
    _original_wc_init(self, *args, **kwargs)

wordcloud.WordCloud.__init__ = _patched_wc_init

# --- 词云绘制安全补丁 (防止空间不足报错) ---
def _safe_plot_wordcloud(config, series):
    try:
        return _safe_plot_wordcloud._original(config, series)
    except ValueError as exc:
        if "Couldn't find space to draw" in str(exc):
            return None
        raise

_safe_plot_wordcloud._original = yp_plot._plot_word_cloud
yp_plot._plot_word_cloud = _safe_plot_wordcloud
# -----------------------------

# ================= 配置区 (仅在此处修改) =================
INPUT_CSV_PATH = r"D:\LocalWorkSpace\20260202_museum_data_crawling\museumschina.cn\data\pottery_details_20260305_210613.csv" 

# 输出目录 (脚本会自动在此目录下创建带时间戳的 HTML)
OUTPUT_DIR = r"D:\LocalWorkSpace\20260202_museum_data_crawling\museumschina.cn\data\analysis_reports"

# 报告标题
REPORT_TITLE = "彩陶详情页数据初步分析报告"
# =======================================================

def run_analysis():
    # 1. 路径检查与准备
    input_path = Path(INPUT_CSV_PATH)
    if not input_path.exists():
        print(f"❌ 错误：找不到输入文件 -> {input_path}")
        return

    output_folder = Path(OUTPUT_DIR)
    output_folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file_name = f"profile_{input_path.stem}_{timestamp}.html"
    output_path = output_folder / output_file_name

    if output_path.exists():
        print(f"⚠️ 警告：输出文件 {output_path} 已存在，请检查命名冲突。")
        sys.exit(1)

    # 2. 加载数据
    print(f"📂 正在加载数据: {input_path.name}...")
    try:
        # 考虑到中文路径或编码问题，显式指定 encoding
        df = pd.read_csv(input_path, encoding='utf-8-sig')
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return

    # 3. 生成分析报告
    print(f"🚀 正在生成分析报告 (数据量: {len(df)} 行)... 这可能需要 1-3 分钟。")
    
    # minimal=True 模式：如果你的数据量极大或特征极多，可以开启以跳过复杂的统计
    profile = ProfileReport(
        df, 
        title=REPORT_TITLE,
        explorative=True,
    )

    # 4. 保存结果
    try:
        profile.to_file(output_path)
        print("-" * 50)
        print(f"✅ 分析完成！")
        print(f"📄 报告位置: {output_path}")
        print("-" * 50)
    except Exception as e:
        print(f"❌ 保存报告失败: {e}")

if __name__ == "__main__":
    run_analysis()