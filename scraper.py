import os
import google.generativeai as genai

print("🚀 CHATPATE-NEWS Scraper Start हो रहा है...")

# 1. API Key Setup (GitHub Secrets से लेगा)
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ Error: GEMINI_API_KEY नहीं मिली! कृपया GitHub Secrets चेक करें।")
    exit(1)

genai.configure(api_key=api_key)

# 2. फिक्स मॉडल सेट कर रहे हैं (ताकि 0 लिमिट वाले पर न जाए)
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("✅ Success! 'gemini-1.5-flash' मॉडल लोड हो गया है।")
except Exception as e:
    print(f"❌ Model load error: {e}")
    exit(1)

# 3. न्यूज़ कंटेंट (यहाँ भविष्य में तुम अपना असली स्क्रैपिंग कोड लगा सकते हो)
# अभी चेक करने के लिए यह डमी न्यूज़ है:
scraped_news = "आज की बड़ी खबर: भारत ने एक शानदार क्रिकेट मैच जीत लिया है। टीम इंडिया के बल्लेबाजों ने कमाल का प्रदर्शन किया।"

print("✍️ 'gemini-1.5-flash' से न्यूज़ की स्क्रिप्ट लिखवा रहा हूँ...")

# 4. जेमिनी से स्क्रिप्ट बनवाना
try:
    prompt = f"इस न्यूज़ को शॉर्ट और चटपटे (मजेदार) अंदाज़ में हिंदी में लिखो:\n\n{scraped_news}"
    
    response = model.generate_content(prompt)
    
    print("\n✅ Script Successfully Generated!\n")
    print("=" * 40)
    print(response.text)
    print("=" * 40)
    
except Exception as e:
    print(f"⚠️ API Error: {e}")
