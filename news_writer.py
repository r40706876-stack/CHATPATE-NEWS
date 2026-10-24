"""
काम की खबर — "खबर पक्की, अंदाज़ देसी". Gemini के सिर्फ़ 3 call में 3 scripts:
  1. चुनो:   आज की खबरों में से 3 जो सीधे आम आदमी की जेब/रोज़ की ज़िंदगी पर असर डालें
  2. जाँचो:  Google Search से हर खबर के पक्के तथ्य (तारीख़, अंक, क्या करना है, स्रोत) — शक हो तो खबर बाहर
  3. लिखो:   खबर (card, बिना मज़ाक) + मतलब (बबलू, देसी तुलना) + मसाला (एक किरदार) + क्या करें
"""
import json
import os
import re
from pathlib import Path

import gemini
import writer

ROOT = Path(__file__).parent
ICONS = {"cylinder", "calendar", "rupee", "bank", "phone", "train", "percent", "check", "alert", "gift"}
LEAN = os.getenv("LEAN", "1") == "1"                      # 1 = कम Gemini calls (free कोटा: एक run में ~4 text calls)
GOLDS = [ROOT / "examples_news_lpg.json", ROOT / "examples_news_rbi.json"]   # मालिक को पसंद आए नमूने

ALLOWED = """कौन-सी खबर लें: वो जिस पर आज लोग WhatsApp/Instagram/चाय की दुकान पर बात कर रहे हों — थोड़ी viral, थोड़ी बेतुकी,
जिसमें हर आम आदमी जुड़ जाए और व्यंग्य अपने-आप निकले ("कागज़ पर बनाम ज़मीन पर", "नियम बनाम हकीकत", "दावा बनाम सच").
जैसे: अजीब सरकारी आदेश/जुर्माना, गड्ढों वाली सड़क पर भारी चालान, पेपर लीक/परीक्षा टली, ट्रेन-बस-flight की अफ़रा-तफ़री,
दाम में अचानक उछाल (प्याज़, टमाटर, गैस, रिचार्ज), बिजली-पानी कटौती, viral हुआ सरकारी दफ़्तर/अस्पताल का हाल, ठगी का नया तरीका,
नया नियम जिससे सब परेशान, त्योहार की भीड़/किराया, AI/फ़ोन/internet वाली चर्चित बात, मौसम की मार (बिना मौत/हादसे).
सूखी "योजना की जानकारी" वाली खबर तभी, जब उसमें कोई बेतुका पेच हो.
**हमारे page के असली आँकड़े (19 reels, अक्टूबर 2026)**: चली — "Return policy ya muft ki almari" 2.7K (skip 40%),
"10 reel banakar saree return" 1.7K (10 shares), "Ramlila mein Shurpanakha" 1.3K (skip 27%), "Garba kam baraat zyada" 900
(6 shares), "Mumbai mein muft action" 461 (सबसे ज़्यादा देखा गया, 60%). यानी लोगों की आदतों/viral trend पर comedy (सोशल मीडिया,
त्योहार, शादी, shopping, रिश्तेदार, सफ़र) जिसमें देखने वाला किसी दोस्त/रिश्तेदार को tag कर सके.
मरी (60-130 views, 70-80% लोग 3 सेकंड में भागे): APK ठगी, DA hike, गोभी के दाम, "दिन भर की खबरें" bulletin, राजनीति/नेता,
सरकारी योजना. Instagram राजनीतिक content अनजान लोगों को कम दिखाता है (मुख्यमंत्री के नाम वाली reel = 10 views).
एक ही विषय दोबारा जल्दी = मर गया (return वाली दूसरी reel 148 views).
इसलिए: 6 में से कम से कम 5 खबरें आदत/viral trend वाली; सूखी सरकारी/दाम वाली ज़्यादा से ज़्यादा 1, वो भी तभी जब उसमें
किसी जानी-पहचानी आदत का मज़ाक बने. सबसे अच्छी खबर वो, जिसकी असली फ़ोटो/वीडियो में ख़ुद कुछ मज़ेदार/अजीब दिखे.
**राष्ट्रीय खबर पहले**: पूरे देश के लोगों पर असर वाली — केंद्र सरकार/RBI/रेलवे/UPI/आधार/टैक्स के नियम, देशभर के दाम,
राष्ट्रीय भर्ती-परीक्षा (SSC, रेलवे, NEET, UPSC), देशभर में viral बात. किसी एक शहर/ज़िले/मोहल्ले की खबर (जैसे "कानपुर की
सड़क", "पटना का सेंटर", "किसी नगर निगम का आदेश") नहीं — सिर्फ़ तब, जब वो पूरे देश में viral हो और हर जगह के लोग जुड़ें.
कभी नहीं: मौत, हादसा, चोट/डूबना/गिरना, हत्या/दंगा/फ़ायरिंग, युद्ध, किसी नेता/पार्टी/चुनाव/मुख्यमंत्री या असली व्यक्ति का
नाम या बयान, धर्म, जाति, celebrity gossip, बीमारी का डर."""


def _cands(c):
    out = []
    for k, label in (("kaam", "काम की"), ("viral", "वायरल"), ("news", "Trends"), ("moments", "त्योहार"), ("insta", "मेरी feed")):
        for it in c.get(k, []):
            extra = it.get("what") or " | ".join(it.get("headlines", [])[:1]) or it.get("source", "")
            out.append(f"- [{it.get('cat') or label}] {it['trend']}" + (f" ({extra})" if extra else ""))
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
असली, ज़रूरी खबर, जिस पर गंभीर news channel वाले चेहरे से तीखा व्यंग्य बने (कागज़ पर क्या कहा गया बनाम ज़मीन पर क्या होता है).

आज की खबरें:
{_cands(c)}

हाल में बन चुकी (दोबारा नहीं):
{recent}

{ALLOWED}

