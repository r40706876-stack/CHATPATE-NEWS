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

ALLOWED = """कौन-सी खबर लें: वो जिस पर आज लोग WhatsApp/Instagram/चाय की दुकान पर बात कर रहे हों — थोड़ी viral, थोड़ी बेतुकी,
जिसमें हर आम आदमी जुड़ जाए और व्यंग्य अपने-आप निकले ("कागज़ पर बनाम ज़मीन पर", "नियम बनाम हकीकत", "दावा बनाम सच").
जैसे: अजीब सरकारी आदेश/जुर्माना, गड्ढों वाली सड़क पर भारी चालान, पेपर लीक/परीक्षा टली, ट्रेन-बस-flight की अफ़रा-तफ़री,
दाम में अचानक उछाल (प्याज़, टमाटर, गैस, रिचार्ज), बिजली-पानी कटौती, viral हुआ सरकारी दफ़्तर/अस्पताल का हाल, ठगी का नया तरीका,
नया नियम जिससे सब परेशान, त्योहार की भीड़/किराया, AI/फ़ोन/internet वाली चर्चित बात, मौसम की मार (बिना मौत/हादसे).
सूखी "योजना की जानकारी" वाली खबर तभी, जब उसमें कोई बेतुका पेच हो.
**राष्ट्रीय खबर पहले**: पूरे देश के लोगों पर असर वाली — केंद्र सरकार/RBI/रेलवे/UPI/आधार/टैक्स के नियम, देशभर के दाम,
राष्ट्रीय भर्ती-परीक्षा (SSC, रेलवे, NEET, UPSC), देशभर में viral बात. किसी एक शहर/ज़िले/मोहल्ले की खबर (जैसे "कानपुर की
सड़क", "पटना का सेंटर", "किसी नगर निगम का आदेश") नहीं — सिर्फ़ तब, जब वो पूरे देश में viral हो और हर जगह के लोग जुड़ें.
कभी नहीं: मौत, हादसा, हत्या/दंगा, युद्ध, किसी नेता/पार्टी/असली व्यक्ति का नाम या बयान, धर्म, जाति, celebrity gossip,
बीमारी का डर."""


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

इनमें से {n} अलग-अलग खबरें चुनो. सबसे पहले ये पूछो: "क्या आम आदमी इस पर आज बात कर रहा है, और सुनते ही बोलेगा —
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


GOLD_SATIRE = ROOT / "episodes/samples_dark.json"     # मालिक को पसंद आया अंदाज़ (बिजली वाली सबसे ऊपर)


def gold_satire():
    try:
        eps = json.load(open(GOLD_SATIRE, encoding="utf-8"))
    except Exception:                                       # noqa: BLE001
        return ""
    eps = sorted(eps, key=lambda e: 0 if "बिजली" in e.get("topic", "") else 1)
    return "\n\n".join(f"[{e['topic']}]\n" + "\n".join(f"  {l['who']}: {l['say']}" for l in e["lines"]) for e in eps)


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

MUHAR = """सबसे बड़ा हथियार — "मुहर वाली line" (मालिक को यही सबसे ज़्यादा पसंद है — जितना हो सके इसी का इस्तेमाल: हर script में कम से कम 3, बेहतर 4;
script का ज़्यादातर मज़ा इन्हीं से आए. ज़्यादातर bablu के मुँह से, बिल्कुल गंभीर anchor की आवाज़ में; कभी-कभी चाचा/दादी भी
इसी ढाँचे में बोल सकते हैं):
  ढाँचा: [पहला वाक्य: सरकारी/विशेषज्ञ/विभाग वाली सीधी, भरोसे वाली बात] + [दूसरा छोटा वाक्य: उसी बात के एक शब्द को पकड़कर
  उलट देना, जो ज़मीनी सच्चाई खोल दे]. दूसरा वाक्य 4-8 शब्द का, आख़िरी शब्द पर वार.
  असली नमूने (इसी स्तर के नए बनाओ, इन्हें दोहराओ मत):
""" + "\n".join(f"   • {l}" for l in GOLD_LINES) + """
  इनमें खेल ये है: "धैर्य" → "धैर्य की आयु सीमा नहीं"; "सेहत बनती है" → "ख़रीदने से नहीं"; "योजना नहीं" → "बिना योजना के";
  "OTP नहीं माँगते" → "बाकी सब माँगते हैं". यानी सरकारी शब्द को उसी के ख़िलाफ़ खड़ा कर दो. ऐसी line के बाद
  "react_pose": "eyeroll"."""

