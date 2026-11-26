"""PostalEdge promo reel: didi's post-office video + Golu/Bhaiya (locked voices) + real course clips + offer."""
import json, math, os, sys, wave, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CORE = "/home/claude/postal-wala-core"
sys.path.insert(0, CORE)
from postal_edge_puppet import puppet
from postal_edge_lip_shapes import measure_mouth

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
FB = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
FM = "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"
MAROON = (125, 32, 40); GOLD = (255, 205, 60); NAVY = (23, 32, 72); CREAM = (255, 248, 236)

@lru_cache(None)
def font(sz, bold=True): return ImageFont.truetype(FB if bold else FM, sz)
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def back(x):
    x = clamp(x); c = 1.9; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def p(t, a, d): return ease((t - a) / d)
def pb(t, a, d): return back((t - a) / d) if t > a else 0.

# ---------------------------------------------------------------- timeline
REP = {x["i"]: x for x in json.load(open("voice/lines_report.json"))}
LINES = {x[0]: x for x in json.load(open("/home/claude/chatpate-news/oneoffs/promo_didi/lines.json"))}
def load_wav(path):
    w = wave.open(path); sr = w.getframerate()
    a = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float64) / 32768
    if w.getnchannels() == 2: a = a.reshape(-1, 2).mean(1)
    return a, sr
VO = {}
def voice(i, start):
    a, sr = load_wav(f"voice/line{i}.wav"); d = len(a) / sr
    VO[i] = dict(a=start, b=start + d, who=LINES[i][1], text=LINES[i][2], audio=a, sr=sr,
                 mouth=measure_mouth(a, FPS, d), words=REP[i]["words"])
    return start + d

SEG = []  # (kind, t0, t1, extra)
t = 0.0
SEG.append(("didi", 0.0, 6.35, dict(dir="didiA", src=0.0))); t = 6.35
T_SYL = t; e = voice(201, t + .12); t = e + .55; SEG.append(("syl", T_SYL, t, {}))
SEG.append(("didi", t, t + 9.7, dict(dir="didiB", src=21.3))); T_B = t; t += 9.7
T_SLEEP = t; e = voice(202, t + .1); t = e + .15; SEG.append(("sleep", T_SLEEP, t, {}))
T_CLASS = t; e = voice(203, t + .1); e = voice(204, e + .22); e = voice(205, e + .75); t = e + .2
SEG.append(("class", T_CLASS, t, {}))
T_COURSE = t; e = voice(206, t + .1); t = e + .2; SEG.append(("course", T_COURSE, t, {}))
T_PRICE = t; e = voice(207, t + .45); e = voice(208, e + .25); t = e + .45; SEG.append(("price", T_PRICE, t, {}))
T_C = t; SEG.append(("didi", t, t + 12.3, dict(dir="didiC", src=31.0))); t += 12.3
T_END = t; t += 2.6; SEG.append(("end", T_END, t, {}))
DUR = t

def W_(i, k):
    """time of the k-th whisper word of line i"""
    L = VO[i]; return L["a"] + L["words"][min(k, len(L["words"]) - 1)][1]

# clip windows inside the class scene
CL_TREE = (VO[203]["a"] - .1, W_(204, 6))          # until "घड़ी"
CL_CLOCK = (W_(204, 6), W_(204, 12))               # until "चाँद"
CL_MOON = (W_(204, 12), VO[205]["b"] + .25)

# didi captions (transcript)
DIDI_CAP = {
    "didiA": [(0.0, 6.35, "आप लोग काफी टाइम से पूछ रहे थे… क्या पढ़ें और कहाँ से?")],
    "didiB": [(0.0, 2.0, "अब सवाल आता है कि आख़िर पढ़ें कहाँ से?"), (2.0, 5.1, "प्रिपरेशन के लिए कई प्लेटफ़ॉर्म अवेलेबल हैं"),
              (5.1, 9.7, "लेकिन पोस्टल रूल्स पढ़ने में कई बार बोरिंग लगते हैं")],
    "didiC": [(0.0, 6.0, "आसान और इंटरेस्टिंग तरीके से समझना है? PostalEdge की वेबसाइट चेक करो"),
              (6.0, 9.6, "वेबसाइट का लिंक चाहिए? कमेंट में लिख दो"), (9.6, 12.3, "लिंक मेरी बायो में भी है")],
}

