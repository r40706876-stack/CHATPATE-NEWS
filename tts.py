"""
Offline Hindi आवाज़ (Kokoro TTS + espeak-ng phonemes), हर किरदार की अलग आवाज़।

Production में इसकी जगह ElevenLabs/vidIQ जैसी बेहतर आवाज़ लगेगी;
pipeline वही रहेगी — हर line का अलग WAV, फिर reel में जोड़ना।
"""
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import onnxruntime as rt
from scipy.io import wavfile

ROOT = Path(__file__).parent
import os
import shutil
MDIR = Path(os.getenv("MODELS_DIR", ROOT / "models"))
MODEL = MDIR / "kokoro.int8.onnx"
VOICES = MDIR / "voices-v1.0.bin"
VOCAB = json.load(open(ROOT / "models" / "kokoro_config.json"))["vocab"]
ESPEAK = shutil.which("espeak-ng") or "/opt/espeak/bin/espeak-ng"
SR = 24000

# किरदार → (Kokoro voice, बोलने की रफ़्तार, pitch बदलाव)
CAST = {
    "bablu": ("hm_omega", 1.08, 1.10),   # बकरा reporter: तेज़, थोड़ा ऊँचा
    "chacha": ("hm_psi", 0.92, 0.84),    # भैंसा चाचा: धीमे, भारी
    "pinky": ("hf_alpha", 1.05, 1.12),   # बिल्ली पिंकी: चुलबुली
    "dadi": ("hf_beta", 1.0, 0.90),      # 3D दादी (video call): भारी, बूढ़ी
    "riya": ("hf_alpha", 1.05, 1.12),    # 3D रिया (सड़क पर, पिंकी वाली आवाज़): चुलबुली, sarcastic
    "bunty": ("hm_omega", 1.15, 1.02),   # 3D बंटी (video call): तेज़, जोशीला
}

sess = rt.InferenceSession(str(MODEL))
voices = np.load(VOICES)


def phonemes(text):
    parts = re.findall(r"[^।!?,]+[।!?,]?", text)
    out = []
    for p in parts:
        punct = p[-1] if p[-1] in "।!?," else ""
        body = p.rstrip("।!?,").strip()
        if not body:
            continue
        ipa = subprocess.run([ESPEAK, "-q", "--ipa", "-v", "hi", body],
                             capture_output=True, text=True).stdout
        ipa = " ".join(ipa.split())
        out.append(ipa + {"।": ".", "!": "!", "?": "?", ",": ","}.get(punct, ""))
    return " ".join(out)


def speak(text, who):
    voice, speed, pitch = CAST[who]
    ph = phonemes(text)
    tokens = [VOCAB[c] for c in ph if c in VOCAB][:510]
    style = voices[voice][len(tokens) - 1]
    audio = sess.run(None, {"tokens": np.array([[0, *tokens, 0]], dtype=np.int64),
                            "style": style.astype(np.float32),
                            "speed": np.array([speed], dtype=np.float32)})[0].ravel()
    return audio, pitch


def pitch_shift(wav_in, wav_out, factor):
    # pitch बदलो पर रफ़्तार वही रखो (asetrate + atempo)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav_in, "-af",
                    f"asetrate={int(SR*factor)},aresample={SR},atempo={1.12/factor:.4f}",
                    wav_out], check=True)


def speak_script(script, out):
    out.mkdir(parents=True, exist_ok=True)
    for i, line in enumerate(script["lines"]):
        audio, pitch = speak(line["say"], line["who"])
        raw = out / f"{i:02d}_raw.wav"
        wavfile.write(raw, SR, (np.clip(audio, -1, 1) * 32767).astype(np.int16))
        pitch_shift(str(raw), str(out / f"{i:02d}.wav"), pitch)
        print(f"{i:02d} {line['who']:<7} {len(audio)/SR:5.2f}s  {line['say'][:40]}")


if __name__ == "__main__":
    import sys
    speak_script(json.load(open(ROOT / (sys.argv[1] if len(sys.argv) > 1 else "script.json"), encoding="utf-8")), ROOT / "audio")