SATIRE = """अंदाज़ (सबसे ज़रूरी): गंभीर news channel जैसा चेहरा, बात बेतुकी सच्चाई की — Prakash Bharati जैसा dark व्यंग्य, पर
हमारे गाँव-कस्बे की ज़बान में. हर खबर में "कागज़/सरकार/विभाग क्या कहता है" बनाम "ज़मीन पर क्या होता है" का फ़ासला ढूँढो और
उसी पर वार करो. इन 5 तरीकों से (हर script में कम से कम 3):
 1. सरकारी भाषा, बेतुका सच: "कटौती की कोई योजना नहीं है। कटौती बिना योजना के हो रही है।"
 2. बात को उसके बेतुके अंजाम तक: "अगली परीक्षा पूरी सुरक्षा में होगी। तारीख़ जल्द ही… लीक की जाएगी।"
 3. छोटा सवाल, 2-4 शब्द का जवाब, punch जवाब में: "परीक्षा कितनी बार हुई?" — "हुई तीन बार। लीक चार बार।"
 4. पहले बनाम अब: "पहले बिजली नहीं थी, तो बिल भी नहीं था। अब तरक्की हुई है, बिल आ गया है।"
 5. काम की बात, तीखे अंदाज़ में: "ठगी हो जाए तो रोना बाद में, पहले एक नौ तीन शून्य पे फ़ोन।"
मना (ऐसा लिखा तो script रद्द): "मतलब… जैसे फूफा/मंदिर की चप्पल" वाली ज़बरदस्ती की तुलना, "हाहा", "नमस्कार, आज हम बात करेंगे",
हर line में देसी शब्द ठूँसना (पूरी script में भइया/लल्ला/गज़ब जैसे 1-2 बस), किसी असली इंसान/नेता/पार्टी/धर्म/जाति पर वार,
मौत/हादसे पर मज़ाक, झूठा तथ्य."""

CASTING = """किरदार — सबकी 3D फ़ोटो तैयार हैं: bablu हमेशा + ज़रूरत हो तो 1-2 और (कुल ज़्यादा से ज़्यादा 3):
- bablu: आज का तेज़ गाँव संवाददाता/anchor. तथ्य बताता है, छोटे सवाल पूछता है, बिल्कुल गंभीर चेहरे से तंज़ (तरीका 1, 2).
- ramesh: 29 साल का परेशान नौजवान — नौकरी, परीक्षा, दफ़्तर के चक्कर, चालान, सिस्टम की परेशानी पर सच्ची भड़ास (तरीका 3).
- chacha: पुरानी सोच वाले चाचा — महँगाई, "हमारे ज़माने में", सबसे गहरा/काला तंज़ (तरीका 4).
- dadi: उम्र ज़्यादा, सोच नई — ठगी से बचाव, योजना, सेहत, घर का बजट, असली काम की सलाह; प्यार से पर तीखी (तरीका 5).
- pinky: अभी-अभी 18 की — फ़ोन, ऑनलाइन, पढ़ाई, सपने बनाम हकीकत, लड़कियों से जुड़ी बात.
मिसाल: पेपर लीक/भर्ती = bablu+ramesh. UPI ठगी = bablu+dadi+pinky. गैस/सब्ज़ी महँगी = bablu+chacha. चालान/सड़क = bablu+ramesh+chacha."""


