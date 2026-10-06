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

# 3. न्यूज़ कंटेंट (यहाँ तुम्हारी स्क्रैप की हुई न्यूज़ आएगी)
scraped_news = "आज की बड़ी खबर: भारत ने एक शानदार क्रिकेट मैच जीत लिया है। टीम इंडिया के बल्लेबाजों ने कमाल का प्रदर्शन किया।"
prompt = f"इस न्यूज़ को शॉर्ट और चटपटे (मजेदार) अंदाज़ में हिंदी में लिखो:\n\n{scraped_news}"

# 4. तुम्हारे आईडिया के हिसाब से मॉडल्स की लिस्ट (Fallback Mechanism)
models_to_try = [
    'gemini-2.5-flash',
    'gemini-2.0-flash',
    'gemini-1.5-flash',
    'gemini-1.5-flash-8b',
    'gemini-1.5-pro',
    'gemini-pro'
]

success = False

# 5. एक-एक करके मॉडल ट्राई करने का लूप
print("\n🔍 एक्टिव मॉडल ढूँढना शुरू कर रहा हूँ...\n")

for model_name in models_to_try:
    print(f"🔄 ट्राई कर रहा हूँ: {model_name}...")
    
    try:
        response = client.models.generate_content(
            model=model_name, 
            contents=prompt
        )
        
        print(f"✅ Success! '{model_name}' ने काम कर दिया!\n")
        print("=" * 40)
        print(response.text)
        print("=" * 40)
        
        success = True
        break  # जैसे ही पहला मॉडल काम कर जाए, लूप को यहीं रोक दो
        
    except Exception as e:
        # अगर मॉडल फेल या बिजी हुआ, तो क्रैश नहीं होगा, बल्कि अगला ट्राई करेगा
        print(f"⚠️ '{model_name}' फेल हो गया। Error: {e}")
        print("➡️ अगले मॉडल पर जा रहा हूँ...\n")

# अगर लिस्ट के सारे मॉडल्स फेल हो जाएं (जो कि लगभग नामुमकिन है)
if not success:
    print("❌ सारे मॉडल्स बिजी हैं या कोई और बड़ी दिक्कत है।")
