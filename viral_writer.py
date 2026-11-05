"""
"वायरल + मज़ाक" format (5 Nov 2026) — हमारे page के असली आँकड़ों से:
  13-20 Oct वाली reels (लहंगा return 2,693 · साड़ी रील 1,725 · रामलीला डांस 1,289 · गरबा बारात 1,157 · free hit 1,244)
  सब उस चीज़ पर थीं जो लोग Instagram पर पहले से देख रहे थे + हमारी रोज़ की आदत/सिस्टम पर मज़ाक. 35 shares.
  सरकारी/पैसे वाली खबरें (DA, गोभी, APK, RBI, Jio) हर format में 50-77% skip.
  बड़े channels (Neeraj Badhwar 0.7-3M, India Daily 4.6M, Priyanka 3.8M) से: पहले second में उल्टा headline + असली clip,
  हर 4-5 सेकंड एक तथ्य + deadpan twist, आख़िर में सबसे बड़ा पंच + सवाल.
Gemini calls: 3 (चुनो → तथ्य के साथ लिखो → जाँचकर कसो).
"""
import json
import re

import gemini

WINNERS = """हमारे page की असली जीतने वाली scripts (इसी स्तर और ढाँचे में लिखो, शब्द मत दोहराओ):
[लहंगा return — 2,693 views, 7 shares]
 bablu: गरबा ख़त्म होते ही महंगे लहंगे वापस लौटने लगे हैं। नाचना दो दिन था, फ़्री ट्रायल सात दिन का।
 pinky: त्योहार पर महंगे कपड़े ख़रीदना परंपरा है। फ़ोटो खिंचवाकर तुरंत लौटा देना आधुनिक परंपरा है।
 bablu: कंपनियों ने कहा रिटर्न पॉलिसी सुविधा के लिए है। ग्राहकों ने सुविधा को ही मुफ़्त की अलमारी बना दिया।
[साड़ी रील — 1,725 views, 10 shares]
 pinky: मैंने पूरी रात चमकदार साड़ी पहनकर दस रील बना लीं। सुबह लिख दूँगी… कि कपड़े का रंग पसंद नहीं आया।
 bablu: अब कंपनियाँ सूँघकर कपड़ा वापस लेंगी। यानी आपकी ईमानदारी का फ़ैसला… अब आपके कपड़ों की महक करेगी।

बड़े channel का ढाँचा (Neeraj Badhwar, 3.2M views) — नाकामी की "तारीफ़", चेहरा बिल्कुल गंभीर:
 headline: "क्यों भारत घूमने आना चाहती है पूरी दुनिया?" — screen पर खुले नाले में गिरती महिला.
 "पता चला है कि महिला मोटरसाइकिल पर बैठकर मुँह पर यमुना का झाग खाना चाहती थी।"
 "सरकार ने दुनिया से अपील की है कि भारतीय वीज़ा के लिए यूँ अपनी जान न दें।"

मालिक को पसंद आई lines:
 • "जापान की मंगल की मिट्टी 2031 में आएगी… तब तक हमारी गली की सड़क भी बन जाएगी।"
 • "चौराहों पर कैमरे अपने-आप चालान काटेंगे… गड्ढे फ़िलहाल कैमरे की पकड़ से बाहर हैं।"
 • "धैर्य बनाए रखने को कहा गया है। धैर्य की कोई अधिकतम आयु सीमा नहीं है।"
"""

PICK = """तुम बकरा न्यूज़ (@bakra_news) के संपादक हो। नीचे आज की खबरें हैं। ऐसी 1 खबर चुनो जिस पर reel सबसे ज़्यादा देखी और भेजी जाएगी।

पहली पसंद (हमारे आँकड़े यही कहते हैं): जो चीज़ लोग Instagram/WhatsApp पर पहले से देख रहे हैं — वायरल वीडियो, अजीब घटना,
नया trend, लोगों की आदत (शादी, shopping, त्योहार, ट्रेन/मेट्रो, दफ़्तर, रील का शौक, क्रिकेट/फ़िल्म फ़ैन), जिसका असली video
YouTube/Instagram पर होगा. उसमें हमारी रोज़ की ज़िंदगी/सिस्टम पर मज़ाक की जगह हो.
मत चुनो: सरकारी सूचना/नियम/किस्त/बैंक/दाम वाली खबर (हमारे page पर 50-77% skip), किसी की मौत/चोट/हादसा/अपराध-पीड़ित,
नेता/पार्टी/चुनाव, धर्म/जाति, एक शहर की छोटी खबर जिससे बाकी देश न जुड़े, recent में बनी खबर.

सिर्फ JSON: {"index": 0, "topic": "खबर एक वाक्य में", "category": "वायरल वीडियो/शादी-रिश्ते/…",
"why_people_watch": "लोग इसे पहले से क्यों देख/बात कर रहे हैं", "daily_life_link": "हमारी किस आदत/सिस्टम से जुड़ती है",
"clip_query": "YouTube पर इसी घटना का video ढूँढने की हिंदी खोज (4-7 शब्द)"}"""

