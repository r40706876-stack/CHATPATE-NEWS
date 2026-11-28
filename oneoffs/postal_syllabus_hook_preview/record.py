"""Use the approved Postal Edge voices and the project's existing TTS engine."""
import json
import os
from pathlib import Path
import sys
import wave

import numpy as np

root = Path.cwd() / "core"
project = Path(__file__).resolve().parent
output = Path("/tmp/syllabus/voice")
sys.path[:0] = [str(root), str(root / "deep")]
os.chdir(root)
import deep_demo as deep

voices = json.loads((root / "brand_config.json").read_text())["character_voices"]
rows = json.loads((project / "lines.json").read_text())
keys = [value for number in range(1, 5) if (value := os.getenv(f"K{number}", "").strip())]
if not keys:
    raise RuntimeError("No configured Gemini key slots")

report = []
for index, role, caption, spoken, style in rows:
    if (index == 0) != (sys.argv[1] == "hook"):
        continue
    voice = voices[role]
    direction = voice["direction"]
    if style == "urgent":
        direction += " A direct, brisk wake-up question to the viewer. Brief pause after निकाला. Finish naturally in 2.6 seconds."
    deep.M.GEMINI_TTS_VOICE, deep.M.GEMINI_TTS_STYLE = voice["voice"], direction
    offset = index % len(keys)
    for key in keys[offset:] + keys[:offset]:
        deep.M.GEMINI_API_KEY = key
        try:
            audio = deep.M._gemini_tts_once([spoken], voice=voice["voice"])
            clip, = deep.cut_lines(audio, [(str(index), spoken)])
            if not .55 < len(clip) / deep.M.SR < 14:
                raise ValueError("Unexpected speech duration")
            break
        except Exception as error:
            print(f"Retry line {index}: {type(error).__name__}", flush=True)
    else:
        if index == 0:
            raise RuntimeError("No approved voice take for the hook")
        print(f"Missing body line {index}", flush=True)
        continue
    path = output / f"line{index}.wav"
    with wave.open(str(path), "wb") as stream:
        stream.setparams((1, 2, deep.M.SR, 0, "NONE", "not compressed"))
        stream.writeframes((np.clip(clip, -1, 1)*32767).astype("<i2").tobytes())
    report.append({"line": index, "voice": voice["voice"], "seconds": len(clip)/deep.M.SR})
    print(report[-1], flush=True)
if sys.argv[1] == "body":
    (output / "voice_timings.json").write_text(json.dumps(report, indent=2))
    (output / "concat.txt").write_text("".join(f"file line{row['line']}.wav\n" for row in report))
