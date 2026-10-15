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

ALLOWED = """सिर्फ़ ऐसी खबरें जो सीधे आम परिवार की ज़िंदगी पर असर डालें और जिनमें "कागज़ पर बनाम ज़मीन पर" वाला फ़ासला हो:
पैसा/दाम (गैस, पेट्रोल, सब्ज़ी, रिचार्ज, बिजली बिल), नए नियम (बैंक, UPI, आधार, राशन, टैक्स, ट्रेन टिकट), सरकारी योजना,
नौकरी/भर्ती/परीक्षा/पेपर लीक, बिजली-पानी-सड़क-अस्पताल जैसी रोज़ की परेशानी, ठगी/साइबर फ़्रॉड से बचाव, त्योहार की भीड़/किराया.
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

इनमें से {n} अलग-अलग खबरें चुनो (अलग विषय: जैसे एक पैसा, एक नियम/योजना, एक सिस्टम की परेशानी). वही लो जिसमें
व्यंग्य का साफ़ मौका हो — दावा बनाम हकीकत, बेतुका नियम, लंबा इंतज़ार, महँगाई. हर एक के लिए Google News पर
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

CASTING = """किरदार — सिर्फ़ वही लो जिसकी इस खबर में ज़रूरत हो (bablu हमेशा; बाकी में से 1-2, कुल ज़्यादा से ज़्यादा 3):
- bablu: आज का तेज़ गाँव संवाददाता/anchor. तथ्य बताता है, छोटे सवाल पूछता है, बिल्कुल गंभीर चेहरे से तंज़ (तरीका 1, 2).
- ramesh: 29 साल का परेशान नौजवान — नौकरी, परीक्षा, दफ़्तर के चक्कर, सिस्टम की परेशानी पर सच्ची भड़ास (तरीका 3).
- chacha: पुरानी सोच वाले चाचा — महँगाई, "हमारे ज़माने में", सबसे गहरा/काला तंज़ (तरीका 4).
- dadi: उम्र ज़्यादा, सोच नई — ठगी से बचाव, योजना, सेहत, असली काम की सलाह, प्यार से पर तीखी (तरीका 5).
- pinky: अभी-अभी 18 की — फ़ोन, ऑनलाइन, पढ़ाई, सपने बनाम हकीकत, लड़कियों से जुड़ी बात.
मिसाल: पेपर लीक = bablu+ramesh+chacha. UPI ठगी = bablu+dadi+pinky. गैस/सब्ज़ी महँगी = bablu+chacha. बिजली/सड़क = bablu+ramesh+dadi."""


def prompt_write(packs):
    return f"""तुम "बकरा न्यूज़" के head writer हो ("खबर सौ टका पक्की, अंदाज़ अधपका!"). तथ्य (सिर्फ़ इन्हीं से, कुछ जोड़ना नहीं):
{json.dumps(packs, ensure_ascii=False, indent=1)}

{SATIRE}

{CASTING}

हर खबर का ढाँचा (30-40 सेकंड, 7-10 lines, कुल 70-120 शब्द, हर line ≤ 20 शब्द):
1. पहली line = सबसे तीखी बात (सवाल-जवाब या बेतुका सच), ≤ 12 शब्द, "नमस्कार" नहीं. यही "hook_text" भी (3-7 शब्द).
2. bablu असली तथ्य बताए (अंक/तारीख़ हूबहू) — ज़रूरी हो तो "card" (tag ≤ 4 शब्द, big ≤ 5 शब्द, sub एक छोटी लाइन, icon).
3. 2-3 punch lines (अलग किरदारों के), "punch": true. punch के बाद 1 सेकंड का reaction: "react_pose" =
   laugh (ठहाका) / facepalm (माथा पकड़ना) / eyeroll (आँखें घुमाना) / thinking (सोचना) — जो उस बात पर स्वाभाविक हो.
4. मौका हो तो एक "विभाग/अधिकारियों ने कहा है…" वाली गंभीर line जो ख़ुद punch बन जाए.
5. एक काम की बात (सिर्फ़ तथ्यों में हो तो).
6. आख़िरी line: "ये वीडियो उसको भेजो, जो…" — किसी ख़ास, पहचाने जाने वाले इंसान का चुटीला चित्रण.
हर line में: "expr" (भाव: hasi / tanz / gussa / hairan / udaas), "set" (bablu के तथ्य/anchor वाले = "studio";
सवाल-जवाब, भड़ास, गाँव की बात = "village"), "visuals" = 2 English खोज (Pixabay पर उस बात को ठोस दिखाने वाली, जैसे
["gas cylinder kitchen", "lpg delivery india"]).
"ticker" = नीचे चलने वाली पट्टी के 3 छोटे जोक (हर एक ≤ 10 शब्द, इसी खबर पर, सरकारी-खबर वाली भाषा में:
"विभाग ने कहा, धैर्य ही असली योजना है").
"say" में अंक शब्दों में ("एक अक्टूबर") और English short form देवनागरी में ("यूपीआई"); "caption" में अंक अंकों में.

हमारे पसंदीदा नमूने (अंदाज़ ऐसा ही — शब्द मत दोहराना):
{gold_satire()}

