"""
बकरा न्यूज़ — असली visuals वाला format (कार्टून नहीं):
  पीछे खबर से जुड़ा असली video/photo (Pixabay), पहले ही frame पर बड़ा hook, बबलू की आवाज़ + चलते captions,
  तथ्य वाले cards, चाचा/पिंकी/दादी की lines chat-bubble बनकर उछलती हैं (अपनी-अपनी आवाज़ में), ऊपर progress bar.
"""
import json
import math
import re
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.io import wavfile

import render_reel as rr
import visuals

ROOT = Path(__file__).parent
AUDIO = ROOT / "audio"
W, H, FPS = rr.W, rr.H, rr.FPS
font = rr.font
WHO = {"chacha": ("चाचा जी", (230, 120, 20), "left"), "pinky": ("पिंकी", (225, 50, 130), "right"),
       "dadi": ("दादी", (120, 70, 190), "left"), "bablu": ("बबलू", (200, 20, 40), "right")}


# ------------------------------------------------------------------ पीछे के visuals
class VideoBG:
    def __init__(self, path, dur):
        self.n, self.last = 0, None
        self.p = subprocess.Popen(
            ["ffmpeg", "-loglevel", "error", "-stream_loop", "-1", "-i", str(path), "-t", f"{dur + 1:.2f}",
             "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},eq=saturation=1.15",
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)

    def frame(self, k):
        while self.n <= k:
            raw = self.p.stdout.read(W * H * 3)
            if len(raw) < W * H * 3:
                break
            self.last = Image.frombuffer("RGB", (W, H), raw)
            self.n += 1
        return self.last.copy() if self.last else Image.new("RGB", (W, H), (20, 24, 40))

    def close(self):
        try:
            self.p.kill()
        except Exception:                                  # noqa: BLE001
            pass


class ImageBG:
    """photo पर धीमा zoom (Ken Burns)."""
    def __init__(self, path, dur):
        im = Image.open(path).convert("RGB")
        s = max(W * 1.15 / im.width, H * 1.15 / im.height)
        self.im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        self.frames = max(1, int(dur * FPS))

    def frame(self, k):
        zf = 1.0 + 0.12 * min(1, k / self.frames)          # धीरे-धीरे अंदर zoom
        cw = min(self.im.width, self.im.height * W / H) / zf
        ch = cw * H / W
        x0, y0 = (self.im.width - cw) / 2, (self.im.height - ch) / 2
        return self.im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BILINEAR)

    def close(self):
        pass


class PlainBG:
    def __init__(self, *_):
        self.im = rr.gradient((18, 32, 78), (8, 12, 30)).resize((W, H))

    def frame(self, k):
        return self.im.copy()

    def close(self):
        pass


def make_bg(query, dur):
    got = visuals.fetch(query)
    try:
        if got and got[0] == "video":
            return VideoBG(got[1], dur)
        if got and got[0] == "image":
            return ImageBG(got[1], dur)
    except Exception as e:                                # noqa: BLE001
        print("  visual नहीं खुला:", e)
    return PlainBG()


