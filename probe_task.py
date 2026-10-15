import re, urllib.parse, json
import news_images as n
q = "pothole road india"
p = n._get("https://duckduckgo.com/?" + urllib.parse.urlencode({"q": q, "iax": "images", "ia": "images"}))
v = re.search(r"vqd=['\"]?([\d-]+)", p).group(1)
for url in ["https://duckduckgo.com/i.js?" + urllib.parse.urlencode({"l": "in-en", "o": "json", "q": q, "vqd": v, "f": ",,,,,", "p": "1"}),
            "https://duckduckgo.com/i.js?" + urllib.parse.urlencode({"l": "wt-wt", "o": "json", "q": q, "vqd": v, "p": "1"})]:
    try:
        t = n._get(url, ref="https://duckduckgo.com/")
        print("len", len(t), t[:400])
        d = json.loads(t); print("results", len(d.get("results", [])), [(r.get("width"), r.get("image")[:80]) for r in d["results"][:3]])
    except Exception as e:
        print("err", repr(e)[:300])