def prompt_write(packs):
    return f"""तुम "बकरा न्यूज़" के head writer हो ("खबर सौ टका पक्की, अंदाज़ अधपका!"). तथ्य (सिर्फ़ इन्हीं से, कुछ जोड़ना नहीं):
{json.dumps(packs, ensure_ascii=False, indent=1)}

{MUHAR}

{SATIRE}

{CASTING}

हर खबर का ढाँचा — **पूरी script "मुहर वाली lines" से बनी** (मालिक का हुक्म: पूरी script ऐसी ही हो). Reels पर लोग
तेज़ी से आगे बढ़ते हैं, इसलिए छोटी और कसी हुई: 20-28 सेकंड, सिर्फ़ 5-6 lines, कुल 55-85 शब्द; bablu के साथ कम से कम
1 और किरदार (एक ही आवाज़ लगातार उबाऊ लगती है). नमूनों वाली lines हूबहू या थोड़ा बदलकर लिखीं तो script रद्द — हर मुहर
line इसी खबर के अपने शब्द (जैसे इस खबर का "पोर्टल", "अनुदान", "KYC") को पकड़कर नई बनाओ.
1. पहली line = hook: सबसे तीखी मुहर वाली line (≤ 16 शब्द), "नमस्कार" नहीं. उसका छोटा रूप "hook_text" (3-7 शब्द).
2. असली तथ्य भी मुहर के पहले वाक्य में ही आएँ: "[तथ्य, अंक/तारीख़ हूबहू]। [उसी का उलटा]" — जैसे
   "गोरखपुर में गोभी सौ रुपये किलो पहुँच गई है। अब गोभी सब्ज़ी नहीं, संपत्ति है।" ज़रूरत हो तो उसी line पर "card".
3. बाकी हर line भी इसी ढाँचे में — हर line अलग शब्द/अलग पहलू उलटे (एक ही चाल दोहराओ मत). ज़्यादातर bablu; बीच में
   1-2 lines दूसरे किरदार अपनी नज़र से उसी ढाँचे में ("कहते हैं मेहनत का फल मीठा होता है। हमारा फल अभी… परीक्षा की तारीख़
   पर लटका है।"). हर line "punch": true; आँख घुमाने/ठहाके वाला "react_pose" सिर्फ़ 2-3 सबसे तेज़ lines पर.
4. "जानकारी वाली" line (पोर्टल पर देखें, यहाँ आवेदन करें) मत लिखो — ये reel है, सूचना-पत्र नहीं. हर line व्यंग्य वाली.
   हर line ज़्यादा से ज़्यादा 16 शब्द (बोलने में 4-5 सेकंड). मज़ाक थोड़ा कम हो चलेगा, व्यंग्य हर line में चाहिए.
5. आख़िरी line: "ये वीडियो उसको भेजो, जो…" — इसी खबर से जुड़ा, पहचाने जाने वाला इंसान (विषय से भटको मत), और हो
   सके तो पहली line के शब्द पर लौटो ताकि video घूमकर शुरुआत से जुड़े (लोग दोबारा देखें).
"ask" = बीच में comment बटोरने वाला छोटा सवाल (≤ 9 शब्द), जिसका जवाब हर कोई अपने अनुभव से दे सके — जैसे
"आपकी कौन-सी परीक्षा सबसे ज़्यादा बार टली?", "आपके गाँव में बिजली कितने घंटे आती है?".
हर line में: "expr" (भाव: gambhir / hasi / tanz / gussa / hairan / udaas — मुहर वाली line पर ज़्यादातर "gambhir":
बिल्कुल गंभीर anchor चेहरा, सीधा कैमरे में; मज़ा बात में हो, चेहरे में नहीं), "set" (पीछे की जगह, बात के हिसाब से: bablu के तथ्य/anchor वाले = "studio"; दफ़्तर/फ़ॉर्म/भर्ती/परीक्षा/बैंक के चक्कर =
"office"; चालान/गड्ढे/ट्रैफिक/पेट्रोल/सड़क = "road"; महँगाई/सब्ज़ी/दाम/बाज़ार = "mandi"; घर/ठगी से बचाव/योजना/बिजली-पानी/
रसोई = "aangan"; फ़ोन/online/पढ़ाई/सोशल मीडिया (ज़्यादातर पिंकी) = "room"; LPG/गैस/पेट्रोल के दाम = "gas"; रसोई का बजट/खाना = "kitchen";
ट्रेन/किराया/भीड़/सफ़र = "station"; अस्पताल/दवा/इलाज = "hospital"; किसान/खाद/फ़सल/मौसम = "khet";
स्कूल/परीक्षा केंद्र/पेपर लीक/रिज़ल्ट = "school"; थाना/शिकायत/साइबर ठगी की रिपोर्ट = "thana"; बैंक/ATM/UPI/लोन = "bank";
बिजली कटौती/बिल/ट्रांसफ़ॉर्मर = "bijli"; राशन/गेहूँ-चावल/राशन कार्ड = "ration"; गाँव/बाकी आम बात = "village"), "visuals" = 3 अलग English खोज जो उस line की बात को screen पर ठोस, असली
तस्वीर में दिखाएँ (बड़ी screen पर चलेंगी, सबसे ज़रूरी हिस्सा): चीज़/जगह/काम का नाम लो, भाव नहीं — जैसे
["lpg gas cylinder", "woman cooking gas stove india", "gas cylinder delivery truck"]; परीक्षा = ["students writing exam hall",
"exam result notice board", "calendar pages"]. "sad", "problem", "system" जैसे खोखले शब्द नहीं.
"photo_hi" = 2 Hindi खबर-खोजें (2-4 शब्द) जिनसे अख़बारों में उसी बात की असली फ़ोटो मिले — जगह/चीज़ का नाम ("बिहार सड़क गड्ढा",
"ट्रैफिक पुलिस चालान मशीन", "छत्तीसगढ़ परीक्षा केंद्र").
"react_pose" (line के ठीक बाद 1 सेकंड का reaction) line के मतलब से ही चुनो:
  eyeroll = सरकारी दावा और सच्चाई उलटी ("कोई कमी नहीं है" वाली lines); facepalm = हद दर्जे की बेवकूफ़ी/बार-बार वही गलती;
  laugh = सच इतना बेतुका कि हँसी छूट जाए; thinking = सवाल छोड़ने वाली line; smug = "समझ गए न?" वाला तंज़.
  जिस line पर react_pose हो, उसी पर "stamp" = 2-4 शब्द का ठप्पा जो उसी line की बात पकड़े (जैसे "धैर्य… उम्र भर!",
  "दिखती ही नहीं!", "OTP छोड़ के सब!"). "गज़ब!", "बवाल!" जैसे हर जगह चलने वाले शब्द नहीं.
"ticker" = नीचे चलने वाली पट्टी के 3 छोटे जोक (हर एक ≤ 10 शब्द, इसी खबर पर, सरकारी-खबर वाली भाषा में:
"विभाग ने कहा, धैर्य ही असली योजना है").
"say" में अंक शब्दों में ("एक अक्टूबर") और English short form देवनागरी में ("यूपीआई"); "caption" में अंक अंकों में.

हमारे पसंदीदा नमूने (अंदाज़ ऐसा ही — शब्द मत दोहराना):
{gold_satire()}

सिर्फ़ JSON — हर खबर का एक episode:
[{{"topic": "...", "category": "money/rules/bank/jobs/scheme/tech/travel/civic/other", "breaking": "6-9 शब्द, सच्ची headline",
  "hook_text": "...", "ask": "...", "source": "प्रकाशकों के नाम", "poll": ["2-4 शब्द", "2-4 शब्द"], "ticker": ["...", "...", "..."],
  "cast_why": "इन किरदारों को क्यों चुना, एक लाइन",
  "lines": [{{"who": "bablu", "say": "...", "caption": "...", "expr": "gambhir", "set": "studio", "visuals": ["...", "...", "..."], "photo_hi": ["...", "..."],
              "card": {{"tag": "...", "big": "...", "sub": "...", "icon": "rupee"}}}},
            {{"who": "ramesh", "say": "...", "caption": "...", "expr": "udaas", "set": "village", "visuals": ["...", "...", "..."],
              "punch": true, "react_pose": "facepalm", "stamp": "2-4 शब्द"}}],
  "caption_post": "एक तीखी लाइन + poll वाला सवाल + 'Family group में भेजो' + स्रोत: ... + 4-5 hashtags + (AI से बने किरदार)"}}]
icon इनमें से: {", ".join(sorted(ICONS))}."""


