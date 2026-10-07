"""
आज के topics → Bakra News का एक episode (script JSON), Gemini से.
CORE: ट्रेंडिंग खबर + Instagram का ट्रेंड पकड़ो, उसे मज़ाकिया तरीके से आम आदमी की ज़िंदगी से जोड़ो.

    python writer.py                 → script_today.json (candidates_today.json से)
"""
import json
import os
import sys
from pathlib import Path

import gemini

ROOT = Path(__file__).parent
WHO = {"bablu", "chacha", "pinky", "dadi", "riya", "bunty"}
SCENE_OF = {"chacha": "chacha", "pinky": "pinky", "dadi": "dadi_call", "riya": "riya_call", "bunty": "bunty_call"}

CAST = """किरदार (स्वभाव कभी मत बदलना):
- bablu: बबलू बकरा, reporter. ज़रूरत से ज़्यादा आत्मविश्वासी, हर खबर "ब्रेकिंग". तकिया-कलाम: "खबर पक्की है, सूत्र मेरे चाचा हैं!" (सूत्र हर बार नया और बेतुका हो सकता है: "सूत्र मेरा कार्ट है").
- chacha: चाचा भैंसा, चाय की दुकान वाले आम आदमी. धीमे, ठंडे दिमाग़ वाले, हर खबर को घर के खर्च/महँगाई/रोज़ की आदत से जोड़कर एक लाइन में पलट देते हैं. "हमें क्या, चाय पियो।"
- pinky: पिंकी बिल्ली, Gen Z, Free Wi-Fi zone में. Instagram की भाषा, तीखा roast, viral lines इस्तेमाल करती है. "Literally scam है ये!"
- dadi: 3D दादी, घर से video call पर (नेटवर्क कमज़ोर). चालाक, घर की असली समस्या पकड़ती हैं, सबसे बड़ा punch अक्सर उन्हीं का.
- riya: 3D रिया (20), कॉलेज से video call पर. fact-checker, सपाट चेहरा, कम शब्दों में सीधा निशाना.
- bunty: 3D बंटी (26), अपने "स्टार्टअप ऑफ़िस" से video call. हर trend में नया startup (सब फ़ेल), English buzzwords गलत जगह, ओवर-कॉन्फ़िडेंट.
  (video call वाला मेहमान हर episode में एक ही: ज़्यादातर dadi; topic के हिसाब से कभी riya या bunty)"""

RULES = """नियम:
1. CORE: trend को आम आदमी की रोज़ की ज़िंदगी से जोड़ो — घर का बजट, खाना, चार्जर, WiFi, मम्मी, शादी, रिश्तेदार, बिजली बिल, EMI.
2. Instagram trend: अगर कोई Insta trend/viral line दी है जो खबर से जुड़ सके, तो उसे episode में ज़रूर पिरोओ (ज़्यादातर पिंकी के मुँह से, या दादी का ट्विस्ट). Viral line वैसी ही रखो जैसी लोग बोलते हैं ताकि पहचान में आए. अगर कोई अच्छी खबर नहीं है, तो सीधे Insta trend पर episode बनाओ ("Viral:" वाली breaking).
3. हर punchline अपने-आप में समझ आए — दर्शक को पहले से कुछ पता न हो तो भी. पहले setup, फिर उलटा twist. छोटे, बोलचाल वाले वाक्य.
4. खबर का तथ्य headline से बिल्कुल मेल खाए ("सकता है" को "हो गया" मत बनाओ). मज़ाक काल्पनिक, खबर नहीं.
5. मनाही: हादसा, अपराध, राजनीति/नेता, धर्म, जाति, किसी असली इंसान या क्षेत्र का मज़ाक, शरीर, मर्द/औरत पर तंज़. मज़ाक हालात पर.
6. ढाँचा (7-8 lines, बोलने में 30-40 सेकंड):
   bablu studio (खबर + बेतुका सूत्र) → bablu chacha से सवाल → chacha punch → bablu pinky से सवाल → pinky बड़ा punch
   → [वैकल्पिक: bablu video call पर एक मेहमान बुलाता है (dadi_call / riya_call / bunty_call) → वो सबसे बड़ा punch] → bablu studio_end (एक लाइन का निचोड़ + comment वाला सवाल).
7. scene: bablu की पहली line "studio", आख़िरी "studio_end"; interview में bablu उसी guest के scene में ("chacha"/"pinky"/"dadi_call"/"riya_call"/"bunty_call").
8. "say": बोलने वाला text, अंक शब्दों में (तीस हज़ार), English शब्द देवनागरी में (कार्ट, सेल). "caption": वही बात, अंक अंकों में (₹30,000), English शब्द चाहें तो Roman में.
9. punch वाली lines पर "punch": true. dadi/riya/bunty की line पर "expr": happy/shock/angry/smug/sad में से एक.
10. "breaking": ऊपर की पट्टी, 6-9 शब्द, सच्ची खबर. "icons": studio screen के 3 छोटे शब्द/चिह्न (जैसे ["SALE","₹","%"]). "ticker": 4 हिस्से "   •   " से जुड़े, 1-2 असली, बाक़ी मज़ाकिया.
11. "caption_post": Instagram caption — मज़ेदार लाइन + सवाल (tag/comment) + असली खबर का source + 4-5 hashtags + आख़िर में "(AI से बने किरदार)"."""


