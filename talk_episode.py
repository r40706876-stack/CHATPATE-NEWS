"""
पूरी episode: कई किरदार, हर line अलग GitHub job में (एक साथ) SadTalker से हिलता चेहरा → जोड़कर पुराना TV look.
    python talk_episode.py prep episodes/x.json   → st_in/<i>/source.png + talk.wav, st_in/audio/NN.wav, st_in/lines.json
    python talk_episode.py post                   → episode.mp4 (+ preview_episode.jpg, Telegram)
"""
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import talk_test as tt

ROOT = Path(__file__).parent
IN, OUT = ROOT / "st_in", ROOT / "st_out"
W, H, FPS = 1080, 1920, 25
TV_X, TV_Y = 60, 250
CHARS = {   # किरदार: (तस्वीर, नाम, पद) — सब काल्पनिक AI किरदार
    "bablu": ("assets/real/bablu.png", "बबलू", "गाँव संवाददाता • सीधे खेत से"),
    "chacha": ("assets/real/chacha.png", "चाचा", "वरिष्ठ विशेषज्ञ • 1975 से नाराज़"),
    "dadi": ("assets/real/dadi.png", "दादी", "तकनीकी सलाहकार • WhatsApp विभाग"),
    "pinky": ("assets/real/pinky.png", "पिंकी", "नई पीढ़ी • अभी-अभी 18 की"),
    "ramesh": ("assets/real/ramesh.png", "रमेश", "आम आदमी • रोज़ का परेशान"),
}


_cut = {}


EXPRS = ("hasi", "hairan", "gussa", "tanz")       # assets/real/<who>_<expr>.png हो तो वही भाव वाली फ़ोटो


def source_img(who, path, expr=""):
    """किरदार की फ़ोटो 960x1280 (line के भाव वाली, अगर है); assets/bg/<who>.jpg हो तो गाँव वाली पृष्ठभूमि."""
    ep = ROOT / f"assets/real/{who}_{expr}.png"
    im = Image.open(ep if expr and ep.exists() else ROOT / CHARS[who][0]).convert("RGB")
    s = max(960 / im.width, 1280 / im.height)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    x0, y0 = (im.width - 960) // 2, int((im.height - 1280) * 0.25)
    im = im.crop((x0, y0, x0 + 960, y0 + 1280))
    bgp = ROOT / f"assets/bg/{who}.jpg"
    if bgp.exists():
        try:
            if (who, expr) not in _cut:
                from rembg import new_session, remove
                _cut[(who, expr)] = remove(im, session=new_session("u2net_human_seg"))
            bg = Image.open(bgp).convert("RGB")
            k = max(960 / bg.width, 1280 / bg.height)
            bg = bg.resize((int(bg.width * k), int(bg.height * k)), Image.LANCZOS)
            bx, by = (bg.width - 960) // 2, (bg.height - 1280) // 2
            from PIL import ImageEnhance, ImageFilter
            bg = ImageEnhance.Brightness(bg.crop((bx, by, bx + 960, by + 1280)).filter(ImageFilter.GaussianBlur(5))).enhance(0.9)
            bg.paste(_cut[(who, expr)], (0, 0), _cut[(who, expr)])
            im = bg
        except Exception as e:                            # noqa: BLE001
            print("  पृष्ठभूमि नहीं बदली:", who, e)
    im.save(path)


def tighten(wav):
    """शुरू/आख़िर की चुप्पी हटाओ + थोड़ा तेज़ (reel की रफ़्तार)."""
    tmp = wav.with_suffix(".t.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-af",
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,atempo=1.1,apad=pad_dur=0.15",
                    str(tmp)], check=True)
    tmp.replace(wav)


