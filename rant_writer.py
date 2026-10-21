"""
"बकरा बहस" — भड़का हुआ anchor-rant format.
Instagram पर 1-4M views वाले Hindi satire reels (vidIQ, अक्टूबर 2026) का असली ढाँचा:
  एक 'समाज' की तरफ़ से ("हम सिंगल लोग", "हम घर के बच्चे") एक बेतुकी शिकायत को राष्ट्रीय संकट बनाकर पूरी पकड़ —
  हर line पिछली से बड़ी → बेतुकी सरकारी माँग → धमकी → अंत में छोटी, घटिया, पहचानी हुई असली वजह → तकिया-कलाम.
हमारे पुराने reels "हर किरदार का एक पंच" वाले थे — अलग-अलग observations, कोई कहानी नहीं — इसलिए 2.7K पर रुक गए.

Gemini calls: news_writer.gather (खबर चुनो + पक्के तथ्य: 2) → मुद्दा-बैंक (1) → script (1) → जज (1) [+ तीखा (1)].
Visuals/आवाज़ के cue (expr, sfx, ठहराव, zoom, बड़े अक्षर) यहीं beat से तय होते हैं — Gemini पर नहीं छोड़े.
"""
import json
import re
from pathlib import Path

import gemini
import news_writer as nw
import writer

ROOT = Path(__file__).parent
GOLD = ROOT / "episodes/samples_rant.json"
BEATS = ("hook", "tathya", "saboot", "maang", "dhamki", "twist", "takiya")

# beat → (expr, sfx जब line शुरू हो, background मूड, आवाज़ का अंदाज़, line के बाद ठहराव सेकंड)
BEAT_CUE = {
    "hook":   ("hairan", "boom",   "tension", "बिल्कुल गंभीर, धीमा, हर शब्द पर ज़ोर — जैसे देश का सबसे बड़ा सवाल पूछ रहा हो", 0.0),
    "tathya": ("gambhir", "whoosh", "tension", "तेज़, साफ़, न्यूज़-रीडर जैसा", 0.0),
    "saboot": ("gussa",  "glitch", "tension", "गुस्सा बढ़ता हुआ, तेज़ रफ़्तार, आख़िरी शब्द पर ज़ोर", 0.0),
    "maang":  ("gussa",  "dhol",   "masti",   "ऐलान की तरह, जोश में, जैसे संसद में भाषण", 0.0),
    "dhamki": ("gambhir", "tick",  "tension", "अचानक बहुत धीमा, रहस्य वाला, लगभग फुसफुसाते हुए", 0.7),
    "twist":  ("hairan", "boom",   "masti",   "धमाके से, जीत वाले अंदाज़ में, आख़िरी हिस्सा ज़ोर से", 0.0),
    "takiya": ("gussa",  "thug",   "masti",   "पूरी ताक़त से चिल्लाकर, मेज़ पर हाथ मारते हुए", 0.3),
}
SAB_SFX = ["whoosh", "glitch", "pop"]                       # सबूत की हर सीढ़ी पर अलग आवाज़ (एक जैसी आवाज़ = बोरियत)

RULES = """कभी नहीं (ऐसा लिखा तो script रद्द): किसी असली इंसान/नेता/पार्टी/celebrity का नाम, धर्म, जाति, मौत/हादसा/चोट/अपराध पर
मज़ाक, औरतों के शरीर/दिखावट पर तंज़, अश्लील या गंदगी वाले जोक, झूठा तथ्य (बेतुकापन सिर्फ़ प्रतिक्रिया में, खबर में नहीं),
"वायरल हो गया/सोशल मीडिया पर" जैसे ख़ाली शब्द, "ये वीडियो भेजो/टैग करो" वाली line, "नमस्कार/आज की खबर" से शुरुआत.
बड़े नाम घसीटने हों तो पद/संस्था से (सरकार, रेलवे, बैंक वाले, मोहल्ला समिति, पापा, मम्मी, शर्मा जी) — असली नाम नहीं."""


def gold_text():
    try:
        g = json.load(open(GOLD, encoding="utf-8"))
    except Exception:                                       # noqa: BLE001
        return ""
    return "\n\n".join(f"[{e['topic']} | समाज: {e['samaj']} | माँग: {e['maang']} | twist: {e['twist']}]\n"
                       + "\n".join(f"  ({l['beat']}) {l['who']}: {l['say']}" for l in e["lines"]) for e in g)


