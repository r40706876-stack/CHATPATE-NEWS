"""दिमाग़ के हिसाब से script (28 Oct 2026, मालिक: "script घिसी-पिटी है… human psychology के हिसाब से काम करो, लक्ष्य 10% skip, 90% retention").

पुराना तरीका: एक ही call में 10 हज़ार अक्षर के नियम → Gemini उन्हें checklist की तरह भरता था → हर script एक जैसी.
नया तरीका — असली comedy writers' room जैसा, 4 छोटे calls (सारी खबरें एक साथ, ताकि कोटा कम लगे):
  1. premise: हर खबर में छिपा सबसे बड़ा विरोधाभास ढूँढो (6 अलग premises), ख़ुद रैंक करो
  2. लिखो: सबसे तगड़े 2 premise पर 2 अलग scripts
  3. दर्शक-जज: 22 साल का कस्बे का लड़का, अँगूठा scroll पर — हर line पर "रुका / हँसा / भागा / भेजेगा"
  4. punch-up: जीती script की सिर्फ़ कमज़ोर lines दोबारा
"""
import json

import gemini

PSYCH = """देखने वाले का दिमाग़ — इन्हीं से हर line तय हो (ये नियम नहीं, वजह हैं):
1. ठहराव (0-1.5 सेकंड): अँगूठा scroll पर है. पहला वाक्य एक खटकने वाला विरोधाभास या अधूरा सवाल खोले, जिसका जवाब दिमाग़
   माँगे ("आज रेल के दो वीडियो वायरल हुए… एक नकली था."). जवाब सबसे आख़िर में — तब तक दिमाग़ रुका रहता है.
   खबर की headline पढ़ना, नमस्कार, "क्या आपके साथ भी…", pun — इन पर अँगूठा चलता रहता है.
2. हर 3-4 सेकंड एक इनाम: नई बात या हँसी. कोई line सिर्फ़ अगली को सेट करने वाली नहीं — इनाम रुका तो दर्शक गया.
3. सीढ़ी: हर पंच पिछले से एक कदम ज़्यादा बेतुका/काला. सबसे बड़ा सबसे आख़िर में. बराबर वज़न के 5 जोक = थकान.
4. पहचान: एक line जिसे सुनकर लगे "अरे ये तो मेरे पापा/फूफा/वो दोस्त है" — ठोस आदत, ठोस चीज़
   (पासबुक के लिए तीन बार लाइन, दाल में इतना पानी कि दाल तैरना सीख गई). यही share करवाती है.
5. ठोस, सामान्य नहीं: ₹, अंक, रोज़ की चीज़ों के नाम, जगह. "परेशानी होती है" पर कोई नहीं हँसता.
6. सुरक्षित उल्लंघन: हँसी सिस्टम/बड़ों की बेतुकी सच्चाई पर; आम आदमी पर नहीं, किसी कमज़ोर पर नहीं.
7. Loop: आख़िरी line पहले वाक्य के किसी शब्द पर लौटे और खुला सवाल बंद करे — reel ख़त्म होते ही शुरू से जुड़ी लगे.
8. deadpan: चेहरा गंभीर, आवाज़ news वाली. मज़ाक समझाओ मत, "हाहा/मज़ेदार बात ये है" नहीं. पंच के बाद सफ़ाई नहीं.
9. बोलचाल: एक line = एक बात, ज़्यादा से ज़्यादा 14 शब्द, चाय की दुकान वाली भाषा. किताबी शब्द (द्वारा, उपभोक्ता, अनिवार्य) नहीं.
10. आँख भी: हर line की तस्वीर अलग ठोस चीज़ दिखाए (एक ही फ़ोटो बार-बार = "same same" लगता है)."""

EXAMPLES = """तरीका दिखाने वाले नमूने (शब्द/पंच कॉपी नहीं — हर खबर के अपने):
[फौजी फर्श पर, AI दुल्हन]
bablu: आज रेलवे के दो वीडियो वायरल हुए. एक नकली था.
bablu: पहले में घूँघट वाली दुल्हन ट्रेन चला रही है. लाखों लोग भावुक.
bablu: दूसरे में ड्यूटी पर लौटता फौजी… बोगी के फर्श पर सो रहा है.
bablu: जाँच हुई. दुल्हन वाला AI निकला… फौजी वाला असली.
chacha: फौजी की ग़लती है बेटा. AI से बनवा लेता, तो सीट भी मिलती, शॉल भी.
bablu: रेलवे ने भरोसा दिलाया है, अगली बार सीट मिलेगी. किस वीडियो में… ये नहीं बताया.
(विरोधाभास: नकली पर हमदर्दी, असली पर चुप्पी. hook का सवाल "कौन-सा नकली?" आख़िर तक खुला. loop: "वीडियो".)

[SBI डेटा लीक]
bablu: SBI ने फिर कहा है — हम कभी आपका डेटा नहीं माँगते.
bablu: माँगने की ज़रूरत भी नहीं. चार हज़ार ग्राहकों का डेटा डार्क वेब पर बिक रहा है.
ramesh: मैं पासबुक अपडेट कराने तीन बार लाइन में लगा. हैकर ने बिना लाइन के करवा ली.
dadi: मैं अपना OTP पोते को नहीं बताती. बैंक ने पूरी दुनिया को बता दिया.
bablu: SBI की अपील है — अपना डेटा किसी को मत दीजिए. जो बचा है.
(पहचान: पासबुक की लाइन, दादी का OTP. आख़िरी शब्द "जो बचा है" सबसे बड़ा वार.)"""


