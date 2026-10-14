"""
तेज़ reel (बिना होंठ हिलाए): हर line पर किरदार की भाव वाली असली जैसी फ़ोटो (assets/expr) — आवाज़ के साथ हल्की धड़कन,
punch के बाद दूसरे किरदार का reaction clip, ऊपर मेल वाले clips/कार्ड, captions, आवाज़ें, poll. एक job, ~3-5 मिनट.
    python make_reel.py episodes/x.json
"""
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image

import talk_episode as te

ROOT = Path(__file__).parent
IN = te.IN
FPS = 25
REACTORS = ("chacha", "dadi", "pinky", "ramesh", "bablu")


def amp_env(wav):
    with wave.open(str(wav)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        sr = w.getframerate()
    hop = sr // FPS
    e = np.array([np.sqrt(np.mean(a[i:i + hop] ** 2)) for i in range(0, max(1, len(a) - hop), hop)])
    return e / (e.max() + 1e-6)


def talking_still(img, env):
    """फ़ोटो + आवाज़ के हिसाब से हल्की धड़कन (बोलते वक़्त ज़रा-सा आगे) + धीमा zoom."""
    for k, a in enumerate(env):
        z = 1 + 0.025 * a + 0.03 * k / max(1, len(env))
        cw, ch = img.width / z, img.height / z
        x0, y0 = (img.width - cw) / 2, (img.height - ch) * 0.35
        yield img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize(img.size, Image.BILINEAR)


def clip_frames(path):
    rd = subprocess.Popen(["ffmpeg", "-loglevel", "quiet", "-i", str(path), "-vf",
                           "fps=25,scale=960:1280:force_original_aspect_ratio=increase,crop=960:1280",
                           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    while True:
        raw = rd.stdout.read(960 * 1280 * 3)
        if len(raw) < 960 * 1280 * 3:
            return
        yield Image.frombuffer("RGB", (960, 1280), raw)


def expr_img(who, expr):
    p = ROOT / f"assets/expr/{who}_{expr}.jpg"
    if expr and p.exists():
        im = Image.open(p).convert("RGB")
        k = max(960 / im.width, 1280 / im.height)
        im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
        x0, y0 = (im.width - 960) // 2, int((im.height - 1280) * 0.25)
        return im.crop((x0, y0, x0 + 960, y0 + 1280))
    return None


def main(script):
    ep = json.load(open(ROOT / script, encoding="utf-8"))
    import tts
    tts.speak_script(ep, IN / "audio")
    lines, audio, faces, stills = [], [], [], []
    used = {l["who"] for l in ep["lines"]}
    for i, ln in enumerate(ep["lines"]):
        wav = IN / f"audio/{i:02d}.wav"
        te.tighten(wav)
        base = IN / f"base_{ln['who']}.png"
        if not base.exists():
            te.source_img(ln["who"], base)
        img = expr_img(ln["who"], ln.get("expr")) or Image.open(base).convert("RGB")
        lines.append(ln), audio.append(wav), stills.append(img), faces.append(talking_still(img, amp_env(wav)))
        if ln.get("punch"):                                     # punch के बाद किसी और का reaction (1.2 सेकंड)
            who = next((r for r in REACTORS if r in used and r != ln["who"] and
                        (ROOT / f"assets/expr/{r}_{ln.get('react', 'hasi')}.mp4").exists()), None)
            if who:
                rw = IN / f"audio/{i:02d}_r.wav"
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                                "-t", "1.2", str(rw)], check=True)
                clip = ROOT / f"assets/expr/{who}_{ln.get('react', 'hasi')}.mp4"
                lines.append({"who": who, "say": "", "caption": " ", "react": True})
                audio.append(rw), stills.append(expr_img(who, ln.get("react", "hasi")) or img), faces.append(clip_frames(clip))
    ep2 = dict(ep, lines=lines)
    pairs = []
    for i, ln in enumerate(lines):
        if ln.get("punch") or ln.get("react"):
            continue
        qs = ln.get("visuals") or ([ln["visual"]] if ln.get("visual") else [])
        pairs += [(i, q) for q in qs[:2]]
    vis = [[] for _ in lines]
    if pairs:
        import visuals
        for (i, _), path in zip(pairs, visuals.pick_checked([(lines[i]["say"], q) for i, q in pairs])):
            if path:
                vis[i].append(Path(path))
    import reel_v3
    out = ROOT / "episode.mp4"
    secs = reel_v3.render(ep2, [te._secs(a) for a in audio], faces, stills, vis, te.CHARS, out,
                          ROOT / "preview_episode.jpg", audio)
    print(f"बन गया: {out} ({secs:.1f}s), clips: {sum(len(v) for v in vis)}")
    import telegram
    telegram.send_video(out, f"🎬 नया तरीका: {ep.get('title', '')} — भाव वाली फ़ोटो + reaction, बिना नकली होंठ")


if __name__ == "__main__":
    main(sys.argv[1])
