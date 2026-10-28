"""
v3 reel: हर 2-3 सेकंड में नज़ारा बदलता है.
  • ऊपर (1080x1000): line से मेल खाता जाँचा हुआ clip/photo — न मिले तो बड़ा "खबर कार्ड" (कभी खाली नहीं)
  • नीचे (1080x920): बोलने वाला किरदार (नाम-पट्टी)          • punch line: पूरा screen किरदार + zoom + धमाका + ठप्पा
  • बीच में बड़े शब्द-दर-शब्द captions (karaoke)            • आवाज़ के साथ whoosh/pop/boom (ख़ुद बनाए, कोई license नहीं)
  • शुरू में झटके वाला hook, आख़िर में poll ("कमेंट में 1 या 2") + follow
"""
import json
import math
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import talk_test as tt

W, H, FPS, SR = 1080, 1920, 25, 24000
TOP, BOT = 1000, 920
RED, YEL, WHITE = (225, 30, 45), (255, 214, 0), (255, 255, 255)
CARD_BG = [((150, 20, 30), (40, 5, 10)), ((20, 60, 140), (5, 15, 45)), ((20, 110, 70), (5, 35, 20)),
           ((120, 60, 10), (35, 15, 0))]
STAMPS = ["गज़ब!", "बवाल!", "सच्ची बात!", "भौकाल!", "हाय राम!"]


# ------------------------------------------------------------------ आवाज़ें (numpy से बनी, free)
def _env(n, a=0.01, r=0.3):
    t = np.linspace(0, 1, n)
    return np.minimum(1, t / max(a, 1e-3)) * np.exp(-t / max(r, 1e-3))


def sfx(kind):
    rng = np.random.default_rng(len(kind))
    if kind == "whoosh":
        n = int(SR * 0.35)
        x = rng.normal(0, 1, n)
        x = np.convolve(x, np.ones(12) / 12, "same")
        return 0.25 * x * np.sin(np.linspace(0, math.pi, n)) ** 2
    if kind == "pop":
        n = int(SR * 0.09)
        t = np.arange(n) / SR
        return 0.35 * np.sin(2 * math.pi * (900 - 4000 * t) * t) * _env(n, 0.05, 0.25)
    if kind == "boom":
        n = int(SR * 0.6)
        t = np.arange(n) / SR
        return 0.6 * np.sin(2 * math.pi * (90 - 60 * t) * t) * _env(n, 0.01, 0.35) + 0.08 * rng.normal(0, 1, n) * _env(n, 0.01, 0.05)
    if kind == "ding":
        n = int(SR * 0.8)
        t = np.arange(n) / SR
        return 0.25 * (np.sin(2 * math.pi * 1320 * t) + 0.5 * np.sin(2 * math.pi * 1980 * t)) * _env(n, 0.005, 0.3)
    if kind == "glitch":                                          # TV glitch: टूटी-टूटी तेज़ आवाज़
        n = int(SR * 0.22)
        x = rng.normal(0, 1, n) * (np.sin(np.arange(n) / SR * 2 * math.pi * 30) > 0)
        return 0.22 * x * _env(n, 0.01, 0.4)
    if kind == "laugh":                                           # हँसी जैसी "हा-हा-हा"
        out = np.zeros(int(SR * 0.9))
        for j in range(5):
            n = int(SR * 0.11)
            t = np.arange(n) / SR
            f = 420 - j * 25
            i0 = int(j * SR * 0.16)
            out[i0:i0 + n] += 0.3 * (np.sin(2 * math.pi * f * t) + 0.5 * np.sin(2 * math.pi * 2 * f * t)) * \
                rng.normal(1, 0.25, n) * _env(n, 0.1, 0.5)
        return out
    if kind == "dhol":                                            # ढोल की दो थाप
        out = np.zeros(int(SR * 0.7))
        for j, (f, a) in enumerate(((95, 0.8), (140, 0.6), (95, 0.9))):
            n = int(SR * 0.22)
            t = np.arange(n) / SR
            i0 = int(j * SR * 0.2)
            out[i0:i0 + n] += a * np.sin(2 * math.pi * f * t * (1 - 0.6 * t)) * np.exp(-t * 16)
        return 0.7 * out
    if kind == "thug":                                            # "Thug life" जैसा भारी bass + ऊँचा ping
        n = int(SR * 0.8)
        t = np.arange(n) / SR
        return 0.5 * np.sin(2 * math.pi * (60 - 20 * t) * t) * np.exp(-t * 4) + \
            0.15 * np.sin(2 * math.pi * 1760 * t) * np.exp(-t * 9)
    if kind == "tick":
        n = int(SR * 0.02)
        return 0.05 * rng.normal(0, 1, n) * _env(n, 0.01, 0.2)
    return np.zeros(1)


