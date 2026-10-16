"""
Studio reel (3D किरदार, बिना retro) — news channel वाला split layout:
  ऊपर ~आधा: बड़ी news screen (खबर से जुड़ा असली clip/photo, "ब्रेकिंग", नीचे लाल headline पट्टी, ठप्पा कोने में)
  नीचे: 3D studio desk (या गाँव की गली) में छोटा किरदार — होंठ SadTalker से, सीधा कैमरे में.
punch पर किरदार पर हल्का zoom, line के बाद 1 सेकंड reaction pose, बड़े captions, ticker, आख़िर में poll.
"""
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import reel_v3 as rv
import talk_test as tt

ROOT = Path(__file__).parent
W, H, FPS = 1080, 1920, 25
SW, SH = 720, 1280                     # SadTalker के लिए source (9:16)
# "tanz" पर भी सीधा देखने वाला गंभीर चेहरा: smug वाली photos में आँखें बग़ल में हैं (बोलते वक़्त अजीब लगता था) —
# वो सिर्फ़ reaction pose "smug" में.
EXPR = {"hasi": "happy", "gussa": "angry", "udaas": "sad", "hairan": "shock", "tanz": "neutral", "gambhir": "neutral",
        "": "neutral"}
_bg = None
_sess = None


def studio_bg(w=W, h=H):
    y = np.linspace(0, 1, h)[:, None]
    x = np.linspace(-1, 1, w)[None, :]
    r = np.clip(1 - np.sqrt(x ** 2 * 0.6 + (y - 0.35) ** 2 * 1.4), 0, 1)
    im = Image.fromarray(np.stack([18 + 60 * r, 28 + 80 * r, 66 + 130 * r], -1).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for k in range(0, w + 400, int(90 * w / W)):
        d.line((k, 0, k - 400 * w / W, h), fill=(40, 60, 120), width=2)
    d.text((w / 2, h * 0.29), "बकरा न्यूज़", font=tt.font(int(170 * w / W)), fill=(58, 82, 148), anchor="mm")
    return im.filter(ImageFilter.GaussianBlur(3 * w / W))


def cutout(path):
    global _sess
    from rembg import new_session, remove
    if _sess is None:
        _sess = new_session("isnet-general-use")
    return remove(Image.open(path).convert("RGB"), session=_sess)


def pose_file(folder, expr):
    folder = Path(folder)
    for name in (f"{EXPR.get(expr, expr)}_closed.png", f"{expr}.png", "neutral_closed.png"):
        if (folder / name).exists():
            return folder / name
    raise FileNotFoundError(folder)


SETS = {k: ROOT / f"assets/sets/{k}.png" for k in ("studio", "village", "office", "road", "mandi", "aangan", "room",
                                                   "gas", "kitchen", "station", "hospital", "khet", "school",
                                                   "thana", "bank", "bijli", "ration")}
DESK_Y = 0.555                                      # studio में desk का ऊपरी किनारा (ऊँचाई का हिस्सा)
SCREEN = (0.005, 0.222, 0.43, 0.245)                 # पीछे वाली बड़ी screen (x, y, w, h — हिस्से में)
_sets = {}


def set_img(name, w, h):
    key = (name, w, h)
    if key not in _sets:
        im = Image.open(SETS[name]).convert("RGB")
        x0, y0 = int(im.width * 0.79), int(im.height * 0.88)   # Gemini ✦ ढको (पास का हिस्सा धुंधला करके)
        box = (x0, y0, x0 + int(im.width * 0.12), y0 + int(im.height * 0.07))
        sh = int(im.width * 0.13)
        im.paste(im.crop((box[0] - sh, box[1], box[2] - sh, box[3])).filter(ImageFilter.GaussianBlur(5)), box)
        _sets[key] = im.resize((w, h), Image.LANCZOS)
    return _sets[key].copy()


SCR = (24, 150, 1056, 860)                          # बड़ी news screen (x0, y0, x1, y1)
STRAP = 66                                          # screen के नीचे लाल headline पट्टी
BAND_Y, BAND_H = 940, 888                           # नीचे किरदार वाला हिस्सा (1080 x 888)


def compose_band(sprite, setname, w=W, h=BAND_H):
    """नीचे वाला हिस्सा: studio = desk के पीछे anchor (desk आगे), village = गली में कमर तक."""
    full = set_img(setname, w, int(w * 1376 / 768))
    if setname == "studio":
        dy = int(full.height * DESK_Y)
        top = dy - int(h * 0.63)
        band = full.crop((0, top, w, top + h))
        s = h * 0.98 / sprite.height
        sp = sprite.resize((int(sprite.width * s), int(sprite.height * s)), Image.LANCZOS)
        band.paste(sp, ((w - sp.width) // 2 + int(w * 0.04), int(h * 0.07)), sp)
        cut = int(h * 0.63)
        band.paste(full.crop((0, dy, w, dy + h - cut)), (0, cut))           # desk किरदार के आगे
        return band
    top = int(full.height * (0.30 if setname == "village" else 0.38))     # नए sets: ज़मीन/बीच का हिस्सा
    band = full.crop((0, top, w, top + h)).filter(ImageFilter.GaussianBlur(1.5))
    s = h * 1.02 / sprite.height
    sp = sprite.resize((int(sprite.width * s), int(sprite.height * s)), Image.LANCZOS)
    band.paste(sp, ((w - sp.width) // 2, int(h * 0.06)), sp)
    return band


def compose(sprite, w=SW, h=SH, scale=1.0):
    """किरदार (RGBA) को studio में बड़ा रखो, नीचे से कटा, हल्की छाया."""
    bg = studio_bg(w, h)
    s = h * 0.92 / sprite.height * scale
    sp = sprite.resize((int(sprite.width * s), int(sprite.height * s)), Image.LANCZOS)
    x, y = (w - sp.width) // 2, h - sp.height + int(h * 0.04)
    sh = Image.new("L", sp.size, 0)
    sh.paste(sp.getchannel("A").point(lambda v: int(v * 0.5)))
    sh = sh.filter(ImageFilter.GaussianBlur(18 * w / W))
    bg.paste(Image.new("RGB", sp.size, (0, 0, 0)), (x + int(18 * w / W), y + int(14 * w / W)), sh)
    bg.paste(sp, (x, y), sp)
    return bg


_cuts = {}


def source_for(folder, expr, out, full=None, setname=None, shot="band"):
    """SadTalker का source. band (split/full shot) = नीचे वाला हिस्सा 1080x888 (चेहरा ~200px);
    close = पूरा close-up 720x1280 (full = उसी की 1080x1920 still)."""
    p = pose_file(folder, expr)
    if p not in _cuts:
        _cuts[p] = cutout(p)
    if shot == "close":                                   # पूरा 1080x1920: चेहरा ~450px, 512 model से साफ़
        compose_close(_cuts[p], setname, W, H).save(out)
        if full:
            compose_close(_cuts[p], setname, W, H).save(full)
        return
    if setname in SETS and SETS[setname].exists():
        im = compose_band(_cuts[p], setname)
    else:
        im = compose(_cuts[p], W, BAND_H, 0.9)
    im.save(out)
    if full:
        im.save(full)


def _frames(video):
    rd = subprocess.Popen(["ffmpeg", "-loglevel", "quiet", "-i", str(video), "-vf",
                           f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}",
                           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    while True:
        raw = rd.stdout.read(W * H * 3)
        if len(raw) < W * H * 3:
            return
        yield Image.frombuffer("RGB", (W, H), raw)


def _zoom(im, z, fy=0.25):
    cw, ch = W / z, H / z
    x0, y0 = (W - cw) / 2, (H - ch) * fy
    return im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BILINEAR)


def inset(im, src_frame, label):
    d = ImageDraw.Draw(im)
    x, y, w, h = 36, 200, 500, 300
    d.rounded_rectangle((x - 8, y - 8, x + w + 8, y + h + 54), 18, fill=(255, 214, 0))
    im.paste(src_frame.resize((w, h), Image.BILINEAR), (x, y))
    d.rectangle((x, y + h, x + w, y + h + 46), fill=(225, 30, 45))
    f = tt.font(30)
    while label and f.getlength(label) > w - 20 and f.size > 18:
        f = tt.font(f.size - 2)
    d.text((x + 14, y + h + 23), label, font=f, fill="white", anchor="lm")


def ticker(d, ep, k):
    """नीचे चलती खबरों की पट्टी (छोटे जोक)."""
    items = ep.get("ticker") or []
    if not items:
        return
    y0, y1 = 1828, 1896
    d.rectangle((0, y0, W, y1), fill=(255, 214, 0))
    txt = "   •   ".join(items) + "   •   "
    f = tt.font(34)
    L = f.getlength(txt)
    x = 200 - (k * 6) % max(1, L)
    for rep in range(3):
        d.text((x + rep * L, (y0 + y1) / 2), txt, font=f, fill=(0, 0, 0), anchor="lm")
    d.rectangle((0, y0, 190, y1), fill=(225, 30, 45))
    d.text((95, (y0 + y1) / 2), "ताज़ा", font=tt.font(36), fill="white", anchor="mm")


STAMP_OF = {"eyeroll": "वाह रे दावा!", "facepalm": "हद है!", "laugh": "सच्ची बात!", "thinking": "सोचो ज़रा!",
            "smug": "समझ गए न?"}
SW_, SH_ = SCR[2] - SCR[0], SCR[3] - SCR[1]
CUT = 2.0                                  # कोई भी तस्वीर इससे ज़्यादा सेकंड नहीं टिकती
YEL, RED = (255, 214, 0), (225, 30, 45)


def shot_for(i, ln):
    """हर line का दृश्य: hook और सबसे तेज़ punch (react वाली) = पूरा close-up; बाकी में बारी-बारी
    split (ऊपर खबर, नीचे किरदार) और full (पूरी screen तस्वीर, कोने में किरदार) — ताकि हर कुछ सेकंड में नज़ारा बदले."""
    # मालिक का फ़ैसला: हमेशा split — ऊपर खबर की screen, नीचे studio में बबलू (close/full बंद)
    return "split"


_cbg = {}


def compose_close(sprite, setname, w=SW, h=SH):
    """close-up: पीछे धुंधला set (गहराई), आगे बड़ा किरदार — punch पर पूरी screen."""
    if (setname, w, h) not in _cbg:
        bg = set_img(setname, w, h) if setname in SETS else studio_bg(w, h)
        bg = bg.filter(ImageFilter.GaussianBlur(7 * w / W))
        _cbg[(setname, w, h)] = Image.blend(bg, Image.new("RGB", bg.size), 0.25)
    bg = _cbg[(setname, w, h)].copy()
    s = h * 0.80 / sprite.height
    sp = sprite.resize((int(sprite.width * s), int(sprite.height * s)), Image.LANCZOS)
    bg.paste(sp, ((w - sp.width) // 2, h - sp.height + int(h * 0.02)), sp)
    return bg


def _cut_cached(p):
    p = Path(p)
    if p not in _cuts:
        _cuts[p] = cutout(p)
    return _cuts[p]


def talk_frames(talk, shot, n, seed):
    """talk = {"folder", "expr", "wav", "set"} → बोलते किरदार के frames (close = 1080x1920, बाकी = 1080x888)."""
    import sprite_talk
    ex = EXPR.get(talk.get("expr", ""), talk.get("expr", "")) or "neutral"
    for sp in sprite_talk.frames(talk["folder"], ex, talk["wav"], n, _cut_cached, seed):
        yield compose_close(sp, talk["set"], W, H) if shot == "close" else compose_band(sp, talk["set"])


def _bases():
    out = {}
    for strap in (True, False):
        y = np.linspace(0, 1, H)[:, None, None]
        g = np.array((10, 16, 40))[None, None] * (1 - y) + np.array((24, 34, 80))[None, None] * y
        im = Image.fromarray(np.repeat(g, W, axis=1).astype(np.uint8))
        ImageDraw.Draw(im).rounded_rectangle((SCR[0] - 9, SCR[1] - 9, SCR[2] + 9, SCR[3] + (STRAP if strap else 0) + 9),
                                             22, fill=YEL)
        out[strap] = im
    return out


def _kinetic(card, bg, t, size):
    """भूरे कार्ड की जगह: पिछली तस्वीर धुंधली करके उस पर उछलते बड़े अक्षर (अंक हो तो 0 से गिनती चढ़े)."""
    import re
    w, h = size
    im = bg.resize(size).filter(ImageFilter.GaussianBlur(14)) if bg is not None else Image.new("RGB", size, (30, 20, 60))
    im = Image.blend(im, Image.new("RGB", size), 0.5)
    d = ImageDraw.Draw(im)
    big, sub = str(card.get("big", "")), str(card.get("sub", ""))
    m = re.search(r"\d[\d,]*", big)
    if m and t < 20 and int(m.group().replace(",", "")) >= 10:     # "1 नवंबर" जैसी तारीख़ नहीं गिनते
        n = int(m.group().replace(",", ""))
        big = big.replace(m.group(), f"{int(n * (1 - (1 - t / 20) ** 3)):,}")
    words = big.split()
    shown = words[:max(1, min(len(words), 1 + t // 4))]          # शब्द एक-एक करके
    p = min(1, t / 5)
    f = tt.font(int(min(118, 118 * w / 1032) * (0.7 + 0.3 * p)))
    rows = rv._wrap(" ".join(shown), f, w - 90)[:3]
    y = h / 2 - (len(rows) - 1) * 66 - (36 if sub else 0)
    for r, row in enumerate(rows):
        d.text((w / 2, y + r * 132), row, font=f, fill=YEL if r == 0 else (255, 255, 255), anchor="mm",
               stroke_width=7, stroke_fill=(0, 0, 0))
    if sub and t > 10:
        fy = y + len(rows) * 132 + 10
        d.rounded_rectangle((60, fy - 44, w - 60, fy + 44), 20, fill=(255, 255, 255))
        d.text((w / 2, fy), sub, font=tt.font(44), fill=(20, 20, 20), anchor="mm")
    return im


def _screen_gen(src, seed, size, bg=None):
    """तस्वीर/clip/कार्ड के frames (size के हिसाब से), ख़त्म नहीं होते."""
    w, h = size
    if isinstance(src, Path) and src.suffix == ".mp4":
        got = False
        for f in rv._video_frames(src, w, h):
            got = True
            yield f
        if got:
            return
        src = {"big": ""}
    if isinstance(src, Path):
        im = Image.open(src).convert("RGB")
        t = 0
        mode = seed % 3
        while True:                                   # तेज़ Ken Burns: अंदर / बाहर / बग़ल
            p = min(1, t / (CUT * FPS))
            if mode == 0:
                yield rv._cover_img(im, w, h, 1.0 + 0.22 * p, 0.4)
            elif mode == 1:
                yield rv._cover_img(im, w, h, 1.25 - 0.22 * p, 0.4)
            else:
                big = rv._cover_img(im, int(w * 1.2), int(h * 1.2), 1.0, 0.4)
                x = int(w * 0.2 * p)
                yield big.crop((x, int(h * 0.1), x + w, int(h * 0.1) + h))
            t += 1
    t = 0
    while True:
        yield _kinetic(src or {}, bg, t, size)
        t += 1


def _credit(src):
    if isinstance(src, Path) and src.with_suffix(".txt").exists():
        return src.with_suffix(".txt").read_text(encoding="utf-8")[:70]
    return ""


def _vid_frames(video, w, h):
    rd = subprocess.Popen(["ffmpeg", "-loglevel", "quiet", "-i", str(video), "-vf",
                           f"fps={FPS},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}",
                           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    while True:
        raw = rd.stdout.read(w * h * 3)
        if len(raw) < w * h * 3:
            return
        yield Image.frombuffer("RGB", (w, h), raw)


def _zoomr(im, z, fy=0.25):
    if z <= 1.001:
        return im
    w, h = im.size
    cw, ch = w / z, h / z
    x0, y0 = (w - cw) / 2, (h - ch) * fy
    return im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((w, h), Image.BILINEAR)


def _stamp(im, text, t, cx, cy, size=64):
    s = 1.5 - 0.5 * min(1, t / 5)
    f = tt.font(int(size * s))
    tw = int(f.getlength(text)) + 70
    lay = Image.new("RGBA", (tw + 20, int(size * 2 * s)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((6, 6, tw + 14, lay.height - 6), 24, fill=YEL + (255,), outline=(0, 0, 0, 255), width=6)
    d.text(((tw + 20) / 2, lay.height / 2), text, font=f, fill=(0, 0, 0), anchor="mm")
    lay = lay.rotate(6, expand=True, resample=Image.BICUBIC)
    x = int(min(W - lay.width - 10, max(10, cx - lay.width / 2)))
    im.paste(lay, (x, int(cy - lay.height / 2)), lay)


def _headline(d, text):
    d.rectangle((SCR[0], SCR[3], SCR[2], SCR[3] + STRAP), fill=RED)
    f = tt.font(40)
    while f.getlength(text) > SW_ - 40 and f.size > 24:
        f = tt.font(f.size - 2)
    d.text((SCR[0] + 20, SCR[3] + STRAP / 2), text, font=f, fill="white", anchor="lm")


def _hook(d, text, cy):
    f = tt.font(84)
    rows = rv._wrap(text, f, 960)[:3]
    y0 = cy - 46 * len(rows) - 20
    d.rounded_rectangle((30, y0, W - 30, y0 + 40 + 92 * len(rows)), 28, fill=YEL, outline=(0, 0, 0), width=6)
    for r, row in enumerate(rows):
        d.text((W / 2, y0 + 66 + r * 92), row, font=f, fill=(0, 0, 0), anchor="mm")


def _ask(d, text, t, y0=1040):
    """बीच में comment वाला सवाल (Instagram पर comments = video आगे बढ़ता है)."""
    a = min(1, t / 5)
    y = int(y0 + (1 - a) * 120)
    f = tt.font(56)
    rows = rv._wrap(text, f, 900)[:2]
    h = 60 + 70 * len(rows) + 70
    d.rounded_rectangle((50, y, W - 50, y + h), 34, fill=(255, 255, 255), outline=RED, width=8)
    for r, row in enumerate(rows):
        d.text((W / 2, y + 60 + r * 70), row, font=f, fill=(20, 20, 20), anchor="mm")
    by = y + h - 50
    d.rounded_rectangle((W / 2 - 190, by - 30, W / 2 + 190, by + 30), 30, fill=RED)
    d.text((W / 2 - 20, by), "कमेंट करो", font=tt.font(40), fill="white", anchor="mm")
    d.polygon([(W / 2 + 120, by - 12), (W / 2 + 156, by - 12), (W / 2 + 138, by + 14)], fill="white")


def _pip(im, band, t, setname="studio"):
    """full shot: कोने में गोल खिड़की में बोलता किरदार (चेहरा भरकर)."""
    fx, fy, r = (int(W * 0.54), int(BAND_H * 0.27), 175) if setname == "studio" else (W // 2, int(BAND_H * 0.25), 175)
    face = band.crop((fx - r, fy - r, fx + r, fy + r)).resize((340, 340), Image.BILINEAR)
    m = Image.new("L", (340, 340), 0)
    ImageDraw.Draw(m).ellipse((0, 0, 339, 339), fill=255)
    x, y = W - 380, 1250
    ImageDraw.Draw(im).ellipse((x - 10, y - 10, x + 350, y + 350), fill=YEL)
    im.paste(face, (x, y), m)


def _bed(n):
    """हल्का news beat (96 bpm) — आवाज़ के नीचे दबता हुआ."""
    t = np.arange(n) / rv.SR
    beat = 60 / 96
    ph = t % beat
    kick = np.sin(2 * math.pi * (55 + 60 * np.exp(-ph * 30)) * ph) * np.exp(-ph * 9)
    ph2 = (t + beat / 2) % beat
    rng = np.random.default_rng(3)
    hat = rng.normal(0, 1, n) * np.exp(-ph2 * 60) * 0.25
    bar = (t % (beat * 4)) // beat
    bass_f = np.choose(bar.astype(int), [55, 55, 65.4, 49])
    bass = np.sin(2 * math.pi * bass_f * t) * 0.35 * np.exp(-ph * 3)
    return 0.07 * (kick + hat + bass)


MOOD_OF = {"hasi": "masti", "gussa": "tension", "hairan": "tension", "udaas": "udaas", "tanz": "news", "gambhir": "news"}


def _note(f, t, decay):
    return np.sin(2 * math.pi * f * t) * np.exp(-t * decay)


def mood_bed(mood, n, seed=0):
    """बिना copyright का, यहीं बना background music (हर मूड अलग), 4 bar का loop."""
    sr = rv.SR
    t = np.arange(n) / sr
    out = np.zeros(n, np.float32)
    bpm = {"news": 96, "masti": 116, "tension": 84, "udaas": 70}[mood]
    beat = 60 / bpm
    rng = np.random.default_rng(seed)
    if mood == "news":                                    # हल्का kick + hat + bass (अभी जैसा)
        return _bed(n).astype(np.float32)
    root = {"masti": 196.0, "tension": 110.0, "udaas": 146.8}[mood]
    scale = {"masti": [0, 4, 7, 9, 12, 9, 7, 4], "tension": [0, 1, 0, 3, 0, 1, 6, 3], "udaas": [0, 3, 7, 10, 7, 3, 2, 0]}[mood]
    step = beat / 2
    k = 0
    while k * step < n / sr:                              # plucked melody (सितार/पिज़्ज़िकाटो जैसा)
        i0 = int(k * step * sr)
        L = min(n - i0, int(sr * (0.5 if mood != "udaas" else 1.2)))
        tt = np.arange(L) / sr
        f = root * 2 ** (scale[k % len(scale)] / 12)
        amp = 0.5 if mood != "tension" or k % 2 == 0 else 0.25
        out[i0:i0 + L] += amp * (_note(f, tt, 7) + 0.4 * _note(2 * f, tt, 11))
        k += 1
    if mood == "masti":                                   # ढोलक जैसा थाप
        for j in range(int(n / sr / beat) + 1):
            i0 = int(j * beat * sr)
            L = min(n - i0, int(sr * 0.25))
            tt = np.arange(L) / sr
            f = 90 if j % 2 == 0 else 160
            out[i0:i0 + L] += 0.8 * np.sin(2 * math.pi * f * tt * (1 - 0.5 * tt)) * np.exp(-tt * 18)
    if mood == "tension":                                 # नीची drone + घड़ी की टिक-टिक
        out += 0.25 * np.sin(2 * math.pi * 55 * t) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.25 * t))
        for j in range(int(n / sr / (beat / 2)) + 1):
            i0 = int(j * beat / 2 * sr)
            L = min(n - i0, int(sr * 0.02))
            out[i0:i0 + L] += 0.35 * rng.normal(0, 1, L) * np.exp(-np.arange(L) / (sr * 0.004))
    if mood == "udaas":                                   # धीमा pad
        out += 0.18 * (np.sin(2 * math.pi * root / 2 * t) + 0.6 * np.sin(2 * math.pi * root / 2 * 1.189 * t))
    return (0.06 * out / max(1e-6, np.abs(out).max()) * 1.6).astype(np.float32)


def mix_studio(voices, events, tail, out, moods=None):
    total = sum(len(v) for v in voices) + int(tail * rv.SR)
    voice = np.zeros(total + rv.SR, np.float32)
    bed = np.zeros(total + rv.SR, np.float32)
    pos = 0
    moods = moods or ["news"] * len(voices)
    cache = {}
    fade = int(0.35 * rv.SR)
    for i, v in enumerate(voices):                        # हर हिस्से का अपना मूड, जोड़ पर धीरे से घुलता हुआ
        voice[pos:pos + len(v)] += v
        m = moods[i]
        if m not in cache:
            cache[m] = mood_bed(m, total + rv.SR, len(cache))
        seg_end = len(bed) if i == len(voices) - 1 else pos + len(v) + fade
        w = np.ones(seg_end - pos, np.float32)
        if i:
            w[:fade] = np.linspace(0, 1, fade)
        if i < len(voices) - 1:
            w[-fade:] = np.minimum(w[-fade:], np.linspace(1, 0, fade))
        bed[pos:seg_end] += cache[m][pos:seg_end] * w
        pos += len(v)
    env = np.convolve(np.abs(voice), np.ones(2400) / 2400, "same")
    duck = 1 - 0.6 * np.clip(env / 0.05, 0, 1)                    # आवाज़ हो तो music धीमा
    mix = voice + bed * duck
    for t, kind in events:
        s = rv.sfx(kind)
        i = int(t * rv.SR)
        mix[i:i + len(s)] += s[:len(mix) - i]
    mix = np.clip(mix[:total], -1, 1)
    import wave
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rv.SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


def render(ep, segs, chars, out, preview):
    """segs: [{"ln", "wav", "face" (video या None), "still" (PIL), "vis" [Path], "react", "shot"}]
    shot: close = पूरा close-up (720x1280 source) | split = ऊपर खबर+नीचे किरदार | full = पूरी तस्वीर+कोने में किरदार."""
    lens = [rv._read(s["wav"]).shape[0] / rv.SR for s in segs]
    counts = [max(1, round(x * FPS)) for x in lens]
    tail = 2.6 if ep.get("poll") else 0.8
    tailn = int(tail * FPS)
    total = sum(counts) + tailn
    events, t0 = [(0.0, "boom")], 0.0
    for s, L in zip(segs, lens):
        if t0:
            events.append((t0, "boom" if s.get("shot") == "close" and not s.get("react") else
                           "pop" if s.get("react") else "whoosh"))
        t0 += L
    events.append((t0, "ding"))
    moods, last_m = [], "news"
    for s_ in segs:                                       # reaction वाला हिस्सा पिछली line का मूड रखता है
        last_m = last_m if s_.get("react") else (s_["ln"].get("mood") or MOOD_OF.get(s_["ln"].get("expr", ""), "news"))
        moods.append(last_m)
    mix_studio([rv._read(s["wav"]) for s in segs], events, tail, out.with_suffix(".wav"), moods)
    wr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", str(out.with_suffix(".wav")), "-c:v", "libx264", "-crf", "20",
                           "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", str(out)],
                          stdin=subprocess.PIPE)
    bases = _bases()
    headline = ep.get("breaking") or ep.get("title") or ""
    last_react = max([i for i, s in enumerate(segs) if s.get("react")], default=-1)
    k, seed, last_screen, prev_im, last_vis = 0, 0, None, None, []
    cur, credit, clean = None, "", None
    st_text, st_t, seen = "", 0, set()
    im = bases[True]
    for si, (s, n) in enumerate(zip(segs, counts)):
        ln, react = s["ln"], s.get("react")
        shot = s.get("shot") or "split"
        _, name, role = chars[ln["who"]]
        size = (W, H) if shot == "full" else (SW_, SH_)
        vis = list(s.get("vis") or [])
        if shot in ("split", "full") and not vis and not react:
            if ln.get("big"):
                vis = [{"big": ln["big"], "sub": ln.get("sub", "")}]
            elif cur is None and not (si == 0 and ep.get("hook")):
                vis = [{"big": headline}]
            else:                                               # intro/outro: नीचे caption + ऊपर hook/सवाल पहले से हैं —
                vis = [{"big": ""}]                             # ऊपर दोबारा वही अक्षर नहीं, सिर्फ़ धुंधली तस्वीर
        if vis and isinstance(vis[0], Path):
            last_vis = vis
        if shot == "full" and not vis:
            shot, size = "split", (SW_, SH_)
        chunk = max(1, int(CUT * FPS))
        if vis and len(vis) * chunk < n:                        # कम तस्वीरें: हर तस्वीर एक ही बार, बराबर समय (A-B-A-B नहीं)
            chunk = max(1, math.ceil(n / len(vis)))
        face = None
        if s.get("talk"):                                       # हमारी 3 मुँह वाली फ़ोटो से बोलना (साफ़ 3D चेहरा)
            face = talk_frames(s["talk"], shot, n, si)
        elif s.get("face"):
            face = _vid_frames(s["face"], W, H) if shot == "close" else _vid_frames(s["face"], W, BAND_H)
        still = s["still"].resize((W, H)) if shot == "close" else s["still"]
        if not react:
            st_text = ""
        last = None                                              # cur/credit पिछली line से चलते रहते हैं (reaction पर भी)
        if shot != "close" and not vis and cur is None:
            cur = _screen_gen({"big": headline}, seed, size, last_screen)
        first_seen = ln["who"] not in seen and not react
        seen.add(ln["who"])
        for t in range(n):
            if shot != "close" and vis and t % chunk == 0:
                j = (t // chunk) % len(vis)
                seed += 1
                if cur is not None:
                    cur.close()
                cur, credit = _screen_gen(vis[j], seed, size, last_screen), _credit(vis[j])
            if face:
                fr = next(face, None) or last or still
                last = fr
            else:
                fr = still
            punchy = shot == "close" and not react
            if shot == "close":
                if punchy:
                    z = 1.0 + 0.08 * min(1, t / 8)
                else:                                     # reaction: ज़िंदा लगे — धीरे-धीरे पास आना + हल्की साँस
                    z = 1.04 + 0.05 * t / n + 0.006 * math.sin(t / 3)
                im = _zoomr(fr, z, 0.3).copy()
            elif shot == "full":
                sf = next(cur)
                last_screen = sf
                im = sf.copy()
                _pip(im, fr, t, ln.get("set", "studio"))
            else:
                sf = next(cur) if cur is not None else Image.new("RGB", size)
                last_screen = sf
                strap = k < FPS * 5 or bool(ep.get("bulletin") and ln.get("headline"))
                im = bases[strap].copy()
                im.paste(sf, (SCR[0], SCR[1]))
                zb = (1.0 + 0.10 * min(1, t / 8)) if (ln.get("punch") and not react) else (1.05 if react else 1.0 + 0.03 * t / n)
                im.paste(_zoomr(fr, zb), (0, BAND_Y))
                clean = im.copy()                                # बिना लिखाई वाला frame (आख़िरी poll के पीछे)
            d = ImageDraw.Draw(im)
            rv.chrome(d, k)
            if shot == "split":
                badge = f"खबर {ln['item']}/{ln['items_total']}" if ln.get("item") else "ब्रेकिंग"
                bw = max(180, int(tt.font(34).getlength(badge)) + 40)
                d.rounded_rectangle((SCR[0] + 16, SCR[1] + 16, SCR[0] + 16 + bw, SCR[1] + 66), 10, fill=RED)
                d.text((SCR[0] + 16 + bw / 2, SCR[1] + 41), badge, font=tt.font(34), fill="white", anchor="mm")
                if ep.get("bulletin") and ln.get("headline"):                # bulletin: हर खबर की अपनी headline हमेशा
                    _headline(d, ln["headline"])
                elif k < FPS * 5:
                    _headline(d, headline)
            if credit and shot != "close":
                f = tt.font(22)
                cw = f.getlength(credit)
                bx1, by1 = (SCR[2], SCR[3]) if shot == "split" else (W - 10, 1236)
                d.rectangle((bx1 - cw - 24, by1 - 38, bx1, by1), fill=(0, 0, 0))
                d.text((bx1 - 12, by1 - 19), credit, font=f, fill=(220, 220, 220), anchor="rm")
            if k < FPS * 1.8 and ep.get("hook"):
                _hook(d, ep["hook"], 330)
            if react:
                d.rounded_rectangle((30, 1500, 560, 1576), 20, fill=RED)
                d.text((58, 1538), f"{name} का रिएक्शन", font=tt.font(44), fill="white", anchor="lm")
            else:
                if first_seen and t < FPS * 2.5 and shot != "close":
                    rv.name_strap(d, (BAND_Y + 490) if shot == "split" else 1130, name, role)
                rv.karaoke(d, ln.get("caption") or ln["say"], t / n, 1716 if shot != "close" else 1560)
            if bool(ln.get("punch")) and not react and not st_text and t >= n * 0.6:
                st_text = ln.get("stamp") or STAMP_OF.get(ln.get("react_pose"), "")
                st_t = 0
            asking = ep.get("ask") and (si == last_react or (last_react < 0 and si == len(segs) - 1))
            if st_text and not asking:                          # सवाल वाले पल ठप्पा नहीं (ऊपर एक-दूसरे पर चढ़ते थे)
                if shot == "close":
                    _stamp(im, st_text, st_t, W / 2 + 60, 330, 78)
                else:
                    _stamp(im, st_text, st_t, SCR[2] - 200, SCR[1] + 120)
                st_t += 1
                d = ImageDraw.Draw(im)
            if ep.get("ask") and (si == last_react or (last_react < 0 and si == len(segs) - 1)):
                _ask(d, ep["ask"], t, 300 if shot == "split" else 1040)
            if shot == "split" and not react:
                ticker(d, ep, k)
            d.rectangle((0, H - 12, int(W * k / total), H), fill=YEL)
            if react and t < 5 and prev_im is not None:        # बोलने से reaction में झटके से नहीं, घुलकर
                im = Image.blend(prev_im, im, (t + 1) / 6)
            wr.stdin.write(im.tobytes())
            k += 1
        prev_im = im
    end = (clean if clean is not None else im).filter(ImageFilter.GaussianBlur(10))
    end = Image.blend(end, Image.new("RGB", end.size), 0.35)
    for t in range(tailn):
        im = end.copy()
        d = ImageDraw.Draw(im)
        rv.chrome(d, k)
        if ep.get("poll"):
            rv.poll(d, ep["poll"], t)
        d.rounded_rectangle((260, 1420, W - 260, 1520), 50, fill=RED)
        d.text((W / 2, 1470), "फ़ॉलो करो • बकरा न्यूज़", font=tt.font(46), fill="white", anchor="mm")
        d.rectangle((0, H - 12, int(W * k / total), H), fill=YEL)
        wr.stdin.write(im.tobytes())
        k += 1
    if cur is not None:
        cur.close()
    wr.stdin.close()
    wr.wait()
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(out), "-vf",
                    f"fps={12 / max(1, total / FPS)},scale=216:-1,tile=6x2", "-frames:v", "1", str(preview)])
    return total / FPS
