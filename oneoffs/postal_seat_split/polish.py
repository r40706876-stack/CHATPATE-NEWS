"""Add evidence and timed metric motion while copying the approved AAC track."""
from functools import lru_cache
from pathlib import Path
import json
import math
import subprocess as sp
import sys

from PIL import Image, ImageDraw, ImageOps
import hook as art

W,H,FPS=720,1280,24
SOURCE=Path(sys.argv[1]).resolve()
OUT=Path(sys.argv[2]).resolve()
OUT.mkdir(parents=True,exist_ok=True)
NAME="Postal_Edge_Postman_50_50_Animated_Final.mp4"
DOC_START_FRAME=72
DOC_FRAMES=32
CARDBASE="#122630"
MATHBASE="#142a34"
BORDER="#426470"

def card(im,box,color,outline=None,radius=12):
    art.rr(im,box,radius,color,outline,2 if outline else 1)

def fade_add(im,overlay,opacity):
    if opacity<=0:
        return
    if opacity<1:
        channel=overlay.getchannel("A").point(lambda v: round(v*opacity))
        overlay.putalpha(channel)
    im.alpha_composite(overlay)

def draw_value(im,x,y,label,size,color,progress,center=False):
    p=art.ease(progress)
    layer=Image.new("RGBA",im.size)
    art.txt(layer,(x,y+round(12*(1-p))),label,size,color,anchor="mm" if center else "lm")
    fade_add(im,layer,p)

def counter(im,x,y,target,t,size,color,center=False,prefix=""):
    p=art.ease(t)
    if p<=0:
        return
    draw_value(im,x,y,prefix+f"{target:,}",size,color,min(1,p*2.0),center)

draft=Image.open(Path(__file__).with_name("schedule.jpg")).convert("RGBA")
def doc(im,n):
    overlay=Image.new("RGBA",im.size)
    card(overlay,(51,213,669,684),"#142a34",BORDER,21)
    art.txt(overlay,(76,258),"ड्राफ्ट की असली कॉपी",31,art.white,True,anchor="lm")
    art.txt(overlay,(642,260),"पेज 4",19,art.aqua,True,anchor="rm")
    paper=draft.resize((566,211),Image.Resampling.LANCZOS)
    marker=Image.new("RGBA",paper.size)
    card(marker,(115,121,181,155),(255,204,85,133),None,4)
    paper.alpha_composite(marker)
    card(overlay,(70,304,650,540),"#f0e8d7",None,9)
    overlay.alpha_composite(paper,(77,315))
    # The table's actual printed number is retained, including the footnote marker.
    ImageDraw.Draw(overlay).rounded_rectangle((192,436,258,470),5,outline="#d28d20",width=2)
    art.txt(overlay,(360,594),"45,899 कुल पोस्टमैन पद",38,art.gold,True)
    art.txt(overlay,(360,642),"स्रोत  |  20 नवंबर 2026 का ड्राफ्ट",21,art.slate,True)
    a=min(1,(n-DOC_START_FRAME+.65)/1.8,(DOC_START_FRAME+DOC_FRAMES-n+.3)/1.8)
    fade_add(im,overlay,a)

def line(im,x,y,width,color,p):
    length=round(width*art.ease(p))
    if length>2:
        art.rr(im,(x,y,x+length,y+3),2,color)

def proof_sum(im,t):
    dt=t-24.625
    if dt<1.05:
        card(im,(77,379,643,475),MATHBASE)
        draw_value(im,360,424,"45,899 × 50%",65,art.gold,(dt-.06)/.68,True)
    if dt<6:
        card(im,(77,480,643,592),MATHBASE)
        counter(im,360,522,22950,(dt-3.80)/1.20,85,art.aqua,True,"≈ ")
    if 4.25<=dt<7.8:
        line(im,175,573,370,"#54a895",(dt-4.25)/.75)

def animated(im,n):
    t=n/FPS
    if DOC_START_FRAME<=n<DOC_START_FRAME+DOC_FRAMES:
        doc(im,n)
    elif 4.333<=t<5.80:
        card(im,(76,317,638,403),CARDBASE)
        counter(im,92,355,45899,(t-4.333)/.73,70,art.white)
        card(im,(76,520,638,606),CARDBASE)
        counter(im,92,558,1870,(t-5.01)/.67,70,art.white)
        line(im,92,395,217,art.gold,(t-4.51)/.58)
        line(im,92,598,159,art.aqua,(t-5.19)/.58)
    elif 13.833<=t<14.70:
        card(im,(68,358,312,436),"#152934")
        draw_value(im,78,392,"50%",64,art.gold,(t-13.833)/.50)
        line(im,80,431,126,art.gold,(t-14.01)/.48)
    elif 20.083<=t<20.96:
        card(im,(68,505,312,582),"#152934")
        draw_value(im,78,542,"50%",64,art.aqua,(t-20.083)/.54)
        line(im,80,579,126,art.aqua,(t-20.28)/.46)
    elif 24.625<=t<32.88:
        proof_sum(im,t)
    elif 32.88<=t<34.12:
        card(im,(151,324,569,434),MATHBASE)
        counter(im,360,394,23,(t-32.91)/.77,110,art.gold,True)
    elif 48.45<=t<49.42:
        # A short accent below the CTA leaves the voice and caption unobstructed.
        line(im,208,573,305,art.aqua,(t-48.53)/.61)
    return im

def main():
    args=["ffmpeg","-v","error"]
    reader=sp.Popen(args+["-i",str(SOURCE),"-map","0:v:0","-f","rawvideo","-pix_fmt","rgb24","-"],stdout=sp.PIPE)
    writer=sp.Popen(args+["-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
        "-i",str(SOURCE),"-map","0:v","-map","1:a:0","-c:v","libx264","-preset","fast","-crf","17","-threads","4",
        "-pix_fmt","yuv420p","-c:a","copy","-movflags","+faststart",str(OUT/NAME)],stdin=sp.PIPE)
    n=0
    try:
        while block:=reader.stdout.read(W*H*3):
            if len(block)!=W*H*3:
                raise RuntimeError("Incomplete video frame")
            frame=Image.frombytes("RGB",(W,H),block).convert("RGBA")
            frame=animated(frame,n).convert("RGB")
            if n in {88,119,134,344,495,599,700,801,915,1180}:
                frame.resize((240,426)).save(OUT/f"polish-review-{n:04d}.jpg",quality=89)
            writer.stdin.write(frame.tobytes())
            n+=1
    finally:
        reader.stdout.close()
        writer.stdin.close()
    assert reader.wait()==writer.wait()==0
    sp.run(args+["-i",str(OUT/NAME),"-f","null","-"],check=True)
    def audio_hash(path):
        return sp.check_output(args+["-i",str(path),"-map","0:a:0","-c","copy","-f","hash","-hash","sha256","-"])
    assert audio_hash(SOURCE)==audio_hash(OUT/NAME)
    print(json.dumps({"frames":n,"document_frames":DOC_FRAMES,"audio":"verified byte-for-byte","fps":FPS}))

if __name__=="__main__":
    main()
