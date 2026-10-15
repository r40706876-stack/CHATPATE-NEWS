"""
खबर की असली तस्वीरें — जहाँ से भी मिलें (मालिक का फ़ैसला), हर तस्वीर पर स्रोत का नाम:
  1. खबर के लेखों की मुख्य फ़ोटो (Bing News → लेख का og:image) — उसी घटना की असली तस्वीर
  2. Image search (DuckDuckGo) — line की ठोस चीज़ (गड्ढा, चालान मशीन, ट्रैफिक पुलिस…)
हर उम्मीदवार: {"id", "url", "thumb", "tags", "credit", "match", "india", "news": True}
"""
import hashlib
import html
import json
import re
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")
BAD = re.compile(r"logo|icon|avatar|sprite|placeholder|default|banner_ad|favicon|whatsapp|youtube_thumb", re.I)


def _get(url, ref=None, timeout=20):
    h = {"User-Agent": UA, "Accept-Language": "hi-IN,hi;q=0.9,en;q=0.8"}
    if ref:
        h["Referer"] = ref
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def _domain(u):
    d = urllib.parse.urlparse(u).netloc.lower()
    return d[4:] if d.startswith("www.") else d


def _id(u):
    return "n" + hashlib.md5(u.encode()).hexdigest()[:12]


def ddg_images(query, n=8):
    """DuckDuckGo image search (बिना key)."""
    try:
        page = _get("https://duckduckgo.com/?" + urllib.parse.urlencode({"q": query, "iax": "images", "ia": "images"}))
        m = re.search(r"vqd=['\"]?([\d-]+)", page) or re.search(r'vqd":"([\d-]+)"', page)
        if not m:
            print("  DDG token नहीं मिला:", query)
            return []
        data = json.loads(_get("https://duckduckgo.com/i.js?" + urllib.parse.urlencode(
            {"l": "in-en", "o": "json", "q": query, "vqd": m.group(1), "f": ",,,,,", "p": "1"}),
            ref="https://duckduckgo.com/"))
    except Exception as e:                                # noqa: BLE001
        print("  DDG नहीं चला:", query, repr(e)[:80])
        return []
    out = []
    for r in data.get("results", []):
        img, src = r.get("image", ""), r.get("url", "")
        if not img or BAD.search(img) or (r.get("width") or 0) < 600:
            continue
        out.append({"id": _id(img), "url": img, "thumb": r.get("thumbnail") or img,
                    "tags": html.unescape(r.get("title", ""))[:80], "credit": f"फ़ोटो: {_domain(src) or _domain(img)}",
                    "match": 1.5, "india": True, "news": True})
        if len(out) >= n:
            break
    return out


def article_images(query, n=6):
    """Bing News (Hindi, भारत) के लेख → हर लेख की मुख्य फ़ोटो (og:image)."""
    try:
        rss = _get("https://www.bing.com/news/search?" + urllib.parse.urlencode(
            {"q": query, "format": "rss", "mkt": "hi-IN", "setlang": "hi"}))
    except Exception as e:                                # noqa: BLE001
        print("  Bing News नहीं चला:", query, repr(e)[:80])
        return []
    links = []
    for it in re.findall(r"<item>(.*?)</item>", rss, re.S):
        link = re.search(r"<link>(.*?)</link>", it)
        title = re.search(r"<title>(.*?)</title>", it)
        if not link:
            continue
        u = html.unescape(link.group(1))
        q = urllib.parse.parse_qs(urllib.parse.urlparse(u).query)
        u = q.get("url", [u])[0]
        links.append((u, html.unescape(title.group(1)) if title else ""))
    from concurrent.futures import ThreadPoolExecutor

    def og(item):
        u, title = item
        try:
            page = _get(u, timeout=12)
        except Exception:                                 # noqa: BLE001
            return None
        m = (re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', page) or
             re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image', page))
        if not m:
            return None
        img = html.unescape(m.group(1))
        if img.startswith("//"):
            img = "https:" + img
        if BAD.search(img) or not img.startswith("http"):
            return None
        return {"id": _id(img), "url": img, "thumb": img, "tags": title[:80],
                "credit": f"फ़ोटो: {_domain(u)}", "match": 2.5, "india": True, "news": True}

    with ThreadPoolExecutor(8) as ex:
        got = [g for g in ex.map(og, links[:10]) if g]
    seen, out = set(), []
    for g in got:
        if g["url"] not in seen:
            seen.add(g["url"])
            out.append(g)
    return out[:n]
