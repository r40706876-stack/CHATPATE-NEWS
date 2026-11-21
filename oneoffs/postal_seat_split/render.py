from bisect import bisect_right
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import importlib.util
import json
import math
from pathlib import Path
import subprocess as sp
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
import hook as art

HERE = Path(__file__).resolve().parent
CORE = Path.cwd()
sys.path.insert(0, str(CORE))

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

voices = load("voices", HERE.parent / "postal_recruitment_two_voices" / "render.py")
from postal_edge_puppet import puppet
from postal_edge_lip_shapes import measure_mouth

OUT = CORE / "reel-work"
ASSETS = OUT / "assets"
W, H, RATE, FPS, LENGTH = 720, 1280, 48000, 24, 50
STARTS = (0, 1.82, 3, 9, 15, 22, 28, 31.65, 33.5, 40, 42.25)
LINES = [
    ("golu", "सारे पद जी डी एस के?", "सारे पद GDS के?"),
    ("bhaiya", "ये देखो।", "ये देखो"),
    ("bhaiya", "ड्राफ्ट में पैंतालीस हज़ार आठ सौ निन्यानवे पोस्टमैन और एक हज़ार आठ सौ सत्तर मेल गार्ड के पद दर्ज हैं।", "45,899 Postman  |  1,870 Mail Guard"),
    ("bhaiya", "ये कुल पद हैं। भर्ती में कितनी सीटें निकलेंगी, वो नोटिफिकेशन में पता चलेगा।", "ये ड्राफ्ट में दर्ज कुल पद हैं"),
    ("bhaiya", "लेकिन सबसे चौंकाने वाली बात ये है कि पोस्टमैन की आधी भर्ती एम टी एस के विभागीय एग्जाम से,", "50%  |  MTS का विभागीय एग्जाम"),
    ("bhaiya", "और आधी जी डी एस के एग्जाम से करने का प्रस्ताव है। मेल गार्ड में भी यही बँटवारा है।", "50%  |  GDS का एग्जाम"),
    ("bhaiya", "अभी ये ड्राफ्ट है। बहुत से साथी फाइनल नियमों का इंतज़ार करेंगे।", "अभी ये प्रस्ताव है"),
    ("golu", "तो पढ़ाई कब से?", "तो पढ़ाई कब से?"),
    ("bhaiya", "आज से। जब वो शुरू करेंगे, तुम अपना पहला रिविज़न कर रहे होगे।", "तैयारी आज से शुरू करो"),
    ("bhaiya", "और सुनो, किसी को मत बताना।", "किसी को मत बताना…"),
    ("bhaiya", "पोस्टल एज पर मुश्किल टॉपिक भी चित्रों से, बिल्कुल शुरुआत से, आसान भाषा में समझाए हैं।", "चित्रों से समझो  |  आसान भाषा में"),
]
voices.OUT = OUT
voices.DIALOGUE = [(role, line) for role, line, _ in LINES]

def execute(*args):
    sp.run(args, check=True)

def voice_audio():
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda role: execute(sys.executable, __file__, role), voices.VOICES))
    dry = np.zeros(RATE*LENGTH, dtype="float32")
    cuts = []
    for i, start in enumerate(STARTS):
        cap = (STARTS[i+1] if i+1<len(STARTS) else LENGTH)-start-.17
        audio = sp.check_output(["ffmpeg","-v","error","-i",str(OUT/f"voice{i}.wav"),
            "-af","silenceremove=start_periods=1:start_duration=0.025:start_threshold=-45dB,loudnorm=I=-16:TP=-2:LRA=7",
            "-ac","1","-ar",str(RATE),"-f","f32le","-"])
        samples = np.frombuffer(audio,dtype="<f4")
        speed = max(1., len(samples)/(RATE*cap)*1.025)
        if speed>1:
            stages = ["atempo=2"] if speed>2 else []
            stages.append(f"atempo={speed/(2 if stages else 1):.5f}")
            data = sp.check_output(["ffmpeg","-v","error","-f","f32le","-ar",str(RATE),"-ac","1","-i","-",
                                   "-af",",".join(stages),"-f","f32le","-"],input=samples.tobytes())
            samples = np.frombuffer(data,dtype="<f4")
        assert 0.38 < len(samples)/RATE <= cap+.06, (i,len(samples)/RATE,cap)
        offset = round((start+.08)*RATE)
        dry[offset:offset+len(samples)] = samples
        cuts.append({"scene":i,"start":start,"speech_seconds":round(len(samples)/RATE,2),"tempo":round(speed,2)})
    mix = dry.copy()
    for moment, power, hz in [(0.02,.21,115),(1.83,.14,165),(2.92,.14,230),(15.1,.065,272),(22.1,.065,354),(39.9,.05,425)]:
        ticks = np.arange(round(.21*RATE))/RATE
        k = round(moment*RATE)
        mix[k:k+len(ticks)] += power*np.sin(2*np.pi*hz*ticks)*np.exp(-28*ticks)
    (OUT/"seat-audio.f32").write_bytes(np.clip(mix,-.96,.96).astype("<f4").tobytes())
    return measure_mouth(dry[::3], FPS, LENGTH), cuts

