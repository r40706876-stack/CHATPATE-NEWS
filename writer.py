"""
आज के topics → Bakra News का एक episode (script JSON), Gemini से — 4 छोटे कदम:
  1. पुल:   topic चुनो + खबर घर के किस रिश्ते/हालत से टकराती है (सूखी खबरें बाहर)
  2. चक्की: बिना JSON, खुलकर 12 सवाल-जवाब, 10 साबित ढाँचों से (joke_bank.py — vidIQ के viral reels)
  3. जज:    3 दर्शकों (आंटी, college लड़का, अंकल) की नज़र से तुलना करके हर किरदार का सबसे अच्छा चुनो
  4. जोड़:   चुने jokes हूबहू रहते हैं; Gemini सिर्फ़ opener, ending, poll, captions लिखता है
तुम्हारी Telegram पसंद taste.json में जुड़ती है और अगली बार की चक्की में दिखाई जाती है.
"""
import difflib
import json
import re
import os
import sys
from pathlib import Path

import gemini
import joke_bank

ROOT = Path(__file__).parent
WHO = {"bablu", "chacha", "pinky", "dadi", "riya", "bunty"}
SCENE_OF = {"chacha": "chacha", "pinky": "pinky", "riya": "riya", "dadi": "dadi_call", "bunty": "bunty_call"}
SCENES = {"studio", "studio_end", "chacha", "pinky", "dadi_call", "card"}

CAST = """किरदार (हर एक की हँसी का अपना पक्का अंदाज़):
- bablu: बबलू बकरा, reporter. ओवर-कॉन्फ़िडेंट, हर छोटी बात "ब्रेकिंग". उसके सवाल में ही joke का setup होता है.
- chacha: चाचा भैंसा, 55 साल, चाय की टपरी. ज़िंदगी देखी हुई. पूरे भरोसे से उल्टा-पर-पक्का logic, पैसे/रिश्तेदार/मोहल्ले के
  असली नियम. कभी हड़बड़ाते नहीं — शांत चेहरे से बम.
- pinky: पिंकी बिल्ली, Free Wi-Fi zone वाली Gen Z. मम्मी-पापा के dialogues हूबहू दोहराती है, Insta की दुनिया, तीखा sarcasm.
  Insta trend ज़्यादातर इसी के मुँह से.
- dadi: 3D दादी (video call). मोहल्ले की सबसे तेज़. पुराना ज़माना बनाम आज, बहू-बेटे-पोते पर प्यार भरा पर चुभता वार,
  और अक्सर पूछने वाले को ही roast. episode का सबसे तीखा punch हमेशा उसका."""


def _lists(c):
    news = "\n".join(f"- {n['trend']}: " + " | ".join(n["headlines"]) for n in c.get("news", [])) or "(कोई नहीं)"
    insta = "\n".join(f"- {i['trend']}" + (f" — {i.get('what', '')}" if i.get("what") else "")
                      + (f" (line: {i['line']})" if i.get("line") else "")
                      + (" [मेरी feed से — इसे पहले लो]" if i.get("priority") else "")
                      for i in c.get("insta", [])) or "(कोई नहीं)"
    viral = "\n".join(f"- {v['trend']}" for v in c.get("viral", [])) or "(कोई नहीं)"
    viral += "\n\nत्योहार/मौसम/घर के पल (Instagram पर इन दिनों सबसे ज़्यादा चलते हैं):\n" + \
        ("\n".join(f"- {m['trend']}: {m['what']}" for m in c.get("moments", [])) or "(कोई नहीं)")
    recent = "\n".join(f"- {r}" for r in c.get("recent", [])) or "(कुछ नहीं)"
    return news, insta, viral, recent


MODE = {
    "viral": "आज का episode VIRAL वाला है: सोशल मीडिया पर वायरल खबर या Instagram trend ही मुख्य topic हो (breaking: \"Viral: ...\").",
    "news": "आज का episode NEWS वाला है: Google Trends की खबर मुख्य topic, साथ में एक Insta trend ज़रूर जुड़े.",
}


