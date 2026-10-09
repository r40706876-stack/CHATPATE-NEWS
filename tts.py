"""
हर किरदार की आवाज़ — तीन रास्ते, जो पहले चल जाए:
  1. Gemini TTS (सबसे असली, free tier; GEMINI_API_KEY) — हर किरदार की अपनी आवाज़ + अंदाज़
  2. edge-tts (Microsoft की Hindi neural आवाज़ें, free)
  3. Kokoro (offline backup)
हर line की अलग WAV: out/<job>/audio/NN.wav
"""
import base64
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
from scipy.io import wavfile

ROOT = Path(__file__).parent
SR = 24000
TEMPO = 1.05                      # थोड़ा तेज़, comedy timing के लिए (pitch नहीं बदलता)

# ---------------------------------------------------------------- 1. Gemini TTS
GEM = {   # किरदार: (voice, अंदाज़)
    "bablu": ("Puck", "जोशीला, ओवर-कॉन्फ़िडेंट हिंदी न्यूज़ रिपोर्टर, तेज़ और साफ़, ब्रेकिंग न्यूज़ वाला अंदाज़"),
    "chacha": ("Algenib", "पचपन साल के चाय वाले चाचा, भारी और धीमी आवाज़, ठंडा देसी अंदाज़, punch से पहले हल्का ठहराव"),
    "pinky": ("Leda", "बीस साल की शहरी लड़की, sassy और sarcastic, Instagram वाली Hinglish, तीखा अंदाज़"),
    "dadi": ("Gacrux", "बहत्तर साल की चुलबुली देसी दादी, बूढ़ी पर दमदार आवाज़, नाटकीय, ताना मारते हुए"),
    "riya": ("Leda", "बीस साल की लड़की, सपाट sarcastic अंदाज़"),
    "bunty": ("Fenrir", "छब्बीस साल का ओवर-एक्साइटेड लड़का, तेज़ बोलता है"),
}
MOOD = {"happy": "खुश होकर", "shock": "चौंककर", "angry": "गुस्से में", "smug": "इतराते हुए, ताना मारते हुए",
        "sad": "दुखी होकर"}
TTS_MODELS = [m for m in (os.getenv("GEMINI_TTS_MODEL"), "gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts",
                          "gemini-3.1-flash-tts-preview", "gemini-2.5-flash-preview-tts") if m]
BASE = "https://generativelanguage.googleapis.com/v1beta"


def _post(url, body, key):
    req = urllib.request.Request(url, json.dumps(body).encode(),
                                 {"Content-Type": "application/json", "x-goog-api-key": key})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def _find_audio(obj):
    """जवाब में कहीं भी base64 audio हो तो निकालो."""
    if isinstance(obj, dict):
        for k in ("data",):
            v = obj.get(k)
            if isinstance(v, str) and len(v) > 1000:
                return base64.b64decode(v)
        for v in obj.values():
            a = _find_audio(v)
            if a:
                return a
    elif isinstance(obj, list):
        for v in obj:
            a = _find_audio(v)
            if a:
                return a
    return None


