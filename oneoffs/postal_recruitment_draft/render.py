"""One-off preview using the Postal Edge deep renderer and approved 2D puppet rig."""
import io
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import wave

import fitz
import numpy as np
from PIL import Image
import requests

ROOT = Path.cwd()
OUT = ROOT / "recruitment_preview"
HERE = Path(__file__).resolve().parent
SOURCE = "https://utilities.cept.gov.in/dop/pdfbind.ashx?id=15720"
FPS = 30
RIG_FPS = 15
SCENES = [
    ("hook", "जी डी एस में तीन साल पूरे? अगला पेपर एम टी एस का… या सीधे पोस्टमैन का? ये मौका पहले कैसे मिल सकता है?"),
    ("service", "एम टी एस के लिए तीन साल की सेवा चाहिए। अब डाक विभाग ने पोस्टमैन और मेल गार्ड के दो हज़ार तेईस वाले नियम में पाँच की जगह तीन साल करने का मसौदा जारी किया है।"),
    ("example", "सोचिए, आपके तीन साल पूरे हैं। अगर मसौदा इसी रूप में लागू हुआ और बाकी शर्तें पूरी हैं, तो एम टी एस बने बिना सीधे पोस्टमैन का पेपर दे सकेंगे।"),
    ("pay", "और चयन हुआ तो? पे लेवल तीन। शुरुआती बेसिक पे, इक्कीस हज़ार सात सौ रुपये। अभी अंतिम अधिसूचना बाकी है।"),
    ("website", "तैयारी अभी से शुरू करें। पोस्टल एज डॉट इन पर फ्री वीडियो डेमो देखें। आसान भाषा और चित्रों से नियम क्लास में ही समझें और याद करें।"),
]

def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)

def proof(pdf, page, phrase, name):
    p = pdf[page - 1]
    matches = p.search_for(phrase)
    if not matches:
        raise ValueError(f"Source phrase absent on PDF page {page}: {phrase}")
    mark = matches[0]
    for rect in matches[1:]:
        if rect.y0 - mark.y1 < 13 and rect.x0 < mark.x1 + 25:
            mark |= rect
        else:
            break
    annot = p.add_highlight_annot(matches[:1] if len(matches) == 1 else [r for r in matches if mark.intersects(r)])
    annot.set_colors(stroke=(1, .79, .18))
    annot.update()
    clip = fitz.Rect(mark.x0 - 6, mark.y0 - 9, mark.x1 + 8, mark.y1 + 10) & p.rect
    p.get_pixmap(matrix=fitz.Matrix(4, 4), clip=clip).save(OUT / (name + ".png"))
    p.delete_annot(annot)

def source_cards():
    local = os.getenv("POSTAL_SOURCE_PDF")
    if local:
        data = Path(local).read_bytes()
    else:
        response = requests.get(SOURCE, timeout=40)
        response.raise_for_status()
        data = response.content
    with fitz.open(stream=data, filetype="pdf") as pdf:
        assert len(pdf) == 7 and "20.11.2026" in pdf[0].get_text()
        proof(pdf, 5, "worked regularly for three years in that capacity", "service")
        proof(pdf, 4, "3 years Diploma course or equivalent", "study")

def narration(keys):
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "deep"))
    import deep_demo as deep

    assert deep.M.pick_gemini_voice() == "hi-in-concierge-10"
    assert deep.M.GEMINI_TTS_MODEL == "gemini-3.8-flash-tts"
    for slot, key in keys[-1:] + keys[:-1]:
        deep.M.GEMINI_API_KEY = key
        try:
            audio = deep.M._gemini_tts_once([text for _, text in SCENES])
        except (RuntimeError, deep.M.VoiceUnavailable) as exc:
            print(f"Narration slot {slot}: {type(exc).__name__}", flush=True)
            continue
        parts = deep.cut_lines(audio, SCENES)
        if len(parts) == len(SCENES) and deep.cuts_ok(parts, SCENES):
            return parts, deep.M.SR, slot
    raise RuntimeError("No Gemini slot produced a complete, aligned voice #18 narration")

def audio_track(scenes, rate):
    track = []
    cues = []
    start = 0
    for i, spoken in enumerate(scenes):
        lead = round(rate * (.16 if i == 0 else .09))
        tail = round(rate * (.85 if i == len(scenes) - 1 else .13))
        track.extend((np.zeros(lead), spoken, np.zeros(tail)))
        cues.append(round(start / rate, 6))
        start += lead + len(spoken) + tail
    samples = np.concatenate(track)
    wav = OUT / "narration.wav"
    with wave.open(str(wav), "wb") as handle:
        handle.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        handle.writeframes((np.clip(samples, -1, 1) * 32767).astype("<i2").tobytes())
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(wav), "-f", "f32le", "-ac", "1", "-ar", "16000", "-"])
    return cues, len(samples) / rate, np.frombuffer(raw, dtype="<f4")