def prompt_bridge(c):
    """कदम 1: topic + 'पुल' — खबर घर के किस रिश्ते/हालत से टकराती है."""
    news, insta, viral, recent = _lists(c)
    return f"""तुम "बकरा न्यूज़" (नकली Hindi न्यूज़ चैनल, Instagram comedy page) के editor हो.

सोशल मीडिया पर वायरल खबरें:
{viral}

Instagram पर अभी viral:
{insta}

Google Trends की खबरें:
{news}

हाल में बन चुके (ये topic दोबारा नहीं; मौसम/बारिश लगातार बिल्कुल नहीं):
{recent}

{MODE.get(c.get("mode", "news"), MODE["news"])}

सबसे ज़रूरी सीख (Instagram पर 1M-15M views वाले Hindi comedy reels से): हँसी खबर पर नहीं आती, घर के रिश्ते पर आती है —
मम्मी, पापा, सास-बहू, पति-पत्नी, दामाद, ससुराल, रिश्तेदार, शर्मा जी, पड़ोसन आंटी, भाई-बहन, बच्चे का homework, शादी, पैसा.
खबर सिर्फ़ बहाना है; joke घर के अंदर जाकर फटता है.

काम:
1. वो topic चुनो जो आज सच में लोगों के feed में है और जिससे घर का कोई रिश्ता/हालत तुरंत टकराए. सूखी खबर (नीति, रिपोर्ट, आँकड़ा
   जिसका घर से कोई लेना-देना नहीं) मत लो, चाहे कितनी बड़ी हो. हादसा, अपराध, राजनीति, धर्म, असली इंसान का मज़ाक नहीं.
2. उस topic के 4 "पुल" लिखो: घर की कौन सी ठोस हालत इस खबर से टकराती है, और उसमें कौन सा रिश्ता है.
   अच्छा पुल: खबर "बिना टिकट पर जुर्माना" → "टिकट के वक़्त बच्चे की उम्र घटाना" (रिश्ता: मम्मी-पापा).
   कमज़ोर पुल: "लोग परेशान हैं" (कोई ठोस तस्वीर नहीं).
3. एक Insta trend चुनो जो जुड़ सके (list से हूबहू, वरना सदाबहार: "Expectation vs Reality", "Me explaining to my mom", "Nobody: / मम्मी:").
सिर्फ़ JSON:
{{"topic": "खबर, 8-12 शब्द", "category": "viral/insta/money/tech/festival/entertainment/sports/weather/other",
 "news_used": "...", "source_headline": "...", "insta_used": "...",
 "bridges": [{{"ghar": "घर की ठोस हालत", "rishta": "कौन-कौन"}}], "best": 0}}"""