def prompt_mudde(packs):
    """मुद्दा-बैंक: हर खबर के 3 अलग 'बेतुके मुद्दे' — script नहीं, सिर्फ़ ढाँचा. सबसे तगड़ा मुद्दा ही script बनेगा."""
    return f"""तुम "बकरा न्यूज़" के head writer हो. हमारा नया segment "बकरा बहस": बबलू (गुस्सैल TV anchor) किसी एक 'समाज' की तरफ़ से
एक छोटी-सी शिकायत को राष्ट्रीय संकट बनाकर पूरे दिल से लड़ता है. Instagram पर 1-4M views वाले Hindi reels यही करते हैं:
- "सिंगल समाज बनाम डांडिया" (2.3M): डांडिया = सिंगल लड़कों के ख़िलाफ़ साज़िश → प्रधानमंत्री, मुख्यमंत्री, विपक्ष सब इसी समाज से
  → माँग: हर डांडिया में सिंगल्स की सीट रिज़र्व → धमकी: जंतर-मंतर पर धरना → twist: धरना तब तक, जब तक हाथ में किसी लड़की
  का हाथ न हो. (असली वजह छोटी, घटिया, पहचानी हुई — यही हँसी है.)
- हमारा अपना नमूना (मालिक को पसंद):
{gold_text()}

आज की खबरें, पक्के तथ्यों के साथ:
{json.dumps(packs, ensure_ascii=False, indent=1)}

हर खबर के 3 अलग मुद्दे लिखो. हर मुद्दा:
- "samaj": किसकी तरफ़ से लड़ेंगे ("हम परदेसी", "हम EMI वाले", "हम घर के बच्चे", "हम पति लोग") — जितना छोटा और पहचाना, उतना अच्छा.
- "ilzaam": एक बेतुका इल्ज़ाम/सवाल जो सुनते ही "ये क्या बोल रहा है!" लगे (≤ 12 शब्द).
- "saboot": 3 सबूत, हर एक पिछले से बड़ा और ज़्यादा ठोस (घर/मोहल्ले की असली तस्वीर: पंखा, कबाड़ी, किटी ग्रुप, वेटिंग नंबर).
- "maang": बेतुकी पर सरकारी भाषा वाली माँग ("पचास प्रतिशत आरक्षण", "संवैधानिक अधिकार", "राष्ट्रीय अवकाश").
- "twist": धमकी का अंत — छोटी, घटिया, सबकी पहचानी हुई असली वजह/पोल (जैसे "रिश्तेदारों वाली सोनपापड़ी").
- "takiya": 3-5 शब्द का तकिया-कलाम जो आख़िर में चिल्लाया जाए (हर मुद्दे का अपना; "जवाब देना होगा…" बार-बार नहीं).
- "tag_who": सुनते ही किसका चेहरा याद आएगा.
- "score": 0-10, ईमानदारी से: twist कितना चौंकाता और हँसाता है + कितने लोग अपने घर में ये देखते हैं. ज़्यादातर 5-7.
{RULES}
सिर्फ़ JSON list, खबरों के क्रम में: [{{"topic": "...", "mudde": [{{"samaj": "...", "ilzaam": "...", "saboot": ["...", "...", "..."],
 "maang": "...", "twist": "...", "takiya": "...", "tag_who": "...", "score": 0}}]}}]"""