सिर्फ़ JSON — हर खबर का एक episode:
[{{"topic": "...", "category": "money/rules/bank/jobs/scheme/tech/travel/civic/other", "breaking": "6-9 शब्द, सच्ची headline",
  "hook_text": "...", "source": "प्रकाशकों के नाम", "poll": ["2-4 शब्द", "2-4 शब्द"], "ticker": ["...", "...", "..."],
  "cast_why": "इन किरदारों को क्यों चुना, एक लाइन",
  "lines": [{{"who": "bablu", "say": "...", "caption": "...", "expr": "tanz", "set": "studio", "visuals": ["...", "..."],
              "card": {{"tag": "...", "big": "...", "sub": "...", "icon": "rupee"}}}},
            {{"who": "ramesh", "say": "...", "caption": "...", "expr": "udaas", "set": "village", "visuals": ["...", "..."],
              "punch": true, "react_pose": "facepalm"}}],
  "caption_post": "एक तीखी लाइन + poll वाला सवाल + 'Family group में भेजो' + स्रोत: ... + 4-5 hashtags + (AI से बने किरदार)"}}]
icon इनमें से: {", ".join(sorted(ICONS))}."""


def prompt_sharpen(eps):
    """जज की बताई कमी दूर करो — तथ्य वही, सिर्फ़ व्यंग्य/hook/punch तीखे."""
    slim = [{"n": i + 1, "weak": (e.get("connect") or {}).get("weak", ""), "fix": (e.get("connect") or {}).get("fix", ""),
             "episode": e} for i, e in enumerate(eps)]
    return f"""तुम "बकरा न्यूज़" के comedy editor हो. इन scripts को जज ने कम नंबर दिए; उसकी बताई कमी ("weak") और सुझाव ("fix")
के हिसाब से दोबारा लिखो:
{json.dumps(slim, ensure_ascii=False, indent=1)}

{SATIRE}
नियम: तथ्य, अंक, तारीख़, card, स्रोत बिल्कुल वही. कोई नया तथ्य नहीं. वही किरदार. JSON का ढाँचा वही (सारे fields रखो).
सिर्फ़ JSON list लौटाओ — उतने ही episodes, उसी क्रम में."""


EXPRS, POSES, SETS_OK = {"hasi", "tanz", "gussa", "hairan", "udaas"}, {"laugh", "facepalm", "eyeroll", "thinking"}, {"studio", "village"}


def finish(ep, strict=True):
    """नए व्यंग्य वाले episode को पक्का करो. strict=False: लंबाई की सख़्ती ढीली (कुछ भी न बने, उससे अच्छा)."""
    ep["format"], ep["label"] = "explain", "काम की खबर"
    ep.setdefault("key_word", "")
    ep.setdefault("icons", ["₹", "NEWS", "%"])
    ep["source"] = ep.get("source") or "Google News"
    ep["ticker"] = [str(t)[:80] for t in (ep.get("ticker") or [])][:4]
    ep["lines"] = [l for l in ep["lines"] if l.get("who") in writer.WHO and str(l.get("say", "")).strip()]
    for ln in ep["lines"]:
        cap = str(ln.get("caption") or "")
        if len(re.findall(r"[\u0900-\u097F]", cap)) < len(re.findall(r"[A-Za-z]", cap)) or len(cap) < 4:
            ln["caption"] = ln["say"]
        vis = [str(v) for v in (ln.get("visuals") or []) if str(v).strip()][:2]
        ln["visuals"] = vis
        if vis and not ln.get("visual"):
            ln["visual"] = vis[0]                           # पुराने renderer के लिए
        ln["expr"] = ln.get("expr") if ln.get("expr") in EXPRS else "tanz"
        ln["set"] = ln.get("set") if ln.get("set") in SETS_OK else ("studio" if ln["who"] == "bablu" else "village")
        if ln.get("react_pose") not in POSES:
            ln.pop("react_pose", None)
        c = ln.get("card")
        if c:
            if not c.get("big"):
                ln.pop("card")
                continue
            c["icon"] = c.get("icon") if c.get("icon") in ICONS else "check"
            c["big"], c["tag"], c["sub"] = str(c["big"])[:40], str(c.get("tag", ""))[:28], str(c.get("sub", ""))[:70]
    if len(ep["lines"]) > 10:
        ep["lines"] = ep["lines"][:9] + ep["lines"][-1:]
    ep = writer.clean(ep, strict=False)
    words = sum(len(l["say"].split()) for l in ep["lines"])
    cast = {l["who"] for l in ep["lines"]}
    if strict:
        assert words <= 140, f"बहुत लंबा: {words} शब्द"
        assert len(cast) <= 4, f"किरदार बहुत: {cast}"
        assert not re.match(r"\s*नमस्कार", ep["lines"][0]["say"]), "नमस्कार से शुरुआत"
    return ep


def write_options(c, n=3):
    import viral_check as vc
    picks = gemini.json_from(gemini.ask(prompt_pick(c, n * 2), json_mode=True, temperature=0.4)).get("picks", [])
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
    picks = ok[:n]
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
    weak = [e for e in eps if (e.get("connect") or {}).get("score", 10) < vc.CONNECT_MIN]
    if weak:                                                # कमज़ोर scripts एक बार और तीखी करो, फिर दोबारा जाँचो
        try:
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
    if not good:
        raise NoViral(c["rejected"])
    return good


class NoViral(RuntimeError):
    """कोई खबर/script viral पैमाने पर पास नहीं हुई."""
    def __init__(self, rejected):
        super().__init__("कोई पास नहीं")
        self.rejected = rejected