def examples():
    out = []
    for f in ("examples_da.json", "examples_sale.json"):
        p = ROOT / f
        if p.exists():
            j = json.load(open(p, encoding="utf-8"))
            out.append(json.dumps({k: j[k] for k in ("breaking", "lines") if k in j}, ensure_ascii=False))
    return "\n\n".join(out)


def build_prompt(c):
    news = "\n".join(f"- {n['trend']}: " + " | ".join(n["headlines"]) for n in c.get("news", [])) or "(कोई नहीं)"
    insta = "\n".join(f"- {i['trend']}" + (f" — {i.get('what', '')}" if i.get("what") else "")
                      + (f" (line: {i['line']})" if i.get("line") else "")
                      + (" [मेरी feed से, पहले इसे देखो]" if i.get("priority") else "")
                      for i in c.get("insta", [])) or "(कोई नहीं)"
    return f"""तुम "बकरा न्यूज़" नाम के Hindi comedy Instagram page के head writer हो — नकली न्यूज़ चैनल जहाँ असली ट्रेंडिंग खबर पर
reporter आम लोगों से राय लेता है और वो उसे अपनी घर की ज़िंदगी से जोड़कर मज़ेदार जवाब देते हैं.

आज की ट्रेंडिंग खबरें (Google Trends India):
{news}

आज Instagram/social पर viral:
{insta}

{CAST}

{RULES}

पहले के दो अच्छे episodes (इनका अंदाज़ और लंबाई पकड़ो, बात नई लिखो):
{examples()}

काम: सबसे मज़ेदार और सबसे relatable topic चुनो (खबर + Insta trend साथ आ सकें तो सबसे अच्छा). 2 अलग episodes लिखो,
फिर ख़ुद सख़्त comedy editor बनकर जाँचो कि किस में punchlines ज़्यादा अपने-आप समझ आती हैं और ज़्यादा हँसी है; उसका index "best" में दो.
सिर्फ़ JSON:
{{"episodes": [{{"topic": "...", "news_used": "...", "insta_used": "Insta trend का नाम, ऊपर की list से हूबहू copy", "source_headline": "...", "breaking": "...", "icons": ["..","..",".."],
  "ticker": "...", "lines": [{{"who": "bablu", "scene": "studio", "say": "...", "caption": "..."}}], "caption_post": "..."}}], "best": 0}}"""


def clean(ep):
    lines = ep["lines"]
    assert 5 <= len(lines) <= 10, f"lines: {len(lines)}"
    for i, ln in enumerate(lines):
        assert ln["who"] in WHO, ln["who"]
        assert ln.get("say") and ln.get("caption")
        if ln["who"] != "bablu":
            ln["scene"] = SCENE_OF[ln["who"]]
        elif ln.get("scene") not in {"studio", "studio_end", "chacha", "pinky", "dadi_call", "riya_call", "bunty_call"}:
            ln["scene"] = "studio"
        if ln["who"] in ("dadi", "riya", "bunty") and ln.get("expr") not in {"neutral", "happy", "shock", "angry", "smug", "sad"}:
            ln["expr"] = "happy"
        ln["punch"] = bool(ln.get("punch"))
    lines[0]["scene"] = "studio"
    lines[-1]["scene"] = "studio_end"
    for i, ln in enumerate(lines[1:-1], 1):                 # bablu का सवाल अगले guest के scene में
        if ln["who"] == "bablu" and i + 1 < len(lines) and lines[i + 1]["who"] != "bablu":
            ln["scene"] = SCENE_OF[lines[i + 1]["who"]]
    icons = (ep.get("icons") or ["₹", "NEWS", "%"])[:3]
    ep["icons"] = (icons + ["₹", "%", "!"])[:3]
    ep.setdefault("ticker", ep["breaking"])
    return ep


def write(c, out="script_today.json"):
    prompt = build_prompt(c)
    if not os.getenv("GEMINI_API_KEY"):
        print(prompt + "\n\n(GEMINI_API_KEY नहीं — ऊपर का prompt Gemini app में चलाकर JSON script_today.json में रख सकते हो)")
        return None
    last = None
    for _ in range(3):
        try:
            data = gemini.json_from(gemini.ask(prompt, json_mode=True, temperature=1.0))
            eps = [clean(e) for e in data["episodes"]]
            ep = eps[int(data.get("best", 0)) % len(eps)]
            json.dump(data, open(ROOT / "episodes_today.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            json.dump(ep, open(ROOT / out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            print(f"  topic: {ep.get('topic')} | Insta: {ep.get('insta_used')}")
            return ROOT / out
        except Exception as e:                              # noqa: BLE001
            last = e
    raise SystemExit(f"script नहीं बनी: {last}")


if __name__ == "__main__":
    write(json.load(open(ROOT / (sys.argv[1] if len(sys.argv) > 1 else "candidates_today.json"), encoding="utf-8")))
