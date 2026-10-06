import os
# नया और सही पैकेज इम्पोर्ट किया है
from google import genai

print("🚀 Testing New GenAI Package...")

# GitHub Secrets से API key उठाना
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: API Key नहीं मिली!")
    exit(1)

try:
    # नए तरीके से क्लाइंट सेटअप (Dry run verified)
    client = genai.Client(api_key=api_key)
    print("✅ Client Set Up Successfully!")

    # नए तरीके से 1.5-flash मॉडल को कॉल करना
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents='हेलो, क्या तुम सही से काम कर रहे हो?'
    )
    
    print("\n✅ API Response:")
    print(response.text)

except Exception as e:
    print(f"❌ Error occurred: {e}")