# ---------------------------------------------------------------- drawing helpers
def rrect(size, r, fill, outline=None, width=0):
    im = Image.new("RGBA", (int(size[0]), int(size[1])))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=fill, outline=outline, width=width)
    return im
def text_w(s, f): b = f.getbbox(s); return b[2] - b[0]
def chip(s, f, fg, bg, padx=26, h=None, outline=None):
    tw = text_w(s, f); hh = h or int(f.size * 1.75)
    c = rrect((tw + 2 * padx, hh), hh // 2, bg, outline, 4 if outline else 0)
    ImageDraw.Draw(c).text((c.width / 2, hh / 2 + f.size * .06), s, font=f, fill=fg, anchor="mm")
    return c
def shadowed(im, blur=22, off=(0, 14), alpha=110):
    pad = blur * 2 + max(abs(off[0]), abs(off[1]))
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad))
    sh = Image.new("RGBA", im.size, (0, 0, 0, alpha)); sh.putalpha(im.getchannel("A").point(lambda v: v * alpha // 255))
    out.alpha_composite(sh, (pad + off[0], pad + off[1])); out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(im, (pad, pad)); return out
def paste_center(dst, im, cx, cy, sc=1., rot=0., alpha=1.):
    if alpha <= 0.01 or sc <= 0.01: return
    if sc != 1: im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
    if rot: im = im.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 1: a = im.getchannel("A").point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    dst.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

@lru_cache(None)
def bg_still(name):
    im = Image.open(name).convert("RGB").filter(ImageFilter.GaussianBlur(16))
    arr = np.asarray(im).astype(np.float32) * .55
    yy, xx = np.mgrid[0:H, 0:W]; v = 1 - .55 * (((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 2.2
    arr = arr * np.clip(v, .35, 1)[..., None] + np.array([40, 8, 12]) * .35
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
def bg(name, t):
    b = bg_still(name); k = 1.04 + .015 * math.sin(t * .35)
    im = b.resize((int(W * k), int(H * k)), Image.BILINEAR)
    return im.crop(((im.width - W) // 2, (im.height - H) // 2, (im.width - W) // 2 + W, (im.height - H) // 2 + H))

LOGO = Image.open(f"{CORE}/site/icon.png").convert("RGBA").resize((70, 70), Image.LANCZOS)
lm = Image.new("L", LOGO.size); ImageDraw.Draw(lm).rounded_rectangle((0, 0, 69, 69), 18, fill=255); LOGO.putalpha(lm)
@lru_cache(None)
def brand_band():
    f1, f2 = font(34), font(30)
    s1, s2 = "PostalEdge", "by Postal Wala"
    s3 = "postaledge.in"
    w = 70 + 18 + text_w(s1, f1) + 12 + text_w(s2, font(24, False)) + 30 + text_w(s3, f2) + 70
    b = rrect((w, 96), 48, (125, 32, 40, 235), (255, 214, 90, 255), 3)
    d = ImageDraw.Draw(b); b.alpha_composite(LOGO, (14, 13)); x = 100
    d.text((x, 50), s1, font=f1, fill=(255, 255, 255), anchor="lm"); x += text_w(s1, f1) + 12
    d.text((x, 54), s2, font=font(24, False), fill=(255, 225, 180), anchor="lm"); x += text_w(s2, font(24, False)) + 22
    d.ellipse((x - 4, 46, x + 4, 54), fill=GOLD); x += 18
    g = chip(s3, f2, NAVY, GOLD, 18, 62); b.alpha_composite(g, (x, 17))
    return b

def caption(im, s, prog, cy, hl=GOLD, maxw=900, top=None):
    """word-by-word highlighted caption on a dark pill"""
    f = font(50); words = s.split(); lines = [[]];
    for w_ in words:
        trial = " ".join(lines[-1] + [w_])
        if lines[-1] and text_w(trial, f) > maxw - 60: lines.append([w_])
        else: lines[-1].append(w_)
    lh = 72; hgt = lh * len(lines) + 34; wid = max(text_w(" ".join(l), f) for l in lines) + 70
    box = rrect((wid, hgt), 30, (12, 14, 30, 200)); d = ImageDraw.Draw(box)
    total = sum(len(x) for x in words); cur = prog * total; seen = 0
    y = 17 + lh / 2
    for l in lines:
        x = (wid - text_w(" ".join(l), f)) / 2
        for w_ in l:
            done = seen + len(w_) <= cur; now = seen <= cur < seen + len(w_)
            col = hl if now else ((255, 255, 255) if done else (205, 208, 225))
            d.text((x, y + 4), w_, font=f, fill=col, anchor="lm"); x += text_w(w_ + " ", f); seen += len(w_)
        y += lh
    paste_center(im, box, W / 2, cy if top is None else top + box.height / 2)

def speaking(who, t):
    for L in VO.values():
        if L["who"] == who and L["a"] <= t < L["b"]:
            k = int((t - L["a"]) * FPS)
            if k < len(L["mouth"]): return tuple(L["mouth"][k])
    return None
def cur_line(t):
    for i, L in VO.items():
        if L["a"] - .05 <= t <= L["b"] + .15: return i
    return None

def char(im, is_golu, t, cx, foot_y, sc, mood="happy", gest="open", facing=0., air=0., alpha=1., glow=False):
    who = "golu" if is_golu else "bhaiya"
    sp = speaking(who, t)
    strength = 1. if sp is not None else .55
    pp = puppet(is_golu, t, 0, facing, sp, mood, (strength, gest), facing * .7, air, 0)
    if glow:
        g = Image.new("RGBA", (int(380 * sc), 110)); ImageDraw.Draw(g).ellipse((8, 22, g.width - 8, 96), fill=(255, 214, 90, 120))
        g = g.filter(ImageFilter.GaussianBlur(16)); im.alpha_composite(g, (int(cx - g.width / 2), int(foot_y - 62)))
    sh = Image.new("RGBA", (int(260 * sc), 50)); ImageDraw.Draw(sh).ellipse((0, 8, sh.width, 44), fill=(0, 0, 0, 90))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)), (int(cx - sh.width / 2), int(foot_y - 30)))
    paste_center(im, pp, cx, foot_y - 520 * sc / 2 + 18 * sc - 40 * air * sc, sc, 0, alpha)

@lru_cache(64)
def jpg(path): return Image.open(path).convert("RGBA")
def didi_frame(d, local):
    files = DIDI_FILES[d]; k = min(len(files) - 1, int(local * FPS)); return jpg(files[k]).copy()
DIDI_FILES = {d: sorted(os.path.join(d, f) for f in os.listdir(d)) for d in ("didiA", "didiB", "didiC")}
CLIPS = {c: sorted(os.path.join(c, f) for f in os.listdir(c)) for c in ("clip_tree", "clip_clock", "clip_moon")}
def clip_img(c, u):
    fs = CLIPS[c]; return Image.open(fs[min(len(fs) - 1, int(u * (len(fs) - 1)))]).convert("RGBA")

SYL_MTS = Image.open("syl_mts.png").convert("RGBA"); SYL_PM = Image.open("syl_pm.png").convert("RGBA")
def card_img(im, w):
    im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    m = Image.new("L", im.size); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), 22, fill=255)
    fr = rrect((im.width + 12, im.height + 12), 28, (255, 255, 255, 255)); fr.paste(im, (6, 6), m); return fr
SYL_CARDS = (card_img(SYL_MTS, 400), card_img(SYL_PM, 400))

# ---------------------------------------------------------------- scenes
def sticker(im, s, t, a, cx, cy, bgc=(255, 214, 70, 255), fg=NAVY, sz=46, rot=-4, d=.35):
    k = pb(t, a, d)
    if k > 0: paste_center(im, shadowed(chip(s, font(sz), fg, bgc, 28)), cx, cy, .3 + .7 * k, rot * (1 + .2 * math.sin(t * 3)))

def scene_didi(im, t, ex, t0):
    local = t - t0; im.alpha_composite(didi_frame(ex["dir"], local))
    # darken bottom for captions
    for c0, c1, s in DIDI_CAP[ex["dir"]]:
        if c0 <= local < c1: caption(im, s, (local - c0) / max(.5, c1 - c0), 1500)
    if ex["dir"] == "didiA":
        # Golu peeks in from the left edge, curious
        k = p(t, 2.0, .5)
        if k > 0:
            char(im, True, t, -140 + 340 * k, 1420, .74, "surprise", "chin", .6)
            paste_center(im, chip("?", font(80), MAROON, GOLD, 26), 150 + 190 * k, 930 - 18 * math.sin(t * 5), .9 * k)
    if ex["dir"] == "didiB":
        if local > 6.7:
            for i in range(3):
                ph = (local - 6.7 - i * .35)
                if ph > 0: paste_center(im, chip("Z", font(44 + 14 * i), (255, 255, 255), (60, 70, 150, 220), 16), 820 + 40 * i + 20 * math.sin(ph * 3), 620 - 60 * i - 25 * ph, 1, 8, clamp(1 - ph / 3))
            sticker(im, "बोरिंग PO Guide?", t, t0 + 7.2, W / 2, 1330, (255, 255, 255, 255), MAROON, 46)
    if ex["dir"] == "didiC":
        k = pb(t, t0 + 2.8, .45)
        if k > 0:
            g = shadowed(chip("postaledge.in", font(70), NAVY, GOLD, 40, 120, (255, 255, 255, 255)))
            paste_center(im, g, W / 2, 330, (.4 + .6 * k) * (1 + .03 * math.sin(t * 6)))
        if local > 6.0:
            sticker(im, "कमेंट करो: LINK", t, t0 + 6.1, W / 2, 470, (255, 255, 255, 255), MAROON, 44, 3)
        if local > 9.6:
            sticker(im, "लिंक बायो में भी", t, t0 + 9.7, W / 2, 590, (36, 170, 110, 255), (255, 255, 255), 44, -3)
        # small Golu & Bhaiya wave at the end
        k = p(t, t0 + 8.8, .5)
        if k > 0:
            char(im, True, t, 150, 1330 + 300 * (1 - k), .5, "happy", "welcome", .5)
            char(im, False, t, 905, 1330 + 300 * (1 - k), .52, "happy", "welcome", -.5)

def scene_syl(im, t, t0, t1):
    im.alpha_composite(bg("bg_8.png", t))
    for i, c in enumerate(SYL_CARDS):
        k = pb(t, t0 + .25 + .3 * i, .5)
        cx = 300 + 480 * i; rot = 6 - 12 * i
        if k > 0: paste_center(im, shadowed(c), cx, 760 - 80 * (1 - k), .55 + .45 * k, rot * k)
    sticker(im, "सेव करो · पूरा सिलेबस", t, t0 + 1.4, W / 2, 1210, sz=48)
    char(im, False, t, 790, 1610, .78, "happy", "left", -.6, glow=True)
    char(im, True, t, 250, 1615, .66, "surprise", "chin", .6)
    L = VO[201]; caption(im, L["text"], (t - L["a"]) / (L["b"] - L["a"]), 0, top=262)

def scene_sleep(im, t, t0, t1):
    im.alpha_composite(bg("bg_8.png", t))
    # big PO Guide book
    k = pb(t, t0 + .1, .45)
    book = rrect((420, 300), 24, (122, 30, 38, 255), (255, 214, 90, 255), 6)
    d = ImageDraw.Draw(book); d.text((210, 110), "PO GUIDE", font=font(58), fill=GOLD, anchor="mm"); d.text((210, 190), "Part I · 1985", font=font(34, False), fill=(255, 230, 200), anchor="mm")
    paste_center(im, shadowed(book), W / 2, 760, (.4 + .6 * k), -6 + 2 * math.sin(t * 2))
    for i in range(4):
        ph = t - (t0 + .6 + i * .45)
        if ph > 0: paste_center(im, chip("Z", font(50 + 12 * (i % 3)), (255, 255, 255), (70, 80, 160, 230), 18), 700 + 70 * math.sin(ph * 2 + i), 620 - 90 * ph, 1, 10, clamp(1.3 - ph / 1.6))
    char(im, True, t, 330, 1620, .82, "think", "chin", .4, glow=True)
    char(im, False, t, 820, 1620, .7, "happy", "open", -.6)
    L = VO[202]; caption(im, L["text"], (t - L["a"]) / (L["b"] - L["a"]), 0, top=262)

def tablet(scr, tag):
    dev = rrect((1000, 590), 46, (16, 18, 26, 255), (90, 96, 120, 255), 3)
    m = Image.new("L", scr.size); ImageDraw.Draw(m).rounded_rectangle((0, 0, scr.width - 1, scr.height - 1), 24, fill=255)
    dev.paste(scr, (20, 25), m)
    ImageDraw.Draw(dev).ellipse((986, 290, 994, 300), fill=(70, 74, 90))
    lv = chip("   चलती क्लास", font(30), (255, 255, 255), (214, 40, 46, 240), 18, 54)
    ImageDraw.Draw(lv).ellipse((22, 19, 38, 35), fill=(255, 255, 255))
    dev.alpha_composite(lv, (40, 46)); tg = chip(tag, font(30), NAVY, GOLD, 18, 54); dev.alpha_composite(tg, (1000 - tg.width - 40, 46))
    return dev

def scene_class(im, t, t0, t1):
    im.alpha_composite(bg("bg_8.png", t))
    # which clip
    if t < CL_TREE[1]: c, a, b, tag, lab = "clip_tree", CL_TREE[0], CL_TREE[1], "क्लॉज़ 2 · भाग 3", "पेड़ की डाली = ब्रांच ऑफ़िस"
    elif t < CL_CLOCK[1]: c, a, b, tag, lab = "clip_clock", CL_CLOCK[0], CL_CLOCK[1], "क्लॉज़ 2 · भाग 3", "BO के घंटे: 4–5"
    else: c, a, b, tag, lab = "clip_moon", CL_MOON[0], CL_MOON[1], "क्लॉज़ 3", "चाँद = रात्रि डाकघर"
    u = clamp((t - a) / (b - a))
    scr = clip_img(c, u)
    # quick flash between clips
    sw = min(abs(t - CL_CLOCK[0]), abs(t - CL_MOON[0]))
    dev = tablet(scr, tag)
    k = pb(t, t0 + .05, .5)
    paste_center(im, shadowed(dev, 26, (0, 18), 120), W / 2, 640, (.55 + .45 * k) * (.97 if sw < .12 else 1))
    if sw < .1:
        fl = Image.new("RGBA", (W, H), (255, 255, 255, int(120 * (1 - sw / .1)))); im.alpha_composite(fl)
    if t > VO[204]["a"] - .1:
        lk = pb(t, a if a > VO[204]["a"] else VO[204]["a"], .35)
        paste_center(im, shadowed(chip(lab, font(50), NAVY, GOLD, 30, 92)), W / 2, 1012, .4 + .6 * lk, -2)
    else:
        sticker(im, "हर नियम animation से", t, VO[203]["a"] + 2.6, W / 2, 1012, (255, 255, 255, 255), MAROON, 50, -2)
    li = cur_line(t)
    gest = "left" if li in (203, 204) else "open"
    g_air = max(0, math.sin(clamp((t - VO[205]["a"]) / .6) * math.pi)) if VO[205]["a"] <= t else 0
    char(im, False, t, 820, 1640, .74, "happy", gest, -.7, glow=li in (203, 204))
    char(im, True, t, 260, 1640, .7, "surprise" if li == 205 else "happy", "hop" if li == 205 else "chin", .5, g_air, glow=li == 205)
    if li == 205:
        for j in range(6):
            ang = j * 1.05 + t * 2; r = 140 + 30 * math.sin(t * 6 + j)
            cx_, cy_ = 260 + r * math.cos(ang), 1300 + r * .6 * math.sin(ang); st = Image.new("RGBA", (40, 40)); ImageDraw.Draw(st).polygon([(20, 0), (25, 15), (40, 20), (25, 25), (20, 40), (15, 25), (0, 20), (15, 15)], fill=GOLD); paste_center(im, st, cx_, cy_)
    if li:
        L = VO[li]; caption(im, L["text"], (t - L["a"]) / (L["b"] - L["a"]), 1140)

COURSES = [("GDS से MTS", "वीडियो कोर्स", (214, 40, 46)), ("GDS/MTS से Postman", "वीडियो कोर्स", (30, 110, 200)), ("Combo: दोनों साथ", "पूरा बैच", (36, 150, 100))]
def course_card(i):
    name, sub, col = COURSES[i]
    c = rrect((900, 170), 34, (255, 252, 245, 255), col + (255,), 5)
    d = ImageDraw.Draw(c)
    d.rounded_rectangle((26, 30, 136, 140), 26, fill=col); d.polygon([(66, 60), (66, 116), (112, 88)], fill=(255, 255, 255))
    d.text((164, 62), name, font=font(50), fill=NAVY, anchor="lm")
    d.text((164, 122), sub + "  •  animation  •  notes  •  mock", font=font(30, False), fill=(90, 90, 110), anchor="lm")
    return c
CC = [course_card(i) for i in range(3)]

def scene_course(im, t, t0, t1):
    im.alpha_composite(bg("bg_40.5.png", t))
    hk = pb(t, t0, .4)
    times = [VO[206]["a"] + .05, W_(206, 4) - .1, W_(206, 10) - .2]
    for i in range(3):
        k = pb(t, times[i], .45)
        if k > 0: paste_center(im, shadowed(CC[i]), W / 2 + 500 * (1 - k) * (1 if i % 2 else -1), 640 + 200 * i, 1)
    kd = pb(t, W_(206, 16) - .15, .4)
    if kd > 0:
        btn = shadowed(chip("पहले Free Demo देखो", font(54), NAVY, GOLD, 40, 110, (255, 255, 255, 255)))
        paste_center(im, btn, W / 2, 1238, (.4 + .6 * kd) * (1 + .04 * math.sin(t * 7)))
    li = cur_line(t)
    char(im, False, t, 800, 1660, .6, "happy", "welcome" if t > W_(206, 16) else "left", -.6, glow=li == 206)
    char(im, True, t, 270, 1660, .56, "happy", "open", .5)
    if li == 206:
        L = VO[206]; caption(im, L["text"], (t - L["a"]) / (L["b"] - L["a"]), 0, maxw=980, top=258)

PRICES = [("GDS से MTS", "₹849", "₹749"), ("GDS/MTS से Postman", "₹949", "₹849"), ("Combo (दोनों)", "₹1,099", "₹999")]
def price_card():
    c = rrect((940, 700), 44, (255, 252, 245, 255), (255, 214, 90, 255), 8); d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, 939, 140), 44, fill=MAROON); d.rectangle((0, 100, 939, 140), fill=MAROON)
    d.text((470, 72), "हर वीडियो कोर्स पर ₹100 OFF", font=font(50), fill=(255, 255, 255), anchor="mm")
    for i, (n, old, new) in enumerate(PRICES):
        y = 215 + 135 * i
        d.text((44, y), n, font=font(44), fill=NAVY, anchor="lm")
        ow = text_w(old, font(38, False)); d.text((700, y), old, font=font(38, False), fill=(150, 150, 160), anchor="rm")
        d.line((700 - ow - 6, y + 2, 706, y + 2), fill=(214, 40, 46), width=5)
        nb = chip(new, font(50), (255, 255, 255), (36, 150, 100), 22, 84); c.alpha_composite(nb, (c.width - nb.width - 30, int(y - 42)))
        if i < 2: d.line((50, y + 68, 890, y + 68), fill=(230, 222, 210), width=3)
    d.text((470, 650), "ऑफ़र सिर्फ़ 1 दिसंबर तक", font=font(42), fill=(214, 40, 46), anchor="mm")
    return c
