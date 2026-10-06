import feedparser
import requests
import os
import random
import time

# GitHub secrets se API key lena
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def get_trending_news():
    url = "https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi"
    try:
        feed = feedparser.parse(url)
        top_entries = feed.entries[:5]
        if not top_entries:
            return "Market crash ho gaya, aur udhar dost ne 500 rupaye wapas nahi kiye."
        return random.choice(top_entries).title
    except:
        return "Market crash ho gaya, aur udhar dost ne 500 rupaye wapas nahi kiye."

def get_active_model():
    """Google API se direct un models ki list mangna jo is API Key ke liye available hain"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            models_data = response.json().get('models', [])
            
            valid_models = []
            for m in models_data:
                # Sirf wo models chunna jo text generate kar sakte hain aur gemini series ke hain
                if 'generateContent' in m.get('supportedGenerationMethods', []) and 'gemini' in m.get('name', '').lower():
                    # 'models/' prefix hatana
                    model_name = m['name'].replace('models/', '')
                    valid_models.append(model_name)
            
            # Agar models mil gaye, toh sabse pehle 1.5-flash dhoondhna
            if valid_models:
                for preferred in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']:
                    for v in valid_models:
                        if preferred in v:
                            return v
                return valid_models[0] # Agar preferred nahi mila toh list ka pehla de do
    except Exception as e:
        print(f"Error fetching models: {e}")
    return None

def generate_script(news_headline):
    print("🔍 Google se aapki API Key ke active models nikal raha hu...")
    active_model = get_active_model()
    
    if not active_model:
        return "Error: Koi valid Gemini model nahi mila. Shayad API Key limit cross ho gayi hai."
        
    print(f"✅ Success! Google ne '{active_model}' model assign kiya hai.")
    
    prompt = f"""
    You are a sarcastic, relatable Indian Gen-Z commentator.
    Take this trending news headline: "{news_headline}"
    
    Write a short 30-second Hinglish (Hindi + English) monologue script for an Instagram Reel.
    Start with a catchy shocking hook. 
    Add a funny punchline relating this news to middle-class life, office struggles, unemployment, or exams.
    Output ONLY the dialogue that needs to be spoken. No emojis, no hashtags, no background instructions, no speaker names.
    Keep it under 4-5 lines.
    """
    
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{active_model}:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    print(f"✍️ '{active_model}' se script likhwa raha hu...")
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            script_text = result['candidates'][0]['content']['parts'][0]['text']
            return script_text.strip()
        else:
            print(f"⚠️ API Error Status: {response.status_code}")
            print(f"Detail: {response.text}")
    except Exception as e:
        print(f"⚠️️ Request me dikkat aayi: {e}")
            
    return "Dosto, lagta hai aaj AI thak gaya hai. Hum kal milte hain nayi news ke sath!"

if __name__ == "__main__":
    print("📰 Trending News dhundh raha hu...")
    news = get_trending_news()
    print(f"Headline: {news}\n")
    
    script = generate_script(news)
    
    print("\n--- FINAL SCRIPT ---")
    print(script)
    print("--------------------\n")
    
    with open("script.txt", "w", encoding="utf-8") as f:
        f.write(script)
    print("✅ Script successfully 'script.txt' me save ho gayi!")
