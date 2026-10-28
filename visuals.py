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
    ua = UA if ("wikimedia" in url or "openverse" in url) else \
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Referer": "https://www.google.com/"})
    with urllib.request.urlopen(req, timeout=120) as r:
        path.write_bytes(r.read())
    return path


def fetch(query, line=""):
    """('video'|'image', path) या None — पुराने renderer के लिए भी अब वही सख़्त जाँच (भारत + मेल)."""
    if not query:
        return None
    p = pick_checked([(line or query, query)])[0]
    if not p:
        return None
    return ("video" if p.suffix == ".mp4" else "image"), p


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
            if re.search(r"\b1[89]\d\d\b", title) and not re.search(r"\b(199|20)\d", title):   # पुरानी ऐतिहासिक फ़ोटो
                continue
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


INDIA = re.compile(r"india|indian|hindu|hindi|bharat|delhi|mumbai|kolkata|chennai|bengal|bihar|uttar|pradesh|rajasthan|"
                   r"gujarat|punjab|kerala|tamil|karnataka|maharashtra|chhattisgarh|odisha|jharkhand|assam|haryana|"
                   r"telangana|andhra|varanasi|lucknow|jaipur|patna|bhopal|raipur|sari|saree|rupee|rickshaw|desi", re.I)


JUNK = re.compile(r"animation|animated|abstract|3d|render|illustration|cartoon|vector|graphic|motion|loop|background|"
                  r"backdrop|wallpaper|particles|ai generated|artificial intelligence|fantasy|flower|bokeh|texture|"
                  r"pattern|gradient|intro|logo|seamless|digital art|cgi", re.I)


def _pixabay(q, key, want, india_q):
    out = []
    qq = urllib.parse.quote(q)
    try:
        hits = _get_json(f"https://pixabay.com/api/videos/?key={key}&q={qq}&per_page=20&safesearch=true").get("hits", [])
    except Exception as e:                                # noqa: BLE001
        print("  Pixabay video नहीं मिला:", q, repr(e)[:80])
        hits = []
    for h in hits:
        if h.get("duration", 0) < 4 or f"v{h['id']}" in _used:
            continue
        v = h.get("videos", {})
        size = next((s for s in ("medium", "small", "large") if v.get(s, {}).get("url")), None)
        if not size:
            continue
        if JUNK.search(h.get("tags", "")):                    # animation/3D/abstract = खबर नहीं
            continue
        tags = {t.strip() for t in h.get("tags", "").lower().replace(",", " ").split()}
        out.append({"id": f"v{h['id']}", "url": v[size]["url"], "thumb": v[size].get("thumbnail") or "",
                    "tags": h.get("tags", ""), "match": len(want & tags), "india": bool(INDIA.search(h.get("tags", "")))})
    try:
        ph = _get_json(f"https://pixabay.com/api/?key={key}&q={qq}&image_type=photo&per_page=20&safesearch=true").get("hits", [])
    except Exception:                                     # noqa: BLE001
        ph = []
    for h in ph:
        if f"i{h['id']}" in _used or JUNK.search(h.get("tags", "")):
            continue
        tags = {t.strip() for t in h.get("tags", "").lower().replace(",", " ").split()}
        out.append({"id": f"i{h['id']}", "url": h["largeImageURL"], "thumb": h.get("webformatURL", ""),
                    "tags": h.get("tags", ""), "match": len(want & tags) - 0.3,
                    "india": bool(INDIA.search(h.get("tags", "")))})
    return out


def candidates(query, k=8, free=True):
    """एक खोज के लिए उम्मीदवार: पहले "<खोज> india" (भारत वाली), फिर सादी खोज — Pixabay video/photo + Wikimedia +
    Openverse. भारत की पहचान वाली (tags/title में India, राज्य, शहर…) सबसे ऊपर; विदेशी माहौल AI जाँच में कटेगा."""
    if not query:
        return []
    key = os.getenv("PIXABAY_API_KEY")
    q = re.sub(r"\s+", " ", query).strip()[:90]
    want = {w for w in q.lower().split() if w not in STOP}
    variants = [q] if INDIA.search(q) else [f"{q} india", q]
    out = []
    for i, v in enumerate(variants):
        if key:
            out += _pixabay(v, key, want, i == 0)
        for c in (free_photos(v, want) if free and i == 0 else []):
            c["india"] = bool(INDIA.search(c["tags"] + " " + c.get("credit", "")))
            out.append(c)
    for c in out:
        c["score"] = c["match"] + (2.5 if c.get("india") else 0)
    seen, uniq = set(), []
    for c in sorted(out, key=lambda c: -c["score"]):
        if c["id"] not in seen and c["tags"] not in seen and (c["match"] >= 0.5 or c.get("india")):
            seen.update((c["id"], c["tags"]))
            uniq.append(c)
    return uniq[:k]


