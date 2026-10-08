"""
आज के topics — तीन तरह के, और पिछले episodes से अलग:
  1. viral:  Google News पर "सोशल मीडिया पर वायरल" वाली ताज़ा खबरें (जो लोग reels/WhatsApp पर देख रहे हैं)
  2. insta:  Instagram पर अभी क्या चल रहा है — topics.txt (तुम्हारी feed) + Gemini + Google Search
  3. news:   Google Trends India (safety filter के साथ)
done.txt में हर episode "तारीख|category|topic" लिखा जाता है; हाल के topics/categories दोबारा नहीं आते.
"""
import datetime as dt
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import trends

ROOT = Path(__file__).parent
BAD = re.compile("|".join(map(re.escape, trends.BLOCK)), re.I)
EXTRA_RECENT = []                                    # अभी-अभी रिजेक्ट हुई scripts के topics
# असली इंसान/celebrity का बयान — इस पर घर वाली हँसी नहीं बनती
CELEB = re.compile(r"बोले|बोलीं|ने कहा|बयान|अभिनेता|अभिनेत्री|एक्ट्रेस|actor|actress|फ़ैन|फैन|बच्चन|चोपड़ा|"
                   r"मंत्री|सांसद|विधायक|नेता|पार्टी|चुनाव|पुलिस|गिरफ़्तार|गिरफ्तार|मौत|हत्या|हादसा", re.I)
WEATHER = re.compile(r"मौसम|बारिश|आंधी|weather|rain|ठंड|गर्मी|तूफ़ान|तूफान|imd|ओले", re.I)


def history(days=7):
    """[(date, category, topic)] पिछले कुछ दिनों के episodes."""
    f = ROOT / "done.txt"
    out = []
    if not f.exists():
        return out
    cut = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    for line in f.read_text(encoding="utf-8").splitlines():
        p = line.split("|")
        if len(p) >= 3 and p[0] >= cut:
            out.append((p[0], p[1], "|".join(p[2:])))
    return out


def done_words():
    f = ROOT / "done.txt"
    return f.read_text(encoding="utf-8") if f.exists() else ""


def _words(s):
    stop = {"में", "की", "का", "के", "से", "और", "है", "पर", "को", "ने", "the", "and"}
    return {w.strip(".,!?:;\"'()|-") for w in s.lower().split()} - stop - {""}


def recently_used(text, days=4):
    words = {w for w in _words(text) if len(w) >= 3}
    for _, _, topic in history(days):
        if len(words & _words(topic)) >= 2:
            return True
    return False


def weather_recent():
    return any(c == "weather" or WEATHER.search(t) for _, c, t in history(3))


def news(feed_file=None, n=6):
    try:
        keep, _ = trends.rank(trends.parse(trends.fetch(feed_file)))
    except Exception as e:                            # noqa: BLE001
        print("  Google Trends नहीं मिला:", e)
        return []
    out, skip_weather = [], weather_recent()
    for t in keep:
        blob = t["trend"] + " " + " ".join(x["headline"] for x in t["news"])
        if recently_used(blob) or (skip_weather and WEATHER.search(blob)):
            continue
        out.append({"kind": "news", "trend": t["trend"],
                    "headlines": [f"{x['headline']} ({x['source']})" for x in t["news"][:3]]})
        if len(out) >= n:
            break
    return out


def viral_news(n=8):
    """Google News: सोशल मीडिया पर वायरल हुई ताज़ा खबरें (हल्की-फुल्की)."""
    out, seen = [], set()
    for q in ("सोशल मीडिया पर वायरल", "वायरल वीडियो इंस्टाग्राम", "trending reel viral India"):
        url = ("https://news.google.com/rss/search?q=" + urllib.parse.quote(q + " when:2d")
               + "&hl=hi&gl=IN&ceid=IN:hi")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                root = ET.fromstring(r.read())
        except Exception as e:                        # noqa: BLE001
            print("  Google News नहीं मिला:", e)
            continue
        for it in root.iter("item"):
            title = (it.findtext("title") or "").strip()
            key = title[:40]
            if not title or key in seen or BAD.search(title) or CELEB.search(title) or recently_used(title):
                continue
            seen.add(key)
            out.append({"kind": "viral", "trend": title.rsplit(" - ", 1)[0],
                        "headlines": [title]})
    return out[:n]


