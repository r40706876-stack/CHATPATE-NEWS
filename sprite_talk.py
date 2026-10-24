"""
3D किरदार का बोलना — बिना AI चेहरा-बिगाड़ के: हमारी अपनी 3 फ़ोटो (मुँह बंद / आधा / खुला) से.
  • सिर्फ़ मुँह-ठुड्डी वाला हिस्सा बदलता है (बाकी चेहरा, आँखें, बाल बिल्कुल साफ़ — 3D render जैसे के तैसे)
  • आवाज़ की ताकत से मुँह खुलता है, और बंद→आधा→खुला के बीच धीरे से घुलता है (पटापट बदलना नहीं)
  • हल्की साँस, ज़ोर वाले शब्द पर हल्का सिर हिलना/झुकना
  • पलक: किरदार के folder में blink.png (आँखें बंद, बाकी neutral_closed जैसा) हो तो हर 2-4 सेकंड में आँखों वाला
    हिस्सा उससे घुलता है
"""
import math
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

FPS = 25
_masks = {}


def _rgba(p, cut):
    return cut(p) if cut else Image.open(p).convert("RGBA")


def mouth_mask(folder, expr):
    """मुँह वाला हिस्सा: बंद और खुली फ़ोटो में जहाँ फ़र्क है (चेहरे के निचले बीच वाले हिस्से में), फैलाकर नरम किनारे."""
    key = (str(folder), expr)
    if key in _masks:
        return _masks[key]
    a = np.asarray(Image.open(Path(folder) / f"{expr}_closed.png").convert("L")).astype(int)
    b = np.asarray(Image.open(Path(folder) / f"{expr}_open.png").convert("L")).astype(int)
    h, w = a.shape
    d = ndimage.binary_opening(np.abs(a - b) > 25, iterations=2)
    lab, n = ndimage.label(d)
    if n:
        sz = ndimage.sum(d, lab, range(1, n + 1))
        big = lab == (int(np.argmax(sz)) + 1)          # सबसे बड़ा फ़र्क = मुँह
        ys, xs = np.nonzero(big)
        cx, cy = xs.mean(), ys.mean()
        rx, ry = (xs.max() - xs.min()) / 2 + w * 0.06, (ys.max() - ys.min()) / 2 + h * 0.035
    else:
        cx, cy, rx, ry = w * 0.52, h * 0.36, w * 0.12, h * 0.06
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).ellipse((cx - rx, cy - ry, cx + rx, cy + ry * 1.25), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(w * 0.018))
    _masks[key] = (m, (cx, cy, rx, ry))
    return _masks[key]


def envelope(wav, n):
    """हर frame पर मुँह कितना खुले (0-1): आवाज़ की ताकत, जल्दी खुले, धीरे बंद हो."""
    with wave.open(str(wav)) as f:
        sr = f.getframerate()
        a = np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(np.float32) / 32768
    hop = sr / FPS
    rms = np.array([np.sqrt(np.mean(a[int(i * hop):int((i + 1) * hop)] ** 2) + 1e-9) for i in range(n)])
    ref = np.percentile(rms[rms > 0.005], 85) if (rms > 0.005).any() else 0.05
    x = np.clip((rms - 0.012) / max(ref - 0.012, 1e-3), 0, 1)
    out, v = np.zeros(n), 0.0
    for i, t in enumerate(x):
        v = v + (t - v) * (0.65 if t > v else 0.35)       # attack तेज़, release धीमा
        out[i] = v
    return out, x


def frames(folder, expr, wav, n, cut=None, seed=0):
    """n frames (RGBA sprite, मूल size) — पीछे का set अलग से लगता है."""
    folder = Path(folder)
    if not (folder / f"{expr}_open.png").exists():
        expr = "neutral"
    imgs = [_rgba(folder / f"{expr}_{s}.png", cut) for s in ("closed", "half", "open")]
    mask, (cx, cy, rx, ry) = mouth_mask(folder, expr)
    env, raw = envelope(wav, n)
    rng = np.random.default_rng(seed)
    blinks = set()
    t = int(rng.integers(20, 50))
    while t < n:                                          # हर 2-4 सेकंड में एक पलक
        blinks.update(range(t, t + 4))
        t += int(rng.integers(50, 100))
    w, h = imgs[0].size
    blink, eye_mask = None, None
    if (folder / "blink.png").exists():
        blink = _rgba(folder / "blink.png", cut)
        a = np.asarray(Image.open(folder / "neutral_closed.png").convert("L")).astype(int)
        b = np.asarray(Image.open(folder / "blink.png").convert("L")).astype(int)
        d = ndimage.binary_opening(np.abs(a - b) > 25, iterations=2)
        d[int(cy - ry * 0.5):, :] = False                 # सिर्फ़ मुँह से ऊपर (आँखें)
        eye_mask = Image.fromarray((ndimage.binary_dilation(d, iterations=int(w * 0.02)) * 255).astype(np.uint8))
        eye_mask = eye_mask.filter(ImageFilter.GaussianBlur(w * 0.01))
    nod, state, hold = 0.0, 0, 0
    for i in range(n):
        # मुँह की 3 साफ़ हालतें (पहले blend से धुंधला "दो-मुँह" दिखता था) — आवाज़ के साथ खुले, शब्दों के बीच बंद
        lvl = 2 if raw[i] > 0.55 else 1 if raw[i] > 0.18 else 0
        if i and lvl != state and hold < 2 and abs(lvl - state) == 1:
            lvl = state                                     # 1 frame की झिलमिल नहीं
        hold = hold + 1 if lvl == state else 0
        state = lvl
        base = imgs[lvl]
        im = Image.composite(base, imgs[0], mask)
        if blink is not None and i in blinks:
            k = i - min(b for b in blinks if b <= i and b > i - 4)
            im = Image.composite(blink, im, eye_mask.point(lambda v, a=[0.5, 1, 1, 0.5][k]: int(v * a)))
        nod += ((raw[i] > 0.6) * 1.0 - nod) * 0.3          # ज़ोर वाले शब्द पर सिर का झटका (पहले लगभग स्थिर — "बेजान" लगता था)
        talk = env[i]
        # मालिक: "किरदार फालतू हिल रहे" — अब सिर लगभग स्थिर: सिर्फ़ धीमी साँस जैसी हल्की हरकत, कोई झटका नहीं
        ang = 0.35 * math.sin(i / 45 + seed)
        dx = 0.0
        dy = 1.5 * math.sin(i / 32 + seed)
        im = im.rotate(ang, resample=Image.BICUBIC, center=(w / 2, h * 0.9), translate=(dx, dy))
        yield im
