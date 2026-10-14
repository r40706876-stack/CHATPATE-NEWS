"""viral_check की जाँच: (1) असली trend नंबर आज की खबरों पर  (2) जज अच्छी और कमज़ोर scripts को अलग पहचानता है या नहीं."""
import json
import viral_check as vc

out = []
for q in ["UPI नया नियम", "LPG सिलेंडर दाम", "दिवाली छुट्टी बैंक", "पेपर लीक", "सेंसेक्स", "8वां वेतन आयोग",
          "साइबर ठगी 1930", "प्याज के दाम", "मोबाइल रिचार्ज महंगा", "रेलवे टिकट नियम"]:
    s, why, h = vc.trend(q)
    out.append(f"TREND {s}/10  {q}  | {why}")
out.append("Google Trends आज (पहले 15): " + ", ".join(t for t, _ in vc.google_trends_today()[:15]))

demo = json.load(open("episodes/demo_thagi.json", encoding="utf-8"))
eps = [
    {"topic": "फ़ोन से ठगी हो जाए तो 1930 (अच्छी — interview format)", "hook_text": demo["hook"], "lines": demo["lines"]},
    {"topic": "पेड़ लगाने के लिए पेड़ काटे (अच्छी — भड़ास format, 9.1M वाले जैसी)", "hook_text": "पेड़ लगाने के लिए… पेड़ काट दिए! 🤡",
     "lines": [{"who": "ramesh", "say": "भइया सुनो, दस हज़ार पेड़ लगाने थे, जगह नहीं मिली, तो पुराने पेड़ ही काट दिए!"},
               {"who": "ramesh", "say": "अब फ़ोटो में हरियाली है, और गाँव में धूप। वाह रे जुगाड़!"},
               {"who": "chacha", "say": "हमारे ज़माने में पेड़ छाँव देते थे… अब सिर्फ़ फ़ाइल में खड़े होते हैं।"},
               {"who": "ramesh", "say": "आपके यहाँ भी ऐसा हुआ है? कमेंट में बताओ, और उस अफ़सर को भेजो!"}]},
    {"topic": "सेंसेक्स 500 अंक चढ़ा (कमज़ोर — दूर की बात)", "hook_text": "आज शेयर बाज़ार में तेज़ी",
     "lines": [{"who": "bablu", "say": "नमस्कार, आज हम बात करेंगे शेयर बाज़ार की। सेंसेक्स पाँच सौ अंक चढ़ा।"},
               {"who": "bablu", "say": "आईटी और बैंक शेयरों में खरीदारी देखी गई।"},
               {"who": "chacha", "say": "हाहा, बढ़िया है भाई!"}]},
    {"topic": "एक अभिनेता का बयान (कमज़ोर)", "hook_text": "अभिनेता ने कहा कुछ बड़ा",
     "lines": [{"who": "bablu", "say": "नमस्कार, एक मशहूर अभिनेता ने कहा कि उन्हें चाय पसंद है।"},
               {"who": "pinky", "say": "वाह, कितनी बड़ी खबर है!"}]},
]
vc.connect(eps)
for e in eps:
    c = e.get("connect") or {}
    out.append(f"CONNECT {c.get('score', '?')}/10 {c.get('parts', '')}  {e['topic']}\n   ✅ {c.get('why', '')}\n   ⚠️ {c.get('weak', '')}\n   🔧 {c.get('fix', '')}")
open("viral_test.txt", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
