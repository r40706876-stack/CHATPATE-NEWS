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


SETS = {"studio": ROOT / "assets/sets/studio.png", "village": ROOT / "assets/sets/village.png"}
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
    top = int(full.height * 0.30)
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


def source_for(folder, expr, out, full=None, setname=None):
    """SadTalker के लिए source = नीचे वाला हिस्सा (1080x888, चेहरा ~200px); full = वही still."""
    p = pose_file(folder, expr)
    if p not in _cuts:
        _cuts[p] = cutout(p)
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


def _base():
    y = np.linspace(0, 1, H)[:, None, None]
    g = np.array((10, 16, 40))[None, None] * (1 - y) + np.array((24, 34, 80))[None, None] * y
    im = Image.fromarray(np.repeat(g, W, axis=1).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((SCR[0] - 9, SCR[1] - 9, SCR[2] + 9, SCR[3] + STRAP + 9), 22, fill=(255, 214, 0))
    return im


def _num_card(card, t, seed):
    """कार्ड (कोई clip न मिले तब): अंक हो तो 0 से गिनती चढ़ती दिखे."""
    import re
    c = dict(card)
    m = re.search(r"\d[\d,]*", c.get("big", ""))
    if m and t < 20:
        n = int(m.group().replace(",", ""))
        e = 1 - (1 - t / 20) ** 3
        c["big"] = c["big"].replace(m.group(), f"{int(n * e):,}")
    return rv._cover_img(rv.card_frame(c, t, seed), SW_, SH_)


def _screen_gen(src, seed):
    """बड़ी screen के frames (कभी ख़त्म नहीं होते — अगली line तक चलते रहते हैं)."""
    if isinstance(src, Path) and src.suffix == ".mp4":
        got = False
        for f in rv._video_frames(src, SW_, SH_):
            got = True
            yield f
        if got:
            return
        src = {"big": ""}
    if isinstance(src, Path):
        im = Image.open(src).convert("RGB")
        t = 0
        while True:
            p = (t % 300) / 300
            z = 1.16 - 0.14 * p if seed % 2 else 1.02 + 0.14 * p
            yield rv._cover_img(im, SW_, SH_, z, 0.4)
            t += 1
    t = 0
    while True:
        yield _num_card(src or {}, t, seed)
        t += 1


def _credit(src):
    if isinstance(src, Path) and src.with_suffix(".txt").exists():
        return src.with_suffix(".txt").read_text(encoding="utf-8")[:70]
    return ""


def _band_frames(video):
    rd = subprocess.Popen(["ffmpeg", "-loglevel", "quiet", "-i", str(video), "-vf",
                           f"fps={FPS},scale={W}:{BAND_H}:force_original_aspect_ratio=increase,crop={W}:{BAND_H}",
                           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    while True:
        raw = rd.stdout.read(W * BAND_H * 3)
        if len(raw) < W * BAND_H * 3:
            return
        yield Image.frombuffer("RGB", (W, BAND_H), raw)


def _zoomb(im, z, fy=0.25):
    if z <= 1.001:
        return im
    cw, ch = W / z, BAND_H / z
    x0, y0 = (W - cw) / 2, (BAND_H - ch) * fy
    return im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, BAND_H), Image.BILINEAR)


def _stamp(im, text, t):
    s = 1.5 - 0.5 * min(1, t / 5)
    f = tt.font(int(64 * s))
    tw = int(f.getlength(text)) + 70
    lay = Image.new("RGBA", (tw + 20, int(130 * s)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((6, 6, tw + 14, lay.height - 6), 24, fill=(255, 214, 0, 255), outline=(0, 0, 0, 255), width=6)
    d.text(((tw + 20) / 2, lay.height / 2), text, font=f, fill=(0, 0, 0), anchor="mm")
    lay = lay.rotate(6, expand=True, resample=Image.BICUBIC)
    im.paste(lay, (min(W - lay.width - 10, SCR[2] - lay.width + 20), SCR[1] + 70), lay)


def _headline(d, text):
    d.rectangle((SCR[0], SCR[3], SCR[2], SCR[3] + STRAP), fill=(225, 30, 45))
    f = tt.font(40)
    while f.getlength(text) > SW_ - 40 and f.size > 24:
        f = tt.font(f.size - 2)
    d.text((SCR[0] + 20, SCR[3] + STRAP / 2), text, font=f, fill="white", anchor="lm")


def render(ep, segs, chars, out, preview):
    """segs: [{"ln", "wav", "face" (video या None), "still" (PIL 1080x888), "vis" [Path], "react"}]"""
    lens = [rv._read(s["wav"]).shape[0] / rv.SR for s in segs]
    counts = [max(1, round(x * FPS)) for x in lens]
    tail = 2.6 if ep.get("poll") else 0.8
    tailn = int(tail * FPS)
    total = sum(counts) + tailn
    events, t0 = [(0.0, "boom")], 0.0
    for s, L in zip(segs, lens):
        if t0:
            events.append((t0, "boom" if s["ln"].get("punch") else "pop" if s.get("react") else "whoosh"))
        t0 += L
    events.append((t0, "ding"))
    rv.mix_audio([rv._read(s["wav"]) for s in segs], events, tail, out.with_suffix(".wav"))
    wr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", str(out.with_suffix(".wav")), "-c:v", "libx264", "-crf", "20",
                           "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", str(out)],
                          stdin=subprocess.PIPE)
    base = _base()
    headline = ep.get("breaking") or ep.get("title") or ""
    k, last, cur, credit, seed = 0, None, None, "", 0
    st_text, st_t = "", 0
    im = base
    for si, (s, n) in enumerate(zip(segs, counts)):
        ln, react = s["ln"], s.get("react")
        punch = bool(ln.get("punch"))
        _, name, role = chars[ln["who"]]
        face = _band_frames(s["face"]) if s.get("face") else None
        vis = list(s.get("vis") or [])
        if not vis and ln.get("big") and not react:
            vis = [{"big": ln["big"], "sub": ln.get("sub", "")}]
        if cur is None and not vis:
            vis = [{"big": headline}]
        per = max(1, n // max(1, len(vis)))
        if not react:
            st_text = ""
        for t in range(n):
            if vis and t % per == 0 and t // per < len(vis):
                j = t // per
                if cur is not None:
                    cur.close()
                seed += 1
                cur, credit = _screen_gen(vis[j], seed), _credit(vis[j])
            sf = next(cur, None)
            if sf is None:
                cur = _screen_gen({"big": headline}, seed)
                sf = next(cur)
            if face:
                fr = next(face, None) or last or s["still"]
                last = fr
            else:
                fr = s["still"]
            if punch:
                z = 1.0 + 0.12 * min(1, t / 6)
            elif react:
                z = 1.06
            else:
                z = 1.0 + 0.03 * t / n
            band = _zoomb(fr, z)
            im = base.copy()
            hook = k < FPS * 2.5 and ep.get("hook")
            im.paste(Image.blend(sf, Image.new("RGB", sf.size), 0.55) if hook else sf, (SCR[0], SCR[1]))
            im.paste(band, (0, BAND_Y))
            d = ImageDraw.Draw(im)
            rv.chrome(d, k)
            d.rounded_rectangle((SCR[0] + 16, SCR[1] + 16, SCR[0] + 196, SCR[1] + 66), 10, fill=(225, 30, 45))
            d.text((SCR[0] + 106, SCR[1] + 41), "ब्रेकिंग", font=tt.font(34), fill="white", anchor="mm")
            if credit:
                f = tt.font(22)
                cw = f.getlength(credit)
                d.rectangle((SCR[2] - cw - 24, SCR[3] - 38, SCR[2], SCR[3]), fill=(0, 0, 0))
                d.text((SCR[2] - 12, SCR[3] - 19), credit, font=f, fill=(220, 220, 220), anchor="rm")
            _headline(d, headline)
            if hook:
                rows = rv._wrap(ep["hook"], tt.font(70), 940)[:3]
                y0 = (SCR[1] + SCR[3]) // 2 - 15 - 44 * len(rows)
                d.rounded_rectangle((SCR[0] + 20, y0, SCR[2] - 20, y0 + 30 + 88 * len(rows)), 24, fill=(255, 214, 0))
                for r, row in enumerate(rows):
                    d.text((W / 2, y0 + 60 + r * 88), row, font=tt.font(70), fill=(0, 0, 0), anchor="mm")
            if react:
                d.rounded_rectangle((30, BAND_Y + 500, 560, BAND_Y + 576), 20, fill=(225, 30, 45))
                d.text((58, BAND_Y + 538), f"{name} का रिएक्शन", font=tt.font(44), fill="white", anchor="lm")
            else:
                rv.name_strap(d, BAND_Y + 490, name, role)
                rv.karaoke(d, ln.get("caption") or ln["say"], t / n, 1716)
            if punch and not st_text and t >= n * 0.55:
                st_text = ln.get("stamp") or STAMP_OF.get(ln.get("react_pose"), "")
                st_t = 0
            if st_text:
                _stamp(im, st_text, st_t)
                st_t += 1
                d = ImageDraw.Draw(im)
            ticker(d, ep, k)
            d.rectangle((0, H - 12, int(W * k / total), H), fill=(255, 214, 0))
            wr.stdin.write(im.tobytes())
            k += 1
    end = im.filter(ImageFilter.GaussianBlur(8))
    for t in range(tailn):
        im = end.copy()
        d = ImageDraw.Draw(im)
        rv.chrome(d, k)
        if ep.get("poll"):
            rv.poll(d, ep["poll"], t)
        d.rounded_rectangle((260, 1420, W - 260, 1520), 50, fill=(225, 30, 45))
        d.text((W / 2, 1470), "फ़ॉलो करो • बकरा न्यूज़", font=tt.font(46), fill="white", anchor="mm")
        d.rectangle((0, H - 12, int(W * k / total), H), fill=(255, 214, 0))
        wr.stdin.write(im.tobytes())
        k += 1
    if cur is not None:
        cur.close()
    wr.stdin.close()
    wr.wait()
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(out), "-vf",
                    f"fps={12 / max(1, total / FPS)},scale=216:-1,tile=6x2", "-frames:v", "1", str(preview)])
    return total / FPS
