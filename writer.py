"""
आज के topics → Bakra News का एक episode (script JSON), Gemini से — 2 चरण:
  1. Joke room: topic चुनो (खबर + Insta trend), हर किरदार के लिए 6 punchline, हर एक को ख़ुद नंबर दो
  2. Script + punch-up: सबसे ऊँचे नंबर वाले jokes से छोटा script, फिर कमज़ोर line दोबारा लिखो
CORE: ट्रेंडिंग खबर + Instagram का ट्रेंड, मज़ाकिया तरीके से आम आदमी की ज़िंदगी से जुड़ा.
"""
import json
import re
import os
import sys
from pathlib import Path

import gemini

ROOT = Path(__file__).parent
WHO = {"bablu", "chacha", "pinky", "dadi", "riya", "bunty"}
SCENE_OF = {"chacha": "chacha", "pinky": "pinky", "riya": "riya", "dadi": "dadi_call", "bunty": "bunty_call"}
SCENES = {"studio", "studio_end", "chacha", "pinky", "dadi_call"}

CAST = """किरदार (हर कोई अपनी दुनिया से जवाब देता है):
- bablu: बबलू बकरा, reporter. ओवर-कॉन्फ़िडेंट, हर खबर "ब्रेकिंग". खबर के बाद एक बेतुका "सूत्र" (हर बार नया, खबर से जुड़ा: "सूत्र मेरा कार्ट है").
- chacha: चाचा भैंसा, चाय वाले आम आदमी. ठंडे दिमाग़ से हर खबर को पैसे/महँगाई/घर के जुगाड़ से पलटते हैं.
- pinky: पिंकी बिल्ली, Free Wi-Fi zone वाली Gen Z. Reels, followers, Instagram की भाषा, तीखा sarcasm.
  Insta trend ज़्यादातर इसी के मुँह से. मम्मी-पापा वाले relatable किस्से इसकी ताक़त.
- dadi: 3D दादी (video call, कमज़ोर नेटवर्क). पुराने ज़माने से तुलना, घर का कड़वा सच, सबसे बड़ा punch. हर episode में मेहमान यही."""

