"""Add the draft arithmetic and Golu's spoken CTA to the approved reel."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import importlib.util
import json
import math
import subprocess as sp
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("seat_reel", HERE / "render.py")
reel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reel)
art, OUT = reel.art, reel.OUT
W, H, FPS, RATE = reel.W, reel.H, reel.FPS, reel.RATE
SOURCE = Path(sys.argv[2]).resolve() if len(sys.argv) == 3 else None
NAME = "Postal_Edge_Postman_50_50_Final.mp4"
LINES = [
    ("bhaiya", "मान लो पूरे पैंतालीस हज़ार आठ सौ निन्यानवे पद खाली होते। आधा हिस्सा करीब बाईस हज़ार नौ सौ पचास होता। यह सिर्फ हिसाब है।", "45,899 का आधा  |  करीब 22,950"),
    ("bhaiya", "देश में तेईस पोस्टल सर्किल हैं। जी डी एस का प्रस्तावित हिस्सा, असल खाली सीटों का आधा है। इसलिए तैयारी पर ध्यान दो।", "असल खाली सीटें  |  GDS का प्रस्तावित हिस्सा 50%"),
    ("golu", "दोस्तों, इसे सेव करके अपने साथी को भेजो।", "सेव करें  |  साथी को भेजें"),
]
reel.LINES = LINES
reel.voices.OUT = OUT
reel.voices.DIALOGUE = [(who, speech) for who, speech, _ in LINES]

def run(*args):
    sp.run(args, check=True)

def take_audio():
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda role: run(sys.executable, __file__, role),reel.voices.VOICES))
    clips=[]
    for i,(who,_,_) in enumerate(LINES):
        fx=("silenceremove=start_periods=1:start_duration=0.025:start_threshold=-45dB:"
            "stop_periods=1:stop_duration=0.25:stop_threshold=-45dB,"
            "loudnorm=I=-16:TP=-2:LRA=7")
        pcm=sp.check_output(["ffmpeg","-v","error","-i",str(OUT/f"voice{i}.wav"),
              "-af",fx,"-ar",str(RATE),"-ac","1","-f","f32le","-"])
        signal=np.frombuffer(pcm,dtype="<f4")
        active=np.flatnonzero(np.abs(signal)>.006)
        assert active.size, who
        signal=signal[:min(len(signal),active[-1]+round(.09*RATE))]
        frames=math.ceil((len(signal)+.25*RATE)*FPS/RATE)
        assert 1.0 < frames/FPS < 15, (i,frames)
        signal=np.pad(signal,(round(.06*RATE),frames*RATE//FPS-len(signal)-round(.06*RATE)))
        pad_path=OUT/f"math-{i}.f32"
        pad_path.write_bytes(signal.astype("<f4").tobytes())
        mouths=reel.measure_mouth(signal[::3],FPS,frames/FPS)
        clips.append((frames,pad_path,mouths))
    return clips

def numbers(im,t):
    art.txt(im,(62,225),"POSTMAN  |  GDS",33,art.gold,anchor="lm")
    art.rr(im,(53,280,667,695),22,"#142a34","#426470",2)
    art.txt(im,(360,327),"अगर सभी पद खाली हों",33,art.white,True)
    art.txt(im,(360,426),"45,899 × 50%",65,art.gold)
    art.txt(im,(360,522),"≈ 22,950",87,art.aqua)
    art.rr(im,(77,610,643,664),10,"#233b45")
    art.txt(im,(360,639),"सिर्फ गणना  |  घोषित वैकेंसी नहीं",25,art.white,True)

def circles(im,t):
    art.txt(im,(61,225),"देशभर की तस्वीर",37,art.gold,True,anchor="lm")
    art.rr(im,(53,280,667,695),22,"#142a34","#426470",2)
    art.txt(im,(360,394),"23",115,art.gold)
    art.txt(im,(360,455),"पोस्टल सर्किल",35,art.white,True)
    art.txt(im,(360,539),"खाली सीटों का 50% GDS के लिए",31,art.aqua,True)
    art.txt(im,(360,604),"सर्किलवार सीटें नोटिफिकेशन में",25,art.white,True)
    art.txt(im,(360,654),"तैयारी आज से शुरू करें",24,art.gold,True)

def cta(im,t):
    art.rr(im,(53,265,667,662),23,"#142a34","#426470",2)
    art.txt(im,(360,338),"POSTAL EDGE",23,art.gold)
    art.txt(im,(360,437),"इसे सेव करें",60,art.white,True)
    art.txt(im,(360,529),"साथी को भेजें",53,art.aqua,True)
    art.txt(im,(360,605),"postaledge.in",26,art.gold)

def render_scene(index, data):
    frame_count, audio, mouths=data
    target=OUT/f"math-{index}.mp4"
    with sp.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}",
       "-r",str(FPS),"-i","-","-f","f32le","-ar",str(RATE),"-ac","1","-i",str(audio),
       "-c:v","libx264","-preset","fast","-crf","18","-pix_fmt","yuv420p","-c:a","aac",
       "-b:a","160k","-t",str(frame_count/FPS),str(target)],stdin=sp.PIPE) as ff:
        for frame in range(frame_count):
            t=frame/FPS
            im=art.base.copy()
            art.masthead(im,True)
            [numbers,circles,cta][index](im,t)
            reel.actors(im,t,index,mouths[min(frame,len(mouths)-1)])
            reel.art_caption(im,index)
            ff.stdin.write(im.convert("RGB").tobytes())
        ff.stdin.close()
        assert ff.wait()==0
    return target

def splice(opening,insert_one,insert_two,end_card):
    filters=(
        "[0:v]trim=end=24.625,setpts=PTS-STARTPTS[before];"
        "[0:a]atrim=end=24.625,asetpts=PTS-STARTPTS[beforeaudio];"
        "[0:v]trim=start=33.833333:end=41.95,setpts=PTS-STARTPTS[d];"
        "[0:a]atrim=start=33.833333:end=41.95,asetpts=PTS-STARTPTS[da];"
        "[0:v]trim=start=33.833333:end=41.95,crop=618:488:51:221,setpts=(PTS-STARTPTS)/1.55[t];"
        "[d][t]overlay=x=51:y=221:eof_action=repeat:repeatlast=1[demo];"
        "[before][beforeaudio][1:v][1:a][2:v][2:a][demo][da][3:v][3:a]concat=n=5:v=1:a=1[v][a]"
    )
    target=OUT/NAME
    run("ffmpeg","-v","error","-y","-filter_complex_threads","2","-i",str(opening),"-i",str(insert_one),
       "-i",str(insert_two),"-i",str(end_card),"-filter_complex",filters,"-map","[v]","-map","[a]",
       "-c:v","libx264","-preset","fast","-crf","18","-r","24","-pix_fmt","yuv420p",
       "-c:a","aac","-b:a","160k","-movflags","+faststart",str(target))
    run("ffmpeg","-v","error","-i",str(target),"-f","null","-")
    return target

def main():
    OUT.mkdir(exist_ok=True)
    clips=take_audio()
    scenes=[render_scene(i,d) for i,d in enumerate(clips)]
    output=splice(SOURCE,*scenes)
    lengths=[data[0]/FPS for data in clips]
    demo=24.625+sum(lengths[:2])
    check=[25,24.625+lengths[0]+.9,demo+5.5,demo+8.35]
    for i,t in enumerate(check):
        run("ffmpeg","-v","error","-y","-ss",str(t),"-i",str(output),"-frames:v","1",
            "-vf","scale=360:640",str(OUT/f"final-review-{i}.jpg"))
    (OUT/"final-check.json").write_text(json.dumps({"opens_math_at":24.625,"new_dialogue_seconds":lengths,
        "demo_starts_at":demo,"voice_roles":[line[0] for line in LINES]},indent=2))

if len(sys.argv)==2:
    reel.voices.voice_parts(sys.argv[1])
else:
    main()
