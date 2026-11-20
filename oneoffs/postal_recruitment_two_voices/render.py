"""Recut the approved Postal Edge narration as a sequence of distinct shots."""
import importlib.util
import io
import json
import math
import os
import shutil
import subprocess
import sys
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "postal_recruitment_draft"
ACTION = HERE.parent / "postal_recruitment_action_cut"
OUT = ROOT / "recruitment_preview"
FILENAME = "Postal_Edge_GDS_Postman_Two_Voices.mp4"
DIALOGUE = [
    ("golu", "भैया, तीन साल जी डी एस सेवा पर सीधे पोस्टमैन का पेपर?"),
    ("bhaiya", "डाक विभाग ने पाँच की जगह तीन साल की सेवा प्रस्तावित की है।"),
    ("golu", "तो पहले एम टी एस बनना पड़ेगा?"),
    ("bhaiya", "प्रस्ताव लागू हुआ और बाकी शर्तें पूरी हैं, तो सीधे पोस्टमैन या मेल गार्ड की परीक्षा दे सकोगे।"),
    ("golu", "और बन गए, तो हाथ में कितने?"),
    ("bhaiya", "दिल्ली के उदाहरण में करीब चवालीस हज़ार रुपये। पूरा हिसाब स्क्रीन पर है।"),
    ("golu", "अच्छा, तैयारी कहाँ से करूँ?"),
    ("bhaiya", "पोस्टल एज डॉट इन पर फ्री वीडियो डेमो देखो। चित्रों से नियम समझो।"),
]
VOICES = {
    "golu": ("hi-in-assistant-10", "A youthful Hindi boy character in a short animation. Light higher register, curious, lively and natural. Sound like you're asking a real question. Quick, playful, clear. Avoid a cartoon squeak."),
    "bhaiya": ("hi-in-concierge-10", "Warm adult male Hindi postman, speaking to a curious youngster. Natural conversation, slightly brisk, clear with small pauses. Avoid announcer delivery."),
}
MINIMUMS = (2.8, 4.1, 2.1, 5.1, 2.4, 7.0, 2.0, 4.1)
RATE = 48000

def voice_parts(role):
    sys.path[:0] = [str(ROOT), str(ROOT / "deep")]
    import deep_demo as deep

    voice, style = VOICES[role]
    deep.M.GEMINI_TTS_VOICE, deep.M.GEMINI_TTS_STYLE = voice, style
    keys = [os.environ.get(f"POSTAL_KEY_{n}", "") for n in (4, 3, 2, 1)]
    keys = [k for k in keys if k.strip()]
    assert keys, "No configured Gemini API slots"
    if role == "golu":
        keys = keys[1:] + keys[:1]
    for index, (speaker, words) in enumerate(DIALOGUE):
        if speaker != role:
            continue
        for key in keys:
            deep.M.GEMINI_API_KEY = key
            try:
                audio = deep.M._gemini_tts_once([words], voice=voice)
                clipped, = deep.cut_lines(audio, [(str(index), words)])
                assert 0.6 < len(clipped)/deep.M.SR < 14
                part = OUT / f"voice{index}.wav"
                pcm = (np.clip(clipped, -1, 1)*32767).astype("<i2")
                with wave.open(str(part), "wb") as out:
                    out.setparams((1,2,deep.M.SR,0,"NONE","not compressed"))
                    out.writeframes(pcm.tobytes())
                print("Dialogue", index, role, voice, round(len(clipped)/deep.M.SR,2), flush=True)
                break
            except (deep.M.VoiceUnavailable, RuntimeError, AssertionError) as exc:
                print("Voice attempt failed", role, index, type(exc).__name__, flush=True)
        else:
            raise RuntimeError(f"Could not generate line {index} for {role}")

def dialogue_audio():
    def worker(role):
        run(sys.executable, __file__, "--voice", role)
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(worker, VOICES))
    cuts, pieces = [], []
    size = 0
    for i, minimum in enumerate(MINIMUMS):
        cuts.append(size / RATE)
        data = subprocess.check_output(["ffmpeg","-v","error","-i",str(OUT / f"voice{i}.wav"),
                                        "-af","loudnorm=I=-17:TP=-2:LRA=8","-ac","1","-ar",str(RATE),"-f","f32le","-"])
        speech = np.frombuffer(data, dtype="<f4")
        if i == 0:
            pad = np.zeros(3840,dtype=np.float32)
        else:
            pad = np.zeros(5760,dtype=np.float32)
        frames = max(round(minimum*30), math.ceil((len(pad) + len(speech) + (int(.45*RATE) if i==7 else int(.17*RATE)))/1600))
        piece = np.pad(np.concatenate([pad,speech]), (0,frames*1600-len(pad)-len(speech)))
        pieces.append(piece.astype("<f4"))
        size += len(piece)
    samples = np.concatenate(pieces)
    raw = OUT / "dialogue.f32"
    raw.write_bytes(samples.tobytes())
    return cuts, size/RATE, raw, samples[::3]