def prompt_write(chosen):
    return f"""तुम "बकरा न्यूज़" के head writer हो — segment "बकरा बहस" ("खबर सौ टका पक्की, अंदाज़ अधपका!").
हर खबर के लिए चुना हुआ मुद्दा और उसके पक्के तथ्य:
{json.dumps(chosen, ensure_ascii=False, indent=1)}

हमारा नमूना (ढाँचा और ऊर्जा ऐसी ही; शब्द, माँग, twist बिल्कुल मत दोहराना):
{gold_text()}

हर मुद्दे की एक script लिखो. ज़्यादातर बबलू बोलेगा (गुस्सैल anchor). चाहो तो बीच में सिर्फ़ 1 line किसी और किरदार की
(pinky = 18 की Gen-Z, ramesh = परेशान नौजवान, chacha = पुरानी सोच, dadi = नई सोच वाली दादी) — जो बबलू की बात को और भड़काए.
lines इसी क्रम में, हर line में "beat":
 1. hook (≤ 12 शब्द): मुद्दे का बेतुका इल्ज़ाम/सवाल — बिल्कुल गंभीर. खबर की headline पढ़ना नहीं.
 2. tathya (≤ 14 शब्द): असली खबर, अंक/तारीख़ हूबहू, उसी line के आख़िर में छोटा पंच. (त्योहार/आदत वाला मुद्दा हो तो वो चलन ही तथ्य है.)
 3-5. saboot ×3 (हर एक ≤ 16 शब्द): हर सबूत पिछले से बड़ा. किसी एक से पहले "और बात यहीं ख़त्म नहीं होती…" (या ऐसा ही अपना
    ठहराव-वाक्य). एक में कोई बड़ा पद/संस्था बेतुके ढंग से घसीटो ("पापा ख़ुद पिछले साल से हिस्सा माँग रहे हैं!").
 6. maang (≤ 18 शब्द): "हमारी माँग:" + बेतुकी सरकारी-भाषा वाली माँग.
 7. dhamki (≤ 7 शब्द): "और अगर माँग नहीं मानी गई…" जैसा धीमा ठहराव (अपने शब्दों में).
 8. twist (≤ 18 शब्द): धमकी का घटिया, पहचाना हुआ अंत — पूरी script का सबसे बड़ा हँसी का पल. सबसे ख़ास, ठोस चीज़ का नाम.
 9. takiya (≤ 6 शब्द): मुद्दे का तकिया-कलाम, चिल्लाकर.
कुल 85-130 शब्द (35-50 सेकंड). हर line अपने-आप में मज़ा दे — एक भी ख़ाली line नहीं. बोलचाल की देसी हिंदी, देवनागरी में;
आम English शब्द (फ़ोन, रील, ग्रुप) चलेंगे.
{RULES}

हर line में: "who", "beat", "say", "caption" (वही बात, अंक अंकों में), "visuals" (3 छोटी English खोजें जो उस line की ठोस चीज़
दिखाएँ: "indian mother cleaning ceiling fan", "kabadiwala weighing scale" — भारत की, भाव नहीं, मशहूर चेहरे नहीं),
"photo_hi" (2 Hindi खोजें, 2-4 शब्द, जिनसे इसी बात की असली फ़ोटो मिले), "stamp" (सिर्फ़ maang/twist/takiya पर: उसी line के
2-4 शब्द, जैसे "सोनपापड़ी की पोल!").
सिर्फ़ JSON list:
[{{"topic": "...", "category": "festival/money/travel/tech/rules/home/viral/other", "breaking": "6-9 शब्द, सच्ची खबर, कोई मज़ाक नहीं",
  "samaj": "...", "maang": "...", "twist": "...", "takiya": "...", "tag_who": "...", "source": "प्रकाशकों के नाम",
  "ask": "≤ 9 शब्द, comment वाला सवाल", "ticker": ["≤ 10 शब्द", "...", "..."],
  "lines": [{{"who": "bablu", "beat": "hook", "say": "...", "caption": "...", "visuals": ["...", "...", "..."], "photo_hi": ["...", "..."]}}],
  "caption_post": "hook + 'Tag करो उसको जो…' (tag_who) + comment वाला सवाल + स्रोत: ... + 4-5 hashtags + (AI से बने किरदार)"}}]"""


RUBRIC = """नंबर (कुल 10). नरमी नहीं — ज़्यादातर scripts 5-6 पाती हैं:
P. पक्ष (0-2): पूरी script एक 'समाज' की तरफ़ से ("हम…"), एक ही बेतुकी शिकायत पर टिकी — इधर-उधर के जोक नहीं.
Q. सीढ़ी (0-2): हर line पिछली से बड़ी; बीच में कोई ढीली/ख़ाली line नहीं; कोई बड़ा पद/रिश्ता बेतुके ढंग से घसीटा गया.
R. Hook (0-2): पहली line ख़ुद बेतुका इल्ज़ाम/सवाल — सुनते ही रुकना पड़े. headline पढ़ना = 0.
S. Twist (0-2): अंत में छोटी, घटिया, पहचानी हुई असली वजह — सच में चौंकाए और हँसाए. अंदाज़ा लग जाए = 1, नहीं = 0.
T. Tag (0-1): सुनते ही किसी जाने-पहचाने (मम्मी, पापा, परदेसी दोस्त, बुआ) का चेहरा याद आए.
U. पकड़ (0-1): तकिया-कलाम ज़ोरदार + हर 3-4 सेकंड नया वार.
F. भरोसा (0 या 1 — 0 = script रद्द): तथ्य सच्चे, कोई असली इंसान/नेता/धर्म/जाति निशाने पर नहीं, मौत/हादसे पर मज़ाक नहीं."""


