"""
Step 5: script.json + audio/*.wav → 1080x1920 reel (MP4).

किरदार code से बनते हैं (original cartoon), हर reel में वही किरदार दिखेंगे.
- बोलने वाले का मुँह आवाज़ के साथ खुलता-बंद होता है
- बीच-बीच में आँख झपकती है
- punchline पर कैमरा zoom-in
- शब्द-दर-शब्द captions (बिना आवाज़ वालों के लिए)
- ऊपर हमेशा BREAKING पट्टी, नीचे चलती ticker
"""
import json
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile

ROOT = Path(__file__).parent
AUDIO = ROOT / "audio"
W, H, FPS, SS = 1080, 1920, 25, 2          # SS = supersampling (चिकने किनारे)
FONT_B = str(Path(__file__).parent / "fonts/Poppins-Bold.ttf")
FONT_M = str(Path(__file__).parent / "fonts/Poppins-Medium.ttf")
RAQM = ImageFont.Layout.RAQM


def font(size, bold=True):
    return ImageFont.truetype(FONT_B if bold else FONT_M, size, layout_engine=RAQM)


# ---------------------------------------------------------------- drawing helpers
class Pen:
    """1080x1920 के निर्देशांक में लिखो, अंदर 2x पर बनता है।"""
    def __init__(self, img):
        self.d = ImageDraw.Draw(img)

    def s(self, pts):
        return [v * SS for v in pts]

    def ell(self, box, fill, outline=None, width=0):
        self.d.ellipse(self.s(box), fill=fill, outline=outline, width=width * SS)

    def rect(self, box, fill, r=0, outline=None, width=0):
        self.d.rounded_rectangle(self.s(box), radius=r * SS, fill=fill, outline=outline, width=width * SS)

    def poly(self, pts, fill, outline=None, width=0):
        self.d.polygon([(x * SS, y * SS) for x, y in pts], fill=fill, outline=outline, width=width * SS)

    def line(self, pts, fill, width):
        self.d.line([(x * SS, y * SS) for x, y in pts], fill=fill, width=width * SS, joint="curve")

    def arc(self, box, a0, a1, fill, width):
        self.d.arc(self.s(box), a0, a1, fill=fill, width=width * SS)

    def text(self, xy, txt, size, fill, anchor="mm", bold=True, stroke=0, stroke_fill=None):
        self.d.text((xy[0] * SS, xy[1] * SS), txt, font=font(size * SS, bold), fill=fill, anchor=anchor,
                    stroke_width=stroke * SS, stroke_fill=stroke_fill)


def rot_ellipse(cx, cy, rx, ry, ang, n=40):
    a = math.radians(ang)
    return [(cx + rx * math.cos(t) * math.cos(a) - ry * math.sin(t) * math.sin(a),
             cy + rx * math.cos(t) * math.sin(a) + ry * math.sin(t) * math.cos(a))
            for t in np.linspace(0, 2 * math.pi, n)]


def curve_horn(x0, y0, x1, y1, bulge, w0, w1, n=24):
    """घुमावदार सींग: एक मोटा से पतला होता चाप।"""
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    nx, ny = -dy / L, dx / L
    cx, cy = mx + nx * bulge, my + ny * bulge
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        px = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t ** 2 * x1
        py = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t ** 2 * y1
        tx = 2 * (1 - t) * (cx - x0) + 2 * t * (x1 - cx)
        ty = 2 * (1 - t) * (cy - y0) + 2 * t * (y1 - cy)
        tl = math.hypot(tx, ty) or 1
        wv = (w0 * (1 - t) + w1 * t) / 2
        left.append((px - ty / tl * wv, py + tx / tl * wv))
        right.append((px + ty / tl * wv, py - tx / tl * wv))
    return left + right[::-1]


# ---------------------------------------------------------------- characters
INK = (30, 24, 40)


def eyes(p, cx, cy, gap, r, blink, lid=0.0):
    for sx in (-1, 1):
        ex = cx + sx * gap
        if blink:
            p.line([(ex - r, cy), (ex + r, cy)], INK, 6)
            continue
        p.ell((ex - r, cy - r * 1.15, ex + r, cy + r * 1.15), "white", INK, 4)
        p.ell((ex - r * 0.45 + 4, cy - r * 0.45, ex + r * 0.45 + 4, cy + r * 0.55), INK)
        p.ell((ex - r * 0.12 + 8, cy - r * 0.3, ex + r * 0.12 + 8, cy - r * 0.05), "white")
        if lid:
            p.rect((ex - r - 4, cy - r * 1.25, ex + r + 4, cy - r * 1.15 + 2 * r * 1.15 * lid), (95, 98, 112))
            p.line([(ex - r, cy - r * 1.15 + 2 * r * 1.15 * lid), (ex + r, cy - r * 1.15 + 2 * r * 1.15 * lid)], INK, 5)


def mouth(p, cx, cy, w, open_):
    if open_:
        p.ell((cx - w * 0.5, cy - w * 0.22, cx + w * 0.5, cy + w * 0.42), (110, 20, 35), INK, 4)
        p.ell((cx - w * 0.28, cy + w * 0.12, cx + w * 0.28, cy + w * 0.38), (235, 110, 120))
    else:
        p.arc((cx - w * 0.5, cy - w * 0.35, cx + w * 0.5, cy + w * 0.25), 20, 160, INK, 6)


