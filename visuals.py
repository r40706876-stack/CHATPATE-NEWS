"""
असली visuals: Pixabay से खबर से जुड़े video (न मिले तो photo). Pixabay का content मुफ़्त है और Instagram पर
लगाना ठीक है (Pixabay Content License). ज़रूरी: PIXABAY_API_KEY (GitHub Secret).
"""
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
CACHE = ROOT / "visuals_cache"
_used = set()

# Hindi शब्द → Pixabay पर खोजने लायक English (तुम्हारी लिखी scripts के लिए)
HINDI = {
    "ट्रेन": "indian train", "रेल": "indian railway", "टिकट": "train station india", "शादी": "indian wedding",
    "बारात": "indian wedding", "पनीर": "indian food", "खाना": "indian food plate", "लिफाफ": "money envelope",
    "सिलेंडर": "gas cylinder", "गैस": "gas stove kitchen", "बैंक": "bank india", "लोन": "bank loan", "ईएमआई": "calculator money",
    "EMI": "calculator money", "UPI": "mobile payment india", "यूपीआई": "mobile payment india", "आधार": "id card",
    "पैसा": "indian rupee", "रुपये": "indian rupee", "₹": "indian rupee", "दाम": "market india", "महँगाई": "vegetable market india",
    "सब्ज़ी": "vegetable market india", "पेट्रोल": "petrol pump", "मोबाइल": "smartphone", "फ़ोन": "smartphone",
    "बिजली": "electricity", "दिवाली": "diwali", "दीवाली": "diwali", "नवरात्रि": "garba", "छुट्टी": "holiday",
    "स्कूल": "indian school", "परीक्षा": "exam students", "मम्मी": "indian mother kitchen", "दादी": "indian grandmother",
    "चाय": "indian tea chai", "बाज़ार": "indian market", "सरकार": "india government building", "योजना": "india village",
    "किसान": "indian farmer", "बारिश": "rain india", "सर्दी": "winter fog", "क्रिकेट": "cricket",
}


def guess(text, default="india street"):
    for k, v in HINDI.items():
        if k in text:
            return v
    return default