def prompt_judge(eps):
    slim = [{"n": i + 1, "samaj": e.get("samaj"), "lines": [f"({l.get('beat')}) {l.get('who')}: {l.get('say')}" for l in e["lines"]]}
            for i, e in enumerate(eps)]
    return f"""तुम Instagram Reels के सख़्त जज हो (भारत, Hindi, 18-45 साल, गाँव-कस्बे से शहर तक). सवाल एक ही: क्या तुम ख़ुद
scroll रोककर ये पूरा देखोगे और किसी को भेजोगे?
{RUBRIC}

Scripts:
{json.dumps(slim, ensure_ascii=False, indent=1)}

सिर्फ़ JSON list: [{{"n": 1, "P": 0, "Q": 0, "R": 0, "S": 0, "T": 0, "U": 0, "F": 1, "total": 0,
  "why": "एक लाइन: सबसे बड़ी ताकत", "weak": "एक लाइन: सबसे बड़ी कमी", "fix": "ठोस सुझाव — कौन सी line, कैसे"}}]"""


def prompt_sharpen(weak):
    slim = [{"n": i + 1, "weak": (e.get("connect") or {}).get("weak", ""), "fix": (e.get("connect") or {}).get("fix", ""),
             "episode": {k: e.get(k) for k in ("topic", "category", "breaking", "samaj", "maang", "twist", "takiya", "tag_who",
                                               "source", "ask", "ticker", "lines", "caption_post")}}
            for i, e in enumerate(weak)]
    return f"""तुम "बकरा बहस" के comedy editor हो. जज की बताई कमी ("weak") और सुझाव ("fix") के हिसाब से इन scripts को और तीखा करो:
{json.dumps(slim, ensure_ascii=False, indent=1)}
{RUBRIC}
{RULES}
तथ्य, अंक, स्रोत वही. beat का क्रम वही (hook, tathya, saboot×3, maang, dhamki, twist, takiya). सबसे ज़्यादा ध्यान twist पर —
वो छोटा, घटिया, पहचाना और चौंकाने वाला हो. सिर्फ़ JSON list लौटाओ — उतने ही episodes, उसी क्रम में, वही fields."""