KAAM_QUERIES = ("नया नियम लागू", "LPG सिलेंडर", "बैंक नियम बदलाव", "UPI नया नियम", "सरकारी योजना आवेदन",
                "रेलवे नया नियम टिकट", "छुट्टी घोषित स्कूल बैंक", "पेट्रोल डीजल दाम", "महंगाई भत्ता", "मोबाइल रिचार्ज महंगा")


def kaam_news(per_query=4, n=24):
    """काम की खबरें: जेब, नियम, बैंक, गैस, ट्रेन, योजना, छुट्टी (पिछले 3 दिन)."""
    out, seen = [], set()
    for q in KAAM_QUERIES:
        url = ("https://news.google.com/rss/search?q=" + urllib.parse.quote(q + " when:3d") + "&hl=hi&gl=IN&ceid=IN:hi")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                root = ET.fromstring(r.read())
        except Exception as e:                        # noqa: BLE001
            print("  काम की खबर नहीं मिली:", q, e)
            continue
        k = 0
        for it in root.iter("item"):
            title = (it.findtext("title") or "").strip()
            key = title[:40]
            if not title or key in seen or BAD.search(title) or CELEB.search(title) or recently_used(title):
                continue
            seen.add(key)
            out.append({"kind": "kaam", "trend": title.rsplit(" - ", 1)[0], "source": title.rsplit(" - ", 1)[-1],
                        "date": (it.findtext("pubDate") or "")[:16]})
            k += 1
            if k >= per_query:
                break
    return out[:n]


