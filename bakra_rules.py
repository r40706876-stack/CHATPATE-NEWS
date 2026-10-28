"""
मालिक के पक्के नियम (bakra-script skill + अक्टूबर 2026 की बातचीत) — Gemini के prompt में भी, और code की सख़्त छलनी भी.
मालिक: "कल ही बोला था" — prompt में लिखा होने पर भी Gemini ने PM का बयान, "क्या… साज़िश है?" hook, मनगढ़ंत क़िस्से दिए.
"""
import re

POLITICS = re.compile(r"मोदी|पीएम|प्रधानमंत्री|मुख्यमंत्री|मंत्री|सांसद|विधायक|नेता|पार्टी|चुनाव|मतदान|वोट|भाजपा|कांग्रेस|"
                      r"राहुल|योगी|केजरीवाल|सरकार ने|विपक्ष|संसद|राज्यपाल|\bPM\b|\bBJP\b|Congress", re.I)
YESNO_HOOK = re.compile(r"^\s*क्या\b.*\?\s*$|साज़िश|साजिश")

GOLD = """मालिक को जो lines सच में पसंद आईं (इसी स्तर का लिखो, शब्द मत दोहराओ):
 • "जापान की मंगल की मिट्टी 2031 में आएगी… तब तक हमारी गली की सड़क भी बन जाएगी।"
 • बिजली हड़ताल, अँधेरे में: "हालात पर नज़र रखी जा रही है।"
 • "चौराहों पर कैमरे अपने-आप चालान काटेंगे… गड्ढे फ़िलहाल कैमरे की पकड़ से बाहर हैं।"
 • "धैर्य बनाए रखने को कहा गया है। धैर्य की कोई अधिकतम आयु सीमा नहीं है।"
 • चाचा ने बारह शेयर लेकर ख़ुद को "जियो का मालिक" बताना शुरू किया; भारत जीता तो मम्मी: "इतनी टेंशन पढ़ाई में लेता…"
पकड़: पंच हमेशा हमारे सिस्टम (सड़क, बिजली, भर्ती, दफ़्तर, ट्रेन) या किसी पहचाने इंसान (चाचा, मम्मी, बॉस, EMI वाला दोस्त) पर.
मालिक ने ठुकराया (कभी नहीं): हर किरदार का एक pun; "क्या… साज़िश है?" जैसा हाँ/ना सवाल वाला hook; मनगढ़ंत पारिवारिक क़िस्सा
("मम्मी ने पायजेब गिरवी रखी") को सच की तरह बोलना; नेता/PM/पार्टी/चुनाव; छोटी या एक शहर की खबर; खबर में न लिखा अंक/तथ्य."""


