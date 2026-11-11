"""
"किरदार चुटकुला" demo (11 Nov 2026). मालिक: AI आवाज़ + AI किरदार ही रहेंगे.
सबूत (vidIQ, Oct-Nov 2026): Hindi AI-किरदार वाले छोटे pages (1.6K-60K followers) की 0.7M-8M वाली reels में —
  • किरदार पूरी screen पर (news template / किसी और का video नहीं), आवाज़ 0 सेकंड से
  • एक ही चुटकुला: 2 किरदारों की बातचीत या एक की बात, 9-16 सेकंड, आख़िरी शब्द पर पंच
  • विषय: रिश्ते/घर/शादी/ससुराल/पैसा (खबर नहीं); अक्सर आख़िर में हँसी वाला reaction/meme clip
हमारे 43 reels (खबर + template): हर format में 5 सेकंड पर आधे लोग गए — यह उससे अलग ढाँचा है, नतीजा post के graph से ही पता चलेगा.
Gemini calls: 2 (8 चुटकुले लिखो → सबसे अच्छा चुनो).
"""
import json
import time
from pathlib import Path

import gemini

ROOT = Path(__file__).parent
SETS = ["aangan", "village", "room", "kitchen", "khet", "road", "office", "school"]

WRITE = """तुम देसी चुटकुलों के उस्ताद हो. Instagram reel के लिए 8 छोटे चुटकुले लिखो — हर एक 2 किरदारों की बातचीत.
किरदार (इन्हीं में से 2): bablu (25 साल, गाँव का चालू लड़का), chacha (60 साल, पुरानी सोच, ताने मारने वाले), pinky (18 साल, तेज़ ज़बान).

नियम:
- वही चुटकुले जो चौपाल/WhatsApp पर चलते हैं और सुनते ही हँसी आती है — रिश्तेदार, शादी, ससुराल, पढ़ाई-नौकरी, उधार, फ़ोन/रील, कंजूसी,
  पड़ोसी, महँगाई. खबर/नेता/धर्म/जाति नहीं, गंदी बात नहीं.
- ठीक 3 lines: (1) सीधी-सादी बात/सवाल, (2) सामने वाले का जवाब जो उम्मीद बनाए, (3) उल्टा पंच — हँसी आख़िरी 2-3 शब्दों पर.
- हर line ≤ 12 शब्द; कुल 22-34 शब्द (10-13 सेकंड). आम बोलचाल, तुक/देसी शब्द चलेंगे. पंच समझाना नहीं.
- पहली line ऐसी कि सुनते ही आगे सुनने का मन हो ("चाचा, शादी कब करूँ?" जैसा सीधा सवाल).

सिर्फ JSON list: [{"title": "screen का छोटा शीर्षक, ≤4 शब्द", "set": "%s में से एक",
"lines": [{"who": "bablu", "say": "..."}, {"who": "chacha", "say": "..."}, {"who": "bablu", "say": "..."}]}]""" % "/".join(SETS)

PICK = """नीचे 8 चुटकुले हैं. एक आम आदमी की तरह पढ़ो और वो 1 चुनो जिसे सुनकर सच में हँसी आए और जिसे कोई दोस्त/परिवार के group में भेजे.
घिसा-पिटा, समझ से बाहर, या जिसका पंच आख़िरी शब्दों पर न हो — मत चुनो.
सिर्फ JSON: {"index": 0, "why": "एक वाक्य"}

%s"""


def write():
    jokes = gemini.ask_json(WRITE, json_mode=True, temperature=1.0)
    jokes = [j for j in jokes if isinstance(j, dict) and len(j.get("lines") or []) == 3
             and all(l.get("who") in ("bablu", "chacha", "pinky") and str(l.get("say", "")).strip() for l in j["lines"])
             and 16 <= sum(len(l["say"].split()) for l in j["lines"]) <= 40]
    if not jokes:
        raise ValueError("कोई चुटकुला नियमों पर खरा नहीं")
    pick = gemini.ask_json(PICK % json.dumps(jokes, ensure_ascii=False, indent=1), json_mode=True, temperature=0.2)
    i = pick.get("index") if isinstance(pick, dict) else 0
    j = jokes[i if isinstance(i, int) and 0 <= i < len(jokes) else 0]
    print("  😂 चुना:", j.get("title"), "|", (pick or {}).get("why", "") if isinstance(pick, dict) else "")
    place = j.get("set") if j.get("set") in SETS else "aangan"
    lines = []
    for k, l in enumerate(j["lines"]):
        last = k == 2
        lines.append({"who": l["who"], "say": l["say"], "caption": l["say"], "set": place, "shot": "close",
                      "expr": "hasi" if last else ("hairan" if k == 1 else "gambhir"), "punch": last, "visuals": [], "photo_hi": []})
    title = " ".join(str(j.get("title") or "देसी चुटकुला").split()[:4])
    return {"topic": title, "breaking": title, "category": "चुटकुला", "hook": lines[0]["say"], "hook_text": lines[0]["say"],
            "hook_short": title, "lines": lines, "format": "skit", "writer": "skit", "label": "बकरा न्यूज़", "style": "close",
            "editorial_mode": "skit", "no_memes": False, "no_clips": True, "lips": "sadtalker", "renderer": "studio",
            "caption_post": f"{title} 😂\n#bakranews #desicomedy #chutkule #funnyreels #comedy",
            "others": [" / ".join(l["say"] for l in x["lines"]) for x in jokes if x is not j][:7]}


if __name__ == "__main__":
    import run_daily
    ep = run_daily.to_studio(write())
    name = f"episodes/skit_{time.strftime('%Y%m%d_%H%M')}.json"
    (ROOT / name).write_text(json.dumps(ep, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "studio_job.txt").write_text(name, encoding="utf-8")
    print("  चुटकुला video job:", name)
    for l in ep["lines"]:
        print("   ", l["who"], ":", l["say"])
