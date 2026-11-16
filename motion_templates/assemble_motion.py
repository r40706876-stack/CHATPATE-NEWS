from pathlib import Path
import json,subprocess
R=Path('/workspace/scratch/b0b64e20710c');J=R/'postal_motion_job';O=J/'final';O.mkdir(exist_ok=True)
def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)]))
jobs=[('01','norm',R/'postal_rule3_job/final/Postal_Wala_GDS_Rule3.mp4',6.03,41.23,'Postal_Wala_GDS_Rule3.mp4'),('02','dates',R/'postal_dates_job/final/Postal_Wala_GDS_Transfer_Dates.mp4',4.82,30.6,'Postal_Wala_GDS_Transfer_Dates.mp4')]
qa=[]
for ep,kind,original,start,end,name in jobs:
 body=J/kind/'body_with_audio.mp4';silent=J/kind/f'{kind}_animated_body.mp4'
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(silent),'-ss',str(start),'-t',str(end-start),'-i',str(original),'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','160k','-ar','48000','-ac','2','-shortest','-movflags','+faststart',str(body)],check=True)
 inputs=[J/'segments'/f'intro_{ep}.mp4',J/'segments/save_prompt.mp4',body,R/'postal_real_demo_job/Postal_Wala_Real_Website_Demo.mp4',J/'segments'/f'outro_{ep}.mp4']
 ds=[float(probe(p)['format']['duration']) for p in inputs];fade=.08;total=ds[0]
 fs=['[5:v]split=2[o1][o2]']
 for i in range(5):
  label=f'p{i}' if i in [2,3] else f'v{i}'
  fs.append(f'[{i}:v]setpts=PTS-STARTPTS,fps=30,settb=AVTB,format=yuv420p[{label}]')
  if i in [2,3]:fs.append(f'[p{i}][o{i-1}]overlay=eof_action=repeat[v{i}]')
  fs.append(f'[{i}:a]asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a{i}]')
 for i in range(1,5):
  prev='v0' if i==1 else f'x{i-1}';fs.append(f'[{prev}][v{i}]xfade=transition=fade:duration={fade}:offset={total-fade}[x{i}]');total+=ds[i]-fade
  prev='a0' if i==1 else f'z{i-1}';fs.append(f'[{prev}][a{i}]acrossfade=d={fade}:c1=tri:c2=tri[z{i}]')
 fs.append('[z4]loudnorm=I=-16:LRA=11:TP=-1.5[a]')
 cmd=['ffmpeg','-v','error','-y','-filter_complex_threads','1']
 for p in inputs:cmd+=['-i',str(p)]
 cmd+=['-i',str(R/'postal_series_job'/f'series_ribbon_{ep}.png'),'-filter_complex',';'.join(fs),'-map','[x4]','-map','[a]','-t',str(total),'-c:v','libx264','-preset','veryfast','-crf','18','-profile:v','high','-level','4.1','-pix_fmt','yuv420p','-r','30','-threads','2','-c:a','aac','-b:a','160k','-ar','48000','-ac','2','-movflags','+faststart',str(O/name)]
 subprocess.run(cmd,check=True);p=probe(O/name);duration=float(p['format']['duration']);v=next(s for s in p['streams'] if s['codec_type']=='video');a=next(s for s in p['streams'] if s['codec_type']=='audio')
 assert abs(duration-total)<.25 and (v['width'],v['height'])==(1080,1920) and a['codec_name']=='aac'
 subprocess.run(['ffmpeg','-v','error','-i',str(O/name),'-f','null','-'],check=True)
 points={'opening':1,'save_prompt':ds[0]+1.5,'main':sum(ds[:2])+1,'motion':sum(ds[:2])+8,'demo':sum(ds[:3])+4,'closing':duration-2}
 for k,t in points.items():subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(O/name),'-frames:v','1',str(O/f'episode_{ep}_{k}.jpg')],check=True)
 qa.append({'episode':ep,'file':str(O/name),'duration_seconds':duration,'dimensions':[1080,1920],'fps':30,'technical_decode':'pass','demo_seconds':12.5,'save_prompt':'ये ज़रूरी नियम है, इसलिए वीडियो पहले ही सेव कर लो।','animation_version':'v2 meaningful scene motion: calendar flips, sequential cards/checks/chance tokens, document stamp, bookmark save, entering series intro/outro','motion_checks':json.loads((J/kind/'Motion_QA.json').read_text())['motion_checks'],'series_name':'Postal Wala — डाक विभाग के डाउट्स','time':'18:30','timezone':'Asia/Kolkata','published':False})
 print(json.dumps(qa[-1],ensure_ascii=False),flush=True)
(O/'Motion_Videos_QA.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2))