def _read(p):
    with wave.open(str(p)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        return a if w.getframerate() == SR else np.interp(np.linspace(0, len(a), int(len(a) * SR / w.getframerate())),
                                                          np.arange(len(a)), a)


def mix_audio(voices, events, tail, out):
    total = sum(len(v) for v in voices) + int(tail * SR)
    mix = np.zeros(total + SR, np.float32)
    pos = 0
    for v in voices:
        mix[pos:pos + len(v)] += v
        pos += len(v)
    for t in np.arange(0, total / SR, 0.5):                      # हल्की "news" टिक-टिक
        s = sfx("tick")
        i = int(t * SR)
        mix[i:i + len(s)] += s
    for t, kind in events:
        s = sfx(kind)
        i = int(t * SR)
        mix[i:i + len(s)] += s[:len(mix) - i]
    mix = np.clip(mix[:total], -1, 1)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


# ------------------------------------------------------------------ चित्र
def _cover_img(im, w, h, z=1.0, fy=0.5):
    k = max(w / im.width, h / im.height) * z
    cw, ch = w / k, h / k
    x0, y0 = (im.width - cw) / 2, (im.height - ch) * fy
    return im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((w, h), Image.BILINEAR)


def _video_frames(path, w, h):
    rd = subprocess.Popen(["ffmpeg", "-loglevel", "quiet", "-stream_loop", "-1", "-i", str(path), "-vf",
                           f"fps={FPS},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}",
                           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    try:
        while True:
            raw = rd.stdout.read(w * h * 3)
            if len(raw) < w * h * 3:
                return
            yield Image.frombuffer("RGB", (w, h), raw)
    finally:
        rd.kill()


def visual_frames(src, n, seed):
    """ऊपर वाले हिस्से के n frames: video / photo (Ken Burns) / कार्ड."""
    if isinstance(src, Path) and src.suffix == ".mp4":
        g = _video_frames(src, W, TOP)
        last = None
        for _ in range(n):
            last = next(g, None) or last or Image.new("RGB", (W, TOP))
            yield last
        g.close()
        return
    if isinstance(src, Path):
        im = Image.open(src).convert("RGB")
        for t in range(n):
            z = 1.18 - 0.16 * t / max(1, n) if seed % 2 else 1.02 + 0.16 * t / max(1, n)
            yield _cover_img(im, W, TOP, z)
        return
    card = src or {}
    for t in range(n):
        yield card_frame(card, t, seed)


def _grad(c1, c2, w, h):
    a = np.linspace(0, 1, h)[:, None, None]
    g = np.array(c1)[None, None] * (1 - a) + np.array(c2)[None, None] * a
    return Image.fromarray(np.repeat(g, w, axis=1).astype(np.uint8))


_grads = {}


def card_frame(card, t, seed):
    key = seed % len(CARD_BG)
    if key not in _grads:
        _grads[key] = _grad(*CARD_BG[key], W, TOP)
    im = _grads[key].copy()
    d = ImageDraw.Draw(im)
    for x in range(-TOP, W, 70):                                   # चलती धारियाँ
        o = (t * 4) % 70
        d.line((x + o, 0, x + o + TOP, TOP), fill=tuple(min(255, c + 14) for c in CARD_BG[key][1]), width=18)
    big, sub = card.get("big", ""), card.get("sub", "")
    p = min(1, t / 6)                                              # pop-in
    s = 0.6 + 0.4 * (1 - (1 - p) ** 3) + (0.06 * math.sin(min(t, 12) / 12 * math.pi) if t < 12 else 0)
    f = tt.font(int(108 * s))
    rows = _wrap(big, f, 960)[:3]
    y = TOP / 2 - (len(rows) - 1) * 62 - (40 if sub else 0)
    for r, txt in enumerate(rows):
        d.text((W / 2, y + r * 124), txt, font=f, fill=YEL if r == 0 else WHITE, anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))
    if sub and t > 8:
        d.rounded_rectangle((90, TOP / 2 + len(rows) * 62 + 10, W - 90, TOP / 2 + len(rows) * 62 + 100), 20, fill=(255, 255, 255))
        d.text((W / 2, TOP / 2 + len(rows) * 62 + 55), sub, font=tt.font(46), fill=(20, 20, 20), anchor="mm")
    return im


def _wrap(text, f, width):
    out, cur = [], ""
    for w in str(text).split():
        t = (cur + " " + w).strip()
        if f.getlength(t) <= width or not cur:
            cur = t
        else:
            out.append(cur)
            cur = w
    return out + ([cur] if cur else [])


def face_frame(fr, w, h, z, fy=0.22):
    return _cover_img(fr, w, h, z, fy)


# ------------------------------------------------------------------ पट्टियाँ
def chrome(d, k):
    d.rounded_rectangle((30, 34, 316, 98), 14, fill=RED)
    d.text((173, 66), "बकरा न्यूज़", font=tt.font(40), fill=WHITE, anchor="mm")
    on = (k // 12) % 2 == 0
    d.rounded_rectangle((330, 42, 450, 90), 12, fill=(0, 0, 0))
    d.ellipse((344, 58, 360, 74), fill=RED if on else (90, 0, 0))
    d.text((405, 66), "LIVE", font=tt.font(28), fill=WHITE, anchor="mm")
    d.rounded_rectangle((W - 196, 42, W - 30, 90), 12, fill=(0, 0, 0))
    d.text((W - 113, 66), "AI किरदार", font=tt.font(24), fill=(230, 230, 230), anchor="mm")


def name_strap(d, y, who_name, role):
    d.rectangle((0, y, 470, y + 62), fill=RED)
    d.text((30, y + 31), who_name, font=tt.font(44), fill=WHITE, anchor="lm")
    d.rectangle((0, y + 62, 620, y + 106), fill=WHITE)
    d.text((30, y + 84), role, font=tt.font(28), fill=(20, 20, 20), anchor="lm")


def karaoke(d, text, frac, cy):
    """3-4 शब्द एक बार में, बोला जा रहा शब्द पीला."""
    words = str(text).split()
    if not words:
        return
    cur = min(len(words) - 1, int(frac * len(words)))
    start = (cur // 4) * 4
    chunk = words[start:start + 4]
    f = tt.font(78)
    widths = [f.getlength(w + " ") for w in chunk]
    total = sum(widths)
    if total > 1000:
        f = tt.font(int(78 * 1000 / total))
        widths = [f.getlength(w + " ") for w in chunk]
        total = sum(widths)
    x = (W - total) / 2
    d.rounded_rectangle((x - 30, cy - 62, x + total + 10, cy + 62), 26, fill=(0, 0, 0))
    for i, (w, wd) in enumerate(zip(chunk, widths)):
        on = start + i == cur
        d.text((x, cy), w, font=f, fill=YEL if on else WHITE, anchor="lm")
        x += wd


def stamp(im, text, t):
    s = 1.6 - 0.6 * min(1, t / 5)
    f = tt.font(int(96 * s))
    lay = Image.new("RGBA", (700, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((10, 30, 690, 230), 30, fill=YEL + (255,), outline=(0, 0, 0, 255), width=8)
    d.text((350, 130), text, font=f, fill=(0, 0, 0), anchor="mm")
    lay = lay.rotate(-8, expand=True, resample=Image.BICUBIC)
    im.paste(lay, ((W - lay.width) // 2 + 140, 210), lay)


def poll(d, p, t):
    a = min(1, t / 8)
    y = int(560 + (1 - a) * 300)
    d.rounded_rectangle((60, y, W - 60, y + 640), 40, fill=(255, 255, 255))
    for r, row in enumerate(_wrap(p.get("q", ""), tt.font(60), 880)[:2]):
        d.text((W / 2, y + 90 + r * 76), row, font=tt.font(60), fill=(20, 20, 20), anchor="mm")
    for j, (opt, col) in enumerate(((p.get("a", ""), (30, 140, 70)), (p.get("b", ""), RED))):
        yy = y + 280 + j * 140
        d.rounded_rectangle((110, yy, W - 110, yy + 110), 55, fill=col)
        d.text((W / 2, yy + 55), f"{j + 1}.  {opt}", font=tt.font(54), fill=WHITE, anchor="mm")
    d.text((W / 2, y + 590), "👇 कमेंट में 1 या 2 लिखो".replace("👇 ", ""), font=tt.font(44), fill=(60, 60, 60), anchor="mm")


# ------------------------------------------------------------------ पूरा reel
def render(ep, lens, faces, stills, visuals, chars, out, preview, audio_paths):
    """lens: हर line के सेकंड; faces[i]: frame generator (या None); visuals[i]: [Path|card dict, ...]."""
    counts = [max(1, round(s * FPS)) for s in lens]
    tail = 2.6 if ep.get("poll") else 0.8
    tailn = int(tail * FPS)
    total = sum(counts) + tailn
    events, t0 = [(0.0, "boom")], 0.0
    for i, ln in enumerate(ep["lines"]):
        if i:
            events.append((t0, "boom" if ln.get("punch") else "pop" if ln.get("react") else "whoosh"))
        nv = max(1, len(visuals[i]))
        for j in range(1, nv):
            events.append((t0 + lens[i] * j / nv, "pop"))
        t0 += lens[i]
    events.append((t0, "ding"))
    mix_audio([_read(p) for p in audio_paths], events, tail, out.with_suffix(".wav"))

    wr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", str(out.with_suffix(".wav")), "-c:v", "libx264", "-crf", "21",
                           "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", str(out)],
                          stdin=subprocess.PIPE)
    k, stamp_i, last_face = 0, 0, None
    for i, ln in enumerate(ep["lines"]):
        n = counts[i]
        react = bool(ln.get("react"))
        punch = bool(ln.get("punch")) or react
        card = {"big": ln.get("big") or "", "sub": ln.get("sub", "")}
        vis = list(visuals[i])
        if card["big"] and len(vis) < 2:                           # clip + खबर कार्ड बारी-बारी
            vis.insert(1 if vis else 0, card)
        vis = vis or [card]
        per = max(1, n // len(vis))
        vgen = None
        _, name, role = chars[ln["who"]]
        for t in range(n):
            if not punch and t % per == 0 and t // per < len(vis):
                vgen = visual_frames(vis[t // per], per if t // per < len(vis) - 1 else n - t, i * 3 + t // per)
            fr = next(faces[i], None) if faces[i] else None
            if fr is None:
                fr = (last_face if t else None) or stills[i]
            last_face = fr
            im = Image.new("RGB", (W, H), (10, 10, 14))
            if punch:                                              # पूरा screen, तेज़ zoom, हल्का झटका
                z = 1.0 + (0.08 if react else 0.25) * min(1, t / 8)
                f = face_frame(fr, W, H, z, 0.1)
                if t < 6 and not react:
                    f = f.transform(f.size, Image.AFFINE, (1, 0, (6 - t) * 6 * (-1) ** t, 0, 1, 0))
                im.paste(f, (0, 0))
                # Long punch/reaction shots otherwise leave the upper screen
                # almost unchanged and fail the retention QA. Rotate a real
                # dialogue-specific kinetic headline every ~1.5 seconds.
                if n > FPS * 3 and (t // max(1, int(FPS * 1.5))) % 2 == 1:
                    beat = card_frame({"big": ln.get("big") or ln.get("say", ""),
                                       "sub": ln.get("sub", "")}, t % max(1, int(FPS * 1.5)), i + t // FPS)
                    im.paste(beat, (0, 0))
            else:
                upper = next(vgen, None) or Image.new("RGB", (W, TOP))
                # A still image or paused source must never occupy the upper
                # screen for an entire long line. Interleave a contextual
                # kinetic card on a fixed 1.2s beat, even without `big`.
                beat_len = max(1, int(FPS * 1.2))
                if n > beat_len * 2 and (t // beat_len) % 2 == 1:
                    upper = card_frame({"big": ln.get("big") or ln.get("say", ""),
                                        "sub": ln.get("sub", "")}, t % beat_len, i * 7 + t // beat_len)
                im.paste(upper, (0, 0))
                im.paste(face_frame(fr, W, BOT, 1.0 + 0.04 * t / n, 0.04), (0, TOP))
            d = ImageDraw.Draw(im)
            chrome(d, k)
            if react:
                d.rounded_rectangle((40, 1560, 600, 1640), 20, fill=RED)
                d.text((70, 1600), f"{name} का रिएक्शन", font=tt.font(46), fill=WHITE, anchor="lm")
            elif punch:
                name_strap(d, 1560, name, role)
                if t >= 4:
                    stamp(im, STAMPS[stamp_i % len(STAMPS)], t - 4)
                    d = ImageDraw.Draw(im)
            else:
                d.rectangle((0, TOP - 6, W, TOP + 6), fill=YEL)
                name_strap(d, H - 150, name, role)
            if k < FPS * 2.5 and ep.get("hook"):                   # hook: पहले 2.5 सेकंड
                rows = _wrap(ep["hook"], tt.font(72), 980)[:3]
                d.rounded_rectangle((24, 130, W - 24, 150 + 92 * len(rows)), 26, fill=YEL)
                for r, row in enumerate(rows):
                    d.text((W / 2, 186 + r * 92), row, font=tt.font(72), fill=(0, 0, 0), anchor="mm")
            karaoke(d, ln.get("caption") or ln["say"], t / n, 1780 if punch else TOP - 80)   # मुँह पर कभी नहीं
            d.rectangle((0, H - 12, int(W * k / total), H), fill=YEL)
            wr.stdin.write(im.tobytes())
            k += 1
        if punch and not react:
            stamp_i += 1
    for t in range(tailn):                                         # आख़िर: poll + follow
        im = Image.new("RGB", (W, H), (10, 10, 14))
        im.paste(face_frame(last_face or stills[-1], W, H, 1.1, 0.2).filter(ImageFilter.GaussianBlur(8)), (0, 0))
        d = ImageDraw.Draw(im)
        chrome(d, k)
        if ep.get("poll"):
            poll(d, ep["poll"], t)
        d.rounded_rectangle((260, 1420, W - 260, 1520), 50, fill=RED)
        d.text((W / 2, 1470), "फ़ॉलो करो • बकरा न्यूज़", font=tt.font(46), fill=WHITE, anchor="mm")
        d.rectangle((0, H - 12, int(W * k / total), H), fill=YEL)
        wr.stdin.write(im.tobytes())
        k += 1
    wr.stdin.close()
    wr.wait()
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(out), "-vf",
                    f"fps={12 / max(1, total / FPS)},scale=216:-1,tile=6x2", "-frames:v", "1", str(preview)])
    return total / FPS
