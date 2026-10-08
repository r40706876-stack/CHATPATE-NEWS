"""
काम की खबर — "खबर पक्की, अंदाज़ देसी". Gemini के सिर्फ़ 3 call में 3 scripts:
  1. चुनो:   आज की खबरों में से 3 जो सीधे आम आदमी की जेब/रोज़ की ज़िंदगी पर असर डालें
  2. जाँचो:  Google Search से हर खबर के पक्के तथ्य (तारीख़, अंक, क्या करना है, स्रोत) — शक हो तो खबर बाहर
  3. लिखो:   खबर (card, बिना मज़ाक) + मतलब (बबलू, देसी तुलना) + मसाला (एक किरदार) + क्या करें
"""
import json
import re
from pathlib import Path

import gemini
import writer

ROOT = Path(__file__).parent
ICONS = {"cylinder", "calendar", "rupee", "bank", "phone", "train", "percent", "check", "alert", "gift"}
GOLD = ROOT / "examples_news_lpg.json"

ALLOWED = """सिर्फ़ ऐसी खबरें जो सीधे आम परिवार पर असर डालें: पैसा/दाम (गैस, पेट्रोल, सब्ज़ी, रिचार्ज), नए नियम (बैंक, UPI,
आधार, PAN, टैक्स, ट्रेन टिकट, ड्राइविंग), सरकारी योजना (कौन ले सकता है, कैसे), छुट्टियाँ/त्योहार की तारीख़ें, exam/भर्ती
की तारीख़ें, बड़ी सेल/फ़ोन, मौसम की चेतावनी जिससे घर का काम बदले.
कभी नहीं: मौत, हादसा, अपराध, दंगा, युद्ध, राजनीति/नेता का बयान, धर्म, जाति, celebrity gossip, बीमारी का डर —
इन पर मज़ाकिया अंदाज़ ठीक नहीं."""


def _cands(c):
    out = []
    for k, label in (("kaam", "काम की"), ("viral", "वायरल"), ("news", "Trends"), ("moments", "त्योहार"), ("insta", "मेरी feed")):
        for it in c.get(k, []):
            extra = it.get("what") or " | ".join(it.get("headlines", [])[:1]) or it.get("source", "")
            out.append(f"- [{label}] {it['trend']}" + (f" ({extra})" if extra else ""))
    return "\n".join(out) or "(कोई नहीं — त्योहार/नियम वाली ताज़ा खबर ख़ुद Search से ढूँढो)"


def prompt_pick(c, n=3):
    recent = "\n".join(f"- {r}" for r in c.get("recent", [])) or "(कुछ नहीं)"
    return f"""तुम "बकरा न्यूज़" के news editor हो. Page की पहचान: "खबर सौ टका पक्की, अंदाज़ अधपका!" —
असली, काम की खबर, जिसे बबलू बकरा मज़ेदार देसी भाषा में समझाता है.

आज की खबरें:
{_cands(c)}

हाल में बन चुकी (दोबारा नहीं):
{recent}

{ALLOWED}

इनमें से {n} अलग-अलग खबरें चुनो (अलग विषय: जैसे एक पैसा, एक नियम, एक त्योहार/योजना). हर एक के लिए Google पर
खोजने लायक साफ़ query लिखो. सिर्फ़ JSON:
{{"picks": [{{"topic": "खबर 8-12 शब्द", "why": "आम आदमी पर असर, एक लाइन", "query": "search query"}}]}}"""


