# बकरा न्यूज़ 🐐📺 — automatic comedy reels

**Format (final):** असली ट्रेंडिंग खबर + Instagram का ट्रेंड → बबलू बकरा reporter आम लोगों (चाचा भैंसा, पिंकी बिल्ली,
video call पर 3D दादी) से पूछता है → वो उसे घर की ज़िंदगी से जोड़कर मज़ेदार जवाब देते हैं → comment वाला सवाल.

## रोज़ अपने-आप कैसे चलता है
1. `topics.py` — Google Trends India की खबरें (safety filter के साथ) + Instagram trends
   (`topics.txt` में तुम्हारी लिखी लाइनें, Gemini + Google Search, Reddit r/IndianMeme)
2. `writer.py` — Gemini 2 episodes लिखता है, ख़ुद सबसे मज़ेदार चुनता है → `script_today.json`
3. `tts.py` — हर किरदार की अपनी आवाज़ (Kokoro, free, offline)
4. `render_reel.py` — किरदार, मुँह, captions, BREAKING पट्टी, ticker, दादी की video call → `reel.mp4`
5. `telegram.py` — reel + caption तुम्हारे फ़ोन पर. वहाँ से Instagram में trending audio लगाकर post करो.

एक command: `python run_daily.py`  (बिना Gemini के: `python run_daily.py --script examples_sale.json`)

## GitHub पर लगाना (एक बार)
1. नया **private** repo बनाओ, ये पूरा folder upload करो.
2. Settings → Secrets and variables → Actions → New secret:
   - `GEMINI_API_KEY` — aistudio.google.com → Get API key (free)
   - `TELEGRAM_BOT_TOKEN` — Telegram में @BotFather → /newbot
   - `TELEGRAM_CHAT_ID` — अपने bot को "hi" भेजो, फिर `https://api.telegram.org/bot<TOKEN>/getUpdates` खोलकर `chat.id`
3. Actions → bakra-news → **Run workflow** (पहली बार हाथ से). फिर रोज़ सुबह ~9:15 और शाम ~6:15 अपने-आप.

## Insta trend जोड़ना (सबसे असरदार)
Feed में कोई viral line/meme दिखे तो `topics.txt` में एक लाइन लिख दो — अगला reel उसी पर बनेगा. भाई में पूरी स्क्रिप्ट अपलोड कर दिया पर उस पर वीडियो नहीं बन रहा पहले उस पर बनाओ


## अक्टूबर 2026 का बड़ा सुधार (19 reels के असली Instagram आँकड़ों से)
- **Script (v4)**: पहली line ≤ 10 शब्द का मज़ाक (खबर पढ़ना नहीं) → तथ्य → टकराव + TAG वाली line → बढ़ता बेतुकापन → मुहर →
  callback. 50-70 शब्द (~20 सेकंड). पहले पंच-बैंक (हर खबर पर 6 hooks + 8 पंच), फिर सबसे तेज़ से script. "वीडियो भेजो" बंद.
  नमूने: `episodes/samples_v4.json`. सख़्त जाँच `news_writer.finish()` में.
- **Topic**: आदत/viral trend वाली 80%+; सूखी सरकारी/दाम वाली 6 में ज़्यादा से ज़्यादा 1; राजनीति, हादसा/चोट/डूबना बाहर;
  एक topic 7 दिन में दोबारा नहीं. तुम्हारी अपनी script पर भी Telegram में ⚠️ चेतावनी (लंबा hook, राजनीति, दोहराव).
- **Video**: सबसे दमदार असली तस्वीर पहले सेकंड पर; screen का hook = पहली बोली गई line; reaction वाला ठहराव बंद; headline
  पट्टी बंद (bulletin छोड़कर); आख़िर में poll वाली 2.6 सेकंड की screen हटी; set बात से (नदी पर मंडी नहीं); हीरो-हीरोइन की
  फ़ोटो और "वायरल/रील" जैसे आम शब्दों से गलत मेल वाली फ़ोटो बंद.
- **Bulletin** का रोज़ वाला समय बंद (Run workflow → bulletin से अब भी बन सकता है).

## ध्यान रखना
- हर post पर Instagram का **AI label** लगाओ.
- Script Telegram पर पहले देख लेना; खबर का तथ्य गलत लगे तो post मत करना.