def finish(ep, strict=True):
    """beat से सारे cue तय करो (expr, sfx, मूड, आवाज़ का अंदाज़, ठहराव, zoom, ठप्पा, बड़े अक्षर) + पक्के नियम."""
    ep["format"], ep["label"] = "rant", "बकरा बहस"
    lines = [l for l in ep.get("lines", []) if l.get("who") in writer.WHO and str(l.get("say", "")).strip()]
    lines = [l for l in lines if not nw.SEND.search(l["say"])]
    if len(lines) > 10:                                     # ज़्यादा से ज़्यादा 10 (writer.clean की सीमा): hook + 8 + takiya
        lines = lines[:9] + lines[-1:]
    ep["lines"] = lines
    topic = str(ep.get("topic") or ep.get("breaking") or "")
    sab = 0
    for i, ln in enumerate(lines):
        b = ln.get("beat") if ln.get("beat") in BEATS else ("hook" if i == 0 else "takiya" if i == len(lines) - 1 else "saboot")
        ln["beat"] = b
        expr, sfx, mood, voice, pause = BEAT_CUE[b]
        if b == "saboot":
            sfx = SAB_SFX[sab % len(SAB_SFX)]
            sab += 1
        if ln["who"] != "bablu" and b in ("saboot", "tathya"):  # दूसरे किरदार का बीच में कूदना = TV glitch
            sfx = "glitch"
        ln.update(expr=expr, sfx=sfx, mood=mood, delivery=voice)
        if pause:
            ln["pause_after"] = pause
        cap = str(ln.get("caption") or "")
        if len(re.findall(r"[ऀ-ॿ]", cap)) < len(re.findall(r"[A-Za-z]", cap)) or len(cap) < 4:
            ln["caption"] = ln["say"]
        ln["visuals"] = [str(v) for v in (ln.get("visuals") or []) if str(v).strip()][:3]
        if ln["visuals"]:
            ln["visual"] = ln["visuals"][0]
        ln["photo_hi"] = [str(v) for v in (ln.get("photo_hi") or []) if str(v).strip()][:2]
        ln["set"] = nw.pick_set(ln["who"], ln["say"], topic, "studio" if ln["who"] == "bablu" else "")
        ln.pop("card", None)
        ln["punch"] = b in ("maang", "dhamki", "twist", "takiya")       # इन पर चेहरे पर zoom
        st = str(ln.get("stamp") or "").strip()
        if b in ("maang", "twist", "takiya"):              # ठप्पा: Gemini का, वरना मुद्दे के शब्द (line के आख़िरी आधे-अधूरे शब्द नहीं)
            fb = {"maang": ep.get("maang"), "twist": ep.get("twist"), "takiya": ln["say"]}[b] or ln["say"]
            words, out = str(st or fb).replace("!", "").split(), ""
            for w in words:                                 # पूरे शब्द, 27 अक्षर तक (≈800px)
                if len((out + " " + w).strip()) > 27:
                    break
                out = (out + " " + w).strip()
            ln["stamp"] = out + "!"
        else:
            ln.pop("stamp", None)
        if b == "maang":                                    # ऊपर की screen पर बड़े अक्षरों में माँग (उसी वक़्त, पहले नहीं)
            ln["big"], ln["sub"] = "हमारी माँग", " ".join(str(ep.get("maang") or ln["say"]).split()[:6])[:34]
    ep = writer.clean(ep, strict=False)
    lines = ep["lines"]
    first = lines[0]["say"].strip()
    ep["hook"] = ep["hook_text"] = first if nw.nwords(first) <= 16 else " ".join(first.split()[:14]) + "…"
    tk = ep.get("ticker") or []
    ep["ticker"] = [str(t)[:80] for t in ([tk] if isinstance(tk, str) else tk)][:4]
    ep["ask"] = str(ep.get("ask") or "")[:60]
    ep["source"] = ep.get("source") or "Google News"
    ep["poll"] = None
    ep.setdefault("key_word", "")
    ep["cast_why"] = f"समाज: {ep.get('samaj', '')} | माँग: {ep.get('maang', '')}"
    words = sum(nw.nwords(l["say"]) for l in lines)
    if strict:
        assert 7 <= len(lines) <= 10, f"lines {len(lines)} (7-10 चाहिए)"
        assert nw.nwords(first) <= 16, f"hook लंबा ({nw.nwords(first)} शब्द)"
        assert 70 <= words <= 145, f"लंबाई {words} शब्द (85-130 चाहिए)"
        assert not re.match(r"\s*(नमस्कार|आज की खबर)", first), "नमस्कार से शुरुआत"
        assert any(l["beat"] == "twist" for l in lines), "twist वाली line नहीं"
        assert lines[-1]["beat"] == "takiya", "आख़िर में तकिया-कलाम नहीं"
        bad = [l["say"] for l in lines if nw.FILLER.search(l["say"])]
        assert not bad, f"ख़ाली शब्द: {bad[0][:40]}"
    return ep


def judge(eps):
    """rant वाले rubric से नंबर; ep["connect"] उसी रूप में जैसा viral_check देता है (Telegram preview वही दिखाता है)."""
    try:
        res = gemini.json_from(gemini.ask(prompt_judge(eps), json_mode=True, temperature=0.2))
    except gemini.QuotaOver:
        raise
    except Exception as e:                                  # noqa: BLE001
        print("  जज नहीं चला:", repr(e)[:120])
        return
    for r in res if isinstance(res, list) else []:
        try:
            ep = eps[int(r.get("n", 0)) - 1]
        except (ValueError, IndexError):
            continue
        parts = {k: int(r.get(k, 0) or 0) for k in "PQRSTU"}
        total = 0 if int(r.get("F", 1) or 0) == 0 else min(10, sum(parts.values()))
        ep["connect"] = {"score": total, "why": str(r.get("why", "")), "weak": str(r.get("weak", "")),
                         "fix": str(r.get("fix", "")), "parts": parts}
    for ep in eps:                                          # नमूने से उठाया = कमज़ोर
        cp = [l["say"] for l in ep["lines"] if any(
            __import__("difflib").SequenceMatcher(None, l["say"], g["say"]).ratio() > 0.7
            for e in json.load(open(GOLD, encoding="utf-8")) for g in e["lines"])]
        if cp and ep.get("connect"):
            ep["connect"].update(score=min(ep["connect"]["score"], 5), weak="नमूने की line उठाई: " + cp[0][:50],
                                 fix="नमूने के शब्द नहीं — इस खबर का अपना twist और तकिया-कलाम")