def violations(ep):
    """script में मालिक के नियम टूटे? [कारण] — ख़ाली = ठीक."""
    lines = [str(l.get("say", "")) for l in ep.get("lines", [])]
    blob = " ".join([str(ep.get("topic", "")), str(ep.get("breaking", ""))] + lines)
    out = []
    if POLITICS.search(blob):
        out.append("नेता/राजनीति")
    if lines and YESNO_HOOK.search(lines[0]):
        out.append("हाँ/ना सवाल वाला hook")
    if lines and len(lines[0].split()) > 10:
        out.append("hook लंबा (>10 शब्द)")
    # bakra-script skill + retention लक्ष्य: news reel छोटी (~12–18 sec ≈ 55 शब्द तक); बकरा बहस (rant) अलग लंबाई रखती है
    words = sum(len(s.split()) for s in lines)
    if ep.get("kind") == "punch" and words > 24:
        out.append(f"एक पंच लंबा ({words} शब्द, सीमा 24)")
    elif ep.get("format") == "rant" and not (70 <= words <= 100):
        out.append(f"बकरा बहस की लंबाई {words} शब्द (70-100 चाहिए)")
    elif ep.get("format") != "rant" and ep.get("kind") != "punch":
        # Full character-clash episodes need enough dialogue for a coherent
        # setup, escalation and payoff. Keep the shorter 55-word news limit.
        limit = 80 if ep.get("comedy_format") == "character_clash" and 7 <= len(lines) <= 9 else 55
        if words > limit:
            out.append(f"script लंबी ({words} शब्द, सीमा {limit})")
    # News format experiments: preserve the existing formats while validating labels.
    comedy_format = ep.get("comedy_format")
    if comedy_format and comedy_format not in ("news_roast", "character_clash", "reverse_punch"):
        out.append("अनजान comedy_format")
    if lines and re.match(r"^\s*(नमस्कार|आज की खबर|हेलो दोस्तों|दोस्तों)", lines[0], re.I):
        out.append("धीमा introduction hook")
    # पहचान/tag: share की वजह — punch और rant में ख़ाली हो तो रद्द (news में writer पहले से रोकता है)
    if ep.get("kind") in ("punch", "tvshop") or ep.get("format") == "rant":
        if not str(ep.get("tag_who", "")).strip():
            out.append("पहचान (tag) नहीं — share की वजह नहीं")
    # किताबी/सरकारी शब्द (वितरक, उपभोक्ता, द्वारा…) — skill की जाँच
    try:
        import news_writer as _nw
        if lines and _nw.bookish(ep.get("lines", [])):
            out.append("किताबी/सरकारी शब्द")
    except Exception:
        pass

    # Reject news scripts that are just a bulletin plus generic reactions.
    # This is a structural filter, NOT a prediction of audience laughter.
    if ep.get("kind") not in ("punch",) and ep.get("format") != "rant":
        dialogue = [str(l.get("say", "")).strip() for l in ep.get("lines", [])]
        if len(dialogue) >= 4 and sum(bool(l.get("news")) for l in ep.get("lines", [])) >= 3:
            out.append("खबर पढ़ना ज़्यादा, किरदारों का टकराव कम")
    # Financial promises and quoted rates must be fact-checked upstream.
    # A generic disclaimer cannot rescue a misleading financial claim.
    finance = bool(re.search(r"एफडी|फिक्स्ड डिपॉजिट|ब्याज दर|FD\\b", blob, re.I))
    if finance and re.search(r"रातों.?रात अमीर|गारंटी.{0,12}अमीर|पैसा दोगुना.{0,12}गारंटी", blob):
        out.append("वित्तीय कमाई की भ्रामक गारंटी")
    if finance and re.search(r"बजाज.{0,65}(आठ दशमलव पच्चीस|8\\.25)", blob, re.I) and not re.search(r"रिन्यू|renew|नवीनीकरण", blob, re.I):
        out.append("8.25% की रिन्यूअल शर्त गायब")
    # Reject obvious generic filler in character payoffs. Human review is still required.
    weak = ("हमारे ज़माने में", "हमारे जमाने में", "वो दोस्त जो", "फिर क्या हुआ", "देखते रहिए")
    for ln in ep.get("lines", [])[1:]:
        if ln.get("who") in ("chacha", "pinky", "dadi", "ramesh") and any(p in str(ln.get("say", "")) for p in weak):
            out.append("किरदार का कमजोर/घिसा-पिटा डायलॉग")
            break
    # Catch the specific stale Telegram formats: a news-reading hook and a non-joke payoff.
    if ep.get("kind") == "punch" and len(lines) >= 2:
        if re.match(r"^(पीईटी|रेलवे|विभाग|बैंक|आरबीआई).{0,45}(चलाएगा|बढ़ाएगा|होगा|कहा है)", lines[0]):
            out.append("पंच की शुरुआत न्यूज़ बुलेटिन जैसी")
    if ep.get("kind") == "tvshop":
        if len(lines) < 5 or not any(l.get("news") for l in ep.get("lines", [])):
            out.append("नकली ऐड में असली खबर का स्पष्ट मोड़ नहीं")
    return out
