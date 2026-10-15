"""
Studio reel (3D किरदार, बिना retro): पूरा screen बड़ा किरदार नीले news studio में — होंठ SadTalker से आवाज़ के साथ,
हर line पर भाव वाली फ़ोटो, खबर का clip कंधे के पास छोटी TV-खिड़की में, punch पर zoom+ठप्पा, फिर reaction pose,
बड़े captions, आवाज़ें, आख़िर में poll.
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
EXPR = {"hasi": "happy", "gussa": "angry", "udaas": "sad", "hairan": "shock", "tanz": "smug", "": "neutral"}
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


def source_for(folder, expr, out, full=None):
    """SadTalker के लिए 720x1280 source; full दिया तो 1080x1920 वाली still भी."""
    p = pose_file(folder, expr)
    if p not in _cuts:
        _cuts[p] = cutout(p)
    compose(_cuts[p]).save(out)
    if full:
        compose(_cuts[p], W, H).save(full)


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


def render(ep, segs, chars, out, preview):
    """segs: [{"ln", "wav", "face" (video path या None), "still" (PIL 1080x1920), "vis" [Path|card], "react"}]"""
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
    k, stamp_i, last = 0, 0, None
    for si, (s, n) in enumerate(zip(segs, counts)):
        ln, react = s["ln"], s.get("react")
        punch = bool(ln.get("punch"))
        _, name, role = chars[ln["who"]]
        face = _frames(s["face"]) if s.get("face") else None
        vis = list(s.get("vis") or [])
        if ln.get("big") and len(vis) < 2 and not punch and not react:
            vis.append({"big": ln["big"], "sub": ln.get("sub", "")})
        per = max(1, n // max(1, len(vis)))
        vgen = None
        for t in range(n):
            if face:
                fr = next(face, None) or last or s["still"]
                last = fr
            else:
                fr = s["still"]
            if punch:
                z = 1.0 + 0.14 * min(1, t / 6)
            elif react:
                z = 1.04 + 0.04 * t / n
            else:
                z = (1.0 if si % 2 == 0 else 1.07) + 0.03 * t / n
            im = _zoom(fr, z)
            if punch and t < 6:
                im = im.transform(im.size, Image.AFFINE, (1, 0, (6 - t) * 5 * (-1) ** t, 0, 1, 0))
            d = ImageDraw.Draw(im)
            rv.chrome(d, k)
            hook = k < FPS * 2.5 and ep.get("hook")
            if vis and not hook:
                j = min(len(vis) - 1, t // per)
                if t % per == 0 and t // per < len(vis):
                    vgen = rv.visual_frames(vis[j], per if j < len(vis) - 1 else n - t, si * 3 + j)
                vf = next(vgen, None) if vgen else None
                if vf is not None:
                    inset(im, vf, ln.get("big") or ln.get("caption") or "")
                    d = ImageDraw.Draw(im)
            if hook:
                rows = rv._wrap(ep["hook"], tt.font(72), 980)[:3]
                d.rounded_rectangle((24, 130, W - 24, 150 + 92 * len(rows)), 26, fill=(255, 214, 0))
                for r, row in enumerate(rows):
                    d.text((W / 2, 186 + r * 92), row, font=tt.font(72), fill=(0, 0, 0), anchor="mm")
            if react:
                d.rounded_rectangle((40, 1440, 620, 1520), 20, fill=(225, 30, 45))
                d.text((70, 1480), f"{name} का रिएक्शन", font=tt.font(46), fill="white", anchor="lm")
            else:
                rv.name_strap(d, 1430, name, role)
                rv.karaoke(d, ln.get("caption") or ln["say"], t / n, 1720)
            if punch and t >= 4:
                rv.stamp(im, rv.STAMPS[stamp_i % len(rv.STAMPS)], t - 4)
                d = ImageDraw.Draw(im)
            d.rectangle((0, H - 12, int(W * k / total), H), fill=(255, 214, 0))
            wr.stdin.write(im.tobytes())
            k += 1
        if punch:
            stamp_i += 1
    end = (last or segs[-1]["still"]).filter(ImageFilter.GaussianBlur(8))
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
    wr.stdin.close()
    wr.wait()
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(out), "-vf",
                    f"fps={12 / max(1, total / FPS)},scale=216:-1,tile=6x2", "-frames:v", "1", str(preview)])
    return total / FPS
