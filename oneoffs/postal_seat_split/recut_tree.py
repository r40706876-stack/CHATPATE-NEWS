"""Trim speech gaps and insert the original Clause 2 tree animation."""
from pathlib import Path
import json
import subprocess as sp
import sys

from playwright.sync_api import sync_playwright

ROOT = Path.cwd()
CORE = Path(sys.argv[1]).resolve()
SOURCE = Path(sys.argv[2]).resolve()
OUT = Path(sys.argv[3]).resolve()
OUT.mkdir(parents=True, exist_ok=True)
FRAMES = OUT / "tree"
FRAMES.mkdir(exist_ok=True)
CUTS = [(0,8.94),(9,13.82),(15,21.24),(22,26.58),(28,31.58),
        (31.65,32.86),(33.5,37.90),(39.90,42.17),(42.25,48.10)]
FPS = 24
DEMO_DURATION = sum(round((end-start)*FPS) for start,end in CUTS[-2:]) / FPS
NAME = "Postal_Edge_Postman_50_50_Tree_Demo.mp4"

def run(*arguments, **kwargs):
    sp.run(arguments, check=True, **kwargs)

def render_tree():
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page(viewport={"width":960,"height":540},device_scale_factor=1.5)
        page.route("https://**/*",lambda route:route.abort())
        page.goto((CORE/"deep"/"premium_c2_1.html").as_uri(),wait_until="load")
        page.add_style_tag(content="""
            #th_tl .tag,#th_dl .tag,#th_pl .tag {font-family:'Noto Sans Devanagari',sans-serif !important}
            #demo-title {position:absolute;left:278px;top:105px;width:404px;text-align:center;font:700 17px 'Noto Sans Devanagari',sans-serif;color:#f9f1d9;z-index:38}
            #chip,#capbox,#vig,#rx { visibility:hidden !important }
        """)
        cue = page.evaluate("""()=>{window.READY();
            const title=document.createElement('div'); title.id='demo-title';
            title.textContent='HO, SO, BO • पेड़ से याद रखो'; document.body.append(title);
            const start=W('t5','तना')-.08, end=LT('t6')-.17;
            window.seek(end);
            const boxes=['th_tree','th_tl','th_dl','th_pl'].map(id=>document.getElementById(id).getBoundingClientRect().toJSON());
            return {start,end,boxes,text:['th_tl','th_dl','th_pl'].map(id=>document.getElementById(id).innerText)};
        }""")
        assert cue["text"]==["तना = HO","डालियाँ = SO","पत्तियाँ = BO"],cue["text"]
        print(json.dumps(cue,ensure_ascii=False),flush=True)
        clip={"x":252,"y":100,"width":456,"height":360}
        count=round(DEMO_DURATION*FPS)+3
        for i in range(count):
            t=cue["start"]+min(1,i/(count-13))*(cue["end"]-cue["start"])
            page.evaluate("t=>window.seek(t)",t)
            page.screenshot(path=str(FRAMES/f"{i:04d}.png"),clip=clip,timeout=10000)
        browser.close()
    return cue

def cut():
    video = []
    audio = []
    for i,(start,end) in enumerate(CUTS):
        video.append(f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}]")
        audio.append(f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}]")
    joined = "".join(f"[v{i}][a{i}]" for i in range(len(CUTS)))
    first = sum(round((end-start)*FPS) for start,end in CUTS[:-2])/FPS
    filters=";".join(video+audio+[
        f"{joined}concat=n={len(CUTS)}:v=1:a=1[base][audio]",
        f"[1:v]scale=618:488,setsar=1,setpts=PTS-STARTPTS+{first:.6f}/TB[tree]",
        f"[base][tree]overlay=x=51:y=221:enable='gte(t,{first:.6f})':eof_action=repeat:repeatlast=1[v]",
    ])
    run("ffmpeg","-hide_banner","-v","error","-y","-filter_complex_threads","2","-i",str(SOURCE),
        "-framerate",str(FPS),"-i",str(FRAMES/"%04d.png"),"-filter_complex",filters,
        "-map","[v]","-map","[audio]","-c:v","libx264","-preset","fast","-crf","18",
        "-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-movflags","+faststart",str(OUT/NAME))
    return first

cue=render_tree()
start=cut()
run("ffmpeg","-v","error","-i",str(OUT/NAME),"-f","null","-")
for index,t in enumerate([1.4,13.6,24.8,start+.45,start+3.0,start+6.8]):
    run("ffmpeg","-y","-v","error","-ss",str(t),"-i",str(OUT/NAME),"-frames:v","1",
        "-vf","scale=240:426",str(OUT/f"review-{index}.jpg"))
print("Verified",NAME,"demo begins",start,flush=True)
