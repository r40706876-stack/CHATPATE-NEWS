from pathlib import Path
import json,hashlib,shutil,zipfile,subprocess
R=Path('/workspace/scratch/b0b64e20710c');J=R/'postal_series_job';F=R/'postal_rule3_instagram_ready';V=J/'final'
qa=json.loads((V/'Series_Video_QA.json').read_text())
assert all(x['technical_decode']=='pass' for x in qa)
for name in ['Postal_Wala_GDS_Rule3.mp4','Postal_Wala_GDS_Transfer_Dates.mp4']:
 shutil.copy2(V/name,F/name)
title1='डाक विभाग के डाउट्स | भाग 01: GDS Transfer—1 साल या 2 साल? | Postal Wala'
title2='डाक विभाग के डाउट्स | भाग 02: GDS Transfer की 5 जरूरी तारीखें | Postal Wala'
cap=(F/'Instagram_Caption.txt').read_text();cap=title1+'\n\n'+cap.split('\n\n',1)[1]
notice='''📮 हमारी नई सीरीज़: डाक विभाग के डाउट्स
ट्रांसफर, सेवा नियम और विभागीय परीक्षा—रोज़ एक टॉपिक, आसान भाषा में।
⏰ रोज़ शाम 6:30 बजे (IST)। अगला भाग देखने के लिए @postal_wala को फॉलो करें।
कल भाग 02: GDS ट्रांसफर की पाँच जरूरी तारीखें और पूरा क्रम।

'''
cap=cap.replace('घर के पास ट्रांसफर चाहते हैं?',notice+'घर के पास ट्रांसफर चाहते हैं?')
cap=cap.replace('#GraminDakSevak','#PostalDoubts');assert len(cap)<2200
(F/'Instagram_Caption.txt').write_text(cap)
cap2='''डाक विभाग के डाउट्स | भाग 02 📮

आज का विषय: GDS ट्रांसफर की पाँच जरूरी तारीखें और पूरी प्रक्रिया का क्रम।
आवेदन, पसंद में बदलाव, मंजूर सूची, रद्द करने की विंडो और रिलीविंग—वीडियो में समझें।

हमारी इस सीरीज़ में ट्रांसफर, सेवा नियम और विभागीय परीक्षा के डाउट्स की जानकारी नियमित आएगी।
⏰ रोज़ शाम 6:30 बजे (IST)। @postal_wala को फॉलो करें और अपने GDS साथी को भेजें।

📚 Postal Wala पर फ्री मॉक टेस्ट कॉम्पिटिशन में हिस्सा लें। सही जवाब की वजह, बाकी विकल्पों की गलती, exam trap और याद रखने की ट्रिक—वेबसाइट के असली सवाल के साथ देखें।
🌐 https://postalwala.pages.dev/#mock

आवेदन से पहले संबंधित साइकिल का आधिकारिक विभागीय पत्र और पोर्टल की समय-सारणी मिलाएँ।

#GDSTransfer #Rule3Transfer #IndiaPost #PostalWala #PostalDoubts'''
assert len(cap2)<2200;(F/'Episode_02_Caption.txt').write_text(cap2)
(F/'Title_and_Tags.txt').write_text(title1+'\n\n#GDSTransfer #Rule3Transfer #PostalDoubts #IndiaPost #PostalWala\n')
(F/'Episode_02_Title_and_Tags.txt').write_text(title2+'\n\n#GDSTransfer #Rule3Transfer #IndiaPost #PostalWala #PostalDoubts\n')
subprocess.run(['ffmpeg','-v','error','-y','-ss','1','-i',str(V/'Postal_Wala_GDS_Transfer_Dates.mp4'),'-frames:v','1',str(F/'Episode_02_Cover.png')],check=True)
plan={'series_name':'Postal Wala — डाक विभाग के डाउट्स','editorial_scope':['ट्रांसफर','सेवा नियम','विभागीय परीक्षा के डाउट्स'],'daily_time':'18:30','timezone':'Asia/Kolkata','review_status':'HOLD_AWAITING_USER_REVIEW','publish_enabled':False,'automation_id':'Automation_d9a899e6cc50819193fbfd7eb4a486cc','automation_enabled':False,'format':['Short series introduction and episode number','One concrete doubt','Clear visual explanation using the Postal Wala character and relevant animation','Actual website question demo limited to 10–15 seconds when included','Regular 6:30 PM IST follow CTA','Episode 01 previews episode 02 as tomorrow’s topic'],'demo_duration_seconds':12.5,'episodes':[{'number':1,'title':title1,'video_file':'Postal_Wala_GDS_Rule3.mp4','library_file_id':'libfile_b9c6a8831f608191a40ee4a041408af4','intended_slot_ist':'2026-11-16T18:30:00+05:30','duration_seconds':qa[0]['duration_seconds'],'teaser':'कल: जीडीएस ट्रांसफर की पाँच जरूरी तारीखें।'},{'number':2,'title':title2,'video_file':'Postal_Wala_GDS_Transfer_Dates.mp4','library_file_id':'libfile_0badc156b0488191a903417c6aced825','intended_slot_ist':'2026-11-17T18:30:00+05:30','duration_seconds':qa[1]['duration_seconds']}],'publication_checks':['Release review hold only on user instruction','Validate official source and dates for the relevant cycle before release','If planned dates slip, adjust tomorrow wording and episode order before publication','Confirm authenticated Instagram account is postal_wala','Use correct episode media, caption and cover','Avoid duplicate media IDs; preserve other queues'],'production_voice_scripts':json.loads((J/'voice/narration.json').read_text())}
(F/'Series_Plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
m=json.loads((F/'Posting_Manifest_HOLD.json').read_text());m.update(status='HOLD_AWAITING_USER_REVIEW',title=title1,caption=cap,hashtags=['#GDSTransfer','#Rule3Transfer','#PostalDoubts','#IndiaPost','#PostalWala'],timezone='Asia/Kolkata',series_name=plan['series_name'],series_episode=1,intended_slot_ist=plan['episodes'][0]['intended_slot_ist'])
assert m['publish_at'] is None and not m['publish_enabled'] and not m['scheduled'] and not m['published']
m['checks']['caption_characters']=len(cap);m['checks']['video']['duration_seconds']=qa[0]['duration_seconds'];m['checks']['sha256']['Postal_Wala_GDS_Rule3.mp4']=hashlib.sha256((F/'Postal_Wala_GDS_Rule3.mp4').read_bytes()).hexdigest();m['series_plan_file']='Series_Plan.json'
(F/'Posting_Manifest_HOLD.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
m2={'status':'HOLD_AWAITING_USER_REVIEW','platform':'instagram','account_username':'postal_wala','series_name':plan['series_name'],'series_episode':2,'title':title2,'caption':cap2,'video_file':'Postal_Wala_GDS_Transfer_Dates.mp4','cover_file':'Episode_02_Cover.png','intended_slot_ist':plan['episodes'][1]['intended_slot_ist'],'publish_at':None,'publish_enabled':False,'scheduled':False,'published':False,'timezone':'Asia/Kolkata','duration_seconds':qa[1]['duration_seconds'],'sha256':{n:hashlib.sha256((F/n).read_bytes()).hexdigest() for n in ['Postal_Wala_GDS_Transfer_Dates.mp4','Episode_02_Cover.png']},'source_check_required_before_publish':True}
(F/'Episode_02_Posting_Manifest_HOLD.json').write_text(json.dumps(m2,ensure_ascii=False,indent=2))
readme=(F/'README_HOLD.txt').read_text().replace('Wait for the user to specify date/time in IST and instruct publication.','Daily slot is confirmed as 6:30 PM IST. Both revised episodes are awaiting user review; publication and the prepared recurring task remain paused.')
readme+='\nSERIES UPDATE: Both episodes now include series identity, episode number, daily 6:30 PM IST follow CTA and a 12.5-second actual website demo. Episode 01 teases episode 02. See Series_Plan.json for the planned order and review hold.\n'
(F/'README_HOLD.txt').write_text(readme)
with zipfile.ZipFile(R/'Postal_Wala_Rule3_Instagram_Ready.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(F.iterdir()):
  if p.is_file():z.write(p,p.name)
print(json.dumps({'videos_updated':2,'series_name':plan['series_name'],'daily_time_ist':'18:30','published':False,'automation_enabled':False,'caption_lengths':[len(cap),len(cap2)]},ensure_ascii=False))