def _get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def _download(url, path):
    if path.exists() and path.stat().st_size > 10000:
        return path
    req = urllib.request.Request(url, headers={"User-Agent": UA if "pixabay" not in url else "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        path.write_bytes(r.read())
    return path


def fetch(query):
    """('video'|'image', path) या None. एक ही video में एक clip दोबारा नहीं."""
    key = os.getenv("PIXABAY_API_KEY")
    if not key or not query:
        return None
    CACHE.mkdir(exist_ok=True)
    q = urllib.parse.quote(re.sub(r"\s+", " ", query).strip()[:90])
    try:
        data = _get_json(f"https://pixabay.com/api/videos/?key={key}&q={q}&per_page=15&safesearch=true")
        for hit in data.get("hits", []):
            vid = f"v{hit['id']}"
            if vid in _used or hit.get("duration", 0) < 4:
                continue
            v = hit.get("videos", {})
            pick = next((v[s] for s in ("medium", "small", "large") if v.get(s, {}).get("url")), None)
            if not pick:
                continue
            _used.add(vid)
            return "video", _download(pick["url"], CACHE / f"{vid}.mp4")
    except Exception as e:                                # noqa: BLE001
        print("  Pixabay video नहीं मिला:", query, e)
    try:
        data = _get_json(f"https://pixabay.com/api/?key={key}&q={q}&image_type=photo&orientation=vertical"
                         f"&per_page=15&safesearch=true")
        for hit in data.get("hits", []):
            iid = f"i{hit['id']}"
            if iid in _used:
                continue
            _used.add(iid)
            return "image", _download(hit["largeImageURL"], CACHE / f"{iid}.jpg")
    except Exception as e:                                # noqa: BLE001
        print("  Pixabay photo नहीं मिली:", query, e)
    return None


def plan(lines, topic=""):
    """हर line का visual query: line का अपना 'visual', वरना Hindi शब्दों से अंदाज़ा, वरना पिछला."""
    out, last = [], guess(topic)
    for ln in lines:
        q = (ln.get("visual") or "").strip()
        if not q:
            g = guess(ln.get("say", "") + " " + str((ln.get("card") or {}).get("big", "")), default="")
            q = g or last
        out.append(q)
        last = q
    return out


# ---------------------------------------------------------------- सावधानी से चुनना (बिना मेल वाला clip नहीं)
STOP = {"the", "a", "of", "in", "and", "with", "on", "indian", "india"}


UA = "BakraNewsBot/1.0 (https://github.com/r40706876-stack/CHATPATE-NEWS)"   # Wikimedia की शर्त: पहचान वाला UA


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def _clean(html):
    return re.sub(r"<[^>]+>", "", html or "").strip()[:40]


def free_photos(query, want):
    """असली photos, जिनको इस्तेमाल करने की खुली इजाज़त है: Wikimedia Commons (भारत की असली जगहें/चीज़ें) + Openverse
    (Flickr वगैरह की CC photos). सिर्फ़ CC0 / Public Domain / CC BY / CC BY-SA — screen पर फ़ोटो वाले का नाम दिखेगा."""
    out = []
    q = urllib.parse.quote(query)
    try:
        pages = _get("https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search"
                     f"&gsrsearch={q}%20filetype:bitmap&gsrnamespace=6&gsrlimit=12&prop=imageinfo"
                     "&iiprop=url|extmetadata|size&iiurlwidth=1280").get("query", {}).get("pages", {})
        for pg in pages.values():
            ii = (pg.get("imageinfo") or [{}])[0]
            meta = ii.get("extmetadata", {})
            lic = (meta.get("LicenseShortName", {}).get("value") or "").lower()
            if not any(k in lic for k in ("cc0", "public domain", "cc by", "pd")) or "nc" in lic or "nd" in lic:
                continue
            if ii.get("width", 0) < 800 or not ii.get("thumburl"):
                continue
            title = pg.get("title", "").replace("File:", "").rsplit(".", 1)[0]
            words = set(re.findall(r"[a-z]+", (title + " " + _clean(meta.get("ImageDescription", {}).get("value"))).lower()))
            out.append({"id": f"w{pg.get('pageid')}", "url": ii["thumburl"], "thumb": ii["thumburl"].replace("1280px", "330px"),
                        "tags": title, "match": len(want & words) - 0.6,
                        "credit": f"फ़ोटो: {_clean(meta.get('Artist', {}).get('value')) or 'Wikimedia'} / Wikimedia ({lic.upper()})"})
    except Exception as e:                                # noqa: BLE001
        print("  Wikimedia नहीं मिला:", query, repr(e)[:80])
    try:
        res = _get(f"https://api.openverse.org/v1/images/?q={q}&license=cc0,pdm,by,by-sa&page_size=12&mature=false").get("results", [])
        for r in res:
            if (r.get("width") or 0) < 800:
                continue
            words = set(re.findall(r"[a-z]+", (r.get("title", "") + " " + " ".join(t.get("name", "") for t in r.get("tags") or [])).lower()))
            out.append({"id": f"o{r['id']}", "url": r["url"], "thumb": r.get("thumbnail") or r["url"],
                        "tags": r.get("title", "")[:60], "match": len(want & words) - 0.7,
                        "credit": f"फ़ोटो: {(r.get('creator') or '')[:30]} / {r.get('source', 'Openverse')} (CC {r.get('license', '').upper()})"})
    except Exception as e:                                # noqa: BLE001
        print("  Openverse नहीं मिला:", query, repr(e)[:80])
    return out


def candidates(query, k=7):
    """Pixabay के पहले 15 video में से tags सबसे ज़्यादा मेल खाने वाले k (thumbnail के साथ)."""
    import urllib.parse as up
    key = os.getenv("PIXABAY_API_KEY")
    if not key or not query:
        return []
    q = up.quote(re.sub(r"\s+", " ", query).strip()[:90])
    try:
        hits = _get_json(f"https://pixabay.com/api/videos/?key={key}&q={q}&per_page=20&safesearch=true").get("hits", [])
    except Exception as e:                                # noqa: BLE001
        print("  Pixabay नहीं मिला:", query, e)
        return []
    want = {w for w in query.lower().split() if w not in STOP}
    out = []
    for h in hits:
        if h.get("duration", 0) < 4 or f"v{h['id']}" in _used:
            continue
        v = h.get("videos", {})
        size = next((s for s in ("medium", "small", "large") if v.get(s, {}).get("url")), None)
        if not size:
            continue
        tags = {t.strip() for t in h.get("tags", "").lower().replace(",", " ").split()}
        out.append({"id": f"v{h['id']}", "url": v[size]["url"], "thumb": v[size].get("thumbnail") or "",
                    "tags": h.get("tags", ""), "match": len(want & tags)})
    try:                                                  # photos भी (भारत की photos videos से कहीं ज़्यादा हैं)
        ph = _get_json(f"https://pixabay.com/api/?key={key}&q={q}&image_type=photo&per_page=20&safesearch=true").get("hits", [])
    except Exception:                                     # noqa: BLE001
        ph = []
    for h in ph:
        if f"i{h['id']}" in _used:
            continue
        tags = {t.strip() for t in h.get("tags", "").lower().replace(",", " ").split()}
        out.append({"id": f"i{h['id']}", "url": h["largeImageURL"], "thumb": h.get("webformatURL", ""),
                    "tags": h.get("tags", ""), "match": len(want & tags) - 0.5})   # बराबरी पर video पहले
    out += free_photos(query, want)
    seen, uniq = set(), []
    for c in sorted(out, key=lambda c: -c["match"]):
        if c["tags"] not in seen and c["match"] >= 0.5:
            seen.add(c["tags"])
            uniq.append(c)
    return uniq[:k]


def _thumb_part(url):
    import base64
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(r.read()).decode()}}