def art_caption(im, i):
    art.rr(im,(50,993,670,1065),13,"#122530","#4d6269",2)
    art.txt(im,(360,1031),LINES[i][2],34 if i==0 else 28,art.white,True)

def actors(im,t,i,mouth,is_hook=False):
    for golu,x in ((True,69),(False,469)):
        active = ("golu" if golu else "bhaiya")==LINES[i][0]
        action = "open" if active else "chin"
        face = .53 if golu else -.58
        strength = .27+.45*math.sin(t*3.25)**2
        person = puppet(golu,t,.03,face,mouth if active else None,"surprise" if i==0 and golu else "happy",
                        (strength,action),face,0,.05)
        w,h = (196,300) if is_hook else (190,291)
        y = (657 if is_hook else 690)-round(8*(1+math.sin(t*2.7)) if active else 0)
        im.alpha_composite(person.resize((w,h),Image.Resampling.LANCZOS),(x,y))

def hook(im,t):
    pull=69*art.ease((t-.36)/1.1)-16*art.ease((t-1.8)/.34)
    art.lay(im,art.mts_tray.resize((245,185)),(179,672),4)
    art.lay(im,art.gds_tray.resize((245,185)),(538,672),-4)
    art.lay(im,art.envelope.resize((465,372)),(351+pull,423),4-10*art.ease(t/1.6),True)
    if t>.48:
        art.lay(im,art.golu.resize((223,112)),(760-185*art.ease((t-.48)/.4),473),183,True)
    if t>1.62:
        art.lay(im,art.dakia.resize((223,112)),(-120+310*art.ease((t-1.62)/.42),440),-8,True)
    if t>2.72:
        p=art.ease((t-2.72)/.28)
        size=(round(110+485*p),round(156+688*p))
        art.lay(im,PAGES[0].resize(size),(365,429),-13*(1-p),True)

PAGES = [art.draft, Image.open(HERE/"page7.jpg").convert("RGBA")]
page_spans = ((81,172),(42,132))
def evidence(p):
    y1,y2=page_spans[p]
    pic=PAGES[p].crop(tuple(round(n*art.scale) for n in (95,y1,252,y2+64)))
    return pic.resize((308,round(pic.height*308/pic.width)),Image.Resampling.LANCZOS)

PROOFS=[evidence(i) for i in range(2)]
def numbers(im,t,i):
    for y,word,count,shade in ((242,"POSTMAN","45,899",art.gold),(445,"MAIL GUARD","1,870",art.aqua)):
        art.rr(im,(60,y,660,y+175),17,"#122630","#435b67",2)
        art.txt(im,(91,y+43),word,24,shade,anchor="lm")
        art.txt(im,(92,y+113),count,70,art.white,anchor="lm")
    art.txt(im,(360,656),"भर्ती की सीटें नोटिफिकेशन में",27,art.slate,True)

def split(im,t,i):
    page=int(t>=25.3)
    art.txt(im,(61,230),"MAIL GUARD" if page else "POSTMAN",40,art.white,anchor="lm")
    art.txt(im,(63,287),"पेज 7  |  कॉलम 10" if page else "पेज 5  |  कॉलम 10",22,art.aqua,True,anchor="lm")
    art.rr(im,(58,335,662,678),14,"#152934","#435b67",2)
    take=PROOFS[page]
    im.alpha_composite(take,(334,365))
    for j,(y,label,color) in enumerate([(392,"MTS",art.gold),(542,"GDS",art.aqua)]):
        focused=(i==4 and j==0) or (i==5)
        art.txt(im,(78,y),"50%",64,color if focused else art.slate,anchor="lm")
        art.txt(im,(85,y+55),label,27,art.white,anchor="lm")
        if focused:
            oy=(365 if j==0 else 542)
            sheet=Image.new("RGBA",im.size)
            art.rr(sheet,(336,oy,635,oy+24),4,(255,197,76,73))
            im.alpha_composite(sheet)

