"""Render से पहले जाँच (29 Oct, मालिक: "credit बर्बाद हो रहे") — बिना Gemini, बिना SadTalker, बिना GitHub.
वही reel_studio.render, वही shot/cold open/अपने दृश्य; आवाज़ की जगह अंदाज़े की लंबाई (शब्द ÷ 2.5/s),
search वाली फ़ोटो की जगह "📷 <खोज>" वाला card. Render तभी जब ये preview पास हो.

    python preview.py episodes/x.json [out_dir]
      → out_dir/preview.mp4, open.jpg (पहले 5 सेकंड, 4 frame/सेकंड), all.jpg (हर सेकंड)
"""
import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import cold_open
import reel_studio
import talk_episode as te
import talk_test as tt

ROOT = Path(__file__).parent


def fake_wav(path, secs, seed):
    sr = 24000
    t = np.arange(int(sr * secs)) / sr
    rng = np.random.default_rng(seed)
    syl = (np.sin(2 * np.pi * 4.2 * t + rng.uniform(0, 6)) > -0.2).astype(float)     # शब्दांश जैसी लय (होंठ हिलें)
    a = 0.25 * np.sin(2 * np.pi * 170 * t) * syl
    a[: int(sr * 0.12)] = 0
    with wave.open(str(path), "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes((a * 32767).astype(np.int16).tobytes())


def placeholder(path, query):
    im = Image.new("RGB", (1280, 720), (40, 70, 60))
    d = ImageDraw.Draw(im)
    d.text((640, 300), "📷 असली फ़ोटो (खोज):", font=tt.font(44), fill=(200, 230, 210), anchor="mm")
    d.text((640, 400), str(query)[:40], font=tt.font(56), fill="white", anchor="mm")
    im.save(path)


def run(script, out_dir):
    out_dir = Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    (out_dir / "vis").mkdir(parents=True)
    ep = json.load(open(script, encoding="utf-8"))
    cold_open.for_episode(ep, out_dir / "cold")
    segs = []
    for i, ln in enumerate(ep["lines"]):
        shot = te.pick_shot(ep, i, ln)
        ln["shot"] = shot
        vis = []
        for k, vf in enumerate(ln.get("visual_files") or []):
            src = Path(vf) if Path(vf).is_absolute() else ROOT / vf
            dst = out_dir / "vis" / f"{i}_0own{k}{src.suffix}"
            shutil.copy(src, dst)
            vis.append(dst)
        if not vis and ln.get("visuals") and shot != "close":
            dst = out_dir / "vis" / f"{i}_ph.png"
            placeholder(dst, ln["visuals"][0])
            vis.append(dst)
        wav = out_dir / f"{i:02d}.wav"
        fake_wav(wav, len(ln.get("say", "").split()) / 2.5 + 0.4, i)
        sprite = te.sprite_of(ep, ln["who"])
        st = ln.get("set") or ("studio" if ln["who"] == "bablu" else "village")
        still_p = out_dir / f"still_{i}.png"
        reel_studio.source_for(sprite, ln.get("expr", ""), out_dir / f"src_{i}.png", still_p, st,
                               "close" if shot == "close" else "band")
        talk = {"folder": sprite, "expr": ln.get("expr", ""), "wav": wav, "set": st}
        segs.append({"ln": ln, "wav": wav, "face": None, "talk": talk, "still": Image.open(still_p).convert("RGB"),
                     "vis": vis, "shot": shot,
                     "voice": te.voice_only(ep, ln) or (shot == "full" and ln.get("who") in te.MASCOT)})
    out = out_dir / "preview.mp4"
    secs = reel_studio.render(ep, segs, te.CHARS, out, out_dir / "first.jpg")
    for name, vf in (("open.jpg", "trim=0:5,fps=4,scale=270:-1,tile=10x2"), ("all.jpg", "fps=1,scale=180:-1,tile=10x8")):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out), "-vf", vf, "-frames:v", "1",
                        str(out_dir / name)], check=True)
    print(f"preview: {out} ({secs:.1f}s)")
    return out


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "/tmp/bakra_preview")
