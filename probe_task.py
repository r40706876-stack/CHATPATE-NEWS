import os, json, urllib.request
for kn in ("GEMINI_API_KEY", "GEMINI_API_KEY2", "GEMINI_API_KEY3"):
    k = os.getenv(kn, "").strip()
    if not k:
        print(kn, "❌ नहीं मिली"); continue
    try:
        r = json.load(urllib.request.urlopen(urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models?pageSize=5", headers={"x-goog-api-key": k}), timeout=30))
        print(kn, "✅ चल रही", "| अलग key:", k[-4:] not in [os.getenv(x, "")[-4:] for x in ("GEMINI_API_KEY", "GEMINI_API_KEY2", "GEMINI_API_KEY3") if x != kn])
    except Exception as e:
        print(kn, "❌", repr(e)[:120])
