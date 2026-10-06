import os
from google import genai

print("🚀 CHATPATE-NEWS Scraper Start हो रहा है...")

# 1. API Key Setup
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ Error: GEMINI_API_KEY नहीं मिली! GitHub Secrets चेक करें।")
    exit(1)

# 2. Client सेटअप
client = genai.Client(api_key=api_key)
print("✅ Client Set Up Successfully!")

# 3. न्यूज़ कंटेंट
scraped_news = "आज की बड़ी खबर: भारत ने एक शानदार क्रिकेट मैच जीत लिया है। टीम इंडिया के बल्लेबाजों ने कमाल का प्रदर्शन किया।"
prompt = f"इस न्यूज़ को शॉर्ट और चटपटे (मजेदार) अंदाज़ में हिंदी में लिखो:\n\n{scraped_news}"

print("\n🔍 Google सर्वर से एक्टिव मॉडल्स की लाइव लिस्ट निकाल रहा हूँ...")

try:
    # 4. बिना कोई नाम लिखे, गूगल से सीधे सारे ज़िंदा (Active) मॉडल्स की लिस्ट माँगना
    live_models = []
    for m in client.models.list():
        # हम सिर्फ 'gemini' वाले मॉडल फिल्टर कर रहे हैं
        if 'gemini' in m.name.lower():
            # नाम में से 'models/' हटाकर साफ़ नाम लिस्ट में डाल रहे हैं
            clean_name = m.name.replace('models/', '')
            live_models.append(clean_name)
            
    print(f"✅ Google ने {len(live_models)} एक्टिव मॉडल्स दिए हैं!")
    
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
        
        print(f"✅ Success! '{model_name}' ने काम कर दिया! 🎉\n")
        print("=" * 40)
        print(response.text)
        print("=" * 40)
        
        success = True
        break  # जैसे ही पहला एक्टिव मॉडल न्यूज़ बना दे, कोड को यहीं रोक दो
        
    except Exception as e:
        # अगर ये मॉडल बिजी हुआ या फेल हुआ, तो अगले पर चला जाएगा
        print(f"⚠️ '{model_name}' बिजी है या फेल हो गया। Error: {e}")
        print("➡️ अगले एक्टिव मॉडल पर जा रहा हूँ...")

if not success:
    print("\n❌ Google के सारे मॉडल्स इस वक्त बिजी हैं।")