WRITE = """तुम बकरा न्यूज़ के लेखक हो। reporter बबलू (गंभीर, deadpan anchor) एक सच्ची वायरल खबर बताता है, पर हर बात में
हमारी रोज़ की ज़िंदगी/सिस्टम का उल्टा सच निकल आता है. Google Search से इस खबर के असली तथ्य जाँचो — खबर पूरी और सही हो,
कोई अंक/नाम/जगह अपनी तरफ़ से मत गढ़ो.

{winners}

ढाँचा (हर नियम ज़रूरी):
1. पहली line (≤12 शब्द): उल्टा headline — घटना को ऐसे बोलो जैसे कोई बड़ी राष्ट्रीय उपलब्धि/गंभीर ब्रेकिंग हो. हाँ/ना सवाल नहीं,
   "नमस्कार/दोस्तों/आपको बता दें" नहीं. सुनते ही अगला सेकंड देखने का मन करे.
2. बीच की 3-5 lines: हर line = खबर का एक असली तथ्य + उसी पर एक छोटा deadpan twist जो हमारी आदत/सिस्टम/पहचाने इंसान
   (चाचा, मम्मी, बॉस, रिश्तेदार, EMI वाला दोस्त) पर लगे. एक ही धागा — हर line पिछली से जुड़ी, खबर पूरी समझ आए.
   एक line में एक ही पंच. आम बोलचाल, देसी शब्द (जुगाड़, मोहल्ला, भैया, टपरी). सरकारी/किताबी शब्द नहीं.
3. आख़िरी line: पूरी reel का सबसे ज़ोरदार पंच — पहली बार सुनने में साफ़, किसी ऐसे इंसान पर जिसे दर्शक तुरंत tag करे.
4. "ask": comment के लिए एक छोटा सवाल (screen पर आख़िर में).
5. कुल 5-7 lines, 70-110 शब्द. ज़्यादातर lines bablu की; chacha (पुरानी सोच, बात को और गहरा ले जाए) या pinky (18 साल,
   नई पीढ़ी) ज़्यादा से ज़्यादा 1-1 line, सिर्फ़ जहाँ टकराव से हँसी बढ़े.
6. पीड़ित पर मज़ाक नहीं; नेता/पार्टी/धर्म नहीं; "वीडियो भेजो/शेयर करो" बोलना नहीं.

हर line में: "who", "say" (बोली जाने वाली), "caption" (वही, छोटा), "expr" (gambhir/tanz/hairan/hasi/gussa/udaas),
"photo_hi": [इस line की बात दिखाने वाली हिंदी खोज], "visuals": [English खोज], "punch": true/false.

खबर: {pick}

सिर्फ JSON (कोई और लिखाई नहीं):
{{"topic": "...", "breaking": "screen headline ≤8 शब्द", "hook_short": "पहले 2 सेकंड का उल्टा headline ≤5 शब्द",
"facts": ["इस खबर के जाँचे तथ्य"], "source": "किस अख़बार/चैनल से", "lines": [...], "ask": "...",
"caption_post": "Instagram caption + 4-5 hashtag"}}"""

JUDGE = """तुम सख़्त comedy editor हो. नीचे की script को इन सवालों पर जाँचो (हर line के लिए):
(1) पहली line सुनकर कोई 3 सेकंड में scroll क्यों नहीं करेगा? (2) पहली हँसी 5 सेकंड के अंदर आई? (3) हर line पिछली से जुड़ी
और खबर पूरी समझ आई? (4) मज़ाक हमारी रोज़ की ज़िंदगी/सिस्टम से जुड़ा या ज़बरदस्ती का? (5) आख़िरी line पहली बार सुनकर साफ़
और सबसे ज़ोरदार है? (6) कोई इसे किसे और क्यों भेजेगा? (7) कोई line किताबी, घिसी (AI जैसी) या समझ से बाहर है?
तथ्य वही रखो (facts में जो है); नया अंक/नाम मत जोड़ो. कमज़ोर lines दोबारा लिखो, ज़रूरत हो तो line हटाओ/जोड़ो (5-7 रहें).
सिर्फ पूरी सुधरी script उसी JSON ढाँचे में लौटाओ, साथ में "judge": {{"weak_before": [...], "share_reason": "..."}}.

{script}"""

BAD_TOPIC = re.compile(r"मौत|मृत|हत्या|हादसा|घायल|डूब|आत्महत्या|रेप|दुष्कर्म|गोली|फायरिंग|फ़ायरिंग|लाश|शव|"
                       r"किस्त|RBI|ब्याज|DA\b|महंगाई भत्ता|पेंशन|नियम लागू", re.I)


