"""Render a high-contrast, vertical pay breakdown in the Postal Edge style."""
from pathlib import Path
import re
import sys

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1080, 1920
NAVY, WHITE, MUTED, GOLD = "#101c31", "#f7f9ff", "#c0cfe4", "#ffe081"
REG = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"
BOLD = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
LATIN_REG = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
LATIN_BOLD = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
im = Image.new("RGB", (WIDTH, HEIGHT), NAVY)
d = ImageDraw.Draw(im)

def txt(x, y, value, size, color=WHITE, bold=False, anchor="la"):
    hindi = ImageFont.truetype(BOLD if bold else REG, size)
    latin = ImageFont.truetype(LATIN_BOLD if bold else LATIN_REG, size)
    tokens = re.findall(r"[A-Za-z•·−]+|[^A-Za-z•·−]+", value)
    parts = [(token, latin if re.fullmatch(r"[A-Za-z•·−]+", token) else hindi) for token in tokens]
    width = sum(font.getlength(token) for token, font in parts)
    x -= width if anchor.startswith("r") else width / 2 if anchor.startswith("m") else 0
    for token, font in parts:
        d.text((x, y + size), token, font=font, fill=color, anchor="ls")
        x += font.getlength(token)

def pill(box, color, radius=20, outline=None):
    d.rounded_rectangle(box, radius=radius, fill=color, outline=outline, width=2)

def rupees(value):
    return f"₹{value:,}"

basic = 21700
da_rate, hra_rate = 63, 30
da = basic * da_rate // 100
hra = basic * hra_rate // 100
ta_base = 3600
ta = ta_base * (100 + da_rate) // 100
gross = basic + da + hra + ta
nps = round((basic + da) / 10)
paid_after_nps = gross - nps
cghs = 250
in_hand_rounded = round((paid_after_nps - cghs) / 1000) * 1000

d.rectangle((0, 0, WIDTH, 16), fill=GOLD)
pill((52, 56, 1028, 1854), "#15243d", radius=37, outline="#385273")
txt(104, 102, "POSTAL EDGE", 45, bold=True)
txt(106, 160, "by Postal Wala", 27, MUTED)
pill((626, 91, 977, 155), GOLD, radius=29)
txt(801, 103, "चयन के बाद का उदाहरण", 28, "#192b45", True, "ma")

txt(104, 239, "Postman की सैलरी", 81, bold=True)
txt(107, 344, "Pay Level 3   •   X-क्लास शहर (दिल्ली)", 41, GOLD, True)
txt(107, 415, "अनुमानित मासिक वेतन · नवंबर 2026 की दरें", 32, MUTED)

pill((103, 496, 977, 1005), "#1d3151", radius=25)
items = [
    ("बेसिक पे", rupees(basic)),
    ("DA · 63%", rupees(da)),
    ("HRA · 30%", rupees(hra)),
    ("ट्रांसपोर्ट अलाउंस + DA", rupees(ta)),
]
for i, (label, amount) in enumerate(items):
    y = 532 + 119 * i
    txt(137, y, label, 46, bold=True)
    txt(944, y, amount, 49, WHITE, True, "ra")
    if i < len(items) - 1:
        d.line((138, y + 90, 942, y + 90), fill="#415c7f", width=2)

pill((103, 1030, 977, 1161), "#263c5d", radius=23)
txt(137, 1059, "कुल वेतन (ग्रॉस)", 45, bold=True)
txt(943, 1052, rupees(gross), 61, GOLD, True, "ra")
txt(105, 1200, "NPS कटौती · बेसिक + DA का 10%", 37, MUTED)
txt(972, 1193, "-" + rupees(nps), 44, MUTED, True, "ra")
txt(105, 1272, "CGHS ₹250, जहाँ लागू हो", 31, MUTED)

pill((103, 1355, 977, 1605), GOLD, radius=28)
txt(540, 1383, "अनुमानित इन-हैंड", 42, "#1d2e47", True, "ma")
txt(540, 1452, "लगभग " + rupees(in_hand_rounded), 82, "#142643", True, "ma")

txt(104, 1655, "HRA व ट्रांसपोर्ट अलाउंस मिलने पर।", 35, MUTED)
txt(104, 1717, "अन्य लागू कटौतियों से इन-हैंड बदल सकता है।", 35, MUTED)
txt(104, 1784, "भर्ती नियमों का अंतिम नोटिफिकेशन बाकी", 28, GOLD, True)

im.save(Path(sys.argv[1]))
