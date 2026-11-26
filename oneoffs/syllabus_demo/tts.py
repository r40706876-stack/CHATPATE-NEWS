"""Syllabus reel demo: each line in the locked Golu / Bhaiya voice (brand_config.json), plus word timings."""
import json, os, sys, wave
from pathlib import Path
import numpy as np

CORE = Path(os.environ["CORE_DIR"]).resolve()
OUT = Path(os.environ["OUT_DIR"]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
sys.path[:0] = [str(CORE), str(CORE / "deep")]
os.chdir(CORE)
import deep_demo as deep

VOICES = json.load(open(CORE / "brand_config.json"))["character_voices"]
LINES = json.load(open(Path(__file__).with_name("lines.json")))
keys = [k for k in (os.environ.get(f"K{n}", "") for n in (1, 2, 3, 4)) if k.strip()]
assert keys, "no Gemini keys"
report = []
for n, (i, who, text, say, style) in enumerate(LINES):
    v = VOICES[who]
    deep.M.GEMINI_TTS_VOICE, deep.M.GEMINI_TTS_STYLE = v["voice"], (os.environ["HOOK_STYLE"] if style == "urgent" else (v["direction"] + " " + os.environ["URL_STYLE"] if style == "url" else v["direction"]))
    for key in keys[n % len(keys):] + keys[:n % len(keys)]:
        deep.M.GEMINI_API_KEY = key
        try:
            audio = deep.M._gemini_tts_once([say], voice=v["voice"])
            clip, = deep.cut_lines(audio, [(str(i), say)])
            assert 0.5 < len(clip) / deep.M.SR < 15
            break
        except Exception as exc:
            print("retry", i, type(exc).__name__, str(exc)[:120], flush=True)
    else:
        raise SystemExit(f"line {i} failed")
    pcm = (np.clip(clip, -1, 1) * 32767).astype("<i2")
    with wave.open(str(OUT / f"line{i}.wav"), "wb") as w:
        w.setparams((1, 2, deep.M.SR, 0, "NONE", "not compressed")); w.writeframes(pcm.tobytes())
    report.append({"i": i, "who": who, "text": text, "voice": v["voice"], "sec": round(len(clip) / deep.M.SR, 3)})
    print("ok", report[-1], flush=True)

from faster_whisper import WhisperModel
model = WhisperModel("small", device="cpu", compute_type="int8")
for r in report:
    segs, _ = model.transcribe(str(OUT / f"line{r['i']}.wav"), language="hi", word_timestamps=True, beam_size=5)
    r["words"] = [[w.word.strip(), round(w.start, 3), round(w.end, 3)] for s in segs for w in s.words]
json.dump(report, open(OUT / "lines_report.json", "w"), ensure_ascii=False, indent=1)

# Didi raw video: word timings for cutting + captions
didi = Path(__file__).with_name("didi.flac")
if didi.exists():
    m2 = WhisperModel("medium", device="cpu", compute_type="int8")
    prompt = "GDS वालो! एक बिल्कुल फ्री मॉक टेस्ट दो, पूरा वीडियो कोर्स फ्री जीत लो। पहले नंबर वाले को 1099 वाला पूरा वीडियो कोर्स। शॉर्ट नोट्स। डेमो वेबसाइट पर फ्री है। MTS, Postman। 5 दिसंबर, 6 दिसंबर, फ़ॉलो, बायो।"
    segs, _ = m2.transcribe(str(didi), language="hi", word_timestamps=True, beam_size=5, initial_prompt=prompt, vad_filter=False)
    out = [{"s": round(s.start, 3), "e": round(s.end, 3), "t": s.text.strip(), "w": [[w.word.strip(), round(w.start, 3), round(w.end, 3)] for w in s.words]} for s in segs]
    json.dump(out, open(OUT / "didi_words.json", "w"), ensure_ascii=False, indent=1)
    print("didi segs", len(out), flush=True)