def _to_array(raw):
    if raw[:4] == b"RIFF":
        sr, a = wavfile.read(io.BytesIO(raw))
    else:
        sr, a = SR, np.frombuffer(raw[: len(raw) // 2 * 2], dtype="<i2")
    a = a.astype(np.float32) / 32768.0
    if a.ndim > 1:
        a = a.mean(axis=1)
    if sr != SR:
        a = np.interp(np.linspace(0, len(a), int(len(a) * SR / sr), endpoint=False), np.arange(len(a)), a)
    return a.astype(np.float32)


_gem_ok = {"model": None, "dead": False}


def gemini_line(text, who, expr, key):
    voice, style = GEM.get(who, GEM["bablu"])
    style = ", ".join(s for s in (style, MOOD.get(expr, expr if len(expr) > 12 else "")) if s)
    errors = []
    models = [_gem_ok["model"]] if _gem_ok["model"] else TTS_MODELS
    for model in models:
        bodies = [
            ("interactions", f"{BASE}/interactions", {
                "model": model,
                "input": [{"type": "user_input", "content": [{"type": "text", "text": text,
                           "annotations": [{"type": "speech_metadata", "style": style}]}]}],
                "response_format": {"type": "audio"},
                "generation_config": {"speech_config": [{"voice": voice}]}}),
            ("generateContent", f"{BASE}/models/{model}:generateContent", {
                "contents": [{"parts": [{"text": f"इस अंदाज़ में बोलो — {style}:\n{text}"}]}],
                "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {
                    "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}),
        ]
        for name, url, body in bodies:
            for attempt in range(2):
                try:
                    raw = _find_audio(_post(url, body, key))
                    if raw:
                        _gem_ok["model"] = model
                        return _to_array(raw)
                    errors.append(f"{model}/{name}: audio नहीं")
                    break
                except urllib.error.HTTPError as e:
                    msg = e.read().decode("utf-8", "ignore")[:160]
                    errors.append(f"{model}/{name}: {e.code} {msg}")
                    if e.code == 429 and attempt == 0 and "limit: 0" not in msg:
                        time.sleep(25)
                        continue
                    break
                except Exception as e:                    # noqa: BLE001
                    errors.append(f"{model}/{name}: {e!r}")
                    break
    raise RuntimeError(" | ".join(errors[-4:]))


# ---------------------------------------------------------------- 2. edge-tts
EDGE = {   # किरदार: (voice, pitch, rate)
    "bablu": ("hi-IN-MadhurNeural", "+6Hz", "+8%"),
    "chacha": ("hi-IN-MadhurNeural", "-14Hz", "-6%"),
    "pinky": ("hi-IN-SwaraNeural", "+12Hz", "+6%"),
    "dadi": ("hi-IN-SwaraNeural", "-10Hz", "-4%"),
    "riya": ("hi-IN-SwaraNeural", "+6Hz", "+4%"),
    "bunty": ("hi-IN-MadhurNeural", "+10Hz", "+12%"),
}


def edge_line(text, who, tmp):
    try:
        import edge_tts                                   # noqa: F401
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "edge-tts"], check=True)
    import asyncio
    import edge_tts
    voice, pitch, rate = EDGE.get(who, EDGE["bablu"])
    mp3 = Path(tmp).with_suffix(".mp3")

    async def go():
        await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(str(mp3))
    asyncio.run(asyncio.wait_for(go(), timeout=60))
    wav = Path(tmp).with_suffix(".e.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3), "-ac", "1", "-ar", str(SR), str(wav)], check=True)
    sr, a = wavfile.read(wav)
    mp3.unlink(missing_ok=True)
    wav.unlink(missing_ok=True)
    return a.astype(np.float32) / 32768.0


# ---------------------------------------------------------------- 3. Kokoro (offline)
KOKORO = {   # (voice, speed, pitch) — pitch कम बदला ताकि "तुतलाना" न लगे
    "bablu": ("hm_omega", 1.05, 1.03),
    "chacha": ("hm_psi", 0.95, 0.92),
    "pinky": ("hf_alpha", 1.03, 1.04),
    "dadi": ("hf_beta", 0.98, 0.94),
    "riya": ("hf_alpha", 1.0, 1.0),
    "bunty": ("hm_omega", 1.1, 1.0),
}
_k = {}


def _kokoro():
    if not _k:
        import onnxruntime as rt
        mdir = Path(os.getenv("MODELS_DIR", ROOT / "models"))
        _k["sess"] = rt.InferenceSession(str(mdir / "kokoro.int8.onnx"))
        _k["voices"] = np.load(mdir / "voices-v1.0.bin")
        _k["vocab"] = json.load(open(ROOT / "models" / "kokoro_config.json"))["vocab"]
        _k["espeak"] = shutil.which("espeak-ng") or "/opt/espeak/bin/espeak-ng"
    return _k


def kokoro_line(text, who, tmp):
    k = _kokoro()
    out = []
    for p in re.findall(r"[^।!?,]+[।!?,]?", text):
        punct = p[-1] if p[-1] in "।!?," else ""
        body = p.rstrip("।!?,").strip()
        if body:
            ipa = subprocess.run([k["espeak"], "-q", "--ipa", "-v", "hi", body], capture_output=True, text=True).stdout
            out.append(" ".join(ipa.split()) + {"।": ".", "!": "!", "?": "?", ",": ","}.get(punct, ""))
    voice, speed, pitch = KOKORO.get(who, KOKORO["bablu"])
    toks = [k["vocab"][c] for c in " ".join(out) if c in k["vocab"]][:510]
    a = k["sess"].run(None, {"tokens": np.array([[0, *toks, 0]], dtype=np.int64),
                             "style": k["voices"][voice][len(toks) - 1].astype(np.float32),
                             "speed": np.array([speed], dtype=np.float32)})[0].ravel()
    raw = Path(tmp).with_suffix(".k.wav")
    shifted = Path(tmp).with_suffix(".k2.wav")
    wavfile.write(raw, SR, (np.clip(a, -1, 1) * 32767).astype(np.int16))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af",
                    f"asetrate={int(SR * pitch)},aresample={SR},atempo={1 / pitch:.4f}", str(shifted)], check=True)
    sr, b = wavfile.read(shifted)
    raw.unlink(missing_ok=True)
    shifted.unlink(missing_ok=True)
    return b.astype(np.float32) / 32768.0


# ---------------------------------------------------------------- सब मिलाकर
def split_by_silence(a, n):
    """एक लंबी आवाज़ को n हिस्सों में काटो — सबसे लंबे ठहराव पर."""
    if n == 1:
        return [a]
    hop = SR // 100                                       # 10ms
    e = np.array([np.sqrt(np.mean(a[i:i + hop] ** 2)) for i in range(0, len(a) - hop, hop)])
    quiet = e < max(0.01, e.max() * 0.04)
    gaps, s = [], None
    for k, q in enumerate(quiet):
        if q and s is None:
            s = k
        if not q and s is not None:
            if k - s >= 18:                               # ≥ 0.18s का ठहराव
                gaps.append((k - s, (s + k) // 2))
            s = None
    if len(gaps) < n - 1:
        raise ValueError(f"{n - 1} ठहराव चाहिए, मिले {len(gaps)}")
    cuts = sorted(c for _, c in sorted(gaps, reverse=True)[: n - 1])
    pts = [0] + [c * hop for c in cuts] + [len(a)]
    return [a[pts[k]:pts[k + 1]] for k in range(n)]


def gemini_character(lines, who, key):
    """एक किरदार की सारी lines एक ही call में — आवाज़ हर line में एक जैसी."""
    if len(lines) == 1:
        return [gemini_line(lines[0]["say"], who, lines[0].get("expr", ""), key)]
    joined = "\n\n".join(l["say"] for l in lines)
    try:
        a = gemini_line(joined + "\n", who, "हर लाइन के बाद पूरा एक सेकंड रुकना", key)
        parts = split_by_silence(a, len(lines))
        for l, p in zip(lines, parts):                    # लंबाई का अंदाज़ा: ~0.06s प्रति अक्षर
            exp = len(l["say"]) * 0.06
            if not (0.3 * exp < len(p) / SR < 3.0 * exp):
                raise ValueError("हिस्से की लंबाई गड़बड़")
        return parts
    except ValueError as e:                               # काटना ठीक न बैठे → line-line, पर वही voice
        print(f"  {who}: एक साथ वाली आवाज़ काट नहीं पाए ({e}), line-line बना रहे हैं")
        return [gemini_line(l["say"], who, l.get("expr", ""), key) for l in lines]


def make_all(script, engine, out, key):
    lines = script["lines"]
    res = [None] * len(lines)
    if engine == "gemini":
        for who in dict.fromkeys(l["who"] for l in lines):      # हर किरदार की आवाज़ शुरू में एक साथ
            idx = [i for i, l in enumerate(lines) if l["who"] == who]
            for i, a in zip(idx, gemini_character([lines[i] for i in idx], who, key)):
                res[i] = a
            print(f"  {who}: {len(idx)} lines की आवाज़ एक साथ बनी")
    else:
        for i, l in enumerate(lines):
            res[i] = (edge_line if engine == "edge" else kokoro_line)(l["say"], l["who"], out / f"{i:02d}")
    return res


LETTER = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", ["ए", "बी", "सी", "डी", "ई", "एफ़", "जी", "एच", "आई", "जे", "के", "एल", "एम",
                                                  "एन", "ओ", "पी", "क्यू", "आर", "एस", "टी", "यू", "वी", "डब्ल्यू", "एक्स", "वाई", "ज़ेड"]))
