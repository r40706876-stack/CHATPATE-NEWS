import importlib.util
import json
import math
from pathlib import Path
import subprocess as sp
import sys

import numpy as np
from PIL import Image

import render_motion as motion
import render_polish as polish

FPS=24
RATE=48000
W,H=720,1280
OUT=Path("transfer-golu-output")
OUT.mkdir(exist_ok=True)
FINAL=OUT/"Postal_Edge_GDS_Transfer_Postman_Draft.mp4"

# The existing cut on a 24 fps timeline. Only Golu is recorded again.
LINES=(
    (0,132,"भैया, ट्रांसफर लेकर फँस गया! नए पोस्टमैन ड्राफ्ट में पुरानी सर्विस बेकार हो गई क्या?"),
    (132,275,"दो साल एम पी में हुए, एक साल हरियाणा में। सब बोल रहे हैं, तीनों साल एक ही डिवीजन में चाहिए!"),
    (628,684,"और ये तीन साल कब तक पूरे होने चाहिए?"),
    (824,888,"अभी ये ड्राफ्ट है। भर्ती का नोटिस ज़रूर देखना।"),
    (888,1057,polish.OUTRO),
)


def record(script):
    spec=importlib.util.spec_from_file_location("original_reel_voices",script)
    voices=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(voices)
    voice_id,direction=voices.VOICES["golu"]
    assert voice_id=="hi-in-assistant-10" and "Quick, playful, clear" in direction
    voices.OUT=OUT.resolve()
    voices.DIALOGUE=tuple(("golu",line) for _,_,line in LINES)
    # Use the historical Postal Edge voice definition verbatim.
    voices.voice_parts("golu")
    return voice_id,direction


def get_wave(index,window):
    p=OUT/f"voice{index}.wav"
    clean="silenceremove=start_periods=1:start_duration=0.020:start_threshold=-44dB:stop_periods=1:stop_duration=0.48:stop_threshold=-52dB,loudnorm=I=-17:TP=-3:LRA=7"
    base=["ffmpeg","-v","error","-i",str(p),"-af"]
    tail=["-ac","1","-ar",str(RATE),"-f","f32le","-"]
    take=np.frombuffer(sp.check_output(base+[clean]+tail),dtype="<f4")
    tempo=max(1,len(take)/(RATE*window))
    if tempo>1:
        data=sp.check_output(["ffmpeg","-v","error","-f","f32le","-ar",str(RATE),"-ac","1","-i","-",
                              "-af",f"atempo={tempo+.015:.5f}","-f","f32le","-"],input=take.tobytes())
        take=np.frombuffer(data,dtype="<f4")
    assert len(take)/RATE<=window+.04, (index,len(take)/RATE,window)
    return take,tempo


