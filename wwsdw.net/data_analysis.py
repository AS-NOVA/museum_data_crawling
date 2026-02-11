import os
import pandas as pd
import wordcloud

LIST_PATH = "list_with_detail.csv"
OUTPUT_NAME = "analysis_report_of_" + LIST_PATH + ".html"
TITLE = "文物山东彩陶数据分析报告"

font_path = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "msyh.ttc")
_original_wc_init = wordcloud.WordCloud.__init__

def _patched_wc_init(self, *args, **kwargs):
    if not kwargs.get("font_path"):
        kwargs["font_path"] = font_path
    _original_wc_init(self, *args, **kwargs)

wordcloud.WordCloud.__init__ = _patched_wc_init

from ydata_profiling import ProfileReport
from ydata_profiling.visualisation import plot as yp_plot

def _safe_plot_wordcloud(config, series):
    try:
        return _safe_plot_wordcloud._original(config, series)
    except ValueError as exc:
        if "Couldn't find space to draw" in str(exc):
            return None
        raise

_safe_plot_wordcloud._original = yp_plot._plot_word_cloud
yp_plot._plot_word_cloud = _safe_plot_wordcloud

# 2. 读取数据 (确保编码与你爬虫保存时一致)
# 我们之前用的是 utf-8-sig，所以这里也用 utf-8-sig
df = pd.read_csv(LIST_PATH, encoding='utf-8-sig')

# 3. 创建报告时，通过 config_file 或直接设置参数来优化
# explorative=True 会生成更深度的分析
profile = ProfileReport(
    df, 
    title="TITLE", 
    explorative=True,
)

# 4. 导出报告
profile.to_file(OUTPUT_NAME)

print("报告已生成，请查看" + OUTPUT_NAME)