CRAFT = """हँसी कैसे बनती है (हर punchline इनमें से किसी तरकीब पर हो):
1. उलटफेर: setup एक दिशा में ले जाए, आख़िरी 2-3 शब्द उलट दें.
   अच्छा: "हमारे घर में हर दिवाली नया फ़ोन आता है… पुराने फ़ोन पर, नया कवर!"
2. तुलना-चढ़ाव: खबर के अंक/बात को घर की चीज़ से छोटा कर दो.
   अच्छा: "तीन परसेंट? बेटा, इतना तो पिछले हफ़्ते टमाटर बढ़ गया था।"
3. तीन की सूची: दो आम बातें, तीसरी बेतुकी पर सच्ची.
   अच्छा: "शादी की तैयारी पूरी: कपड़े तैयार, गिफ़्ट तैयार… और खाने के बाद वाला बहाना भी तैयार।"
4. घर का कड़वा सच: वो बात जो हर घर में होती है पर कोई बोलता नहीं.
   अच्छा: "मम्मी: मुझे कुछ नहीं चाहिए… और सेल ख़त्म होते ही: तुमने मेरे लिए कुछ लिया ही नहीं!"
5. पीढ़ी की तुलना (दादी): "हमारे ज़माने में भी Live होता था बेटा… जब बिजली आ जाती थी!"
6. पुराना viral joke, नए कपड़ों में: वो मशहूर देसी joke/forward जो लोग पहले से जानते हैं (WhatsApp forward, पप्पू-teacher,
   doctor-patient, मम्मी की चप्पल, शर्मा जी का बेटा, रिश्तेदार "beta kya kar rahe ho", बिजली जाते ही पूरे मोहल्ले का "आआआ",
   मम्मी का "पाँच मिनट में आ रही हूँ", पापा का "हमारे ज़माने में", शादी का खाना, दुकानदार से मोल-भाव) — उसे आज की खबर पर फिट करो.
   पहचाना हुआ joke = तुरंत हँसी + comment "ye mere ghar ka hai". हर episode में कम से कम एक ऐसा (ज़्यादातर चाचा का).
   अच्छा: "हमारे मोहल्ले को notification की ज़रूरत नहीं, बिजली जाते ही पूरा मोहल्ला एक साथ 'आआआ' बोलता है!"
   (जाति/धर्म/क्षेत्र/शरीर/औरतों पर बने पुराने jokes बिल्कुल नहीं.)
Instagram पर जुलाई-अक्टूबर 2026 में सच में चले Hindi comedy reels (vidIQ data) — इनके तरीके अपनाओ, शब्द नहीं:
   A. बेतुका-आत्मविश्वासी जवाब (street interview): सवाल सीधा, जवाब पूरे भरोसे से गलत/उल्टे logic वाला.
      "15 अगस्त की ऐसी हिस्ट्री कभी नहीं सुनी होगी" 55.8M | "दारू का दम: इसे मच्छर भी नहीं काटते" 13M |
      AI पर सवाल → "हमारे यहाँ military है ना सर" 0.8M  → चाचा/पिंकी का जवाब ऐसा हो.
   B. ज़रूरत से ज़्यादा सच ("इतना भी सच नहीं बोलना था" 0.5M): जवाब में घर का ऐसा सच जो सब छुपाते हैं.
   C. कहानी वाला चुटकुला (2 वाक्य setup, आख़िरी शब्द पर पलटी): "एक महिला रोज़ बैंक आती थी…" 6.2M + 4.9M (दो पेजों पर).
   D. शब्दों का खेल: "पहले एक कमाता था, नौ खाते थे, इसलिए नौकरी" 2.9M | Jo-Vo वाला pun 1.7M.
   E. "X तीन प्रकार के होते हैं" (तीसरा सबसे सच्चा/बेतुका): "दामाद तीन प्रकार के होते हैं" 7.1M.
   F. महँगाई/पुराना ज़माना अतिशयोक्ति: "सब महँगा हो गया… माचिस आज भी 1 रुपये" 4.8M | "80s में जाकर दादा को ज़मीन बेचने से रोको" 1.3M.
   G. "Wait for reply": सबसे तीखा जवाब आख़िर में (Bhide reply 3.3M, Bharti-Harsh comebacks 3.9M) → दादी का जवाब सबसे तीखा.
   H. न्यूज़ की नक़ल: "भिंड के युवक का मैगी पर बड़ा आरोप" 1M — छोटी बात को राष्ट्रीय ब्रेकिंग की तरह.
   हर episode में कम से कम 3 अलग तरीके (जैसे चाचा = A या F, पिंकी = B या E, दादी = G + C).
सबसे मज़ेदार शब्द line के बिल्कुल आख़िर में. punch के बाद कोई explanation नहीं.
ख़राब (ऐसा कभी मत लिखो):
- "दुकान की पन्नी तो हमेशा उड़ ही जाती है" — बस observation, कोई twist नहीं.
- "इससे Reels का pose बिगड़ जाएगा, literally scam है ये!" — तकिया-कलाम ज़बरदस्ती, joke नहीं.
(ऊपर के उदाहरण सिर्फ़ तरीका समझाने को हैं; उनके topic/शब्द (धनिया, चादर, टमाटर, कवर) मत दोहराना.)
- खबर दोहराना, "देखा आपने" वाली लंबी बातें, समझाना."""

