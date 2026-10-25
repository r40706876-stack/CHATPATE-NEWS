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
    elif ep.get("format") != "rant" and ep.get("kind") != "punch" and words > 55:
        out.append(f"script लंबी ({words} शब्द, सीमा 55)")
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
    return out
