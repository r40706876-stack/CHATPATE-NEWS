import re, urllib.request, urllib.parse
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"}
def get(u, data=None):
    r = urllib.request.urlopen(urllib.request.Request(u, data, UA), timeout=30)
    return r.status, r.read().decode("utf-8", "ignore")
qs = ["India Post Speed Post tariff 2025", "Sukanya Samriddhi Yojana interest rate current quarter", "registered post merged speed post 2025"]
for q in qs:
    for name, url, data in [("ddg-html", "https://html.duckduckgo.com/html/", urllib.parse.urlencode({"q": q}).encode()),
                            ("ddg-lite", "https://lite.duckduckgo.com/lite/", urllib.parse.urlencode({"q": q}).encode()),
                            ("bing", "https://www.bing.com/search?" + urllib.parse.urlencode({"q": q}), None)]:
        try:
            st, t = get(url, data)
            links = [l for l in re.findall(r'href="(https?://[^"]+)"', t) if not re.search(r"duckduckgo|bing\.com|microsoft", l)]
            print(name, "|", q[:30], "|", st, len(t), "| links:", len(links), links[:3])
        except Exception as e:
            print(name, "|", q[:30], "| ERR", str(e)[:100])
for u in ["https://www.indiapost.gov.in/", "https://www.indiapost.gov.in/Financial/Pages/Content/Post-Office-Saving-Schemes.aspx", "https://pib.gov.in/"]:
    try:
        st, t = get(u)
        print("fetch", u, st, len(" ".join(re.sub(r"<[^>]+>", " ", t).split())))
    except Exception as e:
        print("fetch", u, "ERR", str(e)[:100])
