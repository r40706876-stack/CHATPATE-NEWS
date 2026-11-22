import base64
from bisect import bisect_right
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import importlib.util
import io
import json
import math
from pathlib import Path
import subprocess as sp
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import render_natural as art

W, H, FPS, RATE = art.W, art.H, art.FPS, art.RATE
GREEN, CREAM, INK, RED = art.GREEN, art.CREAM, art.INK, art.RED
rect, ease = art.rect, art.ease
OUT = Path("transfer-full-output")
OUT.mkdir(exist_ok=True)
FINAL = OUT / "Postal_Edge_GDS_Transfer_Postman_Draft.mp4"

LINES = (
    ("golu", "भैया, ट्रांसफर लेकर फँस गया! नए पोस्टमैन ड्राफ्ट में पुरानी सर्विस बेकार हो गई क्या?"),
    ("golu", "दो साल एम पी में हुए, एक साल हरियाणा में। सब बोल रहे हैं, तीनों साल एक ही डिवीजन में चाहिए!"),
    ("bhaiya", "पेज पाँच देखो। जिस डिवीजन में भर्ती है, उसके जी डी एस होने चाहिए। और जी डी एस के तौर पर तीन साल नियमित सेवा चाहिए।"),
    ("bhaiya", "तुम्हारे दो साल एम पी में हुए और एक साल हरियाणा में। तीनों साल हरियाणा में ही करने हैं, ऐसा ड्राफ्ट में कहीं नहीं लिखा।"),
    ("golu", "और ये तीन साल कब तक पूरे होने चाहिए?"),
    ("bhaiya", "अगर वैकेंसी दो हज़ार सत्ताईस की है, तो ड्राफ्ट के हिसाब से एक जनवरी दो हज़ार सत्ताईस तक।"),
    ("golu", "अभी ये ड्राफ्ट है। भर्ती का नोटिस ज़रूर देखना। और ये वीडियो ट्रांसफर वाले दोस्त को भेजो!"),
)


def voice_worker(role, script):
    spec = importlib.util.spec_from_file_location("approved_voice", script)
    voices = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(voices)
    voices.OUT = OUT.resolve()
    voices.DIALOGUE = LINES
    name = voices.VOICES[role][0]
    instruction = ("Young male Hindi character Golu, genuine concern in a normal conversation. "
                   "Natural, clear delivery at everyday speaking speed." if role=="golu" else
                   "Warm adult male postman explaining something to Golu. Speak naturally and clearly in Hindi at everyday speaking speed.")
    voices.VOICES[role] = (name, instruction+" Read the exact line, without filler or added words.")
    voices.voice_parts(role)