PC = price_card()

def scene_price(im, t, t0, t1):
    im.alpha_composite(bg("bg_40.5.png", t))
    k = clamp((t - t0 - .05) / .35)
    drop = -900 * (1 - k) ** 2
    shake = (14 * math.sin((t - t0) * 60) * clamp(1 - (t - t0 - .4) / .3)) if t - t0 > .4 else 0
    paste_center(im, shadowed(PC, 28, (0, 20), 130), W / 2 + shake, 640 + drop, 1, -1.5 * (1 - k))
    if t > t0 + .4 and t < t0 + 1.0:
        r = (t - t0 - .4) / .6; ring = Image.new("RGBA", (W, H)); ImageDraw.Draw(ring).ellipse((W / 2 - 600 * r, 640 - 420 * r, W / 2 + 600 * r, 640 + 420 * r), outline=(255, 214, 90, int(200 * (1 - r))), width=10); im.alpha_composite(ring)
    li = cur_line(t)
    if t > VO[208]["a"] - .1:
        ku = pb(t, VO[208]["a"] + 1.4, .4)
        if ku > 0: paste_center(im, shadowed(chip("postaledge.in", font(70), NAVY, GOLD, 44, 126, (255, 255, 255, 255))), W / 2, 1075, (.4 + .6 * ku) * (1 + .03 * math.sin(t * 7)))
    g_air = max(0, math.sin(clamp((t - VO[207]["a"]) / .6) * math.pi)) if t >= VO[207]["a"] else 0
    char(im, True, t, 270, 1660, .64, "surprise", "hop" if li == 207 else "open", .5, g_air, glow=li == 207)
    char(im, False, t, 800, 1660, .66, "happy", "welcome", -.6, glow=li == 208)
    if li:
        L = VO[li]; caption(im, L["text"], (t - L["a"]) / (L["b"] - L["a"]), 1225)