def prep(script_path):
    ep = json.load(open(ROOT / script_path, encoding="utf-8"))
    import tts
    tts.speak_script(ep, IN / "audio")
    for i in range(len(ep["lines"])):
        tighten(IN / f"audio/{i:02d}.wav")
    for i, ln in enumerate(ep["lines"]):
        d = IN / str(i)
        d.mkdir(parents=True, exist_ok=True)
        sprite = (ep.get("sprite") or {}).get(ln["who"])
        if sprite:                                             # 3D किरदार: नीले studio में, line के भाव वाली फ़ोटो
            import reel_studio
            st = ln.get("set") or ("studio" if ln["who"] == "bablu" else "village")
            reel_studio.source_for(sprite, ln.get("expr", ""), d / "source.png", d / "still.png", st)
            rp = ln.get("react_pose")
            if rp:
                reel_studio.source_for(sprite, rp, IN / f"react_{i}_small.png", IN / f"react_{i}.png", st)
        else:
            source_img(ln["who"], d / "source.png", ln.get("expr", ""))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(IN / f"audio/{i:02d}.wav"), "-ar", "16000",
                        "-ac", "1", str(d / "talk.wav")], check=True)
    pairs = []                                                 # हर line के 1-2 visual (खोज), सब एक साथ जाँचे जाएँ
    for i, ln in enumerate(ep["lines"]):
        qs = ln.get("visuals") or ([ln["visual"]] if ln.get("visual") else [])
        pairs += [(i, j, q) for j, q in enumerate(qs[:2]) if not ln.get("punch")]
    if pairs:
        import shutil
        import visuals
        (IN / "broll").mkdir(exist_ok=True)
        got = visuals.pick_checked([(ep["lines"][i]["say"], q) for i, _, q in pairs])
        for (i, j, _), path in zip(pairs, got):
            if path:
                shutil.copy(path, IN / f"broll/{i}_{j}{Path(path).suffix}")
    json.dump(ep, open(IN / "episode.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(json.dumps(list(range(len(ep["lines"])))))


def _secs(p):
    with wave.open(str(p)) as w:
        return w.getnframes() / w.getframerate()


def _frames(video):
    rd = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", str(video), "-vf",
                           f"fps={FPS},scale=960:1280:force_original_aspect_ratio=increase,crop=960:1280",
                           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    while True:
        raw = rd.stdout.read(960 * 1280 * 3)
        if len(raw) < 960 * 1280 * 3:
            return
        yield Image.frombuffer("RGB", (960, 1280), raw)


def _wrap(text, f, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if f.getlength(t) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + [cur] if cur else lines


RED, YEL = (220, 30, 40), (255, 214, 0)
VH = 1440                                                   # ऊपर का video हिस्सा 1080x1440, नीचे caption


def _cover(path, w, h):
    rd = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-stream_loop", "-1", "-i", str(path), "-vf",
                           f"fps={FPS},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}",
                           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    while True:
        raw = rd.stdout.read(w * h * 3)
        if len(raw) < w * h * 3:
            return
        yield Image.frombuffer("RGB", (w, h), raw)


def _kenburns(path, w, h, n):
    im = Image.open(path).convert("RGB")
    k = max(w / im.width, h / im.height) * 1.15
    im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    for t in range(n):
        z = 1 + 0.12 * (1 - t / max(1, n))                    # धीरे-धीरे zoom out
        cw, ch = w * 1.15 / z, h * 1.15 / z
        x0, y0 = (im.width - cw) / 2, (im.height - ch) / 2
        yield im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((w, h), Image.BILINEAR)


def chrome(ep, ln, k, total, broll):
    """ऊपर-नीचे की पट्टियाँ (RGBA, पूरे frame की)."""
    o = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(o)
    d.rounded_rectangle((36, 40, 330, 104), 14, fill=RED + (255,))
    d.text((183, 72), "बकरा न्यूज़", font=tt.font(40), fill="white", anchor="mm")
    d.rounded_rectangle((346, 48, 470, 96), 12, fill=(0, 0, 0, 170))
    d.ellipse((362, 64, 378, 80), fill=RED + (255,))
    d.text((424, 72), "LIVE", font=tt.font(28), fill="white", anchor="mm")
    d.text((W - 36, 72), "AI किरदार", font=tt.font(26), fill=(255, 255, 255, 200), anchor="rm")
    if k < FPS * 3 and ep.get("hook"):                          # पहले 3 सेकंड: hook
        rows = _wrap(ep["hook"], tt.font(64), 960)[:3]
        y0 = 190
        d.rounded_rectangle((30, y0 - 20, W - 30, y0 + 80 * len(rows) + 4), 22, fill=(0, 0, 0, 175))
        for r, t in enumerate(rows):
            d.text((W / 2, y0 + 40 + r * 80), t, font=tt.font(64), fill=YEL, anchor="mm")
    _, name, role = CHARS[ln["who"]]
    if broll:                                                    # b-roll पर: खबर वाली पट्टी
        d.rectangle((0, VH - 150, W, VH - 90), fill=RED + (240,))
        d.text((40, VH - 120), "मुख्य खबर", font=tt.font(36), fill="white", anchor="lm")
    else:                                                        # किरदार पर: नाम-पट्टी
        d.rectangle((0, VH - 170, 520, VH - 105), fill=RED + (245,))
        d.text((36, VH - 138), name, font=tt.font(46), fill="white", anchor="lm")
        d.rectangle((0, VH - 105, 640, VH - 55), fill=(255, 255, 255, 240))
        d.text((36, VH - 80), role, font=tt.font(30), fill=(20, 20, 20), anchor="lm")
    cap = ln.get("caption") or ln["say"]
    rows = _wrap(cap, tt.font(58), 980)[:4]
    yc = VH + (H - VH - 40) / 2 - (len(rows) - 1) * 40
    for r, t in enumerate(rows):
        d.text((W / 2, yc + r * 80), t, font=tt.font(58), fill="white" if r % 2 == 0 else YEL, anchor="mm",
               stroke_width=3, stroke_fill="black")
    d.rectangle((0, H - 14, int(W * k / total), H), fill=YEL + (255,))
    return o


def post_studio(ep):
    import reel_studio
    segs = []
    for i, ln in enumerate(ep["lines"]):
        clips = sorted((OUT / str(i)).rglob("*.mp4"))
        still = Image.open(IN / f"{i}/still.png").convert("RGB")
        vis = sorted((IN / "broll").glob(f"{i}_*")) if (IN / "broll").exists() else []
        mp = IN / f"{i}/still_mask.png"
        segs.append({"ln": ln, "wav": IN / f"audio/{i:02d}.wav", "face": clips[-1] if clips else None,
                     "still": still, "vis": vis, "mask": Image.open(mp).convert("L") if mp.exists() else None})
        if (IN / f"react_{i}.png").exists():
            rw = IN / f"audio/{i:02d}_r.wav"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                            "-t", "1.3", "-c:a", "pcm_s16le", str(rw)], check=True)
            segs.append({"ln": {"who": ln["who"], "say": ""}, "wav": rw, "face": None, "react": True,
                         "still": Image.open(IN / f"react_{i}.png").convert("RGB"), "vis": []})
    out = ROOT / "episode.mp4"
    secs = reel_studio.render(ep, segs, CHARS, out, ROOT / "preview_episode.jpg")
    print(f"बन गया: {out} ({secs:.1f}s)")
    import telegram
    telegram.send_video(out, f"🎬 3D demo (बिना retro): {ep.get('title', '')} — होंठ आवाज़ के साथ, हर line पर भाव")


def post():
    import reel_v3
    ep = json.load(open(IN / "episode.json", encoding="utf-8"))
    if ep.get("sprite"):
        return post_studio(ep)
    n = len(ep["lines"])
    audio = [IN / f"audio/{i:02d}.wav" for i in range(n)]
    lens = [_secs(a) for a in audio]
    faces, stills, vis = [], [], []
    for i in range(n):
        clips = sorted((OUT / str(i)).rglob("*.mp4"))
        faces.append(_frames(clips[-1]) if clips else None)
        stills.append(Image.open(IN / f"{i}/source.png").convert("RGB"))
        vis.append(sorted((IN / "broll").glob(f"{i}_*")) if (IN / "broll").exists() else [])
    out = ROOT / "episode.mp4"
    secs = reel_v3.render(ep, lens, faces, stills, vis, CHARS, out, ROOT / "preview_episode.jpg", audio)
    print(f"बन गया: {out} ({secs:.1f}s)")
    import telegram
    telegram.send_video(out, f"🎬 v3 test: {ep.get('title', '')} — हर 2-3 सेकंड नया नज़ारा, poll के साथ")


_cc = {}


def chrome_cache(ep, ln, k, total, broll):
    key = (id(ln), k < FPS * 3, broll, k * 100 // max(1, total))
    if key not in _cc:
        _cc.clear()
        _cc[key] = chrome(ep, ln, k, total, broll)
    return _cc[key]


def _ring():
    m = Image.new("L", (312, 312), 0)
    ImageDraw.Draw(m).ellipse((0, 0, 311, 311), fill=255)
    return m


if __name__ == "__main__":
    prep(sys.argv[2]) if sys.argv[1] == "prep" else post()
