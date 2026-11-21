from pathlib import Path
from functools import lru_cache
import re
import subprocess
import wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 720, 1280, 30
root = Path(__file__).resolve().parent
work = root
output = root / "Postal_Edge_7s_Hook.mp4"
gold, ivory, white = "#ffc46c", "#eee0c3", "#f5f5ef"
ink, slate, aqua = "#112231", "#9bb2bb", "#84e5d5"
sans = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
hindi = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"

@lru_cache(maxsize=64)
def font(size, devanagari=False):
    return ImageFont.truetype(hindi if devanagari else sans, size)

def txt(im, xy, data, size, color, hi=False, anchor="mm"):
    draw = ImageDraw.Draw(im)
    if not hi or not re.search(r"[A-Za-z0-9]", data):
        draw.text(xy, data, font=font(size, hi), fill=color, anchor=anchor)
        return
    pieces = re.findall(r"[A-Za-z0-9]+|[^A-Za-z0-9]+", data)
    runs = [(piece, font(size, not piece.isascii())) for piece in pieces]
    widths = [draw.textlength(piece, face) for piece, face in runs]
    bounds = [draw.textbbox((0, 0), piece, face, anchor="ls") for piece, face in runs]
    x, y = xy
    x -= {"l": 0, "m": sum(widths)/2, "r": sum(widths)}[anchor[0]]
    y -= (min(box[1] for box in bounds) + max(box[3] for box in bounds))/2
    for (piece, face), width in zip(runs, widths):
        draw.text((x, y), piece, font=face, fill=color, anchor="ls")
        x += width

def rr(im, box, radius, fill, outline=None, width=1):
    ImageDraw.Draw(im).rounded_rectangle(tuple(round(p) for p in box), radius, fill, outline, width)

def ease(v):
    v = min(1, max(0, v))
    return v * v * (3-2*v)

rng = np.random.default_rng(22)
ys, xs = np.mgrid[:H, :W]
beam = np.exp(-(((xs-357)/345)**2 + ((ys-598)/510)**2)*1.5)
grain = rng.normal(0, .95, (H,W)) + .5*np.sin(ys*.42+np.sin(xs/48))
base = Image.fromarray(np.clip(np.stack([
    9 + 46*beam + grain, 19 + 40*beam + grain, 27 + 31*beam + grain,
],axis=-1),0,255).astype("uint8")).convert("RGBA")
d = ImageDraw.Draw(base)
for y in range(124,1160,89):
    d.line((0,y,720,y+12), fill="#1b2931", width=1)

envelope = Image.new("RGBA",(525,420))
rr(envelope,(12,12,513,406),15,"#e9d6ac","#ffecc1",2)
dr = ImageDraw.Draw(envelope)
dr.polygon([(13,398),(262,218),(512,398),(507,405),(18,405)],fill="#d8be90")
dr.line([(13,398),(262,219),(512,398)],fill="#c3a478",width=2)
rr(envelope,(42,37,482,335),7,"#f6e5c1")
dr.rectangle((50,44,474,327),outline="#c5ab83",width=1)
txt(envelope,(262,79),"भर्ती नियमों का ड्राफ्ट",22,ink,True)
dr.line((85,105,439,105),fill="#c89959",width=2)
txt(envelope,(260,179),"45,899",99,ink)
txt(envelope,(261,252),"POSTMAN पद",31,ink,True)
rr(envelope,(191,289,334,310),4,"#eed3a1")
txt(envelope,(262,300),"DEPT. OF POSTS",12,"#694526")
rr(envelope,(245,350,280,368),5,"#9f503c")
dr.line((249,359,276,359),fill="#d98b65",width=2)

def lay(im, sprite, center, angle=0, shadow=False):
    if angle:
        sprite = sprite.rotate(angle,Image.Resampling.BICUBIC,expand=True)
    x = round(center[0]-sprite.width/2)
    y = round(center[1]-sprite.height/2)
    if shadow:
        pad = 30
        shade = Image.new("RGBA",(sprite.width+2*pad,sprite.height+2*pad))
        shade.paste((0,0,0,185),(pad,pad,pad+sprite.width,pad+sprite.height),sprite.getchannel("A"))
        im.alpha_composite(shade.filter(ImageFilter.GaussianBlur(11)),(x-pad+8,y-pad+15))
    im.alpha_composite(sprite,(x,y))

def tray(name,color):
    layer = Image.new("RGBA",(305,228))
    rr(layer,(3,5,302,223),16,"#14252d","#3f535a",2)
    rr(layer,(16,18,289,207),10,"#0d1c25","#344750",2)
    rr(layer,(26,25,279,78),8,"#182d38")
    txt(layer,(152,51),name,32,color)
    for y in (103,119,135,151,167,183):
        ImageDraw.Draw(layer).line((37,y,266,y),fill="#233841",width=2)
    return layer

def hand(official):
    layer = Image.new("RGBA",(300,151))
    skin = "#bd8056" if official else "#d99a69"
    lighter = "#eab284" if official else "#f3c094"
    cuff = "#a94735" if official else "#2e807d"
    rr(layer,(8,60,220,125),28,skin,"#8b533e",2)
    for a,b,c,d in [(154,32,292,63),(160,61,281,94),(144,90,246,119)]:
        rr(layer,(a,b,c,d),14,skin,"#935f46",2)
        rr(layer,(c-26,b+7,c-7,b+16),5,lighter)
    rr(layer,(115,40,206,114),29,skin)
    ImageDraw.Draw(layer).line([(145,89),(167,86),(187,93)],fill="#a2654e",width=2)
    rr(layer,(3,43,109,137),12,cuff)
    rr(layer,(86,43,111,137),5,"#793b2d" if official else "#215b59")
    rr(layer,(21,76,72,93),4,"#ffd688" if official else "#6fb5b4")
    return layer

mts_tray, gds_tray = tray("MTS", gold), tray("GDS", aqua)
golu, dakia = hand(False), hand(True)
draft = Image.open(work/"page5.jpg").convert("RGBA")
scale = 120/72
def crop_doc(bounds):
    return draft.crop(tuple(round(a*scale) for a in bounds))
extracts = [crop_doc((95,81,254,162)),crop_doc((95,172,252,282))]
extracts = [pic.resize((270,round(pic.height*270/pic.width)),Image.Resampling.LANCZOS) for pic in extracts]

def masthead(im, brighter=False):
    accent = aqua if brighter else gold
    d = ImageDraw.Draw(im)
    d.line((57,137,85,137),fill=accent,width=4)
    txt(im,(98,136),"POSTAL EDGE",20,white,anchor="lm")
    txt(im,(662,136),"DRAFT  /  20 NOV 2026",15,slate,anchor="rm")
    d.line((57,167,663,167),fill="#344650",width=1)
    d.line((57,1097,663,1097),fill="#344650",width=1)
    txt(im,(57,1130),"postaledge.in",20,white,anchor="lm")
    txt(im,(663,1130),"POSTMAN  /  भर्ती नियम",17,slate,True,anchor="rm")