def prompt_facts(picks):
    lst = "\n".join(f"{i + 1}. {p['topic']} — search: {p.get('query', p['topic'])}" for i, p in enumerate(picks))
    return f"""Google Search करके इन खबरों के पक्के तथ्य निकालो (आज की तारीख़ के हिसाब से ताज़ा):
{lst}

नियम: सिर्फ़ वही लिखो जो search नतीजों में साफ़ लिखा है. अंक, तारीख़, नियम हूबहू. अंदाज़ा या अपनी जानकारी नहीं.
अगर कोई बात पक्की नहीं मिली तो उसे छोड़ दो; अगर पूरी खबर ही पक्की नहीं तो "confidence": "low".
सिर्फ़ JSON (कोई और text नहीं):
[{{"topic": "...", "confidence": "high/medium/low", "date": "कब से/कब तक",
  "facts": ["तथ्य 1 (अंक/तारीख़ के साथ)", "तथ्य 2", "तथ्य 3"],
  "who": "किस पर असर", "todo": "आम आदमी को क्या करना है (सिर्फ़ अगर स्रोत में हो)",
  "source": "प्रकाशक/संस्था का नाम (जैसे PIB, RBI, Upstox, दैनिक भास्कर)"}}]"""


def prompt_write(packs):
    gold = json.load(open(GOLD, encoding="utf-8")) if GOLD.exists() else {}
    gold_lines = "\n".join(f"  {l['who']}: {l['say']}" + (f"   [CARD: {l['card']['tag']} | {l['card']['big']} | {l['card'].get('sub', '')}]"
                                                            if l.get("card") else "") for l in gold.get("lines", []))
    return f"""तुम "बकरा न्यूज़" के head writer हो. अंदाज़: "खबर सौ टका पक्की, अंदाज़ अधपका!" — तथ्य पक्के, बोली गाँव-कस्बे वाली.
तथ्य (सिर्फ़ इन्हीं से लिखना, कुछ जोड़ना नहीं):
{json.dumps(packs, ensure_ascii=False, indent=1)}

किरदार: bablu (बबलू बकरा, anchor — साफ़ बोलता है, हर तथ्य के बाद "मतलब…" वाली देसी तुलना), chacha (चाचा भैंसा,
चाय की टपरी, एक लाइन की चुटकी, जेब/मोहल्ले वाली), dadi (दादी, video call पर — share करवाने वाली चुटीली लाइन),
pinky (पिंकी बिल्ली, Gen Z — फ़ोन/UPI/online वाली खबर पर).

हर खबर का ढाँचा (30-35 सेकंड, कुल 70-95 शब्द, 8-9 lines):
1. bablu: hook — सीधा असर (नुकसान/फ़ायदा), सच्चा, डराने वाला झूठ नहीं. ≤ 14 शब्द.
2-3. bablu + "card": तथ्य card पर (tag = कब से/किसके लिए, big = मुख्य बात ≤ 5 शब्द, sub = एक छोटी लाइन, icon).
   card पर कभी मज़ाक नहीं. bablu वही तथ्य बोले और साथ में "मतलब…" वाली देसी तुलना जोड़े (घर, मोहल्ला, शादी, मम्मी,
   चप्पल, रिश्तेदार जैसी चीज़ से) — तुलना छोटी, चुटीली, तथ्य को आसान बनाने वाली.
4. एक किरदार (chacha या pinky): एक लाइन की चुटकी, ≤ 16 शब्द, आख़िरी शब्दों में पलटी (शब्दों का खेल/मुहावरा अच्छा चलता है:
   "अंगूठा नहीं लगाया, तो सब्सिडी अंगूठा दिखा देगी").
5. bablu + "card": "क्या करें" — एक साफ़ कदम (सिर्फ़ तथ्यों में हो तो), icon "check".
6. bablu "अब वीडियो कॉल पर दादी!" + dadi: share करवाने वाली चुटीली लाइन (किसे भेजो और क्यों), ≤ 18 शब्द.
7. bablu आख़िरी: comment वाला सवाल, दो विकल्प ("एक, … दो, …") — "poll" में भी वही दो (2-4 शब्द).
बोली: हर script में 2-3 मशहूर देहाती/देसी शब्द, जो पूरे उत्तर भारत में समझे जाते हैं — भइया, का बात है, गज़ब, बवाल,
भौकाल, जुगाड़, तनिक, चकाचक, धाँसू, लल्ला, ठेठ, चौपाल, "ना भइया". स्वाभाविक जगह पर, ज़बरदस्ती नहीं, और card पर कभी नहीं.
icon इनमें से: {", ".join(sorted(ICONS))}.
"say" में अंक शब्दों में ("एक अक्टूबर", "नब्बे परसेंट") और English शब्द/short form देवनागरी में ("ईएमआई", "आरबीआई",
"यूपीआई", "वाईफ़ाई"), "caption" में अंकों में (1 अक्टूबर, 90%), English शब्द Roman में चल सकते हैं.
कोई hashtag line में नहीं. किसी असली इंसान/नेता/धर्म/जाति पर मज़ाक नहीं.

हमारा सबसे अच्छा नमूना (ढाँचा और अंदाज़ ऐसा ही — शब्द मत दोहराना):
{gold_lines}

सिर्फ़ JSON — हर खबर का एक episode:
[{{"topic": "...", "category": "money/rules/bank/festival/scheme/tech/travel/weather/other", "breaking": "6-9 शब्द, सच्ची headline",
  "hook_text": "3-6 शब्द, screen पर बड़ा", "source": "स्रोत का नाम", "poll": ["...", "..."],
  "lines": [{{"who": "bablu", "say": "...", "caption": "...", "card": {{"tag": "...", "big": "...", "sub": "...", "icon": "..."}}}},
            {{"who": "chacha", "say": "...", "caption": "...", "punch": true}},
            {{"who": "dadi", "say": "...", "caption": "...", "punch": true, "expr": "smug"}}],
  "caption_post": "एक मज़ेदार लाइन + वही सवाल + 'Family group में भेजो' + स्रोत: ... + 4-5 hashtags + (AI से बने किरदार)"}}]"""