def rigs(cues, duration, samples):
    from postal_edge_lip_shapes import measure_mouth
    from postal_edge_puppet import puppet

    mouths = measure_mouth(samples, RIG_FPS, duration)
    folders = [OUT / "golu", OUT / "bhaiya"]
    for folder in folders:
        folder.mkdir(exist_ok=True)
    actions = [("hop", "welcome"), ("right", "left"), ("chin", "open"), ("right", "left"), ("welcome", "open")]
    scene = 0
    for frame in range(math.ceil(duration * RIG_FPS)):
        t = frame / RIG_FPS
        if scene + 1 < len(cues) and t >= cues[scene + 1]:
            scene += 1
        elapsed = t - cues[scene]
        for idx, folder in enumerate(folders):
            golu = idx == 0
            gaze = .65 if golu else -.66
            speaking = mouths[min(frame, len(mouths) - 1)] if golu == (scene == 0) else None
            mood = ("surprise" if scene in (0, 2) else "happy") if golu else "happy"
            hop = max(0, math.sin(elapsed * 5)) * .8 if golu and scene == 0 and elapsed < .62 else 0
            image = puppet(golu, t, .50 * math.exp(-elapsed * 4), gaze, speaking, mood,
                           (.64 + .23 * math.sin(t * 4), actions[scene][idx]), gaze, hop, .10 * math.sin(t * 2))
            image.save(folder / f"{frame:04d}.png")

def render(cues, duration):
    html = OUT / "preview.html"
    html.write_text((HERE / "scenes.html").read_text().replace("__DATA__", json.dumps({
        "cues": cues, "total": duration,
        "frames": math.ceil(duration * RIG_FPS),
    })))
    # The original renderer decodes the two approved puppet images before each frame.
    renderer = ROOT / "deep/render_deep.py"
    code = renderer.read_text()
    selector = "#cutImg,#estImg"
    assert selector in code
    renderer.write_text(code.replace(selector, selector + ",#golu,#bhaiya"))
    silent = OUT / "silent.mp4"
    run(sys.executable, str(renderer), str(html), str(silent))
    final = OUT / "Postal_Edge_GDS_Postman_Big_Change.mp4"
    run("ffmpeg", "-y", "-v", "error", "-i", str(silent), "-i", str(OUT / "narration.wav"),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-af", "loudnorm=I=-16:TP=-1.5:LRA=8", "-ar", "48000",
        "-shortest", "-movflags", "+faststart", str(final))
    return final

def quality(final, cues, slot):
    run("ffmpeg", "-v", "error", "-xerror", "-i", str(final), "-f", "null", "-")
    report = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams",
                                                "-show_format", "-of", "json", str(final)]))
    video = next(x for x in report["streams"] if x["codec_type"] == "video")
    audio = next(x for x in report["streams"] if x["codec_type"] == "audio")
    duration = float(report["format"]["duration"])
    assert (video["width"], video["height"], video["r_frame_rate"]) == (1080, 1920, "30/1")
    assert 25 <= duration <= 60 and abs(float(audio["duration"]) - duration) < .2
    sheet = Image.new("RGB", (810, 960), "#10192b")
    for i, time in enumerate([2.1, cues[1]+4.0, cues[2]+4.0, cues[3]+3.0, cues[4]+2.4, duration-.8]):
        data = subprocess.check_output(["ffmpeg", "-v", "error", "-ss", str(time), "-i", str(final),
                                       "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"])
        im = Image.open(io.BytesIO(data))
        if i == 0:
            im.save(OUT / "cover.jpg", quality=94)
        sheet.paste(im.resize((270, 480)), ((i % 3) * 270, (i // 3) * 480))
    sheet.save(OUT / "contact.jpg", quality=94)
    summary = {"seconds": duration, "resolution": "1080x1920", "fps": FPS, "voice": "hi-in-concierge-10",
               "narration_key_slot": slot, "source": SOURCE, "website": "https://postaledge.in",
               "background_sources": "Three newly generated custom postal scenes", "website_course_cards": True,
               "characters": "Approved Postal Edge Golu and Dakia Bhaiya", "scope": "Preview"}
    (OUT / "report.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary), flush=True)

def main():
    OUT.mkdir(exist_ok=True)
    source_cards()
    keys = [(i, os.environ[f"POSTAL_KEY_{i}"]) for i in range(1, 5) if os.getenv(f"POSTAL_KEY_{i}")]
    if not keys:
        raise RuntimeError("No configured Bakra News Gemini keys available to this run")
    print("Configured Gemini slots:", [i for i, _ in keys], flush=True)
    for index in range(3):
        shutil.copyfile(HERE / f"art{index}.jpg", OUT / f"bg{index}.jpg")
    scenes, rate, slot = narration(keys)
    cues, duration, samples = audio_track(scenes, rate)
    rigs(cues, duration, samples)
    website = HERE.parent / "postal_recruitment_website_outro" / "website-courses.jpg"
    shutil.copyfile(website, OUT / "website.jpg")
    final = render(cues, duration)
    quality(final, cues, slot)

if __name__ == "__main__":
    main()
