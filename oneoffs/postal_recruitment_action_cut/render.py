"""Recut the approved Postal Edge narration as a sequence of distinct shots."""
import importlib.util
import io
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "postal_recruitment_draft"
OUT = ROOT / "recruitment_preview"
CUTS = [0, 2.8, 6.3, 11.45, 15.9, 19.9, 24.833333, 31.766667, 35.5]
FILENAME = "Postal_Edge_GDS_Postman_Action_Cut.mp4"

def run(*args):
    subprocess.run(args, check=True)

def puppets(samples, duration):
    sys.path.insert(0, str(ROOT))
    from postal_edge_lip_shapes import measure_mouth
    from postal_edge_puppet import puppet
    rate = 15
    mouths = measure_mouth(samples, rate, duration)
    folders = [OUT / "golu", OUT / "bhaiya"]
    for folder in folders:
        folder.mkdir(exist_ok=True)
    actions = [("hop", "welcome"), ("open", "right"), ("chin", "left"), ("right", "left"),
               ("chin", "open"), ("hop", "welcome"), ("open", "left"), ("right", "welcome"),
               ("open", "right")]
    idx = 0
    for frame in range(math.ceil(duration * rate)):
        t = frame / rate
        if idx + 1 < len(CUTS) and t >= CUTS[idx + 1]:
            idx += 1
        elapsed = t - CUTS[idx]
        for j, folder in enumerate(folders):
            golu = j == 0
            face = .69 if golu else -.64
            active = golu == (idx < 2)
            lips = mouths[min(frame, len(mouths)-1)] if active else None
            excited = golu and idx in (0, 1, 5)
            step = (.82 if idx in (0, 2, 5, 7) else .26) * math.exp(-elapsed * 2.9)
            hop = .8 * max(0, math.sin(elapsed * 5)) if excited and elapsed < .57 else 0
            mood = ("surprise" if idx == 1 else "happy") if excited or not golu else "think"
            strength = .51 + .45 * (math.sin(elapsed * 2.9 + j) ** 2)
            im = puppet(golu, t, step, face, lips, mood, (strength, actions[idx][j]),
                        face, hop, .13 * math.sin(elapsed * 2.35))
            im.save(folder / f"{frame:04d}.png")

def contact(final, duration):
    sheet = Image.new("RGB", (675, 1200), "#15243d")
    for idx, offset in enumerate([1.4, 4.6, 9.1, 13.1, 18.3, 22.4, 27, 34.1, duration-1.3]):
        raw = subprocess.check_output(["ffmpeg","-v","error","-ss",str(offset),"-i",str(final),
                                       "-frames:v","1","-f","image2pipe","-vcodec","png","-"])
        im = Image.open(io.BytesIO(raw))
        if idx == 1:
            im.save(OUT / "cover.jpg", quality=95)
        sheet.paste(im.resize((225,400)), ((idx%3)*225,(idx//3)*400))
    sheet.save(OUT / "contact.jpg", quality=94)

def main():
    original, salary = map(Path, sys.argv[1:3])
    OUT.mkdir(exist_ok=True)
    spec = importlib.util.spec_from_file_location("approved_reel", BASE / "render.py")
    approved = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(approved)
    approved.source_cards()
    for i in range(6):
        shutil.copyfile(HERE / f"location{i}.jpg", OUT / f"location{i}.jpg")
    shutil.copyfile(salary, OUT / "salary.png")
    shutil.copyfile(BASE.parent / "postal_recruitment_website_outro" / "website-courses.jpg", OUT / "website.jpg")
    duration = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration",
                                                  "-of","csv=p=0",str(original)]))
    assert abs(duration - 40.2) < .07
    raw = subprocess.check_output(["ffmpeg","-v","error","-i",str(original),"-f","f32le","-ac","1","-ar","16000","-"])
    puppets(np.frombuffer(raw, dtype="<f4"), duration)
    html = OUT / "action.html"
    html.write_text((HERE / "scenes.html").read_text().replace("__DATA__", json.dumps({
        "cuts": CUTS, "total": duration,
    })))
    renderer = ROOT / "deep/render_deep.py"
    code = renderer.read_text()
    assert "#cutImg,#estImg" in code
    renderer.write_text(code.replace("#cutImg,#estImg", "#cutImg,#estImg,#golu,#bhaiya,#bg,#salary"))
    silent = OUT / "silent.mp4"
    run(sys.executable, str(renderer), str(html), str(silent))
    final = OUT / FILENAME
    run("ffmpeg","-v","error","-xerror","-y","-i",str(silent),"-i",str(original),
        "-map","0:v:0","-map","1:a:0","-c","copy","-movflags","+faststart",str(final))
    run("ffmpeg","-v","error","-xerror","-i",str(final),"-f","null","-")
    def audio_hash(file):
        return subprocess.check_output(["ffmpeg","-v","error","-i",str(file),"-map","0:a:0",
                                        "-c","copy","-f","hash","-hash","sha256","-"])
    assert audio_hash(original) == audio_hash(final)
    contact(final, duration)
    (OUT / "report.json").write_text(json.dumps({
        "seconds": duration, "shots": CUTS, "locations": 6, "salary_card": "X-class Delhi example",
        "voice": "#18, copied from approved cut without re-synthesis", "scope": "Preview",
    }, indent=2))

if __name__ == "__main__":
    main()
