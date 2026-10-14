"""
Viral जाँच — हर खबर/script को नंबर, अंदाज़े से नहीं:
  1. Trend (0-10, Gemini के बिना, free): पिछले 2 दिन में कितने अलग अख़बारों ने छापा + 7 दिन के मुकाबले ताज़गी
     + आज के Google Trends (India) में है या नहीं.  → लिखने से पहले ही कमज़ोर खबरें बाहर.
  2. Connect (0-10, Gemini का 1 call, तीनों scripts एक साथ): नियम उन Hindi reels से बने हैं जो अपने creator की आम reel से
     8x–200x चलीं (vidIQ, जून–अक्टूबर 2026): जेब/रोज़ की ज़िंदगी, सच्ची भड़ास, 3 सेकंड का hook, "इसको भेजो" वाली वजह.
  पास: trend ≥ TREND_MIN और connect ≥ CONNECT_MIN. बाकी Telegram तक पहुँचती ही नहीं.
"""
import json
import re
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

TREND_MIN, CONNECT_MIN = 4, 7
_today = None


def _words(s):
    return {w for w in re.findall(r"[ऀ-ॿ]+|[A-Za-z0-9]+", s.lower()) if len(w) > 2}


def google_trends_today():
    global _today
    if _today is None:
        try:
            import trends
            _today = [(t["trend"], t.get("traffic", 0)) for t in trends.parse(trends.fetch())]
        except Exception as e:                            # noqa: BLE001
            print("  Google Trends नहीं मिला:", e)
            _today = []
    return _today


def _age_h(d):
    try:
        return (datetime.now(timezone.utc) - parsedate_to_datetime(d + " GMT")).total_seconds() / 3600
    except Exception:                                     # noqa: BLE001
        return 999


def trend(query):
    """(score 0-10, कारण, headlines) — headlines आगे तथ्यों के सबूत में काम आती हैं."""
    import topics
    h7 = topics.rss_search(query, n=60, days=7)
    h2 = [h for h in h7 if _age_h(h[2]) <= 48]
    src2 = {s.strip().lower() for _, s, _ in h2}
    s = 0
    s += 5 if len(src2) >= 8 else 4 if len(src2) >= 5 else 2 if len(src2) >= 3 else 1 if src2 else 0
    fresh = len(h2) / max(1, len(h7))                     # सारी खबर पिछले 2 दिन की = अभी उठी है
    s += 2 if fresh >= 0.6 and len(h2) >= 3 else 1 if fresh >= 0.3 else 0
    q = _words(query)
    hit = next((t for t, _ in google_trends_today() if len(q & _words(t)) >= 1 and len(_words(t)) <= 6), None)
    s += 3 if hit else 0
    why = f"{len(src2)} अख़बार/चैनल 2 दिन में, {len(h7)} खबरें 7 दिन में" + (f", Google Trends में: {hit}" if hit else "")
    return min(10, s), why, h7[:10]


RUBRIC = """नियम (ये उन Hindi Instagram reels से निकले हैं जो अपने creator की आम reel से 8 से 200 गुना ज़्यादा चलीं):
A. जेब / रोज़ की ज़िंदगी (0-3): गाँव-कस्बे के आम परिवार के पैसे, काम, बिजली-पानी, फ़ोन, बैंक, नौकरी पर सीधा असर?
   3 = हर घर पर आज ही असर; 1 = कुछ लोगों पर; 0 = दूर की बात (शेयर बाज़ार, विदेश, किसी सेलिब्रिटी का बयान).
B. सच्ची भावना (0-2): देखने वाला सोचे "अरे! ये तो मेरे साथ भी होता है" — सिस्टम पर झुँझलाहट, हैरानी, राहत. ज़बरदस्ती का मज़ाक = 0.
C. Hook (0-2): पहली line 12 शब्द से कम, सवाल या झटका, 3 सेकंड में मुद्दा साफ़. "नमस्कार, आज हम बात करेंगे…" = 0.
D. भेजने की वजह (0-1): किसी ख़ास इंसान को भेजने/tag करने का साफ़ कारण (जैसे "OTP बताने वाले को भेजो").
E. असली हँसी (0-1): punchline किसी असली सच्चाई पर टिकी है (जैसे "पहले चोर घर में घुसता था, अब फ़ोन से निकल जाता है"),
   सिर्फ़ शब्दों का खेल या "हाहा" नहीं.
F. भरोसा (0-1): तथ्य स्रोत वाले, कोई असली व्यक्ति/नेता/जाति/धर्म निशाने पर नहीं. यहाँ 0 = script रद्द."""


def prompt_connect(eps):
    slim = [{"n": i + 1, "topic": e.get("topic"), "hook": e.get("hook_text"),
             "lines": [f"{l.get('who')}: {l.get('say')}" for l in e.get("lines", [])]} for i, e in enumerate(eps)]
    return f"""तुम Instagram Reels के सख़्त जज हो (भारत, Hindi, गाँव-कस्बे के 18-45 साल के लोग). नरमी नहीं — ज़्यादातर scripts 5-6 पाती हैं.
{RUBRIC}

Scripts:
{json.dumps(slim, ensure_ascii=False, indent=1)}

हर script के लिए सिर्फ़ JSON list:
[{{"n": 1, "A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0, "total": 0,
   "why": "एक लाइन: सबसे बड़ी ताकत", "weak": "एक लाइन: सबसे बड़ी कमी", "fix": "कमी दूर करने का ठोस सुझाव"}}]"""


def connect(eps):
    import gemini
    try:
        res = gemini.json_from(gemini.ask(prompt_connect(eps), json_mode=True, temperature=0.2))
    except gemini.QuotaOver:
        raise
    except Exception as e:                                # noqa: BLE001
        print("  connect जाँच नहीं हुई:", repr(e)[:150])
        return
    for r in res if isinstance(res, list) else []:
        i = int(r.get("n", 0)) - 1
        if 0 <= i < len(eps):
            parts = [int(r.get(k, 0) or 0) for k in "ABCDEF"]
            total = sum(parts) if parts[5] else 0
            eps[i]["connect"] = {"score": total, "why": r.get("why", ""), "weak": r.get("weak", ""),
                                 "fix": r.get("fix", ""), "parts": dict(zip("ABCDEF", parts))}


def line(ep):
    t, c = ep.get("trend") or {}, ep.get("connect") or {}
    out = []
    if t:
        out.append(f"📈 Trend {t['score']}/10 — {t['why']}")
    if c:
        out.append(f"❤️ Connect {c['score']}/10 — ✅ {c['why']}  ⚠️ {c['weak']}")
    return "\n".join(out)