def finish(ep):
    """काम की खबर वाले episode को पक्का करो."""
    ep["format"], ep["label"] = "explain", "काम की खबर"
    ep.setdefault("key_word", "")
    ep.setdefault("icons", ["₹", "NEWS", "%"])
    for ln in ep["lines"]:
        c = ln.get("card")
        if c:
            assert c.get("big"), "card खाली"
            c["icon"] = c.get("icon") if c.get("icon") in ICONS else "check"
            c["big"] = str(c["big"])[:40]
            c["tag"] = str(c.get("tag", ""))[:28]
            c["sub"] = str(c.get("sub", ""))[:70]
    ep = writer.clean(ep, strict=False)
    n_cards = sum(1 for l in ep["lines"] if l.get("card"))
    assert 2 <= n_cards <= 4, f"cards: {n_cards}"
    words = sum(len(l["say"].split()) for l in ep["lines"])
    assert words <= 120, f"बहुत लंबा: {words} शब्द"
    assert ep.get("source"), "स्रोत नहीं"
    return ep


def write_options(c, n=3):
    picks = gemini.json_from(gemini.ask(prompt_pick(c, n), json_mode=True, temperature=0.4)).get("picks", [])[:n]
    for p in picks:
        print("  चुनी:", p.get("topic"), "|", p.get("why", ""))
    packs = gemini.json_from(gemini.ask(prompt_facts(picks), search=True, temperature=0.2))
    packs = [p for p in packs if str(p.get("confidence", "")).lower() != "low" and p.get("facts")]
    for p in packs:
        print("  तथ्य:", p.get("topic"), "|", p.get("source"), "|", p.get("confidence"))
    if not packs:
        raise SystemExit("एक भी खबर के पक्के तथ्य नहीं मिले")
    eps = []
    for ep in gemini.json_from(gemini.ask(prompt_write(packs), json_mode=True, temperature=0.8)):
        try:
            eps.append(finish(ep))
        except Exception as e:                              # noqa: BLE001
            print("  episode छोड़ा:", ep.get("topic"), "—", e)
    if not eps:
        raise SystemExit("एक भी script नहीं बनी")
    return eps
