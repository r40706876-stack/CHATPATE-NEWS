"""Build the faster Postal Edge recut from the approved video and narration."""
import bisect
from functools import lru_cache
import importlib.util
import io
import json
import math
from pathlib import Path
import subprocess as sp

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("prior", HERE.parent / "postal_easy_hindi_reel" / "render.py")
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
W,H,FPS,RATE=r.W,r.H,r.FPS,r.RATE
OUT,ASSETS=r.OUT,r.ASSETS
CUT=374/30
LENGTH=50-CUT
PACE=1.12
PRIOR=r.CORE / "previews" / "Postal_Edge_Postman_Easy_Hindi_50s.mp4"
OFFICE_LABELS=("डाकघर","डाक काउंटर","डाकघर का बरामदा")
FILE="Postal_Edge_Postman_Post_Office_50s.mp4"

def audio(cues):
    raw=sp.check_output(["ffmpeg","-v","error","-ss",str(CUT),"-i",str(PRIOR),
       "-vn","-af",f"atempo={PACE}","-ac","1","-ar",str(RATE),"-f","f32le","-"])
    samples=np.frombuffer(raw,dtype="<f4")
    count=round(LENGTH*RATE)
    assert 30<len(samples)/RATE<LENGTH
    speech=np.zeros(count,dtype="<f4")
    speech[:len(samples)]=samples
    # A soft finish under the clickable-looking demo card, after the final spoken line.
    mix=speech.copy()
    for offset, frequency in ((0,523.25),(.13,659.25),(.25,783.99)):
        t=np.arange(round(.44*RATE))/RATE
        tone=.026*np.sin(2*np.pi*frequency*t)*np.minimum(1,t/.025)*np.exp(-t*8)
        start=round((len(samples)/RATE-.06+offset)*RATE)
        mix[start:start+len(tone)] += tone
    (OUT/"paced.f32").write_bytes(mix.tobytes())
    at=[(c-CUT)/PACE for c in cues]
    return at,r.measure_mouth(speech[::3],FPS,LENGTH),len(samples)/RATE

@lru_cache
def office(index):
    photo=Image.open(ASSETS/f"office{index}.jpg").convert("RGB")
    fill=ImageOps.fit(photo,(W,H),Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(29))
    frame=Image.blend(fill,Image.new("RGB",(W,H),"#f2d7a8"),.22).convert("RGBA")
    foreground=ImageOps.fit(photo,(W,1210),Image.Resampling.LANCZOS,centering=(.5,.45)).convert("RGBA")
    frame.alpha_composite(foreground)
    wash=Image.new("RGBA",(W,H));d=ImageDraw.Draw(wash)
    for y in range(H):
        alpha=round(58*(1-r.ease(y,0,280))+230*r.ease(y,1390,1830))
        d.line((0,y,W,y),fill=(29,23,17,alpha) if y<500 else (247,233,199,alpha))
    return Image.alpha_composite(frame,wash)

def place_labels(d,index):
    r.box(d,(65,125,388,194),27,"#fff5df")
    r.text(d,226,160,"POSTAL EDGE",26,r.RED)
    r.box(d,(456,276,1004,398),20,"#a72223","#f4c774",4)
    r.text(d,730,336,OFFICE_LABELS[index],64,"#fff4d6")

def demo_end(d,age):
    p=r.ease(age,.05,.62)
    r.box(d,(136,350,944,870),58,"#fffaf0","#ead4af",4)
    r.text(d,540,460,"वीडियो क्लास",64,r.INK)
    r.box(d,(222,536,858,672),49,"#ffdc92")
    x=290+round(13*p)
    d.polygon([(x,580),(x,628),(x+38,604)],fill=r.RED)
    r.text(d,590,604,"फ्री डेमो देखें",53,r.RED)
    r.text(d,540,766,"postaledge.in",67,r.INK)