def _thumb_part(url):
    """AI को दिखाने के लिए छोटी (320px) JPEG."""
    import base64
    import io
    from PIL import Image
    ua = UA if "wikimedia" in url else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Referer": "https://www.google.com/"})
    with urllib.request.urlopen(req, timeout=25) as r:
        im = Image.open(io.BytesIO(r.read())).convert("RGB")
    im.thumbnail((320, 320))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=80)
    return {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(buf.getvalue()).decode()}}


def pick_checked(items):
    """items: [(line_text, query)] → हर एक के लिए (path या None). Gemini तस्वीरें देखकर तय करता है कि clip सच में
    line से मेल खाता है; मेल न हो तो None (तब उस line पर किरदार ही दिखेगा, बेमेल clip नहीं)."""
    import gemini
    cands = [candidates(q) for _, q in items]
    parts = [{"text": "तुम भारत के Hindi news channel के सख़्त photo editor हो. हर line के लिए कुछ तस्वीरें हैं. नियम:\n"
                      "1. खबर भारत की है — तस्वीर में भारत दिखे (भारतीय लोग/कपड़े, Hindi/भारतीय बोर्ड, भारतीय सड़क/गाँव/दफ़्तर, ₹), "
                      "या सिर्फ़ कोई चीज़ का close-up हो जिसमें देश पता न चले (फ़ोन की screen, कैलेंडर, घड़ी, फ़ाइलें, नोट).\n"
                      "2. विदेशी पहचान = तुरंत -1: गोरे विदेशी लोग, यूरोप/अमेरिका की गलियाँ-इमारतें, बर्फ़ीले पहाड़, विदेशी पुलिस/वर्दी, "
                      "अंग्रेज़ी दुकानों वाली सड़कें, डॉलर/यूरो.\n"
                      "3. तस्वीर line की बात को सीधे दिखाए (परीक्षा = परीक्षा/छात्र/कॉपी; फ़ोन नियम = फ़ोन/कॉल; शादी योजना = भारतीय शादी). "
                      "सिर्फ़ 'ठीक-ठाक' या खूबसूरत पर बेमेल = -1.\n"
                      "शक हो तो -1 (तब वहाँ बड़े अक्षरों वाला कार्ड लगेगा, जो बेमेल तस्वीर से बेहतर है).\n"
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
        print("  AI जाँच नहीं हुई, सिर्फ़ भारत वाली + पक्के मेल वाली ले रहे:", repr(e)[:120])
        picks = [next((j for j, c in enumerate(cs) if c.get("india") and c["match"] >= 1), -1) for cs in cands]
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


# ---------------------------------------------------------------- हर line के लिए 1-2 पक्की तस्वीरें (बड़ा pool)
HSTOP = set("है हैं था थे की का के को में से पर और भी तो ही कि जो वो ये यह वह अब कर करें करना किया गया गई रहे रहा रही "
             "होता होती होगा होगी नहीं सब कुछ एक दो साफ़ कहना कहा कहते लिए साथ बाद पहले उसको उसे इस उस हमारे ज़माने "
             "वीडियो भेजो जिसका जिसकी वायरल रील रीलें रील्स सोशल मीडिया खबर ख़बर मामला लोगों लोग इंटरनेट यूजर्स यूज़र्स "
             "देखिए जानिए देखें जानें अजब गजब अनोखा ताज़ा ताजा बड़ी बड़ा viral video reel news".split())


def _stems(text):
    """मोटे शब्दों के 4-अक्षर वाले सिरे (गड्ढे/गड्ढा → गड्ढ), तस्वीर के title से मिलाने के लिए."""
    out = set()
    for w in re.findall(r"[\u0900-\u0963\u0966-\u097F]+|[A-Za-z]+", str(text).lower()):
        if len(w) >= 3 and w not in HSTOP and w not in STOP:
            out.add(w[:4])
    return out


def _hindi_keys(text):
    """Gemini न चले तो: line के 2-3 भारी शब्द (अख़बारों में खोजने के लिए)."""
    words = [w.strip("।,!?…\"'") for w in text.split()]
    keys = [w for w in words if len(w) > 3 and w not in HSTOP and re.search(r"[\u0900-\u097F]", w)]
    return " ".join(keys[:3])


def short_queries(lines, topic=""):
    """हर line के लिए: 4 छोटी English खोजें (Pixabay/Wikimedia) + 2 Hindi खबर-खोजें (अख़बारों की असली फ़ोटो के लिए)."""
    if lines and all(len(ln.get("visuals") or []) >= 2 and ln.get("photo_hi") for ln in lines):   # script ने खोजें दी हैं
        return [([" ".join(str(q).split()[:3]) for q in ln["visuals"]][:6], [str(q) for q in ln["photo_hi"]][:2])
                for ln in lines]                           # → Gemini का एक call बचा
    import gemini
    rows = "\n".join(f"{i + 1}. {ln.get('say', '')}" for i, ln in enumerate(lines))
    try:
        res = gemini.json_from(gemini.ask(
            f"खबर: {topic}\nभारत की Hindi news reel की हर line के लिए खोजें दो:\n"
            "en = 4 छोटी English stock-photo खोजें (1-3 शब्द, ठोस चीज़/जगह/लोग; लोग/जगह हों तो 'indian' जोड़ो, जैसे "
            "'indian traffic police', 'road pothole', 'sim card', 'indian wedding');\n"
            "hi = 2 Hindi खबर-खोजें (2-4 शब्द) जिनसे अख़बारों में उसी चीज़ की असली फ़ोटो मिले, जैसे 'सड़क गड्ढा बिहार', "
            "'ट्रैफिक चालान मशीन'.\n" + rows +
            '\nसिर्फ़ JSON: {"q": [{"en": ["..", "..", "..", ".."], "hi": ["..", ".."]}, ...]}',
            json_mode=True, temperature=0.3, patient=False)).get("q", [])
    except Exception as e:                                # noqa: BLE001
        print("  छोटी खोजें नहीं बनीं:", repr(e)[:100])
        res = []
    out = []
    for i, ln in enumerate(lines):
        r = res[i] if i < len(res) and isinstance(res[i], dict) else {}
        qs = [str(q) for q in r.get("en", [])][:4]
        for q in ln.get("visuals") or []:
            qs.append(" ".join(str(q).split()[:3]))
        seen, uniq = set(), []
        for q in qs:
            if q.lower() not in seen:
                seen.add(q.lower())
                uniq.append(q)
        hi = ([str(q) for q in ln.get("photo_hi") or []] + [str(q) for q in r.get("hi", [])])[:2] or [_hindi_keys(ln.get("say", ""))]
        out.append((uniq[:6], hi))
    return out


_hashes = []


def _ahash(path):
    """8x8 average hash (photo के लिए; video पर None)."""
    try:
        from PIL import Image
        if path.suffix == ".mp4":
            return None
        im = Image.open(path).convert("L").resize((8, 8))
        px = list(im.getdata())
        avg = sum(px) / 64
        return sum(1 << i for i, v in enumerate(px) if v > avg)
    except Exception:                                     # noqa: BLE001
        return None


def pick_for_lines(lines, per_line=3, pool=9, topic="", strict=False):   # 3 तक: एक तस्वीर पर देर तक न अटके
    # strict=True ("बकरा बहस"): AI ने देखकर पास न की हो तो कोई तस्वीर नहीं — पहले बिना जाँच वाली cartoon/model फ़ोटो 30 सेकंड अटकी रही
    """{line_index: [path, ...]} — हर line की सारी खोजों का एक pool, AI एक बार में देखकर हर line के लिए 2 तक चुनता है
    (भारत की / बात से सीधी जुड़ी; विदेशी पहचान वाली कभी नहीं)."""
    import gemini
    want_lines = [i for i, ln in enumerate(lines) if ln.get("_need_vis", True)]
    queries = short_queries([lines[i] for i in want_lines], topic)
    import news_images
    _tp = {}

    def topic_pool(tp):
        """इसी खबर के लेखों की असली फ़ोटो (Google News headlines से और अख़बार)."""
        if tp in _tp:
            return _tp[tp]
        imgs, seen_u = [], set()
        tqs = [tp, " ".join(str(tp).split()[:5])]
        try:
            import topics
            tqs += [h for h, _, _ in topics.rss_search(" ".join(str(tp).split()[:6]), n=5)]
        except Exception:                                                  # noqa: BLE001
            pass
        tw0 = _stems(tp)
        need = 2 if len(tw0) >= 3 else 1
        for tq in dict.fromkeys(q for q in tqs if q):
            for c in news_images.article_images(tq, n=8):
                if c["url"] in seen_u:
                    continue
                if len(tw0 & _stems(c.get("tags", ""))) < need:            # उसी खबर का लेख नहीं (दूसरी खबर की फ़ोटो) = नहीं
                    continue
                seen_u.add(c["url"])
                c["same_story"] = True
                imgs.append(c)
            if len(imgs) >= 16:
                break
        print(f"  '{str(tp)[:40]}' के लेखों से {len(imgs)} फ़ोटो")
        _tp[tp] = imgs
        return imgs

    pools = []
    for n, (i, (qs, hi)) in enumerate(zip(want_lines, queries)):
        cs, seen = [], set()
        ltopic = lines[i].get("topic") or topic                           # bulletin: हर line की अपनी खबर
        topic_imgs = topic_pool(ltopic) if ltopic else []
        L = len(topic_imgs)                                                # हर line को लेखों की अलग-अलग फ़ोटो पहले
        news = [topic_imgs[(2 * n + k) % L] for k in range(min(3, L))] if L else []
        for h in hi:                                                       # line की चीज़ वाली अख़बार-फ़ोटो
            if h and h != ltopic:
                news += news_images.article_images(h, n=4)
        lw = _stems(lines[i].get("say", "") + " " + " ".join(hi))           # line की बात
        tw = _stems(ltopic)                                                # खबर की बात
        kept = []
        for c in news:                                                     # title में न line की बात, न खबर की = बेमेल (बैंक छुट्टी, बिजली…)
            tt_ = _stems(c.get("tags", ""))
            ml, mt = len(lw & tt_), len(tw & tt_)
            if not c.get("same_story") and (ml == 0 or mt == 0):       # line-खोज वाली फ़ोटो: line और खबर दोनों से मेल ज़रूरी
                continue
            c["score"] = c["match"] + 2.5 + 1.5 * ml + 0.5 * mt
            kept.append(c)
        news = kept
        for qi, q in enumerate(qs):                                        # stock फ़ोटो सिर्फ़ AI जाँच के लिए (बिना जाँच कभी नहीं)
            for c in candidates(q, k=4, free=qi < 2):
                c["stock"] = True
                c["score"] = c.get("score", 0) - 2
                news.append(c)
        for c in sorted(news, key=lambda c: -c["score"]):
            if c["id"] not in seen and c["id"] not in _used:
                seen.add(c["id"])
                cs.append(c)
        pools.append((i, qs, cs[:pool]))
    head = ("तुम भारत के Hindi news channel के सख़्त photo editor हो. हर line के लिए कुछ तस्वीरें हैं — हर line के "
            f"लिए {per_line} तक सबसे अच्छी चुनो (सबसे अच्छी पहले). नियम:\n"
            "1. तस्वीर line की बात को सीधे दिखाए. 2. भारत दिखे (भारतीय लोग/कपड़े/सड़क/दफ़्तर/गाँव, Hindi बोर्ड, ₹) "
            "या ऐसा असली close-up जिसमें देश पता न चले (फ़ोन, सिम, कैलेंडर, फ़ाइलें, नोट, हाथ). इसी खबर के अख़बार/"
            "न्यूज़ site वाली असली फ़ोटो सबसे अच्छी. 3. विदेशी पहचान "
            "(गोरे विदेशी लोग, यूरोप-अमेरिका की गलियाँ/इमारतें, बर्फ़ीले पहाड़, डॉलर/यूरो, विदेशी पुलिस) कभी नहीं. "
            "4. animation, 3D, कार्टून, फूल-पत्ती, सजावटी background, watermark वाली, पुरानी black-and-white/ऐतिहासिक "
            "(अंग्रेज़ों के ज़माने की) तस्वीर = कभी नहीं. "
            "5. फ़िल्मी हीरो-हीरोइन/मशहूर चेहरे का portrait या photoshoot = कभी नहीं (line उसी के बारे में हो तब भी नहीं). "
            "किसी एक अनजान आदमी/औरत का posed stock portrait (कैमरे की तरफ़ मुस्कुराता model, जैसे 'बॉस', 'कर्मचारी') = नहीं — "
            "देखने वाला उसे असली इंसान समझता है; ऐसी line पर [] दो (पिछली तस्वीर चलती रहेगी). "
            "सिर्फ़ हाथ/फ़ोन वाली आम stock तस्वीर तभी, जब line सच में फ़ोन/screen की बात करे. "
            "बड़े अक्षरों/headline/thumbnail text वाली तस्वीर (दूसरे channel का title छपा हो) = नहीं — screen पर कटा-फटा text दिखता है. "
            "6. सुंदर पर बेमेल = नहीं. कोई ठीक न हो तो उस line के लिए [] दो.\n"
            "साथ में \"hero\": इन सब तस्वीरों में से वो एक, जो reel के पहले सेकंड में सबसे ज़्यादा रोके — असली घटना/हरकत "
            "दिखे (लोग कुछ अजीब/मज़ेदार करते हुए), ख़ाली सड़क/इमारत/logo नहीं. ज़रूरी: वो तस्वीर जो खबर की **सबसे अजीब/"
            "अनोखी चीज़** दिखाए (जैसे 'उड़कर दफ़्तर' = उड़ता आदमी), आम माहौल नहीं (ट्रैफिक जाम, भीड़, सड़क, इमारत — ये रोज़ "
            "दिखते हैं, पहले सेकंड पर रोकते नहीं; 'उड़कर ऑफिस' reel पर जाम की फ़ोटो पहले लगी तो 51% लोग भागे). उसी घटना का video clip हो तो "
            "वही सबसे पहले (हरकत रोकती है); \"score\" 0-10.\n"
            'सिर्फ़ JSON: {"picks": [[पहली line के नंबर], [दूसरी line के नंबर], ...], '
            '"hero": {"line": line नंबर (1 से), "pick": तस्वीर नंबर, "score": 0-10}}')
    picks, heroes = [], []
    for b0 in range(0, len(pools), 3):                     # 3-3 lines, हर line की 9 तक तस्वीरें (पहले 2×14) — कम Gemini calls
        batch = pools[b0:b0 + 3]
        parts = [{"text": head}]
        for n, (i, qs, cs) in enumerate(batch):
            parts.append({"text": f"\nLine {n + 1}: \"{lines[i].get('say', '')}\" — {len(cs)} तस्वीरें:"})
            for j, c in enumerate(cs):
                try:
                    parts += [{"text": f"तस्वीर {j} [{c['tags'][:50]}]:"}, _thumb_part(c["thumb"])]
                except Exception:                         # noqa: BLE001
                    parts.append({"text": f"तस्वीर {j}: (नहीं खुली)"})
        got = None
        for attempt in range(1):
            try:
                res = gemini.json_from(gemini.ask(parts, json_mode=True, temperature=0.1, patient=False))
                got = res.get("picks", [])
                hr = res.get("hero") or {}
                try:
                    hl, hp, hs = int(hr.get("line", 0)) - 1, int(hr.get("pick", -1)), float(hr.get("score", 0))
                    if 0 <= hl < len(batch) and 0 <= hp < len(batch[hl][2]):
                        heroes.append((hs, b0 + hl, hp))
                except (TypeError, ValueError):
                    pass
                break
            except gemini.QuotaOver:
                break
            except Exception as e:                        # noqa: BLE001
                print("  AI जाँच में गड़बड़, दोबारा:", repr(e)[:100])
        if got is None and strict:
            # पहले: Gemini का कोटा ख़त्म = कोई तस्वीर नहीं = ऊपर पूरी video काला text-card (28 Oct: real_visual_lines 0).
            # अब: इसी खबर के अख़बार-लेख की अपनी मुख्य फ़ोटो (same_story, title में खबर के 2+ शब्द) बिना AI जाँच भी चलेगी —
            # वो उसी घटना की असली फ़ोटो होती है. stock फ़ोटो अब भी बिना जाँच कभी नहीं.
            print("  AI जाँच नहीं हुई — strict: सिर्फ़ इसी खबर के लेखों की असली फ़ोटो")
            got = [[j for j, c in enumerate(cs) if c.get("same_story") and not c.get("stock")
                    and len(_stems(lines[i].get("topic") or topic) & _stems(c.get("tags", ""))) >= 2][:per_line]
                   for i, _, cs in batch]
        if got is None:                                 # AI नहीं चला: बिना देखे कुछ नहीं लगाते — सिर्फ़ भारत वाली पक्की photo
            print("  AI जाँच नहीं हुई — खबर/search वाली असली फ़ोटो (search engine का मेल), वरना भारत वाली पक्की photo")
            got = [[j for j, c in enumerate(cs) if c.get("news") and not c.get("stock")
                    and len(_stems(lines[i].get("topic") or topic) & _stems(c.get("tags", ""))) >= 2][:per_line]
                   for i, _, cs in batch]
        picks += [got[n] if n < len(got) else [] for n in range(len(batch))]
    CACHE.mkdir(exist_ok=True)
    out, where = {}, {}
    for n, (i, qs, cs) in enumerate(pools):
        got = []
        sel = picks[n] if n < len(picks) and isinstance(picks[n], list) else []
        for j in sel[:per_line]:
            if not isinstance(j, int) or not 0 <= j < len(cs) or cs[j]["id"] in _used:
                continue
            c = cs[j]
            ext = ".mp4" if c["id"].startswith("v") else ".jpg"
            try:
                path = _download(c["url"], CACHE / f"{c['id']}{ext}")
            except Exception as e:                        # noqa: BLE001
                print("  download नहीं हुआ:", repr(e)[:80])
                continue
            h = _ahash(path)
            if h is not None and any(bin(h ^ x).count("1") <= 6 for x in _hashes):   # वही फ़ोटो दूसरी site से = दोबारा नहीं
                print("  एक जैसी फ़ोटो छोड़ी:", c.get("credit", ""))
                continue
            if h is not None:
                _hashes.append(h)
            _used.add(c["id"])
            if c.get("credit"):
                path.with_suffix(".txt").write_text(c["credit"], encoding="utf-8")
            got.append(path)
            where[(n, j)] = path
        if not got and not strict:                        # कोई नहीं: इसी खबर के लेख की बची फ़ोटो — सिर्फ़ जब title में खबर के
            tw_ = _stems(lines[i].get("topic") or topic)   # कम से कम 2 असली शब्द हों (वरना पिछली तस्वीर चलती रहे, बेमेल नहीं)
            for c in cs:
                if c.get("same_story") and c["id"] not in _used and len(tw_ & _stems(c.get("tags", ""))) >= 2:
                    try:
                        path = _download(c["url"], CACHE / f"{c['id']}.jpg")
                    except Exception:                     # noqa: BLE001
                        continue
                    _used.add(c["id"])
                    if c.get("credit"):
                        path.with_suffix(".txt").write_text(c["credit"], encoding="utf-8")
                    got.append(path)
                    break
        out[i] = got
        print(f"  line {i + 1}: {len(got)} तस्वीर ({', '.join(qs[:4])})" + ("" if got else "  ❌"))
    # सबसे दमदार तस्वीर (असली घटना) पहले सेकंड पर — पहले वो 30वें सेकंड पर आती थी, जब तक लोग जा चुके होते थे
    heroes.sort(reverse=True)
    for hs, hn, hp in heroes:
        hpath = where.get((hn, hp))
        if not hpath or not pools or hs < 5:
            continue
        first_i, hero_i = pools[0][0], pools[hn][0]
        if hero_i != first_i and len(out.get(hero_i, [])) > 1:
            out[hero_i] = [p for p in out[hero_i] if p != hpath]
        out[first_i] = [hpath] + [p for p in out.get(first_i, []) if p != hpath][:per_line - 1]
        print(f"  ⭐ सबसे दमदार तस्वीर पहले सेकंड पर: line {hn + 1} से ({hs}/10)")
        break
    return out
