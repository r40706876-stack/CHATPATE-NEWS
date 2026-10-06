import feedparser
import google.generativeai as genai
import os
import random
import time

# GitHub secrets se Gemini API key lena
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

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
    
    # ⬇️ तुम्हारा ऑटो-स्विच (Fallback) लॉजिक
    fallback_models = [
        'gemini-2.5-flash',   # Future model
        'gemini-2.0-flash',   # Latest fast model
        'gemini-1.5-pro',     # Powerful model
        'gemini-1.5-flash',   # Standard model
        'gemini-1.5-flash-8b' # Lightweight model
    ]
    
    for model_name in fallback_models:
        print(f"🔄 Try kar raha hu model: {model_name}...")
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            print(f"✅ Success! Script '{model_name}' ne likhi hai.")
            return response.text.strip()
            
        except Exception as e:
            print(f"⚠️ {model_name} fail ho gaya. Error: {e}")
            print("⏬ Niche wale model par switch kar raha hu...\n")
            time.sleep(2) # Agle try se pehle thoda wait karega
            
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
    
    with open("script.txt", "w", encoding="utf-8") as f:
        f.write(script)
    print("✅ Script successfully 'script.txt' me save ho gayi!")
