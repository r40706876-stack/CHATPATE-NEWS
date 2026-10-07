"""
Step 1 + 2: trend पकड़ना और safety filter.

Google Trends की India feed (RSS) से trends उठाता है, हर trend की headlines देखता है,
और दुख/राजनीति/अपराध/असली-लोगों वाली खबरें अपने आप हटा देता है।
बचे हुए trends में से "मज़ाक लायक" trends को score करके ऊपर रखता है।

चलाना:
    python trends.py                 # live feed (GitHub Actions / आपके PC पर)
    python trends.py --file sample_trends.xml   # offline demo
"""
import argparse
import json
import math
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

FEED = "https://trends.google.com/trending/rss?geo=IN"
NS = {"ht": "https://trends.google.com/trending/rss"}

# --- Safety filter: इनमें से कोई शब्द headline में हो तो trend बाहर ---
BLOCK = [
    # हादसा / मौत / आपदा
    "मौत", "मृत", "हादसा", "हादसे", "दुर्घटना", "accident", "died", "death", "dead", "बाढ़", "flood",
    "भूकंप", "earthquake", "आग", "fire", "हत्या", "murder", "आत्महत्या", "suicide", "शहीद",
    # अपराध
    "रेप", "rape", "गिरफ्तार", "arrest", "हनीट्रैप", "honeytrap", "ब्लैकमेल", "blackmail", "ठगी",
    "scam", "fraud", "पुलिस", "police", "court", "कोर्ट", "हाईकोर्ट", "जेल", "आतंक", "terror",
    # राजनीति / धर्म
    "bjp", "भाजपा", "कांग्रेस", "congress", "aap", "चुनाव", "election", "मोदी", "राहुल", "मंत्री",
    "minister", "सांसद", "विधायक", "party", "पार्टी", "rnc", "democrat", "republican", "protest",
    "प्रदर्शन", "मंदिर", "मस्जिद", "धर्म", "hindu", "muslim", "जाति", "caste",
    # युद्ध
    "war", "युद्ध", "हमला", "attack", "missile", "सेना",
]

# --- मज़ाक लायक विषय: ये हों तो score बढ़ता है ---
BOOST = {
    "पैसा/घर का खर्च": ["da ", "डीए", "da,", "salary", "सैलरी", "वेतन", "pay commission", "महंगाई", "मजदूरी",
                         "price", "दाम", "पेट्रोल", "गैस", "lpg", "टमाटर", "प्याज", "pension", "पेंशन", "emi"],
    "त्योहार/मौसम": ["दिवाली", "होली", "करवा", "नवरात्र", "दशहरा", "छठ", "श्राद्ध", "बारिश", "ठंड", "गर्मी", "ग्रहण", "eclipse"],
    "tech/app": ["iphone", "launch", "upi", "whatsapp", "instagram", "ai ", "5g", "recharge"],
    "खेल": ["cricket", "क्रिकेट", "match", "vs", "world cup", "ipl", "football"],
    "मनोरंजन": ["movie", "फिल्म", "trailer", "box office", "song", "youtuber", "home tour"],
}


def fetch(path=None):
    if path:
        return open(path, encoding="utf-8").read()
    req = urllib.request.Request(FEED, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8")


def parse(xml_text):
    root = ET.fromstring(xml_text)
    out = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        traffic = item.findtext("ht:approx_traffic", default="0", namespaces=NS)
        news = []
        for n in item.findall("ht:news_item", NS):
            news.append({
                "headline": (n.findtext("ht:news_item_title", default="", namespaces=NS) or "").strip(),
                "url": n.findtext("ht:news_item_url", default="", namespaces=NS),
                "source": n.findtext("ht:news_item_source", default="", namespaces=NS),
            })
        out.append({"trend": title, "traffic": int(re.sub(r"\D", "", traffic) or 0), "news": news})
    return out


def is_hindi_or_english(text):
    # Bengali, Telugu, Tamil वगैरह की खबरें हमारी Hindi audience के लिए नहीं
    other_scripts = re.search(r"[ঀ-৿஀-௿ఀ-౿ಀ-೿ഀ-ൿ઀-૿]", text)
    return other_scripts is None


def check(t):
    blob = (t["trend"] + " " + " ".join(n["headline"] for n in t["news"])).lower()
    if not is_hindi_or_english(blob):
        return False, "दूसरी भाषा", []
    hits = [w for w in BLOCK if w.lower() in blob]
    if hits:
        return False, "blocked: " + ", ".join(hits[:3]), []
    tags = [k for k, words in BOOST.items() if any(w in blob for w in words)]
    return True, "ok", tags


def rank(trends):
    keep, dropped = [], []
    for t in trends:
        ok, why, tags = check(t)
        if ok:
            t["tags"] = tags
            # traffic (log) + मज़ाक-लायक विषय + Hindi headline का bonus
            hindi = any(re.search(r"[\u0900-\u097F]", n["headline"]) for n in t["news"])
            t["score"] = round(1000 * math.log10(t["traffic"] + 1) + 2500 * len(tags) + (1000 if hindi else 0))
            keep.append(t)
        else:
            dropped.append({"trend": t["trend"], "why": why})
    keep.sort(key=lambda x: -x["score"])
    return keep, dropped


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--file")
    ap.add_argument("--out", default="candidates.json")
    a = ap.parse_args()
    trends = parse(fetch(a.file))
    keep, dropped = rank(trends)
    print(f"कुल trends: {len(trends)} | बचे: {len(keep)} | हटाए: {len(dropped)}\n")
    for d in dropped:
        print(f"  ✗ {d['trend']:<22} {d['why']}")
    print()
    for k in keep:
        print(f"  ✓ {k['trend']:<22} score={k['score']:<6} tags={k['tags']}")
        print(f"      → {k['news'][0]['headline'][:80] if k['news'] else ''}")
    json.dump(keep, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("\nScript step को जाने वाले top 3:", ", ".join(k["trend"] for k in keep[:3]))
