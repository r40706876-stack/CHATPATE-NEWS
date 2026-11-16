import json,os,pathlib,subprocess,sys,shutil
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from deep import deep_demo as D
from playwright.sync_api import sync_playwright
D.M.TTS_WAITS=(20,40);os.environ['GEMINI_TTS_KEYS']=''
original_bed=D.M.music_bed
D.M.music_bed=lambda t:original_bed(t)*.5
src=pathlib.Path(__file__).with_name('dates.html');out=ROOT/'demo_out/rule3_dates/Postal_Wala_GDS_Transfer_Dates.mp4';out.parent.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
 b=p.chromium.launch();page=b.new_page(viewport={'width':540,'height':960},device_scale_factor=2);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(src.as_uri());page.evaluate('window.READY()');assert page.evaluate('Number.isFinite(window.TOTAL)');assert page.evaluate('gsap.version')=='3.12.5';assert not errors,errors
 for t in [2,10,20,30,40,50]:
  page.evaluate('(t)=>window.seek(t)',t);page.screenshot(path=str(out.parent/f'layout_{t}.png'))
 b.close()
previous=out.parent/'previous_render.mp4'
cuefile=pathlib.Path(str(out)+'.cues.json')
if out.exists() and cuefile.exists():
 shutil.copy2(out,previous)
 silent=out.parent/'dates_new_silent.mp4'
 print('REUSE_VERIFIED_NARRATION_AND_CUES: no Gemini generation',flush=True)
 subprocess.run([sys.executable,str(ROOT/'deep/render_deep.py'),str(src),str(silent),str(cuefile)],check=True)
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(silent),'-i',str(previous),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','copy','-shortest','-movflags','+faststart',str(out)],check=True)
 previous.unlink();silent.unlink()
else:
 D.sys.argv=['deep_demo.py',str(src),str(out)];D.main()
info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(out)]));v=next(x for x in info['streams'] if x['codec_type']=='video');a=next(x for x in info['streams'] if x['codec_type']=='audio');assert (v['width'],v['height'])==(1080,1920);assert v['codec_name']=='h264' and a['codec_name']=='aac';assert 30<float(info['format']['duration'])<110
subprocess.run(['ffmpeg','-v','error','-i',str(out),'-f','null','-'],check=True)
for t in [2,10,18,26,34,42]:
 if t<float(info['format']['duration']):subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(out),'-frames:v','1',str(out.parent/f'frame_{t}.jpg')],check=True)
(out.parent/'QA.json').write_text(json.dumps({'duration':float(info['format']['duration']),'width':1080,'height':1920,'video':'h264','audio':'aac','decode':'pass','animation':'GSAP 3.12.5 + character + calendar + timeline','gemini_key_slot':4,'date_source':'User-confirmed dates from shared reference reel; original circular not independently retrieved','cta':'GDS के सभी अपडेट के लिए हमसे जुड़े रहें। Postal Wala.','publication_status':'PREVIEW_ONLY'},ensure_ascii=False,indent=2))
print('DATES_VIDEO_VERIFIED',str(out),flush=True)
