# बकरा न्यूज़ — जरूरी खबर, साफ जानकारी, स्वाभाविक व्यंग्य

## वर्तमान संपादकीय नीति — 2 नवंबर 2026
- प्राथमिकता: जनहित, लोगों पर असर, तात्कालिकता, उपयोगिता और विश्वसनीय स्रोत।
- विषय: नियम, बैंक/UPI/पेंशन, रोजगार/परीक्षा, सफर, सेवाएं, सुरक्षा, मौसम और सार्वजनिक स्वास्थ्य।
- खबर मजाकिया या वायरल होना जरूरी नहीं। गंभीर खबर भी ली जा सकती है; पीड़ितों पर मजाक नहीं।
- हल्का पंच तभी जब स्वाभाविक हो। हंसी, loop, tag, fixed cast या punch count अनिवार्य नहीं।
- स्क्रिप्ट की कोई तय अवधि, शब्द संख्या, line count या पहली line की शब्द सीमा नहीं। खबर पूरी समझने जितनी लंबाई रखें।
- सही तथ्य, मूल स्रोत, लागू क्षेत्र/तारीख, प्रस्ताव बनाम लागू नियम, अपवाद और स्पष्ट भाषा जरूरी हैं।
- अपने shares/likes को दर्शकों की organic engagement का प्रमाण न मानें। पुराने comedy insights विषय चयन का नियम नहीं हैं।

## वर्तमान production flow
`scheduled_production.py` → `run_daily.do_direct()` → `news_first.collect()` → `news_first.write()` → `talk_episode.py` → Telegram.
`news_first` जरूरी विषयों की RSS खबरें जुटाता है, महत्व से चुनता है, Google Search के साथ तथ्य/स्रोत मांगता है,
स्क्रिप्ट की factual lines को fact IDs से जोड़ता है और स्रोतों से मेल की model review कराता है।
यह automated editorial review है, मानव fact-check या views की गारंटी नहीं। स्रोत न मिले/जाँच असफल हो तो पुराने comedy/demo पर fallback नहीं।
पुराने comedy modules historical/manual उपयोग के लिए रखे हैं; scheduled/default script production उन्हें नहीं बुलाता।

समय: 07:00, 10:00, 13:00, 16:00, 19:00 Asia/Kolkata. तैयार स्क्रिप्ट retry पर reuse होती है।
नई नीति अगली नई script generation पर लागू है; पहले से तैयार/running scripts अपने-आप rewrite नहीं होतीं।
वीडियो: 9:16, पुराने 3D किरदार, SadTalker lipsync, प्रासंगिक visuals और captions, तकनीकी QA और Telegram delivery।
QA में अवधि की रोक/छोटी अवधि का लक्ष्य हटा है; unreadable file और दृश्य/आवाज की जाँच जारी है।

Secrets: GEMINI_API_KEY, GEMINI_API_KEY2, GEMINI_API_KEY3, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID; वैकल्पिक PIXABAY_API_KEY, YT_COOKIES.
Run workflow → bakra-news → direct, या `python scheduled_production.py`.
