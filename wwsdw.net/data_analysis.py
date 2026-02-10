import os

import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import pandas as pd
import wordcloud

# 1. 解决 Matplotlib 的中文显示问题（针对报告中的图表）
# 通过显式加载字体文件，避免 Matplotlib 查找字体失败
def _set_chinese_font():
    font_dir = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
    candidates = [
        "msyh.ttc",
        "msyh.ttf",
        "simhei.ttf",
        "simsun.ttc",
        "arialuni.ttf",
    ]
    for font_file in candidates:
        font_path = os.path.join(font_dir, font_file)
        if os.path.exists(font_path):
            fm.fontManager.addfont(font_path)
            font_name = fm.FontProperties(fname=font_path).get_name()
            plt.rcParams["font.family"] = font_name
            plt.rcParams["font.sans-serif"] = [font_name]
            return font_path, font_name
    return None, None

def _force_wordcloud_font(font_path):
    if not font_path:
        return
    original_init = wordcloud.WordCloud.__init__

    def _patched_init(self, *args, **kwargs):
        if not kwargs.get("font_path"):
            kwargs["font_path"] = font_path
        original_init(self, *args, **kwargs)

    wordcloud.WordCloud.__init__ = _patched_init

font_path, font_name = _set_chinese_font()
_force_wordcloud_font(font_path)
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示异常问题

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
df = pd.read_csv('shandong_neolithic_pottery.csv', encoding='utf-8-sig')

# 3. 创建报告时，通过 config_file 或直接设置参数来优化
# explorative=True 会生成更深度的分析
profile = ProfileReport(
    df, 
    title="山东博物馆藏品数据分析报告", 
    explorative=True,
)

# 4. 导出报告
profile.to_file("analysis_report.html")

print("报告已生成，请查看 analysis_report.html")