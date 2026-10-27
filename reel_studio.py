"""
Studio reel (3D किरदार, बिना retro) — news channel वाला split layout:
  ऊपर ~आधा: बड़ी news screen (खबर से जुड़ा असली clip/photo, "ब्रेकिंग", नीचे लाल headline पट्टी, ठप्पा कोने में)
  नीचे: 3D studio desk (या गाँव की गली) में छोटा किरदार — होंठ SadTalker से, सीधा कैमरे में.
punch पर किरदार पर हल्का zoom, line के बाद 1 सेकंड reaction pose, बड़े captions, ticker, आख़िर में poll.
"""
import math
import re
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


SCR = (12, 130, 1068, 940)                          # बड़ी news screen (x0, y0, x1, y1)
STRAP = 66                                          # screen के नीचे लाल headline पट्टी
BAND_Y, BAND_H = 1010, 888                          # नीचे किरदार वाला हिस्सा (1080 x 888)


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
HOOK_EVENT = 1.2                                  # सेकंड: hook में कुछ "होता" है (ठप्पा गिरता है) — virality skill
CUT = 1.7                                  # कोई भी तस्वीर इससे ज़्यादा सेकंड नहीं टिकती (virality skill: हर 1.5-2 सेकंड नया नज़ारा)
YEL, RED = (255, 214, 0), (225, 30, 45)


def shot_for(i, ln):
    """हर line का दृश्य: hook और सबसे तेज़ punch (react वाली) = पूरा close-up; बाकी में बारी-बारी
    split (ऊपर खबर, नीचे किरदार) और full (पूरी screen तस्वीर, कोने में किरदार) — ताकि हर कुछ सेकंड में नज़ारा बदले."""
    # मालिक का फ़ैसला: हमेशा split — ऊपर खबर की screen, नीचे studio में बबलू (close/full बंद).
    # virality skill: सिर्फ़ पहली line (पहले 2-3 सेकंड) में पूरी screen पर असली खबर की तस्वीर/clip, कोने में बबलू —
    # scroll करता अँगूठा studio नहीं, पहचानी हुई खबर देखकर रुकता है. उसके बाद वही split.
    return "full" if i == 0 else "split"


def shot_v2(i, ln):
    """नई presentation (style "v2"): पहली line और तथ्य = पूरी screen पर तस्वीर/clip (कोने में किरदार),
    पंच/tag वाली line = किरदार का बड़ा close-up, बाकी split — हर line पर नज़ारा बदले, template जैसा न लगे."""
    if i == 0 or (ln.get("who") == "bablu" and not ln.get("punch")):
        return "full"
    # Keep the speaking character small even on punch lines: close-ups reveal
    # synthetic mouth movement. Split screen lets visuals carry the story.
    return "split"


_cbg = {}


def compose_close(sprite, setname, w=SW, h=SH):
    """close-up: पीछे धुंधला set (गहराई), आगे बड़ा किरदार — punch पर पूरी screen."""
    if (setname, w, h) not in _cbg:
        bg = set_img(setname, w, h) if setname in SETS else studio_bg(w, h)
        bg = bg.filter(ImageFilter.GaussianBlur(7 * w / W))
        _cbg[(setname, w, h)] = Image.blend(bg, Image.new("RGB", bg.size), 0.25)
    bg = _cbg[(setname, w, h)].copy()
    s = h * 0.72 / sprite.height                      # 768x1376 फ़ोटो कभी बड़ी (upscale) नहीं — पास से खिंचकर नक़ली दिखती थी
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