def plan(im,t,i):
    art.rr(im,(58,278,662,634),20,"#172e39","#53707a",2)
    art.txt(im,(360,352),"अभी ये ड्राफ्ट है",44,art.gold,True)
    art.txt(im,(360,461),"तैयारी",68,art.white,True)
    art.txt(im,(360,551),"आज से शुरू करो",46,art.aqua,True)

@lru_cache(maxsize=20)
def lesson(index):
    return Image.open(LESSON[index]).convert("RGBA")

def study(im,t):
    art.rr(im,(49,248,671,698),19,"#152a35","#486471",2)
    art.txt(im,(77,295),"फ्री क्लास की झलक",29,art.aqua,True,anchor="lm")
    pic=lesson(min(len(LESSON)-1,round((t-40)*8)))
    im.alpha_composite(pic,((W-pic.width)//2,332))

@lru_cache(maxsize=2)
def location(background):
    if background == "counter":
        scene = ImageOps.fit(Image.open(ASSETS/"background1.jpg").convert("RGBA"),(W,H))
        scene = scene.filter(ImageFilter.GaussianBlur(3))
        return Image.blend(scene,art.base,.69)
    scene = Image.new("RGBA",(W,H),"#132c39")
    return Image.blend(scene,art.base,.46)

def main():
    OUT.mkdir(exist_ok=True)
    mouths,cuts=voice_audio()
    lesson_dir=OUT/"seats-lesson"
    lesson_dir.mkdir(exist_ok=True)
    execute("ffmpeg","-v","error","-y","-i",str(ASSETS/"lesson.mp4"),"-t","10",
        "-vf","fps=8,scale=565:315:force_original_aspect_ratio=decrease",str(lesson_dir/"%03d.jpg"))
    LESSON.extend(sorted(lesson_dir.glob("*.jpg")))
    assert LESSON
    target=OUT/"Postal_Edge_Postman_50_50_Full_Reel.mp4"
    previews=[]
    with sp.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}",
        "-r",str(FPS),"-i","-","-f","f32le","-ar",str(RATE),"-ac","1","-i",str(OUT/"seat-audio.f32"),
        "-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","160k","-movflags","+faststart","-t",str(LENGTH),str(target)],stdin=sp.PIPE) as ff:
        for n in range(FPS*LENGTH):
            t=n/FPS
            i=bisect_right(STARTS,t)-1
            if 6 <= i <= 8:
                im=location("counter").copy()
            elif i>=9:
                im=location("lesson").copy()
            else:
                im=art.base.copy()
            art.masthead(im,i>=3)
            if i<=1:
                hook(im,t)
            elif i<=3:
                numbers(im,t,i)
            elif i<=5:
                split(im,t,i)
            elif i<=8:
                plan(im,t,i)
            else:
                study(im,t)
            actors(im,t,i,mouths[min(n,len(mouths)-1)],i<=1)
            art_caption(im,i)
            result=im.convert("RGB")
            if n in {0,42,120,385,570,625,768,860,1043,1190}:
                previews.append(result.resize((240,426)))
            ff.stdin.write(result.tobytes())
        ff.stdin.close()
        assert ff.wait()==0
    grid=Image.new("RGB",(5*240,2*426))
    for j,preview in enumerate(previews):
        grid.paste(preview,(j%5*240,j//5*426))
    grid.save(OUT/"seat-review.jpg",quality=91)
    (OUT/"seat-check.json").write_text(json.dumps({"seconds":50,"voices":{k:v[0] for k,v in voices.VOICES.items()},
        "cuts":cuts,"frames":FPS*LENGTH},indent=2))
    execute("ffmpeg","-v","error","-i",str(target),"-f","null","-")
    print("Verified render",target.name,flush=True)

LESSON=[]
if __name__=="__main__":
    if len(sys.argv)>1:
        voices.voice_parts(sys.argv[1])
    else:
        main()
