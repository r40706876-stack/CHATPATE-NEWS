from pathlib import Path
import json,hashlib,shutil,zipfile
R=Path('/workspace/scratch/b0b64e20710c');J=R/'postal_motion_job';F=R/'postal_rule3_instagram_ready'
qa=json.loads((J/'final/Motion_Videos_QA.json').read_text());assert len(qa)==2 and all(x['technical_decode']=='pass' for x in qa)
for name in ['Postal_Wala_GDS_Rule3.mp4','Postal_Wala_GDS_Transfer_Dates.mp4']:shutil.copy2(J/'final'/name,F/name)
sentence='ये ज़रूरी नियम है, इसलिए वीडियो पहले ही सेव कर लो।'
for name in ['Instagram_Caption.txt','Episode_02_Caption.txt']:
 cap=(F/name).read_text()
 if sentence not in cap:cap=cap.split('\n\n',1)[0]+'\n\n📌 '+sentence+'\n\n'+cap.split('\n\n',1)[1]
 assert len(cap)<2200;(F/name).write_text(cap)
for i,manifest in enumerate(['Posting_Manifest_HOLD.json','Episode_02_Posting_Manifest_HOLD.json']):
 p=F/manifest;m=json.loads(p.read_text());assert not m['publish_enabled'] and not m['published'] and not m['scheduled']
 m['caption']=(F/('Instagram_Caption.txt' if i==0 else 'Episode_02_Caption.txt')).read_text();m['animation_version']='v2';m['save_prompt_in_voice_and_visuals']=sentence
 name=qa[i]['file'].split('/')[-1];sha=hashlib.sha256((F/name).read_bytes()).hexdigest()
 if i==0:m['checks']['video']['duration_seconds']=qa[i]['duration_seconds'];m['checks']['caption_characters']=len(m['caption']);m['checks']['sha256'][name]=sha
 else:m['duration_seconds']=qa[i]['duration_seconds'];m['sha256'][name]=sha
 p.write_text(json.dumps(m,ensure_ascii=False,indent=2))
p=F/'Series_Plan.json';s=json.loads(p.read_text());s['save_prompt']=sentence;s['animation_version']='v2';s['animation_requirements']=['Meaningful visuals match the spoken topic','Calendar pages flip and relevant dates highlight in order','Verification cards and check marks appear sequentially','Transfer chances appear as individual tokens','Cancellation uses an animated document/stamp','Save CTA uses an animated bookmark and check','Series title/topic/next-episode teaser enter in stages','Keep actual website UI demo to 10–15 seconds; no fabricated question UI']
for i,e in enumerate(s['episodes']):e['duration_seconds']=qa[i]['duration_seconds']
assert not s['publish_enabled'] and not s['automation_enabled'];p.write_text(json.dumps(s,ensure_ascii=False,indent=2))
(F/'Motion_Videos_QA.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2))
p=F/'README_HOLD.txt';p.write_text(p.read_text()+'\nMOTION V2: Both reels now include the spoken save-first prompt, animated bookmark, motion-rich explanatory scenes and staged series intros/outros. Publication and the recurring task remain on review HOLD.\n')
with zipfile.ZipFile(R/'Postal_Wala_Rule3_Instagram_Ready.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(F.iterdir()):
  if f.is_file():z.write(f,f.name)
print(json.dumps({'updated':2,'durations':[x['duration_seconds'] for x in qa],'animation_version':'v2','published':False},ensure_ascii=False))