def prompt_sharpen(eps):
    """जज की बताई कमी दूर करो — तथ्य वही, सिर्फ़ व्यंग्य/hook/punch तीखे."""
    slim = [{"n": i + 1, "weak": (e.get("connect") or {}).get("weak", ""), "fix": (e.get("connect") or {}).get("fix", ""),
             "episode": e} for i, e in enumerate(eps)]
    return f"""तुम "बकरा न्यूज़" के comedy editor हो. इन scripts को जज ने कम नंबर दिए; उसकी बताई कमी ("weak") और सुझाव ("fix")
के हिसाब से दोबारा लिखो:
{json.dumps(slim, ensure_ascii=False, indent=1)}

{MUHAR}

{SATIRE}
नियम: तथ्य, अंक, तारीख़, card, स्रोत बिल्कुल वही. कोई नया तथ्य नहीं. वही किरदार. JSON का ढाँचा वही (सारे fields रखो).
सिर्फ़ JSON list लौटाओ — उतने ही episodes, उसी क्रम में."""


EXPRS, POSES, SETS_OK = {"gambhir", "hasi", "tanz", "gussa", "hairan", "udaas"}, {"laugh", "facepalm", "eyeroll", "thinking", "smug"}, {"studio", "village", "office", "road", "mandi", "aangan", "room", "gas", "kitchen", "station", "hospital", "khet", "school", "thana", "bank", "bijli", "ration"}