def candidates(c):
    """topics.collect_news() से: पहले वायरल/आदत वाली, फिर बाकी (सरकारी/हादसे वाली हटाकर)."""
    import topics
    rows = []
    for v in c.get("viral", []):
        rows.append({"cat": "वायरल", "title": v.get("trend", ""), "more": v.get("headlines", [])[:2]})
    for k in c.get("kaam", []):
        if k.get("cat") in topics.VIRAL_CATS:
            rows.append({"cat": k.get("cat"), "title": k.get("title") or k.get("trend", ""), "more": [k.get("source", "")]})
    for n in c.get("news", []):
        rows.append({"cat": "Google Trends", "title": n.get("trend", ""), "more": n.get("headlines", [])[:2]})
    out, seen = [], set()
    for r in rows:
        t = str(r["title"]).strip()
        if not t or t[:30] in seen or BAD_TOPIC.search(t + " " + " ".join(map(str, r["more"]))):
            continue
        seen.add(t[:30])
        out.append(r)
    return out[:25]


def check(ep):
    """code की सख़्त छलनी — टूटा तो कारण लौटाओ."""
    import bakra_rules
    lines = ep.get("lines") or []
    why = []
    if not 5 <= len(lines) <= 7:
        why.append(f"{len(lines)} lines (5-7 चाहिए)")
    for ln in lines:
        if ln.get("who") not in ("bablu", "chacha", "pinky") or not str(ln.get("say", "")).strip():
            why.append("ग़लत किरदार/ख़ाली line")
            break
    words = sum(len(str(l.get("say", "")).split()) for l in lines)
    if not 55 <= words <= 125:
        why.append(f"{words} शब्द (70-110 चाहिए)")
    others = [l["who"] for l in lines if l.get("who") != "bablu"]
    if any(others.count(w) > 1 for w in set(others)):
        why.append("chacha/pinky की 1 से ज़्यादा line")
    why += [v for v in bakra_rules.violations(dict(ep, format="viral")) if not v.startswith("script लंबी")]
    return why


def write(c, recent=()):
    cands = candidates(c)
    if not cands:
        raise RuntimeError("आज कोई वायरल/आदत वाली खबर नहीं मिली")
    pick = gemini.ask_json(PICK + "\n\nrecent (ये/इनसे मिलती दोबारा नहीं): " + json.dumps(list(recent)[-30:], ensure_ascii=False)
                           + "\n\nखबरें:\n" + json.dumps(cands, ensure_ascii=False), json_mode=True, temperature=0.3)
    if isinstance(pick, list):
        pick = pick[0]
    print("  🎯 चुनी खबर:", pick.get("topic"), "|", pick.get("why_people_watch", "")[:80])
    raw = gemini.ask(WRITE.format(winners=WINNERS, pick=json.dumps(pick, ensure_ascii=False)), search=True, temperature=0.8)
    ep = gemini.json_from(raw)
    ep = gemini.ask_json(JUDGE.format(script=json.dumps(ep, ensure_ascii=False)), json_mode=True, temperature=0.5)
    why = check(ep)
    if why:
        print("  ⚠️ छलनी:", why, "— एक बार सुधरवा रहे")
        ep = gemini.ask_json(JUDGE.format(script=json.dumps(ep, ensure_ascii=False))
                             + "\n\nये नियम टूटे हैं, ठीक करो: " + "; ".join(why), json_mode=True, temperature=0.4)
        why = check(ep)
        if why:
            raise ValueError("वायरल script नियमों पर खरी नहीं: " + "; ".join(why))
    for ln in ep["lines"]:
        ln.setdefault("caption", ln["say"])
        ln["expr"] = ln.get("expr") if ln.get("expr") in ("gambhir", "tanz", "hairan", "hasi", "gussa", "udaas") else "gambhir"
        ln["set"] = "studio" if ln["who"] == "bablu" else "village"
        ln["photo_hi"] = [str(x) for x in (ln.get("photo_hi") or [])][:2]
        ln["visuals"] = [str(x) for x in (ln.get("visuals") or [])][:2]
    if pick.get("clip_query"):
        ep["lines"][0]["photo_hi"] = [pick["clip_query"]] + ep["lines"][0]["photo_hi"][:1]
    ep.update(format="viral", writer="viral", label="अधपकी खबर", layout="anchor", category=pick.get("category", "वायरल"),
              editorial_mode="viral_mazaak", style="flow", lips="sadtalker", renderer="studio", no_memes=True)
    first = ep["lines"][0]["say"]
    ep["hook"] = ep["hook_text"] = first
    ep["hook_short"] = " ".join(str(ep.get("hook_short") or ep.get("breaking") or first).split()[:5])
    if ep.get("source"):
        ep["caption_post"] = str(ep.get("caption_post") or ep["topic"]) + "\nस्रोत: " + str(ep["source"])
    return ep


if __name__ == "__main__":
    import topics
    print(json.dumps(write(topics.collect_news(), [t for _, _, t in topics.history(7)]), ensure_ascii=False, indent=1))