def pick_checked(items):
    """items: [(line_text, query)] → हर एक के लिए (path या None). Gemini तस्वीरें देखकर तय करता है कि clip सच में
    line से मेल खाता है; मेल न हो तो None (तब उस line पर किरदार ही दिखेगा, बेमेल clip नहीं)."""
    import gemini
    cands = [candidates(q) for _, q in items]
    parts = [{"text": "तुम video editor हो. हर line के लिए कुछ stock video की तस्वीरें हैं. वही चुनो जो line की बात को सीधे "
                      "दिखाए (भारत/गाँव जैसा माहौल हो तो और अच्छा). थोड़ा भी बेमेल, विदेशी पहचान वाला, या अजीब हो तो -1. "
                      "असली भारत की photo (Wikimedia/Openverse) मिले और बात से मेल खाए तो उसे पहले चुनो. "
                      "सिर्फ़ JSON: {\"picks\": [line क्रम में चुनी तस्वीर का नंबर या -1]}"}]
    for i, ((text, q), cs) in enumerate(zip(items, cands)):
        parts.append({"text": f"\nLine {i + 1}: \"{text}\" (खोज: {q}) — {len(cs)} तस्वीरें:"})
        for j, c in enumerate(cs):
            try:
                parts += [{"text": f"तस्वीर {j} [{c['tags'][:50]}]:"}, _thumb_part(c["thumb"])]
            except Exception:                             # noqa: BLE001
                parts.append({"text": f"तस्वीर {j}: (नहीं खुली)"})
    try:
        picks = gemini.json_from(gemini.ask(parts, json_mode=True, temperature=0.1)).get("picks", [])
    except Exception as e:                                # noqa: BLE001  Gemini न चले: सिर्फ़ पक्के tag-मेल वाले
        print("  AI जाँच नहीं हुई, tags से चुन रहे (कम से कम 2 मेल):", repr(e)[:120])
        picks = [next((j for j, c in enumerate(cs) if c["match"] >= 2), -1) for cs in cands]
    out = []
    CACHE.mkdir(exist_ok=True)
    for i, cs in enumerate(cands):
        j = picks[i] if i < len(picks) and isinstance(picks[i], int) else -1
        if 0 <= j < len(cs):
            _used.add(cs[j]["id"])
            ext = ".mp4" if cs[j]["id"].startswith("v") else ".jpg"
            try:
                path = _download(cs[j]["url"], CACHE / f"{cs[j]['id']}{ext}")
            except Exception as e:                        # noqa: BLE001
                print("  download नहीं हुआ:", repr(e)[:80])
                out.append(None)
                continue
            if cs[j].get("credit"):
                path.with_suffix(".txt").write_text(cs[j]["credit"], encoding="utf-8")
            out.append(path)
            print(f"  ✅ clip: {items[i][1]} → {cs[j]['tags']}")
        else:
            out.append(None)
            print(f"  ❌ कोई मेल वाला clip नहीं: {items[i][1]} (किरदार ही दिखेगा)")
    return out
