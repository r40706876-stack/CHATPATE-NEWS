"""Re-edit existing media only. Preserve source AAC audio without re-encoding.
No script rewriting, TTS, image generation or external API calls.
"""
import argparse, json, math, subprocess, wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import numpy as np

W,H,FPS=1080,1920,25
S=1.5
NAVY=(18,40,68); RED=(224,67,57); CREAM=(247,245,239)
def p(v):return round(v*S)
def box(x):return tuple(p(v) for v in x)
FONT=None
_fonts={}
def font(n):
 n=p(n)
 if n not in _fonts:_fonts[n]=ImageFont.truetype(FONT,n,layout_engine=ImageFont.Layout.RAQM)
 return _fonts[n]
def cover(im,w,h,z=1,fx=.5,fy=.5):
 k=max(w/im.width,h/im.height)*z
 cw,ch=w/k,h/k
 x=(im.width-cw)*fx;y=(im.height-ch)*fy
 return im.crop((x,y,x+cw,y+ch)).resize((w,h),Image.Resampling.LANCZOS)
def wrap(text,f,width):
 rows=[];cur=''
 for word in text.split():
  nxt=(cur+' '+word).strip()
  if f.getlength(nxt)>width and cur:rows.append(cur);cur=word
  else:cur=nxt
 return rows+([cur] if cur else [])
def txt(d,xy,text,size=30,fill=NAVY,anchor='la'):
 d.text((p(xy[0]),p(xy[1])),text,font=font(size),fill=fill,anchor=anchor)
def panel(im,rect,img,z=1,fx=.5,fy=.5):
 x,y,w,h=rect
 piece=cover(img,p(w),p(h),z,fx,fy)
 mask=Image.new('L',piece.size);ImageDraw.Draw(mask).rounded_rectangle((0,0,p(w),p(h)),radius=p(20),fill=255)
 im.paste(piece,(p(x),p(y)),mask)

