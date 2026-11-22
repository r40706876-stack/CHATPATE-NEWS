import importlib.util
import json
import math
from pathlib import Path
import subprocess as sp
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import uniform_filter1d

import render_motion as motion

W,H,FPS,RATE=720,1280,24,48000
HOLD=.70
SWITCH=37.0
OUTRO="पोस्टल एज पर चित्रों से पढ़ेंगे। एक पेड़ से एच ओ, एस ओ और बी ओ आसानी से याद हो जाएंगे।"
OUT=Path("transfer-polished-output")
OUT.mkdir(exist_ok=True)
FINAL=OUT/"Postal_Edge_GDS_Transfer_Postman_Draft.mp4"


def voice(script):
    spec=importlib.util.spec_from_file_location("approved_voice",script)
    synth=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(synth)
    synth.OUT=OUT.resolve()
    synth.DIALOGUE=(("golu",OUTRO),)
    key=synth.VOICES["golu"][0]
    assert key=="hi-in-assistant-10",key
    synth.VOICES["golu"]=(key,"Golu, a young male Hindi speaker. Same natural conversational delivery as earlier, now smiling. Read the line word for word, without rushing the final words; end naturally on 'जाएंगे'.")
    synth.voice_parts("golu")
    data=sp.check_output(["ffmpeg","-v","error","-i",str(OUT/"voice0.wav"),"-af",
                          "silenceremove=start_periods=1:start_duration=0.02:start_threshold=-44dB:stop_periods=1:stop_duration=0.44:stop_threshold=-52dB,loudnorm=I=-17:TP=-3:LRA=7",
                          "-ac","1","-ar",str(RATE),"-f","f32le","-"])
    return np.frombuffer(data,dtype="<f4"),key


