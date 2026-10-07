"""
आज के topics इकट्ठा करो — दो तरह के:
  1. खबर:   Google Trends India (trends.py का safety filter लगा हुआ)
  2. Insta: Instagram/social पर जो अभी viral है — viral line, meme, audio, challenge
            (a) topics.txt — तुम्हारी feed से तुमने जो लिखा (सबसे भरोसेमंद, सबसे पहले)
            (b) Gemini + Google Search — "इस हफ़्ते India में क्या viral है"
            (c) Reddit r/IndianMeme — hot posts के titles

    python topics.py          → candidates_today.json
"""
import json
import os
import re
import urllib.request
from pathlib import Path

import trends

ROOT = Path(__file__).parent


def done_set():
    f = ROOT / "done.txt"
    return set(f.read_text(encoding="utf-8").splitlines()) if f.exists() else set()


def news(feed_file=None, n=6):
    try:
        keep, _ = trends.rank(trends.parse(trends.fetch(feed_file)))
    except Exception as e:                            # noqa: BLE001
        print("  Google Trends नहीं मिला:", e)
        return []
    out = []
    for t in keep[:n]:
        out.append({"kind": "news", "trend": t["trend"],
                    "headlines": [f"{x['headline']} ({x['source']})" for x in t["news"][:3]],
                    "url": (t["news"][0]["url"] if t["news"] else "")})
    return out


def manual():
    f = ROOT / "topics.txt"
    if not f.exists():
        return []
    done = done_set()
    out = []
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and line not in done:
            out.append({"kind": "insta", "source": "मेरी feed", "trend": line, "priority": True})
    return out


INSTA_PROMPT = """आज की तारीख़ के हिसाब से Google Search करके बताओ: इस हफ़्ते भारत में Instagram Reels / social media पर
Hindi/Hinglish audience के बीच क्या-क्या viral चल रहा है — viral dialogue या line, meme format, trending audio/गाना,
challenge, या कोई मज़ेदार viral वीडियो/किस्सा.
सिर्फ़ वो रखो जिन पर परिवार वाला हल्का मज़ाक बन सके.
हटाओ: हादसा, अपराध, राजनीति, धर्म, जाति, किसी असली इंसान का मज़ाक, अश्लील, नफ़रत.
सिर्फ़ JSON दो (8 items तक):
[{"trend": "छोटा नाम", "what": "ये क्या है, 1 लाइन", "line": "viral line/शब्द जैसा लोग बोलते हैं (हो तो)", "why_funny": "घर की ज़िंदगी से कैसे जुड़ेगा"}]"""


def insta_gemini():
    if not os.getenv("GEMINI_API_KEY"):
        return []
    try:
        import gemini
        items = gemini.json_from(gemini.ask(INSTA_PROMPT, search=True, temperature=0.4))
        return [dict(kind="insta", source="Gemini+Search", **{k: str(v) for k, v in it.items()}) for it in items[:8]]
    except Exception as e:                            # noqa: BLE001
        print("  Insta trends (Gemini) नहीं मिले:", e)
        return []


def insta_reddit():
    try:
        req = urllib.request.Request("https://www.reddit.com/r/IndianMeme/hot.json?limit=20",
                                     headers={"User-Agent": "Mozilla/5.0 gharkikhabar-bot"})
        with urllib.request.urlopen(req, timeout=20) as r:
            posts = json.load(r)["data"]["children"]
    except Exception as e:                            # noqa: BLE001
        print("  Reddit नहीं मिला:", e)
        return []
    bad = re.compile("|".join(map(re.escape, trends.BLOCK)), re.I)
    out = []
    for p in posts:
        d = p["data"]
        if d.get("stickied") or d.get("over_18") or bad.search(d.get("title", "")):
            continue
        out.append({"kind": "insta", "source": "r/IndianMeme", "trend": d["title"][:120], "ups": d.get("ups", 0)})
    out.sort(key=lambda x: -x["ups"])
    return out[:6]


def collect(feed_file=None):
    c = {"news": news(feed_file), "insta": manual() + insta_gemini() + insta_reddit()}
    json.dump(c, open(ROOT / "candidates_today.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"  topics: {len(c['news'])} खबरें, {len(c['insta'])} Insta trends")
    return c


if __name__ == "__main__":
    import sys
    collect(sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--file" else None)
