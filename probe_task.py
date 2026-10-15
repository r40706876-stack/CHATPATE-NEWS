import re, urllib.parse, json, html
import news_images as n
for q in ["pothole road india", "बिहार ट्रैफिक चालान"]:
    t = n._get("https://www.bing.com/images/async?" + urllib.parse.urlencode({"q": q, "first": 0, "count": 35, "mmasync": 1, "setmkt": "en-IN"}))
    ms = re.findall(r'\bm="(\{.*?\})"', t)
    print(q, "len", len(t), "items", len(ms))
    for m in ms[:4]:
        d = json.loads(html.unescape(m)); print("  ", d.get("murl", "")[:90], "|", d.get("purl", "")[:60], "|", d.get("t", "")[:50])