def scene_end(im, t, t0, t1):
    im.alpha_composite(bg("bg_8.png", t))
    k = pb(t, t0, .5)
    big = LOGO.resize((200, 200), Image.LANCZOS); m = Image.new("L", big.size); ImageDraw.Draw(m).rounded_rectangle((0, 0, 199, 199), 48, fill=255); big.putalpha(m)
    paste_center(im, shadowed(big), W / 2, 520, .4 + .6 * k)
    d = ImageDraw.Draw(im)
    paste_center(im, chip("PostalEdge by Postal Wala", font(56), (255, 255, 255), (0, 0, 0, 0), 10), W / 2, 700, 1, 0, k)
    paste_center(im, shadowed(chip("postaledge.in", font(78), NAVY, GOLD, 48, 140, (255, 255, 255, 255))), W / 2, 860, (.4 + .6 * pb(t, t0 + .25, .45)) * (1 + .03 * math.sin(t * 7)))
    paste_center(im, chip("Free Demo  •  वीडियो कोर्स ₹749 से", font(46), (255, 255, 255), (214, 40, 46, 235), 30, 92), W / 2, 1030, .4 + .6 * pb(t, t0 + .5, .4))
    char(im, True, t, 300, 1560, .66, "happy", "welcome", .5)
    char(im, False, t, 780, 1560, .7, "happy", "welcome", -.5)