def add_effects(clean):
    n=len(clean)
    bed=np.zeros(n,dtype=np.float32)
    notes=((55,60,64,67),(53,57,60,64),(57,60,64,69),(55,59,62,67))
    for j in range(math.ceil(n/(RATE*.51))):
        begin=round(j*.51*RATE)
        chord=notes[(j//8)%len(notes)]
        pitch=chord[(0,2,1,3,1,2,3,2)[j%8]]
        t=np.arange(min(n-begin,round(1.05*RATE)),dtype=np.float32)/RATE
        if not len(t):
            continue
        f=440*2**((pitch-69)/12)
        env=np.minimum(1,t/.035)*np.exp(-4.7*t)
        bed[begin:begin+len(t)]+=.024*env*(np.sin(2*np.pi*f*t)+.22*np.sin(4*np.pi*f*t))
    # Quiet chord texture, gently tucked under speech.
    peak=uniform_filter1d(np.abs(clean),size=9601)
    gain=1-.54*np.clip(peak/.078,0,1)
    bed*=gain
    bed[:RATE]=bed[:RATE]*np.linspace(0,1,RATE)
    length=round(1.05*RATE)
    bed[-length:]*=np.linspace(1,0,length)**1.6
    effects=np.zeros(n,dtype=np.float32)
    rng=np.random.default_rng(98)
    pops=(5.5,11.93,15.55,22.45,26.13,29.12,34.33,37.22,39.75,40.6)
    for when in pops:
        start=round(when*RATE)
        t=np.arange(round(.115*RATE))/RATE
        # A soft, descending mallet tap without a sharp transient.
        body=np.sin(2*np.pi*(610*t-1450*t*t)) * np.exp(-39*t)*np.minimum(1,t/.007)
        effects[start:start+len(t)]+=.035*body
    for when in (2.55,8.3,19.03,28.5,37.0):
        start=round(when*RATE)
        t=np.arange(round(.16*RATE))/RATE
        z=rng.normal(0,1,len(t))
        filtered=uniform_filter1d(z,size=17)-uniform_filter1d(z,size=68)
        effects[start:start+len(t)]+=.039*filtered*np.sin(np.pi*t/.16)**2
    print(json.dumps({"music_rms":float(np.sqrt(np.mean(bed**2))),"sfx_peak":float(np.max(np.abs(effects)))},ensure_ascii=False),flush=True)
    return np.clip(clean+bed+effects,-.98,.98).astype("<f4")


def render(previous,reference,assets,demo_path):
    end,key=voice(reference)
    assert 3*RATE < len(end) < 8*RATE, len(end)
    preserved=motion.read_audio(previous)[:round(SWITCH*RATE)]
    end_track=np.concatenate((np.zeros(round(.04*RATE),dtype=np.float32),end,np.zeros(round(HOLD*RATE),dtype=np.float32)))
    samples=np.concatenate((preserved,end_track))
    spf=RATE//FPS
    signal=np.pad(samples,(0,(-len(samples))%spf))
    duration=len(signal)/RATE
    add_effects(signal).tofile(OUT/"polish.f32")
    mouths=motion.art.art.measure_mouth(signal[::3],FPS,duration)
    report={"duration":duration,"line":OUTRO,"ending_dialogue_seconds":round(len(end)/RATE,3),
            "dialogue_hold_seconds":round(duration-SWITCH-.04-len(end)/RATE,3),"voice":key,
            "retained_dialogue_until":SWITCH}
    (OUT/"review.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False),flush=True)

    motion.BACKS={"office":motion.bg_photo(assets/"office1.jpg","#F3E6C9"),"board":motion.board()}
    motion.DESK=motion.art.art.counter()
    demo=sp.check_output(["ffmpeg","-v","error","-ss","36.65","-i",str(demo_path),"-an","-vf",
                          f"crop=618:488:51:221,fps={FPS}","-pix_fmt","rgb24","-f","rawvideo","-"])
    bs=618*488*3
    tree=[Image.frombytes("RGB",(618,488),demo[i:i+bs]).convert("RGBA") for i in range(0,len(demo),bs)]
    assert len(tree)>60,len(tree)
    src_actor=motion.actor

    def expressive(im,golu,t,mouth,x,y,w,mood="think",gesture="open",strength=.73,walking=0.,facing=None):
        if golu and t < 5.5:
            push=motion.ease((t-.07)/.65)*(1-.29*motion.ease((t-1.28)/.68)) if t<2.55 else .65+.35*motion.ease((t-2.55)/.78)
            width=round(w*(1+.073*push))
            x-=(width-w)/2
            y-=round(22*push)
            w=width
            mood="think" if t<.55 else "surprise"
            strength=.43+.4*motion.ease((t-.39)/.5)
        if golu and t >= SWITCH:
            smile=motion.ease((t-SWITCH)/.47)
            width=round(w*(1+.105*smile))
            x-=(width-w)/2
            y-=round(12*smile)
            w=width
            mood="think" if t<SWITCH+.22 else "happy"
            gesture="hop" if t>duration-.72 else "open"
            strength=.50+.40*smile
        return src_actor(im,golu,t,mouth,x,y,w,mood,gesture,strength,walking,facing)

    motion.actor=expressive
    begin=round(5.5*FPS)
    cut=round(SWITCH*FPS)
    nframes=len(signal)//spf
    decoder=["ffmpeg","-v","error","-ss","5.5","-i",str(previous),"-an","-frames:v",str(cut-begin),
             "-pix_fmt","rgb24","-f","rawvideo","-"]
    encoder=["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-framerate",str(FPS),"-i","-",
             "-f","f32le","-ar",str(RATE),"-ac","1","-i",str(OUT/"polish.f32"),"-c:v","libx264","-preset","veryfast",
             "-crf","17","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart",str(FINAL)]
    inspect={13,84,cut+48,nframes-8}
    frame_bytes=W*H*3
    with sp.Popen(decoder,stdout=sp.PIPE) as src,sp.Popen(encoder,stdin=sp.PIPE) as dst:
        for n in range(nframes):
            if begin<=n<cut:
                data=src.stdout.read(frame_bytes)
                if len(data)!=frame_bytes:
                    raise RuntimeError(f"Unexpected end of source frame at {n}")
            else:
                picture=motion.frame(n/FPS,mouths[n],None,tree)
                if n in inspect:
                    picture.resize((360,640),Image.Resampling.LANCZOS).save(OUT/f"qc-{n}.jpg",quality=92)
                data=picture.tobytes()
            dst.stdin.write(data)
        dst.stdin.close()
        if src.wait() or dst.wait():
            raise RuntimeError("Video encoding failed")
    sp.run(["ffmpeg","-v","error","-xerror","-i",str(FINAL),"-f","null","-"],check=True)


if __name__=="__main__":
    render(*map(Path,sys.argv[1:5]))
