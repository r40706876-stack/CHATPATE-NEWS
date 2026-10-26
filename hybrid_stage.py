"""Animated topic-aware visual stage: reusable vector props, no stock or API quota."""
import math
import re
from PIL import Image, ImageDraw, ImageFont

TOPICS = {
 "train": ("ट्रेन","रेल","टिकट","स्टेशन","यात्री"),
 "money": ("रुपये","₹","बिल","पैसे","महंगा","कीमत","बैंक","लोन"),
 "phone": ("मोबाइल","फोन","ऐप","ऑनलाइन","otp","इंटरनेट"),
 "office": ("ऑफिस","नौकरी","बॉस","कर्मचारी","छुट्टी","ड्यूटी"),
 "parcel": ("पार्सल","डिलीवरी","कूरियर","cod"),
 "gas": ("गैस","सिलेंडर","एलपीजी","lpg"),
 "exam": ("परीक्षा","एग्जाम","पेपर","रिजल्ट","मार्क्स"),
}
def topic_of(text):
    s=str(text).lower()
    for key, words in TOPICS.items():
        if any(word in s for word in words):
            return key
    return "news"

def stage_frames(card, size, fps=25):
    """Generate looping animated illustrated visual; headline is NOT a repeated full-screen card."""
    w,h=size
    kind=card.get("topic","news")
    caption=" ".join(str(card.get("caption") or "").split()[:6])
    t=0
    while True:
        p=t/fps
        im=Image.new("RGB",(w,h),(235,244,252))
        d=ImageDraw.Draw(im)
        d.rectangle((0,int(h*.77),w,h),fill=(204,223,238))
        d.rounded_rectangle((30,25,w-30,110),radius=22,fill=(27,52,86))
        try:
            font=ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",42)
        except OSError:
            font=ImageFont.load_default()
        d.text((w//2,68),caption,font=font,anchor="mm",fill="white")
        shift=int(26*math.sin(p*3.2))
        cx,cy=w//2,int(h*.46)+shift
        if kind=="train":
            d.rounded_rectangle((cx-320,cy-170,cx+320,cy+150),radius=42,fill=(56,117,185),outline=(25,55,91),width=9)
            for x in (-230,0,230):
                d.rounded_rectangle((cx+x-72,cy-110,cx+x+72,cy+12),radius=12,fill=(171,226,245))
            d.ellipse((cx-230,cy+105,cx-145,cy+190),fill=(36,48,66))
            d.ellipse((cx+145,cy+105,cx+230,cy+190),fill=(36,48,66))
            for y in (cy+205,cy+245):d.line((40,y,w-40,y),fill=(70,83,97),width=10)
        elif kind=="money":
            d.rounded_rectangle((cx-260,cy-160,cx+260,cy+165),radius=30,fill=(195,235,197),outline=(43,111,70),width=12)
            d.ellipse((cx-110,cy-115,cx+110,cy+115),fill=(118,189,129))
            d.text((cx,cy),"₹",font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",165),anchor="mm",fill=(25,85,49))
        elif kind=="phone":
            d.rounded_rectangle((cx-175,cy-255,cx+175,cy+265),radius=42,fill=(40,56,82))
            d.rounded_rectangle((cx-147,cy-205,cx+147,cy+190),radius=20,fill=(116,201,225))
            d.ellipse((cx-18,cy+214,cx+18,cy+250),fill="white")
            d.ellipse((cx-85,cy-80,cx+85,cy+90),fill=(250,215,109))
        elif kind=="office" or kind=="exam":
            d.rounded_rectangle((cx-230,cy-230,cx+230,cy+225),radius=25,fill="white",outline=(61,91,126),width=10)
            for j in range(4):
                y=cy-125+j*85
                d.rectangle((cx-150,y-16,cx-100,y+32),outline=(65,105,145),width=6)
                d.line((cx-65,y+7,cx+145,y+7),fill=(91,125,158),width=8)
        elif kind=="gas":
            d.rounded_rectangle((cx-210,cy-180,cx+210,cy+245),radius=65,fill=(213,66,63),outline=(116,35,37),width=10)
            d.rounded_rectangle((cx-100,cy-230,cx+100,cy-145),radius=12,outline=(116,35,37),width=15)
        elif kind=="parcel":
            d.rounded_rectangle((cx-270,cy-185,cx+270,cy+185),radius=22,fill=(210,157,95),outline=(113,73,44),width=10)
            d.rectangle((cx-38,cy-185,cx+38,cy+185),fill=(243,214,156))
        else:
            d.ellipse((cx-230,cy-230,cx+230,cy+230),fill=(246,199,89),outline=(198,120,55),width=14)
            d.text((cx,cy),"!",font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",270),anchor="mm",fill=(76,60,85))
        # moving emphasis rings add motion even if the main prop is momentarily static
        radius=30+int(20*(1+math.sin(p*5)))
        for x in (90,w-90):
            d.ellipse((x-radius,cy-radius,x+radius,cy+radius),outline=(232,112,79),width=9)
        yield im
        t+=1
