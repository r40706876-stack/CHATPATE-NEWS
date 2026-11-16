import os,json,sys,pathlib,subprocess,concurrent.futures
from PIL import Image,ImageChops,ImageStat
from playwright.sync_api import sync_playwright
kind=sys.argv[1];P=pathlib.Path(__file__).resolve().parent;S=pathlib.Path('../base').resolve();O=pathlib.Path('../out').resolve();O.mkdir(exist_ok=True)
source=S/('postal_rule3_preview/rule3.html' if kind=='norm' else 'postal_dates_preview/dates.html')
html=source.read_text();html=html.replace('</html>','<script>'+ (P/'motion.js').read_text()+'</script></html>')
local=source.with_name('motion_v2.html');local.write_text(html)
cues=json.loads((P/(kind+'_cues.json')).read_text());start,end=(6.03,41.23) if kind=='norm' else (4.82,30.60)
fps=30;n=round((end-start)*fps);F=O/'frames';F.mkdir(exist_ok=True)
def openpage(p):
 b=p.chromium.launch();pg=b.new_page(viewport={'width':540,'height':960},device_scale_factor=2);errors=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.add_init_script('window.CUES='+json.dumps(cues)+';');pg.goto(local.as_uri());pg.evaluate('document.fonts.ready');pg.evaluate('window.READY?window.READY():1');assert not errors,errors;return b,pg
def part(lo,hi):
 with sync_playwright() as p:
  b,pg=openpage(p)
  for i in range(lo,hi):
   pg.evaluate('(t)=>window.seek(t)',start+i/fps);pg.screenshot(path=str(F/f'{i:05d}.jpg'),type='jpeg',quality=93)
  b.close()
 print('FRAMES',kind,lo,hi,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
 futures=[ex.submit(part,n*k//3,n*(k+1)//3) for k in range(3)]
 for f in futures:f.result()
subprocess.run(['ffmpeg','-v','error','-y','-framerate',str(fps),'-i',str(F/'%05d.jpg'),'-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-threads','2','-movflags','+faststart',str(O/(kind+'_animated_body.mp4'))],check=True)
checks=[]
with sync_playwright() as p:
 b,pg=openpage(p)
 for i,t in enumerate(([6.4,9.8,15.3,28.7,33.1] if kind=='norm' else [5.2,11,14.7,18.4,27.4])):
  shots=[]
  for k,delta in enumerate([0,.45]):
   pg.evaluate('(t)=>window.seek(t)',t+delta);file=O/f'pose_{i}_{k}.jpg';pg.screenshot(path=str(file),type='jpeg',quality=94);shots.append(Image.open(file).crop((40,570,1040,1340)).convert('RGB'))
  diff=ImageChops.difference(*shots);mean=sum(ImageStat.Stat(diff).mean)/3;checks.append({'scene_time':t,'delta_seconds':.45,'visual_region_mean_pixel_change':round(mean,3)});assert mean>.30,(kind,t,mean)
 b.close()
(O/'Motion_QA.json').write_text(json.dumps({'kind':kind,'duration_seconds':n/fps,'original_time_range':[start,end],'fps':fps,'motion_checks':checks,'voice_timing_reused':True},indent=2))
print('ANIMATED_BODY_COMPLETE',kind,flush=True)
