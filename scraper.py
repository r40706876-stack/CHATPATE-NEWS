import feedparser
import google.generativeai as genai
import os
import random

# GitHub secrets se Gemini API key lena
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

def get_trending_news():
    # Google News se Hindi/India ki trending news uthana
    url = "https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi"
    feed = feedparser.parse(url)
    
    # Top 5 news me se koi ek random uthana taaki hamesha fresh video bane
    top_entries = feed.entries[:5]
    selected_news = random.choice(top_entries).title
    return selected_news

def generate_script(news_headline):
    # Gemini AI ko prompt dena
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    You are a sarcastic, relatable Indian Gen-Z commentator.
    Take this trending news headline: "{news_headline}"
    
    Write a short 30-second Hinglish (Hindi + English) monologue script for an Instagram Reel.
    Start with a catchy shocking hook. 
    Add a funny punchline relating this news to middle-class life, office struggles, unemployment, or exams.
    Output ONLY the dialogue that needs to be spoken. No emojis, no hashtags, no background instructions, no speaker names.
    Keep it under 4-5 lines.
    """
    
    response = model.generate_content(prompt)
    return response.text.strip()

if __name__ == "__main__":
    print("📰 Trending News dhundh raha hu...")
    news = get_trending_news()
    print(f"Headline: {news}\n")
    
    print("✍️ Gemini AI se script likhwa raha hu...")
    script = generate_script(news)
    
    print("\n--- FINAL SCRIPT ---")
    print(script)
    print("--------------------\n")
    
    # Is script ko ek text file me save karna taaki agla audio wala code isko padh sake
    with open("script.txt", "w", encoding="utf-8") as f:
        f.write(script)
    print("✅ Script successfully 'script.txt' me save ho gayi!")
