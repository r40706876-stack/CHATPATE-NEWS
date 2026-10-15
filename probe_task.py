import re, urllib.parse
import news_images as n
p = n._get("https://duckduckgo.com/?" + urllib.parse.urlencode({"q": "bihar traffic challan", "iax": "images", "ia": "images"}))
print(len(p)); print(re.findall(r"vqd.{0,40}", p)[:3])
r = n.ddg_images("bihar traffic challan"); print("ddg", len(r), r[:1])
a = n.article_images("बिहार ट्रैफिक चालान"); print("art", len(a), a[:2])
try:
    rss = n._get("https://www.bing.com/news/search?q=%E0%A4%9A%E0%A4%BE%E0%A4%B2%E0%A4%BE%E0%A4%A8&format=rss&mkt=hi-IN")
    print("bing rss", len(rss), rss[:300])
except Exception as e:
    print("bing err", e)
