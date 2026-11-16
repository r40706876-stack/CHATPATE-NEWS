import json,os,pathlib,sys,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from deep import deep_demo as D
from playwright.sync_api import sync_playwright
D.M.TTS_WAITS=(20,40);os.environ['GEMINI_TTS_KEYS']=''
bed=D.M.music_bed;D.M.music_bed=lambda t:bed(t)*.5
src=pathlib.Path(__file__).with_name('promo.html');out=ROOT/'demo_out/mock_promo/Postal_Wala_Mock_Promo.mp4';out.parent.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
 b=p.chromium.launch();pg=b.new_page(viewport={'width':540,'height':960},device_scale_factor=2);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.goto(src.as_uri());pg.evaluate('window.READY()');assert pg.evaluate('Number.isFinite(TOTAL)');assert not errs,errs
 for t in [2,8,15,23,30]:pg.evaluate('(t)=>seek(t)',t);pg.screenshot(path=str(out.parent/f'layout_{t}.png'))
 b.close()
D.sys.argv=['deep_demo.py',str(src),str(out)];D.main()
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(out)]));v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio');assert (v['width'],v['height'])==(1080,1920);assert v['codec_name']=='h264' and a['codec_name']=='aac'
subprocess.run(['ffmpeg','-v','error','-i',str(out),'-f','null','-'],check=True)
for t in [2,9,16,23,28]:
 if t<float(probe['format']['duration']):subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(out),'-frames:v','1',str(out.parent/f'frame_{t}.jpg')],check=True)
(out.parent/'QA.json').write_text(json.dumps({'duration':float(probe['format']['duration']),'dimensions':[1080,1920],'decode':'pass','claims':{'free_mock_competition':'Provided by the brand owner','deep_explanation':'Present on source website'},'example_ids':['ministry','p_95658e4d21'],'sources':['https://postalwala.pages.dev/#mock','https://www.indiapost.gov.in/organisation','https://www.indiapost.gov.in/documents/documents/actsandpolicies/PORegulationAct2024.pdf'],'publish':False},indent=2))
print('MOCK_PROMO_VERIFIED',out,flush=True)
