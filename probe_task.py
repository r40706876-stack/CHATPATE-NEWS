import re, urllib.parse, json, html
import news_images as n
q = "pothole road bihar"
tests = {
 "bing": "https://www.bing.com/images/search?" + urllib.parse.urlencode({"q": q, "form": "HDRSC2", "first": 1}),
 "yahoo": "https://images.search.yahoo.com/search/images?" + urllib.parse.urlencode({"p": q}),
 "google": "https://www.google.com/search?" + urllib.parse.urlencode({"q": q, "tbm": "isch", "hl": "en"}),
}
for k, u in tests.items():
    try:
        t = n._get(u)
        print(k, len(t), "murl", len(re.findall(r"murl&quot;:&quot;(.*?)&quot;", t)), "yahoo-imgurl", len(re.findall(r'"iurl":"(.*?)"', t)) , len(re.findall(r"imgurl=", t)), "jpg", len(re.findall(r"https?://[^\"' ]+?\.(?:jpg|jpeg|webp)", t)))
        print("   ", re.findall(r"murl&quot;:&quot;(.*?)&quot;", t)[:2], re.findall(r"https?://[^\"' ]+?\.(?:jpg|jpeg|webp)", t)[:3])
    except Exception as e:
        print(k, "err", repr(e)[:150])
