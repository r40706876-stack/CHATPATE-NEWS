import base64
from bisect import bisect_right
from functools import lru_cache
import io
import json
import math
from pathlib import Path
import subprocess as sp
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
import render_full as art

W,H,RATE,FPS=720,1280,48000,24
CREAM,INK,GREEN,RED=art.CREAM,art.INK,art.GREEN,art.RED
MINT, GOLD = "#BFE1C4", "#F4CD76"
BASE_CUT=37.0
END_LINE="पोस्टल एज पर चित्रों से पढ़ेंगे। देखो, एक पेड़ से एच ओ, एस ओ, बी ओ समझो।"
OUT=Path("transfer-motion-output")
OUT.mkdir(exist_ok=True)
text,rect,ease=art.text,art.rect,art.ease
SCENES=(0.,2.55,5.5,8.3,11.433333333,15.55,19.033333333,22.45,26.133333333,28.5,34.333333333,37.)
NAMES=("hook","golu","states","travel","page","proof","bhaiya","three","date_question","calendar","notice","demo")


def read_audio(file):
    data=sp.check_output(["ffmpeg","-v","error","-i",str(file),"-vn","-ac","1","-ar",str(RATE),"-f","f32le","-"])
    return np.frombuffer(data,dtype="<f4")


def audio(previous, voice_script):
    import importlib.util
    spec=importlib.util.spec_from_file_location("approved_voice",voice_script)
    voice=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(voice)
    voice.OUT=OUT.resolve()
    voice.DIALOGUE=(("golu",END_LINE),)
    name=voice.VOICES["golu"][0]
    voice.VOICES["golu"]=(name,"Natural young male Hindi speaker Golu, same pitch and relaxed energy as the prior scene. Read this exact line fairly clearly at everyday speed.")
    voice.voice_parts("golu")
    raw=sp.check_output(["ffmpeg","-v","error","-i",str(OUT/"voice0.wav"),"-af",
                         "silenceremove=start_periods=1:start_duration=0.02:start_threshold=-44dB:stop_periods=1:stop_duration=0.45:stop_threshold=-50dB,loudnorm=I=-17:TP=-3:LRA=7",
                         "-ac","1","-ar",str(RATE),"-f","f32le","-"])
    tail=np.frombuffer(raw,dtype="<f4")
    assert 2.5*RATE < len(tail) < 7*RATE, len(tail)
    head=read_audio(previous)[:round(BASE_CUT*RATE)]
    end_frames=math.ceil((len(tail)/RATE+.27)*FPS)
    narration=np.concatenate((head,np.pad(tail,(round(.04*RATE),end_frames*(RATE//FPS)-len(tail)-round(.04*RATE)))))
    narration.astype("<f4").tofile(OUT/"audio.f32")
    duration=len(narration)/RATE
    summary={"duration":duration,"reused_audio_until":BASE_CUT,"demo_line_seconds":round(len(tail)/RATE,2),"golu_voice":name,"outro":END_LINE}
    (OUT/"motion-check.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    print(json.dumps(summary,ensure_ascii=False),flush=True)
    return art.art.measure_mouth(narration[::3],FPS,duration),duration


def bg_photo(path, tone):
    crop=ImageOps.fit(Image.open(path).convert("RGB"),(W,H),centering=(.50,.46))
    return Image.blend(crop,Image.new("RGB",(W,H),tone),.22).convert("RGBA")


def board():
    im=Image.new("RGBA",(W,H),"#E4EEE1")
    d=ImageDraw.Draw(im)
    for x in range(0,W,28):
        d.line((x,0,x,H), fill="#D6E5D6",width=1)
    for y in range(0,H,28):
        d.line((0,y,W,y), fill="#D6E5D6",width=1)
    return im


def upper(im,label):
    rect(im,(40,78,680,124),CREAM,10)
    text(im,156,101,"POSTAL EDGE",20,INK,False)
    text(im,550,101,"postaledge.in",18,INK,False)
    rect(im,(53,157,667,206),GREEN,10)
    text(im,360,182,label,26,CREAM)


def actor(im,golu,t,mouth,x,y,w,mood="think",gesture="open",strength=.73,walking=0.,facing=None):
    face=(.53 if golu else -.64) if facing is None else facing
    pose=art.art.puppet(golu,t,walking,face,mouth,mood,(strength,gesture),face,0,.12)
    h=round(w*520/340)
    im.alpha_composite(pose.resize((w,h),Image.Resampling.LANCZOS),(round(x),round(y)))


def label(im,y,top,bottom=None):
    height=155 if bottom else 86
    rect(im,(49,y,671,y+height),CREAM,16,"#B5CDB2",2)
    if bottom:
        text(im,360,y+48,top,42,INK)
        text(im,360,y+109,bottom,54,INK)
    else:
        text(im,360,y+43,top,35,INK)


def load_page():
    return Image.open(io.BytesIO(base64.b64decode(b"".join(p.read_bytes() for p in sorted(Path(__file__).with_name("motion_draft").glob("draft-*.b64")))))).convert("RGBA")


def draw_proof(im,page,t,dt,mouth,zoomed=False):
    if zoomed:
        label(im,239,"नियम की असली लाइन")
        crop_rect=(86,196,271,265)
        crop=page.crop(tuple(round(value*(page.width/612 if i%2==0 else page.height/792)) for i,value in enumerate(crop_rect)))
        x,y,w=48,407,622
        h=round(w*crop.height/crop.width)
        crop=crop.resize((w,h),Image.Resampling.LANCZOS)
        rect(im,(x-8,y-10,x+w+8,y+h+10),CREAM,13,"#ACCAA8",2)
        im.alpha_composite(crop,(x,y))
        tint=Image.new("RGBA",(W,H))
        d=ImageDraw.Draw(tint)
        for ya,yb,col in ((212,225,(130,210,152,102)),(226,250,(248,202,100,108))):
            d.rectangle((x+10,y+round((ya-196)*h/69),x+w-9,y+round((yb-196)*h/69)),fill=col)
        im.alpha_composite(tint)
        actor(im,False,t,mouth,373-14*ease(dt/.42),559,304,"happy","left",.94)
        label(im,976,"जी डी एस के तौर पर 3 साल")
        return
    # Keep the whole original page visible while Bhaiya crosses to its margin.
    p=ease(dt/.63)
    w=round(622-52*(1-p)); h=round(w*page.height/page.width)
    x=(W-w)//2; y=243+round(27*(1-p))
    rect(im,(x-8,y-8,x+w+8,y+h+8),CREAM,12,"#ADC9AB",2)
    im.alpha_composite(page.resize((w,h),Image.Resampling.LANCZOS),(x,y))
    approach=ease((dt-.25)/1.05)
    pointing=ease((dt-1.02)/.48)
    px=x+round(w*269/612)
    py=y+round(h*226/792)
    tint=Image.new("RGBA",(W,H))
    if pointing:
        hi=ImageDraw.Draw(tint)
        hi.rounded_rectangle((x+round(w*89/612),y+round(h*212/792),px, y+round(h*251/792)),
                             radius=4,fill=(255,204,99,round(115*pointing)),
                             outline=(156,91,39,round(225*pointing)),width=2)
    im.alpha_composite(tint)
    ax=round(px-14 + 161*(1-approach))
    ay=round(py-166+114*(1-approach))
    actor(im,False,t,mouth,ax,ay,232,"happy","left",.46+.54*pointing, .78*math.sin(math.pi*approach))
    if pointing>.70:
        d=ImageDraw.Draw(im)
        d.ellipse((px-5,py-5,px+5,py+5),fill=GREEN,outline=CREAM,width=2)
    rect(im,(65,1083,655,1156),CREAM,12,"#ABCAB1",2)
    text(im,360,1119,"भर्ती वाली डिवीजन की शर्त",30,INK)


def state_map(im,t,dt,mouth,travel):
    lt=412+round(25*(1-ease(dt/.36)))
    for x, place, count, hindi in ((177,"MP","2 साल",False),(543,"हरियाणा","1 साल",True)):
        rect(im,(x-135,lt-62,x+135,lt+76),CREAM,16,"#A9C7A9",2)
        text(im,x,lt-22,place,34,INK,hindi)
        text(im,x,lt+35,count,42,GREEN)
    d=ImageDraw.Draw(im)
    d.line((316,lt+5,403,lt+5),fill=GREEN,width=5)
    d.polygon([(410,lt+5),(396,lt-4),(396,lt+14)],fill=GREEN)
    q=ease(dt/.53)
    stamp_x=147+427*q if travel else 178
    rect(im,(stamp_x-58,lt+99,stamp_x+58,lt+155),GREEN,8)
    text(im,stamp_x,lt+127,"सेवा",25,CREAM)
    if travel:
        label(im,897,"तीनों साल एक डिवीजन में?")
    else:
        label(im,897,"ट्रांसफर से पहले और बाद")
    actor(im,True,t,mouth,120+176*q if travel else 238,647,236,"surprise","open")


@lru_cache(maxsize=25)
def image_zoom(base_id, step):
    im=BACKS[base_id]
    z=step*.004
    if not z: return im
    x,y=round(W*z),round(H*z)
    return im.crop((x,y,W-x,H-y)).resize((W,H),Image.Resampling.BICUBIC)


def frame(t,mouth,page,tree):
    i=bisect_right(SCENES,t+1e-8)-1
    scene=NAMES[i]; dt=t-SCENES[i]
    if scene in ("states","page","proof","calendar","demo"):
        base="board"
    elif scene=="travel":
        base="outside"
    elif scene in ("bhaiya","three","notice"):
        base="side"
    else:
        base="office"
    if scene in ("hook","golu","bhaiya","date_question"):
        im=image_zoom(base,round(8*ease(dt/.77))).copy()
    else:
        im=BACKS[base].copy()
    tags={"hook":"नया पोस्टमैन ड्राफ्ट","golu":"गोलू का सवाल","states":"सेवा का उदाहरण","travel":"ट्रांसफर के बाद","page":"असली ड्राफ्ट   पूरा पेज 5",
          "proof":"ड्राफ्ट   पेज 5 का क्लोज़-अप","bhaiya":"डाकिया भैया की बात","three":"एक ही डिवीजन की शर्त?","date_question":"गोलू का अगला सवाल",
          "calendar":"तारीख का उदाहरण","notice":"भर्ती का नोटिस देखें","demo":"चित्रों से पढ़ाई   असली क्लास डेमो"}
    upper(im,tags[scene])
    if scene=="hook":
        art.title(im,("ट्रांसफर लेकर","फँस गए?"))
        actor(im,False,t,None,381,493,285,"happy","chin")
        actor(im,True,t,mouth,39,461,330,"surprise","open")
        im.alpha_composite(DESK,(0,858))
        folder=art.art.document(dt).rotate(10-14*ease(dt/.38),Image.Resampling.BICUBIC,expand=True)
        im.alpha_composite(folder,(round(-71+256*ease(dt/.38)),727))
    elif scene=="golu":
        actor(im,True,t,mouth,100-8*ease(dt/.60),317-22*ease(dt/.60),520,"surprise","open")
        label(im,1001,"पुरानी सर्विस गिनेगी?")
    elif scene in ("states","travel"):
        state_map(im,t,dt,mouth,scene=="travel")
    elif scene in ("page","proof"):
        draw_proof(im,page,t,dt,mouth,scene=="proof")
    elif scene=="bhaiya":
        actor(im,False,t,mouth,114-12*ease(dt/.55),293,515,"happy","left",.87)
        label(im,983,"2 साल एमपी में और 1 साल हरियाणा में")
    elif scene=="three":
        label(im,278,"तीनों साल","हरियाणा में ही?")
        actor(im,False,t,mouth,329,545,334,"happy","left")
        rect(im,(54,942,666,1053),GREEN,15)
        text(im,360,996,"ड्राफ्ट में ऐसी शर्त नहीं लिखी",33,CREAM)
    elif scene=="date_question":
        actor(im,True,t,mouth,108,333,501,"think","chin")
        label(im,991,"तीन साल कब तक पूरे हों?")
    elif scene=="calendar":
        p=ease(dt/.50)
        y=280+round(67*(1-p))
        rect(im,(62,y,658,y+401),CREAM,20,"#B0C9AA",3)
        rect(im,(62,y,658,y+104),GREEN,19)
        text(im,360,y+51,"अगर वैकेंसी 2027 की है",38,CREAM)
        text(im,360,y+204,"1 जनवरी",77,INK)
        text(im,360,y+303,"2027",76,GREEN,False)
        actor(im,False,t,mouth,410,701,255,"happy","left")
        rect(im,(65,978,368,1051),CREAM,14)
        text(im,216,1015,"ड्राफ्ट के हिसाब से",26,INK)
    elif scene=="notice":
        label(im,268,"अभी यह","ड्राफ्ट है")
        actor(im,True,t,mouth,66,456,329,"think","chin")
        actor(im,False,t,None,395,507,266,"happy","chin")
        im.alpha_composite(DESK,(0,854))
        label(im,965,"भर्ती का नोटिस ज़रूर देखें")
    else:
        q=ease(dt/.42)
        y=263+round(35*(1-q))
        shown=tree[min(len(tree)-1,round(dt*FPS))]
        rect(im,(39,y-9,681,y+504),CREAM,18,"#A9CAA8",2)
        im.alpha_composite(shown,(51,y))
        actor(im,True,t,mouth,46,759,201,"happy","open")
        rect(im,(261,804,665,898),GREEN,15)
        text(im,463,850,"ऐसे चित्रों से समझेंगे",31,CREAM)
        rect(im,(275,927,649,993),CREAM,12)
        text(im,462,960,"postaledge.in",25,INK,False)
    return im.convert("RGB")


def main():
    previous,voice_script,assets,lesson=map(Path,sys.argv[1:5])
    mouths,duration=audio(previous,voice_script)
    end_count=round((duration-BASE_CUT)*FPS)
    demo=sp.check_output(["ffmpeg","-v","error","-ss","36.65","-i",str(lesson),"-an",
                          "-vf",f"crop=618:488:51:221,fps={FPS}","-frames:v",str(end_count),
                          "-pix_fmt","rgb24","-f","rawvideo","-"])
    image_bytes=618*488*3
    tree=[Image.frombytes("RGB",(618,488),demo[i:i+image_bytes]).convert("RGBA") for i in range(0,len(demo),image_bytes)]
    assert len(tree)>60,len(tree)
    global DESK, BACKS
    DESK=art.art.counter()
    BACKS={"office":bg_photo(assets/"office1.jpg","#F3E6C9"),"outside":bg_photo(assets/"office0.jpg","#E9EBD9"),
           "side":bg_photo(assets/"office2.jpg","#EFE6CD"),"board":board()}
    page=load_page()
    qc={round((s+(1.9 if j==4 else 1.0 if j==11 else .62))*FPS) for j,s in enumerate(SCENES)}
    qc.add(round((duration-.32)*FPS))
    final=OUT/"Postal_Edge_GDS_Transfer_Postman_Draft.mp4"
    command=["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24",
             "-s",f"{W}x{H}","-framerate",str(FPS),"-i","-","-f","f32le","-ar",str(RATE),
             "-ac","1","-i",str(OUT/"audio.f32"),"-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p",
             "-c:a","aac","-b:a","192k","-movflags","+faststart",str(final)]
    with sp.Popen(command,stdin=sp.PIPE) as enc:
        for n,m in enumerate(mouths):
            im=frame(n/FPS,m,page,tree)
            if n in qc:
                im.resize((360,640),Image.Resampling.LANCZOS).save(OUT/f"qc-{n:04d}.jpg",quality=92)
            enc.stdin.write(im.tobytes())
        enc.stdin.close()
        if enc.wait(): raise RuntimeError("Video encode failed")
    sp.run(["ffmpeg","-v","error","-xerror","-i",str(final),"-f","null","-"],check=True)


if __name__=="__main__":
    main()
