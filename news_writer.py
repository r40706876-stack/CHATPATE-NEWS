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
GOLDS = [ROOT / "examples_news_lpg.json", ROOT / "examples_news_rbi.json"]   # मालिक को पसंद आए नमूने

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


def gold_text(path):
    g = json.load(open(path, encoding="utf-8"))
    rows = []
    for l in g["lines"]:
        c = l.get("card")
        rows.append(f"  {l['who']}: {l['say']}" + (f"   [CARD: {c['tag']} | {c['big']} | {c.get('sub', '')}]" if c else ""))
    return f"[{g.get('topic')}]\n" + "\n".join(rows)


MASALA = """मसाले का पैमाना (मालिक को यही पसंद आया — हर line इस स्तर की हो):
- बबलू का "मतलब…" = तथ्य को घर/मोहल्ले की किसी ठोस तस्वीर से जोड़ो, आख़िर में हल्की पलटी:
    "मतलब अब सिलेंडर भी पूछ रहा है: पहले बताओ, तुम हो कौन?"
    "सब्सिडी ऐसे ग़ायब, जैसे मंदिर के बाहर से नई चप्पल!"
    "मतलब पापा का 'बाहर खाना खाएँगे' वाला वादा, फिर अगले महीने पर!"
    "बैंक को पैसा महँगा मिलेगा, तो आपको सस्ता कौन देगा, भइया?"
- किरदार की चुटकी = शब्दों का खेल या मुहावरा उलटना, सबसे मज़ेदार शब्द आख़िर में:
    "मशीन पर अंगूठा नहीं लगाया, तो सब्सिडी अंगूठा दिखा देगी!"   "अब उधार वाली चाय पर भी ब्याज लगेगा!"
- दादी = किसे भेजना है, उस आदमी का चुटीला चित्रण: "उस लल्ला को भेजो, जो हर चीज़ EMI पर उठा लाता है!"
- hook = चौंकाने वाला/चुटीला: "गैस सिलेंडर ने नया नखरा दिखाया है!", "EMI वालों के लिए बवाल वाली खबर!"
ख़राब (सिर्फ़ सलाह/सीधी बात, कोई तस्वीर या पलटी नहीं — ऐसा कभी नहीं):
    "बिना गारंटी के लाख रुपये मिल रहे हैं, अब बहाने छोड़ो और काम शुरू करो!"
    "नाम बदलना कोई खेल नहीं, अधिकारी भाव नहीं देंगे!"
"""


def prompt_masala(eps):
    """चौथा कदम: तथ्य वैसे ही, सिर्फ़ मज़ाकिया हिस्से और तीखे."""
    return f"""तुम "बकरा न्यूज़" के comedy editor हो ("खबर सौ टका पक्की, अंदाज़ अधपका!"). ये scripts तैयार हैं:
{json.dumps(eps, ensure_ascii=False, indent=1)}

{MASALA}
काम: हर script में सिर्फ़ ये हिस्से दोबारा लिखो, ताकि हर एक ऊपर वाले पैमाने तक पहुँचे:
1. पहली line (hook) और "hook_text"   2. card वाली हर bablu line का "मतलब/यानी…" वाला हिस्सा (तथ्य वाला हिस्सा शब्दशः वैसा ही)
3. chacha/pinky की line   4. dadi की line
नियम: card, अंक, तारीख़, स्रोत बिल्कुल नहीं बदलना. कोई नया तथ्य नहीं. हर line ≤ 22 शब्द. देसी शब्द (भइया, गज़ब, बवाल, भौकाल,
जुगाड़, तनिक, लल्ला) स्वाभाविक जगह. "say" में अंक शब्दों में और English short form देवनागरी में; "caption" भी उसी हिसाब से बदलो.
वही JSON list लौटाओ (उतनी ही scripts, उतनी ही lines, वही क्रम) — सिर्फ़ JSON."""


