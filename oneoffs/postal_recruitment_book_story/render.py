"""Smooth recut of the verified two-speaker reel."""
import importlib.util
import io
import json
import math
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

CORE = Path.cwd()
HERE = Path(__file__).resolve().parent
ONEOFFS = HERE.parent
OUT = CORE / "recruitment_preview"
FPS = 30
RATE = 48000
RIG_FPS = 15
FILENAME = "Postal_Edge_GDS_Postman_Book_Story.mp4"
DIALOGUE = [
    ("bhaiya","गोलू, पोस्टमैन की किताब बक्से में क्यों रख दी?"),
    ("golu","तीन साल ही हुए हैं, भैया। दो साल और रुकना है।"),
    ("bhaiya","एक मिनट। ये लाइन पढ़ो।"),
    ("golu","तीन साल?"),
    ("bhaiya","हाँ। पोस्टमैन और मेल गार्ड के लिए पाँच की जगह तीन साल की नियमित जी डी एस सेवा का प्रस्ताव है।"),
    ("golu","फिर पहले एम टी एस बनना पड़ेगा?"),
    ("bhaiya","प्रस्ताव लागू हुआ और बाकी शर्तें पूरी हैं, तो सीधे परीक्षा दे सकोगे।"),
    ("golu","और चयन हो गया तो हाथ में?"),
    ("bhaiya","दिल्ली के उदाहरण में, करीब चवालीस हज़ार रुपये महीने।"),
    ("golu","भैया, किताब वापस देना।"),
    ("bhaiya","पहला टॉपिक साथ में देखते हैं। पोस्टल एज डॉट इन की फ्री डेमो क्लास में पी ओ गाइड के नियम चित्रों और उदाहरणों से समझाए जाते हैं।"),
]
MIN_HOLD = {8: 4.5, 10: 5.6}

def run(*args):
    subprocess.run(args,check=True)

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

def voice(role):
    prior=module("voices",ONEOFFS/"postal_recruitment_two_voices"/"render.py")
    prior.DIALOGUE=DIALOGUE
    prior.voice_parts(role)

def prepare_audio():
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda role: run(sys.executable,__file__,"--voice",role), ("golu","bhaiya")))
    def read(i,factor):
        raw=subprocess.check_output(["ffmpeg","-v","error","-i",str(OUT/f"voice{i}.wav"),
            "-af",f"atempo={factor:.5f},loudnorm=I=-17:TP=-2:LRA=8",
            "-ac","1","-ar",str(RATE),"-f","f32le","-"])
        return np.frombuffer(raw,dtype="<f4")
    def assemble(lines):
        cuts,pieces=[],[]
        n=0
        for i,line in enumerate(lines):
            cuts.append(n/RATE)
            pre=round(RATE*(.20 if i==3 else .09))
            tail=round(RATE*(.36 if i==len(lines)-1 else .11))
            length=max(round(MIN_HOLD.get(i,0)*RATE),len(line)+pre+tail)
            length=math.ceil(length/1600)*1600
            block=np.zeros(length,dtype="<f4")
            block[pre:pre+len(line)]=line
            pieces.append(block)
            n+=length
        return cuts,np.concatenate(pieces)
    cuts,audio=assemble([read(i,1.0) for i in range(len(DIALOGUE))])
    factor=1.0
    while len(audio)/RATE>39.9:
        factor+=.045
        assert factor<=1.32,"Dialogue exceeds the 40-second limit"
        cuts,audio=assemble([read(i,factor) for i in range(len(DIALOGUE))])
    final=OUT/"dialogue.f32"
    final.write_bytes(audio.tobytes())
    return cuts,len(audio)/RATE,final,audio[::3],factor

def build_puppets(samples,duration,cues,roles):
    sys.path.insert(0,str(CORE))
    from postal_edge_lip_shapes import measure_mouth
    from postal_edge_puppet import puppet

    mouths = measure_mouth(samples,RIG_FPS,duration)
    folders = [OUT/"golu",OUT/"bhaiya"]
    for folder in folders:
        folder.mkdir(exist_ok=True)
    gestures=[("open","stop"),("chin","left"),("open","left"),("chin","left"),
              ("chin","open"),("open","welcome"),("chin","open"),("open","welcome"),
              ("chin","open"),("open","left"),("open","right")]
    turn=0
    for i in range(math.ceil(duration*RIG_FPS)):
        t=i/RIG_FPS
        if turn+1 < len(cues) and t>=cues[turn+1]:
            turn+=1
        dt=t-cues[turn]
        for j,folder in enumerate(folders):
            golu=j==0
            active=roles[turn]==("golu" if golu else "bhaiya")
            face=.6 if golu else -.62
            lips=mouths[min(i,len(mouths)-1)] if active else None
            gesture=(.43+.28*math.sin(dt*2.85)**2,gestures[turn][j])
            if turn == 2 and not golu:
                reach = min(1, max(0, dt/.36))
                release = min(1, max(0, (dt-.98)/.48))
                gesture = (.48 + .47*reach*(1-release), "left")
            if golu and turn in (0,1,9):
                beat=min(1,max(0,(dt+.13)/.55))
                gesture=(.46+.48*beat,"open")
            mood="surprise" if golu and turn==3 else ("happy" if not golu or active else "think")
            im=puppet(golu,t,.28*math.exp(-t*3),face,lips,mood,gesture,face,0,.055*math.sin(t*1.65))
            im.save(folder/f"{i:04d}.png")

