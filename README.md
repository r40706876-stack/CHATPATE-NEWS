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
Feed में कोई viral line/meme दिखे तो `topics.txt` में एक लाइन लिख दो — अगला reel उसी पर बनेगा.

## ध्यान रखना
- हर post पर Instagram का **AI label** लगाओ.
- Script Telegram पर पहले देख लेना; खबर का तथ्य गलत लगे तो post मत करना.