CONNECT_MIN = 7


def write_options(c, n=3):
    """n "बकरा बहस" scripts. c = topics.collect_news(). news_writer.QuotaOver/NoViral ऊपर जाते हैं."""
    c = nw._safe(c)
    packs, picks = nw.gather(c, n)
    return write_from(c, packs, picks, n)


def write_from(c, packs, picks, n=3):
    """पक्के तथ्यों (news_writer.gather) से n "बकरा बहस" scripts."""
    bank = gemini.json_from(gemini.ask(prompt_mudde(packs), json_mode=True, temperature=0.95))
    chosen = []
    for b, pk in zip(bank if isinstance(bank, list) else [], packs):
        mudde = sorted(b.get("mudde") or [], key=lambda m: -int(m.get("score", 0) or 0))
        if mudde:
            chosen.append({"facts": pk, "mudda": mudde[0], "dusra": mudde[1] if len(mudde) > 1 else None})
            print(f"  मुद्दा ({mudde[0].get('score')}/10): {mudde[0].get('samaj')} — {mudde[0].get('ilzaam')}")
    chosen.sort(key=lambda x: -int(x["mudda"].get("score", 0) or 0))
    chosen = chosen[:n + 1]
    c["rant_topics"] = [str(x["facts"].get("topic", "")) for x in chosen]   # "वायरल खबर" वाली इनसे अलग खबरें ले
    if not chosen:
        raise SystemExit("एक भी मुद्दा नहीं बना")
    raw = gemini.json_from(gemini.ask(prompt_write(chosen), json_mode=True, temperature=0.85))
    eps = []
    for ep in raw if isinstance(raw, list) else []:
        if not isinstance(ep, dict) or not ep.get("lines"):
            continue
        for strict in (True, False):
            try:
                fe = finish(json.loads(json.dumps(ep)), strict)
                if not strict:
                    fe["_loose"] = True
                eps.append(fe)
                break
            except Exception as e:                          # noqa: BLE001
                print(f"  rant ({'सख़्त' if strict else 'ढीला'}) नहीं बना:", ep.get("topic"), "—", e)
    if not eps:
        raise SystemExit("एक भी rant script नहीं बनी")
    for ep in eps:                                          # हर script पर उसकी खबर का trend नंबर
        w = set(str(ep.get("topic", "")).split())
        best = max(picks, key=lambda p: len(w & set(str(p.get("topic", "")).split())))
        ep["trend"] = best.get("trend")
        ep["hasi"] = f"टैग: {ep.get('tag_who', '')} | twist: {ep.get('twist', '')}"
    judge(eps)
    weak = [e for e in eps if (e.get("connect") or {}).get("score", 10) < CONNECT_MIN]
    if weak:
        try:
            again = gemini.json_from(gemini.ask(prompt_sharpen(weak), json_mode=True, temperature=0.85))
            fixed = []
            for old, new in zip(weak, again if isinstance(again, list) else []):
                try:
                    ne = finish(new, strict=False)
                    ne["trend"], ne["hasi"] = old.get("trend"), old.get("hasi")
                    fixed.append((old, ne))
                except Exception as e:                      # noqa: BLE001
                    print("  तीखी rant नहीं बनी:", e)
            if fixed:
                judge([ne for _, ne in fixed])
                for old, ne in fixed:
                    if (ne.get("connect") or {}).get("score", 0) > (old.get("connect") or {}).get("score", 0):
                        eps[eps.index(old)] = ne
                        print(f"  ✍️ तीखी की: {ne.get('topic')} → {ne['connect']['score']}/10")
        except gemini.QuotaOver:
            raise
        except Exception as e:                              # noqa: BLE001
            print("  तीखा करने वाला कदम छोड़ा:", repr(e)[:150])
    eps.sort(key=lambda e: (bool(e.get("_loose")), -(e.get("connect") or {}).get("score", 0)))
    for e in eps:
        print(f"  {(e.get('connect') or {}).get('score', '?')}/10: {e.get('topic')} | {e.get('samaj')}")
    return eps[:n]