def run(*args):
    subprocess.run(args, check=True)

def puppets(samples, duration, cuts):
    sys.path.insert(0, str(ROOT))
    from postal_edge_lip_shapes import measure_mouth
    from postal_edge_puppet import puppet
    rate = 15
    mouths = measure_mouth(samples, rate, duration)
    folders = [OUT / "golu", OUT / "bhaiya"]
    for folder in folders:
        folder.mkdir(exist_ok=True)
    actions = [("hop", "welcome"), ("chin", "right"), ("open", "left"), ("chin", "open"),
               ("hop", "welcome"), ("open", "left"), ("right", "welcome"), ("open", "right")]
    idx = 0
    for frame in range(math.ceil(duration * rate)):
        t = frame / rate
        if idx + 1 < len(cuts) and t >= cuts[idx + 1]:
            idx += 1
        elapsed = t - cuts[idx]
        for j, folder in enumerate(folders):
            golu = j == 0
            face = .69 if golu else -.64
            active = golu == (DIALOGUE[idx][0] == "golu")
            lips = mouths[min(frame, len(mouths)-1)] if active else None
            excited = golu and idx in (0, 2, 4, 6)
            step = (.82 if idx in (0, 2, 5, 7) else .26) * math.exp(-elapsed * 2.9)
            hop = .8 * max(0, math.sin(elapsed * 5)) if excited and elapsed < .57 else 0
            mood = ("surprise" if idx == 1 else "happy") if excited or not golu else "think"
            strength = .51 + .45 * (math.sin(elapsed * 2.9 + j) ** 2)
            im = puppet(golu, t, step, face, lips, mood, (strength, actions[idx][j]),
                        face, hop, .13 * math.sin(elapsed * 2.35))
            im.save(folder / f"{frame:04d}.png")

def contact(final, duration, cuts):
    sheet = Image.new("RGB", (675, 1200), "#15243d")
    for idx, offset in enumerate([t + .85 for t in cuts] + [duration-.7]):
        raw = subprocess.check_output(["ffmpeg","-v","error","-ss",str(offset),"-i",str(final),
                                       "-frames:v","1","-f","image2pipe","-vcodec","png","-"])
        im = Image.open(io.BytesIO(raw))
        if idx == 0:
            im.save(OUT / "cover.jpg", quality=95)
        sheet.paste(im.resize((225,400)), ((idx%3)*225,(idx//3)*400))
    sheet.save(OUT / "contact.jpg", quality=94)

def main():
    salary = Path(sys.argv[1])
    OUT.mkdir(exist_ok=True)
    spec = importlib.util.spec_from_file_location("approved_reel", BASE / "render.py")
    approved = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(approved)
    approved.source_cards()
    for i in range(6):
        shutil.copyfile(ACTION / f"location{i}.jpg", OUT / f"location{i}.jpg")
    shutil.copyfile(salary, OUT / "salary.png")
    shutil.copyfile(BASE.parent / "postal_recruitment_website_outro" / "website-courses.jpg", OUT / "website.jpg")
    cuts, duration, audio, samples = dialogue_audio()
    assert 25 < duration < 47
    puppets(samples, duration, cuts)
    html = OUT / "action.html"
    html.write_text((HERE / "scenes.html").read_text().replace("__DATA__", json.dumps({
        "cuts": cuts, "total": duration, "speakers": [role for role, _ in DIALOGUE],
    })))
    renderer = ROOT / "deep/render_deep.py"
    code = renderer.read_text()
    assert "#cutImg,#estImg" in code
    renderer.write_text(code.replace("#cutImg,#estImg", "#cutImg,#estImg,#golu,#bhaiya,#bg,#salary"))
    silent = OUT / "silent.mp4"
    run(sys.executable, str(renderer), str(html), str(silent))
    final = OUT / FILENAME
    run("ffmpeg","-v","error","-xerror","-y","-i",str(silent),"-f","f32le","-ar",str(RATE),"-ac","1","-i",str(audio),
        "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","160k","-movflags","+faststart",str(final))
    run("ffmpeg","-v","error","-xerror","-i",str(final),"-f","null","-")
    contact(final, duration, cuts)
    (OUT / "report.json").write_text(json.dumps({
        "seconds": duration, "shots": cuts, "salary_card": "X-class Delhi example",
        "voices": {role: voice for role, (voice, _) in VOICES.items()},
        "dialogue": DIALOGUE, "scope": "Preview",
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    if sys.argv[1] == "--voice":
        voice_parts(sys.argv[2])
    else:
        main()