def soundtrack(previous,voice_script):
    voice,direction=record(voice_script)
    old=motion.read_audio(previous)
    nframes=LINES[-1][1]
    per_frame=RATE//FPS
    clean=np.zeros(nframes*per_frame,dtype=np.float32)
    clean[:min(len(old),len(clean))]=old[:len(clean)]
    records=[]
    for index,(beg,end,words) in enumerate(LINES):
        start=beg*per_frame
        stop=end*per_frame
        hold=.66 if index==4 else .12
        gap=.045
        limit=(end-beg)/FPS-gap-hold
        take,tempo=get_wave(index,limit)
        cue=start+round(gap*RATE)
        clean[start:stop]=0
        clean[cue:cue+len(take)]=take
        records.append({"seconds":round(len(take)/RATE,3),"tempo":round(tempo,3),"line":words})
    polish.add_effects(clean).tofile(OUT/"audio.f32")
    report={"duration":nframes/FPS,"golu_voice":voice,"historical_instruction":direction,"golu_lines":records,
            "end_hold":round((LINES[-1][1]-LINES[-1][0])/FPS-.045-records[-1]["seconds"],3)}
    (OUT/"check.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False),flush=True)
    return motion.art.art.measure_mouth(clean[::3],FPS,nframes/FPS)


def actors():
    original=motion.actor
    def redraw(im,golu,t,mouth,x,y,w,mood="think",gesture="open",strength=.73,walking=0.,facing=None):
        if golu and t<5.5:
            zoom=motion.ease((t-.08)/.64) if t<2.55 else .65+.35*motion.ease((t-2.55)/.78)
            new_w=round(w*(1+.073*zoom))
            x-=(new_w-w)/2
            y-=round(22*zoom)
            w=new_w
            mood="think" if t<.55 else "surprise"
            strength=.43+.4*motion.ease((t-.39)/.5)
        elif golu and t>=37:
            smile=motion.ease((t-37)/.47)
            new_w=round(w*(1+.105*smile))
            x-=(new_w-w)/2
            y-=round(12*smile)
            w=new_w
            mood="think" if t<37.22 else "happy"
            gesture="hop" if t>43.32 else "open"
            strength=.50+.40*smile
        return original(im,golu,t,mouth,x,y,w,mood,gesture,strength,walking,facing)
    motion.actor=redraw


def main(previous,original_dialogue,script,assets,demo):
    mouths=soundtrack(original_dialogue,script)
    motion.BACKS={"board":motion.board(),"office":motion.bg_photo(assets/"office1.jpg","#F3E6C9"),
                  "outside":motion.bg_photo(assets/"office0.jpg","#E9EBD9"),"side":motion.bg_photo(assets/"office2.jpg","#EFE6CD")}
    motion.DESK=motion.art.art.counter()
    actors()
    data=sp.check_output(["ffmpeg","-v","error","-ss","36.65","-i",str(demo),"-an","-vf",f"crop=618:488:51:221,fps={FPS}",
                          "-pix_fmt","rgb24","-f","rawvideo","-"])
    bw=618*488*3
    tree=[Image.frombytes("RGB",(618,488),data[i:i+bw]).convert("RGBA") for i in range(0,len(data),bw)]
    nframes=LINES[-1][1]
    decoder=["ffmpeg","-v","error","-i",str(previous),"-an","-frames:v",str(nframes),"-pix_fmt","rgb24","-f","rawvideo","-"]
    encoder=["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-framerate",str(FPS),"-i","-",
             "-f","f32le","-ar",str(RATE),"-ac","1","-i",str(OUT/"audio.f32"),"-c:v","libx264","-preset","veryfast","-crf","17",
             "-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart",str(FINAL)]
    with sp.Popen(decoder,stdout=sp.PIPE) as src,sp.Popen(encoder,stdin=sp.PIPE) as dst:
        for n in range(nframes):
            current=src.stdout.read(W*H*3)
            if len(current)!=W*H*3:
                raise RuntimeError(f"Unexpected end of source at frame {n}")
            if any(start<=n<end for start,end,_ in LINES):
                t=n/FPS
                im=motion.frame(t,mouths[n],None,tree)
                if 132<=n<275:
                    words="ट्रांसफर से पहले और बाद" if t<8.3 else "तीनों साल एक डिवीजन में?"
                    motion.rect(im,(48,896,672,1016),motion.CREAM,16,"#B5CDB2",2)
                    motion.text(im,360,954,words,35,motion.INK)
                if n in (18,83,155,251,665,860,925,1047):
                    im.resize((360,640),Image.Resampling.LANCZOS).save(OUT/f"qc-{n:04d}.jpg",quality=92)
                current=im.tobytes()
            dst.stdin.write(current)
        dst.stdin.close()
        if src.wait() or dst.wait():
            raise RuntimeError("Video encoding failed")
    sp.run(["ffmpeg","-v","error","-xerror","-i",str(FINAL),"-f","null","-"],check=True)


if __name__=="__main__":
    main(*map(Path,sys.argv[1:6]))