def mic(p, hx, hy, ang=-60, label=True):
    a = math.radians(ang)
    tip = (hx + 150 * math.cos(a), hy + 150 * math.sin(a))
    p.line([(hx, hy), tip], (40, 40, 48), 22)
    p.ell((tip[0] - 38, tip[1] - 38, tip[0] + 38, tip[1] + 38), (70, 70, 80), INK, 4)
    for k in (-18, 0, 18):
        p.line([(tip[0] - 26, tip[1] + k), (tip[0] + 26, tip[1] + k)], (110, 110, 120), 3)
    if label:
        bx, by = hx + 70 * math.cos(a), hy + 70 * math.sin(a)
        p.rect((bx - 46, by - 30, bx + 46, by + 30), (210, 30, 45), 8, INK, 3)
        p.text((bx, by + 2), "बकरा", 26, "white")
    p.ell((hx - 34, hy - 30, hx + 34, hy + 34), (245, 235, 225), INK, 4)


def goat(p, cx, cy, s, mouth_open, blink, mic_ang=-60):
    """बबलू बकरा — reporter. (cx, cy) = चेहरे का केंद्र, s = scale."""
    S = lambda v: v * s
    # शरीर: लाल blazer
    p.poly([(cx - S(190), cy + S(560)), (cx - S(150), cy + S(190)), (cx + S(150), cy + S(190)), (cx + S(190), cy + S(560))],
           (200, 35, 50), INK, 5)
    p.poly([(cx - S(60), cy + S(190)), (cx, cy + S(330)), (cx + S(60), cy + S(190))], "white", INK, 4)
    p.poly([(cx - S(16), cy + S(205)), (cx + S(16), cy + S(205)), (cx + S(24), cy + S(310)), (cx, cy + S(340)), (cx - S(24), cy + S(310))],
           (30, 70, 160), INK, 3)
    # सींग
    p.poly(curve_horn(cx - S(70), cy - S(130), cx - S(150), cy - S(300), S(-40), S(46), S(8)), (200, 170, 120), INK, 4)
    p.poly(curve_horn(cx + S(70), cy - S(130), cx + S(150), cy - S(300), S(40), S(46), S(8)), (200, 170, 120), INK, 4)
    # कान
    p.poly(rot_ellipse(cx - S(165), cy - S(40), S(95), S(36), 25), (225, 220, 210), INK, 4)
    p.poly(rot_ellipse(cx + S(165), cy - S(40), S(95), S(36), -25), (225, 220, 210), INK, 4)
    p.poly(rot_ellipse(cx - S(165), cy - S(40), S(65), S(18), 25), (240, 180, 180))
    p.poly(rot_ellipse(cx + S(165), cy - S(40), S(65), S(18), -25), (240, 180, 180))
    # सिर
    p.ell((cx - S(125), cy - S(170), cx + S(125), cy + S(170)), (248, 245, 238), INK, 5)
    # दाढ़ी
    p.poly([(cx - S(40), cy + S(150)), (cx + S(40), cy + S(150)), (cx, cy + S(250))], (235, 232, 222), INK, 4)
    # थूथन
    p.ell((cx - S(85), cy + S(30), cx + S(85), cy + S(160)), (245, 205, 200), INK, 4)
    p.ell((cx - S(40), cy + S(55), cx - S(18), cy + S(80)), INK)
    p.ell((cx + S(18), cy + S(55), cx + S(40), cy + S(80)), INK)
    # माथे पर बाल
    p.poly([(cx - S(50), cy - S(160)), (cx, cy - S(205)), (cx + S(10), cy - S(150)), (cx + S(55), cy - S(185)), (cx + S(45), cy - S(140))],
           (120, 85, 60), INK, 3)
    eyes(p, cx, cy - S(45), S(58), S(34), blink)
    mouth(p, cx, cy + S(118), S(70), mouth_open)
    mic(p, cx + S(170), cy + S(330), mic_ang)


