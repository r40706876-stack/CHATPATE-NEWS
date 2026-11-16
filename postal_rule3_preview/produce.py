"""Source-backed Rule 3 professional explainer; one explicitly selected Gemini key."""
import json, os, pathlib, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from deep import deep_demo as D
D.M.TTS_WAITS=(20,40)
os.environ['GEMINI_TTS_KEYS']=''
src=pathlib.Path(__file__).with_name('rule3.html')
out=ROOT/'demo_out/rule3/Postal_Wala_GDS_Rule3.mp4'
D.sys.argv=['deep_demo.py',str(src),str(out)]
D.main()
info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(out)]))
v=next(x for x in info['streams'] if x['codec_type']=='video')
a=next(x for x in info['streams'] if x['codec_type']=='audio')
assert (v['width'],v['height'])==(1080,1920)
assert v['codec_name']=='h264' and a['codec_name']=='aac'
assert 35<float(info['format']['duration'])<125
subprocess.run(['ffmpeg','-v','error','-i',str(out),'-f','null','-'],check=True)
for t in [2,12,23,34,45,56]:
 if t<float(info['format']['duration']):subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(out),'-frames:v','1',str(out.parent/f'frame_{t}.jpg')],check=True)
(out.parent/'technical_qa.json').write_text(json.dumps({'duration':float(info['format']['duration']),'width':v['width'],'height':v['height'],'video_codec':v['codec_name'],'audio_codec':a['codec_name'],'decode_check':'pass','gemini_key_slot':4,'source':'https://utilities.cept.gov.in/dop/pdfbind.ashx?id=14939','source_date':'21-05-2026','scope':'eligibility explainer; no unverified cycle dates'},indent=2))
(out.parent/'sources.txt').write_text('Department of Posts, 21-05-2026, No.17-31/2016-GDS(Pt.I), Annexure FAQ 1–4 and 18.\nhttps://utilities.cept.gov.in/dop/pdfbind.ashx?id=14939\nEligibility explainer; no announcement of current application dates.\n')
print('RULE3_PRODUCTION_VERIFIED',str(out),flush=True)
