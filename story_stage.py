"""Single-stage visual comedy for character-only episodes.

Unlike the old split-screen template, the speaker, the house and the objects
share one continuous 9:16 scene. All props are local vector drawings; no
unverified external images or generated 'news footage' are represented as real.
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import talk_test as tt

SIZE = (1080, 1920)
INK = (42, 57, 76)
RED = (206, 63, 64)
YELLOW = (255, 214, 79)


def scene_for(line):
    scene = str(line.get("scene") or "")
    return scene if scene in ("sweets", "arrival", "freight", "bill", "house") else "sweets"


def _box(d, x, y, w=230, h=160, label="COD"):
    x, y = int(x), int(y)
    d.rounded_rectangle((x, y, x+w, y+h), 16, fill=(205, 145, 84), outline=(102, 68, 47), width=7)
    d.rectangle((x+w//2-18, y, x+w//2+18, y+h), fill=(246, 211, 145))
    if label:
        d.rounded_rectangle((x+20, y+42, x+w-20, y+104), 10, fill=(255, 249, 227))
        d.text((x+w//2, y+73), label, font=tt.font(43), fill=RED, anchor="mm")


def _tv(d, x, y, w=400, h=300):
    x, y = int(x), int(y)
    d.rounded_rectangle((x, y, x+w, y+h), 22, fill=INK, outline=(25, 35, 48), width=10)
    d.rounded_rectangle((x+24, y+24, x+w-24, y+h-40), 12, fill=(100, 185, 211))
    d.polygon([(x+24,y+h-40),(x+w//2,y+50),(x+w-24,y+h-40)], fill=(246, 204, 110))
    d.line((x+w//2,y+h,x+w//2,y+h+35),fill=INK,width=15)
    d.line((x+w//2-90,y+h+35,x+w//2+90,y+h+35),fill=INK,width=15)


def _worker(d, x, y, arm=0):
    x, y = int(x), int(y)
    d.ellipse((x+60,y,x+190,y+130),fill=(234,177,129),outline=INK,width=5)
    d.rounded_rectangle((x+30,y+115,x+220,y+410),38,fill=(70,133,195),outline=INK,width=5)
    d.line((x+60,y+190,x-40,y+260+arm),fill=(70,133,195),width=32)
    d.line((x+195,y+185,x+295,y+225-arm),fill=(70,133,195),width=32)
    d.line((x+90,y+405,x+70,y+540),fill=INK,width=36)
    d.line((x+170,y+405,x+190,y+540),fill=INK,width=36)


def _house_base():
    # Use the existing high-quality 3D-style village set, not a flat geometric house.
    try:
        from reel_studio import set_img
        return ImageEnhance.Brightness(set_img("village",*SIZE).filter(ImageFilter.GaussianBlur(1.2))).enhance(0.88)
    except (OSError, KeyError, ValueError):
        pass
    im=Image.new("RGB",SIZE,(232,245,252))
    d=ImageDraw.Draw(im)
    d.rectangle((0,1320,1080,1920),fill=(193,212,207))
    d.rectangle((0,1380,1080,1470),fill=(172,192,185))
    d.rounded_rectangle((75,400,1005,1400),30,fill=(246,218,183),outline=(154,112,84),width=10)
    d.polygon([(35,435),(540,215),(1045,435)],fill=(173,77,72))
    d.rounded_rectangle((120,740,370,1320),16,fill=(120,79,58),outline=(76,53,44),width=8)
    d.ellipse((320,1030,342,1052),fill=YELLOW)
    d.rounded_rectangle((745,690,940,955),14,fill=(166,205,218),outline=(88,112,130),width=10)
    d.line((840,690,840,955),fill=(88,112,130),width=7)
    return im


def _character(im, sprite, x, y, height, flip=False):
    if sprite is None:
        return
    w=int(sprite.width*height/max(1,sprite.height))
    sp=sprite.resize((w,height),Image.Resampling.LANCZOS)
    if flip:
        sp=sp.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    im.paste(sp,(int(x),int(y)),sp)


def _scene_action(im, scene, t, n):
    d=ImageDraw.Draw(im)
    q=min(1.0,t/max(1,n-1))
    wobble=int(12*math.sin(t/5))
    if scene=="sweets":
        d.rounded_rectangle((80,560,470,830),20,fill=(255,237,176),outline=(171,112,58),width=10)
        for j in range(3):
            d.ellipse((125+j*100,625,210+j*100,710),fill=(235,159,57),outline=(163,96,37),width=5)
        _tv(d, int(1110-570*min(1,t/14)), 600+wobble, 390,285)
        d.rounded_rectangle((565,925,1000,1045),20,fill=RED)
        d.text((782,982),"₹1,69,000",font=tt.font(77),fill="white",anchor="mm")
    elif scene=="arrival":
        for j in range(3):
            _box(d, int(1100-350*min(1,(t-j*7)/17))-j*175, 910-j*120+wobble, 240,160)
        _tv(d,485,570+wobble,360,265)
        d.rounded_rectangle((435,455,920,535),18,fill=INK)
        d.text((677,495),"घर बना शोरूम!",font=tt.font(58),fill="white",anchor="mm")
    elif scene=="freight":
        d.rounded_rectangle((415,710,925,1120),42,fill=(34,52,73),outline=YELLOW,width=13)
        d.rounded_rectangle((450,745,890,1070),26,fill=(243,249,252))
        d.text((670,835),"UPI",font=tt.font(105),fill=INK,anchor="mm")
        d.text((670,955),"FAILED",font=tt.font(83),fill=RED,anchor="mm")
        # The courier is an existing 3D-style Ramesh sprite, composited below.
        d.rounded_rectangle((555,480,930,670),25,fill=(44,60,83))
        d.text((742,570),"UPI बेहोश!",font=tt.font(118),fill=YELLOW,anchor="mm")
        d.ellipse((740,1090,930,1280),fill=(247,193,99),outline=INK,width=7)
        d.text((835,1185),"?",font=tt.font(140),fill=INK,anchor="mm")
    elif scene=="bill":
        _tv(d,500,590+wobble,365,265)
        # The courier is an existing 3D-style Ramesh sprite, composited below.
        d.rounded_rectangle((470,930,1030,1290),20,fill="white",outline=RED,width=14)
        d.text((750,1010),"COD बिल",font=tt.font(71),fill=INK,anchor="mm")
        d.text((750,1130),"₹1,69,000",font=tt.font(76),fill=RED,anchor="mm")
        d.rounded_rectangle((540,1210,965,1270),12,fill=YELLOW)
        d.text((752,1240),"चाचा एक्सचेंज?!",font=tt.font(44),fill=INK,anchor="mm")
    elif scene=="house":
        # The courier is an existing 3D-style Ramesh sprite, composited below.
        d.rounded_rectangle((375,520,1000,870),25,fill=(250,241,214),outline=RED,width=16)
        d.text((685,635),"चाचा एक्सचेंज!",font=tt.font(85),fill=RED,anchor="mm")
        d.text((685,755),"पता गलत!",font=tt.font(39),fill=INK,anchor="mm")
        for j in range(3):
            x=530+j*150
            _box(d,x,950+j*32+wobble,145,120,"COD")
        if t>int(n*.48):
            d.line((350,860,975,860),fill=RED,width=22)
            d.line((400,780,940,920),fill=RED,width=20)


    # Story-first action overlays. Do not cycle giant text cards every 1.3s:
    # those used to cover the actual gag and made the scene look like a slideshow.
    phase=t/max(1,n-1)
    if scene=="sweets":
        # The COD carton slides across the sweets: the promised gift is replaced.
        if phase>0.34:
            x=int(50+min(1,(phase-.34)/.35)*190)
            _box(d,x,545,290,240,"COD")
    elif scene=="arrival":
        # Delivery stack keeps growing instead of alternating unrelated cards.
        if phase>.38:
            _box(d,int(930-400*min(1,(phase-.38)/.4)),735,200,145,"COD")
    elif scene=="freight":
        # Visible impact: a lightning crack travels down the failed UPI phone.
        if phase>.20:
            yy=int(785+min(1,(phase-.2)/.6)*190)
            d.line([(850,yy-60),(790,yy-5),(835,yy+5),(765,yy+90)],
                   fill=(236,72,64),width=20,joint="curve")
    elif scene=="bill":
        # An exchange arrow connects the expensive TV to the person being offered.
        x=int(450-65*math.sin(phase*math.pi))
        d.line([(x,820),(x-170,820)],fill=YELLOW,width=24)
        d.polygon([(x-195,820),(x-145,786),(x-145,854)],fill=YELLOW)
    elif scene=="house":
        # A red return stamp lands on the COD parcel as Dadi finishes the punch.
        if phase>.48:
            scale=min(1,(phase-.48)/.26)
            cx,cy=765,1090
            r=int(125*scale)
            if r>5:
                d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=RED,width=18)
                d.line((cx-r//2,cy-r//2,cx+r//2,cy+r//2),fill=RED,width=15)


def frames(line, episode, talk, n, cut, seed=0):
    """Yield full-screen scene with two cutout characters, voice-driven mouth and actual prop actions."""
    import sprite_talk
    from reel_studio import EXPR, pose_file
    scene=scene_for(line)
    base=_house_base()
    who=line.get("who","bablu")
    supporter="chacha" if who!="chacha" else "pinky"
    if who=="chacha":
        supporter="pinky"
    folder=Path(episode["sprite"][who])
    expr=EXPR.get(talk.get("expr",""),talk.get("expr","")) or "neutral"
    talking=sprite_talk.frames(folder,expr,talk["wav"],n,cut,seed)
    supporting=None
    if supporter in episode.get("sprite",{}):
        supporting=cut(pose_file(episode["sprite"][supporter],"hairan"))
    courier=None
    if "ramesh" in episode.get("sprite",{}):
        courier=cut(pose_file(episode["sprite"]["ramesh"],"neutral"))
    for t,sp in enumerate(talking):
        im=base.copy()
        _scene_action(im,scene,t,n)
        if scene in ("freight","bill","house"):
            _character(im,courier,70+int(9*math.sin(t/7)),810,575)
        _character(im,supporting,5+int(9*math.sin(t/8)),1120+int(5*math.sin(t/10)),610,flip=True)
        _character(im,sp,600+int(8*math.sin(t/6)),990+int(7*math.sin(t/9)),760)
        d=ImageDraw.Draw(im)
        if scene=="house" and t>=int(n*.40):
            # Physical payoff: Dadi has packed Chacha, not merely flashed a RETURN icon.
            # Leave his face visible; the carton covers his torso and stays attached to him.
            d.rounded_rectangle((12,1390,430,1730),20,fill=(201,146,92),outline=(108,69,44),width=14)
            d.rectangle((200,1390,242,1730),fill=(246,212,150))
            d.rounded_rectangle((45,1490,398,1635),14,fill=(255,250,233),outline=RED,width=8)
            d.text((221,1535),"पता गलत!",font=tt.font(57),fill=RED,anchor="mm")
            d.text((221,1594),"चाचा पैक!",font=tt.font(42),fill=INK,anchor="mm")
        yield im