def finish(ep, strict=True):
    """नए व्यंग्य वाले episode को पक्का करो. strict=False: लंबाई की सख़्ती ढीली (कुछ भी न बने, उससे अच्छा)."""
    ep["format"], ep["label"] = "explain", "काम की खबर"
    ep.setdefault("key_word", "")
    ep.setdefault("icons", ["₹", "NEWS", "%"])
    ep["source"] = ep.get("source") or "Google News"
    ep["ticker"] = [str(t)[:80] for t in (ep.get("ticker") or [])][:4]
    ep["ask"] = str(ep.get("ask") or "")[:60]
    ep["hook"] = ep.get("hook") or ep.get("hook_text") or ""
    ep["lines"] = [l for l in ep["lines"] if l.get("who") in writer.WHO and str(l.get("say", "")).strip()]
    for ln in ep["lines"]:
        cap = str(ln.get("caption") or "")
        if len(re.findall(r"[\u0900-\u097F]", cap)) < len(re.findall(r"[A-Za-z]", cap)) or len(cap) < 4:
            ln["caption"] = ln["say"]
        vis = [str(v) for v in (ln.get("visuals") or []) if str(v).strip()][:3]
        ln["visuals"] = vis
        if vis and not ln.get("visual"):
            ln["visual"] = vis[0]                           # पुराने renderer के लिए
        ln["expr"] = ln.get("expr") if ln.get("expr") in EXPRS else "gambhir"
        ln["set"] = ln.get("set") if ln.get("set") in SETS_OK else ("studio" if ln["who"] == "bablu" else "village")
        if ln.get("react_pose") not in POSES:
            ln.pop("react_pose", None)
            ln.pop("stamp", None)
        elif ln.get("stamp"):
            ln["stamp"] = str(ln["stamp"])[:22]
        c = ln.get("card")
        if c:
            if not c.get("big"):
                ln.pop("card")
                continue
            c["icon"] = c.get("icon") if c.get("icon") in ICONS else "check"
            c["big"], c["tag"], c["sub"] = str(c["big"])[:40], str(c.get("tag", ""))[:28], str(c.get("sub", ""))[:70]
    if len(ep["lines"]) > 6:                                # reel 20-28 सेकंड: ज़्यादा से ज़्यादा 6 lines
        ep["lines"] = ep["lines"][:5] + ep["lines"][-1:]
    ep = writer.clean(ep, strict=False)
    words = sum(len(l["say"].split()) for l in ep["lines"])
    cast = {l["who"] for l in ep["lines"]}
    if strict:
        assert words <= 140, f"बहुत लंबा: {words} शब्द"
        assert len(cast) <= 4, f"किरदार बहुत: {cast}"
        assert not re.match(r"\s*नमस्कार", ep["lines"][0]["say"]), "नमस्कार से शुरुआत"
    return ep