RULES = """नियम:
- सबसे ज़रूरी — एक comic premise: पूरा episode एक ही मज़ेदार सोच पर टिका हो ("premise"), और खबर का एक key शब्द ("key_word",
  जैसे "चाँद") हर मेहमान की punch line में वापस आए. हर जवाब उसी खबर/चीज़ को घर से जोड़े — कोई भी line दूसरे topic पर न भटके.
  आख़िरी सवाल/poll भी उसी premise पर हो (जैसे "चाँद पर पहले कौन पहुँचा? 1 = रॉकेट, 2 = टमाटर के दाम").
- भाषा: "say" और "caption" दोनों हिंदी (देवनागरी) में. English सिर्फ़ आम बोलचाल के शब्द (WiFi, reel, app). पूरा वाक्य English में कभी नहीं.
- CORE: खबर को आम घर की ज़िंदगी से जोड़ो (मम्मी, बजट, बिजली, WiFi, चार्जर, कपड़े, रिश्तेदार, EMI).
- Instagram trend ज़रूरी: ऊपर की list से एक trend/viral line/format इस्तेमाल करो (वैसा ही, पहचान में आए). list खाली हो तो
  कोई सदाबहार Insta format लो: "POV: …", "Nobody: … / मम्मी: …", "Expectation vs Reality", "Me explaining to my mom".
  जिस line में Insta trend है उस पर "insta": "trend का छोटा नाम" (screen पर badge अपने-आप दिखेगा).
  "POV", "Nobody", "Expectation vs Reality" जैसे format के नाम कभी बोले नहीं जाएँगे — line सीधी बोलचाल में हो
  ("बाहर आंधी है, और मम्मी कहती हैं…"), format का नाम सिर्फ़ "insta" field में.
- पहले 2 सेकंड: "hook_text" = 3-6 शब्द, screen पर बड़ा पीला text, जो scroll रोक दे — खबर का सबसे चौंकाने वाला/बेतुका हिस्सा
  (जैसे "गोभी में ज़िंदा कीड़ा 😱" नहीं, बल्कि "10 मिनट में कीड़ा डिलीवर!"). emoji मत डालो.
- Stop-scroll test: हर punch ऐसा हो कि 20 साल का लड़का उसे पढ़कर family group में भेजे. "ठीक-ठाक" वाला joke = फेल, दोबारा लिखो.
  सबसे अच्छे joke में एक ठोस, दिखने वाली तस्वीर होती है (चादर, सायरन, कवर) — गोल-मोल बात नहीं.
- तकिया-कलाम ("हमें क्या, चाय पियो" / "Literally scam है ये!") सिर्फ़ तब जब punch को और तेज़ करे, वरना मत डालो.
- Interaction: आख़िरी line comment करवाए — दो विकल्प वाला सवाल ("1 = मम्मी, 2 = पापा"); दोनों विकल्प "poll" में भी दो
  (हर विकल्प 2-4 शब्द, screen पर बटन बनेंगे).
  caption_post भी इसी सवाल से शुरू हो.
- छोटा: कुल 7 lines, पूरे episode में 90 शब्द से कम (बोलने में ~30 सेकंड). bablu की हर line ≤ 15 शब्द, मेहमान का जवाब ≤ 20 शब्द.
- खबर का तथ्य headline जैसा ("सकता है" को "हो गया" मत बनाओ). मज़ाक हालात पर: कोई असली इंसान, नेता, धर्म, जाति, क्षेत्र,
  शरीर, मर्द/औरत पर तंज़, हादसा या अपराध नहीं."""

FORMAT = """lines का ढाँचा (7 lines):
1 bablu "studio": ब्रेकिंग + खबर (छोटी) + बेतुका सूत्र
2 bablu "chacha": चाचा से छोटा सवाल   3 chacha: punch
4 bablu "pinky": पिंकी से छोटा सवाल   5 pinky: punch (अक्सर Insta trend)
6 bablu "dadi_call": दादी को video call पर बुलाओ + सवाल   7 dadi: सबसे बड़ा punch
8 bablu "studio_end": एक मज़ेदार निचोड़ + comment वाला सवाल (कुल 8 lines भी चलेगा)
"say": अंक शब्दों में, English शब्द देवनागरी में. "caption": वही, अंक अंकों में (₹30,000), English Roman में चल सकती है.
punch वाली lines पर "punch": true. dadi पर "expr": happy/shock/angry/smug/sad."""


def _lists(c):
    news = "\n".join(f"- {n['trend']}: " + " | ".join(n["headlines"]) for n in c.get("news", [])) or "(कोई नहीं)"
    insta = "\n".join(f"- {i['trend']}" + (f" — {i.get('what', '')}" if i.get("what") else "")
                      + (f" (line: {i['line']})" if i.get("line") else "")
                      + (" [मेरी feed से — इसे पहले लो]" if i.get("priority") else "")
                      for i in c.get("insta", [])) or "(कोई नहीं)"
    viral = "\n".join(f"- {v['trend']}" for v in c.get("viral", [])) or "(कोई नहीं)"
    recent = "\n".join(f"- {r}" for r in c.get("recent", [])) or "(कुछ नहीं)"
    return news, insta, viral, recent


MODE = {
    "viral": "आज का episode VIRAL वाला है: सोशल मीडिया पर वायरल खबर या Instagram trend ही मुख्य topic हो (breaking: \"Viral: ...\").",
    "news": "आज का episode NEWS वाला है: Google Trends की खबर मुख्य topic, साथ में एक Insta trend ज़रूर जुड़े.",
}


