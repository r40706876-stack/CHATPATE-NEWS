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
    style = ", ".join(s for s in (style, MOOD.get(expr, "")) if s)
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
def speak_script(script, out):
    out.mkdir(parents=True, exist_ok=True)
    key = os.getenv("GEMINI_API_KEY")
    engine = "gemini" if key and os.getenv("TTS_ENGINE", "gemini") == "gemini" else "edge"
    for i, line in enumerate(script["lines"]):
        dst = out / f"{i:02d}.wav"
        a = None
        while a is None:
            try:
                if engine == "gemini":
                    a = gemini_line(line["say"], line["who"], line.get("expr", ""), key)
                elif engine == "edge":
                    a = edge_line(line["say"], line["who"], dst)
                else:
                    a = kokoro_line(line["say"], line["who"], dst)
            except Exception as e:                        # noqa: BLE001
                nxt = {"gemini": "edge", "edge": "kokoro"}.get(engine)
                print(f"  आवाज़ ({engine}) नहीं चली: {str(e)[:300]}")
                if not nxt:
                    raise
                engine = nxt
                print(f"  अब {engine} से")
        tmp = out / f"{i:02d}_raw.wav"
        wavfile.write(tmp, SR, (np.clip(a, -1, 1) * 32767).astype(np.int16))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp), "-af", f"atempo={TEMPO}",
                        "-ar", str(SR), "-ac", "1", str(dst)], check=True)
        tmp.unlink(missing_ok=True)
        print(f"  {i:02d} {line['who']:<7} [{engine}] {line['say'][:40]}")
    return engine


if __name__ == "__main__":
    speak_script(json.load(open(ROOT / (sys.argv[1] if len(sys.argv) > 1 else "script.json"), encoding="utf-8")),
                 ROOT / "audio")
