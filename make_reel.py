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


SPRITE_EXPR = {"hasi": "happy", "gussa": "angry", "udaas": "sad", "hairan": "shock", "tanz": "smug"}


def sprite_frames(folder, expr, env):
    """3D किरदार (assets/<x>/<भाव>_<closed|half|open>.webp): आवाज़ के हिसाब से मुँह खुलता-बंद होता है."""
    folder = ROOT / folder
    e = SPRITE_EXPR.get(expr or "", expr if expr and (folder / f"{expr}_closed.png").exists() else "neutral")
    who = folder.name
    bgp = next((p for p in (folder / "home.jpg", ROOT / f"assets/bg/{who}.jpg") if p.exists()), None)
    bg = Image.open(bgp).convert("RGB") if bgp else Image.new("RGB", (960, 1280), (200, 170, 140))
    k = max(960 / bg.width, 1280 / bg.height)
    bg = bg.resize((int(bg.width * k), int(bg.height * k)))
    bg = bg.crop(((bg.width - 960) // 2, (bg.height - 1280) // 2, (bg.width - 960) // 2 + 960, (bg.height - 1280) // 2 + 1280))
    if bgp and bgp.parent.name == "bg":                              # गाँव वाली पृष्ठभूमि थोड़ी धुंधली (किरदार उभरे)
        from PIL import ImageFilter
        bg = bg.filter(ImageFilter.GaussianBlur(4))
    cache = {}

    def load(m):
        p = folder / f"{e}_{m}.webp"
        if p.exists():
            return Image.open(p).convert("RGBA")
        p = folder / f"{e}_{m}.png"
        if not p.exists():
            p = folder / f"{e}_closed.png"
        cut = IN / f"cut_{who}_{p.stem}.png"                         # स्लेटी पृष्ठभूमि हटाओ (एक बार)
        if not cut.exists():
            from rembg import new_session, remove
            global _SESS
            if "_SESS" not in globals():
                _SESS = new_session("isnet-general-use")
            IN.mkdir(exist_ok=True)
            remove(Image.open(p).convert("RGB"), session=_SESS).save(cut)
        return Image.open(cut).convert("RGBA")

    def pose(m):
        if m not in cache:
            sp = load(m)
            sc = 1250 / sp.height
            sp = sp.resize((int(sp.width * sc), 1250), Image.LANCZOS)
            im = bg.copy()
            im.paste(sp, ((960 - sp.width) // 2, 1280 - 1250 + 60), sp)
            cache[m] = im
        return cache[m]
    for i, a in enumerate(env):
        m = "open" if a > 0.55 else "half" if a > 0.2 else "closed"
        z = 1 + 0.02 * a + 0.03 * i / max(1, len(env))
        im = pose(m)
        cw, ch = 960 / z, 1280 / z
        yield im.crop((int((960 - cw) / 2), int((1280 - ch) * 0.2), int((960 + cw) / 2), int((1280 - ch) * 0.2 + ch))).resize((960, 1280))


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
        if not base.exists() and not (ep.get("sprite") or {}).get(ln["who"]):
            te.source_img(ln["who"], base)
        sprite = (ep.get("sprite") or {}).get(ln["who"])
        if sprite:
            fr = list(sprite_frames(sprite, ln.get("expr"), amp_env(wav)))
            lines.append(ln), audio.append(wav), stills.append(fr[0]), faces.append(iter(fr))
            continue
        img = expr_img(ln["who"], ln.get("expr")) or Image.open(base).convert("RGB")
        lines.append(ln), audio.append(wav), stills.append(img), faces.append(talking_still(img, amp_env(wav)))
        if ln.get("punch"):                                     # punch के बाद किसी और का reaction (1.2 सेकंड)
            who = next((r for r in REACTORS if r in used and r != ln["who"] and
                        (ROOT / f"assets/expr/{r}_{ln.get('react', 'tanz')}.mp4").exists()), None)
            if who:
                rw = IN / f"audio/{i:02d}_r.wav"
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                                "-t", "1.2", str(rw)], check=True)
                clip = ROOT / f"assets/expr/{who}_{ln.get('react', 'tanz')}.mp4"
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
