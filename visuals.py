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
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
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