def frame(t):
    im = Image.new("RGBA", (W, H), (20, 20, 30, 255))
    for kind, a, b, ex in SEG:
        if a <= t < b or (kind == "end" and t >= a):
            if kind == "didi": scene_didi(im, t, ex, a)
            elif kind == "syl": scene_syl(im, t, a, b)
            elif kind == "sleep": scene_sleep(im, t, a, b)
            elif kind == "class": scene_class(im, t, a, b)
            elif kind == "course": scene_course(im, t, a, b)
            elif kind == "price": scene_price(im, t, a, b)
            elif kind == "end": scene_end(im, t, a, b)
            # quick white wipe into each new scene
            if t - a < .12 and a > 0:
                im.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(150 * (1 - (t - a) / .12)))))
            break
    paste_center(im, brand_band(), W / 2, 190)
    return im.convert("RGB")

# ---------------------------------------------------------------- audio
SR = 48000
def rs(a, sr):
    from scipy.signal import resample_poly
    g = math.gcd(sr, SR); return resample_poly(a, SR // g, sr // g)
def sfx(kind):
    n = lambda s: np.linspace(0, s, int(SR * s), False)
    if kind == "whoosh":
        x = n(.38); z = np.random.default_rng(1).standard_normal(len(x))
        from scipy.signal import lfilter
        z = lfilter([1], [1, -.97], z); z /= np.abs(z).max(); return .25 * z * np.sin(np.pi * x / .38) ** 2
    if kind == "thud":
        x = n(.5); return .55 * np.sin(2 * np.pi * (70 - 30 * x) * x) * np.exp(-x * 9)
    if kind == "ding":
        x = n(.9); return .22 * (np.sin(2 * np.pi * 1320 * x) + .6 * np.sin(2 * np.pi * 1980 * x)) * np.exp(-x * 5)
    if kind == "pop":
        x = n(.12); return .3 * np.sin(2 * np.pi * (900 - 3000 * x) * x) * np.exp(-x * 40)
def mix_audio():
    out = np.zeros(int(SR * (DUR + .5)))
    def add(a, t0, g=1.):
        i = int(t0 * SR); a = a[: max(0, len(out) - i)]; out[i:i + len(a)] += a * g
    da, dsr = load_wav("didi48.wav")
    for kind, a, b, ex in SEG:
        if kind == "didi":
            s = da[int(ex["src"] * dsr): int((ex["src"] + (b - a)) * dsr)].copy()
            f = int(.03 * SR); s[:f] *= np.linspace(0, 1, f); s[-f:] *= np.linspace(1, 0, f)
            add(s, a, 1.0)
    for L in VO.values(): add(rs(L["audio"], L["sr"]), L["a"], 1.0)
    for kind, a, b, ex in SEG:
        if a > 0: add(sfx("whoosh"), a - .15)
    add(sfx("pop"), 2.0); add(sfx("pop"), T_SYL + .25); add(sfx("pop"), T_SYL + .55)
    add(sfx("ding"), CL_CLOCK[0]); add(sfx("ding"), CL_MOON[0]); add(sfx("ding"), VO[205]["a"])
    for tt in (VO[206]["a"], W_(206, 4) - .1, W_(206, 10) - .2): add(sfx("pop"), tt)
    add(sfx("thud"), T_PRICE + .4); add(sfx("ding"), VO[208]["a"] + 1.4); add(sfx("ding"), T_END + .25)
    add(sfx("pop"), T_C + 2.8); add(sfx("pop"), T_C + 6.1); add(sfx("pop"), T_C + 9.7)
    pk = np.abs(out).max(); out = out / max(pk, 1) * .95 if pk > .95 else out
    pcm = (np.clip(out, -1, 1) * 32767).astype("<i2")
    with wave.open("mix.wav", "wb") as w: w.setparams((1, 2, SR, 0, "NONE", "not compressed")); w.writeframes(pcm.tobytes())

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stills":
        for x in sys.argv[2:]: frame(float(x)).save(f"still_{float(x):05.2f}.jpg", quality=88)
        print("DUR", round(DUR, 2), "segs", [(k, round(a, 2), round(b, 2)) for k, a, b, _ in SEG]); sys.exit()
    part, parts = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 1)
    n = int(DUR * FPS); lo, hi = n * part // parts, n * (part + 1) // parts
    if part == 0: mix_audio()
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", f"part{part}.mp4"], stdin=subprocess.PIPE)
    for k in range(lo, hi): ff.stdin.write(frame(k / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print("done", part)