def _ask(prompt, temp):
    return gemini.json_from(gemini.ask(prompt, json_mode=True, temperature=temp))


def prompt_premises(packs):
    return f"""तुम "बकरा न्यूज़" (देसी deadpan व्यंग्य, Instagram reels) के head writer हो. खबरें और पक्के तथ्य:
{json.dumps(packs, ensure_ascii=False, indent=1)}

{PSYCH}

हर खबर के लिए 6 premise लिखो — हर एक अलग ढाँचे का (विरोधाभास, दाम/आकार की टक्कर, सरकारी बयान का उल्टा मतलब,
बड़ी खबर पर छोटा निजी मोड़, जाना-माना ढाँचा ग़लत जगह जैसे documentary/WWE commentary/मौसम समाचार, पहचान वाला किरदार).
premise = खबर में छिपी वो बेतुकी सच्चाई जिस पर गाँव-कस्बे का आदमी पहली बार सुनकर हँसे. ज़बरदस्ती का मज़ाक नहीं —
अगर खबर में आम आदमी से जुड़ी कोई बेतुकी बात नहीं, तो "skip": true.
हर premise को ख़ुद 0-10 दो: हँसी (कितना अनपेक्षित), पहचान (कितने लोग "ये मेरे साथ" कहेंगे), hook (पहला वाक्य कितना खटकता है).
सिर्फ़ JSON: [{{"topic": "...", "skip": false, "premises": [{{"dhaancha": "...", "premise": "...", "hook": "पहला वाक्य",
"payoff": "आख़िरी वार", "pehchaan": "किस जाने-पहचाने इंसान/आदत पर", "hasi": 0, "pehchaan_score": 0, "hook_score": 0}}]}}]"""


def prompt_scripts(chosen, fields, casting):
    return f"""तुम "बकरा न्यूज़" के head writer हो. हर खबर के लिए चुने 2 premise पर 2 अलग scripts लिखो (A और B).
{json.dumps(chosen, ensure_ascii=False, indent=1)}

{PSYCH}

{casting}

{EXAMPLES}

लंबाई: 5-8 lines, कुल 45-90 शब्द. लंबाई पैमाना नहीं — हर line का इनाम पैमाना है. तथ्य सिर्फ़ ऊपर वाले, अंक हूबहू;
कल्पना वाली line कल्पना की तरह (किसी असली नेता/इंसान के मुँह में नकली बात नहीं).
{fields}
सिर्फ़ JSON — हर खबर का [A, B] (episode ढाँचा):
[{{"topic": "...", "versions": [{{"premise": "...", "category": "money/rules/bank/jobs/scheme/tech/travel/civic/other",
  "breaking": "6-9 शब्द सच्ची headline", "hook_screen": "≤ 5 शब्द", "source": "प्रकाशक", "tag_who": "कौन किसे भेजेगा और क्यों",
  "ask": "≤ 9 शब्द comment सवाल", "loop_word": "पहली और आख़िरी line का साझा शब्द",
  "lines": [{{"who": "bablu", "say": "...", "caption": "...", "expr": "gambhir", "set": "studio",
             "visuals": ["...", "...", "..."], "photo_hi": ["...", "..."]}}],
  "caption_post": "पहली line + 'Tag करो उसको जो…' + सवाल + स्रोत + 4-5 hashtags + (AI से बने किरदार)"}}]}}]"""


def prompt_audience(cands):
    slim = [{"id": i, "topic": c["topic"], "lines": [f'{l["who"]}: {l["say"]}' for l in c["ep"]["lines"]]}
            for i, c in enumerate(cands)]
    return f"""तुम 22 साल के हो, कस्बे में रहते हो, Instagram reels तेज़ी से scroll करते हो. तुम्हें मनाना मुश्किल है —
ज़्यादातर reels 2 सेकंड में छोड़ देते हो. हर script को line-by-line ईमानदारी से पढ़ो, जैसे reel चल रही हो.
{json.dumps(slim, ensure_ascii=False, indent=1)}

हर line पर बताओ: "ruka" (रुके रहे?), "hasa" (हँसी आई? 0 / 1 मुस्कान / 2 ज़ोर से), "kyon" (5-8 शब्द).
पहली line पर अगर अँगूठा चलता रहता, तो ruka=false और बाकी पढ़ो ही मत (score कम).
फिर: "share_kisko" (किसे भेजोगे — नाम-रिश्ता, या "किसी को नहीं"), "skip_sec" (किस सेकंड पर जाते, या "पूरा देखा"),
"score" 0-10 (10 = पूरा देखा, दोबारा देखा, भेजा), "kamzor" (सबसे कमज़ोर lines के index, 0 से).
खुद को नरम मत रखो — 7 से ऊपर तभी, जब सच में भेजोगे.
सिर्फ़ JSON: [{{"id": 0, "lines": [{{"ruka": true, "hasa": 1, "kyon": "..."}}], "share_kisko": "...", "skip_sec": "...",
"score": 0, "kamzor": [2, 4]}}]"""


