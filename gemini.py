"""Gemini API (free tier) — एक छोटा helper. Key: GEMINI_API_KEY."""
import json
import os
import re
import time
import urllib.error
import urllib.request

MODELS = [m for m in (os.getenv("GEMINI_MODEL"), "gemini-flash-latest", "gemini-2.5-flash") if m]


def ask(prompt, search=False, json_mode=False, temperature=0.9):
    """search=True → Google Search से ताज़ा जानकारी (grounding). लौटाता है text."""
    key = os.environ["GEMINI_API_KEY"]
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature}}
    if search:
        body["tools"] = [{"google_search": {}}]
    elif json_mode:
        body["generationConfig"]["responseMimeType"] = "application/json"
    last = None
    for model in MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, json.dumps(body).encode(),
                                             {"Content-Type": "application/json", "x-goog-api-key": key})
                with urllib.request.urlopen(req, timeout=180) as r:
                    data = json.load(r)
                parts = data["candidates"][0]["content"]["parts"]
                return "".join(p.get("text", "") for p in parts)
            except urllib.error.HTTPError as e:
                last = f"{model}: {e.code} {e.read()[:200]!r}"
                if e.code == 429:
                    time.sleep(25 * (attempt + 1))
                    continue
                break
            except Exception as e:                     # noqa: BLE001
                last = f"{model}: {e!r}"
                time.sleep(3)
    raise RuntimeError("Gemini नहीं चला — " + str(last))


def json_from(text):
    """जवाब में से पहला JSON (```json ... ``` हो तब भी)."""
    m = re.search(r"```(?:json)?\s*(.+?)```", text, re.S)
    s = m.group(1) if m else text
    start = min([i for i in (s.find("{"), s.find("[")) if i >= 0] or [0])
    return json.loads(s[start:s.rfind("}" if s[start] == "{" else "]") + 1])