इनमें से {n} अलग-अलग खबरें चुनो. कम से कम 80% खबरें लोगों की आदतों/viral trend वाली हों ([वायरल वीडियो],
[रील का शौक], [शादी-रिश्ते], [shopping-आदत], [त्योहार-ट्रेंड], [सफ़र-जुगाड़], [दफ़्तर-नौकरी], [फ़िल्म-क्रिकेट फैन]) — ऐसी जिसमें
पढ़ते ही किसी जानने वाले का चेहरा याद आए; बाकी सिर्फ़ बहुत बड़ी ज़रूरी खबर. "हाल में बन चुकी" वाली बात या उससे
मिलती-जुलती (वही विषय दूसरे शब्दों में) बिल्कुल नहीं. सबसे पहले ये पूछो: "क्या आम आदमी इस पर आज बात कर रहा है, और सुनते ही बोलेगा —
'अरे, ये तो हमारे साथ भी होता है!'?" जो खबर viral हो रही हो ([वायरल]/[Trends] वाली, या जिस पर कई अख़बार लिख रहे हों)
और जिसमें व्यंग्य का साफ़ मौका हो (दावा बनाम हकीकत, बेतुका नियम, लंबा इंतज़ार, अचानक महँगाई) — वही पहले.
सूखी जानकारी वाली ("योजना में आवेदन ऐसे करें") सबसे आख़िर में. हर एक के लिए Google News पर
खोजने लायक छोटी query लिखो (2-5 शब्द, हिंदी में, जैसे "रेपो रेट बढ़ा" या "LPG आधार नियम").
विविधता ज़रूरी: हर खबर अलग विषय ([...] में लिखा विषय) से हो — एक ही विषय से दो कभी नहीं. पिछले 2 दिन में ये विषय हो चुके,
इन्हें तभी लो जब कोई बहुत बड़ी नई बात हो: {", ".join(c.get("recent_cats", [])) or "(कोई नहीं)"}.
गैस/रेल किराया जैसी हर हफ़्ते वाली खबरें तभी, जब सच में नई और बड़ी हों. सिर्फ़ JSON:
{{"picks": [{{"topic": "खबर 8-12 शब्द", "cat": "विषय (जैसे [..] में)", "why": "आम आदमी पर असर, एक लाइन", "query": "search query"}}]}}"""


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


GOLD_SATIRE = ROOT / "episodes/samples_v4.json"       # मालिक को पसंद आया v4 ढाँचा (मज़ाक से शुरुआत, टकराव, callback)


def gold_eps():
    try:
        return json.load(open(GOLD_SATIRE, encoding="utf-8"))
    except Exception:                                       # noqa: BLE001
        return []


def gold_satire():
    return "\n\n".join(f"[{e['topic']}]\n" + "\n".join(f"  {l['who']}: {l['say']}" for l in e["lines"]) for e in gold_eps())


# मालिक को सबसे ज़्यादा पसंद आई lines — यही हमारा असली हथियार है ("मुहर वाली line")
GOLD_LINES = [
    "अभ्यर्थियों से धैर्य बनाए रखने को कहा गया है। धैर्य की कोई अधिकतम आयु सीमा नहीं है।",
    "विशेषज्ञों का कहना है, सब्ज़ी खाने से सेहत बनती है। ख़रीदने से नहीं।",
    "विभाग ने साफ़ किया है, कटौती की कोई योजना नहीं है। कटौती बिना योजना के हो रही है।",
    "बैंकों ने फिर साफ़ किया है, वो कभी ओटीपी नहीं माँगते। बाकी सब माँगते हैं।",
    "अस्पताल प्रशासन ने कहा है, मरीज़ों की पूरी देखभाल की जा रही है। देखभाल करने वाले मरीज़ घर से लाते हैं।",
    "विभाग ने कहा है, परीक्षा पूरी पारदर्शिता से होगी। फ़िलहाल पारदर्शी सिर्फ़ तारीख़ है… दिखती ही नहीं।",
    "सरकार के मुताबिक़ खाद की कोई कमी नहीं है। कमी सिर्फ़ उस खिड़की की है, जहाँ खाद मिलती है।",
    "पुलिस का कहना है, चालान आपकी सुरक्षा के लिए है। सड़क के गड्ढे आपकी हिम्मत के लिए हैं।",
]

MUHAR = """"मुहर वाली line" (पूरी script में सिर्फ़ 1, ज़्यादा से ज़्यादा 2 — हर line में ये ढाँचा आया तो दूसरी line तक पैटर्न
पकड़ में आ जाता है और लोग आगे बढ़ जाते हैं):
  ढाँचा: [सरकारी/विशेषज्ञ/विभाग वाली भरोसे की बात] + [उसी के एक शब्द को पकड़कर 4-8 शब्द का उलटा वार, आख़िरी शब्द पर चोट].
  असली नमूने (स्तर समझो, शब्द मत दोहराओ):
""" + "\n".join(f"   • {l}" for l in GOLD_LINES) + """
  "शायद", "थोड़ा", "लगता है" जैसे नरम शब्द वार को मार देते हैं — वार सीधा और पक्का हो."""

SATIRE = """अंदाज़: Prakash Bharati जैसा गहरा, काला व्यंग्य — चेहरा बिल्कुल गंभीर, बात सिस्टम की कड़वी सच्चाई, पर हमारे गाँव-कस्बे
की बोलचाल में (सरकारी/अख़बारी शब्द नहीं: "दंपत्ति", "निस्तारण", "जलापूर्ति", "प्रशासन द्वारा" जैसे शब्द बोलचाल में बदलो).
गहराई कैसे आती है: छोटी खबर को बड़ी सच्चाई से जोड़ो — ज़िंदगी भर के चक्कर, काग़ज़ पर मिले हक़, बेकार समझे जाने वाले बुज़ुर्ग,
"नियम बनाम ज़मीन". पर हर गहरी बात का अंत **हँसी** पर हो, उदासी पर नहीं (बेतुकेपन को और आगे बढ़ाओ, रोओ मत).
मना (ऐसा लिखा तो script रद्द): "नमस्कार/आज की खबर" वाली शुरुआत, ज़बरदस्ती की तुलना, "हाहा", हर line में देसी शब्द ठूँसना,
किसी असली इंसान/नेता/पार्टी/धर्म/जाति पर वार, मौत/हादसे/चोट पर मज़ाक, झूठा तथ्य, "ये वीडियो उसको भेजो" वाली line."""

CASTING = """किरदार — सबकी 3D फ़ोटो तैयार हैं: कुल 2-3 किरदार (ज़्यादा से ज़्यादा 4) (bablu ज़रूरी नहीं, पर तथ्य वाली line अक्सर उसी की):
- bablu: तेज़ गाँव संवाददाता/anchor. तथ्य और सरकारी दावे वाली मुहर line, बिल्कुल गंभीर चेहरा.
- ramesh: 29 साल का परेशान नौजवान — नौकरी, परीक्षा, दफ़्तर, चालान, सिस्टम पर सच्ची भड़ास; सवाल पूछने वाला.
- chacha: पुरानी सोच वाले चाचा — "हमारे ज़माने में" को पलटकर सबसे गहरा/काला तंज़ (dark satire इन्हीं से).
- dadi: उम्र ज़्यादा, सोच नई — प्यार से पर सबसे तीखी, घर की "सरकार".
- pinky: अभी-अभी 18 की — फ़ोन, रील, online, सपने बनाम हकीकत; सबसे पहले भिड़ने वाली.
टकराव वाली जोड़ियाँ (सबसे अच्छी): pinky बनाम chacha/dadi, ramesh बनाम bablu (सरकारी दावा बनाम भड़ास), chacha बनाम ramesh."""

STRUCTURE = """ढाँचा — हमारे page के असली आँकड़ों से (19 reels, अक्टूबर 2026): जिन reels ने पहले 3 सेकंड में मज़ाक किया, उन्हें 2-10 गुना
views मिले; "खबर पढ़ने" से शुरू होने वाली reels पर 70-80% लोग 3 सेकंड में भाग गए. लोग line 2-3 पर इसलिए छोड़ते थे कि हर line
का ढाँचा एक जैसा था. Share सिर्फ़ उन पर हुए जिनमें किसी जानने वाले की आदत पर सटीक चोट थी (saree, garba, return).
सबसे पहला नियम — समझ टेस्ट: जिसने ये खबर कभी नहीं सुनी, वो पहली 2 lines सुनकर बता सके — किसने, किसके साथ, क्या किया.
(गैस-एजेंसी वाली script "वितरकों का आरोप, कंपनियाँ दबाव डाल रहीं…" मालिक ख़ुद नहीं समझ पाया — जो समझ न आए, उस पर कोई नहीं हँसता.)
  • बोलचाल के शब्द: "वितरक" नहीं "एजेंसी वाले/डीलर", "उपभोक्ता" नहीं "ग्राहक", "अनिवार्य" नहीं "ज़रूरी", "द्वारा/कथित" नहीं.
  • कौन → किस पर → क्या, एक वाक्य में साफ़ ("गैस कंपनियाँ एजेंसी वालों से ज़बरदस्ती मिठाई-नमकीन ख़रीदवा रहीं").
  • खबर दो कंपनियों/दुकानदारों/दफ़्तरों के बीच की हो और आम आदमी पर सीधा असर न हो, तो कोई किरदार अपना जाना-पहचाना अनुभव
    जोड़े (जैसे वही एजेंसी जो हमें ज़बरदस्ती पाइप बेचती है) — वरना देखने वाला सोचेगा "मुझे क्या?".
  • जोक तथ्य जैसा न लगे: जो खबर में हुआ ही नहीं (जैसे "ग्राहकों को सिलेंडर के साथ नमकीन मिल रही"), वो सच की तरह मत बोलो.
