import os

from wordcloud import WordCloud

font_path = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "msyh.ttc")

text = "山东博物馆 文物 陶器 青铜器 文化 历史" * 10

wc = WordCloud(
	font_path=font_path,
	width=800,
	height=400,
	background_color="white",
)
wc.generate(text)
output_path = "wordcloud_font_test.png"
wc.to_file(output_path)

print("Font test output:", output_path)