def main():
 global FONT
 a=argparse.ArgumentParser();a.add_argument('--input',required=True);a.add_argument('--prepared',required=True);a.add_argument('--faces',required=True);a.add_argument('--font',required=True);a.add_argument('--output',required=True);a.add_argument('--preview');args=a.parse_args()
 FONT=args.font;root=Path(args.prepared);out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
 ep=json.loads((root/'episode.json').read_text());lines=ep['lines']
 durations=[]
 for i in range(len(lines)):
  with wave.open(str(root/f'audio/{i:02d}.wav')) as wf:durations.append(wf.getnframes()/wf.getframerate())
 duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',args.input]))
 total=round(duration*FPS);bounds=[0]
 for dur in durations:bounds.append(round((bounds[-1]/FPS+dur)*FPS))
 bounds[-1]=total
 event=Image.open(root/'broll/1_0.jpg').convert('RGB').crop((40,0,565,360))
 crowd=Image.open(root/'broll/2_1.jpg').convert('RGB')
 train=Image.open(root/'broll/5_0.jpg').convert('RGB')
 outer=Image.open(root/'broll/5_1.jpg').convert('RGB')
 titles=['ट्रेन लेट नहीं थी…','चादर तानकर नींद!','जगह कहाँ मिली?','असली फ़ाइनेंशियल प्लानिंग!','यह संवाद काल्पनिक व्यंग्य है','मेरी ट्रेन आउटर पर खड़ी है!']
 names={'bablu':'बबलू • रिपोर्टर','chacha':'चाचा • देसी सलाह','ramesh':'रमेश • आम यात्री'}
 rawout=out.with_suffix('.silent.mp4')
 enc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-threads','4',str(rawout)],stdin=subprocess.PIPE)
 stills=[];shotlog=[]
 for i,ln in enumerate(lines):
  fp=next((Path(args.faces)/str(i)).rglob('*.mp4'))
  dims=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height','-of','json',str(fp)]))['streams'][0]
  fw,fh=dims['width'],dims['height']
  rd=subprocess.Popen(['ffmpeg','-v','error','-threads','1','-i',str(fp),'-vf',f'fps={FPS}','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
  last=Image.open(root/f'{i}/source.png').convert('RGB')
  text=ln.get('caption') or ln['say'];words=text.split();n=bounds[i+1]-bounds[i]
  print(f'line {i+1}: {n/FPS:.2f}s, existing face, original dialogue',flush=True)
  for t in range(n):
   raw=rd.stdout.read(fw*fh*3)
   if len(raw)==fw*fh*3:last=Image.frombytes('RGB',(fw,fh),raw)
   # Two-second edits; preserve the actual news photo for factual lines.
   beat=int(t/(FPS*2.0));mode=['split','face','photo'][beat%3]
   if i==0 and beat==0:mode='photo'
   if i in (2,5) and mode=='split':mode='face'
   hero=event if i in (0,1) else crowd if i==2 else train if i in (3,4) else outer
   im=Image.new('RGB',(W,H),CREAM);d=ImageDraw.Draw(im)
   d.rounded_rectangle(box((24,25,253,80)),p(13),fill=NAVY);txt(d,(40,35),'बकरा न्यूज़',31,(255,255,255))
   d.rounded_rectangle(box((466,29,696,77)),p(12),fill=RED);txt(d,(581,39),'खबर + व्यंग्य',24,(255,255,255),'ma')
   title=titles[i];rows=wrap(title,font(40),p(660))
   for j,row in enumerate(rows[:2]):txt(d,(30,105+j*51),row,40)
   y=220;z=1.015+.045*(t%(FPS*2))/(FPS*2)
   if mode=='split':
    panel(im,(24,y,672,505),hero,z,fx=.47+.05*math.sin(t/70),fy=.5)
    panel(im,(24,744,672,355),last.crop((0,560,1080,1400)) if i==0 else last,1.0,fy=.12)
    d=ImageDraw.Draw(im)
    d.rounded_rectangle(box((36,1052,325,1090)),p(8),fill=NAVY);txt(d,(50,1057),names.get(ln['who'],ln['who']),22,(255,255,255))
   elif mode=='face':
    face_view=last.crop((0,480,1080,1900)) if i==0 else last.crop((280,20,920,870)) if i in (1,4) else last.crop((200,0,880,888)) if i==3 else last
    panel(im,(24,y,672,879),face_view,1.0,fy=.08)
    panel(im,(462,241,214,162),hero,1)
    d=ImageDraw.Draw(im)
    d.rounded_rectangle(box((36,1046,340,1090)),p(8),fill=NAVY);txt(d,(50,1053),names.get(ln['who'],ln['who']),22,(255,255,255))
   else:
    # Large, correctly framed event, with a subtle pan instead of a long static slide.
    panel(im,(24,y,672,879),hero,z,fx=.4+.16*(t%(FPS*2))/(FPS*2),fy=.5)
    if i in (0,1):
     # Preserve the complete photograph as an inset when the portrait crop is tighter.
     panel(im,(430,890,246,169),hero,1)
    d=ImageDraw.Draw(im)
   credit='घटना की तस्वीर: Jagran / सोशल मीडिया' if i in (0,1) else 'प्रतीकात्मक दृश्य • मूल episode के स्रोत'
   d.rounded_rectangle(box((32,224,680,258)),p(6),fill=(255,255,255));txt(d,(45,228),credit,19)
   if i in (0,3,4):
    note='काल्पनिक व्यंग्य • आधिकारिक नियम की सूचना नहीं' if i==4 else 'किरदारों के संवाद व्यंग्य हैं'
    d.rounded_rectangle(box((32,684 if mode=='split' else 990,688,729 if mode=='split' else 1035)),p(9),fill=(255,232,177))
    txt(d,(46,692 if mode=='split' else 998),note,21,NAVY)
   # Show the exact existing caption in short, readable groups.
   wi=min(len(words)-1,int(t/max(1,n)*len(words)));start=wi//4*4;chunk=' '.join(words[start:start+4])
   rows=wrap(chunk,font(35),p(610));sz=35
   if len(rows)>2:sz=31;rows=wrap(chunk,font(sz),p(610))
   d.rounded_rectangle(box((24,1116,696,1234)),p(17),fill=NAVY)
   for k,row in enumerate(rows[:2]):txt(d,(360,1130+k*45),row,sz,(255,255,255),'ma')
   txt(d,(28,1244),'मुंबई लोकल  /  NEWS SATIRE',17,(84,98,112))
   d.rounded_rectangle(box((24,1270,696,1277)),p(3),fill=(211,218,225))
   d.rounded_rectangle(box((24,1270,24+672*(bounds[i]+t+1)/total,1277)),p(3),fill=RED)
   if t in (0,min(n-1,round(n*.55))):
    if args.preview:stills.append(im.resize((270,480)))
   enc.stdin.write(im.tobytes())
  rd.kill();rd.stdout.close();rd.wait()
 enc.stdin.close()
 if enc.wait():raise RuntimeError('video encoding failed')
 # Input AAC is copied bit-for-bit; never regenerate or shorten dialogue.
 subprocess.run(['ffmpeg','-y','-v','error','-i',str(rawout),'-i',args.input,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','copy','-map_metadata','-1','-movflags','+faststart',str(out)],check=True)
 rawout.unlink()
 if args.preview:
  sheet=Image.new('RGB',(270*6,480*2),CREAM)
  for k,st in enumerate(stills[:12]):sheet.paste(st,((k%6)*270,(k//6)*480))
  sheet.save(args.preview)
 print('DONE',out,flush=True)
if __name__=='__main__':main()
