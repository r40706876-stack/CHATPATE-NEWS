from functools import lru_cache
from pathlib import Path
import bisect
import json
import math
import re
import subprocess as sp
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

CORE = Path.cwd()
sys.path.insert(0, str(CORE))
from postal_edge_puppet import puppet
from postal_edge_lip_shapes import measure_mouth

OUT = CORE / "reel-work"
ASSETS = OUT / "assets"
VOICES = OUT / "voices"
W, H, FPS, RATE = 1080, 1920, 20, 48000
LENGTH = 43
INK = "#223742"
RED = "#982f26"
GOLD = "#ffdf99"
GREEN = "#25624e"
CREAM = "#fffaf0"
WHITE = "#fffef9"
CAPTIONS = [
    ["GDS से सीधे Postman का पेपर", "पहले MTS बनना ज़रूरी नहीं।"],
    ["Postman और Mail Guard", "ड्राफ्ट में 5 की जगह 3 साल।"],
    ["मेरे 3 साल हो गए।", "तो फॉर्म भर दूँ?"],
    ["अभी ड्राफ्ट है।", "भर्ती की खबर आने पर पता चलेगा।"],
    ["तो तब तक मैं क्या करूँ?"],
    ["आज से पढ़ना शुरू करो।", "आगे वक्त कम मिल सकता है।"],
    ["ठीक है भैया, शुरुआत कहाँ से करूँ?"],
    ["वीडियो क्लास का फ्री डेमो", "postaledge.in पर देखो।"],
    ["आसान भाषा और चित्रों से", "क्लास में ही नियम याद करो।"],
]
GOLU = {2,4,6}

@lru_cache
def font(n, hindi=False):
    return ImageFont.truetype(f"/usr/share/fonts/truetype/noto/NotoSans{'Devanagari' if hindi else ''}-Bold.ttf",n)

def text(draw, x,y,words,size,fill=INK,align="center"):
    script = re.findall(r"[\u0900-\u097f]+|[^\u0900-\u097f]+", words)
    parts = [(p,font(size,bool(re.search(r"[\u0900-\u097f]",p)))) for p in script]
    widths = [draw.textlength(p,font=f) for p,f in parts]
    if align == "center":
        x -= sum(widths)/2
    elif align == "right":
        x -= sum(widths)
    for (part,face),width in zip(parts,widths):
        draw.text((x,y+size*.32),part,font=face,fill=fill,anchor="ls")
        x += width

def box(d,coords,radius=30,color=WHITE,outline=None,width=2):
    d.rounded_rectangle(coords,radius=radius,fill=color,outline=outline,width=width)

def ease(v,a,b):
    p = max(0,min(1,(v-a)/(b-a)))
    return p*p*(3-2*p)

def audio():
    trimmed = []
    for i in range(9):
        source = VOICES / f"voice{i}.wav"
        audio = sp.check_output(["ffmpeg","-v","error","-i",str(source),"-af",
           "silenceremove=start_periods=1:start_duration=0.025:start_threshold=-45dB:start_silence=0.025,loudnorm=I=-16:TP=-2:LRA=7","-ar",str(RATE),"-ac","1","-f","f32le","-"])
        line = np.frombuffer(audio,dtype="<f4")
        points = np.flatnonzero(abs(line)>.002)
        assert points.size
        trimmed.append(line[:points[-1]+round(RATE*.06)])
    spoken = sum(map(len,trimmed))/RATE
    multiplier = max(.81, min(1.32,(LENGTH-2.1)/spoken))
    lines = []
    for i,line in enumerate(trimmed):
        if abs(multiplier-1)>.02:
            line = np.frombuffer(sp.check_output(["ffmpeg","-v","error","-f","f32le","-ar",str(RATE),
                "-ac","1","-i","-","-af",f"atempo={1/multiplier:.5f}","-f","f32le","-"],input=line.tobytes()),dtype="<f4")
        lines.append(line)
    remaining = LENGTH - sum(map(len,lines))/RATE
    assert remaining>.65, (spoken,remaining)
    gap = min(.42,max(.09,(remaining-.65)/8))
    hold = remaining-8*gap
    speech = np.zeros(LENGTH*RATE,dtype=np.float32)
    cuts, tick = [], .075
    for line in lines:
        cuts.append(tick)
        j=round(tick*RATE)
        speech[j:j+len(line)] = line
        tick += len(line)/RATE+gap
    mix=speech.copy()
    for i in (1,2,4,7):
        p = round(cuts[i]*RATE)
        length = round(.15*RATE)
        a = np.arange(length)/RATE
        mix[p:p+length] += .017*np.sin(a*2*np.pi*(615+85*i))*np.minimum(1,a/.012)*np.exp(-27*a)
    (OUT/"tail.f32").write_bytes(mix.tobytes())
    report={"duration":50,"hook_seconds":7,"continuation_cues":[round(7+t,3) for t in cuts],
            "spoken_seconds":round(spoken,2),"end_hold":round(hold,2)}
    (OUT/"timing.json").write_text(json.dumps(report,indent=2))
    print(report,flush=True)
    return cuts,measure_mouth(speech[::3],FPS,LENGTH)

