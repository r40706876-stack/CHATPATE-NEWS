import feedparser
from google import genai
import os
import random

# GitHub secrets se Gemini API key lena
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

def get_trending_news():
    # Google News se Hindi/India ki trending news uthana
    url = "https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi"
    feed = feedparser.parse(url)
    
    top_entries = feed.entries[:5]
    if not top_entries:
        return "Market crash ho gaya, aur udhar dost ne 500 rupaye wapas nahi kiye."
        
    selected_news = random.choice(top_entries).title
    return selected_news

def generate_script(news_headline):
    prompt = f"""
    You are a sarcastic, relatable Indian Gen-Z commentator.
    Take this trending news headline: "{news_headline}"
    
    Write a short 30-second Hinglish (Hindi + English) monologue script for an Instagram Reel.
    Start with a catchy shocking hook. 
    Add a funny punchline relating this news to middle-class life, office struggles, unemployment, or exams.
    Output ONLY the dialogue that needs to be spoken. No emojis, no hashtags, no background instructions, no speaker names.
    Keep it under 4-5 lines.
    """
    
    # ⬇️ मॉडल्स की लिस्ट (सबसे हाईएस्ट से सबसे लोएस्ट की तरफ)
    fallback_models = [
        'gemini-2.5-flash',   # Future/Latest model
        'gemini-2.0-flash',   # Current best fast model
        'gemini-1.5-pro',     # Powerful but sometimes hits quota limits
        'gemini-1.5-flash',   # Standard stable model
        'gemini-1.5-flash-8b' # Basic lightweight model (hamesha khali milta hai)
    ]
    
    # ऑटो-स्विच लॉजिक (Fallback Loop)
    for model_name in fallback_models:
        print(f"🔄 Try kar raha hu model: {model_name}...")
        try:
            response = client.models.generate_content(
                model=model_name, 
                contents=prompt
            )
            print(f"✅ Success! Script '{model_name}' ne likhi hai.")
            return response.text.strip()
            
        except Exception as e:
            # Agar error aati hai (busy, deprecated, limit crossed), toh agla try karega
            print(f"⚠️ {model_name} fail ho gaya ya busy hai. Error: {e}")
            print("⏬ Niche wale model par switch kar raha hu...\n")
            
    # Agar saare models fail ho jayein (Rare case)
    return "Dosto, lagta hai aaj AI bhi thak gaya hai. Hum kal milte hain nayi news ke sath!"

if __name__ == "__main__":
    print("📰 Trending News dhundh raha hu...")
    news = get_trending_news()
    print(f"Headline: {news}\n")
    
    print("✍️ Gemini AI se script likhwa raha hu...")
    script = generate_script(news)
    
    print("\n--- FINAL SCRIPT ---")
    print(script)
    print("--------------------\n")
    
    # Is script ko ek text file me save karna
    with open("script.txt", "w", encoding="utf-8") as f:
        f.write(script)
    print("✅ Script successfully 'script.txt' me save ho gayi!")