def manual():
    f = ROOT / "topics.txt"
    if not f.exists():
        return []
    done = done_words()
    return [{"kind": "insta", "source": "मेरी feed", "trend": l.strip(), "priority": True}
            for l in f.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#") and l.strip() not in done]


INSTA_PROMPT = """आज ({today}) Google Search करके पता करो: पिछले 7 दिनों में भारत में Instagram Reels पर Hindi/Hinglish
audience के बीच क्या viral है. ठोस नाम चाहिए, आम बातें नहीं:
- viral dialogue या line (जैसे लोग comments में लिख रहे हैं)
- trending audio/गाना जिस पर reels बन रहे हैं
- meme format या challenge
- कोई viral वीडियो/किस्सा जिस पर सब मज़ाक कर रहे हैं
सिर्फ़ वो जिन पर परिवार वाला हल्का मज़ाक बन सके (किसी celebrity/नेता का बयान या gossip नहीं). हादसा, अपराध, राजनीति, धर्म, जाति, किसी असली इंसान का मज़ाक, अश्लील — नहीं.
इनसे अलग रखो (हाल में बन चुके): {recent}
सिर्फ़ JSON (8 items तक):
[{{"trend": "छोटा नाम", "what": "क्या है, 1 लाइन", "line": "viral line जैसी लोग बोलते हैं", "why_funny": "घर से कैसे जुड़ेगा"}}]"""


def insta_gemini():
    if not os.getenv("GEMINI_API_KEY"):
        return []
    try:
        import gemini
        recent = ", ".join(t for _, _, t in history(10)) or "कुछ नहीं"
        p = INSTA_PROMPT.format(today=dt.date.today().isoformat(), recent=recent)
        items = gemini.json_from(gemini.ask(p, search=True, temperature=0.4))
        out = [dict(kind="insta", source="Gemini+Search", **{k: str(v) for k, v in it.items()}) for it in items[:8]]
        return [i for i in out if not BAD.search(i["trend"] + i.get("what", ""))]
    except Exception as e:                            # noqa: BLE001
        print("  Insta trends (Gemini) नहीं मिले:", e)
        return []


# त्योहार/मौसम — Instagram पर हर साल इन्हीं दिनों सबसे ज़्यादा comedy reels चलती हैं (2026 की तारीख़ें)
CALENDAR = [
    ("2026-10-01", "2026-10-20", "नवरात्रि (11-20 अक्टूबर)", "गरबा-डांडिया की तैयारी, नौ दिन व्रत, मम्मी का व्रत वाला खाना, कपड़ों पर ख़र्च"),
    ("2026-10-12", "2026-10-21", "दशहरा (20 अक्टूबर)", "रावण दहन, मेला, बच्चों की ज़िद, घर का 'रावण' कौन"),
    ("2026-10-10", "2026-11-07", "दिवाली की सफ़ाई", "पूरे घर की सफ़ाई, पुराना सामान, कबाड़ी, छत/टांड़, मम्मी का हुक्म"),
    ("2026-10-20", "2026-10-29", "करवा चौथ (29 अक्टूबर)", "चाँद का इंतज़ार, पति का व्रत, सरगी, मेहंदी, गिफ़्ट की उम्मीद"),
    ("2026-10-15", "2026-11-06", "दिवाली बोनस और सेल", "ऑफ़िस बोनस का इंतज़ार, ऑनलाइन सेल, कार्ट, मिठाई के डिब्बे घूमना"),
    ("2026-10-25", "2026-11-06", "धनतेरस (6 नवंबर)", "बर्तन/सोना खरीदना, बजट, 'कुछ तो लेना पड़ता है'"),
    ("2026-10-28", "2026-11-09", "दिवाली (8 नवंबर)", "पटाखे, रंगोली, रिश्तेदार, सोनपापड़ी का डिब्बा, बिजली की झालर"),
    ("2026-11-08", "2026-11-12", "भाई दूज (11 नवंबर)", "भाई-बहन, गिफ़्ट, पैसे का लिफ़ाफ़ा"),
    ("2026-10-15", "2026-12-15", "सर्दी शुरू", "रज़ाई/स्वेटर निकालना, नहाने से बचना, गीज़र, मम्मी की 'स्वेटर पहन'"),
    ("2026-11-01", "2027-02-28", "शादी का सीज़न", "रिश्तेदार, शगुन, शादी का खाना, 'बेटा तुम्हारी कब'"),
]
EVERGREEN = [
    ("WiFi और मम्मी", "मम्मी का WiFi बंद करना, password, 'फ़ोन रख'"),
    ("बिजली का बिल", "AC, पापा का गुस्सा, 'लाइट बंद करो'"),
    ("सैलरी आई और गई", "महीने की पहली तारीख़, EMI, 25 तारीख़ के बाद की हालत"),
    ("रिश्तेदारों के सवाल", "नौकरी, शादी, नंबर, 'हमारे बेटे को देखो'"),
    ("घर का रिमोट/चार्जर", "एक चार्जर, पाँच फ़ोन; रिमोट किसके हाथ"),
    ("मेहमान आने वाले हैं", "घर की सफ़ाई, अच्छे बिस्किट छुपाना, 'बेटा नमस्ते करो'"),
]


def moments(today=None):
    d = (today or dt.date.today()).isoformat()
    out = [{"kind": "moment", "trend": name, "what": what} for a, b, name, what in CALENDAR if a <= d <= b]
    out += [{"kind": "evergreen", "trend": n, "what": w} for n, w in EVERGREEN]
    return [m for m in out if not recently_used(m["trend"] + " " + m["what"], days=3)]


def collect_news(feed_file=None):
    """काम की खबर वाले page के लिए: Gemini का कोई call नहीं (कोटा बचाओ)."""
    c = {"kaam": kaam_news(), "viral": viral_news(), "news": news(feed_file), "insta": manual(),
         "moments": [m for m in moments() if m["kind"] == "moment"],
         "recent": [f"{d} {cat}: {t}" for d, cat, t in history(10)]
         + [f"(अभी रिजेक्ट हुआ, ये बिल्कुल नहीं) {t}" for t in EXTRA_RECENT]}
    json.dump(c, open(ROOT / "candidates_today.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"  topics: {len(c['kaam'])} काम की, {len(c['viral'])} वायरल, {len(c['news'])} Trends, {len(c['moments'])} त्योहार")
    return c


def collect(feed_file=None):
    c = {"viral": viral_news(), "insta": manual() + insta_gemini(), "news": news(feed_file), "moments": moments(),
         "recent": [f"{d} {cat}: {t}" for d, cat, t in history(7)]
         + [f"(अभी रिजेक्ट हुआ, ये बिल्कुल नहीं) {t}" for t in EXTRA_RECENT]}
    json.dump(c, open(ROOT / "candidates_today.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"  topics: {len(c['viral'])} viral खबरें, {len(c['insta'])} Insta trends, {len(c['news'])} Google Trends, {len(c['moments'])} त्योहार/घर के पल"
          f" | हाल के: {len(c['recent'])}")
    return c


if __name__ == "__main__":
    import sys
    collect(sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--file" else None)
