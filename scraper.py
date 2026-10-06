import feedparser
import requests
import os
import random
import time

# GitHub secrets se API key lena
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def get_trending_news():
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
    
    # Models ki list
    fallback_models = [
        'gemini-2.5-flash',
        'gemini-2.0-flash',
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-pro'
    ]
    
    # Direct REST API call (No Google SDK required)
    for model_name in fallback_models:
        print(f"🔄 Try kar raha hu model: {model_name}...")
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        try:
            response = requests.post(api_url, json=payload)
            if response.status_code == 200:
                result = response.json()
                script_text = result['candidates'][0]['content']['parts'][0]['text']
                print(f"✅ Success! Script '{model_name}' ne likhi hai.")
                return script_text.strip()
            else:
                # Agar model available nahi hai, toh agla try karega
                print(f"⚠️ {model_name} fail ho gaya. Status: {response.status_code}")
                print("⏬ Niche wale model par switch kar raha hu...\n")
                time.sleep(2)
                
        except Exception as e:
            print(f"⚠️ API request me dikkat aayi: {e}")
            time.sleep(2)
            
    return "Dosto, lagta hai aaj AI bhi thak gaya hai. Hum kal milte hain nayi news ke sath!"

if __name__ == "__main__":
    print("📰 Trending News dhundh raha hu...")
    news = get_trending_news()
    print(f"Headline: {news}\n")
    
    print("✍️ Gemini API se script likhwa raha hu...")
    script = generate_script(news)
    
    print("\n--- FINAL SCRIPT ---")
    print(script)
    print("--------------------\n")
    
    with open("script.txt", "w", encoding="utf-8") as f:
        f.write(script)
    print("✅ Script successfully 'script.txt' me save ho gayi!")