def prompt_room(c):
    news, insta, viral, recent = _lists(c)
    mode = c.get("mode", "news")
    return f"""तुम "बकरा न्यूज़" (नकली Hindi न्यूज़ चैनल, comedy Instagram page) के writers' room के head हो.

सोशल मीडिया पर वायरल खबरें (Google News):
{viral}

Instagram/social पर अभी viral:
{insta}

Google Trends की खबरें:
{news}

हाल में बन चुके episodes (इनका topic और category दोबारा मत लेना; मौसम/बारिश वाला लगातार बिल्कुल नहीं):
{recent}

{MODE.get(mode, MODE["news"])}

{CAST}

{CRAFT}

काम (joke room):
1. वो एक topic चुनो जो आज सच में लोगों के feed में चल रहा है और जिस पर हर घर हँस सके (मौसम सिर्फ़ तब जब कोई और विकल्प न हो),
   और एक Insta trend जो उससे जुड़ सके. "category" दो: viral/insta/money/tech/festival/entertainment/sports/weather/other.
2. इन slots के लिए 6-6 अलग punchlines लिखो, हर एक अलग तरकीब से: "source" (बबलू का बेतुका सूत्र), "chacha" (कम से कम 3 पुराने मशहूर jokes पर), "pinky", "guest" (दादी), "ending" (comment करवाने वाला सवाल).
3. हर punchline को सख़्ती से नंबर दो (1-10): "surprise" (उलटफेर कितना अनपेक्षित), "relate" (कितने घरों में होता है), "clear" (बिना context समझ आए).
   8 से कम औसत वाली को ईमानदारी से कम नंबर दो.
सिर्फ़ JSON:
{{"category": "...", "news_used": "...", "source_headline": "...", "insta_used": "list से हूबहू नाम या सदाबहार format", "guest": "dadi",
 "jokes": {{"source": [{{"text": "...", "trick": "...", "surprise": 0, "relate": 0, "clear": 0}}], "chacha": [], "pinky": [], "guest": [], "ending": []}}}}"""


def gold_examples():
    out = []
    for f in ("examples_chaand.json", "examples_sale.json"):
        p = ROOT / f
        if p.exists():
            j = json.load(open(p, encoding="utf-8"))
            lines = "\n".join(f"  {l['who']}: {l['say']}" for l in j["lines"])
            out.append(f"[{j.get('breaking', '')}] premise: {j.get('premise', '-')}\n{lines}")
    return "\n\n".join(out)


def prompt_critic(ep):
    lines = "\n".join(f"{i}. {l['who']}: {l['say']}" for i, l in enumerate(ep["lines"]))
    return f"""तुम Instagram के सबसे सख़्त Hindi comedy editor हो. ये episode देखो:
खबर: {ep.get('breaking')} | premise: {ep.get('premise')} | key_word: {ep.get('key_word')}
{lines}

हर punch line (chacha, pinky, dadi, आख़िरी सवाल) को जाँचो:
1. connection: क्या ये उसी खबर/premise से जुड़ी है और key_word या उसकी चीज़ वापस आती है? (नहीं = फेल)
2. हँसी: क्या आख़िरी शब्दों में साफ़ पलटी है, और 20 साल का लड़का इसे family group में भेजेगा? (1-10)
3. ये viral तरीकों में से कौन सा है: बेतुका-आत्मविश्वासी जवाब / ज़्यादा सच / कहानी-चुटकुला / शब्दों का खेल / तीन प्रकार / महँगाई-अतिशयोक्ति / आख़िर में सबसे तीखा जवाब.
जो line फेल हो या 8 से कम हो, उसे दोबारा लिखो (हिंदी में, ≤ 20 शब्द, उसी किरदार के अंदाज़ में). बाक़ी lines जैसी हैं वैसी रखो.
सिर्फ़ JSON: {{"fixes": [{{"index": 0, "say": "...", "caption": "..."}}], "verdict": "एक लाइन"}}"""