लक्ष्य (virality skill, 24 अक्टूबर 2026): share सबसे ज़्यादा, औसत 70% देखा जाए, skip 10-20%. हमारे page पर लोग औसतन
सिर्फ़ ~8 सेकंड देखते थे, जबकि reel ~30 सेकंड की थी — इसलिए अब reel छोटी और कसी: 70% = ~11 सेकंड.
कुल 4-6 lines, 35-50 शब्द (बोलने में 13-18 सेकंड; 55 से ज़्यादा = script रद्द). क्रम:
 1. HOOK (≤ 8 शब्द): line ख़ुद मज़ाक है — खबर का सबसे बेतुका पहलू, बीच-बहस से शुरुआत ("भाई, ट्रेन लेट है… या रिटायर हो गई?")
    या उलटा सच. खबर पढ़ना नहीं. **सबसे चौंकाने वाला शब्द पहले 3 शब्दों में** — भूमिका से शुरुआत नहीं
    ("ट्रैफिक जाम से बचने के लिए बंदा उड़कर…" गलत, 51% लोग भागे; "बंदा उड़कर दफ़्तर पहुँचा… जाम देखता रह गया!" सही).
    सबसे अच्छा: hook में एक सवाल/रहस्य, जिसका जवाब आख़िरी line में ("अंदर चिट्ठी है!" → "हमने भी नहीं खाई").
    vidIQ (25 अक्टूबर 2026, Hindi satire reels जो अपने औसत से 6-165 गुना चलीं) — इन्हीं ढाँचों में से एक चुनो, पिछली scripts से अलग:
     • जाना-माना ढाँचा ग़लत जगह: खबर पर WWE/क्रिकेट commentary, documentary ("भारत के छुपे अजूबे" = गड्ढा), मौसम-समाचार, शादी का कार्ड.
     • सरकारी साहब को व्यंग्य भरा सलाम + सबूत ("राम राम सरपंच साहब…" और फिर वही टूटी सड़क).
     • दाम/आकार की टक्कर ("₹5 के बिस्कुट पर पूरी जानकारी, ₹100 करोड़ की सड़क पर कुछ नहीं?").
     • बड़ी खबर पर छोटा निजी मोड़ ("हर दो महीने दिल्ली में आंदोलन… पर मेरा नाम कहीं नहीं आता").
     • ताना भरा सवाल ("क्यों भारत घूमने आना चाहती है पूरी दुनिया?" + जो दिख रहा है वही जवाब).
     • पहचान वाला किरदार ("सरकारी नौकरी वाला दामाद है… तो सब चलता है").
    हमारे page पर pun वाली headline सबसे ज़्यादा भागी ("टिकट कन्फ़र्म… पर सपने में" 65% skip) — शब्दों का खेल नहीं, सिस्टम पर सीधी चोट.
 2. तथ्य + पंच (≤ 12 शब्द): असली बात (अंक/तारीख़ हूबहू) एक छोटे वाक्य में, और **उसी line के आख़िर में छोटा पंच**.
    Instagram के retention graph में हर reel पर 3-5 सेकंड पर आधे लोग जाते थे — ठीक यहाँ, जब मज़ा रुककर खबर पढ़ी जाती थी.
    सही: "पीठ पर मशीन बाँधकर बंदा उड़कर दफ़्तर पहुँचा… attendance फिर भी half-day लगी।"
    गलत: "पीठ पर उड़ने वाली मशीन बाँधकर ऑफिस जाने वाले व्यक्ति का वीडियो वायरल हुआ है।" ("वायरल हो गया/हुआ", "सोशल
    मीडिया पर…", "लोगों ने देखा" जैसे ख़ाली शब्द किसी line में कभी नहीं — script रद्द). "card" यहीं (वैकल्पिक).
 3. RE-HOOK (≤ 10 शब्द): ठीक ~5 सेकंड पर (यहीं हमारे लोग जाते थे) मोड़ — "पर असली खेल तो अब है…", "और सरकार का जवाब
    सुनिए…" जैसा (अपने शब्दों में) + पिछली से बड़ी बात. "वैसे/ख़ैर/तो दोस्तों" जैसी ढीली line कभी नहीं.
 4. PEHCHAAN / TAG वाली line (≤ 14 शब्द, ज़रूरी): किसी पहचाने जाने वाले इंसान की आदत पर इतनी सटीक चोट कि देखने वाला बोले
    "अरे ये तो बिल्कुल पापा/फूफा/राहुल है!" — यही line share करवाती है (हमारी सबसे ज़्यादा share वाली reel "भैया थोड़ा खिसक
    जाओ" ऐसी ही थी; "Free hit" को 1,240 views मिले पर ऐसा पल नहीं था → 0 share). इस line पर "tag": true और
    "tag_screen" (≤ 6 शब्द, screen पर: "वो पापा जो छत पर…"). अगर तुम नहीं बता सकते कि देखने वाला ये reel किसे भेजेगा — script रद्द.
 5. आख़िरी line = सबसे बड़ा वार (मुहर वाली हो सकती है) + LOOP: पहली line का कोई शब्द पकड़कर पलटो, ताकि reel ख़त्म होते ही
    शुरू से जुड़ी लगे और लोग दोबारा देखें ("आसमान से इंटरनेट…" → "…गली का तार अब भी आसमान से लटका है"). सबसे मज़ेदार शब्द सबसे आख़िर में.
    "ये वीडियो उसको भेजो/शेयर करो/टैग करो/फ़ॉलो करो" कभी नहीं — भेजने की वजह line 4 की चोट है, बोलकर माँगना नहीं.
हर line पिछली से एक सीढ़ी ज़्यादा बेतुकी, और अलग ढाँचे की (सवाल, भड़ास, तुलना, मुहर, callback). कोई line सिर्फ़ अगली line
को सेट करने के लिए नहीं — हर line में अपना मज़ा."""

FIELDS = """हर line में: "expr" (gambhir / hasi / tanz / gussa / hairan / udaas — एक ही भाव लगातार 2 से ज़्यादा नहीं; bablu की
मुहर line "gambhir"), "set" (पीछे की जगह — line की बात से, किरदार से नहीं: bablu तथ्य/मुहर = "studio"; दफ़्तर/फ़ॉर्म/भर्ती =
"office"; चालान/गड्ढे/सड़क/ट्रैफिक = "road"; सब्ज़ी/दाम/बाज़ार = "mandi"; घर/परिवार/आँगन की बात = "aangan"; फ़ोन/रील/online/पढ़ाई =
"room"; गैस/सिलेंडर = "gas"; रसोई/खाना = "kitchen"; ट्रेन/स्टेशन/सफ़र = "station"; अस्पताल = "hospital"; खेत/किसान = "khet";
स्कूल/परीक्षा = "school"; बैंक/UPI/लोन = "bank"; बिजली = "bijli"; राशन = "ration"; ठगी की रिपोर्ट = "thana"; बाकी = "village").
"visuals" = 3 English खोज जो उस line की ठोस चीज़/जगह दिखाएँ ("indian train platform crowd", "train engine door") — भाव नहीं,
हीरो-हीरोइन/मशहूर चेहरे नहीं. "photo_hi" = 2 Hindi खबर-खोजें (2-4 शब्द, जगह/चीज़ का नाम) जिनसे इसी खबर की असली फ़ोटो मिले.
"punch": true + "stamp" (2-4 शब्द, उसी line के शब्दों से: "सुविधा… आउटर पर!") सिर्फ़ 2 सबसे तेज़ lines पर.
"say" में अंक शब्दों में ("चौबीस घंटे"), English short form देवनागरी में; "caption" = वही बात, अंक अंकों में."""


def prompt_punches(packs):
    """पंच-बैंक: हर खबर पर पहले ढेर सारे hooks/पंच — फिर सिर्फ़ सबसे तेज़ से script बनती है (एक बार में लिखी script औसत रहती है)."""
    return f"""तुम "बकरा न्यूज़" के सबसे तेज़ comedy writer हो (Prakash Bharati जैसा गहरा, देसी व्यंग्य). तथ्य (सिर्फ़ इन्हीं से):
{json.dumps(packs, ensure_ascii=False, indent=1)}

{SATIRE}

हर खबर के लिए कच्चा माल लिखो (script नहीं — सिर्फ़ ढेर सारे विकल्प, हर एक अलग ढाँचे का):
- "people": 3 पहचाने जाने वाले इंसान जिनकी आदत इस खबर से जुड़ती है ("वो दोस्त जो हर ट्रेन को टाइम पे बताता है").
- "hooks": 6 पहली lines (≤ 10 शब्द, सबसे चौंकाने वाला शब्द पहले 3 शब्दों में, "X से बचने के लिए…" जैसी भूमिका नहीं), हर एक ख़ुद में मज़ाक: 2 बीच-बहस वाली (किरदार की भड़ास/सवाल), 2 उलटा सच, 2 बेतुका अंजाम.
  छहों अलग-अलग HOOK ढाँचे से हों (एक ही ढाँचा दोबारा नहीं): समय सिकुड़ा ("पहले राशन कार्ड 1 महीने में, अब ऑनलाइन — 3 महीने"),
  पहले-और-बाद ("2019 में सड़क ऐसी, 2026 में ऐसी — फ़र्क सिर्फ़ बोर्ड की तारीख़ का"), आमने-सामने ("जापान की मंगल मिट्टी बनाम हमारी गली की मिट्टी"),
  इजाज़त ("आपको सड़क की ज़रूरत नहीं — आपके पास धैर्य है"), आधे वाक्य से ("...और तभी पता चला पुल उद्घाटन से पहले ही आराम कर रहा है"),
  उल्टी कहावत ("जहाँ चाह, वहाँ राह — बशर्ते PWD ने खोदी न हो"), खुलासा ("ये है नया स्मार्ट सिटी…"), सबसे बड़ा ("देश का सबसे तेज़ सिस्टम है चालान").
  ये उदाहरण सिर्फ़ ढाँचा दिखाने को हैं — शब्द कॉपी मत करो, हर hook इसी खबर के तथ्य से बने.
- "tags": 3 TAG lines (≤ 18 शब्द) — "people" में से किसी की आदत पर ऐसी सटीक चोट कि सुनने वाला किसी को tag करे.
- "facts": 3 "तथ्य + पंच" lines (≤ 12 शब्द): असली बात छोटे वाक्य में और उसी line के आख़िर में छोटा पंच
  ("वायरल हो गया है" जैसे ख़ाली शब्द नहीं). जिसने खबर नहीं सुनी, वो इसी line से समझे: किसने, किसके साथ, क्या —
  बोलचाल के शब्दों में ("वितरक/उपभोक्ता/अनिवार्यता/द्वारा" नहीं).
- "stories": 2 छोटी कहानियाँ (3 lines): एक किरदार ने क्या किया → फिर क्या हुआ → उलटा नतीजा.
- "punches": 8 पंच (≤ 18 शब्द): 2 मुहर वाली (सरकारी दावा + उसी शब्द का उलटा), 2 "हमारे ज़माने" को पलटकर काला तंज़ (चाचा),
  2 बेतुका अंजाम तक, 2 छोटा सवाल-छोटा जवाब.
- "callbacks": 3 आख़िरी lines (≤ 10 शब्द) जो किसी hook के शब्द पर लौटें.
सिर्फ़ JSON list, खबरों के क्रम में: [{{"topic": "...", "people": [...], "hooks": [...], "facts": [...], "stories": [[...]], "tags": [...], "punches": [...], "callbacks": [...]}}]"""


def prompt_write(packs, bank=None):
    raw = ""
    if bank:
        raw = f"""
हर खबर का कच्चा माल (पंच-बैंक) — पहले सख़्त editor बनो: हर खबर के लिए सबसे तेज़ 1 hook, 1 "तथ्य + पंच", 1 TAG (पहचान) line, 1 पंच और 1 callback चुनो (पैमाना:
"क्या गाँव-कस्बे का आदमी पहली बार सुनकर हँसेगा, और किसी को tag करेगा?"), फिर script उन्हीं के चारों ओर बनाओ — ज़रूरत हो तो
उन्हें और तेज़ करो, पर कमज़ोर filler line मत जोड़ो (हर line में अपना मज़ा हो):
{json.dumps(bank, ensure_ascii=False, indent=1)}
"""
    return f"""तुम "बकरा न्यूज़" के head writer हो ("खबर सौ टका पक्की, अंदाज़ अधपका!"). तथ्य (सिर्फ़ इन्हीं से, कुछ जोड़ना नहीं):
{json.dumps(packs, ensure_ascii=False, indent=1)}
{raw}
{STRUCTURE}

{SATIRE}

{MUHAR}

{CASTING}

{FIELDS}
"ask" = आख़िर में screen पर लिखा comment वाला सवाल (≤ 9 शब्द, बोला नहीं जाएगा), जिसका जवाब हर कोई अपने अनुभव से दे.
"ticker" = 3 छोटे जोक (≤ 10 शब्द, सरकारी-खबर वाली भाषा में).

हमारे पसंदीदा नमूने — ढाँचा और गहराई ऐसी ही (शब्द/पंच मत दोहराना, हर खबर के अपने शब्द पकड़ो):
{gold_satire()}

सिर्फ़ JSON — हर खबर का एक episode:
[{{"topic": "...", "category": "money/rules/bank/jobs/scheme/tech/travel/civic/other", "breaking": "6-9 शब्द, सच्ची headline",
  "hook_text": "पहली line हूबहू", "hook_screen": "≤ 5 शब्द, पहले 2 सेकंड screen पर (बोली गई line का सबसे चौंकाने वाला हिस्सा)", "ask": "...", "source": "प्रकाशकों के नाम", "poll": ["2-4 शब्द", "2-4 शब्द"], "ticker": ["...", "...", "..."],
  "cast_why": "इन किरदारों में टकराव क्या है, एक लाइन", "tag_who": "किस पहचाने जाने वाले इंसान पर चोट है",
  "lines": [{{"who": "ramesh", "say": "...", "caption": "...", "expr": "gussa", "set": "station", "visuals": ["...", "...", "..."], "photo_hi": ["...", "..."]}},
            {{"who": "bablu", "say": "...", "caption": "...", "expr": "gambhir", "set": "studio", "visuals": ["...", "...", "..."], "photo_hi": ["...", "..."],
              "card": {{"tag": "...", "big": "...", "sub": "...", "icon": "train"}}}},
            {{"who": "chacha", "say": "...", "caption": "...", "expr": "tanz", "set": "station", "visuals": ["...", "...", "..."],
              "tag": true, "tag_screen": "≤ 6 शब्द"}},
            {{"who": "bablu", "say": "...", "caption": "...", "expr": "gambhir", "set": "studio", "visuals": ["...", "...", "..."],
              "punch": true, "stamp": "2-4 शब्द"}}],
  "caption_post": "पहली line + 'Tag करो उसको जो…' (tag_who वाला इंसान) + comment वाला सवाल + स्रोत: ... + 4-5 hashtags + (AI से बने किरदार)"}}]
icon इनमें से: {", ".join(sorted(ICONS))}."""


def prompt_sharpen(eps):
    """जज की बताई कमी दूर करो — तथ्य वही, सिर्फ़ व्यंग्य/hook/पंच तीखे."""
    slim = [{"n": i + 1, "weak": (e.get("connect") or {}).get("weak", ""), "fix": (e.get("connect") or {}).get("fix", ""),
             "episode": e} for i, e in enumerate(eps)]
    return f"""तुम "बकरा न्यूज़" के comedy editor हो. इन scripts को जज ने कम नंबर दिए; उसकी बताई कमी ("weak") और सुझाव ("fix")
के हिसाब से दोबारा लिखो:
{json.dumps(slim, ensure_ascii=False, indent=1)}

{STRUCTURE}

{SATIRE}

{MUHAR}
नियम: तथ्य, अंक, तारीख़, card, स्रोत बिल्कुल वही. कोई नया तथ्य नहीं. JSON का ढाँचा वही (सारे fields रखो, "hook_text" = पहली line).
सिर्फ़ JSON list लौटाओ — उतने ही episodes, उसी क्रम में."""


EXPRS, POSES, SETS_OK = {"gambhir", "hasi", "tanz", "gussa", "hairan", "udaas"}, {"laugh", "facepalm", "eyeroll", "thinking", "smug"}, {"studio", "village", "office", "road", "mandi", "aangan", "room", "gas", "kitchen", "station", "hospital", "khet", "school", "thana", "bank", "bijli", "ration"}


SET_PAT = {   # set → उसकी बात के शब्द. Gemini का चुना set line/खबर से मेल न खाए तो शब्दों से सही set (नदी वाली खबर पर मंडी नहीं)
    "thana": "ठगी|थाना|पुलिस|फ़्रॉड|फ्रॉड|साइबर|हैक|एपीके|लिंक|ओटीपी",
    "road": "चालान|गड्ढ|सड़क|ट्रैफिक|हेलमेट|बाइक|गाड़ी|स्कूटी",
    "mandi": "सब्ज़ी|सब्जी|टमाटर|प्याज़|प्याज|मंडी|बाज़ार|बाजार|भाव|दाम",
    "office": "दफ़्तर|दफ्तर|(?<!प्लेट)फ़ॉर्म|(?<!प्लेट)फॉर्म|भर्ती|बाबू|फ़ाइल|फाइल|नौकरी|बॉस|ऑफिस|पेंशन",
    "school": "परीक्षा|पेपर|रिज़ल्ट|रिजल्ट|स्कूल|कॉलेज|छात्र",
    "bank": "बैंक|यूपीआई|लोन|एटीएम|खाता|किस्त|ईएमआई",
    "bijli": "बिजली|ट्रांसफ़ॉर्मर|ट्रांसफार्मर|कटौती",
    "station": "ट्रेन|रेल|स्टेशन|टिकट|प्लेटफ़ॉर्म|प्लेटफार्म|सफ़र|सफर|बस अड्डा|बस स्टैंड",
    "hospital": "अस्पताल|डॉक्टर|दवा|इलाज|मरीज़|मरीज",
    "khet": "किसान|खाद|फ़सल|फसल|खेत",
    "gas": "गैस|सिलेंडर",
    "ration": "राशन",
    "kitchen": "रसोई|खाना|थाली|चूल्हा",
    "room": "फ़ोन|फोन|मोबाइल|ऑनलाइन|इंस्टा|रील|वाई-फ़ाई|इंटरनेट|शॉपिंग|पार्सल|लहंगा|साड़ी",
    "aangan": "घर|मम्मी|पापा|सफ़ाई|सफाई|कबाड़|रिश्तेदार|शादी|बुआ|दिवाली|त्योहार|गरबा",
}
SEND = re.compile(r"(वीडियो|वीडिओ|video|रील).{0,25}(भेजो|भेज दो|शेयर|टैग)|उसको भेजो|उसे भेजो")
FILLER = re.compile(r"वायरल (हो गया|हो गई|हो रहा|हो रही|हुआ|हुई)|सोशल मीडिया पर (इस|एक|ये|यह|तेज़ी|तेजी|खूब|जमकर)|"
                    r"लोगों ने (देख|देखा)|तेज़ी से वायरल|तेजी से वायरल")   # retention graph: यहीं लोग भागते थे
# अख़बारी शब्द → बोलचाल (मालिक "वितरकों का आरोप" वाली गैस-एजेंसी script ख़ुद नहीं समझ पाया था, 23 अक्टूबर 2026).
# SWAP = सीधे बदलने लायक (पूरा शब्द ही); HARD = बदलना वाक्य पर निर्भर → strict में script रद्द, ढीली में ⚠️ और जज के नंबर कम.
SWAP = [("वितरकों", "डीलरों"), ("वितरक", "डीलर"), ("उपभोक्ताओं", "ग्राहकों"), ("उपभोक्ता", "ग्राहक"), ("दंपत्ति", "पति-पत्नी"),
        ("दंपति", "पति-पत्नी"), ("दंपती", "पति-पत्नी"), ("अनिवार्य", "ज़रूरी"), ("एवं", "और"), ("के हेतु", "के लिए"),
        ("हेतु", "के लिए"), ("किंतु", "लेकिन"), ("परंतु", "लेकिन"), ("अतः", "इसलिए")]
HARD = re.compile(r"(?<![ऀ-ॿ])(द्वारा|कथित|विनियमन|अधिसूचना|प्रावधान|संचालक|क्रियान्वयन|अनिवार्यता|उपरोक्त|तत्पश्चात|"
                  r"जलापूर्ति|निस्तारण)")


def plain(t):
    """किताबी शब्द → बोलचाल. सिर्फ़ पूरे शब्द पर (गुरुद्वारा/तथाकथित/तत्काल टिकट जैसे शब्द नहीं छूते)."""
    for a, b in SWAP:
        t = re.sub(rf"(?<![ऀ-ॿ]){a}(?![ऀ-ॿ])", b, str(t))
    return t


def bookish(lines):
    """lines में बचे किताबी शब्द (SWAP वाले भी, अगर plain() नहीं चला) — चेतावनी/जज के लिए."""
    found = []
    for l in lines:
        s = str(l.get("say", ""))
        found += HARD.findall(s)
        found += [a for a, _ in SWAP if re.search(rf"(?<![ऀ-ॿ]){a}(?![ऀ-ॿ])", s)]
    return list(dict.fromkeys(found))


def pick_set(who, text, topic, given=""):
    """line की बात से set: पहले line के शब्द, फिर खबर के. bablu का anchor/तथ्य = studio."""
    if given in SET_PAT and re.search(SET_PAT[given], text + " " + topic):
        return given
    if who == "bablu" and given in ("studio", ""):
        return "studio"
    for src in (text, topic):
        for name, pat in SET_PAT.items():
            if re.search(pat, src):
                return name
    return "studio" if who == "bablu" else ("village" if given not in SETS_OK or given in SET_PAT else given)


def nwords(t):
    return len(str(t).split())


def finish(ep, strict=True):
    """नए v4 ढाँचे वाले episode को पक्का करो. strict=False: लंबाई की सख़्ती ढीली (कुछ भी न बने, उससे अच्छा).
    पक्के नियम (असली आँकड़ों से): पहली line = मज़ाक वाला hook ≤ 12 शब्द, कुल ≤ 78 शब्द, "वीडियो भेजो" वाली line नहीं,
    hook (screen) = पहली बोली गई line, reaction वाला ठहराव नहीं, ज़्यादा से ज़्यादा 2 पंच."""
    ep["format"], ep["label"] = "explain", "काम की खबर"
    ep.setdefault("key_word", "")
    ep.setdefault("icons", ["₹", "NEWS", "%"])
    ep["source"] = ep.get("source") or "Google News"
    ep["ticker"] = [str(t)[:80] for t in (ep.get("ticker") or [])][:4]
    ep["ask"] = str(ep.get("ask") or "")[:60]
    ep["lines"] = [l for l in ep["lines"] if l.get("who") in writer.WHO and str(l.get("say", "")).strip()]
    sends = [l for l in ep["lines"] if SEND.search(l["say"])]
    if sends and len(ep["lines"]) - len(sends) >= 5:            # "ये वीडियो उसको भेजो" — बोलकर माँगने से share नहीं होता
        ep["lines"] = [l for l in ep["lines"] if l not in sends]
    topic = str(ep.get("topic") or ep.get("breaking") or "")
    punches = 0
    ep["ask"] = plain(ep["ask"])
    for ln in ep["lines"]:
        ln["say"] = plain(ln["say"])                          # "\u0935\u093F\u0924\u0930\u0915" \u2192 "\u0921\u0940\u0932\u0930" \u0935\u0917\u0948\u0930\u0939: \u091C\u094B \u0938\u0941\u0928\u0928\u0947 \u092E\u0947\u0902 \u0938\u092E\u091D \u0928 \u0906\u090F, \u0909\u0938 \u092A\u0930 \u0939\u0901\u0938\u0940 \u0928\u0939\u0940\u0902
        cap = plain(ln.get("caption") or "")
        ln["caption"] = cap
        if len(re.findall(r"[\u0900-\u097F]", cap)) < len(re.findall(r"[A-Za-z]", cap)) or len(cap) < 4:
            ln["caption"] = ln["say"]
        vis = [str(v) for v in (ln.get("visuals") or []) if str(v).strip()][:3]
        ln["visuals"] = vis
        if vis and not ln.get("visual"):
            ln["visual"] = vis[0]                           # पुराने renderer के लिए
        ln["expr"] = ln.get("expr") if ln.get("expr") in EXPRS else "gambhir"
        ln["set"] = pick_set(ln["who"], ln["say"], topic, ln.get("set") if ln.get("set") in SETS_OK else "")
        ln.pop("react_pose", None)                          # reaction का 0.7 सेकंड ठहराव = flow टूटता था → हटाया
        if ln.get("punch") and punches < 2:
            punches += 1
            if ln.get("stamp"):
                ln["stamp"] = str(ln["stamp"])[:22]
        else:
            ln.pop("punch", None)
            ln.pop("stamp", None)
        c = ln.get("card")
        if c:
            if not c.get("big"):
                ln.pop("card")
                continue
            c["icon"] = c.get("icon") if c.get("icon") in ICONS else "check"
            c["big"], c["tag"], c["sub"] = str(c["big"])[:40], str(c.get("tag", ""))[:28], str(c.get("sub", ""))[:70]
    if len(ep["lines"]) > 6:                                # virality skill: reel 13-18 सेकंड — ज़्यादा से ज़्यादा 6 lines (आख़िरी = loop)
        ep["lines"] = ep["lines"][:5] + ep["lines"][-1:]
    ep = writer.clean(ep, strict=False)
    first = ep["lines"][0]["say"].strip()
    ep["hook"] = ep["hook_text"] = first if nwords(first) <= 12 else " ".join(first.split()[:10]) + "…"
    hs = str(ep.get("hook_screen") or "").strip()
    if hs and not ep.get("hook_short"):                     # पहले 2 सेकंड screen पर ≤ 5 शब्द (एक नज़र में पढ़ा जाए)
        ep["hook_short"] = " ".join(hs.split()[:5])
    for ln in ep["lines"]:                                  # पहचान वाली line का छोटा रूप screen पर — यही share करवाता है
        ts = str(ln.get("tag_screen") or "").strip()
        if ln.get("tag") and ts and not ln.get("tag_text"):
            ln["tag_text"] = " ".join(ts.split()[:6])
    words = sum(nwords(l["say"]) for l in ep["lines"])
    cast = {l["who"] for l in ep["lines"]}
    if strict:
        assert nwords(first) <= 10, f"पहली line लंबी ({nwords(first)} शब्द) — hook 8 शब्द तक"
        assert words <= 55, f"बहुत लंबा: {words} शब्द (35-50 चाहिए, reel 13-18 सेकंड)"
        assert any(l.get("tag") for l in ep["lines"]), "पहचान (tag) वाली line नहीं — share की वजह नहीं"
        assert len(cast) <= 4, f"किरदार बहुत: {cast}"
        assert len(cast) >= 2, "टकराव के लिए कम से कम 2 किरदार"
        assert not any(SEND.search(l["say"]) for l in ep["lines"]), "'वीडियो भेजो' वाली line"
        assert not re.match(r"\s*(नमस्कार|आज की खबर)", first), "नमस्कार/आज की खबर से शुरुआत"
        assert nwords(ep["lines"][1]["say"]) <= 15, f"दूसरी line लंबी ({nwords(ep['lines'][1]['say'])} शब्द) — 3-5 सेकंड वाली खाई"
        bad = [l["say"] for l in ep["lines"] if FILLER.search(l["say"])]
        assert not bad, f"ख़ाली शब्द ('वायरल हो गया' वगैरह): {bad[0][:40]}"
        hard = bookish(ep["lines"])
        assert not hard, f"किताबी शब्द ({', '.join(hard)}) — आम आदमी पहली बार सुनकर नहीं समझेगा"
    return ep


RISKY = re.compile(r"हत्या|मर्डर|रेप|दुष्कर्म|बलात्कार|यौन|आत्महत्या|सुसाइड|लाश|शव|मौत|मारे गए|हमला|आतंक|गोली|"
                   r"घायल|डूब|बह गए|बह गई|नदी में गिर|छत से गिर|फ़ायरिंग|फायरिंग|झुलस|डंक|अस्पताल पहुं|अस्पताल पहुँ|"
                   r"रेस्क्यू|फंसी मासूम|फंसा मासूम|फंसी बच्ची|जेल|"
                   r"murder|rape|suicide|killed|dead|terror|sex", re.I)


def _safe(c):
    """Gemini का safety filter पूरा prompt रोक दे तो: अपराध/मौत वाली खबरें हटाकर (वैसे भी हम उन पर व्यंग्य नहीं करते)."""
    c2 = dict(c)
    for k in ("kaam", "viral", "news", "moments", "insta"):
        c2[k] = [it for it in c.get(k, []) if not RISKY.search(json.dumps(it, ensure_ascii=False))]
    return c2


def gather(c, n):
    """खबरें चुनो → trend जाँचो → पक्के तथ्य. लौटाता है (packs, picks). c["rejected"] भरता है. rant_writer भी यही इस्तेमाल करता है."""
    import viral_check as vc
    try:
        raw = gemini.ask(prompt_pick(c, min(n * 2 + 3, 15)), json_mode=True, temperature=0.4)
    except gemini.QuotaOver:
        raise
    except gemini.Blocked as e:                            # सिर्फ़ safety filter पर (कोटा/busy पर दोबारा भेजना बेकार था)
        print("  खबरों की list Gemini ने नहीं ली, अपराध/मौत वाली हटाकर दोबारा:", repr(e)[:150])
        c.update(_safe(c))                                  # वही dict रहे (c["rejected"] बाहर भी दिखे)
        raw = gemini.ask(prompt_pick(c, min(n * 2 + 3, 15)), json_mode=True, temperature=0.4)
    picks = [p for p in gemini.json_from(raw).get("picks", [])
             if p.get("topic") and not RISKY.search(str(p.get("topic")) + " " + str(p.get("query", "")))]
    for p in picks:                                         # पहली जाँच: खबर सच में आज उठी हुई है? (free, Gemini नहीं)
        sc, why, heads = vc.trend(p.get("query") or p["topic"])
        p["trend"], p["_heads"] = {"score": sc, "why": why}, heads
        print(f"  {'✅' if sc >= vc.TREND_MIN else '❌'} trend {sc}/10: {p.get('topic')} | {why}")
    recent = set(c.get("recent_cats", []))
    picks.sort(key=lambda p: (str(p.get("cat", "")) in recent, -p["trend"]["score"]))   # नए विषय पहले
    c["rejected"] = [p for p in picks if p["trend"]["score"] < vc.TREND_MIN]
    import topics
    ok, cats = [], set()

    def dry(p):                                             # सूखी खबर (APK/DA/सब्ज़ी के दाम: 70-80% skip) — 6 में ज़्यादा से ज़्यादा 1
        cat = str(p.get("cat", ""))                         # Gemini "[वायरल]" जैसे brackets के साथ भी लौटाता है
        return not any(v in cat for v in (*topics.VIRAL_CATS, "वायरल", "Trends", "त्योहार", "मेरी feed", "रील"))

    def room(p):
        return not dry(p) or sum(dry(q) for q in ok) < 1

    for p in picks:                                         # एक विषय से एक ही खबर
        cat = str(p.get("cat") or p.get("topic"))
        if p["trend"]["score"] >= vc.TREND_MIN and cat not in cats and room(p):
            ok.append(p)
            cats.add(cat)
    for p in picks:                                         # कम पड़ें तो: थोड़ी कम चर्चित पर असली खबरें (2+ अख़बार) से 3 पूरे
        cat = str(p.get("cat") or p.get("topic"))
        if len(ok) >= n + 1:
            break
        if p not in ok and p["trend"]["score"] >= (1 if any(v in cat for v in topics.VIRAL_CATS) else 2) \
                and p.get("_heads") and cat not in cats and room(p):
            ok.append(p)
            cats.add(cat)
    picks = ok[:n + 1]                                      # 1 ज़्यादा, ताकि आगे कोई कटे तो भी 3 बचें
    print("  चुने विषय:", [p.get("cat") for p in picks])
    if not picks:
        raise NoViral(c["rejected"])
    evidence = {i: p.pop("_heads") for i, p in enumerate(picks)}
    packs = gemini.json_from(gemini.ask(prompt_facts(picks, evidence), json_mode=True, temperature=0.1))
    packs = [p for p in packs if str(p.get("confidence", "")).lower() != "low" and p.get("facts")]
    for p in packs:
        print("  तथ्य:", p.get("topic"), "|", p.get("source"), "|", p.get("confidence"))
    if not packs:
        raise SystemExit("एक भी खबर के पक्के तथ्य नहीं मिले")
    return packs, picks


def write_options(c, n=3):
    c = _safe(c)                                            # मौत/हादसा/चोट/अपराध वाली खबरें शुरू से बाहर (उन पर हँसी नहीं बनती)
    packs, picks = gather(c, n)
    return write_from(c, packs, picks, n)


def write_from(c, packs, picks, n=3):
    """पक्के तथ्यों (gather) से "वायरल खबर" वाली n scripts — पंच-बैंक → script → जज → तीखा."""
    import viral_check as vc
    c.setdefault("rejected", [])
    bank = None                                             # पंच-बैंक: पहले ढेर सारे hooks/पंच, फिर सबसे तेज़ से script
    try:
        bank = None if LEAN else gemini.json_from(gemini.ask(prompt_punches(packs), json_mode=True, temperature=0.95))
        bank = bank if isinstance(bank, list) and bank else None
        print("  पंच-बैंक:", sum(len(b.get("punches", [])) + len(b.get("hooks", [])) for b in bank or []), "विकल्प")
    except gemini.QuotaOver:
        raise
    except Exception as e:                                  # noqa: BLE001
        print("  पंच-बैंक नहीं बना, सीधे script:", repr(e)[:120])
    raw = gemini.json_from(gemini.ask(prompt_write(packs, bank), json_mode=True, temperature=0.8))
    raw = [r for r in raw if isinstance(r, dict) and r.get("lines")]
    eps = []
    for ep in raw:
        for strict in (True, False):
            try:
                fe = finish(json.loads(json.dumps(ep)), strict)
                if not strict:
                    fe["_loose"] = True                     # ढाँचे से बाहर — Telegram पर ⚠️, और चुनाव में सबसे आख़िर
                eps.append(fe)
                break
            except Exception as e:                          # noqa: BLE001
                print(f"  episode ({'सख़्त' if strict else 'ढीला'}) नहीं बना:", ep.get("topic"), "—", e)
    if not eps:
        raise SystemExit("एक भी script नहीं बनी")
    for ep in eps:                                          # हर script पर उसकी खबर का trend नंबर
        w = set(str(ep.get("topic", "")).split())
        best = max(picks, key=lambda p: len(w & set(str(p.get("topic", "")).split())))
        ep["trend"] = best["trend"]
        ep["category"] = best.get("cat") or ep.get("category", "other")
    if not LEAN:                                            # LEAN: जज/तीखा वाले calls बंद (free कोटा बचे; चुनाव मालिक करता है)
        vc.connect(eps)                                     # दूसरी जाँच: लोग जुड़ेंगे? (Gemini 1 call)
    penalize(eps)
    weak = [] if LEAN else [e for e in eps if (e.get("connect") or {}).get("score", 10) < vc.CONNECT_MIN]
    if weak:                                                # कमज़ोर scripts एक बार और तीखी करो, फिर दोबारा जाँचो
        try:
            try:
                again = gemini.json_from(gemini.ask(prompt_sharpen(weak), json_mode=True, temperature=0.85))
            except gemini.QuotaOver:
                raise
            except Exception as e:                          # noqa: BLE001  Gemini busy (503) — 1 मिनट रुककर एक बार और
                print("  तीखा करने में Gemini busy, 60s बाद दोबारा:", repr(e)[:80])
                import time
                time.sleep(60)
                again = gemini.json_from(gemini.ask(prompt_sharpen(weak), json_mode=True, temperature=0.85))
            fixed = []
            for old_ep, new_ep in zip(weak, again if isinstance(again, list) else []):
                try:
                    ne = finish(new_ep, strict=False)
                    ne["trend"] = old_ep.get("trend")
                    fixed.append((old_ep, ne))
                except Exception as e:                      # noqa: BLE001
                    print("  तीखी script नहीं बनी:", e)
            if fixed:
                vc.connect([ne for _, ne in fixed])
                penalize([ne for _, ne in fixed])
                for old_ep, ne in fixed:
                    if (ne.get("connect") or {}).get("score", 0) > (old_ep.get("connect") or {}).get("score", 0):
                        eps[eps.index(old_ep)] = ne
                        print(f"  ✍️ तीखी की: {ne.get('topic')} → {(ne.get('connect') or {}).get('score')}/10")
        except gemini.QuotaOver:
            raise
        except Exception as e:                              # noqa: BLE001
            print("  तीखा करने वाला कदम छोड़ा:", repr(e)[:150])
    good = [e for e in eps if (e.get("connect") or {}).get("score", vc.CONNECT_MIN) >= vc.CONNECT_MIN]
    for e in eps:
        print(f"  {'✅' if e in good else '❌'} connect {(e.get('connect') or {}).get('score', '?')}/10: {e.get('topic')}")
    c["rejected"] += [e for e in eps if e not in good]
    if len(good) < n and eps:                               # हमेशा 3 विकल्प: कम पड़ें तो बाकी में से सबसे अच्छी (नंबर साफ़ दिखते हैं)
        rest = sorted([e for e in eps if e not in good],
                      key=lambda e: (bool(e.get("_loose")), -(e.get("connect") or {}).get("score", 0)))
        good = good + rest[:n - len(good)]
        print("  कोई 7+ नहीं — फिर भी सबसे अच्छी", len(good), "भेज रहे (नंबर साफ़ दिखेंगे)")
    if not good:
        raise NoViral(c["rejected"])
    if LEAN:                                                # सबसे चर्चित खबर पहले
        good.sort(key=lambda e: -((e.get("trend") or {}).get("score", 0)))
    return good


def copied(ep):
    """नमूनों (GOLD_LINES) से हूबहू/थोड़ा बदलकर उठाई lines."""
    import difflib
    out = []
    golds = GOLD_LINES + [l["say"] for e in gold_eps() for l in e.get("lines", [])]
    for ln in ep.get("lines", []):
        for g in golds:
            if difflib.SequenceMatcher(None, ln.get("say", ""), g).ratio() > 0.7:
                out.append(ln["say"])
                break
    return out


def penalize(eps):
    """जज नरम न रहे: मुहर वाली नई lines कम (E=0) हों तो ज़्यादा से ज़्यादा 6; नमूना उठाया तो 5 — फिर ये दोबारा लिखी जाती हैं."""
    for ep in eps:
        c = ep.get("connect")
        if not c:
            continue
        cp = copied(ep)
        if cp:
            c["score"] = min(c["score"], 5)
            c["weak"] = "नमूने की line उठाई: " + cp[0][:50]
            c["fix"] = "इस खबर के अपने शब्द को पकड़कर बिल्कुल नई मुहर वाली line लिखो, नमूने मत दोहराओ"
        elif c.get("parts", {}).get("E", 1) == 0:
            c["score"] = min(c["score"], 6)
        hard = bookish(ep.get("lines", []))
        if hard:                                            # समझ न आए तो हँसी नहीं — तीखा करने वाले कदम को साफ़ वजह मिले
            c["score"] = min(c["score"], 6)
            c["weak"] = "किताबी शब्द: " + ", ".join(hard) + " — आम आदमी पहली बार सुनकर नहीं समझेगा"
            c["fix"] = "बोलचाल के शब्द (वितरक → एजेंसी वाले/डीलर, द्वारा → ने), और line 2 में साफ़: किसने, किसके साथ, क्या"


class NoViral(RuntimeError):
    """कोई खबर/script viral पैमाने पर पास नहीं हुई."""
    def __init__(self, rejected):
        super().__init__("कोई पास नहीं")
        self.rejected = rejected


# ================================================================ दूसरा format: "दिन भर की खबरें" (bulletin)
def prompt_bulletin_pick(c, n=4):
    return f"""तुम "बकरा न्यूज़" के news editor हो. आज का "दिन भर की खबरें" bulletin बनना है — आज की {n} सबसे बड़ी/चर्चित
**राष्ट्रीय** खबरें, जो पूरे देश के आम भारतीय परिवार के लिए मायने रखें (किसी एक शहर/ज़िले की खबर नहीं, जब तक वो
देशभर में viral न हो). मिलाजुला रखो: 1-2 ज़रूरी खबरें (नियम, दाम, मौसम, परीक्षा, योजना —
इनमें व्यंग्य कम हो तो भी चलेगा) + 2-3 चर्चित/viral खबरें जिन पर व्यंग्य बने. हर खबर अलग विषय से.

आज की खबरें:
{_cands(c)}

{ALLOWED}

सिर्फ़ JSON: {{"picks": [{{"topic": "खबर 8-12 शब्द", "cat": "विषय", "query": "Google News पर खोज (2-5 शब्द, हिंदी)",
  "kind": "zaruri या charcha"}}]}}"""


def prompt_bulletin(items):
    blocks = []
    for i, p in enumerate(items):
        rows = "\n".join(f"   - {h} ({s}, {d})" for h, s, d in p.get("_heads", [])[:8]) or "   (headline नहीं)"
        blocks.append(f"{i + 1}. [{p.get('kind', '')}] {p['topic']}\n{rows}")
    return f"""तुम "बकरा न्यूज़" के anchor बबलू के writer हो — "दिन भर की खबरें" bulletin (30-45 सेकंड, सिर्फ़ बबलू बोलेगा, 3D news
studio से). हर खबर के नीचे Google News की असली headlines हैं — तथ्य सिर्फ़ इन्हीं से, अंक/तारीख़ हूबहू, अपनी तरफ़ से कुछ नहीं:
{chr(10).join(blocks)}

{MUHAR}

हर खबर पर बबलू की 1 line (ज़्यादा से ज़्यादा 18 शब्द): पहला वाक्य तथ्य, दूसरा छोटा व्यंग्य वाला वार (मुहर वाली line जैसा).
दूसरा वाक्य पहले वाक्य के किसी एक शब्द को पकड़कर उलटे और एक बार सुनते ही साफ़ समझ आए — उलझा, आधा या बेतुका नहीं.
सही: "दिवाली सफ़ाई के लिए नहर बंद की गई है। सफ़ाई चालू है, नल बंद।" गलत (मतलब नहीं बनता): "फ़ैसला टला है, नियम नहीं।"
लिखने के बाद हर line ख़ुद से पूछो: "क्या गाँव का आदमी पहली बार सुनकर हँसेगा/समझेगा?" नहीं तो दोबारा लिखो.
"stamp" उसी line के दूसरे वाक्य के शब्दों से बने (जैसे "नल बंद!", "रटने में अव्वल!"); "अनोखा कांड", "कबाड़ पुराण" जैसे
खबर से न जुड़े शब्द नहीं.
"zaruri" खबर में व्यंग्य हल्का रखो (तथ्य साफ़ रहे); "charcha" वाली में तीखा. नेता/पार्टी/धर्म/जाति पर वार नहीं.
सबसे पहले एक intro line (≤ 10 शब्द, जैसे "आज की चार बड़ी खबरें, बकरा अंदाज़ में!") और आख़िर में एक outro line
("कौन-सी खबर सबसे बेतुकी लगी? कमेंट में नंबर लिखो!" जैसी).
हर खबर line में: "headline" (screen पर दिखने वाली 4-8 शब्द की headline, अंक अंकों में), "topic" (ऊपर वाला topic हूबहू),
"visuals" (3 छोटी English खोजें, जैसे "indian traffic police"), "photo_hi" (2 Hindi खबर-खोजें जिनसे अख़बारों में उसी बात की
असली फ़ोटो मिले), "expr" (gambhir/hairan/udaas/hasi), "stamp" (2-3 शब्द का ठप्पा, सिर्फ़ charcha वाली पर).
"say" में अंक शब्दों में, English short form देवनागरी में; "caption" में अंक अंकों में.
सिर्फ़ JSON:
{{"title": "दिन भर की खबरें", "hook": "≤ 6 शब्द", "ask": "कौन-सी खबर सबसे बेतुकी लगी?",
  "intro": {{"say": "...", "caption": "..."}},
  "items": [{{"headline": "...", "topic": "...", "say": "...", "caption": "...", "expr": "gambhir", "visuals": ["..", "..", ".."],
             "photo_hi": ["..", ".."], "stamp": ""}}],
  "outro": {{"say": "...", "caption": "..."}},
  "caption_post": "एक तीखी लाइन + 'आज की खबरें' + स्रोत + 4-5 hashtags + (AI से बने किरदार)"}}"""


def write_bulletin(c, n=4):
    """दिन की 4 खबरें → talk_episode वाला episode (सिर्फ़ बबलू, studio, हर खबर की अपनी headline और फ़ोटो)."""
    import viral_check as vc
    picks = gemini.json_from(gemini.ask(prompt_bulletin_pick(_safe(c), n + 2), json_mode=True, temperature=0.4)).get("picks", [])
    for p in picks:
        sc, why, heads = vc.trend(p.get("query") or p["topic"])
        p["trend"], p["_heads"] = sc, heads
        print(f"  trend {sc}/10: {p['topic']}")
    picks = [p for p in picks if p["_heads"]]
    picks.sort(key=lambda p: -p["trend"])
    items, cats = [], set()
    for p in picks:
        if p.get("cat") not in cats:
            cats.add(p.get("cat"))
            items.append(p)
        if len(items) >= n:
            break
    if not items:
        raise SystemExit("bulletin के लिए खबर नहीं मिली")
    raw = gemini.json_from(gemini.ask(prompt_bulletin(items), json_mode=True, temperature=0.7))
    lines = []
    intro = raw.get("intro") or {}
    if intro.get("say"):
        lines.append({"who": "bablu", "set": "studio", "expr": "hasi", "say": intro["say"],
                      "caption": intro.get("caption") or intro["say"], "headline": "आज की बड़ी खबरें"})
    its = raw.get("items") or []
    for k, it in enumerate(its):
        if not str(it.get("say", "")).strip():
            continue
        ln = {"who": "bablu", "set": "studio", "say": it["say"], "caption": it.get("caption") or it["say"],
              "expr": it.get("expr") if it.get("expr") in EXPRS else "gambhir",
              "headline": str(it.get("headline") or "")[:60], "topic": it.get("topic") or items[min(k, len(items) - 1)]["topic"],
              "visuals": [str(v) for v in it.get("visuals") or []][:3], "photo_hi": [str(v) for v in it.get("photo_hi") or []][:2],
              "item": k + 1, "items_total": len(its)}
        st = str(it.get("stamp") or "")[:22]
        import visuals as _v
        if st and _v._stems(st) & _v._stems(it["say"]):        # ठप्पा उसी line की बात से — वरना नहीं
            ln["stamp"], ln["punch"] = st, True
        lines.append(ln)
    outro = raw.get("outro") or {}
    if outro.get("say"):
        lines.append({"who": "bablu", "set": "studio", "expr": "hasi", "say": outro["say"],
                      "caption": outro.get("caption") or outro["say"]})
    ep = {"title": raw.get("title") or "दिन भर की खबरें", "breaking": "दिन भर की खबरें • बकरा अंदाज़ में",
          "hook": raw.get("hook") or "आज की बड़ी खबरें!", "ask": str(raw.get("ask") or "")[:60],
          "bulletin": True, "lines": lines, "caption_post": raw.get("caption_post", ""),
          "ticker": [i.get("headline", "") for i in its if i.get("headline")][:4],
          "poll": None, "category": "bulletin", "topic": "दिन भर की खबरें: " + " | ".join(p["topic"] for p in items)}
    return ep
