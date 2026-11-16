from pathlib import Path
from PIL import Image,ImageDraw
import subprocess,json
from render_series import font,NAVY,CREAM
R=Path('/workspace/scratch/b0b64e20710c');J=R/'postal_series_job';O=J/'final';O.mkdir(exist_ok=True)
def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)]))
jobs=[('01',R/'postal_rule3_job/final/Postal_Wala_GDS_Rule3.mp4',6.03,41.23,'Postal_Wala_GDS_Rule3.mp4'),('02',R/'postal_dates_job/final/Postal_Wala_GDS_Transfer_Dates.mp4',4.82,30.60,'Postal_Wala_GDS_Transfer_Dates.mp4')]
qa=[]
for ep,source,start,end,name in jobs:
 overlay=Image.new('RGBA',(1080,1920),(0,0,0,0));d=ImageDraw.Draw(overlay)
 d.rectangle((0,19,1080,69),fill=CREAM)
 d.text((62,27),'डाक विभाग के डाउट्स / भाग '+ep,font=font(28,True),fill=NAVY)
 d.text((1018,27),'रोज़ शाम 6:30',font=font(28,True),fill=NAVY,anchor='rt')
 op=J/f'series_ribbon_{ep}.png';overlay.save(op)
 intro=J/'segments'/f'intro_{ep}.mp4';outro=J/'segments'/f'outro_{ep}.mp4';demo=J/'assets/actual_website_demo.mp4'
 ds=[float(probe(intro)['format']['duration']),end-start,float(probe(demo)['format']['duration']),float(probe(outro)['format']['duration'])]
 filters=['[4:v]split=2[o1][o2]', '[0:v]setpts=PTS-STARTPTS,fps=30,settb=AVTB,format=yuv420p[v0]',f'[1:v]trim=start={start}:end={end},setpts=PTS-STARTPTS,fps=30,settb=AVTB,format=yuv420p[m1]','[m1][o1]overlay=eof_action=repeat[v1]','[2:v]setpts=PTS-STARTPTS,fps=30,settb=AVTB,format=yuv420p[m2]','[m2][o2]overlay=eof_action=repeat[v2]','[3:v]setpts=PTS-STARTPTS,fps=30,settb=AVTB,format=yuv420p[v3]']
 fade=.08;total=ds[0]
 for i in range(1,4):
  prev='v0' if i==1 else f'x{i-1}'
  filters.append(f'[{prev}][v{i}]xfade=transition=fade:duration={fade}:offset={total-fade}[x{i}]');total+=ds[i]-fade
 for i in range(4):
  trim=f'atrim=start={start}:end={end},' if i==1 else ''
  filters.append(f'[{i}:a]{trim}asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a{i}]')
 for i in range(1,4):
  prev='a0' if i==1 else f'z{i-1}'
  filters.append(f'[{prev}][a{i}]acrossfade=d={fade}:c1=tri:c2=tri[z{i}]')
 filters.append('[z3]loudnorm=I=-16:LRA=11:TP=-1.5[a]')
 cmd=['ffmpeg','-v','error','-y','-filter_complex_threads','1','-i',str(intro),'-i',str(source),'-i',str(demo),'-i',str(outro),'-i',str(op),'-filter_complex',';'.join(filters),'-map','[x3]','-map','[a]','-t',str(total),'-c:v','libx264','-preset','veryfast','-crf','18','-profile:v','high','-level','4.1','-pix_fmt','yuv420p','-r','30','-threads','2','-c:a','aac','-b:a','160k','-ar','48000','-ac','2','-movflags','+faststart',str(O/name)]
 subprocess.run(cmd,check=True)
 p=probe(O/name);actual=float(p['format']['duration']);v=next(s for s in p['streams'] if s['codec_type']=='video');a=next(s for s in p['streams'] if s['codec_type']=='audio')
 assert abs(actual-total)<.3 and (v['width'],v['height'])==(1080,1920) and v['codec_name']=='h264' and a['codec_name']=='aac'
 subprocess.run(['ffmpeg','-v','error','-i',str(O/name),'-f','null','-'],check=True)
 for tag,t in [('opening',1),('body',ds[0]+2),('demo',ds[0]+ds[1]+4),('closing',actual-3)]:
  subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(O/name),'-frames:v','1',str(O/f'episode_{ep}_{tag}.jpg')],check=True)
 qa.append({'episode':ep,'file':str(O/name),'duration_seconds':actual,'dimensions':[1080,1920],'demo_seconds':12.5,'series_name':'Postal Wala — डाक विभाग के डाउट्स','time':'18:30','timezone':'Asia/Kolkata','main_content_range':[start,end],'technical_decode':'pass','published':False})
 print(json.dumps(qa[-1],ensure_ascii=False),flush=True)
(O/'Series_Video_QA.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2))
