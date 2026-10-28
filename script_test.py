"""नया script तरीका आज़माओ: आज की खबरें → psych_writer → Telegram पर सिर्फ़ पढ़ने के लिए (video/चुनाव नहीं)."""
import json

import news_writer as nw
import run_daily
import telegram
import topics

news = topics.collect_news(None)
c = nw._safe(news)
packs, picks = nw.gather(c, 4)
eps = nw._write_psych(c, packs, picks, 4)
json.dump(eps, open("script_test.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
telegram.send_text("🧪 नया script तरीका (दिमाग़ के हिसाब से) — सिर्फ़ पढ़ने के लिए, इन पर नंबर मत भेजना.\n"
                   "हर script पर बताओ: कहाँ हँसे, कहाँ बोर हुए.")
txt = run_daily.preview(eps)
txt = txt[:txt.rfind("\n👉 जो पसंद")] if "👉 जो पसंद" in txt else txt   # यहाँ नंबर भेजने से video नहीं बनता
telegram.send_text(txt.replace("आज की", "🧪 TEST —") + "\n\n🧪 ये सिर्फ़ जाँच हैं — नंबर मत भेजना.")