def chrome_safe(d, k):
    """Logo/LIVE/AI पट्टी Instagram-YouTube के ऊपरी buttons से हटकर — नीचे वाले हिस्से के ऊपर बाएँ."""
    y = BAND_Y + 14
    d.rounded_rectangle((20, y, 250, y + 52), 12, fill=RED)
    d.text((135, y + 26), "बकरा न्यूज़", font=tt.font(34), fill="white", anchor="mm")
    on = (k // 12) % 2 == 0
    d.rounded_rectangle((262, y + 6, 360, y + 46), 10, fill=(0, 0, 0))
    d.ellipse((274, y + 18, 288, y + 32), fill=RED if on else (90, 0, 0))
    d.text((324, y + 26), "LIVE", font=tt.font(24), fill="white", anchor="mm")
    d.rounded_rectangle((372, y + 6, 520, y + 46), 10, fill=(0, 0, 0))
    d.text((446, y + 26), "AI किरदार", font=tt.font(22), fill=(230, 230, 230), anchor="mm")


def speech_span(wav):
    """आवाज़ असल में कहाँ से कहाँ तक है (0-1, segment के हिस्से में) — शुरू/आख़िर की चुप्पी पर caption न भागे."""
    try:
        a = rv._read(wav)
        hop = max(1, len(a) // 400)
        e = np.array([np.abs(a[i:i + hop]).mean() for i in range(0, len(a), hop)])
        on = np.nonzero(e > max(0.01, e.max() * 0.12))[0]
        if len(on):
            return on[0] / len(e), (on[-1] + 1) / len(e)
    except Exception:                                     # noqa: BLE001
        pass
    return 0.0, 1.0


PUNCT = ",।…!?;:"


def _weight(w):
    """एक शब्द बोलने में लगने वाला मोटा समय: अक्षर (व्यंजन/स्वर/अंक) गिनकर."""
    import re
    return max(1, len(re.findall(r"[\u0915-\u0939\u0958-\u095F\u0905-\u0914A-Za-z0-9]", w))) + 0.6


def word_times(wav, say, n_words=None):
    """हर शब्द कब शुरू होता है (सेकंड) — असली आवाज़ से: चुप्पी के ठहराव (comma/पूर्णविराम पर) ढूँढकर वाक्य-टुकड़े
    आवाज़ पर बिठाओ, फिर टुकड़े के अंदर शब्दों की लंबाई से. (पहले सिर्फ़ लंबाई से अंदाज़ा = लिखाई आगे-पीछे.)"""
    words = str(say).split()
    if not words:
        return []
    try:
        a = np.abs(rv._read(wav).astype(np.float32))
        hop = max(1, int(rv.SR * 0.01))
        env = np.array([a[i:i + hop].mean() for i in range(0, len(a), hop)])
        on = env > max(0.006, env.max() * 0.08)
        idx = np.nonzero(on)[0]
        s0, s1 = (int(idx[0]), int(idx[-1]) + 1) if len(idx) else (0, len(env))
        pauses, k = [], s0
        while k < s1:                                     # 120ms+ की चुप्पी = ठहराव
            if not on[k]:
                j = k
                while j < s1 and not on[j]:
                    j += 1
                if j - k >= 12:
                    pauses.append((k, j))
                k = j
            else:
                k += 1
        wts = np.array([_weight(w) for w in words])
        cum = np.concatenate([[0], np.cumsum(wts)]) / wts.sum()
        bounds = [i + 1 for i, w in enumerate(words[:-1]) if w[-1] in PUNCT]
        anchors, used = [(0, s0)], set()
        speech = s1 - s0 - sum(b - a_ for a_, b in pauses)
        for b in bounds:                                  # हर comma/पूर्णविराम के लिए सबसे नज़दीक का ठहराव
            exp = s0 + cum[b] * (s1 - s0)
            best = min((p for p in pauses if p not in used), key=lambda p: abs(p[1] - exp), default=None)
            if best and abs(best[1] - exp) < max(60, 0.25 * speech) and best[1] > anchors[-1][1]:
                used.add(best)
                anchors.append((b, best[1]))
        anchors.append((len(words), s1))
        out = []
        for (wa, ta), (wb, tb) in zip(anchors, anchors[1:]):
            seg = wts[wa:wb]
            c = np.concatenate([[0], np.cumsum(seg)[:-1]]) / max(1e-6, seg.sum())
            out += [(ta + x * (tb - ta)) / 100 for x in c]
        times = out
    except Exception:                                     # noqa: BLE001
        L = 1.0
        times = list(np.linspace(0, L, len(words), endpoint=False))
    if n_words and n_words != len(times):                 # caption के शब्द (अंक वगैरह) अलग गिनती — अनुपात से
        times = [times[min(len(times) - 1, int(i * len(times) / n_words))] for i in range(n_words)]
    return times


def karaoke_timed(d, text, now, times, cy):
    """असली आवाज़ के समय वाले captions: जो शब्द बोला जा रहा है, वही पीला; टुकड़ा comma/पूर्णविराम पर टूटे (4 शब्द तक)."""
    words = str(text).split()
    if not words or not times:
        return
    cur = max(0, int(np.searchsorted(np.array(times), now, side="right")) - 1)
    chunks, c = [], []
    for i, w in enumerate(words):
        c.append(i)
        if len(c) >= 4 or w[-1] in PUNCT:
            chunks.append(c)
            c = []
    if c:
        chunks.append(c)
    chunk = next(ch for ch in chunks if cur <= ch[-1])
    f = tt.font(62)
    ws = [words[i] for i in chunk]
    widths = [f.getlength(w + " ") for w in ws]
    total = sum(widths)
    if total > 940:
        f = tt.font(int(62 * 940 / total))
        widths = [f.getlength(w + " ") for w in ws]
        total = sum(widths)
    x = (W - total) / 2
    d.rounded_rectangle((x - 26, cy - 50, x + total + 8, cy + 50), 24, fill=(0, 0, 0), outline=YEL, width=4)
    for i, w, wd in zip(chunk, ws, widths):
        d.text((x, cy), w, font=f, fill=YEL if i == cur else (255, 255, 255), anchor="lm", stroke_width=3,
               stroke_fill=(0, 0, 0))
        x += wd


def hook_low(d, text):
    """पहली line का पीला hook — किरदार के चेहरे/मुँह के नीचे (ठोड़ी से नीचे), ज़्यादा से ज़्यादा 3 छोटी lines."""
    f = tt.font(66)
    rows = rv._wrap(text, f, 980)[:3]
    if len(rows) == 3:
        f = tt.font(58)
        rows = rv._wrap(text, f, 990)[:3]
    lh = int(f.size * 1.12)
    top = BAND_Y + 440
    d.rounded_rectangle((24, top, W - 24, top + 30 + lh * len(rows)), 24, fill=YEL, outline=(0, 0, 0), width=5)
    for r, row in enumerate(rows):
        d.text((W / 2, top + 15 + lh * r + lh / 2), row, font=f, fill=(0, 0, 0), anchor="mm")


def karaoke_safe(d, text, frac, cy, span=(0.0, 1.0)):
    """बोले जा रहे शब्द के साथ चलते captions (4 शब्द एक बार में): समय शब्दों की लंबाई के हिसाब से बँटता है
    (लंबा शब्द = ज़्यादा देर), और सिर्फ़ आवाज़ वाले हिस्से में — ताकि caption आगे-पीछे न हो."""
    words = str(text).split()
    if not words:
        return
    a, b = span
    p = min(1.0, max(0.0, (frac - a) / max(0.05, b - a)))
    wts = np.array([len(w) + 2 for w in words], float)
    cum = np.cumsum(wts) / wts.sum()
    cur = int(min(len(words) - 1, np.searchsorted(cum, p, side="right")))
    start = (cur // 4) * 4
    chunk = words[start:start + 4]
    f = tt.font(62)
    widths = [f.getlength(w + " ") for w in chunk]
    total = sum(widths)
    if total > 940:
        f = tt.font(int(62 * 940 / total))
        widths = [f.getlength(w + " ") for w in chunk]
        total = sum(widths)
    x = (W - total) / 2
    d.rounded_rectangle((x - 26, cy - 50, x + total + 8, cy + 50), 24, fill=(0, 0, 0), outline=YEL, width=4)
    for i, (w, wd) in enumerate(zip(chunk, widths)):
        on = start + i == cur
        d.text((x, cy), w, font=f, fill=YEL if on else (255, 255, 255), anchor="lm", stroke_width=3, stroke_fill=(0, 0, 0))
        x += wd


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


def _card_rgb(color):
    """Normalize script card colors (CSS names/hex or RGB) before NumPy math."""
    from PIL import ImageColor
    if isinstance(color, str):
        try:
            return ImageColor.getrgb(color)[:3]
        except ValueError:
            return (60, 40, 100)
    try:
        values = tuple(max(0, min(255, int(v))) for v in color)
        return values[:3] if len(values) >= 3 else (60, 40, 100)
    except (TypeError, ValueError):
        return (60, 40, 100)


def _kinetic(card, bg, t, size):
    """भूरे कार्ड की जगह: पिछली तस्वीर धुंधली करके उस पर उछलते बड़े अक्षर (अंक हो तो 0 से गिनती चढ़े)."""
    import re
    w, h = size
    if card.get("color"):                                         # "बकरा बहस" beat card: साफ़ रंगीन पट्टी, पीछे धुंधली परछाईं नहीं
        c = card["color"]
        # Card colors may arrive as CSS hex or named strings from Gemini.
        # Normalize before NumPy arithmetic and PIL drawing.
        from PIL import ImageColor
        if isinstance(c, str):
            try:
                c = ImageColor.getrgb(c)
            except ValueError:
                c = (45, 35, 90)
        if not isinstance(c, (tuple, list)) or len(c) < 3:
            c = (45, 35, 90)
        c = tuple(max(0, min(255, int(v))) for v in c[:3])
        y = np.linspace(0, 1, h)[:, None, None]
        g = np.array(c)[None, None] * (1 - 0.55 * y)
        im = Image.fromarray(np.repeat(g, w, axis=1).astype(np.uint8))
        dd = ImageDraw.Draw(im)
        for k in range(-h, w, 70):                                # TV-बहस जैसी तिरछी धारियाँ
            dd.line((k, h, k + h, 0), fill=tuple(min(255, int(x * 1.18)) for x in c), width=18)
    else:
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


def _story_scene(card, size):
    """Looping illustrated news props; no random internet media."""
    w,h=size
    base_scene=card.get("scene","delivery")
    sequence={"sweets":["sweets","arrival","showroom"],"arrival":["arrival","showroom","arrival"],"showroom":["arrival","showroom","laddoo_hdmi"],"laddoo_hdmi":["laddoo_hdmi","laddoo_connected","showroom"],"bill":["bill","bill_shock","delivery"],"shop":["shop","sweets","arrival"],"delivery":["delivery","delivery_overload","arrival"]}.get(base_scene,[base_scene,"arrival"])
    t=0
    while True:
        scene=sequence[(t//max(1,int(FPS*1.35)))%len(sequence)]
        im=Image.new("RGB",(w,h),(235,245,252))
        d=ImageDraw.Draw(im)
        d.rectangle((0,int(h*.79),w,h),fill=(198,220,232))
        title={"sweets":"मिठाई माँगी!","arrival":"घर पर COD पार्सल!","showroom":"टीवी-फ्रिज आ गए!","laddoo_hdmi":"लड्डू में HDMI?!","laddoo_connected":"लड्डू से टीवी चालू!","bill":"COD बिल ₹1.69 लाख","bill_shock":"इतना बड़ा COD बिल!","shop":"मिठाई की दुकान!","delivery":"डिलीवरी वाले परेशान!","delivery_overload":"पार्सलों का पहाड़!"}.get(scene,"COD खबर")
        d.rounded_rectangle((15,20,w-15,110),radius=20,fill=(31,55,90))
        ft=tt.font(54)
        while ft.getlength(title)>w-55 and ft.size>25:ft=tt.font(ft.size-2)
        d.text((w//2,65),title,font=ft,anchor="mm",fill="white")
        bounce=int(35*abs(np.sin(t*.12)))
        def parcel(x,y,ww=215,hh=150):
            d.rounded_rectangle((x,y,x+ww,y+hh),radius=12,fill=(212,156,91),outline=(88,61,43),width=6)
            d.line((x+ww//2,y,x+ww//2,y+hh),fill=(245,216,154),width=12)
        def tv(x,y):
            d.rounded_rectangle((x,y,x+330,y+245),radius=20,fill=(31,45,65),outline=(82,105,124),width=7)
            d.rectangle((x+22,y+22,x+308,y+206),fill=(83,184,216))
            d.ellipse((x+90,y+55,x+210,y+175),fill=(245,209,98))
        def fridge(x,y):
            d.rounded_rectangle((x,y,x+175,y+350),radius=20,fill=(219,234,239),outline=(79,105,121),width=7)
            d.line((x,y+150,x+175,y+150),fill=(79,105,121),width=7)
            d.line((x+145,y+50,x+145,y+125),fill=(79,105,121),width=10)
        if scene=="sweets":
            parcel(85,int(h*.53),300,170)
            for j in range(3):d.ellipse((115+j*85,int(h*.56),180+j*85,int(h*.65)),fill=(248,204,101))
            if t>8:tv(w-450,int(h*.40)-bounce)
        elif scene=="arrival":
            # Parcel enters the door scene from the right instead of reusing the showroom.
            door_x=100
            d.rounded_rectangle((door_x,int(h*.28),door_x+270,int(h*.78)),radius=14,fill=(124,79,59),outline=(70,48,41),width=9)
            d.ellipse((door_x+225,int(h*.54),door_x+246,int(h*.57)),fill=(247,210,112))
            slide=int((1-min(1,(t%max(1,int(FPS*1.35)))/(FPS*.65)))*360)
            parcel(w-400+slide,int(h*.59)-bounce,310,175)
            d.text((w-250,int(h*.44)),"COD",font=tt.font(88),anchor="mm",fill=(195,60,60))
        elif scene=="showroom":
            tv(100,int(h*.43)-bounce)
            fridge(w-305,int(h*.36))
        elif scene in ("laddoo_hdmi","laddoo_connected"):
            # Visual joke: HDMI cable slides into the laddoo, then the TV powers on.
            phase=1.0 if scene=="laddoo_connected" else (t%max(1,int(FPS*1.35)))/max(1,int(FPS*1.35))
            lad_x=145
            lad_y=int(h*.40)
            d.ellipse((lad_x,lad_y,lad_x+355,lad_y+355),fill=(247,177,55),outline=(157,92,27),width=10)
            for xx,yy in ((210,.49),(340,.54),(265,.66),(415,.68)):
                d.ellipse((xx,int(h*yy),xx+22,int(h*yy)+22),fill=(209,123,34))
            plug_x=int(840-310*min(1,phase*2.1))
            cable_y=int(h*.59)
            d.line((plug_x+65,cable_y,980,cable_y,1010,cable_y+85),fill=(39,48,63),width=24)
            d.rounded_rectangle((plug_x,cable_y-36,plug_x+85,cable_y+36),radius=10,fill=(54,62,76))
            d.rectangle((plug_x-30,cable_y-20,plug_x,cable_y+20),fill=(176,180,183),outline=(45,49,55),width=4)
            if phase>.42:
                d.rounded_rectangle((580,int(h*.32),w-35,int(h*.54)),radius=16,fill=(28,50,71),outline=(83,110,130),width=7)
                d.rectangle((596,int(h*.34),w-51,int(h*.51)),fill=(84,210,139))
                d.text(((580+w-35)//2,int(h*.43)),"CONNECTED!",font=tt.font(53),anchor="mm",fill=(22,56,39))
                for j in range(3):
                    sx=480+j*45
                    d.line((sx,int(h*.36),sx+24,int(h*.32)),fill=(242,198,49),width=9)
            else:
                d.text((w//2,int(h*.27)),"लड्डू में HDMI?",font=tt.font(67),anchor="mm",fill=(193,55,56))
        elif scene in ("bill","bill_shock"):
            if scene=="bill_shock":
                d.rectangle((0,115,w,int(h*.79)),fill=(255,224,219))
                d.rounded_rectangle((120,int(h*.27),w-120,int(h*.75)),radius=22,fill="white",outline=(200,58,58),width=16)
                d.text((w//2,int(h*.38)),"COD बिल!",font=tt.font(95),anchor="mm",fill=(200,58,58))
                d.text((w//2,int(h*.58)),"₹1,69,000",font=tt.font(120),anchor="mm",fill=(38,53,79))
                yield im
                t+=1
                continue
            tv(50,int(h*.43)-bounce)
            d.rounded_rectangle((450,int(h*.32),w-40,int(h*.76)),radius=20,fill="white",outline=(68,79,99),width=8)
            d.text((w-300,int(h*.46)),"COD",font=tt.font(95),anchor="mm",fill=(199,66,65))
            bill_size=int(63+12*abs(np.sin(t*.16)))
            d.text((w-300,int(h*.59)),"₹1,69,000",font=tt.font(bill_size),anchor="mm",fill=(34,53,77))
        elif scene=="shop":
            d.rectangle((110,int(h*.40),w-110,int(h*.77)),fill=(249,216,159),outline=(103,74,53),width=8)
            d.polygon([(80,int(h*.40)),(w//2,int(h*.21)),(w-80,int(h*.40))],fill=(203,82,75))
            parcel(w//2-150,int(h*.52)-bounce,300,160)
        else:
            if scene=="delivery_overload":
                d.rectangle((0,115,w,int(h*.79)),fill=(244,232,211))
                for j in range(9):
                    parcel(45+(j%4)*245,int(h*.72)-(j//4)*190,215,160)
                d.ellipse((w-190,int(h*.23),w-80,int(h*.38)),fill=(238,183,135),outline=(79,57,48),width=6)
                d.text((w//2,int(h*.18)),"इतने पार्सल?!",font=tt.font(76),anchor="mm",fill=(179,59,55))
                yield im
                t+=1
                continue
            # The delivery-worker silhouette and increasing parcel stack are the punchline.
            d.ellipse((w-220,int(h*.37),w-120,int(h*.49)),fill=(238,183,135),outline=(79,57,48),width=5)
            d.line((w-170,int(h*.49),w-170,int(h*.70)),fill=(55,94,151),width=40)
            d.line((w-170,int(h*.55),w-285,int(h*.61)),fill=(55,94,151),width=22)
            d.line((w-170,int(h*.55),w-60,int(h*.62)),fill=(55,94,151),width=22)
            d.line((w-170,int(h*.70),w-230,int(h*.79)),fill=(52,58,69),width=23)
            d.line((w-170,int(h*.70),w-95,int(h*.79)),fill=(52,58,69),width=23)
            for j in range(5):
                if t<j*5:continue
                parcel(45+(j%3)*230,int(h*.68)-(j//3)*180-(bounce if j==4 else 0),205,140)
            d.text((w//2,int(h*.28)),"COD",font=tt.font(110),anchor="mm",fill=(204,66,60))
        yield im
        t+=1


def _screen_gen(src, seed, size, bg=None, hero=False):
    """तस्वीर/clip/कार्ड के frames (size के हिसाब से), ख़त्म नहीं होते.
    hero=True (reel का पहला frame): तेज़ "झटके वाला" zoom — पहले 2 सेकंड में हरकत (graph: 3-5 सेकंड पर आधे लोग जाते थे)."""
    w, h = size
    if isinstance(src, dict) and src.get("hybrid_stage"):
        from hybrid_stage import stage_frames
        yield from stage_frames(src, size, FPS)
        return
    if isinstance(src, dict) and src.get('scene'):
        yield from _story_scene(src, size)
        return
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
        if hero:                                      # 1.45 से 1.08 तक 0.6 सेकंड में (झटका), फिर धीरे-धीरे अंदर
            while True:
                q = min(1, t / (0.6 * FPS))
                z = 1.45 - 0.37 * (1 - (1 - q) ** 3) + 0.06 * max(0, t - 0.6 * FPS) / (CUT * FPS)
                yield rv._cover_img(im, w, h, z, 0.4)
                t += 1
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


def key_phrase(ln):
    """card पर line की मुख्य बात — सिर्फ़ पूरी, अपने-आप में समझ आने वाली (ठप्पा, या "…"/"," के बाद का 2-4 शब्द का टुकड़ा).
    आधे-अधूरे टुकड़े ("ने वही किया", "पहले रूठ") नहीं — तब card ही नहीं, तस्वीर चलेगी."""
    import re
    if ln.get("stamp"):
        return str(ln["stamp"])
    t = str(ln.get("caption") or ln.get("say") or "").strip()
    parts = [x.strip(" ।!?\"'") for x in re.split(r"…|\.\.\.|।|,|:|!|\?", t) if x.strip(" ।!?\"'")]
    bad_start = {"के", "की", "का", "लिए", "में", "से", "को", "पर", "और", "तो", "भी", "फिर", "ही", "अब", "बस", "ने", "जो", "कि"}
    for seg in reversed(parts):
        w = seg.split()
        if 2 <= len(w) <= 4 and w[0] not in bad_start:
            return seg + ("!" if t.endswith("!") else "")
    return ""


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


def _hook_big(d, text, cy):
    """बहुत बड़े अक्षर, 1-2 lines (≤6 शब्द) — scroll करते अँगूठे को 1 नज़र में पढ़ने लायक."""
    f = tt.font(118)
    rows = rv._wrap(text, f, 1000)[:2]
    while len(rows) > 2 or any(f.getlength(r) > 1000 for r in rows):
        f = tt.font(f.size - 6)
        rows = rv._wrap(text, f, 1000)[:2]
    lh = int(f.size * 1.15)
    y0 = cy - lh * len(rows) // 2 - 24
    d.rounded_rectangle((24, y0, W - 24, y0 + 48 + lh * len(rows)), 30, fill=YEL, outline=(0, 0, 0), width=7)
    for r, row in enumerate(rows):
        d.text((W / 2, y0 + 24 + lh * r + lh / 2), row, font=f, fill=(0, 0, 0), anchor="mm")


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


def _pip(im, band, t, setname="studio", left=False):
    """full shot: कोने में गोल खिड़की में बोलता किरदार (चेहरा भरकर)."""
    fx, fy, r = (int(W * 0.54), int(BAND_H * 0.27), 175) if setname == "studio" else (W // 2, int(BAND_H * 0.25), 175)
    face = band.crop((fx - r, fy - r, fx + r, fy + r)).resize((340, 340), Image.BILINEAR)
    m = Image.new("L", (340, 340), 0)
    ImageDraw.Draw(m).ellipse((0, 0, 339, 339), fill=255)
    x, y = (40, 1250) if left else (W - 380, 1250)   # v2: बाएँ, ताकि Instagram के दाएँ buttons के नीचे न दबे
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
    # A hard clip produced inter-sample AAC peaks above 0 dBFS in the
    # independently decoded 34.72s episode. Use a gentle peak-safe limiter
    # before PCM encoding; leave headroom for AAC reconstruction overshoot.
    mix = 0.62 * np.tanh(mix[:total] * 1.25) / np.tanh(1.25)
    import wave
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rv.SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


LINE_SFX = {"boom", "ding", "glitch", "whoosh", "pop", "laugh", "dhol", "thug", "tick"}


def render(ep, segs, chars, out, preview):
    """segs: [{"ln", "wav", "face" (video या None), "still" (PIL), "vis" [Path], "react", "shot"}]
    shot: close = पूरा close-up (720x1280 source) | split = ऊपर खबर+नीचे किरदार | full = पूरी तस्वीर+कोने में किरदार."""
    lens = [rv._read(s["wav"]).shape[0] / rv.SR for s in segs]
    counts = [max(1, round(x * FPS)) for x in lens]
    # virality skill: आख़िर में ख़ाली/धुंधला "फ़ॉलो करो" वाला हिस्सा नहीं — वो % देखा गिराता और loop तोड़ता था.
    # comment वाला सवाल अब सिर्फ़ caption में; "टैग:" वाली बात पहचान वाली line पर screen पर.
    tail = 0.3
    if ep.get("tag_ask") and not any(s_["ln"].get("tag_text") for s_ in segs):
        real = [s_ for s_ in segs if not s_.get("react")]
        if len(real) >= 3:
            real[-2]["ln"]["tag_text"] = re.sub(r"[\U0001F000-\U0001FFFF\u2600-\u27BF\uFE0F]", "", ep["tag_ask"]).strip()
    tailn = int(tail * FPS)
    total = sum(counts) + tailn
    events, t0 = [(0.0, "whoosh"), (HOOK_EVENT, "boom")], 0.0        # 1.2 सेकंड पर "अधपकी खबर" का ठप्पा + धमाका
    REACT_SFX = {"laugh": "laugh", "eyeroll": "thug", "smug": "thug", "facepalm": "dhol", "thinking": "glitch"}
    prev_who = None
    for i_, (s, L) in enumerate(zip(segs, lens)):
        if t0:
            if s.get("react"):                                # reaction कभी चुप नहीं: मज़ेदार आवाज़ तुरंत
                pose = (segs[i_ - 1]["ln"].get("react_pose") if i_ else "") or "laugh"
                events.append((t0, REACT_SFX.get(pose, "laugh")))
            elif s["ln"].get("sfx") in LINE_SFX:              # script ने beat के हिसाब से आवाज़ तय की ("बकरा बहस")
                events.append((t0, s["ln"]["sfx"]))
            else:                                             # किरदार बदले = TV glitch, वही रहे = whoosh
                events.append((t0, "glitch" if s["ln"]["who"] != prev_who else "whoosh"))
        if not s.get("react"):
            prev_who = s["ln"]["who"]
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
    pool = list(dict.fromkeys(p for s in segs for p in (s.get("vis") or []) if isinstance(p, Path)))   # सारी असली तस्वीरें
    v2 = ep.get("style") in ("v2", "nochar")
    nochar = ep.get("style") == "nochar"                 # बिना किरदार: सिर्फ़ तस्वीर/clip + बड़े अक्षर + आवाज़
    k, seed, last_screen, prev_im, last_vis, carry = 0, 0, None, None, [], 0
    cur, credit, clean = None, "", None
    st_text, st_t, seen = "", 0, set()
    im = bases[True]
    for si, (s, n) in enumerate(zip(segs, counts)):
        ln, react = s["ln"], s.get("react")
        shot = s.get("shot") or "split"
        _, name, role = chars[ln["who"]]
        size = (W, H) if shot in ("full", "story") else (SW_, SH_)
        vis = list(s.get("vis") or [])
        if ln.get("big") and vis and not react and shot in ("split", "full"):   # माँग वाली line: पहले बड़े अक्षर, फिर तस्वीर
            card = [{"big": ln["big"], "sub": ln.get("sub", ""), "color": ln.get("card_color")}]
            vis = (vis + card) if si == 0 else (card + vis)   # पहला सेकंड असली तस्वीर का (scroll वहीं रुकता है)
        if shot in ("split", "full") and not vis and not react and pool and not ln.get("big") and carry < 1:
            # तस्वीर नहीं मिली: ख़ाली/धुंधली screen नहीं (पहली video में 2.5 से 13 सेकंड तक ऊपर काला रहा — ठीक खाई पर) —
            # इसी खबर की दूसरी lines की असली तस्वीरें, जो अभी-अभी न दिखी हों, नए zoom के साथ
            # पहले यहाँ दूसरी lines की फ़ोटो लगती थीं — बोल कुछ और, screen पर कुछ और (मालिक: "mismatch न हो").
            # अब: पिछली line वाली तस्वीर ही चलती रहे (बात उसी से जुड़ी होती है), हर 2 सेकंड नए zoom/कोण से.
            # line के आख़िरी शब्द बड़े अक्षरों में नहीं — वो बोलने से पहले दिखकर punch बिगाड़ते थे और टूटे टुकड़े ("में? मम्मी के!") बनते थे
            vis = [last_vis[0]] if last_vis else []
            carry += 1                                          # एक ही तस्वीर 2 lines से ज़्यादा नहीं (पहले 30 सेकंड अटकी रही)
        if shot in ("split", "full") and not vis and not react:
            if ln.get("big"):
                vis = [{"big": ln["big"], "sub": ln.get("sub", ""), "color": ln.get("card_color")}]
            elif cur is None and not (si == 0 and ep.get("hook")):
                vis = [{"big": headline}]
            elif last_screen is None or not last_vis:           # एक भी तस्वीर नहीं मिली: काली screen नहीं, headline के अक्षर
                vis = [{"big": headline if si else ""}]
            else:                                               # intro/outro: नीचे caption + ऊपर hook/सवाल पहले से हैं —
                vis = [{"big": ""}]                             # ऊपर दोबारा वही अक्षर नहीं, सिर्फ़ धुंधली तस्वीर
        if vis and isinstance(vis[0], Path):
            last_vis = vis
        if list(s.get("vis") or []):
            carry = 0                                           # इस line की अपनी तस्वीर मिली
        # Never recycle an old photo for a line without its own verified visual.
        # Keep the speaker SMALL in split screen; alternate story-specific cards.
        # A generated *_set.png is only a room backdrop, NOT a news visual.
        # Never show it in the upper story panel as if it illustrated the line.
        own_verified = any(isinstance(v, Path) and v.exists() and not v.stem.endswith("_set")
                           for v in (s.get("vis") or []))
        if shot in ("split", "full") and not own_verified:
            shot, size = "split", (SW_, SH_)
            from visual_strategy import select_visual
            vis, visual_reason = select_visual(ln, ep, si)
            print(f"VISUAL_AUDIT line={si+1} speaker={ln.get('who')} strategy={visual_reason} verified_media=False")
        elif shot in ("split", "full"):
            print(f"VISUAL_AUDIT line={si+1} speaker={ln.get('who')} strategy=verified-media verified_media=True")
        if shot == "full" and not vis:
            shot, size = "split", (SW_, SH_)
        cut_s = CUT - 0.4 * int(ep.get("_fix") or 0)            # जाँच में कमी मिली = दोबारा बनाते वक़्त और जल्दी बदलें
        chunk = max(1, int(cut_s * FPS))                        # हर 2 सेकंड नया नज़ारा
        need = math.ceil(n / chunk) + int(ep.get("_fix") or 0)
        if shot != "close" and not react and vis and len(vis) < need and own_verified:
            # सिर्फ़ zoom बदलने से वही तस्वीर 5 सेकंड "रुकी" दिखती थी (छठ वाली video) — कमी हो तो: line की मुख्य बात
            # वाला card, फिर इसी खबर की दूसरी असली तस्वीरें (जो अभी इस line में नहीं)
            extra = []
            key = key_phrase(ln) if isinstance(vis[0], Path) else ""
            if key:
                extra.append({"big": key})
            extra += [p for p in pool if p not in vis and p not in last_vis] + [p for p in pool if p not in vis]
            for e_ in extra:
                if len(vis) >= need:
                    break
                if e_ not in vis:
                    vis.insert(1 if len(vis) == 1 else len(vis), e_)
        story_gen = None
        if shot == "story" and s.get("talk") and not react:
            import story_stage
            story_gen = story_stage.frames(ln, ep, s["talk"], n, _cut_cached, si)
            print(f"VISUAL_AUDIT line={si+1} speaker={ln.get('who')} strategy=full-story:{ln.get('scene')}")
        face = None
        if s.get("talk") and shot != "story":                                       # हमारी 3 मुँह वाली फ़ोटो से बोलना (साफ़ 3D चेहरा)
            face = talk_frames(s["talk"], shot, n, si)
        elif s.get("face"):
            face = _vid_frames(s["face"], W, H) if shot == "close" else _vid_frames(s["face"], W, BAND_H)
        still = s["still"].resize((W, H)) if shot == "close" else s["still"]
        if not react:
            st_text = ""
        span = speech_span(s["wav"]) if not react else (0.0, 1.0)
        cap_text = ln.get("caption") or ln.get("say", "")
        wtimes = word_times(s["wav"], ln.get("say", ""), len(cap_text.split())) if not react else []
        last = None                                              # cur/credit पिछली line से चलते रहते हैं (reaction पर भी)
        if shot != "close" and not vis and cur is None:
            cur = _screen_gen({"big": headline}, seed, size, last_screen)
        first_seen = ln["who"] not in seen and not react
        seen.add(ln["who"])
        for t in range(n):
            only_cards = all(isinstance(v, dict) for v in vis)
            if shot != "close" and vis and t % chunk == 0 and not (only_cards and t and len(vis) == 1):
                # (अकेला card पूरी line एक ही बार उभरे — हर 2 सेकंड दोबारा उछलना झिलमिल लगता था)
                j = (t // chunk) % len(vis)
                seed += 1
                if cur is not None:
                    cur.close()
                beat_card = isinstance(vis[j], dict) and vis[j].get("color")
                cur, credit = _screen_gen(vis[j], seed, size, None if beat_card else last_screen,
                                          hero=(si == 0 and t == 0)), _credit(vis[j])
            if face:
                fr = next(face, None) or last or still
                last = fr
            else:
                fr = still
            punchy = shot == "close" and not react
            if shot == "story":
                im = next(story_gen)
            elif shot == "close":
                if punchy:
                    # Long punch lines need a real camera change, not an almost-static face.
                    # A modest jump cut every ~1.6s preserves lip sync and the same character.
                    # This also makes _fix retries meaningful for close shots.
                    jump_frames = max(18, int((1.6 - 0.2 * int(ep.get("_fix") or 0)) * FPS))
                    angle = (t // jump_frames) % 2 if n > int(2.8 * FPS) else 0
                    z = (1.04 if angle == 0 else 1.23) + 0.012 * min(1, (t % jump_frames) / 8)
                    fy = 0.30 if angle == 0 else 0.24
                else:                                     # reaction: ज़िंदा लगे — धीरे-धीरे पास आना + हल्की साँस
                    z = 1.04 + 0.05 * t / n + 0.006 * math.sin(t / 3)
                    fy = 0.30
                im = _zoomr(fr, z, fy).copy()
                # Real full-frame visual interruption, not merely a tiny face zoom.
                # Older reels kept the same portrait for 3-5s and failed visual QA.
                if ln.get("big") and n > int(2.9 * FPS):
                    flash_cycle = max(18, int((1.8 - 0.2 * int(ep.get("_fix") or 0)) * FPS))
                    flash_len = max(6, int(0.42 * FPS))
                    if t >= flash_cycle and t % flash_cycle < flash_len:
                        im = _kinetic({"big": ln["big"], "color": ln.get("card_color") or "#4328A5"},
                                      None, t % flash_cycle, (W, H))
            elif shot == "full":
                sf = next(cur)
                last_screen = sf
                im = sf.copy()
                if not nochar:
                    _pip(im, fr, t, ln.get("set", "studio"), left=v2)
            else:
                sf = next(cur) if cur is not None else Image.new("RGB", size)
                last_screen = sf
                strap = bool(ep.get("bulletin") and ln.get("headline"))   # headline पट्टी सिर्फ़ bulletin में (पहले 4 परतें लिखाई की थीं)
                im = bases[strap].copy()
                im.paste(sf, (SCR[0], SCR[1]))
                # Keep cinematic motion, but cap the speaker zoom so fake lip-sync never fills the frame.
                # Story visuals above remain free to pan, zoom and animate.
                zb = 1.0 + (0.035 if ln.get("punch") else 0.022) * min(1.0, t / max(1, n))
                dx = int(7 * math.sin(t * 0.16)) if ln.get("beat") in ("twist", "takiya") else 0
                im.paste(_zoomr(fr, zb), (dx, BAND_Y))
                clean = im.copy()                                # बिना लिखाई वाला frame (आख़िरी poll के पीछे)
            d = ImageDraw.Draw(im)
            if k >= FPS * 2 and shot != "story":                                 # vidIQ + virality skill: पहले 2 सेकंड कोई logo/पट्टी नहीं (हर style में) — सिर्फ़ तस्वीर + 4 शब्द
                chrome_safe(d, k)
            if shot == "split":
                badge = f"खबर {ln['item']}/{ln['items_total']}" if ln.get("item") else "ब्रेकिंग"
                bw = max(180, int(tt.font(34).getlength(badge)) + 40)
                d.rounded_rectangle((SCR[0] + 16, SCR[1] + 16, SCR[0] + 16 + bw, SCR[1] + 66), 10, fill=RED)
                d.text((SCR[0] + 16 + bw / 2, SCR[1] + 41), badge, font=tt.font(34), fill="white", anchor="mm")
                if ep.get("bulletin") and ln.get("headline"):                # bulletin: हर खबर की अपनी headline हमेशा
                    _headline(d, ln["headline"])
            if credit and shot != "close":
                f = tt.font(22)
                cw = f.getlength(credit)
                bx1, by1 = (SCR[2], SCR[3]) if shot == "split" else (W - 10, 1236)
                d.rectangle((bx1 - cw - 24, by1 - 38, bx1, by1), fill=(0, 0, 0))
                d.text((bx1 - 12, by1 - 19), credit, font=f, fill=(220, 220, 220), anchor="rm")
            if react:
                d.rounded_rectangle((30, BAND_Y + 380, 560, BAND_Y + 456), 20, fill=RED)
                d.text((58, BAND_Y + 418), f"{name} का रिएक्शन", font=tt.font(44), fill="white", anchor="lm")
            else:
                # Keep the headline for the opening 1.8s only. The old full-line
                # yellow card obscured the action for ~4.5s and looked static.
                hooking = si == 0 and bool(ep.get("hook")) and t < int(FPS * 1.1)
                cy = 1685 if shot == "story" else (1150 if (v2 and shot == "full") else BAND_Y + 460)
                if first_seen and t < FPS * 2.5 and shot != "close" and not hooking and not (v2 and shot == "full"):
                    rv.name_strap(d, (BAND_Y + 84) if shot == "split" else 1130, name, role)
                if nochar:                                        # हर line ऊपर बड़े अक्षरों में (meme reel जैसा)
                    _hook(d, ep["hook"] if hooking else cap_text, 330)
                elif hooking and ep.get("hook_short") and not v2:           # पहले 3 सेकंड: 3 lines पढ़नी पड़ती थीं (skip 46%) — अब ≤6 शब्द, बड़े
                    _hook_big(d, re.sub(r"[\U0001F000-\U0001FFFF\u2600-\u27BF\uFE0F]", "", ep["hook_short"]).strip(), 360)
                    if wtimes:
                        karaoke_timed(d, cap_text, t / FPS, wtimes, cy)
                elif hooking and v2 and shot == "story":
                    _hook(d, ep.get("hook_short") or ep["hook"], 190)
                    if wtimes:
                        karaoke_timed(d, cap_text, t / FPS, wtimes, cy)
                elif hooking and v2:
                    # Do not cover the animated news story with a huge 3-line
                    # yellow card. Put the hook on the desk BELOW the speaker;
                    # the COD delivery and TV must remain visible immediately.
                    hook_low(d, ep.get("hook_short") or ep["hook"])
                elif hooking:
                    hook_low(d, ep["hook"])
                else:
                    # A kinetic story card already displays the line's key text.
                    # Do not overlay a second giant yellow tag over the same visual.
                    kinetic_story = shot == "split" and vis and all(
                        isinstance(v, dict) and "big" in v for v in vis)
                    if ln.get("tag_text") and not kinetic_story and shot != "story":
                        _hook(d, ln["tag_text"], 330)
                    if wtimes:
                        karaoke_timed(d, cap_text, t / FPS, wtimes, cy)
                    else:
                        karaoke_safe(d, cap_text, t / n, cy, span)
            if si == 0 and not react and not st_text and t == int(HOOK_EVENT * FPS):   # hook का "event"
                st_text, st_t = ep.get("hook_stamp") or "अधपकी खबर!", 0
            if bool(ln.get("punch")) and not react and not st_text and t >= n * 0.6:
                st_text = ln.get("stamp") or STAMP_OF.get(ln.get("react_pose"), "")
                st_t = 0
            asking = False                                      # सवाल अब सिर्फ़ अंत में (पंच line साफ़ सुनाई-दिखाई दे)
            if st_text and not asking and shot != "story":                          # सवाल वाले पल ठप्पा नहीं (ऊपर एक-दूसरे पर चढ़ते थे)
                if si == 0:                                     # hook का ठप्पा: hook के बड़े अक्षरों के नीचे, बीच में
                    _stamp(im, st_text, st_t, W / 2, 640 if shot != "split" else SCR[2] - 160, 48)
                elif shot == "close":
                    _stamp(im, st_text, st_t, W / 2 + 60, 1080, 62)  # chest, never across face
                else:
                    _stamp(im, st_text, st_t, SCR[2] - 200, SCR[1] + 120)
                st_t += 1
                d = ImageDraw.Draw(im)
            if asking:
                _ask(d, ep["ask"], t, 300 if shot == "split" else 1040)
            if shot == "split" and not react:
                pass                                             # नीचे की पट्टी Instagram caption के नीचे छिपती थी — हटाई
            d.rectangle((0, H - 12, int(W * k / total), H), fill=YEL)
            if react and t < 5 and prev_im is not None:        # बोलने से reaction में झटके से नहीं, घुलकर
                im = Image.blend(prev_im, im, (t + 1) / 6)
            wr.stdin.write(im.tobytes())
            k += 1
        prev_im = im
    end = im                                             # आख़िरी पंच वाला frame ही थोड़ा रुके (loop: सीधे शुरू से जुड़े)
    for t in range(tailn):
        im = end.copy()
        d = ImageDraw.Draw(im)
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
