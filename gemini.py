"""Gemini API (free tier). Model ka naam khud Google se poochhta hai."""
import json
import os
import re
import time
import urllib.error
import urllib.request

BASE = "https://generativelanguage.googleapis.com/v1beta"
_models = {}                                      # हर key की अपनी model list
_dead = set()
_dead = set()                                     # (key, model) जिनका आज का कोटा ख़त्म
_gone = set()                                     # 404 वाले (बंद हो चुके) models


def keys():
    """सारी Gemini keys क्रम से: पहली का कोटा ख़त्म हो तो दूसरी."""
    ks = [os.getenv(n, "").strip() for n in ("GEMINI_API_KEY", "GEMINI_API_KEY2", "GEMINI_API_KEY3")]
    return list(dict.fromkeys(k for k in ks if k))


def _get(url, key, body=None):
    req = urllib.request.Request(url, json.dumps(body).encode() if body else None,
                                 {"Content-Type": "application/json", "x-goog-api-key": key})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)


def models(key):
    """Is key par jo text models chalte hain, unki list (flash pehle)."""
    if key in _models:
        return _models[key]
    names = []
    try:
        data = _get(f"{BASE}/models?pageSize=200", key)
        for m in data.get("models", []):
            n = m["name"].split("/")[-1]
            if "generateContent" not in m.get("supportedGenerationMethods", []):
                continue
            if re.search(r"tts|image|embed|audio|live|vision|aqa|learnlm|gemma|research|computer|robotic|veo|imagen|lyria|nano|banana", n):
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
    _models[key] = ([env] if env else []) + names[:5] + [p for p in pros if p not in names[:5]] + ["gemini-flash-latest"]
    print("  Gemini models:", ", ".join(_models[key]))
    return _models[key]


class QuotaOver(RuntimeError):
    """आज का free कोटा ख़त्म — दोबारा कोशिश बेकार."""


def ask(prompt, search=False, json_mode=False, temperature=0.9, prefer=None, patient=True):
    """पहली key से; उसका आज का कोटा ख़त्म हो तो अगली key से."""
    ks = keys()
    if not ks:
        raise RuntimeError("GEMINI_API_KEY नहीं मिली")
    for n, key in enumerate(ks, 1):
        if key in _dead:                              # इस run में पहले ही ख़त्म मिली — सीधे अगली
            continue
        try:
            return _ask(key, prompt, search, json_mode, temperature, prefer, patient)
        except QuotaOver:
            _dead.add(key)
            if n < len(ks):
                print(f"    key {n} का कोटा ख़त्म → key {n + 1}")
        except RuntimeError as e:                      # कोई और गड़बड़ — अगली key भी आज़माओ
            last = e
            if n < len(ks):
                print(f"    key {n} नहीं चली → key {n + 1}")
            elif not [k for k in ks if k in _dead]:
                raise
    raise QuotaOver("सारी Gemini keys का आज का कोटा ख़त्म")


class Blocked(RuntimeError):
    """Gemini ने prompt ही रोक दिया (कोई खबर safety filter में अटकी)."""


def _ask(key, prompt, search, json_mode, temperature, prefer, patient=True):
    parts = prompt if isinstance(prompt, list) else [{"text": prompt}]     # list = text + तस्वीरें (inline_data)
    body = {"contents": [{"parts": parts}], "generationConfig": {"temperature": temperature},
            "safetySettings": [{"category": f"HARM_CATEGORY_{c}", "threshold": "BLOCK_ONLY_HIGH"}     # खबरों में अपराध/हादसे
                               for c in ("HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT")]}
    if search:
        body["tools"] = [{"google_search": {}}]
    elif json_mode:
        body["generationConfig"]["responseMimeType"] = "application/json"
    errors = []
    order = [m for m in models(key) if m not in _gone and (key, m) not in _dead]
    if os.getenv("GEMINI_PRO", "0") != "1":           # 31 Oct log: free keys पर pro हर बार 429 (कोटा 0) — उसे गिनना/पूछना बंद;
        order = [m for m in order if "pro" not in m]  # वरना busy flash के साथ मिलकर "कोटा ख़त्म" का झूठा फ़ैसला
    if not order:
        raise QuotaOver("इस key पर कोई model नहीं बचा")
    if prefer:                                        # जैसे "pro": पहले वो, फिर बाक़ी
        order = [m for m in order if prefer in m] + [m for m in order if prefer not in m]
    for rnd in range(2 if patient else 1):            # सीमा लगे तो रुको नहीं, अगला model; सब पर लगे तभी एक बार रुको
        busy, daily_hits = False, 0
        for model in order:
            try:
                t0 = time.time()
                data = _get(f"{BASE}/models/{model}:generateContent", key, body)
                print(f"    Gemini {model}: {time.time() - t0:.0f}s")
                if not data.get("candidates"):
                    raise Blocked(str(data.get("promptFeedback") or data)[:300])
                return "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
            except urllib.error.HTTPError as e:
                msg = e.read().decode("utf-8", "ignore")[:3000]
                errors.append(f"{model}: {e.code} {msg[:120]}")
                if e.code == 404:
                    _gone.add(model)
                daily = e.code == 429 and "PerMinute" not in msg       # मिनट वाली नहीं = दिन का कोटा ख़त्म
                daily_hits += daily
                if daily:                                 # इस model का आज का कोटा गया — इस run में दोबारा मत पूछो
                    _dead.add((key, model))               # (29 Oct: हर call पहले pro पर 429 खाकर समय गँवाती थी)
                busy |= e.code in (429, 503) and not daily
            except Blocked as e:                      # दूसरे model पर भी यही होगा — सीधे बताओ
                print("    Gemini ने prompt रोका:", e)
                raise
            except Exception as e:                    # noqa: BLE001
                errors.append(f"{model}: {e!r}")
        # आधे या ज़्यादा models पर दिन वाली सीमा = कोटा ख़त्म (पहले किसी एक model का 503 इसे "busy" बना देता था →
        # 40s + 4 मिनट के बेकार retry और Telegram पर ग़लत "busy" message)
        if daily_hits and (not busy or daily_hits * 2 >= len(order)):
            for er in errors[:3]:                         # 30 Oct: reset के तुरंत बाद भी "ख़त्म" — असली वजह log में दिखे
                print("    429:", er[:160].replace("\n", " "))
            raise QuotaOver("आज का Gemini कोटा ख़त्म")
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


def ask_json(prompt, tries=3, **kw):
    """ask + json_from; Gemini कभी-कभी टूटा JSON देता है (30 Oct: एक कॉमा कम = पूरी सुबह की scripts नहीं बनीं) — दोबारा पूछो."""
    last = None
    for k in range(tries):
        txt = ask(prompt, **kw)
        try:
            return json_from(txt)
        except (ValueError, IndexError) as e:
            last = e
            print(f"    टूटा JSON ({k + 1}/{tries}):", repr(e)[:80])
    raise last