def buffalo(p, cx, cy, s, mouth_open, blink):
    """चाचा भैंसा — आम आदमी, हाथ में चाय।"""
    S = lambda v: v * s
    p.poly([(cx - S(230), cy + S(600)), (cx - S(190), cy + S(200)), (cx + S(190), cy + S(200)), (cx + S(230), cy + S(600))],
           (245, 242, 230), INK, 5)                                           # कुर्ता
    p.rect((cx - S(175), cy + S(185), cx + S(175), cy + S(245)), (240, 140, 40), S(28), INK, 4)   # गमछा
    p.rect((cx - S(150), cy + S(220), cx - S(90), cy + S(420)), (240, 140, 40), S(20), INK, 4)
    for k in range(3):
        p.line([(cx - S(150), cy + S(260 + 50 * k)), (cx - S(90), cy + S(260 + 50 * k))], (200, 60, 40), 4)
    p.poly(curve_horn(cx - S(110), cy - S(110), cx - S(300), cy - S(40), S(-120), S(60), S(10)), (170, 160, 140), INK, 4)
    p.poly(curve_horn(cx + S(110), cy - S(110), cx + S(300), cy - S(40), S(120), S(60), S(10)), (170, 160, 140), INK, 4)
    p.poly(rot_ellipse(cx - S(185), cy - S(10), S(60), S(28), 15), (70, 72, 84), INK, 4)
    p.poly(rot_ellipse(cx + S(185), cy - S(10), S(60), S(28), -15), (70, 72, 84), INK, 4)
    p.ell((cx - S(150), cy - S(160), cx + S(150), cy + S(150)), (80, 83, 96), INK, 5)
    p.ell((cx - S(115), cy + S(20), cx + S(115), cy + S(200)), (140, 130, 135), INK, 4)
    p.ell((cx - S(55), cy + S(70), cx - S(25), cy + S(105)), INK)
    p.ell((cx + S(25), cy + S(70), cx + S(55), cy + S(105)), INK)
    eyes(p, cx, cy - S(50), S(62), S(30), blink, lid=0.45)                   # आधी बंद आँखें
    mouth(p, cx, cy + S(160), S(80), mouth_open)
    # चाय का गिलास
    gx, gy = cx + S(250), cy + S(330)
    p.poly([(gx - S(45), gy - S(70)), (gx + S(45), gy - S(70)), (gx + S(35), gy + S(60)), (gx - S(35), gy + S(60))],
           (230, 240, 245), INK, 4)
    p.poly([(gx - S(41), gy - S(30)), (gx + S(41), gy - S(30)), (gx + S(35), gy + S(56)), (gx - S(35), gy + S(56))], (190, 120, 60))
    for k in (-20, 5, 30):
        p.arc((gx + S(k) - S(14), gy - S(150), gx + S(k) + S(14), gy - S(95)), 90, 270, (180, 180, 190), 4)
    p.ell((gx - S(80), gy - S(10), gx - S(20), gy + S(50)), (80, 83, 96), INK, 4)


def cat(p, cx, cy, s, mouth_open, blink):
    """पिंकी बिल्ली — Gen Z, धूप का चश्मा और फ़ोन।"""
    S = lambda v: v * s
    p.poly([(cx - S(190), cy + S(560)), (cx - S(150), cy + S(180)), (cx + S(150), cy + S(180)), (cx + S(190), cy + S(560))],
           (240, 120, 170), INK, 5)                                           # hoodie
    p.arc((cx - S(80), cy + S(160), cx + S(80), cy + S(260)), 0, 180, INK, 5)
    for sx in (-1, 1):
        p.poly([(cx + sx * S(40), cy - S(120)), (cx + sx * S(150), cy - S(250)), (cx + sx * S(140), cy - S(70))], (245, 150, 60), INK, 5)
        p.poly([(cx + sx * S(65), cy - S(115)), (cx + sx * S(135), cy - S(200)), (cx + sx * S(128), cy - S(95))], (250, 190, 200))
    p.ell((cx - S(150), cy - S(150), cx + S(150), cy + S(140)), (245, 150, 60), INK, 5)
    p.ell((cx - S(90), cy + S(10), cx + S(90), cy + S(125)), (255, 245, 235), INK, 3)
    for sx in (-1, 1):
        for k in (-12, 8):
            p.line([(cx + sx * S(70), cy + S(60 + k)), (cx + sx * S(180), cy + S(45 + k * 2))], INK, 3)
    p.poly([(cx - S(16), cy + S(30)), (cx + S(16), cy + S(30)), (cx, cy + S(50))], (230, 90, 110), INK, 3)
    # चश्मा (आँखें ढकीं)
    p.rect((cx - S(125), cy - S(80), cx - S(15), cy - S(15)), (25, 25, 35), S(18), INK, 4)
    p.rect((cx + S(15), cy - S(80), cx + S(125), cy - S(15)), (25, 25, 35), S(18), INK, 4)
    p.line([(cx - S(15), cy - S(55)), (cx + S(15), cy - S(55))], INK, 6)
    p.line([(cx - S(100), cy - S(65)), (cx - S(70), cy - S(45))], (120, 120, 140), 4)
    mouth(p, cx, cy + S(85), S(60), mouth_open)
    # फ़ोन
    fx, fy = cx - S(250), cy + S(300)
    p.rect((fx - S(45), fy - S(85), fx + S(45), fy + S(85)), (40, 40, 55), S(14), INK, 4)
    p.rect((fx - S(35), fy - S(70), fx + S(35), fy + S(70)), (120, 200, 255), S(8))
    p.ell((fx - S(5), fy + S(30), fx + S(65), fy + S(95)), (245, 150, 60), INK, 4)


# ---------------------------------------------------------------- backgrounds
def gradient(top, bottom):
    t = np.linspace(0, 1, H * SS)[:, None, None]
    arr = (np.array(top) * (1 - t) + np.array(bottom) * t).astype(np.uint8)
    return Image.fromarray(np.repeat(arr, W * SS, axis=1), "RGB")


ICONS = ["₹", "DA", "%"]


