import os
from google import genai

print("🚀 CHATPATE-NEWS Viral Script Generator Start हो रहा है...")

# 1. API Key Setup
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ Error: GEMINI_API_KEY नहीं मिली! GitHub Secrets चेक करें।")
    exit(1)

# 2. Client सेटअप
client = genai.Client(api_key=api_key)
print("✅ Client Set Up Successfully!")

# 3. न्यूज़ कंटेंट (यहाँ तुम्हारी असली न्यूज़ आएगी)
# अभी टेस्टिंग के लिए मैंने एक थोड़ी 'ड्रामा' वाली न्यूज़ डाली है
scraped_news = "गौतम गंभीर ने प्रेस कॉन्फ्रेंस में विराट कोहली के आलोचकों को करारा जवाब दिया और कहा कि पहले उनके जितने रन बनाकर दिखाओ।"

# 4. 🔥 PRO-LEVEL PROMPT (यही सारा जादू करेगा) 🔥
prompt = f"""तुम एक बहुत ही फेमस और वायरल 'इंस्टाग्राम रील्स' क्रिएटर हो, जो बोरिंग न्यूज़ को एकदम देसी, मीम-मटेरियल और चटपटी स्क्रिप्ट में बदल देता है।
तुम्हारी ऑडियंस 15 से 35 साल के युवा हैं, जिन्हें सस्पेंस, कॉमेडी और रोस्टिंग पसंद है।

नीचे दी गई न्यूज़ के आधार पर एक 30-40 सेकंड की वायरल रील स्क्रिप्ट तैयार करो। 
मुझे आउटपुट बिल्कुल इसी स्ट्रक्चर में चाहिए (हिंदी में):

🔥 1. Viral Hook (0-3 Sec): वीडियो शुरू होते ही वो कौन सी सस्पेंस वाली या भड़काऊ लाइन बोलनी है जिससे लोग वीडियो में रुक जाएं।
🎬 2. Visual & Meme Idea: बैकग्राउंड में कैसी वीडियो क्लिप लगानी है? और किस डायलॉग पर कौन सा फेमस मीम (जैसे- हेरा फेरी, पंचायत, मिर्ज़ापुर, या कोई फनी रिएक्शन) लगाना सही रहेगा?
🗣️ 3. Voiceover Script (वॉयसओवर): बोलने के लिए एकदम देसी, फनी और कनेक्टिंग स्क्रिप्ट। (4-5 लाइनें, जिसमें बीच-बीच में मज़ाक भी हो)।
💬 4. On-Screen Text: वीडियो के बीच में स्क्रीन पर क्या बड़े-बड़े पॉप-अप टेक्स्ट (कैप्शन) आने चाहिए?

न्यूज़ कंटेंट यहाँ है: {scraped_news}"""

print("\n🔍 Google से एक्टिव मॉडल ढूँढ रहा हूँ...")

try:
    live_models = []
    for m in client.models.list():
        if 'gemini' in m.name.lower():
            clean_name = m.name.replace('models/', '')
            live_models.append(clean_name)
except Exception as e:
    print(f"❌ मॉडल्स लिस्ट निकालने में दिक्कत: {e}")
    exit(1)

success = False

# 5. लाइव लिस्ट में से एक-एक करके ट्राई करना
for model_name in live_models:
    print(f"\n🔄 ट्राई कर रहा हूँ: {model_name}...")
    
    try:
        response = client.models.generate_content(
            model=model_name, 
            contents=prompt
        )
        
        print(f"✅ Success! '{model_name}' ने स्क्रिप्ट बना दी! 🎉\n")
        print("=" * 50)
        print(response.text)
        print("=" * 50)
        
        success = True
        break 
        
    except Exception as e:
        print(f"⚠️ '{model_name}' फेल हो गया। Error: {e}")

if not success:
    print("\n❌ Google के सारे मॉडल्स इस वक्त बिजी हैं।")