def prompt_plan(c, n=3):
    """आज के n topics एक साथ — हर उम्मीदवार को 'हँसी की गुंजाइश' पर परखकर."""
    news, insta, viral, recent = _lists(c)
    return f"""तुम "बकरा न्यूज़" (Instagram पर Hindi comedy page, नकली न्यूज़ चैनल) के programming head हो.
हमारी कोई मजबूरी नहीं कि हर खबर पर comedy ठूँसें. हम सिर्फ़ वो topic लेते हैं जिस पर अपने-आप हँसी बने.

उम्मीदवार:
वायरल खबरें:
{viral}

Instagram पर अभी viral:
{insta}

Google Trends:
{news}

हाल में बन चुके (दोबारा नहीं):
{recent}

Instagram पर 1M-15M views वाले Hindi comedy reels की सीख: हँसी घर के रिश्ते/पल पर आती है (मम्मी, पापा, सास-बहू, पति-पत्नी,
रिश्तेदार, भाई-बहन, शादी, त्योहार की तैयारी, पैसा). त्योहार/मौसम के दिनों में उसी पर बने reels सबसे ज़्यादा share होते हैं.

हर उम्मीदवार को मन में परखो:
1. पहचान: क्या भारत का हर आम घर इसे ख़ुद जीता/जानता है? (celebrity का बयान, gossip, नीति, रिपोर्ट, कंपनी की खबर = नहीं)
2. तस्वीर: क्या इसमें घर की कोई ठोस, दिखने वाली हालत है (झाड़ू, रज़ाई, थाली, चार्जर, लिफ़ाफ़ा)?
3. तीन आवाज़ें: क्या चाचा (पैसा/मोहल्ला), पिंकी (Gen Z/मम्मी के dialogue) और दादी (पुराना ज़माना/roast) तीनों इस पर अलग-अलग हँसा सकते हैं?
4. ताज़गी: आज/इस हफ़्ते लोग इसके बारे में सोच रहे हैं.
किसी असली इंसान, नेता, धर्म, जाति, हादसे, अपराध पर कुछ नहीं. खबर तभी लो जब वो ख़ुद में मज़ेदार हो और सीधे घर से जुड़े;
वरना त्योहार/मौसम/घर का पल लो — वो भी "ताज़ा" ही है.

आज के {n} सबसे मज़ेदार topic चुनो — तीनों अलग दुनिया के (जैसे एक त्योहार, एक वायरल/Insta, एक घर का पल). हर एक के 3 "पुल"
(घर की ठोस हालत + रिश्ता) और एक Insta trend (list से हूबहू, वरना सदाबहार: "Expectation vs Reality", "Me explaining to my mom", "Nobody: / मम्मी:").
सिर्फ़ JSON:
{{"topics": [{{"topic": "8-12 शब्द", "category": "festival/viral/insta/money/tech/entertainment/sports/weather/home/other",
  "news_used": "...", "source_headline": "असली खबर हो तो उसकी headline, वरना त्योहार/पल का नाम", "insta_used": "...",
  "hasi": "एक लाइन — इस पर हँसी क्यों आएगी", "bridges": [{{"ghar": "...", "rishta": "..."}}]}}]}}"""


def prompt_mill(meta):
    """कदम 2: खुलकर jokes — JSON नहीं, ताकि सारा दिमाग़ हँसी पर लगे."""
    bridges = "\n".join(f"- {b.get('ghar')} ({b.get('rishta')})" for b in meta.get("bridges", []))
    return f"""तुम भारत के सबसे तेज़ Hindi comedy writer हो (Instagram reels). आज की खबर: {meta.get('topic')}
घर से जुड़ने के पुल:
{bridges}
Insta trend जो किसी एक जवाब में आना है: {meta.get('insta_used')}

{CAST}

ये 10 ढाँचे Instagram पर सच में करोड़ों views लाए (सबूत साथ में). हर उदाहरण में setup बबलू के सवाल में है, और हँसी जवाब के
आख़िरी 2-4 शब्दों में:
{joke_bank.as_text()}

ये joke नहीं हैं (हमारे पुराने reels में ऐसी ग़लतियाँ हुईं):
{joke_bank.bad_text()}
{taste_text()}
काम: आज की खबर पर 12 सवाल-जवाब लिखो — chacha के 4, pinky के 4, dadi के 4. हर एक अलग ढाँचे से.
- सवाल (बबलू): खबर का एक ठोस हिस्सा लेकर, ≤ 14 शब्द. सवाल में ही setup हो.
- जवाब: ≤ 22 शब्द, किसी पुल से घर के अंदर जाए, किसी असली रिश्ते या घर की चीज़ का नाम ले, सबसे मज़ेदार शब्द बिल्कुल आख़िर में.
- उदाहरणों के शब्द/topic मत दोहराना (EMI-रिश्तेदार, अंक, थैला, रुमाल वग़ैरह) — सिर्फ़ ढाँचा लो.
- सब हिंदी (देवनागरी) में; आम English शब्द (WiFi, reel, phone) चलेंगे. कोई hashtag नहीं. जाति/धर्म/शरीर/औरतों पर तंज़ नहीं.
हर line बिल्कुल इसी रूप में (और कुछ नहीं):
1 | chacha | ढाँचे का नाम | सवाल: ... | जवाब: ..."""