def backdrop(i):
    image = Image.open(ASSETS/f"background{i}.jpg").convert("RGB")
    image = ImageOps.fit(image,(W,H),Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(5))
    image = Image.blend(image,Image.new("RGB",(W,H),"#fff3d8"), (.55,.47,.73)[i])
    overlay=Image.new("RGBA",(W,H))
    d=ImageDraw.Draw(overlay)
    for y in range(H):
        alpha=round(210*(1-ease(y,0,735)) + 213*ease(y,1070,1770))
        d.line((0,y,W,y),fill=(255,247,227,alpha))
    return Image.alpha_composite(image.convert("RGBA"),overlay)

def arrow(d,a,b,color=GREEN,width=12):
    d.line((*a,*b),fill=color,width=width)
    angle=math.atan2(b[1]-a[1],b[0]-a[0])
    for z in (-.58,.58):
        d.line((b[0],b[1],b[0]-26*math.cos(angle+z),b[1]-26*math.sin(angle+z)),fill=color,width=width)

def routes(d,dt):
    box(d,(81,257,999,896),56,"#244c47")
    box(d,(102,276,978,876),44,CREAM)
    box(d,(457,294,623,303),4,"#aac1ae")
    text(d,540,374,"GDS वाले कौन-सा पेपर दे सकते हैं?",44)
    lanes = [("MTS का पेपर",563,"#e7efe2"),("सीधे Postman का पेपर",686,GOLD)]
    shift=ease(dt,.02,.60)
    for title,y,color in lanes:
        box(d,(142,y-44,305,y+44),24,"#e3f1e7")
        box(d,(487,y-44,937,y+44),24,color)
        text(d,223,y,"GDS",38,GREEN)
        text(d,712,y,title,38,RED if y==686 else INK)
        if shift>.08:
            arrow(d,(324,y),(round(324+144*shift),y),RED if y==686 else GREEN,8)
    text(d,540,802,"Postman के लिए पहले MTS बनना ज़रूरी नहीं।",31,GREEN)

def draft(f,d,dt,proof):
    box(d,(72,285,1008,879),52,CREAM,"#e5c799",3)
    box(d,(100,316,980,397),24,"#e0eee3")
    text(d,130,357,"20 नवंबर 2026",35,GREEN,align="left")
    text(d,950,357,"DRAFT",35,RED,align="right")
    text(d,540,462,"Postman / Mail Guard",51)
    text(d,540,544,"GDS में काम करने के साल",37,GREEN)
    p=ease(dt,.1,.62)
    box(d,(221,596,859,720),30,GOLD)
    text(d,351,659,"5 साल",66,RED)
    if p>.07:
        arrow(d,(466,659),(round(466+123*p),659),RED,10)
    text(d,721,659,"3 साल",66,RED)
    f.alpha_composite(proof,(172,745))