WORDS = {"wifi": "वाईफ़ाई", "wi-fi": "वाईफ़ाई", "reel": "रील", "reels": "रील्स", "phone": "फ़ोन", "online": "ऑनलाइन",
         "offline": "ऑफ़लाइन", "app": "ऐप", "instagram": "इंस्टाग्राम", "video": "वीडियो", "comment": "कमेंट",
         "follow": "फ़ॉलो", "share": "शेयर", "sale": "सेल", "ok": "ओके", "loan": "लोन", "bank": "बैंक", "mobile": "मोबाइल",
         "recharge": "रिचार्ज", "data": "डेटा", "google": "गूगल", "youtube": "यूट्यूब", "marie": "मैरी", "ketchup": "केचप",
         "maggi": "मैगी", "family": "फ़ैमिली", "group": "ग्रुप", "save": "सेव", "live": "लाइव", "news": "न्यूज़", "and": "और", "or": "या", "the": ""}


def speakable(text):
    """आवाज़ के लिए: English शब्द देवनागरी में (EMI → ईएमआई), ताकि अटपटा न पढ़ा जाए. caption वैसा ही रहता है."""
    def word(m):
        w = m.group(0)
        if w.lower() in WORDS:
            return WORDS[w.lower()]
        if w.isupper() and 2 <= len(w) <= 6:                       # RBI, EMI, LPG, UPI, ATM
            return "".join(LETTER[c] for c in w)
        return w
    text = re.sub(r"[A-Za-z][A-Za-z-]*", word, text)
    return re.sub(r"(\d+)\s*%", r"\1 परसेंट", text)


