"""Smooth recut of the verified two-speaker reel."""
import importlib.util
import io
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

CORE = Path.cwd()
HERE = Path(__file__).resolve().parent
ONEOFFS = HERE.parent
OUT = CORE / "recruitment_preview"
FPS = 30
RATE = 48000
RIG_FPS = 15
FILENAME = "Postal_Edge_GDS_Postman_Smooth_Cut.mp4"
TRIMS = [(224,231), (547,556), (684,765)]

def run(*args):
    subprocess.run(args, check=True)

def prepare_audio(original, report):
    raw = subprocess.check_output(["ffmpeg","-v","error","-i",str(original),"-ac","1",
                                  "-ar",str(RATE),"-f","f32le","-"])
    frame_size = RATE // FPS
    length = round(float(report["seconds"])*FPS)
    full = np.frombuffer(raw,dtype="<f4")[:length*frame_size]
    assert len(full) == length*frame_size
    keep = list(zip([0]+[b for _,b in TRIMS], [a for a,_ in TRIMS]+[length]))
    parts = []
    fade = np.linspace(0,1,240,dtype=np.float32)
    for i,(start,end) in enumerate(keep):
        block = full[start*frame_size:end*frame_size].copy()
        if i:
            block[:len(fade)] *= fade
        if i<len(keep)-1:
            block[-len(fade):] *= fade[::-1]
        parts.append(block)
    audio = np.concatenate(parts)
    path = OUT / "dialogue.f32"
    path.write_bytes(audio.tobytes())
    def map_frame(frame):
        return frame - sum(max(0,min(b,frame)-a) for a,b in TRIMS)
    cues = [map_frame(round(t*FPS))/FPS for t in report["shots"]]
    return cues,len(audio)/RATE,path,audio[::3]

def build_puppets(samples,duration,cues,roles):
    sys.path.insert(0,str(CORE))
    from postal_edge_lip_shapes import measure_mouth
    from postal_edge_puppet import puppet

    mouths = measure_mouth(samples,RIG_FPS,duration)
    folders = [OUT/"golu",OUT/"bhaiya"]
    for folder in folders:
        folder.mkdir(exist_ok=True)
    gestures=[("open","welcome"),("chin","right"),("open","left"),("chin","open"),
              ("open","welcome"),("chin","open"),("right","welcome"),("open","right")]
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
            mood="happy" if not golu or active else "think"
            im=puppet(golu,t,.28*math.exp(-t*3),face,lips,mood,gesture,face,0,.055*math.sin(t*1.65))
            im.save(folder/f"{i:04d}.png")

def contact(final,cues,duration):
    sheet=Image.new("RGB",(660,1176),"#071222")
    for i,t in enumerate([.75,cues[1]+1,cues[2]+.55,cues[3]+.7,cues[4]+.6,cues[5]+1,
                          cues[5]+3.5,cues[6]+.6,duration-1]):
        raw=subprocess.check_output(["ffmpeg","-v","error","-ss",str(t),"-i",str(final),
                                     "-frames:v","1","-f","image2pipe","-vcodec","png","-"])
        im=Image.open(io.BytesIO(raw))
        if i==0:
            im.save(OUT/"cover.jpg",quality=95)
        sheet.paste(im.resize((220,392)),((i%3)*220,(i//3)*392))
    sheet.save(OUT/"contact.jpg",quality=94)

def main():
    previous,salary=map(Path,sys.argv[1:3])
    OUT.mkdir(exist_ok=True)
    report=json.loads((previous/"report.json").read_text())
    original=previous/"Postal_Edge_GDS_Postman_Two_Voices.mp4"
    spec=importlib.util.spec_from_file_location("sources",ONEOFFS/"postal_recruitment_draft"/"render.py")
    sources=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sources)
    sources.source_cards()
    for index in (0,1,5):
        shutil.copyfile(ONEOFFS/"postal_recruitment_action_cut"/f"location{index}.jpg",OUT/f"location{index}.jpg")
    shutil.copyfile(salary,OUT/"salary.png")
    shutil.copyfile(ONEOFFS/"postal_recruitment_website_outro"/"website-courses.jpg",OUT/"website.jpg")
    cues,duration,audio,samples=prepare_audio(original,report)
    assert 28.8<duration<29.3
    roles=[role for role,_ in report["dialogue"]]
    build_puppets(samples,duration,cues,roles)
    html=OUT/"smooth.html"
    html.write_text((HERE/"scenes.html").read_text().replace("__DATA__",json.dumps({
        "cues":cues,"roles":roles,"duration":duration})))
    renderer=CORE/"deep/render_deep.py"
    code=renderer.read_text()
    assert "#cutImg,#estImg" in code
    renderer.write_text(code.replace("#cutImg,#estImg","#cutImg,#estImg,#background,#golu,#bhaiya"))
    silent=OUT/"silent.mp4"
    run(sys.executable,str(renderer),str(html),str(silent))
    final=OUT/FILENAME
    run("ffmpeg","-v","error","-xerror","-y","-i",str(silent),"-f","f32le","-ar",str(RATE),"-ac","1","-i",str(audio),
        "-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","160k","-movflags","+faststart",str(final))
    run("ffmpeg","-v","error","-xerror","-i",str(final),"-f","null","-")
    contact(final,cues,duration)
    (OUT/"report.json").write_text(json.dumps({"seconds":duration,"cues":cues,
       "visual_scene_count":4,"voice":report["voices"],"pause_removed_seconds":sum(b-a for a,b in TRIMS)/FPS},indent=2))

if __name__=="__main__":
    main()
