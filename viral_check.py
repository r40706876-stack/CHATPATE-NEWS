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
    h7 = topics.rss_search(query, n=100, days=7)
    h2 = [h for h in h7 if _age_h(h[2]) <= 48]
    src2 = {s.strip().lower() for _, s, _ in h2}
    n = len(src2)                                         # कितने अलग अख़बार/चैनल 2 दिन में (असली test में 4 से 36 तक)
    s = 6 if n >= 25 else 5 if n >= 15 else 4 if n >= 10 else 3 if n >= 6 else 2 if n >= 3 else 1 if n else 0
    fresh = len(h2) / max(1, len(h7))                     # 7 दिन की ज़्यादातर खबरें पिछले 2 दिन की = अभी उठी है
    s += 2 if fresh >= 0.5 and len(h2) >= 5 else 1 if fresh >= 0.3 else 0
    q = _words(query)
    hit = next((t for t, _ in google_trends_today() if len(q & _words(t)) >= 1 and len(_words(t)) <= 6), None)
    s += 2 if hit else 0
    why = f"{len(src2)} अख़बार/चैनल 2 दिन में, {len(h7)} खबरें 7 दिन में" + (f", Google Trends में: {hit}" if hit else "")
    return min(10, s), why, h7[:10]


RUBRIC = """नियम (हमारे page के 19 reels के असली आँकड़ों से: मज़ाक से शुरू होने वाली reels पर skip 26-40% और 900-2.7K views;
खबर पढ़कर शुरू होने वाली पर skip 70-80% और ~120 views. लोग line 2-3 पर इसलिए भागते थे कि हर line एक ही ढाँचे की थी):
A. जुड़ाव (0-2): आम परिवार की रोज़ की आदत/जेब/रिश्ते से सीधा रिश्ता? सूखी सरकारी जानकारी = 0.
B. हँसी (0-2): गाँव-कस्बे का आदमी पहली बार सुनकर सच में हँसेगा? गहरी बात उदासी पर ख़त्म = 1, ज़बरदस्ती का मज़ाक = 0.
C. Hook (0-2): पहली line ≤ 10 शब्द, ख़ुद में मज़ाक/झटका, और चौंकाने वाला शब्द पहले 3 शब्दों में = 2; झटका देर से
   (भूमिका के बाद, जैसे "जाम से बचने के लिए बंदा उड़कर…") या खबर पढ़ने जैसा = 1;
   "खबर की headline पढ़ना"/"नमस्कार" = 0.
D. Tag की वजह (0-2): बीच में कोई line किसी पहचाने जाने वाले इंसान (दोस्त/बुआ/मम्मी/रिश्तेदार) की आदत पर इतनी सटीक कि
   देखने वाला उसे tag करे = 2; हल्की = 1; नहीं = 0. ("ये वीडियो उसको भेजो" बोलना = 0, वो share नहीं कराता.)
E. पंच (0-1): कम से कम एक मुहर वाली line (दावा + उसी शब्द का उलटा, पक्का वार) जो असली सच्चाई पर टिकी हो.
G. बहाव (0-1): दूसरी line ≤ 12 शब्द और उसमें भी पंच (Instagram graph: 3-5 सेकंड पर आधे लोग वहीं जाते थे जहाँ खबर पढ़ी
   जाती थी) + बीच में एक किरदार की छोटी कहानी (क्या किया → क्या हुआ → उलटा नतीजा) + कम से कम एक टकराव = 1;
   "वीडियो वायरल हुआ है" जैसी ख़ाली line, या अलग-अलग भाषण = 0.
F. भरोसा (0 या 1, नंबर में नहीं जुड़ता — 0 = script रद्द): तथ्य स्रोत वाले, कोई असली व्यक्ति/नेता/जाति/धर्म निशाने पर नहीं,
   मौत/चोट/हादसे पर मज़ाक नहीं."""


def prompt_connect(eps):
    slim = [{"n": i + 1, "topic": e.get("topic"), "hook": e.get("hook_text"),
             "lines": [f"{l.get('who')}: {l.get('say')}" for l in e.get("lines", [])]} for i, e in enumerate(eps)]
    return f"""तुम Instagram Reels के सख़्त जज हो (भारत, Hindi, गाँव-कस्बे के 18-45 साल के लोग). नरमी नहीं — ज़्यादातर scripts 5-6 पाती हैं.
{RUBRIC}

Scripts:
{json.dumps(slim, ensure_ascii=False, indent=1)}

हर script के लिए सिर्फ़ JSON list:
[{{"n": 1, "A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "G": 0, "F": 1, "total": 0,
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
            parts = [int(r.get(k, 0) or 0) for k in "ABCDEFG"]
            total = (sum(parts) - parts[5]) if parts[5] else 0   # F = भरोसे का दरवाज़ा, नंबर में नहीं
            eps[i]["connect"] = {"score": total, "why": r.get("why", ""), "weak": r.get("weak", ""),
                                 "fix": r.get("fix", ""), "parts": dict(zip("ABCDEFG", parts))}


def line(ep):
    t, c = ep.get("trend") or {}, ep.get("connect") or {}
    out = []
    if t:
        out.append(f"📈 Trend {t['score']}/10 — {t['why']}")
    if c:
        out.append(f"❤️ Connect {c['score']}/10 — ✅ {c['why']}  ⚠️ {c['weak']}")
    return "\n".join(out)