def speak_script(script, out):
    """पूरी script एक ही engine से — ताकि किसी किरदार की आवाज़ बीच में न बदले."""
    out.mkdir(parents=True, exist_ok=True)
    script = dict(script, lines=[dict(l, say=speakable(l["say"])) for l in script["lines"]])
    import gemini as _g
    gkeys = _g.keys()                                  # पहली key की आवाज़ का कोटा ख़त्म हो तो दूसरी
    key = gkeys[0] if gkeys else None
    order = (["gemini"] * len(gkeys)) + ["edge", "kokoro"]
    if os.getenv("TTS_ENGINE") in order:
        order = order[order.index(os.getenv("TTS_ENGINE")):]
    last, gi = None, 0
    for engine in order:
        if engine == "gemini":
            key, gi = gkeys[gi], gi + 1
        try:
            audios = make_all(script, engine, out, key)
            break
        except Exception as e:                            # noqa: BLE001
            last = e
            print(f"  आवाज़ ({engine}) पूरी नहीं बनी: {str(e)[:300]} → सारी lines अगले engine से")
    else:
        raise RuntimeError(f"कोई आवाज़ नहीं चली: {last}")
    for i, (line, a) in enumerate(zip(script["lines"], audios)):
        tmp = out / f"{i:02d}_raw.wav"
        wavfile.write(tmp, SR, (np.clip(a, -1, 1) * 32767).astype(np.int16))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp), "-af", f"atempo={TEMPO}",
                        "-ar", str(SR), "-ac", "1", str(out / f"{i:02d}.wav")], check=True)
        tmp.unlink(missing_ok=True)
    print(f"  आवाज़: {engine} (सारी {len(audios)} lines, हर किरदार की एक ही voice)")
    return engine


if __name__ == "__main__":
    speak_script(json.load(open(ROOT / (sys.argv[1] if len(sys.argv) > 1 else "script.json"), encoding="utf-8")),
                 ROOT / "audio")
