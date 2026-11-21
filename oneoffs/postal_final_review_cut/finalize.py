"""Final Postal Edge cut, assembled from the approved video and dialogue."""
import bisect
import importlib.util
import io
import json
import math
from functools import lru_cache
from pathlib import Path
import subprocess as sp

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("office_cut", HERE.parent / "postal_office_recut" / "revise.py")
office_cut = importlib.util.module_from_spec(spec)
spec.loader.exec_module(office_cut)
r = office_cut.r
W,H,FPS,RATE = r.W,r.H,r.FPS,r.RATE
OUT,ASSETS = r.OUT,r.ASSETS
PRIOR=office_cut.PRIOR
LENGTH=43
ORDER=(0,2,1,3,4,5,6,7,8)
GOLU={2,4,6}
NAME="Postal_Edge_Postman_Final_50s.mp4"
OFFICES={0:1,2:1,1:1,3:1,4:0,5:0,6:2,7:2,8:2}

def samples(start,end):
    return np.frombuffer(sp.check_output(["ffmpeg","-v","error","-ss",str(start),"-i",str(PRIOR),
         "-t",str(end-start),"-vn","-ar",str(RATE),"-ac","1","-f","f32le","-"]),dtype="<f4")

def trim_trailing(line):
    audible=np.flatnonzero(np.abs(line)>.004)
    assert audible.size
    return line[:min(len(line),audible[-1]+round(RATE*.065))]

def prepare_audio(cues):
    track=np.zeros(RATE*LENGTH,dtype="<f4")
    at=.065
    shots=[]
    for index in ORDER:
        end = cues[index+1]-.025 if index+1<len(cues) else 50
        line=trim_trailing(samples(cues[index],end))
        speed=1 if index in GOLU else 1.22
        if speed!=1:
            line=np.frombuffer(sp.check_output(["ffmpeg","-v","error","-f","f32le","-ar",str(RATE),"-ac","1","-i","-",
                "-af",f"atempo={speed}","-f","f32le","-"],input=line.tobytes()),dtype="<f4")
        start=round(at*RATE)
        track[start:start+len(line)]=line
        speech_end=at+len(line)/RATE
        shots.append({"index":index,"start":round(at,4),"end":round(speech_end,4),"speed":speed})
        at=speech_end+.13
    # Keep the website visible during a moving sample from the class.
    finish=shots[-1]["end"]
    assert 29<finish<LENGTH-.9,finish
    mix=track.copy()
    t=np.arange(round(RATE*.54))/RATE
    tone=.013*(np.sin(t*2*np.pi*523.25)+.45*np.sin(t*2*np.pi*784))*np.minimum(1,t/.035)*np.exp(-7*t)
    offset=round(RATE*(finish+.115))
    mix[offset:offset+len(tone)]+=tone
    (OUT/"speech.f32").write_bytes(mix.tobytes())
    return shots,r.measure_mouth(track[::3],FPS,LENGTH)

@lru_cache
def illustrated_office(i):
    return office_cut.office(i)