def prompt_script(room, c):
    best = {}
    for slot, items in room.get("jokes", {}).items():
        items = sorted(items, key=lambda j: -(j.get("surprise", 0) + j.get("relate", 0) + j.get("clear", 0)))
        best[slot] = [j["text"] for j in items[:2]]
    return f"""तुम "बकरा न्यूज़" के head writer हो. Joke room ने ये चुना:
खबर: {room.get('news_used')} | headline: {room.get('source_headline')}
Insta trend: {room.get('insta_used')} | मेहमान: {room.get('guest')}
हर slot के 2 सबसे अच्छे jokes (पहला सबसे ऊपर): {json.dumps(best, ensure_ascii=False)}

{CAST}

{CRAFT}

{RULES}

{FORMAT}

हमारे सबसे अच्छे पूरे episodes (ढाँचा, connection और लंबाई ऐसी ही — इनके शब्द/jokes मत दोहराना):
{gold_examples()}

काम: इन jokes से episode लिखो (ज़रूरत हो तो और तेज़ कर दो). फिर punch-up: हर punch line को सख़्त editor की तरह 1-10 दो;
जो 8 से कम हो उसे दोबारा लिखो जब तक 8+ न हो. आख़िर में सिर्फ़ final episode JSON दो:
{{"topic": "...", "premise": "एक लाइन की comic सोच", "key_word": "खबर का एक शब्द", "category": "{room.get('category', 'other')}", "news_used": "...", "insta_used": "...", "source_headline": "...", "breaking": "6-9 शब्द, सच्ची खबर",
 "hook_text": "3-6 शब्द", "poll": ["विकल्प 1", "विकल्प 2"], "icons": ["3 छोटे शब्द, सिर्फ़ अक्षर, emoji नहीं"], "ticker": "4 हिस्से '   •   ' से जुड़े, 1-2 असली बाक़ी मज़ाकिया",
 "lines": [{{"who": "bablu", "scene": "studio", "say": "...", "caption": "...", "punch": false, "insta": ""}}],
 "caption_post": "मज़ेदार लाइन + सवाल (family group में भेजो/tag करो) + असली खबर का source + 4-5 hashtags + (AI से बने किरदार)"}}"""


def clean(ep, strict=True):
    lines = ep["lines"]
    assert 5 <= len(lines) <= 10, f"lines: {len(lines)}"
    for ln in lines:
        assert ln["who"] in WHO, ln["who"]
        assert ln.get("say") and ln.get("caption")
        if ln["who"] != "bablu":
            ln["scene"] = SCENE_OF[ln["who"]]
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
        if ln["who"] == "bablu" and lines[i + 1]["who"] != "bablu":
            ln["scene"] = SCENE_OF[lines[i + 1]["who"]]
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
    assert words <= 130, f"बहुत लंबा: {words} शब्द"
    ep["icons"] = ((ep.get("icons") or []) + ["₹", "NEWS", "%"])[:3]
    ep.setdefault("ticker", ep.get("breaking", ""))
    return ep


def write(c, out="script_today.json"):
    if not os.getenv("GEMINI_API_KEY"):
        print(prompt_room(c) + "\n\n(GEMINI_API_KEY नहीं)")
        return None
    last = None
    for attempt in range(3):
        strict = attempt < 2                                # आख़िरी कोशिश में keyword वाली सख़्ती ढीली
        try:
            room = gemini.json_from(gemini.ask(prompt_room(c), json_mode=True, temperature=1.0, prefer="pro"))
            ep = clean(gemini.json_from(gemini.ask(prompt_script(room, c), json_mode=True, temperature=0.8, prefer="pro")), strict)
            try:                                           # तीसरी नज़र: सख़्त editor कमज़ोर lines दोबारा लिखे
                fx = gemini.json_from(gemini.ask(prompt_critic(ep), json_mode=True, temperature=0.6, prefer="pro"))
                for f in fx.get("fixes", []):
                    i = int(f["index"])
                    if 0 < i < len(ep["lines"]) and f.get("say") and f.get("caption"):
                        ep["lines"][i]["say"], ep["lines"][i]["caption"] = f["say"], f["caption"]
                print("  editor:", fx.get("verdict", ""), f"({len(fx.get('fixes', []))} lines सुधरीं)")
                ep = clean(ep, strict)
            except Exception as e:                         # noqa: BLE001
                print("  editor वाला कदम छोड़ा:", str(e)[:120])
            json.dump({"room": room, "episode": ep}, open(ROOT / "episodes_today.json", "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)
            json.dump(ep, open(ROOT / out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            print(f"  topic: {ep.get('topic')} | Insta: {ep.get('insta_used')}")
            return ROOT / out
        except Exception as e:                              # noqa: BLE001
            last = e
            print("  दोबारा कोशिश:", e)
    raise SystemExit(f"script नहीं बनी: {last}")


if __name__ == "__main__":
    write(json.load(open(ROOT / (sys.argv[1] if len(sys.argv) > 1 else "candidates_today.json"), encoding="utf-8")))