def prompt_punchup(items):
    return f"""तुम "बकरा न्यूज़" के punch-up writer हो. नीचे की scripts में दर्शक ने कुछ lines कमज़ोर बताईं (उसकी वजह साथ है).
सिर्फ़ उन्हीं lines को दोबारा लिखो — तथ्य, किरदार, क्रम वही; बाकी lines जस की तस. हर नई line पिछली से ज़्यादा
ठोस, ज़्यादा अनपेक्षित, और सीढ़ी में सही जगह. loop और आख़िरी वार न टूटे.
{json.dumps(items, ensure_ascii=False, indent=1)}

{PSYCH}

सिर्फ़ JSON: [{{"id": 0, "lines": [पूरी lines की नई list, हर line में वही सारे fields]}}]"""


def write(packs, n, fields, casting):
    """packs = gather() के तथ्य. लौटाता है episodes की list (lines वाले dicts), सबसे ऊँचे दर्शक-नंबर पहले."""
    prem = _ask(prompt_premises(packs), 1.0)
    chosen = []
    for t in prem if isinstance(prem, list) else []:
        if not isinstance(t, dict) or t.get("skip"):
            continue
        ps = sorted(t.get("premises") or [], key=lambda p: -(
            float(p.get("hasi", 0) or 0) + float(p.get("pehchaan_score", 0) or 0) + 1.5 * float(p.get("hook_score", 0) or 0)))
        if ps:
            pk = next((p for p in packs if str(p.get("topic", ""))[:20] in str(t.get("topic", "")) or
                       str(t.get("topic", ""))[:20] in str(p.get("topic", ""))), None)
            chosen.append({"topic": t.get("topic"), "facts": pk or {}, "premises": ps[:2]})
            print(f"  💡 {t.get('topic')}: {ps[0].get('premise', '')[:70]}")
    if not chosen:
        raise RuntimeError("एक भी premise नहीं बना")
    chosen = chosen[:n + 1]
    raw = _ask(prompt_scripts(chosen, fields, casting), 0.9)
    cands = []
    for t in raw if isinstance(raw, list) else []:
        for v in (t.get("versions") or [])[:2]:
            if isinstance(v, dict) and v.get("lines"):
                v["topic"] = t.get("topic")
                cands.append({"topic": t.get("topic"), "ep": v})
    if not cands:
        raise RuntimeError("script नहीं बनी")
    try:
        votes = _ask(prompt_audience(cands), 0.2)
        for vt in votes if isinstance(votes, list) else []:
            i = vt.get("id")
            if isinstance(i, int) and 0 <= i < len(cands):
                cands[i]["vote"] = vt
    except gemini.QuotaOver:
        raise
    except Exception as e:                                  # noqa: BLE001
        print("  दर्शक-जज नहीं चला:", repr(e)[:100])
    best = {}
    for c in cands:                                         # हर खबर का A या B — जिसे दर्शक ने ज़्यादा नंबर दिए
        s = float((c.get("vote") or {}).get("score", 0) or 0)
        if c["topic"] not in best or s > best[c["topic"]][0]:
            best[c["topic"]] = (s, c)
    winners = [c for _, c in sorted(best.values(), key=lambda x: -x[0])][:n]
    weak = [(k, c) for k, c in enumerate(winners) if (c.get("vote") or {}).get("kamzor") and
            float(c["vote"].get("score", 0) or 0) < 9]
    if weak:
        items = [{"id": k, "lines": c["ep"]["lines"], "kamzor": c["vote"]["kamzor"],
                  "darshak": [ln.get("kyon") for ln in c["vote"].get("lines", [])]} for k, c in weak]
        try:
            fixed = _ask(prompt_punchup(items), 0.9)
            for f in fixed if isinstance(fixed, list) else []:
                k = f.get("id")
                if isinstance(k, int) and 0 <= k < len(winners) and isinstance(f.get("lines"), list) and \
                        len(f["lines"]) >= 4:
                    winners[k]["ep"]["lines"] = f["lines"]
                    winners[k]["punched"] = True
                    print(f"  🥊 punch-up: {winners[k]['topic']}")
        except gemini.QuotaOver:
            raise
        except Exception as e:                              # noqa: BLE001
            print("  punch-up नहीं हुआ:", repr(e)[:100])
    out = []
    for c in winners:
        ep, v = c["ep"], c.get("vote") or {}
        ep["connect"] = {"score": v.get("score", "?"), "why": f"भेजेगा: {v.get('share_kisko', '?')} | जाता: {v.get('skip_sec', '?')}",
                         "weak": "", "fix": ""}
        ep["writer"] = "psych" + ("+punchup" if c.get("punched") else "")
        out.append(ep)
        print(f"  👀 दर्शक {v.get('score', '?')}/10 — {c['topic']} | भेजेगा: {v.get('share_kisko', '?')}")
    return out
