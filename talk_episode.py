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


def source_img(who, path):
    im = Image.open(ROOT / CHARS[who][0]).convert("RGB")
    s = max(960 / im.width, 1280 / im.height)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    x0, y0 = (im.width - 960) // 2, int((im.height - 1280) * 0.25)
    im.crop((x0, y0, x0 + 960, y0 + 1280)).save(path)


def prep(script_path):
    ep = json.load(open(ROOT / script_path, encoding="utf-8"))
    import tts
    tts.speak_script(ep, IN / "audio")
    for i, ln in enumerate(ep["lines"]):
        d = IN / str(i)
        d.mkdir(parents=True, exist_ok=True)
        source_img(ln["who"], d / "source.png")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(IN / f"audio/{i:02d}.wav"), "-ar", "16000",
                        "-ac", "1", str(d / "talk.wav")], check=True)
    want = [(i, ln) for i, ln in enumerate(ep["lines"]) if ln.get("visual")]
    if want:                                                   # b-roll: सिर्फ़ जाँचा हुआ, मेल वाला clip
        import shutil
        import visuals
        (IN / "broll").mkdir(exist_ok=True)
        for (i, ln), path in zip(want, visuals.pick_checked([(ln["say"], ln["visual"]) for _, ln in want])):
            if path:
                shutil.copy(path, IN / f"broll/{i}.mp4")
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


def post():
    ep = json.load(open(IN / "episode.json", encoding="utf-8"))
    n = len(ep["lines"])
    lens = [_secs(IN / f"audio/{i:02d}.wav") for i in range(n)]
    counts = [max(1, round(s * FPS)) for s in lens]
    total = sum(counts)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *sum([["-i", str(IN / f"audio/{i:02d}.wav")] for i in range(n)], []),
                    "-filter_complex", "".join(f"[{i}:a]" for i in range(n)) + f"concat=n={n}:v=0:a=1[a]",
                    "-map", "[a]", str(IN / "all.wav")], check=True)
    out = ROOT / "episode.mp4"
    wr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", str(IN / "all.wav"), "-c:v", "libx264", "-crf", "20",
                           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", str(out)],
                          stdin=subprocess.PIPE)
    mask = Image.new("L", (300, 300), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 299, 299), fill=255)
    k = 0
    for i, ln in enumerate(ep["lines"]):
        clips = sorted((OUT / str(i)).rglob("*.mp4"))
        face = _frames(clips[-1]) if clips else iter(())
        still = Image.open(IN / f"{i}/source.png").convert("RGB")
        br = IN / f"broll/{i}.mp4"
        bg = _cover(br, W, VH) if br.exists() else None
        last = None
        for _ in range(counts[i]):
            fr = next(face, None) or last or still
            last = fr
            f = Image.new("RGB", (W, H), (12, 12, 16))
            if bg is not None:
                f.paste(next(bg, None) or Image.new("RGB", (W, VH), (0, 0, 0)), (0, 0))
                pip = fr.resize((300, 400)).crop((0, 30, 300, 330))
                f.paste((255, 255, 255), (W - 346, VH - 456, W - 34, VH - 144), _ring())
                f.paste(pip, (W - 340, VH - 450), mask)
            else:                                                # editor वाली हरकत: हर line पर wide/close बदलो + धीमा zoom
                z = (1.0 if i % 2 == 0 else 1.14) + 0.04 * (_ / max(1, counts[i]))
                cw, ch = 960 / z, 1280 / z
                x0, y0 = (960 - cw) / 2, (1280 - ch) * 0.3
                f.paste(fr.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, VH), Image.LANCZOS), (0, 0))
            c = chrome_cache(ep, ln, k, total, bg is not None)
            f.paste(c, (0, 0), c)
            wr.stdin.write(f.tobytes())
            k += 1
    wr.stdin.close()
    wr.wait()
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(out), "-vf",
                    f"fps={10 / max(1, total / FPS)},scale=270:-1,tile=5x2", "-frames:v", "1",
                    str(ROOT / "preview_episode.jpg")])
    print(f"बन गया: {out} ({total / FPS:.1f}s)")
    import telegram
    telegram.send_video(out, f"🎬 नया (आज का) look test: {ep.get('title', '')} — {n} lines")


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