def parse_mill(text):
    pairs = []
    for line in text.splitlines():
        p = [x.strip() for x in line.strip().strip("*").split("|")]
        if len(p) == 4 and p[0].lower().strip("* ") in ("chacha", "pinky", "dadi"):
            p = ["0"] + p                                  # नंबर के बिना वाली line
        if len(p) < 5:
            continue
        who = p[1].lower().strip("* ")
        q = re.sub(r"^(सवाल|Q)\s*[:：]\s*", "", p[3]).strip(' "“”')
        a = re.sub(r"^(जवाब|A)\s*[:：]\s*", "", "|".join(p[4:])).strip(' "“”')
        if who in ("chacha", "pinky", "dadi") and q and a and "#" not in a:
            pairs.append({"who": who, "tpl": p[2], "q": q, "a": a})
    return pairs


def prompt_judge(meta, pairs):
    """कदम 3: तुलना करके चुनो (अकेले-अकेले नंबर नहीं — वो हमेशा 8/10 दे देता है)."""
    lst = "\n".join(f"{i}. [{p['who']}] बबलू: {p['q']}  →  {p['a']}" for i, p in enumerate(pairs))
    return f"""तुम 3 लोग हो जो Instagram reels scroll कर रहे हैं: कानपुर की 45 साल की आंटी, दिल्ली का 21 साल का college लड़का,
जयपुर के 62 साल के रिटायर्ड अंकल. खबर: {meta.get('topic')}

{lst}

हर जोड़े को तीनों की नज़र से देखो:
- क्या 2 सेकंड में समझ आया, बिना खबर पढ़े?  - क्या आख़िरी शब्दों पर सच में हँसी/"हाय, ये तो मेरे घर का है" आया?
- क्या कोई इसे family group में भेजेगा या किसी को tag करेगा?
तुरंत बाहर: सिर्फ़ topic का नाम/observation, समझाना, लंबा जवाब, पलटी बीच में, किसी पर बुरा तंज़.
फिर chacha, pinky, dadi — हर एक का सबसे अच्छा एक जोड़ा चुनो (dadi वाला पूरे episode का सबसे तीखा हो).
चाहो तो चुने हुए जवाब से फ़ालतू शब्द काट सकते हो (पलटी और आख़िरी शब्द वैसे ही रहें), नया joke मत लिखो.
सिर्फ़ JSON: {{"chacha": 0, "pinky": 0, "dadi": 0, "trim": {{"<नंबर>": "छोटा जवाब"}}, "dadi_expr": "smug/happy/shock/angry/sad",
"why": "एक लाइन — dadi वाला सबसे अच्छा क्यों"}}"""