def soundtrack(voice_script):
    workers = tuple(sp.Popen([sys.executable,__file__,"--voice",role,str(voice_script)])
                    for role in ("golu","bhaiya"))
    status = [worker.wait() for worker in workers]
    if any(status):
        raise RuntimeError(f"Voice preparation failed: {status}")
    dry_parts, report = [], []
    offset=0
    for i,(role,words) in enumerate(LINES):
        raw=sp.check_output(["ffmpeg","-v","error","-i",str(OUT/f"voice{i}.wav"),
                             "-af","silenceremove=start_periods=1:start_duration=0.024:start_threshold=-45dB:stop_periods=1:stop_duration=0.45:stop_threshold=-49dB,loudnorm=I=-17:TP=-3:LRA=7",
                             "-ac","1","-ar",str(RATE),"-f","f32le","-"])
        voice=np.frombuffer(raw,dtype="<f4")
        assert 1.1*RATE < len(voice)<13*RATE,(i,len(voice))
        start_pad=.035 if i==0 else .07
        end_pad=.27 if i<6 else .37
        scene_frames=math.ceil((len(voice)/RATE+start_pad+end_pad)*FPS)
        scene=np.zeros(scene_frames*(RATE//FPS),dtype="float32")
        p=round(start_pad*RATE)
        scene[p:p+len(voice)] = voice
        dry_parts.append(scene)
        report.append({"start":offset/RATE,"scene":i,"speaker":role,"voice_seconds":round(len(voice)/RATE,3),"end":(offset+len(scene))/RATE})
        offset+=len(scene)
    dry=np.concatenate(dry_parts)
    mix=dry.copy()
    rng=np.random.default_rng(29)
    cues=[(.16,.057),(.43,.036),(report[1]["start"]+.06,.033),
          (report[2]["start"]+.06,.044),(report[5]["start"]+.12,.038),
          (report[6]["start"]+.14,.031)]
    for moment, gain in cues:
        ticks=np.arange(int(.11*RATE))/RATE
        noise=rng.uniform(-1,1,len(ticks))
        effect=gain*(.39*(noise-np.r_[0,noise[:-1]])+.61*np.sin(2*np.pi*151*ticks))
        effect*=np.sin(np.pi*ticks/.11)**2
        start=round(moment*RATE)
        mix[start:start+len(ticks)]+=effect
    (OUT/"dialogue.f32").write_bytes(np.clip(mix,-.96,.96).astype("<f4").tobytes())
    (OUT/"timing.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
    length=len(dry)/RATE
    print(json.dumps({"duration":length,"lines":report,"audio_speed":"original"},ensure_ascii=False),flush=True)
    return art.measure_mouth(dry[::3], FPS, length),report


@lru_cache(maxsize=48)
def face(size, hindi):
    return ImageFont.truetype(art.DEV if hindi else art.LAT, size)


def text(im,x,y,value,size,color,hindi=True):
    d=ImageDraw.Draw(im)
    f=face(size,hindi)
    a,b,c,e=d.textbbox((0,0),value,font=f)
    d.text((x-(a+c)/2,y-(b+e)/2),value,font=f,fill=color)


def title(im,lines):
    rect(im,(43,260,677,425),CREAM,19,"#DADECB",2)
    rect(im,(68,286,78,395),GREEN,4)
    text(im,365,314,lines[0],44,INK)
    text(im,365,376,lines[1],62,INK)


def note(im, lines, y=978):
    if len(lines)==1:
        rect(im,(64,y-41,656,y+41),CREAM,14,"#ABCAB1",2)
        text(im,360,y,lines[0],31,INK)
    else:
        rect(im,(65,y-56,655,y+56),CREAM,14,"#ABCAB1",2)
        text(im,360,y-21,lines[0],31,INK)
        text(im,360,y+22,lines[1],26,INK)


def state_cards(im, t, y=973):
    xoff=137+13*ease(t/.34)
    for x,state,count,is_hindi in ((360-xoff,"MP","2 साल",False),(360+xoff,"हरियाणा","1 साल",True)):
        rect(im,(x-125,y-43,x+125,y+43),CREAM,13,"#ABCAB1",2)
        rect(im,(x-111,y-26,x-103,y+27),GREEN,4)
        text(im,x-45,y,state,27,INK,is_hindi)
        text(im,x+57,y,count,30,INK)
    d=ImageDraw.Draw(im)
    d.line((337,y,381,y),fill=CREAM,width=3)
    d.polygon([(381,y),(371,y-6),(371,y+6)],fill=CREAM)


def proof_card(im, scan, t, length):
    p=.91+.09*ease(t/.42)
    wide=round(557*p)
    high=round(scan.height*wide/scan.width)
    x=(W-wide)//2
    y=352+(round(18*(1-ease(t/.44))))
    rect(im,(x-12,y-61,x+wide+12,y+high+20),CREAM,14,"#ABCAB1",2)
    text(im,360,y-33,"भर्ती नियमों का ड्राफ्ट · पेज 5",28,INK)
    sheet=scan.resize((wide,high),Image.Resampling.LANCZOS)
    mask=Image.new("RGBA",sheet.size)
    d=ImageDraw.Draw(mask)
    phase=t/max(.1,length)
    if phase>=.18:
        for ya,yb in ((199,211),(212,225)):
            d.rectangle((10,round(high*(ya-167)/112),round(wide*.975),round(high*(yb-167)/112)),fill=(144,211,161,96))
    if phase>=.55:
        for ya,yb in ((226,238),(239,250)):
            d.rectangle((10,round(high*(ya-167)/112),round(wide*.975),round(high*(yb-167)/112)),fill=(245,210,118,83))
    im.alpha_composite(Image.alpha_composite(sheet,mask),(x,y))


def render_frame(base,desk,scan,scene,t,elapsed,length,mouth):
    speaker=LINES[scene][0]
    zoom=.037*ease(elapsed/2.25) if scene==0 else .012*ease(elapsed/.5)
    dx,dy=round(W*zoom),round(H*zoom)
    im=base.crop((dx,dy,W-dx,H-dy)).resize((W,H),Image.Resampling.BICUBIC) if dx else base.copy()
    rect(im,(45,84,675,132),CREAM,10)
    text(im,145,108,"POSTAL EDGE",18,INK,False)
    text(im,564,108,"postaledge.in",17,INK,False)
    rect(im,(411,166,658,217),RED,7)
    text(im,534,192,"डाक काउंटर",25,CREAM)
    rect(im,(235,222,485,251),GREEN,6)
    text(im,360,236,"नया पोस्टमैन ड्राफ्ट",19,CREAM)

    if scene==0:
        title(im,("ट्रांसफर लेकर","फँस गए?"))
    elif scene==1:
        title(im,("ट्रांसफर के बाद","3 साल कैसे गिनें?"))
    elif scene==3:
        title(im,("तीनों साल","एक ही जगह?"))
    elif scene==4:
        title(im,("3 साल","कब तक पूरे हों?"))
    elif scene==5:
        rect(im,(45,285,675,473),CREAM,18,"#ABCAB1",2)
        text(im,360,333,"अगर वैकेंसी 2027 की है",33,INK)
        date_p=ease((elapsed-.65)/.45)
        if date_p>0:
            text(im,360,405+round(10*(1-date_p)),"1 जनवरी 2027",62,INK)
    elif scene==6:
        rect(im,(45,285,675,473),CREAM,18,"#ABCAB1",2)
        text(im,360,345,"अभी यह ड्राफ्ट है",50,INK)
        text(im,360,418,"भर्ती का नोटिस देखें",36,INK)

    focus=ease(elapsed/1.9)
    for golu in (False,True):
        active=(golu and speaker=="golu") or (not golu and speaker=="bhaiya")
        direction=1 if golu else -1
        gaze=direction*(.29+.47*ease((elapsed-.39)/.62))
        scale=(.83 if scene==2 else 1.0)+.059*focus*active
        x=(45 if golu else 357)+(-8 if golu else 5)*focus
        y=(632 if scene==2 else 507)-(0 if scene==2 else 12*focus)+4*math.sin(t*2.5+int(golu))
        gesture=("right" if scene==0 and elapsed<.78 else "open") if active else "chin"
        energy=.36+.34*ease(elapsed/.5)
        mood=("surprise" if scene<=1 else "think") if golu else "happy"
        person=art.puppet(golu,t,0,gaze,mouth if active else None,mood,(energy,gesture),gaze,0,0)
        person=person.resize((round(298*scale),round(456*scale)),Image.Resampling.LANCZOS)
        im.alpha_composite(person,(round(x),round(y)))

    im.alpha_composite(desk,(0,857))
    if scene==2:
        proof_card(im,scan,elapsed,length)
        note(im,("भर्ती वाली डिवीजन के GDS","GDS के तौर पर 3 साल नियमित सेवा"),1004)
    else:
        folder_at=elapsed if scene==0 else .85
        f=art.document(folder_at)
        slide=ease(folder_at/.31)
        f=f.rotate(15-19*slide,Image.Resampling.BICUBIC,expand=True)
        im.alpha_composite(f,(round(182-259*(1-slide)),round(742-29*math.sin(math.pi*slide))))
        if scene==0 and elapsed>length*.58:
            note(im,("पुरानी सर्विस गिनेगी?",))
        elif scene==1:
            state_cards(im,elapsed)
        elif scene==3:
            if elapsed<length*.53:
                state_cards(im,elapsed)
            else:
                note(im,("एक ही जगह 3 साल की शर्त","ड्राफ्ट में नहीं लिखी"))
        elif scene==4:
            note(im,("तीन साल कब तक पूरे हों?",))
        elif scene==5:
            note(im,("ड्राफ्ट के हिसाब से",))
        elif scene==6:
            rect(im,(61,943,659,1025),CREAM,14,"#ABCAB1",2)
            text(im,360,984,"ट्रांसफर वाले दोस्त को भेजो",31,INK)
    return im.convert("RGB")


def main(asset, voice_script):
    lips, report=soundtrack(voice_script)
    backdrop,desk=art.backdrop(asset),art.counter()
    page_file=Path(__file__).with_name("page5.b64")
    scan=Image.open(io.BytesIO(base64.b64decode(page_file.read_bytes()))).convert("RGBA")
    start_times=[item["start"] for item in report]
    qc_frames={0,*[round((item["start"]+.70)*FPS) for item in report]}
    command=["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24",
             "-s",f"{W}x{H}","-framerate",str(FPS),"-i","-","-f","f32le","-ar",str(RATE),
             "-ac","1","-i",str(OUT/"dialogue.f32"),"-c:v","libx264","-preset","fast","-crf","18",
             "-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-movflags","+faststart",str(FINAL)]
    with sp.Popen(command, stdin=sp.PIPE) as encoder:
        for frame_id,mouth in enumerate(lips):
            t=frame_id/FPS
            scene=bisect_right(start_times,t+1e-8)-1
            cue=report[scene]
            im=render_frame(backdrop,desk,scan,scene,t,t-cue["start"],cue["end"]-cue["start"],mouth)
            if frame_id in qc_frames:
                im.resize((360,640),Image.Resampling.LANCZOS).save(OUT/f"qc-{frame_id:04d}.jpg",quality=91)
            encoder.stdin.write(im.tobytes())
        encoder.stdin.close()
        if encoder.wait():
            raise RuntimeError("Video encoding failed")
    sp.run(["ffmpeg","-v","error","-xerror","-i",str(FINAL),"-f","null","-"],check=True)
    package=OUT/"review"
    package.mkdir(exist_ok=True)
    for path in (*OUT.glob("qc-*.jpg"),OUT/"timing.json"):
        path.rename(package/path.name)


if __name__=="__main__":
    if sys.argv[1]=="--voice":
        voice_worker(sys.argv[2],Path(sys.argv[3]).resolve())
    else:
        main(Path(sys.argv[1]),Path(sys.argv[2]))