def prompt_pick(c, n=3):
    recent = "\n".join(f"- {r}" for r in c.get("recent", [])) or "(कुछ नहीं)"
    return f"""तुम "बकरा न्यूज़" के news editor हो. Page की पहचान: "खबर सौ टका पक्की, अंदाज़ अधपका!" —
असली, काम की खबर, जिसे बबलू बकरा मज़ेदार देसी भाषा में समझाता है.

आज की खबरें:
{_cands(c)}

हाल में बन चुकी (दोबारा नहीं):
{recent}

{ALLOWED}

इनमें से {n} अलग-अलग खबरें चुनो (अलग विषय: जैसे एक पैसा, एक नियम, एक त्योहार/योजना). हर एक के लिए Google News पर
खोजने लायक छोटी query लिखो (2-5 शब्द, हिंदी में, जैसे "रेपो रेट बढ़ा" या "LPG आधार नियम"). सिर्फ़ JSON:
{{"picks": [{{"topic": "खबर 8-12 शब्द", "why": "आम आदमी पर असर, एक लाइन", "query": "search query"}}]}}"""


def prompt_facts(picks, evidence):
    """तथ्य: Google News की असली headlines से (Gemini का Search वाला कोटा बहुत कम है, इसलिए वो नहीं)."""
    blocks = []
    for i, p in enumerate(picks):
        ev = evidence.get(i) or []
        rows = "\n".join(f"   - {h} ({s}, {d})" for h, s, d in ev) or "   (कोई headline नहीं मिली)"
        blocks.append(f"{i + 1}. {p['topic']}\n{rows}")
    return f"""ये आज की खबरें हैं, और हर एक के नीचे Google News की असली headlines (प्रकाशक और तारीख़ के साथ):
{chr(10).join(blocks)}

इन headlines से पक्के तथ्य निकालो. नियम:
- सिर्फ़ वही तथ्य जो headlines में साफ़ लिखा है — अंक, तारीख़, नियम हूबहू. अपनी जानकारी या अंदाज़ा बिल्कुल नहीं.
- जो बात 2 या ज़्यादा प्रकाशकों में मिले, वो सबसे पक्की. headlines आपस में टकराएँ तो वो बात छोड़ दो.
- confidence: "high" = 2+ प्रकाशक एक बात कहें; "medium" = एक भरोसेमंद प्रकाशक; "low" = headline नहीं या साफ़ नहीं.
- "todo" सिर्फ़ तब, जब headline में हो; वरना "अपने बैंक/एजेंसी/दफ़्तर से पता करो" जैसा आम सुझाव.
सिर्फ़ JSON:
[{{"topic": "...", "confidence": "high/medium/low", "date": "कब से/कब तक",
  "facts": ["तथ्य 1 (अंक/तारीख़ के साथ)", "तथ्य 2"], "who": "किस पर असर", "todo": "...",
  "source": "प्रकाशकों के नाम, जैसे 'दैनिक भास्कर, ABP News'"}}]"""


def prompt_write(packs):
    gold_lines = "\n\n".join(gold_text(g) for g in GOLDS if g.exists())
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

{MASALA}
हमारे सबसे अच्छे नमूने (ढाँचा और अंदाज़ ऐसा ही — शब्द मत दोहराना):
{gold_lines}