def board(frame,d,i,dt,proof,site,lesson,remaining):
    if i==0:
        card=Image.new("RGBA",(W,1100))
        r.routes(ImageDraw.Draw(card),dt)
        frame.alpha_composite(card,(0,120))
    elif i==1:
        r.box(d,(88,500,992,1097),48,r.CREAM,"#e5c799",3)
        r.text(d,540,599,"Postman / Mail Guard",57)
        r.text(d,540,686,"ड्राफ्ट में यही लिखा है",42,r.RED)
        frame.alpha_composite(proof,((W-proof.width)//2,779))
        r.text(d,540,1000,"डाक विभाग · 20 नवंबर 2026",35,r.GREEN)
    elif i==3:
        r.box(d,(113,532,967,919),52,r.CREAM,"#e5c799",3)
        r.text(d,540,646,"अभी ड्राफ्ट है",76,r.RED)
        r.text(d,540,795,"भर्ती की खबर आने पर पता चलेगा।",44,r.INK)
    elif i==5:
        r.box(d,(125,538,955,954),53,r.CREAM,"#e5c799",3)
        r.text(d,540,670,"पढ़ाई आज से शुरू करो",67)
        r.box(d,(228,755,852,876),39,r.GOLD)
        r.text(d,540,814,"आगे वक्त कम मिल सकता है",45,r.RED)
    elif i>=7:
        r.box(d,(70,489,1010,1192),52,r.CREAM,"#e5c799",3)
        r.text(d,540,592,"फ्री वीडियो क्लास",61,r.RED)
        if i==7:
            visual=site
        else:
            frame_index=round(dt*12)
            step=1 if remaining>0 else 2
            span=len(lesson)-1
            reflected=frame_index*step%(2*span)
            visual=lesson[min(reflected,2*span-reflected)]
        frame.alpha_composite(visual,((W-visual.width)//2,671))
        r.box(d,(243,1053,837,1142),35,r.GOLD)
        r.text(d,540,1096,"postaledge.in",43,r.INK)

def puppet_at(frame,t,dt,i,mouths,close):
    golu=i in GOLU
    mouths_at=mouths[min(len(mouths)-1,round(t*FPS))]
    if close:
        phase=r.ease(dt,0,.44)
        size=(int(712+32*phase),int(1089+49*phase))
        person=r.puppet(golu,t,0,.40 if golu else -.36,mouths_at,
                       "surprise" if golu and dt<.55 else "happy",(.77,"open"),.08,0,.12)
        frame.alpha_composite(person.resize(size,Image.Resampling.BICUBIC),((W-size[0])//2,485))
    else:
        for is_golu,x in ((True,102),(False,562)):
            face=.67 if is_golu else -.68
            mouth=mouths_at if is_golu==golu else None
            bob=(.24+.47*math.sin(math.pi*r.ease(dt,0,.65))) if is_golu==golu else .20
            action="chin" if is_golu!=golu else "left" if i in (0,1,7,8) else "open"
            character=r.puppet(is_golu,t,.04,face,mouth,"happy",(bob,action),face,0,.05)
            frame.alpha_composite(character.resize((401,614),Image.Resampling.BICUBIC),(x,978 if i>=7 else 935))

def captions(d,i):
    if i==1:
        words=["Postman और Mail Guard", "के लिए 5 की जगह 3 साल की बात।"]
    else:
        words=r.CAPTIONS[i]
    r.box(d,(84,1547,996,1724),42,r.WHITE,"#e5c799",3)
    r.text(d,540,1589,"गोलू" if i in GOLU else "डाकिया भैया",30,r.RED)
    for j,line in enumerate(words):
        r.text(d,540,1650 if len(words)==1 else 1635+47*j,line,43)

def picture(t,shoot,starts,mouths,proof,site,lesson):
    pos=max(0,bisect.bisect_right(starts,t)-1)
    shot=shoot[pos]
    i=shot["index"]
    dt=max(0,t-shot["start"])
    remaining=shoot[-1]["end"]-t
    frame=illustrated_office(OFFICES[i]).copy()
    d=ImageDraw.Draw(frame)
    r.box(d,(413,256,981,367),22,"#a72223","#f4c774",4)
    r.text(d,697,311,office_cut.OFFICE_LABELS[OFFICES[i]],56,"#fff4d6")
    close=i in GOLU
    if not close:
        board(frame,d,i,dt,proof,site,lesson,remaining)
    puppet_at(frame,t,dt,i,mouths,close)
    if remaining>-.12:
        captions(d,i)
    else:
        r.box(d,(130,1553,950,1708),36,r.WHITE,"#e5c799",3)
        r.text(d,540,1630,"क्लास की झलक · फ्री डेमो",44,r.RED)
    return frame

def main():
    source=json.loads((OUT/"original-timing.json").read_text())
    assert source["duration"]==50 and source["hook_seconds"]==7
    shots,mouths=prepare_audio(source["continuation_cues"])
    starts=[s["start"] for s in shots]
    proof=Image.open(ASSETS/"service.png").convert("RGBA").resize((754,175),Image.Resampling.LANCZOS)
    site=Image.open(ASSETS/"website.jpg").convert("RGBA").resize((620,375),Image.Resampling.LANCZOS)
    folder=OUT/"lesson"
    folder.mkdir(exist_ok=True)
    r.run("ffmpeg","-v","error","-y","-i",str(ASSETS/"lesson.mp4"),"-vf","fps=12,scale=630:-2",str(folder/"%03d.jpg"))
    lesson=[Image.open(p).convert("RGBA") for p in sorted(folder.glob("*.jpg"))]
    assert len(lesson)>1
    tail=OUT/"tail.mp4"
    with sp.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}",
        "-r",str(FPS),"-i","-","-f","f32le","-ar",str(RATE),"-ac","1","-i",str(OUT/"speech.f32"),
        "-c:v","libx264","-preset","fast","-crf","22","-pix_fmt","yuv420p","-r","30",
        "-c:a","aac","-b:a","128k","-t",str(LENGTH),str(tail)],stdin=sp.PIPE) as pipe:
        for i in range(FPS*LENGTH):
            pipe.stdin.write(picture(i/FPS,shots,starts,mouths,proof,site,lesson).convert("RGB").tobytes())
        pipe.stdin.close()
        if pipe.wait():
            raise RuntimeError("Scene render failed")
    final=OUT/NAME
    font="/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
    filters=("[0:v]trim=end=7,setpts=PTS-STARTPTS,setsar=1[v0];[0:a]atrim=end=7,asetpts=PTS-STARTPTS[a0];"
        "[1:v]setsar=1[v1];[v0][a0][v1][1:a]concat=n=2:v=1:a=1[c][a];"
        "[c]drawbox=x=72:y=118:w=936:h=91:color=0xfff5df:t=fill,"
        "drawbox=x=72:y=205:w=936:h=4:color=0xb9412d:t=fill,"
        f"drawtext=fontfile={font}:text='POSTAL EDGE':x=110:y=146:fontsize=33:fontcolor=0x842e26,"
        f"drawtext=fontfile={font}:text='postaledge.in':x='676+24*sin(t/2)':y=143:fontsize=40:fontcolor=0x223742[v]")
    r.run("ffmpeg","-v","error","-y","-i",str(PRIOR),"-i",str(tail),"-filter_complex",filters,
       "-map","[v]","-map","[a]","-c:v","libx264","-preset","fast","-crf","22","-maxrate","1350k","-bufsize","2700k",
       "-r","30","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k","-t","50","-movflags","+faststart",str(final))
    r.run("ffmpeg","-v","error","-xerror","-i",str(final),"-f","null","-")
    meta=json.loads(sp.check_output(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_type,width,height","-of","json",str(final)]))
    assert abs(float(meta["format"]["duration"])-50)<.04 and len(meta["streams"])==2
    (OUT/"final-check.json").write_text(json.dumps({"media":meta,"shots":shots},indent=2))
    sheet=Image.new("RGB",(1080,1152))
    for pos,t in enumerate([.3,5.8]+[7+s["start"]+.35 for s in shots]+[49.5]):
        frame=sp.check_output(["ffmpeg","-v","error","-ss",str(t),"-i",str(final),"-vf","scale=216:384",
           "-frames:v","1","-f","image2pipe","-vcodec","mjpeg","-"])
        sheet.paste(Image.open(io.BytesIO(frame)),((pos%5)*216,(pos//5)*384))
    sheet.save(OUT/"review.jpg",quality=94)

if __name__=="__main__":
    main()