def planning(d,i,dt):
    if i==2:
        text(d,540,409,"3 साल हो गए। फॉर्म भर दूँ?",54)
        box(d,(240,529,840,711),35,GOLD)
        text(d,540,620,"गोलू का सवाल",45,RED)
        return
    if i==3:
        text(d,540,409,"अभी ड्राफ्ट है",76)
        box(d,(210,529,870,711),35,GOLD)
        text(d,540,620,"भर्ती की खबर का इंतज़ार",46,RED)
        return
    text(d,540,402,"तैयारी आज से",76)
    box(d,(135,513,945,799),38,"#fff9e7","#e9d1a4")
    for x,heading,detail in ((340,"आज","तैयारी शुरू"),(738,"भर्ती आएगी","तब फॉर्म देखो")):
        d.ellipse((x-22,569,x+22,613),fill=GREEN if x==340 else "#c99037")
        text(d,x,659,heading,44)
        text(d,x,730,detail,32,GREEN)
    p=ease(dt,0,.7)
    if p>.03:
        arrow(d,(401,591),(round(401+273*p),591),RED,8)
    if i==5:
        text(d,540,856,"नया नियम आया तो पढ़ने का वक्त कम मिल सकता है।",35,RED)

def show_site(f,d,i,dt,site,lesson_frames):
    box(d,(74,283,1006,945),54,"#fffdf5","#e3c998",3)
    text(d,540,366,"postaledge.in",62,RED)
    text(d,540,451,"वीडियो कोर्स का फ्री डेमो",47)
    thumb = site if i != 8 else lesson_frames[min(round(dt*12),len(lesson_frames)-1)]
    if i==6:
        text(d,540,519,"पहला पाठ · डाकघरों के प्रकार",31,GREEN)
    f.alpha_composite(thumb,((W-thumb.width)//2,538 if i!=6 else 554))
    if i==8:
        box(d,(285,865,795,931),30,GOLD)
        text(d,540,897,"चित्रों से सीखें",33,RED)

def character(f,d,t,dt,i,mouths):
    phase=ease(dt,0,.72)
    reaction=math.sin(math.pi*phase)
    for golu,x in ((True,120),(False,629)):
        active=(i in GOLU)==golu
        facing=.67 if golu else -.68
        if golu:
            xx=x+(28 if i in (2,4,6) else 12)*phase
            action="open" if active else ("chin" if i<6 else "right")
        else:
            xx=x-(32 if active else 8)*phase
            action="left" if i in (0,1,3,7,8) else "open"
        size=(356,544)
        yy=907 if i<6 else 933
        d.ellipse((xx+31,yy+484,xx+315,yy+524),fill="#ccb494")
        mouth=mouths[min(len(mouths)-1,round(t*FPS))] if active else None
        im=puppet(golu,t,.14*reaction if active else .01,facing,mouth,
            "surprise" if golu and active and dt<.64 else "happy",
            (.53+.42*reaction,action),facing,.50*reaction if golu and active else 0,.14*reaction)
        f.alpha_composite(im.resize(size,Image.Resampling.BICUBIC),(round(xx),round(yy-(30 if active else 12)*reaction)))

def compose(t,cuts,mouths,plates,proof,site,lesson):
    i=max(0,bisect.bisect_right(cuts,t)-1)
    dt=max(0,t-cuts[i])
    scene=1 if i<=1 else 0 if i<=5 else 2
    if i in (2,6) and dt<.38:
        old=1 if i==2 else 0
        f=Image.blend(plates[old],plates[scene],ease(dt,0,.38))
    else:
        f=plates[scene].copy()
    d=ImageDraw.Draw(f)
    box(d,(336,119,744,194),36,CREAM,"#e3c799")
    text(d,540,157,"POSTAL EDGE",31,RED)
    if i==0:
        routes(d,dt)
    elif i==1:
        draft(f,d,dt,proof)
    elif i<=5:
        box(d,(75,290,1005,914),52,CREAM,"#e5c799",3)
        planning(d,i,dt)
    else:
        show_site(f,d,i,dt,site,lesson)
    character(f,d,t,dt,i,mouths)
    box(d,(89,1490,991,1692),38,WHITE,"#e5c799",3)
    text(d,540,1533,"गोलू" if i in GOLU else "डाकिया भैया",30,RED)
    words=CAPTIONS[i]
    for offsets, caption in enumerate(words):
        text(d,540,(1601 if len(words)==1 else 1585)+55*offsets,caption,43)
    return f

def run(*args):
    sp.run(args,check=True)

def main():
    cues,mouths=audio()
    plates=[backdrop(i) for i in range(3)]
    proof=Image.open(ASSETS/"service.png").convert("RGBA").resize((736,115),Image.Resampling.LANCZOS)
    site=Image.open(ASSETS/"website.jpg").convert("RGBA").resize((620,375),Image.Resampling.LANCZOS)
    frames=OUT/"lesson"
    frames.mkdir(exist_ok=True)
    run("ffmpeg","-v","error","-y","-i",str(ASSETS/"lesson.mp4"),"-vf","fps=12,scale=630:-2",str(frames/"%03d.jpg"))
    lesson=[Image.open(p).convert("RGBA") for p in sorted(frames.glob("*.jpg"))]
    if not lesson:
        raise RuntimeError("Missing lesson example frames")
    with sp.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}",
       "-r",str(FPS),"-i","-","-f","f32le","-ar",str(RATE),"-ac","1","-i",str(OUT/"tail.f32"),
       "-c:v","libx264","-preset","fast","-crf","22","-pix_fmt","yuv420p","-r","30",
       "-c:a","aac","-b:a","128k","-t",str(LENGTH),str(OUT/"tail.mp4")],stdin=sp.PIPE) as pipe:
        for n in range(LENGTH*FPS):
            image=compose(n/FPS,cues,mouths,plates,proof,site,lesson)
            pipe.stdin.write(image.convert("RGB").tobytes())
        pipe.stdin.close()
        if pipe.wait():
            raise RuntimeError("Could not render continuation")
    final=OUT/"Postal_Edge_Postman_Easy_Hindi_50s.mp4"
    run("ffmpeg","-v","error","-y","-i",str(ASSETS/"intro.mp4"),"-i",str(OUT/"tail.mp4"),
        "-filter_complex","[0:v]setsar=1[v0];[1:v]setsar=1[v1];[v0][0:a][v1][1:a]concat=n=2:v=1:a=1[v][a]",
        "-map","[v]","-map","[a]","-c:v","libx264","-preset","fast","-crf","22","-maxrate","1350k","-bufsize","2700k",
        "-r","30","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k","-t","50","-movflags","+faststart",str(final))
    run("ffmpeg","-v","error","-xerror","-i",str(final),"-f","null","-")
    meta=json.loads(sp.check_output(["ffprobe","-v","error","-show_entries","format=duration:stream=width,height,codec_type",
                                    "-of","json",str(final)]))
    assert abs(float(meta["format"]["duration"])-50)<.04 and len(meta["streams"])==2, meta
    (OUT/"verification.json").write_text(json.dumps(meta,indent=2))
    sheet=Image.new("RGB",(864,768))
    for n,t in enumerate([.4,4.2,7+cues[0]+.8,7+cues[1]+1,
                          7+cues[4]+1,7+cues[5]+1,7+cues[7]+1,49.5]):
        data=sp.check_output(["ffmpeg","-v","error","-ss",str(t),"-i",str(final),
             "-vf","scale=216:384","-frames:v","1","-f","image2pipe","-vcodec","mjpeg","-"])
        import io
        sheet.paste(Image.open(io.BytesIO(data)),((n%4)*216,(n//4)*384))
    sheet.save(OUT/"checks.jpg",quality=91)

if __name__=="__main__":
    main()
