"""⚡ एक पंच (experiment, 25 अक्टूबर 2026) — 8-10 सेकंड की reel: HOOK + एक मुहर वाला वार, सीधा loop.

मालिक का लक्ष्य: skip ~10%, retention ~90%. vidIQ में ऐसा retention सिर्फ़ बहुत छोटी, loop होने वाली reels पर दिखा —
इसलिए ये format बाकी दोनों (🔥 बकरा बहस, 📰 वायरल खबर) के साथ रोज़ 1 विकल्प के रूप में आता है. जो चलेगा, वही बढ़ेगा.
PUNCH=0 करने पर बंद.
"""
import json
import re

import gemini
import news_writer as nw

MAX_WORDS = 32          # एक पंच: ~10-12 सेकंड तक ठीक (मालिक 28 Oct: लंबाई नहीं, मज़ा पैमाना)


def prompt_write(packs, n):
    return f"""तुम "बकरा न्यूज़" के सबसे तेज़ व्यंग्य writer हो. तथ्य (सिर्फ़ इन्हीं से, कोई नया तथ्य नहीं):
{json.dumps(packs, ensure_ascii=False, indent=1)}

{nw.SATIRE}

{nw.MUHAR}

काम: {n} अलग खबरों पर "⚡ एक पंच" scripts — पूरी reel सिर्फ़ 8-10 सेकंड, ताकि लोग पूरी देखें और अपने-आप दोबारा चले.
ढाँचा (बस 2 lines, ज़्यादा से ज़्यादा 3; कुल {MAX_WORDS} शब्द से कम):
 1. HOOK (≤ 8 शब्द, bablu या ramesh): खबर का सबसे बेतुका सच, सबसे चौंकाने वाला शब्द पहले 3 शब्दों में. जिसने खबर नहीं सुनी,
    वो भी इसी line से समझे क्या हुआ. खबर पढ़ना, "नमस्कार", pun/शब्दों का खेल — मना.
 2. वार (≤ 14 शब्द, अलग किरदार — chacha/ramesh/bablu): मुहर वाली line या दाम की टक्कर या पहचान वाली चोट — सिस्टम या किसी
    जाने-पहचाने इंसान पर. **आख़िरी शब्द hook के किसी शब्द पर लौटे** (loop), ताकि reel ख़त्म होते ही शुरू से जुड़ी लगे.
 बीच में कोई सेट-अप line नहीं, कोई "और सुनिए", "वैसे" नहीं. हर शब्द काम का.
नमूना (स्तर समझो, शब्द मत दोहराओ):
  bablu: "जापान मंगल से मिट्टी लाएगा — 2031 में."
  chacha: "तब तक हमारी गली की खुदी सड़क भी बन जाएगी… 2031 में."
सिर्फ़ JSON list:
[{{"topic": "खबर 3-6 शब्द", "breaking": "≤ 10 शब्द", "source": "प्रकाशक", "hook_screen": "≤ 5 शब्द",
  "tag_who": "किसे भेजेंगे (वो दोस्त जो…)",
  "lines": [{{"who": "bablu", "say": "...", "caption": "...", "expr": "gambhir", "visuals": ["english search", "..."], "photo_hi": ["हिंदी खोज", "..."]}},
            {{"who": "chacha", "say": "...", "caption": "...", "expr": "tanz", "punch": true, "stamp": "2-4 शब्द", "visuals": ["..."], "photo_hi": ["..."]}}],
  "caption_post": "hook + एक comment वाला सवाल + स्रोत: ... + 3-5 hashtags + (AI से बने किरदार)"}}]
"say" में अंक शब्दों में, "caption" में अंकों में."""


def finish(ep):
    lines = [l for l in ep.get("lines") or [] if l.get("who") in nw.writer.WHO and str(l.get("say", "")).strip()][:3]
    assert 2 <= len(lines) <= 3, f"lines: {len(lines)}"
    topic = str(ep.get("topic") or ep.get("breaking") or "")
    for ln in lines:
        ln["say"] = nw.plain(ln["say"])
        ln["caption"] = nw.plain(ln.get("caption") or "") or ln["say"]
        ln["expr"] = ln.get("expr") if ln.get("expr") in nw.EXPRS else "gambhir"
        ln["set"] = nw.pick_set(ln["who"], ln["say"], topic, ln.get("set") if ln.get("set") in nw.SETS_OK else "")
        ln["visuals"] = [str(v) for v in (ln.get("visuals") or []) if str(v).strip()][:3]
        ln["topic"] = topic
    words = sum(nw.nwords(l["say"]) for l in lines)
    first = lines[0]["say"].strip()
    assert nw.nwords(first) <= 14, f"hook लंबा ({nw.nwords(first)} शब्द)"
    assert words <= MAX_WORDS, f"लंबा: {words} शब्द (8-10 सेकंड = {MAX_WORDS} तक)"
    assert not re.match(r"\s*(नमस्कार|आज की खबर)", first), "नमस्कार से शुरुआत"
    assert not nw.bookish(lines), "किताबी शब्द"
    assert not any(nw.SEND.search(l["say"]) or nw.FILLER.search(l["say"]) for l in lines), "ख़ाली/भेजो वाली line"
    for ln in lines[:-1]:
        ln.pop("punch", None)
        ln.pop("stamp", None)
    if lines[-1].get("stamp"):
        lines[-1]["stamp"] = str(lines[-1]["stamp"])[:22]
    ep["lines"] = lines
    ep["format"], ep["kind"], ep["label"] = "explain", "punch", "एक पंच"
    ep["hook"] = ep["hook_text"] = first
    hs = str(ep.get("hook_screen") or "").strip()
    if hs:
        ep["hook_short"] = " ".join(hs.split()[:5])
    ep["source"] = ep.get("source") or "Google News"
    ep["hasi"] = f"⚡ {words} शब्द (~{round(words / 2.6)} सेकंड) | टैग: {ep.get('tag_who', '')}"
    return ep


def write_from(c, packs, picks, n=1):
    """पक्के तथ्यों (news_writer.gather) से n "एक पंच" scripts (1 Gemini call)."""
    raw = gemini.json_from(gemini.ask(prompt_write(packs, n + 1), json_mode=True, temperature=0.9))
    eps = []
    for ep in raw if isinstance(raw, list) else []:
        if not isinstance(ep, dict):
            continue
        try:
            eps.append(finish(json.loads(json.dumps(ep))))
        except Exception as e:                              # noqa: BLE001
            print("  एक पंच नहीं बना:", ep.get("topic"), "—", e)
    for ep in eps:
        w = set(str(ep.get("topic", "")).split())
        best = max(picks, key=lambda p: len(w & set(str(p.get("topic", "")).split()))) if picks else {}
        ep["trend"] = best.get("trend")
        ep["category"] = best.get("cat") or "other"
    return eps[:n]