RISKY = re.compile(r"हत्या|मर्डर|रेप|दुष्कर्म|बलात्कार|यौन|आत्महत्या|सुसाइड|लाश|शव|मौत|मारे गए|हमला|आतंक|गोली|"
                   r"murder|rape|suicide|killed|dead|terror|sex", re.I)


def _safe(c):
    """Gemini का safety filter पूरा prompt रोक दे तो: अपराध/मौत वाली खबरें हटाकर (वैसे भी हम उन पर व्यंग्य नहीं करते)."""
    c2 = dict(c)
    for k in ("kaam", "viral", "news", "moments", "insta"):
        c2[k] = [it for it in c.get(k, []) if not RISKY.search(json.dumps(it, ensure_ascii=False))]
    return c2


def write_options(c, n=3):
    import viral_check as vc
    try:
        raw = gemini.ask(prompt_pick(c, min(n * 2 + 3, 15)), json_mode=True, temperature=0.4)
    except gemini.QuotaOver:
        raise
    except RuntimeError as e:
        print("  खबरों की list Gemini ने नहीं ली, अपराध/मौत वाली हटाकर दोबारा:", repr(e)[:150])
        c = _safe(c)
        raw = gemini.ask(prompt_pick(c, min(n * 2 + 3, 15)), json_mode=True, temperature=0.4)
    picks = gemini.json_from(raw).get("picks", [])
    for p in picks:                                         # पहली जाँच: खबर सच में आज उठी हुई है? (free, Gemini नहीं)
        sc, why, heads = vc.trend(p.get("query") or p["topic"])
        p["trend"], p["_heads"] = {"score": sc, "why": why}, heads
        print(f"  {'✅' if sc >= vc.TREND_MIN else '❌'} trend {sc}/10: {p.get('topic')} | {why}")
    recent = set(c.get("recent_cats", []))
    picks.sort(key=lambda p: (str(p.get("cat", "")) in recent, -p["trend"]["score"]))   # नए विषय पहले
    c["rejected"] = [p for p in picks if p["trend"]["score"] < vc.TREND_MIN]
    ok, cats = [], set()
    for p in picks:                                         # एक विषय से एक ही खबर
        cat = str(p.get("cat") or p.get("topic"))
        if p["trend"]["score"] >= vc.TREND_MIN and cat not in cats:
            ok.append(p)
            cats.add(cat)
    for p in picks:                                         # कम पड़ें तो: थोड़ी कम चर्चित पर असली खबरें (2+ अख़बार) से 3 पूरे
        cat = str(p.get("cat") or p.get("topic"))
        if len(ok) >= n + 1:
            break
        if p not in ok and p["trend"]["score"] >= 2 and p.get("_heads") and cat not in cats:
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
    raw = gemini.json_from(gemini.ask(prompt_write(packs), json_mode=True, temperature=0.8))
    raw = [r for r in raw if isinstance(r, dict) and r.get("lines")]
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
    for ep in eps:                                          # हर script पर उसकी खबर का trend नंबर
        w = set(str(ep.get("topic", "")).split())
        best = max(picks, key=lambda p: len(w & set(str(p.get("topic", "")).split())))
        ep["trend"] = best["trend"]
        ep["category"] = best.get("cat") or ep.get("category", "other")
    vc.connect(eps)                                         # दूसरी जाँच: लोग जुड़ेंगे? (Gemini 1 call)
    penalize(eps)
    weak = [e for e in eps if (e.get("connect") or {}).get("score", 10) < vc.CONNECT_MIN]
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
        rest = sorted([e for e in eps if e not in good], key=lambda e: -(e.get("connect") or {}).get("score", 0))
        good = good + rest[:n - len(good)]
        print("  कोई 7+ नहीं — फिर भी सबसे अच्छी", len(good), "भेज रहे (नंबर साफ़ दिखेंगे)")
    if not good:
        raise NoViral(c["rejected"])
    return good


def copied(ep):
    """नमूनों (GOLD_LINES) से हूबहू/थोड़ा बदलकर उठाई lines."""
    import difflib
    out = []
    for ln in ep.get("lines", []):
        for g in GOLD_LINES:
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
