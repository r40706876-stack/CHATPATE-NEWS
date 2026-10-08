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
            if not title or key in seen or BAD.search(title) or recently_used(title):
                continue
            seen.add(key)
            out.append({"kind": "viral", "trend": title.rsplit(" - ", 1)[0],
                        "headlines": [title]})
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
सिर्फ़ वो जिन पर परिवार वाला हल्का मज़ाक बन सके. हादसा, अपराध, राजनीति, धर्म, जाति, किसी असली इंसान का मज़ाक, अश्लील — नहीं.
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


def collect(feed_file=None):
    c = {"viral": viral_news(), "insta": manual() + insta_gemini(), "news": news(feed_file),
         "recent": [f"{d} {cat}: {t}" for d, cat, t in history(7)]}
    json.dump(c, open(ROOT / "candidates_today.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"  topics: {len(c['viral'])} viral खबरें, {len(c['insta'])} Insta trends, {len(c['news'])} Google Trends"
          f" | हाल के: {len(c['recent'])}")
    return c


if __name__ == "__main__":
    import sys
    collect(sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--file" else None)