def bg_studio():
    img = gradient((18, 32, 78), (8, 12, 30))
    p = Pen(img)
    for i, x in enumerate((90, 380, 670)):
        p.rect((x, 470, x + 320, 760), (30, 60, 130), 18, (70, 110, 200), 4)
        p.text((x + 160, 615), ICONS[i], 120 if len(ICONS[i]) < 3 else 80, (90, 140, 230))
    p.rect((0, 1290, W, 1460), (150, 25, 40), 0)                          # desk
    p.rect((0, 1290, W, 1306), (230, 190, 90), 0)
    p.text((W / 2, 1385), "बकरा न्यूज़", 64, (255, 230, 150))
    return img


def bg_mohalla(sign, sign_color, sx=560):
    img = gradient((120, 190, 245), (255, 220, 170))
    p = Pen(img)
    p.ell((800, 420, 980, 600), (255, 210, 80))
    houses = [(0, 640, 260, 1300, (230, 160, 120)), (240, 560, 520, 1300, (150, 200, 170)),
              (500, 680, 780, 1300, (240, 210, 130)), (760, 600, 1080, 1300, (200, 160, 210))]
    for x0, y0, x1, y1, c in houses:
        p.rect((x0, y0, x1, y1), c, 0, INK, 4)
        for wx in range(x0 + 40, x1 - 60, 110):
            p.rect((wx, y0 + 60, wx + 60, y0 + 140), (90, 130, 170), 6, INK, 3)
    p.line([(0, 600), (1080, 560)], (60, 60, 60), 4)                     # बिजली का तार
    p.rect((0, 1300, W, 1920), (190, 160, 120), 0)
    p.rect((sx, 430, sx + 440, 540), sign_color, 14, INK, 5)
    p.text((sx + 220, 487), sign, 54, "white")
    return img


# ---------------------------------------------------------------- overlays
def overlay_static(headline):
    """ऊपर logo + BREAKING पट्टी (हर frame पर एक जैसी)।"""
    img = Image.new("RGBA", (W, 420), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 170), fill=(12, 14, 26, 235))
    d.rounded_rectangle((36, 40, 120, 124), radius=16, fill=(210, 30, 45))
    d.text((78, 84), "ब", font=font(58), fill="white", anchor="mm")
    d.text((142, 60), "बकरा न्यूज़", font=font(54), fill="white", anchor="lm")
    d.text((144, 122), "सबसे तेज़, सबसे अधपकी खबर", font=font(30, False), fill=(255, 210, 120), anchor="lm")
    d.rounded_rectangle((860, 58, 1040, 112), radius=10, fill=(210, 30, 45))
    d.ellipse((884, 76, 904, 96), fill="white")
    d.text((965, 86), "LIVE", font=font(32), fill="white", anchor="mm")
    d.rectangle((0, 196, 300, 270), fill=(255, 205, 40))
    d.text((150, 234), "BREAKING", font=font(44), fill=(150, 0, 20), anchor="mm")
    d.rectangle((0, 270, W, 390), fill=(200, 20, 40))
    f = font(52)
    while d.textlength(headline, font=f) > W - 60:
        f = font(f.size - 2)
    d.text((W / 2, 330), headline, font=f, fill="white", anchor="mm")
    return img


def ticker_strip(msg):
    msg = "   •   " + msg
    f = font(40)
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    tw = int(tmp.textbbox((0, 45), msg, font=f, anchor="lm")[2]) + 40
    one = Image.new("RGB", (tw, 90), (12, 14, 26))
    ImageDraw.Draw(one).text((0, 45), msg, font=f, fill="white", anchor="lm")
    img = Image.new("RGB", (tw * 2 + W, 90), (12, 14, 26))
    for k in (0, tw, 2 * tw):
        img.paste(one, (k, 0))
    return img, tw


# ---------------------------------------------------------------- scene renderer with cache
SCENES = {
    "studio": lambda: bg_studio(),
    "studio_end": lambda: bg_studio(),
    "chacha": lambda: bg_mohalla("चाचा टी स्टॉल", (150, 60, 40)),
    "pinky": lambda: bg_mohalla("Free Wi-Fi Zone", (60, 90, 200)),
    "dadi_call": lambda: bg_studio(),
    "riya_call": lambda: bg_studio(),
    "bunty_call": lambda: bg_studio(),
    "riya_live": lambda: bg_mohalla("Free Wi-Fi Zone", (60, 90, 200)),
    "riya": lambda: bg_mohalla("Free Wi-Fi Zone", (60, 90, 200), sx=40),
}

_street = {}


def street_sprite(who, expr, mouth, height=900):
    """3D किरदार को सड़क वाले scene में खड़ा करने के लिए (पैर ज़मीन पर)."""
    key = (who, expr, mouth, height)
    if key not in _street:
        p = ROOT / "assets" / who / f"{expr}_{mouth}.webp"
        if not p.exists():
            p = ROOT / "assets" / who / f"{expr}_closed.webp"
        if not p.exists():
            p = ROOT / "assets" / who / "neutral_closed.webp"
        im = Image.open(p).convert("RGBA")
        im = im.resize((int(im.width * height / im.height), height), Image.LANCZOS)
        sh = Image.new("RGBA", (im.width, 60), (0, 0, 0, 0))   # पैरों के नीचे परछाईं
        ImageDraw.Draw(sh).ellipse((im.width * 0.2, 10, im.width * 0.8, 50), fill=(0, 0, 0, 70))
        _street[key] = (im, sh)
    return _street[key]


