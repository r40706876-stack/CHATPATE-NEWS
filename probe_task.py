import os, json, urllib.request
for kn in ("GEMINI_API_KEY", "GEMINI_API_KEY2"):
    k = os.getenv(kn)
    if not k: print(kn, "missing"); continue
    r = json.load(urllib.request.urlopen(urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models?pageSize=200", headers={"x-goog-api-key": k})))
    print(kn, [m["name"] for m in r.get("models", []) if "tts" in m["name"] or "audio" in m["name"]])