def prompt_assemble(meta, pick):
    qa = "\n".join(f"{w}: बबलू: {p['q']} → {p['a']}" for w, p in pick.items())
    return f"""तुम "बकरा न्यूज़" के head writer हो. खबर: {meta.get('topic')} | Insta trend: {meta.get('insta_used')}
चुने हुए jokes (ये हूबहू रहेंगे, इन्हें मत बदलना):
{qa}

{CAST}

बाक़ी हिस्से लिखो:
- opener: बबलू "ब्रेकिंग न्यूज़!" + खबर (headline जैसी सच्ची, छोटी) + एक बेतुका सूत्र जो ख़ुद में joke हो ("सूत्र: मेरी मम्मी की किटी पार्टी"). ≤ 22 शब्द.
- ending: बबलू का एक छोटा मज़ेदार निचोड़ + दो विकल्प वाला सवाल ("1 = ..., 2 = ..."), जो ऊपर के jokes से जुड़ा हो और comment करवाए. ≤ 20 शब्द.
- poll: वही दो विकल्प (2-4 शब्द). hook_text: 3-6 शब्द, scroll रोकने वाला, emoji नहीं.
- captions: हर बोली गई line का screen caption — वही शब्द, अंक अंकों में (₹500), English शब्द Roman में.
सिर्फ़ JSON:
{{"breaking": "6-9 शब्द, सच्ची खबर", "premise": "एक लाइन", "key_word": "खबर का एक शब्द", "opener": "...", "opener_caption": "...",
 "ending": "...", "ending_caption": "...", "poll": ["...", "..."], "hook_text": "...",
 "captions": {{"chacha_q": "...", "chacha_a": "...", "pinky_q": "...", "pinky_a": "...", "dadi_q": "...", "dadi_a": "..."}},
 "insta_on": "chacha/pinky/dadi — किस जवाब में Insta trend है", "icons": ["3 छोटे शब्द, emoji नहीं"],
 "ticker": "4 हिस्से '   •   ' से जुड़े, 1-2 असली बाक़ी मज़ाकिया",
 "caption_post": "मज़ेदार लाइन + वही सवाल (family group में भेजो/tag करो) + असली खबर का source + 4-5 hashtags + (AI से बने किरदार)"}}"""


def _cap(said, cap):
    """Gemini का caption तभी जब वही बात हो, वरना बोली गई line ही."""
    if cap and difflib.SequenceMatcher(None, said, cap).ratio() > 0.55:
        return cap
    return said


def build(meta, pick, asm, expr):
    call = "अब वीडियो कॉल पर दादी! "
    C = asm.get("captions", {})
    lines = [{"who": "bablu", "scene": "studio", "say": asm["opener"], "caption": _cap(asm["opener"], asm.get("opener_caption"))}]
    for w in ("chacha", "pinky", "dadi"):
        p = pick[w]
        q = (call if w == "dadi" else "") + p["q"]
        lines.append({"who": "bablu", "scene": SCENE_OF[w], "say": q,
                      "caption": (call if w == "dadi" else "") + _cap(p["q"], C.get(f"{w}_q"))})
        ln = {"who": w, "scene": SCENE_OF[w], "say": p["a"], "caption": _cap(p["a"], C.get(f"{w}_a")), "punch": True}
        if w == "dadi":
            ln["expr"] = expr
        if str(asm.get("insta_on", "")).strip().lower() == w:
            ln["insta"] = meta.get("insta_used", "")
        lines.append(ln)
    lines.append({"who": "bablu", "scene": "studio_end", "say": asm["ending"], "caption": _cap(asm["ending"], asm.get("ending_caption"))})
    ep = {k: asm.get(k) for k in ("breaking", "premise", "key_word", "poll", "hook_text", "icons", "ticker", "caption_post")}
    ep.update(topic=meta.get("topic"), category=meta.get("category", "other"), news_used=meta.get("news_used", ""),
              insta_used=meta.get("insta_used", ""), source_headline=meta.get("source_headline", ""), lines=lines,
              jokes=[dict(p, who=w) for w, p in pick.items()])
    return ep


TASTE = ROOT / "taste.json"


def taste_text():
    """मालिक की पसंद: Telegram पर चुनी/ठुकराई scripts के jokes."""
    if not TASTE.exists():
        return ""
    t = json.load(open(TASTE, encoding="utf-8"))
    out = ""
    if t.get("liked"):
        out += "\nमालिक ने (जो रोज़ script चुनते हैं) ये jokes पसंद किए — इनके जैसा स्तर चाहिए:\n" + \
               "\n".join(f"- {p['q']} → {p['a']}" for p in t["liked"][-6:])
    if t.get("disliked"):
        out += "\nमालिक ने ये ठुकराए — ऐसा मत लिखना:\n" + "\n".join(f"- {p['q']} → {p['a']}" for p in t["disliked"][-6:])
    return out + "\n" if out else ""