# ---------------------------------------------------------------- 3D रिया: Instagram LIVE
LIVE_COMMENTS = ["mummy same karti hai", "relatable 100%", "didi sahi bola", "mera ghar exact yahi",
                 "tag kar raha hu bhai ko", "hahaha sach", "ye to har ghar ki kahani", "papa dekh lo"]


def live_window(expr, mouth, who="riya"):
    key = ("live", who, expr, mouth)
    if key in _call_cache:
        return _call_cache[key]
    x0, y0, x1, y1 = CALL
    w, h = x1 - x0, y1 - y0 + 80
    home = Image.open(ROOT / "assets" / "dadi" / "home.jpg").convert("RGB")
    home = home.resize((w, int(home.height * w / home.width))).crop((0, 120, w, 120 + h))
    ch = Image.open(ROOT / "assets" / who / f"{expr}_{mouth}.webp").convert("RGBA")
    home.paste(ch, (w // 2 - ch.width // 2 + 10, 110), ch)
    win = Image.new("RGBA", (w + 24, h + 24), (0, 0, 0, 0))
    g = Image.new("RGBA", win.size)
    gd = ImageDraw.Draw(g)
    for yy in range(win.height):                      # Instagram gradient border
        k = yy / win.height
        gd.line([(0, yy), (win.width, yy)], fill=(int(250 - 40 * k), int(80 + 60 * k), int(150 + 80 * k), 255))
    m = Image.new("L", win.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, win.width - 1, win.height - 1), 40, fill=255)
    win.paste(g, (0, 0), m)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), 30, fill=255)
    win.paste(home, (12, 12), mask)
    d = ImageDraw.Draw(win)
    d.ellipse((34, 34, 104, 104), fill=(255, 255, 255), outline=(240, 90, 160), width=6)
    d.text((69, 69), "R", font=font(40), fill=(230, 80, 150), anchor="mm")
    d.text((120, 56), "riya.ki.reels", font=font(34), fill="white", anchor="lm", stroke_width=3, stroke_fill=(0, 0, 0))
    d.rounded_rectangle((120, 80, 210, 120), 10, fill=(230, 30, 90))
    d.text((165, 100), "LIVE", font=font(28), fill="white", anchor="mm")
    d.rounded_rectangle((222, 80, 360, 120), 10, fill=(0, 0, 0, 140))
    d.text((291, 100), "2.4K देख रहे", font=font(24, False), fill="white", anchor="mm")
    _call_cache[key] = win
    return win


def live_overlay(frame, ox, oy, ww, hh, t):
    """तैरते दिल + नीचे चलते comments."""
    d = ImageDraw.Draw(frame)
    for k in range(6):
        ph = (t * 0.6 + k / 6) % 1.0
        x = ox + ww - 90 + 30 * math.sin(ph * 6 + k)
        y = oy + hh - 120 - ph * 520
        s = 26 * (1 - ph * 0.4)
        col = [(255, 60, 110), (255, 120, 170), (255, 200, 60)][k % 3]
        d.ellipse((x - s, y - s, x, y), fill=col)
        d.ellipse((x - 4, y - s, x + s - 4, y), fill=col)
        d.polygon([(x - s, y - s / 2), (x + s - 4, y - s / 2), (x - 2, y + s * 0.9)], fill=col)
    base = int(t * 0.9)
    for j in range(3):
        txt = LIVE_COMMENTS[(base + j) % len(LIVE_COMMENTS)]
        yy = oy + hh - 230 + j * 62
        tw = d.textlength(txt, font=font(28, False))
        d.rounded_rectangle((ox + 30, yy, ox + 60 + tw, yy + 48), 22, fill=(0, 0, 0))
        d.text((ox + 45, yy + 24), txt, font=font(28, False), fill="white", anchor="lm")


# ---------------------------------------------------------------- 3D दादी: खराब नेटवर्क वाली video call
CALL = (330, 420, 1050, 1270)            # window: x0, y0, x1, y1
_call_cache = {}


CALL_TITLE = {"dadi": "Video Call • दादी (घर से)", "riya": "Video Call • रिया (कॉलेज से)",
              "bunty": "Video Call • बंटी (स्टार्टअप ऑफ़िस से)"}


