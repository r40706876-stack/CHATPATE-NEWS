from pathlib import Path
import sys,math,json,subprocess
from PIL import Image,ImageDraw
R=Path('/workspace/scratch/b0b64e20710c');sys.path.insert(0,str(R/'postal_series_job'))
import render_series as S
J=R/'postal_motion_job';O=J/'segments';O.mkdir(exist_ok=True)
def ease(t):return 1-(1-max(0,min(1,t)))**3
def animate_region(im,box,t,delay,dx=0,dy=0):
 x1,y1,x2,y2=box;piece=im.crop(box);d=ImageDraw.Draw(im);d.rectangle(box,fill=S.CREAM)
 p=ease((t-delay)/.65)
 if p<=0:return
 alpha=Image.new('L',piece.size,int(255*p));im.paste(piece,(round(x1+dx*(1-p)),round(y1+dy*(1-p))),alpha)
def normal_frame(name,t,dur):
 im=S.frame(name,t,dur)
 if name.startswith('intro'):
  animate_region(im,(36,190,1044,505),t,0,dy=70)
  animate_region(im,(48,558,1032,1006),t,2.45,dx=940)
  animate_region(im,(30,1010,1060,1515),t,.45,dx=-360)
  animate_region(im,(48,1545,1032,1750),t,.9,dy=180)
 else:
  animate_region(im,(36,195,1044,410),t,0,dy=-55)
  animate_region(im,(50,430,1030,670),t,1.25 if name.endswith('01') else 2.8,dx=700)
  animate_region(im,(48,720,1032,1178),t,4.0 if name.endswith('01') else .45,dy=130)
  animate_region(im,(45,1635,1035,1802),t,max(.5,dur-2.8),dy=160)
 return im
def save_frame(t,dur):
 im=Image.new('RGB',(1080,1920),S.CREAM);d=ImageDraw.Draw(im)
 for x in range(-20,1120,76):d.polygon([(x,0),(x+38,0),(x+9,18),(x-29,18)],fill=S.RED if (x//76)%2 else S.NAVY)
 S.tx(d,(540,100),'POSTAL WALA',45,S.RED,True)
 S.tx(d,(540,295),'ये ज़रूरी नियम है',72,S.NAVY,True)
 S.tx(d,(540,425),'वीडियो पहले ही सेव कर लो',53,S.RED,True)
 d.ellipse((165,665,895,1395),fill='#eee1ca')
 # A bookmark travels into the saved collection; the tick is drawn after arrival.
 p=ease((t-.25)/1.05);x=210+395*p;y=610+380*p-200*math.sin(math.pi*p);scale=.65+.35*p
 pts=[(-80,-110),(80,-110),(80,110),(0,62),(-80,110)]
 angle=(-28+28*p)*math.pi/180
 transformed=[(x+scale*(a*math.cos(angle)-b*math.sin(angle)),y+scale*(a*math.sin(angle)+b*math.cos(angle))) for a,b in pts]
 d.rounded_rectangle((270,1130,810,1325),radius=30,fill=S.NAVY)
 S.tx(d,(540,1190),'सेव किया',57,'white',True)
 d.polygon(transformed,fill=S.GOLD,outline=S.RED,width=6)
 if t>1.3:
  q=ease((t-1.3)/.4);d.ellipse((690,935,810,1055),fill=S.TEAL)
  path=[(717,995),(741,1017),(784,970)];lengths=[math.dist(path[0],path[1]),math.dist(path[1],path[2])];remain=q*sum(lengths)
  for i,length in enumerate(lengths):
   if remain<=0:break
   part=min(1,remain/length);a=path[i];b=path[i+1];d.line((a[0],a[1],a[0]+(b[0]-a[0])*part,a[1]+(b[1]-a[1])*part),fill='white',width=10);remain-=length
 S.tx(d,(540,1535),'बाद में दोबारा समझने के लिए',39,S.NAVY,True)
 S.tx(d,(540,1660),'रोज़ शाम 6:30 बजे',43,S.RED,True)
 return im
def duration(w):return float(json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-of','json',str(w)]))['format']['duration'])
def render(name,wav):
 dur=math.ceil((duration(wav)+.3)*30)/30
 fun=save_frame if name=='save_prompt' else lambda t,d:normal_frame(name,t,d)
 for t in [min(.6,dur/2),dur-1]:fun(t,dur).save(J/f'{name}_{round(t,1)}.jpg',quality=93)
 cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','1080x1920','-framerate','30','-i','-','-i',str(wav),'-filter_complex',f'[1:a]adelay=120|120,apad,atrim=duration={dur}[a]','-map','0:v','-map','[a]','-t',str(dur),'-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-threads','2','-c:a','aac','-b:a','160k','-ar','48000','-ac','2','-movflags','+faststart',str(O/(name+'.mp4'))]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 for i in range(round(dur*30)):p.stdin.write(fun(i/30,dur).tobytes())
 p.stdin.close();assert p.wait()==0;print(name,dur,flush=True);return dur
if __name__=='__main__':
 report={n:render(n,R/'postal_series_job/voice'/f'{n}.wav') for n in ['intro_01','intro_02','outro_01','outro_02']}
 report['save_prompt']=render('save_prompt',J/'voice/save_prompt.wav')
 (J/'segment_durations.json').write_text(json.dumps(report,indent=2))