def learn(eps, liked):
    t = json.load(open(TASTE, encoding="utf-8")) if TASTE.exists() else {"liked": [], "disliked": []}
    key = "liked" if liked else "disliked"
    for ep in eps:
        t[key] += [{"q": j["q"], "a": j["a"]} for j in ep.get("jokes", [])]
    t[key] = t[key][-30:]
    json.dump(t, open(TASTE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def clean(ep, strict=True):
    lines = ep["lines"]
    assert 5 <= len(lines) <= 10, f"lines: {len(lines)}"
    for ln in lines:
        assert ln["who"] in WHO, ln["who"]
        assert ln.get("say") and ln.get("caption")
        if ln["who"] != "bablu":
            ln["scene"] = SCENE_OF[ln["who"]]
        elif ln.get("card"):
            ln["scene"] = "card"
        elif ln.get("scene") not in SCENES:
            ln["scene"] = "studio"
        if ln["who"] == "riya":                            # सड़क वाली लड़की = पिंकी
            ln["who"], ln["scene"] = "pinky", "pinky"
        if ln["who"] in ("bunty",):                        # मेहमान अभी सिर्फ़ दादी
            ln["who"], ln["scene"] = "dadi", "dadi_call"
        if ln["who"] in ("dadi", "riya", "bunty") and ln.get("expr") not in {"neutral", "happy", "shock", "angry", "smug", "sad"}:
            ln["expr"] = "happy"
        ln["punch"] = bool(ln.get("punch"))
        ln["insta"] = str(ln.get("insta") or "")[:24]
    lines[0]["scene"] = "studio"
    lines[-1]["scene"] = "studio_end"
    for i, ln in enumerate(lines[1:-1], 1):                 # bablu का सवाल अगले मेहमान के scene में
        if ln["who"] == "bablu" and lines[i + 1]["who"] != "bablu" and not ln.get("card"):
            ln["scene"] = SCENE_OF[lines[i + 1]["who"]]
    for ln in lines:                                       # hashtag कभी बोले/लिखे न जाएँ
        for k in ("say", "caption"):
            ln[k] = re.sub(r"\s*#\S+", "", ln[k]).strip()
        assert len(ln["say"]) >= 4, "line सिर्फ़ hashtag थी"
    for ln in lines:                                       # captions हिंदी में हों
        dev = len(re.findall(r"[\u0900-\u097F]", ln["caption"]))
        lat = len(re.findall(r"[A-Za-z]", ln["caption"]))
        assert dev >= lat, f"caption हिंदी में नहीं: {ln['caption'][:40]}"
    kw = str(ep.get("key_word") or "").strip()
    if kw and strict:
        guests = [l for l in lines if l["who"] != "bablu"]
        hit = sum(kw[:3] in l["say"] for l in guests)
        assert hit >= max(1, len(guests) - 1), f"key_word '{kw}' मेहमानों की lines में नहीं — joke खबर से नहीं जुड़े"
    words = sum(len(l["say"].split()) for l in lines)
    assert words <= 160, f"बहुत लंबा: {words} शब्द"
    ep["icons"] = ((ep.get("icons") or []) + ["₹", "NEWS", "%"])[:3]
    ep.setdefault("ticker", ep.get("breaking", ""))
    return ep


def write_one(c, meta0=None):
    """एक episode: पुल → 12 jokes → तुलना करके चुनना → जोड़ना. लौटाता है episode dict.
    meta0 (programming head का चुना topic) हो तो पुल वाला कदम छूट जाता है."""
    last = None
    for attempt in range(3):
        try:
            meta = dict(meta0) if meta0 else gemini.json_from(gemini.ask(prompt_bridge(c), json_mode=True, temperature=0.7))
            b = meta.get("bridges") or []
            if b:                                           # सबसे अच्छा पुल सबसे ऊपर
                k = int(meta.get("best", 0)) if str(meta.get("best", 0)).isdigit() else 0
                meta["bridges"] = [b[min(k, len(b) - 1)]] + [x for i, x in enumerate(b) if i != k]
            pairs = parse_mill(gemini.ask(prompt_mill(meta), temperature=1.0))
            have = {p["who"] for p in pairs}
            assert {"chacha", "pinky", "dadi"} <= have, f"jokes अधूरे: {len(pairs)} मिले"
            jd = gemini.json_from(gemini.ask(prompt_judge(meta, pairs), json_mode=True, temperature=0.2, prefer="pro"))
            pick = {}
            for w in ("chacha", "pinky", "dadi"):
                i = int(jd.get(w, -1)) if str(jd.get(w, "")).lstrip("-").isdigit() else -1
                if not (0 <= i < len(pairs)) or pairs[i]["who"] != w:
                    i = next(n for n, p in enumerate(pairs) if p["who"] == w)
                p = dict(pairs[i])
                tr = (jd.get("trim") or {}).get(str(i))
                if tr and len(tr) < len(p["a"]) and tr.split()[-1:] == p["a"].split()[-1:]:
                    p["a"] = tr                             # सिर्फ़ छोटा किया, आख़िरी शब्द वही
                pick[w] = p
            print("  judge:", jd.get("why", ""))
            asm = gemini.json_from(gemini.ask(prompt_assemble(meta, pick), json_mode=True, temperature=0.6))
            expr = jd.get("dadi_expr") if jd.get("dadi_expr") in {"smug", "happy", "shock", "angry", "sad"} else "smug"
            ep = clean(build(meta, pick, asm, expr), strict=False)
            ep["hasi"] = meta.get("hasi", "")
            print(f"  topic: {ep.get('topic')} | Insta: {ep.get('insta_used')}")
            return ep
        except Exception as e:                              # noqa: BLE001
            last = e
            print("  दोबारा कोशिश:", repr(e)[:200])
    raise RuntimeError(f"script नहीं बनी: {last}")


def write_options(c, n=3):
    """n अलग topic वाले episodes — तुम Telegram पर एक चुनोगे. topics एक ही बार में, हँसी की गुंजाइश देखकर."""
    metas = []
    try:
        metas = gemini.json_from(gemini.ask(prompt_plan(c, n), json_mode=True, temperature=0.6)).get("topics", [])[:n]
        for m in metas:
            print("  topic चुना:", m.get("topic"), "|", m.get("hasi", ""))
    except Exception as e:                                  # noqa: BLE001
        print("  programming वाला कदम नहीं चला:", repr(e)[:150])
    eps = []
    for k in range(n):
        m = metas[k] if k < len(metas) and m_ok(metas[k]) else None
        c2 = dict(c, recent=list(c.get("recent", [])) + [f"(आज का विकल्प, इससे अलग topic लो) {e.get('topic')}" for e in eps])
        try:
            eps.append(write_one(c2, m))
        except Exception as e:                              # noqa: BLE001
            print(f"  विकल्प {k + 1} नहीं बना:", e)
    if not eps:
        raise SystemExit("एक भी script नहीं बनी")
    return eps


def m_ok(m):
    return bool(m.get("topic")) and bool(m.get("bridges"))


def write(c, out="script_today.json"):
    if not os.getenv("GEMINI_API_KEY"):
        print(prompt_bridge(c) + "\n\n(GEMINI_API_KEY नहीं)")
        return None
    ep = write_one(c)
    json.dump(ep, open(ROOT / out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return ROOT / out


if __name__ == "__main__":
    write(json.load(open(ROOT / (sys.argv[1] if len(sys.argv) > 1 else "candidates_today.json"), encoding="utf-8")))