def dadi_window(expr, mouth, glitch=0, who="dadi"):
    key = (who, expr, mouth, glitch)
    if key in _call_cache:
        return _call_cache[key]
    x0, y0, x1, y1 = CALL
    w, h = x1 - x0, y1 - y0
    home = Image.open(ROOT / "assets" / "dadi" / "home.jpg").convert("RGB")
    home = home.resize((w, int(home.height * w / home.width))).crop((0, 200, w, 200 + h))
    ch = Image.open(ROOT / "assets" / who / f"{expr}_{mouth}.webp").convert("RGBA")
    if who != "dadi":                                  # लंबे किरदार: थोड़ा छोटा, चेहरा ऊपर
        ch = ch.resize((int(ch.width * 0.9), int(ch.height * 0.9)), Image.LANCZOS)
    home.paste(ch, (w // 2 - ch.width // 2 + 20, 120 if who == "dadi" else 60), ch)
    if glitch:                                        # pixel वाला कमज़ोर नेटवर्क
        sm = home.resize((w // (6 * glitch), h // (6 * glitch)), Image.NEAREST)
        home = sm.resize((w, h), Image.NEAREST)
    win = Image.new("RGBA", (w + 16, h + 86), (0, 0, 0, 0))
    d = ImageDraw.Draw(win)
    d.rounded_rectangle((0, 0, w + 15, h + 85), 26, fill=(245, 245, 245, 255))
    d.rounded_rectangle((8, 8, w + 7, 70), 18, fill=(30, 140, 70, 255))
    d.text((30, 39), CALL_TITLE.get(who, "Video Call"), font=font(34), fill="white", anchor="lm")
    for k in range(4):                                # signal: सिर्फ़ 1 डंडी
        c = (255, 255, 255) if k == 0 else (110, 170, 130)
        d.rectangle((w - 70 + k * 14, 52 - k * 9, w - 61 + k * 14, 56), fill=c)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), 18, fill=255)
    win.paste(home, (8, 78), mask)
    if glitch:
        ImageDraw.Draw(win).text((w // 2 + 8, h // 2 + 78), "कनेक्ट हो रहा है…", font=font(44),
                                 fill="white", anchor="mm", stroke_width=5, stroke_fill="black")
    _call_cache[key] = win
    return win
_bg, _cache = {}, {}


def scene_frame(scene, speaker, mouth_open, blink):
    key = (scene, speaker, mouth_open, blink)
    if key in _cache:
        return _cache[key]
    if scene not in _bg:
        _bg[scene] = SCENES[scene]()
    img = _bg[scene].copy()
    p = Pen(img)
    if scene == "riya":
        goat(p, 250, 960, 0.72, speaker == "bablu" and mouth_open, blink, mic_ang=-30)
    elif scene == "riya_live":
        goat(p, 190, 1000, 0.62, speaker == "bablu" and mouth_open, blink, mic_ang=-45)
    elif scene.endswith("_call"):
        goat(p, 190, 1000, 0.62, speaker == "bablu" and mouth_open, blink, mic_ang=-45)
        p.rect((0, 1290, W, 1460), (150, 25, 40), 0)
        p.rect((0, 1290, W, 1306), (230, 190, 90), 0)
        p.text((W / 2, 1385), "बकरा न्यूज़", 64, (255, 230, 150))
    elif scene.startswith("studio"):
        goat(p, 540, 880, 1.05, speaker == "bablu" and mouth_open, blink, mic_ang=-75)
        p.rect((0, 1290, W, 1460), (150, 25, 40), 0)                        # desk आगे
        p.rect((0, 1290, W, 1306), (230, 190, 90), 0)
        p.text((W / 2, 1385), "बकरा न्यूज़", 64, (255, 230, 150))
    else:
        guest = buffalo if scene == "chacha" else cat
        guest(p, 720, 870, 0.95, speaker != "bablu" and mouth_open, blink)
        goat(p, 250, 960, 0.72, speaker == "bablu" and mouth_open, blink, mic_ang=-30)
    out = img.resize((W, H), Image.LANCZOS)
    _cache[key] = out
    return out


_badge = {}


def insta_badge(name, age):
    if name not in _badge:
        f = font(40)
        txt = f"INSTA TREND • {name}"
        tw = int(ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(txt, font=f))
        img = Image.new("RGBA", (tw + 80, 84), (0, 0, 0, 0))
        g = Image.new("RGBA", img.size)
        gd = ImageDraw.Draw(g)
        for x in range(img.width):                       # Instagram जैसा gradient
            k = x / img.width
            gd.line([(x, 0), (x, 84)], fill=(int(250 - 60 * k), int(60 + 20 * k), int(120 + 100 * k), 255))
        m = Image.new("L", img.size, 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, img.width - 1, 83), 42, fill=255)
        img.paste(g, (0, 0), m)
        ImageDraw.Draw(img).text((40, 42), txt, font=f, fill="white", anchor="lm")
        _badge[name] = img
    img = _badge[name]
    s = min(1.0, age / 0.18)
    if s < 1:
        img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))))
    return img, (W // 2 - img.width // 2, 1366), img


# ---------------------------------------------------------------- captions
def caption_layer(words, active):
    """3-5 शब्दों का टुकड़ा, बोला जा रहा शब्द पीला।"""
    img = Image.new("RGBA", (W, 330), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font(70)
    lines, cur = [], []
    for i, w in enumerate(words):
        test = " ".join(x for x, _ in cur + [(w, i)])
        if cur and d.textlength(test, font=f) > W - 120:
            lines.append(cur)
            cur = []
        cur.append((w, i))
    lines.append(cur)
    y = 165 - (len(lines) - 1) * 52
    for ln in lines:
        total = d.textlength(" ".join(w for w, _ in ln), font=f)
        x = (W - total) / 2
        for w, i in ln:
            col = (255, 220, 40) if i == active else "white"
            d.text((x, y), w, font=f, fill=col, anchor="lm", stroke_width=7, stroke_fill=(0, 0, 0))
            x += d.textlength(w + " ", font=f)
        y += 104
    return img


def chunk_words(caption):
    words = caption.split()
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 4 or w[-1] in "!?।,":
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return chunks


# ---------------------------------------------------------------- audio helpers
def read_wav(path):
    sr, a = wavfile.read(path)
    a = a.astype(np.float32) / 32768.0
    return sr, a


def tone(sr, freqs, dur, vol=0.25, sweep=None):
    t = np.arange(int(sr * dur)) / sr
    env = np.minimum(1, t * 40) * np.exp(-t * 4)
    out = np.zeros_like(t)
    for f in freqs:
        ph = 2 * np.pi * (f * t + (0.5 * sweep * t ** 2 if sweep else 0))
        out += np.sin(ph)
    return (out / len(freqs) * env * vol).astype(np.float32)


def bed_music(sr, dur):
    """धीमा background loop (code से बना, copyright-free)।"""
    t = np.arange(int(sr * dur)) / sr
    chords = [(220, 277, 330), (196, 247, 294), (174, 220, 262), (196, 247, 294)]
    out = np.zeros_like(t)
    for i, ch in enumerate(chords * int(dur // 8 + 2)):
        s0, s1 = int(i * 2 * sr), int((i + 1) * 2 * sr)
        if s0 >= len(t):
            break
        seg = t[s0:s1] - t[s0]
        env = np.minimum(1, seg * 3) * np.minimum(1, (2 - seg) * 3)
        for f in ch:
            out[s0:s1] += np.sin(2 * np.pi * f * seg) * env[: len(seg)]
        beat = (np.mod(seg, 0.5) < 0.04) * np.sin(2 * np.pi * 70 * seg) * 2
        out[s0:s1] += beat
    return (out / 6 * 0.08).astype(np.float32)


# ---------------------------------------------------------------- main
def main(path="script.json", outname="bakra_news_demo.mp4"):
    global ICONS
    script = json.load(open(ROOT / path, encoding="utf-8"))
    ICONS = script.get("icons", ICONS)
    sr = 24000
    clips, timeline, cursor = [], [], 0.0
    sting = tone(sr, [523, 659, 784], 0.7, 0.3)
    clips.append((0.0, sting))
    cursor = 0.75
    for i, line in enumerate(script["lines"]):
        _, a = read_wav(AUDIO / f"{i:02d}.wav")
        # शुरू-आख़िर की खामोशी काटो
        nz = np.where(np.abs(a) > 0.02)[0]
        a = a[max(0, nz[0] - 600): nz[-1] + 1200] if len(nz) else a
        dur = len(a) / sr
        timeline.append({**line, "start": cursor, "end": cursor + dur, "audio": a})
        clips.append((cursor, a))
        cursor += dur
        if line.get("punch"):
            clips.append((cursor + 0.05, tone(sr, [330], 0.45, 0.25, sweep=-500)))   # "बोइंग"
            cursor += 0.55
        else:
            cursor += 0.22
    total = cursor + 1.6                                                       # आख़िरी card
    mix = np.zeros(int(total * sr) + sr, np.float32)
    for st, a in clips:
        s0 = int(st * sr)
        mix[s0: s0 + len(a)] += a
    mix += bed_music(sr, len(mix) / sr)[: len(mix)]
    mix = np.clip(mix / max(1, np.abs(mix).max() / 0.95), -1, 1)
    wavfile.write(ROOT / "mix.wav", sr, (mix * 32767).astype(np.int16))

    # हर frame पर आवाज़ की ताकत (मुँह खोलने के लिए)
    hop = sr // FPS
    def loud(seg, t):
        k = int((t - seg["start"]) * sr)
        w = seg["audio"][max(0, k - hop // 2): k + hop // 2]
        return float(np.sqrt(np.mean(w ** 2))) if len(w) else 0.0

    top = overlay_static(script["breaking"])
    tick, tw = ticker_strip(script.get("ticker", "DA 3% बढ़ सकता है   •   सूत्र: बबलू के चाचा"))
    nframes = int(total * FPS)
    frames_dir = ROOT / "frames"
    frames_dir.mkdir(exist_ok=True)
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(ROOT / "mix.wav"),
                             "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                             "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
                             str(ROOT / outname)], stdin=subprocess.PIPE)
    for fi in range(nframes):
        t = fi / FPS
        seg = next((s for s in timeline if s["start"] <= t < s["end"] + 0.25), None)
        if seg is None:
            seg = timeline[0] if t < timeline[0]["start"] else timeline[-1]
        speaking = seg["start"] <= t < seg["end"]
        mouth_open = speaking and loud(seg, t) > 0.035 and (fi % 3 != 0)
        blink = (fi % 90) in (0, 1, 2)
        frame = scene_frame(seg["scene"], seg["who"], mouth_open, blink).copy()
        if seg["scene"] == "riya":                     # 3D रिया सड़क पर, पिंकी की जगह
            talk = seg["who"] == "riya" and speaking
            if talk:
                lv = loud(seg, (fi - fi % 2) / FPS)
                rm = "open" if lv > 0.09 else "half" if lv > 0.035 else "closed"
                rex = seg.get("expr", "smug")
            else:
                rm, rex = "closed", "neutral"
            im, sh = street_sprite("riya", rex, rm)
            fx = 735 - im.width // 2
            frame.paste(sh, (fx, 1270), sh)
            frame.paste(im, (fx, 1300 - im.height), im)
        if seg["scene"] == "riya_live":
            talk = seg["who"] == "riya" and speaking
            if talk:
                lv = loud(seg, (fi - fi % 3) / FPS)
                dm = "open" if lv > 0.09 else "half" if lv > 0.035 else "closed"
                dex = seg.get("expr", "neutral")
            else:
                dm, dex = "closed", "smug"
            cs = next(s for s in timeline if s["scene"] == "riya_live")["start"]
            win = live_window(dex, dm)
            pop = min(1, (t - cs) / 0.25)
            if pop < 1:
                win = win.resize((max(1, int(win.width * pop)), max(1, int(win.height * pop))))
            ox = CALL[0] + (CALL[2] - CALL[0]) // 2 - win.width // 2
            oy = 402 + (954 - win.height) // 2
            frame.paste(win, (ox, oy), win)
            if pop >= 1:
                live_overlay(frame, ox, oy, win.width, win.height, t)
        if seg["scene"].endswith("_call"):
            cwho = seg["scene"][:-5]
            dadi_talk = seg["who"] == cwho and speaking
            if dadi_talk:
                lv = loud(seg, (fi - fi % 2) / FPS)            # 12 fps, सिर्फ़ मुँह बदलता है
                dm = "open" if lv > 0.09 else "half" if lv > 0.035 else "closed"
                dex = seg.get("expr", "neutral")
            else:
                dm, dex = "closed", "happy"
            cs = next(s for s in timeline if s["scene"] == seg["scene"])["start"]
            g = 2 if 0.0 <= t - cs < 0.5 else (1 if dadi_talk and 2.2 < t - seg["start"] < 2.45 else 0)
            win = dadi_window(dex, "closed" if g else dm, g, cwho)
            pop = min(1, (t - cs) / 0.25)
            if pop < 1:
                win = win.resize((max(1, int(win.width * pop)), max(1, int(win.height * pop))))
            frame.paste(win, (CALL[0] + (CALL[2] - CALL[0]) // 2 - win.width // 2,
                              CALL[1] + (CALL[3] - CALL[1]) // 2 - win.height // 2 + 30), win)

        # punchline पर धीरे-धीरे zoom-in
        if seg.get("punch") and t > seg["start"]:
            z = 1 + 0.12 * min(1, (t - seg["start"]) / max(0.5, seg["end"] - seg["start"]))
            cw, ch = int(W / z), int(H / z)
            x0, y0 = int(720 - cw / 2 + (W / 2 - 720) / z), int(880 - ch * 0.42)
            x0, y0 = max(0, min(W - cw, x0)), max(0, min(H - ch, y0))
            frame = frame.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BILINEAR)

        # ऊपर की पट्टी: पहले 0.6 सेकंड में ऊपर से फिसल कर आती है
        slide = int(-420 * max(0, 1 - t / 0.6))
        frame.paste(top, (0, slide), top)

        # captions
        if speaking:
            chunks = chunk_words(seg["caption"])
            nwords = sum(len(c) for c in chunks)
            prog = (t - seg["start"]) / (seg["end"] - seg["start"])
            # शब्द की लंबाई के हिसाब से समय बाँटो
            lens = [len(w) + 2 for c in chunks for w in c]
            cum = np.cumsum(lens) / sum(lens)
            wi = int(np.searchsorted(cum, prog))
            wi = min(wi, nwords - 1)
            base = 0
            for c in chunks:
                if wi < base + len(c):
                    cap = caption_layer(c, wi - base)
                    frame.paste(cap, (0, 1450), cap)
                    break
                base += len(c)

        # Insta trend वाली line पर गुलाबी badge
        if speaking and seg.get("insta"):
            frame.paste(*insta_badge(seg["insta"], t - seg["start"]))

        # आख़िरी card
        if t >= timeline[-1]["end"] + 0.2:
            d = ImageDraw.Draw(frame)
            d.rounded_rectangle((90, 1440, 990, 1760), radius=30, fill=(255, 205, 40), outline=(0, 0, 0), width=6)
            d.text((W / 2, 1530), "Follow करो", font=font(76), fill=(150, 0, 20), anchor="mm")
            d.text((W / 2, 1650), "कल की अधपकी खबर भी आएगी!", font=font(50), fill=(20, 20, 30), anchor="mm")

        # नीचे चलती ticker
        off = int((t * 160) % tw)
        frame.paste(tick.crop((off, 0, off + W, 90)), (0, H - 90))
        proc.stdin.write(frame.tobytes())
        if fi in (int(0.3 * FPS), int(timeline[0]["start"] * FPS) + 30, int(timeline[2]["start"] * FPS) + 40,
                  int(timeline[4]["end"] * FPS) - 5, nframes - 5):
            frame.save(frames_dir / f"f{fi:04d}.png")
    proc.stdin.close()
    proc.wait()
    print(f"बन गया: {outname} ({total:.1f}s, {nframes} frames)")


if __name__ == "__main__":
    import sys
    main(*(sys.argv[1:3] if len(sys.argv) > 1 else []))