# ------------------------------------------------------------------ ऊपर की परतें
def shade():
    """ऊपर-नीचे गहरी परछाई ताकि text हर photo पर पढ़ा जाए."""
    a = np.zeros((H, W), np.float32)
    y = np.arange(H)[:, None]
    a += np.clip(1 - y / 420, 0, 1) * 190
    a += np.clip((y - 1050) / 870, 0, 1) * 225
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    img.putalpha(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
    return img


def brand(label, headline):
    img = Image.new("RGBA", (W, 330), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((30, 40, 640, 140), 26, fill=(10, 12, 24, 215))
    d.rounded_rectangle((44, 52, 120, 128), 16, fill=(210, 30, 45))
    d.text((82, 90), "ब", font=font(52), fill="white", anchor="mm")
    d.text((138, 72), "बकरा न्यूज़", font=font(46), fill="white", anchor="lm")
    d.text((140, 118), rr.TAGLINE, font=font(26, False), fill=(255, 210, 120), anchor="lm")
    d.rounded_rectangle((880, 62, 1050, 116), 12, fill=(210, 30, 45))
    d.text((978, 89), "LIVE", font=font(32), fill="white", anchor="mm")
    if headline:
        fl = font(34)
        lw = d.textlength(label, font=fl)
        d.rounded_rectangle((30, 170, 54 + lw, 222), 10, fill=(255, 205, 40))
        d.text((42 + lw / 2, 196), label, font=fl, fill=(150, 0, 20), anchor="mm")
        f = font(44)
        while d.textlength(headline, font=f) > W - 80 and f.size > 28:
            f = font(f.size - 2)
        d.text((32, 268), headline, font=f, fill="white", anchor="lm", stroke_width=5, stroke_fill=(0, 0, 0))
    return img


_bub = {}


def bubble(who, text, age):
    """chat-bubble: नाम की पट्टी + सफ़ेद बादल, बगल से फिसलकर आए."""
    key = (who, text)
    if key not in _bub:
        name, col, side = WHO.get(who, (who, (60, 60, 90), "left"))
        f = font(58)
        d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        lines = rr._wrap(d0, text, f, 820)[:6]
        bh = 70 * len(lines) + 70
        img = Image.new("RGBA", (W, bh + 110), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        x0, x1 = (50, 980) if side == "left" else (100, 1030)
        d.rounded_rectangle((x0 + 4, 74, x1 + 4, 74 + bh + 4), 40, fill=(0, 0, 0, 90))
        d.rounded_rectangle((x0, 70, x1, 70 + bh), 40, fill=(255, 255, 255, 250))
        tx = x0 + 60 if side == "left" else x1 - 60
        d.polygon([(tx - 25, 70 + bh - 2), (tx + 25, 70 + bh - 2), (tx + (-40 if side == "left" else 40), 70 + bh + 45)],
                  fill=(255, 255, 255, 250))
        nf = font(42)
        nw = d.textlength(name, font=nf)
        nx = x0 + 30 if side == "left" else x1 - 30 - nw - 50
        d.rounded_rectangle((nx, 20, nx + nw + 50, 90), 35, fill=col)
        d.text((nx + 25 + nw / 2, 55), name, font=nf, fill="white", anchor="mm")
        for i, ln in enumerate(lines):
            d.text((x0 + 50, 140 + i * 70), ln, font=f, fill=(25, 25, 35), anchor="lm")
        _bub[key] = (img, side)
    img, side = _bub[key]
    k = min(1.0, age / 0.22)
    k = 1 - (1 - k) ** 3
    dx = int((1 - k) * (-W if side == "left" else W) * 0.6)
    return img, dx


def progress(frame, t, total):
    d = ImageDraw.Draw(frame)
    d.rectangle((0, 0, W, 10), fill=(255, 255, 255, 60) if frame.mode == "RGBA" else (60, 60, 60))
    d.rectangle((0, 0, int(W * min(1, t / total)), 10), fill=(255, 205, 40))


# ------------------------------------------------------------------ मुख्य
def main(path, outname):
    script = json.load(open(ROOT / path, encoding="utf-8"))
    rr.CLEAN = True
    sr = 24000
    lines = script["lines"]
    queries = visuals.plan(lines, script.get("topic", ""))
    cards = [l for l in lines if l.get("card")]
    for n, l in enumerate(cards, 1):
        l["card"].update(_n=n, _N=len(cards), _src=str(script.get("source", ""))[:60])

    clips, timeline, cursor = [(0.0, rr.tone(sr, [523, 784], 0.3, 0.25))], [], 0.3
    for i, line in enumerate(lines):
        _, a = rr.read_wav(AUDIO / f"{i:02d}.wav")
        nz = np.where(np.abs(a) > 0.02)[0]
        a = a[max(0, nz[0] - 600): nz[-1] + 1200] if len(nz) else a
        dur = len(a) / sr
        if i and queries[i] != queries[i - 1]:
            clips.append((max(0, cursor - 0.1), rr.whoosh_sfx(sr) * 0.6))
        timeline.append({**line, "start": cursor, "end": cursor + dur, "audio": a, "q": queries[i]})
        clips.append((cursor, a))
        cursor += dur + (0.42 if (line.get("card") or line["who"] != "bablu") else 0.2)
    poll = rr.get_poll(script)
    total = cursor + (2.8 if poll else 1.8)
    mix = np.zeros(int(total * sr) + sr, np.float32)
    for st, a in clips:
        s0 = int(st * sr)
        mix[s0: s0 + len(a)] += a
    mix += rr.bed_music(sr, len(mix) / sr)[: len(mix)] * 0.7
    mix = np.clip(mix / max(1, np.abs(mix).max() / 0.95), -1, 1)
    wavfile.write(ROOT / "mix.wav", sr, (mix * 32767).astype(np.int16))

    # visual के हिस्से: लगातार एक जैसे query वाली lines एक ही clip पर
    spans = []
    for seg in timeline:
        if spans and spans[-1]["q"] == seg["q"]:
            spans[-1]["end"] = seg["end"]
        else:
            spans.append({"q": seg["q"], "start": seg["start"] if spans else 0.0, "end": seg["end"]})
    spans[-1]["end"] = total
    for a, b in zip(spans, spans[1:]):
        a["end"] = b["start"]

    top_shade = shade()
    head_on = brand(script.get("label", "BREAKING"), script.get("breaking", ""))
    head_off = brand("", "")
    nframes = int(total * FPS)
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(ROOT / "mix.wav"),
                             "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
                             "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
                             str(ROOT / outname)], stdin=subprocess.PIPE)
    si, bg = -1, None
    for fi in range(nframes):
        t = fi / FPS
        while si + 1 < len(spans) and t >= spans[si + 1]["start"]:
            si += 1
            if bg:
                bg.close()
            sp = spans[si]
            bg = make_bg(sp["q"], sp["end"] - sp["start"])
            sp["f0"] = fi
            print(f"  visual {si + 1}/{len(spans)}: {sp['q']} ({type(bg).__name__})")
        frame = bg.frame(fi - spans[si]["f0"])
        age_span = t - spans[si]["start"]
        if si and age_span < 0.2:                         # नया visual हल्के zoom-झटके से
            z = 1.06 - 0.3 * age_span
            frame = rr.camera(frame, z, W / 2, H / 2)
        frame = frame.convert("RGBA")
        frame.alpha_composite(top_shade)

        past = [s for s in timeline if s["start"] <= t]
        seg = past[-1] if past else timeline[0]
        speaking = seg["start"] <= t < seg["end"]
        hook_on = script.get("hook_text") and t < 2.6
        frame.alpha_composite(head_off if hook_on else head_on)

        if hook_on:                                       # पहले frame से ही बड़ा hook — कोई इंतज़ार नहीं
            img, pos, mask = rr.hook_layer(script["hook_text"], 1.0)
            pulse = 1 + 0.03 * math.sin(t * 9)
            if abs(pulse - 1) > 0.005:
                img = img.resize((int(img.width * pulse), int(img.height * pulse)))
            frame.alpha_composite(img.convert("RGBA"), (W // 2 - img.width // 2, 860 - img.height // 2))

        if seg.get("card") and not hook_on:
            img, pos, _ = rr.card_layer(seg["card"], t - seg["start"])
            frame.alpha_composite(img.convert("RGBA"), (pos[0], pos[1]))

        if seg["who"] != "bablu" and t < seg["end"] + 0.4:
            img, dx = bubble(seg["who"], seg["caption"], t - seg["start"])
            y = 1180 if not seg.get("card") else 1250
            frame.paste(img, (dx, y), img)
        elif speaking and not hook_on:
            chunks = rr.chunk_words(seg["caption"])
            nwords = sum(len(c) for c in chunks)
            prog = (t - seg["start"]) / max(0.01, seg["end"] - seg["start"])
            lens = [len(w) + 2 for c in chunks for w in c]
            cum = np.cumsum(lens) / sum(lens)
            wi = min(int(np.searchsorted(cum, prog)), nwords - 1)
            base = 0
            for c in chunks:
                if wi < base + len(c):
                    cap = rr.caption_layer(c, wi - base)
                    frame.alpha_composite(cap.convert("RGBA"), (0, 1440))
                    break
                base += len(c)

        if t >= timeline[-1]["end"] + 0.2:                # आख़िर: poll / follow
            if poll:
                card = rr.poll_card(poll, t - timeline[-1]["end"] - 0.2)
                frame.alpha_composite(card.convert("RGBA"), (0, 1180))
            d = ImageDraw.Draw(frame)
            d.rounded_rectangle((160, 1730, 920, 1840), 30, fill=(255, 205, 40, 245))
            d.text((W / 2, 1785), "Follow करो • Family group में भेजो", font=font(40), fill=(120, 0, 20), anchor="mm")

        if int(t * 2) % 2:
            ImageDraw.Draw(frame).ellipse((898, 79, 918, 99), fill=(255, 255, 255))
        out = frame.convert("RGB")
        progress(out, t, total)
        proc.stdin.write(out.tobytes())
    if bg:
        bg.close()
    proc.stdin.close()
    proc.wait()
    print(f"बन गया: {outname} ({total:.1f}s, {nframes} frames, {len(spans)} visuals)")