def scene(t,cues,mouths,proof,site,lesson,spoken):
    index=max(1,bisect.bisect_right(cues,t)-1)
    dt=max(0,t-cues[index])
    ending=t>=spoken+.10
    office_id=1 if index<=3 else 0 if index<=5 else 2
    previous=1 if index==4 else 0 if index==6 else office_id
    frame=Image.blend(office(previous),office(office_id),r.ease(dt,0,.36)) if previous!=office_id and dt<.36 else office(office_id).copy()
    d=ImageDraw.Draw(frame)
    place_labels(d,office_id)

    # Keep the real office facade visible above the explainer and the characters in front.
    panel=Image.new("RGBA",(W,980))
    pd=ImageDraw.Draw(panel)
    if ending:
        demo_end(pd,t-spoken)
    elif index==1:
        r.draft(panel,pd,dt,proof)
    elif index<=5:
        r.box(pd,(85,324,995,930),46,r.CREAM,"#e5c799",3)
        r.planning(pd,index,dt)
    else:
        r.show_site(panel,pd,index,dt,site,lesson)
    frame.alpha_composite(panel,(0,200))

    people=Image.new("RGBA",(W,H))
    r.character(people,ImageDraw.Draw(people),t,dt,index,mouths)
    crop=people.crop((0,895,W,1480)).resize((880,477),Image.Resampling.LANCZOS)
    frame.alpha_composite(crop,(100,1107))

    if not ending:
        r.box(d,(90,1563,990,1729),38,r.WHITE,"#e5c799",3)
        r.text(d,540,1603,"गोलू" if index in r.GOLU else "डाकिया भैया",28,r.RED)
        words=r.CAPTIONS[index]
        for i, caption in enumerate(words):
            r.text(d,540,(1663 if len(words)==1 else 1649)+47*i,caption,40)
    return frame

def main():
    source=json.loads((OUT/"original-timing.json").read_text())
    assert source["duration"]==50 and abs(source["continuation_cues"][1]-CUT)<.03
    cues,mouths,spoken=audio(source["continuation_cues"])
    proof=Image.open(ASSETS/"service.png").convert("RGBA").resize((736,115),Image.Resampling.LANCZOS)
    site=Image.open(ASSETS/"website.jpg").convert("RGBA").resize((620,375),Image.Resampling.LANCZOS)
    path=OUT/"lesson"
    path.mkdir(exist_ok=True)
    r.run("ffmpeg","-v","error","-y","-i",str(ASSETS/"lesson.mp4"),"-vf","fps=12,scale=630:-2",str(path/"%03d.jpg"))
    lesson=[Image.open(p).convert("RGBA") for p in sorted(path.glob("*.jpg"))]
    assert lesson
    tail=OUT/"new-tail.mp4"
    with sp.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}",
        "-r",str(FPS),"-i","-","-f","f32le","-ar",str(RATE),"-ac","1","-i",str(OUT/"paced.f32"),
        "-c:v","libx264","-preset","fast","-crf","22","-pix_fmt","yuv420p","-r","30",
        "-c:a","aac","-b:a","128k","-t",str(LENGTH),str(tail)],stdin=sp.PIPE) as pipe:
        for i in range(math.ceil(FPS*LENGTH)):
            pipe.stdin.write(scene(i/FPS,cues,mouths,proof,site,lesson,spoken).convert("RGB").tobytes())
        pipe.stdin.close()
        if pipe.wait():
            raise RuntimeError("Could not render the post-office scenes")
    final=OUT/FILE
    cut=f"{CUT:.9f}"
    r.run("ffmpeg","-v","error","-y","-i",str(PRIOR),"-i",str(tail),"-filter_complex",
       f"[0:v]trim=end={cut},setpts=PTS-STARTPTS,setsar=1[v0];[0:a]atrim=end={cut},asetpts=PTS-STARTPTS[a0];[1:v]setsar=1[v1];[v0][a0][v1][1:a]concat=n=2:v=1:a=1[v][a]",
       "-map","[v]","-map","[a]","-c:v","libx264","-preset","fast","-crf","22","-maxrate","1350k","-bufsize","2700k",
       "-r","30","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k","-t","50","-movflags","+faststart",str(final))
    r.run("ffmpeg","-v","error","-xerror","-i",str(final),"-f","null","-")
    info=json.loads(sp.check_output(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_type,width,height","-of","json",str(final)]))
    assert abs(float(info["format"]["duration"])-50)<.04 and len(info["streams"])==2,info
    details={"preserved_seconds":CUT,"narration_speed":PACE,"demo_card_seconds":round(LENGTH-spoken-.10,2),"media":info}
    print(details,flush=True)
    (OUT/"pace-check.json").write_text(json.dumps(details,indent=2))
    sheet=Image.new("RGB",(864,768))
    for i,t in enumerate([.5,8.3,CUT+1,CUT+cues[4]+1,CUT+cues[5]+1,CUT+cues[7]+1,CUT+cues[8]+1,49.6]):
        data=sp.check_output(["ffmpeg","-v","error","-ss",str(t),"-i",str(final),
           "-vf","scale=216:384","-frames:v","1","-f","image2pipe","-vcodec","mjpeg","-"])
        sheet.paste(Image.open(io.BytesIO(data)),(i%4*216,i//4*384))
    sheet.save(OUT/"checks.jpg",quality=91)

if __name__=="__main__":
    main()
