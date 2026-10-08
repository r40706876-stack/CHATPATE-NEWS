"""Gemini API (free tier). Model ka naam khud Google se poochhta hai."""
import json
import os
import re
import time
import urllib.error
import urllib.request

BASE = "https://generativelanguage.googleapis.com/v1beta"
_models = []


def _get(url, key, body=None):
    req = urllib.request.Request(url, json.dumps(body).encode() if body else None,
                                 {"Content-Type": "application/json", "x-goog-api-key": key})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)


def models(key):
    """Is key par jo text models chalte hain, unki list (flash pehle)."""
    if _models:
        return _models
    names = []
    try:
        data = _get(f"{BASE}/models?pageSize=200", key)
        for m in data.get("models", []):
            n = m["name"].split("/")[-1]
            if "generateContent" not in m.get("supportedGenerationMethods", []):
                continue
            if re.search(r"tts|image|embed|audio|live|vision|aqa|learnlm|gemma", n):
                continue
            names.append(n)
    except Exception as e:                            # noqa: BLE001
        print("  model list nahi mili:", e)
    def rank(n):
        return (0 if "flash" in n and "lite" not in n else 1 if "flash" in n else 2,
                0 if "latest" in n else 1, -len(re.findall(r"\d", n)), n)
    names.sort(key=rank)
    env = os.getenv("GEMINI_MODEL")
    pros = [n for n in names if "pro" in n][:2]
    _models[:] = ([env] if env else []) + names[:5] + [p for p in pros if p not in names[:5]] + ["gemini-flash-latest"]
    print("  Gemini models:", ", ".join(_models))
    return _models


def ask(prompt, search=False, json_mode=False, temperature=0.9, prefer=None):
    key = os.environ["GEMINI_API_KEY"]
    body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": temperature}}
    if search:
        body["tools"] = [{"google_search": {}}]
    elif json_mode:
        body["generationConfig"]["responseMimeType"] = "application/json"
    errors = []
    order = models(key)
    if prefer:                                        # जैसे "pro": पहले वो, फिर बाक़ी
        order = [m for m in order if prefer in m] + [m for m in order if prefer not in m]
    for rnd in range(2):                              # सीमा लगे तो रुको नहीं, अगला model; सब पर लगे तभी एक बार रुको
        busy = False
        for model in order:
            try:
                t0 = time.time()
                data = _get(f"{BASE}/models/{model}:generateContent", key, body)
                print(f"    Gemini {model}: {time.time() - t0:.0f}s")
                return "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
            except urllib.error.HTTPError as e:
                msg = e.read().decode("utf-8", "ignore")[:300]
                errors.append(f"{model}: {e.code} {msg[:120]}")
                busy |= e.code in (429, 503) and "limit: 0" not in msg
            except Exception as e:                    # noqa: BLE001
                errors.append(f"{model}: {e!r}")
        if not busy:
            break
        print("    सब models busy — 40s रुककर दोबारा")
        time.sleep(40)
    raise RuntimeError("Gemini nahi chala:\n  " + "\n  ".join(errors))


def json_from(text):
    m = re.search(r"```(?:json)?\s*(.+?)```", text, re.S)
    s = m.group(1) if m else text
    start = min([i for i in (s.find("{"), s.find("[")) if i >= 0] or [0])
    return json.loads(s[start:s.rfind("}" if s[start] == "{" else "]") + 1])