def class_excerpt():
    """Render the original Mobile Post Offices lesson's illustrated route segment."""
    env = {**os.environ, "LAND": "1"}
    subprocess.run([sys.executable,"deep/premium/build.py","4"],check=True,env=env)
    lesson = CORE/"deep/premium_c4.html"
    output = OUT/"lesson"
    output.mkdir(exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width":960,"height":540})
        page.goto(lesson.as_uri(),wait_until="domcontentloaded")
        page.evaluate("document.fonts.ready")
        page.evaluate("window.READY()")
        start, duration = page.evaluate('[LT("w4") + .4, LD("w4") - .5]')
        assert duration > 3.0
        length = min(4.0,duration)
        total = math.ceil(length*15)
        for i in range(total):
            page.evaluate("t => window.seek(t)",start+i/15)
            page.screenshot(path=str(output/f"{i:03d}.jpg"),type="jpeg",quality=92)
        browser.close()
    return total

def contact(final,cues,duration):
    sheet=Image.new("RGB",(660,1176),"#071222")
    times=[.7,cues[1]+.6,cues[2]+1.1,cues[3]+.3,cues[4]+.7,cues[6]+.55,
           cues[8]+1,cues[9]+.6,duration-1]
    for i,t in enumerate(times):
        raw=subprocess.check_output(["ffmpeg","-v","error","-ss",str(t),"-i",str(final),
                                     "-frames:v","1","-f","image2pipe","-vcodec","png","-"])
        im=Image.open(io.BytesIO(raw))
        if i==0:
            im.save(OUT/"cover.jpg",quality=95)
        sheet.paste(im.resize((220,392)),((i%3)*220,(i//3)*392))
    sheet.save(OUT/"contact.jpg",quality=94)

def main():
    salary=Path(sys.argv[1])
    OUT.mkdir(exist_ok=True)
    spec=importlib.util.spec_from_file_location("sources",ONEOFFS/"postal_recruitment_draft"/"render.py")
    sources=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sources)
    sources.source_cards()
    for index in (0,1,5):
        shutil.copyfile(ONEOFFS/"postal_recruitment_action_cut"/f"location{index}.jpg",OUT/f"location{index}.jpg")
    shutil.copyfile(salary,OUT/"salary.png")
    shutil.copyfile(ONEOFFS/"postal_recruitment_website_outro"/"website-courses.jpg",OUT/"website.jpg")
    lesson_count=class_excerpt()
    cues,duration,audio,samples,tempo=prepare_audio()
    assert 32<duration<=40
    roles=[role for role,_ in DIALOGUE]
    build_puppets(samples,duration,cues,roles)
    html=OUT/"smooth.html"
    html.write_text((HERE/"scenes.html").read_text().replace("__DATA__",json.dumps({
        "cues":cues,"roles":roles,"duration":duration,"lessonFrames":lesson_count})))
    renderer=CORE/"deep/render_deep.py"
    code=renderer.read_text()
    assert "#cutImg,#estImg" in code
    renderer.write_text(code.replace("#cutImg,#estImg","#cutImg,#estImg,#background,#golu,#bhaiya,#lessonClip"))
    silent=OUT/"silent.mp4"
    run(sys.executable,str(renderer),str(html),str(silent))
    final=OUT/FILENAME
    run("ffmpeg","-v","error","-xerror","-y","-i",str(silent),"-f","f32le","-ar",str(RATE),"-ac","1","-i",str(audio),
        "-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","160k","-movflags","+faststart",str(final))
    run("ffmpeg","-v","error","-xerror","-i",str(final),"-f","null","-")
    contact(final,cues,duration)
    (OUT/"report.json").write_text(json.dumps({"seconds":duration,"cues":cues,
       "visual_scene_count":4,"lesson_source":"Original Postal Edge lesson: Clause 4, Mobile Post Offices (illustrated route)","roles":roles,"tempo":tempo,"dialogue":DIALOGUE},indent=2))

if __name__=="__main__":
    if sys.argv[1]=="--voice":
        voice(sys.argv[2])
    else:
        main()
