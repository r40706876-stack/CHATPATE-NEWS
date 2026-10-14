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


def strap(who):
    _, name, role = CHARS[who]
    tv = Image.new("RGBA", (960, 1280), (0, 0, 0, 0))
    d = ImageDraw.Draw(tv)
    d.rectangle((640, 50, 920, 230), fill=(12, 16, 40, 230), outline=(200, 170, 90), width=3)
    d.ellipse((700, 70, 860, 210), outline=(110, 150, 200), width=4)
    d.ellipse((730, 90, 830, 190), fill=(40, 80, 130))
    d.text((780, 140), "बकरा न्यूज़", font=tt.font(40), fill=(245, 225, 160), anchor="mm", stroke_width=3,
           stroke_fill=(0, 0, 0))
    d.rectangle((40, 1060, 600, 1200), fill=(10, 10, 14, 235), outline=(200, 170, 90), width=3)
    d.text((70, 1105), name, font=tt.font(56), fill=(245, 225, 160), anchor="lm")
    d.text((70, 1165), role, font=tt.font(30), fill=(220, 210, 190), anchor="lm")
    return tv


def frame_bg(ep, ln, k, total):
    f = Image.new("RGB", (W, H), (8, 8, 10))
    d = ImageDraw.Draw(f)
    if k < FPS * 3 and ep.get("hook"):                              # पहले 3 सेकंड: hook बड़ा
        for j, t in enumerate(_wrap(ep["hook"], tt.font(54), 980)[:2]):
            d.text((W / 2, 95 + j * 72), t, font=tt.font(54), fill=(255, 214, 0), anchor="mm", stroke_width=3,
                   stroke_fill=(0, 0, 0))
    else:
        d.text((W / 2, 90), "बकरा न्यूज़", font=tt.font(52), fill=(235, 215, 150), anchor="mm")
        d.text((W / 2, 160), "खबर सौ टका पक्की, अंदाज़ अधपका!", font=tt.font(34), fill=(200, 190, 170), anchor="mm")
    cap = ln.get("caption") or ln["say"]
    for j, t in enumerate(_wrap(cap, tt.font(50), 960)[:3]):
        d.text((W / 2, 1610 + j * 70), t, font=tt.font(50), fill=(255, 255, 255), anchor="mm", stroke_width=4,
               stroke_fill=(0, 0, 0))
    d.text((W - 40, H - 40), "AI किरदार • काल्पनिक", font=tt.font(24), fill=(120, 120, 120), anchor="rs")
    d.rectangle((0, H - 12, int(W * k / total), H), fill=(255, 214, 0))
    return f


def post():
    ep = json.load(open(IN / "episode.json", encoding="utf-8"))
    lens = [_secs(IN / f"audio/{i:02d}.wav") for i in range(len(ep["lines"]))]
    counts = [max(1, round(s * FPS)) for s in lens]
    total = sum(counts)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *sum([["-i", str(IN / f"audio/{i:02d}.wav")]
                    for i in range(len(lens))], []), "-filter_complex",
                    "".join(f"[{i}:a]" for i in range(len(lens))) + f"concat=n={len(lens)}:v=0:a=1[a]",
                    "-map", "[a]", str(IN / "all.wav")], check=True)
    out = ROOT / "episode.mp4"
    wr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", str(IN / "all.wav"), "-c:v", "libx264", "-crf", "20",
                           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", str(out)],
                          stdin=subprocess.PIPE)
    _, vign = tt.overlays("", "")
    rng = np.random.default_rng(1)
    k = 0
    for i, ln in enumerate(ep["lines"]):
        clips = sorted((OUT / str(i)).rglob("*.mp4"))
        over = strap(ln["who"])
        last = None
        src = _frames(clips[-1]) if clips else iter(())
        for _ in range(counts[i]):
            fr = next(src, None) or last or Image.open(IN / f"{i}/source.png").convert("RGB")
            last = fr
            tv = fr.convert("RGBA")
            tv.alpha_composite(over)
            tv = tt.vhs(tv.convert("RGB"), k, rng)
            tv = Image.composite(tv, Image.new("RGB", tv.size, (0, 0, 0)), vign)
            f = frame_bg(ep, ln, k, total)
            f.paste(tv, (TV_X, TV_Y))
            wr.stdin.write(f.tobytes())
            k += 1
    wr.stdin.close()
    wr.wait()
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(out), "-vf",
                    f"fps={10 / max(1, total / FPS)},scale=270:-1,tile=5x2", "-frames:v", "1",
                    str(ROOT / "preview_episode.jpg")])
    print(f"बन गया: {out} ({total / FPS:.1f}s)")
    import telegram
    telegram.send_video(out, f"🎬 पूरी episode test: {ep.get('title', '')} — {len(lens)} lines, AI हिलते चेहरे")


if __name__ == "__main__":
    prep(sys.argv[2]) if sys.argv[1] == "prep" else post()
