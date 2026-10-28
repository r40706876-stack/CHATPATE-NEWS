"""असली data से सीखना (29 Oct): हर post हुई reel का skip/watch/share उसकी script के साथ reel_results.json में.
writer अगली scripts से पहले lessons() पढ़ता है — कौन-सी शुरुआत जीती, कौन-सी हारी (अंदाज़ा नहीं, असली दर्शक).

Telegram पर मालिक भेजे (video पहुँचने के बाद, Instagram insights देखकर):
    डेटा skip 57 watch 6.2 share 0          ← आख़िरी भेजे गए video के लिए
    डेटा फ़ोन skip 40 watch 9                ← किसी ख़ास video के लिए (topic का कोई शब्द)
"""
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).parent
FILE, LAST = ROOT / "reel_results.json", ROOT / "last_delivered.json"
DATA_MSG = re.compile(r"^\s*(डेटा|data|डाटा)\b", re.I)


def _load():
    return json.load(open(FILE, encoding="utf-8")) if FILE.exists() else []


def delivered(ep, secs):
    """talk_episode: video Telegram पर गया — उसकी पहचान याद रखो (data बाद में इसी से जुड़ेगा)."""
    lines = [f'{l.get("who")}: {l.get("say")}' for l in ep.get("lines", [])]
    d = {"at": int(time.time()), "topic": ep.get("topic") or ep.get("title", ""), "secs": round(secs, 1),
         "cold_open": (ep.get("cold_open") or {}).get("kind", ""), "first": lines[:2], "lines": lines}
    hist = json.load(open(LAST, encoding="utf-8")) if LAST.exists() else []
    hist = [h for h in hist if h.get("topic") != d["topic"]][-19:] + [d]
    json.dump(hist, open(LAST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def _num(key, text):
    m = re.search(key + r"\D{0,8}?(\d+(?:\.\d+)?)", text, re.I)
    return float(m.group(1)) if m else None


def record(text):
    """'डेटा …' message → reel_results.json. लौटाता है जवाब (Telegram पर भेजने को) या None."""
    if not DATA_MSG.search(text):
        return None
    hist = json.load(open(LAST, encoding="utf-8")) if LAST.exists() else []
    if not hist:
        return "⚠️ अभी कोई भेजा गया video याद नहीं — data किससे जोड़ूँ?"
    words = [w for w in re.findall(r"[ऀ-ॿ]{3,}", DATA_MSG.sub("", text)) if w not in ("स्किप", "शेयर", "वॉच")]
    ep = next((h for h in reversed(hist) if any(w in h["topic"] for w in words)), hist[-1])
    row = {"topic": ep["topic"], "skip": _num(r"(skip|स्किप)", text), "watch": _num(r"(watch|वॉच|avg)", text),
           "share": _num(r"(share|शेयर)", text), "views": _num(r"(views?|व्यू)", text), "secs": ep.get("secs"),
           "cold_open": ep.get("cold_open"), "first": ep.get("first"), "lines": ep.get("lines"), "at": int(time.time())}
    if row["skip"] is None and row["watch"] is None:
        return "समझ नहीं आया 🙂 ऐसे भेजो: डेटा skip 57 watch 6.2 share 0"
    rows = [r for r in _load() if r["topic"] != row["topic"]] + [row]
    json.dump(rows, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    pct = f" (~{100 * row['watch'] / row['secs']:.0f}% देखा)" if row["watch"] and row["secs"] else ""
    return f"✅ याद रखा — {row['topic'][:40]}: skip {row['skip']}%, watch {row['watch']}s{pct}. अगली scripts इससे सीखेंगी."


def lessons(k=3):
    """writer के लिए: असली data से जीती/हारी शुरुआतें (skip कम = जीता)."""
    rows = [r for r in _load() if r.get("skip") is not None and r.get("first")]
    if not rows:
        return ""
    rows.sort(key=lambda r: r["skip"])
    out = ["हमारे page का असली data (Instagram insights) — इससे सीखो, अंदाज़े से नहीं. लक्ष्य: skip 10% से नीचे."]
    def row(r):
        w = f", औसत {r['watch']}s/{r.get('secs')}s" if r.get("watch") else ""
        return f"  skip {r['skip']}%{w}, cold open: {r.get('cold_open') or 'नहीं'} — " + " / ".join(r["first"])
    if len(rows) < 2 * k:                                  # कम data: बस सब, बिना जीत/हार का ठप्पा
        out.append("अब तक की reels (सबसे कम skip पहले):")
        out += [row(r) for r in rows]
        return "\n".join(out)
    out.append("✓ सबसे कम skip (ऐसी शुरुआत रोकती है):")
    out += [row(r) for r in rows[:k]]
    out.append("✗ सबसे ज़्यादा skip (ऐसी शुरुआत पर लोग भागे):")
    out += [row(r) for r in rows[-k:][::-1]]
    return "\n".join(out)
