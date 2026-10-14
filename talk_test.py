"""
B वाला test: एक तस्वीर + आवाज़ → SadTalker (free AI, Apache-2.0) से पूरा हिलता चेहरा → पुराने TV (VHS) वाला रूप.
    python talk_test.py prep IMAGE "बोलने वाली लाइन" who     → st_in/source.png, st_in/talk.wav
    python talk_test.py post st_out/<video>.mp4 "नाम" "पद"   → talk_demo.mp4 (+ preview_talk.jpg, Telegram)
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).parent
FONT = str(ROOT / "fonts/Poppins-Bold.ttf")
W, H, FPS = 1080, 1920, 25


def font(s):
    return ImageFont.truetype(FONT, s, layout_engine=ImageFont.Layout.RAQM)


def prep(img, text, who):
    out = ROOT / "st_in"
    out.mkdir(exist_ok=True)
    raw = Image.open(ROOT / img)
    if raw.mode != "RGBA":                                         # असली फ़ोटो: बस 3:4 में काटो (सिर ऊपर रहे)
        im = raw.convert("RGB")
        s = max(960 / im.width, 1280 / im.height)
        im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        x0 = (im.width - 960) // 2
        y0 = int((im.height - 1280) * 0.25)
        im.crop((x0, y0, x0 + 960, y0 + 1280)).save(out / "source.png")
        im = None
    else:
        im = raw.convert("RGBA")
    if im is None:
        pass
    else:
        _place(im, out)
    import tts
    tts.speak_script({"lines": [{"who": who, "say": text, "caption": text, "expr": "smug"}]}, out / "audio")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out / "audio/00.wav"), "-ar", "16000", "-ac", "1",
                    str(out / "talk.wav")], check=True)
    print("तैयार:", out / "source.png", out / "talk.wav")


def _place(im, out):
    bg = Image.new("RGB", (960, 1280), (176, 160, 140))           # गर्म भूरा-स्लेटी पर्दा
    d = ImageDraw.Draw(bg)
    for x in range(0, 960, 48):                                    # पर्दे की सिलवटें
        d.rectangle((x, 0, x + 22, 1280), fill=(168, 152, 132))
    bg = bg.filter(ImageFilter.GaussianBlur(10))
    bb = im.getbbox() or (0, 0, im.width, im.height)
    im = im.crop(bb)
    s = 2100 / im.height                                          # छाती तक का frame (anchor जैसा)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    bg.paste(im, ((960 - im.width) // 2, 70), im)
    bg.save(out / "source.png")



def vhs(fr, k, rng):
    a = np.asarray(fr).astype(np.float32)
    g = a @ np.array([[0.95, 0.06, 0.02], [0.10, 0.88, 0.05], [0.02, 0.10, 0.80]]).T   # फीका पुराना रंग
    g = g * 0.92 + 14
    g[:, :, 0] = np.roll(g[:, :, 0], 3, axis=1)                    # रंग थोड़ा खिसका (chroma bleed)
    g[:, :, 2] = np.roll(g[:, :, 2], -2, axis=1)
    g[::3, :, :] *= 0.9                                            # scanlines
    g += rng.normal(0, 6, g.shape[:2])[:, :, None]                 # grain
    if k % 97 < 2:                                                 # कभी-कभी tape का झटका
        y = rng.integers(0, g.shape[0] - 30)
        g[y:y + 18] = np.roll(g[y:y + 18], 14, axis=1)
    return Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))


def overlays(name, role):
    tv = Image.new("RGBA", (960, 1280), (0, 0, 0, 0))
    d = ImageDraw.Draw(tv)
    d.rectangle((640, 50, 920, 230), fill=(12, 16, 40, 230), outline=(200, 170, 90), width=3)
    d.ellipse((700, 70, 860, 210), outline=(110, 150, 200), width=4)
    d.ellipse((730, 90, 830, 190), fill=(40, 80, 130))
    d.text((780, 140), "बकरा न्यूज़", font=font(40), fill=(245, 225, 160), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
    d.rectangle((40, 1000, 560, 1150), fill=(10, 10, 14, 235), outline=(200, 170, 90), width=3)
    d.text((70, 1050), name, font=font(58), fill=(245, 225, 160), anchor="lm")
    d.text((70, 1115), role, font=font(32), fill=(220, 210, 190), anchor="lm")
    vign = Image.new("L", (960, 1280), 0)
    ImageDraw.Draw(vign).ellipse((-160, -120, 1120, 1400), fill=255)
    vign = vign.filter(ImageFilter.GaussianBlur(120))
    return tv, vign


def post(video, name, role):
    meta = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                           "-of", "json", video], capture_output=True, text=True).stdout
    vw, vh = [json.loads(meta)["streams"][0][k] for k in ("width", "height")]
    rd = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", video, "-vf", f"fps={FPS},scale=960:1280:force_original_aspect_ratio=increase,crop=960:1280",
                           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    out = ROOT / "talk_demo.mp4"
    wr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", video, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264",
                           "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(out)], stdin=subprocess.PIPE)
    tv_over, vign = overlays(name, role)
    frame_bg = Image.new("RGB", (W, H), (8, 8, 10))
    d = ImageDraw.Draw(frame_bg)
    d.text((W / 2, 150), "बकरा न्यूज़ • पुराने अंदाज़ में", font=font(46), fill=(235, 215, 150), anchor="mm")
    d.text((W / 2, 1800), "खबर सौ टका पक्की, अंदाज़ अधपका!", font=font(40), fill=(200, 190, 170), anchor="mm")
    rng = np.random.default_rng(1)
    k = 0
    while True:
        raw = rd.stdout.read(960 * 1280 * 3)
        if len(raw) < 960 * 1280 * 3:
            break
        tv = Image.frombuffer("RGB", (960, 1280), raw).convert("RGBA")
        tv.alpha_composite(tv_over)
        tv = vhs(tv.convert("RGB"), k, rng)
        tv = Image.composite(tv, Image.new("RGB", tv.size, (0, 0, 0)), vign)
        f = frame_bg.copy()
        f.paste(tv, (60, 300))
        wr.stdin.write(f.tobytes())
        k += 1
    wr.stdin.close()
    wr.wait()
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(out), "-vf", "fps=2,scale=270:-1,tile=5x2",
                    "-frames:v", "1", str(ROOT / "preview_talk.jpg")])
    print(f"बन गया: {out} ({k} frames, स्रोत {vw}x{vh})")
    import telegram
    telegram.send_video(out, f"🧪 B वाला test: {name} — AI से हिलता चेहरा (SadTalker) + पुराना TV look")


if __name__ == "__main__":
    if sys.argv[1] == "prep":
        prep(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "dadi")
    else:
        post(sys.argv[2], sys.argv[3], sys.argv[4])
