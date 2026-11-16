from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import subprocess,json,math
ROOT=Path('/workspace/scratch/b0b64e20710c');J=ROOT/'postal_series_job';OUT=J/'segments';OUT.mkdir(exist_ok=True)
NAVY='#202e4b';RED='#b6302c';CREAM='#faf3e7';GOLD='#f4c35e';TEAL='#28745c'
def font(n,b=False,latin=False):
 family='NotoSans' if latin else 'NotoSansDevanagari'
 return ImageFont.truetype('/usr/share/fonts/truetype/noto/'+family+('-Bold' if b else '-Regular')+'.ttf',n)
def tx(d,xy,s,n,fill=NAVY,b=False,anchor='mt'):
 d.text(xy,s,font=font(n,b,s.isascii()),fill=fill,anchor=anchor)
def lines(d,y,ss,n,fill=NAVY,b=False,gap=1.35):
 for i,s in enumerate(ss):tx(d,(540,y+i*n*gap),s,n,fill,b)
def rr(d,box,fill,rad=28,outline=None,width=1):d.rounded_rectangle(box,radius=rad,fill=fill,outline=outline,width=width)
CHAR=Image.open(J/'assets/bhaiya.webp').convert('RGBA')
def clock(d,cx,cy,r,t):
 d.ellipse((cx-r,cy-r,cx+r,cy+r),fill='#fffdf8',outline=NAVY,width=7)
 for h in range(12):
  a=h*math.pi/6;d.line((cx+math.sin(a)*(r-10),cy-math.cos(a)*(r-10),cx+math.sin(a)*(r-18),cy-math.cos(a)*(r-18)),fill='#c7baa7',width=4)
 # 6:30: hour halfway from six toward seven.
 a=195*math.pi/180;d.line((cx,cy,cx+math.sin(a)*r*.48,cy-math.cos(a)*r*.48),fill=NAVY,width=8)
 d.line((cx,cy,cx,cy+r*.74),fill=RED,width=6);d.ellipse((cx-6,cy-6,cx+6,cy+6),fill=RED)
def frame(name,t,duration):
 im=Image.new('RGB',(1080,1920),CREAM);d=ImageDraw.Draw(im)
 for x in range(-20,1120,76):d.polygon([(x,0),(x+38,0),(x+9,18),(x-29,18)],fill=RED if (x//76)%2 else NAVY)
 tx(d,(62,80),'POSTAL WALA',42,RED,True,'lt')
 ep='01' if name.endswith('01') else '02';intro=name.startswith('intro')
 rr(d,(825,69,1018,134),NAVY,30);tx(d,(922,82),'भाग '+ep,32,'white',True)
 if intro:
  tx(d,(540,205),'नई सीरीज़' if ep=='01' else 'हमारी सीरीज़ का दूसरा भाग',33,RED,True)
  lines(d,280,['डाक विभाग के','डाउट्स'],82,b=True,gap=1.2)
  rr(d,(55,565,1025,1000),'#fffdf8',32,'#dfd2be',2)
  tx(d,(540,610),'आज पहला डाउट' if ep=='01' else 'आज का डाउट',37,TEAL,True)
  if ep=='01':lines(d,705,['ट्रांसफर:','1 साल या 2 साल?'],74,b=True,gap=1.4)
  else:lines(d,705,['जीडीएस ट्रांसफर की','5 जरूरी तारीखें'],68,b=True,gap=1.5)
  # The host gestures towards a gently pulsing question or calendar badge.
  char=CHAR.resize((518,474),Image.Resampling.LANCZOS)
  im.paste(char,(510,1025+round(5*math.sin(t*2.4))),char)
  d.ellipse((65,1060,485,1480),fill='#eee1ca',outline='#dfcba7',width=3)
  if ep=='01':
   tx(d,(275,1125),'?',190,RED,True);tx(d,(275,1370),'डाउट क्लियर',31,NAVY,True)
  else:
   rr(d,(150,1140,405,1390),'#fffdf8',25);rr(d,(150,1140,405,1208),RED,25)
   tx(d,(277,1235),'5',100,NAVY,True)
  rr(d,(55,1550,1025,1745),NAVY,30)
  tx(d,(540,1585),'रोज़ शाम 6:30 बजे',57,'white',True)
  tx(d,(540,1680),'एक टॉपिक, आसान भाषा में',30,'#fff0c4')
  tx(d,(540,1810),'ट्रांसफर / सेवा नियम / विभागीय परीक्षा',30,'#716a61')
 else:
  tx(d,(540,212),'डाक विभाग के डाउट्स',62,NAVY,True)
  tx(d,(540,325),'रोज़ एक नया डाउट',47,TEAL,True)
  # Schedule is the visual anchor; only a subtle ring moves around it.
  clock(d,170,553,89,t)
  tx(d,(650,450),'शाम',42,NAVY,True)
  tx(d,(650,525),'6:30 बजे',100,RED,True)
  rr(d,(55,730,1025,1170),'#fffdf8',32,'#dfd2be',2)
  if ep=='01':
   tx(d,(540,778),'कल / भाग 02',43,RED,True)
   lines(d,880,['जीडीएस ट्रांसफर की','5 जरूरी तारीखें'],65,b=True,gap=1.45)
  else:
   tx(d,(540,778),'इस सीरीज़ में नियमित जानकारी',40,RED,True)
   lines(d,875,['ट्रांसफर और सेवा नियम','विभागीय परीक्षा के डाउट्स'],51,b=True,gap=1.65)
  char=CHAR.resize((440,403),Image.Resampling.LANCZOS)
  im.paste(char,(615,1190+round(4*math.sin(t*2.1))),char)
  tx(d,(305,1260),'सही जानकारी,',45,TEAL,True)
  tx(d,(305,1330),'आसान भाषा में।',45,TEAL,True)
  rr(d,(55,1640,1025,1795),NAVY,30)
  tx(d,(540,1680),'पोस्टल वाला को फॉलो करें',53,'white',True)
  tx(d,(540,1840),'@postal_wala',32,RED,True)
 # Small moving lower progress line.
 d.rectangle((0,1908,int(1080*min(1,t/duration)),1920),fill=RED)
 return im
def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)]))
def render(name):
 wav=J/'voice'/f'{name}.wav';duration=float(probe(wav)['format']['duration'])+.30
 # Exact frame count, no added silent end card.
 count=math.ceil(duration*30);duration=count/30
 for t in [min(1,duration/2),duration-1]:frame(name,t,duration).save(J/f'{name}_{round(t,1)}.jpg',quality=93)
 cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','1080x1920','-framerate','30','-i','-','-i',str(wav),'-filter_complex',f'[1:a]adelay=120|120,apad,atrim=duration={duration}[a]','-map','0:v','-map','[a]','-t',str(duration),'-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-threads','2','-c:a','aac','-b:a','160k','-ar','48000','-ac','2','-movflags','+faststart',str(OUT/f'{name}.mp4')]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 for i in range(count):p.stdin.write(frame(name,i/30,duration).tobytes())
 p.stdin.close();assert p.wait()==0
 print(name,duration,flush=True);return duration
if __name__=='__main__':
 report={name:render(name) for name in ['intro_01','intro_02','outro_01','outro_02']}
 (J/'segment_durations.json').write_text(json.dumps(report,indent=2))