सिर्फ़ JSON — हर खबर का एक episode:
[{{"topic": "...", "category": "money/rules/bank/festival/scheme/tech/travel/weather/other", "breaking": "6-9 शब्द, सच्ची headline",
  "hook_text": "3-6 शब्द, screen पर बड़ा", "source": "स्रोत का नाम", "poll": ["...", "..."],
  "lines": [{{"who": "bablu", "say": "...", "caption": "...", "card": {{"tag": "...", "big": "...", "sub": "...", "icon": "..."}}}},
            {{"who": "chacha", "say": "...", "caption": "...", "punch": true}},
            {{"who": "dadi", "say": "...", "caption": "...", "punch": true, "expr": "smug"}}],
  "caption_post": "एक मज़ेदार लाइन + वही सवाल + 'Family group में भेजो' + स्रोत: ... + 4-5 hashtags + (AI से बने किरदार)"}}]"""


def finish(ep, strict=True):
    """काम की खबर वाले episode को पक्का करो. strict=False: लंबाई/cards की सख़्ती ढीली (कुछ भी न बने, उससे अच्छा)."""
    ep["format"], ep["label"] = "explain", "काम की खबर"
    ep.setdefault("key_word", "")
    ep.setdefault("icons", ["₹", "NEWS", "%"])
    ep["source"] = ep.get("source") or "Google News"
    ep["lines"] = [l for l in ep["lines"] if l.get("who") in writer.WHO and str(l.get("say", "")).strip()]
    for ln in ep["lines"]:                                  # caption गड़बड़ हो तो बोली गई line ही caption
        cap = str(ln.get("caption") or "")
        if len(re.findall(r"[\u0900-\u097F]", cap)) < len(re.findall(r"[A-Za-z]", cap)) or len(cap) < 4:
            ln["caption"] = ln["say"]
    if not strict and len(ep["lines"]) > 10:
        ep["lines"] = ep["lines"][:9] + ep["lines"][-1:]
    for ln in ep["lines"]:
        c = ln.get("card")
        if c:
            if not c.get("big"):
                ln.pop("card")
                continue
            c["icon"] = c.get("icon") if c.get("icon") in ICONS else "check"
            c["big"] = str(c["big"])[:40]
            c["tag"] = str(c.get("tag", ""))[:28]
            c["sub"] = str(c.get("sub", ""))[:70]
    ep = writer.clean(ep, strict=False)
    n_cards = sum(1 for l in ep["lines"] if l.get("card"))
    words = sum(len(l["say"].split()) for l in ep["lines"])
    if strict:
        assert 2 <= n_cards <= 4, f"cards: {n_cards}"
        assert words <= 165, f"बहुत लंबा: {words} शब्द"
    else:
        assert n_cards >= 1, "एक भी card नहीं"
    return ep


def write_options(c, n=3):
    picks = gemini.json_from(gemini.ask(prompt_pick(c, n), json_mode=True, temperature=0.4)).get("picks", [])[:n]
    for p in picks:
        print("  चुनी:", p.get("topic"), "|", p.get("why", ""))
    import topics
    evidence = {i: topics.rss_search(p.get("query") or p["topic"]) for i, p in enumerate(picks)}
    for i, p in enumerate(picks):
        print(f"  सबूत: {p.get('topic')} → {len(evidence[i])} headlines")
    packs = gemini.json_from(gemini.ask(prompt_facts(picks, evidence), json_mode=True, temperature=0.1))
    packs = [p for p in packs if str(p.get("confidence", "")).lower() != "low" and p.get("facts")]
    for p in packs:
        print("  तथ्य:", p.get("topic"), "|", p.get("source"), "|", p.get("confidence"))
    if not packs:
        raise SystemExit("एक भी खबर के पक्के तथ्य नहीं मिले")
    raw = gemini.json_from(gemini.ask(prompt_write(packs), json_mode=True, temperature=0.8))
    raw = [r for r in raw if isinstance(r, dict) and r.get("lines")]
    try:                                                    # चौथा कदम: मसाला तेज़ करो (तथ्य/cards वही)
        spicy = gemini.json_from(gemini.ask(prompt_masala(raw), json_mode=True, temperature=0.9))
        if isinstance(spicy, list) and len(spicy) == len(raw):
            for old, new in zip(raw, spicy):
                if len(new.get("lines", [])) == len(old["lines"]):
                    for lo, ln in zip(old["lines"], new["lines"]):
                        if ln.get("say") and ln.get("who") == lo["who"]:
                            lo["say"], lo["caption"] = ln["say"], ln.get("caption") or ln["say"]
                    old["hook_text"] = new.get("hook_text") or old.get("hook_text")
            print("  मसाला: lines और तीखी कीं")
    except Exception as e:                                  # noqa: BLE001
        print("  मसाला वाला कदम छोड़ा:", repr(e)[:120])
    eps = []
    for ep in raw:
        for strict in (True, False):
            try:
                eps.append(finish(json.loads(json.dumps(ep)), strict))
                break
            except Exception as e:                          # noqa: BLE001
                print(f"  episode ({'सख़्त' if strict else 'ढीला'}) नहीं बना:", ep.get("topic"), "—", e)
    if not eps:
        raise SystemExit("एक भी script नहीं बनी")
    return eps
